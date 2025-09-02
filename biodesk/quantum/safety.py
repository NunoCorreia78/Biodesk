"""
Sistema de Segurança e Interlocks - Biodesk Quantum
═══════════════════════════════════════════════════════════════════════

Sistema modular de segurança com validação de parâmetros, verificação de
condições médicas do paciente e confirmações obrigatórias.

Funcionalidades:
- Validação rigorosa de amplitude e offset
- Verificação de contraindicações médicas
- Sistema de confirmações obrigatórias
- Mensagens claras em português
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SafetyError(Exception):
    """Erro de segurança do sistema"""
    pass


class SafetyLevel(Enum):
    """Níveis de criticidade de segurança"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass
class SafetyLimits:
    """
    Configuração dos limites de segurança do sistema
    
    Todos os valores são configuráveis e devem ser ajustados
    conforme os requisitos de segurança específicos.
    """
    # Limites elétricos
    max_amp_vpp: float = 2.0  # Amplitude máxima pico-a-pico (V)
    max_offset_v: float = 0.5  # Offset DC máximo (V)
    max_total_voltage: float = 2.5  # Tensão total máxima |amp + offset| (V)
    
    # Isolamento e proteção
    require_isolation_confirmed: bool = True
    require_series_resistor_ohm: float = 100_000.0  # Resistor de proteção mínimo (Ω)
    min_isolation_resistance_ohm: float = 1_000_000.0  # Isolamento mínimo (MΩ)
    
    # Contraindicações médicas (flags que bloqueiam tratamento)
    forbidden_flags: Dict[str, bool] = field(default_factory=lambda: {
        # Dispositivos implantados
        "pacemaker": True,
        "desfibrilador": True,
        "bomba_insulina": True,
        "implante_coclear": True,
        "estimulador_cerebral": True,
        "prótese_metalica": True,
        
        # Condições médicas
        "epilepsia": True,
        "gravidez": True,
        "cancer_ativo": True,
        "quimioterapia_recente": True,
        "radioterapia_recente": True,
        
        # Condições especiais
        "menor_idade": True,
        "estado_critico": True,
        "medicacao_anticoagulante": True,
        "historico_convulsoes": True,
        
        # Procedimentos recentes
        "cirurgia_recente": True,
        "procedimento_invasivo": True
    })
    
    # Confirmações obrigatórias
    required_confirmations: List[str] = field(default_factory=lambda: [
        "isolamento_verificado",
        "resistor_instalado", 
        "paciente_informado",
        "consentimento_assinado",
        "emergencia_preparada",
        "supervisor_presente"
    ])
    
    # Limites de frequência (Hz)
    min_frequency_hz: float = 0.1
    max_frequency_hz: float = 100_000.0
    
    # Limites de tempo
    max_session_duration_min: float = 60.0
    max_single_frequency_duration_min: float = 10.0


def assert_safe_output(amp_vpp: float, 
                      offset_v: float, 
                      limits: SafetyLimits) -> None:
    """
    Validação rigorosa dos parâmetros de saída
    
    Args:
        amp_vpp: Amplitude pico-a-pico em volts
        offset_v: Offset DC em volts
        limits: Configuração dos limites de segurança
        
    Raises:
        SafetyError: Se algum parâmetro violar os limites de segurança
    """
    logger = logging.getLogger("QuantumSafety")
    
    # Validação de tipos
    if not isinstance(amp_vpp, (int, float)) or not isinstance(offset_v, (int, float)):
        raise SafetyError("❌ ERRO CRÍTICO: Parâmetros devem ser numéricos")
    
    # Validação de amplitude
    if amp_vpp < 0:
        raise SafetyError("❌ AMPLITUDE INVÁLIDA: Não pode ser negativa")
    
    if amp_vpp > limits.max_amp_vpp:
        raise SafetyError(
            f"❌ AMPLITUDE EXCESSIVA: {amp_vpp:.3f}V excede limite máximo "
            f"de {limits.max_amp_vpp:.3f}V"
        )
    
    # Validação de offset
    if abs(offset_v) > limits.max_offset_v:
        raise SafetyError(
            f"❌ OFFSET EXCESSIVO: {abs(offset_v):.3f}V excede limite máximo "
            f"de ±{limits.max_offset_v:.3f}V"
        )
    
    # Validação de tensão total (amplitude + offset)
    total_positive = amp_vpp/2 + offset_v
    total_negative = -amp_vpp/2 + offset_v
    max_total = max(abs(total_positive), abs(total_negative))
    
    if max_total > limits.max_total_voltage:
        raise SafetyError(
            f"❌ TENSÃO TOTAL EXCESSIVA: {max_total:.3f}V excede limite "
            f"de {limits.max_total_voltage:.3f}V (amplitude + offset)"
        )
    
    # Log de aprovação
    logger.info(
        f"✅ Parâmetros aprovados: Amplitude {amp_vpp:.3f}V, "
        f"Offset {offset_v:.3f}V, Tensão total {max_total:.3f}V"
    )


