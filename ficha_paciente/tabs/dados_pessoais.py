"""
Tab de dados pessoais - versão otimizada
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLineEdit, QComboBox, QDateEdit, QPushButton, 
                           QLabel, QGroupBox, QScrollArea)
from PyQt6.QtCore import pyqtSignal, QDate
from ..utils.validators import EmailValidator, PhoneValidator
from ..utils.styles import StyleManager


class DadosPessoaisTab(QWidget):
    """Tab para gestão de dados pessoais do paciente"""
    
    dados_alterados = pyqtSignal(dict)
    
    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data or {}
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        """Configura a interface"""
        layout = QVBoxLayout(self)
        
        # Área com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        content_layout = QVBoxLayout(content_widget)
        
        # Grupos de dados
        content_layout.addWidget(self._create_dados_basicos())
        content_layout.addWidget(self._create_contatos())
        content_layout.addWidget(self._create_dados_fisicos())
        content_layout.addWidget(self._create_informacoes_adicionais())
        content_layout.addStretch()
        
        layout.addWidget(scroll)
    
    def _create_dados_basicos(self) -> QGroupBox:
        """Cria grupo de dados básicos"""
        group = QGroupBox("Dados Básicos")
        layout = QFormLayout()
        
        self.nome_edit = QLineEdit()
        self.nome_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Nome:", self.nome_edit)
        
        self.data_nascimento_edit = QDateEdit()
        self.data_nascimento_edit.setCalendarPopup(True)
        self.data_nascimento_edit.setDisplayFormat("dd/MM/yyyy")
        self.data_nascimento_edit.dateChanged.connect(self._on_data_changed)
        layout.addRow("Data Nascimento:", self.data_nascimento_edit)
        
        self.nif_edit = QLineEdit()
        self.nif_edit.setMaxLength(9)
        self.nif_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("NIF:", self.nif_edit)
        
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["", "Masculino", "Feminino", "Outro"])
        self.genero_combo.currentTextChanged.connect(self._on_data_changed)
        layout.addRow("Género:", self.genero_combo)
        
        group.setLayout(layout)
        StyleManager.apply_group_style(group)
        return group
    
    def _create_contatos(self) -> QGroupBox:
        """Cria grupo de contatos"""
        group = QGroupBox("Contatos")
        layout = QFormLayout()
        
        self.contacto_edit = QLineEdit()
        self.contacto_edit.textChanged.connect(self._validate_phone)
        layout.addRow("Telefone:", self.contacto_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.textChanged.connect(self._validate_email)
        layout.addRow("Email:", self.email_edit)
        
        self.morada_edit = QLineEdit()
        self.morada_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Morada:", self.morada_edit)
        
        group.setLayout(layout)
        StyleManager.apply_group_style(group)
        return group
    
    def _create_dados_fisicos(self) -> QGroupBox:
        """Cria grupo de dados físicos"""
        group = QGroupBox("Dados Físicos")
        layout = QFormLayout()
        
        self.peso_edit = QLineEdit()
        self.peso_edit.setPlaceholderText("kg")
        self.peso_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Peso:", self.peso_edit)
        
        self.altura_edit = QLineEdit()
        self.altura_edit.setPlaceholderText("cm")
        self.altura_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Altura:", self.altura_edit)
        
        group.setLayout(layout)
        StyleManager.apply_group_style(group)
        return group
    
    def _create_informacoes_adicionais(self) -> QGroupBox:
        """Cria grupo de informações adicionais"""
        group = QGroupBox("Informações Adicionais")
        layout = QFormLayout()
        
        self.profissao_edit = QLineEdit()
        self.profissao_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Profissão:", self.profissao_edit)
        
        self.local_combo = QComboBox()
        self.local_combo.addItems(["", "Lisboa", "Porto", "Online"])
        self.local_combo.currentTextChanged.connect(self._on_data_changed)
        layout.addRow("Local Habitual:", self.local_combo)
        
        self.conheceu_combo = QComboBox()
        self.conheceu_combo.addItems(["", "Internet", "Recomendação", "Redes Sociais", "Outro"])
        self.conheceu_combo.currentTextChanged.connect(self._on_data_changed)
        layout.addRow("Como Conheceu:", self.conheceu_combo)
        
        self.referenciado_edit = QLineEdit()
        self.referenciado_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Referenciado por:", self.referenciado_edit)
        
        group.setLayout(layout)
        StyleManager.apply_group_style(group)
        return group
    
    def _load_data(self):
        """Carrega dados do paciente"""
        if not self.paciente_data:
            return
        
        # Dados básicos
        self.nome_edit.setText(self.paciente_data.get('nome', ''))
        
        data_nasc = self.paciente_data.get('data_nascimento', '')
        if data_nasc:
            self.data_nascimento_edit.setDate(QDate.fromString(data_nasc, 'dd/MM/yyyy'))
        
        self.nif_edit.setText(self.paciente_data.get('nif', ''))
        self.genero_combo.setCurrentText(self.paciente_data.get('genero', ''))
        
        # Contatos
        self.contacto_edit.setText(self.paciente_data.get('contacto', ''))
        self.email_edit.setText(self.paciente_data.get('email', ''))
        self.morada_edit.setText(self.paciente_data.get('morada', ''))
        
        # Dados físicos
        self.peso_edit.setText(str(self.paciente_data.get('peso', '')))
        self.altura_edit.setText(str(self.paciente_data.get('altura', '')))
        
        # Informações adicionais
        self.profissao_edit.setText(self.paciente_data.get('profissao', ''))
        self.local_combo.setCurrentText(self.paciente_data.get('local_habitual', ''))
        self.conheceu_combo.setCurrentText(self.paciente_data.get('conheceu', ''))
        self.referenciado_edit.setText(self.paciente_data.get('referenciado', ''))
    
    def get_data(self) -> dict:
        """Retorna dados atuais"""
        return {
            'nome': self.nome_edit.text(),
            'data_nascimento': self.data_nascimento_edit.date().toString('dd/MM/yyyy'),
            'nif': self.nif_edit.text(),
            'genero': self.genero_combo.currentText(),
            'contacto': self.contacto_edit.text(),
            'email': self.email_edit.text(),
            'morada': self.morada_edit.text(),
            'peso': self.peso_edit.text(),
            'altura': self.altura_edit.text(),
            'profissao': self.profissao_edit.text(),
            'local_habitual': self.local_combo.currentText(),
            'conheceu': self.conheceu_combo.currentText(),
            'referenciado': self.referenciado_edit.text()
        }
    
    def update_data(self, paciente_data: dict):
        """Atualiza com novos dados"""
        self.paciente_data = paciente_data
        self._load_data()
    
    def _on_data_changed(self):
        """Emite sinal quando dados mudam"""
        self.dados_alterados.emit(self.get_data())
    
    def _validate_email(self):
        """Valida email"""
        email = self.email_edit.text()
        if email and not EmailValidator.validate(email):
            self.email_edit.setStyleSheet("border: 2px solid red;")
        else:
            self.email_edit.setStyleSheet("")
        self._on_data_changed()
    
    def _validate_phone(self):
        """Valida telefone"""
        phone = self.contacto_edit.text()
        if phone and not PhoneValidator.validate(phone):
            self.contacto_edit.setStyleSheet("border: 2px solid red;")
        else:
            self.contacto_edit.setStyleSheet("")
        self._on_data_changed()
