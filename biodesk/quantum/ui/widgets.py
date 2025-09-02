"""
Widgets Auxiliares para Terapia Quântica - Biodesk
═══════════════════════════════════════════════════════════════════════

Coleção de widgets especializados para interface de terapia quântica.
Inclui componentes reutilizáveis e customizados.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QRadioButton, QTextEdit,
    QProgressBar, QSlider, QDial, QLCDNumber,
    QFrame, QGroupBox, QTabWidget, QSplitter,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QScrollArea,
    QHeaderView, QAbstractItemView, QMessageBox,
    QFileDialog, QColorDialog, QFontDialog,
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QStyleOptionButton, QStyle, QPainter
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, QMutex, QWaitCondition,
    pyqtSignal, QPropertyAnimation, QEasingCurve,
    QRect, QPoint, QSize, QRectF, QPointF
)
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QPalette, QPen, QBrush,
    QColor, QPainter, QLinearGradient, QRadialGradient,
    QPolygonF, QPainterPath
)


class StatusIndicator(QWidget):
    """Indicador visual de status com cores e animações"""
    
    class Status(Enum):
        OK = "ok"
        WARNING = "warning"
        ERROR = "error"
        UNKNOWN = "unknown"
        DISABLED = "disabled"
    
    def __init__(self, size: int = 20):
        super().__init__()
        self.setFixedSize(size, size)
        self._status = self.Status.UNKNOWN
        self._animated = False
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self.update)
        self._animation_phase = 0
        
    def set_status(self, status: Status, animated: bool = False):
        """Definir status do indicador"""
        self._status = status
        self._animated = animated
        
        if animated:
            self._animation_timer.start(100)  # 10 FPS
        else:
            self._animation_timer.stop()
        
        self.update()
    
    def paintEvent(self, event):
        """Desenhar indicador"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Escolher cor baseada no status
        colors = {
            self.Status.OK: QColor(46, 204, 113),      # Verde
            self.Status.WARNING: QColor(241, 196, 15),  # Amarelo
            self.Status.ERROR: QColor(231, 76, 60),     # Vermelho
            self.Status.UNKNOWN: QColor(149, 165, 166), # Cinza
            self.Status.DISABLED: QColor(189, 195, 199) # Cinza claro
        }
        
        base_color = colors.get(self._status, colors[self.Status.UNKNOWN])
        
        # Aplicar animação se ativada
        if self._animated:
            self._animation_phase = (self._animation_phase + 1) % 20
            alpha = int(128 + 127 * abs(10 - self._animation_phase) / 10)
            base_color.setAlpha(alpha)
        
        # Desenhar círculo
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.setBrush(QBrush(base_color))
        painter.setPen(QPen(base_color.darker(), 1))
        painter.drawEllipse(rect)


class FrequencyDisplay(QLCDNumber):
    """Display LCD para frequência com formatação automática"""
    
    def __init__(self, digits: int = 8):
        super().__init__(digits)
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.setStyleSheet("""
            QLCDNumber {
                background-color: #2c3e50;
                color: #3498db;
                border: 2px solid #34495e;
                border-radius: 5px;
            }
        """)
        self._frequency = 0.0
        
    def set_frequency(self, freq_hz: float):
        """Definir frequência com formatação automática"""
        self._frequency = freq_hz
        
        if freq_hz >= 1000:
            # Mostrar em kHz
            self.display(f"{freq_hz/1000:.3f}")
        elif freq_hz >= 1:
            # Mostrar em Hz com decimais
            self.display(f"{freq_hz:.2f}")
        else:
            # Mostrar com mais decimais para frequências baixas
            self.display(f"{freq_hz:.4f}")


