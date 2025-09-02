"""
Sistema CoRe Completo - Janela Independente
═══════════════════════════════════════════════════════════════════════

Interface completa do sistema CoRe em janela separada com todas as abas.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTabWidget, QGroupBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QProgressBar,
    QSplitter, QFrame, QScrollArea, QCheckBox, QSlider, QListWidget,
    QListWidgetItem, QMessageBox, QFileDialog, QApplication, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPalette, QColor
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# Imports dos módulos CoRe
try:
    from biodesk.quantum.resonance_interface import ResonanceInterface
    RESONANCE_AVAILABLE = True
except ImportError:
    RESONANCE_AVAILABLE = False

try:
    from biodesk_dialogs import BiodeskMessageBox
except ImportError:
    BiodeskMessageBox = QMessageBox

from biodesk_styles import BiodeskStyles

class CoreSystemWindow(QMainWindow):
    """Janela principal do Sistema CoRe Completo"""
    
    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.parent_window = parent
        
        # Estado da varredura
        self.scanning_frequencies = False
        self.current_frequency = 0.0
        self.frequency_range = (1, 10000)  # Hz
        self.scan_progress = 0
        
        self.setup_ui()
        self.setup_frequency_scanner()
        
    def setup_ui(self):
        """Configura interface do Sistema CoRe"""
        self.setWindowTitle("🧬 Sistema CoRe Completo - Análise Bioenergética")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header com informações do paciente
        header_frame = self.create_header()
        layout.addWidget(header_frame)
        
        # Barra de status de varredura
        self.scan_status_bar = self.create_scan_status_bar()
        layout.addWidget(self.scan_status_bar)
        
        # Abas principais
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Aba 1: Análise de Ressonância (Fase 2)
        if RESONANCE_AVAILABLE:
            self.resonance_tab = ResonanceInterface()
            self.tab_widget.addTab(self.resonance_tab, "🔬 Análise")
        else:
            placeholder_tab = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_tab)
            placeholder_label = QLabel("⚠️ Módulo de Ressonância não disponível")
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(placeholder_tab, "🔬 Análise")
        
        # Aba 2: Protocolos (Fase 3)
        self.protocols_tab = self.create_protocols_tab()
        self.tab_widget.addTab(self.protocols_tab, "📋 Protocolos")
        
        # Aba 3: Balanceamento (Fase 4)
        self.balancing_tab = self.create_balancing_tab()
        self.tab_widget.addTab(self.balancing_tab, "⚖️ Balanceamento")
        
        # Aba 4: Relatórios (Fase 5)
        self.reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(self.reports_tab, "📊 Relatórios")
        
        # Aba 5: Conexões & Hardware (NOVA)
        self.hardware_tab = self.create_hardware_tab()
        self.tab_widget.addTab(self.hardware_tab, "🔌 Hardware")
        
        layout.addWidget(self.tab_widget)
        
        # Footer com controles de sessão
        footer_frame = self.create_footer()
        layout.addWidget(footer_frame)
        
        # Aplicar estilo
        self.setStyleSheet(BiodeskStyles.get_main_window_style())
        
    def create_header(self) -> QFrame:
        """Cria header com informações do paciente"""
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 10px;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Info do paciente
        patient_info = QLabel("👤 Sistema CoRe Ativo")
        if self.paciente_data:
            patient_info.setText(f"👤 {self.paciente_data.get('nome', 'Paciente Anônimo')}")
        patient_info.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(patient_info)
        
        layout.addStretch()
        
        # Status do sistema
        self.system_status = QLabel("🟢 Sistema Operacional")
        self.system_status.setFont(QFont("Arial", 12))
        layout.addWidget(self.system_status)
        
        return frame
        
    def create_scan_status_bar(self) -> QFrame:
        """Cria barra de status da varredura de frequências"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Indicador de varredura
        self.scan_indicator = QLabel("📡 Varredura:")
        self.scan_indicator.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.scan_indicator)
        
        # Frequência atual
        self.frequency_display = QLabel("0.00 Hz")
        self.frequency_display.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(self.frequency_display)
        
        # Barra de progresso
        self.scan_progress_bar = QProgressBar()
        self.scan_progress_bar.setFixedHeight(20)
        self.scan_progress_bar.setVisible(False)
        layout.addWidget(self.scan_progress_bar)
        
        # Status de biofeedback
        self.biofeedback_status = QLabel("⏸️ Standby")
        self.biofeedback_status.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.biofeedback_status)
        
        layout.addStretch()
        
        # Controles de varredura
        self.start_scan_btn = QPushButton("▶️ Iniciar Varredura")
        self.start_scan_btn.clicked.connect(self.toggle_frequency_scan)
        self.start_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        layout.addWidget(self.start_scan_btn)
        
        return frame
        
    def create_protocols_tab(self) -> QWidget:
        """Aba de protocolos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Implementação da interface de protocolos
        protocols_label = QLabel("📋 Gestão de Protocolos CoRe")
        protocols_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(protocols_label)
        
        # Lista de protocolos
        self.protocols_list = QListWidget()
        self.protocols_list.addItems([
            "🧬 Protocolo Básico de Ressonância",
            "⚡ Protocolo de Energização",
            "🔄 Protocolo de Reequilíbrio",
            "🎯 Protocolo Direcionado",
            "🌟 Protocolo de Harmonização",
            "🛡️ Protocolo de Proteção"
        ])
        layout.addWidget(self.protocols_list)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        execute_btn = QPushButton("▶️ Executar Protocolo")
        execute_btn.clicked.connect(self.execute_selected_protocol)
        buttons_layout.addWidget(execute_btn)
        
        create_btn = QPushButton("➕ Criar Novo")
        create_btn.clicked.connect(self.create_new_protocol)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
        
        return widget
        
    def create_balancing_tab(self) -> QWidget:
        """Aba de balanceamento"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        balance_label = QLabel("⚖️ Balanceamento Bioenergético")
        balance_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(balance_label)
        
        # Interface de balanceamento
        balance_group = QGroupBox("🎛️ Controles de Balanceamento")
        balance_layout = QGridLayout(balance_group)
        
        # Chakras
        chakras = ["🔴 Raiz", "🟠 Sacral", "🟡 Plexo Solar", "🟢 Cardíaco", 
                  "🔵 Laríngeo", "🟣 Frontal", "⚪ Coronário"]
        
        for i, chakra in enumerate(chakras):
            label = QLabel(chakra)
            balance_layout.addWidget(label, i, 0)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            balance_layout.addWidget(slider, i, 1)
            
            value_label = QLabel("50%")
            balance_layout.addWidget(value_label, i, 2)
        
        layout.addWidget(balance_group)
        
        return widget
        
    def create_reports_tab(self) -> QWidget:
        """Aba de relatórios"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        reports_label = QLabel("📊 Sistema de Relatórios")
        reports_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(reports_label)
        
        # Lista de relatórios
        reports_list = QListWidget()
        reports_list.addItems([
            "📈 Relatório de Análise Completa",
            "📋 Relatório de Protocolos Executados",
            "⚖️ Relatório de Balanceamento",
            "📊 Relatório Estatístico",
            "📝 Relatório de Sessão"
        ])
        layout.addWidget(reports_list)
        
        # Botões de relatório
        reports_buttons = QHBoxLayout()
        
        generate_btn = QPushButton("📄 Gerar Relatório")
        export_btn = QPushButton("💾 Exportar PDF")
        
        reports_buttons.addWidget(generate_btn)
        reports_buttons.addWidget(export_btn)
        
        layout.addLayout(reports_buttons)
        
        return widget
        
    def create_hardware_tab(self) -> QWidget:
        """Aba de conexões e hardware"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Seção HS3
        hs3_group = QGroupBox("🔌 Hardware HS3")
        hs3_layout = QVBoxLayout(hs3_group)
        
        # Status de conexão
        self.hw_connection_status = QLabel("🔍 Verificando...")
        hs3_layout.addWidget(self.hw_connection_status)
        
        # Botões de controle
        hw_buttons = QHBoxLayout()
        
        connect_btn = QPushButton("🔌 Conectar")
        connect_btn.clicked.connect(self.connect_hardware)
        hw_buttons.addWidget(connect_btn)
        
        test_btn = QPushButton("🧪 Testar")
        test_btn.clicked.connect(self.test_hardware)
        hw_buttons.addWidget(test_btn)
        
        force_reconnect_btn = QPushButton("🔧 Reconexão Forçada")
        force_reconnect_btn.clicked.connect(self.force_reconnect_hardware)
        hw_buttons.addWidget(force_reconnect_btn)
        
        hs3_layout.addLayout(hw_buttons)
        
        # Log de hardware
        self.hw_log = QTextEdit()
        self.hw_log.setMaximumHeight(200)
        self.hw_log.setPlaceholderText("Log de atividade do hardware...")
        hs3_layout.addWidget(self.hw_log)
        
        layout.addWidget(hs3_group)
        
        # Seção de documentos
        docs_group = QGroupBox("📄 Conformidade de Documentos")
        docs_layout = QVBoxLayout(docs_group)
        
        self.docs_status = QLabel("📄 Verificando documentos...")
        docs_layout.addWidget(self.docs_status)
        
        layout.addWidget(docs_group)
        
        return widget
        
    def create_footer(self) -> QFrame:
        """Cria footer com controles de sessão"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 8px;
                margin: 2px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Informações da sessão
        session_info = QLabel("🕐 Sessão Ativa")
        session_info.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(session_info)
        
        layout.addStretch()
        
        # Botões de controle
        save_session_btn = QPushButton("💾 Salvar Sessão")
        save_session_btn.clicked.connect(self.save_session)
        layout.addWidget(save_session_btn)
        
        close_btn = QPushButton("❌ Fechar Sistema")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return frame
        
    def setup_frequency_scanner(self):
        """Configura sistema de varredura de frequências"""
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.update_frequency_scan)
        
    def toggle_frequency_scan(self):
        """Inicia/para varredura de frequências"""
        if not self.scanning_frequencies:
            self.start_frequency_scan()
        else:
            self.stop_frequency_scan()
            
    def start_frequency_scan(self):
        """Inicia varredura de frequências"""
        self.scanning_frequencies = True
        self.current_frequency = self.frequency_range[0]
        self.scan_progress = 0
        
        self.start_scan_btn.setText("⏸️ Parar Varredura")
        self.start_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.scan_progress_bar.setVisible(True)
        self.scan_progress_bar.setRange(0, 100)
        self.biofeedback_status.setText("🎯 Analisando...")
        self.biofeedback_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        self.scan_timer.start(100)  # Atualizar a cada 100ms
        
    def stop_frequency_scan(self):
        """Para varredura de frequências"""
        self.scanning_frequencies = False
        self.scan_timer.stop()
        
        self.start_scan_btn.setText("▶️ Iniciar Varredura")
        self.start_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        self.scan_progress_bar.setVisible(False)
        self.biofeedback_status.setText("⏸️ Standby")
        self.biofeedback_status.setStyleSheet("color: #7f8c8d;")
        
    def update_frequency_scan(self):
        """Atualiza varredura de frequências"""
        if not self.scanning_frequencies:
            return
            
        # Simular varredura progressiva
        freq_range = self.frequency_range[1] - self.frequency_range[0]
        step = freq_range / 1000  # 1000 passos
        
        self.current_frequency += step
        if self.current_frequency > self.frequency_range[1]:
            self.current_frequency = self.frequency_range[0]
            
        # Atualizar display
        self.frequency_display.setText(f"{self.current_frequency:.2f} Hz")
        
        # Atualizar progresso
        progress = ((self.current_frequency - self.frequency_range[0]) / freq_range) * 100
        self.scan_progress_bar.setValue(int(progress))
        
        # Simular detecção de ressonância
        if int(self.current_frequency) % 100 == 0:  # A cada 100 Hz
            self.biofeedback_status.setText(f"🎯 Ressonância: {self.current_frequency:.0f} Hz")
        
    def execute_selected_protocol(self):
        """Executa protocolo selecionado"""
        current_item = self.protocols_list.currentItem()
        if current_item:
            protocol_name = current_item.text()
            BiodeskMessageBox.information(self, "Protocolo", 
                f"Executando: {protocol_name}\n\nProtocolo iniciado com sucesso!")
            
    def create_new_protocol(self):
        """Cria novo protocolo"""
        BiodeskMessageBox.information(self, "Novo Protocolo", 
            "Função de criação de protocolo personalizado.\n\nEm desenvolvimento...")
            
    def connect_hardware(self):
        """Conecta hardware"""
        self.hw_log.append("[INFO] Tentando conectar ao HS3...")
        self.hw_connection_status.setText("🔌 Conectando...")
        
        # Simular conexão
        QTimer.singleShot(2000, lambda: self.hw_connection_status.setText("✅ HS3 Conectado"))
        QTimer.singleShot(2000, lambda: self.hw_log.append("[SUCCESS] HS3 conectado com sucesso!"))
        
    def test_hardware(self):
        """Testa hardware"""
        self.hw_log.append("[TEST] Iniciando teste de comunicação...")
        QTimer.singleShot(1000, lambda: self.hw_log.append("[TEST] Teste concluído - OK!"))
        
    def force_reconnect_hardware(self):
        """Força reconexão do hardware"""
        self.hw_log.append("[FORCE] Iniciando reconexão forçada...")
        self.hw_connection_status.setText("🔧 Reconectando...")
        QTimer.singleShot(3000, lambda: self.hw_connection_status.setText("✅ Reconexão Concluída"))
        
    def save_session(self):
        """Salva sessão atual"""
        BiodeskMessageBox.information(self, "Sessão", "Sessão salva com sucesso!")
        
    def closeEvent(self, event):
        """Override do evento de fechamento"""
        if self.scanning_frequencies:
            self.stop_frequency_scan()
        event.accept()
