"""
Exemplo de Integração de Estatísticas - Biodesk + Quarkus
═══════════════════════════════════════════════════════════════

Este exemplo demonstra como integrar o sistema de estatísticas
do Quarkus Super Heroes com o dashboard do Biodesk.
"""

import sys
import os
import time
import json
from pathlib import Path

# Adicionar diretório pai ao path para importar o cliente
sys.path.append(str(Path(__file__).parent.parent))

from biodesk_quarkus_client import BiodeskQuarkusIntegration
import logging

def display_statistics_dashboard():
    """Exibir dashboard de estatísticas"""
    
    print("📊 DASHBOARD DE ESTATÍSTICAS - BIODESK + QUARKUS")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.WARNING)  # Reduzir verbosidade para o dashboard
    
    # Inicializar cliente
    client = BiodeskQuarkusIntegration()
    
    # Verificar serviços necessários
    required_services = ['statistics-service', 'hero-service', 'villain-service', 'fight-service']
    available_services = []
    
    print("🔍 Verificando disponibilidade dos serviços...")
    health_status = client.check_services_health()
    
    for service in required_services:
        if service in health_status and health_status[service].healthy:
            available_services.append(service)
            print(f"  ✅ {service}: Disponível")
        else:
            print(f"  ❌ {service}: Indisponível")
    
    if not available_services:
        print("\n❌ Nenhum serviço disponível para estatísticas")
        print("   Execute 'docker-compose up -d' no diretório quarkus-super-heroes")
        return False
    
    print(f"\n📈 Gerando dashboard com {len(available_services)} serviços...\n")
    
    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 1: ESTATÍSTICAS GERAIS
    # ═══════════════════════════════════════════════════════════════
    
    print("📋 ESTATÍSTICAS GERAIS")
    print("-" * 40)
    
    try:
        # Contadores básicos
        heroes_count = 0
        villains_count = 0
        fights_count = 0
        
        if 'hero-service' in available_services:
            heroes = client.get_heroes()
            heroes_count = len(heroes) if heroes else 0
            print(f"🦸 Heróis cadastrados: {heroes_count}")
        
        if 'villain-service' in available_services:
            villains = client.get_villains()
            villains_count = len(villains) if villains else 0
            print(f"👹 Vilões cadastrados: {villains_count}")
        
        if 'fight-service' in available_services:
            fights = client.get_fights()
            fights_count = len(fights) if fights else 0
            print(f"⚔️ Combates realizados: {fights_count}")
        
        print(f"🎯 Total de entidades: {heroes_count + villains_count + fights_count}")
        
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas gerais: {e}")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 2: ESTATÍSTICAS DE COMBATE
    # ═══════════════════════════════════════════════════════════════
    
    if 'statistics-service' in available_services:
        print("⚔️ ESTATÍSTICAS DE COMBATE")
        print("-" * 40)
        
        try:
            fight_stats = client.get_fight_statistics()
            
            if fight_stats:
                # Exibir estatísticas de combate
                if isinstance(fight_stats, dict):
                    for key, value in fight_stats.items():
                        if isinstance(value, (int, float)):
                            print(f"📊 {key.replace('_', ' ').title()}: {value}")
                        elif isinstance(value, str):
                            print(f"📝 {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"📊 Estatísticas obtidas: {type(fight_stats)}")
                
                # Estatísticas por equipe
                team_stats = client.get_team_statistics()
                if team_stats:
                    print("\n🏆 ESTATÍSTICAS POR EQUIPE:")
                    if isinstance(team_stats, dict):
                        for team, stats in team_stats.items():
                            print(f"  🔹 {team}: {stats}")
                    
            else:
                print("❌ Não foi possível obter estatísticas de combate")
                
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas de combate: {e}")
        
        print()
    
    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 3: ANÁLISE DE HERÓIS
    # ═══════════════════════════════════════════════════════════════
    
    if 'hero-service' in available_services:
        print("🦸 ANÁLISE DE HERÓIS")
        print("-" * 40)
        
        try:
            heroes = client.get_heroes()
            
            if heroes and len(heroes) > 0:
                # Análise de níveis
                levels = [hero.level for hero in heroes if hero.level]
                if levels:
                    avg_level = sum(levels) / len(levels)
                    max_level = max(levels)
                    min_level = min(levels)
                    
                    print(f"📈 Nível médio: {avg_level:.1f}")
                    print(f"⭐ Nível máximo: {max_level}")
                    print(f"🔻 Nível mínimo: {min_level}")
                
                # Top 3 heróis por nível
                heroes_by_level = sorted(heroes, key=lambda h: h.level or 0, reverse=True)
                print(f"\n🏆 TOP 3 HERÓIS POR NÍVEL:")
                for i, hero in enumerate(heroes_by_level[:3], 1):
                    print(f"  {i}. {hero.name} (Nível {hero.level})")
                
                # Análise de poderes
                all_powers = []
                for hero in heroes:
                    if hero.powers:
                        powers = [p.strip() for p in hero.powers.split(',')]
                        all_powers.extend(powers)
                
                if all_powers:
                    # Contar poderes mais comuns
                    power_count = {}
                    for power in all_powers:
                        power_lower = power.lower()
                        power_count[power_lower] = power_count.get(power_lower, 0) + 1
                    
                    # Top 3 poderes
                    top_powers = sorted(power_count.items(), key=lambda x: x[1], reverse=True)[:3]
                    print(f"\n⚡ PODERES MAIS COMUNS:")
                    for power, count in top_powers:
                        print(f"  • {power.title()}: {count} herói(s)")
                
            else:
                print("❌ Nenhum herói disponível para análise")
                
        except Exception as e:
            print(f"❌ Erro na análise de heróis: {e}")
        
        print()
    
    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 4: ANÁLISE DE PERFORMANCE DO SISTEMA
    # ═══════════════════════════════════════════════════════════════
    
    print("🔧 PERFORMANCE DO SISTEMA")
    print("-" * 40)
    
    try:
        # Status de integração
        integration_status = client.get_integration_status()
        
        print(f"🌐 Serviços conectados: {integration_status['services_healthy']}/{integration_status['services_total']}")
        print(f"💾 Entradas no cache: {integration_status['cache_entries']}")
        print(f"✅ Sistema funcional: {'Sim' if integration_status['integration_healthy'] else 'Não'}")
        
        # Tempo de resposta dos serviços
        print(f"\n⏱️ TEMPOS DE RESPOSTA:")
        for service_name, status in client.services_status.items():
            if status.healthy:
                response_time = status.response_time_ms
                if response_time < 100:
                    icon = "🟢"
                elif response_time < 500:
                    icon = "🟡"
                else:
                    icon = "🔴"
                print(f"  {icon} {service_name}: {response_time}ms")
        
    except Exception as e:
        print(f"❌ Erro na análise de performance: {e}")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 5: SIMULAÇÃO DE SINCRONIZAÇÃO
    # ═══════════════════════════════════════════════════════════════
    
    print("🔄 SINCRONIZAÇÃO COM BIODESK")
    print("-" * 40)
    
    try:
        # Simular sincronização
        sync_result = client.sync_therapy_data()
        
        if sync_result['success']:
            print("✅ Sincronização bem-sucedida!")
            print(f"🦸 Heróis sincronizados: {sync_result['heroes_synced']}")
            print(f"👹 Vilões sincronizados: {sync_result['villains_synced']}")
            print(f"⚔️ Combates sincronizados: {sync_result['fights_synced']}")
            print(f"📊 Estatísticas atualizadas: {'Sim' if sync_result['statistics_updated'] else 'Não'}")
        else:
            print("⚠️ Sincronização parcial ou com problemas")
            if 'error' in sync_result:
                print(f"Erro: {sync_result['error']}")
    
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
    
    print("\n" + "=" * 60)
    print("📊 DASHBOARD ATUALIZADO EM:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("🔄 Para atualizar, execute este script novamente")
    
    return True

def continuous_monitoring():
    """Monitor contínuo das estatísticas"""
    
    print("\n🔄 MODO DE MONITORAMENTO CONTÍNUO")
    print("=" * 60)
    print("Pressione Ctrl+C para parar\n")
    
    client = BiodeskQuarkusIntegration()
    update_interval = 30  # segundos
    
    try:
        while True:
            print(f"\n📊 Atualização: {time.strftime('%H:%M:%S')}")
            print("-" * 30)
            
            # Status rápido
            health_status = client.check_services_health()
            healthy_count = sum(1 for status in health_status.values() if status.healthy)
            
            print(f"🌐 Serviços ativos: {healthy_count}/{len(health_status)}")
            
            # Estatísticas rápidas se disponível
            if client.is_service_healthy('statistics-service'):
                try:
                    stats = client.get_fight_statistics()
                    if stats:
                        print("📈 Estatísticas: OK")
                    else:
                        print("📈 Estatísticas: Sem dados")
                except:
                    print("📈 Estatísticas: Erro")
            
            # Cache info
            print(f"💾 Cache: {len(client.cache)} entradas")
            
            print(f"⏳ Próxima atualização em {update_interval}s...")
            
            time.sleep(update_interval)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoramento interrompido pelo usuário")

def export_statistics_json():
    """Exportar estatísticas para JSON"""
    
    print("\n💾 EXPORTANDO ESTATÍSTICAS PARA JSON")
    print("-" * 40)
    
    client = BiodeskQuarkusIntegration()
    
    # Coletar todos os dados disponíveis
    export_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "integration_status": client.get_integration_status(),
        "services_health": {},
        "heroes": [],
        "villains": [],
        "fights": [],
        "statistics": {},
        "team_statistics": {}
    }
    
    # Status dos serviços
    health_status = client.check_services_health()
    for name, status in health_status.items():
        export_data["services_health"][name] = {
            "healthy": status.healthy,
            "response_time_ms": status.response_time_ms,
            "last_check": status.last_check,
            "url": status.url
        }
    
    # Dados dos serviços
    try:
        if client.is_service_healthy('hero-service'):
            heroes = client.get_heroes()
            if heroes:
                export_data["heroes"] = [
                    {
                        "id": h.id,
                        "name": h.name,
                        "other_name": h.other_name,
                        "level": h.level,
                        "powers": h.powers
                    } for h in heroes
                ]
        
        if client.is_service_healthy('villain-service'):
            villains = client.get_villains()
            if villains:
                export_data["villains"] = [
                    {
                        "id": v.id,
                        "name": v.name,
                        "other_name": v.other_name,
                        "level": v.level,
                        "powers": v.powers
                    } for v in villains
                ]
        
        if client.is_service_healthy('fight-service'):
            fights = client.get_fights()
            if fights:
                export_data["fights"] = [
                    {
                        "id": f.id,
                        "fight_date": f.fight_date,
                        "winner_name": f.winner_name,
                        "winner_level": f.winner_level,
                        "loser_name": f.loser_name,
                        "loser_level": f.loser_level,
                        "winner_team": f.winner_team,
                        "loser_team": f.loser_team
                    } for f in fights
                ]
        
        if client.is_service_healthy('statistics-service'):
            stats = client.get_fight_statistics()
            if stats:
                export_data["statistics"] = stats
                
            team_stats = client.get_team_statistics()
            if team_stats:
                export_data["team_statistics"] = team_stats
    
    except Exception as e:
        print(f"⚠️ Erro ao coletar alguns dados: {e}")
    
    # Salvar JSON
    output_file = Path("biodesk_quarkus_statistics.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Estatísticas exportadas para: {output_file}")
        print(f"📊 Total de heróis: {len(export_data['heroes'])}")
        print(f"👹 Total de vilões: {len(export_data['villains'])}")
        print(f"⚔️ Total de combates: {len(export_data['fights'])}")
        print(f"🌐 Serviços saudáveis: {sum(1 for s in export_data['services_health'].values() if s['healthy'])}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")

def main():
    """Função principal"""
    
    while True:
        print("\n📊 SISTEMA DE ESTATÍSTICAS - BIODESK + QUARKUS")
        print("=" * 60)
        print("Escolha uma opção:")
        print("1. 📋 Dashboard completo de estatísticas")
        print("2. 🔄 Monitoramento contínuo")
        print("3. 💾 Exportar estatísticas para JSON")
        print("4. 🔍 Status dos serviços")
        print("0. ❌ Sair")
        
        try:
            choice = input("\nOpção: ").strip()
            
            if choice == '0':
                print("👋 Encerrando sistema de estatísticas...")
                break
                
            elif choice == '1':
                display_statistics_dashboard()
                input("\nPressione Enter para continuar...")
                
            elif choice == '2':
                continuous_monitoring()
                
            elif choice == '3':
                export_statistics_json()
                input("\nPressione Enter para continuar...")
                
            elif choice == '4':
                client = BiodeskQuarkusIntegration()
                health_status = client.check_services_health()
                
                print(f"\n🔍 STATUS DOS SERVIÇOS:")
                print("-" * 30)
                for name, status in health_status.items():
                    icon = "✅" if status.healthy else "❌"
                    print(f"{icon} {name}")
                    print(f"   URL: {status.url}")
                    print(f"   Resposta: {status.response_time_ms}ms")
                    if not status.healthy and status.error_message:
                        print(f"   Erro: {status.error_message}")
                    print()
                
                input("Pressione Enter para continuar...")
                
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()