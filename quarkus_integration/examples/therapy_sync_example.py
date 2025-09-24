"""
Exemplo de Sincronização de Terapia - Biodesk + Quarkus
═══════════════════════════════════════════════════════════════

Este exemplo demonstra como sincronizar dados de terapia quântica
do Biodesk com os sistemas Quarkus Super Heroes.
"""

import sys
import os
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar diretório pai ao path para importar o cliente
sys.path.append(str(Path(__file__).parent.parent))

from biodesk_quarkus_client import BiodeskQuarkusIntegration, Hero, Villain, Fight
import logging

# Dados de exemplo para simulação da terapia Biodesk
THERAPY_MODALITIES = [
    "Quantum Resonance Therapy",
    "Biofield Healing",
    "Frequency Therapy", 
    "Quantum Information Therapy",
    "Bioresonance Treatment",
    "Quantum Field Therapy",
    "Informational Medicine",
    "Quantum Cellular Therapy"
]

THERAPY_OUTCOMES = [
    "Improved energy levels",
    "Better sleep quality",
    "Enhanced immune response",
    "Reduced stress markers",
    "Improved cellular function",
    "Balanced biofield",
    "Optimized frequency patterns",
    "Enhanced wellbeing"
]

def simulate_therapy_session():
    """Simular uma sessão de terapia quântica do Biodesk"""
    
    session_data = {
        "session_id": f"BIODESK-{int(time.time())}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_id": f"PT-{random.randint(1000, 9999)}",
        "therapy_type": random.choice(THERAPY_MODALITIES),
        "duration_minutes": random.randint(30, 90),
        "frequencies_used": [
            round(random.uniform(0.1, 1000.0), 2) for _ in range(random.randint(3, 8))
        ],
        "outcome": random.choice(THERAPY_OUTCOMES),
        "effectiveness_score": round(random.uniform(7.0, 10.0), 1),
        "notes": f"Session completed successfully with {random.choice(['excellent', 'good', 'satisfactory'])} patient response"
    }
    
    return session_data

def create_therapy_heroes(client: BiodeskQuarkusIntegration, therapy_sessions: list) -> list:
    """Criar heróis baseados nos dados de terapia"""
    
    print("🦸 Criando heróis baseados em terapias realizadas...")
    
    created_heroes = []
    
    for session in therapy_sessions[:3]:  # Criar apenas 3 heróis de exemplo
        # Criar herói inspirado na sessão de terapia
        hero_name = f"Quantum {session['therapy_type'].split()[0]} Master"
        hero_other_name = f"Biodesk Therapist #{session['patient_id'].split('-')[1]}"
        hero_level = int(session['effectiveness_score'] * 10)  # Converter score para nível
        
        # Poderes baseados nas frequências usadas
        main_frequency = max(session['frequencies_used'])
        if main_frequency < 10:
            power_category = "Low frequency healing"
        elif main_frequency < 100:
            power_category = "Mid frequency therapy"
        else:
            power_category = "High frequency resonance"
        
        hero_powers = f"{power_category}, {session['outcome']}, {session['therapy_type']}"
        
        new_hero = Hero(
            name=hero_name,
            other_name=hero_other_name,
            level=hero_level,
            powers=hero_powers,
            picture=f"https://biodesk.com/avatars/therapist_{session['patient_id'].split('-')[1]}.jpg"
        )
        
        print(f"  🔨 Criando: {new_hero.name} (Nível {new_hero.level})")
        
        # Tentar criar o herói
        try:
            created_hero = client.create_hero(new_hero)
            if created_hero:
                created_heroes.append(created_hero)
                print(f"    ✅ Criado com ID: {created_hero.id}")
            else:
                print(f"    ⚠️ Não foi possível criar (serviço read-only?)")
                # Adicionar à lista de qualquer forma para demonstração
                created_heroes.append(new_hero)
        except Exception as e:
            print(f"    ❌ Erro: {e}")
    
    return created_heroes

