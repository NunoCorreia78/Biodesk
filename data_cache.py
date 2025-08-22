"""
Biodesk - Cache de Dados Inteligente
===================================

Sistema de cache com TTL automático para melhorar performance
na consulta de dados de pacientes e templates.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta


class DataCache:
    """Cache inteligente com TTL (Time To Live) automático"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Retorna a instância singleton do cache"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._cache: Dict[str, Tuple[Any, float]] = {}  # {key: (value, timestamp)}
            self._ttl_settings: Dict[str, int] = {
                'patient_data': 300,      # 5 minutos
                'templates': 600,         # 10 minutos
                'email_config': 1800,     # 30 minutos
                'iris_analysis': 3600,    # 1 hora
                'user_preferences': 7200, # 2 horas
                'system_config': 86400    # 24 horas
            }
            self._max_size = 1000  # Máximo de entradas no cache
            self._cleanup_interval = 300  # Limpeza a cada 5 minutos
            self._last_cleanup = time.time()
            self._initialized = True
    
    def _get_ttl_for_key(self, key: str) -> int:
        """Determina TTL baseado no tipo de chave"""
        for prefix, ttl in self._ttl_settings.items():
            if key.startswith(prefix):
                return ttl
        return 300  # TTL padrão de 5 minutos
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, (value, timestamp) in self._cache.items():
            ttl = self._get_ttl_for_key(key)
            if current_time - timestamp > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            print(f"🗑️ Cache: Removidas {len(expired_keys)} entradas expiradas")
        
        self._last_cleanup = current_time
    
    def _enforce_size_limit(self):
        """Garante que o cache não excede o tamanho máximo"""
        if len(self._cache) > self._max_size:
            # Remove 20% das entradas mais antigas
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
            remove_count = int(self._max_size * 0.2)
            
            for i in range(remove_count):
                key = sorted_items[i][0]
                del self._cache[key]
            
            print(f"🗑️ Cache: Removidas {remove_count} entradas para manter limite de tamanho")
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache se não expirado"""
        # Limpeza periódica
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
        
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        ttl = self._get_ttl_for_key(key)
        
        if current_time - timestamp > ttl:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Armazena valor no cache com timestamp atual"""
        self._cache[key] = (value, time.time())
        self._enforce_size_limit()
    
    def delete(self, key: str) -> bool:
        """Remove chave específica do cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Remove todas as chaves com determinado prefixo"""
        keys_to_remove = [key for key in self._cache.keys() if key.startswith(prefix)]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        return len(keys_to_remove)
    
    def clear_all(self) -> None:
        """Limpa todo o cache"""
        count = len(self._cache)
        self._cache.clear()
        print(f"🗑️ Cache: Removidas todas as {count} entradas")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        current_time = time.time()
        expired_count = 0
        
        for key, (value, timestamp) in self._cache.items():
            ttl = self._get_ttl_for_key(key)
            if current_time - timestamp > ttl:
                expired_count += 1
        
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired_count,
            'active_entries': len(self._cache) - expired_count,
            'max_size': self._max_size,
            'last_cleanup': datetime.fromtimestamp(self._last_cleanup).strftime('%H:%M:%S'),
            'ttl_settings': self._ttl_settings
        }
    
    def get_patient_data(self, patient_id: int, db_manager=None) -> Optional[Dict]:
        """Cache otimizado para dados de pacientes"""
        key = f"patient_data_{patient_id}"
        cached_data = self.get(key)
        
        if cached_data is not None:
            print(f"📋 Cache: Dados do paciente {patient_id} obtidos do cache")
            return cached_data
        
        # Se não está no cache, buscar na BD
        if db_manager:
            try:
                data = db_manager.obter_paciente(patient_id)
                if data:
                    self.set(key, data)
                    print(f"📋 Cache: Dados do paciente {patient_id} armazenados no cache")
                return data
            except Exception as e:
                print(f"❌ Erro ao buscar dados do paciente: {e}")
                return None
        
        return None
    
    def get_templates_data(self, categoria: str, template_manager=None) -> Optional[list]:
        """Cache otimizado para templates"""
        key = f"templates_{categoria}"
        cached_data = self.get(key)
        
        if cached_data is not None:
            print(f"📝 Cache: Templates da categoria '{categoria}' obtidos do cache")
            return cached_data
        
        # Se não está no cache, buscar do gestor de templates
        if template_manager:
            try:
                data = template_manager.obter_templates_por_categoria(categoria)
                if data:
                    self.set(key, data)
                    print(f"📝 Cache: Templates da categoria '{categoria}' armazenados no cache")
                return data
            except Exception as e:
                print(f"❌ Erro ao buscar templates: {e}")
                return None
        
        return None
    
    def invalidate_patient_data(self, patient_id: int) -> None:
        """Invalida cache de um paciente específico"""
        key = f"patient_data_{patient_id}"
        if self.delete(key):
            print(f"🗑️ Cache: Dados do paciente {patient_id} invalidados")
    
    def invalidate_templates(self, categoria: str = None) -> None:
        """Invalida cache de templates"""
        if categoria:
            key = f"templates_{categoria}"
            if self.delete(key):
                print(f"🗑️ Cache: Templates da categoria '{categoria}' invalidados")
        else:
            count = self.clear_prefix("templates_")
            print(f"🗑️ Cache: {count} categorias de templates invalidadas")


# Singleton global para uso em toda aplicação
cache = DataCache()


def get_cache() -> DataCache:
    """Obtém instância global do cache"""
    return cache
