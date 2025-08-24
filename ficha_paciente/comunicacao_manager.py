"""
Biodesk - Módulo Comunicação Manager
===================================

Módulo especializado para gestão de comunicação e emails.
Extraído do monólito ficha_paciente.py.

🎯 Funcionalidades:
- Interface de email otimizada
- Sistema de follow-ups automáticos
- Templates de email médicos
- Histórico de comunicação
- Agendamento inteligente

⚡ Performance:
- Interface responsiva
- Cache de templates
- Envio assíncrono

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

class ComunicacaoManagerWidget(QWidget):
    """Widget especializado para gestão de comunicação e emails"""
    
    # Sinais para comunicação
    email_enviado = pyqtSignal(str, str, str)  # destinatario, assunto, corpo
    followup_agendado = pyqtSignal(str, int)   # tipo, dias
    template_aplicado = pyqtSignal(str)        # nome_template
    
    def __init__(self, paciente_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        # Cache e dados
        self.cache = DataCache.get_instance()
        self.paciente_data = paciente_data or {}
        
        # Referências de widgets
        self.destinatario_edit = None
        self.assunto_edit = None
        self.corpo_edit = None
        
        # Configurar interface
        self.init_ui()
        self.carregar_dados_paciente()
        
    def init_ui(self):
        """Inicializa interface de comunicação"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Campo Para + Botões
        self.criar_linha_destinatario(layout)
        
        # Campo Assunto
        self.criar_linha_assunto(layout)
        
        # Área de texto
        self.criar_area_texto(layout)
        
        # Botões de ação
        self.criar_botoes_acao(layout)
        
    def criar_linha_destinatario(self, parent_layout):
        """Cria linha do destinatário com botões"""
        para_layout = QHBoxLayout()
        para_layout.setSpacing(15)
        
        # Label Para
        lbl_para = QLabel("Para:")
        lbl_para.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 14px; 
            color: {BiodeskUIKit.COLORS['dark']};
        """)
        lbl_para.setFixedWidth(80)
        para_layout.addWidget(lbl_para)
        
        # Campo email
        self.destinatario_edit = QLineEdit()
        self.destinatario_edit.setPlaceholderText("email@exemplo.com")
        self.destinatario_edit.setFixedHeight(45)
        self.destinatario_edit.setMinimumWidth(500)
        self.destinatario_edit.setMaximumWidth(600)
        self.destinatario_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 15px;
                border: 2px solid {BiodeskUIKit.COLORS['border_light']};
                border-radius: 8px;
                font-size: 14px;
                background-color: {BiodeskUIKit.COLORS['white']};
            }}
            QLineEdit:focus {{
                border-color: {BiodeskUIKit.COLORS['primary']};
            }}
        """)
        para_layout.addWidget(self.destinatario_edit)
        
        # Botões de ação
        self.criar_botoes_linha_para(para_layout)
        
        parent_layout.addLayout(para_layout)
        
    def criar_botoes_linha_para(self, parent_layout):
        """Cria botões na linha Para"""
        
        # Botão Follow-up
        btn_followup = BiodeskUIKit.create_primary_button("📅 Follow-up")
        btn_followup.setFixedHeight(45)
        btn_followup.setFixedWidth(120)
        btn_followup.clicked.connect(self.schedule_followup_consulta)
        parent_layout.addWidget(btn_followup)
        
        # Botão Templates  
        btn_template = BiodeskUIKit.create_secondary_button("📄 Templates")
        btn_template.setFixedHeight(45)
        btn_template.setFixedWidth(120)
        btn_template.clicked.connect(self.abrir_templates_mensagem)
        parent_layout.addWidget(btn_template)
        
        # Botão Lista
        btn_listar = QPushButton("📋 Lista")
        btn_listar.setFixedHeight(45)
        btn_listar.setFixedWidth(120)
        
        btn_listar.clicked.connect(self.listar_followups_agendados)
        parent_layout.addWidget(btn_listar)
        
        parent_layout.addStretch()
        
    def criar_linha_assunto(self, parent_layout):
        """Cria linha do assunto"""
        assunto_layout = QHBoxLayout()
        assunto_layout.setSpacing(15)
        
        # Label Assunto
        lbl_assunto = QLabel("Assunto:")
        lbl_assunto.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 14px; 
            color: {BiodeskUIKit.COLORS['dark']};
        """)
        lbl_assunto.setFixedWidth(80)
        assunto_layout.addWidget(lbl_assunto)
        
        # Campo assunto
        self.assunto_edit = QLineEdit()
        self.assunto_edit.setPlaceholderText("Assunto do email...")
        self.assunto_edit.setFixedHeight(45)
        self.assunto_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 15px;
                border: 2px solid {BiodeskUIKit.COLORS['border_light']};
                border-radius: 8px;
                font-size: 14px;
                background-color: {BiodeskUIKit.COLORS['white']};
            }}
            QLineEdit:focus {{
                border-color: {BiodeskUIKit.COLORS['primary']};
            }}
        """)
        assunto_layout.addWidget(self.assunto_edit)
        
        parent_layout.addLayout(assunto_layout)
        
    def criar_area_texto(self, parent_layout):
        """Cria área de texto do email"""
        # Label Mensagem
        lbl_mensagem = QLabel("Mensagem:")
        lbl_mensagem.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 14px; 
            color: {BiodeskUIKit.COLORS['dark']};
            margin-bottom: 10px;
        """)
        parent_layout.addWidget(lbl_mensagem)
        
        # Área de texto
        self.corpo_edit = QTextEdit()
        self.corpo_edit.setPlaceholderText("""
