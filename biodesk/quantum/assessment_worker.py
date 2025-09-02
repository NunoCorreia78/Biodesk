"""
Sistema de Avaliação (Challenge-Response) - Biodesk Quantum
═══════════════════════════════════════════════════════════════════════

Sistema de avaliação automática que testa frequências individuais,
mede respostas fisiológicas reais e classifica por eficácia.

Funcionalidades:
- Teste sequencial de frequências com medição objetiva
- Cálculo de impedância e métricas bioeléctricas
- Ranking automático baseado em score composto
- Detecção de artefactos e problemas de contacto
- Baseline automático para comparação relativa
"""

import time
import random
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PyQt6.QtCore import QThread, pyqtSignal

# Importar módulos do sistema
try:
    from .safety import SafetyLimits, SafetyError, assert_safe_output
    # from .hs3_service import HS3Service, HS3NotFoundError  # Descomentado quando necessário
except ImportError:
    # Fallback para testes diretos
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from biodesk.quantum.safety import SafetyLimits, SafetyError, assert_safe_output


class AssessmentState(Enum):
    """Estados do worker de avaliação"""
    IDLE = "idle"
    PREPARING = "preparing"
    BASELINE = "baseline"
    TESTING = "testing"
    ANALYZING = "analyzing"
    FINISHED = "finished"
    ERROR = "error"
    ABORTED = "aborted"


@dataclass
class FrequencyMetrics:
    """Métricas calculadas para uma frequência específica"""
    frequency_hz: float
    
    # Métricas brutas do canal do paciente (CH2)
    vrms_patient: float
    vpp_patient: float
    vdc_patient: float
    
    # Métricas do canal shunt (CH1) 
    vrms_shunt: float
    current_estimated_ma: float
    
    # Impedância estimada
    impedance_ohm: float
    impedance_phase_deg: float
    
    # Deltas relativos ao baseline
    delta_z_percent: float
    delta_rms_percent: float
    delta_vpp_percent: float
    delta_energy_01_5hz: float
    
    # Score e qualidade
    score: float
    artifact_level: float
    is_valid: bool
    
    # Metadados
    test_duration_s: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BaselineMetrics:
    """Métricas de baseline (sem estímulo)"""
    vrms_patient: float
    vpp_patient: float
    vdc_patient: float
    vrms_shunt: float
    impedance_ohm: float
    energy_01_5hz: float
    noise_level: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AssessmentConfig:
    """Configuração da avaliação"""
    frequencies: List[float]
    dwell_s: float = 3.0
    test_amp_vpp: float = 1.0
    r_shunt_ohm: float = 100_000.0
    top_n: int = 10
    baseline_duration_s: float = 5.0
    sample_rate_hz: float = 1000.0
    voltage_range_v: float = 2.0
    randomize_order: bool = True
    safety_limits: Optional[SafetyLimits] = None
    
    def __post_init__(self):
        """Validação após criação"""
        if not self.frequencies:
            raise ValueError("Lista de frequências não pode estar vazia")
        if self.dwell_s <= 0:
            raise ValueError("Tempo de permanência deve ser positivo")
        if self.test_amp_vpp <= 0:
            raise ValueError("Amplitude de teste deve ser positiva")
        if self.r_shunt_ohm <= 0:
            raise ValueError("Resistência shunt deve ser positiva")
        if self.top_n <= 0:
            raise ValueError("Top N deve ser positivo")