def check_patient_flags(patient_dict: Dict[str, Any], 
                       limits: Optional[SafetyLimits] = None) -> List[str]:
    """
    Verificar contraindicações médicas do paciente
    
    Args:
        patient_dict: Dicionário com dados do paciente
        limits: Configuração dos limites (usa padrão se None)
        
    Returns:
        Lista de mensagens de bloqueio (vazia se seguro)
    """
    if limits is None:
        limits = SafetyLimits()
    
    bloqueios = []
    forbidden_flags = limits.forbidden_flags
    
    # Verificar cada flag de contraindicação
    for flag_name, is_forbidden in forbidden_flags.items():
        if not is_forbidden:
            continue  # Flag não é bloqueante
        
        # Verificar se paciente tem esta condição
        patient_value = patient_dict.get(flag_name, False)
        
        # Considerar diferentes formatos de valor
        has_condition = False
        if isinstance(patient_value, bool):
            has_condition = patient_value
        elif isinstance(patient_value, str):
            has_condition = patient_value.lower() in ['sim', 'yes', 'true', '1', 'positivo']
        elif isinstance(patient_value, (int, float)):
            has_condition = bool(patient_value)
        
        if has_condition:
            # Gerar mensagem específica em português
            mensagem = _gerar_mensagem_bloqueio(flag_name)
            bloqueios.append(mensagem)
    
    return bloqueios


def require_confirmations(confirmations_dict: Dict[str, bool], 
                         limits: Optional[SafetyLimits] = None) -> None:
    """
    Verificar se todas as confirmações obrigatórias foram feitas
    
    Args:
        confirmations_dict: Dicionário com estado das confirmações
        limits: Configuração dos limites (usa padrão se None)
        
    Raises:
        SafetyError: Se alguma confirmação obrigatória estiver em falta
    """
    if limits is None:
        limits = SafetyLimits()
    
    confirmacoes_em_falta = []
    
    for required_confirmation in limits.required_confirmations:
        confirmed = confirmations_dict.get(required_confirmation, False)
        
        if not confirmed:
            mensagem = _gerar_mensagem_confirmacao(required_confirmation)
            confirmacoes_em_falta.append(mensagem)
    
    if confirmacoes_em_falta:
        erro_msg = (
            "❌ CONFIRMAÇÕES EM FALTA:\n" + 
            "\n".join(f"   • {msg}" for msg in confirmacoes_em_falta)
        )
        raise SafetyError(erro_msg)


def validate_frequency_range(frequency_hz: float, 
                            limits: Optional[SafetyLimits] = None) -> None:
    """
    Validar se a frequência está dentro dos limites seguros
    
    Args:
        frequency_hz: Frequência em Hz
        limits: Configuração dos limites (usa padrão se None)
        
    Raises:
        SafetyError: Se a frequência estiver fora dos limites
    """
    if limits is None:
        limits = SafetyLimits()
    
    if not isinstance(frequency_hz, (int, float)):
        raise SafetyError("❌ FREQUÊNCIA INVÁLIDA: Deve ser numérica")
    
    if frequency_hz <= 0:
        raise SafetyError("❌ FREQUÊNCIA INVÁLIDA: Deve ser positiva")
    
    if frequency_hz < limits.min_frequency_hz:
        raise SafetyError(
            f"❌ FREQUÊNCIA MUITO BAIXA: {frequency_hz:.2f}Hz está abaixo "
            f"do mínimo de {limits.min_frequency_hz:.2f}Hz"
        )
    
    if frequency_hz > limits.max_frequency_hz:
        raise SafetyError(
            f"❌ FREQUÊNCIA MUITO ALTA: {frequency_hz:.2f}Hz excede "
            f"o máximo de {limits.max_frequency_hz:.2f}Hz"
        )


def validate_session_duration(duration_min: float, 
                             limits: Optional[SafetyLimits] = None) -> None:
    """
    Validar duração da sessão
    
    Args:
        duration_min: Duração em minutos
        limits: Configuração dos limites (usa padrão se None)
        
    Raises:
        SafetyError: Se a duração exceder os limites
    """
    if limits is None:
        limits = SafetyLimits()
    
    if duration_min <= 0:
        raise SafetyError("❌ DURAÇÃO INVÁLIDA: Deve ser positiva")
    
    if duration_min > limits.max_session_duration_min:
        raise SafetyError(
            f"❌ SESSÃO MUITO LONGA: {duration_min:.1f}min excede "
            f"o máximo de {limits.max_session_duration_min:.1f}min"
        )


