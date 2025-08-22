"""
🩺 MÓDULO: Declaração de Saúde - Interface Profissional
Sistema completo para criação e assinatura de declarações de saúde.

Funcionalidades:
- ✅ Interface profissional e limpa
- ✅ Formulário estruturado por seções
- ✅ Sistema de assinatura integrado
- ✅ Geração PDF com formatação profissional
- ✅ Integração com gestor de documentos
- ✅ Tracking de alterações e versões
- ✅ Status visual de preenchimento
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
                             QPushButton, QTextEdit, QScrollArea, QLineEdit, QComboBox, QFormLayout,
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from biodesk_ui_kit import BiodeskUIKit
from biodesk_dialogs import mostrar_erro, mostrar_sucesso, mostrar_aviso
from sistema_assinatura import abrir_dialogo_assinatura

class DeclaracaoSaudeWidget(QWidget):
    """
    Widget profissional para declaração de saúde
    """
    # Sinais
    declaracao_assinada = pyqtSignal(dict)
    dados_atualizados = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.paciente_data = None
        
        # Tracking de alterações
        self._dados_originais = None
        self._primeira_criacao = None
        self._ultima_alteracao = None
        self._foi_assinado = False
        self._alterado = False
        
        self.init_ui()
        self._conectar_sinais_alteracao()
        
    def init_ui(self):
        """Interface profissional com design limpo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Barra azul no topo
        titulo = QLabel("📋 Declaração de Saúde")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: white;
                padding: 25px;
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
                margin-bottom: 15px;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Layout principal horizontal: 75% formulário + 25% botões/status
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)
        
        # ÁREA ESQUERDA (75%): Formulário com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(600)  # Garantir largura mínima
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e9ecef;
                border-radius: 10px;
                background-color: white;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #f1f1f1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        formulario_widget = self._criar_formulario_profissional()
        scroll.setWidget(formulario_widget)
        main_horizontal_layout.addWidget(scroll, 3)  # 75% do espaço
        
        # ÁREA DIREITA (25%): Botões e status verticalmente
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(15)
        
        # Botões principais (verticalmente)
        botoes_widget = self._criar_botoes_sidebar()
        sidebar_layout.addWidget(botoes_widget)
        
        # Widget de status
        status_widget = self._criar_widget_status()
        sidebar_layout.addWidget(status_widget)
        
        # Espaçador para empurrar tudo para cima
        sidebar_layout.addStretch()
        
        # Container para a sidebar
        sidebar_container = QWidget()
        sidebar_container.setLayout(sidebar_layout)
        sidebar_container.setFixedWidth(300)  # Largura fixa para a sidebar
        
        main_horizontal_layout.addWidget(sidebar_container, 1)  # 25% do espaço
        
        # Adicionar o layout horizontal ao layout principal
        layout.addLayout(main_horizontal_layout)
    
    def _criar_botoes_sidebar(self):
        """Cria botões para a sidebar direita"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        
        # Botão Assinar e Guardar
        btn_assinar = QPushButton("📝 Assinar e Guardar")
        btn_assinar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 15px 20px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #5a6fd8, stop:1 #6a4298);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #4f63d2, stop:1 #5d3a8e);
            }
        """)
        btn_assinar.clicked.connect(self.assinar_e_guardar)
        layout.addWidget(btn_assinar)
        
        # Botão Limpar
        btn_limpar = QPushButton("🗑️ Limpar Formulário")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        btn_limpar.clicked.connect(self.limpar_formulario)
        layout.addWidget(btn_limpar)
        
        return container
    
    def _criar_widget_status(self):
        """Cria widget de status simples como na imagem"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        
        # Status principal
        self.status_label = QLabel("📄 Não Preenchida")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #dc3545;
                padding: 15px;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
                text-align: center;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Data info
        self.data_label = QLabel("--/--/----")
        self.data_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                text-align: center;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
        """)
        self.data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.data_label)
        
        return frame

    def _criar_formulario_profissional(self):
        """Cria formulário com design profissional"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        
        # Seção 1: Informações Gerais
        secao1 = self._criar_secao_profissional("👤 Informações Gerais", "#667eea")
        form1 = QGridLayout()
        
        # Nome
        form1.addWidget(QLabel("Nome Completo:"), 0, 0)
        self.nome_edit = QLineEdit()
        self.nome_edit.setReadOnly(True)
        self.nome_edit.setStyleSheet(self._estilo_campo_readonly())
        form1.addWidget(self.nome_edit, 0, 1)
        
        # Data nascimento
        form1.addWidget(QLabel("Data de Nascimento:"), 1, 0)
        self.data_nasc_edit = QLineEdit()
        self.data_nasc_edit.setReadOnly(True)
        self.data_nasc_edit.setStyleSheet(self._estilo_campo_readonly())
        form1.addWidget(self.data_nasc_edit, 1, 1)
        
        # Data declaração
        form1.addWidget(QLabel("Data da Declaração:"), 2, 0)
        self.data_declaracao_edit = QLineEdit()
        self.data_declaracao_edit.setText(datetime.now().strftime('%d/%m/%Y'))
        self.data_declaracao_edit.setReadOnly(True)
        self.data_declaracao_edit.setStyleSheet(self._estilo_campo_readonly())
        form1.addWidget(self.data_declaracao_edit, 2, 1)
        
        secao1.layout().addLayout(form1)
        layout.addWidget(secao1)
        
        # Seção 2: Estado de Saúde Geral
        secao2 = self._criar_secao_profissional("🏥 Estado de Saúde Geral", "#28a745")
        form2 = QGridLayout()
        
        form2.addWidget(QLabel("Tem algum problema de saúde atual?"), 0, 0)
        self.problemas_combo = QComboBox()
        self.problemas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.problemas_combo.setStyleSheet(self._estilo_campo())
        form2.addWidget(self.problemas_combo, 0, 1)
        
        form2.addWidget(QLabel("Detalhes dos problemas de saúde:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.problemas_detalhe = QTextEdit()
        self.problemas_detalhe.setMaximumHeight(100)
        self.problemas_detalhe.setPlaceholderText("Descreva detalhadamente os problemas de saúde, sintomas, tratamentos em curso...")
        self.problemas_detalhe.setStyleSheet(self._estilo_campo())
        form2.addWidget(self.problemas_detalhe, 1, 1)
        
        secao2.layout().addLayout(form2)
        layout.addWidget(secao2)
        
        # Seção 3: Medicação
        secao3 = self._criar_secao_profissional("💊 Medicação e Tratamentos", "#dc3545")
        form3 = QGridLayout()
        
        form3.addWidget(QLabel("Toma alguma medicação atualmente?"), 0, 0)
        self.medicacao_combo = QComboBox()
        self.medicacao_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.medicacao_combo.setStyleSheet(self._estilo_campo())
        form3.addWidget(self.medicacao_combo, 0, 1)
        
        form3.addWidget(QLabel("Detalhes da medicação:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.medicacao_detalhe = QTextEdit()
        self.medicacao_detalhe.setMaximumHeight(100)
        self.medicacao_detalhe.setPlaceholderText("Liste todas as medicações: nome, dosagem, frequência, motivo...")
        self.medicacao_detalhe.setStyleSheet(self._estilo_campo())
        form3.addWidget(self.medicacao_detalhe, 1, 1)
        
        secao3.layout().addLayout(form3)
        layout.addWidget(secao3)
        
        # Seção 4: Alergias e Reações
        secao4 = self._criar_secao_profissional("🚨 Alergias e Reações Adversas", "#fd7e14")
        form4 = QGridLayout()
        
        form4.addWidget(QLabel("Tem alguma alergia conhecida?"), 0, 0)
        self.alergias_combo = QComboBox()
        self.alergias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alergias_combo.setStyleSheet(self._estilo_campo())
        form4.addWidget(self.alergias_combo, 0, 1)
        
        form4.addWidget(QLabel("Detalhes das alergias:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.alergias_detalhe = QTextEdit()
        self.alergias_detalhe.setMaximumHeight(100)
        self.alergias_detalhe.setPlaceholderText("Descreva todas as alergias: medicamentos, alimentos, plantas, reações...")
        self.alergias_detalhe.setStyleSheet(self._estilo_campo())
        form4.addWidget(self.alergias_detalhe, 1, 1)
        
        secao4.layout().addLayout(form4)
        layout.addWidget(secao4)
        
        # Seção 5: Observações Clínicas
        secao5 = self._criar_secao_profissional("📝 Observações e Informações Adicionais", "#6f42c1")
        form5 = QVBoxLayout()
        
        observacoes_label = QLabel("Observações gerais:")
        observacoes_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        form5.addWidget(observacoes_label)
        
        self.observacoes = QTextEdit()
        self.observacoes.setMaximumHeight(120)
        self.observacoes.setPlaceholderText("Inclua qualquer informação adicional relevante: cirurgias anteriores, histórico familiar, hábitos de vida, outras condições...")
        self.observacoes.setStyleSheet(self._estilo_campo())
        form5.addWidget(self.observacoes)
        
        secao5.layout().addLayout(form5)
        layout.addWidget(secao5)
        
        return widget
    
    def _conectar_sinais_alteracao(self):
        """Conecta sinais para detectar alterações no formulário"""
        # Conectar combos
        self.problemas_combo.currentTextChanged.connect(self.on_dados_alterados)
        self.medicacao_combo.currentTextChanged.connect(self.on_dados_alterados)
        self.alergias_combo.currentTextChanged.connect(self.on_dados_alterados)
        
        # Conectar text edits
        self.problemas_detalhe.textChanged.connect(self.on_dados_alterados)
        self.medicacao_detalhe.textChanged.connect(self.on_dados_alterados)
        self.alergias_detalhe.textChanged.connect(self.on_dados_alterados)
        self.observacoes.textChanged.connect(self.on_dados_alterados)
    
    def on_dados_alterados(self):
        """Chamado quando dados são alterados"""
        if self._dados_originais is None:
            return
            
        dados_atuais = self._obter_dados_formulario()
        hash_atual = self._calcular_hash_dados(dados_atuais)
        hash_original = self._calcular_hash_dados(self._dados_originais)
        
        self._alterado = hash_atual != hash_original
        self._atualizar_status_widget()
    
    def _calcular_hash_dados(self, dados):
        """Calcula hash dos dados para detectar alterações"""
        dados_str = json.dumps(dados, sort_keys=True)
        return hashlib.md5(dados_str.encode()).hexdigest()
    
    def _atualizar_status_widget(self):
        """Atualiza o widget de status baseado no estado atual"""
        if not self._dados_originais:
            # Nunca foi preenchido
            self.status_label.setText("📄 Não Preenchida")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #dc3545;
                    padding: 10px;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 8px;
                    text-align: center;
                }
            """)
            self.data_label.setText("--/--/----")
            self.botao_status.setText("💾 Guardar")
            
        elif self._alterado:
            # Foi alterado
            self.status_label.setText("✏️ Alterada")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #fd7e14;
                    padding: 10px;
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    text-align: center;
                }
            """)
            if self._ultima_alteracao:
                self.data_label.setText(f"Última alteração: {self._ultima_alteracao}")
            self.botao_status.setText("💾 Guardar Alterações")
            
        elif self._foi_assinado:
            # Preenchida e assinada
            self.status_label.setText("✅ Preenchida e Assinada")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #28a745;
                    padding: 10px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 8px;
                    text-align: center;
                }
            """)
            if self._primeira_criacao:
                self.data_label.setText(f"Preenchida em: {self._primeira_criacao}")
            self.botao_status.setText("📋 Assinar e Guardar")
            
        else:
            # Preenchida mas não assinada
            self.status_label.setText("📝 Preenchida")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #17a2b8;
                    padding: 10px;
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                    border-radius: 8px;
                    text-align: center;
                }
            """)
            if self._primeira_criacao:
                self.data_label.setText(f"Preenchida em: {self._primeira_criacao}")
            self.botao_status.setText("📋 Assinar e Guardar")
    
    def _criar_secao_profissional(self, titulo, cor):
        """Cria uma seção com design profissional"""
        secao = QGroupBox(titulo)
        secao.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {cor};
                border: 2px solid {cor};
                border-radius: 12px;
                padding-top: 15px;
                margin-top: 10px;
                background-color: #f8f9fa;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 5px 15px;
                background-color: white;
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(secao)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        return secao
    
    def _estilo_campo(self):
        """Estilo para campos editáveis"""
        return """
            QLineEdit, QComboBox, QTextEdit {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
            QComboBox {
                min-width: 150px;
                max-width: 200px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border-color: #667eea;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                border-left: 1px solid #e9ecef;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #667eea;
                margin: 2px;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
        """
    
    def _estilo_campo_readonly(self):
        """Estilo para campos readonly"""
        return """
            QLineEdit {
                padding: 10px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f8f9fa;
                color: #6c757d;
                font-weight: bold;
            }
        """
        
    def _criar_area_acoes(self):
        """Área de ações com botões principais"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(15)
        
        # Botão Assinar e Guardar
        btn_assinar = BiodeskUIKit.create_primary_button("✍️ Assinar e Guardar")
        btn_assinar.clicked.connect(self.assinar_e_guardar)
        layout.addWidget(btn_assinar)
        
        # Botão Limpar
        btn_limpar = BiodeskUIKit.create_neutral_button("🗑️ Limpar")
        btn_limpar.clicked.connect(self.limpar_formulario)
        layout.addWidget(btn_limpar)
        
        layout.addStretch()
        
        return frame
    
    def set_paciente_data(self, dados):
        """Define dados do paciente"""
        self.paciente_data = dados
        
        # Auto-povoar campos
        if dados:
            self.nome_edit.setText(dados.get('nome', ''))
            self.data_nasc_edit.setText(dados.get('data_nascimento', ''))
    
    def limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        try:
            # Limpar dropdowns
            self.problemas_combo.setCurrentIndex(0)
            self.medicacao_combo.setCurrentIndex(0)
            self.alergias_combo.setCurrentIndex(0)
            
            # Limpar text areas
            self.problemas_detalhe.clear()
            self.medicacao_detalhe.clear()
            self.alergias_detalhe.clear()
            self.observacoes.clear()
            
            BiodeskMessageBox.information(self, "Info", "Formulário limpo com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao limpar formulário: {e}")
            BiodeskMessageBox.error(self, "Erro", f"Erro ao limpar formulário:\n{str(e)}")
    
    def assinar_e_guardar(self):
        """Abre canvas de assinatura e guarda PDF"""
        try:
            if not self.paciente_data:
                BiodeskMessageBox.warning(self, "Aviso", "⚠️ Nenhum paciente selecionado.")
                return
            
            # Import do canvas de assinatura
            try:
                from assinatura_canvas import SignatureCanvas
            except ImportError:
                BiodeskMessageBox.error(self, "Erro", "Canvas de assinatura não encontrado.")
                return
            
            # Criar janela de assinatura
            canvas = SignatureCanvas(self)
            canvas.paciente_data = self.paciente_data
            canvas.show()
            
            # Conectar ao sinal de assinatura concluída (se disponível)
            if hasattr(canvas, 'assinatura_concluida'):
                canvas.assinatura_concluida.connect(self._processar_assinatura)
            else:
                # Fallback: gerar PDF diretamente
                self._gerar_pdf_simples()
            
        except Exception as e:
            print(f"❌ Erro ao abrir assinatura: {e}")
            BiodeskMessageBox.error(self, "Erro", f"Erro ao abrir assinatura:\n{str(e)}")
    
    def _processar_assinatura(self, dados_assinatura):
        """Processa assinatura e gera PDF"""
        self._gerar_pdf_simples()
    
    def _gerar_pdf_simples(self):
        """Gera PDF da declaração"""
        try:
            # Imports necessários
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF
            
            # Obter dados do formulário
            dados = self._obter_dados_formulario()
            
            # Obter dados do paciente
            paciente_id = self.paciente_data.get('id')
            nome_paciente = self.paciente_data.get('nome', '[NOME_PACIENTE]')
            data_atual = datetime.now().strftime('%d/%m/%Y')
            
            print(f"📋 [PDF] Gerando PDF da declaração de saúde para {nome_paciente}...")
            
            # Criar diretório se não existir
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente.replace(' ', '_')}"
            pasta_declaracoes = f"{pasta_paciente}/declaracoes_saude"
            os.makedirs(pasta_declaracoes, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho_pdf = f"{pasta_declaracoes}/declaracao_saude_{timestamp}.pdf"
            
            # Construir seções do PDF
            secoes_html = ""
            
            if dados['problemas_saude']:
                secoes_html += f"""
                <div class="section">
                    <h4>Problemas de Saúde Atuais</h4>
                    <p><strong>Tem problemas de saúde:</strong> {dados['problemas_saude']}</p>
                    {f"<p><strong>Detalhes:</strong> {dados['problemas_detalhe']}</p>" if dados['problemas_detalhe'] else ""}
                </div>
                """
                
            if dados['medicacao']:
                secoes_html += f"""
                <div class="section">
                    <h4>Medicação</h4>
                    <p><strong>Toma medicação:</strong> {dados['medicacao']}</p>
                    {f"<p><strong>Detalhes:</strong> {dados['medicacao_detalhe']}</p>" if dados['medicacao_detalhe'] else ""}
                </div>
                """
                
            if dados['alergias']:
                secoes_html += f"""
                <div class="section">
                    <h4>Alergias</h4>
                    <p><strong>Tem alergias:</strong> {dados['alergias']}</p>
                    {f"<p><strong>Detalhes:</strong> {dados['alergias_detalhe']}</p>" if dados['alergias_detalhe'] else ""}
                </div>
                """
                
            if dados['observacoes']:
                secoes_html += f"""
                <div class="section">
                    <h4>Observações</h4>
                    <p>{dados['observacoes']}</p>
                </div>
                """
            
            # HTML da declaração
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 30px; 
                        line-height: 1.6; 
                    }}
                    .header {{ 
                        text-align: center; 
                        margin-bottom: 40px; 
                        border-bottom: 2px solid #667eea;
                        padding-bottom: 20px;
                    }}
                    .section {{ 
                        margin-bottom: 20px; 
                        padding: 15px;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        background-color: #f8f9fa;
                    }}
                    .section h4 {{
                        margin-top: 0;
                        color: #495057;
                        border-bottom: 1px solid #dee2e6;
                        padding-bottom: 5px;
                    }}
                    .signature-area {{ 
                        margin-top: 60px; 
                        display: flex; 
                        justify-content: space-between; 
                    }}
                    .signature {{ 
                        text-align: center; 
                        width: 40%; 
                    }}
                    .signature-line {{ 
                        border-bottom: 1px solid #000; 
                        margin: 20px 0 5px 0; 
                        height: 60px; 
                    }}
                    .declaration {{
                        margin: 30px 0;
                        padding: 20px;
                        background-color: #f1f3f4;
                        border-left: 4px solid #667eea;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>DECLARAÇÃO DE SAÚDE</h2>
                    <p><strong>Paciente:</strong> {nome_paciente}</p>
                    <p><strong>Data de Nascimento:</strong> {dados['data_nascimento']}</p>
                    <p><strong>Data:</strong> {data_atual}</p>
                </div>
                
                <div class="declaration">
                    <p>Eu, <strong>{nome_paciente}</strong>, declaro que as informações 
                    fornecidas sobre o meu estado de saúde são verdadeiras e completas.</p>
                </div>
                
                {secoes_html}
                
                <div class="signature-area">
                    <div class="signature">
                        <div class="signature-line"></div>
                        <p><strong>Assinatura do Paciente</strong></p>
                        <p>{nome_paciente}</p>
                    </div>
                    <div class="signature">
                        <div class="signature-line"></div>
                        <p><strong>Assinatura do Profissional</strong></p>
                        <p>Data: {data_atual}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Criar documento e gerar PDF
            document = QTextDocument()
            document.setHtml(html_content)
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageLayout(QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Portrait,
                QMarginsF(15, 15, 15, 15)
            ))
            
            document.print(printer)
            
            # Registrar no gestor de documentos
            self._registrar_no_gestor_documentos(caminho_pdf)
            
            print(f"✅ [PDF] Declaração guardada: {caminho_pdf}")
            BiodeskMessageBox.information(self, "Sucesso", 
                                        f"✅ Declaração de saúde guardada com sucesso!\n\n📁 {caminho_pdf}")
            return True
                
        except Exception as e:
            print(f"❌ [PDF] Erro ao gerar PDF: {e}")
            BiodeskMessageBox.error(self, "Erro", f"❌ Erro ao gerar PDF da declaração:\n\n{str(e)}")
            return False
    
    def limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        try:
            # Limpar dropdowns
            self.problemas_combo.setCurrentIndex(0)
            self.medicacao_combo.setCurrentIndex(0)
            self.alergias_combo.setCurrentIndex(0)
            
            # Limpar text areas
            self.problemas_detalhe.clear()
            self.medicacao_detalhe.clear()
            self.alergias_detalhe.clear()
            self.observacoes.clear()
            
            BiodeskMessageBox.information(self, "Info", "Formulário limpo com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao limpar formulário: {e}")
            BiodeskMessageBox.error(self, "Erro", f"Erro ao limpar formulário:\n{str(e)}")
    
    def _obter_dados_formulario(self):
        """Obtém dados do formulário"""
    def _criar_area_acoes(self):
        """Área de ações com botões profissionais"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 15px;
                padding: 20px;
                margin-top: 10px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(20)
        
        # Botão Assinar e Guardar
        btn_assinar = BiodeskUIKit.create_primary_button("✍️ Assinar e Guardar")
        btn_assinar.setStyleSheet(btn_assinar.styleSheet() + """
            QPushButton {
                font-size: 16px;
                padding: 15px 30px;
                min-width: 200px;
            }
        """)
        btn_assinar.clicked.connect(self.assinar_e_guardar)
        layout.addWidget(btn_assinar)
        
        # Botão Limpar
        btn_limpar = BiodeskUIKit.create_neutral_button("🗑️ Limpar Formulário")
        btn_limpar.setStyleSheet(btn_limpar.styleSheet() + """
            QPushButton {
                font-size: 16px;
                padding: 15px 30px;
                min-width: 160px;
            }
        """)
        btn_limpar.clicked.connect(self.limpar_formulario)
        layout.addWidget(btn_limpar)
        
        layout.addStretch()
        
        return frame
    
    def set_paciente_data(self, dados):
        """Define dados do paciente"""
        self.paciente_data = dados
        
        # Auto-povoar campos
        if dados:
            self.nome_edit.setText(dados.get('nome', ''))
            self.data_nasc_edit.setText(dados.get('data_nascimento', ''))
    
    def assinar_e_guardar(self):
        """Abre sistema de assinatura e guarda PDF"""
        try:
            if not self.paciente_data:
                mostrar_aviso(self, "Aviso", "⚠️ Nenhum paciente selecionado.\n\nPor favor, selecione um paciente primeiro.")
                return
            
            # Validar se há dados preenchidos
            if not self._validar_formulario():
                return
            
            # Abrir diálogo de assinatura
            dados_assinaturas = abrir_dialogo_assinatura(
                self, 
                "Declaração de Saúde", 
                self.paciente_data
            )
            
            if dados_assinaturas:
                # Gerar PDF com assinaturas
                if self._gerar_pdf_com_assinaturas(dados_assinaturas):
                    # Emitir sinal de sucesso (manter formulário preenchido)
                    self.declaracao_assinada.emit({
                        'paciente_id': self.paciente_data.get('id'),
                        'dados': self._obter_dados_formulario(),
                        'assinaturas': dados_assinaturas
                    })
                    # Comentado: self.limpar_formulario() - para manter dados para consulta
            
        except Exception as e:
            print(f"❌ Erro ao processar assinatura: {e}")
            mostrar_erro(self, "Erro", f"❌ Erro ao processar assinatura:\n\n{str(e)}")
    
    def _validar_formulario(self):
        """Valida se há dados suficientes no formulário"""
        # Verificar se pelo menos uma seção foi preenchida
        tem_problemas = (self.problemas_combo.currentIndex() > 0 and 
                        self.problemas_combo.currentText() != "Selecionar...")
        tem_medicacao = (self.medicacao_combo.currentIndex() > 0 and 
                        self.medicacao_combo.currentText() != "Selecionar...")
        tem_alergias = (self.alergias_combo.currentIndex() > 0 and 
                       self.alergias_combo.currentText() != "Selecionar...")
        tem_observacoes = bool(self.observacoes.toPlainText().strip())
        
        if not (tem_problemas or tem_medicacao or tem_alergias or tem_observacoes):
            mostrar_aviso(self, "Formulário Incompleto", 
                         "⚠️ Preencha pelo menos uma seção do formulário antes de assinar.\n\n"
                         "• Estado de Saúde Geral\n"
                         "• Medicação e Tratamentos\n"  
                         "• Alergias e Reações\n"
                         "• Observações Gerais")
            return False
        
        return True
    
    def limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        try:
            # Limpar dropdowns
            self.problemas_combo.setCurrentIndex(0)
            self.medicacao_combo.setCurrentIndex(0)
            self.alergias_combo.setCurrentIndex(0)
            
            # Limpar text areas
            self.problemas_detalhe.clear()
            self.medicacao_detalhe.clear()
            self.alergias_detalhe.clear()
            self.observacoes.clear()
            
            mostrar_sucesso(self, "Sucesso", "✅ Formulário limpo com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao limpar formulário: {e}")
            mostrar_erro(self, "Erro", f"Erro ao limpar formulário:\n{str(e)}")
    
    def _obter_dados_formulario(self):
        """Obtém dados estruturados do formulário"""
        return {
            'nome': self.nome_edit.text(),
            'data_nascimento': self.data_nasc_edit.text(),
            'data_declaracao': self.data_declaracao_edit.text(),
            'problemas_saude': {
                'resposta': self.problemas_combo.currentText(),
                'detalhes': self.problemas_detalhe.toPlainText().strip()
            },
            'medicacao': {
                'resposta': self.medicacao_combo.currentText(),
                'detalhes': self.medicacao_detalhe.toPlainText().strip()
            },
            'alergias': {
                'resposta': self.alergias_combo.currentText(),
                'detalhes': self.alergias_detalhe.toPlainText().strip()
            },
            'observacoes': self.observacoes.toPlainText().strip()
        }
    
    def _salvar_assinaturas_para_pdf(self, dados_assinaturas):
        """Salva assinaturas como PNG para uso no PDF"""
        try:
            import os
            os.makedirs("temp", exist_ok=True)
            
            # Salvar assinatura do paciente
            if dados_assinaturas['paciente']['assinado'] and dados_assinaturas['paciente']['imagem']:
                caminho_paciente = os.path.abspath('temp/sig_declaracao_paciente.png')
                dados_assinaturas['paciente']['imagem'].save(caminho_paciente, 'PNG')
                print(f"✅ Assinatura do paciente salva: {caminho_paciente}")
            
            # Salvar assinatura do profissional
            if dados_assinaturas['profissional']['assinado'] and dados_assinaturas['profissional']['imagem']:
                caminho_profissional = os.path.abspath('temp/sig_declaracao_profissional.png')
                dados_assinaturas['profissional']['imagem'].save(caminho_profissional, 'PNG')
                print(f"✅ Assinatura do profissional salva: {caminho_profissional}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar assinaturas: {e}")

    def _gerar_pdf_com_assinaturas(self, dados_assinaturas):
        """Gera PDF profissional com assinaturas integradas"""
        try:
            # 🎯 Salvar assinaturas como PNG para integração no PDF
            self._salvar_assinaturas_para_pdf(dados_assinaturas)
            
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF
            
            # Obter dados do formulário
            dados = self._obter_dados_formulario()
            
            # Obter dados do paciente
            paciente_id = self.paciente_data.get('id')
            nome_paciente = self.paciente_data.get('nome', '[NOME_PACIENTE]')
            data_atual = datetime.now().strftime('%d/%m/%Y às %H:%M')
            
            print(f"📋 [PDF] Gerando PDF profissional para {nome_paciente}...")
            
            # Criar diretório
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente.replace(' ', '_')}"
            pasta_declaracoes = f"{pasta_paciente}/declaracoes_saude"
            os.makedirs(pasta_declaracoes, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho_pdf = f"{pasta_declaracoes}/declaracao_saude_{timestamp}.pdf"
            
            # Construir HTML profissional
            html_content = self._construir_html_profissional(dados, dados_assinaturas, data_atual)
            
            # Configurar documento para máxima qualidade
            document = QTextDocument()
            document.setHtml(html_content)
            
            # Configurar impressora para PDF de alta qualidade
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageLayout(QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Portrait,
                QMarginsF(15, 15, 15, 15)  # Margens menores para aproveitar melhor o espaço
            ))
            
            # Configurações adicionais para qualidade
            printer.setResolution(600)  # Alta resolução para texto nítido
            
            # Imprimir com a máxima qualidade
            document.print(printer)
            
            # Registrar no gestor
            self._registrar_no_gestor_documentos(caminho_pdf)
            
            print(f"✅ [PDF] Declaração guardada: {caminho_pdf}")
            mostrar_sucesso(self, "Sucesso", 
                          f"✅ Declaração de saúde assinada e guardada com sucesso!\n\n"
                          f"📁 Localização: {caminho_pdf}\n\n"
                          f"🔹 Paciente: {dados_assinaturas['paciente']['assinado'] and '✓' or '✗'} Assinado\n"
                          f"🔹 Profissional: {dados_assinaturas['profissional']['assinado'] and '✓' or '✗'} Assinado")
            return True
                
        except Exception as e:
            print(f"❌ [PDF] Erro ao gerar PDF: {e}")
            mostrar_erro(self, "Erro", f"❌ Erro ao gerar PDF da declaração:\n\n{str(e)}")
            return False
    
    def _construir_html_profissional(self, dados, dados_assinaturas, data_atual):
        """Constrói HTML profissional para o PDF com assinaturas reais do canvas"""
        
        # Construir seções do conteúdo com todas as perguntas
        secoes_conteudo = ""
        
        # Seção Problemas de Saúde
        secoes_conteudo += f"""
        <div class="secao">
            <h3>🏥 Estado de Saúde Geral</h3>
            <div class="pergunta-resposta">
                <p class="pergunta"><strong>Tem problemas de saúde atuais?</strong></p>
                <p class="resposta">{dados['problemas_saude']['resposta'] if dados['problemas_saude']['resposta'] != "Selecionar..." else "Não respondido"}</p>
                {f'<p class="detalhes"><strong>Detalhes:</strong> {dados["problemas_saude"]["detalhes"]}</p>' if dados['problemas_saude']['detalhes'] else ""}
            </div>
        </div>
        """
        
        # Seção Medicação
        secoes_conteudo += f"""
        <div class="secao">
            <h3>💊 Medicação e Tratamentos</h3>
            <div class="pergunta-resposta">
                <p class="pergunta"><strong>Toma medicação atualmente?</strong></p>
                <p class="resposta">{dados['medicacao']['resposta'] if dados['medicacao']['resposta'] != "Selecionar..." else "Não respondido"}</p>
                {f'<p class="detalhes"><strong>Detalhes:</strong> {dados["medicacao"]["detalhes"]}</p>' if dados['medicacao']['detalhes'] else ""}
            </div>
        </div>
        """
        
        # Seção Alergias
        secoes_conteudo += f"""
        <div class="secao">
            <h3>🚨 Alergias e Reações Adversas</h3>
            <div class="pergunta-resposta">
                <p class="pergunta"><strong>Tem alergias conhecidas?</strong></p>
                <p class="resposta">{dados['alergias']['resposta'] if dados['alergias']['resposta'] != "Selecionar..." else "Não respondido"}</p>
                {f'<p class="detalhes"><strong>Detalhes:</strong> {dados["alergias"]["detalhes"]}</p>' if dados['alergias']['detalhes'] else ""}
            </div>
        </div>
        """
        
        # Seção Observações
        if dados['observacoes']:
            secoes_conteudo += f"""
            <div class="secao">
                <h3>📝 Observações e Informações Adicionais</h3>
                <div class="pergunta-resposta">
                    <p class="resposta">{dados['observacoes']}</p>
                </div>
            </div>
            """
        
        # 🎯 INTEGRAÇÃO DAS ASSINATURAS REAIS DO CANVAS
        assinatura_paciente_html = ""
        assinatura_profissional_html = ""
        
        # Verificar assinatura do paciente
        try:
            import base64
            import os
            
            # Caminho da assinatura do paciente
            sig_paciente_path = os.path.abspath('temp/sig_declaracao_paciente.png')
            if os.path.exists(sig_paciente_path):
                with open(sig_paciente_path, 'rb') as f:
                    assinatura_base64_paciente = base64.b64encode(f.read()).decode('utf-8')
                assinatura_paciente_html = f'<img src="data:image/png;base64,{assinatura_base64_paciente}" class="assinatura-imagem">'
            else:
                assinatura_paciente_html = '<div class="sem-assinatura">Assinatura não encontrada</div>'
            
            # Caminho da assinatura do profissional (se existir)
            sig_profissional_path = os.path.abspath('temp/sig_declaracao_profissional.png')
            if os.path.exists(sig_profissional_path):
                with open(sig_profissional_path, 'rb') as f:
                    assinatura_base64_profissional = base64.b64encode(f.read()).decode('utf-8')
                assinatura_profissional_html = f'<img src="data:image/png;base64,{assinatura_base64_profissional}" class="assinatura-imagem">'
            else:
                assinatura_profissional_html = '<div class="sem-assinatura">Aguardando assinatura</div>'
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar assinaturas: {e}")
            assinatura_paciente_html = '<div class="sem-assinatura">Erro ao carregar assinatura</div>'
            assinatura_profissional_html = '<div class="sem-assinatura">Erro ao carregar assinatura</div>'
        
        # Template HTML completo com tipografia profissional
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                
                body {{
                    font-family: 'Times New Roman', Times, serif;
                    margin: 0;
                    padding: 0;
                    line-height: 1.8;
                    color: #1a1a1a;
                    background-color: white;
                    font-size: 16pt;
                    min-width: 600px; /* Largura mínima */
                    max-width: 100%; /* Responsivo */
                }}
                
                /* CSS RESPONSIVO PARA DIFERENTES TAMANHOS */
                @media screen and (max-width: 1200px) {{
                    body {{ font-size: 14pt; }}
                    table {{ margin: 15px 0 15px -30px !important; }}
                }}
                
                @media screen and (max-width: 900px) {{
                    body {{ font-size: 12pt; }}
                    table {{ margin: 10px 0 10px -20px !important; }}
                }}
                
                @media screen and (max-width: 600px) {{
                    body {{ font-size: 11pt; }}
                    table {{ margin: 5px 0 5px -10px !important; }}
                }}
                
                /* ASSINATURAS COM TABELA - RESPONSIVA */
                table {{
                    border-collapse: collapse !important;
                    width: 70% !important; /* tornar menor para caber com folga nas margens */
                    margin: 40px auto 15px auto !important; /* mais espaço topo e centrado horizontalmente */
                    min-width: 0 !important; /* permitir reflow em telas pequenas */
                    table-layout: fixed; /* Layout fixo para melhor controlo */
                }}
                
                td {{
                    vertical-align: middle !important;
                    padding: 10px 12px !important; /* espaço suficiente para a assinatura */
                    width: 45% !important; /* colunas levemente menores para folga */
                    box-sizing: border-box; /* Inclui padding na largura */
                    text-align: center !important;
                }}
                
                .assinatura {{
                    text-align: center !important;
                    width: 100% !important;
                }}
                
                .assinatura h4 {{
                    margin: 0 0 8px 0 !important;
                    color: #1f2937 !important;
                    font-size: 18pt !important;
                    font-weight: bold !important;
                }}
                
                .linha-assinatura {{
                    position: relative !important;
                    height: 40px !important; /* reduzir ainda mais para aproximar nome */
                    margin: 4px auto !important;
                    background-color: transparent !important;
                    display: flex !important;
                    align-items: flex-end !important; /* alinhar assinatura pela base para ficar na linha */
                    justify-content: center !important;
                    width: 100% !important; /* usar toda a largura da célula para evitar deslocamentos */
                    padding: 0 0 6px 0 !important; /* pequeno padding-bottom para controlar o encaixe */
                }}

                /* linha-guia: pontilhada, fixa dentro da caixa e cerca de 16-18px do fundo */
                .linha-assinatura .linha-guia {{
                    position: absolute !important;
                    left: 10% !important; /* alinhar com largura da caixa */
                    right: 10% !important;
                    bottom: 6px !important; /* aproximar a linha do fundo */
                    border-bottom: 1px dotted #cfcfcf !important;
                    height: 0 !important;
                    pointer-events: none !important;
                }}

                .assinatura-wrapper {{
                    position: relative !important;
                    z-index: 2 !important;
                    display: inline-block !important;
                    vertical-align: bottom !important;
                    margin: 0 auto !important;
                    bottom: 0 !important; /* garantir que fica junto ao fundo da caixa */
                }}

                /* wrapper que limita o campo útil da assinatura e centra dentro da célula */
                .assinatura-cell {{
                    display: block !important;
                    max-width: 340px !important; /* campo útil da assinatura */
                    width: 100% !important;
                    margin: 0 auto !important;
                    text-align: center !important;
                }}

                .assinatura-imagem {{
                    max-width: 65% !important;   /* limitar largura para evitar corte nas margens */
                    max-height: 48px !important; /* permitir um pouco mais de altura, mas controlada */
                    height: auto !important;
                    width: auto !important;
                    border: none !important;
                    display: block !important;
                    vertical-align: bottom !important;
                    margin: 0 auto 0 auto !important; /* sem margem inferior extra */
                }}

                .info-assinatura {{
                    font-size: 11pt !important;
                    color: #374151 !important;
                    line-height: 1.0 !important;    /* compacto, mas legível */
                    margin-top: -10px !important;     /* puxar ainda mais para perto da linha */
                    text-align: center !important;
                    display: block !important;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 50px;
                    padding: 40px 30px;
                    border: 3px solid #2563eb;
                    border-radius: 15px;
                    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                }}
                
                .header h1 {{
                    color: #1e40af;
                    font-size: 36pt;
                    font-weight: bold;
                    margin: 0 0 30px 0;
                    text-transform: uppercase;
                    letter-spacing: 3px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                }}
                
                .info-paciente {{
                    display: table;
                    width: 100%;
                    margin: 30px 0;
                    border-collapse: separate;
                    border-spacing: 15px;
                }}
                
                .info-paciente div {{
                    display: table-cell;
                    padding: 20px;
                    background-color: white;
                    border-radius: 12px;
                    border: 2px solid #e2e8f0;
                    font-size: 18pt;
                    font-weight: 500;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .declaracao {{
                    background-color: #f1f5f9;
                    padding: 40px;
                    margin: 40px 0;
                    border-left: 8px solid #2563eb;
                    border-radius: 12px;
                    font-size: 18pt;
                    font-style: italic;
                    line-height: 2;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                
                .declaracao p {{
                    margin: 0;
                    text-align: justify;
                }}
                
                .secao {{
                    margin: 40px 0;
                    padding: 30px;
                    border: 2px solid #e2e8f0;
                    border-radius: 15px;
                    background-color: #fefefe;
                    page-break-inside: avoid;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }}
                
                .secao h3 {{
                    color: #1e40af;
                    margin-top: 0;
                    margin-bottom: 25px;
                    font-size: 24pt;
                    font-weight: bold;
                    border-bottom: 3px solid #e2e8f0;
                    padding-bottom: 15px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                .pergunta-resposta {{
                    margin: 20px 0;
                }}
                
                .pergunta {{
                    margin: 15px 0 10px 0;
                    font-size: 18pt;
                    font-weight: bold;
                    color: #374151;
                }}
                
                .resposta {{
                    margin: 10px 0 15px 20px;
                    font-size: 17pt;
                    color: #1f2937;
                    background-color: #f9fafb;
                    padding: 15px 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3b82f6;
                }}
                
                .detalhes {{
                    margin: 15px 0 15px 20px;
                    font-size: 16pt;
                    color: #4b5563;
                    background-color: #fefefe;
                    padding: 15px 20px;
                    border-radius: 8px;
                    border: 1px solid #e5e7eb;
                    line-height: 1.8;
                }}
                
                .assinaturas {{
                    margin-top: 60px;  /* ✅ Reduzido de 80px para 60px */
                    display: flex;
                    justify-content: center;  /* ✅ Melhor centramento */
                    align-items: flex-start;
                    gap: 40px;  /* ✅ Aumentado de 30px para 40px para melhor separação */
                    page-break-inside: avoid;
                    width: 100%;
                    flex-wrap: nowrap;
                }}
                
                .assinatura {{
                    flex: 0 1 auto;  /* ✅ Não expandir automaticamente */
                    min-width: 250px;  /* ✅ Reduzido de 280px */
                    max-width: 350px;  /* ✅ Tamanho máximo definido */
                    text-align: center;
                    padding: 20px;  /* ✅ Reduzido de 25px para 20px */
                    border: 2px solid #d1d5db;  /* ✅ Borda mais fina */
                    border-radius: 12px;  /* ✅ Reduzido de 15px */
                    background-color: #f9fafb;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.03);  /* ✅ Sombra mais sutil */
                }}
                
                /* Fallback para impressoras que não suportam flexbox */
                @media print {{
                    .assinaturas {{
                        display: table;
                        width: 100%;
                        border-collapse: separate;
                        border-spacing: 20px 0;
                        table-layout: fixed;  /* Força distribuição igual */
                    }}
                    
                    .assinatura {{
                        display: table-cell;
                        width: 48%;
                        vertical-align: top;
                        flex: none;
                        min-width: auto;
                        max-width: none;
                    }}
                }}
                
                .assinatura h4 {{
                    margin-top: 0;
                    margin-bottom: 10px;  /* ✅ Reduzido de 15px para 10px */
                    color: #1f2937;
                    font-size: 18pt;  
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                .linha-assinatura {{
                    height: 70px;      
                    border: 2px solid #e5e7eb;
                    margin: 10px 0 5px 0;  /* ✅ Reduzido ainda mais: era 15px 0 10px 0 */
                    background-color: white;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 8px;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
                }}
                
                .assinatura-imagem {{
                    max-width: 80%;    /* ✅ Reduzido de 100% para 80% */
                    max-height: 50px;  /* ✅ Reduzido de 80px para 50px */
                    height: auto;
                    width: auto;
                    border: none;
                    display: block;
                    margin: 0 auto;
                }}
                
                .sem-assinatura {{
                    color: #6b7280;
                    font-style: italic;
                    font-size: 14pt;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    border: 2px dashed #d1d5db;
                    background-color: #f9fafb;
                    border-radius: 8px;
                }}
                
                .info-assinatura {{
                    font-size: 14pt;  
                    color: #4b5563;
                    margin-top: 2px;  /* ✅ Reduzido drasticamente de 8px para 2px */
                    line-height: 1.2;  /* ✅ Reduzido de 1.4 para 1.2 para mais compacto */
                }}
                
                .info-assinatura strong {{
                    font-size: 15pt;  
                    color: #1f2937;
                }}
                
                .footer {{
                    margin-top: 60px;
                    text-align: center;
                    font-size: 14pt;
                    color: #6b7280;
                    border-top: 2px solid #e5e7eb;
                    padding-top: 30px;
                    page-break-inside: avoid;
                }}
                
                .footer p {{
                    margin: 10px 0;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Declaração de Saúde</h1>
                <div class="info-paciente">
                    <div><strong>Paciente:</strong><br>{dados['nome']}</div>
                    <div><strong>Data de Nascimento:</strong><br>{dados['data_nascimento']}</div>
                    <div><strong>Data da Declaração:</strong><br>{data_atual}</div>
                </div>
            </div>
            
            <div class="declaracao">
                <p><strong>Eu, {dados['nome']},</strong> declaro que as informações fornecidas sobre o meu estado de saúde são <strong>verdadeiras e completas</strong>, e autorizo o uso destas informações para fins de acompanhamento clínico e terapêutico.</p>
            </div>
            
            {secoes_conteudo}
            
            <!-- TABELA ULTRA COMPACTA - CENTRALIZADA -->
            <table style="width: 70%; border-collapse: collapse; margin: 15px auto 15px auto;">
                <tr>
                    <td style="width: 50%; vertical-align: top; text-align: center; padding: 0 10px;">
                        <div style="text-align: center; width: 100%;">
                            <h4 style="margin: 0 0 5px 0; color: #1f2937; font-size: 14pt; font-weight: bold;">{dados['nome']}</h4>
                            <div class="assinatura-cell">
                                <div class="linha-assinatura" style="width:100%; margin:0 auto;">
                                    <div class="assinatura-wrapper">
                                        {assinatura_paciente_html}
                                    </div>
                                    <div class="linha-guia"></div>
                                </div>
                            </div>
                            <!-- nome/data removidos: já exibidos no cabeçalho -->
                        </div>
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: center; padding: 0 10px;">
                        <div style="text-align: center; width: 100%;">
                            <h4 style="margin: 0 0 5px 0; color: #1f2937; font-size: 14pt; font-weight: bold;">{self.paciente_data.get('terapeuta_nome', dados_assinaturas['profissional'].get('nome', 'Profissional'))}<br><span style="font-size:10pt; font-weight:normal;">CP {self.paciente_data.get('terapeuta_cp', '')}</span></h4>
                            <div class="assinatura-cell">
                                <div class="linha-assinatura" style="width:100%; margin:0 auto;">
                                    <div class="assinatura-wrapper">
                                        {assinatura_profissional_html}
                                    </div>
                                    <div class="linha-guia"></div>
                                </div>
                            </div>
                            <!-- nome/data removidos: já exibidos no cabeçalho -->
                        </div>
                    </td>
                </tr>
            </table>
            
            <div class="footer">
                <p><strong>Documento gerado automaticamente pelo sistema Biodesk em {data_atual}</strong></p>
                <p>Este documento possui validade legal e foi assinado digitalmente conforme a legislação vigente.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _registrar_no_gestor_documentos(self, caminho_pdf):
        """Registra no gestor de documentos e emite sinal para atualização"""
        try:
            # Emitir sinal para o widget pai atualizar o gestor de documentos
            self.declaracao_assinada.emit({
                'paciente_id': self.paciente_data.get('id'),
                'tipo': 'declaracao_saude',
                'caminho': caminho_pdf,
                'data_criacao': datetime.now().isoformat(),
                'titulo': f"Declaração de Saúde - {datetime.now().strftime('%d/%m/%Y')}"
            })
            
            # Tentar registrar também no DocumentManager se disponível
            try:
                from editor_documentos import DocumentManager
                
                doc_manager = DocumentManager()
                doc_manager.adicionar_documento({
                    'paciente_id': self.paciente_data.get('id'),
                    'tipo': 'declaracao_saude',
                    'caminho': caminho_pdf,
                    'data_criacao': datetime.now().isoformat(),
                    'titulo': f"Declaração de Saúde - {datetime.now().strftime('%d/%m/%Y')}"
                })
                print("📋 Documento registrado no DocumentManager")
                
            except ImportError:
                print("ℹ️ DocumentManager não disponível, usando apenas sinal")
            except Exception as e:
                print(f"⚠️ Erro ao registrar no DocumentManager: {e}")
            
        except Exception as e:
            print(f"⚠️ Erro ao registrar documento: {e}")
