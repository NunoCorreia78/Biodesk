"""
Tab de irisdiagnose - placeholder para implementação futura
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class IrisdiagnoseTab(QWidget):
    """Tab para análise de íris - placeholder"""

    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data or {}
        self._setup_ui()

    def _setup_ui(self):
        """Configura interface básica"""
        layout = QVBoxLayout(self)
        label = QLabel("👁️ IRISDIAGNOSE\n\nEm desenvolvimento...")
        label.setStyleSheet("font-size: 18px; color: #666; text-align: center;")
        layout.addWidget(label)

    def get_data(self) -> dict:
        """Retorna dados (placeholder)"""
        return {}

    def update_data(self, paciente_data: dict):
        """Atualiza dados (placeholder)"""
        self.paciente_data = paciente_data