class AmplitudeKnob(QDial):
    """Knob rotativo para controle de amplitude"""
    
    value_changed = pyqtSignal(float)  # amplitude_vpp
    
    def __init__(self, min_v: float = 0.0, max_v: float = 5.0):
        super().__init__()
        self.min_voltage = min_v
        self.max_voltage = max_v
        
        # Configurar dial
        self.setRange(0, 1000)  # Resolução interna
        self.setValue(int(1000 * min_v / max_v))  # Valor inicial
        self.setNotchesVisible(True)
        self.setWrapping(False)
        
        # Conectar sinal
        self.valueChanged.connect(self._on_value_changed)
        
        # Estilo
        self.setStyleSheet("""
            QDial {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 50px;
            }
            QDial::handle {
                background-color: #3498db;
                border: 2px solid #2980b9;
                border-radius: 8px;
                width: 16px;
                height: 16px;
            }
        """)
    
    def _on_value_changed(self, raw_value: int):
        """Converter valor interno para voltagem"""
        voltage = self.min_voltage + (raw_value / 1000.0) * (self.max_voltage - self.min_voltage)
        self.value_changed.emit(voltage)
    
    def set_voltage(self, voltage: float):
        """Definir voltagem externamente"""
        if self.min_voltage <= voltage <= self.max_voltage:
            raw_value = int(1000 * (voltage - self.min_voltage) / (self.max_voltage - self.min_voltage))
            self.blockSignals(True)
            self.setValue(raw_value)
            self.blockSignals(False)


class WaveformSelector(QWidget):
    """Seletor visual de forma de onda"""
    
    waveform_changed = pyqtSignal(str)  # waveform_type
    
    def __init__(self):
        super().__init__()
        self._current_waveform = "sine"
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        
        # Botões para cada forma de onda
        waveforms = [
            ("sine", "Seno", "🌊"),
            ("square", "Quadrada", "⬜"),
            ("triangle", "Triangular", "🔺"),
            ("sawtooth", "Dente de Serra", "📈")
        ]
        
        self.buttons = {}
        
        for waveform, name, icon in waveforms:
            btn = QPushButton(f"{icon}\n{name}")
            btn.setCheckable(True)
            btn.setFixedSize(80, 60)
            btn.clicked.connect(lambda checked, w=waveform: self._select_waveform(w))
            
            self.buttons[waveform] = btn
            layout.addWidget(btn)
        
        # Selecionar seno por padrão
        self.buttons["sine"].setChecked(True)
        
        # Estilo dos botões
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #ecf0f1;
                font-size: 10px;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
                border-color: #2980b9;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:checked:hover {
                background-color: #2980b9;
            }
        """)
    
    def _select_waveform(self, waveform: str):
        """Selecionar forma de onda"""
        # Desmarcar todos os botões
        for btn in self.buttons.values():
            btn.setChecked(False)
        
        # Marcar o selecionado
        self.buttons[waveform].setChecked(True)
        
        self._current_waveform = waveform
        self.waveform_changed.emit(waveform)
    
    def get_waveform(self) -> str:
        """Obter forma de onda atual"""
        return self._current_waveform
    
    def set_waveform(self, waveform: str):
        """Definir forma de onda"""
        if waveform in self.buttons:
            self._select_waveform(waveform)


class ProgressRing(QWidget):
    """Anel de progresso animado"""
    
    def __init__(self, size: int = 100):
        super().__init__()
        self.setFixedSize(size, size)
        self._progress = 0.0  # 0.0 a 1.0
        self._animated = False
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self.update)
        self._rotation = 0
        
    def set_progress(self, progress: float, animated: bool = False):
        """Definir progresso (0.0 a 1.0)"""
        self._progress = max(0.0, min(1.0, progress))
        self._animated = animated
        
        if animated:
            self._animation_timer.start(50)  # 20 FPS
        else:
            self._animation_timer.stop()
        
        self.update()
    
    def paintEvent(self, event):
        """Desenhar anel de progresso"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dimensões
        rect = self.rect().adjusted(10, 10, -10, -10)
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2
        
        # Animação de rotação
        if self._animated:
            self._rotation = (self._rotation + 2) % 360
            painter.translate(center)
            painter.rotate(self._rotation)
            painter.translate(-center)
        
        # Desenhar fundo
        painter.setPen(QPen(QColor(236, 240, 241), 8, Qt.PenStyle.SolidLine))
        painter.drawEllipse(rect)
        
        # Desenhar progresso
        if self._progress > 0:
            painter.setPen(QPen(QColor(52, 152, 219), 8, Qt.PenStyle.SolidLine))
            span_angle = int(360 * self._progress * 16)  # Qt usa 1/16 de grau
            painter.drawArc(rect, 90 * 16, -span_angle)  # Começar do topo
        
        # Desenhar texto central
        painter.setPen(QPen(QColor(44, 62, 80), 1))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._progress*100:.0f}%")


