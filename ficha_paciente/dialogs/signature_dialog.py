"""
Biodesk - SignatureDialog
=========================

Dialog para assinatura de documentos PDF.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Interface simplificada para assinatura
- Instruções claras para o usuário
- Importação de documentos assinados
- Gestão de arquivos temporários

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Optional, Callable

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PyQt6.QtCore import Qt

from ficha_paciente.core.button_manager import ButtonManager


class SignatureDialog(QDialog):
    """Dialog para assinatura de documentos PDF"""
    
    def __init__(self, arquivo_temp: str, arquivo_final: str, 
                 callback: Optional[Callable[[str, str], None]] = None, parent=None):
        """
        Args:
            arquivo_temp: Caminho do arquivo temporário para assinatura
            arquivo_final: Caminho onde será salvo o arquivo final
            callback: Função a ser chamada quando importar assinado
            parent: Widget pai
        """
        super().__init__(parent)
        self.arquivo_temp = arquivo_temp
        self.arquivo_final = arquivo_final
        self.callback = callback
        self.setupUI()
        
    def setupUI(self):
        """Configura a interface do diálogo"""
        self.setWindowTitle("📝 Assinatura de Documento")
        self.setFixedSize(500, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Ícone e título
        titulo = QLabel("📝 PDF ABERTO PARA ASSINATURA")
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2980b9;
            padding: 15px;
            text-align: center;
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Instruções
        instrucoes = QLabel("""
<div style='font-size: 14px; line-height: 1.6;'>
<b>📋 INSTRUÇÕES SIMPLES:</b><br><br>
1️⃣ <b>Assine</b> o documento no Adobe Reader/visualizador<br>
2️⃣ <b>Guarde</b> o documento (Ctrl+S ou File → Save)<br>
3️⃣ <b>Feche</b> o Adobe Reader<br>
4️⃣ <b>Clique "✅ Importar"</b> abaixo
</div>
        """)
        instrucoes.setStyleSheet("""
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2980b9;
        """)
        layout.addWidget(instrucoes)
        
        # Localização do arquivo
        local = QLabel(f"📁 <b>Localização:</b> {self.arquivo_temp}")
        local.setStyleSheet("font-size: 11px; color: #666; padding: 10px;")
        local.setWordWrap(True)
        layout.addWidget(local)
        
        # Botões usando ButtonManager
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        
        btn_cancelar = ButtonManager.cancelar_button(self, self.reject)
        btn_cancelar.setFixedSize(120, 40)
        
        btn_importar = QPushButton("✅ Importar Assinado")
        btn_importar.setFixedSize(160, 40)
        btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        btn_importar.clicked.connect(self.importar_assinado)
        
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addWidget(btn_importar)
        layout.addLayout(botoes_layout)
    
    def importar_assinado(self):
        """Executa a importação do documento assinado"""
        try:
            if self.callback:
                self.callback(self.arquivo_temp, self.arquivo_final)
            self.accept()
        except Exception as e:
            print(f"[ERRO] Erro ao importar assinado: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", f"Erro ao importar documento:\n{str(e)}")
    
    @staticmethod
    def abrir_dialog(arquivo_temp: str, arquivo_final: str, 
                    callback: Optional[Callable[[str, str], None]] = None, 
                    parent=None) -> bool:
        """
        Método estático para abrir o diálogo de forma conveniente
        
        Args:
            arquivo_temp: Caminho do arquivo temporário para assinatura
            arquivo_final: Caminho onde será salvo o arquivo final
            callback: Função a ser chamada quando importar assinado
            parent: Widget pai
            
        Returns:
            True se o usuário confirmou a importação, False se cancelou
        """
        dialog = SignatureDialog(arquivo_temp, arquivo_final, callback, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
