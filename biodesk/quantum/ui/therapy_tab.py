"""
UI Principal da Terapia Quântica - Biodesk
═══════════════════════════════════════════════════════════════════════

Interface principal do módulo de Terapia Quântica com layout completo:
- Protocolo: Seleção e configuração
- Execução: Controles e progresso  
- Monitorização: Gráficos tempo-real
- Registo: Log de sessão e exportação
- Avaliação: Assessment e ranking
"""

import logging
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QGroupBox, QLabel, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem,
    QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
    QProgressBar, QTextEdit, QSplitter, QFrame,
    QHeaderView, QAbstractItemView, QMessageBox,
    QFileDialog, QToolButton, QButtonGroup
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, QMutex,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette

# PyQtGraph para gráficos tempo-real
try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget, PlotItem, mkPen
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("⚠️ PyQtGraph não disponível - gráficos desabilitados")

# Imports do sistema Biodesk
from biodesk_styles import aplicar_estilos
from biodesk_ui_kit import criar_botao, criar_grupo


class ProtocolConfigWidget(QGroupBox):
    """Widget de configuração de protocolo"""
    
    protocol_changed = pyqtSignal(dict)  # protocol_config
    
    def __init__(self):
        super().__init__("📋 Configuração do Protocolo")
        self.logger = logging.getLogger("ProtocolConfig")
        self.current_protocol = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Seleção de doença/condição
        disease_layout = QHBoxLayout()
        disease_layout.addWidget(QLabel("Condição:"))
        
        self.disease_combo = QComboBox()
        self.disease_combo.setEditable(True)
        self.disease_combo.setPlaceholderText("Digite ou selecione uma condição...")
        self.disease_combo.currentTextChanged.connect(self._on_disease_changed)
        disease_layout.addWidget(self.disease_combo)
        
        self.load_protocol_btn = QPushButton("📥 Carregar")
        self.load_protocol_btn.clicked.connect(self._load_protocol)
        disease_layout.addWidget(self.load_protocol_btn)
        
        layout.addLayout(disease_layout)
        
        # Tabela de passos do protocolo
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(5)
        self.steps_table.setHorizontalHeaderLabels([
            "Passo", "Frequência (Hz)", "Amplitude (V)", "Duração (s)", "Forma"
        ])
        
        # Configurar tabela
        header = self.steps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.steps_table.setAlternatingRowColors(True)
        self.steps_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.steps_table)
        
        # Opções de execução
        options_group = QGroupBox("⚙️ Opções de Execução")
        options_layout = QGridLayout(options_group)
        
        # Modo de execução
        options_layout.addWidget(QLabel("Modo:"), 0, 0)
        self.sequential_radio = QRadioButton("Sequencial")
        self.random_radio = QRadioButton("Aleatório")
        self.sequential_radio.setChecked(True)
        
        mode_group = QButtonGroup()
        mode_group.addButton(self.sequential_radio)
        mode_group.addButton(self.random_radio)
        
        options_layout.addWidget(self.sequential_radio, 0, 1)
        options_layout.addWidget(self.random_radio, 0, 2)
        
        # Tempo de permanência padrão
        options_layout.addWidget(QLabel("Dwell padrão (s):"), 1, 0)
        self.dwell_spin = QDoubleSpinBox()
        self.dwell_spin.setRange(0.1, 300.0)
        self.dwell_spin.setValue(3.0)
        self.dwell_spin.setSuffix(" s")
        options_layout.addWidget(self.dwell_spin, 1, 1)
        
        # Pausa entre frequências
        options_layout.addWidget(QLabel("Pausa (s):"), 1, 2)
        self.pause_spin = QDoubleSpinBox()
        self.pause_spin.setRange(0.0, 60.0)
        self.pause_spin.setValue(0.5)
        self.pause_spin.setSuffix(" s")
        options_layout.addWidget(self.pause_spin, 1, 3)
        
        # Forma de onda padrão
        options_layout.addWidget(QLabel("Forma:"), 2, 0)
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(["sine", "square", "triangle", "sawtooth"])
        options_layout.addWidget(self.waveform_combo, 2, 1)
        
        # Amplitude padrão
        options_layout.addWidget(QLabel("Amplitude (V):"), 2, 2)
        self.amplitude_spin = QDoubleSpinBox()
        self.amplitude_spin.setRange(0.1, 5.0)
        self.amplitude_spin.setValue(1.0)
        self.amplitude_spin.setSuffix(" V")
        options_layout.addWidget(self.amplitude_spin, 2, 3)
        
        # Rampa suave
        self.ramp_checkbox = QCheckBox("Rampa suave")
        self.ramp_checkbox.setChecked(True)
        options_layout.addWidget(self.ramp_checkbox, 3, 0, 1, 2)
        
        layout.addWidget(options_group)
        
        # Conectar sinais
        for widget in [self.dwell_spin, self.pause_spin, self.amplitude_spin,
                      self.waveform_combo, self.ramp_checkbox]:
            if hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(self._emit_protocol_changed)
            elif hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(self._emit_protocol_changed)
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(self._emit_protocol_changed)
    
    def load_diseases_from_excel(self, diseases: List[str]):
        """Carregar lista de doenças do Excel"""
        self.disease_combo.clear()
        self.disease_combo.addItems(sorted(diseases))
        self.logger.info(f"Carregadas {len(diseases)} condições")
    
    def _on_disease_changed(self, disease_name: str):
        """Doença selecionada mudou"""
        if disease_name.strip():
            self.logger.info(f"Condição selecionada: {disease_name}")
    
    def _load_protocol(self):
        """Carregar protocolo para a doença selecionada"""
        disease = self.disease_combo.currentText().strip()
        if not disease:
            QMessageBox.warning(self, "Aviso", "Selecione uma condição primeiro")
            return
        
        # TODO: Integrar com ExcelFrequencyParser
        self.logger.info(f"Carregando protocolo para: {disease}")
        # Emitir sinal para carregamento
        
    def set_protocol_steps(self, steps: List[Dict]):
        """Definir passos do protocolo"""
        self.steps_table.setRowCount(len(steps))
        
        for row, step in enumerate(steps):
            self.steps_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.steps_table.setItem(row, 1, QTableWidgetItem(f"{step.get('frequency', 0):.2f}"))
            self.steps_table.setItem(row, 2, QTableWidgetItem(f"{step.get('amplitude', 1.0):.2f}"))
            self.steps_table.setItem(row, 3, QTableWidgetItem(f"{step.get('duration', 3.0):.1f}"))
            self.steps_table.setItem(row, 4, QTableWidgetItem(step.get('waveform', 'sine')))
        
        self.current_protocol = steps
        self._emit_protocol_changed()
    
    def _emit_protocol_changed(self):
        """Emitir sinal de mudança de protocolo"""
        config = {
            'steps': self.current_protocol or [],
            'sequential': self.sequential_radio.isChecked(),
            'default_dwell': self.dwell_spin.value(),
            'pause_between': self.pause_spin.value(),
            'default_waveform': self.waveform_combo.currentText(),
            'default_amplitude': self.amplitude_spin.value(),
            'soft_ramp': self.ramp_checkbox.isChecked()
        }
        self.protocol_changed.emit(config)