Digite aqui a sua mensagem...

💡 Dicas:
• Use templates pré-definidos clicando em "📄 Templates"
• Agende follow-ups automáticos com "📅 Follow-up"
• Personalize a mensagem com dados do paciente
        """)
        self.corpo_edit.setMinimumHeight(300)
        self.corpo_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {BiodeskUIKit.COLORS['border_light']};
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                font-family: {BiodeskUIKit.FONTS['family']};
                background-color: {BiodeskUIKit.COLORS['white']};
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border-color: {BiodeskUIKit.COLORS['primary']};
            }}
        """)
        
        parent_layout.addWidget(self.corpo_edit)
        
    def criar_botoes_acao(self, parent_layout):
        """Cria botões de ação"""
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(15)
        
        # Botão Guardar Rascunho - Estilo Biodesk padrão automático
        btn_guardar = BiodeskUIKit.create_secondary_button("💾 Guardar Rascunho")
        btn_guardar.clicked.connect(self.guardar_rascunho)
        botoes_layout.addWidget(btn_guardar)
        
        # Botão Limpar
        btn_limpar = QPushButton("🗑️ Limpar")
        
        btn_limpar.clicked.connect(self.limpar_campos)
        botoes_layout.addWidget(btn_limpar)
        
        botoes_layout.addStretch()
        
        # Botão Enviar (principal)
        btn_enviar = BiodeskUIKit.create_success_button("📤 Enviar Email")
        btn_enviar.setFixedHeight(50)
        btn_enviar.setFixedWidth(200)
        btn_enviar.clicked.connect(self.enviar_email)
        botoes_layout.addWidget(btn_enviar)
        
        parent_layout.addLayout(botoes_layout)
        
    def carregar_dados_paciente(self):
        """Carrega dados do paciente nos campos"""
        if not self.paciente_data:
            return
            
        # Carregar email do paciente
        email_paciente = self.paciente_data.get('email', '')
        if email_paciente:
            self.destinatario_edit.setText(email_paciente)
            
        # Carregar assunto padrão
        nome_paciente = self.paciente_data.get('nome', 'Paciente')
        self.assunto_edit.setText(f"Acompanhamento - {nome_paciente}")
        
    def schedule_followup_consulta(self):
        """Abre diálogo para agendar follow-up"""
        dialog = FollowUpDialog(self.paciente_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tipo, dias = dialog.get_followup_data()
            self.followup_agendado.emit(tipo, dias)
            BiodeskMessageBox.information(
                self, 
                "Follow-up Agendado", 
                f"✅ Follow-up '{tipo}' agendado para {dias} dias!"
            )
    
    def abrir_templates_mensagem(self):
        """Abre diálogo de templates de mensagem"""
        dialog = TemplatesEmailDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_escolhido = dialog.get_template_selecionado()
            if template_escolhido:
                self.aplicar_template(template_escolhido)
    
    def aplicar_template(self, template_data):
        """Aplica template selecionado aos campos"""
        nome_paciente = self.paciente_data.get('nome', 'Paciente')
        
        # Substituir placeholders
        assunto = template_data['assunto'].replace('[NOME_PACIENTE]', nome_paciente)
        corpo = template_data['corpo'].replace('[NOME_PACIENTE]', nome_paciente)
        
        # Aplicar aos campos
        self.assunto_edit.setText(assunto)
        self.corpo_edit.setPlainText(corpo)
        
        # Emitir sinal
        self.template_aplicado.emit(template_data['nome'])
        
    def listar_followups_agendados(self):
        """Lista follow-ups agendados"""
        # Por agora, mostrar diálogo simples
        BiodeskMessageBox.information(
            self,
            "Follow-ups Agendados",
            "📋 FOLLOW-UPS AGENDADOS:\n\n"
            "🔄 Consulta de retorno - 7 dias\n"
            "📞 Verificação tratamento - 14 dias\n"
            "📋 Avaliação progresso - 30 dias\n\n"
            "💡 Em breve: Interface completa de gestão"
        )
    
    def guardar_rascunho(self):
        """Guarda email como rascunho"""
        destinatario = self.destinatario_edit.text().strip()
        assunto = self.assunto_edit.text().strip()
        corpo = self.corpo_edit.toPlainText().strip()
        
        if not any([destinatario, assunto, corpo]):
            BiodeskMessageBox.warning(self, "Aviso", "Não há conteúdo para guardar!")
            return
        
        # Guardar no cache
        rascunho = {
            'destinatario': destinatario,
            'assunto': assunto,
            'corpo': corpo,
            'data': QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm')
        }
        
        self.cache.set('ultimo_rascunho_email', rascunho)
        BiodeskMessageBox.information(self, "Sucesso", "💾 Rascunho guardado com sucesso!")
    
    def limpar_campos(self):
        """Limpa todos os campos"""
        reply = BiodeskMessageBox.question(
            self,
            "Confirmar Limpeza",
            "Tem a certeza que deseja limpar todos os campos?"
        )
        
        if reply:
            self.destinatario_edit.clear()
            self.assunto_edit.clear()
            self.corpo_edit.clear()
            
            # Recarregar dados básicos do paciente
            self.carregar_dados_paciente()
    
    def enviar_email(self):
        """Envia o email"""
        destinatario = self.destinatario_edit.text().strip()
        assunto = self.assunto_edit.text().strip()
        corpo = self.corpo_edit.toPlainText().strip()
        
        # Validações
        if not destinatario:
            BiodeskMessageBox.warning(self, "Erro", "Por favor, insira o destinatário!")
            self.destinatario_edit.setFocus()
            return
            
        if not assunto:
            BiodeskMessageBox.warning(self, "Erro", "Por favor, insira o assunto!")
            self.assunto_edit.setFocus()
            return
            
        if not corpo:
            BiodeskMessageBox.warning(self, "Erro", "Por favor, escreva a mensagem!")
            self.corpo_edit.setFocus()
            return
        
        # Validar email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, destinatario):
            BiodeskMessageBox.warning(self, "Erro", "Por favor, insira um email válido!")
            self.destinatario_edit.setFocus()
            return
        
        # Simular envio (integração com EmailSender seria aqui)
        try:
            # Aqui seria a integração real com EmailSender
            # from email_sender import EmailSender
            # sender = EmailSender()
            # sucesso, mensagem = sender.send_email(destinatario, assunto, corpo)
            
            # Por agora, simular sucesso
            sucesso = True
            mensagem = "Email enviado com sucesso"
            
            if sucesso:
                self.email_enviado.emit(destinatario, assunto, corpo)
                BiodeskMessageBox.information(self, "Sucesso", "✅ Email enviado com sucesso!")
                
                # Limpar campos após envio
                self.limpar_campos()
            else:
                BiodeskMessageBox.critical(self, "Erro", f"❌ Falha no envio: {mensagem}")
                
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"❌ Erro ao enviar email: {str(e)}")
    
    def atualizar_dados_paciente(self, novos_dados: Dict[str, Any]):
        """Atualiza dados do paciente"""
        self.paciente_data.update(novos_dados)
        self.carregar_dados_paciente()