def map_therapy_to_fights(therapy_sessions: list, heroes: list, villains: list) -> dict:
    """Mapear sessões de terapia para combates conceituais"""
    
    print("\n⚔️ Mapeando terapias para combates conceituais...")
    
    fight_mappings = []
    
    for session in therapy_sessions:
        # Selecionar herói aleatório (representando o aspecto positivo da terapia)
        hero = random.choice(heroes) if heroes else None
        
        # Selecionar vilão aleatório (representando o problema/doença)
        villain = random.choice(villains) if villains else None
        
        if hero and villain:
            # Determinar vencedor baseado na efetividade da terapia
            therapy_success = session['effectiveness_score'] >= 8.0
            
            fight_mapping = {
                "session_id": session['session_id'],
                "therapy_type": session['therapy_type'],
                "hero": hero,
                "villain": villain,
                "winner": "hero" if therapy_success else "villain",
                "effectiveness": session['effectiveness_score'],
                "fight_concept": f"Treatment of patient with {session['therapy_type']}",
                "outcome": session['outcome']
            }
            
            fight_mappings.append(fight_mapping)
            
            winner_name = hero.name if therapy_success else villain.name
            print(f"  ⚡ {session['session_id']}: {winner_name} vence (Score: {session['effectiveness_score']})")
    
    return fight_mappings

def sync_therapy_data_advanced(client: BiodeskQuarkusIntegration) -> dict:
    """Sincronização avançada de dados de terapia"""
    
    print("🔄 SINCRONIZAÇÃO AVANÇADA DE DADOS DE TERAPIA")
    print("=" * 60)
    
    sync_results = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "therapy_sessions_generated": 0,
        "heroes_created": 0,
        "fight_mappings": 0,
        "statistics_updated": False,
        "errors": [],
        "success": False
    }
    
    try:
        # 1. Gerar sessões de terapia simuladas
        print("1. 🧪 Gerando sessões de terapia simuladas...")
        therapy_sessions = []
        
        for i in range(5):  # Gerar 5 sessões de exemplo
            session = simulate_therapy_session()
            therapy_sessions.append(session)
            print(f"   📋 Sessão {i+1}: {session['therapy_type']} - Score: {session['effectiveness_score']}")
        
        sync_results["therapy_sessions_generated"] = len(therapy_sessions)
        
        # 2. Obter heróis e vilões existentes
        print(f"\n2. 📚 Obtendo dados existentes do Quarkus...")
        
        existing_heroes = client.get_heroes() or []
        existing_villains = client.get_villains() or []
        
        print(f"   🦸 Heróis existentes: {len(existing_heroes)}")
        print(f"   👹 Vilões existentes: {len(existing_villains)}")
        
        # 3. Criar novos heróis baseados nas terapias (se possível)
        print(f"\n3. ⚡ Integrando dados de terapia...")
        
        if client.is_service_healthy('hero-service'):
            new_heroes = create_therapy_heroes(client, therapy_sessions)
            sync_results["heroes_created"] = len(new_heroes)
            # Combinar heróis existentes com novos
            all_heroes = existing_heroes + new_heroes
        else:
            print("   ⚠️ Hero service indisponível - usando heróis existentes apenas")
            all_heroes = existing_heroes
        
        # 4. Mapear terapias para combates conceituais
        print(f"\n4. 🗺️ Criando mapeamentos conceituais...")
        
        if all_heroes and existing_villains:
            fight_mappings = map_therapy_to_fights(therapy_sessions, all_heroes, existing_villains)
            sync_results["fight_mappings"] = len(fight_mappings)
        else:
            print("   ⚠️ Dados insuficientes para mapeamentos")
            fight_mappings = []
        
        # 5. Atualizar estatísticas (se possível)
        print(f"\n5. 📊 Atualizando estatísticas...")
        
        if client.is_service_healthy('statistics-service'):
            try:
                stats = client.get_fight_statistics()
                if stats:
                    sync_results["statistics_updated"] = True
                    print("   ✅ Estatísticas obtidas e integradas")
                else:
                    print("   ⚠️ Estatísticas não disponíveis")
            except Exception as e:
                sync_results["errors"].append(f"Statistics error: {e}")
                print(f"   ❌ Erro nas estatísticas: {e}")
        else:
            print("   ⚠️ Statistics service indisponível")
        
        # 6. Gerar relatório de sincronização
        print(f"\n6. 📋 Gerando relatório...")
        
        success_criteria = (
            sync_results["therapy_sessions_generated"] > 0 and
            (sync_results["heroes_created"] > 0 or len(existing_heroes) > 0) and
            len(sync_results["errors"]) == 0
        )
        
        sync_results["success"] = success_criteria
        sync_results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Salvar mapeamentos para referência futura
        mappings_file = Path("therapy_quarkus_mappings.json")
        try:
            import json
            
            mappings_data = {
                "sync_results": sync_results,
                "therapy_sessions": therapy_sessions,
                "fight_mappings": [
                    {
                        "session_id": fm["session_id"],
                        "therapy_type": fm["therapy_type"],
                        "hero_name": fm["hero"].name,
                        "villain_name": fm["villain"].name,
                        "winner": fm["winner"],
                        "effectiveness": fm["effectiveness"]
                    } for fm in fight_mappings
                ]
            }
            
            with open(mappings_file, 'w', encoding='utf-8') as f:
                json.dump(mappings_data, f, indent=2, ensure_ascii=False)
            
            print(f"   📄 Mapeamentos salvos em: {mappings_file}")
            
        except Exception as e:
            sync_results["errors"].append(f"File save error: {e}")
        
        return sync_results
        
    except Exception as e:
        sync_results["errors"].append(f"General error: {e}")
        sync_results["success"] = False
        return sync_results