class VoltageSlider(QWidget):
    """Slider vertical para voltagem com escala"""
    
    voltage_changed = pyqtSignal(float)  # voltage
    
    def __init__(self, min_v: float = 0.0, max_v: float = 5.0):
        super().__init__()
        self.min_voltage = min_v
        self.max_voltage = max_v
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QHBoxLayout(self)
        
        # Escala (labels)
        scale_layout = QVBoxLayout()
        scale_layout.setSpacing(0)
        
        # Criar labels de escala
        steps = 10
        for i in range(steps + 1):
            voltage = self.max_voltage - (i * (self.max_voltage - self.min_voltage) / steps)
            label = QLabel(f"{voltage:.1f}V")
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
            scale_layout.addWidget(label)
        
        layout.addLayout(scale_layout)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 1000)  # Resolução interna
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TickPosition.TicksLeft)
        self.slider.setTickInterval(100)
        self.slider.valueChanged.connect(self._on_value_changed)
        
        # Estilo do slider
        self.slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #ecf0f1;
                width: 10px;
                border-radius: 5px;
            }
            QSlider::handle:vertical {
                background: #3498db;
                border: 2px solid #2980b9;
                height: 20px;
                border-radius: 10px;
                margin: -5px;
            }
            QSlider::add-page:vertical {
                background: #bdc3c7;
                border-radius: 5px;
            }
            QSlider::sub-page:vertical {
                background: #3498db;
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(self.slider)
        
        # Display digital
        self.display = QLabel("0.0V")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: #3498db;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New';
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        display_layout = QVBoxLayout()
        display_layout.addStretch()
        display_layout.addWidget(self.display)
        layout.addLayout(display_layout)
    
    def _on_value_changed(self, raw_value: int):
        """Converter valor interno para voltagem"""
        voltage = self.min_voltage + (raw_value / 1000.0) * (self.max_voltage - self.min_voltage)
        self.display.setText(f"{voltage:.2f}V")
        self.voltage_changed.emit(voltage)
    
    def set_voltage(self, voltage: float):
        """Definir voltagem externamente"""
        if self.min_voltage <= voltage <= self.max_voltage:
            raw_value = int(1000 * (voltage - self.min_voltage) / (self.max_voltage - self.min_voltage))
            self.slider.blockSignals(True)
            self.slider.setValue(raw_value)
            self.slider.blockSignals(False)
            self.display.setText(f"{voltage:.2f}V")


class StatusBar(QWidget):
    """Barra de status customizada com múltiplas seções"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Status de conexão
        self.connection_indicator = StatusIndicator(16)
        self.connection_label = QLabel("Desconectado")
        layout.addWidget(self.connection_indicator)
        layout.addWidget(self.connection_label)
        
        layout.addWidget(self._create_separator())
        
        # Status de execução
        self.execution_indicator = StatusIndicator(16)
        self.execution_label = QLabel("Parado")
        layout.addWidget(self.execution_indicator)
        layout.addWidget(self.execution_label)
        
        layout.addWidget(self._create_separator())
        
        # Timestamp
        self.timestamp_label = QLabel("--:--:--")
        layout.addWidget(self.timestamp_label)
        
        layout.addStretch()
        
        # Mensagem temporária
        self.message_label = QLabel("")
        layout.addWidget(self.message_label)
        
        # Timer para atualizar timestamp
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timestamp)
        self.timer.start(1000)  # 1 segundo
        
    def _create_separator(self) -> QFrame:
        """Criar separador vertical"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        return line
    
    def _update_timestamp(self):
        """Atualizar timestamp"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.timestamp_label.setText(current_time)
    
    def set_connection_status(self, connected: bool, device: str = ""):
        """Definir status de conexão"""
        if connected:
            self.connection_indicator.set_status(StatusIndicator.Status.OK)
            self.connection_label.setText(f"Conectado: {device}")
        else:
            self.connection_indicator.set_status(StatusIndicator.Status.ERROR)
            self.connection_label.setText("Desconectado")
    
    def set_execution_status(self, status: str):
        """Definir status de execução"""
        status_map = {
            "idle": (StatusIndicator.Status.UNKNOWN, "Parado"),
            "running": (StatusIndicator.Status.OK, "Executando"),
            "paused": (StatusIndicator.Status.WARNING, "Pausado"),
            "error": (StatusIndicator.Status.ERROR, "Erro")
        }
        
        if status in status_map:
            indicator_status, label_text = status_map[status]
            self.execution_indicator.set_status(indicator_status, status == "running")
            self.execution_label.setText(label_text)
    
    def show_message(self, message: str, duration: int = 3000):
        """Mostrar mensagem temporária"""
        self.message_label.setText(message)
        self.message_label.setStyleSheet("color: #2980b9; font-weight: bold;")
        
        # Timer para limpar mensagem
        QTimer.singleShot(duration, lambda: self.message_label.setText(""))


class ParameterGroup(QGroupBox):
    """Grupo de parâmetros com validação automática"""
    
    parameters_changed = pyqtSignal(dict)  # parameter_dict
    
    def __init__(self, title: str, parameters: Dict[str, Dict]):
        """
        Criar grupo de parâmetros
        
        Args:
            title: Título do grupo
            parameters: Dict com definição dos parâmetros
                {
                    'param_name': {
                        'type': 'float|int|str|bool',
                        'min': valor_minimo,
                        'max': valor_maximo,
                        'default': valor_padrao,
                        'unit': 'unidade',
                        'label': 'Nome Exibido'
                    }
                }
        """
        super().__init__(title)
        self.parameters_def = parameters
        self.widgets = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface"""
        layout = QGridLayout(self)
        
        row = 0
        for param_name, param_def in self.parameters_def.items():
            # Label
            label_text = param_def.get('label', param_name)
            unit = param_def.get('unit', '')
            if unit:
                label_text += f" ({unit})"
            
            label = QLabel(label_text + ":")
            layout.addWidget(label, row, 0)
            
            # Widget baseado no tipo
            param_type = param_def.get('type', 'str')
            widget = self._create_widget(param_name, param_def)
            
            self.widgets[param_name] = widget
            layout.addWidget(widget, row, 1)
            
            row += 1
    
    def _create_widget(self, param_name: str, param_def: Dict) -> QWidget:
        """Criar widget para parâmetro"""
        param_type = param_def.get('type', 'str')
        default_value = param_def.get('default', 0)
        
        if param_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(param_def.get('min', 0.0), param_def.get('max', 100.0))
            widget.setValue(default_value)
            widget.setSingleStep(0.1)
            widget.valueChanged.connect(self._emit_changed)
            
            unit = param_def.get('unit', '')
            if unit:
                widget.setSuffix(f" {unit}")
                
        elif param_type == 'int':
            widget = QSpinBox()
            widget.setRange(param_def.get('min', 0), param_def.get('max', 100))
            widget.setValue(default_value)
            widget.valueChanged.connect(self._emit_changed)
            
            unit = param_def.get('unit', '')
            if unit:
                widget.setSuffix(f" {unit}")
                
        elif param_type == 'str':
            widget = QLineEdit()
            widget.setText(str(default_value))
            widget.textChanged.connect(self._emit_changed)
            
        elif param_type == 'bool':
            widget = QCheckBox()
            widget.setChecked(bool(default_value))
            widget.toggled.connect(self._emit_changed)
            
        else:
            # Fallback para string
            widget = QLineEdit()
            widget.setText(str(default_value))
            widget.textChanged.connect(self._emit_changed)
        
        return widget
    
    def _emit_changed(self):
        """Emitir sinal de mudança de parâmetros"""
        values = self.get_values()
        self.parameters_changed.emit(values)
    
    def get_values(self) -> Dict[str, Any]:
        """Obter valores atuais dos parâmetros"""
        values = {}
        
        for param_name, widget in self.widgets.items():
            param_def = self.parameters_def[param_name]
            param_type = param_def.get('type', 'str')
            
            if param_type == 'float':
                values[param_name] = widget.value()
            elif param_type == 'int':
                values[param_name] = widget.value()
            elif param_type == 'str':
                values[param_name] = widget.text()
            elif param_type == 'bool':
                values[param_name] = widget.isChecked()
            else:
                values[param_name] = widget.text()
        
        return values
    
    def set_values(self, values: Dict[str, Any]):
        """Definir valores dos parâmetros"""
        for param_name, value in values.items():
            if param_name in self.widgets:
                widget = self.widgets[param_name]
                param_def = self.parameters_def[param_name]
                param_type = param_def.get('type', 'str')
                
                widget.blockSignals(True)
                
                if param_type in ['float', 'int']:
                    widget.setValue(value)
                elif param_type == 'str':
                    widget.setText(str(value))
                elif param_type == 'bool':
                    widget.setChecked(bool(value))
                
                widget.blockSignals(False)


# ═══════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO E TESTES
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Criar aplicação
    app = QApplication(sys.argv)
    
    # Criar janela de demonstração
    demo_widget = QWidget()
    demo_widget.setWindowTitle("🧪 Demo: Widgets Auxiliares")
    demo_widget.resize(800, 600)
    
    layout = QVBoxLayout(demo_widget)
    
    # Demonstrar StatusIndicator
    status_layout = QHBoxLayout()
    status_layout.addWidget(QLabel("Status Indicators:"))
    
    for status in StatusIndicator.Status:
        indicator = StatusIndicator()
        indicator.set_status(status, status == StatusIndicator.Status.WARNING)
        status_layout.addWidget(indicator)
        status_layout.addWidget(QLabel(status.value))
    
    layout.addLayout(status_layout)
    
    # Demonstrar FrequencyDisplay
    freq_display = FrequencyDisplay()
    freq_display.set_frequency(440.0)
    layout.addWidget(freq_display)
    
    # Demonstrar WaveformSelector
    waveform_selector = WaveformSelector()
    layout.addWidget(waveform_selector)
    
    # Demonstrar ProgressRing
    progress_ring = ProgressRing()
    progress_ring.set_progress(0.75, True)
    layout.addWidget(progress_ring)
    
    # Demonstrar ParameterGroup
    params_def = {
        'frequency': {
            'type': 'float',
            'min': 0.1,
            'max': 10000.0,
            'default': 440.0,
            'unit': 'Hz',
            'label': 'Frequência'
        },
        'amplitude': {
            'type': 'float',
            'min': 0.0,
            'max': 5.0,
            'default': 1.0,
            'unit': 'V',
            'label': 'Amplitude'
        },
        'enabled': {
            'type': 'bool',
            'default': True,
            'label': 'Habilitado'
        }
    }
    
    param_group = ParameterGroup("Parâmetros de Teste", params_def)
    layout.addWidget(param_group)
    
    # StatusBar
    status_bar = StatusBar()
    status_bar.set_connection_status(True, "HS3 Demo")
    status_bar.set_execution_status("running")
    layout.addWidget(status_bar)
    
    # Mostrar janela
    demo_widget.show()
    
    # Timer para demonstrar atualizações
    def update_demo():
        import random
        freq_display.set_frequency(random.uniform(100, 1000))
        progress_ring.set_progress(random.random(), True)
    
    timer = QTimer()
    timer.timeout.connect(update_demo)
    timer.start(2000)  # 2 segundos
    
    # Executar aplicação
    sys.exit(app.exec())
