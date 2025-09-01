"""
Biodesk - ImportPdfDialog
=========================

Dialog para importação de PDFs assinados.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Seleção de arquivo PDF assinado
- Validação de arquivo
- Integração com sistema de documentos
- Feedback visual para o usuário

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Optional, Callable

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog)

from ficha_paciente.core.button_manager import ButtonManager


class ImportPdfDialog(QDialog):
    """Dialog para importação de PDFs assinados"""
    
    def __init__(self, arquivo_temp: str, 
                 callback: Optional[Callable[[str, str], bool]] = None, parent=None):
        """
        Args:
            arquivo_temp: Caminho do arquivo temporário
            callback: Função para processar o arquivo selecionado (retorna True se sucesso)
            parent: Widget pai
        """
        super().__init__(parent)
        self.arquivo_temp = arquivo_temp
        self.callback = callback
        self.setupUI()
        
    def setupUI(self):
        """Configura a interface do diálogo"""
        self.setWindowTitle("Importar PDF Assinado")
        self.setFixedSize(450, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Informação
        info_label = QLabel(
            "📄 Importe o PDF assinado para finalizar o processo:\n\n"
            "• Selecione o arquivo PDF que foi assinado\n"
            "• O documento será guardado na pasta do paciente\n"
            "• O consentimento ficará marcado como assinado"
        )
        info_label.setStyleSheet("""
            font-size: 12px; 
            padding: 15px; 
            background-color: #f8f9fa; 
            border-radius: 6px;
            border-left: 4px solid #2980b9;
            line-height: 1.4;
        """)
        layout.addWidget(info_label)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        
        btn_importar = QPushButton("📁 Selecionar PDF Assinado")
        btn_importar.setFixedSize(180, 35)
        btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        btn_importar.clicked.connect(self.selecionar_e_importar_pdf)
        
        btn_cancelar = ButtonManager.cancelar_button(self, self.reject)
        btn_cancelar.setFixedSize(100, 35)
        
        botoes_layout.addWidget(btn_importar)
        botoes_layout.addWidget(btn_cancelar)
        layout.addLayout(botoes_layout)
    
    def selecionar_e_importar_pdf(self):
        """Seleciona e importa o PDF assinado"""
        try:
            # Selecionar arquivo PDF assinado
            arquivo_assinado, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar PDF Assinado",
                "",
                "PDF files (*.pdf)"
            )
            
            if arquivo_assinado:
                # Chamar callback se fornecido
                if self.callback:
                    sucesso = self.callback(arquivo_assinado, self.arquivo_temp)
                    if sucesso:
                        self.accept()
                else:
                    self.accept()
                    
        except Exception as e:
            print(f"[ERRO] Erro ao importar PDF: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
            self,
            "Erro",
            f"❌ Erro ao importar PDF:\n\n{str(e
        )}")
    
    @staticmethod
    def abrir_dialog(arquivo_temp: str, 
                    callback: Optional[Callable[[str, str], bool]] = None, 
                    parent=None) -> bool:
        """
        Método estático para abrir o diálogo de forma conveniente
        
        Args:
            arquivo_temp: Caminho do arquivo temporário
            callback: Função para processar o arquivo selecionado
            parent: Widget pai
            
        Returns:
            True se o usuário confirmou a importação, False se cancelou
        """
        dialog = ImportPdfDialog(arquivo_temp, callback, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
