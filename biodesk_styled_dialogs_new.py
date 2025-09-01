"""
Diálogos estilizados para o Biodesk - VERSÃO PADRÃO
Design usando QMessageBox padrão do PyQt6 (sem personalização roxa)
"""

from PyQt6.QtWidgets import QMessageBox, QDialog


class BiodeskMessageBox:
    """MessageBox usando estilo padrão PyQt6 (sem personalização)"""
    
    @staticmethod
    def information(parent, title, message):
        """Exibe mensagem de informação usando QMessageBox padrão"""
        return QMessageBox.information(parent, title, message)
    
    @staticmethod
    def warning(parent, title, message):
        """Exibe mensagem de aviso usando QMessageBox padrão"""
        return QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def critical(parent, title, message):
        """Exibe mensagem de erro usando QMessageBox padrão"""
        return QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def question(parent, title, message):
        """Exibe pergunta usando QMessageBox padrão"""
        return QMessageBox.question(parent, title, message)


class BiodeskStyledDialog(QDialog):
    """Classe de compatibilidade - usa QDialog padrão"""
    
    def __init__(self, parent=None, title="Biodesk", width=500, height=350):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)
    
    @staticmethod
    def question(parent, title, message):
        """Compatibilidade - redireciona para QMessageBox"""
        return QMessageBox.question(parent, title, message)
