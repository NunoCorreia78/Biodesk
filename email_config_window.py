from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from email_config import email_config
from email_sender import email_sender
from biodesk_dialogs import BiodeskMessageBox
from biodesk_ui_kit import BiodeskUIKit
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janela de Configuração de Email para Biodesk
"""

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QGroupBox, QSpinBox, QCheckBox,
    QTextEdit, QTabWidget, QWidget
)

class TestEmailThread(QThread):
    """Thread para testar conexão de email"""
    resultado = pyqtSignal(bool, str)
    
    def run(self):
        sucesso, mensagem = email_sender.test_connection()
        self.resultado.emit(sucesso, mensagem)

class EmailConfigWindow(QDialog):
    """Janela de configuração de email"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📧 Configuração de Email")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("📧 Configuração de Email")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(titulo)
        
        # Abas
        tabs = QTabWidget()
        
        # Aba 1: Configuração SMTP
        tab_smtp = self.criar_aba_smtp()
        tabs.addTab(tab_smtp, "🔧 Servidor SMTP")
        
        # Aba 2: Dados da Clínica
        tab_clinica = self.criar_aba_clinica()
        tabs.addTab(tab_clinica, "🏥 Dados da Clínica")
        
        # Aba 3: Templates
        tab_templates = self.criar_aba_templates()
        tabs.addTab(tab_templates, "📝 Templates")
        
        layout.addWidget(tabs)
        
        # Botões
        layout_botoes = QHBoxLayout()
        
        btn_testar = QPushButton("🔍 Testar Conexão")
        btn_testar.clicked.connect(self.testar_conexao)
        BiodeskUIKit.apply_universal_button_style(btn_testar)
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar_config)
        BiodeskUIKit.apply_universal_button_style(btn_guardar)
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        layout_botoes.addWidget(btn_testar)
        layout_botoes.addStretch()
        layout_botoes.addWidget(btn_guardar)
        layout_botoes.addWidget(btn_cancelar)
        
        layout.addLayout(layout_botoes)
        self.setLayout(layout)
    
    def criar_aba_smtp(self):
        """Cria aba de configuração SMTP"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Grupo de servidor
        grupo_servidor = QGroupBox("🔧 Configuração do Servidor")
        form_servidor = QFormLayout()
        
        self.input_smtp_server = QLineEdit()
        self.input_smtp_server.setPlaceholderText("smtp.gmail.com")
        form_servidor.addRow("Servidor SMTP:", self.input_smtp_server)
        
        self.input_smtp_port = QSpinBox()
        self.input_smtp_port.setRange(1, 65535)
        self.input_smtp_port.setValue(587)
        form_servidor.addRow("Porta:", self.input_smtp_port)
        
        self.check_use_tls = QCheckBox("Usar TLS/SSL")
        self.check_use_tls.setChecked(True)
        form_servidor.addRow("", self.check_use_tls)
        
        grupo_servidor.setLayout(form_servidor)
        layout.addWidget(grupo_servidor)
        
        # Grupo de autenticação
        grupo_auth = QGroupBox("🔐 Autenticação")
        form_auth = QFormLayout()
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("seu.email@gmail.com")
        form_auth.addRow("Email:", self.input_email)
        
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Senha ou App Password")
        form_auth.addRow("Senha:", self.input_password)
        
        grupo_auth.setLayout(form_auth)
        layout.addWidget(grupo_auth)
        
        # Nota sobre App Passwords
        nota = QLabel("""
        💡 <b>Para Gmail:</b><br>
        • Ative autenticação de 2 fatores<br>
        • Use "App Password" em vez da senha normal<br>
        • Google Account → Segurança → App passwords
        """)
        nota.setStyleSheet("""
            color: #666;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        """)
        layout.addWidget(nota)
        
        widget.setLayout(layout)
        return widget
    
    def criar_aba_clinica(self):
        """Cria aba de dados da clínica"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.input_nome_clinica = QLineEdit()
        self.input_nome_clinica.setPlaceholderText("Nome da Clínica")
        form.addRow("Nome da Clínica:", self.input_nome_clinica)
        
        self.input_telefone = QLineEdit()
        self.input_telefone.setPlaceholderText("+351 XXX XXX XXX")
        form.addRow("Telefone:", self.input_telefone)
        
        self.input_endereco = QLineEdit()
        self.input_endereco.setPlaceholderText("Rua, Número, Código Postal, Cidade")
        form.addRow("Endereço:", self.input_endereco)
        
        self.input_horario_semana = QLineEdit()
        self.input_horario_semana.setPlaceholderText("9:00 - 18:00")
        form.addRow("Horário (Seg-Sex):", self.input_horario_semana)
        
        self.input_horario_sabado = QLineEdit()
        self.input_horario_sabado.setPlaceholderText("9:00 - 13:00")
        form.addRow("Horário (Sábado):", self.input_horario_sabado)
        
        self.input_whatsapp = QLineEdit()
        self.input_whatsapp.setPlaceholderText("+351 XXX XXX XXX")
        form.addRow("WhatsApp:", self.input_whatsapp)
        
        layout.addLayout(form)
        widget.setLayout(layout)
        return widget
    
    def criar_aba_templates(self):
        """Cria aba de templates"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("📝 Assinatura de Email")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.input_assinatura = QTextEdit()
        self.input_assinatura.setPlaceholderText("""Com os melhores cumprimentos,
Equipa {nome_clinica}
📞 {telefone} | 📧 {email}
📍 {endereco}""")
        self.input_assinatura.setMaximumHeight(150)
        layout.addWidget(self.input_assinatura)
        
        info = QLabel("""
        💡 <b>Variáveis disponíveis:</b><br>
        • {nome_clinica} - Nome da clínica<br>
        • {telefone} - Telefone da clínica<br>
        • {email} - Email da clínica<br>
        • {endereco} - Endereço da clínica<br>
        • {nome} - Nome do paciente
        """)
        info.setStyleSheet("""
            color: #666;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        """)
        layout.addWidget(info)
        
        widget.setLayout(layout)
        return widget
    
    def load_config(self):
        """Carrega configuração atual"""
        config = email_config.config
        
        # SMTP
        self.input_smtp_server.setText(config.get("smtp_server", ""))
        self.input_smtp_port.setValue(config.get("smtp_port", 587))
        self.check_use_tls.setChecked(config.get("use_tls", True))
        self.input_email.setText(config.get("email", ""))
        self.input_password.setText(config.get("password", ""))
        
        # Clínica
        self.input_nome_clinica.setText(config.get("nome_clinica", ""))
        self.input_telefone.setText(config.get("telefone", ""))
        self.input_endereco.setText(config.get("endereco", ""))
        self.input_horario_semana.setText(config.get("horario_semana", ""))
        self.input_horario_sabado.setText(config.get("horario_sabado", ""))
        self.input_whatsapp.setText(config.get("whatsapp", ""))
        
        # Templates
        self.input_assinatura.setPlainText(config.get("assinatura", ""))
    
    def guardar_config(self):
        """Guarda configuração"""
        # Validar campos obrigatórios
        if not self.input_email.text().strip():
            BiodeskMessageBox.warning(self, "Campo Obrigatório", "Email é obrigatório!")
            return
        
        if not self.input_nome_clinica.text().strip():
            BiodeskMessageBox.warning(self, "Campo Obrigatório", "Nome da clínica é obrigatório!")
            return
        
        # Guardar configuração
        email_config.set("smtp_server", self.input_smtp_server.text().strip())
        email_config.set("smtp_port", self.input_smtp_port.value())
        email_config.set("use_tls", self.check_use_tls.isChecked())
        email_config.set("email", self.input_email.text().strip())
        email_config.set("password", self.input_password.text().strip())
        
        email_config.set("nome_clinica", self.input_nome_clinica.text().strip())
        email_config.set("telefone", self.input_telefone.text().strip())
        email_config.set("endereco", self.input_endereco.text().strip())
        email_config.set("horario_semana", self.input_horario_semana.text().strip())
        email_config.set("horario_sabado", self.input_horario_sabado.text().strip())
        email_config.set("whatsapp", self.input_whatsapp.text().strip())
        
        email_config.set("assinatura", self.input_assinatura.toPlainText().strip())
        
        if email_config.save_config():
            BiodeskMessageBox.information(self, "Sucesso", "✅ Configuração guardada com sucesso!")
            self.accept()
        else:
            BiodeskMessageBox.critical(self, "Erro", "❌ Erro ao guardar configuração!")
    
    def testar_conexao(self):
        """Testa conexão com servidor SMTP"""
        # Guardar configuração temporariamente
        temp_config = email_config.config.copy()
        
        email_config.set("smtp_server", self.input_smtp_server.text().strip())
        email_config.set("smtp_port", self.input_smtp_port.value())
        email_config.set("use_tls", self.check_use_tls.isChecked())
        email_config.set("email", self.input_email.text().strip())
        email_config.set("password", self.input_password.text().strip())
        
        # Testar conexão
        self.thread_test = TestEmailThread()
        self.thread_test.resultado.connect(self.mostrar_resultado_teste)
        self.thread_test.start()
        
        # Mostrar progresso
        BiodeskMessageBox.information(self, "Testando", "🔄 Testando conexão... Aguarde.")
    
    def mostrar_resultado_teste(self, sucesso, mensagem):
        """Mostra resultado do teste"""
        if sucesso:
            BiodeskMessageBox.information(self, "Teste de Conexão", f"✅ {mensagem}")
        else:
            BiodeskMessageBox.warning(self, "Teste de Conexão", f"❌ {mensagem}")
