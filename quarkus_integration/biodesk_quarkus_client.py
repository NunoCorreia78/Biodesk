"""
Cliente de Integração Biodesk - Quarkus Super Heroes
═══════════════════════════════════════════════════════════════════

Cliente Python para integração entre o sistema Biodesk e os microserviços
Quarkus Super Heroes, fornecendo uma API unificada para comunicação.

Funcionalidades:
- Conectividade com todos os microserviços Quarkus
- Sistema de health check e monitoramento
- Tratamento de erros e reconexão automática
- Cache de dados para performance
- Logging integrado com Biodesk
"""

import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import urllib.request
import urllib.parse
import urllib.error

# Configurações de serviços
DEFAULT_SERVICES_CONFIG = {
    "hero-service": {
        "url": "http://localhost:8083",
        "endpoints": {
            "list": "/api/heroes",
            "get": "/api/heroes/{id}",
            "create": "/api/heroes",
            "update": "/api/heroes/{id}",
            "delete": "/api/heroes/{id}",
            "random": "/api/heroes/random"
        }
    },
    "villain-service": {
        "url": "http://localhost:8084", 
        "endpoints": {
            "list": "/api/villains",
            "get": "/api/villains/{id}",
            "create": "/api/villains",
            "update": "/api/villains/{id}",
            "delete": "/api/villains/{id}",
            "random": "/api/villains/random"
        }
    },
    "fight-service": {
        "url": "http://localhost:8082",
        "endpoints": {
            "list": "/api/fights",
            "get": "/api/fights/{id}",
            "create": "/api/fights",
            "random": "/api/fights/randomfight"
        }
    },
    "statistics-service": {
        "url": "http://localhost:8085",
        "endpoints": {
            "stats": "/api/statistics",
            "team-stats": "/api/statistics/team"
        }
    },
    "event-statistics": {
        "url": "http://localhost:8086",
        "endpoints": {
            "events": "/",
            "health": "/q/health"
        }
    }
}

@dataclass
class ServiceStatus:
    """Status de um serviço"""
    name: str
    url: str
    healthy: bool
    response_time_ms: int
    last_check: float
    error_message: Optional[str] = None

@dataclass 
class Hero:
    """Modelo de dados para Herói"""
    id: Optional[int] = None
    name: str = ""
    other_name: str = ""
    level: int = 1
    picture: str = ""
    powers: str = ""

@dataclass
class Villain:
    """Modelo de dados para Vilão"""
    id: Optional[int] = None
    name: str = ""
    other_name: str = ""
    level: int = 1
    picture: str = ""
    powers: str = ""

@dataclass
class Fight:
    """Modelo de dados para Combate"""
    id: Optional[int] = None
    fight_date: str = ""
    winner_name: str = ""
    winner_level: int = 0
    winner_picture: str = ""
    loser_name: str = ""
    loser_level: int = 0
    loser_picture: str = ""
    winner_team: str = ""
    loser_team: str = ""

