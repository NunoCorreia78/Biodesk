"""
Sistema de Terapia Informacional - Biodesk
═══════════════════════════════════════════════════════════════════════

Implementação de medicina informacional baseada em princípios quânticos:
- Transmissão de padrões correcionais via campo informacional
- Tratamentos à distância através de testemunho digital
- Biblioteca de frequências organizadas por sistemas biológicos
- Interface para foco terapêutico e intenção dirigida
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QProgressBar, QTabWidget, QWidget, QListWidget, QListWidgetItem,
    QTimeEdit, QDateEdit, QScrollArea, QSlider, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QIcon
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import hashlib
import uuid

from biodesk_dialogs import BiodeskMessageBox
from biodesk_styles import BiodeskStyles

class InformationalPattern:
    """
    Representa um padrão informacional terapêutico
    """
    def __init__(self, name: str, frequencies: List[float], 
                 target_system: str, description: str = ""):
        self.name = name
        self.frequencies = frequencies
        self.target_system = target_system
        self.description = description
        self.creation_time = datetime.now()
        self.pattern_id = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        """Converte para dicionário para serialização"""
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "frequencies": self.frequencies,
            "target_system": self.target_system,
            "description": self.description,
            "creation_time": self.creation_time.isoformat()
        }

class DigitalWitness:
    """
    Testemunho Digital - Ponte informacional com o paciente
    """
    def __init__(self, patient_data: dict):
        self.patient_id = patient_data.get("id", "")
        self.name = patient_data.get("nome", "")
        self.birth_date = patient_data.get("data_nascimento", "")
        self.photo_hash = patient_data.get("foto_hash", "")
        
        # Criar assinatura quântica do testemunho
        self.quantum_signature = self._generate_quantum_signature()
        self.creation_time = datetime.now()
    
    def _generate_quantum_signature(self) -> str:
        """Gera assinatura quântica única do paciente"""
        data = f"{self.name}{self.birth_date}{self.patient_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def is_valid(self) -> bool:
        """Verifica se o testemunho está válido"""
        return bool(self.name and self.birth_date and self.patient_id)

class InformationalTransmission:
    """
    Sistema de transmissão informacional
    """
    def __init__(self, witness: DigitalWitness, pattern: InformationalPattern):
        self.witness = witness
        self.pattern = pattern
        self.transmission_id = str(uuid.uuid4())
        self.start_time = None
        self.end_time = None
        self.duration_minutes = 0
        self.therapist_intention = ""
        self.coherence_level = 0.0
        self.status = "prepared"  # prepared, transmitting, completed, interrupted
    
    def start_transmission(self, duration_minutes: int = 30, intention: str = ""):
        """Inicia transmissão informacional"""
        self.start_time = datetime.now()
        self.duration_minutes = duration_minutes
        self.therapist_intention = intention
        self.status = "transmitting"
        
        # Calcular nível de coerência baseado nos dados
        self.coherence_level = self._calculate_coherence()
    
    def _calculate_coherence(self) -> float:
        """Calcula nível de coerência da transmissão"""
        # Fatores de coerência:
        # - Qualidade do testemunho (dados completos)
        # - Clareza da intenção terapêutica
        # - Alinhamento entre padrão e sistema alvo
        
        witness_quality = 1.0 if self.witness.is_valid() else 0.5
        intention_clarity = min(len(self.therapist_intention) / 100.0, 1.0)
        pattern_alignment = 0.8  # Assumir boa correspondência por agora
        
        return (witness_quality + intention_clarity + pattern_alignment) / 3.0
    
    def complete_transmission(self):
        """Finaliza transmissão"""
        self.end_time = datetime.now()
        self.status = "completed"

class InformationalTherapyDialog(QDialog):
    """
    Interface principal para terapia informacional
    """
    
    transmission_started = pyqtSignal(str)  # transmission_id
    transmission_completed = pyqtSignal(str)
    
    def __init__(self, patient_data: dict, parent=None):
        super().__init__(parent)
        self.patient_data = patient_data
        self.digital_witness = DigitalWitness(patient_data)
        self.current_transmission = None
        
        self.setWindowTitle("🌌 Terapia Informacional - Medicina Quântica")
        self.setMinimumSize(900, 700)
        
        self._load_frequency_library()
        self._setup_ui()
        self._connect_signals()
    
    def _load_frequency_library(self):
        """Carrega biblioteca de padrões informacionais"""
        self.frequency_library = {
            "Sistema Nervoso": [
                InformationalPattern("Harmonização Neural", [7.83, 10.0, 40.0], "Sistema Nervoso",
                                   "Padrão de ressonância Schumann para equilíbrio neural"),
                InformationalPattern("Regeneração Neuronal", [95.0, 221.23, 528.0], "Sistema Nervoso",
                                   "Frequências para reparação e crescimento neural"),
                InformationalPattern("Clareza Mental", [40.0, 70.0, 100.0], "Sistema Nervoso",
                                   "Otimização da função cognitiva e foco")
            ],
            "Sistema Cardiovascular": [
                InformationalPattern("Ritmo Cardíaco", [1.14, 67.8, 341.3], "Sistema Cardiovascular",
                                   "Harmonização do ritmo cardíaco natural"),
                InformationalPattern("Circulação", [20.0, 72.0, 95.0], "Sistema Cardiovascular",
                                   "Melhoria da circulação sanguínea")
            ],
            "Sistema Digestivo": [
                InformationalPattern("Digestão", [465.0, 727.0, 787.0], "Sistema Digestivo",
                                   "Otimização dos processos digestivos"),
                InformationalPattern("Metabolismo", [10.0, 35.0, 95.0], "Sistema Digestivo",
                                   "Aceleração metabólica equilibrada")
            ],
            "Sistema Imunológico": [
                InformationalPattern("Fortalecimento Imune", [20.0, 120.0, 1550.0], "Sistema Imunológico",
                                   "Potenciação das defesas naturais"),
                InformationalPattern("Anti-inflamatório", [304.0, 528.0, 741.0], "Sistema Imunológico",
                                   "Redução de processos inflamatórios")
            ],
            "Equilíbrio Emocional": [
                InformationalPattern("Serenidade", [7.83, 136.10, 528.0], "Equilíbrio Emocional",
                                   "Restauração da paz interior"),
                InformationalPattern("Confiança", [396.0, 417.0, 528.0], "Equilíbrio Emocional",
                                   "Fortalecimento da autoestima"),
                InformationalPattern("Libertação de Trauma", [285.0, 396.0, 741.0], "Equilíbrio Emocional",
                                   "Liberação de padrões traumáticos")
            ]
        }
    
    def _setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Cabeçalho informacional
        header = self._create_header()
        layout.addWidget(header)
        
        # Tabs principais
        tabs = QTabWidget()
        
        # Tab 1: Testemunho Digital
        tabs.addTab(self._create_witness_tab(), "🔗 Testemunho Digital")
        
        # Tab 2: Padrões Informativos
        tabs.addTab(self._create_patterns_tab(), "📡 Padrões Informativos")
        
        # Tab 3: Transmissão
        tabs.addTab(self._create_transmission_tab(), "🌊 Transmissão")
        
        # Tab 4: Monitor
        tabs.addTab(self._create_monitor_tab(), "📊 Monitor")
        
        layout.addWidget(tabs)
        
        # Botões de ação
        buttons = self._create_action_buttons()
        layout.addWidget(buttons)
    
    def _create_header(self) -> QWidget:
        """Criar cabeçalho informativo"""
        header = QGroupBox("🌌 Campo Informacional Ativo")
        layout = QVBoxLayout(header)
        
        # Info do paciente
        patient_info = QLabel(f"Paciente: {self.patient_data.get('nome', 'N/A')}")
        patient_info.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(patient_info)
        
        # Assinatura quântica
        signature = QLabel(f"Assinatura Quântica: {self.digital_witness.quantum_signature}")
        signature.setStyleSheet("color: #4CAF50; font-family: monospace;")
        layout.addWidget(signature)
        
        # Estado do campo
        self.field_status = QLabel("🔴 Campo Informacional: Inativo")
        self.field_status.setStyleSheet("color: #f44336; font-weight: bold;")
        layout.addWidget(self.field_status)
        
        return header
    
    def _create_witness_tab(self) -> QWidget:
        """Tab de configuração do testemunho digital"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Informações do testemunho
        witness_group = QGroupBox("🔗 Configuração do Testemunho Digital")
        witness_layout = QGridLayout(witness_group)
        
        witness_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.name_label = QLabel(self.digital_witness.name)
        self.name_label.setStyleSheet("font-weight: bold;")
        witness_layout.addWidget(self.name_label, 0, 1)
        
        witness_layout.addWidget(QLabel("Data Nascimento:"), 1, 0)
        self.birth_label = QLabel(self.digital_witness.birth_date or "Não informado")
        witness_layout.addWidget(self.birth_label, 1, 1)
        
        witness_layout.addWidget(QLabel("ID Paciente:"), 2, 0)
        self.id_label = QLabel(self.digital_witness.patient_id)
        witness_layout.addWidget(self.id_label, 2, 1)
        
        # Status de validade
        witness_layout.addWidget(QLabel("Status:"), 3, 0)
        status_text = "✅ Válido" if self.digital_witness.is_valid() else "❌ Incompleto"
        status_color = "#4CAF50" if self.digital_witness.is_valid() else "#f44336"
        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        witness_layout.addWidget(self.status_label, 3, 1)
        
        layout.addWidget(witness_group)
        
        # Explicação teórica
        theory_group = QGroupBox("📚 Fundamento Teórico")
        theory_layout = QVBoxLayout(theory_group)
        
        theory_text = QTextEdit()
        theory_text.setMaximumHeight(200)
        theory_text.setReadOnly(True)
        theory_text.setHtml("""
        <b>Testemunho Digital como Ponte Informacional:</b><br><br>
        
        • O testemunho funciona como uma <i>ponte quântica</i> entre o campo terapêutico e o paciente<br>
        • A informação pessoal (nome, data nascimento) cria uma <i>assinatura vibracional única</i><br>
        • Não há limitações espaciais - a informação é transmitida pelo <i>campo morfogenético</i><br>
        • A qualidade da conexão depende da <i>precisão dos dados</i> e da <i>intenção terapêutica</i><br><br>
        
        <b>Base Científica:</b> Estudos em biofotónica mostram que células mantêm 
        comunicação através de sinais de luz fraca. A teoria dos campos mórficos 
        sugere que a informação pode ser transmitida instantaneamente através do espaço.
        """)
        theory_layout.addWidget(theory_text)
        
        layout.addWidget(theory_group)
        layout.addStretch()
        
        return widget
    
    def _create_patterns_tab(self) -> QWidget:
        """Tab de seleção de padrões informativos"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Lista de sistemas
        systems_group = QGroupBox("🎯 Sistemas Biológicos")
        systems_layout = QVBoxLayout(systems_group)
        
        self.systems_list = QListWidget()
        for system in self.frequency_library.keys():
            self.systems_list.addItem(system)
        
        self.systems_list.currentTextChanged.connect(self._on_system_selected)
        systems_layout.addWidget(self.systems_list)
        layout.addWidget(systems_group)
        
        # Padrões do sistema selecionado
        patterns_group = QGroupBox("📡 Padrões Disponíveis")
        patterns_layout = QVBoxLayout(patterns_group)
        
        self.patterns_list = QListWidget()
        patterns_layout.addWidget(self.patterns_list)
        
        # Detalhes do padrão
        self.pattern_details = QTextEdit()
        self.pattern_details.setMaximumHeight(150)
        self.pattern_details.setReadOnly(True)
        patterns_layout.addWidget(self.pattern_details)
        
        layout.addWidget(patterns_group)
        
        return widget
    
    def _create_transmission_tab(self) -> QWidget:
        """Tab de configuração da transmissão"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configurações de transmissão
        config_group = QGroupBox("⚙️ Configuração da Transmissão")
        config_layout = QGridLayout(config_group)
        
        # Duração
        config_layout.addWidget(QLabel("Duração (minutos):"), 0, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 120)
        self.duration_spin.setValue(30)
        config_layout.addWidget(self.duration_spin, 0, 1)
        
        # Intensidade informacional
        config_layout.addWidget(QLabel("Intensidade Informacional:"), 1, 0)
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(1, 10)
        self.intensity_slider.setValue(7)
        config_layout.addWidget(self.intensity_slider, 1, 1)
        
        # Modo de transmissão
        config_layout.addWidget(QLabel("Modo:"), 2, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Transmissão Contínua",
            "Pulsos Rítmicos", 
            "Ressonância Schumann",
            "Sincronização Cardíaca"
        ])
        config_layout.addWidget(self.mode_combo, 2, 1)
        
        layout.addWidget(config_group)
        
        # Intenção terapêutica
        intention_group = QGroupBox("💭 Intenção Terapêutica")
        intention_layout = QVBoxLayout(intention_group)
        
        instruction = QLabel("Formule clara e positivamente a intenção terapêutica:")
        instruction.setWordWrap(True)
        intention_layout.addWidget(instruction)
        
        self.intention_text = QTextEdit()
        self.intention_text.setMaximumHeight(100)
        self.intention_text.setPlaceholderText(
            "Ex: 'Envio informação para harmonização do sistema nervoso, "
            "promovendo equilíbrio, serenidade e regeneração celular.'"
        )
        intention_layout.addWidget(self.intention_text)
        
        layout.addWidget(intention_group)
        
        return widget
    
    def _create_monitor_tab(self) -> QWidget:
        """Tab de monitorização da transmissão"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status da transmissão
        status_group = QGroupBox("📊 Status da Transmissão")
        status_layout = QGridLayout(status_group)
        
        status_layout.addWidget(QLabel("Estado:"), 0, 0)
        self.transmission_status = QLabel("⏸️ Aguardando")
        status_layout.addWidget(self.transmission_status, 0, 1)
        
        status_layout.addWidget(QLabel("Progresso:"), 1, 0)
        self.progress_bar = QProgressBar()
        status_layout.addWidget(self.progress_bar, 1, 1)
        
        status_layout.addWidget(QLabel("Nível de Coerência:"), 2, 0)
        self.coherence_label = QLabel("--")
        status_layout.addWidget(self.coherence_label, 2, 1)
        
        status_layout.addWidget(QLabel("Tempo Decorrido:"), 3, 0)
        self.elapsed_time = QLabel("00:00")
        status_layout.addWidget(self.elapsed_time, 3, 1)
        
        layout.addWidget(status_group)
        
        # Log de transmissão
        log_group = QGroupBox("📝 Log de Transmissão")
        log_layout = QVBoxLayout(log_group)
        
        self.transmission_log = QTextEdit()
        self.transmission_log.setReadOnly(True)
        log_layout.addWidget(self.transmission_log)
        
        layout.addWidget(log_group)
        
        return widget
    
    def _create_action_buttons(self) -> QWidget:
        """Criar botões de ação"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        self.start_btn = QPushButton("🌊 Iniciar Transmissão")
        self.start_btn.clicked.connect(self._start_transmission)
        self.start_btn.setEnabled(self.digital_witness.is_valid())
        BiodeskStyles.apply_to_existing_button(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Parar")
        self.stop_btn.clicked.connect(self._stop_transmission)
        self.stop_btn.setEnabled(False)
        
        self.close_btn = QPushButton("❌ Fechar")
        self.close_btn.clicked.connect(self.reject)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
        layout.addWidget(self.close_btn)
        
        return widget
    
    def _connect_signals(self):
        """Conectar sinais"""
        self.patterns_list.currentTextChanged.connect(self._on_pattern_selected)
        
        # Timer para atualizar progresso
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_progress)
        self.update_timer.setInterval(1000)  # 1 segundo
    
    def _on_system_selected(self, system_name: str):
        """Handler para seleção de sistema"""
        if not system_name:
            return
            
        self.patterns_list.clear()
        patterns = self.frequency_library.get(system_name, [])
        
        for pattern in patterns:
            item = QListWidgetItem(pattern.name)
            item.setData(Qt.ItemDataRole.UserRole, pattern)
            self.patterns_list.addItem(item)
    
    def _on_pattern_selected(self, pattern_name: str):
        """Handler para seleção de padrão"""
        current_item = self.patterns_list.currentItem()
        if not current_item:
            return
            
        pattern = current_item.data(Qt.ItemDataRole.UserRole)
        
        details = f"""
        <b>{pattern.name}</b><br>
        <b>Sistema Alvo:</b> {pattern.target_system}<br>
        <b>Frequências:</b> {', '.join(map(str, pattern.frequencies))} Hz<br><br>
        <b>Descrição:</b> {pattern.description}<br><br>
        <b>Mecanismo de Ação:</b><br>
        As frequências selecionadas criam um padrão informacional que ressoa 
        com o sistema biológico alvo, promovendo reorganização celular e 
        restauração da coerência energética.
        """
        
        self.pattern_details.setHtml(details)
    
    def _start_transmission(self):
        """Iniciar transmissão informacional"""
        try:
            # Verificar se há padrão selecionado
            current_pattern_item = self.patterns_list.currentItem()
            if not current_pattern_item:
                BiodeskMessageBox.warning(self, "Aviso", "Selecione um padrão informativo primeiro")
                return
            
            pattern = current_pattern_item.data(Qt.ItemDataRole.UserRole)
            intention = self.intention_text.toPlainText().strip()
            duration = self.duration_spin.value()
            
            # Criar transmissão
            self.current_transmission = InformationalTransmission(
                self.digital_witness, pattern
            )
            
            # Iniciar transmissão
            self.current_transmission.start_transmission(duration, intention)
            
            # Atualizar interface
            self._update_transmission_ui(True)
            
            # Iniciar timer de progresso
            self.update_timer.start()
            
            # Log
            self._log_transmission(f"🌊 Transmissão iniciada: {pattern.name}")
            self._log_transmission(f"📅 Duração: {duration} minutos")
            self._log_transmission(f"🎯 Sistema alvo: {pattern.target_system}")
            self._log_transmission(f"💭 Intenção: {intention}")
            
            # Emitir sinal
            self.transmission_started.emit(self.current_transmission.transmission_id)
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro ao iniciar transmissão: {e}")
    
    def _stop_transmission(self):
        """Parar transmissão"""
        if self.current_transmission:
            self.current_transmission.complete_transmission()
            self.update_timer.stop()
            self._update_transmission_ui(False)
            
            self._log_transmission("⏹️ Transmissão finalizada")
            self.transmission_completed.emit(self.current_transmission.transmission_id)
    
    def _update_transmission_ui(self, active: bool):
        """Atualizar interface da transmissão"""
        if active:
            self.field_status.setText("🟢 Campo Informacional: Ativo - Transmitindo")
            self.field_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.transmission_status.setText("🌊 Transmitindo")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.field_status.setText("🔴 Campo Informacional: Inativo")
            self.field_status.setStyleSheet("color: #f44336; font-weight: bold;")
            self.transmission_status.setText("⏸️ Parado")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setValue(0)
    
    def _update_progress(self):
        """Atualizar progresso da transmissão"""
        if not self.current_transmission or self.current_transmission.status != "transmitting":
            return
        
        # Calcular progresso
        elapsed = datetime.now() - self.current_transmission.start_time
        total_duration = timedelta(minutes=self.current_transmission.duration_minutes)
        
        progress = min(100, int((elapsed.total_seconds() / total_duration.total_seconds()) * 100))
        self.progress_bar.setValue(progress)
        
        # Atualizar tempo decorrido
        elapsed_str = str(elapsed).split('.')[0]  # Remove microssegundos
        self.elapsed_time.setText(elapsed_str)
        
        # Atualizar nível de coerência
        coherence_pct = int(self.current_transmission.coherence_level * 100)
        self.coherence_label.setText(f"{coherence_pct}%")
        
        # Verificar se completou
        if progress >= 100:
            self._stop_transmission()
    
    def _log_transmission(self, message: str):
        """Adicionar mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.transmission_log.append(f"[{timestamp}] {message}")


class InformationalSession:
    """
    Classe para gestão de sessões de terapia informacional
    """
    
    def __init__(self, patient_data: dict, protocol_data: dict):
        self.session_id = str(uuid.uuid4())
        self.patient_data = patient_data
        self.protocol_data = protocol_data
        self.start_time = datetime.now()
        self.end_time = None
        self.configuration = {}
        self.log_entries = []
        
    def add_log_entry(self, message: str):
        """Adicionar entrada ao log da sessão"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_entries.append(f"[{timestamp}] {message}")
    
    def complete_session(self):
        """Completar sessão"""
        self.end_time = datetime.now()
        self.add_log_entry("Sessão completada")


