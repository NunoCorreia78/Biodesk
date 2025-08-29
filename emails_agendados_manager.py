"""
📧 Interface de Gestão de Emails Agendados
Permite visualizar, agendar, editar e cancelar emails agendados
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QDialog, QDateTimeEdit,
    QLineEdit, QTextEdit, QComboBox, QMessageBox, QHeaderView,
    QFrame, QSplitter, QGroupBox, QGridLayout, QSpacerItem,
    QSizePolicy, QFileDialog, QListWidget, QListWidgetItem,
    QMainWindow
)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os
from email_scheduler import get_email_scheduler


class EmailAgendamentoDialog(QDialog):
    """Dialog para agendar/editar emails"""
    
    def __init__(self, parent=None, email_data=None):
        super().__init__(parent)
        self.email_data = email_data or {}
        self.anexos_selecionados = []
        
        self.setWindowTitle("📅 Agendar Email" if not email_data else "✏️ Editar Email Agendado")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.carregar_dados()
    
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📅 Novo Email Agendado" if not self.email_data else "✏️ Editar Email Agendado")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Separador
        linha = QFrame()
        linha.setFrameShape(QFrame.Shape.HLine)
        linha.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(linha)
        
        # Formulário
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        
        # Paciente
        form_layout.addWidget(QLabel("👤 Paciente:"), 0, 0)
        self.combo_paciente = QComboBox()
        self.combo_paciente.setEditable(True)
        self.carregar_pacientes()
        form_layout.addWidget(self.combo_paciente, 0, 1)
        
        # Email destinatário
        form_layout.addWidget(QLabel("📧 Email:"), 1, 0)
        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("email@exemplo.com")
        form_layout.addWidget(self.edit_email, 1, 1)
        
        # Assunto
        form_layout.addWidget(QLabel("📝 Assunto:"), 2, 0)
        self.edit_assunto = QLineEdit()
        self.edit_assunto.setPlaceholderText("Assunto do email")
        form_layout.addWidget(self.edit_assunto, 2, 1)
        
        # Data e hora de envio
        form_layout.addWidget(QLabel("🕒 Enviar em:"), 3, 0)
        self.datetime_envio = QDateTimeEdit()
        self.datetime_envio.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # +1 hora
        self.datetime_envio.setDisplayFormat("dd/MM/yyyy hh:mm")
        self.datetime_envio.setCalendarPopup(True)
        form_layout.addWidget(self.datetime_envio, 3, 1)
        
        layout.addWidget(form_widget)
        
        # Mensagem
        msg_group = QGroupBox("💬 Mensagem")
        msg_layout = QVBoxLayout(msg_group)
        
        self.edit_mensagem = QTextEdit()
        self.edit_mensagem.setPlaceholderText("Conteúdo do email...")
        self.edit_mensagem.setMaximumHeight(120)
        msg_layout.addWidget(self.edit_mensagem)
        
        layout.addWidget(msg_group)
        
        # Anexos
        anexos_group = QGroupBox("📎 Anexos")
        anexos_layout = QVBoxLayout(anexos_group)
        
        anexos_buttons = QHBoxLayout()
        btn_adicionar_anexo = QPushButton("➕ Adicionar Arquivo")
        btn_adicionar_anexo.clicked.connect(self.adicionar_anexo)
        btn_remover_anexo = QPushButton("➖ Remover")
        btn_remover_anexo.clicked.connect(self.remover_anexo)
        
        anexos_buttons.addWidget(btn_adicionar_anexo)
        anexos_buttons.addWidget(btn_remover_anexo)
        anexos_buttons.addStretch()
        anexos_layout.addLayout(anexos_buttons)
        
        self.lista_anexos = QListWidget()
        self.lista_anexos.setMaximumHeight(80)
        anexos_layout.addWidget(self.lista_anexos)
        
        layout.addWidget(anexos_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        btn_agendar = QPushButton("📅 Agendar" if not self.email_data else "💾 Salvar")
        btn_agendar.clicked.connect(self.agendar_email)
        btn_agendar.setDefault(True)
        
        buttons_layout.addWidget(btn_cancelar)
        buttons_layout.addWidget(btn_agendar)
        
        layout.addLayout(buttons_layout)
    
    def carregar_pacientes(self):
        """Carregar lista de pacientes do sistema"""
        try:
            # Tentar carregar pacientes do sistema
            if os.path.exists("pacientes.db"):
                import sqlite3
                conn = sqlite3.connect("pacientes.db")
                cursor = conn.cursor()
                cursor.execute("SELECT nome, email FROM pacientes ORDER BY nome")
                pacientes = cursor.fetchall()
                conn.close()
                
                for nome, email in pacientes:
                    texto = f"{nome}"
                    if email:
                        texto += f" ({email})"
                    self.combo_paciente.addItem(texto)
            
        except Exception as e:
            print(f"❌ Erro ao carregar pacientes: {e}")
    
    def adicionar_anexo(self):
        """Adicionar arquivo anexo"""
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo",
            "",
            "Todos os Arquivos (*.*)"
        )
        
        if arquivo:
            self.anexos_selecionados.append(arquivo)
            nome_arquivo = os.path.basename(arquivo)
            item = QListWidgetItem(f"📄 {nome_arquivo}")
            item.setData(Qt.ItemDataRole.UserRole, arquivo)
            self.lista_anexos.addItem(item)
    
    def remover_anexo(self):
        """Remover arquivo anexo selecionado"""
        item_atual = self.lista_anexos.currentItem()
        if item_atual:
            arquivo = item_atual.data(Qt.ItemDataRole.UserRole)
            if arquivo in self.anexos_selecionados:
                self.anexos_selecionados.remove(arquivo)
            
            row = self.lista_anexos.row(item_atual)
            self.lista_anexos.takeItem(row)
    
    def carregar_dados(self):
        """Carregar dados do email para edição"""
        if not self.email_data:
            return
        
        # Preencher campos
        if self.email_data.get("paciente_nome"):
            self.combo_paciente.setCurrentText(self.email_data["paciente_nome"])
        
        if self.email_data.get("destinatario"):
            self.edit_email.setText(self.email_data["destinatario"])
        
        if self.email_data.get("assunto"):
            self.edit_assunto.setText(self.email_data["assunto"])
        
        if self.email_data.get("mensagem"):
            self.edit_mensagem.setPlainText(self.email_data["mensagem"])
        
        if self.email_data.get("data_envio"):
            try:
                dt = datetime.strptime(self.email_data["data_envio"], "%Y-%m-%d %H:%M:%S")
                self.datetime_envio.setDateTime(QDateTime.fromSecsSinceEpoch(int(dt.timestamp())))
            except:
                pass
        
        # Carregar anexos
        anexos = self.email_data.get("anexos", [])
        for anexo in anexos:
            if os.path.exists(anexo):
                self.anexos_selecionados.append(anexo)
                nome = os.path.basename(anexo)
                item = QListWidgetItem(f"📄 {nome}")
                item.setData(Qt.ItemDataRole.UserRole, anexo)
                self.lista_anexos.addItem(item)
    
    def agendar_email(self):
        """Processar agendamento do email"""
        # Validar campos obrigatórios
        if not self.edit_email.text().strip():
            QMessageBox.warning(self, "Aviso", "📧 Email é obrigatório!")
            return
        
        if not self.edit_assunto.text().strip():
            QMessageBox.warning(self, "Aviso", "📝 Assunto é obrigatório!")
            return
        
        # Validar data
        data_envio = self.datetime_envio.dateTime().toPython()
        if data_envio <= datetime.now():
            QMessageBox.warning(self, "Aviso", "🕒 Data de envio deve ser no futuro!")
            return
        
        # Preparar dados
        dados_email = {
            "paciente_nome": self.combo_paciente.currentText().split(" (")[0],
            "paciente_id": self.combo_paciente.currentText(),  # Simplificado
            "destinatario": self.edit_email.text().strip(),
            "assunto": self.edit_assunto.text().strip(),
            "mensagem": self.edit_mensagem.toPlainText(),
            "data_envio": data_envio.strftime("%Y-%m-%d %H:%M:%S"),
            "anexos": self.anexos_selecionados.copy()
        }
        
        # Salvar dados para uso posterior
        self.dados_finais = dados_email
        
        self.accept()


class EmailsAgendadosWidget(QWidget):
    """Widget principal para gestão de emails agendados"""
    
    # Sinais
    email_agendado = pyqtSignal(dict)
    email_cancelado = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Referência ao scheduler
        self.scheduler = get_email_scheduler()
        
        # Conectar sinais do scheduler
        self.scheduler.email_enviado.connect(self.on_email_enviado)
        self.scheduler.email_falhado.connect(self.on_email_falhado)
        self.scheduler.status_atualizado.connect(self.on_status_atualizado)
        
        # Timer para atualização automática
        self.timer_atualizacao = QTimer()
        self.timer_atualizacao.timeout.connect(self.atualizar_tabela)
        self.timer_atualizacao.start(30000)  # Atualizar a cada 30 segundos
        
        self.setup_ui()
        self.atualizar_tabela()
        
        # Iniciar scheduler se não estiver ativo
        if not self.scheduler.ativo:
            self.scheduler.iniciar()
    
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        titulo = QLabel("📧 Gestão de Emails Agendados")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(titulo)
        
        header_layout.addStretch()
        
        # Status do scheduler
        self.label_status = QLabel("⏸️ Scheduler Parado")
        self.label_status.setStyleSheet("color: #666; font-weight: bold;")
        header_layout.addWidget(self.label_status)
        
        layout.addLayout(header_layout)
        
        # Botões de ação (apenas Cancelar e Atualizar)
        buttons_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.cancelar_email)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #ddd;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
            }
        """)
        
        btn_atualizar = QPushButton("� Verificar e Atualizar")
        btn_atualizar.clicked.connect(self.atualizar_tabela)
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #ddd;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81c784;
                color: white;
            }
        """)
        
        buttons_layout.addWidget(btn_cancelar)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_atualizar)
        
        layout.addLayout(buttons_layout)
        
        # Tabela de emails com visual melhorado
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setWordWrap(True)  # Habilitar quebra de linha automática
        self.tabela.setTextElideMode(Qt.TextElideMode.ElideNone)  # Não cortar texto
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabela.setShowGrid(False)  # Remover linhas de grade
        self.tabela.setWordWrap(True)   # Quebra de linha automática
        
        # Estilo visual melhorado similar à imagem
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f0f0f0;
                border-right: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTableWidget::item:hover {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #fafafa;
                color: #424242;
                font-weight: bold;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        # Configurar colunas (sem cabeçalho visível)
        colunas = [
            "📅 Data Agendamento", "👤 Paciente", "📧 Email", 
            "📝 Assunto", "📎 Anexos", "🔄 Status"
        ]
        self.tabela.setColumnCount(len(colunas))
        self.tabela.setHorizontalHeaderLabels(colunas)
        
        # Ocultar cabeçalho da tabela
        self.tabela.horizontalHeader().setVisible(False)
        
        # Configurar altura das linhas como automática/adaptável
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Ajustar largura das colunas para melhor visualização
        header = self.tabela.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Data
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Paciente
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Email
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Assunto
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Anexos
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Status
        
        # Altura das linhas para melhor visualização
        self.tabela.verticalHeader().setDefaultSectionSize(50)
        self.tabela.verticalHeader().setVisible(False)  # Esconder números das linhas
        
        layout.addWidget(self.tabela)
        
        # Estatísticas
        stats_layout = QHBoxLayout()
        
        self.label_total = QLabel("Total: 0")
        self.label_agendados = QLabel("📅 Agendados: 0")
        self.label_enviados = QLabel("✅ Enviados: 0")
        self.label_cancelados = QLabel("❌ Cancelados: 0")
        self.label_falhados = QLabel("⚠️ Falhados: 0")
        self.label_ultimo_check = QLabel("Última verificação: Nunca")
        
        for label in [self.label_total, self.label_agendados, self.label_enviados, 
                     self.label_cancelados, self.label_falhados]:
            label.setStyleSheet("font-weight: bold; margin: 5px;")
        
        self.label_ultimo_check.setStyleSheet("color: #666; margin: 5px;")
        
        stats_layout.addWidget(self.label_total)
        stats_layout.addWidget(QLabel("|"))
        stats_layout.addWidget(self.label_agendados)
        stats_layout.addWidget(self.label_enviados)
        stats_layout.addWidget(self.label_cancelados)
        stats_layout.addWidget(self.label_falhados)
        stats_layout.addStretch()
        stats_layout.addWidget(self.label_ultimo_check)
        
        layout.addLayout(stats_layout)
    
    def novo_email(self):
        """Abrir dialog para novo email"""
        dialog = EmailAgendamentoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dados = dialog.dados_finais
            
            # Agendar via scheduler
            email_id = self.scheduler.agendar_email(dados)
            
            if email_id:
                QMessageBox.information(self, "Sucesso", "📅 Email agendado com sucesso!")
                self.atualizar_tabela()
                self.email_agendado.emit(dados)
            else:
                QMessageBox.critical(self, "Erro", "❌ Erro ao agendar email!")
    
    def editar_email(self):
        """Editar email selecionado"""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um email para editar!")
            return
        
        email_id = self.tabela.item(row, 0).data(Qt.ItemDataRole.UserRole)
        emails = self.scheduler.obter_emails_agendados()
        
        email_data = None
        for email in emails:
            if email.get("id") == email_id:
                email_data = email
                break
        
        if not email_data:
            QMessageBox.warning(self, "Erro", "Email não encontrado!")
            return
        
        if email_data.get("status") != "agendado":
            QMessageBox.warning(self, "Aviso", "Apenas emails agendados podem ser editados!")
            return
        
        dialog = EmailAgendamentoDialog(self, email_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Cancelar email atual e criar novo
            self.scheduler.cancelar_email(email_id)
            
            dados = dialog.dados_finais
            novo_id = self.scheduler.agendar_email(dados)
            
            if novo_id:
                QMessageBox.information(self, "Sucesso", "📝 Email atualizado com sucesso!")
                self.atualizar_tabela()
            else:
                QMessageBox.critical(self, "Erro", "❌ Erro ao atualizar email!")
    
    def cancelar_email(self):
        """Cancelar email selecionado"""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um email para cancelar!")
            return
        
        email_id = self.tabela.item(row, 0).data(Qt.ItemDataRole.UserRole)
        assunto = self.tabela.item(row, 3).text()  # Coluna 3 = Assunto
        
        resp = QMessageBox.question(
            self,
            "Confirmar Cancelamento",
            f"Cancelar email '{assunto}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resp == QMessageBox.StandardButton.Yes:
            if self.scheduler.cancelar_email(email_id):
                QMessageBox.information(self, "Sucesso", "❌ Email cancelado!")
                self.atualizar_tabela()
                self.email_cancelado.emit(email_id)
            else:
                QMessageBox.critical(self, "Erro", "❌ Erro ao cancelar email!")
    
    def carregar_historico_completo(self):
        """Carregar histórico completo de emails enviados"""
        historico_emails = []
        
        # Arquivos de histórico para verificar
        arquivos_historico = [
            "historico_envios/historico_envios.json",
            "historico_envios/emails_enviados.json"
        ]
        
        for arquivo in arquivos_historico:
            try:
                if os.path.exists(arquivo):
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        if isinstance(dados, list):
                            historico_emails.extend(dados)
                        elif isinstance(dados, dict):
                            # Se for um dict, adicionar como lista
                            historico_emails.append(dados)
            except Exception as e:
                print(f"❌ Erro ao carregar {arquivo}: {e}")
        
        return historico_emails
    
    def definir_paciente_filtro(self, paciente_id, paciente_nome=None):
        """Definir filtro por paciente"""
        self.paciente_id = paciente_id
        self.paciente_nome = paciente_nome
        print(f"🎯 Filtro definido: ID={paciente_id}, Nome={paciente_nome}")
        self.atualizar_tabela()
    
    def atualizar_tabela(self):
        """Atualizar dados da tabela com histórico completo E verificar emails pendentes"""
        try:
            # 🔍 PRIMEIRO: Verificar e enviar emails pendentes
            self.scheduler.verificar_emails_pendentes()
            
            # 🔄 SEGUNDO: Carregar dados atualizados
            # Carregar emails agendados
            emails_agendados = self.scheduler.obter_emails_agendados()
            
            # Carregar histórico de emails enviados
            emails_historico = self.carregar_historico_completo()
            
            # Combinar todos os emails
            todos_emails = emails_agendados + emails_historico
            
            # Filtrar por paciente se definido (por ID ou nome)
            if hasattr(self, 'paciente_id') and self.paciente_id:
                paciente_id_str = str(self.paciente_id)
                paciente_nome_filtro = getattr(self, 'paciente_nome', None)
                
                print(f"🔍 Filtro aplicado: ID={paciente_id_str}, Nome={paciente_nome_filtro}")
                print(f"📊 Total de emails antes do filtro: {len(todos_emails)}")
                
                emails_filtrados = []
                for email in todos_emails:
                    # Verificar por ID do paciente
                    if email.get('paciente_id') == paciente_id_str:
                        emails_filtrados.append(email)
                        continue
                    
                    # Verificar por nome do paciente
                    if paciente_nome_filtro and email.get('paciente_nome') == paciente_nome_filtro:
                        emails_filtrados.append(email)
                        continue
                    
                    # Verificar campo paciente (backup)
                    if email.get('paciente') == paciente_id_str or email.get('paciente') == paciente_nome_filtro:
                        emails_filtrados.append(email)
                
                todos_emails = emails_filtrados
                print(f"📊 Total de emails após filtro: {len(todos_emails)}")
            
            # Ordenar por data (mais recentes primeiro)
            todos_emails.sort(key=lambda x: x.get("data_envio", ""), reverse=True)
            
            self.tabela.setRowCount(len(todos_emails))
            
            for row, email in enumerate(todos_emails):
                # Coluna 0: Data de Agendamento
                data_envio = email.get("data_envio", "")
                # Formatar data para display mais amigável
                try:
                    from datetime import datetime
                    data_obj = datetime.fromisoformat(data_envio.replace('Z', '+00:00'))
                    data_formatada = data_obj.strftime("%d/%m/%Y\n%H:%M")
                except:
                    data_formatada = data_envio
                
                item_data = QTableWidgetItem(data_formatada)
                item_data.setData(Qt.ItemDataRole.UserRole, email.get("id"))
                item_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(row, 0, item_data)
                
                # Coluna 1: Paciente
                paciente = email.get("paciente_nome", "")
                if not paciente:
                    paciente = "👤 Paciente não informado"
                else:
                    paciente = f"👤 {paciente}"
                self.tabela.setItem(row, 1, QTableWidgetItem(paciente))
                
                # Coluna 2: Email
                destinatario = email.get("destinatario", "")
                email_item = QTableWidgetItem(f"📧 {destinatario}")
                self.tabela.setItem(row, 2, email_item)
                
                # Coluna 3: Assunto
                assunto = email.get("assunto", "")
                assunto_item = QTableWidgetItem(f"📝 {assunto}")
                self.tabela.setItem(row, 3, assunto_item)
                
                # Coluna 4: Anexos com nomes dos arquivos (todos visíveis)
                anexos = email.get("anexos", [])
                if anexos:
                    if len(anexos) == 1:
                        # Um anexo: mostrar o nome
                        nome_arquivo = os.path.basename(anexos[0]) if isinstance(anexos[0], str) else "Arquivo"
                        anexos_text = f"📎 {nome_arquivo}"
                    else:
                        # Múltiplos anexos: mostrar TODOS os nomes
                        nomes_anexos = []
                        for anexo in anexos:  # Mostrar TODOS os anexos
                            nome = os.path.basename(anexo) if isinstance(anexo, str) else "Arquivo"
                            nomes_anexos.append(f"• {nome}")
                        
                        anexos_text = f"📎 {len(anexos)} arquivo(s):\n" + "\n".join(nomes_anexos)
                else:
                    anexos_text = "📎 Sem anexos"
                
                anexos_item = QTableWidgetItem(anexos_text)
                anexos_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                # Habilitar quebra de linha para mostrar todos os anexos
                anexos_item.setData(Qt.ItemDataRole.DisplayRole, anexos_text)
                self.tabela.setItem(row, 4, anexos_item)
                
                # Coluna 5: Status com cores
                status = email.get("status", "")
                status_configs = {
                    "agendado": ("📅 Agendado", QColor(173, 216, 230)),   # Light blue
                    "enviado": ("✅ Enviado", QColor(144, 238, 144)),    # Light green
                    "cancelado": ("❌ Cancelado", QColor(211, 211, 211)), # Light gray
                    "falhado": ("⚠️ Falhado", QColor(255, 255, 0))       # Yellow
                }
                
                status_text, cor = status_configs.get(status, (status, QColor(255, 255, 255)))
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(cor)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Adicionar efeito visual para status
                if status == "agendado":
                    status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                elif status == "enviado":
                    status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                
                self.tabela.setItem(row, 5, status_item)
            
            # Atualizar estatísticas
            self.atualizar_estatisticas()
            
        except Exception as e:
            print(f"❌ Erro ao atualizar tabela: {e}")
    
    def atualizar_estatisticas(self):
        """Atualizar labels de estatísticas com dados completos"""
        try:
            # Obter dados completos (agendados + histórico)
            emails_agendados = self.scheduler.obter_emails_agendados()
            emails_historico = self.carregar_historico_completo()
            todos_emails = emails_agendados + emails_historico
            
            # Filtrar por paciente se definido
            if hasattr(self, 'paciente_id') and self.paciente_id:
                todos_emails = [email for email in todos_emails 
                              if email.get('paciente_id') == str(self.paciente_id)]
            
            # Calcular estatísticas
            total = len(todos_emails)
            agendados = len([e for e in todos_emails if e.get('status') == 'agendado'])
            enviados = len([e for e in todos_emails if e.get('status') == 'enviado'])
            cancelados = len([e for e in todos_emails if e.get('status') == 'cancelado'])
            falhados = len([e for e in todos_emails if e.get('status') == 'falhado'])
            
            # Atualizar labels
            self.label_total.setText(f"Total: {total}")
            self.label_agendados.setText(f"📅 Agendados: {agendados}")
            self.label_enviados.setText(f"✅ Enviados: {enviados}")
            self.label_cancelados.setText(f"❌ Cancelados: {cancelados}")
            self.label_falhados.setText(f"⚠️ Falhados: {falhados}")
            
            # Status do scheduler
            stats_scheduler = self.scheduler.obter_estatisticas()
            self.label_ultimo_check.setText(f"Última verificação: {stats_scheduler.get('ultimo_verificacao', 'Nunca')}")
            
            if stats_scheduler.get("ativo"):
                self.label_status.setText("✅ Scheduler Ativo")
                self.label_status.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.label_status.setText("⏸️ Scheduler Parado")
                self.label_status.setStyleSheet("color: red; font-weight: bold;")
                
        except Exception as e:
            print(f"❌ Erro ao atualizar estatísticas: {e}")
    
    def on_email_enviado(self, email_data):
        """Callback quando email é enviado"""
        print(f"✅ Email enviado: {email_data.get('assunto')}")
        self.atualizar_tabela()
    
    def on_email_falhado(self, email_data, erro):
        """Callback quando envio falha"""
        print(f"❌ Falha no email: {email_data.get('assunto')} - {erro}")
        self.atualizar_tabela()
    
    def on_status_atualizado(self, status):
        """Callback quando status do scheduler muda"""
        print(f"📧 Scheduler: {status}")


class EmailsAgendadosWindow(QMainWindow):
    """Janela principal para gestão de emails agendados"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📧 Gestão de Emails Agendados")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Widget principal
        self.widget_principal = EmailsAgendadosWidget()
        layout.addWidget(self.widget_principal)
        
        # Maximizar automaticamente
        self.showMaximized()
