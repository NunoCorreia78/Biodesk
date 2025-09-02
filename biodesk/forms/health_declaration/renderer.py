"""
Renderizador de Formulários de Saúde - Biodesk
═══════════════════════════════════════════════════════════════════════

Sistema de renderização dinâmica de formulários baseado em especificação JSON.
Suporta todos os tipos de campo e lógica condicional (show_if).
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QDateEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QFrame, QScrollArea,
    QSlider, QProgressBar, QMessageBox, QFileDialog,
    QTabWidget, QSplitter, QStackedWidget
)
from PyQt6.QtCore import (
    Qt, QDate, QRegularExpression, pyqtSignal,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QPen, QColor,
    QRegularExpressionValidator, QIntValidator, QDoubleValidator
)


class SignatureWidget(QWidget):
    """Widget para captura de assinatura digital"""
    
    signature_changed = pyqtSignal()
    
    def __init__(self, width: int = 400, height: int = 150):
        super().__init__()
        self.setFixedSize(width, height)
        self.setStyleSheet("""
            SignatureWidget {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
        """)
        
        self.signature_points = []
        self.drawing = False
        self.last_point = None
        
    def mousePressEvent(self, event):
        """Iniciar desenho da assinatura"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.position().toPoint()
            self.signature_points.append([])  # Nova linha
    
    def mouseMoveEvent(self, event):
        """Continuar desenho da assinatura"""
        if self.drawing and self.last_point:
            current_point = event.position().toPoint()
            self.signature_points[-1].append((self.last_point, current_point))
            self.last_point = current_point
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Terminar desenho da assinatura"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.signature_changed.emit()
    
    def paintEvent(self, event):
        """Desenhar assinatura"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        
        for line in self.signature_points:
            for start_point, end_point in line:
                painter.drawLine(start_point, end_point)
        
        # Desenhar instrução se vazio
        if not self.signature_points:
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            font = QFont()
            font.setItalic(True)
            painter.setFont(font)
            painter.drawText(
                self.rect(), 
                Qt.AlignmentFlag.AlignCenter,
                "Clique e arraste para assinar"
            )
    
    def clear_signature(self):
        """Limpar assinatura"""
        self.signature_points.clear()
        self.update()
        self.signature_changed.emit()
    
    def has_signature(self) -> bool:
        """Verificar se tem assinatura"""
        return len(self.signature_points) > 0
    
    def get_signature_data(self) -> List[List]:
        """Obter dados da assinatura para serialização"""
        return self.signature_points.copy()
    
    def set_signature_data(self, data: List[List]):
        """Definir dados da assinatura"""
        self.signature_points = data
        self.update()


class RatingWidget(QWidget):
    """Widget para avaliação por escala (0-10)"""
    
    value_changed = pyqtSignal(int)
    
    def __init__(self, min_value: int = 0, max_value: int = 10, labels: Dict[str, str] = None):
        super().__init__()
        self.min_value = min_value
        self.max_value = max_value
        self.labels = labels or {}
        self.current_value = min_value
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interface"""
        layout = QVBoxLayout(self)
        
        # Slider principal
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(self.min_value, self.max_value)
        self.slider.setValue(self.min_value)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.slider)
        
        # Labels de escala
        labels_layout = QHBoxLayout()
        
        for value in range(self.min_value, self.max_value + 1):
            if str(value) in self.labels:
                label_text = f"{value}\n{self.labels[str(value)]}"
            else:
                label_text = str(value)
            
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 10px;")
            labels_layout.addWidget(label)
        
        layout.addLayout(labels_layout)
        
        # Display do valor atual
        self.value_label = QLabel(f"Valor selecionado: {self.min_value}")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-weight: bold; margin: 10px;")
        layout.addWidget(self.value_label)
    
    def _on_value_changed(self, value: int):
        """Valor do slider mudou"""
        self.current_value = value
        self.value_label.setText(f"Valor selecionado: {value}")
        self.value_changed.emit(value)
    
    def get_value(self) -> int:
        """Obter valor atual"""
        return self.current_value
    
    def set_value(self, value: int):
        """Definir valor"""
        if self.min_value <= value <= self.max_value:
            self.slider.setValue(value)


