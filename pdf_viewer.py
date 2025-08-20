"""
Sistema de Visualização de PDFs para Biodesk
Permite visualizar PDFs gerados diretamente na interface
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

try:
    # Desabilitar QWebEngineView para evitar janela que pisca
    # from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = False
except ImportError:
    WEB_ENGINE_AVAILABLE = False


class PDFViewer(QDialog):
    """Visualizador de PDF integrado"""
    
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.init_ui()
    
    def init_ui(self):
        """Inicializa a interface do visualizador"""
        self.setWindowTitle("📄 Visualizador de PDF - Biodesk")
        self.setGeometry(50, 50, 1200, 800)  # Janela maior para melhor visualização
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Margens menores para mais espaço
        layout.setSpacing(5)
        
        # Cabeçalho compacto
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        header_layout = QHBoxLayout(header)
        
        # Título compacto
        title = QLabel(f"📄 {os.path.basename(self.pdf_path)}")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: white;
            margin: 0;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botões melhorados
        btn_open_external = QPushButton("🔗 Abrir Externa")
        btn_open_external.clicked.connect(self.open_external)
        btn_open_external.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        header_layout.addWidget(btn_open_external)
        
        btn_close = QPushButton("❌ Fechar")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.3);
            }
        """)
        header_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # Área de conteúdo melhorada
        if WEB_ENGINE_AVAILABLE and self.can_display_pdf():
            # ✅ LAZY LOADING: Só criar QWebEngineView quando realmente necessário
            try:
                self.web_view = QWebEngineView(parent=self)  # Definir parent para evitar janela independente
                
                # Configurar para melhor visualização de PDF
                self.web_view.setStyleSheet("""
                    QWebEngineView {
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        background-color: #f9f9f9;
                    }
                """)
                
                pdf_url = QUrl.fromLocalFile(os.path.abspath(self.pdf_path))
                self.web_view.load(pdf_url)
                layout.addWidget(self.web_view)
                print("✅ [PDF_VIEWER] QWebEngineView criado com parent adequado")
                
            except Exception as e:
                print(f"⚠️ [PDF_VIEWER] Erro ao criar QWebEngineView: {e}")
                self.show_fallback_info(layout)
        else:
            # Fallback - mostrar informação e abrir externamente
            self.show_fallback_info(layout)
    
    def can_display_pdf(self) -> bool:
        """Verifica se o PDF pode ser exibido diretamente"""
        if not WEB_ENGINE_AVAILABLE:
            return False
        
        if not os.path.exists(self.pdf_path):
            return False
        
        try:
            # Verificar se o arquivo não está muito grande (limite 100MB)
            file_size = os.path.getsize(self.pdf_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                return False
            
            # Verificar se é realmente um PDF
            with open(self.pdf_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ [PDF_VIEWER] Erro ao verificar PDF: {e}")
            return False
    
    def show_fallback_info(self, layout):
        """Mostra informação quando não é possível visualizar diretamente"""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 2px solid #2196F3;
                border-radius: 12px;
                padding: 40px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.setSpacing(20)
        
        # Ícone e título melhorados
        title = QLabel("📄 PDF Pronto para Visualização")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1976D2;
            margin-bottom: 10px;
        """)
        info_layout.addWidget(title)
        
        # Informação melhorada
        file_size = os.path.getsize(self.pdf_path) / 1024  # KB
        info_text = QLabel(f"""
        ✅ O seu documento PDF foi gerado com sucesso!
        
        📊 Informações:
        • Tamanho: {file_size:.1f} KB
        • Localização: {os.path.basename(self.pdf_path)}
        
        🎯 Para visualizar:
        • Clique no botão "Abrir PDF" abaixo
        • O documento será aberto no seu visualizador preferido
        • Pode imprimir, guardar ou partilhar conforme necessário
        
        📍 Caminho completo:
        {self.pdf_path}
        """)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_text.setStyleSheet("""
            font-size: 16px;
            color: #1565C0;
            line-height: 1.8;
            margin: 10px;
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        # Botão grande melhorado para abrir
        btn_open_big = QPushButton("🔗 Abrir PDF no Visualizador Externo")
        btn_open_big.setFixedHeight(60)
        btn_open_big.clicked.connect(self.open_external)
        btn_open_big.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """)
        info_layout.addWidget(btn_open_big)
        
        layout.addWidget(info_frame)
    
    def open_external(self):
        """Abre o PDF no aplicativo padrão do sistema"""
        try:
            if os.path.exists(self.pdf_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.pdf_path)))
            else:
                QMessageBox.warning(self, "Erro", "Ficheiro PDF não encontrado!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir PDF:\n{str(e)}")


def mostrar_pdf(pdf_path: str, parent=None) -> bool:
    """
    Função principal para mostrar um PDF
    Retorna True se foi possível mostrar, False caso contrário
    """
    if not os.path.exists(pdf_path):
        QMessageBox.warning(parent, "Erro", "Ficheiro PDF não encontrado!")
        return False
    
    try:
        viewer = PDFViewer(pdf_path, parent)
        viewer.exec()
        return True
    except Exception as e:
        QMessageBox.critical(parent, "Erro", f"Erro ao abrir visualizador de PDF:\n{str(e)}")
        return False


def is_pdf_viewer_available() -> bool:
    """Verifica se o visualizador de PDF está disponível"""
    return WEB_ENGINE_AVAILABLE


def get_pdf_viewer_info() -> str:
    """Retorna informação sobre as capacidades do visualizador"""
    if WEB_ENGINE_AVAILABLE:
        return "✅ Biodesk PDF Viewer: Visualização integrada disponível (QtWebEngine)"
    else:
        return "📄 Biodesk PDF Viewer: Modo aplicativo externo (QtWebEngine não disponível)"
