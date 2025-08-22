"""
Biodesk - Módulo Templates Manager
=================================

Módulo especializado para gestão de templates e prescrições médicas.
Extraído do monólito ficha_paciente.py.

🎯 Funcionalidades:
- Sistema de templates por categorias
- Preview integrado de texto e PDF
- Gestão de protocolos terapêuticos
- Templates editáveis e personalizáveis
- Geração automática de documentos

⚡ Performance:
- Lazy loading de templates
- Cache de templates usados frequentemente
- Preview otimizado sem QWebEngine

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from biodesk_ui_kit import BiodeskUIKit
from data_cache import DataCache
from biodesk_dialogs import BiodeskMessageBox


class TemplatesManagerWidget(QWidget):
    """Widget especializado para gestão de templates e prescrições"""
    
    # Sinais para comunicação
    template_selecionado = pyqtSignal(dict)  # Template selecionado
    protocolo_adicionado = pyqtSignal(str)   # Protocolo adicionado
    template_gerado = pyqtSignal(str, str)   # Tipo, conteúdo gerado
    
    def __init__(self, paciente_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        # Cache e dados
        self.cache = DataCache.get_instance()
        self.paciente_data = paciente_data or {}
        
        # Estado interno
        self.protocolos_selecionados = []
        self.template_atual = None
        self.pdf_path_atual = None
        
        # Referências de widgets
        self.btn_categories = {}
        self.templates_areas = {}
        self.template_preview = None
        self.preview_stack = None
        
        # Configurar interface
        self.init_ui()
        self.inicializar_templates_padrao()
        
    def init_ui(self):
        """Inicializa interface dos templates"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Layout horizontal principal
        main_horizontal = QHBoxLayout()
        
        # Área de categorias (esquerda)
        self.criar_area_categorias(main_horizontal)
        
        # Área de preview (centro)
        self.criar_area_preview(main_horizontal)
        
        # Área de botões (direita)
        self.criar_area_botoes(main_horizontal)
        
        layout.addLayout(main_horizontal, 1)
        
    def criar_area_categorias(self, parent_layout):
        """Cria área de categorias de templates"""
        categorias_frame = QFrame()
        categorias_frame.setFixedWidth(280)
        categorias_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BiodeskUIKit.COLORS['background_light']};
                border: 1px solid {BiodeskUIKit.COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        categorias_layout = QVBoxLayout(categorias_frame)
        
        # Título
        cat_titulo = QLabel("🩺 Protocolos Terapêuticos")
        cat_titulo.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {BiodeskUIKit.COLORS['dark']};
            margin-bottom: 8px;
            padding: 6px;
            background-color: {BiodeskUIKit.COLORS['border_light']};
            border-radius: 5px;
        """)
        cat_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        categorias_layout.addWidget(cat_titulo)
        
        # Scroll area para categorias
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Guardar referência
        self.categorias_scroll_layout = scroll_layout
        
        # Categorias de templates
        self.template_categories = [
            ("🏃", "Exercícios e Alongamentos", "exercicios", "#ffeaa7"),
            ("🥗", "Nutrição & Dietética", "dietas", "#a8e6cf"),
            ("💊", "Suplementação", "suplementos", "#ffd3e1"),
            ("📋", "Autocuidado e Rotinas", "orientacoes", "#e6d7ff"),
            ("📚", "Guias Educativos", "educativos", "#e1f5fe"),
            ("🎯", "Específicos por Condição", "condicoes", "#f3e5f5")
        ]
        
        # Criar botões de categorias
        for emoji, nome, categoria, cor in self.template_categories:
            categoria_container = QWidget()
            categoria_container_layout = QVBoxLayout(categoria_container)
            categoria_container_layout.setContentsMargins(0, 0, 0, 5)
            
            # Botão da categoria
            btn = QPushButton(f"{emoji} {nome}")
            btn.setFixedHeight(35)
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px;
                    font-weight: 600;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 10px;
                    background-color: {cor};
                    color: {BiodeskUIKit.COLORS['dark']};
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(cor, 15)};
                }}
                QPushButton:pressed {{
                    background-color: {self._lighten_color(cor, 25)};
                }}
            """)
            
            # Área para templates (inicialmente oculta)
            templates_area = QWidget()
            templates_layout = QVBoxLayout(templates_area)
            templates_layout.setContentsMargins(15, 5, 0, 0)
            templates_area.setVisible(False)
            
            self.templates_areas[categoria] = templates_area
            self.btn_categories[categoria] = btn
            
            # Conectar clique
            btn.clicked.connect(lambda checked, cat=categoria: self.toggle_categoria_templates(cat))
            
            categoria_container_layout.addWidget(btn)
            categoria_container_layout.addWidget(templates_area)
            categoria_container_layout.addSpacing(15)
            
            scroll_layout.addWidget(categoria_container)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        categorias_layout.addWidget(scroll_area)
        parent_layout.addWidget(categorias_frame, 3)
        
    def criar_area_preview(self, parent_layout):
        """Cria área de preview dos templates"""
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BiodeskUIKit.COLORS['white']};
                border: 3px solid {BiodeskUIKit.COLORS['primary']};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        # Widget empilhado para texto/PDF
        self.preview_stack = QStackedWidget()
        
        # Preview de texto
        self.template_preview = QTextEdit()
        self.template_preview.setMinimumHeight(250)
        self.template_preview.setMaximumHeight(300)
        self.template_preview.setPlaceholderText("""
📄 PREVIEW INTEGRADO - TEMPLATES MÉDICOS

Selecione um template à esquerda para visualizar:

📝 TEMPLATES TEXTO: Conteúdo formatado médico
📄 TEMPLATES PDF: Documentos especializados

🩺 Cabeçalho com logo Dr. Nuno Correia
📋 Dados completos do paciente  
📝 Conteúdo do template formatado
✅ Orientações médicas personalizadas
👨‍⚕️ Assinatura profissional

✨ Sistema otimizado sem janelas popup
        """)
        self.template_preview.setStyleSheet(f"""
            QTextEdit {{
                background: {BiodeskUIKit.COLORS['white']};
                border: none;
                border-radius: 5px;
                padding: 20px;
                font-family: 'Times New Roman', serif;
                font-size: 11px;
                color: {BiodeskUIKit.COLORS['dark']};
                line-height: 1.4;
            }}
        """)
        self.template_preview.setReadOnly(True)
        
        # Widget para PDFs externos
        self.pdf_external_widget = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_external_widget)
        
        pdf_label = QLabel("📄 Visualização de PDFs")
        pdf_label.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold; 
            color: {BiodeskUIKit.COLORS['dark']};
            padding: 10px;
        """)
        
        self.btn_abrir_pdf_externo = BiodeskUIKit.create_primary_button("🔍 Abrir PDF no Visualizador Externo")
        self.btn_abrir_pdf_externo.clicked.connect(self.abrir_pdf_atual_externo)
        self.btn_abrir_pdf_externo.setEnabled(False)
        
        info_label = QLabel("💡 Os PDFs serão abertos no seu visualizador padrão\\n(Adobe Reader, Navegador, etc.)")
        info_label.setStyleSheet(f"""
            color: {BiodeskUIKit.COLORS['text_muted']};
            font-size: 12px;
            padding: 10px;
            background: {BiodeskUIKit.COLORS['background_light']};
            border-radius: 4px;
            border: 1px solid {BiodeskUIKit.COLORS['border_light']};
        """)
        
        pdf_layout.addWidget(pdf_label)
        pdf_layout.addWidget(self.btn_abrir_pdf_externo)
        pdf_layout.addWidget(info_label)
        pdf_layout.addStretch()
        
        # Adicionar ao stack
        self.preview_stack.addWidget(self.template_preview)
        self.preview_stack.addWidget(self.pdf_external_widget)
        self.preview_stack.setCurrentIndex(0)
        
        preview_layout.addWidget(self.preview_stack, 1)
        
        # Botão PDF
        self.btn_pdf_preview = BiodeskUIKit.create_secondary_button("🔍 Abrir PDF Completo")
        self.btn_pdf_preview.clicked.connect(self.abrir_pdf_atual_externo)
        self.btn_pdf_preview.setEnabled(False)
        self.btn_pdf_preview.setVisible(False)
        
        preview_layout.addWidget(self.btn_pdf_preview)
        parent_layout.addWidget(preview_frame, 2)
        
    def criar_area_botoes(self, parent_layout):
        """Cria área de botões de ação"""
        botoes_frame = QFrame()
        botoes_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {BiodeskUIKit.COLORS['background_light']}, 
                    stop:1 {BiodeskUIKit.COLORS['border_light']});
                border: 2px solid {BiodeskUIKit.COLORS['border']};
                border-radius: 12px;
                padding: 20px;
                margin: 5px;
            }}
        """)
        botoes_layout = QVBoxLayout(botoes_frame)
        botoes_layout.setSpacing(12)
        
        # Área de protocolos selecionados
        protocolos_frame = QFrame()
        protocolos_frame.setMinimumHeight(130)
        protocolos_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #fff3cd, stop:1 #ffeaa7);
                border: 2px solid #f0c14b;
                border-radius: 10px;
                padding: 12px;
                margin: 5px 0px;
            }
        """)
        protocolos_layout = QVBoxLayout(protocolos_frame)
        protocolos_layout.setSpacing(8)
        
        protocolos_titulo = QLabel("📋 Protocolos Selecionados")
        protocolos_titulo.setStyleSheet("""
            font-weight: bold; 
            color: #856404; 
            font-size: 11px;
            margin-bottom: 8px;
            padding: 4px;
            background-color: rgba(255,255,255,0.7);
            border-radius: 4px;
        """)
        protocolos_layout.addWidget(protocolos_titulo)
        
        # Lista de protocolos
        self.protocolos_lista = QListWidget()
        self.protocolos_lista.setMaximumHeight(70)
        self.protocolos_lista.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.9);
                border: 1px solid #f0c14b;
                border-radius: 4px;
                font-size: 10px;
                color: #856404;
            }
            QListWidget::item {
                padding: 2px 5px;
                border-bottom: 1px solid #f0c14b;
            }
            QListWidget::item:selected {
                background: #f0c14b;
                color: white;
            }
        """)
        protocolos_layout.addWidget(self.protocolos_lista)
        
        botoes_layout.addWidget(protocolos_frame)
        
        # Botões de ação
        self.btn_adicionar_protocolo = BiodeskUIKit.create_success_button("➕ Adicionar")
        self.btn_adicionar_protocolo.clicked.connect(self.adicionar_protocolo_atual)
        self.btn_adicionar_protocolo.setEnabled(False)
        botoes_layout.addWidget(self.btn_adicionar_protocolo)
        
        self.btn_remover_protocolo = BiodeskUIKit.create_danger_button("➖ Remover")
        self.btn_remover_protocolo.clicked.connect(self.remover_protocolo_selecionado)
        self.btn_remover_protocolo.setEnabled(False)
        botoes_layout.addWidget(self.btn_remover_protocolo)
        
        self.btn_gerar_prescricao = BiodeskUIKit.create_primary_button("📄 Gerar Prescrição")
        self.btn_gerar_prescricao.clicked.connect(self.gerar_prescricao_completa)
        botoes_layout.addWidget(self.btn_gerar_prescricao)
        
        self.btn_novo_template = BiodeskUIKit.create_secondary_button("➕ Novo Template")
        self.btn_novo_template.clicked.connect(self.criar_novo_template)
        botoes_layout.addWidget(self.btn_novo_template)
        
        botoes_layout.addStretch()
        parent_layout.addWidget(botoes_frame, 2)
        
    def toggle_categoria_templates(self, categoria):
        """Alterna visibilidade dos templates de uma categoria"""
        templates_area = self.templates_areas.get(categoria)
        if not templates_area:
            return
            
        # Alternar visibilidade
        is_visible = templates_area.isVisible()
        templates_area.setVisible(not is_visible)
        
        # Carregar templates se necessário
        if not is_visible and not templates_area.layout().count():
            self.carregar_templates_categoria(categoria)
    
    def carregar_templates_categoria(self, categoria):
        """Carrega templates de uma categoria específica"""
        templates_area = self.templates_areas.get(categoria)
        if not templates_area:
            return
            
        layout = templates_area.layout()
        
        # Templates por categoria (simulando base de dados)
        templates_db = {
            'exercicios': [
                'Alongamentos Cervicais',
                'Exercícios Posturais',
                'Fortalecimento Core',
                'Mobilização Articular'
            ],
            'dietas': [
                'Dieta Anti-inflamatória',
                'Plano Detox 7 dias',
                'Alimentação Alcalina',
                'Dieta Mediterrânica'
            ],
            'suplementos': [
                'Complexo Vitamínico B',
                'Ómega 3 + Cúrcuma',
                'Magnésio + Zinco',
                'Probióticos Intestinais'
            ],
            'orientacoes': [
                'Higiene do Sono',
                'Gestão do Stress',
                'Hidratação Adequada',
                'Rotina Matinal'
            ],
            'educativos': [
                'Guia Alimentação Saudável',
                'Manual Exercícios Casa',
                'Técnicas Relaxamento',
                'Prevenção Lesões'
            ],
            'condicoes': [
                'Protocolo Ansiedade',
                'Tratamento Insónia',
                'Dores Articulares',
                'Fadiga Crónica'
            ]
        }
        
        templates = templates_db.get(categoria, [])
        
        for template_nome in templates:
            btn_template = QPushButton(f"📄 {template_nome}")
            btn_template.setFixedHeight(25)
            btn_template.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BiodeskUIKit.COLORS['white']};
                    color: {BiodeskUIKit.COLORS['dark']};
                    border: 1px solid {BiodeskUIKit.COLORS['border_light']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {BiodeskUIKit.COLORS['primary']};
                    color: {BiodeskUIKit.COLORS['white']};
                }}
            """)
            
            # Conectar seleção de template
            btn_template.clicked.connect(
                lambda checked, nome=template_nome, cat=categoria: 
                self.selecionar_template(nome, cat)
            )
            
            layout.addWidget(btn_template)
    
    def selecionar_template(self, nome, categoria):
        """Seleciona um template e mostra preview"""
        self.template_atual = {'nome': nome, 'categoria': categoria}
        
        # Simular carregamento de template
        conteudo = self.gerar_conteudo_template(nome, categoria)
        
        # Mostrar no preview
        self.template_preview.setHtml(conteudo)
        self.preview_stack.setCurrentIndex(0)  # Mostrar texto
        
        # Ativar botão de adicionar
        self.btn_adicionar_protocolo.setEnabled(True)
        
        # Emitir sinal
        self.template_selecionado.emit(self.template_atual)
    
    def gerar_conteudo_template(self, nome, categoria):
        """Gera conteúdo HTML do template"""
        nome_paciente = self.paciente_data.get('nome', 'Paciente')
        
        # Template base
        html = f"""
        <div style="font-family: 'Times New Roman', serif; line-height: 1.6; color: #2c3e50;">
            <div style="text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin: 0;">Dr. Nuno Correia</h2>
                <p style="margin: 5px 0; color: #7f8c8d;">Medicina Integrativa & Terapias Naturais</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="color: #e74c3c; border-left: 4px solid #e74c3c; padding-left: 10px;">
                    📋 {nome}
                </h3>
                <p><strong>Paciente:</strong> {nome_paciente}</p>
                <p><strong>Data:</strong> {QDate.currentDate().toString('dd/MM/yyyy')}</p>
            </div>
            
            <div style="background: #ecf0f1; padding: 15px; border-radius: 8px; margin: 15px 0;">
                {self._gerar_conteudo_especifico(nome, categoria)}
            </div>
            
            <div style="margin-top: 30px; border-top: 1px solid #bdc3c7; padding-top: 15px;">
                <p style="text-align: center; color: #7f8c8d; font-size: 12px;">
                    Documento gerado em {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm')}
                </p>
            </div>
        </div>
        """
        
        return html
    
    def _gerar_conteudo_especifico(self, nome, categoria):
        """Gera conteúdo específico baseado no template"""
        conteudos = {
            'Alongamentos Cervicais': """
                <h4>🏃 Protocolo de Alongamentos Cervicais</h4>
                <ol>
                    <li><strong>Alongamento lateral:</strong> Inclinar cabeça para o lado, manter 30s cada lado</li>
                    <li><strong>Rotação:</strong> Girar cabeça suavemente, 10 repetições cada lado</li>
                    <li><strong>Flexão/Extensão:</strong> Queixo ao peito e depois para trás, 10 repetições</li>
                </ol>
                <p><em>Realizar 2x por dia, manhã e noite.</em></p>
            """,
            'Dieta Anti-inflamatória': """
                <h4>🥗 Plano Alimentar Anti-inflamatório</h4>
                <p><strong>Alimentos a privilegiar:</strong></p>
                <ul>
                    <li>Peixes ricos em ómega-3 (salmão, sardinha, cavala)</li>
                    <li>Vegetais de folha verde escura</li>
                    <li>Frutos vermelhos e açaí</li>
                    <li>Cúrcuma e gengibre</li>
                </ul>
                <p><strong>Evitar:</strong> Açúcar refinado, alimentos processados, gorduras trans</p>
            """,
            'Complexo Vitamínico B': """
                <h4>💊 Protocolo de Suplementação - Complexo B</h4>
                <p><strong>Dosagem:</strong> 1 cápsula ao pequeno-almoço</p>
                <p><strong>Duração:</strong> 3 meses</p>
                <p><strong>Benefícios:</strong> Energia, função neurológica, metabolismo</p>
                <p><strong>Observações:</strong> Tomar com alimentos para melhor absorção</p>
            """
        }
        
        return conteudos.get(nome, f"<p>Conteúdo do template <strong>{nome}</strong> da categoria {categoria}.</p>")
    
    def adicionar_protocolo_atual(self):
        """Adiciona o template atual aos protocolos selecionados"""
        if not self.template_atual:
            return
            
        nome = self.template_atual['nome']
        if nome not in self.protocolos_selecionados:
            self.protocolos_selecionados.append(nome)
            self.protocolos_lista.addItem(nome)
            self.btn_remover_protocolo.setEnabled(True)
            
            # Emitir sinal
            self.protocolo_adicionado.emit(nome)
    
    def remover_protocolo_selecionado(self):
        """Remove protocolo selecionado da lista"""
        current_row = self.protocolos_lista.currentRow()
        if current_row >= 0:
            item = self.protocolos_lista.takeItem(current_row)
            if item:
                self.protocolos_selecionados.remove(item.text())
                
        if not self.protocolos_selecionados:
            self.btn_remover_protocolo.setEnabled(False)
    
    def gerar_prescricao_completa(self):
        """Gera prescrição completa com todos os protocolos"""
        if not self.protocolos_selecionados:
            BiodeskMessageBox.warning(self, "Aviso", "Selecione pelo menos um protocolo!")
            return
            
        # Gerar HTML completo
        html_completo = self._gerar_prescricao_html()
        
        # Emitir sinal com prescrição gerada
        self.template_gerado.emit("prescricao_completa", html_completo)
        
        # Mostrar preview
        self.template_preview.setHtml(html_completo)
        
        BiodeskMessageBox.information(self, "Sucesso", "✅ Prescrição gerada com sucesso!")
    
    def _gerar_prescricao_html(self):
        """Gera HTML da prescrição completa"""
        nome_paciente = self.paciente_data.get('nome', 'Paciente')
        
        protocolos_html = ""
        for i, protocolo in enumerate(self.protocolos_selecionados, 1):
            protocolos_html += f"""
                <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #28a745;">
                    <h4 style="color: #28a745; margin: 0 0 10px 0;">{i}. {protocolo}</h4>
                    {self._gerar_conteudo_especifico(protocolo, "geral")}
                </div>
            """
        
        html = f"""
        <div style="font-family: 'Times New Roman', serif; line-height: 1.6; color: #2c3e50;">
            <div style="text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 25px;">
                <h1 style="color: #2c3e50; margin: 0;">Dr. Nuno Correia</h1>
                <p style="margin: 5px 0; color: #7f8c8d; font-size: 14px;">Medicina Integrativa & Terapias Naturais</p>
            </div>
            
            <div style="margin-bottom: 25px;">
                <h2 style="color: #e74c3c; border-left: 6px solid #e74c3c; padding-left: 15px; margin: 0;">
                    📋 Prescrição Terapêutica Integrada
                </h2>
                <div style="margin: 15px 0; padding: 10px; background: #ecf0f1; border-radius: 5px;">
                    <p><strong>Paciente:</strong> {nome_paciente}</p>
                    <p><strong>Data:</strong> {QDate.currentDate().toString('dd/MM/yyyy')}</p>
                    <p><strong>Protocolos Prescritos:</strong> {len(self.protocolos_selecionados)}</p>
                </div>
            </div>
            
            <div>
                {protocolos_html}
            </div>
            
            <div style="margin-top: 40px; border-top: 2px solid #bdc3c7; padding-top: 20px;">
                <p style="text-align: center; color: #7f8c8d; font-size: 12px;">
                    <strong>Dr. Nuno Correia</strong><br>
                    Documento gerado em {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm')}
                </p>
            </div>
        </div>
        """
        
        return html
    
    def criar_novo_template(self):
        """Abre diálogo para criar novo template"""
        # Por agora, mostrar mensagem simples
        BiodeskMessageBox.information(
            self, 
            "Novo Template", 
            "🚧 Funcionalidade em desenvolvimento!\n\nEm breve poderá criar templates personalizados."
        )
    
    def abrir_pdf_atual_externo(self):
        """Abre PDF atual no visualizador externo"""
        if not self.pdf_path_atual:
            BiodeskMessageBox.warning(self, "Aviso", "Nenhum PDF selecionado!")
            return
            
        # Simular abertura de PDF externo
        BiodeskMessageBox.information(
            self, 
            "PDF Externo", 
            f"🔍 Abrindo PDF no visualizador externo:\n{self.pdf_path_atual}"
        )
    
    def inicializar_templates_padrao(self):
        """Inicializa templates padrão no sistema"""
        # Cache de templates padrão
        if not self.cache.get('templates_inicializados'):
            # print("📋 Inicializando templates padrão...")
            
            # Simular carregamento de templates
            templates_count = sum(len(templates) for templates in [
                ['Alongamentos Cervicais', 'Exercícios Posturais', 'Fortalecimento Core'],
                ['Dieta Anti-inflamatória', 'Plano Detox 7 dias', 'Alimentação Alcalina'],
                ['Complexo Vitamínico B', 'Ómega 3 + Cúrcuma', 'Magnésio + Zinco'],
                ['Higiene do Sono', 'Gestão do Stress', 'Hidratação Adequada'],
                ['Guia Alimentação Saudável', 'Manual Exercícios Casa'],
                ['Protocolo Ansiedade', 'Tratamento Insónia', 'Dores Articulares']
            ])
            
            self.cache.set('templates_inicializados', True)
            self.cache.set('templates_count', templates_count)
            
            # print(f"✅ {templates_count} templates carregados no sistema")
    
    def _lighten_color(self, color_hex, percentage):
        """Clareia uma cor hexadecimal"""
        # Remover # se presente
        color_hex = color_hex.lstrip('#')
        
        # Converter para RGB
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        
        # Calcular nova cor
        factor = 1 + (percentage / 100)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def atualizar_dados_paciente(self, novos_dados: Dict[str, Any]):
        """Atualiza dados do paciente"""
        self.paciente_data.update(novos_dados)
        
        # Atualizar preview se há template selecionado
        if self.template_atual:
            self.selecionar_template(
                self.template_atual['nome'], 
                self.template_atual['categoria']
            )
    
    def obter_protocolos_selecionados(self) -> List[str]:
        """Retorna lista de protocolos selecionados"""
        return self.protocolos_selecionados.copy()
    
    def limpar_protocolos(self):
        """Limpa todos os protocolos selecionados"""
        self.protocolos_selecionados.clear()
        self.protocolos_lista.clear()
        self.btn_remover_protocolo.setEnabled(False)
