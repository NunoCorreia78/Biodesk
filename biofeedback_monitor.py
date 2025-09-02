"""
Monitor de Biofeedback para Terapia Quântica
═══════════════════════════════════════════════════════════════════════

Sistema de monitorização em tempo real durante sessões terapêuticas.
Coleta e apresenta dados de resposta do paciente ao tratamento.
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
import pyqtgraph as pg
import numpy as np

from hs3_hardware import hs3_hardware

@dataclass
class BiofeedbackReading:
    """Leitura individual de biofeedback"""
    timestamp: datetime
    frequency: float
    amplitude: float
    offset: float
    measured_response: Optional[float] = None
    impedance: Optional[float] = None
    phase: Optional[float] = None
    quality_score: Optional[float] = None
    notes: str = ""

@dataclass
class SessionBiofeedback:
    """Dados completos de biofeedback de uma sessão"""
    session_id: str
    patient_name: str
    start_time: datetime
    readings: List[BiofeedbackReading]
    statistics: Optional[Dict] = None

class BiofeedbackMonitor(QObject):
    """
    Monitor de biofeedback em tempo real
    Coleta dados do HS3 e calcula métricas de resposta
    """
    
    # Sinais
    reading_available = pyqtSignal(dict)      # Nova leitura disponível
    statistics_updated = pyqtSignal(dict)     # Estatísticas atualizadas
    quality_changed = pyqtSignal(str, float)  # Mudança na qualidade (status, score)
    alert_triggered = pyqtSignal(str, str)    # Alerta (tipo, mensagem)
    
    def __init__(self, sampling_rate: int = 10):
        super().__init__()
        self.sampling_rate = sampling_rate  # Hz
        self.is_monitoring = False
        self.current_session_id = None
        self.readings: List[BiofeedbackReading] = []
        
        # Timer para amostragem
        self.sample_timer = QTimer()
        self.sample_timer.timeout.connect(self._collect_sample)
        self.sample_timer.setInterval(1000 // sampling_rate)  # Converter para ms
        
        # Timer para estatísticas
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.setInterval(5000)  # Atualizar a cada 5 segundos
        
        # Buffers para análise
        self.response_buffer = []
        self.impedance_buffer = []
        self.quality_buffer = []
        self.buffer_size = 100  # Manter últimas 100 amostras
        
        # Limiares de alerta
        self.quality_threshold = 0.7
        self.impedance_threshold = 10000  # Ohms
        self.response_threshold = 0.1     # V
    
    def start_monitoring(self, session_id: str, patient_name: str) -> bool:
        """Inicia monitorização para uma sessão"""
        try:
            if not hs3_hardware.is_connected():
                return False
            
            self.current_session_id = session_id
            self.is_monitoring = True
            self.readings.clear()
            
            # Limpar buffers
            self.response_buffer.clear()
            self.impedance_buffer.clear()
            self.quality_buffer.clear()
            
            # Iniciar timers
            self.sample_timer.start()
            self.stats_timer.start()
            
            print(f"📊 Biofeedback iniciado para sessão {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar biofeedback: {e}")
            return False
    
    def stop_monitoring(self) -> SessionBiofeedback:
        """Para monitorização e retorna dados coletados"""
        try:
            # Parar timers
            self.sample_timer.stop()
            self.stats_timer.stop()
            
            # Criar dados finais
            session_data = SessionBiofeedback(
                session_id=self.current_session_id,
                patient_name="",  # TODO: Obter do contexto
                start_time=self.readings[0].timestamp if self.readings else datetime.now(),
                readings=self.readings.copy(),
                statistics=self._calculate_final_statistics()
            )
            
            # Resetar estado
            self.is_monitoring = False
            self.current_session_id = None
            
            print(f"📊 Biofeedback finalizado - {len(self.readings)} amostras coletadas")
            return session_data
            
        except Exception as e:
            print(f"❌ Erro ao parar biofeedback: {e}")
            return SessionBiofeedback("", "", datetime.now(), [])
    
    def pause_monitoring(self):
        """Pausa monitorização"""
        self.sample_timer.stop()
        self.stats_timer.stop()
    
    def resume_monitoring(self):
        """Retoma monitorização"""
        if self.is_monitoring:
            self.sample_timer.start()
            self.stats_timer.start()
    
    def get_current_statistics(self) -> Dict:
        """Obtém estatísticas atuais"""
        if not self.readings:
            return {}
        
        recent_readings = self.readings[-50:]  # Últimas 50 amostras
        
        # Calcular estatísticas básicas
        responses = [r.measured_response for r in recent_readings if r.measured_response is not None]
        impedances = [r.impedance for r in recent_readings if r.impedance is not None]
        qualities = [r.quality_score for r in recent_readings if r.quality_score is not None]
        
        stats = {
            "total_samples": len(self.readings),
            "recent_samples": len(recent_readings),
            "sampling_rate": self.sampling_rate,
            "session_duration": self._get_session_duration()
        }
        
        if responses:
            stats.update({
                "avg_response": np.mean(responses),
                "std_response": np.std(responses),
                "min_response": np.min(responses),
                "max_response": np.max(responses)
            })
        
        if impedances:
            stats.update({
                "avg_impedance": np.mean(impedances),
                "std_impedance": np.std(impedances),
                "min_impedance": np.min(impedances),
                "max_impedance": np.max(impedances)
            })
        
        if qualities:
            stats.update({
                "avg_quality": np.mean(qualities),
                "quality_trend": self._calculate_trend(qualities)
            })
        
        return stats
    
    def export_data(self, filename: str) -> bool:
        """Exporta dados para arquivo JSON"""
        try:
            session_data = SessionBiofeedback(
                session_id=self.current_session_id or "unknown",
                patient_name="",
                start_time=self.readings[0].timestamp if self.readings else datetime.now(),
                readings=self.readings,
                statistics=self.get_current_statistics()
            )
            
            # Converter para dicionário serializável
            export_data = {
                "session_id": session_data.session_id,
                "patient_name": session_data.patient_name,
                "start_time": session_data.start_time.isoformat(),
                "readings": [asdict(reading) for reading in session_data.readings],
                "statistics": session_data.statistics
            }
            
            # Converter timestamps nos readings
            for reading in export_data["readings"]:
                if isinstance(reading["timestamp"], datetime):
                    reading["timestamp"] = reading["timestamp"].isoformat()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar dados: {e}")
            return False
    
    # Métodos privados
    def _collect_sample(self):
        """Coleta uma amostra de biofeedback"""
        try:
            if not self.is_monitoring:
                return
            
            # Obter estado atual do HS3
            hs3_status = hs3_hardware.get_status()
            
            if not hs3_status.get("generating", False):
                return  # Não está gerando, pular amostra
            
            # TODO: Implementar leituras reais do HS3
            # Por agora, simular dados para desenvolvimento
            current_time = datetime.now()
            
            # Simular leitura (substituir por comando real do HS3)
            measured_response = self._read_response_from_hs3()
            impedance = self._read_impedance_from_hs3()
            phase = self._read_phase_from_hs3()
            
            # Calcular qualidade do sinal
            quality_score = self._calculate_quality_score(measured_response, impedance)
            
            # Criar leitura
            reading = BiofeedbackReading(
                timestamp=current_time,
                frequency=hs3_status.get("current_frequency", 0),
                amplitude=hs3_status.get("current_amplitude", 0),
                offset=hs3_status.get("current_offset", 0),
                measured_response=measured_response,
                impedance=impedance,
                phase=phase,
                quality_score=quality_score
            )
            
            # Adicionar à lista
            self.readings.append(reading)
            
            # Atualizar buffers
            self._update_buffers(reading)
            
            # Verificar alertas
            self._check_alerts(reading)
            
            # Emitir sinal
            self.reading_available.emit(asdict(reading))
            
        except Exception as e:
            print(f"⚠️ Erro ao coletar amostra de biofeedback: {e}")
    
    def _read_response_from_hs3(self) -> Optional[float]:
        """
        Lê resposta medida do HS3
        TODO: Implementar comando real do HS3
        """
        try:
            # Comando simulado - substituir por comando real
            # response = hs3_hardware._send_command("MEASURE:RESPONSE?\n")
            
            # Simulação para desenvolvimento
            base_response = 0.5
            noise = np.random.normal(0, 0.05)
            trend = 0.1 * np.sin(time.time() * 0.1)  # Variação lenta
            
            return base_response + noise + trend
            
        except Exception:
            return None
    
    def _read_impedance_from_hs3(self) -> Optional[float]:
        """
        Lê impedância do HS3
        TODO: Implementar comando real do HS3
        """
        try:
            # Simulação para desenvolvimento
            base_impedance = 1000  # Ohms
            variation = np.random.normal(0, 100)
            
            return max(100, base_impedance + variation)
            
        except Exception:
            return None
    
    def _read_phase_from_hs3(self) -> Optional[float]:
        """
        Lê fase do sinal do HS3
        TODO: Implementar comando real do HS3
        """
        try:
            # Simulação para desenvolvimento
            base_phase = 0  # Graus
            variation = np.random.normal(0, 5)
            
            return base_phase + variation
            
        except Exception:
            return None
    
    def _calculate_quality_score(self, response: Optional[float], 
                                impedance: Optional[float]) -> Optional[float]:
        """Calcula score de qualidade do sinal"""
        try:
            if response is None or impedance is None:
                return None
            
            # Score baseado em múltiplos fatores
            response_score = min(1.0, max(0.0, response / 1.0))  # Normalizar resposta
            impedance_score = 1.0 / (1.0 + impedance / 1000.0)  # Impedância baixa = melhor
            
            # Estabilidade (baseada em variações recentes)
            stability_score = 1.0
            if len(self.response_buffer) > 10:
                recent_std = np.std(self.response_buffer[-10:])
                stability_score = 1.0 / (1.0 + recent_std * 10)
            
            # Score final (média ponderada)
            quality = (response_score * 0.4 + impedance_score * 0.4 + stability_score * 0.2)
            
            return quality
            
        except Exception:
            return None
    
    def _update_buffers(self, reading: BiofeedbackReading):
        """Atualiza buffers circulares"""
        if reading.measured_response is not None:
            self.response_buffer.append(reading.measured_response)
            if len(self.response_buffer) > self.buffer_size:
                self.response_buffer.pop(0)
        
        if reading.impedance is not None:
            self.impedance_buffer.append(reading.impedance)
            if len(self.impedance_buffer) > self.buffer_size:
                self.impedance_buffer.pop(0)
        
        if reading.quality_score is not None:
            self.quality_buffer.append(reading.quality_score)
            if len(self.quality_buffer) > self.buffer_size:
                self.quality_buffer.pop(0)
    
    def _check_alerts(self, reading: BiofeedbackReading):
        """Verifica condições de alerta"""
        try:
            # Alerta de qualidade baixa
            if reading.quality_score is not None and reading.quality_score < self.quality_threshold:
                self.alert_triggered.emit("quality", f"Qualidade baixa: {reading.quality_score:.2f}")
                self.quality_changed.emit("low", reading.quality_score)
            
            # Alerta de impedância alta
            if reading.impedance is not None and reading.impedance > self.impedance_threshold:
                self.alert_triggered.emit("impedance", f"Impedância alta: {reading.impedance:.0f}Ω")
            
            # Alerta de resposta baixa
            if reading.measured_response is not None and reading.measured_response < self.response_threshold:
                self.alert_triggered.emit("response", f"Resposta baixa: {reading.measured_response:.3f}V")
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar alertas: {e}")
    
    def _update_statistics(self):
        """Atualiza estatísticas periodicamente"""
        if self.is_monitoring:
            stats = self.get_current_statistics()
            self.statistics_updated.emit(stats)
    
    def _calculate_final_statistics(self) -> Dict:
        """Calcula estatísticas finais da sessão"""
        if not self.readings:
            return {}
        
        # Análise completa dos dados
        responses = [r.measured_response for r in self.readings if r.measured_response is not None]
        impedances = [r.impedance for r in self.readings if r.impedance is not None]
        qualities = [r.quality_score for r in self.readings if r.quality_score is not None]
        
        stats = {
            "session_summary": {
                "total_samples": len(self.readings),
                "session_duration": self._get_session_duration(),
                "sampling_rate": self.sampling_rate,
                "data_completeness": len(responses) / len(self.readings) if self.readings else 0
            }
        }
        
        if responses:
            stats["response_analysis"] = {
                "mean": float(np.mean(responses)),
                "std": float(np.std(responses)),
                "min": float(np.min(responses)),
                "max": float(np.max(responses)),
                "trend": self._calculate_trend(responses),
                "stability": self._calculate_stability(responses)
            }
        
        if impedances:
            stats["impedance_analysis"] = {
                "mean": float(np.mean(impedances)),
                "std": float(np.std(impedances)),
                "min": float(np.min(impedances)),
                "max": float(np.max(impedances))
            }
        
        if qualities:
            stats["quality_analysis"] = {
                "mean": float(np.mean(qualities)),
                "trend": self._calculate_trend(qualities),
                "below_threshold_percent": len([q for q in qualities if q < self.quality_threshold]) / len(qualities) * 100
            }
        
        return stats
    
    def _get_session_duration(self) -> float:
        """Calcula duração da sessão em segundos"""
        if not self.readings:
            return 0.0
        
        start_time = self.readings[0].timestamp
        end_time = self.readings[-1].timestamp
        
        return (end_time - start_time).total_seconds()
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula tendência dos valores"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Regressão linear simples
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_stability(self, values: List[float]) -> float:
        """Calcula score de estabilidade (0-1)"""
        if len(values) < 10:
            return 0.5
        
        # Calcular variação relativa
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if mean_val == 0:
            return 0.0
        
        cv = std_val / mean_val  # Coeficiente de variação
        stability = 1.0 / (1.0 + cv * 5)  # Normalizar para 0-1
        
        return float(stability)

# Widget de visualização em tempo real
class BiofeedbackWidget(QWidget):
    """Widget para mostrar dados de biofeedback em tempo real"""
    
    def __init__(self, monitor: BiofeedbackMonitor):
        super().__init__()
        self.monitor = monitor
        self.setup_ui()
        self.connect_signals()
        
        # Dados para gráficos
        self.time_data = []
        self.response_data = []
        self.impedance_data = []
        self.quality_data = []
        self.max_points = 300  # Manter últimos 5 minutos a 1Hz
    
    def setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("📊 Biofeedback em Tempo Real")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Indicadores de estado
        status_layout = QHBoxLayout()
        
        self.quality_bar = QProgressBar()
        self.quality_bar.setRange(0, 100)
        self.quality_bar.setFormat("Qualidade: %p%")
        status_layout.addWidget(QLabel("Qualidade:"))
        status_layout.addWidget(self.quality_bar)
        
        self.status_label = QLabel("Estado: Aguardando...")
        status_layout.addWidget(self.status_label)
        
        layout.addLayout(status_layout)
        
        # Gráficos
        self.graph_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph_widget)
        
        # Gráfico de resposta
        self.response_plot = self.graph_widget.addPlot(title="Resposta Medida (V)")
        self.response_curve = self.response_plot.plot(pen='b')
        self.response_plot.setLabel('left', 'Tensão', units='V')
        self.response_plot.setLabel('bottom', 'Tempo', units='s')
        
        # Nova linha
        self.graph_widget.nextRow()
        
        # Gráfico de impedância
        self.impedance_plot = self.graph_widget.addPlot(title="Impedância (Ω)")
        self.impedance_curve = self.impedance_plot.plot(pen='r')
        self.impedance_plot.setLabel('left', 'Impedância', units='Ω')
        self.impedance_plot.setLabel('bottom', 'Tempo', units='s')
    
    def connect_signals(self):
        """Conecta sinais do monitor"""
        self.monitor.reading_available.connect(self.update_display)
        self.monitor.statistics_updated.connect(self.update_statistics)
        self.monitor.quality_changed.connect(self.update_quality_indicator)
        self.monitor.alert_triggered.connect(self.show_alert)
    
    def update_display(self, reading_data: Dict):
        """Atualiza display com nova leitura"""
        try:
            # Adicionar aos dados
            current_time = time.time()
            self.time_data.append(current_time)
            
            if reading_data.get('measured_response') is not None:
                self.response_data.append(reading_data['measured_response'])
            else:
                self.response_data.append(0)
            
            if reading_data.get('impedance') is not None:
                self.impedance_data.append(reading_data['impedance'])
            else:
                self.impedance_data.append(0)
            
            if reading_data.get('quality_score') is not None:
                self.quality_data.append(reading_data['quality_score'])
            else:
                self.quality_data.append(0)
            
            # Manter tamanho máximo
            if len(self.time_data) > self.max_points:
                self.time_data = self.time_data[-self.max_points:]
                self.response_data = self.response_data[-self.max_points:]
                self.impedance_data = self.impedance_data[-self.max_points:]
                self.quality_data = self.quality_data[-self.max_points:]
            
            # Atualizar gráficos
            if len(self.time_data) > 1:
                # Normalizar tempo (últimos pontos)
                time_relative = [t - self.time_data[0] for t in self.time_data]
                
                self.response_curve.setData(time_relative, self.response_data)
                self.impedance_curve.setData(time_relative, self.impedance_data)
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar display: {e}")
    
    def update_statistics(self, stats: Dict):
        """Atualiza estatísticas"""
        try:
            # Atualizar barra de qualidade
            avg_quality = stats.get('avg_quality', 0)
            self.quality_bar.setValue(int(avg_quality * 100))
            
            # Atualizar estado
            total_samples = stats.get('total_samples', 0)
            duration = stats.get('session_duration', 0)
            self.status_label.setText(f"Amostras: {total_samples} | Duração: {duration:.1f}s")
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar estatísticas: {e}")
    
    def update_quality_indicator(self, status: str, score: float):
        """Atualiza indicador de qualidade"""
        if status == "low":
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        else:
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
        
        self.quality_bar.setValue(int(score * 100))
    
    def show_alert(self, alert_type: str, message: str):
        """Mostra alerta"""
        print(f"🚨 Alerta {alert_type}: {message}")
        # TODO: Implementar notificação visual mais evidente

# Instância global do monitor
biofeedback_monitor = BiofeedbackMonitor()
