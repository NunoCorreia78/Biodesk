"""
Utilitários de diálogo para o módulo ficha_paciente
"""

from PyQt6.QtWidgets import QMessageBox, QWidget


def show_success(parent: QWidget, message: str):
    """Mostra diálogo de sucesso"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle("Sucesso")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def show_error(parent: QWidget, message: str):
    """Mostra diálogo de erro"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Erro")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def show_warning(parent: QWidget, message: str):
    """Mostra diálogo de aviso"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle("Aviso")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def confirm_action(parent: QWidget, message: str) -> bool:
    """Pede confirmação ao usuário"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle("Confirmação")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    return msg_box.exec() == QMessageBox.StandardButton.Yes
