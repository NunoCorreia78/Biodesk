from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QValidator
import re
from datetime import datetime
from biodesk_ui_kit import BiodeskUIKit
"""
Widget de data moderno para o Biodesk
Permite digitação manual no formato ddmmaaaa e formatação automática para dd/mm/aaaa
Inclui calendário popup melhorado com navegação fácil de ano e mês
"""

    QWidget, QHBoxLayout, QLineEdit, QPushButton, QCalendarWidget, 
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialog
)


class DateValidator(QValidator):
    """Validador personalizado para entrada de data"""
    
    def validate(self, input_str, pos):
        # Remove caracteres não numéricos
        digits_only = re.sub(r'\D', '', input_str)
        
        # Máximo 8 dígitos (ddmmaaaa)
        if len(digits_only) > 8:
            return (QValidator.State.Invalid, input_str, pos)
        
        return (QValidator.State.Acceptable, input_str, pos)


class ModernCalendarDialog(QDialog):
    """Diálogo de calendário moderno com navegação fácil"""
    
    dateSelected = pyqtSignal(QDate)
    
    def __init__(self, current_date=None, parent=None):
        super().__init__(parent)
        self.current_date = current_date or QDate.currentDate()
        self.setWindowTitle("📅 Selecionar Data")
        self.setModal(True)
        self.setFixedSize(380, 350)
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Barra de navegação superior
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        # Seletores de mês e ano
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ])
        self.month_combo.setCurrentIndex(self.current_date.month() - 1)
        self.month_combo.currentIndexChanged.connect(self.update_calendar)

        self.year_combo = QComboBox()
        current_year = self.current_date.year()
        for year in range(1920, 2030):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self.update_calendar)

        # Botão "Hoje"
        today_btn = QPushButton("📍 Hoje")
        today_btn.setToolTip("Ir para a data de hoje")
        today_btn.clicked.connect(self.go_to_today)

        # Montar a barra de navegação
        nav_layout.addWidget(self.month_combo)
        nav_layout.addWidget(self.year_combo)
        nav_layout.addStretch(1)
        nav_layout.addWidget(today_btn)
        layout.addLayout(nav_layout)

        # Calendário
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setSelectedDate(self.current_date)
        self.calendar.clicked.connect(self.date_clicked)
        
        # Ocultar barra de navegação nativa do calendário
        self.calendar.setNavigationBarVisible(False)
        
        layout.addWidget(self.calendar)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("✅ Confirmar")
        ok_btn.clicked.connect(self.accept_date)
        ok_btn.setDefault(True)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(ok_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        
    def update_calendar(self):
        """Atualiza o calendário quando mês ou ano mudam"""
        try:
            month = self.month_combo.currentIndex() + 1
            year = int(self.year_combo.currentText())
            
            # Manter o dia se possível, senão usar o último dia do mês
            current_selected = self.calendar.selectedDate()
            day = min(current_selected.day(), QDate(year, month, 1).daysInMonth())
            
            new_date = QDate(year, month, day)
            self.calendar.setSelectedDate(new_date)
            
        except (ValueError, TypeError):
            pass
    
    def go_to_today(self):
        """Vai para a data de hoje"""
        today = QDate.currentDate()
        self.month_combo.setCurrentIndex(today.month() - 1)
        self.year_combo.setCurrentText(str(today.year()))
        self.calendar.setSelectedDate(today)
    
    def date_clicked(self, date):
        """Quando uma data é clicada no calendário"""
        # Atualizar os combos para refletir a data selecionada
        self.month_combo.setCurrentIndex(date.month() - 1)
        self.year_combo.setCurrentText(str(date.year()))
    
    def accept_date(self):
        """Aceita a data selecionada"""
        selected_date = self.calendar.selectedDate()
        self.dateSelected.emit(selected_date)
        self.accept()
        
    def apply_styles(self):
        """Aplica estilos modernos iris ao diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
                color: #495057;
                min-width: 80px;
                min-height: 16px;
            }
            
            QComboBox:hover {
                border: 2px solid #6c757d;
            }
            
            QComboBox:focus {
                border: 2px solid #007bff;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6c757d;
                margin-right: 5px;
            }
            
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: white;
                padding: 4px;
            }
            
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                min-width: 70px;
                min-height: 16px;
            }
            
            QPushButton:hover {
                background-color: #007bff;
                color: white;
                border: 2px solid #007bff;
            }
            
            QPushButton:pressed {
                background-color: #0056b3;
                border: 2px solid #0056b3;
            }
            
            QPushButton[default="true"] {
                background-color: #28a745;
                color: white;
                border: 2px solid #28a745;
            }
            
            QPushButton[default="true"]:hover {
                background-color: #1e7e34;
                border: 2px solid #1e7e34;
            }
            
            QCalendarWidget {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #f8f9fa;
            }
            
            /* Ocultar barra de navegação do calendário */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: transparent;
                border: none;
                max-height: 0px;
                min-height: 0px;
            }
            
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                max-width: 0px;
                min-width: 0px;
                max-height: 0px;
                min-height: 0px;
                border: none;
                background-color: transparent;
            }
            
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                max-width: 0px;
                min-width: 0px;
                max-height: 0px;
                min-height: 0px;
                border: none;
                background-color: transparent;
            }
            
            QCalendarWidget QToolButton {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                color: #495057;
                font-weight: bold;
                padding: 6px 10px;
                margin: 2px;
                min-height: 16px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #007bff;
                color: white;
                border: 2px solid #007bff;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 13px;
                color: #495057;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: white;
                border-radius: 4px;
            }
            
            QCalendarWidget QAbstractItemView:selected {
                background-color: #007bff;
                color: white;
                border: 2px solid #0056b3;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QCalendarWidget QHeaderView::section {
                background-color: #f8f9fa;
                color: #6c757d;
                border: none;
                font-weight: bold;
                padding: 4px;
            }
            
            QLabel {
                font-size: 14px;
                color: #495057;
                font-weight: normal;
            }
        """)


