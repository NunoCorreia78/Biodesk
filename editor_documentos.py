"""
Editor Avançado de Documentos - Biodesk
Permite editar templates e criar documentos personalizados
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
# Lazy import do QWebEngineView para evitar janela que pisca
# from PyQt6.QtWebEngineWidgets import QWebEngineView
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import tempfile

# ✅ SISTEMA NOVO: BiodeskStyles v2.0 - Estilos centralizados
try:
    from biodesk_styles import BiodeskStyles, DialogStyles, ButtonType
    BIODESK_STYLES_AVAILABLE = True
    # print("✅ BiodeskStyles v2.0 carregado no editor_documentos.py")
except ImportError as e:
    BIODESK_STYLES_AVAILABLE = False
    print(f"⚠️ BiodeskStyles não disponível: {e}")
from biodesk_dialogs import BiodeskMessageBox
from PyQt6.QtWidgets import QMessageBox
import os


class EditorDocumentos(QMainWindow):
    def __init__(self, dados_paciente=None, parent=None, template_inicial=None):
        super().__init__(parent)
        self.dados_paciente = dados_paciente or {}
        self.template_atual = None
        self.categoria_atual = None
        self.template_inicial = template_inicial  # Template para carregar automaticamente
        self.setupUI()
        self.carregar_templates()
        
        # Carregar template inicial se fornecido
        if self.template_inicial:
            self.carregar_template_inicial()
        
    def setupUI(self):
        """Configurar interface do editor"""
        self.setWindowTitle("📝 Editor de Documentos - Biodesk")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # === PAINEL ESQUERDO - Seleção e Edição ===
        left_panel = QWidget()
        left_panel.setFixedWidth(500)
        left_layout = QVBoxLayout(left_panel)
        
        # Seleção de categoria
        categoria_frame = QGroupBox("📂 Categoria de Template")
        categoria_layout = QVBoxLayout(categoria_frame)
        
        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems([
            "orientacoes", "suplementos", "dietas", 
            "exercicios", "relatorios", "prescricoes"
        ])
        self.combo_categoria.currentTextChanged.connect(self.carregar_templates_categoria)
        categoria_layout.addWidget(self.combo_categoria)
        
        left_layout.addWidget(categoria_frame)
        
        # Seleção de template
        template_frame = QGroupBox("📄 Templates Disponíveis")
        template_layout = QVBoxLayout(template_frame)
        
        self.lista_templates = QListWidget()
        self.lista_templates.itemClicked.connect(self.carregar_template)
        template_layout.addWidget(self.lista_templates)
        
        left_layout.addWidget(template_frame)
        
        # Editor de texto
        editor_frame = QGroupBox("✏️ Editor de Conteúdo")
        editor_layout = QVBoxLayout(editor_frame)
        
        # Toolbar para formatação
        toolbar = QToolBar()
        
        # Ações de formatação
        bold_action = QAction("🔸 Negrito", self)
        bold_action.triggered.connect(self.toggle_bold)
        toolbar.addAction(bold_action)
        
        italic_action = QAction("📐 Itálico", self)
        italic_action.triggered.connect(self.toggle_italic)
        toolbar.addAction(italic_action)
        
        toolbar.addSeparator()
        
        vars_action = QAction("🔧 Inserir Variável", self)
        vars_action.triggered.connect(self.mostrar_variaveis)
        toolbar.addAction(vars_action)
        
        editor_layout.addWidget(toolbar)
        
        # Editor de texto rico
        self.editor_texto = QTextEdit()
        self.editor_texto.setMinimumHeight(300)
        self.editor_texto.textChanged.connect(self.atualizar_preview)
        editor_layout.addWidget(self.editor_texto)
        
        left_layout.addWidget(editor_frame)
        
        # Botões de ação
        botoes_frame = QGroupBox("🎯 Ações")
        botoes_layout = QHBoxLayout(botoes_frame)
        
        if BIODESK_STYLES_AVAILABLE:
            self.btn_preview = BiodeskStyles.create_button("👁️ Preview", ButtonType.NAVIGATION)
        else:
            self.btn_preview = QPushButton("👁️ Preview")
        self.btn_preview.clicked.connect(self.gerar_preview)
        botoes_layout.addWidget(self.btn_preview)
        
        if BIODESK_STYLES_AVAILABLE:
            self.btn_salvar = BiodeskStyles.create_button("💾 Salvar Template", ButtonType.SAVE)
        else:
            self.btn_salvar = QPushButton("💾 Salvar Template")
        self.btn_salvar.clicked.connect(self.salvar_template)
        botoes_layout.addWidget(self.btn_salvar)
        
        if BIODESK_STYLES_AVAILABLE:
            self.btn_gerar_pdf = BiodeskStyles.create_button("📄 Gerar PDF", ButtonType.TOOL)
        else:
            self.btn_gerar_pdf = QPushButton("📄 Gerar PDF")
        self.btn_gerar_pdf.clicked.connect(self.gerar_pdf)
        botoes_layout.addWidget(self.btn_gerar_pdf)
        
        left_layout.addWidget(botoes_frame)
        
        main_layout.addWidget(left_panel)
        
        # === PAINEL DIREITO - Preview ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_frame = QGroupBox("👁️ Preview do Documento")
        preview_layout = QVBoxLayout(preview_frame)
        
        # Área de preview usando QTextEdit para evitar janela que pisca
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                padding: 10px;
            }
        """)
        preview_layout.addWidget(self.preview_area)
        
        right_layout.addWidget(preview_frame)
        main_layout.addWidget(right_panel)
        
        # Aplicar estilo
        self.aplicar_estilo()
        
    def aplicar_estilo(self):
        """Aplicar estilo visual moderno"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #9C27B0;
                border: 2px solid #E1BEE7;
                border-radius: 8px;
                margin: 10px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
            QPushButton {
                background: linear-gradient(135deg, #9C27B0, #7B1FA2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #7B1FA2, #6A1B9A);
            }
            QListWidget {
                border: 2px solid #E1BEE7;
                border-radius: 6px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #E1BEE7;
                color: #9C27B0;
            }
            QTextEdit {
                border: 2px solid #E1BEE7;
                border-radius: 6px;
                background-color: white;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12px;
            }
            QComboBox {
                border: 2px solid #E1BEE7;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
            }
        """)
        
    def carregar_templates(self):
        """Carregar templates da categoria inicial"""
        self.carregar_templates_categoria("orientacoes")
        
    def carregar_templates_categoria(self, categoria):
        """Carregar templates de uma categoria específica"""
        self.categoria_atual = categoria
        self.lista_templates.clear()
        
        # 1. Carregar templates JSON
        templates_file = Path("templates") / f"{categoria}.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                
                for template in templates:
                    item = QListWidgetItem(f"📝 {template['nome']}")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'tipo': 'json',
                        'template': template,
                        'categoria': categoria
                    })
                    self.lista_templates.addItem(item)
            except Exception as e:
                print(f"Erro ao carregar templates JSON: {e}")
        
        # 2. Carregar PDFs
        categoria_dir = Path("templates") / categoria
        if categoria_dir.exists():
            for arquivo in categoria_dir.iterdir():
                if arquivo.suffix.lower() == '.pdf':
                    nome = arquivo.stem
                    item = QListWidgetItem(f"📄 {nome}")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'tipo': 'pdf',
                        'arquivo': str(arquivo),
                        'nome': nome,
                        'categoria': categoria
                    })
                    self.lista_templates.addItem(item)
        
        # 3. Carregar templates TXT
        if categoria_dir.exists():
            for arquivo in categoria_dir.iterdir():
                if arquivo.suffix.lower() == '.txt':
                    nome = arquivo.stem.replace('_', ' ').title()
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    item = QListWidgetItem(f"📝 {nome}")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'tipo': 'txt',
                        'arquivo': str(arquivo),
                        'nome': nome,
                        'conteudo': conteudo,
                        'categoria': categoria
                    })
                    self.lista_templates.addItem(item)
                    
    def carregar_template(self, item):
        """Carregar template selecionado no editor"""
        dados = item.data(Qt.ItemDataRole.UserRole)
        self.template_atual = dados
        
        if dados['tipo'] == 'json':
            # Template JSON tradicional
            if 'template' in dados and 'texto' in dados['template']:
                texto = dados['template']['texto']
            elif 'conteudo' in dados:
                texto = dados['conteudo']
            elif 'texto' in dados:
                texto = dados['texto']
            else:
                texto = "# Template JSON\n\nConteúdo não encontrado"
            self.editor_texto.setPlainText(texto)
            
        elif dados['tipo'] == 'txt':
            # Template de arquivo TXT
            self.editor_texto.setPlainText(dados['conteudo'])
            
        elif dados['tipo'] == 'pdf':
            # PDF - criar template editável baseado no PDF
            self.editor_texto.setPlainText(f"""
# Documento baseado em: {dados['nome']}

**Paciente:** {{nome_paciente}}
**Data:** {{data_consulta}}

---

[Edite aqui o conteúdo personalizado baseado no PDF original]

**Dr./Dra.:** {{nome_profissional}}
**Clínica:** {{nome_clinica}}
            """.strip())
        
        self.atualizar_preview()
        
    def mostrar_variaveis(self):
        """Mostrar diálogo com variáveis disponíveis"""
        # Organizar variáveis por categoria
        variaveis_por_categoria = {
            "👤 Dados do Paciente": [
                "{{nome_paciente}}", "{{idade}}", "{{data_nascimento}}",
                "{{telefone}}", "{{email}}", "{{peso}}", "{{altura}}", 
                "{{imc}}", "{{pressao_arterial}}"
            ],
            "📅 Data e Hora": [
                "{{data_hoje}}", "{{data_consulta}}", "{{data_completa}}", 
                "{{data_envio}}", "{{hora_atual}}", "{{hora_completa}}", 
                "{{hora_envio}}", "{{data_hora}}", "{{timestamp}}"
            ],
            "🏥 Informações da Clínica": [
                "{{nome_profissional}}", "{{especialidade}}", "{{nome_clinica}}",
                "{{endereco_clinica}}", "{{telefone_clinica}}", "{{email_clinica}}", 
                "{{website}}"
            ],
            "📅 Calendário": [
                "{{mes_atual}}", "{{ano_atual}}", "{{dia_semana}}", "{{saudacao}}"
            ]
        }
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🔧 Variáveis Disponíveis para Autopreenchimento")
        dialog.setFixedSize(600, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Informação sobre autopreenchimento
        info = QLabel("""
💡 <b>Sistema de Autopreenchimento Biodesk</b><br>
As variáveis são substituídas automaticamente na geração do documento.<br>
<b>Dica:</b> Clique duas vezes para inserir no template.
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Criar abas para cada categoria
        tabs = QTabWidget()
        
        for categoria, variaveis in variaveis_por_categoria.items():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            lista = QListWidget()
            for var in variaveis:
                item = QListWidgetItem(var)
                # Adicionar descrição como tooltip
                item.setToolTip(self.obter_descricao_variavel(var))
                lista.addItem(item)
            
            def criar_inserir_func(lista_widget):
                def inserir_variavel():
                    item = lista_widget.currentItem()
                    if item:
                        cursor = self.editor_texto.textCursor()
                        cursor.insertText(item.text())
                        dialog.accept()
                return inserir_variavel
            
            lista.itemDoubleClicked.connect(criar_inserir_func(lista))
            tab_layout.addWidget(lista)
            
            tabs.addTab(tab, categoria)
        
        layout.addWidget(tabs)
        
        # Botões
        botoes_layout = QHBoxLayout()
        
        if BIODESK_STYLES_AVAILABLE:
            btn_inserir = BiodeskStyles.create_button("✅ Inserir Selecionada", ButtonType.SAVE)
        else:
            btn_inserir = QPushButton("✅ Inserir Selecionada")
        btn_inserir.clicked.connect(lambda: self.inserir_variavel_selecionada(tabs, dialog))
        botoes_layout.addWidget(btn_inserir)
        
        if BIODESK_STYLES_AVAILABLE:
            btn_fechar = BiodeskStyles.create_button("❌ Fechar", ButtonType.DEFAULT)
        else:
            btn_fechar = QPushButton("❌ Fechar")
        btn_fechar.clicked.connect(dialog.reject)
        botoes_layout.addWidget(btn_fechar)
        
        layout.addLayout(botoes_layout)
        
        dialog.exec()
    
    def obter_descricao_variavel(self, variavel):
        """Obter descrição de uma variável"""
        descricoes = {
            "{{nome_paciente}}": "Nome completo do paciente",
            "{{idade}}": "Idade do paciente",
            "{{data_hoje}}": "Data atual (DD/MM/AAAA)",
            "{{data_consulta}}": "Data da consulta (DD/MM/AAAA)",
            "{{hora_atual}}": "Hora atual (HH:MM)",
            "{{data_hora}}": "Data e hora completas",
            "{{nome_profissional}}": "Nome do profissional",
            "{{especialidade}}": "Especialidade médica",
            "{{saudacao}}": "Saudação automática (Bom dia/Boa tarde/Boa noite)",
            "{{mes_atual}}": "Mês atual por extenso",
            "{{ano_atual}}": "Ano atual",
            "{{dia_semana}}": "Dia da semana"
        }
        return descricoes.get(variavel, "Variável de autopreenchimento")
    
    def inserir_variavel_selecionada(self, tabs, dialog):
        """Inserir variável selecionada na aba atual"""
        tab_atual = tabs.currentWidget()
        if tab_atual:
            lista = tab_atual.findChild(QListWidget)
            if lista and lista.currentItem():
                cursor = self.editor_texto.textCursor()
                cursor.insertText(lista.currentItem().text())
                dialog.accept()
        
    def toggle_bold(self):
        """Alternar negrito"""
        cursor = self.editor_texto.textCursor()
        if cursor.hasSelection():
            format = cursor.charFormat()
            if format.fontWeight() == QFont.Weight.Bold:
                format.setFontWeight(QFont.Weight.Normal)
            else:
                format.setFontWeight(QFont.Weight.Bold)
            cursor.mergeCharFormat(format)
            
    def toggle_italic(self):
        """Alternar itálico"""
        cursor = self.editor_texto.textCursor()
        if cursor.hasSelection():
            format = cursor.charFormat()
            format.setFontItalic(not format.fontItalic())
            cursor.mergeCharFormat(format)
            
    def substituir_variaveis(self, texto):
        """Substituir variáveis do template com dados reais"""
        from datetime import datetime
        
        # Variáveis automáticas de data e hora
        agora = datetime.now()
        
        # Mapeamento básico de variáveis de paciente
        substituicoes_paciente = {}
        if self.dados_paciente:
            substituicoes_paciente = {
                '{{nome_paciente}}': self.dados_paciente.get('nome', '[Nome do Paciente]'),
                '{{idade}}': str(self.dados_paciente.get('idade', '[Idade]')),
                '{{data_nascimento}}': self.dados_paciente.get('data_nascimento', '[Data de Nascimento]'),
                '{{telefone}}': self.dados_paciente.get('telefone', '[Telefone]'),
                '{{email}}': self.dados_paciente.get('email', '[Email]'),
                '{{peso}}': self.dados_paciente.get('peso', '[Peso]'),
                '{{altura}}': self.dados_paciente.get('altura', '[Altura]'),
                '{{imc}}': self.dados_paciente.get('imc', '[IMC]'),
                '{{pressao_arterial}}': self.dados_paciente.get('pressao_arterial', '[Pressão Arterial]')
            }
        
        # Variáveis automáticas de data/hora - SEMPRE DISPONÍVEIS
        substituicoes_automaticas = {
            # Data de hoje em vários formatos
            '{{data_hoje}}': agora.strftime('%d/%m/%Y'),
            '{{data_consulta}}': agora.strftime('%d/%m/%Y'),
            '{{data_completa}}': agora.strftime('%d de %B de %Y'),
            '{{data_envio}}': agora.strftime('%d/%m/%Y'),
            
            # Hora atual em vários formatos
            '{{hora_atual}}': agora.strftime('%H:%M'),
            '{{hora_completa}}': agora.strftime('%H:%M:%S'),
            '{{hora_envio}}': agora.strftime('%H:%M'),
            
            # Data e hora combinadas
            '{{data_hora}}': agora.strftime('%d/%m/%Y às %H:%M'),
            '{{timestamp}}': agora.strftime('%d/%m/%Y %H:%M:%S'),
            
            # Informações do sistema/clínica
            '{{nome_profissional}}': 'Dr. Nuno Correia',
            '{{especialidade}}': 'Medicina Integrativa',
            '{{nome_clinica}}': 'Biodesk - Medicina Integrativa',
            '{{endereco_clinica}}': '[Endereço da Clínica]',
            '{{telefone_clinica}}': '[Telefone da Clínica]',
            '{{email_clinica}}': 'contato@biodesk.com',
            '{{website}}': 'www.biodesk.com',
            
            # Meses em português
            '{{mes_atual}}': agora.strftime('%B'),
            '{{ano_atual}}': agora.strftime('%Y'),
            '{{dia_semana}}': agora.strftime('%A'),
            
            # Saudações automáticas baseadas na hora
            '{{saudacao}}': self.gerar_saudacao_automatica(agora),
        }
        
        # Aplicar todas as substituições
        all_substituicoes = {**substituicoes_automaticas, **substituicoes_paciente}
        
        for var, valor in all_substituicoes.items():
            texto = texto.replace(var, str(valor))
            
        return texto
    
    def gerar_saudacao_automatica(self, agora):
        """Gera saudação automática baseada na hora do dia"""
        hora = agora.hour
        
        if 5 <= hora < 12:
            return "Bom dia"
        elif 12 <= hora < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
        
    def atualizar_preview(self):
        """Atualizar preview do documento"""
        self.gerar_preview()
        
    def gerar_preview(self):
        """Gerar preview HTML do documento"""
        texto = self.editor_texto.toPlainText()
        texto_processado = self.substituir_variaveis(texto)
        
        # Converter markdown simples para HTML
        html = self.markdown_para_html(texto_processado)
        
        # Template HTML com estilo profissional
        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: white;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #9C27B0;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    color: #9C27B0;
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .content {{
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 40px;
                    text-align: center;
                    border-top: 1px solid #ddd;
                    padding-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
                h1, h2, h3 {{
                    color: #9C27B0;
                }}
                strong {{
                    color: #7B1FA2;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">🌿 BIODESK - Clínica de Iridologia</div>
                <div>Análise Holística e Medicina Natural</div>
            </div>
            <div class="content">
                {html}
            </div>
            <div class="footer">
                <p>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                <p>© Biodesk - Sistema de Gestão de Iridologia</p>
            </div>
        </body>
        </html>
        """
        
        # Converter HTML para texto simples para QTextEdit
        import re
        # Remover tags HTML e manter apenas o texto
        texto_limpo = re.sub('<[^<]+?>', '', html_completo)
        # Limpar espaços extras
        texto_limpo = re.sub(r'\n\s*\n', '\n\n', texto_limpo)
        texto_limpo = texto_limpo.strip()
        
        self.preview_area.setPlainText(texto_limpo)
        
    def markdown_para_html(self, texto):
        """Converter markdown simples para HTML"""
        linhas = texto.split('\n')
        html_linhas = []
        
        for linha in linhas:
            linha = linha.strip()
            
            if linha.startswith('# '):
                html_linhas.append(f'<h1>{linha[2:]}</h1>')
            elif linha.startswith('## '):
                html_linhas.append(f'<h2>{linha[3:]}</h2>')
            elif linha.startswith('### '):
                html_linhas.append(f'<h3>{linha[4:]}</h3>')
            elif linha.startswith('**') and linha.endswith('**'):
                html_linhas.append(f'<p><strong>{linha[2:-2]}</strong></p>')
            elif linha.startswith('---'):
                html_linhas.append('<hr>')
            elif linha:
                # Processar formatação inline
                linha = linha.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                html_linhas.append(f'<p>{linha}</p>')
            else:
                html_linhas.append('<br>')
                
        return '\n'.join(html_linhas)
        
    def salvar_template(self):
        """Salvar template editado"""
        if not self.template_atual:
            BiodeskMessageBox.warning(self, "Aviso", "Nenhum template selecionado.")
            return
            
        texto = self.editor_texto.toPlainText()
        
        # Perguntar nome do template
        nome, ok = BiodeskMessageBox.getText(self, "💾 Salvar Template", 
                                       "Nome do template:")
        if not ok or not nome:
            return
            
        # Salvar como arquivo TXT na categoria atual
        categoria_dir = Path("templates") / self.categoria_atual
        categoria_dir.mkdir(exist_ok=True)
        
        arquivo = categoria_dir / f"{nome.replace(' ', '_').lower()}.txt"
        
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(texto)
            
            BiodeskMessageBox.information(self, "✅ Sucesso", 
                                  f"Template salvo como:\n{arquivo}")
            
            # Recarregar lista
            self.carregar_templates_categoria(self.categoria_atual)
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "❌ Erro", f"Erro ao salvar: {e}")
            
    def gerar_pdf(self):
        """Gerar PDF do documento"""
        texto = self.editor_texto.toPlainText()
        texto_processado = self.substituir_variaveis(texto)
        
        # Escolher local para salvar
        arquivo, _ = QFileDialog.getSaveFileName(
            self, "💾 Salvar PDF", 
            f"documento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not arquivo:
            return
            
        try:
            self.criar_pdf_profissional(texto_processado, arquivo)
            BiodeskMessageBox.information(self, "✅ Sucesso", 
                                  f"PDF gerado com sucesso:\n{arquivo}")
            
            # Abrir PDF
            resposta = BiodeskMessageBox.question(self, "📄 Abrir PDF", 
                                          "Deseja abrir o PDF gerado?")
            if resposta:  # BiodeskMessageBox.question retorna True/False
                os.startfile(arquivo)
                
        except Exception as e:
            BiodeskMessageBox.critical(self, "❌ Erro", f"Erro ao gerar PDF: {e}")
            
    def criar_pdf_profissional(self, texto, arquivo):
        """Criar PDF com layout profissional"""
        doc = SimpleDocTemplate(arquivo, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo customizado para título
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#9C27B0',
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # Estilo para texto normal
        texto_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            textColor='#333333',
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Construir documento
        elementos = []
        
        # Cabeçalho
        elementos.append(Paragraph("🌿 BIODESK", titulo_style))
        elementos.append(Paragraph("Clínica de Iridologia e Medicina Natural", styles['Normal']))
        elementos.append(Spacer(1, 20))
        
        # Linha separadora
        elementos.append(Paragraph("_" * 80, styles['Normal']))
        elementos.append(Spacer(1, 20))
        
        # Conteúdo
        linhas = texto.split('\n')
        for linha in linhas:
            linha = linha.strip()
            if linha:
                if linha.startswith('#'):
                    # Título
                    elementos.append(Paragraph(linha.replace('#', '').strip(), titulo_style))
                else:
                    # Texto normal
                    elementos.append(Paragraph(linha, texto_style))
            else:
                elementos.append(Spacer(1, 12))
        
        # Rodapé
        elementos.append(Spacer(1, 30))
        elementos.append(Paragraph("_" * 80, styles['Normal']))
        elementos.append(Spacer(1, 10))
        
        rodape_texto = f"""
        <para align="center">
        Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>
        © Biodesk - Sistema de Gestão de Iridologia
        </para>
        """
        elementos.append(Paragraph(rodape_texto, styles['Normal']))
        
        # Gerar PDF
        doc.build(elementos)

    def carregar_template_inicial(self):
        """Carrega automaticamente o template inicial fornecido"""
        try:
            if not self.template_inicial:
                print("⚠️ [EDITOR] Nenhum template inicial fornecido")
                return
                
            template = self.template_inicial
            print(f"🔄 [EDITOR] Carregando template inicial: {template.get('nome', 'Sem nome')}")
            print(f"🔍 [EDITOR] Dados do template: {template}")
            
            # Determinar tipo do template e carregar
            if template.get('tipo') == 'TXT':
                conteudo = ""
                
                # Template TXT com arquivo
                if 'caminho' in template:
                    print(f"📁 [EDITOR] Carregando de arquivo: {template['caminho']}")
                    with open(template['caminho'], 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                # Template TXT com conteúdo direto (JSON)
                elif 'conteudo' in template:
                    print("📝 [EDITOR] Carregando conteúdo direto")
                    conteudo = template['conteudo']
                elif 'texto' in template:  # Compatibilidade com templates antigos
                    print("📝 [EDITOR] Carregando campo 'texto'")
                    conteudo = template['texto']
                else:
                    print("⚠️ [EDITOR] Template TXT sem conteúdo ou caminho")
                    print(f"🔍 [EDITOR] Chaves disponíveis: {list(template.keys())}")
                    return
                    
                # Carregar no editor
                self.template_atual = template
                self.editor_texto.setPlainText(conteudo)
                
                # Atualizar categoria se possível
                if 'categoria' in template:
                    categoria = template['categoria']
                    print(f"📂 [EDITOR] Definindo categoria: {categoria}")
                    # Tentar selecionar categoria no combo
                    index = self.categoria_combo.findText(categoria.title())
                    if index >= 0:
                        self.categoria_combo.setCurrentIndex(index)
                        self.categoria_atual = categoria
                        print(f"✅ [EDITOR] Categoria selecionada: {categoria}")
                    else:
                        print(f"⚠️ [EDITOR] Categoria '{categoria}' não encontrada no combo")
                
                # Atualizar preview
                self.atualizar_preview()
                
                print(f"✅ [EDITOR] Template '{template.get('nome')}' carregado com sucesso")
                
            elif template.get('tipo') == 'PDF':
                print("ℹ️ [EDITOR] Templates PDF não são editáveis no editor avançado")
                BiodeskMessageBox.information(
                    self, 
                    "Informação", 
                    f"O template '{template.get('nome')}' é um PDF e não pode ser editado.\n\n"
                    "Use os templates TXT para edição ou crie um novo template."
                )
            else:
                print(f"⚠️ [EDITOR] Tipo de template não suportado: {template.get('tipo', 'Desconhecido')}")
                print(f"🔍 [EDITOR] Template completo: {template}")
                
        except Exception as e:
            print(f"❌ [EDITOR] Erro ao carregar template inicial: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Função principal para teste - apenas para desenvolvimento"""
    print("⚠️  Este módulo deve ser usado através do main_window.py")
    print("🚀 Execute: python main_window.py")
    return


# Este módulo é importado pelo ficha_paciente.py
if __name__ == "__main__":
    main()
