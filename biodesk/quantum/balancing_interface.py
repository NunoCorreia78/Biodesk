"""
FASE 4: Interface de Balanceamento
=================================

Interface para criação e execução de protocolos terapêuticos
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QComboBox, QGroupBox, QTextEdit, QProgressBar,
                            QSplitter, QFrame, QSpinBox, QDoubleSpinBox,
                            QHeaderView, QTabWidget, QSlider, QCheckBox,
                            QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QColor, QBrush, QPalette
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .protocol_generator import (ProtocolGenerator, TherapyProtocol, ProtocolStep, 
                               ProtocolType, protocol_generator)
from .resonance_analysis import ResonanceItem
from .resonance_interface import ModernWidget

class ProtocolCreationWidget(ModernWidget):
    """Widget para criação de protocolos"""
    
    protocol_created = pyqtSignal(object)  # TherapyProtocol
    
    def __init__(self):
        super().__init__()
        self.analysis_results = []
        self.current_protocol = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("⚛️ Geração de Protocolos Terapêuticos")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #ecf0f1, stop:0.5 #ffffff, stop:1 #ecf0f1);
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Configurações do protocolo
        config_group = QGroupBox("⚙️ Configuração do Protocolo")
        config_layout = QGridLayout(config_group)
        
        # Tipo de protocolo
        config_layout.addWidget(QLabel("Tipo de Protocolo:"), 0, 0)
        self.protocol_type_combo = QComboBox()
        
        for ptype in ProtocolType:
            display_name = {
                ProtocolType.HARMONIZACAO: "🎵 Harmonização (reforçar positivos)",
                ProtocolType.NEUTRALIZACAO: "🛡️ Neutralização (eliminar stressors)",
                ProtocolType.FORTALECIMENTO: "💪 Fortalecimento (amplificar benefícios)",
                ProtocolType.EQUILIBRIO: "⚖️ Equilíbrio (neutralizar + harmonizar)",
                ProtocolType.DETOX: "🧹 Detox (limpeza profunda)",
                ProtocolType.REGENERACAO: "🌱 Regeneração (revitalização)"
            }[ptype]
            
            self.protocol_type_combo.addItem(display_name, ptype)
        
        config_layout.addWidget(self.protocol_type_combo, 0, 1)
        
        # Opções avançadas
        config_layout.addWidget(QLabel("Duração máxima (min):"), 1, 0)
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setRange(10, 120)
        self.max_duration_spin.setValue(30)
        config_layout.addWidget(self.max_duration_spin, 1, 1)
        
        config_layout.addWidget(QLabel("Intensidade:"), 2, 0)
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(1, 10)
        self.intensity_slider.setValue(5)
        self.intensity_label = QLabel("5/10")
        self.intensity_slider.valueChanged.connect(
            lambda v: self.intensity_label.setText(f"{v}/10")
        )
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(self.intensity_slider)
        intensity_layout.addWidget(self.intensity_label)
        config_layout.addLayout(intensity_layout, 2, 1)
        
        # Incluir preparação e integração
        self.include_prep_check = QCheckBox("Incluir preparação e integração")
        self.include_prep_check.setChecked(True)
        config_layout.addWidget(self.include_prep_check, 3, 0, 1, 2)
        
        layout.addWidget(config_group)
        
        # Estatísticas dos dados de entrada
        stats_group = QGroupBox("📊 Dados de Entrada")
        stats_layout = QVBoxLayout(stats_group)
        
        self.input_stats_label = QLabel("Nenhuma análise carregada")
        stats_layout.addWidget(self.input_stats_label)
        
        layout.addWidget(stats_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🚀 Gerar Protocolo")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_protocol)
        self.generate_btn.setEnabled(False)
        
        self.preview_btn = QPushButton("👁️ Pré-visualizar")
        self.preview_btn.clicked.connect(self.preview_protocol)
        self.preview_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.preview_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Área de pré-visualização
        preview_group = QGroupBox("👁️ Pré-visualização do Protocolo")
        preview_layout = QVBoxLayout(preview_group)
        
        self.protocol_preview = QTextEdit()
        self.protocol_preview.setMaximumHeight(200)
        self.protocol_preview.setPlaceholderText("Gere um protocolo para ver a pré-visualização...")
        preview_layout.addWidget(self.protocol_preview)
        
        layout.addWidget(preview_group)
        layout.addStretch()
        
    def set_analysis_results(self, results: List[ResonanceItem], 
                           patient_witness: Dict, field_used: str):
        """Define resultados da análise para geração de protocolo"""
        self.analysis_results = results
        self.patient_witness = patient_witness
        self.field_used = field_used
        
        # Atualizar estatísticas
        if results:
            positive = len([r for r in results if r.resonance_value > 0])
            negative = len([r for r in results if r.resonance_value < 0])
            avg_resonance = sum(r.resonance_value for r in results) / len(results)
            
            stats_text = f"""
            📊 <b>Análise carregada:</b><br>
            • Total de itens: {len(results)}<br>
            • Ressonantes positivos: {positive}<br>
            • Stressors (negativos): {negative}<br>
            • Ressonância média: {avg_resonance:+.1f}<br>
            • Campo usado: {field_used}<br>
            • Paciente: {patient_witness.get('name', 'N/A')}
            """
            self.input_stats_label.setText(stats_text)
            self.generate_btn.setEnabled(True)
        else:
            self.input_stats_label.setText("Nenhuma análise carregada")
            self.generate_btn.setEnabled(False)
    
    def generate_protocol(self):
        """Gera protocolo baseado nas configurações"""
        if not self.analysis_results:
            return
            
        try:
            # Obter configurações
            protocol_type = self.protocol_type_combo.currentData()
            max_duration = self.max_duration_spin.value() * 60  # converter para segundos
            intensity = self.intensity_slider.value()
            
            # Opções para o gerador
            options = {
                'max_duration': max_duration,
                'intensity': intensity / 10.0,  # normalizar 0-1
                'include_preparation': self.include_prep_check.isChecked()
            }
            
            # Gerar protocolo
            self.current_protocol = protocol_generator.generate_protocol(
                analysis_results=self.analysis_results,
                protocol_type=protocol_type,
                patient_witness=self.patient_witness,
                field_used=self.field_used,
                options=options
            )
            
            # Atualizar pré-visualização
            self.update_preview()
            
            # Habilitar botão de pré-visualização
            self.preview_btn.setEnabled(True)
            
            # Emitir sinal
            self.protocol_created.emit(self.current_protocol)
            
        except Exception as e:
            self.protocol_preview.setText(f"❌ Erro ao gerar protocolo: {e}")
    
    def update_preview(self):
        """Atualiza pré-visualização do protocolo"""
        if not self.current_protocol:
            return
            
        protocol = self.current_protocol
        duration_min = protocol.total_duration / 60
        
        preview_text = f"""
        <h3>📋 {protocol.name}</h3>
        <p><b>Tipo:</b> {protocol.protocol_type.value.title()}</p>
        <p><b>Duração total:</b> {duration_min:.1f} minutos</p>
        <p><b>Número de passos:</b> {len(protocol.steps)}</p>
        <p><b>Descrição:</b> {protocol.description}</p>
        
        <h4>🔧 Passos do Protocolo:</h4>
        <ol>
        """
        
        for i, step in enumerate(protocol.steps):
            step_min = step.duration / 60
            preview_text += f"""
            <li><b>{step.name}</b><br>
                🎵 {step.frequency:.1f}Hz | 
                📶 {step.amplitude:.1f}V | 
                ⏱️ {step_min:.1f}min
            """
            if step.pause_after > 0:
                preview_text += f" | ⏸️ {step.pause_after}s pausa"
            preview_text += "</li>"
        
        preview_text += "</ol>"
        
        # Estatísticas de eficácia
        effectiveness = protocol_generator.estimate_protocol_effectiveness(protocol)
        preview_text += f"""
        <h4>📊 Estimativa de Eficácia:</h4>
        <ul>
            <li>🔋 Força: {effectiveness['strength']*100:.0f}%</li>
            <li>⚖️ Equilíbrio: {effectiveness['balance']*100:.0f}%</li>
            <li>🎵 Coerência: {effectiveness['coherence']*100:.0f}%</li>
            <li>⏱️ Duração: {effectiveness['duration_score']*100:.0f}%</li>
            <li><b>🎯 Geral: {effectiveness['overall']*100:.0f}%</b></li>
        </ul>
        """
        
        self.protocol_preview.setHtml(preview_text)
    
    def preview_protocol(self):
        """Abre janela de pré-visualização detalhada"""
        if not self.current_protocol:
            return
            
        # Por agora, mostrar na área de texto
        # Em implementação futura, abrir janela separada
        pass

class ProtocolExecutionWidget(ModernWidget):
    """Widget para execução de protocolos"""
    
    execution_started = pyqtSignal()
    execution_completed = pyqtSignal()
    execution_paused = pyqtSignal()
    execution_stopped = pyqtSignal()
    step_changed = pyqtSignal(int)  # índice do passo atual
    progress_updated = pyqtSignal(int)  # 0-100%
    
    def __init__(self):
        super().__init__()
        self.current_protocol = None
        self.execution_timer = QTimer()
        self.current_step_index = 0
        self.step_start_time = None
        self.is_paused = False
        self.is_running = False
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("▶️ Execução de Protocolo")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #e8f5e8, stop:0.5 #ffffff, stop:1 #e8f5e8);
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Informações do protocolo
        info_group = QGroupBox("📋 Informações do Protocolo")
        info_layout = QVBoxLayout(info_group)
        
        self.protocol_info_label = QLabel("Nenhum protocolo carregado")
        info_layout.addWidget(self.protocol_info_label)
        
        layout.addWidget(info_group)
        
        # Controles de execução
        controls_group = QGroupBox("🎮 Controles")
        controls_layout = QHBoxLayout(controls_group)
        
        self.start_btn = QPushButton("▶️ Iniciar")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover:enabled {
                background-color: #2ecc71;
            }
        """)
        self.start_btn.clicked.connect(self.start_execution)
        self.start_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("⏸️ Pausar")
        self.pause_btn.clicked.connect(self.pause_execution)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹️ Parar")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover:enabled {
                background-color: #c0392b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Progresso geral
        progress_group = QGroupBox("📊 Progresso")
        progress_layout = QVBoxLayout(progress_group)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        progress_layout.addWidget(QLabel("Progresso Geral:"))
        progress_layout.addWidget(self.overall_progress)
        
        self.step_progress = QProgressBar()
        self.step_progress.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #27ae60;
            }
        """)
        progress_layout.addWidget(QLabel("Passo Atual:"))
        progress_layout.addWidget(self.step_progress)
        
        layout.addWidget(progress_group)
        
        # Passo atual
        current_step_group = QGroupBox("🎯 Passo Atual")
        current_step_layout = QVBoxLayout(current_step_group)
        
        self.current_step_label = QLabel("Aguardando início...")
        self.current_step_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        current_step_layout.addWidget(self.current_step_label)
        
        self.step_details_label = QLabel("")
        current_step_layout.addWidget(self.step_details_label)
        
        layout.addWidget(current_step_group)
        
        # Tabela de passos
        steps_group = QGroupBox("📝 Lista de Passos")
        steps_layout = QVBoxLayout(steps_group)
        
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(5)
        self.steps_table.setHorizontalHeaderLabels([
            "Passo", "Frequência", "Amplitude", "Duração", "Status"
        ])
        
        # Configurar larguras das colunas
        header = self.steps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.steps_table.setColumnWidth(1, 100)
        self.steps_table.setColumnWidth(2, 80)
        self.steps_table.setColumnWidth(3, 80)
        self.steps_table.setColumnWidth(4, 100)
        
        steps_layout.addWidget(self.steps_table)
        layout.addWidget(steps_group)
        
    def connect_signals(self):
        """Conecta sinais internos"""
        self.execution_timer.timeout.connect(self.update_execution)
        
    def set_protocol(self, protocol: TherapyProtocol):
        """Define protocolo para execução"""
        self.current_protocol = protocol
        
        if protocol:
            # Atualizar informações
            duration_min = protocol.total_duration / 60
            info_text = f"""
            <b>📋 {protocol.name}</b><br>
            🎭 Tipo: {protocol.protocol_type.value.title()}<br>
            ⏱️ Duração: {duration_min:.1f} minutos<br>
            🔧 Passos: {len(protocol.steps)}<br>
            👤 Paciente: {protocol.patient_witness.get('name', 'N/A')}<br>
            🔮 Campo: {protocol.field_used}
            """
            self.protocol_info_label.setText(info_text)
            
            # Preencher tabela de passos
            self.populate_steps_table()
            
            # Habilitar botão de início
            self.start_btn.setEnabled(True)
        else:
            self.protocol_info_label.setText("Nenhum protocolo carregado")
            self.start_btn.setEnabled(False)
            
    def populate_steps_table(self):
        """Preenche tabela com passos do protocolo"""
        if not self.current_protocol:
            return
            
        steps = self.current_protocol.steps
        self.steps_table.setRowCount(len(steps))
        
        for i, step in enumerate(steps):
            # Nome do passo
            name_item = QTableWidgetItem(step.name)
            self.steps_table.setItem(i, 0, name_item)
            
            # Frequência
            freq_item = QTableWidgetItem(f"{step.frequency:.1f} Hz")
            self.steps_table.setItem(i, 1, freq_item)
            
            # Amplitude
            ampl_item = QTableWidgetItem(f"{step.amplitude:.1f} V")
            self.steps_table.setItem(i, 2, ampl_item)
            
            # Duração
            duration_min = step.duration / 60
            dur_item = QTableWidgetItem(f"{duration_min:.1f} min")
            self.steps_table.setItem(i, 3, dur_item)
            
            # Status
            status_item = QTableWidgetItem("⏳ Pendente")
            status_item.setBackground(QBrush(QColor(245, 245, 245)))
            self.steps_table.setItem(i, 4, status_item)
    
    def start_execution(self):
        """Inicia execução do protocolo"""
        if not self.current_protocol or self.is_running:
            return
            
        self.is_running = True
        self.is_paused = False
        self.current_step_index = 0
        self.step_start_time = datetime.now()
        
        # Atualizar controles
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # Iniciar timer (atualizar a cada 100ms)
        self.execution_timer.start(100)
        
        # Emitir sinal
        self.execution_started.emit()
        
        # Atualizar interface
        self.update_current_step_display()
        
    def pause_execution(self):
        """Pausa/despausa execução"""
        if not self.is_running:
            return
            
        if self.is_paused:
            # Despausar
            self.is_paused = False
            self.pause_btn.setText("⏸️ Pausar")
            self.execution_timer.start(100)
        else:
            # Pausar
            self.is_paused = True
            self.pause_btn.setText("▶️ Continuar")
            self.execution_timer.stop()
            self.execution_paused.emit()
    
    def stop_execution(self):
        """Para execução do protocolo"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.is_paused = False
        self.execution_timer.stop()
        
        # Atualizar controles
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸️ Pausar")
        self.stop_btn.setEnabled(False)
        
        # Resetar progresso
        self.overall_progress.setValue(0)
        self.step_progress.setValue(0)
        self.current_step_label.setText("Execução parada")
        self.step_details_label.setText("")
        
        # Emitir sinal
        self.execution_stopped.emit()
        
    def update_execution(self):
        """Atualiza execução do protocolo"""
        if not self.is_running or self.is_paused or not self.current_protocol:
            return
            
        current_time = datetime.now()
        step = self.current_protocol.steps[self.current_step_index]
        
        # Calcular tempo decorrido no passo atual
        elapsed_time = (current_time - self.step_start_time).total_seconds()
        
        # Atualizar progresso do passo
        step_progress = min(100, int((elapsed_time / step.duration) * 100))
        self.step_progress.setValue(step_progress)
        
        # Verificar se passo terminou
        if elapsed_time >= step.duration:
            # Marcar passo como completo
            status_item = self.steps_table.item(self.current_step_index, 4)
            if status_item:
                status_item.setText("✅ Completo")
                status_item.setBackground(QBrush(QColor(144, 238, 144)))
            
            # Pausa após passo (se configurada)
            if step.pause_after > 0:
                # Implementar pausa aqui se necessário
                pass
            
            # Avançar para próximo passo
            self.current_step_index += 1
            
            if self.current_step_index >= len(self.current_protocol.steps):
                # Protocolo completo
                self.complete_execution()
            else:
                # Próximo passo
                self.step_start_time = current_time
                self.update_current_step_display()
                self.step_changed.emit(self.current_step_index)
        
        # Atualizar progresso geral
        total_steps = len(self.current_protocol.steps)
        overall_progress = int(((self.current_step_index + (elapsed_time / step.duration)) / total_steps) * 100)
        self.overall_progress.setValue(min(100, overall_progress))
        self.progress_updated.emit(overall_progress)
    
    def complete_execution(self):
        """Completa execução do protocolo"""
        self.is_running = False
        self.execution_timer.stop()
        
        # Atualizar interface
        self.overall_progress.setValue(100)
        self.step_progress.setValue(100)
        self.current_step_label.setText("✅ Protocolo Completo!")
        self.step_details_label.setText("Todas as frequências foram aplicadas com sucesso")
        
        # Atualizar controles
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # Emitir sinal
        self.execution_completed.emit()
        
    def update_current_step_display(self):
        """Atualiza display do passo atual"""
        if not self.current_protocol or self.current_step_index >= len(self.current_protocol.steps):
            return
            
        step = self.current_protocol.steps[self.current_step_index]
        
        # Atualizar label do passo atual
        self.current_step_label.setText(f"🎯 Passo {self.current_step_index + 1}: {step.name}")
        
        # Detalhes do passo
        details = f"""
        🎵 Frequência: {step.frequency:.1f} Hz
        📶 Amplitude: {step.amplitude:.1f} V  
        ⏱️ Duração: {step.duration / 60:.1f} minutos
        📝 {step.description}
        """
        if step.resonance_item:
            details += f"\n🔮 Item: {step.resonance_item.name} ({step.resonance_item.resonance_value:+d})"
            
        self.step_details_label.setText(details)
        
        # Marcar passo como ativo na tabela
        for i in range(self.steps_table.rowCount()):
            status_item = self.steps_table.item(i, 4)
            if status_item:
                if i == self.current_step_index:
                    status_item.setText("▶️ Ativo")
                    status_item.setBackground(QBrush(QColor(255, 215, 0)))  # Dourado
                elif i < self.current_step_index:
                    if status_item.text() != "✅ Completo":
                        status_item.setText("✅ Completo")
                        status_item.setBackground(QBrush(QColor(144, 238, 144)))

