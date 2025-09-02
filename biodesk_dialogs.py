"""
Sistema de diálogos padrão para o Biodesk - PyQt6 Standard
=========================================================
Substitui todos os diálogos personalizados por diálogos padrão do PyQt6
"""

from PyQt6.QtWidgets import QMessageBox, QInputDialog, QDialog
from PyQt6.QtCore import Qt


class BiodeskMessageBox:
    """Sistema de diálogos usando QMessageBox padrão do PyQt6"""
    
    @staticmethod
    def information(parent, title, message, details=None):
        """Exibe mensagem de informação"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Definir texto em português europeu
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        
        return msg.exec()
    
    @staticmethod
    def warning(parent, title, message, details=None):
        """Exibe mensagem de aviso"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Definir texto em português europeu
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        
        return msg.exec()
    
    @staticmethod
    def critical(parent, title, message, details=None):
        """Exibe mensagem de erro crítico"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Definir texto em português europeu
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        
        return msg.exec()
    
    @staticmethod
    def show_error(parent, title, message, details=None):
        """Alias para critical"""
        return BiodeskMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_warning(parent, title, message, details=None):
        """Alias para warning"""
        return BiodeskMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_question(parent, title, message, details=None):
        if details:
            msg.setDetailedText(details)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Definir texto em português europeu
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        
        return msg.exec()
    
    @staticmethod
    def warning(parent, title, message):
        """Exibe mensagem de aviso"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Definir texto em português europeu
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        
        return msg.exec()
    
    @staticmethod
    def critical(parent, title, message):
        """Exibe mensagem de erro"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Definir texto em português europeu
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        
        return msg.exec()
    
    @staticmethod
    def question(parent, title, message, details=None):
        """Exibe mensagem de pergunta com opções Sim/Não"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # Definir textos em português europeu
        msg.button(QMessageBox.StandardButton.Yes).setText("Sim")
        msg.button(QMessageBox.StandardButton.No).setText("Não")
        
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        result = msg.exec()
        return result == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def success(parent, title, message, details=None):
        """Exibe mensagem de sucesso (usando information)"""
        return BiodeskMessageBox.information(parent, title, message, details)
    
    @staticmethod
    def getText(parent, title, label, text=""):
        """Exibe diálogo de entrada de texto"""
        text_input, ok = QInputDialog.getText(parent, title, label, text=text)
        return text_input, ok
    
    @staticmethod
    def getItem(parent, title, label, items, current=0, editable=False):
        """Exibe diálogo de seleção de item"""
        item, ok = QInputDialog.getItem(parent, title, label, items, current, editable)
        return item, ok


# Aliases para compatibilidade com código existente
BiodeskStyledDialog = QDialog
BiodeskDialog = QDialog


# Funções auxiliares para compatibilidade
def mostrar_informacao(parent, titulo, mensagem, tipo="info"):
    """Mostra diálogo de informação padrão"""
    return BiodeskMessageBox.information(parent, titulo, mensagem)


def mostrar_aviso(parent, titulo, mensagem):
    """Mostra diálogo de aviso padrão"""
    return BiodeskMessageBox.warning(parent, titulo, mensagem)


def mostrar_confirmacao(parent, titulo, mensagem, btn_sim="Sim", btn_nao="Não"):
    """Mostra diálogo de confirmação padrão"""
    return BiodeskMessageBox.question(parent, titulo, mensagem)


def mostrar_erro(parent, titulo, mensagem):
    """Mostra diálogo de erro padrão"""
    return BiodeskMessageBox.critical(parent, titulo, mensagem)


def mostrar_sucesso(parent, titulo, mensagem):
    """Mostra diálogo de sucesso padrão"""
    return BiodeskMessageBox.success(parent, titulo, mensagem)


def mostrar_informacao_com_callback(parent, titulo, mensagem, callback_ok=None, tipo="info"):
    """Mostra diálogo de informação padrão com callback"""
    result = BiodeskMessageBox.information(parent, titulo, mensagem)
    if result == QMessageBox.StandardButton.Ok and callback_ok:
        callback_ok()