class BiodeskQuarkusIntegration:
    """Cliente principal de integração Biodesk-Quarkus"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Inicializar cliente de integração
        
        Args:
            config_file: Caminho para arquivo de configuração (opcional)
        """
        self.logger = logging.getLogger("BiodeskQuarkusIntegration")
        
        # Carregar configuração
        self.config_file = config_file or Path(__file__).parent / "config.json"
        self.services_config = self._load_config()
        
        # Estado do cliente
        self.services_status: Dict[str, ServiceStatus] = {}
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutos
        self.request_timeout = 30
        self.retry_attempts = 3
        self.retry_delay = 1
        
        # Inicializar monitoramento
        self._initialize_services_status()
        
    def _load_config(self) -> Dict:
        """Carregar configuração dos serviços"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('services', DEFAULT_SERVICES_CONFIG)
            else:
                self.logger.warning(f"Arquivo de configuração não encontrado: {self.config_file}")
                return DEFAULT_SERVICES_CONFIG
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            return DEFAULT_SERVICES_CONFIG
    
    def _initialize_services_status(self):
        """Inicializar status dos serviços"""
        for service_name, config in self.services_config.items():
            self.services_status[service_name] = ServiceStatus(
                name=service_name,
                url=config['url'],
                healthy=False,
                response_time_ms=0,
                last_check=0
            )
    
    def _make_request(self, url: str, method: str = 'GET', data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Tuple[Optional[Dict], bool]:
        """
        Fazer requisição HTTP com tratamento de erros
        
        Returns:
            Tuple[response_data, success]
        """
        if headers is None:
            headers = {'Content-Type': 'application/json', 'User-Agent': 'Biodesk-Integration/1.0'}
        
        for attempt in range(self.retry_attempts):
            try:
                # Preparar requisição
                if data and method in ['POST', 'PUT']:
                    data_bytes = json.dumps(data).encode('utf-8')
                    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
                else:
                    req = urllib.request.Request(url, headers=headers, method=method)
                
                # Executar requisição
                start_time = time.time()
                with urllib.request.urlopen(req, timeout=self.request_timeout) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # Ler resposta
                    response_data = response.read().decode('utf-8')
                    
                    # Parse JSON se possível
                    try:
                        json_data = json.loads(response_data) if response_data else {}
                        return json_data, True
                    except json.JSONDecodeError:
                        return {"raw_response": response_data}, True
                        
            except urllib.error.HTTPError as e:
                self.logger.warning(f"HTTP Error {e.code} para {url} (tentativa {attempt + 1})")
                if attempt == self.retry_attempts - 1:
                    return None, False
                    
            except urllib.error.URLError as e:
                self.logger.warning(f"URL Error para {url}: {e.reason} (tentativa {attempt + 1})")
                if attempt == self.retry_attempts - 1:
                    return None, False
                    
            except Exception as e:
                self.logger.error(f"Erro inesperado para {url}: {e} (tentativa {attempt + 1})")
                if attempt == self.retry_attempts - 1:
                    return None, False
            
            # Aguardar antes de tentar novamente
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return None, False
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Obter dados do cache se válidos"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry.get('timestamp', 0) < self.cache_ttl:
                return entry['data']
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Armazenar dados no cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def check_services_health(self) -> Dict[str, ServiceStatus]:
        """
        Verificar saúde de todos os serviços
        
        Returns:
            Dict com status de cada serviço
        """
        self.logger.info("🔍 Verificando saúde dos serviços Quarkus...")
        
        for service_name, config in self.services_config.items():
            status = self.services_status[service_name]
            
            # URL de health check (usar endpoint específico ou raiz)
            health_url = config['url']
            if 'health' in config.get('endpoints', {}):
                health_url += config['endpoints']['health']
            elif service_name == 'event-statistics':
                health_url += "/"
            else:
                # Para outros serviços, usar o endpoint principal
                endpoints = config.get('endpoints', {})
                if endpoints:
                    health_url += list(endpoints.values())[0]
            
            start_time = time.time()
            _, success = self._make_request(health_url, 'GET')
            response_time = int((time.time() - start_time) * 1000)
            
            # Atualizar status
            status.healthy = success
            status.response_time_ms = response_time
            status.last_check = time.time()
            
            if success:
                status.error_message = None
                self.logger.info(f"  ✅ {service_name}: OK ({response_time}ms)")
            else:
                status.error_message = "Service unavailable"
                self.logger.warning(f"  ❌ {service_name}: FALHA")
        
        return self.services_status
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Verificar se um serviço específico está saudável"""
        if service_name not in self.services_status:
            return False
        
        status = self.services_status[service_name]
        
        # Verificar se precisa atualizar o status
        if time.time() - status.last_check > 60:  # 1 minuto
            self.check_services_health()
        
        return status.healthy
    
    def get_all_healthy_services(self) -> List[str]:
        """Obter lista de serviços saudáveis"""
        self.check_services_health()
        return [name for name, status in self.services_status.items() if status.healthy]
    
    # ═══════════════════════════════════════════════════════════════
    # HEROES SERVICE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_heroes(self, use_cache: bool = True) -> Optional[List[Hero]]:
        """Obter lista de heróis"""
        cache_key = "heroes_list"
        
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return [Hero(**hero) for hero in cached_data]
        
        if not self.is_service_healthy('hero-service'):
            self.logger.error("Hero service não disponível")
            return None
        
        config = self.services_config['hero-service']
        url = config['url'] + config['endpoints']['list']
        
        data, success = self._make_request(url)
        if success and data:
            heroes_data = data if isinstance(data, list) else data.get('heroes', [])
            if use_cache:
                self._set_cache(cache_key, heroes_data)
            return [Hero(**hero) for hero in heroes_data]
        
        return None
    
    def get_hero(self, hero_id: int) -> Optional[Hero]:
        """Obter herói específico por ID"""
        if not self.is_service_healthy('hero-service'):
            self.logger.error("Hero service não disponível")
            return None
        
        config = self.services_config['hero-service']
        url = config['url'] + config['endpoints']['get'].format(id=hero_id)
        
        data, success = self._make_request(url)
        if success and data:
            return Hero(**data)
        
        return None
    
    def get_random_hero(self) -> Optional[Hero]:
        """Obter herói aleatório"""
        if not self.is_service_healthy('hero-service'):
            self.logger.error("Hero service não disponível")
            return None
        
        config = self.services_config['hero-service']
        url = config['url'] + config['endpoints']['random']
        
        data, success = self._make_request(url)
        if success and data:
            return Hero(**data)
        
        return None
    
    def create_hero(self, hero: Hero) -> Optional[Hero]:
        """Criar novo herói"""
        if not self.is_service_healthy('hero-service'):
            self.logger.error("Hero service não disponível")
            return None
        
        config = self.services_config['hero-service']
        url = config['url'] + config['endpoints']['create']
        
        hero_data = asdict(hero)
        if hero_data.get('id') is None:
            del hero_data['id']  # Remove ID para criação
        
        data, success = self._make_request(url, 'POST', hero_data)
        if success and data:
            # Limpar cache
            self._clear_heroes_cache()
            return Hero(**data)
        
        return None
    
    def _clear_heroes_cache(self):
        """Limpar cache de heróis"""
        cache_keys = [k for k in self.cache.keys() if k.startswith('heroes')]
        for key in cache_keys:
            del self.cache[key]
    
    # ═══════════════════════════════════════════════════════════════
    # VILLAINS SERVICE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_villains(self, use_cache: bool = True) -> Optional[List[Villain]]:
        """Obter lista de vilões"""
        cache_key = "villains_list"
        
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return [Villain(**villain) for villain in cached_data]
        
        if not self.is_service_healthy('villain-service'):
            self.logger.error("Villain service não disponível")
            return None
        
        config = self.services_config['villain-service']
        url = config['url'] + config['endpoints']['list']
        
        data, success = self._make_request(url)
        if success and data:
            villains_data = data if isinstance(data, list) else data.get('villains', [])
            if use_cache:
                self._set_cache(cache_key, villains_data)
            return [Villain(**villain) for villain in villains_data]
        
        return None
    
    def get_random_villain(self) -> Optional[Villain]:
        """Obter vilão aleatório"""
        if not self.is_service_healthy('villain-service'):
            self.logger.error("Villain service não disponível")
            return None
        
        config = self.services_config['villain-service']
        url = config['url'] + config['endpoints']['random']
        
        data, success = self._make_request(url)
        if success and data:
            return Villain(**data)
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # FIGHTS SERVICE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_fights(self, use_cache: bool = True) -> Optional[List[Fight]]:
        """Obter lista de combates"""
        cache_key = "fights_list"
        
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return [Fight(**fight) for fight in cached_data]
        
        if not self.is_service_healthy('fight-service'):
            self.logger.error("Fight service não disponível")
            return None
        
        config = self.services_config['fight-service']
        url = config['url'] + config['endpoints']['list']
        
        data, success = self._make_request(url)
        if success and data:
            fights_data = data if isinstance(data, list) else data.get('fights', [])
            if use_cache:
                self._set_cache(cache_key, fights_data)
            return [Fight(**fight) for fight in fights_data]
        
        return None
    
    def create_random_fight(self) -> Optional[Fight]:
        """Criar combate aleatório"""
        if not self.is_service_healthy('fight-service'):
            self.logger.error("Fight service não disponível")
            return None
        
        config = self.services_config['fight-service']
        url = config['url'] + config['endpoints']['random']
        
        data, success = self._make_request(url, 'POST')
        if success and data:
            # Limpar cache de fights
            self._clear_fights_cache()
            return Fight(**data)
        
        return None
    
    def _clear_fights_cache(self):
        """Limpar cache de combates"""
        cache_keys = [k for k in self.cache.keys() if k.startswith('fights')]
        for key in cache_keys:
            del self.cache[key]
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTICS SERVICE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_fight_statistics(self) -> Optional[Dict]:
        """Obter estatísticas de combates"""
        cache_key = "fight_statistics"
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        if not self.is_service_healthy('statistics-service'):
            self.logger.error("Statistics service não disponível")
            return None
        
        config = self.services_config['statistics-service']
        url = config['url'] + config['endpoints']['stats']
        
        data, success = self._make_request(url)
        if success and data:
            self._set_cache(cache_key, data)
            return data
        
        return None
    
    def get_team_statistics(self) -> Optional[Dict]:
        """Obter estatísticas por equipe"""
        cache_key = "team_statistics"
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        if not self.is_service_healthy('statistics-service'):
            self.logger.error("Statistics service não disponível")
            return None
        
        config = self.services_config['statistics-service']
        url = config['url'] + config['endpoints']['team-stats']
        
        data, success = self._make_request(url)
        if success and data:
            self._set_cache(cache_key, data)
            return data
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def clear_cache(self):
        """Limpar todo o cache"""
        self.cache.clear()
        self.logger.info("Cache limpo")
    
    def get_integration_status(self) -> Dict:
        """Obter status completo da integração"""
        healthy_services = self.get_all_healthy_services()
        
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "services_total": len(self.services_config),
            "services_healthy": len(healthy_services),
            "services_status": {name: status.healthy for name, status in self.services_status.items()},
            "cache_entries": len(self.cache),
            "integration_healthy": len(healthy_services) >= 3  # Pelo menos 3 serviços funcionando
        }
    
    def sync_therapy_data(self) -> Dict:
        """
        Sincronizar dados de terapia com sistema Quarkus
        
        Este método pode ser usado para integrar dados da terapia quântica
        do Biodesk com os sistemas de estatísticas do Quarkus
        """
        self.logger.info("🔄 Sincronizando dados de terapia...")
        
        sync_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "heroes_synced": 0,
            "villains_synced": 0,
            "fights_synced": 0,
            "statistics_updated": False,
            "success": False
        }
        
        try:
            # Obter dados dos serviços
            heroes = self.get_heroes()
            villains = self.get_villains()
            fights = self.get_fights()
            stats = self.get_fight_statistics()
            
            if heroes:
                sync_result["heroes_synced"] = len(heroes)
            
            if villains:
                sync_result["villains_synced"] = len(villains)
                
            if fights:
                sync_result["fights_synced"] = len(fights)
                
            if stats:
                sync_result["statistics_updated"] = True
            
            # Se conseguiu obter pelo menos alguns dados
            if any([heroes, villains, fights, stats]):
                sync_result["success"] = True
                self.logger.info("✅ Sincronização concluída com sucesso")
            else:
                self.logger.warning("⚠️ Nenhum dado foi sincronizado")
                
        except Exception as e:
            self.logger.error(f"❌ Erro durante sincronização: {e}")
            sync_result["error"] = str(e)
        
        return sync_result
    
    def __str__(self):
        return f"BiodeskQuarkusIntegration(services={len(self.services_config)}, healthy={len(self.get_all_healthy_services())})"


