#!/usr/bin/env python3
"""
Script de Instalação Automatizada do Quarkus Super Heroes para Biodesk
═══════════════════════════════════════════════════════════════════════

Este script automatiza a instalação e configuração da aplicação de demonstração
Quarkus Super Heroes para integração com o sistema Biodesk.

Uso:
    python install_quarkus_heroes.py [--auto-setup] [--docker-mode]
    
Opções:
    --auto-setup    : Instalação automática sem prompts interativos
    --docker-mode   : Usar Docker Compose para execução (recomendado)
    --dev-mode      : Instalar em modo desenvolvimento
    --help          : Mostrar esta ajuda
"""

import os
import sys
import subprocess
import argparse
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configurações
QUARKUS_REPO_URL = "https://github.com/quarkusio/quarkus-super-heroes.git"
REQUIRED_JAVA_VERSION = "11"
REQUIRED_MAVEN_VERSION = "3.8"

# URLs dos serviços após instalação
SERVICES_CONFIG = {
    "hero-service": {"port": 8083, "path": "/api/heroes"},
    "villain-service": {"port": 8084, "path": "/api/villains"}, 
    "fight-service": {"port": 8082, "path": "/api/fights"},
    "statistics-service": {"port": 8085, "path": "/api/statistics"},
    "event-statistics": {"port": 8086, "path": "/"}
}

