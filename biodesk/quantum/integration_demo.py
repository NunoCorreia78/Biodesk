"""
Exemplo de Integração Completa: Excel Parser + Protocol Runner
═══════════════════════════════════════════════════════════════════════

Demonstra o fluxo completo desde a leitura do Excel de frequências
até a execução do protocolo com o HS3Service.
"""

import sys
sys.path.append('.')

from biodesk.quantum.excel_parser import ExcelFrequencyParser
from biodesk.quantum.protocol_runner import (
    ProtocolRunner, Protocol, FrequencyStep, ProtocolMode, create_simple_protocol
)
from biodesk.quantum.safety import SafetyLimits, comprehensive_safety_check

def exemplo_fluxo_completo():
    """Demonstração do fluxo completo de terapia quântica"""
    
    print("🧬 FLUXO COMPLETO DE TERAPIA QUÂNTICA")
    print("═" * 50)
    
    # 1. Carregar frequências do Excel
    print("\n📊 1. Carregando frequências do Excel...")
    
    parser = ExcelFrequencyParser()
    parser.load_data()
    
    stats = parser.get_statistics()
    print(f"   Carregadas {stats['total_entries']} entradas")
    print(f"   {stats['unique_diseases']} doenças únicas")
    print(f"   {stats['unique_frequencies']} frequências únicas")
    
    # 2. Pesquisar condição médica
    print("\n🔍 2. Pesquisando condições médicas...")
    
    # Pesquisar por "stress"
    search_results = parser.search("stress")
    print(f"   Resultados para 'stress': {len(search_results)} encontrados")
    
    if search_results:
        for i, (disease, indication) in enumerate(search_results[:3]):
            print(f"   {i+1}. {disease} - {indication}")
    
    # Pesquisar por "pain" (dor)
    pain_results = parser.search("pain")
    print(f"   Resultados para 'pain': {len(pain_results)} encontrados")
    
    if pain_results:
        selected_disease = pain_results[0][0]  # Primeira doença encontrada
        print(f"   Selecionada: {selected_disease}")
        
        # 3. Obter frequências para a condição
        print("\n🎵 3. Obtendo frequências terapêuticas...")
        
        frequencies = parser.get_frequencies_by_disease(selected_disease)
        print(f"   Frequências para '{selected_disease}': {len(frequencies)}")
        print(f"   Primeiras 10: {frequencies[:10]}")
        print(f"   Faixa: {min(frequencies):.1f} - {max(frequencies):.1f} Hz")
        
        # 4. Criar protocolo
        print("\n📋 4. Criando protocolo terapêutico...")
        
        # Limitar a 8 frequências para demonstração
        selected_frequencies = frequencies[:8]
        
        protocol = create_simple_protocol(
            name=f"Protocolo {selected_disease}",
            frequencies=selected_frequencies,
            dwell_time=2.0,
            amplitude=0.8,
            waveform="sine"
        )
        
        # Adicionar limites de segurança personalizados
        protocol.safety_limits = SafetyLimits(
            max_amp_vpp=1.0,
            max_offset_v=0.3,
            max_frequency_hz=10000.0  # Limite para demonstração
        )
        
        print(f"   Protocolo criado: {protocol.name}")
        print(f"   Passos: {len(protocol.steps)}")
        print(f"   Duração estimada: {protocol.total_duration_s:.1f}s")
        
        # 5. Validação de segurança
        print("\n🛡️ 5. Validação de segurança...")
        
        # Dados do paciente (exemplo)
        paciente = {
            'nome': 'João Silva',
            'pacemaker': False,
            'gravidez': False,
            'epilepsia': False,
            'cancer_ativo': False,
            'idade': 45
        }
        
        # Confirmações de segurança
        confirmacoes = {
            'isolamento_verificado': True,
            'resistor_instalado': True,
            'paciente_informado': True,
            'consentimento_assinado': True,
            'emergencia_preparada': True,
            'supervisor_presente': True
        }
        
        try:
            # Validar primeiro passo como exemplo
            first_step = protocol.steps[0]
            comprehensive_safety_check(
                amp_vpp=first_step.amp_vpp,
                offset_v=first_step.offset_v,
                frequency_hz=first_step.hz,
                patient_dict=paciente,
                confirmations_dict=confirmacoes,
                limits=protocol.safety_limits
            )
            print("   ✅ Validação de segurança aprovada")
            
        except Exception as e:
            print(f"   ❌ Validação rejeitada: {e}")
            return False
        
        # 6. Executar protocolo (simulação)
        print("\n🚀 6. Executando protocolo (simulação)...")
        
        runner = ProtocolRunner(hs3_service=None)  # Simulação sem hardware
        
        # Monitorização básica
        def on_step_started(step_index, step):
            print(f"   🎵 Iniciando passo {step_index + 1}: {step.hz:.1f}Hz por {step.dwell_s:.1f}s")
        
        def on_step_finished(step_index):
            print(f"   ✅ Passo {step_index + 1} concluído")
        
        def on_finished():
            print("   🏁 Protocolo concluído com sucesso!")
        
        runner.step_started.connect(on_step_started)
        runner.step_finished.connect(on_step_finished)
        runner.finished.connect(on_finished)
        
        # Iniciar execução
        success = runner.start_protocol(protocol)
        if success:
            print("   ▶️ Protocolo iniciado")
            # Em aplicação real, aguardaria conclusão
            # Aqui simulamos com timer
            import time
            time.sleep(1)
            runner.abort_protocol("Teste concluído")
        else:
            print("   ❌ Falha ao iniciar protocolo")
    
    # 7. Estatísticas finais
    print("\n📈 7. Estatísticas da sessão...")
    
    # Criar protocolo de varredura como exemplo adicional
    from biodesk.quantum.protocol_runner import create_sweep_protocol
    
    sweep = create_sweep_protocol(
        name="Varredura Alpha",
        start_hz=8.0,
        end_hz=13.0,
        steps=6,
        dwell_s=1.5,
        amp_vpp=0.4
    )
    
    print(f"   Protocolo adicional criado: {sweep.name}")
    print(f"   Faixa: {sweep.frequency_range[0]:.1f} - {sweep.frequency_range[1]:.1f}Hz")
    print(f"   Duração: {sweep.total_duration_s:.1f}s")
    
    # Criar protocolo com diferentes modos
    mixed_steps = [
        FrequencyStep(hz=440.0, dwell_s=2.0, amp_vpp=0.5, mode=ProtocolMode.CONTINUOUS),
        FrequencyStep(hz=528.0, dwell_s=1.5, amp_vpp=0.6, mode=ProtocolMode.BURST, burst_cycles=150),
        FrequencyStep(hz=741.0, dwell_s=2.0, amp_vpp=0.4, mode=ProtocolMode.GATED)
    ]
    
    mixed_protocol = Protocol(
        name="Protocolo Misto",
        description="Demonstração de modos diferentes",
        steps=mixed_steps
    )
    
    print(f"   Protocolo misto: {mixed_protocol.name}")
    print(f"   Modos utilizados: {[step.mode.value for step in mixed_protocol.steps]}")
    
    return True


