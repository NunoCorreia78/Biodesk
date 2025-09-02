"""
Gerador de Frequências para Terapia Quântica
═══════════════════════════════════════════════════════════════════════

Módulo responsável por gerar frequências terapêuticas usando o HS3.
Inclui validações de segurança e monitorização em tempo real.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QApplication

from hs3_hardware import hs3_hardware, HS3Response
from hs3_config import hs3_config

@dataclass
class FrequencyStep:
    """Passo individual de frequência"""
    frequency: float
    amplitude: float
    offset: float
    duration_seconds: int
    description: str = ""

@dataclass
class GenerationSession:
    """Sessão de geração completa"""
    session_id: str
    patient_name: str
    protocol_name: str
    steps: List[FrequencyStep]
    total_duration: int  # segundos
    created_at: datetime
    notes: str = ""

class FrequencyGenerator(QObject):
    """
    Gerador de frequências com validações de segurança
    Controla o HS3 para executar protocolos terapêuticos
    """
    
    # Sinais PyQt6
    session_started = pyqtSignal(str)      # ID da sessão
    session_completed = pyqtSignal(str)    # ID da sessão  
    session_paused = pyqtSignal(str)       # ID da sessão
    session_error = pyqtSignal(str, str)   # ID da sessão, erro
    
    step_started = pyqtSignal(int, dict)   # Número do passo, dados
    step_completed = pyqtSignal(int)       # Número do passo
    
    progress_updated = pyqtSignal(int)     # Progresso 0-100%
    status_updated = pyqtSignal(str)       # Estado atual
    
    # Dados em tempo real
    realtime_data = pyqtSignal(dict)       # Dados de monitorização
    
    def __init__(self):
        super().__init__()
        self.current_session: Optional[GenerationSession] = None
        self.current_step = 0
        self.is_running = False
        self.is_paused = False
        self.start_time: Optional[datetime] = None
        
        # Timer para controlo de passos
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self._next_step)
        self.step_timer.setSingleShot(True)
        
        # Timer para monitorização em tempo real
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._collect_realtime_data)
        self.monitor_timer.setInterval(100)  # 10Hz
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
    
    def start_session(self, session: GenerationSession) -> HS3Response:
        """
        Inicia uma sessão de geração de frequências
        """
        try:
            # Verificar se HS3 está conectado
            if not hs3_hardware.is_connected():
                return HS3Response(False, "HS3 não conectado. Conecte o dispositivo primeiro.")
            
            # Verificar se já existe sessão ativa
            if self.is_running:
                return HS3Response(False, "Já existe uma sessão ativa. Pare a sessão atual primeiro.")
            
            # Validar sessão
            validation_result = self._validate_session(session)
            if not validation_result.success:
                return validation_result
            
            # Configurar sessão
            self.current_session = session
            self.current_step = 0
            self.is_running = True
            self.is_paused = False
            self.start_time = datetime.now()
            
            # Iniciar monitorização
            self.monitor_timer.start()
            
            # Emitir sinal de início
            self.session_started.emit(session.session_id)
            self.status_updated.emit("Sessão iniciada")
            
            # Iniciar primeiro passo
            return self._execute_current_step()
            
        except Exception as e:
            error_msg = f"Erro ao iniciar sessão: {e}"
            self.logger.error(error_msg)
            return HS3Response(False, error_msg)
    
    def pause_session(self) -> HS3Response:
        """Pausa a sessão atual"""
        if not self.is_running:
            return HS3Response(False, "Nenhuma sessão ativa")
        
        try:
            # Parar geração no HS3
            hs3_hardware.stop_generation()
            
            # Parar timers
            self.step_timer.stop()
            self.monitor_timer.stop()
            
            self.is_paused = True
            self.session_paused.emit(self.current_session.session_id)
            self.status_updated.emit("Sessão pausada")
            
            return HS3Response(True, "Sessão pausada")
            
        except Exception as e:
            error_msg = f"Erro ao pausar sessão: {e}"
            self.logger.error(error_msg)
            return HS3Response(False, error_msg)
    
    def resume_session(self) -> HS3Response:
        """Retoma a sessão pausada"""
        if not self.is_running or not self.is_paused:
            return HS3Response(False, "Nenhuma sessão pausada")
        
        try:
            self.is_paused = False
            self.monitor_timer.start()
            self.status_updated.emit("Sessão retomada")
            
            # Retomar passo atual
            return self._execute_current_step()
            
        except Exception as e:
            error_msg = f"Erro ao retomar sessão: {e}"
            self.logger.error(error_msg)
            return HS3Response(False, error_msg)
    
    def stop_session(self) -> HS3Response:
        """Para a sessão atual"""
        try:
            # Parar geração no HS3
            hs3_hardware.stop_generation()
            
            # Parar timers
            self.step_timer.stop()
            self.monitor_timer.stop()
            
            # Resetar estado
            session_id = self.current_session.session_id if self.current_session else "unknown"
            self.current_session = None
            self.current_step = 0
            self.is_running = False
            self.is_paused = False
            self.start_time = None
            
            self.session_completed.emit(session_id)
            self.status_updated.emit("Sessão parada")
            
            return HS3Response(True, "Sessão parada")
            
        except Exception as e:
            error_msg = f"Erro ao parar sessão: {e}"
            self.logger.error(error_msg)
            return HS3Response(False, error_msg)
    
    def emergency_stop(self) -> HS3Response:
        """Paragem de emergência"""
        try:
            # Parar imediatamente
            hs3_hardware.stop_generation()
            
            # Parar todos os timers
            self.step_timer.stop()
            self.monitor_timer.stop()
            
            # Resetar completamente
            self.current_session = None
            self.current_step = 0
            self.is_running = False
            self.is_paused = False
            self.start_time = None
            
            self.status_updated.emit("⛔ PARAGEM DE EMERGÊNCIA")
            self.session_error.emit("emergency", "Paragem de emergência ativada")
            
            return HS3Response(True, "Paragem de emergência executada")
            
        except Exception as e:
            error_msg = f"Erro na paragem de emergência: {e}"
            self.logger.critical(error_msg)
            return HS3Response(False, error_msg)
    
    def get_session_status(self) -> Dict:
        """Obtém estado atual da sessão"""
        if not self.current_session:
            return {
                "active": False,
                "status": "Nenhuma sessão ativa"
            }
        
        # Calcular progresso
        total_steps = len(self.current_session.steps)
        progress = int((self.current_step / total_steps) * 100) if total_steps > 0 else 0
        
        # Calcular tempo decorrido
        elapsed = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        return {
            "active": True,
            "session_id": self.current_session.session_id,
            "patient": self.current_session.patient_name,
            "protocol": self.current_session.protocol_name,
            "current_step": self.current_step,
            "total_steps": total_steps,
            "progress": progress,
            "running": self.is_running,
            "paused": self.is_paused,
            "elapsed_time": str(elapsed).split('.')[0],  # Remover microssegundos
            "current_frequency": self.current_session.steps[self.current_step].frequency if self.current_step < total_steps else 0
        }
    
    def create_simple_protocol(self, frequencies: List[float], 
                             amplitude: float = 2.0, offset: float = 0.0,
                             step_duration: int = 60) -> List[FrequencyStep]:
        """
        Cria protocolo simples com lista de frequências
        """
        steps = []
        
        for i, freq in enumerate(frequencies):
            # Validar parâmetros
            safe_params = hs3_config.get_safe_parameters(amplitude, offset, freq, step_duration)
            
            step = FrequencyStep(
                frequency=safe_params['frequency'],
                amplitude=safe_params['amplitude'],
                offset=safe_params['offset'],
                duration_seconds=safe_params['duration'] * 60,  # Converter para segundos
                description=f"Frequência {freq}Hz - Passo {i+1}"
            )
            steps.append(step)
        
        return steps
    
    def create_sweep_protocol(self, start_freq: float, end_freq: float,
                            steps: int = 10, amplitude: float = 2.0,
                            step_duration: int = 30) -> List[FrequencyStep]:
        """
        Cria protocolo de varredura de frequências
        """
        protocol_steps = []
        
        # Calcular passo de frequência
        freq_step = (end_freq - start_freq) / (steps - 1)
        
        for i in range(steps):
            frequency = start_freq + (i * freq_step)
            
            # Validar parâmetros
            safe_params = hs3_config.get_safe_parameters(amplitude, 0.0, frequency, step_duration)
            
            step = FrequencyStep(
                frequency=safe_params['frequency'],
                amplitude=safe_params['amplitude'],
                offset=safe_params['offset'],
                duration_seconds=safe_params['duration'] * 60,
                description=f"Varredura {frequency:.1f}Hz - Passo {i+1}/{steps}"
            )
            protocol_steps.append(step)
        
        return protocol_steps
    
    # Métodos privados
    def _validate_session(self, session: GenerationSession) -> HS3Response:
        """Valida sessão antes de iniciar"""
        
        # Verificar se tem passos
        if not session.steps:
            return HS3Response(False, "Sessão sem passos definidos")
        
        # Validar cada passo
        for i, step in enumerate(session.steps):
            # Validar frequência
            valid, msg = hs3_config.validate_frequency(step.frequency)
            if not valid:
                return HS3Response(False, f"Passo {i+1}: {msg}")
            
            # Validar amplitude
            valid, msg = hs3_config.validate_amplitude(step.amplitude)
            if not valid:
                return HS3Response(False, f"Passo {i+1}: {msg}")
            
            # Validar offset
            valid, msg = hs3_config.validate_offset(step.offset)
            if not valid:
                return HS3Response(False, f"Passo {i+1}: {msg}")
            
            # Validar duração (converter segundos para minutos para validação)
            duration_minutes = step.duration_seconds // 60
            if duration_minutes < 1:
                duration_minutes = 1
            
            valid, msg = hs3_config.validate_duration(duration_minutes)
            if not valid:
                return HS3Response(False, f"Passo {i+1}: {msg}")
        
        return HS3Response(True, "Sessão válida")
    
    def _execute_current_step(self) -> HS3Response:
        """Executa o passo atual"""
        if not self.current_session or self.current_step >= len(self.current_session.steps):
            return self._complete_session()
        
        try:
            step = self.current_session.steps[self.current_step]
            
            # Configurar HS3
            freq_result = hs3_hardware.set_frequency(step.frequency)
            if not freq_result.success:
                return freq_result
            
            ampl_result = hs3_hardware.set_amplitude(step.amplitude)
            if not ampl_result.success:
                return ampl_result
            
            offs_result = hs3_hardware.set_offset(step.offset)
            if not offs_result.success:
                return offs_result
            
            # Iniciar geração
            start_result = hs3_hardware.start_generation()
            if not start_result.success:
                return start_result
            
            # Emitir sinal de início do passo
            step_data = {
                "frequency": step.frequency,
                "amplitude": step.amplitude,
                "offset": step.offset,
                "duration": step.duration_seconds,
                "description": step.description
            }
            self.step_started.emit(self.current_step, step_data)
            
            # Programar próximo passo
            self.step_timer.start(step.duration_seconds * 1000)  # Converter para ms
            
            self.status_updated.emit(f"Executando: {step.description}")
            
            return HS3Response(True, f"Passo {self.current_step + 1} iniciado")
            
        except Exception as e:
            error_msg = f"Erro ao executar passo: {e}"
            self.logger.error(error_msg)
            self.session_error.emit(self.current_session.session_id, error_msg)
            return HS3Response(False, error_msg)
    
    def _next_step(self):
        """Avança para o próximo passo"""
        if not self.is_running or self.is_paused:
            return
        
        # Parar geração atual
        hs3_hardware.stop_generation()
        
        # Emitir sinal de conclusão do passo
        self.step_completed.emit(self.current_step)
        
        # Avançar
        self.current_step += 1
        
        # Atualizar progresso
        if self.current_session:
            total_steps = len(self.current_session.steps)
            progress = int((self.current_step / total_steps) * 100)
            self.progress_updated.emit(progress)
        
        # Executar próximo passo ou completar
        self._execute_current_step()
    
    def _complete_session(self) -> HS3Response:
        """Completa a sessão"""
        try:
            # Parar geração
            hs3_hardware.stop_generation()
            
            # Parar timers
            self.step_timer.stop()
            self.monitor_timer.stop()
            
            session_id = self.current_session.session_id if self.current_session else "unknown"
            
            # Resetar estado
            self.current_session = None
            self.current_step = 0
            self.is_running = False
            self.is_paused = False
            self.start_time = None
            
            # Emitir sinais
            self.progress_updated.emit(100)
            self.session_completed.emit(session_id)
            self.status_updated.emit("✅ Sessão concluída com sucesso")
            
            return HS3Response(True, "Sessão concluída")
            
        except Exception as e:
            error_msg = f"Erro ao completar sessão: {e}"
            self.logger.error(error_msg)
            return HS3Response(False, error_msg)
    
    def _collect_realtime_data(self):
        """Coleta dados em tempo real"""
        try:
            if not self.is_running or self.is_paused:
                return
            
            # Obter estado do HS3
            hs3_status = hs3_hardware.get_status()
            
            # Dados de monitorização
            data = {
                "timestamp": datetime.now().isoformat(),
                "hs3_status": hs3_status,
                "session_status": self.get_session_status(),
                "current_step_data": None
            }
            
            # Adicionar dados do passo atual
            if self.current_session and self.current_step < len(self.current_session.steps):
                current_step = self.current_session.steps[self.current_step]
                data["current_step_data"] = {
                    "frequency": current_step.frequency,
                    "amplitude": current_step.amplitude,
                    "offset": current_step.offset,
                    "description": current_step.description
                }
            
            # Emitir dados
            self.realtime_data.emit(data)
            
        except Exception as e:
            self.logger.warning(f"Erro ao coletar dados em tempo real: {e}")

# Instância global do gerador
frequency_generator = FrequencyGenerator()