class QuarkusInstaller:
    """Classe principal para instalação do Quarkus Super Heroes"""
    
    def __init__(self, auto_setup: bool = False, docker_mode: bool = False, dev_mode: bool = False):
        self.auto_setup = auto_setup
        self.docker_mode = docker_mode
        self.dev_mode = dev_mode
        self.base_dir = Path(__file__).parent
        self.quarkus_dir = self.base_dir / "quarkus-super-heroes"
        self.installation_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Logger centralizado"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.installation_log.append(log_entry)
        
    def check_prerequisites(self) -> bool:
        """Verificar pré-requisitos do sistema"""
        self.log("🔍 Verificando pré-requisitos do sistema...")
        
        checks_passed = True
        
        # Verificar Java
        java_version = self.check_java_version()
        if java_version:
            self.log(f"✅ Java detectado: versão {java_version}")
        else:
            self.log("❌ Java não encontrado. Instale Java 11+ para continuar.", "ERROR")
            checks_passed = False
            
        # Verificar Maven (se não usar Docker)
        if not self.docker_mode:
            maven_version = self.check_maven_version()
            if maven_version:
                self.log(f"✅ Maven detectado: versão {maven_version}")
            else:
                self.log("❌ Maven não encontrado. Instale Maven 3.8+ ou use --docker-mode.", "ERROR")
                checks_passed = False
                
        # Verificar Docker (se usar modo Docker)
        if self.docker_mode:
            docker_available = self.check_docker()
            if docker_available:
                self.log("✅ Docker e Docker Compose detectados")
            else:
                self.log("❌ Docker não encontrado. Instale Docker para usar --docker-mode.", "ERROR")
                checks_passed = False
                
        # Verificar Git
        if self.check_git():
            self.log("✅ Git detectado")
        else:
            self.log("❌ Git não encontrado. Instale Git para continuar.", "ERROR")
            checks_passed = False
            
        # Verificar conectividade de rede
        if self.check_network():
            self.log("✅ Conectividade de rede OK")
        else:
            self.log("⚠️ Problemas de rede detectados - pode afetar o download", "WARNING")
            
        return checks_passed
    
    def check_java_version(self) -> Optional[str]:
        """Verificar versão do Java"""
        try:
            result = subprocess.run(
                ["java", "-version"], 
                capture_output=True, 
                text=True, 
                stderr=subprocess.STDOUT
            )
            if result.returncode == 0:
                # Java imprime a versão no stderr
                version_line = result.stderr.split('\n')[0] if result.stderr else result.stdout.split('\n')[0]
                return version_line.split('"')[1] if '"' in version_line else "unknown"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return None
        
    def check_maven_version(self) -> Optional[str]:
        """Verificar versão do Maven"""
        try:
            result = subprocess.run(
                ["mvn", "-version"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return version_line.split()[2] if len(version_line.split()) > 2 else "unknown"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return None
        
    def check_docker(self) -> bool:
        """Verificar Docker e Docker Compose"""
        try:
            # Verificar Docker
            docker_result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True
            )
            if docker_result.returncode != 0:
                return False
                
            # Verificar Docker Compose
            compose_result = subprocess.run(
                ["docker-compose", "--version"], 
                capture_output=True
            )
            return compose_result.returncode == 0
        except FileNotFoundError:
            return False
            
    def check_git(self) -> bool:
        """Verificar Git"""
        try:
            result = subprocess.run(
                ["git", "--version"], 
                capture_output=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
            
    def check_network(self) -> bool:
        """Verificar conectividade de rede"""
        try:
            urllib.request.urlopen("https://github.com", timeout=10)
            return True
        except urllib.error.URLError:
            return False
    
    def clone_repository(self) -> bool:
        """Clonar o repositório Quarkus Super Heroes"""
        self.log("📥 Clonando repositório Quarkus Super Heroes...")
        
        if self.quarkus_dir.exists():
            if not self.auto_setup:
                response = input("Diretório quarkus-super-heroes já existe. Remover e clonar novamente? (s/N): ")
                if response.lower() != 's':
                    self.log("ℹ️ Usando repositório existente")
                    return True
                    
            self.log("🗑️ Removendo diretório existente...")
            import shutil
            shutil.rmtree(self.quarkus_dir)
            
        try:
            result = subprocess.run([
                "git", "clone", QUARKUS_REPO_URL, str(self.quarkus_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Repositório clonado com sucesso")
                return True
            else:
                self.log(f"❌ Erro ao clonar repositório: {result.stderr}", "ERROR")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Erro ao executar git clone: {e}", "ERROR")
            return False
    
    def build_services(self) -> bool:
        """Construir os serviços Quarkus"""
        if self.docker_mode:
            return self.build_with_docker()
        else:
            return self.build_with_maven()
            
    def build_with_maven(self) -> bool:
        """Construir usando Maven diretamente"""
        self.log("🔨 Construindo serviços com Maven...")
        
        try:
            os.chdir(self.quarkus_dir)
            
            # Construir todos os módulos
            build_command = ["./mvnw", "clean", "package"]
            if self.dev_mode:
                build_command.append("-DskipTests")
                
            result = subprocess.run(
                build_command,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log("✅ Build Maven concluído com sucesso")
                return True
            else:
                self.log(f"❌ Erro no build Maven: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro durante build Maven: {e}", "ERROR")
            return False
        finally:
            os.chdir(self.base_dir)
    
    def build_with_docker(self) -> bool:
        """Construir usando Docker Compose"""
        self.log("🐳 Preparando ambiente Docker...")
        
        try:
            os.chdir(self.quarkus_dir)
            
            # Procurar arquivo docker-compose apropriado
            compose_files = [
                "deploy/docker-compose/java11.yml",
                "deploy/docker-compose/java17.yml", 
                "docker-compose.yml"
            ]
            
            compose_file = None
            for cf in compose_files:
                if Path(cf).exists():
                    compose_file = cf
                    break
                    
            if not compose_file:
                self.log("❌ Nenhum arquivo docker-compose encontrado", "ERROR")
                return False
                
            self.log(f"🐳 Usando {compose_file}")
            
            # Baixar imagens e construir
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "build"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Build Docker concluído com sucesso")
                return True
            else:
                self.log(f"❌ Erro no build Docker: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro durante build Docker: {e}", "ERROR")
            return False
        finally:
            os.chdir(self.base_dir)
    
    def create_configuration_files(self) -> bool:
        """Criar arquivos de configuração para integração"""
        self.log("⚙️ Criando arquivos de configuração...")
        
        # Arquivo .env
        env_content = f"""# Configuração Quarkus Super Heroes - Biodesk Integration
# Gerado automaticamente em {time.strftime("%Y-%m-%d %H:%M:%S")}

# URLs dos Serviços Quarkus
QUARKUS_HERO_SERVICE_URL=http://localhost:8083
QUARKUS_VILLAIN_SERVICE_URL=http://localhost:8084
QUARKUS_FIGHT_SERVICE_URL=http://localhost:8082
QUARKUS_STATS_SERVICE_URL=http://localhost:8085
QUARKUS_EVENT_STATS_URL=http://localhost:8086

# Configuração de Integração Biodesk
BIODESK_INTEGRATION_ENABLED=true
BIODESK_LOG_LEVEL=INFO
BIODESK_QUARKUS_TIMEOUT=30
BIODESK_RETRY_ATTEMPTS=3

# Modo de Execução
QUARKUS_DOCKER_MODE={"true" if self.docker_mode else "false"}
QUARKUS_DEV_MODE={"true" if self.dev_mode else "false"}
"""
        
        env_file = self.base_dir / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
            
        # Arquivo de configuração JSON
        config_data = {
            "installation": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mode": "docker" if self.docker_mode else "maven",
                "dev_mode": self.dev_mode,
                "auto_setup": self.auto_setup
            },
            "services": SERVICES_CONFIG,
            "integration": {
                "enabled": True,
                "timeout": 30,
                "retry_attempts": 3,
                "health_check_interval": 60
            }
        }
        
        config_file = self.base_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            
        self.log("✅ Arquivos de configuração criados")
        return True
    
    def start_services(self) -> bool:
        """Iniciar os serviços"""
        if self.docker_mode:
            return self.start_docker_services()
        else:
            self.log("ℹ️ Para iniciar os serviços manualmente:")
            self.log("   cd quarkus-super-heroes")
            self.log("   ./mvnw quarkus:dev (para cada módulo)")
            return True
    
    def start_docker_services(self) -> bool:
        """Iniciar serviços com Docker Compose"""
        self.log("🚀 Iniciando serviços com Docker Compose...")
        
        try:
            os.chdir(self.quarkus_dir)
            
            compose_file = "deploy/docker-compose/java11.yml"
            if not Path(compose_file).exists():
                compose_file = "docker-compose.yml"
                
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Serviços iniciados com sucesso")
                self.log("⏳ Aguardando inicialização...")
                time.sleep(30)  # Dar tempo para os serviços iniciarem
                return True
            else:
                self.log(f"❌ Erro ao iniciar serviços: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao iniciar serviços: {e}", "ERROR")
            return False
        finally:
            os.chdir(self.base_dir)
    
    def verify_installation(self) -> bool:
        """Verificar se a instalação foi bem-sucedida"""
        self.log("🔍 Verificando instalação...")
        
        services_ok = 0
        total_services = len(SERVICES_CONFIG)
        
        for service_name, config in SERVICES_CONFIG.items():
            url = f"http://localhost:{config['port']}{config['path']}"
            if self.check_service_health(url, service_name):
                services_ok += 1
                
        if services_ok == total_services:
            self.log(f"✅ Todos os {total_services} serviços estão funcionando")
            return True
        elif services_ok > 0:
            self.log(f"⚠️ {services_ok}/{total_services} serviços funcionando", "WARNING")
            return True
        else:
            self.log("❌ Nenhum serviço está respondendo", "ERROR")
            return False
    
    def check_service_health(self, url: str, service_name: str) -> bool:
        """Verificar saúde de um serviço específico"""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Biodesk-Quarkus-Installer'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    self.log(f"  ✅ {service_name}: OK")
                    return True
        except Exception:
            pass
            
        self.log(f"  ❌ {service_name}: Não disponível")
        return False
    
    def save_installation_log(self):
        """Salvar log da instalação"""
        log_file = self.base_dir / "installation.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.installation_log))
        self.log(f"📄 Log salvo em: {log_file}")
    
    def run_installation(self) -> bool:
        """Executar o processo completo de instalação"""
        self.log("🚀 Iniciando instalação do Quarkus Super Heroes para Biodesk")
        self.log("=" * 70)
        
        steps = [
            ("Verificação de pré-requisitos", self.check_prerequisites),
            ("Clone do repositório", self.clone_repository),
            ("Build dos serviços", self.build_services),
            ("Criação de configurações", self.create_configuration_files),
        ]
        
        if self.docker_mode:
            steps.append(("Inicialização dos serviços", self.start_services))
            steps.append(("Verificação da instalação", self.verify_installation))
        
        for step_name, step_function in steps:
            self.log(f"\n📋 {step_name}...")
            if not step_function():
                self.log(f"❌ Falha em: {step_name}", "ERROR")
                self.save_installation_log()
                return False
                
        self.log("\n🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        self.log("=" * 70)
        
        # Mostrar informações úteis
        self.show_post_installation_info()
        self.save_installation_log()
        
        return True
    
    def show_post_installation_info(self):
        """Mostrar informações pós-instalação"""
        self.log("\n📋 INFORMAÇÕES DE ACESSO:")
        self.log("-" * 50)
        
        for service_name, config in SERVICES_CONFIG.items():
            url = f"http://localhost:{config['port']}{config['path']}"
            self.log(f"🔗 {service_name}: {url}")
            
        self.log("\n📚 PRÓXIMOS PASSOS:")
        self.log("-" * 50)
        self.log("1. Verificar se todos os serviços estão rodando")
        self.log("2. Executar testes de integração:")
        self.log("   python examples/hero_management_example.py")
        self.log("3. Integrar com Biodesk usando:")
        self.log("   from quarkus_integration.biodesk_quarkus_client import BiodeskQuarkusIntegration")
        
        if self.docker_mode:
            self.log("\n🐳 COMANDOS DOCKER ÚTEIS:")
            self.log("-" * 50)
            self.log("Parar serviços: docker-compose down")
            self.log("Ver logs: docker-compose logs -f")
            self.log("Reiniciar: docker-compose restart")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Instalador do Quarkus Super Heroes para Biodesk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python install_quarkus_heroes.py                    # Instalação interativa
  python install_quarkus_heroes.py --auto-setup      # Instalação automática
  python install_quarkus_heroes.py --docker-mode     # Usar Docker
  python install_quarkus_heroes.py --auto-setup --docker-mode  # Completamente automático
        """
    )
    
    parser.add_argument(
        "--auto-setup", 
        action="store_true", 
        help="Executar instalação automática sem prompts"
    )
    
    parser.add_argument(
        "--docker-mode", 
        action="store_true", 
        help="Usar Docker Compose (recomendado)"
    )
    
    parser.add_argument(
        "--dev-mode", 
        action="store_true", 
        help="Instalar em modo desenvolvimento"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              QUARKUS SUPER HEROES - BIODESK INSTALLER           ║
║                                                                  ║
║  Instalação e configuração automática da aplicação de           ║
║  demonstração Quarkus Super Heroes para integração com Biodesk  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar instalador
    installer = QuarkusInstaller(
        auto_setup=args.auto_setup,
        docker_mode=args.docker_mode,
        dev_mode=args.dev_mode
    )
    
    # Executar instalação
    try:
        success = installer.run_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        installer.log("\n⚠️ Instalação cancelada pelo usuário", "WARNING")
        sys.exit(130)
    except Exception as e:
        installer.log(f"\n❌ Erro inesperado: {e}", "ERROR")
        import traceback
        installer.log(traceback.format_exc(), "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()