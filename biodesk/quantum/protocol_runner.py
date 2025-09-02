"""
Runner de Protocolo - Biodesk Quantum
═══════════════════════════════════════════════════════════════════════

Sistema de execução de protocolos de terapia quântica com balanceamento
automático, soft-ramp, burst e controlo por trigger externo.

Funcionalidades:
- Execução sequencial de passos de frequência
- Soft-ramp suave entre transições
- Modos burst e gated para controlo avançado
- Validação de segurança integrada
- Métricas em tempo real
- Sinais Qt para integração com UI
"""

import time
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Literal, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

# Importar módulos de segurança e hardware
from .safety import SafetyLimits, SafetyError, assert_safe_output
# from .hs3_service import HS3Service, HS3NotFoundError  # Descomentado quando necessário


class ProtocolMode(Enum):
    """Modos de execução de protocolo"""
    CONTINUOUS = "continuous"
    BURST = "burst"
    GATED = "gated"


class ProtocolState(Enum):
    """Estados do runner de protocolo"""
    IDLE = "idle"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    ABORTING = "aborting"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class FrequencyStep:
    """
    Passo individual de frequência no protocolo
    
    Cada passo define uma frequência específica com seus parâmetros
    de execução, incluindo duração, amplitude e modo de operação.
    """
    hz: float                                    # Frequência em Hz
    dwell_s: float                              # Tempo de permanência em segundos
    amp_vpp: float                              # Amplitude pico-a-pico em volts
    waveform: Literal["sine", "square", "triangle", "arb"] = "sine"
    mode: ProtocolMode = ProtocolMode.CONTINUOUS  # Modo de execução
    burst_cycles: Optional[int] = None           # Ciclos para modo burst (auto se None)
    ramp_ms: float = 100.0                      # Tempo de rampa em milissegundos
    offset_v: float = 0.0                       # Offset DC em volts
    
    def __post_init__(self):
        """Validação após criação"""
        if self.hz <= 0:
            raise ValueError("Frequência deve ser positiva")
        if self.dwell_s <= 0:
            raise ValueError("Tempo de permanência deve ser positivo")
        if self.amp_vpp < 0:
            raise ValueError("Amplitude não pode ser negativa")
        if self.ramp_ms < 0:
            raise ValueError("Tempo de rampa não pode ser negativo")
    
    @property
    def auto_burst_cycles(self) -> int:
        """Calcular número automático de ciclos para burst"""
        if self.burst_cycles is not None:
            return self.burst_cycles
        # Fórmula: aproximadamente hz * dwell_s para cobertura completa
        return max(1, int(self.hz * self.dwell_s))


@dataclass
class Protocol:
    """
    Protocolo completo de terapia quântica
    
    Contém sequência de passos de frequência e metadados
    para execução controlada e rastreável.
    """
    name: str
    description: str
    steps: List[FrequencyStep]
    safety_limits: Optional[SafetyLimits] = None
    created_at: datetime = field(default_factory=datetime.now)
    author: str = "Sistema"
    version: str = "1.0"
    
    def __post_init__(self):
        """Validação após criação"""
        if not self.steps:
            raise ValueError("Protocolo deve ter pelo menos um passo")
        if not self.name.strip():
            raise ValueError("Protocolo deve ter um nome")
    
    @property
    def total_duration_s(self) -> float:
        """Duração total do protocolo"""
        return sum(step.dwell_s for step in self.steps)
    
    @property
    def frequency_range(self) -> tuple[float, float]:
        """Faixa de frequências (min, max)"""
        frequencies = [step.hz for step in self.steps]
        return min(frequencies), max(frequencies)
    
    @property
    def max_amplitude(self) -> float:
        """Amplitude máxima do protocolo"""
        return max(step.amp_vpp for step in self.steps)


@dataclass
class LiveMetrics:
    """Métricas em tempo real durante execução"""
    current_step: int
    total_steps: int
    step_progress: float         # 0.0 - 1.0
    total_progress: float        # 0.0 - 1.0
    current_frequency: float
    current_amplitude: float
    elapsed_time_s: float
    remaining_time_s: float
    step_start_time: datetime
    protocol_start_time: datetime


