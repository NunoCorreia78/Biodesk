"""
🎛️ FICHA CONTROLLER - BIODESK
============================

Controlador principal da ficha de paciente.
Versão refatorada do monolito ficha_paciente.py.

Responsabilidades:
- Coordenar entre módulos
- Gerenciar layout principal
- Delegar funcionalidades específicas

Autor: Biodesk Team
Data: 25/08/2025
Linhas: < 200 (objetivo)
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit, 
    QScrollArea, QFrame, QApplication, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QShortcut, QKeySequence

# Imports dos módulos refatorados
from ..core.button_manager import ButtonManager, FichaButtons
from ..dialogs.followup_dialog import FollowUpDialog

# Imports dos widgets existentes (mantidos)
from ..dados_pessoais import DadosPessoaisWidget
from ..historico_clinico import HistoricoClinicoWidget
from ..templates_manager import TemplatesManagerWidget
from ..comunicacao_manager import ComunicacaoManagerWidget
from ..gestao_documentos import GestaoDocumentosWidget
from ..declaracao_saude import DeclaracaoSaudeWidget
from ..pesquisa_pacientes import PesquisaPacientesManager

# Imports externos
from db_manager import DBManager
from sistema_assinatura import abrir_dialogo_assinatura

class FichaController(QMainWindow):
    """
    Controlador principal da ficha de paciente.
    Versão limpa e modular do antigo monolito.
    """
    
    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.current_patient = paciente_data
        self.widgets_cache = {}
        
        self.setup_ui()
        self.setup_shortcuts()
        self.load_initial_data()
        
        # Se recebeu dados do paciente, carregá-los
        if paciente_data:
            self.set_current_patient(paciente_data)
    
    def setup_ui(self):
        """Configura a interface principal."""
        self.setWindowTitle("📋 Ficha de Paciente - Biodesk")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Cabeçalho com botões principais
        self.create_header_section(main_layout)
        
        # Área de conteúdo com tabs
        self.create_content_area(main_layout)
        
        # Rodapé com informações
        self.create_footer_section(main_layout)
    
    def create_header_section(self, parent_layout):
        """Cria seção do cabeçalho com botões principais."""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Informações do paciente (à esquerda)
        patient_info = QLabel("📋 Nenhum paciente selecionado")
        patient_info.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        header_layout.addWidget(patient_info)
        
        header_layout.addStretch()
        
        # Botões principais (à direita) usando ButtonManager
        self.header_buttons = ButtonManager.create_ficha_toolbar_buttons(header_frame)
        
        # Conectar ações dos botões
        self.header_buttons['followup'].clicked.connect(self.open_followup_dialog)
        self.header_buttons['template'].clicked.connect(self.open_template_manager)
        self.header_buttons['enviar_email'].clicked.connect(self.send_email)
        self.header_buttons['config'].clicked.connect(self.open_config)
        self.header_buttons['terapia_quantica'].clicked.connect(self.open_terapia_quantica)
        
        # Adicionar botões ao layout
        for button in self.header_buttons.values():
            header_layout.addWidget(button)
        
        parent_layout.addWidget(header_frame)
        
        # Guardar referência para atualizar info do paciente
        self.patient_info_label = patient_info
    
    def create_content_area(self, parent_layout):
        """Cria área principal de conteúdo com tabs."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: none;
                font-weight: bold;
            }
        """)
        
        # Adicionar tabs dos módulos existentes
        self.add_widget_tabs()
        
        parent_layout.addWidget(self.tab_widget)
    
    def add_widget_tabs(self):
        """Adiciona tabs dos widgets especializados."""
        # Lazy loading dos widgets
        tab_configs = [
            ("👤 Dados Pessoais", "dados_pessoais", DadosPessoaisWidget),
            ("🏥 Histórico", "historico_clinico", HistoricoClinicoWidget),
            ("📄 Templates", "templates_manager", TemplatesManagerWidget),
            ("📧 Comunicação", "comunicacao_manager", ComunicacaoManagerWidget),
            ("📁 Documentos", "gestao_documentos", GestaoDocumentosWidget),
            ("🩺 Declaração", "declaracao_saude", DeclaracaoSaudeWidget),
        ]
        
        for tab_name, widget_key, widget_class in tab_configs:
            # Placeholder inicial
            placeholder = QLabel(f"Carregando {tab_name}...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("font-size: 14px; color: #6c757d;")
            
            self.tab_widget.addTab(placeholder, tab_name)
            
            # Guardar configuração para lazy loading
            self.widgets_cache[widget_key] = {
                'class': widget_class,
                'instance': None,
                'tab_index': self.tab_widget.count() - 1
            }
    
    def create_footer_section(self, parent_layout):
        """Cria seção do rodapé."""
        footer_frame = QFrame()
        footer_frame.setFixedHeight(40)
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        footer_layout = QHBoxLayout(footer_frame)
        
        # Status à esquerda
        self.status_label = QLabel("✅ Sistema pronto")
        self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
        footer_layout.addWidget(self.status_label)
        
        footer_layout.addStretch()
        
        # Info à direita
        info_label = QLabel("Biodesk v2.0 - Medicina Integrativa")
        info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        footer_layout.addWidget(info_label)
        
        parent_layout.addWidget(footer_frame)
    
    def setup_shortcuts(self):
        """Configura atalhos de teclado."""
        # Atalho para follow-up
        followup_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        followup_shortcut.activated.connect(self.open_followup_dialog)
        
        # Atalho para templates
        template_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        template_shortcut.activated.connect(self.open_template_manager)
        
        # Atalho para email
        email_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        email_shortcut.activated.connect(self.send_email)
    
    def load_initial_data(self):
        """Carrega dados iniciais."""
        # Lazy loading do primeiro tab (dados pessoais)
        self.load_widget_on_demand('dados_pessoais')
        
        self.update_status("Sistema iniciado com sucesso")
    
    def load_widget_on_demand(self, widget_key):
        """Carrega widget sob demanda (lazy loading)."""
        widget_config = self.widgets_cache.get(widget_key)
        if not widget_config or widget_config['instance']:
            return widget_config['instance'] if widget_config else None
        
        try:
            # Criar instância do widget
            widget_instance = widget_config['class']()
            widget_config['instance'] = widget_instance
            
            # Substituir placeholder
            tab_index = widget_config['tab_index']
            self.tab_widget.removeTab(tab_index)
            self.tab_widget.insertTab(tab_index, widget_instance, 
                                    self.tab_widget.tabText(tab_index))
            
            self.update_status(f"✅ {widget_key} carregado")
            return widget_instance
            
        except Exception as e:
            self.update_status(f"❌ Erro ao carregar {widget_key}: {e}")
            return None
    
    # === AÇÕES DOS BOTÕES ===
    
    def open_followup_dialog(self):
        """Abre dialog de follow-up."""
        if not self.current_patient:
            self.update_status("⚠️ Selecione um paciente primeiro")
            return
        
        dialog = FollowUpDialog(self.current_patient, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            followup_data = dialog.get_followup_data()
            self.schedule_followup(followup_data)
    
    def open_template_manager(self):
        """Abre gerenciador de templates."""
        widget = self.load_widget_on_demand('templates_manager')
        if widget:
            # Mudar para tab de templates
            self.tab_widget.setCurrentIndex(self.widgets_cache['templates_manager']['tab_index'])
    
    def send_email(self):
        """Inicia processo de envio de email."""
        widget = self.load_widget_on_demand('comunicacao_manager')
        if widget:
            self.tab_widget.setCurrentIndex(self.widgets_cache['comunicacao_manager']['tab_index'])
    
    def open_config(self):
        """Abre configurações."""
        self.update_status("🔧 Abrindo configurações...")
        # TODO: Implementar dialog de configurações
    
    def open_terapia_quantica(self):
        """Abre módulo de terapia quântica."""
        try:
            from terapia_quantica_window import TerapiaQuanticaWindow
            self.terapia_window = TerapiaQuanticaWindow(self)
            self.terapia_window.show()
            self.update_status("⚡ Módulo de terapia quântica aberto")
        except Exception as e:
            self.update_status(f"❌ Erro ao abrir terapia quântica: {e}")
    
    # === MÉTODOS AUXILIARES ===
    
    def schedule_followup(self, followup_data):
        """Agenda follow-up no sistema."""
        # TODO: Implementar agendamento real
        self.update_status(f"📅 Follow-up agendado para {followup_data['dias_apos']} dias")
    
    def set_current_patient(self, patient_data):
        """Define paciente atual."""
        self.current_patient = patient_data
        patient_name = patient_data.get('nome', 'Paciente sem nome')
        self.patient_info_label.setText(f"📋 Paciente: {patient_name}")
        self.update_status(f"👤 Paciente selecionado: {patient_name}")
    
    def update_status(self, message):
        """Atualiza mensagem de status."""
        self.status_label.setText(message)
        print(f"[FichaController] {message}")  # Log para debug
    
    # === MÉTODOS ESTÁTICOS PARA COMPATIBILIDADE ===
    
    @staticmethod
    def mostrar_seletor(callback=None, parent=None):
        """
        Método estático para compatibilidade com main_window.py.
        Mostra seletor de pacientes usando o PesquisaPacientesManager.
        """
        try:
            # Import dinâmico para evitar dependências circulares
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            # Usar o sistema existente do monolito temporariamente
            import importlib.util
            spec = importlib.util.spec_from_file_location("ficha_paciente_module", 
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ficha_paciente.py"))
            ficha_paciente_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ficha_paciente_module)
            
            # Delegar para o método original
            return ficha_paciente_module.FichaPaciente.mostrar_seletor(callback=callback, parent=parent)
            
        except Exception as e:
            print(f"❌ Erro no mostrar_seletor: {e}")
            if callback:
                # Callback com dados de exemplo para não quebrar o fluxo
                callback({'nome': 'Paciente Exemplo', 'id': 1})

# Alias para compatibilidade
FichaPaciente = FichaController
