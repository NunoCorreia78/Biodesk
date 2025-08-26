"""
📅 FOLLOW-UP DIALOG - BIODESK
============================

Dialog para configurar follow-ups automáticos.
Extraído do monolito ficha_paciente.py para melhor organização.

Autor: Biodesk Team
Data: 25/08/2025
"""

from datetime import datetime, timedelta, time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QRadioButton, QButtonGroup, QDateEdit, QTimeEdit, QPushButton,
    QApplication
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont
from ..core.button_manager import ButtonManager

class FollowUpDialog(QDialog):
    """Dialog para configurar follow-ups automáticos."""
    
    def __init__(self, paciente_data, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("📅 Agendar Follow-up Automático")
        self.setFixedSize(500, 650)  # Tamanho fixo maior para evitar cortes
        self.setModal(True)
        
        # Centralizar a janela mais alta no ecrã
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 500) // 2
        y = max(50, (screen.height() - 700) // 2)  # Mínimo 50px do topo
        self.move(x, y)
        
        # Estilo geral do dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info do paciente
        info_label = QLabel(f"📋 Paciente: {self.paciente_data.get('nome', 'N/A')}")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: bold; 
                color: #2c3e50; 
                background-color: #ffffff;
                padding: 10px;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout.addWidget(info_label)
        
        # Tipo de follow-up
        tipo_label = QLabel("Tipo de Follow-up:")
        tipo_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057; margin-top: 5px;")
        layout.addWidget(tipo_label)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
                color: #212529;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
                margin-right: 5px;
            }
        """)
        
        # Adicionar itens individualmente com dados associados
        self.combo_tipo.addItem("📧 Follow-up Padrão", "padrao")
        self.combo_tipo.addItem("🆕 Primeira Consulta", "primeira_consulta")
        self.combo_tipo.addItem("💊 Acompanhamento de Tratamento", "tratamento")
        self.combo_tipo.addItem("📊 Evolução e Resultados", "resultado")
        
        self.combo_tipo.setCurrentIndex(0)
        layout.addWidget(self.combo_tipo)
        
        # Quando enviar - opções predefinidas
        quando_label = QLabel("Quando enviar:")
        quando_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057; margin-top: 15px;")
        layout.addWidget(quando_label)
        
        self.radio_group = QButtonGroup()
        self.radio_3_dias = QRadioButton("📅 Em 3 dias")
        self.radio_7_dias = QRadioButton("📅 Em 1 semana")
        self.radio_14_dias = QRadioButton("📅 Em 2 semanas")
        self.radio_custom = QRadioButton("🗓️ Data/hora personalizada")
        
        # Estilo dos radio buttons
        radio_style = """
            QRadioButton {
                font-size: 13px;
                color: #495057;
                padding: 5px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #6c757d;
                border-radius: 9px;
                background-color: #ffffff;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #007bff;
                border-radius: 9px;
                background-color: #007bff;
            }
            QRadioButton::indicator:checked::after {
                content: "";
                width: 6px;
                height: 6px;
                border-radius: 3px;
                background-color: #ffffff;
                margin: 4px;
            }
        """
        
        self.radio_3_dias.setStyleSheet(radio_style)
        self.radio_7_dias.setStyleSheet(radio_style)
        self.radio_14_dias.setStyleSheet(radio_style)
        self.radio_custom.setStyleSheet(radio_style)
        
        self.radio_3_dias.setChecked(True)  # Default
        
        self.radio_group.addButton(self.radio_3_dias, 0)
        self.radio_group.addButton(self.radio_7_dias, 1)
        self.radio_group.addButton(self.radio_14_dias, 2)
        self.radio_group.addButton(self.radio_custom, 3)
        
        layout.addWidget(self.radio_3_dias)
        layout.addWidget(self.radio_7_dias)
        layout.addWidget(self.radio_14_dias)
        layout.addWidget(self.radio_custom)
        
        # Data/hora personalizada
        custom_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate().addDays(3))
        self.time_edit = QTimeEdit(QTime(10, 0))  # 10:00 por default
        
        # Estilo para date/time edits
        datetime_style = """
            QDateEdit, QTimeEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                background-color: #ffffff;
                color: #212529;
                min-height: 18px;
            }
            QDateEdit:focus, QTimeEdit:focus {
                border-color: #007bff;
            }
            QDateEdit:disabled, QTimeEdit:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """
        
        self.date_edit.setStyleSheet(datetime_style)
        self.time_edit.setStyleSheet(datetime_style)
        self.date_edit.setEnabled(False)
        self.time_edit.setEnabled(False)
        
        data_label = QLabel("Data:")
        data_label.setStyleSheet("font-size: 13px; color: #495057; font-weight: 500;")
        hora_label = QLabel("Hora:")
        hora_label.setStyleSheet("font-size: 13px; color: #495057; font-weight: 500;")
        
        custom_layout.addWidget(data_label)
        custom_layout.addWidget(self.date_edit)
        custom_layout.addWidget(hora_label)
        custom_layout.addWidget(self.time_edit)
        layout.addLayout(custom_layout)
        
        # Conectar radio button para habilitar/desabilitar campos
        self.radio_custom.toggled.connect(self._toggle_custom_datetime)
        
        # Preview
        preview_label = QLabel("👀 Preview do agendamento:")
        preview_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057; margin-top: 15px;")
        layout.addWidget(preview_label)
        
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', monospace;
                font-size: 12px;
                color: #495057;
                line-height: 1.4;
            }
        """)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        # Conectar sinais para atualizar preview
        self.combo_tipo.currentTextChanged.connect(self._update_preview)
        self.radio_group.buttonClicked.connect(self._update_preview)
        self.date_edit.dateChanged.connect(self._update_preview)
        self.time_edit.timeChanged.connect(self._update_preview)
        
        # Botões usando ButtonManager
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Criar botões usando o ButtonManager centralizado
        buttons = ButtonManager.create_dialog_buttons(self)
        btn_cancelar = buttons['cancelar']
        btn_agendar = ButtonManager.create_button(
            text="✅ Agendar Follow-up",
            button_type='primary',
            tooltip="Agendar o follow-up",
            parent=self
        )
        
        btn_cancelar.clicked.connect(self.reject)
        btn_agendar.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_agendar)
        layout.addLayout(btn_layout)
        
        # Atualizar preview inicial
        self._update_preview()
        
    def _toggle_custom_datetime(self, checked):
        """Habilita/desabilita campos de data/hora personalizada."""
        self.date_edit.setEnabled(checked)
        self.time_edit.setEnabled(checked)
        
    def _update_preview(self):
        """Atualiza o preview do agendamento."""
        tipo = self.combo_tipo.currentData() or "padrao"
        
        # Calcular quando será enviado
        if self.radio_3_dias.isChecked():
            quando = datetime.now() + timedelta(days=3)
            dias_apos = 3
        elif self.radio_7_dias.isChecked():
            quando = datetime.now() + timedelta(days=7)
            dias_apos = 7
        elif self.radio_14_dias.isChecked():
            quando = datetime.now() + timedelta(days=14)
            dias_apos = 14
        else:  # custom
            date = self.date_edit.date().toPyDate()
            time = self.time_edit.time().toPyTime()
            quando = datetime.combine(date, time)
            hoje = datetime.now().date()
            dias_apos = (date - hoje).days
            
        # Simular ajuste para horário comercial se não for personalizado
        when_adjusted = quando
        is_custom = self.radio_custom.isChecked()
        
        if not is_custom:
            when_adjusted = self._simulate_business_hours_adjust(quando)
            
        if is_custom:
            preview_text = f"""📧 Tipo: {tipo.replace('_', ' ').title()}
📅 Enviar em: {quando.strftime('%d/%m/%Y às %H:%M')}
⚡ Horário: PERSONALIZADO (mantém hora exata)
⏱️ Daqui a: {dias_apos} dia(s)
📋 Para: {self.paciente_data.get('email', 'Email não definido')}
🌐 Sistema: Retry automático se sem internet"""
        else:
            preview_text = f"""📧 Tipo: {tipo.replace('_', ' ').title()}
📅 Enviar em: {when_adjusted.strftime('%d/%m/%Y às %H:%M')}
⏰ Horário: Entre 11h-17h (horário comercial)
⏱️ Daqui a: {dias_apos} dia(s)
📋 Para: {self.paciente_data.get('email', 'Email não definido')}
🌐 Sistema: Retry automático se sem internet"""
        
        self.preview_label.setText(preview_text)
        
    def _simulate_business_hours_adjust(self, when_dt):
        """Simula o ajuste para horário comercial no preview."""
        import random
        from datetime import time
        target_date = when_dt.date()
        
        # Gerar horário aleatório entre 11h-17h para preview
        random_hour = random.randint(11, 16)
        random_minute = random.randint(0, 59)
        new_time = time(random_hour, random_minute)
        
        return datetime.combine(target_date, new_time)
        
    def get_followup_data(self):
        """Retorna os dados do follow-up configurado."""
        # Determinar tipo usando currentData()
        tipo = self.combo_tipo.currentData() or "padrao"
        is_custom = self.radio_custom.isChecked()
            
        # Calcular quando
        if self.radio_3_dias.isChecked():
            quando = datetime.now() + timedelta(days=3)
            dias_apos = 3
        elif self.radio_7_dias.isChecked():
            quando = datetime.now() + timedelta(days=7)
            dias_apos = 7
        elif self.radio_14_dias.isChecked():
            quando = datetime.now() + timedelta(days=14)
            dias_apos = 14
        else:  # custom
            from datetime import time
            date = self.date_edit.date().toPyDate()
            time_selected = self.time_edit.time().toPyTime()
            quando = datetime.combine(date, time_selected)
            hoje = datetime.now().date()
            dias_apos = (date - hoje).days
            
        return {
            'tipo': tipo,
            'quando': quando,
            'dias_apos': dias_apos,
            'is_custom': is_custom
        }
