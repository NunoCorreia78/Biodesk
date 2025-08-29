"""
Tab de histórico clínico - versão otimizada
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                           QPushButton, QLabel, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt
from datetime import datetime
from ..utils.styles import StyleManager


class HistoricoTab(QWidget):
    """Tab para gestão do histórico clínico"""
    
    historico_alterado = pyqtSignal(str)
    
    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data or {}
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout(self)
        
        # Cabeçalho com ações
        header = self._create_header()
        layout.addWidget(header)
        
        # Editor de histórico
        self.historico_edit = QTextEdit()
        self.historico_edit.textChanged.connect(self._on_historico_changed)
        StyleManager.apply_text_edit_style(self.historico_edit)
        layout.addWidget(self.historico_edit)
        
        # Barra de ferramentas
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
    
    def _create_header(self) -> QFrame:
        """Cria cabeçalho com ações"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        
        title = QLabel("🏥 <b>Histórico Clínico</b>")
        title.setStyleSheet("font-size: 16px; color: #2c3e50;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Botões de ação rápida
        btn_declaracao = QPushButton("📋 Declaração")
        btn_declaracao.clicked.connect(self._abrir_declaracao)
        
        btn_prescricao = QPushButton("💊 Prescrição")
        btn_prescricao.clicked.connect(self._abrir_prescricao)
        
        btn_protocolo = QPushButton("📋 Protocolos")
        btn_protocolo.clicked.connect(self._abrir_protocolos)
        
        for btn in [btn_declaracao, btn_prescricao, btn_protocolo]:
            StyleManager.apply_button_style(btn)
            layout.addWidget(btn)
        
        return frame
    
    def _create_toolbar(self) -> QFrame:
        """Cria barra de ferramentas"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        
        btn_data = QPushButton("📅 Inserir Data")
        btn_data.clicked.connect(self._inserir_data)
        
        btn_template = QPushButton("📝 Templates")
        btn_template.clicked.connect(self._abrir_templates)
        
        for btn in [btn_data, btn_template]:
            StyleManager.apply_button_style(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Contador de caracteres
        self.char_count = QLabel("0 caracteres")
        self.char_count.setStyleSheet("color: #666;")
        layout.addWidget(self.char_count)
        
        return frame
    
    def _load_data(self):
        """Carrega histórico do paciente"""
        historico = self.paciente_data.get('historico', '')
        if isinstance(historico, dict):
            historico = historico.get('texto', '')
        self.historico_edit.setPlainText(historico)
        self._update_char_count()
    
    def get_data(self) -> dict:
        """Retorna dados do histórico"""
        return {'historico': self.historico_edit.toPlainText()}
    
    def update_data(self, paciente_data: dict):
        """Atualiza com novos dados"""
        self.paciente_data = paciente_data
        self._load_data()
    
    def _on_historico_changed(self):
        """Emite sinal quando histórico muda"""
        self._update_char_count()
        self.historico_alterado.emit(self.historico_edit.toPlainText())
    
    def _update_char_count(self):
        """Atualiza contador de caracteres"""
        count = len(self.historico_edit.toPlainText())
        self.char_count.setText(f"{count} caracteres")
    
    def _inserir_data(self):
        """Insere data atual no histórico"""
        data_atual = datetime.now().strftime("%d/%m/%Y")
        cursor = self.historico_edit.textCursor()
        cursor.insertText(f"\n--- {data_atual} ---\n")
    
    def _abrir_declaracao(self):
        """Abre dialog de declaração"""
        from ..dialogs.declaracao_dialog import DeclaracaoDialog
        dialog = DeclaracaoDialog(self.paciente_data, self)
        dialog.exec()
    
    def _abrir_prescricao(self):
        """Abre dialog de prescrição"""
        from ..dialogs.prescricao_dialog import PrescricaoDialog
        dialog = PrescricaoDialog(self.paciente_data, self)
        dialog.exec()
    
    def _abrir_protocolos(self):
        """Abre dialog de protocolos"""
        from ..dialogs.protocolo_dialog import ProtocoloDialog
        dialog = ProtocoloDialog(self.paciente_data, self)
        if dialog.exec():
            protocolo = dialog.get_selected_protocol()
            if protocolo:
                cursor = self.historico_edit.textCursor()
                cursor.insertText(f"\n{protocolo}\n")
    
    def _abrir_templates(self):
        """Abre dialog de templates"""
        from ..dialogs.template_dialog import TemplateDialog
        dialog = TemplateDialog(self)
        if dialog.exec():
            template = dialog.get_selected_template()
            if template:
                cursor = self.historico_edit.textCursor()
                cursor.insertText(template)
    
    def print(self):
        """Imprime histórico"""
        from ..services.print_service import PrintService
        PrintService.print_text(self.historico_edit.toPlainText(), "Histórico Clínico")