class FieldRenderer:
    """Renderizador de campos individuais"""
    
    def __init__(self):
        self.logger = logging.getLogger("FieldRenderer")
    
    def create_field_widget(self, field_spec: Dict[str, Any]) -> QWidget:
        """
        Criar widget para um campo baseado na especificação
        
        Args:
            field_spec: Especificação do campo
            
        Returns:
            Widget renderizado
        """
        field_type = field_spec.get('type', 'text')
        
        if field_type == 'text':
            return self._create_text_field(field_spec)
        elif field_type == 'textarea':
            return self._create_textarea_field(field_spec)
        elif field_type == 'date':
            return self._create_date_field(field_spec)
        elif field_type == 'number':
            return self._create_number_field(field_spec)
        elif field_type == 'checkbox':
            return self._create_checkbox_field(field_spec)
        elif field_type == 'checkbox_group':
            return self._create_checkbox_group_field(field_spec)
        elif field_type == 'radio':
            return self._create_radio_field(field_spec)
        elif field_type == 'select':
            return self._create_select_field(field_spec)
        elif field_type == 'multiselect':
            return self._create_multiselect_field(field_spec)
        elif field_type == 'signature':
            return self._create_signature_field(field_spec)
        elif field_type == 'file':
            return self._create_file_field(field_spec)
        elif field_type == 'rating':
            return self._create_rating_field(field_spec)
        else:
            self.logger.warning(f"Tipo de campo desconhecido: {field_type}")
            return self._create_text_field(field_spec)  # Fallback
    
    def _create_text_field(self, spec: Dict) -> QLineEdit:
        """Criar campo de texto"""
        widget = QLineEdit()
        
        # Placeholder
        if 'placeholder' in spec:
            widget.setPlaceholderText(spec['placeholder'])
        
        # Comprimento máximo
        if 'maxLength' in spec:
            widget.setMaxLength(spec['maxLength'])
        
        # Padrão de validação
        if 'pattern' in spec:
            regex = QRegularExpression(spec['pattern'])
            validator = QRegularExpressionValidator(regex)
            widget.setValidator(validator)
        
        return widget
    
    def _create_textarea_field(self, spec: Dict) -> QTextEdit:
        """Criar campo de texto multilinha"""
        widget = QTextEdit()
        widget.setMaximumHeight(100)  # Altura limitada
        
        # Placeholder
        if 'placeholder' in spec:
            widget.setPlaceholderText(spec['placeholder'])
        
        return widget
    
    def _create_date_field(self, spec: Dict) -> QDateEdit:
        """Criar campo de data"""
        widget = QDateEdit()
        widget.setDate(QDate.currentDate())
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("dd/MM/yyyy")
        
        return widget
    
    def _create_number_field(self, spec: Dict) -> QSpinBox:
        """Criar campo numérico"""
        if spec.get('decimal', False):
            widget = QDoubleSpinBox()
        else:
            widget = QSpinBox()
        
        # Limites
        if 'min' in spec:
            widget.setMinimum(spec['min'])
        if 'max' in spec:
            widget.setMaximum(spec['max'])
        
        return widget
    
    def _create_checkbox_field(self, spec: Dict) -> QWidget:
        """Criar campo checkbox (pode ter múltiplas opções)"""
        if 'options' in spec and isinstance(spec['options'], list):
            # Múltiplas checkboxes
            container = QWidget()
            layout = QVBoxLayout(container)
            
            for option in spec['options']:
                checkbox = QCheckBox(option)
                layout.addWidget(checkbox)
            
            return container
        else:
            # Checkbox simples
            label = spec.get('label', 'Aceito')
            return QCheckBox(label)
    
    def _create_checkbox_group_field(self, spec: Dict) -> QGroupBox:
        """Criar grupo de checkboxes"""
        group = QGroupBox()
        layout = QVBoxLayout(group)
        
        options = spec.get('options', [])
        for option in options:
            if isinstance(option, dict):
                checkbox = QCheckBox(option['label'])
                checkbox.setProperty('value', option['value'])
            else:
                checkbox = QCheckBox(str(option))
                checkbox.setProperty('value', str(option))
            
            layout.addWidget(checkbox)
        
        return group
    
    def _create_radio_field(self, spec: Dict) -> QGroupBox:
        """Criar grupo de radio buttons"""
        group = QGroupBox()
        layout = QVBoxLayout(group)
        
        button_group = QButtonGroup(group)
        
        options = spec.get('options', [])
        for option in options:
            if isinstance(option, dict):
                radio = QRadioButton(option['label'])
                radio.setProperty('value', option['value'])
            else:
                radio = QRadioButton(str(option))
                radio.setProperty('value', str(option))
            
            button_group.addButton(radio)
            layout.addWidget(radio)
        
        return group
    
    def _create_select_field(self, spec: Dict) -> QComboBox:
        """Criar campo de seleção"""
        widget = QComboBox()
        
        options = spec.get('options', [])
        for option in options:
            if isinstance(option, dict):
                widget.addItem(option['label'], option['value'])
            else:
                widget.addItem(str(option), str(option))
        
        return widget
    
    def _create_multiselect_field(self, spec: Dict) -> QGroupBox:
        """Criar campo de seleção múltipla (similar a checkbox_group)"""
        return self._create_checkbox_group_field(spec)
    
    def _create_signature_field(self, spec: Dict) -> QWidget:
        """Criar campo de assinatura"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Instruções
        if 'instructions' in spec:
            instructions = QLabel(spec['instructions'])
            instructions.setStyleSheet("font-style: italic; color: #666;")
            layout.addWidget(instructions)
        
        # Widget de assinatura
        signature_widget = SignatureWidget()
        layout.addWidget(signature_widget)
        
        # Botão para limpar
        clear_btn = QPushButton("🗑️ Limpar Assinatura")
        clear_btn.clicked.connect(signature_widget.clear_signature)
        layout.addWidget(clear_btn)
        
        return container
    
    def _create_file_field(self, spec: Dict) -> QWidget:
        """Criar campo de arquivo"""
        container = QWidget()
        layout = QHBoxLayout(container)
        
        # Campo de texto mostrando arquivo selecionado
        file_display = QLineEdit()
        file_display.setReadOnly(True)
        file_display.setPlaceholderText("Nenhum arquivo selecionado")
        layout.addWidget(file_display)
        
        # Botão para selecionar arquivo
        select_btn = QPushButton("📁 Selecionar Arquivo")
        
        def select_file():
            file_path, _ = QFileDialog.getOpenFileName(
                container, "Selecionar Arquivo",
                "", "Todos os Arquivos (*.*)"
            )
            if file_path:
                file_display.setText(file_path)
        
        select_btn.clicked.connect(select_file)
        layout.addWidget(select_btn)
        
        return container
    
    def _create_rating_field(self, spec: Dict) -> RatingWidget:
        """Criar campo de avaliação"""
        min_val = spec.get('min', 0)
        max_val = spec.get('max', 10)
        labels = spec.get('labels', {})
        
        return RatingWidget(min_val, max_val, labels)


class FormValidator:
    """Validador de formulários"""
    
    def __init__(self, form_spec: Dict):
        self.form_spec = form_spec
        self.logger = logging.getLogger("FormValidator")
    
    def validate_form(self, form_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validar dados do formulário
        
        Args:
            form_data: Dados preenchidos
            
        Returns:
            Dict com erros por campo
        """
        errors = {}
        
        # Validar campos obrigatórios
        self._validate_required_fields(form_data, errors)
        
        # Validar contraindicações críticas
        self._validate_critical_contraindications(form_data, errors)
        
        # Validar consentimento final
        self._validate_final_consent(form_data, errors)
        
        return errors
    
    def _validate_required_fields(self, form_data: Dict, errors: Dict):
        """Validar campos obrigatórios"""
        for section in self.form_spec['form_spec']['sections']:
            for field in section['fields']:
                field_id = field['id']
                
                if field.get('required', False):
                    # Verificar se campo está visível (show_if)
                    if self._is_field_visible(field, form_data):
                        if field_id not in form_data or not form_data[field_id]:
                            if field_id not in errors:
                                errors[field_id] = []
                            errors[field_id].append("Campo obrigatório")
    
    def _validate_critical_contraindications(self, form_data: Dict, errors: Dict):
        """Validar contraindicações críticas"""
        validation_rules = self.form_spec['form_spec'].get('validation_rules', {})
        critical_rules = validation_rules.get('critical_contraindications', {})
        
        blocking_values = critical_rules.get('blocking_values', {})
        
        for field_id, values in blocking_values.items():
            if field_id in form_data:
                field_value = form_data[field_id]
                
                # Verificar se valor atual é bloqueante
                if isinstance(field_value, list):
                    # Para checkbox groups
                    if any(val in values for val in field_value):
                        if field_id not in errors:
                            errors[field_id] = []
                        errors[field_id].append("CONTRAINDICAÇÃO ABSOLUTA: Este tratamento não é seguro para o seu caso")
                else:
                    # Para campos únicos
                    if field_value in values:
                        if field_id not in errors:
                            errors[field_id] = []
                        errors[field_id].append("CONTRAINDICAÇÃO ABSOLUTA: Este tratamento não é seguro para o seu caso")
    
    def _validate_final_consent(self, form_data: Dict, errors: Dict):
        """Validar consentimento final obrigatório"""
        validation_rules = self.form_spec['form_spec'].get('validation_rules', {})
        required_consent = validation_rules.get('required_final_consent', [])
        
        for field_id in required_consent:
            if field_id not in form_data or not form_data[field_id]:
                if field_id not in errors:
                    errors[field_id] = []
                errors[field_id].append("CONSENTIMENTO OBRIGATÓRIO: Deve aceitar todos os termos para prosseguir")
    
    def _is_field_visible(self, field: Dict, form_data: Dict) -> bool:
        """Verificar se campo está visível baseado em show_if"""
        show_if = field.get('show_if')
        if not show_if:
            return True
        
        condition_field = show_if.get('field')
        condition_value = show_if.get('value')
        
        if condition_field in form_data:
            return form_data[condition_field] == condition_value
        
        return False
    
    def has_critical_contraindications(self, form_data: Dict[str, Any]) -> bool:
        """Verificar se há contraindicações que impedem o tratamento"""
        errors = self.validate_form(form_data)
        
        validation_rules = self.form_spec['form_spec'].get('validation_rules', {})
        critical_fields = validation_rules.get('critical_contraindications', {}).get('fields', [])
        
        for field_id in critical_fields:
            if field_id in errors:
                for error in errors[field_id]:
                    if "CONTRAINDICAÇÃO ABSOLUTA" in error:
                        return True
        
        return False