def display_sync_report(sync_results: dict):
    """Exibir relatório detalhado da sincronização"""
    
    print("\n📊 RELATÓRIO DE SINCRONIZAÇÃO")
    print("=" * 60)
    
    # Status geral
    status_icon = "✅" if sync_results["success"] else "❌"
    print(f"{status_icon} Status: {'SUCESSO' if sync_results['success'] else 'FALHA'}")
    
    print(f"⏰ Início: {sync_results['start_time']}")
    if 'end_time' in sync_results:
        print(f"⏰ Fim: {sync_results['end_time']}")
    
    print()
    
    # Métricas
    print("📈 MÉTRICAS:")
    print(f"  🧪 Sessões de terapia geradas: {sync_results['therapy_sessions_generated']}")
    print(f"  🦸 Heróis criados: {sync_results['heroes_created']}")
    print(f"  🗺️ Mapeamentos conceituais: {sync_results['fight_mappings']}")
    print(f"  📊 Estatísticas atualizadas: {'✅' if sync_results['statistics_updated'] else '❌'}")
    
    # Erros
    if sync_results["errors"]:
        print(f"\n⚠️ ERROS ({len(sync_results['errors'])}):")
        for error in sync_results["errors"]:
            print(f"  • {error}")
    else:
        print(f"\n✅ Nenhum erro encontrado")