def comprehensive_safety_check(amp_vpp: float,
                             offset_v: float,
                             frequency_hz: float,
                             patient_dict: Dict[str, Any],
                             confirmations_dict: Dict[str, bool],
                             limits: Optional[SafetyLimits] = None) -> None:
    """
    Verificação completa de segurança antes de iniciar terapia
    
    Args:
        amp_vpp: Amplitude pico-a-pico
        offset_v: Offset DC
        frequency_hz: Frequência
        patient_dict: Dados do paciente
        confirmations_dict: Estado das confirmações
        limits: Configuração dos limites
        
    Raises:
        SafetyError: Se qualquer verificação falhar
    """
    if limits is None:
        limits = SafetyLimits()
    
    # 1. Verificar parâmetros elétricos
    assert_safe_output(amp_vpp, offset_v, limits)
    
    # 2. Verificar frequência
    validate_frequency_range(frequency_hz, limits)
    
    # 3. Verificar contraindicações do paciente
    bloqueios = check_patient_flags(patient_dict, limits)
    if bloqueios:
        erro_msg = (
            "❌ TRATAMENTO BLOQUEADO - CONTRAINDICAÇÕES:\n" +
            "\n".join(f"   • {bloqueio}" for bloqueio in bloqueios)
        )
        raise SafetyError(erro_msg)
    
    # 4. Verificar confirmações obrigatórias
    require_confirmations(confirmations_dict, limits)
    
    # Log final de aprovação
    logger = logging.getLogger("QuantumSafety")
    logger.info("🛡️ VERIFICAÇÃO COMPLETA DE SEGURANÇA: APROVADA")


# ═══════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES PARA MENSAGENS EM PORTUGUÊS
# ═══════════════════════════════════════════════════════════════════════

def _gerar_mensagem_bloqueio(flag_name: str) -> str:
    """Gerar mensagem de bloqueio específica em português"""
    mensagens = {
        # Dispositivos implantados
        "pacemaker": "Saída bloqueada: pacemaker declarado",
        "desfibrilador": "Saída bloqueada: desfibrilador implantado",
        "bomba_insulina": "Saída bloqueada: bomba de insulina implantada",
        "implante_coclear": "Saída bloqueada: implante coclear detectado",
        "estimulador_cerebral": "Saída bloqueada: estimulador cerebral profundo",
        "prótese_metalica": "Saída bloqueada: prótese metálica implantada",
        
        # Condições médicas
        "epilepsia": "Saída bloqueada: histórico de epilepsia",
        "gravidez": "Saída bloqueada: paciente grávida",
        "cancer_ativo": "Saída bloqueada: cancro ativo em tratamento",
        "quimioterapia_recente": "Saída bloqueada: quimioterapia recente",
        "radioterapia_recente": "Saída bloqueada: radioterapia recente",
        
        # Condições especiais
        "menor_idade": "Saída bloqueada: paciente menor de idade",
        "estado_critico": "Saída bloqueada: paciente em estado crítico",
        "medicacao_anticoagulante": "Saída bloqueada: medicação anticoagulante",
        "historico_convulsoes": "Saída bloqueada: histórico de convulsões",
        
        # Procedimentos recentes
        "cirurgia_recente": "Saída bloqueada: cirurgia recente",
        "procedimento_invasivo": "Saída bloqueada: procedimento invasivo recente"
    }
    
    return mensagens.get(flag_name, f"Saída bloqueada: {flag_name} declarado")


def _gerar_mensagem_confirmacao(confirmation_name: str) -> str:
    """Gerar mensagem de confirmação específica em português"""
    mensagens = {
        "isolamento_verificado": "Isolamento elétrico não verificado",
        "resistor_instalado": "Resistor de proteção não confirmado",
        "paciente_informado": "Paciente não foi devidamente informado",
        "consentimento_assinado": "Consentimento informado não assinado",
        "emergencia_preparada": "Protocolo de emergência não preparado",
        "supervisor_presente": "Supervisor qualificado não presente"
    }
    
    return mensagens.get(confirmation_name, f"Confirmação em falta: {confirmation_name}")


# ═══════════════════════════════════════════════════════════════════════
# CLASSES DE CONVENIÊNCIA PARA USO AVANÇADO
# ═══════════════════════════════════════════════════════════════════════

