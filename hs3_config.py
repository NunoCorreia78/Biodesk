"""
Configurações de Segurança para Gerador HS3
═══════════════════════════════════════════════════════════════════════

Este arquivo define os limites de segurança e configurações do gerador HS3.
NUNCA altere estes valores sem conhecimento técnico adequado.
"""

from typing import Dict, Tuple
import json
import os
from dataclasses import dataclass

@dataclass
class HS3SafetyLimits:
    """Limites de segurança absolutos do HS3"""
    # Amplitude (V)
    MIN_AMPLITUDE: float = 0.1
    MAX_AMPLITUDE: float = 5.0
    DEFAULT_AMPLITUDE: float = 2.0
    
    # Offset (V)
    MIN_OFFSET: float = -2.5
    MAX_OFFSET: float = 2.5
    DEFAULT_OFFSET: float = 0.0
    
    # Frequência (Hz)
    MIN_FREQUENCY: float = 0.1
    MAX_FREQUENCY: float = 1_000_000.0
    DEFAULT_FREQUENCY: float = 1000.0
    
    # Duração (minutos)
    MIN_DURATION: int = 1
    MAX_DURATION: int = 60
    DEFAULT_DURATION: int = 5
    
    # Comunicação
    SERIAL_TIMEOUT: float = 2.0
    SERIAL_BAUDRATE: int = 115200
    CONNECTION_RETRY_ATTEMPTS: int = 3
    CONNECTION_RETRY_DELAY: float = 1.0

class HS3Config:
    """
    Gestão de configurações do HS3 com validação de segurança
    """
    
    def __init__(self, config_file: str = "hs3_config.json"):
        self.config_file = config_file
        self.limits = HS3SafetyLimits()
        self.user_config = self._load_user_config()
    
    def _load_user_config(self) -> Dict:
        """Carrega configurações do utilizador"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar configuração: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Configuração padrão"""
        return {
            "amplitude_padrao": self.limits.DEFAULT_AMPLITUDE,
            "offset_padrao": self.limits.DEFAULT_OFFSET,
            "duracao_padrao": self.limits.DEFAULT_DURATION,
            "porta_com": "AUTO",  # Detecção automática
            "logs_detalhados": True,
            "som_alertas": True,
            "confirmacao_inicio": True,
            "pausa_automatica": True,
            "backup_sessoes": True
        }
    
    def save_config(self):
        """Grava configurações"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao gravar configuração: {e}")
    
    def validate_amplitude(self, amplitude: float) -> Tuple[bool, str]:
        """Valida amplitude"""
        if not isinstance(amplitude, (int, float)):
            return False, "Amplitude deve ser um número"
        
        if amplitude < self.limits.MIN_AMPLITUDE:
            return False, f"Amplitude mínima: {self.limits.MIN_AMPLITUDE}V"
        
        if amplitude > self.limits.MAX_AMPLITUDE:
            return False, f"Amplitude máxima: {self.limits.MAX_AMPLITUDE}V"
        
        return True, "OK"
    
    def validate_offset(self, offset: float) -> Tuple[bool, str]:
        """Valida offset"""
        if not isinstance(offset, (int, float)):
            return False, "Offset deve ser um número"
        
        if offset < self.limits.MIN_OFFSET:
            return False, f"Offset mínimo: {self.limits.MIN_OFFSET}V"
        
        if offset > self.limits.MAX_OFFSET:
            return False, f"Offset máximo: {self.limits.MAX_OFFSET}V"
        
        return True, "OK"
    
    def validate_frequency(self, frequency: float) -> Tuple[bool, str]:
        """Valida frequência"""
        if not isinstance(frequency, (int, float)):
            return False, "Frequência deve ser um número"
        
        if frequency < self.limits.MIN_FREQUENCY:
            return False, f"Frequência mínima: {self.limits.MIN_FREQUENCY}Hz"
        
        if frequency > self.limits.MAX_FREQUENCY:
            return False, f"Frequência máxima: {self.limits.MAX_FREQUENCY:,}Hz"
        
        return True, "OK"
    
    def validate_duration(self, duration: int) -> Tuple[bool, str]:
        """Valida duração"""
        if not isinstance(duration, int):
            return False, "Duração deve ser um número inteiro"
        
        if duration < self.limits.MIN_DURATION:
            return False, f"Duração mínima: {self.limits.MIN_DURATION} minuto(s)"
        
        if duration > self.limits.MAX_DURATION:
            return False, f"Duração máxima: {self.limits.MAX_DURATION} minuto(s)"
        
        return True, "OK"
    
    def validate_all_parameters(self, amplitude: float, offset: float, 
                              frequency: float, duration: int) -> Tuple[bool, str]:
        """Valida todos os parâmetros de uma só vez"""
        
        # Validar amplitude
        valid, msg = self.validate_amplitude(amplitude)
        if not valid:
            return False, f"Amplitude inválida: {msg}"
        
        # Validar offset
        valid, msg = self.validate_offset(offset)
        if not valid:
            return False, f"Offset inválido: {msg}"
        
        # Validar frequência
        valid, msg = self.validate_frequency(frequency)
        if not valid:
            return False, f"Frequência inválida: {msg}"
        
        # Validar duração
        valid, msg = self.validate_duration(duration)
        if not valid:
            return False, f"Duração inválida: {msg}"
        
        return True, "Todos os parâmetros são válidos"
    
    def get_safe_parameters(self, amplitude: float = None, offset: float = None,
                          frequency: float = None, duration: int = None) -> Dict:
        """
        Retorna parâmetros seguros, aplicando limites se necessário
        """
        result = {}
        
        # Amplitude
        if amplitude is None:
            result['amplitude'] = self.user_config.get('amplitude_padrao', self.limits.DEFAULT_AMPLITUDE)
        else:
            result['amplitude'] = max(self.limits.MIN_AMPLITUDE, 
                                    min(amplitude, self.limits.MAX_AMPLITUDE))
        
        # Offset
        if offset is None:
            result['offset'] = self.user_config.get('offset_padrao', self.limits.DEFAULT_OFFSET)
        else:
            result['offset'] = max(self.limits.MIN_OFFSET, 
                                 min(offset, self.limits.MAX_OFFSET))
        
        # Frequência
        if frequency is None:
            result['frequency'] = self.limits.DEFAULT_FREQUENCY
        else:
            result['frequency'] = max(self.limits.MIN_FREQUENCY, 
                                    min(frequency, self.limits.MAX_FREQUENCY))
        
        # Duração
        if duration is None:
            result['duration'] = self.user_config.get('duracao_padrao', self.limits.DEFAULT_DURATION)
        else:
            result['duration'] = max(self.limits.MIN_DURATION, 
                                   min(duration, self.limits.MAX_DURATION))
        
        return result

# Instância global das configurações
hs3_config = HS3Config()
