import os
import sys
import sqlite3
import csv
import time
import random
from datetime import datetime, date
from pathlib import Path
from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap`nfrom biodesk_dialogs import BiodeskMessageBox
    from email_config import email_config
    from email_sender import email_sender
import sys
import sqlite3
import csv
import time
import random
from datetime import datetime, date
from pathlib import Path
from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap`nfrom biodesk_dialogs import BiodeskMessageBox
    from email_config import email_config
    from email_sender import email_sender
            from email_config_window import EmailConfigWindow
import random
from biodesk_ui_kit import BiodeskUIKit
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget do Centro de Comunicação para Biodesk
Sistema de comunicação via Email
"""


    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QFileDialog, 
    QProgressBar, QTableWidget, QTableWidgetItem, QTabWidget, 
    QGroupBox, QFormLayout, QSpinBox, QCheckBox, QListWidget, 
    QListWidgetItem, QSplitter, QFrame, QScrollArea, QDialog
)

try:
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("Sistema de email não disponível - usando modo simulação")


class CentroComunicacaoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
                    if sucesso:
                        BiodeskMessageBox.information(
                            self,
                            "Email Enviado",
                            f"✅ Email enviado com sucesso para {nome}!\n\n"
                            f"📧 Destinatário: {email}"
                        )
                        estado = "enviado"
                    else:
                        BiodeskMessageBox.warning(
                            self,
                            "Erro no Envio",
                            f"❌ Erro ao enviar email:\n\n{mensagem_resultado}"
                        )
                        estado = "erro"
                        
                except Exception as e:
                    BiodeskMessageBox.critical(
                        self,
                        "Erro",
                        f"❌ Erro inesperado:\n\n{str(e)}"
                    )
                    estado = "erro"
            else:
                return
        else:
            # Simulação de envio
            BiodeskMessageBox.information(
                self,
                "Email Simulado",
                f"✅ Email simulado enviado para {nome}!\n\n"
                f"📧 Email: {email}\n"
                f"📞 Telefone: {telefone}\n\n"
                "💡 Esta é uma simulação. Para envios reais,\n"
                "configure o email clicando em '⚙️ Configurar Email'."
            )
            estado = "simulado"
        
        # Registrar na base de dados
        self.registrar_envio(nome, email, "email", mensagem, estado, None, "Envio rápido")g.clicked.connect(self.abrir_configuracao_email)
        BiodeskUIKit.apply_universal_button_style(btn_config)
        
        # Status do email
        self.label_status_email = QLabel("📧 Email não configurado")
        self.label_status_email.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.atualizar_status_email()
        
        layout_config.addWidget(btn_config)
        layout_config.addStretch()
        layout_config.addWidget(self.label_status_email)
        
        layout.addLayout(layout_config)rt os

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QFileDialog, 
    QProgressBar, QTableWidget, QTableWidgetItem, QTabWidget, 
    QGroupBox, QFormLayout, QSpinBox, QCheckBox, QListWidget, 
    QListWidgetItem, QSplitter, QFrame, QScrollArea, QDialog
)

try:
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("Sistema de email não disponível - usando modo simulação")

class ComunicacaoThread(QThread):
    """Thread para processamento de comunicações por email"""
    progresso_atualizado = pyqtSignal(int, str)
    envio_concluido = pyqtSignal(str, str, str, bool)
    processamento_finalizado = pyqtSignal(int, int)
    
    def __init__(self, pacientes, canal, mensagem, modo_simulacao=True, assunto=""):
        super().__init__()
        self.pacientes = pacientes
        self.canal = canal  # Sempre será "email"
        self.mensagem = mensagem
        self.assunto = assunto
        self.modo_simulacao = modo_simulacao
        self.pausado = False
        
    def run(self):
        sucessos = 0
        erros = 0
        
        for i, paciente in enumerate(self.pacientes):
            if self.pausado:
                break
                
            nome = paciente.get('nome', 'N/A')
            email = paciente.get('email', '')
            
            # Atualizar progresso
            self.progresso_atualizado.emit(
                int((i + 1) / len(self.pacientes) * 100),
                f"Enviando email para {nome}..."
            )
            
            # Simular envio ou envio real
            if self.modo_simulacao or not EMAIL_AVAILABLE:
                # Simulação - 95% de sucesso
                time.sleep(1)  # Simular tempo de processamento
                sucesso = random.random() > 0.05
                if sucesso:
                    self.envio_concluido.emit(nome, email, "✅ Email simulado com sucesso", True)
                    sucessos += 1
                else:
                    self.envio_concluido.emit(nome, email, "❌ Erro simulado", False)
                    erros += 1
            else:
                # Envio real de email
                try:
                    sucesso, mensagem_resultado = email_sender.send_email(
                        email, self.assunto, self.mensagem, nome
                    )
                    
                    if sucesso:
                        self.envio_concluido.emit(nome, email, "✅ Email enviado com sucesso", True)
                        sucessos += 1
                    else:
                        self.envio_concluido.emit(nome, email, f"❌ {mensagem_resultado}", False)
                        erros += 1
                        
                except Exception as e:
                    self.envio_concluido.emit(nome, email, f"❌ Erro: {str(e)}", False)
                    erros += 1
                
                # Pequena pausa entre envios para evitar spam
                time.sleep(2)
                
        self.processamento_finalizado.emit(sucessos, erros)

class CentroComunicacaoWidget(QWidget):
    """Widget principal do Centro de Comunicação"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pacientes_carregados = []
        self.thread_comunicacao = None
        self.db_path = "comunicacao_biodesk.db"
        self.init_database()
        self.init_ui()
        
    def init_database(self):
        """Inicializa a base de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de envios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS envios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL,
                    telefone TEXT,
                    canal TEXT NOT NULL DEFAULT 'email',
                    assunto TEXT,
                    mensagem TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    erro TEXT,
                    template_usado TEXT
                )
            ''')
            
            conn.commit()
    
    def init_ui(self):
        """Inicializa a interface"""
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("� Centro de Comunicação - Email")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(titulo)
        
        # Criar abas
        tabs = QTabWidget()
        
        # Aba 1: Envio Rápido
        tab_envio = self.criar_aba_envio_rapido()
        tabs.addTab(tab_envio, "📤 Envio Rápido")
        
        # Aba 2: Envio em Massa (CSV)
        tab_massa = self.criar_aba_envio_massa()
        tabs.addTab(tab_massa, "📋 Envio em Massa")
        
        # Aba 3: Histórico
        tab_historico = self.criar_aba_historico()
        tabs.addTab(tab_historico, "📊 Histórico")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
    def criar_aba_envio_rapido(self):
        """Cria a aba de envio rápido"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Grupo de destinatário
        grupo_dest = QGroupBox("👤 Destinatário")
        form_dest = QFormLayout()
        
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome do paciente")
        form_dest.addRow("Nome:", self.input_nome)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("email@exemplo.com")
        form_dest.addRow("Email:", self.input_email)
        
        self.input_numero = QLineEdit()
        self.input_numero.setPlaceholderText("+351 XXX XXX XXX")
        form_dest.addRow("Telefone:", self.input_numero)
        
        grupo_dest.setLayout(form_dest)
        layout.addWidget(grupo_dest)
        
        # Grupo de mensagem
        grupo_msg = QGroupBox("✉️ Mensagem")
        layout_msg = QVBoxLayout()
        
        self.input_mensagem = QTextEdit()
        self.input_mensagem.setPlaceholderText("Digite sua mensagem aqui...")
        self.input_mensagem.setMaximumHeight(150)
        layout_msg.addWidget(self.input_mensagem)
        
        # Templates rápidos
        layout_templates = QHBoxLayout()
        
        btn_template_consulta = QPushButton("📅 Lembrete de Consulta")
        btn_template_consulta.clicked.connect(self.aplicar_template_consulta)
        
        btn_template_resultado = QPushButton("📋 Resultado de Exame")
        btn_template_resultado.clicked.connect(self.aplicar_template_resultado)
        
        btn_template_boas_vindas = QPushButton("👋 Boas-vindas")
        btn_template_boas_vindas.clicked.connect(self.aplicar_template_boas_vindas)
        
        layout_templates.addWidget(btn_template_consulta)
        layout_templates.addWidget(btn_template_resultado)
        layout_templates.addWidget(btn_template_boas_vindas)
        layout_msg.addLayout(layout_templates)
        
        grupo_msg.setLayout(layout_msg)
        layout.addWidget(grupo_msg)
        
        # Botão de envio
        self.btn_enviar_rapido = QPushButton("🚀 Enviar Mensagem")
        self.BiodeskUIKit.apply_universal_button_style(btn_enviar_rapido)
        self.btn_enviar_rapido.clicked.connect(self.enviar_mensagem_rapida)
        layout.addWidget(self.btn_enviar_rapido)
        
        widget.setLayout(layout)
        return widget
        
    def criar_aba_envio_massa(self):
        """Cria a aba de envio em massa"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Seleção de arquivo CSV
        grupo_csv = QGroupBox("📁 Arquivo de Pacientes")
        layout_csv = QVBoxLayout()
        
        layout_arquivo = QHBoxLayout()
        self.input_arquivo_csv = QLineEdit()
        self.input_arquivo_csv.setPlaceholderText("Selecione um arquivo CSV...")
        self.input_arquivo_csv.setReadOnly(True)
        
        btn_selecionar = QPushButton("📂 Selecionar CSV")
        btn_selecionar.clicked.connect(self.selecionar_arquivo_csv)
        
        layout_arquivo.addWidget(self.input_arquivo_csv)
        layout_arquivo.addWidget(btn_selecionar)
        layout_csv.addLayout(layout_arquivo)
        
        # Informações sobre formato CSV
        info_csv = QLabel("""
        📝 <b>Formato do CSV:</b><br>
        • Colunas obrigatórias: <code>nome</code>, <code>email</code><br>
        • Coluna opcional: <code>telefone</code><br>
        • Formato de email: usuario@dominio.com<br>
        • Exemplo: nome,email,telefone<br>
        • João Silva,joao@email.com,+351912345678
        """)
        info_csv.setStyleSheet("color: #666; font-size: 11px; margin: 5px;")
        layout_csv.addWidget(info_csv)
        
        grupo_csv.setLayout(layout_csv)
        layout.addWidget(grupo_csv)
        
        # Preview dos pacientes
        self.tabela_pacientes = QTableWidget()
        self.tabela_pacientes.setColumnCount(4)
        self.tabela_pacientes.setHorizontalHeaderLabels(["Nome", "Email", "Telefone", "Status"])
        self.tabela_pacientes.setMaximumHeight(200)
        layout.addWidget(QLabel("👥 Pacientes carregados:"))
        layout.addWidget(self.tabela_pacientes)
        
        # Configurações de envio
        grupo_config = QGroupBox("⚙️ Configurações de Email")
        form_config = QFormLayout()
        
        self.input_assunto = QLineEdit()
        self.input_assunto.setPlaceholderText("Assunto do email")
        form_config.addRow("Assunto:", self.input_assunto)
        
        self.input_mensagem_massa = QTextEdit()
        self.input_mensagem_massa.setPlaceholderText("Digite a mensagem para todos os pacientes...")
        self.input_mensagem_massa.setMaximumHeight(100)
        form_config.addRow("Mensagem:", self.input_mensagem_massa)
        
        self.check_simulacao = QCheckBox("Modo simulação (não envia realmente)")
        self.check_simulacao.setChecked(True)
        form_config.addRow("", self.check_simulacao)
        
        grupo_config.setLayout(form_config)
        layout.addWidget(grupo_config)
        
        # Progresso e controles
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.label_status = QLabel("")
        layout.addWidget(self.label_status)
        
        # Botões
        layout_botoes = QHBoxLayout()
        
        self.btn_processar = QPushButton("🚀 Processar Envios")
        self.btn_processar.setEnabled(False)
        self.btn_processar.clicked.connect(self.processar_envios_massa)
        self.BiodeskUIKit.apply_universal_button_style(btn_processar)
        
        self.btn_parar = QPushButton("⏸️ Parar")
        self.btn_parar.setEnabled(False)
        self.btn_parar.clicked.connect(self.parar_processamento)
        
        layout_botoes.addWidget(self.btn_processar)
        layout_botoes.addWidget(self.btn_parar)
        layout.addLayout(layout_botoes)
        
        widget.setLayout(layout)
        return widget
        
    def criar_aba_historico(self):
        """Cria a aba de histórico"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Estatísticas
        grupo_stats = QGroupBox("📊 Estatísticas")
        layout_stats = QHBoxLayout()
        
        self.label_total_envios = QLabel("Total: 0")
        self.label_email_envios = QLabel("Emails: 0")
        self.label_email_sucessos = QLabel("Sucessos: 0")
        
        layout_stats.addWidget(self.label_total_envios)
        layout_stats.addWidget(self.label_email_envios)
        layout_stats.addWidget(self.label_email_sucessos)
        
        grupo_stats.setLayout(layout_stats)
        layout.addWidget(grupo_stats)
        
        # Tabela de histórico
        self.tabela_historico = QTableWidget()
        self.tabela_historico.setColumnCount(6)
        self.tabela_historico.setHorizontalHeaderLabels([
            "Data/Hora", "Nome", "Email", "Assunto", "Estado", "Mensagem"
        ])
        layout.addWidget(QLabel("📋 Histórico de Envios:"))
        layout.addWidget(self.tabela_historico)
        
        # Botão atualizar
        btn_atualizar = QPushButton("🔄 Atualizar Histórico")
        btn_atualizar.clicked.connect(self.carregar_historico)
        layout.addWidget(btn_atualizar)
        
        widget.setLayout(layout)
        return widget
    
    def aplicar_template_consulta(self):
        """Aplica template de lembrete de consulta via email"""
        assunto = "Lembrete de Consulta - {nome}"
        template = """Caro(a) {nome},

Esperamos que se encontre bem!

🏥 LEMBRETE DA SUA CONSULTA

📅 Data: [DATA]
🕐 Hora: [HORA]
👨‍⚕️ Profissional: Dr./Dra. [MÉDICO]
📍 Local: [ENDEREÇO_CLÍNICA]

Por favor, confirme a sua presença respondendo a este email ou contactando-nos pelo telefone [TELEFONE].

📋 Recomendações para a consulta:
• Chegue 15 minutos antes da hora marcada
• Traga documentos de identificação
• Traga exames anteriores, se aplicável

Agradecemos a sua preferência.

Com os melhores cumprimentos,
Equipa [NOME_CLÍNICA]
📞 [TELEFONE] | 📧 [EMAIL]"""
        
        self.input_assunto.setText(assunto)
        self.input_mensagem.setPlainText(template)
    
    def aplicar_template_resultado(self):
        """Aplica template de resultado de exame via email"""
        assunto = "Resultados de Exame Disponíveis - {nome}"
        template = """Caro(a) {nome},

Esperamos que se encontre bem!

📋 RESULTADOS DE EXAME PRONTOS

Os seus resultados de exame já estão disponíveis.

🏥 Para recolher os resultados:
📍 Visite a nossa receção durante o horário de funcionamento
🕐 Segunda a Sexta: [HORÁRIO]
📞 Ou contacte-nos para agendar uma consulta de discussão dos resultados

👨‍⚕️ IMPORTANTE:
Se desejar uma consulta para discussão detalhada dos resultados com o médico, por favor agende através do nosso contacto.

📞 Contactos:
Telefone: [TELEFONE]
Email: [EMAIL]
WhatsApp: [WHATSAPP]

Obrigado pela sua confiança nos nossos serviços.

Com os melhores cumprimentos,
Equipa [NOME_CLÍNICA]"""
        
        self.input_assunto.setText(assunto)
        self.input_mensagem.setPlainText(template)
    
    def aplicar_template_boas_vindas(self):
        """Aplica template de boas-vindas para novos pacientes"""
        assunto = "Bem-vindo(a) à {nome_clinica} - {nome}"
        template = """Caro(a) {nome},

É com grande satisfação que damos as boas-vindas à [NOME_CLÍNICA]!

👋 BEM-VINDO(A) À NOSSA CLÍNICA

Agradecemos por ter escolhido os nossos serviços de saúde. O nosso compromisso é oferecer-lhe o melhor cuidado e acompanhamento personalizado.

🏥 INFORMAÇÕES IMPORTANTES:

📞 Contactos:
• Telefone: [TELEFONE]
• Email: [EMAIL]
• WhatsApp: [WHATSAPP]

🕐 Horário de Funcionamento:
• Segunda a Sexta: [HORÁRIO_SEMANA]
• Sábado: [HORÁRIO_SABADO]

📍 Morada:
[ENDEREÇO_COMPLETO]

📋 PARA MARCAÇÕES:
• Telefone durante horário de funcionamento
• Email (resposta em 24h)
• WhatsApp para marcações urgentes

💡 DICAS IMPORTANTES:
• Chegue sempre 15 minutos antes da consulta
• Traga documento de identificação
• Informe sobre alergias ou medicação atual
• Traga exames anteriores, se aplicável

Estamos ansiosos por cuidar da sua saúde!

Com os melhores cumprimentos,
Equipa [NOME_CLÍNICA]"""
        
        self.input_assunto.setText(assunto)
        self.input_mensagem.setPlainText(template)
    
    def selecionar_arquivo_csv(self):
        """Seleciona arquivo CSV"""
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo CSV",
            "",
            "Arquivos CSV (*.csv);;Todos os arquivos (*)"
        )
        
        if arquivo:
            self.input_arquivo_csv.setText(arquivo)
            self.carregar_pacientes_csv(arquivo)
    
    def carregar_pacientes_csv(self, arquivo):
        """Carrega pacientes do arquivo CSV"""
        try:
            self.pacientes_carregados = []
            
            with open(arquivo, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'nome' in row and 'email' in row:
                        self.pacientes_carregados.append({
                            'nome': row['nome'].strip(),
                            'email': row['email'].strip(),
                            'telefone': row.get('telefone', '').strip()
                        })
            
            # Atualizar tabela
            self.atualizar_tabela_pacientes()
            
            # Habilitar botão processar
            self.btn_processar.setEnabled(len(self.pacientes_carregados) > 0)
            
            BiodeskMessageBox.information(
                self,
                "CSV Carregado",
                f"✅ {len(self.pacientes_carregados)} pacientes carregados com sucesso!"
            )
            
        except Exception as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar CSV:\n\n{str(e)}"
            )
    
    def atualizar_tabela_pacientes(self):
        """Atualiza a tabela de pacientes"""
        self.tabela_pacientes.setRowCount(len(self.pacientes_carregados))
        
        for i, paciente in enumerate(self.pacientes_carregados):
            self.tabela_pacientes.setItem(i, 0, QTableWidgetItem(paciente['nome']))
            self.tabela_pacientes.setItem(i, 1, QTableWidgetItem(paciente['email']))
            self.tabela_pacientes.setItem(i, 2, QTableWidgetItem(paciente.get('telefone', '')))
            self.tabela_pacientes.setItem(i, 3, QTableWidgetItem("⏳ Aguardando"))
    
    def enviar_mensagem_rapida(self):
        """Envia mensagem rápida"""
        nome = self.input_nome.text().strip()
        email = self.input_email.text().strip()
        telefone = self.input_numero.text().strip()
        mensagem = self.input_mensagem.toPlainText().strip()
        
        if not nome or not email or not mensagem:
            BiodeskMessageBox.warning(self, "Dados Incompletos", "Preencha pelo menos Nome, Email e Mensagem!")
            return
        
        # Simulação de envio
        BiodeskMessageBox.information(
            self,
            "Email Enviado",
            f"✅ Email simulado enviado para {nome}!\n\n"
            f"� Email: {email}\n"
            f"📞 Telefone: {telefone}\n\n"
            "💡 Esta é uma simulação. Para envios reais,\n"
            "configure as credenciais de email no sistema."
        )
        
        # Registrar na base de dados
        self.registrar_envio(nome, email, "email", mensagem, "simulado", None, "Envio rápido")
        
        # Limpar campos
        self.input_nome.clear()
        self.input_email.clear()
        self.input_numero.clear()
        self.input_mensagem.clear()
    
    def processar_envios_massa(self):
        """Processa envios em massa"""
        if not self.pacientes_carregados:
            BiodeskMessageBox.warning(self, "Nenhum Paciente", "Carregue um arquivo CSV primeiro!")
            return
        
        mensagem = self.input_mensagem_massa.toPlainText().strip()
        assunto = self.input_assunto.text().strip()
        
        if not mensagem or not assunto:
            BiodeskMessageBox.warning(self, "Dados Incompletos", "Digite o assunto e a mensagem!")
            return
        
        modo_simulacao = self.check_simulacao.isChecked()
        
        # Configurar interface
        self.btn_processar.setEnabled(False)
        self.btn_parar.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Iniciar thread
        self.thread_comunicacao = ComunicacaoThread(
            self.pacientes_carregados, "email", mensagem, modo_simulacao, assunto
        )
        self.thread_comunicacao.progresso_atualizado.connect(self.atualizar_progresso)
        self.thread_comunicacao.envio_concluido.connect(self.processar_envio_concluido)
        self.thread_comunicacao.processamento_finalizado.connect(self.finalizar_processamento)
        self.thread_comunicacao.start()
    
    def atualizar_progresso(self, valor, texto):
        """Atualiza barra de progresso"""
        self.progress_bar.setValue(valor)
        self.label_status.setText(texto)
    
    def processar_envio_concluido(self, nome, numero, resultado, sucesso):
        """Processa envio concluído"""
        # Atualizar tabela
        for i in range(self.tabela_pacientes.rowCount()):
            if self.tabela_pacientes.item(i, 0).text() == nome:
                self.tabela_pacientes.setItem(i, 2, QTableWidgetItem(resultado))
                break
    
    def finalizar_processamento(self, sucessos, erros):
        """Finaliza processamento"""
        self.btn_processar.setEnabled(True)
        self.btn_parar.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        BiodeskMessageBox.information(
            self,
            "Processamento Concluído",
            f"✅ Processamento finalizado!\n\n"
            f"🟢 Sucessos: {sucessos}\n"
            f"🔴 Erros: {erros}\n\n"
            f"📊 Total processado: {sucessos + erros}"
        )
        
        self.label_status.setText("✅ Processamento concluído!")
    
    def parar_processamento(self):
        """Para o processamento"""
        if self.thread_comunicacao:
            self.thread_comunicacao.pausado = True
            self.btn_parar.setEnabled(False)
            self.label_status.setText("⏸️ Parando...")
    
    def registrar_envio(self, nome, email, canal, mensagem, estado, erro=None, assunto=None):
        """Registra envio na base de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO envios (nome, email, canal, mensagem, estado, erro, assunto)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, email, canal, mensagem, estado, erro, assunto))
            conn.commit()
    
    def carregar_historico(self):
        """Carrega histórico de envios"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_envio, nome, email, assunto, estado, mensagem
                FROM envios
                ORDER BY data_envio DESC
                LIMIT 100
            ''')
            envios = cursor.fetchall()
        
        self.tabela_historico.setRowCount(len(envios))
        
        for i, envio in enumerate(envios):
            for j, valor in enumerate(envio):
                self.tabela_historico.setItem(i, j, QTableWidgetItem(str(valor)))
        
        # Atualizar estatísticas
        self.atualizar_estatisticas()
    
    def atualizar_estatisticas(self):
        """Atualiza estatísticas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM envios")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM envios WHERE canal = 'email'")
            emails = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM envios WHERE canal = 'email' AND estado = 'enviado'")
            sucessos = cursor.fetchone()[0]
        
        self.label_total_envios.setText(f"Total: {total}")
        self.label_email_envios.setText(f"Emails: {emails}")
        self.label_email_sucessos.setText(f"Sucessos: {sucessos}")
    
    def abrir_configuracao_email(self):
        """Abre janela de configuração de email"""
        if not EMAIL_AVAILABLE:
            BiodeskMessageBox.warning(
                self,
                "Sistema Indisponível",
                "Sistema de email não está disponível.\n"
                "Verifique se os módulos necessários estão instalados."
            )
            return
        
        try:
            
            config_window = EmailConfigWindow(self)
            if config_window.exec() == QDialog.DialogCode.Accepted:
                self.atualizar_status_email()
                BiodeskMessageBox.information(
                    self,
                    "Configuração",
                    "✅ Configuração de email atualizada!\n\n"
                    "Agora pode usar o modo real de envio."
                )
        except ImportError as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"Erro ao importar janela de configuração:\n{str(e)}"
            )
    
    def atualizar_status_email(self):
        """Atualiza status da configuração de email"""
        if not EMAIL_AVAILABLE:
            self.label_status_email.setText("📧 Sistema indisponível")
            self.label_status_email.setStyleSheet("color: #dc3545; font-weight: bold;")
            return
        
        if email_config.is_configured():
            self.label_status_email.setText("📧 Email configurado")
            self.label_status_email.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.label_status_email.setText("📧 Email não configurado")
            self.label_status_email.setStyleSheet("color: #dc3545; font-weight: bold;")

# Importar random para simulação