class SafetyValidator:
    """
    Validador de segurança com estado persistente
    
    Útil para manter configurações e histórico de validações
    durante uma sessão de terapia.
    """
    
    def __init__(self, limits: Optional[SafetyLimits] = None):
        """
        Inicializar validador
        
        Args:
            limits: Configuração dos limites (usa padrão se None)
        """
        self.limits = limits or SafetyLimits()
        self.logger = logging.getLogger("SafetyValidator")
        self.validation_history: List[Dict[str, Any]] = []
    
    def validate_output(self, amp_vpp: float, offset_v: float) -> bool:
        """
        Validar saída e registrar no histórico
        
        Args:
            amp_vpp: Amplitude pico-a-pico
            offset_v: Offset DC
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            assert_safe_output(amp_vpp, offset_v, self.limits)
            self._log_validation(True, "Parâmetros aprovados", {
                "amp_vpp": amp_vpp, "offset_v": offset_v
            })
            return True
        except SafetyError as e:
            self._log_validation(False, str(e), {
                "amp_vpp": amp_vpp, "offset_v": offset_v
            })
            return False
    
    def validate_patient(self, patient_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validar paciente e retornar resultado detalhado
        
        Args:
            patient_dict: Dados do paciente
            
        Returns:
            Tupla (is_safe, list_of_blockages)
        """
        bloqueios = check_patient_flags(patient_dict, self.limits)
        is_safe = len(bloqueios) == 0
        
        self._log_validation(is_safe, 
                           "Paciente aprovado" if is_safe else f"{len(bloqueios)} bloqueios",
                           {"patient_flags": patient_dict})
        
        return is_safe, bloqueios
    
    def _log_validation(self, success: bool, message: str, data: Dict[str, Any]) -> None:
        """Registrar validação no histórico"""
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.now(),
            "success": success,
            "message": message,
            "data": data
        }
        
        self.validation_history.append(entry)
        
        # Manter apenas últimas 100 validações
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]


# ═══════════════════════════════════════════════════════════════════════
# TESTES UNITÁRIOS
# ═══════════════════════════════════════════════════════════════════════

def test_safety_limits():
    """Teste de criação e configuração de limites"""
    limits = SafetyLimits()
    assert limits.max_amp_vpp == 2.0
    assert limits.max_offset_v == 0.5
    assert limits.forbidden_flags["pacemaker"] is True
    assert "isolamento_verificado" in limits.required_confirmations


def test_assert_safe_output():
    """Teste de validação de parâmetros de saída"""
    limits = SafetyLimits()
    
    # Parâmetros válidos
    assert_safe_output(1.0, 0.2, limits)  # Deve passar
    
    # Amplitude excessiva
    try:
        assert_safe_output(3.0, 0.0, limits)
        assert False, "Deveria ter levantado SafetyError"
    except SafetyError:
        pass
    
    # Offset excessivo
    try:
        assert_safe_output(1.0, 1.0, limits)
        assert False, "Deveria ter levantado SafetyError"
    except SafetyError:
        pass


def test_check_patient_flags():
    """Teste de verificação de contraindicações"""
    limits = SafetyLimits()
    
    # Paciente seguro
    paciente_seguro = {"pacemaker": False, "gravidez": False}
    bloqueios = check_patient_flags(paciente_seguro, limits)
    assert len(bloqueios) == 0
    
    # Paciente com pacemaker
    paciente_pacemaker = {"pacemaker": True}
    bloqueios = check_patient_flags(paciente_pacemaker, limits)
    assert len(bloqueios) == 1
    assert "pacemaker" in bloqueios[0]


def test_require_confirmations():
    """Teste de verificação de confirmações"""
    limits = SafetyLimits()
    
    # Todas as confirmações feitas
    confirmacoes_completas = {conf: True for conf in limits.required_confirmations}
    require_confirmations(confirmacoes_completas, limits)  # Deve passar
    
    # Confirmação em falta
    confirmacoes_incompletas = {conf: True for conf in limits.required_confirmations}
    confirmacoes_incompletas["isolamento_verificado"] = False
    
    try:
        require_confirmations(confirmacoes_incompletas, limits)
        assert False, "Deveria ter levantado SafetyError"
    except SafetyError:
        pass


if __name__ == "__main__":
    # Executar testes
    print("🧪 Executando testes do sistema de segurança...")
    
    test_safety_limits()
    print("✅ test_safety_limits")
    
    test_assert_safe_output()
    print("✅ test_assert_safe_output")
    
    test_check_patient_flags()
    print("✅ test_check_patient_flags")
    
    test_require_confirmations()
    print("✅ test_require_confirmations")
    
    print("🎉 Todos os testes de segurança passaram!")
