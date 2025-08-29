"""
Estilos centralizados para o módulo ficha_paciente
"""

from PyQt6.QtWidgets import QGroupBox, QTextEdit, QPushButton


class StyleManager:
    """Gerenciador centralizado de estilos"""

    @staticmethod
    def apply_group_style(group: QGroupBox):
        """Aplica estilo padrão aos grupos"""
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)

    @staticmethod
    def apply_text_edit_style(text_edit: QTextEdit):
        """Aplica estilo padrão aos editores de texto"""
        text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 2px solid #3498db;
            }
        """)

    @staticmethod
    def apply_button_style(button: QPushButton):
        """Aplica estilo padrão aos botões"""
        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

    @staticmethod
    def apply_error_style(widget):
        """Aplica estilo de erro"""
        widget.setStyleSheet("""
            border: 2px solid #e74c3c;
            background-color: #fdf2f2;
        """)

    @staticmethod
    def apply_success_style(widget):
        """Aplica estilo de sucesso"""
        widget.setStyleSheet("""
            border: 2px solid #27ae60;
            background-color: #f2fdf8;
        """)

    @staticmethod
    def reset_style(widget):
        """Remove estilos aplicados"""
        widget.setStyleSheet("")