class AssessmentWorker(QThread):
    """
    Worker thread para execução de avaliação de frequências
    
    Executa teste sequencial de frequências, mede respostas reais
    e calcula ranking baseado em métricas objetivas.
    """
    
    # Sinais Qt
    progress = pyqtSignal(int)              # progress(percentage)
    baseline_measured = pyqtSignal(dict)    # baseline_measured(baseline_dict)
    result_item = pyqtSignal(dict)          # result_item(frequency_result_dict)
    finished = pyqtSignal(list)             # finished(sorted_results_list)
    error = pyqtSignal(str)                 # error(error_message)
    state_changed = pyqtSignal(str)         # state_changed(new_state)
    
    def __init__(self, hs3_service=None):
        """
        Inicializar worker de avaliação
        
        Args:
            hs3_service: Instância do HS3Service (obrigatório para funcionamento real)
        """
        super().__init__()
        
        self.logger = logging.getLogger("AssessmentWorker")
        self.hs3_service = hs3_service
        
        # Estado do worker
        self.state = AssessmentState.IDLE
        self.config: Optional[AssessmentConfig] = None
        self.baseline: Optional[BaselineMetrics] = None
        self.results: List[FrequencyMetrics] = []
        
        # Controlo de execução
        self.abort_requested = False
        self.current_frequency_index = 0
        
        # Cache para otimização
        self._fft_cache = {}
    
    def set_hs3_service(self, hs3_service) -> None:
        """Definir serviço HS3"""
        self.hs3_service = hs3_service
        self.logger.info("🔌 HS3Service configurado no AssessmentWorker")
    
    def start_assessment(self, config: AssessmentConfig) -> bool:
        """
        Iniciar avaliação de frequências
        
        Args:
            config: Configuração da avaliação
            
        Returns:
            True se iniciado com sucesso, False caso contrário
        """
        if self.isRunning():
            self.logger.warning("⚠️ Avaliação já está em execução")
            return False
        
        if not self.hs3_service:
            self.error.emit("❌ HS3Service não configurado")
            return False
        
        try:
            # Validar configuração
            self._validate_config(config)
            
            # Preparar execução
            self.config = config
            self.baseline = None
            self.results = []
            self.abort_requested = False
            self.current_frequency_index = 0
            
            # Iniciar thread
            self.start()
            
            self.logger.info(f"▶️ Avaliação iniciada: {len(config.frequencies)} frequências")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao iniciar avaliação: {e}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
            return False
    
    def abort_assessment(self) -> None:
        """Abortar avaliação em execução"""
        if self.isRunning():
            self.abort_requested = True
            self.logger.info("🛑 Abort solicitado")
    
    def run(self) -> None:
        """Método principal da thread (executado automaticamente)"""
        try:
            self._change_state(AssessmentState.PREPARING)
            
            # Verificar hardware
            if not self.hs3_service.is_connected():
                raise RuntimeError("HS3 não está conectado")
            
            # 1. Medir baseline
            self._measure_baseline()
            
            if self.abort_requested:
                self._change_state(AssessmentState.ABORTED)
                return
            
            # 2. Preparar lista de frequências
            frequencies_to_test = self.config.frequencies.copy()
            if self.config.randomize_order:
                random.shuffle(frequencies_to_test)
                self.logger.info("🔀 Ordem de teste randomizada")
            
            # 3. Testar cada frequência
            self._change_state(AssessmentState.TESTING)
            
            for i, frequency in enumerate(frequencies_to_test):
                if self.abort_requested:
                    break
                
                self.current_frequency_index = i
                progress_percent = int((i / len(frequencies_to_test)) * 100)
                self.progress.emit(progress_percent)
                
                # Testar frequência individual
                result = self._test_single_frequency(frequency)
                
                if result:
                    self.results.append(result)
                    
                    # Emitir resultado individual
                    result_dict = self._frequency_metrics_to_dict(result)
                    self.result_item.emit(result_dict)
                    
                    self.logger.info(
                        f"✅ Frequência {frequency:.1f}Hz: Score {result.score:.3f}"
                    )
                else:
                    self.logger.warning(f"⚠️ Frequência {frequency:.1f}Hz: Teste inválido")
            
            if self.abort_requested:
                self._change_state(AssessmentState.ABORTED)
                return
            
            # 4. Analisar e ranquear resultados
            self._change_state(AssessmentState.ANALYZING)
            self.progress.emit(100)
            
            # Ordenar por score (maior primeiro)
            sorted_results = sorted(
                self.results, 
                key=lambda x: x.score if x.is_valid else -1000,
                reverse=True
            )
            
            # Limitar ao top N
            top_results = sorted_results[:self.config.top_n]
            
            # Emitir resultados finais
            final_results = [self._frequency_metrics_to_dict(r) for r in top_results]
            self.finished.emit(final_results)
            
            self._change_state(AssessmentState.FINISHED)
            
            self.logger.info(
                f"🏁 Avaliação concluída: {len(self.results)} testadas, "
                f"Top {len(top_results)} selecionadas"
            )
            
        except Exception as e:
            error_msg = f"Erro durante avaliação: {e}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
            self._change_state(AssessmentState.ERROR)
    
    def _validate_config(self, config: AssessmentConfig) -> None:
        """Validar configuração da avaliação"""
        # Validar segurança se especificado
        if config.safety_limits:
            assert_safe_output(config.test_amp_vpp, 0.0, config.safety_limits)
        
        # Validar frequências
        for freq in config.frequencies:
            if freq <= 0:
                raise ValueError(f"Frequência inválida: {freq}")
            if freq > 100000:  # Limite razoável
                raise ValueError(f"Frequência muito alta: {freq}")
        
        # Validar parâmetros de aquisição
        if config.sample_rate_hz < 2 * max(config.frequencies):
            self.logger.warning(
                f"⚠️ Sample rate {config.sample_rate_hz}Hz pode ser insuficiente "
                f"para frequência máxima {max(config.frequencies)}Hz"
            )
    
    def _change_state(self, new_state: AssessmentState) -> None:
        """Mudar estado e emitir sinal"""
        old_state = self.state
        self.state = new_state
        self.state_changed.emit(new_state.value)
        self.logger.info(f"📊 Estado: {old_state.value} → {new_state.value}")
    
    def _measure_baseline(self) -> None:
        """Medir métricas de baseline (sem estímulo)"""
        self._change_state(AssessmentState.BASELINE)
        self.logger.info(f"📏 Medindo baseline por {self.config.baseline_duration_s:.1f}s...")
        
        try:
            # Garantir que não há saída
            self.hs3_service.stop_output()
            time.sleep(0.5)  # Aguardar estabilização
            
            # Iniciar stream
            self.hs3_service.start_stream(
                sample_hz=self.config.sample_rate_hz,
                v_range=self.config.voltage_range_v
            )
            
            # Aguardar estabilização do stream
            time.sleep(0.5)
            
            # Capturar dados de baseline
            ch1_data, ch2_data = self.hs3_service.read_stream(self.config.baseline_duration_s)
            
            self.hs3_service.stop_stream()
            
            # Calcular métricas de baseline
            self.baseline = self._calculate_baseline_metrics(ch1_data, ch2_data)
            
            # Emitir baseline
            baseline_dict = {
                'vrms_patient': self.baseline.vrms_patient,
                'vpp_patient': self.baseline.vpp_patient,
                'vdc_patient': self.baseline.vdc_patient,
                'vrms_shunt': self.baseline.vrms_shunt,
                'impedance_ohm': self.baseline.impedance_ohm,
                'energy_01_5hz': self.baseline.energy_01_5hz,
                'noise_level': self.baseline.noise_level
            }
            
            self.baseline_measured.emit(baseline_dict)
            
            self.logger.info(
                f"📏 Baseline: Z={self.baseline.impedance_ohm:.0f}Ω, "
                f"RMS={self.baseline.vrms_patient*1000:.1f}mV, "
                f"Ruído={self.baseline.noise_level*1000:.1f}mV"
            )
            
        except Exception as e:
            raise RuntimeError(f"Erro ao medir baseline: {e}")
    
    def _test_single_frequency(self, frequency: float) -> Optional[FrequencyMetrics]:
        """
        Testar uma frequência individual
        
        Args:
            frequency: Frequência a testar em Hz
            
        Returns:
            Métricas calculadas ou None se inválido
        """
        try:
            self.logger.debug(f"🎵 Testando {frequency:.1f}Hz...")
            
            # Configurar gerador
            self.hs3_service.configure_generator(
                signal_type="sine",
                amplitude_vpp=self.config.test_amp_vpp,
                offset_v=0.0
            )
            
            self.hs3_service.set_frequency(frequency)
            
            # Iniciar stream
            self.hs3_service.start_stream(
                sample_hz=self.config.sample_rate_hz,
                v_range=self.config.voltage_range_v
            )
            
            # Pequena pausa para estabilização
            time.sleep(0.2)
            
            # Iniciar estímulo
            start_time = time.time()
            self.hs3_service.start_output()
            
            # Capturar dados durante estímulo
            ch1_data, ch2_data = self.hs3_service.read_stream(self.config.dwell_s)
            
            # Parar estímulo
            self.hs3_service.stop_output()
            self.hs3_service.stop_stream()
            
            test_duration = time.time() - start_time
            
            # Calcular métricas
            metrics = self._calculate_frequency_metrics(
                frequency, ch1_data, ch2_data, test_duration
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao testar {frequency:.1f}Hz: {e}")
            
            # Garantir que tudo está parado
            try:
                self.hs3_service.stop_output()
                self.hs3_service.stop_stream()
            except:
                pass
            
            return None
    
    def _calculate_baseline_metrics(self, ch1_data: np.ndarray, ch2_data: np.ndarray) -> BaselineMetrics:
        """Calcular métricas de baseline"""
        # Métricas básicas do paciente (CH2)
        vrms_patient = np.sqrt(np.mean(ch2_data**2))
        vpp_patient = np.ptp(ch2_data)
        vdc_patient = np.mean(ch2_data)
        
        # Métricas do shunt (CH1)
        vrms_shunt = np.sqrt(np.mean(ch1_data**2))
        
        # Impedância estimada (simplificada)
        if vrms_shunt > 1e-6:  # Evitar divisão por zero
            impedance_ohm = (vrms_patient / vrms_shunt) * self.config.r_shunt_ohm
        else:
            impedance_ohm = float('inf')
        
        # Energia na banda 0.1-5Hz
        energy_01_5hz = self._calculate_band_energy(ch2_data, 0.1, 5.0)
        
        # Nível de ruído (desvio padrão)
        noise_level = np.std(ch2_data)
        
        return BaselineMetrics(
            vrms_patient=vrms_patient,
            vpp_patient=vpp_patient,
            vdc_patient=vdc_patient,
            vrms_shunt=vrms_shunt,
            impedance_ohm=impedance_ohm,
            energy_01_5hz=energy_01_5hz,
            noise_level=noise_level
        )
    
    def _calculate_frequency_metrics(self, 
                                   frequency: float,
                                   ch1_data: np.ndarray, 
                                   ch2_data: np.ndarray,
                                   test_duration: float) -> FrequencyMetrics:
        """Calcular métricas para uma frequência específica"""
        
        # Métricas brutas do paciente (CH2)
        vrms_patient = np.sqrt(np.mean(ch2_data**2))
        vpp_patient = np.ptp(ch2_data)
        vdc_patient = np.mean(ch2_data)
        
        # Métricas do shunt (CH1)
        vrms_shunt = np.sqrt(np.mean(ch1_data**2))
        current_estimated_ma = (vrms_shunt / self.config.r_shunt_ohm) * 1000  # mA
        
        # Impedância estimada
        if vrms_shunt > 1e-6:
            impedance_ohm = (vrms_patient / vrms_shunt) * self.config.r_shunt_ohm
        else:
            impedance_ohm = float('inf')
        
        # Fase da impedância (simplificada usando correlação cruzada)
        impedance_phase_deg = self._calculate_phase_difference(ch1_data, ch2_data)
        
        # Energia na banda 0.1-5Hz
        energy_01_5hz = self._calculate_band_energy(ch2_data, 0.1, 5.0)
        
        # Calcular deltas relativos ao baseline
        if self.baseline:
            delta_z_percent = ((impedance_ohm - self.baseline.impedance_ohm) / 
                             self.baseline.impedance_ohm) * 100 if self.baseline.impedance_ohm != 0 else 0
            
            delta_rms_percent = ((vrms_patient - self.baseline.vrms_patient) / 
                               self.baseline.vrms_patient) * 100 if self.baseline.vrms_patient != 0 else 0
            
            delta_vpp_percent = ((vpp_patient - self.baseline.vpp_patient) / 
                               self.baseline.vpp_patient) * 100 if self.baseline.vpp_patient != 0 else 0
            
            delta_energy_01_5hz = energy_01_5hz - self.baseline.energy_01_5hz
        else:
            delta_z_percent = 0
            delta_rms_percent = 0
            delta_vpp_percent = 0
            delta_energy_01_5hz = 0
        
        # Calcular nível de artefacto
        artifact_level = self._calculate_artifact_level(ch2_data)
        
        # Calcular score composto
        score = self._calculate_score(
            delta_z_percent, delta_rms_percent, delta_vpp_percent, artifact_level
        )
        
        # Validar resultado
        is_valid = self._validate_measurement(impedance_ohm, vrms_patient, artifact_level)
        
        return FrequencyMetrics(
            frequency_hz=frequency,
            vrms_patient=vrms_patient,
            vpp_patient=vpp_patient,
            vdc_patient=vdc_patient,
            vrms_shunt=vrms_shunt,
            current_estimated_ma=current_estimated_ma,
            impedance_ohm=impedance_ohm,
            impedance_phase_deg=impedance_phase_deg,
            delta_z_percent=delta_z_percent,
            delta_rms_percent=delta_rms_percent,
            delta_vpp_percent=delta_vpp_percent,
            delta_energy_01_5hz=delta_energy_01_5hz,
            score=score,
            artifact_level=artifact_level,
            is_valid=is_valid,
            test_duration_s=test_duration
        )
    
    def _calculate_band_energy(self, data: np.ndarray, f_low: float, f_high: float) -> float:
        """Calcular energia numa banda de frequência específica"""
        # Cache FFT para otimização
        data_key = id(data)
        if data_key not in self._fft_cache:
            fft = np.fft.fft(data)
            freqs = np.fft.fftfreq(len(data), 1/self.config.sample_rate_hz)
            self._fft_cache[data_key] = (fft, freqs)
        else:
            fft, freqs = self._fft_cache[data_key]
        
        # Encontrar índices da banda
        band_mask = (np.abs(freqs) >= f_low) & (np.abs(freqs) <= f_high)
        
        # Calcular energia na banda
        band_energy = np.sum(np.abs(fft[band_mask])**2)
        
        return float(band_energy)
    
    def _calculate_phase_difference(self, ch1_data: np.ndarray, ch2_data: np.ndarray) -> float:
        """Calcular diferença de fase entre canais (simplificada)"""
        try:
            # Correlação cruzada para encontrar delay
            correlation = np.correlate(ch1_data, ch2_data, mode='full')
            lag = np.argmax(correlation) - len(ch2_data) + 1
            
            # Converter delay para fase (aproximação)
            phase_deg = (lag / len(ch1_data)) * 360
            
            # Normalizar para [-180, 180]
            while phase_deg > 180:
                phase_deg -= 360
            while phase_deg < -180:
                phase_deg += 360
            
            return float(phase_deg)
            
        except:
            return 0.0  # Fallback
    
    def _calculate_artifact_level(self, data: np.ndarray) -> float:
        """
        Calcular nível de artefacto usando heurística simples
        
        Combina variância alta e detecção de spikes
        """
        # Variância normalizada
        variance_norm = np.var(data) / (np.mean(np.abs(data)) + 1e-10)
        
        # Detecção de spikes (valores > 3 desvios padrão)
        std_dev = np.std(data)
        mean_val = np.mean(data)
        spike_mask = np.abs(data - mean_val) > 3 * std_dev
        spike_rate = np.sum(spike_mask) / len(data)
        
        # Score combinado de artefacto
        artifact_score = variance_norm + 10 * spike_rate
        
        return float(artifact_score)
    
    def _calculate_score(self, delta_z: float, delta_rms: float, 
                        delta_vpp: float, artifact: float) -> float:
        """
        Calcular score composto para ranking
        
        Fórmula: E = 1.5*|ΔZ| + 1.0*|ΔRMS| + 0.5*|ΔVpp| - 0.3*artefacto
        """
        score = (1.5 * abs(delta_z) + 
                1.0 * abs(delta_rms) + 
                0.5 * abs(delta_vpp) - 
                0.3 * artifact)
        
        return float(score)
    
    def _validate_measurement(self, impedance: float, vrms: float, artifact: float) -> bool:
        """Validar se a medição é confiável"""
        # Impedância absurda indica perda de contacto
        if impedance > 10_000_000 or impedance < 100:  # 100Ω a 10MΩ
            return False
        
        # Sinal muito baixo
        if vrms < 1e-6:  # < 1μV
            return False
        
        # Artefacto excessivo
        if artifact > 100:  # Threshold empírico
            return False
        
        return True
    
    def _frequency_metrics_to_dict(self, metrics: FrequencyMetrics) -> Dict[str, Any]:
        """Converter FrequencyMetrics para dicionário"""
        return {
            'frequency_hz': metrics.frequency_hz,
            'vrms_patient': metrics.vrms_patient,
            'vpp_patient': metrics.vpp_patient,
            'vdc_patient': metrics.vdc_patient,
            'vrms_shunt': metrics.vrms_shunt,
            'current_estimated_ma': metrics.current_estimated_ma,
            'impedance_ohm': metrics.impedance_ohm,
            'impedance_phase_deg': metrics.impedance_phase_deg,
            'delta_z_percent': metrics.delta_z_percent,
            'delta_rms_percent': metrics.delta_rms_percent,
            'delta_vpp_percent': metrics.delta_vpp_percent,
            'delta_energy_01_5hz': metrics.delta_energy_01_5hz,
            'score': metrics.score,
            'artifact_level': metrics.artifact_level,
            'is_valid': metrics.is_valid,
            'test_duration_s': metrics.test_duration_s,
            'timestamp': metrics.timestamp.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════
# TESTES UNITÁRIOS
# ═══════════════════════════════════════════════════════════════════════

class MockHS3Service:
    """Mock do HS3Service para testes unitários"""
    
    def __init__(self):
        self.connected = True
        self.generating = False
        self.streaming = False
        self.current_frequency = 0.0
        self.current_amplitude = 0.0
    
    def is_connected(self) -> bool:
        return self.connected
    
    def configure_generator(self, signal_type: str, amplitude_vpp: float, offset_v: float):
        self.current_amplitude = amplitude_vpp
    
    def set_frequency(self, freq_hz: float):
        self.current_frequency = freq_hz
    
    def start_output(self):
        self.generating = True
    
    def stop_output(self):
        self.generating = False
    
    def start_stream(self, sample_hz: float, v_range: float):
        self.streaming = True
        self.sample_rate = sample_hz
    
    def stop_stream(self):
        self.streaming = False
    
    def read_stream(self, seconds: float) -> Tuple[np.ndarray, np.ndarray]:
        """Gerar dados simulados realistas"""
        n_samples = int(seconds * self.sample_rate)
        t = np.linspace(0, seconds, n_samples)
        
        # Simular resposta realística
        if self.generating and self.current_frequency > 0:
            # CH1 (shunt): sinal de corrente
            ch1_signal = 0.001 * np.sin(2 * np.pi * self.current_frequency * t)
            ch1_noise = 0.0001 * np.random.normal(0, 1, n_samples)
            ch1_data = ch1_signal + ch1_noise
            
            # CH2 (paciente): sinal de tensão com impedância simulada
            z_sim = 1000  # 1kΩ simulado
            ch2_signal = ch1_signal * z_sim * (1 + 0.1 * np.sin(2 * np.pi * 0.5 * t))  # Variação lenta
            ch2_noise = 0.001 * np.random.normal(0, 1, n_samples)
            ch2_data = ch2_signal + ch2_noise
        else:
            # Apenas ruído de baseline
            ch1_data = 0.0001 * np.random.normal(0, 1, n_samples)
            ch2_data = 0.001 * np.random.normal(0, 1, n_samples)
        
        return ch1_data, ch2_data


def test_assessment_config():
    """Teste de configuração de avaliação"""
    config = AssessmentConfig(
        frequencies=[100.0, 200.0, 300.0],
        dwell_s=2.0,
        test_amp_vpp=0.5,
        r_shunt_ohm=100000.0,
        top_n=5
    )
    
    assert config.frequencies == [100.0, 200.0, 300.0]
    assert config.dwell_s == 2.0
    assert config.test_amp_vpp == 0.5
    assert config.top_n == 5


def test_frequency_metrics_creation():
    """Teste de criação de métricas de frequência"""
    metrics = FrequencyMetrics(
        frequency_hz=440.0,
        vrms_patient=0.001,
        vpp_patient=0.003,
        vdc_patient=0.0,
        vrms_shunt=0.0001,
        current_estimated_ma=1.0,
        impedance_ohm=1000.0,
        impedance_phase_deg=10.0,
        delta_z_percent=5.0,
        delta_rms_percent=10.0,
        delta_vpp_percent=15.0,
        delta_energy_01_5hz=0.001,
        score=25.0,
        artifact_level=0.1,
        is_valid=True,
        test_duration_s=3.0
    )
    
    assert metrics.frequency_hz == 440.0
    assert metrics.impedance_ohm == 1000.0
    assert metrics.score == 25.0
    assert metrics.is_valid is True


def test_mock_hs3_service():
    """Teste do mock HS3Service"""
    mock_hs3 = MockHS3Service()
    
    assert mock_hs3.is_connected() is True
    
    mock_hs3.configure_generator("sine", 1.0, 0.0)
    mock_hs3.set_frequency(440.0)
    mock_hs3.start_output()
    mock_hs3.start_stream(1000.0, 2.0)
    
    ch1, ch2 = mock_hs3.read_stream(1.0)
    
    assert len(ch1) == 1000
    assert len(ch2) == 1000
    assert np.std(ch1) > 0  # Tem sinal
    assert np.std(ch2) > 0  # Tem sinal


def test_assessment_worker_initialization():
    """Teste de inicialização do worker"""
    mock_hs3 = MockHS3Service()
    worker = AssessmentWorker(mock_hs3)
    
    assert worker.hs3_service is not None
    assert worker.state == AssessmentState.IDLE
    assert worker.config is None
    assert worker.baseline is None
    assert len(worker.results) == 0


if __name__ == "__main__":
    # Executar testes
    print("🧪 Executando testes do AssessmentWorker...")
    
    test_assessment_config()
    print("✅ test_assessment_config")
    
    test_frequency_metrics_creation()
    print("✅ test_frequency_metrics_creation")
    
    test_mock_hs3_service()
    print("✅ test_mock_hs3_service")
    
    test_assessment_worker_initialization()
    print("✅ test_assessment_worker_initialization")
    
    print("🎉 Todos os testes do AssessmentWorker passaram!")
    print("\n💡 NOTA: Para teste completo com simulação, use:")
    print("   python -c 'from biodesk.quantum.assessment_worker import *; run_simulation_test()'")


def run_simulation_test():
    """Teste de simulação completa (não executado automaticamente)"""
    from PyQt6.QtCore import QCoreApplication
    import sys
    
    app = QCoreApplication(sys.argv)
    
    print("\n🔬 TESTE DE SIMULAÇÃO COMPLETA")
    print("═" * 40)
    
    # Configurar mock
    mock_hs3 = MockHS3Service()
    
    # Configurar worker
    worker = AssessmentWorker(mock_hs3)
    
    # Configurar sinais para captura
    results_captured = []
    
    def capture_result(result_dict):
        results_captured.append(result_dict)
        freq = result_dict['frequency_hz']
        score = result_dict['score']
        print(f"   📊 {freq:.1f}Hz: Score {score:.2f}")
    
    def capture_baseline(baseline_dict):
        print(f"   📏 Baseline: Z={baseline_dict['impedance_ohm']:.0f}Ω")
    
    def capture_finished(final_results):
        print(f"   🏁 Avaliação concluída: Top {len(final_results)} selecionadas")
        for i, result in enumerate(final_results):
            freq = result['frequency_hz']
            score = result['score']
            print(f"      #{i+1}: {freq:.1f}Hz (Score: {score:.2f})")
    
    worker.result_item.connect(capture_result)
    worker.baseline_measured.connect(capture_baseline)
    worker.finished.connect(capture_finished)
    
    # Configurar avaliação
    config = AssessmentConfig(
        frequencies=[100.0, 200.0, 300.0, 440.0, 528.0],
        dwell_s=1.0,  # Teste rápido
        test_amp_vpp=0.5,
        top_n=3
    )
    
    print(f"▶️ Iniciando avaliação de {len(config.frequencies)} frequências...")
    
    if worker.start_assessment(config):
        # Aguardar conclusão
        worker.wait(10000)  # 10s timeout
        
        print(f"✅ Resultados capturados: {len(results_captured)}")
    else:
        print("❌ Falha ao iniciar avaliação")
    
    print("🎉 Teste de simulação concluído!")