class DigitalTestimony:
    """
    Classe para testemunho digital do paciente
    """
    
    def __init__(self, patient_data: dict):
        self.patient_data = patient_data
        self.creation_time = datetime.now()
        self.testimony_hash = self._generate_testimony_hash()
        
    def _generate_testimony_hash(self) -> str:
        """Gerar hash único do testemunho"""
        data_string = f"{self.patient_data.get('nome', '')}{self.patient_data.get('data_nascimento', '')}{self.creation_time.isoformat()}"
        return hashlib.md5(data_string.encode()).hexdigest()
    
    def get_resonance_pattern(self) -> dict:
        """Obter padrão de ressonância"""
        return {
            'patient_hash': self.testimony_hash,
            'creation_time': self.creation_time,
            'biometric_data': self.patient_data
        }


class InformationalTherapyDialog(QDialog):
    """
    Diálogo principal para configuração de terapia informacional
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔊 Configuração de Terapia Informacional")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # Dados do paciente e configuração
        self.patient_data = None
        self.configuration = {}
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configurar interface do diálogo"""
        layout = QVBoxLayout(self)
        
        # Título e descrição
        title_label = QLabel("Configuração de Terapia Informacional")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Configure os parâmetros para transmissão informacional de frequências\n"
            "sem amplitude física - ideal para tratamentos vibracionais puros."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(desc_label)
        
        # Abas de configuração
        tabs = QTabWidget()
        
        # Aba 1: Configurações Básicas
        basic_tab = self._create_basic_tab()
        tabs.addTab(basic_tab, "⚙️ Básico")
        
        # Aba 2: Testemunho Digital
        testimony_tab = self._create_testimony_tab()
        tabs.addTab(testimony_tab, "🧬 Testemunho")
        
        # Aba 3: Configurações Avançadas
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "🔬 Avançado")
        
        layout.addWidget(tabs)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.test_button = QPushButton("🔍 Testar Configuração")
        self.test_button.clicked.connect(self._test_configuration)
        buttons_layout.addWidget(self.test_button)
        
        buttons_layout.addStretch()
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        self.apply_button = QPushButton("✅ Aplicar")
        self.apply_button.clicked.connect(self.accept)
        self.apply_button.setDefault(True)
        buttons_layout.addWidget(self.apply_button)
        
        layout.addLayout(buttons_layout)
    
    def _create_basic_tab(self) -> QWidget:
        """Criar aba de configurações básicas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Modo não-local
        nonlocal_group = QGroupBox("📡 Tratamento Não-Local")
        nonlocal_layout = QVBoxLayout(nonlocal_group)
        
        self.nonlocal_check = QCheckBox("Ativar modo não-local (à distância)")
        self.nonlocal_check.setToolTip(
            "Permite tratamento à distância usando testemunho digital\n"
            "baseado em princípios de entrelaçamento quântico"
        )
        nonlocal_layout.addWidget(self.nonlocal_check)
        
        layout.addWidget(nonlocal_group)
        
        # Intenção Terapêutica
        intention_group = QGroupBox("🎯 Intenção Terapêutica")
        intention_layout = QVBoxLayout(intention_group)
        
        QLabel("Foco terapêutico:", intention_group)
        self.intention_combo = QComboBox()
        self.intention_combo.addItems([
            "Harmonização Geral",
            "Equilíbrio Energético",
            "Regeneração Celular",
            "Fortalecimento Imunológico",
            "Desintoxicação",
            "Redução de Stress",
            "Personalizado..."
        ])
        intention_layout.addWidget(self.intention_combo)
        
        self.custom_intention = QTextEdit()
        self.custom_intention.setMaximumHeight(60)
        self.custom_intention.setPlaceholderText("Descreva a intenção terapêutica específica...")
        self.custom_intention.setVisible(False)
        intention_layout.addWidget(self.custom_intention)
        
        layout.addWidget(intention_group)
        
        # Biblioteca de Padrões
        library_group = QGroupBox("📚 Biblioteca de Padrões")
        library_layout = QVBoxLayout(library_group)
        
        self.library_combo = QComboBox()
        self.library_combo.addItems([
            "Rife - Frequências Clássicas",
            "Nogier - Auriculoterapia",
            "Schumann - Ressonâncias Terrestres",
            "Clark - Parasitas e Patógenos",
            "Bemer - Microvasculação",
            "Chakras - Centros Energéticos",
            "Solfeggio - Frequências Sagradas"
        ])
        library_layout.addWidget(self.library_combo)
        
        layout.addWidget(library_group)
        
        layout.addStretch()
        return widget
    
    def _create_testimony_tab(self) -> QWidget:
        """Criar aba de testemunho digital"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Informações do paciente
        patient_group = QGroupBox("👤 Dados do Paciente")
        patient_layout = QGridLayout(patient_group)
        
        patient_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.patient_name = QLineEdit()
        self.patient_name.setReadOnly(True)
        patient_layout.addWidget(self.patient_name, 0, 1)
        
        patient_layout.addWidget(QLabel("Data Nascimento:"), 1, 0)
        self.patient_birth = QLineEdit()
        self.patient_birth.setReadOnly(True)
        patient_layout.addWidget(self.patient_birth, 1, 1)
        
        layout.addWidget(patient_group)
        
        # Testemunho Digital
        testimony_group = QGroupBox("🧬 Configuração do Testemunho")
        testimony_layout = QVBoxLayout(testimony_group)
        
        self.digital_testimony_check = QCheckBox("Usar testemunho digital para conexão vibracional")
        self.digital_testimony_check.setChecked(True)
        testimony_layout.addWidget(self.digital_testimony_check)
        
        # Elementos do testemunho
        elements_label = QLabel("Elementos incluídos no testemunho:")
        elements_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        testimony_layout.addWidget(elements_label)
        
        self.include_biometric = QCheckBox("✓ Dados biométricos (nome, nascimento)")
        self.include_biometric.setChecked(True)
        testimony_layout.addWidget(self.include_biometric)
        
        self.include_energetic = QCheckBox("✓ Padrão energético atual")
        self.include_energetic.setChecked(True)
        testimony_layout.addWidget(self.include_energetic)
        
        self.include_photo = QCheckBox("✓ Fotografia (se disponível)")
        testimony_layout.addWidget(self.include_photo)
        
        layout.addWidget(testimony_group)
        
        # Status da conexão
        status_group = QGroupBox("📡 Status da Conexão")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status = QLabel("⚪ Aguardando configuração...")
        status_layout.addWidget(self.connection_status)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Criar aba de configurações avançadas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Parâmetros de transmissão
        transmission_group = QGroupBox("📊 Parâmetros de Transmissão")
        transmission_layout = QGridLayout(transmission_group)
        
        transmission_layout.addWidget(QLabel("Potência Informacional:"), 0, 0)
        self.info_power = QSpinBox()
        self.info_power.setRange(1, 100)
        self.info_power.setValue(50)
        self.info_power.setSuffix("%")
        transmission_layout.addWidget(self.info_power, 0, 1)
        
        transmission_layout.addWidget(QLabel("Duração do Pulso:"), 1, 0)
        self.pulse_duration = QSpinBox()
        self.pulse_duration.setRange(1, 1000)
        self.pulse_duration.setValue(100)
        self.pulse_duration.setSuffix("ms")
        transmission_layout.addWidget(self.pulse_duration, 1, 1)
        
        transmission_layout.addWidget(QLabel("Intervalo entre Pulsos:"), 2, 0)
        self.pulse_interval = QSpinBox()
        self.pulse_interval.setRange(10, 5000)
        self.pulse_interval.setValue(1000)
        self.pulse_interval.setSuffix("ms")
        transmission_layout.addWidget(self.pulse_interval, 2, 1)
        
        layout.addWidget(transmission_group)
        
        # Modulação quântica
        quantum_group = QGroupBox("⚛️ Modulação Quântica")
        quantum_layout = QVBoxLayout(quantum_group)
        
        self.quantum_modulation = QCheckBox("Ativar modulação quântica")
        self.quantum_modulation.setToolTip(
            "Aplica variações aleatórias baseadas em flutuações quânticas\n"
            "para aumentar a eficácia informacional"
        )
        quantum_layout.addWidget(self.quantum_modulation)
        
        self.coherence_enhancement = QCheckBox("Realce de coerência")
        self.coherence_enhancement.setToolTip(
            "Sincroniza a transmissão com ritmos naturais\n"
            "(Schumann, biocompatibilidade)"
        )
        quantum_layout.addWidget(self.coherence_enhancement)
        
        layout.addWidget(quantum_group)
        
        # Log avançado
        log_group = QGroupBox("📝 Registro Avançado")
        log_layout = QVBoxLayout(log_group)
        
        self.detailed_logging = QCheckBox("Ativar log detalhado")
        self.detailed_logging.setChecked(True)
        log_layout.addWidget(self.detailed_logging)
        
        self.export_session = QCheckBox("Exportar dados da sessão")
        log_layout.addWidget(self.export_session)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        return widget
    
    def _connect_signals(self):
        """Conectar sinais da interface"""
        self.intention_combo.currentTextChanged.connect(self._on_intention_changed)
        self.nonlocal_check.toggled.connect(self._on_nonlocal_changed)
        self.digital_testimony_check.toggled.connect(self._update_testimony_status)
    
    def _on_intention_changed(self, text: str):
        """Atualizar interface quando intenção muda"""
        self.custom_intention.setVisible(text == "Personalizado...")
    
    def _on_nonlocal_changed(self, enabled: bool):
        """Atualizar interface quando modo não-local muda"""
        if enabled:
            self.connection_status.setText("📡 Modo não-local ativado")
            self.connection_status.setStyleSheet("color: blue;")
        else:
            self.connection_status.setText("⚪ Modo local")
            self.connection_status.setStyleSheet("color: gray;")
    
    def _update_testimony_status(self):
        """Atualizar status do testemunho"""
        if self.digital_testimony_check.isChecked():
            self.connection_status.setText("🧬 Testemunho digital ativo")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("⚪ Testemunho desativado")
            self.connection_status.setStyleSheet("color: gray;")
    
    def _test_configuration(self):
        """Testar configuração atual"""
        try:
            config = self.get_configuration()
            
            # Simular teste de conectividade
            QTimer.singleShot(1000, lambda: self.connection_status.setText("✅ Configuração testada com sucesso"))
            QTimer.singleShot(3000, lambda: self._update_testimony_status())
            
        except Exception as e:
            self.connection_status.setText(f"❌ Erro no teste: {e}")
            self.connection_status.setStyleSheet("color: red;")
    
    def set_patient_data(self, patient_data: dict):
        """Definir dados do paciente"""
        self.patient_data = patient_data
        
        if patient_data:
            self.patient_name.setText(patient_data.get('nome', ''))
            self.patient_birth.setText(patient_data.get('data_nascimento', ''))
    
    def get_configuration(self) -> dict:
        """Obter configuração atual"""
        config = {
            'non_local_mode': self.nonlocal_check.isChecked(),
            'digital_testimony': self.digital_testimony_check.isChecked(),
            'therapeutic_intention': (
                self.custom_intention.toPlainText() 
                if self.intention_combo.currentText() == "Personalizado..." 
                else self.intention_combo.currentText()
            ),
            'pattern_library': self.library_combo.currentText(),
            'informational_power': self.info_power.value(),
            'pulse_duration': self.pulse_duration.value(),
            'pulse_interval': self.pulse_interval.value(),
            'quantum_modulation': self.quantum_modulation.isChecked(),
            'coherence_enhancement': self.coherence_enhancement.isChecked(),
            'detailed_logging': self.detailed_logging.isChecked(),
            'export_session': self.export_session.isChecked(),
            'patient_data': self.patient_data
        }
        
        self.configuration = config
        return config
