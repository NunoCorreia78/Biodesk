"""
Diálogos estilizados para o Biodesk
Design moderno e elegante seguindo a identidade visual
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QMessageBox, QWidget, QFrame,
    QScrollArea, QComboBox, QSpinBox, QCheckBox, QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor, QPalette
import os


class BiodeskDialog(QDialog):
    """Classe base para diálogos Biodesk com estilo consistente"""
    
    def __init__(self, parent=None, title="Biodesk", width=500, height=350):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)
        self.resultado = None
        
        # Aplicar estilo Biodesk
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:0.5 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #9C27B0;
                border-radius: 15px;
            }
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)


class BiodeskStyledDialog(QDialog):
    """Diálogo base com estilo Biodesk elegante"""
    
    def __init__(self, parent=None, title="Biodesk", width=500, height=350):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)
        self.resultado = None
        
        # Aplicar estilo Biodesk moderno
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:0.5 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #9C27B0;
                border-radius: 20px;
            }
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#titulo {
                color: #9C27B0;
                font-size: 18px;
                font-weight: bold;
                margin: 10px 0;
            }
            QLabel#mensagem {
                color: #495057;
                font-size: 14px;
                line-height: 1.4;
                margin: 15px 0;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9C27B0, stop:1 #7B1FA2);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-width: 120px;
                min-height: 45px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #AB47BC, stop:1 #8E24AA);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7B1FA2, stop:1 #6A1B9A);
            }
            QPushButton#btn_ok {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
            }
            QPushButton#btn_ok:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34ce57, stop:1 #28a745);
            }
            QPushButton#btn_cancel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #495057);
            }
            QPushButton#btn_cancel:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a8288, stop:1 #545b62);
            }
            QPushButton#btn_warning {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffc107, stop:1 #e0a800);
                color: #212529;
            }
            QPushButton#btn_warning:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffcd39, stop:1 #ffc107);
            }
            QPushButton#btn_danger {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
            }
            QPushButton#btn_danger:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e4606d, stop:1 #dc3545);
            }
            QTextEdit, QLineEdit, QTextBrowser {
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
                color: #495057;
            }
            QTextEdit:focus, QLineEdit:focus {
                border-color: #9C27B0;
                background: #fafafa;
            }
            QComboBox {
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                color: #495057;
                min-height: 25px;
            }
            QComboBox:focus {
                border-color: #9C27B0;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #9C27B0;
                margin-right: 5px;
            }
        """)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Container de conteúdo
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container de botões
        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setSpacing(15)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Adicionar ao layout principal
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.button_widget)