def demonstrar_integracao_hs3():
    """Demonstrar integração com HS3Service (conceitual)"""
    
    print("\n🔌 8. Integração com HS3Service (conceitual)...")
    
    # Código conceitual para integração real
    print("""
    # Em ambiente de produção:
    
    from biodesk.quantum.hs3_service import HS3Service
    
    # Inicializar hardware
    hs3 = HS3Service()
    hs3.open()
    
    # Criar runner com hardware real
    runner = ProtocolRunner(hs3_service=hs3)
    
    # Executar protocolo
    runner.start_protocol(protocol)
    
    # Monitorizar progresso em tempo real
    runner.live_metrics.connect(update_ui)
    
    # Cleanup
    hs3.close()
    """)
    
    print("   💡 Para execução real, descomente as linhas do HS3Service")
    print("   💡 Certifique-se de que o hardware HS3 está conectado")


if __name__ == "__main__":
    try:
        success = exemplo_fluxo_completo()
        
        if success:
            demonstrar_integracao_hs3()
            
            print("\n🎉 DEMONSTRAÇÃO COMPLETA CONCLUÍDA!")
            print("\n🌟 RESUMO DOS MÓDULOS INTEGRADOS:")
            print("   📊 ExcelFrequencyParser - Leitura de frequências")
            print("   🛡️ SafetyLimits - Validação de segurança")
            print("   🏃 ProtocolRunner - Execução de protocolos")
            print("   🔌 HS3Service - Controlo de hardware")
            print("\n✅ Sistema de Terapia Quântica completamente funcional!")
        
    except Exception as e:
        print(f"\n❌ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()