class HealthDeclarationRenderer(QWidget):
    """Renderizador principal da declaração de saúde"""
    
    form_completed = pyqtSignal(dict)  # form_data
    form_validated = pyqtSignal(bool)  # is_valid
    
    def __init__(self, form_spec_path: Path):
        super().__init__()
        self.logger = logging.getLogger("HealthDeclarationRenderer")
        
        # Carregar especificação do formulário
        with open(form_spec_path, 'r', encoding='utf-8') as f:
            self.form_spec = json.load(f)
        
        self.field_renderer = FieldRenderer()
        self.validator = FormValidator(self.form_spec)
        
        # Estado do formulário
        self.field_widgets = {}  # field_id -> widget
        self.current_data = {}
        
        self.setup_ui()
        self.setup_validation()
    
    def setup_ui(self):
        """Configurar interface principal"""
        self.setWindowTitle(self.form_spec['form_spec']['title'])
        self.resize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Área de scroll para o formulário
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget do formulário
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # Renderizar seções
        for section in self.form_spec['form_spec']['sections']:
            section_widget = self._create_section(section)
            form_layout.addWidget(section_widget)
        
        form_layout.addStretch()
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)
        
        # Rodapé com botões
        footer = self._create_footer()
        main_layout.addWidget(footer)
        
        # Aplicar estilos
        self._apply_styles()
    
    def _create_header(self) -> QWidget:
        """Criar cabeçalho do formulário"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout(header)
        
        # Título
        title = QLabel(self.form_spec['form_spec']['title'])
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title)
        
        # Descrição
        description = QLabel(self.form_spec['form_spec']['description'])
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; margin: 5px;")
        layout.addWidget(description)
        
        # Aviso legal
        legal_text = self.form_spec['form_spec']['legal_text']['disclaimer']
        disclaimer = QLabel(f"⚠️ {legal_text}")
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 10px;")
        layout.addWidget(disclaimer)
        
        return header
    
    def _create_section(self, section_spec: Dict) -> QGroupBox:
        """Criar seção do formulário"""
        section = QGroupBox(section_spec['title'])
        section.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(section)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        for field_spec in section_spec['fields']:
            field_widget = self._create_field(field_spec)
            
            # Adicionar ao layout
            label_text = field_spec['label']
            if field_spec.get('required', False):
                label_text += " *"
            
            label = QLabel(label_text)
            if field_spec.get('style') == 'critical':
                label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            layout.addRow(label, field_widget)
            
            # Armazenar referência
            self.field_widgets[field_spec['id']] = field_widget
        
        return section
    
    def _create_field(self, field_spec: Dict) -> QWidget:
        """Criar widget para um campo"""
        widget = self.field_renderer.create_field_widget(field_spec)
        
        # Configurar visibilidade condicional
        if 'show_if' in field_spec:
            widget.setVisible(False)  # Inicialmente oculto
        
        return widget
    
    def _create_footer(self) -> QWidget:
        """Criar rodapé com botões"""
        footer = QWidget()
        layout = QHBoxLayout(footer)
        
        # Status de validação
        self.validation_status = QLabel("❌ Formulário incompleto")
        self.validation_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(self.validation_status)
        
        layout.addStretch()
        
        # Botões
        self.preview_btn = QPushButton("👀 Pré-visualizar")
        self.preview_btn.clicked.connect(self._preview_form)
        layout.addWidget(self.preview_btn)
        
        self.submit_btn = QPushButton("✅ Submeter Declaração")
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._submit_form)
        self.submit_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.submit_btn)
        
        return footer
    
    def setup_validation(self):
        """Configurar validação em tempo real"""
        # TODO: Conectar sinais de mudança dos widgets para validação automática
        pass
    
    def _apply_styles(self):
        """Aplicar estilos ao formulário"""
        self.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                margin: 10px 0px;
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
                margin: 2px;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
            QCheckBox, QRadioButton {
                margin: 5px;
            }
        """)
    
    def _preview_form(self):
        """Pré-visualizar formulário preenchido"""
        form_data = self._collect_form_data()
        errors = self.validator.validate_form(form_data)
        
        preview_text = "DECLARAÇÃO DE ESTADO DE SAÚDE\n"
        preview_text += "=" * 50 + "\n\n"
        
        for section in self.form_spec['form_spec']['sections']:
            preview_text += f"{section['title'].upper()}\n"
            preview_text += "-" * len(section['title']) + "\n"
            
            for field in section['fields']:
                field_id = field['id']
                if field_id in form_data and form_data[field_id]:
                    preview_text += f"{field['label']}: {form_data[field_id]}\n"
            
            preview_text += "\n"
        
        if errors:
            preview_text += "\nERROS ENCONTRADOS:\n"
            preview_text += "-" * 20 + "\n"
            for field_id, field_errors in errors.items():
                preview_text += f"- {field_id}: {', '.join(field_errors)}\n"
        
        # Mostrar em janela separada
        msg = QMessageBox(self)
        msg.setWindowTitle("Pré-visualização da Declaração")
        msg.setText(preview_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def _submit_form(self):
        """Submeter formulário"""
        form_data = self._collect_form_data()
        errors = self.validator.validate_form(form_data)
        
        if errors:
            # Mostrar erros
            error_text = "Formulário contém erros:\n\n"
            for field_id, field_errors in errors.items():
                error_text += f"• {field_id}: {', '.join(field_errors)}\n"
            
            QMessageBox.warning(self, "Formulário Inválido", error_text)
            return
        
        # Verificar contraindicações críticas
        if self.validator.has_critical_contraindications(form_data):
            QMessageBox.critical(
                self, "Contraindicação Absoluta",
                "ATENÇÃO: Foram identificadas contraindicações absolutas.\n\n"
                "Por razões de segurança, este tratamento NÃO pode ser realizado.\n\n"
                "Consulte o seu médico para alternativas terapêuticas."
            )
            return
        
        # Adicionar timestamp e metadados
        form_data['_metadata'] = {
            'submission_time': datetime.now().isoformat(),
            'form_version': self.form_spec['form_spec']['version'],
            'validation_passed': True,
            'ip_address': 'localhost',  # TODO: Obter IP real se necessário
            'user_agent': 'Biodesk Quantum Therapy'
        }
        
        self.form_completed.emit(form_data)
        
        QMessageBox.information(
            self, "Declaração Submetida",
            "✅ Declaração de estado de saúde submetida com sucesso!\n\n"
            "O tratamento pode prosseguir de acordo com os protocolos estabelecidos."
        )
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Coletar dados preenchidos no formulário"""
        data = {}
        
        # TODO: Implementar coleta real dos dados dos widgets
        # Por agora, dados de exemplo
        data = {
            'nome_completo': 'João Silva',
            'data_nascimento': '1980-01-01',
            'contacto_telefone': '+351 912345678',
            'doencas_cronicas': ['nenhuma'],
            'dispositivos_implantados': ['nenhum'],
            'sintomas_atuais': ['nenhum'],
            'decl_confirmo': True
        }
        
        return data


# ═══════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Criar aplicação
    app = QApplication(sys.argv)
    
    # Caminho para especificação do formulário
    form_spec_path = Path(__file__).parent / "form_spec.json"
    
    if not form_spec_path.exists():
        print("❌ Arquivo form_spec.json não encontrado")
        sys.exit(1)
    
    # Criar e mostrar formulário
    form_renderer = HealthDeclarationRenderer(form_spec_path)
    
    def on_form_completed(form_data):
        print("✅ Formulário completado:")
        for key, value in form_data.items():
            print(f"   {key}: {value}")
    
    form_renderer.form_completed.connect(on_form_completed)
    form_renderer.show()
    
    # Executar aplicação
    sys.exit(app.exec())