class BalancingInterface(ModernWidget):
    """Interface principal para balanceamento"""
    
    def __init__(self):
        super().__init__()
        self.current_analysis_results = []
        self.current_patient_witness = {}
        self.current_field = ""
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título principal
        main_title = QLabel("⚖️ INTERFACE DE BALANCEAMENTO TERAPÊUTICO")
        main_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #f8f9fa, stop:0.5 #e3f2fd, stop:1 #f8f9fa);
                border: 3px solid #2196f3;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        layout.addWidget(main_title)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo - Criação de protocolo
        self.protocol_creation = ProtocolCreationWidget()
        main_splitter.addWidget(self.protocol_creation)
        
        # Painel direito - Execução
        self.protocol_execution = ProtocolExecutionWidget()
        main_splitter.addWidget(self.protocol_execution)
        
        # Configurar proporções
        main_splitter.setSizes([600, 600])
        
        layout.addWidget(main_splitter)
        
    def connect_signals(self):
        """Conecta sinais entre componentes"""
        self.protocol_creation.protocol_created.connect(
            self.protocol_execution.set_protocol
        )
    
    def set_analysis_data(self, results: List[ResonanceItem], 
                         patient_witness: Dict, field_used: str):
        """Define dados da análise para geração de protocolos"""
        self.current_analysis_results = results
        self.current_patient_witness = patient_witness  
        self.current_field = field_used
        
        # Passar para widget de criação
        self.protocol_creation.set_analysis_results(results, patient_witness, field_used)
