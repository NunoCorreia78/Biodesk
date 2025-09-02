"""
Sistema de Segurança para Terapia Quântica
═══════════════════════════════════════════════════════════════════════

Sistema de segurança que monitoriza todas as operações da terapia quântica,
garantindo que nunca são ultrapassados os limites de segurança estabelecidos.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from hs3_config import hs3_config, HS3SafetyLimits
from hs3_hardware import hs3_hardware

class SafetyLevel(Enum):
    """Níveis de segurança"""
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"

class SafetyEventType(Enum):
    """Tipos de eventos de segurança"""
    PARAMETER_LIMIT = "parameter_limit"
    HARDWARE_ERROR = "hardware_error"
    CONNECTION_LOST = "connection_lost"
    USER_INTERVENTION = "user_intervention"
    SYSTEM_ERROR = "system_error"
    EMERGENCY_STOP = "emergency_stop"

@dataclass
class SafetyEvent:
    """Evento de segurança"""
    timestamp: datetime
    event_type: SafetyEventType
    level: SafetyLevel
    message: str
    parameters: Optional[Dict] = None
    action_taken: str = ""

@dataclass
class SafetyRule:
    """Regra de segurança"""
    rule_id: str
    name: str
    description: str
    check_function: Callable
    level: SafetyLevel
    enabled: bool = True

class SafetyManager(QObject):
    """
    Gestor de segurança que monitoriza continuamente o sistema
    e garante operação dentro de limites seguros
    """
    
    # Sinais
    safety_event = pyqtSignal(dict)           # Evento de segurança
    safety_violation = pyqtSignal(str, str)   # Violação (nível, mensagem)
    emergency_stop_triggered = pyqtSignal()   # Paragem de emergência
    safety_status_changed = pyqtSignal(str)   # Mudança de estado
    
    def __init__(self):
        super().__init__()
        self.is_monitoring = False
        self.current_safety_level = SafetyLevel.SAFE
        self.safety_events: List[SafetyEvent] = []
        self.safety_rules: List[SafetyRule] = []
        self.limits = HS3SafetyLimits()
        
        # Estado atual do sistema
        self.current_parameters = {
            "frequency": 0.0,
            "amplitude": 0.0,
            "offset": 0.0,
            "generating": False
        }
        
        # Timers de monitorização
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._perform_safety_checks)
        self.monitor_timer.setInterval(1000)  # Verificar a cada segundo
        
        # Timer para limpeza de eventos antigos
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_old_events)
        self.cleanup_timer.setInterval(300000)  # Limpar a cada 5 minutos
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar regras de segurança
        self._init_safety_rules()
    
    def start_monitoring(self) -> bool:
        """Inicia monitorização de segurança"""
        try:
            self.is_monitoring = True
            self.current_safety_level = SafetyLevel.SAFE
            
            # Verificação inicial
            initial_check = self.perform_comprehensive_safety_check()
            if not initial_check[0]:
                self.is_monitoring = False
                return False
            
            # Iniciar timers
            self.monitor_timer.start()
            self.cleanup_timer.start()
            
            # Registar evento
            self._log_safety_event(
                SafetyEventType.USER_INTERVENTION,
                SafetyLevel.SAFE,
                "Sistema de segurança iniciado"
            )
            
            self.safety_status_changed.emit("monitoring_started")
            self.logger.info("🛡️ Sistema de segurança ativado")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar monitorização de segurança: {e}")
            return False
    
    def stop_monitoring(self):
        """Para monitorização de segurança"""
        try:
            self.monitor_timer.stop()
            self.cleanup_timer.stop()
            self.is_monitoring = False
            
            # Registar evento
            self._log_safety_event(
                SafetyEventType.USER_INTERVENTION,
                SafetyLevel.SAFE,
                "Sistema de segurança desativado"
            )
            
            self.safety_status_changed.emit("monitoring_stopped")
            self.logger.info("🛡️ Sistema de segurança desativado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar monitorização: {e}")
    
    def validate_parameters_before_start(self, frequency: float, amplitude: float, 
                                       offset: float) -> Tuple[bool, str]:
        """
        Valida parâmetros antes de iniciar geração
        Esta é a última linha de defesa
        """
        try:
            # Verificar cada parâmetro individualmente
            valid, msg = hs3_config.validate_frequency(frequency)
            if not valid:
                self._log_safety_event(
                    SafetyEventType.PARAMETER_LIMIT,
                    SafetyLevel.DANGER,
                    f"Frequência rejeitada: {msg}",
                    {"frequency": frequency}
                )
                return False, f"❌ FREQUÊNCIA REJEITADA: {msg}"
            
            valid, msg = hs3_config.validate_amplitude(amplitude)
            if not valid:
                self._log_safety_event(
                    SafetyEventType.PARAMETER_LIMIT,
                    SafetyLevel.DANGER,
                    f"Amplitude rejeitada: {msg}",
                    {"amplitude": amplitude}
                )
                return False, f"❌ AMPLITUDE REJEITADA: {msg}"
            
            valid, msg = hs3_config.validate_offset(offset)
            if not valid:
                self._log_safety_event(
                    SafetyEventType.PARAMETER_LIMIT,
                    SafetyLevel.DANGER,
                    f"Offset rejeitado: {msg}",
                    {"offset": offset}
                )
                return False, f"❌ OFFSET REJEITADO: {msg}"
            
            # Verificações adicionais de segurança
            
            # 1. Combinação amplitude + offset não pode exceder limites absolutos
            max_voltage = amplitude + abs(offset)
            if max_voltage > self.limits.MAX_AMPLITUDE:
                error_msg = f"Tensão total ({max_voltage:.1f}V) excede limite máximo ({self.limits.MAX_AMPLITUDE}V)"
                self._log_safety_event(
                    SafetyEventType.PARAMETER_LIMIT,
                    SafetyLevel.CRITICAL,
                    error_msg,
                    {"amplitude": amplitude, "offset": offset, "total_voltage": max_voltage}
                )
                return False, f"❌ TENSÃO TOTAL REJEITADA: {error_msg}"
            
            # 2. Verificar se HS3 está conectado e funcional
            if not hs3_hardware.is_connected():
                error_msg = "HS3 não conectado - não é possível garantir segurança"
                self._log_safety_event(
                    SafetyEventType.HARDWARE_ERROR,
                    SafetyLevel.CRITICAL,
                    error_msg
                )
                return False, f"❌ HARDWARE: {error_msg}"
            
            # 3. Verificar saúde geral do sistema
            comprehensive_check = self.perform_comprehensive_safety_check()
            if not comprehensive_check[0]:
                return False, f"❌ SISTEMA: {comprehensive_check[1]}"
            
            # Tudo OK - registar aprovação
            self._log_safety_event(
                SafetyEventType.PARAMETER_LIMIT,
                SafetyLevel.SAFE,
                f"Parâmetros aprovados: {frequency}Hz, {amplitude}V, {offset}V",
                {"frequency": frequency, "amplitude": amplitude, "offset": offset}
            )
            
            return True, "✅ Parâmetros aprovados pelo sistema de segurança"
            
        except Exception as e:
            error_msg = f"Erro na validação de segurança: {e}"
            self._log_safety_event(
                SafetyEventType.SYSTEM_ERROR,
                SafetyLevel.CRITICAL,
                error_msg
            )
            return False, f"❌ ERRO DE VALIDAÇÃO: {error_msg}"
    
    def perform_comprehensive_safety_check(self) -> Tuple[bool, str]:
        """
        Executa verificação completa de segurança
        Usado antes de iniciar operações críticas
        """
        try:
            issues = []
            
            # 1. Verificar conectividade do hardware
            if not hs3_hardware.is_connected():
                issues.append("HS3 não conectado")
            
            # 2. Verificar estado do HS3
            try:
                hs3_status = hs3_hardware.get_status()
                if not hs3_status.get("connected", False):
                    issues.append("HS3 em estado inválido")
            except Exception:
                issues.append("Impossível verificar estado do HS3")
            
            # 3. Executar todas as regras de segurança
            for rule in self.safety_rules:
                if rule.enabled:
                    try:
                        rule_result = rule.check_function()
                        if not rule_result:
                            issues.append(f"Falha na regra: {rule.name}")
                    except Exception as e:
                        issues.append(f"Erro na regra {rule.name}: {e}")
            
            # 4. Verificar limites de configuração
            config_check = self._check_configuration_limits()
            if not config_check[0]:
                issues.append(config_check[1])
            
            # Avaliar resultado
            if issues:
                error_msg = "Falhas de segurança: " + "; ".join(issues)
                self._log_safety_event(
                    SafetyEventType.SYSTEM_ERROR,
                    SafetyLevel.DANGER,
                    error_msg
                )
                return False, error_msg
            else:
                return True, "Sistema seguro"
                
        except Exception as e:
            error_msg = f"Erro na verificação de segurança: {e}"
            self._log_safety_event(
                SafetyEventType.SYSTEM_ERROR,
                SafetyLevel.CRITICAL,
                error_msg
            )
            return False, error_msg
    
    def emergency_shutdown(self, reason: str = "Paragem de emergência manual") -> bool:
        """
        Paragem de emergência imediata
        Para tudo e coloca sistema em estado seguro
        """
        try:
            self.logger.critical(f"🚨 PARAGEM DE EMERGÊNCIA: {reason}")
            
            # 1. Parar geração imediatamente
            if hs3_hardware.is_connected():
                hs3_hardware.stop_generation()
                hs3_hardware.disconnect()
            
            # 2. Parar monitorização
            self.stop_monitoring()
            
            # 3. Registar evento crítico
            self._log_safety_event(
                SafetyEventType.EMERGENCY_STOP,
                SafetyLevel.CRITICAL,
                reason
            )
            
            # 4. Emitir sinais
            self.emergency_stop_triggered.emit()
            self.safety_status_changed.emit("emergency_stop")
            
            # 5. Atualizar estado
            self.current_safety_level = SafetyLevel.CRITICAL
            
            return True
            
        except Exception as e:
            self.logger.critical(f"ERRO NA PARAGEM DE EMERGÊNCIA: {e}")
            return False
    
    def get_safety_status(self) -> Dict:
        """Obtém estado atual da segurança"""
        recent_events = [
            {
                "timestamp": event.timestamp.isoformat(),
                "type": event.event_type.value,
                "level": event.level.value,
                "message": event.message
            }
            for event in self.safety_events[-10:]  # Últimos 10 eventos
        ]
        
        return {
            "monitoring": self.is_monitoring,
            "safety_level": self.current_safety_level.value,
            "total_events": len(self.safety_events),
            "recent_events": recent_events,
            "current_parameters": self.current_parameters.copy(),
            "rules_count": len([r for r in self.safety_rules if r.enabled])
        }
    
    def add_custom_safety_rule(self, rule: SafetyRule) -> bool:
        """Adiciona regra personalizada de segurança"""
        try:
            # Verificar se regra já existe
            existing = [r for r in self.safety_rules if r.rule_id == rule.rule_id]
            if existing:
                return False
            
            self.safety_rules.append(rule)
            
            self._log_safety_event(
                SafetyEventType.USER_INTERVENTION,
                SafetyLevel.SAFE,
                f"Regra de segurança adicionada: {rule.name}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar regra: {e}")
            return False
    
    def disable_safety_rule(self, rule_id: str) -> bool:
        """Desativa regra de segurança (USE COM CUIDADO!)"""
        try:
            rule = next((r for r in self.safety_rules if r.rule_id == rule_id), None)
            if not rule:
                return False
            
            rule.enabled = False
            
            self._log_safety_event(
                SafetyEventType.USER_INTERVENTION,
                SafetyLevel.WARNING,
                f"⚠️ Regra de segurança DESATIVADA: {rule.name}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao desativar regra: {e}")
            return False
    
    # Métodos privados
    def _init_safety_rules(self):
        """Inicializa regras básicas de segurança"""
        
        # Regra 1: Hardware conectado
        self.safety_rules.append(SafetyRule(
            rule_id="hardware_connected",
            name="Hardware HS3 Conectado",
            description="Verifica se o HS3 está conectado e respondendo",
            check_function=lambda: hs3_hardware.is_connected(),
            level=SafetyLevel.CRITICAL
        ))
        
        # Regra 2: Parâmetros dentro de limites
        def check_parameter_limits():
            if not self.current_parameters["generating"]:
                return True  # OK se não estiver gerando
            
            freq = self.current_parameters["frequency"]
            ampl = self.current_parameters["amplitude"]
            offs = self.current_parameters["offset"]
            
            freq_ok = self.limits.MIN_FREQUENCY <= freq <= self.limits.MAX_FREQUENCY
            ampl_ok = self.limits.MIN_AMPLITUDE <= ampl <= self.limits.MAX_AMPLITUDE
            offs_ok = self.limits.MIN_OFFSET <= offs <= self.limits.MAX_OFFSET
            
            return freq_ok and ampl_ok and offs_ok
        
        self.safety_rules.append(SafetyRule(
            rule_id="parameter_limits",
            name="Limites de Parâmetros",
            description="Verifica se todos os parâmetros estão dentro dos limites",
            check_function=check_parameter_limits,
            level=SafetyLevel.CRITICAL
        ))
        
        # Regra 3: Tensão total segura
        def check_total_voltage():
            if not self.current_parameters["generating"]:
                return True
            
            ampl = self.current_parameters["amplitude"]
            offs = self.current_parameters["offset"]
            total = ampl + abs(offs)
            
            return total <= self.limits.MAX_AMPLITUDE
        
        self.safety_rules.append(SafetyRule(
            rule_id="total_voltage",
            name="Tensão Total Segura",
            description="Verifica se amplitude + offset não excedem limite",
            check_function=check_total_voltage,
            level=SafetyLevel.CRITICAL
        ))
    
    def _perform_safety_checks(self):
        """Executa verificações de segurança periódicas"""
        if not self.is_monitoring:
            return
        
        try:
            # Atualizar parâmetros atuais
            self._update_current_parameters()
            
            # Executar regras críticas
            critical_violations = []
            warning_violations = []
            
            for rule in self.safety_rules:
                if not rule.enabled:
                    continue
                
                try:
                    result = rule.check_function()
                    if not result:
                        if rule.level == SafetyLevel.CRITICAL:
                            critical_violations.append(rule)
                        elif rule.level == SafetyLevel.WARNING:
                            warning_violations.append(rule)
                
                except Exception as e:
                    self.logger.error(f"Erro ao executar regra {rule.name}: {e}")
                    critical_violations.append(rule)
            
            # Processar violações críticas
            if critical_violations:
                violation_names = [r.name for r in critical_violations]
                error_msg = f"Violações críticas de segurança: {', '.join(violation_names)}"
                
                self._log_safety_event(
                    SafetyEventType.SYSTEM_ERROR,
                    SafetyLevel.CRITICAL,
                    error_msg
                )
                
                # Paragem de emergência automática
                self.emergency_shutdown(f"Violações automáticas: {error_msg}")
                
                return
            
            # Processar avisos
            if warning_violations:
                warning_names = [r.name for r in warning_violations]
                warning_msg = f"Avisos de segurança: {', '.join(warning_names)}"
                
                self._log_safety_event(
                    SafetyEventType.SYSTEM_ERROR,
                    SafetyLevel.WARNING,
                    warning_msg
                )
                
                self.safety_violation.emit("warning", warning_msg)
            
            # Atualizar nível de segurança
            new_level = SafetyLevel.WARNING if warning_violations else SafetyLevel.SAFE
            if new_level != self.current_safety_level:
                old_level = self.current_safety_level
                self.current_safety_level = new_level
                self.safety_status_changed.emit(f"level_changed_{old_level.value}_{new_level.value}")
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de segurança: {e}")
    
    def _update_current_parameters(self):
        """Atualiza parâmetros atuais do sistema"""
        try:
            if hs3_hardware.is_connected():
                status = hs3_hardware.get_status()
                
                # TODO: Obter parâmetros reais do HS3
                # Por agora, manter valores conhecidos
                self.current_parameters.update({
                    "generating": status.get("generating", False)
                })
            else:
                self.current_parameters.update({
                    "frequency": 0.0,
                    "amplitude": 0.0,
                    "offset": 0.0,
                    "generating": False
                })
                
        except Exception as e:
            self.logger.warning(f"Erro ao atualizar parâmetros: {e}")
    
    def _check_configuration_limits(self) -> Tuple[bool, str]:
        """Verifica limites de configuração"""
        try:
            # Verificar se configuração foi alterada maliciosamente
            if (self.limits.MAX_AMPLITUDE > 10.0 or 
                self.limits.MAX_FREQUENCY > 2_000_000 or
                abs(self.limits.MIN_OFFSET) > 5.0 or
                abs(self.limits.MAX_OFFSET) > 5.0):
                return False, "Limites de configuração foram alterados para valores inseguros"
            
            return True, "Configuração OK"
            
        except Exception as e:
            return False, f"Erro ao verificar configuração: {e}"
    
    def _log_safety_event(self, event_type: SafetyEventType, level: SafetyLevel, 
                         message: str, parameters: Dict = None):
        """Regista evento de segurança"""
        try:
            event = SafetyEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                level=level,
                message=message,
                parameters=parameters or {}
            )
            
            self.safety_events.append(event)
            
            # Emitir sinal
            event_dict = {
                "timestamp": event.timestamp.isoformat(),
                "type": event.event_type.value,
                "level": event.level.value,
                "message": event.message,
                "parameters": event.parameters
            }
            self.safety_event.emit(event_dict)
            
            # Log no sistema
            log_level = {
                SafetyLevel.SAFE: logging.INFO,
                SafetyLevel.WARNING: logging.WARNING,
                SafetyLevel.DANGER: logging.ERROR,
                SafetyLevel.CRITICAL: logging.CRITICAL
            }.get(level, logging.INFO)
            
            self.logger.log(log_level, f"[{level.value.upper()}] {message}")
            
        except Exception as e:
            self.logger.error(f"Erro ao registar evento de segurança: {e}")
    
    def _cleanup_old_events(self):
        """Remove eventos antigos para poupar memória"""
        try:
            # Manter apenas eventos dos últimos 7 dias
            cutoff_date = datetime.now() - timedelta(days=7)
            
            initial_count = len(self.safety_events)
            self.safety_events = [
                event for event in self.safety_events 
                if event.timestamp > cutoff_date
            ]
            
            removed_count = initial_count - len(self.safety_events)
            if removed_count > 0:
                self.logger.info(f"🧹 {removed_count} eventos de segurança antigos removidos")
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza de eventos: {e}")

# Instância global do gestor de segurança
safety_manager = SafetyManager()
