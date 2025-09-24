"""
Exemplo de Gestão de Heróis - Integração Biodesk-Quarkus
═══════════════════════════════════════════════════════════════

Este exemplo demonstra como usar o cliente de integração para
gerenciar heróis no sistema Quarkus Super Heroes através do Biodesk.
"""

import sys
import os
from pathlib import Path

# Adicionar diretório pai ao path para importar o cliente
sys.path.append(str(Path(__file__).parent.parent))

from biodesk_quarkus_client import BiodeskQuarkusIntegration, Hero
import logging

def demo_hero_management():
    """Demonstração da gestão de heróis"""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    print("🦸 DEMO: GESTÃO DE HERÓIS - BIODESK + QUARKUS")
    print("=" * 60)
    
    # Inicializar cliente
    client = BiodeskQuarkusIntegration()
    
    # Verificar se o hero service está disponível
    if not client.is_service_healthy('hero-service'):
        print("❌ Hero Service não está disponível")
        print("   Certifique-se de que os serviços Quarkus estão rodando:")
        print("   docker-compose up -d")
        return False
    
    print("✅ Hero Service conectado\n")
    
    # 1. Listar heróis existentes
    print("📋 1. LISTANDO HERÓIS EXISTENTES")
    print("-" * 40)
    
    heroes = client.get_heroes()
    if heroes:
        print(f"Encontrados {len(heroes)} heróis:")
        for i, hero in enumerate(heroes[:5], 1):  # Mostrar apenas os primeiros 5
            print(f"  {i}. {hero.name} (Nível {hero.level}) - {hero.other_name}")
        
        if len(heroes) > 5:
            print(f"  ... e mais {len(heroes) - 5} heróis")
    else:
        print("  Nenhum herói encontrado")
    
    print()
    
    # 2. Obter herói aleatório
    print("🎲 2. HERÓI ALEATÓRIO")
    print("-" * 40)
    
    random_hero = client.get_random_hero()
    if random_hero:
        print(f"🦸 Nome: {random_hero.name}")
        print(f"👤 Outro nome: {random_hero.other_name}")
        print(f"⭐ Nível: {random_hero.level}")
        print(f"⚡ Poderes: {random_hero.powers}")
        if random_hero.picture:
            print(f"🖼️ Imagem: {random_hero.picture}")
    else:
        print("  Não foi possível obter herói aleatório")
    
    print()
    
    # 3. Criar novo herói (exemplo)
    print("➕ 3. CRIANDO NOVO HERÓI (EXEMPLO)")
    print("-" * 40)
    
    # Criar herói de exemplo inspirado na terapia quântica
    new_hero = Hero(
        name="Quantum Healer",
        other_name="Dr. Biodesk",
        level=50,
        powers="Quantum resonance, biofield healing, frequency therapy",
        picture="https://example.com/quantum-healer.jpg"
    )
    
    print(f"🔨 Criando herói: {new_hero.name}")
    print(f"   Outros nomes: {new_hero.other_name}")
    print(f"   Nível: {new_hero.level}")
    print(f"   Poderes: {new_hero.powers}")
    
    # Tentar criar o herói
    created_hero = client.create_hero(new_hero)
    if created_hero:
        print(f"✅ Herói criado com ID: {created_hero.id}")
        print(f"   Nome: {created_hero.name}")
        print(f"   Nível: {created_hero.level}")
    else:
        print("❌ Não foi possível criar o herói")
        print("   (Isso é normal se o serviço estiver rodando em modo read-only)")
    
    print()
    
    # 4. Buscar herói específico
    print("🔍 4. BUSCANDO HERÓI ESPECÍFICO")
    print("-" * 40)
    
    if heroes and len(heroes) > 0:
        first_hero_id = heroes[0].id
        specific_hero = client.get_hero(first_hero_id)
        
        if specific_hero:
            print(f"🦸 Herói encontrado (ID {first_hero_id}):")
            print(f"   Nome: {specific_hero.name}")
            print(f"   Outros nomes: {specific_hero.other_name}")
            print(f"   Nível: {specific_hero.level}")
            print(f"   Poderes: {specific_hero.powers}")
        else:
            print(f"❌ Não foi possível encontrar herói com ID {first_hero_id}")
    else:
        print("  Nenhum herói disponível para busca")
    
    print()
    
    # 5. Estatísticas
    print("📊 5. ESTATÍSTICAS DE INTEGRAÇÃO")
    print("-" * 40)
    
    integration_status = client.get_integration_status()
    print(f"Serviços saudáveis: {integration_status['services_healthy']}/{integration_status['services_total']}")
    print(f"Entradas no cache: {integration_status['cache_entries']}")
    print(f"Integração funcional: {'✅' if integration_status['integration_healthy'] else '❌'}")
    
    # Status específico do hero service
    hero_service_status = client.services_status.get('hero-service')
    if hero_service_status:
        print(f"Hero Service - Tempo de resposta: {hero_service_status.response_time_ms}ms")
        print(f"Hero Service - Última verificação: {hero_service_status.last_check}")
    
    print("\n🎉 DEMO CONCLUÍDA!")
    return True

