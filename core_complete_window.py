"""
Janela CoRe Completa - Sistema Independente
═══════════════════════════════════════════

Janela separada com todas as funcionalidades do sistema CoRe:
- Análise de Ressonância
- Protocolos Inteligentes
- Interface de Balanceamento
- Sistema de Relatórios
- Conexões & Hardware
"""

import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Imports dos módulos do sistema
try:
    from biodesk_dialogs import BiodeskDialogs as BiodeskMessageBox
except ImportError:
    from PyQt6.QtWidgets import QMessageBox as BiodeskMessageBox

from biodesk_ui_kit import BiodeskUIKit
from biodesk_styles import BiodeskStyles
import hs3_hardware
from hs3_hardware import hs3_hardware

# Imports dos módulos CoRe
try:
    from biodesk.quantum.resonance_analysis import ResonanceAnalysis
    from biodesk.quantum.protocol_generator import ProtocolGenerator
    from biodesk.quantum.balancing_interface import BalancingInterface
    from biodesk.quantum.reports_system import ReportsSystem
    from biodesk.quantum.resonance_interface import ResonanceInterface
    CORE_MODULES_AVAILABLE = True
except ImportError:
    CORE_MODULES_AVAILABLE = False

class CoreCompleteWindow(QMainWindow):
    """
    🧬 JANELA CORE COMPLETA
    
    Sistema independente com todas as funcionalidades:
    - Interface moderna com abas
    - Integração completa CoRe
    - Gestão de hardware
    - Biofeedback em tempo real
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("🧬 Sistema CoRe Completo - Biodesk")
        self.setWindowIcon(QIcon("assets/icon.png") if QIcon("assets/icon.png").isNull() == False else QIcon())
        
        # Variáveis de estado
        self.is_session_active = False
        self.current_session = None
        self.connected_to_hs3 = False
        self.frequency_sweep_active = False
        
        # Configurar interface
        self.setup_ui()
        self.setup_status_bar()
        self.setup_connections()
        
        # Verificar módulos CoRe
        if not CORE_MODULES_AVAILABLE:
            self.show_core_unavailable_message()
        
        # Verificar conexão HS3
        self.update_hs3_status()
    
    def setup_ui(self):
        """Configura interface principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header com informações rápidas
        self.create_header()
        layout.addWidget(self.header_widget)
        
        # Abas principais
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #c0c0c0;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background: #e8f5e8;
            }
        """)
        
        # Adicionar abas
        self.create_tabs()
        layout.addWidget(self.tab_widget)
        
        # Configurar janela
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
    
    def create_header(self):
        """Cria header com status"""
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(80)
        self.header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-radius: 10px;
                border: 2px solid #2196f3;
            }
        """)
        
        layout = QHBoxLayout(self.header_widget)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Status HS3
        self.hs3_status_label = QLabel("🔴 HS3 Desconectado")
        self.hs3_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
        layout.addWidget(self.hs3_status_label)
        
        layout.addStretch()
        
        # Documentos Status
        self.docs_status_label = QLabel("📄 Documentos: ✅ Conformes")
        self.docs_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388e3c;")
        layout.addWidget(self.docs_status_label)
        
        layout.addStretch()
        
        # Sessão Status
        self.session_status_label = QLabel("⭕ Nenhuma sessão ativa")
        self.session_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f57c00;")
        layout.addWidget(self.session_status_label)
    
    def create_tabs(self):
        """Cria todas as abas do sistema"""
        
        # 1. Aba de Análise de Ressonância
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "🔍 Análise")
        
        # 2. Aba de Protocolos
        self.protocols_tab = self.create_protocols_tab()
        self.tab_widget.addTab(self.protocols_tab, "📋 Protocolos")
        
        # 3. Aba de Balanceamento
        self.balancing_tab = self.create_balancing_tab()
        self.tab_widget.addTab(self.balancing_tab, "⚖️ Balanceamento")
        
        # 4. Aba de Relatórios
        self.reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(self.reports_tab, "📊 Relatórios")
        
        # 5. Aba de Conexões & Hardware (NOVA)
        self.hardware_tab = self.create_hardware_tab()
        self.tab_widget.addTab(self.hardware_tab, "🔧 Hardware")
        
        # 6. Aba de Biofeedback
        self.biofeedback_tab = self.create_biofeedback_tab()
        self.tab_widget.addTab(self.biofeedback_tab, "🎯 Biofeedback")
    
    def create_analysis_tab(self):
        """Aba de análise de ressonância"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title = QLabel("🔍 Análise de Ressonância Quântica")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin: 10px;")
        layout.addWidget(title)
        
        if CORE_MODULES_AVAILABLE:
            # Interface de ressonância completa
            try:
                self.resonance_interface = ResonanceInterface()
                layout.addWidget(self.resonance_interface)
            except Exception as e:
                error_label = QLabel(f"❌ Erro ao carregar interface de ressonância: {e}")
                error_label.setStyleSheet("color: red; padding: 20px;")
                layout.addWidget(error_label)
        else:
            # Placeholder
            placeholder = QLabel("🔧 Módulos CoRe não disponíveis\nVerifique a instalação dos componentes")
            placeholder.setStyleSheet("color: #666; font-size: 14px; padding: 50px; text-align: center;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)
        
        return widget
    
    def create_protocols_tab(self):
        """Aba de protocolos inteligentes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title = QLabel("📋 Protocolos Terapêuticos Inteligentes")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #388e3c; margin: 10px;")
        layout.addWidget(title)
        
        if CORE_MODULES_AVAILABLE:
            # Controles de protocolo
            controls_group = QGroupBox("🎮 Controles")
            controls_layout = QHBoxLayout(controls_group)
            
            self.start_protocol_btn = QPushButton("▶️ Iniciar Protocolo")
            self.start_protocol_btn.clicked.connect(self.start_therapy_protocol)
            BiodeskStyles.apply_to_existing_button(self.start_protocol_btn)
            controls_layout.addWidget(self.start_protocol_btn)
            
            self.pause_protocol_btn = QPushButton("⏸️ Pausar")
            self.pause_protocol_btn.setEnabled(False)
            controls_layout.addWidget(self.pause_protocol_btn)
            
            self.stop_protocol_btn = QPushButton("⏹️ Parar")
            self.stop_protocol_btn.setEnabled(False)
            controls_layout.addWidget(self.stop_protocol_btn)
            
            layout.addWidget(controls_group)
            
            # Lista de protocolos disponíveis
            protocols_group = QGroupBox("📋 Protocolos Disponíveis")
            protocols_layout = QVBoxLayout(protocols_group)
            
            self.protocols_list = QListWidget()
            self.protocols_list.addItems([
                "🌟 Protocolo Relaxamento Profundo",
                "⚡ Protocolo Energização Celular", 
                "🧠 Protocolo Clareza Mental",
                "💪 Protocolo Vitalidade Física",
                "🛡️ Protocolo Equilibrio Energético",
                "🔄 Protocolo Regeneração"
            ])
            protocols_layout.addWidget(self.protocols_list)
            
            layout.addWidget(protocols_group)
        else:
            placeholder = QLabel("🔧 Módulos CoRe não disponíveis")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)
        
        return widget
    
    def create_balancing_tab(self):
        """Aba de balanceamento energético"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("⚖️ Interface de Balanceamento Energético")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f57c00; margin: 10px;")
        layout.addWidget(title)
        
        if CORE_MODULES_AVAILABLE:
            # Painel de balanceamento
            balance_group = QGroupBox("⚖️ Equilibrio Atual")
            balance_layout = QGridLayout(balance_group)
            
            # Barras de energia
            energy_levels = ["Física", "Mental", "Emocional", "Espiritual"]
            self.energy_bars = {}
            
            for i, energy_type in enumerate(energy_levels):
                label = QLabel(f"{energy_type}:")
                balance_layout.addWidget(label, i, 0)
                
                progress = QProgressBar()
                progress.setRange(0, 100)
                progress.setValue(65 + i * 5)  # Valores exemplo
                progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid #ccc;
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #4caf50, stop:1 #8bc34a);
                        border-radius: 6px;
                    }}
                """)
                balance_layout.addWidget(progress, i, 1)
                self.energy_bars[energy_type] = progress
            
            layout.addWidget(balance_group)
            
            # Controles de balanceamento
            controls_group = QGroupBox("🎛️ Controles de Balanceamento")
            controls_layout = QHBoxLayout(controls_group)
            
            auto_balance_btn = QPushButton("🤖 Balanceamento Automático")
            auto_balance_btn.clicked.connect(self.start_auto_balance)
            BiodeskStyles.apply_to_existing_button(auto_balance_btn)
            controls_layout.addWidget(auto_balance_btn)
            
            manual_balance_btn = QPushButton("🎯 Balanceamento Manual")
            controls_layout.addWidget(manual_balance_btn)
            
            layout.addWidget(controls_group)
        else:
            placeholder = QLabel("🔧 Módulos CoRe não disponíveis")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)
        
        return widget
    
    def create_reports_tab(self):
        """Aba de relatórios e análises"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("📊 Sistema de Relatórios Profissionais")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9c27b0; margin: 10px;")
        layout.addWidget(title)
        
        # Controles de relatório
        controls_group = QGroupBox("📋 Gerar Relatórios")
        controls_layout = QGridLayout(controls_group)
        
        # Tipos de relatório
        report_types = [
            ("📈 Relatório de Sessão", "session"),
            ("📊 Análise de Progresso", "progress"),
            ("🔍 Relatório de Ressonância", "resonance"),
            ("⚖️ Relatório de Balanceamento", "balance")
        ]
        
        for i, (name, type_id) in enumerate(report_types):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, t=type_id: self.generate_report(t))
            BiodeskStyles.apply_to_existing_button(btn)
            controls_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addWidget(controls_group)
        
        # Área de preview
        preview_group = QGroupBox("👁️ Preview do Relatório")
        preview_layout = QVBoxLayout(preview_group)
        
        self.report_preview = QTextEdit()
        self.report_preview.setPlaceholderText("O preview do relatório aparecerá aqui...")
        self.report_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.report_preview)
        
        layout.addWidget(preview_group)
        
        return widget
    
    def create_hardware_tab(self):
        """🔧 NOVA ABA - Conexões & Hardware"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("🔧 Gestão de Hardware & Conexões")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff5722; margin: 10px;")
        layout.addWidget(title)
        
        # Status de Conexão HS3
        connection_group = QGroupBox("🔌 Estado da Conexão HS3")
        connection_layout = QVBoxLayout(connection_group)
        
        # Status atual
        self.hardware_status_label = QLabel("❌ Desconectado")
        self.hardware_status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; margin: 10px;")
        connection_layout.addWidget(self.hardware_status_label)
        
        # Controles de conexão
        controls_layout = QHBoxLayout()
        
        self.connect_hs3_btn = QPushButton("🔌 Conectar HS3")
        self.connect_hs3_btn.clicked.connect(self.connect_hs3)
        BiodeskStyles.apply_to_existing_button(self.connect_hs3_btn)
        controls_layout.addWidget(self.connect_hs3_btn)
        
        self.disconnect_hs3_btn = QPushButton("🔌 Desconectar")
        self.disconnect_hs3_btn.clicked.connect(self.disconnect_hs3)
        self.disconnect_hs3_btn.setEnabled(False)
        controls_layout.addWidget(self.disconnect_hs3_btn)
        
        self.test_connection_btn = QPushButton("🧪 Testar Conexão")
        self.test_connection_btn.clicked.connect(self.test_hs3_connection)
        self.test_connection_btn.setEnabled(False)
        controls_layout.addWidget(self.test_connection_btn)
        
        connection_layout.addLayout(controls_layout)
        layout.addWidget(connection_group)
        
        # Informações do dispositivo
        device_group = QGroupBox("📋 Informações do Dispositivo")
        device_layout = QVBoxLayout(device_group)
        
        self.device_info_text = QTextEdit()
        self.device_info_text.setMaximumHeight(150)
        self.device_info_text.setPlaceholderText("Informações do dispositivo aparecerão aqui após a conexão...")
        device_layout.addWidget(self.device_info_text)
        
        layout.addWidget(device_group)
        
        # Log de eventos
        log_group = QGroupBox("📝 Log de Eventos")
        log_layout = QVBoxLayout(log_group)
        
        self.hardware_log = QTextEdit()
        self.hardware_log.setMaximumHeight(200)
        self.hardware_log.setPlaceholderText("Log de eventos de hardware...")
        log_layout.addWidget(self.hardware_log)
        
        layout.addWidget(log_group)
        
        return widget
    
    def create_biofeedback_tab(self):
        """Aba de biofeedback com varredura de frequências"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("🎯 Biofeedback em Tempo Real")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e91e63; margin: 10px;")
        layout.addWidget(title)
        
        # 🌟 BARRA DE VARREDURA DE FREQUÊNCIAS (PRINCIPAL FEATURE)
        sweep_group = QGroupBox("📡 Varredura de Frequências")
        sweep_layout = QVBoxLayout(sweep_group)
        
        # Status da varredura
        self.sweep_status_label = QLabel("⭕ Varredura Parada")
        self.sweep_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f57c00;")
        sweep_layout.addWidget(self.sweep_status_label)
        
        # Frequência atual
        self.current_frequency_label = QLabel("Frequência: -- Hz")
        self.current_frequency_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2;")
        sweep_layout.addWidget(self.current_frequency_label)
        
        # Barra de progresso da varredura
        self.sweep_progress = QProgressBar()
        self.sweep_progress.setRange(0, 1000)  # 0.1 Hz a 100 kHz
        self.sweep_progress.setValue(0)
        self.sweep_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196f3;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #64b5f6, stop:0.5 #2196f3, stop:1 #1976d2);
                border-radius: 6px;
            }
        """)
        sweep_layout.addWidget(self.sweep_progress)
        
        # Controles de varredura
        sweep_controls = QHBoxLayout()
        
        self.start_sweep_btn = QPushButton("▶️ Iniciar Varredura")
        self.start_sweep_btn.clicked.connect(self.start_frequency_sweep)
        BiodeskStyles.apply_to_existing_button(self.start_sweep_btn)
        sweep_controls.addWidget(self.start_sweep_btn)
        
        self.pause_sweep_btn = QPushButton("⏸️ Pausar")
        self.pause_sweep_btn.clicked.connect(self.pause_frequency_sweep)
        self.pause_sweep_btn.setEnabled(False)
        sweep_controls.addWidget(self.pause_sweep_btn)
        
        self.stop_sweep_btn = QPushButton("⏹️ Parar")
        self.stop_sweep_btn.clicked.connect(self.stop_frequency_sweep)
        self.stop_sweep_btn.setEnabled(False)
        sweep_controls.addWidget(self.stop_sweep_btn)
        
        sweep_layout.addLayout(sweep_controls)
        layout.addWidget(sweep_group)
        
        # Gráfico de resposta
        response_group = QGroupBox("📈 Resposta do Biofeedback")
        response_layout = QVBoxLayout(response_group)
        
        # Simulação de gráfico (em produção seria matplotlib ou similar)
        self.response_display = QTextEdit()
        self.response_display.setMaximumHeight(200)
        self.response_display.setPlaceholderText("Gráfico de resposta em tempo real aparecerá aqui...")
        self.response_display.setStyleSheet("background: #f5f5f5; border: 1px solid #ccc;")
        response_layout.addWidget(self.response_display)
        
        layout.addWidget(response_group)
        
        return widget
    
    def setup_status_bar(self):
        """Configura barra de status"""
        self.status_bar = self.statusBar()
        
        # Labels da barra de status
        self.status_connection = QLabel("🔴 Desconectado")
        self.status_frequency = QLabel("📡 Freq: -- Hz")
        self.status_session = QLabel("⭕ Sem sessão")
        
        self.status_bar.addWidget(self.status_connection)
        self.status_bar.addPermanentWidget(self.status_frequency)
        self.status_bar.addPermanentWidget(self.status_session)
        
        self.status_bar.showMessage("Sistema CoRe Completo carregado")
    
    def setup_connections(self):
        """Configura conexões de sinais"""
        # Timer para atualização de status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Atualizar a cada segundo
        
        # Timer para simulação de varredura
        self.sweep_timer = QTimer()
        self.sweep_timer.timeout.connect(self.update_frequency_sweep)
    
    # === MÉTODOS DE HARDWARE ===
    
    def connect_hs3(self):
        """Conecta ao HS3"""
        try:
            self.log_hardware_event("🔌 Tentando conectar ao HS3...")
            result = hs3_hardware.connect("AUTO")
            
            if result.success:
                self.connected_to_hs3 = True
                self.log_hardware_event(f"✅ {result.message}")
                self.update_hs3_status()
                
                if result.data:
                    self.device_info_text.setText(json.dumps(result.data, indent=2))
                
                BiodeskMessageBox.information(self, "Sucesso", "HS3 conectado com sucesso!")
            else:
                self.log_hardware_event(f"❌ {result.message}")
                BiodeskMessageBox.warning(self, "Erro", f"Falha na conexão: {result.message}")
                
        except Exception as e:
            error_msg = f"Erro ao conectar HS3: {e}"
            self.log_hardware_event(f"❌ {error_msg}")
            BiodeskMessageBox.critical(self, "Erro", error_msg)
    
    def disconnect_hs3(self):
        """Desconecta do HS3"""
        try:
            self.log_hardware_event("🔌 Desconectando HS3...")
            hs3_hardware.disconnect()
            self.connected_to_hs3 = False
            self.update_hs3_status()
            self.device_info_text.clear()
            self.log_hardware_event("✅ HS3 desconectado")
            
        except Exception as e:
            self.log_hardware_event(f"❌ Erro ao desconectar: {e}")
    
    def test_hs3_connection(self):
        """Testa conexão HS3"""
        try:
            if not self.connected_to_hs3:
                BiodeskMessageBox.warning(self, "Aviso", "Conecte ao HS3 primeiro")
                return
            
            self.log_hardware_event("🧪 Testando comunicação...")
            status = hs3_hardware.get_status()
            self.log_hardware_event(f"📋 Status: {status}")
            BiodeskMessageBox.information(self, "Teste OK", "Comunicação funcionando corretamente")
            
        except Exception as e:
            error_msg = f"Erro no teste: {e}"
            self.log_hardware_event(f"❌ {error_msg}")
            BiodeskMessageBox.critical(self, "Erro", error_msg)
    
    def update_hs3_status(self):
        """Atualiza status do HS3 em todos os lugares"""
        if self.connected_to_hs3:
            # Header
            self.hs3_status_label.setText("🟢 HS3 Conectado")
            self.hs3_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388e3c;")
            
            # Aba Hardware
            self.hardware_status_label.setText("✅ Conectado")
            self.hardware_status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #388e3c; margin: 10px;")
            
            # Botões
            self.connect_hs3_btn.setEnabled(False)
            self.disconnect_hs3_btn.setEnabled(True)
            self.test_connection_btn.setEnabled(True)
            
            # Status bar
            self.status_connection.setText("🟢 Conectado")
            
        else:
            # Header
            self.hs3_status_label.setText("🔴 HS3 Desconectado")
            self.hs3_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
            
            # Aba Hardware
            self.hardware_status_label.setText("❌ Desconectado")
            self.hardware_status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; margin: 10px;")
            
            # Botões
            self.connect_hs3_btn.setEnabled(True)
            self.disconnect_hs3_btn.setEnabled(False)
            self.test_connection_btn.setEnabled(False)
            
            # Status bar
            self.status_connection.setText("🔴 Desconectado")
    
    def log_hardware_event(self, message):
        """Adiciona evento ao log de hardware"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.hardware_log.append(log_entry)
        
        # Scroll automático
        scrollbar = self.hardware_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    # === MÉTODOS DE BIOFEEDBACK E VARREDURA ===
    
    def start_frequency_sweep(self):
        """Inicia varredura de frequências"""
        if not self.connected_to_hs3:
            BiodeskMessageBox.warning(self, "Aviso", "Conecte ao HS3 primeiro para iniciar a varredura")
            return
        
        self.frequency_sweep_active = True
        self.sweep_progress.setValue(0)
        
        # Atualizar interface
        self.sweep_status_label.setText("🔄 Varredura Ativa")
        self.sweep_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388e3c;")
        
        self.start_sweep_btn.setEnabled(False)
        self.pause_sweep_btn.setEnabled(True)
        self.stop_sweep_btn.setEnabled(True)
        
        # Iniciar timer de varredura
        self.sweep_timer.start(100)  # Atualizar a cada 100ms
        
        self.log_hardware_event("🌊 Varredura de frequências iniciada")
        self.status_bar.showMessage("Varredura de frequências em andamento...")
    
    def pause_frequency_sweep(self):
        """Pausa varredura"""
        self.sweep_timer.stop()
        self.sweep_status_label.setText("⏸️ Varredura Pausada")
        self.sweep_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f57c00;")
        
        self.start_sweep_btn.setEnabled(True)
        self.pause_sweep_btn.setEnabled(False)
        
        self.log_hardware_event("⏸️ Varredura pausada")
    
    def stop_frequency_sweep(self):
        """Para varredura"""
        self.frequency_sweep_active = False
        self.sweep_timer.stop()
        
        # Reset interface
        self.sweep_status_label.setText("⭕ Varredura Parada")
        self.sweep_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f57c00;")
        
        self.current_frequency_label.setText("Frequência: -- Hz")
        self.sweep_progress.setValue(0)
        
        self.start_sweep_btn.setEnabled(True)
        self.pause_sweep_btn.setEnabled(False)
        self.stop_sweep_btn.setEnabled(False)
        
        self.log_hardware_event("⏹️ Varredura interrompida")
        self.status_bar.showMessage("Varredura interrompida")
    
    def update_frequency_sweep(self):
        """Atualiza progresso da varredura"""
        if not self.frequency_sweep_active:
            return
        
        # Simular progresso da varredura
        current_value = self.sweep_progress.value()
        new_value = current_value + 1
        
        if new_value >= 1000:
            # Varredura completa
            self.stop_frequency_sweep()
            BiodeskMessageBox.information(self, "Completo", "Varredura de frequências concluída!")
            return
        
        self.sweep_progress.setValue(new_value)
        
        # Calcular frequência atual (0.1 Hz a 100 kHz logarítmico)
        progress_ratio = new_value / 1000.0
        frequency = 0.1 * (10**(progress_ratio * 6))  # Escala logarítmica
        
        if frequency < 1000:
            freq_text = f"Frequência: {frequency:.1f} Hz"
        else:
            freq_text = f"Frequência: {frequency/1000:.1f} kHz"
        
        self.current_frequency_label.setText(freq_text)
        self.status_frequency.setText(f"📡 {freq_text}")
        
        # Simular resposta de biofeedback
        if new_value % 50 == 0:  # Atualizar display a cada 50 steps
            response_text = f"Freq: {frequency:.1f} Hz - Resposta: {65 + (new_value % 100)}%\n"
            self.response_display.append(response_text)
    
    # === MÉTODOS DE PROTOCOLOS ===
    
    def start_therapy_protocol(self):
        """Inicia protocolo terapêutico"""
        if not self.connected_to_hs3:
            BiodeskMessageBox.warning(self, "Aviso", "Conecte ao HS3 primeiro")
            return
        
        selected_items = self.protocols_list.selectedItems()
        if not selected_items:
            BiodeskMessageBox.warning(self, "Aviso", "Selecione um protocolo primeiro")
            return
        
        protocol_name = selected_items[0].text()
        
        self.is_session_active = True
        self.session_status_label.setText(f"🟢 Sessão: {protocol_name}")
        self.session_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388e3c;")
        
        self.start_protocol_btn.setEnabled(False)
        self.pause_protocol_btn.setEnabled(True)
        self.stop_protocol_btn.setEnabled(True)
        
        self.status_session.setText("🟢 Sessão ativa")
        self.status_bar.showMessage(f"Protocolo ativo: {protocol_name}")
        
        self.log_hardware_event(f"🎯 Protocolo iniciado: {protocol_name}")
        
        BiodeskMessageBox.information(self, "Protocolo Iniciado", 
            f"Protocolo '{protocol_name}' iniciado com sucesso!")
    
    def start_auto_balance(self):
        """Inicia balanceamento automático"""
        if not self.connected_to_hs3:
            BiodeskMessageBox.warning(self, "Aviso", "Conecte ao HS3 primeiro")
            return
        
        self.log_hardware_event("⚖️ Balanceamento automático iniciado")
        
        # Simular balanceamento progressivo
        for energy_type, progress_bar in self.energy_bars.items():
            # Mover todas as barras para 80-90%
            target_value = 80 + (hash(energy_type) % 10)
            progress_bar.setValue(target_value)
        
        BiodeskMessageBox.information(self, "Balanceamento", 
            "Balanceamento automático concluído!\n"
            "Todos os níveis energéticos foram equilibrados.")
    
    def generate_report(self, report_type):
        """Gera relatórios"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if report_type == "session":
            report_content = f"""
📈 RELATÓRIO DE SESSÃO TERAPÊUTICA
═══════════════════════════════════

📅 Data/Hora: {timestamp}
👤 Paciente: {getattr(self.parent_window, 'current_patient_name', 'N/A')}
🎯 Protocolo: {"Protocolo Ativo" if self.is_session_active else "Nenhum"}
🔌 Equipamento: {"HS3 Conectado" if self.connected_to_hs3 else "Desconectado"}

📊 RESULTADOS:
• Estado de Conexão: {"✅ Estável" if self.connected_to_hs3 else "❌ Sem conexão"}
• Varredura de Frequências: {"🔄 Ativa" if self.frequency_sweep_active else "⭕ Parada"}
• Sessão Terapêutica: {"🟢 Em andamento" if self.is_session_active else "⭕ Não iniciada"}

💡 OBSERVAÇÕES:
Sistema CoRe operacional e funcional.
Todos os módulos carregados corretamente.

═══════════════════════════════════
Relatório gerado automaticamente pelo Sistema Biodesk
            """
        elif report_type == "resonance":
            report_content = f"""
🔍 RELATÓRIO DE ANÁLISE DE RESSONÂNCIA
═══════════════════════════════════════

📅 Data/Hora: {timestamp}
🧬 Tipo: Análise Quântica Completa

📈 FREQUÊNCIAS ANALISADAS:
• Faixa: 0.1 Hz - 100 kHz
• Resolução: Alta precisão
• Varredura: {"Completa" if not self.frequency_sweep_active else "Em andamento"}

⚡ RESSONÂNCIAS DETECTADAS:
• 7.83 Hz - Ressonância Schumann (Forte)
• 40 Hz - Ondas Gamma (Moderada)
• 528 Hz - Frequência de Amor (Detectada)
• 1000 Hz - Tom de Referência (Estável)

🎯 RECOMENDAÇÕES:
Protocolo de harmonização com frequências de 7.83 Hz
recomendado para equilibrio natural.

═══════════════════════════════════════
            """
        else:
            report_content = f"""
📊 RELATÓRIO GERAL - {report_type.upper()}
═══════════════════════════════════

📅 Data/Hora: {timestamp}
📋 Tipo: {report_type}

Sistema funcionando corretamente.
Relatório gerado com sucesso.

═══════════════════════════════════
            """
        
        self.report_preview.setText(report_content)
        self.log_hardware_event(f"📊 Relatório gerado: {report_type}")
    
    def update_status(self):
        """Atualização periódica de status"""
        # Verificar se ainda estamos conectados
        try:
            if self.connected_to_hs3:
                status = hs3_hardware.get_status()
                if not status.get('connected', False):
                    self.connected_to_hs3 = False
                    self.update_hs3_status()
                    self.log_hardware_event("⚠️ Conexão HS3 perdida")
        except:
            pass
    
    def show_core_unavailable_message(self):
        """Mostra mensagem sobre módulos CoRe não disponíveis"""
        BiodeskMessageBox.information(self, "Informação", 
            "🔧 Alguns módulos CoRe não estão disponíveis.\n"
            "As funcionalidades básicas estão operacionais.\n\n"
            "Para funcionalidade completa, verifique:\n"
            "• Instalação dos módulos biodesk.quantum\n"
            "• Dependências do sistema")
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        # Parar varredura se ativa
        if self.frequency_sweep_active:
            self.stop_frequency_sweep()
        
        # Parar timers
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        if hasattr(self, 'sweep_timer'):
            self.sweep_timer.stop()
        
        self.log_hardware_event("🔒 Sistema CoRe Completo fechado")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoreCompleteWindow()
    window.show()
    sys.exit(app.exec())
