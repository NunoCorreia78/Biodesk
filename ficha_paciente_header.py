# -*- coding: utf-8 -*-
"""
Módulo da Ficha do Paciente - Interface principal para gestão de pacientes
Funcionalidades: Dados pessoais, Histórico clínico, Templates, Comunicação, Consentimentos
"""

import sys
import os
import json
import unicodedata
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGridLayout, QTabWidget, QLabel, QLineEdit, QTextEdit, 
                            QComboBox, QDateEdit, QPushButton, QScrollArea, QFrame, 
                            QSplitter, QFileDialog, QCheckBox, QSpinBox, QToolBar, 
                            QApplication, QDialog, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QShortcut, QKeySequence, QPainter, QPen, QColor, QPainterPath

from db_manager import DBManager
from modern_date_widget import ModernDateWidget
from sistema_assinatura import abrir_dialogo_assinatura
from biodesk_dialogs import BiodeskMessageBox
from biodesk_ui_kit import BiodeskUIKit
from datetime import datetime

def importar_modulos_especializados():
    """Importa módulos especializados apenas quando necessário"""
    try:
        from ficha_paciente.dados_pessoais import DadosPessoaisWidget
        from ficha_paciente.historico_clinico import HistoricoClinicoWidget
        from ficha_paciente.templates_manager import TemplatesManagerWidget
        from ficha_paciente.comunicacao_manager import ComunicacaoManagerWidget
        from ficha_paciente.gestao_documentos import GestaoDocumentosWidget
        from ficha_paciente.declaracao_saude import DeclaracaoSaudeWidget
        from ficha_paciente.pesquisa_pacientes import PesquisaPacientesManager
        return DadosPessoaisWidget, HistoricoClinicoWidget, TemplatesManagerWidget, ComunicacaoManagerWidget, GestaoDocumentosWidget, DeclaracaoSaudeWidget, None, PesquisaPacientesManager
    except ImportError:
        return None, None, None, None, None, None, None, None


class FichaPacienteWindow(QMainWindow):
    paciente_atualizado = pyqtSignal(dict)  # Signal para notificar atualizações de paciente
    
    def __init__(self, parent=None, paciente_data=None):
        super().__init__(parent)
        self.setWindowTitle("Ficha do Paciente - Biodesk")
        
        # Garantir que a janela sempre abre maximizada
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        self.parent_window = parent
        self.paciente_data = paciente_data
        self.db = DBManager()
        
        # Aplicar estilos universais
        BiodeskUIKit.apply_universal_window_style(self)
        
        # Configurar interface
        self.init_ui()
        self.setup_toolbar()
        
        # Dados do paciente
        if paciente_data:
            self.carregar_dados_paciente(paciente_data)

    def resizeEvent(self, event):
        """Força a janela a permanecer sempre maximizada"""
        if self.windowState() != Qt.WindowState.WindowMaximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)
        super().resizeEvent(event)

    def changeEvent(self, event):
        """Intercepta mudanças de estado da janela"""
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() != Qt.WindowState.WindowMaximized:
                self.setWindowState(Qt.WindowState.WindowMaximized)
        super().changeEvent(event)

    def setup_toolbar(self):
        """Configura toolbar com estilo universal"""
        toolbar = self.addToolBar("Navegação")
        toolbar.setMovable(False)
        
        # Aplicar estilo universal à toolbar
        BiodeskUIKit.style_toolbar(toolbar)
        
        # Configurar ações
        voltar_action = QAction("Voltar", self)
        voltar_action.triggered.connect(self.close)
        toolbar.addAction(voltar_action)
        
        # Aplicar estilo universal aos botões da toolbar
        for action in toolbar.actions():
            if hasattr(action, 'setFont'):
                action.setFont(QFont("Segoe UI", 10))

    def abrir_ficha_consentimentos(self):
        """Abre a ficha de consentimentos"""
        from consentimentos_manager import ConsentimentosManager
        manager = ConsentimentosManager()
        manager.show()

    # O resto do arquivo será mantido como está
    # Este é apenas o cabeçalho corrigido