def interactive_hero_explorer():
    """Explorador interativo de heróis"""
    
    print("\n🔧 MODO INTERATIVO - EXPLORADOR DE HERÓIS")
    print("=" * 60)
    
    client = BiodeskQuarkusIntegration()
    
    if not client.is_service_healthy('hero-service'):
        print("❌ Hero Service não disponível para modo interativo")
        return
    
    while True:
        print("\nOpções disponíveis:")
        print("1. Listar todos os heróis")
        print("2. Herói aleatório")
        print("3. Buscar herói por ID")
        print("4. Status dos serviços")
        print("5. Limpar cache")
        print("0. Sair")
        
        try:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '0':
                print("👋 Encerrando explorador...")
                break
                
            elif choice == '1':
                heroes = client.get_heroes()
                if heroes:
                    print(f"\n📋 {len(heroes)} heróis encontrados:")
                    for hero in heroes:
                        print(f"  ID {hero.id}: {hero.name} (Lv.{hero.level})")
                else:
                    print("❌ Nenhum herói encontrado")
                    
            elif choice == '2':
                hero = client.get_random_hero()
                if hero:
                    print(f"\n🎲 Herói Aleatório:")
                    print(f"  ID: {hero.id}")
                    print(f"  Nome: {hero.name}")
                    print(f"  Outros nomes: {hero.other_name}")
                    print(f"  Nível: {hero.level}")
                    print(f"  Poderes: {hero.powers}")
                else:
                    print("❌ Não foi possível obter herói aleatório")
                    
            elif choice == '3':
                try:
                    hero_id = int(input("Digite o ID do herói: "))
                    hero = client.get_hero(hero_id)
                    if hero:
                        print(f"\n🦸 Herói encontrado:")
                        print(f"  ID: {hero.id}")
                        print(f"  Nome: {hero.name}")
                        print(f"  Outros nomes: {hero.other_name}")
                        print(f"  Nível: {hero.level}")
                        print(f"  Poderes: {hero.powers}")
                    else:
                        print(f"❌ Herói com ID {hero_id} não encontrado")
                except ValueError:
                    print("❌ Por favor digite um número válido")
                    
            elif choice == '4':
                status = client.check_services_health()
                print(f"\n📊 Status dos Serviços:")
                for name, service_status in status.items():
                    icon = "✅" if service_status.healthy else "❌"
                    print(f"  {icon} {name}: {service_status.response_time_ms}ms")
                    
            elif choice == '5':
                client.clear_cache()
                print("🧹 Cache limpo!")
                
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    print("🚀 INICIANDO DEMO DE GESTÃO DE HERÓIS")
    
    # Executar demo básica
    success = demo_hero_management()
    
    if success:
        # Perguntar se quer modo interativo
        try:
            response = input("\nDeseja usar o modo interativo? (s/N): ").lower()
            if response == 's':
                interactive_hero_explorer()
        except KeyboardInterrupt:
            print("\n👋 Até logo!")

if __name__ == "__main__":
    main()