def monitor_therapy_integration():
    """Monitor contínuo da integração de terapia"""
    
    print("\n🔄 MONITOR DE INTEGRAÇÃO DE TERAPIA")
    print("=" * 60)
    print("Executando sincronização a cada 2 minutos...")
    print("Pressione Ctrl+C para parar\n")
    
    client = BiodeskQuarkusIntegration()
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            
            print(f"🔄 CICLO {cycle_count} - {time.strftime('%H:%M:%S')}")
            print("-" * 40)
            
            # Verificar saúde dos serviços
            health_status = client.check_services_health()
            healthy_services = [name for name, status in health_status.items() if status.healthy]
            
            print(f"🌐 Serviços ativos: {len(healthy_services)}/{len(health_status)}")
            
            if len(healthy_services) >= 2:  # Pelo menos 2 serviços para funcionar
                # Executar sincronização básica
                basic_sync = client.sync_therapy_data()
                
                if basic_sync['success']:
                    print("✅ Sincronização básica: OK")
                    print(f"   Heróis: {basic_sync['heroes_synced']}")
                    print(f"   Vilões: {basic_sync['villains_synced']}")
                    print(f"   Combates: {basic_sync['fights_synced']}")
                else:
                    print("⚠️ Sincronização básica: Problemas")
                
                # A cada 3 ciclos, fazer sincronização avançada
                if cycle_count % 3 == 0:
                    print("\n🔄 Executando sincronização avançada...")
                    advanced_sync = sync_therapy_data_advanced(client)
                    
                    if advanced_sync['success']:
                        print("✅ Sincronização avançada: Concluída")
                    else:
                        print("⚠️ Sincronização avançada: Problemas")
            else:
                print("❌ Serviços insuficientes para sincronização")
            
            print(f"\n⏳ Próximo ciclo em 2 minutos...\n")
            time.sleep(120)  # 2 minutos
            
    except KeyboardInterrupt:
        print("\n👋 Monitor interrompido pelo usuário")
        print(f"Total de ciclos executados: {cycle_count}")

def main():
    """Função principal"""
    
    while True:
        print("\n🧪 SISTEMA DE SINCRONIZAÇÃO DE TERAPIA")
        print("=" * 60)
        print("Escolha uma opção:")
        print("1. 🔄 Executar sincronização avançada única")
        print("2. 🧪 Simular sessões de terapia")
        print("3. 🔍 Monitor contínuo de integração")
        print("4. 📊 Status dos serviços")
        print("5. 🧹 Limpar cache")
        print("0. ❌ Sair")
        
        try:
            choice = input("\nOpção: ").strip()
            
            if choice == '0':
                print("👋 Encerrando sistema de sincronização...")
                break
                
            elif choice == '1':
                client = BiodeskQuarkusIntegration()
                sync_results = sync_therapy_data_advanced(client)
                display_sync_report(sync_results)
                input("\nPressione Enter para continuar...")
                
            elif choice == '2':
                print("\n🧪 SIMULANDO SESSÕES DE TERAPIA")
                print("-" * 40)
                
                num_sessions = int(input("Quantas sessões simular? (1-10): ") or "3")
                num_sessions = max(1, min(10, num_sessions))
                
                for i in range(num_sessions):
                    session = simulate_therapy_session()
                    print(f"\n📋 Sessão {i+1}:")
                    print(f"   ID: {session['session_id']}")
                    print(f"   Paciente: {session['patient_id']}")
                    print(f"   Terapia: {session['therapy_type']}")
                    print(f"   Duração: {session['duration_minutes']} min")
                    print(f"   Efetividade: {session['effectiveness_score']}/10")
                    print(f"   Resultado: {session['outcome']}")
                
                input("\nPressione Enter para continuar...")
                
            elif choice == '3':
                monitor_therapy_integration()
                
            elif choice == '4':
                client = BiodeskQuarkusIntegration()
                print(f"\n🔍 STATUS DOS SERVIÇOS:")
                print("-" * 30)
                
                health_status = client.check_services_health()
                for name, status in health_status.items():
                    icon = "✅" if status.healthy else "❌"
                    print(f"{icon} {name}: {status.response_time_ms}ms")
                
                print(f"\n📊 Resumo da integração:")
                integration_status = client.get_integration_status()
                print(f"Serviços saudáveis: {integration_status['services_healthy']}/{integration_status['services_total']}")
                print(f"Cache ativo: {integration_status['cache_entries']} entradas")
                
                input("\nPressione Enter para continuar...")
                
            elif choice == '5':
                client = BiodeskQuarkusIntegration()
                client.clear_cache()
                print("🧹 Cache limpo!")
                input("\nPressione Enter para continuar...")
                
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            break
        except ValueError as e:
            print(f"❌ Valor inválido: {e}")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()