# ═══════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════

def main():
    """Exemplo de uso do cliente de integração"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 TESTE DE INTEGRAÇÃO BIODESK-QUARKUS")
    print("=" * 50)
    
    # Inicializar cliente
    client = BiodeskQuarkusIntegration()
    
    # Verificar saúde dos serviços
    print("\n🔍 Verificando serviços...")
    health_status = client.check_services_health()
    
    for name, status in health_status.items():
        status_icon = "✅" if status.healthy else "❌"
        print(f"{status_icon} {name}: {status.response_time_ms}ms")
    
    # Testar funcionalidades se serviços estão saudáveis
    healthy_services = client.get_all_healthy_services()
    if len(healthy_services) >= 2:
        print(f"\n🎯 Testando funcionalidades ({len(healthy_services)} serviços ativos)...")
        
        # Testar heróis
        if 'hero-service' in healthy_services:
            heroes = client.get_heroes()
            if heroes:
                print(f"📋 Encontrados {len(heroes)} heróis")
                
                random_hero = client.get_random_hero()
                if random_hero:
                    print(f"🦸 Herói aleatório: {random_hero.name} (Nível {random_hero.level})")
        
        # Testar vilões
        if 'villain-service' in healthy_services:
            villains = client.get_villains()
            if villains:
                print(f"👹 Encontrados {len(villains)} vilões")
        
        # Testar estatísticas
        if 'statistics-service' in healthy_services:
            stats = client.get_fight_statistics()
            if stats:
                print("📊 Estatísticas obtidas com sucesso")
        
        # Sincronizar dados
        print("\n🔄 Testando sincronização...")
        sync_result = client.sync_therapy_data()
        if sync_result['success']:
            print("✅ Sincronização bem-sucedida")
        
    else:
        print("⚠️ Poucos serviços disponíveis para testes completos")
    
    # Status final
    print(f"\n📋 STATUS FINAL:")
    integration_status = client.get_integration_status()
    print(f"Serviços saudáveis: {integration_status['services_healthy']}/{integration_status['services_total']}")
    print(f"Integração funcional: {'✅' if integration_status['integration_healthy'] else '❌'}")
    

if __name__ == "__main__":
    main()