class ExecutionControlWidget(QGroupBox):
    """Widget de controle de execução"""
    
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    emergency_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__("▶️ Controle de Execução")
        self.execution_state = "idle"  # idle, running, paused, stopped
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Botões de controle
        buttons_layout = QHBoxLayout()
        
        self.start_btn = criar_botao("▶️ Iniciar", "primary")
        self.start_btn.clicked.connect(self.start_requested.emit)
        buttons_layout.addWidget(self.start_btn)
        
        self.pause_btn = criar_botao("⏸️ Pausar", "secondary")
        self.pause_btn.clicked.connect(self.pause_requested.emit)
        self.pause_btn.setEnabled(False)
        buttons_layout.addWidget(self.pause_btn)
        
        self.stop_btn = criar_botao("⏹️ Parar", "secondary")
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        # Botão de emergência - destaque especial
        self.emergency_btn = QPushButton("🚨 EMERGÊNCIA")
        self.emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 2px solid #c0392b;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.emergency_btn.clicked.connect(self.emergency_requested.emit)
        buttons_layout.addWidget(self.emergency_btn)
        
        layout.addLayout(buttons_layout)
        
        # Progresso do passo atual
        step_group = QGroupBox("Passo Atual")
        step_layout = QVBoxLayout(step_group)
        
        self.current_step_label = QLabel("Aguardando início...")
        self.current_step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_layout.addWidget(self.current_step_label)
        
        self.step_progress = QProgressBar()
        self.step_progress.setVisible(False)
        step_layout.addWidget(self.step_progress)
        
        layout.addWidget(step_group)
        
        # Progresso total
        total_group = QGroupBox("Progresso Total")
        total_layout = QVBoxLayout(total_group)
        
        self.total_progress_label = QLabel("0 / 0 passos")
        self.total_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(self.total_progress_label)
        
        self.total_progress = QProgressBar()
        total_layout.addWidget(self.total_progress)
        
        # Tempo estimado
        self.time_label = QLabel("Tempo estimado: --:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(self.time_label)
        
        layout.addWidget(total_group)
    
    def set_execution_state(self, state: str):
        """Definir estado de execução"""
        self.execution_state = state
        
        if state == "idle":
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.start_btn.setText("▶️ Iniciar")
            
        elif state == "running":
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
        elif state == "paused":
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.start_btn.setText("▶️ Retomar")
            
        elif state == "stopped":
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.start_btn.setText("▶️ Iniciar")
    
    def update_step_progress(self, step_info: Dict):
        """Atualizar progresso do passo atual"""
        frequency = step_info.get('frequency', 0)
        duration = step_info.get('duration', 0)
        elapsed = step_info.get('elapsed', 0)
        
        self.current_step_label.setText(
            f"Frequência: {frequency:.1f}Hz | {elapsed:.1f}s / {duration:.1f}s"
        )
        
        if duration > 0:
            progress = int((elapsed / duration) * 100)
            self.step_progress.setValue(progress)
            self.step_progress.setVisible(True)
        else:
            self.step_progress.setVisible(False)
    
    def update_total_progress(self, current_step: int, total_steps: int, 
                            estimated_time: float = 0):
        """Atualizar progresso total"""
        self.total_progress_label.setText(f"{current_step} / {total_steps} passos")
        
        if total_steps > 0:
            progress = int((current_step / total_steps) * 100)
            self.total_progress.setValue(progress)
        
        if estimated_time > 0:
            minutes = int(estimated_time // 60)
            seconds = int(estimated_time % 60)
            self.time_label.setText(f"Tempo estimado: {minutes:02d}:{seconds:02d}")


class MonitoringWidget(QGroupBox):
    """Widget de monitorização em tempo real"""
    
    def __init__(self):
        super().__init__("📊 Monitorização em Tempo Real")
        self.logger = logging.getLogger("Monitoring")
        self.plot_data = {
            'time': [],
            'rms': [],
            'vpp': [],
            'dc': [],
            'impedance': [],
            'frequency': []
        }
        self.max_points = 1000  # Máximo de pontos no gráfico
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        if not PYQTGRAPH_AVAILABLE:
            # Fallback se PyQtGraph não disponível
            fallback_label = QLabel("⚠️ PyQtGraph não disponível\nGráficos desabilitados")
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet("color: orange; font-weight: bold;")
            layout.addWidget(fallback_label)
            return
        
        # Configurar gráfico principal
        self.plot_widget = PlotWidget()
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Tempo (s)')
        self.plot_widget.setTitle('Sinais em Tempo Real')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMinimumHeight(300)
        
        # Configurar curvas
        self.curves = {}
        colors = {'rms': 'r', 'vpp': 'g', 'dc': 'b', 'impedance': 'y'}
        
        for signal, color in colors.items():
            self.curves[signal] = self.plot_widget.plot(
                pen=mkPen(color, width=2),
                name=signal.upper()
            )
        
        # Adicionar legenda
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
        
        # Painel de valores atuais
        values_group = QGroupBox("Valores Atuais")
        values_layout = QGridLayout(values_group)
        
        self.value_labels = {}
        labels = [
            ('frequency', 'Freq. (Hz)', 0, 0),
            ('rms', 'RMS (mV)', 0, 1),
            ('vpp', 'Vpp (mV)', 0, 2),
            ('dc', 'DC (mV)', 1, 0),
            ('impedance', 'Z (Ω)', 1, 1),
            ('current', 'I (mA)', 1, 2)
        ]
        
        for key, text, row, col in labels:
            label = QLabel(text + ":")
            value_label = QLabel("--")
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            
            values_layout.addWidget(label, row * 2, col)
            values_layout.addWidget(value_label, row * 2 + 1, col)
            
            self.value_labels[key] = value_label
        
        layout.addWidget(values_group)
    
    def add_data_point(self, timestamp: float, measurements: Dict):
        """Adicionar ponto de dados ao gráfico"""
        if not PYQTGRAPH_AVAILABLE:
            return
        
        # Adicionar aos dados
        self.plot_data['time'].append(timestamp)
        self.plot_data['rms'].append(measurements.get('rms', 0) * 1000)  # mV
        self.plot_data['vpp'].append(measurements.get('vpp', 0) * 1000)  # mV
        self.plot_data['dc'].append(measurements.get('dc', 0) * 1000)    # mV
        self.plot_data['impedance'].append(measurements.get('impedance', 0))  # Ω
        self.plot_data['frequency'].append(measurements.get('frequency', 0))
        
        # Limitar número de pontos
        if len(self.plot_data['time']) > self.max_points:
            for key in self.plot_data:
                self.plot_data[key] = self.plot_data[key][-self.max_points:]
        
        # Atualizar gráficos
        time_data = self.plot_data['time']
        for signal, curve in self.curves.items():
            if signal in self.plot_data:
                curve.setData(time_data, self.plot_data[signal])
        
        # Atualizar valores atuais
        self.value_labels['frequency'].setText(f"{measurements.get('frequency', 0):.1f}")
        self.value_labels['rms'].setText(f"{measurements.get('rms', 0)*1000:.2f}")
        self.value_labels['vpp'].setText(f"{measurements.get('vpp', 0)*1000:.2f}")
        self.value_labels['dc'].setText(f"{measurements.get('dc', 0)*1000:.2f}")
        self.value_labels['impedance'].setText(f"{measurements.get('impedance', 0):.0f}")
        self.value_labels['current'].setText(f"{measurements.get('current', 0)*1000:.3f}")
    
    def clear_data(self):
        """Limpar dados do gráfico"""
        for key in self.plot_data:
            self.plot_data[key].clear()
        
        if PYQTGRAPH_AVAILABLE:
            for curve in self.curves.values():
                curve.clear()
        
        for label in self.value_labels.values():
            label.setText("--")


class SessionLogWidget(QGroupBox):
    """Widget de registo de sessão"""
    
    export_requested = pyqtSignal(str)  # file_path
    
    def __init__(self):
        super().__init__("📝 Registo da Sessão")
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Exportar CSV")
        self.export_btn.clicked.connect(self._export_session)
        toolbar_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("🗑️ Limpar")
        self.clear_btn.clicked.connect(self._clear_log)
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addStretch()
        
        # Contador de entradas
        self.count_label = QLabel("0 entradas")
        toolbar_layout.addWidget(self.count_label)
        
        layout.addLayout(toolbar_layout)
        
        # Tabela de registo
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels([
            "Hora", "Frequência (Hz)", "Amplitude (V)", 
            "RMS Medido (mV)", "Status", "Notas"
        ])
        
        # Configurar tabela
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSortingEnabled(True)
        
        layout.addWidget(self.log_table)
    
    def add_log_entry(self, timestamp: datetime, frequency: float, 
                     amplitude: float, rms_measured: float, 
                     status: str = "OK", notes: str = ""):
        """Adicionar entrada ao registo"""
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        
        # Formatar timestamp
        time_str = timestamp.strftime("%H:%M:%S")
        
        # Adicionar dados
        self.log_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.log_table.setItem(row, 1, QTableWidgetItem(f"{frequency:.2f}"))
        self.log_table.setItem(row, 2, QTableWidgetItem(f"{amplitude:.2f}"))
        self.log_table.setItem(row, 3, QTableWidgetItem(f"{rms_measured*1000:.2f}"))
        self.log_table.setItem(row, 4, QTableWidgetItem(status))
        self.log_table.setItem(row, 5, QTableWidgetItem(notes))
        
        # Rolar para o final
        self.log_table.scrollToBottom()
        
        # Atualizar contador
        self.count_label.setText(f"{row + 1} entradas")
    
    def _export_session(self):
        """Exportar sessão para CSV"""
        if self.log_table.rowCount() == 0:
            QMessageBox.information(self, "Info", "Nenhum dado para exportar")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Sessão", 
            f"sessao_terapia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            self.export_requested.emit(file_path)
    
    def _clear_log(self):
        """Limpar registo"""
        reply = QMessageBox.question(
            self, "Confirmar", 
            "Limpar todo o registo da sessão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_table.setRowCount(0)
            self.count_label.setText("0 entradas")


class InterlocksPanel(QWidget):
    """Painel de estado dos interlocks"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔒 Estado dos Interlocks")
        self.setFixedSize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Estado dos Sistemas de Segurança")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Estados dos interlocks
        self.status_labels = {}
        
        interlocks = [
            ('isolation', '🔌 Isolação Confirmada'),
            ('resistor', '⚡ Resistor Série'),
            ('pedal', '🦶 Pedal/Trigger'),
            ('patient', '👤 Estado do Paciente'),
            ('hardware', '🔧 Hardware HS3'),
            ('emergency', '🚨 Sistema Emergência')
        ]
        
        for key, text in interlocks:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame_layout = QHBoxLayout(frame)
            
            label = QLabel(text)
            frame_layout.addWidget(label)
            
            status_label = QLabel("❌ Não Verificado")
            status_label.setStyleSheet("color: red; font-weight: bold;")
            frame_layout.addWidget(status_label)
            frame_layout.addStretch()
            
            self.status_labels[key] = status_label
            layout.addWidget(frame)
        
        layout.addStretch()
        
        # Botão de atualização
        refresh_btn = QPushButton("🔄 Atualizar Estado")
        refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(refresh_btn)
    
    def set_interlock_status(self, key: str, status: bool, message: str = ""):
        """Definir estado de um interlock"""
        if key in self.status_labels:
            if status:
                self.status_labels[key].setText(f"✅ {message or 'OK'}")
                self.status_labels[key].setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_labels[key].setText(f"❌ {message or 'Falha'}")
                self.status_labels[key].setStyleSheet("color: red; font-weight: bold;")
    
    def refresh_status(self):
        """Atualizar estado dos interlocks"""
        # TODO: Integrar com sistemas reais
        pass


class AssessmentTab(QWidget):
    """Aba de avaliação (Assessment Worker)"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface da avaliação"""
        layout = QVBoxLayout(self)
        
        # TODO: Implementar interface completa do Assessment Worker
        placeholder = QLabel("🔬 Sistema de Avaliação\n\n"
                            "TODO: Implementar interface completa:\n"
                            "- Configuração de baseline\n"
                            "- Fila de teste\n"
                            "- Ranking Top-N\n"
                            "- Botão 'Enviar para Balancing'")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder)


class TherapyTabWidget(QWidget):
    """Widget principal da aba Terapia Quântica"""
    
    # Sinais para comunicação com sistema principal
    protocol_load_requested = pyqtSignal(str)  # disease_name
    execution_started = pyqtSignal(dict)       # protocol_config
    execution_paused = pyqtSignal()
    execution_stopped = pyqtSignal()
    emergency_triggered = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("TherapyTab")
        
        # Estado interno
        self.current_protocol = None
        self.execution_active = False
        self.interlocks_panel = None
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Configurar interface principal"""
        # Layout principal
        main_layout = QHBoxLayout(self)
        
        # Splitter principal (esquerda / direita)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === LADO ESQUERDO: Protocolo ===
        self.protocol_widget = ProtocolConfigWidget()
        main_splitter.addWidget(self.protocol_widget)
        
        # === LADO DIREITO: Execução + Monitorização + Registo ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Execução (topo)
        self.execution_widget = ExecutionControlWidget()
        right_layout.addWidget(self.execution_widget)
        
        # Splitter vertical (monitorização / registo)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Monitorização
        self.monitoring_widget = MonitoringWidget()
        right_splitter.addWidget(self.monitoring_widget)
        
        # Tabs para registo e avaliação
        bottom_tabs = QTabWidget()
        
        # Aba de registo
        self.session_log_widget = SessionLogWidget()
        bottom_tabs.addTab(self.session_log_widget, "📝 Registo")
        
        # Aba de avaliação
        self.assessment_tab = AssessmentTab()
        bottom_tabs.addTab(self.assessment_tab, "🔬 Avaliação")
        
        right_splitter.addWidget(bottom_tabs)
        
        right_layout.addWidget(right_splitter)
        main_splitter.addWidget(right_widget)
        
        # Configurar proporções
        main_splitter.setSizes([400, 800])  # 1/3 esquerda, 2/3 direita
        right_splitter.setSizes([400, 300])  # Monitorização maior que registo
        
        main_layout.addWidget(main_splitter)
        
        # Barra de ferramentas adicional
        self.add_toolbar()
        
    def add_toolbar(self):
        """Adicionar barra de ferramentas"""
        # Encontrar layout principal
        main_layout = self.layout()
        
        # Criar toolbar
        toolbar_layout = QHBoxLayout()
        
        # Botão de interlocks
        self.interlocks_btn = QPushButton("🔒 Interlocks")
        self.interlocks_btn.clicked.connect(self.show_interlocks)
        toolbar_layout.addWidget(self.interlocks_btn)
        
        # Status de conexão
        self.connection_label = QLabel("🔴 Desconectado")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        toolbar_layout.addWidget(self.connection_label)
        
        toolbar_layout.addStretch()
        
        # Inserir toolbar no topo
        main_layout.insertLayout(0, toolbar_layout)
    
    def connect_signals(self):
        """Conectar sinais internos"""
        # Protocolo
        self.protocol_widget.protocol_changed.connect(self._on_protocol_changed)
        
        # Execução
        self.execution_widget.start_requested.connect(self._start_execution)
        self.execution_widget.pause_requested.connect(self._pause_execution)
        self.execution_widget.stop_requested.connect(self._stop_execution)
        self.execution_widget.emergency_requested.connect(self._emergency_stop)
        
        # Registo
        self.session_log_widget.export_requested.connect(self._export_session)
    
    def _on_protocol_changed(self, config: Dict):
        """Protocolo foi alterado"""
        self.current_protocol = config
        self.logger.info(f"Protocolo atualizado: {len(config.get('steps', []))} passos")
    
    def _start_execution(self):
        """Iniciar execução"""
        if not self.current_protocol or not self.current_protocol.get('steps'):
            QMessageBox.warning(self, "Aviso", "Carregue um protocolo primeiro")
            return
        
        # TODO: Verificar interlocks
        
        self.execution_active = True
        self.execution_widget.set_execution_state("running")
        self.execution_started.emit(self.current_protocol)
        self.logger.info("Execução iniciada")
    
    def _pause_execution(self):
        """Pausar execução"""
        self.execution_widget.set_execution_state("paused")
        self.execution_paused.emit()
        self.logger.info("Execução pausada")
    
    def _stop_execution(self):
        """Parar execução"""
        self.execution_active = False
        self.execution_widget.set_execution_state("stopped")
        self.execution_stopped.emit()
        self.logger.info("Execução parada")
    
    def _emergency_stop(self):
        """Parada de emergência"""
        self.execution_active = False
        self.execution_widget.set_execution_state("stopped")
        self.emergency_triggered.emit()
        
        # Mostrar alerta visual
        QMessageBox.critical(self, "EMERGÊNCIA", 
                           "🚨 PARADA DE EMERGÊNCIA ATIVADA\n\n"
                           "Todos os sistemas foram desligados.")
        self.logger.critical("PARADA DE EMERGÊNCIA ATIVADA")
    
    def show_interlocks(self):
        """Mostrar painel de interlocks"""
        if not self.interlocks_panel:
            self.interlocks_panel = InterlocksPanel()
        
        self.interlocks_panel.show()
        self.interlocks_panel.raise_()
    
    def _export_session(self, file_path: str):
        """Exportar sessão para arquivo"""
        # TODO: Implementar exportação real
        self.logger.info(f"Exportando sessão para: {file_path}")
    
    def set_connection_status(self, connected: bool, device_info: str = ""):
        """Definir estado de conexão"""
        if connected:
            self.connection_label.setText(f"🟢 Conectado: {device_info}")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("🔴 Desconectado")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
    
    def update_monitoring_data(self, measurements: Dict):
        """Atualizar dados de monitorização"""
        import time
        self.monitoring_widget.add_data_point(time.time(), measurements)
    
    def update_execution_progress(self, step_info: Dict, total_info: Dict):
        """Atualizar progresso de execução"""
        self.execution_widget.update_step_progress(step_info)
        self.execution_widget.update_total_progress(
            total_info.get('current_step', 0),
            total_info.get('total_steps', 0),
            total_info.get('estimated_time', 0)
        )


# ═══════════════════════════════════════════════════════════════════════
# TESTES E DEMONSTRAÇÃO
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Criar aplicação
    app = QApplication(sys.argv)
    
    # Aplicar estilos
    try:
        aplicar_estilos(app)
    except:
        pass  # Ignorar se biodesk_styles não disponível
    
    # Criar e mostrar widget
    therapy_tab = TherapyTabWidget()
    therapy_tab.setWindowTitle("🧬 Terapia Quântica - Demo")
    therapy_tab.resize(1200, 800)
    therapy_tab.show()
    
    # Simular alguns dados para demonstração
    import random
    import time
    from PyQt6.QtCore import QTimer
    
    # Timer para simular dados
    def simulate_data():
        measurements = {
            'frequency': random.uniform(100, 1000),
            'rms': random.uniform(0.001, 0.01),
            'vpp': random.uniform(0.002, 0.02),
            'dc': random.uniform(-0.001, 0.001),
            'impedance': random.uniform(500, 2000),
            'current': random.uniform(0.001, 0.005)
        }
        therapy_tab.update_monitoring_data(measurements)
        
        # Simular entrada de log ocasional
        if random.random() < 0.1:  # 10% de chance
            from datetime import datetime
            therapy_tab.session_log_widget.add_log_entry(
                datetime.now(),
                measurements['frequency'],
                1.0,  # amplitude
                measurements['rms'],
                "OK"
            )
    
    # Configurar timer
    timer = QTimer()
    timer.timeout.connect(simulate_data)
    timer.start(500)  # 500ms
    
    # Simular protocolo
    demo_steps = [
        {'frequency': 100.0, 'amplitude': 1.0, 'duration': 3.0, 'waveform': 'sine'},
        {'frequency': 200.0, 'amplitude': 1.0, 'duration': 3.0, 'waveform': 'sine'},
        {'frequency': 300.0, 'amplitude': 1.0, 'duration': 3.0, 'waveform': 'sine'},
    ]
    therapy_tab.protocol_widget.set_protocol_steps(demo_steps)
    
    # Simular conexão
    therapy_tab.set_connection_status(True, "HS3 Demo")
    
    # Executar aplicação
    sys.exit(app.exec())
