"""
Gerenciador de estado centralizado
Substitui múltiplas flags espalhadas pelo código
"""

from enum import Enum
from typing import Dict, Set


class TabState(Enum):
    NOT_LOADED = 0
    LOADING = 1
    LOADED = 2
    ERROR = 3


class StateManager:
    """Gerencia todo o estado da aplicação"""

    def __init__(self):
        self._dirty = False
        self._tab_states: Dict[int, TabState] = {}
        self._loading_locks: Set[str] = set()

    def is_dirty(self) -> bool:
        """Verifica se há alterações não salvas"""
        return self._dirty

    def set_dirty(self, value: bool):
        """Define estado dirty"""
        self._dirty = value

    def is_tab_loaded(self, index: int) -> bool:
        """Verifica se tab está carregada"""
        return self._tab_states.get(index) == TabState.LOADED

    def mark_tab_loaded(self, index: int):
        """Marca tab como carregada"""
        self._tab_states[index] = TabState.LOADED

    def is_loading(self, key: str) -> bool:
        """Verifica se recurso está sendo carregado"""
        return key in self._loading_locks

    def start_loading(self, key: str) -> bool:
        """Inicia carregamento de recurso"""
        if key in self._loading_locks:
            return False
        self._loading_locks.add(key)
        return True

    def end_loading(self, key: str):
        """Finaliza carregamento de recurso"""
        self._loading_locks.discard(key)