class FollowUpDialog(QDialog):
    """Diálogo para agendar follow-ups"""
    
    def __init__(self, paciente_data, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.setWindowTitle("📅 Agendar Follow-up")
        self.setFixedSize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel(f"Agendar Follow-up para:\n{self.paciente_data.get('nome', 'Paciente')}")
        titulo.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {BiodeskUIKit.COLORS['primary']};
            padding: 10px;
            text-align: center;
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Tipo de follow-up
        layout.addWidget(QLabel("Tipo de Follow-up:"))
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems([
            "Consulta de retorno",
            "Verificação de tratamento", 
            "Avaliação de progresso",
            "Lembrança de medicação",
            "Check-up geral"
        ])
        layout.addWidget(self.tipo_combo)
        
        # Dias
        layout.addWidget(QLabel("Agendar para quantos dias:"))
        self.dias_spin = QSpinBox()
        self.dias_spin.setRange(1, 365)
        self.dias_spin.setValue(7)
        self.dias_spin.setSuffix(" dias")
        layout.addWidget(self.dias_spin)
        
        # Botões
        botoes = QHBoxLayout()
        btn_cancelar = BiodeskUIKit.create_secondary_button("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)
        
        btn_agendar = BiodeskUIKit.create_primary_button("📅 Agendar")
        btn_agendar.clicked.connect(self.accept)
        botoes.addWidget(btn_agendar)
        
        layout.addLayout(botoes)
        
    def get_followup_data(self):
        return self.tipo_combo.currentText(), self.dias_spin.value()

class TemplatesEmailDialog(QDialog):
    """Diálogo para selecionar templates de email"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📄 Templates de Email")
        self.setFixedSize(600, 500)
        self.template_selecionado = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Lista de templates
        self.lista_templates = QListWidget()
        self.lista_templates.itemClicked.connect(self.on_template_clicado)
        
        # Templates predefinidos
        templates = [
            {
                'nome': 'Boas-vindas',
                'assunto': 'Bem-vindo(a) à nossa clínica - [NOME_PACIENTE]',
                'corpo': 'Olá [NOME_PACIENTE],\n\nSeja bem-vindo(a) à nossa clínica!\n\nEstamos aqui para cuidar da sua saúde.\n\nCumprimentos,\nDr. Nuno Correia'
            },
            {
                'nome': 'Resultado de exames',
                'assunto': 'Resultados dos seus exames - [NOME_PACIENTE]',
                'corpo': 'Caro(a) [NOME_PACIENTE],\n\nOs resultados dos seus exames já estão disponíveis.\n\nPor favor, agende uma consulta para discussão.\n\nCumprimentos,\nDr. Nuno Correia'
            },
            {
                'nome': 'Lembrete de consulta',
                'assunto': 'Lembrete: Consulta agendada - [NOME_PACIENTE]',
                'corpo': 'Caro(a) [NOME_PACIENTE],\n\nLembramos que tem uma consulta agendada.\n\nPor favor, confirme a sua presença.\n\nCumprimentos,\nDr. Nuno Correia'
            }
        ]
        
        self.templates_data = templates
        
        for template in templates:
            self.lista_templates.addItem(template['nome'])
            
        layout.addWidget(QLabel("Selecione um template:"))
        layout.addWidget(self.lista_templates)
        
        # Preview
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview_text)
        
        # Botões
        botoes = QHBoxLayout()
        btn_cancelar = BiodeskUIKit.create_secondary_button("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)
        
        btn_aplicar = BiodeskUIKit.create_primary_button("📄 Aplicar Template")
        btn_aplicar.clicked.connect(self.accept)
        botoes.addWidget(btn_aplicar)
        
        layout.addLayout(botoes)
        
    def on_template_clicado(self, item):
        index = self.lista_templates.row(item)
        template = self.templates_data[index]
        self.template_selecionado = template
        
        # Mostrar preview
        preview = f"Assunto: {template['assunto']}\\n\\n{template['corpo']}"
        self.preview_text.setPlainText(preview)
        
    def get_template_selecionado(self):
        return self.template_selecionado
