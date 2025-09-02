"""
Exemplo de Integração: HS3Service + Sistema de Segurança
═══════════════════════════════════════════════════════════════════════

Demonstra como usar o sistema de segurança em conjunto com o HS3Service
para garantir operação segura do equipamento de terapia quântica.
"""

# Exemplo conceitual de integração (não executar sem hardware)

from biodesk.quantum.safety import (
    SafetyLimits, SafetyError, SafetyValidator, 
    comprehensive_safety_check
)

# from biodesk.quantum.hs3_service import HS3Service  # Descomentado quando necessário

def exemplo_terapia_segura():
    """
    Exemplo de como executar uma terapia com todas as verificações de segurança
    """
    
    # 1. Configurar limites de segurança
    safety_limits = SafetyLimits(
        max_amp_vpp=1.5,        # Limite mais restritivo que o padrão
        max_offset_v=0.3,       # Limite mais restritivo
        max_frequency_hz=50000  # Máximo 50kHz
    )
    
    # 2. Dados do paciente (exemplo)
    paciente = {
        'nome': 'João Silva',
        'idade': 45,
        'pacemaker': False,
        'gravidez': False,
        'epilepsia': False,
        'medicacao_anticoagulante': False,
        'consentimento_assinado': True
    }
    
    # 3. Confirmações de segurança
    confirmacoes = {
        'isolamento_verificado': True,
        'resistor_instalado': True,
        'paciente_informado': True,
        'consentimento_assinado': True,
        'emergencia_preparada': True,
        'supervisor_presente': True
    }
    
    # 4. Parâmetros da terapia
    parametros_terapia = {
        'amplitude_vpp': 1.0,
        'offset_v': 0.1,
        'frequencies': [440.0, 528.0, 741.0, 852.0],  # Frequências de exemplo
        'dwell_time_s': 3.0,
        'waveform': 'sine'
    }
    
    print("🛡️ Executando terapia com verificações de segurança...")
    
    try:
        # 5. Verificação completa de segurança para cada frequência
        for freq in parametros_terapia['frequencies']:
            print(f"\n🔍 Verificando frequência {freq}Hz...")
            
            comprehensive_safety_check(
                amp_vpp=parametros_terapia['amplitude_vpp'],
                offset_v=parametros_terapia['offset_v'],
                frequency_hz=freq,
                patient_dict=paciente,
                confirmations_dict=confirmacoes,
                limits=safety_limits
            )
            
            print(f"✅ Frequência {freq}Hz aprovada")
        
        print("\n🎯 Todas as verificações passaram!")
        print("💚 Terapia pode ser executada com segurança")
        
        # 6. Aqui seria a execução real com HS3Service
        """
        # Pseudo-código para execução real:
        
        hs3 = HS3Service()
        hs3.open()
        
        try:
            hs3.configure_generator(
                signal_type=parametros_terapia['waveform'],
                amplitude_vpp=parametros_terapia['amplitude_vpp'],
                offset_v=parametros_terapia['offset_v']
            )
            
            for freq in parametros_terapia['frequencies']:
                print(f"🎵 Aplicando {freq}Hz por {parametros_terapia['dwell_time_s']}s...")
                
                hs3.set_frequency(freq)
                hs3.start_output()
                time.sleep(parametros_terapia['dwell_time_s'])
                hs3.stop_output()
                
                # Pequena pausa entre frequências
                time.sleep(0.5)
            
        finally:
            hs3.close()
        """
        
    except SafetyError as e:
        print(f"\n❌ TERAPIA BLOQUEADA POR SEGURANÇA:")
        print(f"   {e}")
        print("\n🚫 Corrija os problemas antes de continuar")
        return False
    
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")
        return False
    
    return True


def exemplo_validador_avancado():
    """
    Exemplo de uso do SafetyValidator para monitorização contínua
    """
    print("\n🔬 Exemplo do SafetyValidator avançado...")
    
    # Configurar validador
    validator = SafetyValidator(SafetyLimits())
    
    # Simular série de validações
    test_cases = [
        (0.5, 0.1),  # Seguro
        (1.5, 0.2),  # Seguro
        (2.5, 0.0),  # Amplitude excessiva
        (1.0, 0.8),  # Offset excessivo
    ]
    
    print("\n📊 Resultados das validações:")
    for amp, offset in test_cases:
        is_valid = validator.validate_output(amp, offset)
        status = "✅ APROVADO" if is_valid else "❌ REJEITADO"
        print(f"   {amp}V/{offset}V: {status}")
    
    # Verificar histórico
    print(f"\n📈 Histórico: {len(validator.validation_history)} validações registadas")
    
    # Estatísticas simples
    successful = sum(1 for v in validator.validation_history if v['success'])
    failed = len(validator.validation_history) - successful
    print(f"   Sucessos: {successful}, Falhas: {failed}")


if __name__ == "__main__":
    print("🧪 EXEMPLO DE INTEGRAÇÃO: HS3Service + Sistema de Segurança")
    print("═" * 65)
    
    # Executar exemplo de terapia segura
    exemplo_terapia_segura()
    
    # Executar exemplo de validador avançado
    exemplo_validador_avancado()
    
    print("\n🎉 Exemplos de integração concluídos!")
    print("\n💡 NOTA: Para execução real, descomente as linhas do HS3Service")
    print("   e certifique-se de que o hardware está conectado.")