class ModernDateWidget(QWidget):
    """Widget de data moderno com digitação manual e calendário popup"""
    
    dateChanged = pyqtSignal(QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate(1920, 1, 1)  # Data padrão
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # SEM ESPAÇO para ficar colado
        
        # Campo de entrada de texto
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("dd/mm/aaaa")
        self.date_input.setInputMask("99/99/9999")
        self.date_input.setText("__/__/____")
        self.date_input.setFixedWidth(140)
        # REMOVER altura fixa para usar o padrão dos outros campos
        self.date_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Conectar eventos
        self.date_input.textChanged.connect(self.on_text_changed)
        self.date_input.editingFinished.connect(self.validate_and_format)
        
        # Botão do calendário - COLADO ao campo
        self.calendar_btn = QPushButton("📅")
        # REMOVER tamanho fixo para ajustar automaticamente à altura do campo
        self.calendar_btn.setFixedWidth(36)  # Só largura fixa
        self.calendar_btn.clicked.connect(self.show_calendar)
        self.calendar_btn.setToolTip("Abrir calendário")
        
        layout.addWidget(self.date_input)
        layout.addWidget(self.calendar_btn)
        
        self.setLayout(layout)
        
    def on_text_changed(self, text):
        """Processa mudanças no texto enquanto o usuário digita"""
        # Remove caracteres de máscara para trabalhar apenas com dígitos
        digits = ''.join(filter(str.isdigit, text))
        
        # Auto-formatação durante a digitação
        if len(digits) >= 2:
            formatted = digits[:2]
            if len(digits) >= 4:
                formatted += '/' + digits[2:4]
                if len(digits) >= 8:
                    formatted += '/' + digits[4:8]
                elif len(digits) > 4:
                    formatted += '/' + digits[4:]
            elif len(digits) > 2:
                formatted += '/' + digits[2:]
            
            # Atualizar o campo sem disparar o evento novamente
            self.date_input.blockSignals(True)
            cursor_pos = self.date_input.cursorPosition()
            self.date_input.setText(formatted)
            self.date_input.setCursorPosition(min(cursor_pos, len(formatted)))
            self.date_input.blockSignals(False)
    
    def validate_and_format(self):
        """Valida e formata a data quando a edição termina"""
        text = self.date_input.text()
        
        # Extrair dígitos
        digits = ''.join(filter(str.isdigit, text))
        
        if len(digits) == 8:
            try:
                day = int(digits[:2])
                month = int(digits[2:4])
                year = int(digits[4:8])
                
                # Validar a data
                if 1 <= day <= 31 and 1 <= month <= 12 and 1920 <= year <= 2030:
                    # Verificar se a data é válida
                    try:
                        test_date = datetime(year, month, day)
                        new_date = QDate(year, month, day)
                        
                        if new_date != self.current_date:
                            self.current_date = new_date
                            self.dateChanged.emit(new_date)
                            
                        # Formatar o texto final
                        self.date_input.setText(f"{day:02d}/{month:02d}/{year}")
                        return
                        
                    except ValueError:
                        pass  # Data inválida (ex: 31/02/2023)
                        
            except ValueError:
                pass
        
        # Se chegou aqui, a data é inválida - restaurar a data atual
        if self.current_date.isValid() and self.current_date != QDate(1920, 1, 1):
            self.date_input.setText(self.current_date.toString("dd/MM/yyyy"))
        else:
            self.date_input.setText("__/__/____")
    
    def show_calendar(self):
        """Mostra o diálogo do calendário moderno"""
        dialog = ModernCalendarDialog(self.current_date, self)
        dialog.dateSelected.connect(self.set_date)
        
        # Posicionar o diálogo próximo ao widget
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        dialog.move(global_pos.x(), global_pos.y() + 5)
        
        dialog.exec()
    
    def set_date(self, date):
        """Define a data programaticamente"""
        if date.isValid():
            self.current_date = date
            self.date_input.setText(date.toString("dd/MM/yyyy"))
            self.dateChanged.emit(date)
    
    def date(self):
        """Retorna a data atual"""
        return self.current_date
    
    def setDate(self, date):
        """Define a data (compatibilidade com QDateEdit)"""
        self.set_date(date)
    
    def setMinimumDate(self, date):
        """Define a data mínima (para compatibilidade)"""
        pass
    
    def setMaximumDate(self, date):
        """Define a data máxima (para compatibilidade)"""
        pass
    
    def setDateRange(self, min_date, max_date):
        """Define o intervalo de datas (para compatibilidade)"""
        pass
    
    def apply_styles(self):
        """Aplica estilos modernos iris ao widget"""
        BiodeskUIKit.apply_universal_button_style(self)
