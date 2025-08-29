"""
Gerenciador centralizado de tabs
Implementa lazy loading real e gerenciamento de memória
"""

from typing import Dict, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class TabManager:
    """Gerencia todas as tabs da aplicação"""

    def __init__(self, parent):
        self.parent = parent
        self.loaded_tabs: Dict[int, QWidget] = {}

    def load_tab(self, index: int, container: QWidget, paciente_data: dict):
        """Carrega uma tab específica sob demanda"""
        if index in self.loaded_tabs:
            return self.loaded_tabs[index]

        # Criar layout se não existir
        if not container.layout():
            container.setLayout(QVBoxLayout())

        # Carregar tab apropriada
        tab_widget = self._create_tab_widget(index, paciente_data)
        if tab_widget:
            container.layout().addWidget(tab_widget)
            self.loaded_tabs[index] = tab_widget

        return tab_widget

    def _create_tab_widget(self, index: int, paciente_data: dict) -> Optional[QWidget]:
        """Cria widget da tab baseado no índice"""
        tab_mapping = {
            0: self._create_dados_pessoais,
            1: self._create_historico,
            2: self._create_irisdiagnose,
            3: self._create_comunicacao
        }

        creator = tab_mapping.get(index)
        if creator:
            return creator(paciente_data)
        return None

    def _create_dados_pessoais(self, paciente_data: dict) -> QWidget:
        """Cria tab de dados pessoais"""
        from ..tabs.dados_pessoais import DadosPessoaisTab
        return DadosPessoaisTab(paciente_data, self.parent)

    def _create_historico(self, paciente_data: dict) -> QWidget:
        """Cria tab de histórico"""
        from ..tabs.historico import HistoricoTab
        return HistoricoTab(paciente_data, self.parent)

    def _create_irisdiagnose(self, paciente_data: dict) -> QWidget:
        """Cria tab de irisdiagnose"""
        from ..tabs.irisdiagnose import IrisdiagnoseTab
        return IrisdiagnoseTab(paciente_data, self.parent)

    def _create_comunicacao(self, paciente_data: dict) -> QWidget:
        """Cria tab de comunicação"""
        from ..tabs.comunicacao import ComunicacaoTab
        return ComunicacaoTab(paciente_data, self.parent)

    def update_all_tabs(self, paciente_data: dict):
        """Atualiza todas as tabs carregadas com novos dados"""
        for tab in self.loaded_tabs.values():
            if hasattr(tab, 'update_data'):
                tab.update_data(paciente_data)

    def collect_all_data(self) -> dict:
        """Coleta dados de todas as tabs"""
        data = {}
        for tab in self.loaded_tabs.values():
            if hasattr(tab, 'get_data'):
                data.update(tab.get_data())
        return data

    def print_current_tab(self, index: int):
        """Imprime tab atual"""
        if index in self.loaded_tabs:
            tab = self.loaded_tabs[index]
            if hasattr(tab, 'print'):
                tab.print()

    def refresh_tab(self, index: int):
        """Atualiza tab específica"""
        if index in self.loaded_tabs:
            tab = self.loaded_tabs[index]
            if hasattr(tab, 'refresh'):
                tab.refresh()

    def cleanup(self):
        """Limpa recursos de todas as tabs"""
        for tab in self.loaded_tabs.values():
            if hasattr(tab, 'cleanup'):
                tab.cleanup()
        self.loaded_tabs.clear()