class BiodeskMessageBox:
    """MessageBox personalizada com estilo Biodesk"""
    
    @staticmethod
    def information(parent, title, message):
        """Exibe mensagem de informação"""
        dialog = BiodeskStyledDialog(parent, title, 450, 250)
        
        # Ícone de informação
        icon_label = QLabel("ℹ️")
        icon_label.setStyleSheet("font-size: 32px; margin-right: 15px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("titulo")
        
        # Mensagem
        msg_label = QLabel(message)
        msg_label.setObjectName("mensagem")
        msg_label.setWordWrap(True)
        
        # Layout do conteúdo
        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(title_label)
        text_layout.addWidget(msg_label)
        content_layout.addLayout(text_layout)
        
        dialog.content_layout.addLayout(content_layout)
        
        # Botão OK
        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("btn_ok")
        btn_ok.clicked.connect(dialog.accept)
        dialog.button_layout.addStretch()
        dialog.button_layout.addWidget(btn_ok)
        
        dialog.exec()
    
    @staticmethod
    def warning(parent, title, message):
        """Exibe mensagem de aviso"""
        dialog = BiodeskStyledDialog(parent, title, 450, 250)
        
        # Ícone de aviso
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px; margin-right: 15px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("titulo")
        
        # Mensagem
        msg_label = QLabel(message)
        msg_label.setObjectName("mensagem")
        msg_label.setWordWrap(True)
        
        # Layout do conteúdo
        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(title_label)
        text_layout.addWidget(msg_label)
        content_layout.addLayout(text_layout)
        
        dialog.content_layout.addLayout(content_layout)
        
        # Botão OK
        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("btn_warning")
        btn_ok.clicked.connect(dialog.accept)
        dialog.button_layout.addStretch()
        dialog.button_layout.addWidget(btn_ok)
        
        dialog.exec()
    
    @staticmethod
    def critical(parent, title, message):
        """Exibe mensagem de erro"""
        dialog = BiodeskStyledDialog(parent, title, 450, 250)
        
        # Ícone de erro
        icon_label = QLabel("❌")
        icon_label.setStyleSheet("font-size: 32px; margin-right: 15px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("titulo")
        
        # Mensagem
        msg_label = QLabel(message)
        msg_label.setObjectName("mensagem")
        msg_label.setWordWrap(True)
        
        # Layout do conteúdo
        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(title_label)
        text_layout.addWidget(msg_label)
        content_layout.addLayout(text_layout)
        
        dialog.content_layout.addLayout(content_layout)
        
        # Botão OK
        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("btn_danger")
        btn_ok.clicked.connect(dialog.accept)
        dialog.button_layout.addStretch()
        dialog.button_layout.addWidget(btn_ok)
        
        dialog.exec()
    
    @staticmethod
    def question(parent, title, message):
        """Exibe mensagem de pergunta com Sim/Não"""
        dialog = BiodeskStyledDialog(parent, title, 450, 250)
        
        # Ícone de pergunta
        icon_label = QLabel("❓")
        icon_label.setStyleSheet("font-size: 32px; margin-right: 15px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("titulo")
        
        # Mensagem
        msg_label = QLabel(message)
        msg_label.setObjectName("mensagem")
        msg_label.setWordWrap(True)
        
        # Layout do conteúdo
        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(title_label)
        text_layout.addWidget(msg_label)
        content_layout.addLayout(text_layout)
        
        dialog.content_layout.addLayout(content_layout)
        
        # Botões Sim/Não
        btn_yes = QPushButton("Sim")
        btn_yes.setObjectName("btn_ok")
        btn_yes.clicked.connect(lambda: setattr(dialog, 'resultado', True) or dialog.accept())
        
        btn_no = QPushButton("Não")
        btn_no.setObjectName("btn_cancel")
        btn_no.clicked.connect(lambda: setattr(dialog, 'resultado', False) or dialog.reject())
        
        dialog.button_layout.addStretch()
        dialog.button_layout.addWidget(btn_no)
        dialog.button_layout.addWidget(btn_yes)
        
        dialog.exec()
        return dialog.resultado or False

    @staticmethod
    def question(parent, title, message, details=None):
        """Exibe mensagem de pergunta com opções Sim/Não"""
        dialog = BiodeskStyledDialog(parent, title, 500, 300 if details else 200)
        
        # Ícone de pergunta
        icon_label = QLabel("❓")
        icon_label.setStyleSheet("font-size: 32px; margin-right: 15px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("titulo")
        
        # Mensagem
        msg_label = QLabel(message)
        msg_label.setObjectName("mensagem")
        msg_label.setWordWrap(True)
        
        # Layout do conteúdo
        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(title_label)
        text_layout.addWidget(msg_label)
        
        # Adicionar detalhes se fornecidos
        if details:
            details_label = QLabel("📋 Detalhes:")
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px; font-size: 12px;")
            
            details_text = QTextBrowser()
            details_text.setPlainText(details)
            details_text.setMaximumHeight(100)
            details_text.setStyleSheet("""
                QTextBrowser {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 10px;
                    padding: 8px;
                }
            """)
            
            text_layout.addWidget(details_label)
            text_layout.addWidget(details_text)
        
        content_layout.addLayout(text_layout)
        dialog.content_layout.addLayout(content_layout)
        
        # Botões personalizados
        button_layout = QHBoxLayout()
        
        # Criar funções locais para aceitar resultado
        def aceitar_sim():
            dialog.resultado = True
            dialog.accept()
            
        def aceitar_nao():
            dialog.resultado = False
            dialog.accept()
        
        # Botão Sim
        sim_btn = QPushButton("✅ Sim")
        sim_btn.setObjectName("botao_primario")
        sim_btn.clicked.connect(aceitar_sim)
        
        # Botão Não
        nao_btn = QPushButton("❌ Não")
        nao_btn.setObjectName("botao_secundario")
        nao_btn.clicked.connect(aceitar_nao)
        
        button_layout.addWidget(nao_btn)
        button_layout.addWidget(sim_btn)
        dialog.content_layout.addLayout(button_layout)
        
        dialog.exec()
        return dialog.resultado
    
    @staticmethod
    def _aceitar_question(dialog, valor):
        """Método auxiliar para definir resultado e fechar diálogo"""
        dialog.resultado = valor
        dialog.accept()

    @staticmethod
    def success(parent, title, message, details=None):
        """Exibe mensagem de sucesso com detalhes opcionais"""
        dialog = BiodeskStyledDialog(parent, title, 550, 400 if details else 250)
        
        # Ícone de sucesso
        icon_label = QLabel("✅")
        icon_label.setStyleSheet("font-size: 32px; margin-right: 15px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("titulo")
        
        # Mensagem
        msg_label = QLabel(message)
        msg_label.setObjectName("mensagem")
        msg_label.setWordWrap(True)
        
        # Layout do conteúdo
        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(title_label)
        text_layout.addWidget(msg_label)
        
        # Adicionar detalhes se fornecidos
        if details:
            details_label = QLabel("📋 Detalhes:")
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px; font-size: 12px;")
            
            details_text = QTextBrowser()
            details_text.setPlainText(details)
            details_text.setMaximumHeight(150)
            details_text.setStyleSheet("""
                QTextBrowser {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 10px;
                    padding: 8px;
                }
            """)
            
            text_layout.addWidget(details_label)
            text_layout.addWidget(details_text)
        
        content_layout.addLayout(text_layout)
        dialog.content_layout.addLayout(content_layout)
        
        # Botão OK
        btn_ok = QPushButton("✅ OK")
        btn_ok.setObjectName("btn_ok")
        btn_ok.clicked.connect(dialog.accept)
        dialog.button_layout.addStretch()
        dialog.button_layout.addWidget(btn_ok)
        
        dialog.exec()


class BiodeskTemplateDialog(BiodeskStyledDialog):
    """Diálogo estilizado para templates de prescrição"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "📄 Modelos de Prescrição", 800, 600)
        
        # Título principal
        title = QLabel("📄 Modelos de Prescrição")
        title.setObjectName("titulo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        
        self.content_layout.addWidget(title)
        
        # Área de scroll para templates
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #9C27B0;
                border-radius: 15px;
                background: white;
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #9C27B0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #AB47BC;
            }
        """)
        
        self.template_widget = QWidget()
        self.template_layout = QVBoxLayout(self.template_widget)
        scroll_area.setWidget(self.template_widget)
        
        self.content_layout.addWidget(scroll_area)
        
        # Área de preview
        preview_label = QLabel("👁️ Preview do PDF")
        preview_label.setObjectName("titulo")
        preview_label.setStyleSheet("font-size: 16px; margin-top: 15px;")
        
        self.preview_area = QTextBrowser()
        self.preview_area.setMaximumHeight(150)
        self.preview_area.setStyleSheet("""
            QTextBrowser {
                background: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        
        self.content_layout.addWidget(preview_label)
        self.content_layout.addWidget(self.preview_area)
        
        # Botões
        btn_criar = QPushButton("📝 Criar Novo Template")
        btn_criar.setObjectName("btn_ok")
        
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("btn_cancel")
        btn_fechar.clicked.connect(self.close)
        
        self.button_layout.addWidget(btn_criar)
        self.button_layout.addStretch()
        self.button_layout.addWidget(btn_fechar)
