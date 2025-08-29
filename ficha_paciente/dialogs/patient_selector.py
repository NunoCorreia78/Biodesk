"""
Diálogo para seleção de pacientes
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                           QListWidgetItem, QPushButton, QLabel, QLineEdit)
from PyQt6.QtCore import Qt


class PatientSelector(QDialog):
    """Diálogo para selecionar paciente"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_patient = None
        self._setup_ui()
        self._load_patients()

    def _setup_ui(self):
        """Configura interface"""
        self.setWindowTitle("Selecionar Paciente")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Campo de busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._filter_patients)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Lista de pacientes
        self.patient_list = QListWidget()
        self.patient_list.itemDoubleClicked.connect(self._on_patient_selected)
        layout.addWidget(self.patient_list)

        # Botões
        buttons_layout = QHBoxLayout()
        self.select_btn = QPushButton("Selecionar")
        self.select_btn.clicked.connect(self._on_select_clicked)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.select_btn)
        buttons_layout.addWidget(self.cancel_btn)
        layout.addLayout(buttons_layout)

    def _load_patients(self):
        """Carrega lista de pacientes"""
        try:
            from db_manager import DBManager
            db = DBManager.get_instance()
            patients = db.obter_todos_pacientes()

            for patient in patients:
                item_text = f"{patient.get('nome', 'Sem nome')} - {patient.get('contacto', 'Sem contacto')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, patient)
                self.patient_list.addItem(item)

        except Exception as e:
            print(f"Erro ao carregar pacientes: {e}")

    def _filter_patients(self, text: str):
        """Filtra pacientes baseado no texto de busca"""
        for i in range(self.patient_list.count()):
            item = self.patient_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_patient_selected(self, item):
        """Quando paciente é selecionado"""
        self.selected_patient = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_select_clicked(self):
        """Botão selecionar clicado"""
        current_item = self.patient_list.currentItem()
        if current_item:
            self.selected_patient = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def get_selected_patient(self):
        """Retorna paciente selecionado"""
        return self.selected_patient
