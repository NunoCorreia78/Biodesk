"""
Serviço de impressão para o módulo ficha_paciente
"""

from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import QApplication


class PrintService:
    """Serviço para operações de impressão"""

    @staticmethod
    def print_text(text: str, title: str = "Documento") -> bool:
        """
        Imprime texto

        Args:
            text: Texto a imprimir
            title: Título do documento

        Returns:
            bool: True se impresso com sucesso
        """
        try:
            printer = QPrinter()
            printer.setDocName(title)

            dialog = QPrintDialog(printer)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Criar documento para impressão
                from PyQt6.QtGui import QTextDocument
                document = QTextDocument()
                document.setPlainText(text)
                document.print(printer)
                return True

            return False

        except Exception as e:
            print(f"Erro ao imprimir: {e}")
            return False

    @staticmethod
    def print_html(html: str, title: str = "Documento") -> bool:
        """
        Imprime HTML

        Args:
            html: HTML a imprimir
            title: Título do documento

        Returns:
            bool: True se impresso com sucesso
        """
        try:
            printer = QPrinter()
            printer.setDocName(title)

            dialog = QPrintDialog(printer)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Criar documento para impressão
                from PyQt6.QtGui import QTextDocument
                document = QTextDocument()
                document.setHtml(html)
                document.print(printer)
                return True

            return False

        except Exception as e:
            print(f"Erro ao imprimir HTML: {e}")
            return False