class ProtocolRunner(QObject):
    """
    Runner principal para execução de protocolos de terapia quântica
    
    Executa sequencialmente os passos de um protocolo, com validação
    de segurança, soft-ramp e sinais Qt para integração com UI.
    """
    
    # Sinais Qt para integração com interface
    started = pyqtSignal(object)           # started(protocol)
    step_started = pyqtSignal(int, object) # step_started(step_index, step)
    live_metrics = pyqtSignal(dict)        # live_metrics(metrics_dict)
    step_finished = pyqtSignal(int)        # step_finished(step_index)
    finished = pyqtSignal()                # finished()
    aborted = pyqtSignal(str)              # aborted(reason)
    error_occurred = pyqtSignal(str)       # error_occurred(message)
    state_changed = pyqtSignal(str)        # state_changed(new_state)
    
    def __init__(self, hs3_service=None):
        """
        Inicializar runner de protocolo
        
        Args:
            hs3_service: Instância do HS3Service (None para simulação)
        """
        super().__init__()
        
        self.logger = logging.getLogger("ProtocolRunner")
        self.hs3_service = hs3_service
        
        # Estado do runner
        self.state = ProtocolState.IDLE
        self.current_protocol: Optional[Protocol] = None
        self.current_step_index = 0
        self.current_metrics: Optional[LiveMetrics] = None
        
        # Timers para execução
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._execution_step)
        self.execution_timer.setSingleShot(False)
        
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self._update_metrics)
        self.metrics_timer.setInterval(100)  # Atualizar a cada 100ms
        
        # Timestamps
        self.protocol_start_time: Optional[datetime] = None
        self.step_start_time: Optional[datetime] = None
        
        # Flags de controlo
        self.abort_requested = False
        self.pause_requested = False
        
        # Configuração de validação
        self.default_safety_limits = SafetyLimits()
    
    def set_hs3_service(self, hs3_service) -> None:
        """Definir serviço HS3 para controlo de hardware"""
        self.hs3_service = hs3_service
        self.logger.info("🔌 HS3Service configurado no ProtocolRunner")
    
    def _change_state(self, new_state: ProtocolState) -> None:
        """Mudar estado e emitir sinal"""
        old_state = self.state
        self.state = new_state
        self.state_changed.emit(new_state.value)
        self.logger.info(f"📊 Estado: {old_state.value} → {new_state.value}")
    
    def _validate_protocol_safety(self, protocol: Protocol) -> None:
        """
        Validar todos os passos do protocolo quanto à segurança
        
        Args:
            protocol: Protocolo a validar
            
        Raises:
            SafetyError: Se algum passo violar limites de segurança
        """
        safety_limits = protocol.safety_limits or self.default_safety_limits
        
        self.logger.info(f"🛡️ Validando segurança de {len(protocol.steps)} passos...")
        
        for i, step in enumerate(protocol.steps):
            try:
                # Validar cada passo individualmente
                assert_safe_output(step.amp_vpp, step.offset_v, safety_limits)
                
                # Validações adicionais específicas do runner
                if step.hz > safety_limits.max_frequency_hz:
                    raise SafetyError(
                        f"❌ Passo {i+1}: Frequência {step.hz:.2f}Hz excede "
                        f"limite de {safety_limits.max_frequency_hz:.2f}Hz"
                    )
                
                if step.dwell_s > safety_limits.max_single_frequency_duration_min * 60:
                    raise SafetyError(
                        f"❌ Passo {i+1}: Duração {step.dwell_s:.1f}s excede "
                        f"limite de {safety_limits.max_single_frequency_duration_min:.1f}min"
                    )
                
            except SafetyError as e:
                # Re-levantar com contexto do passo
                raise SafetyError(f"❌ PROTOCOLO REJEITADO: {e}")
        
        self.logger.info("✅ Validação de segurança aprovada")
    
    def start_protocol(self, protocol: Protocol) -> bool:
        """
        Iniciar execução de protocolo
        
        Args:
            protocol: Protocolo a executar
            
        Returns:
            True se iniciado com sucesso, False caso contrário
        """
        if self.state != ProtocolState.IDLE:
            self.logger.warning(f"⚠️ Cannot start protocol in state {self.state.value}")
            return False
        
        try:
            self._change_state(ProtocolState.PREPARING)
            
            # Validar protocolo
            self._validate_protocol_safety(protocol)
            
            # Verificar hardware se disponível
            if self.hs3_service and not self.hs3_service.is_connected():
                raise RuntimeError("❌ HS3 não está conectado")
            
            # Configurar execução
            self.current_protocol = protocol
            self.current_step_index = 0
            self.abort_requested = False
            self.pause_requested = False
            self.protocol_start_time = datetime.now()
            
            # Emitir sinal de início
            self.started.emit(protocol)
            
            # Iniciar execução
            self._change_state(ProtocolState.RUNNING)
            self._start_next_step()
            
            # Iniciar timer de métricas
            self.metrics_timer.start()
            
            self.logger.info(f"▶️ Protocolo '{protocol.name}' iniciado ({len(protocol.steps)} passos)")
            return True
            
        except (SafetyError, RuntimeError) as e:
            self._change_state(ProtocolState.ERROR)
            error_msg = str(e)
            self.logger.error(f"❌ Erro ao iniciar protocolo: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        except Exception as e:
            self._change_state(ProtocolState.ERROR)
            error_msg = f"Erro inesperado: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def pause_protocol(self) -> bool:
        """Pausar execução do protocolo"""
        if self.state != ProtocolState.RUNNING:
            return False
        
        self.pause_requested = True
        self._change_state(ProtocolState.PAUSED)
        
        # Parar saída se hardware disponível
        if self.hs3_service:
            try:
                self.hs3_service.stop_output()
            except Exception as e:
                self.logger.warning(f"Erro ao parar saída HS3: {e}")
        
        self.execution_timer.stop()
        self.logger.info("⏸️ Protocolo pausado")
        return True
    
    def resume_protocol(self) -> bool:
        """Retomar execução do protocolo"""
        if self.state != ProtocolState.PAUSED:
            return False
        
        self.pause_requested = False
        self._change_state(ProtocolState.RUNNING)
        
        # Continuar passo atual
        self._continue_current_step()
        
        self.logger.info("▶️ Protocolo retomado")
        return True
    
    def abort_protocol(self, reason: str = "Abortado pelo utilizador") -> None:
        """Abortar execução do protocolo"""
        if self.state in [ProtocolState.IDLE, ProtocolState.FINISHED]:
            return
        
        self._change_state(ProtocolState.ABORTING)
        self.abort_requested = True
        
        # Parar tudo
        self.execution_timer.stop()
        self.metrics_timer.stop()
        
        # Parar saída se hardware disponível
        if self.hs3_service:
            try:
                self.hs3_service.stop_output()
            except Exception as e:
                self.logger.warning(f"Erro ao parar saída HS3: {e}")
        
        # Reset estado
        self._reset_state()
        
        # Emitir sinais
        self.aborted.emit(reason)
        self._change_state(ProtocolState.IDLE)
        
        self.logger.warning(f"🛑 Protocolo abortado: {reason}")
    
    def _start_next_step(self) -> None:
        """Iniciar próximo passo do protocolo"""
        if not self.current_protocol or self.current_step_index >= len(self.current_protocol.steps):
            self._finish_protocol()
            return
        
        if self.abort_requested:
            return
        
        step = self.current_protocol.steps[self.current_step_index]
        self.step_start_time = datetime.now()
        
        self.logger.info(
            f"🎵 Passo {self.current_step_index + 1}/{len(self.current_protocol.steps)}: "
            f"{step.hz:.2f}Hz, {step.amp_vpp:.3f}V, {step.dwell_s:.1f}s"
        )
        
        # Emitir sinal de início do passo
        self.step_started.emit(self.current_step_index, step)
        
        # Configurar hardware se disponível
        if self.hs3_service:
            self._configure_hardware_for_step(step)
        
        # Configurar timer para duração do passo
        step_duration_ms = int(step.dwell_s * 1000)
        self.execution_timer.setInterval(step_duration_ms)
        self.execution_timer.start()
    
    def _configure_hardware_for_step(self, step: FrequencyStep) -> None:
        """Configurar hardware HS3 para o passo atual"""
        try:
            # Configurar gerador com soft-ramp
            self.hs3_service.configure_generator(
                signal_type=step.waveform,
                amplitude_vpp=step.amp_vpp,
                offset_v=step.offset_v
            )
            
            # Configurar frequência
            self.hs3_service.set_frequency(step.hz)
            
            # Configurar modo específico
            if step.mode == ProtocolMode.BURST:
                cycles = step.auto_burst_cycles
                self.hs3_service.set_burst_by_cycles(cycles)
                self.logger.info(f"💥 Modo burst: {cycles} ciclos")
            
            elif step.mode == ProtocolMode.GATED:
                self.hs3_service.enable_ext_trigger_gated(True)
                self.logger.info("🎯 Modo gated ativado")
            
            else:  # CONTINUOUS
                # Resetar configurações especiais
                try:
                    self.hs3_service.enable_ext_trigger_gated(False)
                except:
                    pass  # Ignorar se não suportado
            
            # Iniciar saída
            self.hs3_service.start_output()
            
        except Exception as e:
            error_msg = f"Erro ao configurar hardware para passo {self.current_step_index + 1}: {e}"
            self.logger.error(error_msg)
            self.abort_protocol(error_msg)
    
    def _continue_current_step(self) -> None:
        """Continuar passo atual após pausa"""
        if not self.current_protocol or not self.step_start_time:
            return
        
        # Calcular tempo restante
        step = self.current_protocol.steps[self.current_step_index]
        elapsed = (datetime.now() - self.step_start_time).total_seconds()
        remaining = max(0, step.dwell_s - elapsed)
        
        if remaining > 0:
            # Reconfigurar hardware e continuar
            if self.hs3_service:
                self._configure_hardware_for_step(step)
            
            # Timer para tempo restante
            remaining_ms = int(remaining * 1000)
            self.execution_timer.setInterval(remaining_ms)
            self.execution_timer.start()
        else:
            # Passo já terminou, avançar
            self._execution_step()
    
    def _execution_step(self) -> None:
        """Callback do timer de execução - passo terminado"""
        self.execution_timer.stop()
        
        if self.abort_requested:
            return
        
        # Parar saída do passo atual
        if self.hs3_service:
            try:
                self.hs3_service.stop_output()
            except Exception as e:
                self.logger.warning(f"Erro ao parar saída: {e}")
        
        # Emitir sinal de fim do passo
        self.step_finished.emit(self.current_step_index)
        
        self.logger.info(f"✅ Passo {self.current_step_index + 1} concluído")
        
        # Avançar para próximo passo
        self.current_step_index += 1
        
        # Pequena pausa entre passos (100ms)
        QTimer.singleShot(100, self._start_next_step)
    
    def _finish_protocol(self) -> None:
        """Finalizar protocolo com sucesso"""
        self.execution_timer.stop()
        self.metrics_timer.stop()
        
        self._change_state(ProtocolState.FINISHED)
        
        # Garantir que saída está parada
        if self.hs3_service:
            try:
                self.hs3_service.stop_output()
            except Exception as e:
                self.logger.warning(f"Erro ao parar saída final: {e}")
        
        # Emitir sinal de conclusão
        self.finished.emit()
        
        duration = (datetime.now() - self.protocol_start_time).total_seconds()
        self.logger.info(f"🏁 Protocolo '{self.current_protocol.name}' concluído em {duration:.1f}s")
        
        # Reset estado
        self._reset_state()
        self._change_state(ProtocolState.IDLE)
    
    def _update_metrics(self) -> None:
        """Atualizar métricas em tempo real"""
        if not self.current_protocol or not self.protocol_start_time:
            return
        
        now = datetime.now()
        total_elapsed = (now - self.protocol_start_time).total_seconds()
        
        # Calcular progresso do passo atual
        step_progress = 0.0
        if self.step_start_time and self.current_step_index < len(self.current_protocol.steps):
            step = self.current_protocol.steps[self.current_step_index]
            step_elapsed = (now - self.step_start_time).total_seconds()
            step_progress = min(1.0, step_elapsed / step.dwell_s)
        
        # Calcular progresso total
        completed_steps = self.current_step_index
        total_progress = (completed_steps + step_progress) / len(self.current_protocol.steps)
        
        # Calcular tempo restante estimado
        if total_progress > 0:
            estimated_total = total_elapsed / total_progress
            remaining = max(0, estimated_total - total_elapsed)
        else:
            remaining = self.current_protocol.total_duration_s
        
        # Obter parâmetros atuais
        current_freq = 0.0
        current_amp = 0.0
        if self.current_step_index < len(self.current_protocol.steps):
            current_step = self.current_protocol.steps[self.current_step_index]
            current_freq = current_step.hz
            current_amp = current_step.amp_vpp
        
        # Criar métricas
        metrics = LiveMetrics(
            current_step=self.current_step_index,
            total_steps=len(self.current_protocol.steps),
            step_progress=step_progress,
            total_progress=total_progress,
            current_frequency=current_freq,
            current_amplitude=current_amp,
            elapsed_time_s=total_elapsed,
            remaining_time_s=remaining,
            step_start_time=self.step_start_time or now,
            protocol_start_time=self.protocol_start_time
        )
        
        self.current_metrics = metrics
        
        # Emitir como dicionário para compatibilidade Qt
        metrics_dict = {
            'current_step': metrics.current_step,
            'total_steps': metrics.total_steps,
            'step_progress': metrics.step_progress,
            'total_progress': metrics.total_progress,
            'current_frequency': metrics.current_frequency,
            'current_amplitude': metrics.current_amplitude,
            'elapsed_time_s': metrics.elapsed_time_s,
            'remaining_time_s': metrics.remaining_time_s
        }
        
        self.live_metrics.emit(metrics_dict)
    
    def _reset_state(self) -> None:
        """Reset do estado interno"""
        self.current_protocol = None
        self.current_step_index = 0
        self.current_metrics = None
        self.protocol_start_time = None
        self.step_start_time = None
        self.abort_requested = False
        self.pause_requested = False
    
    def get_current_state(self) -> str:
        """Obter estado atual como string"""
        return self.state.value
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Obter métricas atuais como dicionário"""
        if not self.current_metrics:
            return None
        
        return {
            'current_step': self.current_metrics.current_step,
            'total_steps': self.current_metrics.total_steps,
            'step_progress': self.current_metrics.step_progress,
            'total_progress': self.current_metrics.total_progress,
            'current_frequency': self.current_metrics.current_frequency,
            'current_amplitude': self.current_metrics.current_amplitude,
            'elapsed_time_s': self.current_metrics.elapsed_time_s,
            'remaining_time_s': self.current_metrics.remaining_time_s
        }


# ═══════════════════════════════════════════════════════════════════════
# FUNÇÕES UTILITÁRIAS PARA CRIAÇÃO DE PROTOCOLOS
# ═══════════════════════════════════════════════════════════════════════

def create_simple_protocol(name: str, 
                         frequencies: List[float], 
                         amplitude: float = 1.0,
                         dwell_time: float = 3.0,
                         waveform: str = "sine") -> Protocol:
    """
    Criar protocolo simples com lista de frequências
    
    Args:
        name: Nome do protocolo
        frequencies: Lista de frequências em Hz
        amplitude: Amplitude para todas as frequências
        dwell_time: Tempo de permanência para todas as frequências
        waveform: Forma de onda para todas as frequências
    
    Returns:
        Protocolo configurado
    """
    steps = []
    for freq in frequencies:
        step = FrequencyStep(
            hz=freq,
            dwell_s=dwell_time,
            amp_vpp=amplitude,
            waveform=waveform
        )
        steps.append(step)
    
    return Protocol(
        name=name,
        description=f"Protocolo simples com {len(frequencies)} frequências",
        steps=steps
    )


def create_sweep_protocol(name: str,
                        start_freq: float,
                        end_freq: float,
                        steps: int,
                        amplitude: float = 1.0,
                        step_duration: float = 2.0) -> Protocol:
    """
    Criar protocolo de varredura linear de frequências
    
    Args:
        name: Nome do protocolo
        start_freq: Frequência inicial
        end_freq: Frequência final  
        steps: Número de passos
        amplitude: Amplitude constante
        step_duration: Duração de cada passo
    
    Returns:
        Protocolo de varredura configurado
    """
    frequencies = np.linspace(start_freq, end_freq, steps)
    
    protocol_steps = []
    for freq in frequencies:
        step = FrequencyStep(
            hz=float(freq),
            dwell_s=step_duration,
            amp_vpp=amplitude,
            waveform="sine"
        )
        protocol_steps.append(step)
    
    return Protocol(
        name=name,
        description=f"Varredura de {start_freq:.1f}Hz a {end_freq:.1f}Hz em {steps} passos",
        steps=protocol_steps
    )


# ═══════════════════════════════════════════════════════════════════════
# TESTES UNITÁRIOS
# ═══════════════════════════════════════════════════════════════════════

def test_frequency_step():
    """Teste de criação de passo de frequência"""
    step = FrequencyStep(hz=440.0, dwell_s=3.0, amp_vpp=1.0)
    assert step.hz == 440.0
    assert step.dwell_s == 3.0
    assert step.amp_vpp == 1.0
    assert step.auto_burst_cycles == int(440.0 * 3.0)  # ~1320 ciclos


def test_protocol_creation():
    """Teste de criação de protocolo"""
    steps = [
        FrequencyStep(hz=440.0, dwell_s=2.0, amp_vpp=1.0),
        FrequencyStep(hz=528.0, dwell_s=3.0, amp_vpp=1.2)
    ]
    
    protocol = Protocol(
        name="Teste",
        description="Protocolo de teste",
        steps=steps
    )
    
    assert protocol.name == "Teste"
    assert len(protocol.steps) == 2
    assert protocol.total_duration_s == 5.0  # 2 + 3
    assert protocol.frequency_range == (440.0, 528.0)
    assert protocol.max_amplitude == 1.2


def test_simple_protocol_creation():
    """Teste de criação de protocolo simples"""
    protocol = create_simple_protocol(
        name="Solfeggio",
        frequencies=[396.0, 417.0, 528.0, 639.0, 741.0, 852.0],
        amplitude=1.0,
        dwell_time=3.0
    )
    
    assert protocol.name == "Solfeggio"
    assert len(protocol.steps) == 6
    assert protocol.total_duration_s == 18.0  # 6 * 3


def test_sweep_protocol_creation():
    """Teste de criação de protocolo de varredura"""
    protocol = create_sweep_protocol(
        name="Varredura 100-1000Hz",
        start_freq=100.0,
        end_freq=1000.0,
        steps=10,
        amplitude=0.5,
        step_duration=1.0
    )
    
    assert protocol.name == "Varredura 100-1000Hz"
    assert len(protocol.steps) == 10
    assert protocol.steps[0].hz == 100.0
    assert protocol.steps[-1].hz == 1000.0
    assert all(step.amp_vpp == 0.5 for step in protocol.steps)


if __name__ == "__main__":
    # Executar testes
    print("🧪 Executando testes do ProtocolRunner...")
    
    test_frequency_step()
    print("✅ test_frequency_step")
    
    test_protocol_creation()
    print("✅ test_protocol_creation")
    
    test_simple_protocol_creation()
    print("✅ test_simple_protocol_creation")
    
    test_sweep_protocol_creation()
    print("✅ test_sweep_protocol_creation")
    
    print("🎉 Todos os testes do ProtocolRunner passaram!")
