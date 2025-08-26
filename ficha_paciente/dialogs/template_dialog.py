"""
Biodesk - TemplateDialog
=======================

Dialog para seleção e aplicação de templates de mensagem.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Lista de templates predefinidos
- Preview do template selecionado
- Aplicação do template ao editor

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Dict, Optional, Callable

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QTextEdit, QMessageBox)

from ficha_paciente.core.button_manager import ButtonManager


class TemplateDialog(QDialog):
    """Dialog para seleção de templates de mensagem"""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None, parent=None):
        """
        Args:
            callback: Função a ser chamada com o template selecionado
            parent: Widget pai
        """
        super().__init__(parent)
        self.callback = callback
        self.templates = {
            "Consulta Inicial": "Obrigado por ter escolhido os nossos serviços...",
            "Follow-up": "Como tem estado desde a nossa última consulta?",
            "Agendamento": "Gostaria de agendar a sua próxima consulta..."
        }
        self.setupUI()
        
    def setupUI(self):
        """Configura a interface do diálogo"""
        self.setWindowTitle("📝 Usar Template")
        self.resize(650, 500)  # Tamanho otimizado
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Lista de templates
        self.lista_templates = QListWidget()
        self.lista_templates.setStyleSheet("""
            QListWidget {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        
        for nome in self.templates.keys():
            self.lista_templates.addItem(nome)
        layout.addWidget(self.lista_templates)
        
        # Preview do template
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                background-color: #f8f9fa;
                color: #495057;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.preview)
        
        # Conectar sinal para atualizar preview
        self.lista_templates.itemSelectionChanged.connect(self.atualizar_preview)
        
        # Botões usando ButtonManager
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        btn_cancelar = ButtonManager.cancelar_button(self, self.reject)
        btn_usar = ButtonManager.usar_template_button(self, self.usar_template)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addWidget(btn_usar)
        layout.addLayout(botoes_layout)
        
        # Selecionar primeiro item por padrão
        if self.lista_templates.count() > 0:
            self.lista_templates.setCurrentRow(0)
            self.atualizar_preview()
    
    def atualizar_preview(self):
        """Atualiza o preview do template selecionado"""
        item_atual = self.lista_templates.currentItem()
        if item_atual:
            nome = item_atual.text()
            self.preview.setPlainText(self.templates[nome])
    
    def usar_template(self):
        """Aplica o template selecionado"""
        item_atual = self.lista_templates.currentItem()
        if item_atual:
            nome = item_atual.text()
            template_texto = self.templates[nome]
            
            # Chamar callback se fornecido
            if self.callback:
                self.callback(template_texto)
            
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", "Selecione um template primeiro.")
    
    def get_template_texto(self) -> Optional[str]:
        """Retorna o texto do template selecionado"""
        item_atual = self.lista_templates.currentItem()
        if item_atual:
            nome = item_atual.text()
            return self.templates[nome]
        return None
    
    @staticmethod
    def abrir_dialog(callback: Optional[Callable[[str], None]] = None, parent=None) -> Optional[str]:
        """
        Método estático para abrir o diálogo de forma conveniente
        
        Args:
            callback: Função a ser chamada com o template selecionado
            parent: Widget pai
            
        Returns:
            Texto do template selecionado ou None se cancelado
        """
        dialog = TemplateDialog(callback, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_template_texto()
        return None
