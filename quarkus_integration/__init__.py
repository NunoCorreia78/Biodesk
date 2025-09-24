"""
Módulo de Integração Quarkus Super Heroes - Biodesk
═══════════════════════════════════════════════════════════════

Módulo completo para integração entre o sistema Biodesk e a aplicação
de demonstração Quarkus Super Heroes.

Componentes principais:
- BiodeskQuarkusIntegration: Cliente principal de integração
- HealthMonitor: Monitor de saúde dos serviços
- Exemplos: Scripts de demonstração e uso
- Instalação automatizada: Script de setup

Uso básico:
    from quarkus_integration import BiodeskQuarkusIntegration
    
    client = BiodeskQuarkusIntegration()
    if client.check_services_health():
        heroes = client.get_heroes()
        stats = client.get_fight_statistics()
"""

from .biodesk_quarkus_client import (
    BiodeskQuarkusIntegration,
    Hero,
    Villain,
    Fight,
    ServiceStatus
)

from .health_monitor import HealthMonitor

__version__ = "1.0.0"
__author__ = "Biodesk Development Team"

__all__ = [
    # Cliente principal
    'BiodeskQuarkusIntegration',
    
    # Modelos de dados
    'Hero',
    'Villain', 
    'Fight',
    'ServiceStatus',
    
    # Monitor de saúde
    'HealthMonitor'
]

# Configurações padrão
DEFAULT_CONFIG = {
    "services": {
        "hero-service": "http://localhost:8083",
        "villain-service": "http://localhost:8084",
        "fight-service": "http://localhost:8082",
        "statistics-service": "http://localhost:8085",
        "event-statistics": "http://localhost:8086"
    },
    "timeouts": {
        "request_timeout": 30,
        "retry_attempts": 3,
        "cache_ttl": 300
    }
}

def create_client(config_file: str = None) -> BiodeskQuarkusIntegration:
    """
    Factory function para criar cliente de integração
    
    Args:
        config_file: Caminho para arquivo de configuração (opcional)
        
    Returns:
        BiodeskQuarkusIntegration: Cliente configurado
    """
    from pathlib import Path
    
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path(__file__).parent / "config.json"
    
    return BiodeskQuarkusIntegration(config_path)

def quick_health_check() -> dict:
    """
    Verificação rápida de saúde dos serviços
    
    Returns:
        dict: Status resumido dos serviços
    """
    client = create_client()
    health_status = client.check_services_health()
    
    healthy_count = sum(1 for status in health_status.values() if status.healthy)
    
    return {
        "healthy_services": healthy_count,
        "total_services": len(health_status),
        "integration_ready": healthy_count >= 3,
        "services": {name: status.healthy for name, status in health_status.items()}
    }

# Metadados do módulo
MODULE_INFO = {
    "name": "quarkus_integration",
    "version": __version__,
    "description": "Integração completa entre Biodesk e Quarkus Super Heroes",
    "dependencies": [
        "urllib3",
        "json",
        "pathlib",
        "asyncio",
        "logging"
    ],
    "services_supported": [
        "hero-service",
        "villain-service", 
        "fight-service",
        "statistics-service",
        "event-statistics"
    ],
    "author": __author__
}