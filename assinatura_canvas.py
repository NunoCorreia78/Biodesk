import sys
import os
from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt6.QtGui import (
import base64
from io import BytesIO
from biodesk_dialogs import BiodeskMessageBox
    from PyQt6.QtCore import pyqtSignal
    from PyQt6.QtWidgets import QApplication
from biodesk_ui_kit import BiodeskUIKit
"""
Canvas de Assinatura para Declaração de Saúde
Permite captura de assinatura digital para documentos
"""

    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem
)
    QPainter, QPen, QPixmap, QColor, QFont,
    QBrush, QPainterPath
)


class AssinaturaCanvas(QDialog):
    """
    Dialog para captura de assinatura digital
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✍️ Assinatura Digital")
        self.setModal(True)
        self.resize(600, 400)
        
        # Estado da assinatura
        self.drawing = False
        self.last_point = QPointF()
        self.signature_paths = []
        self.current_path = QPainterPath()
        
        # Canvas
        self.canvas_width = 500
        self.canvas_height = 200
        
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Inicializa interface do usuário"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título e instruções
        self.create_header(layout)
        
        # Área de assinatura
        self.create_signature_area(layout)
        
        # Botões de ação
        self.create_action_buttons(layout)
        
    def create_header(self, layout):
        """Cria cabeçalho com instruções"""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        
        # Título
        titulo = QLabel("✍️ Assinatura Digital")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        header_layout.addWidget(titulo)
        
        # Instruções
        instrucoes = QLabel(
            "🖱️ Use o mouse ou touch para assinar na área abaixo\n"
            "📝 Assine de forma clara e legível\n"
            "🔄 Use 'Limpar' para recomeçar se necessário"
        )
        instrucoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instrucoes.setStyleSheet("color: #7f8c8d; line-height: 1.6;")
        header_layout.addWidget(instrucoes)
        
        layout.addWidget(header_frame)
        
    def create_signature_area(self, layout):
        """Cria área de assinatura"""
        # Frame container
        signature_frame = QFrame()
        signature_frame.setFixedHeight(self.canvas_height + 40)
        signature_layout = QVBoxLayout(signature_frame)
        signature_layout.setContentsMargins(10, 10, 10, 10)
        
        # Label
        label = QLabel("📝 Área de Assinatura:")
        label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        label.setStyleSheet("color: #495057; margin-bottom: 5px;")
        signature_layout.addWidget(label)
        
        # Canvas de assinatura
        self.signature_widget = SignatureWidget(self.canvas_width, self.canvas_height)
        self.signature_widget.signature_changed.connect(self.on_signature_changed)
        signature_layout.addWidget(self.signature_widget)
        
        layout.addWidget(signature_frame)
        
    def create_action_buttons(self, layout):
        """Cria botões de ação"""
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        
        # Botão limpar
        self.btn_limpar = QPushButton("🗑️ Limpar")
        self.btn_limpar.setFixedSize(100, 35)
        self.btn_limpar.clicked.connect(self.limpar_assinatura)
        buttons_layout.addWidget(self.btn_limpar)
        
        buttons_layout.addStretch()
        
        # Botão cancelar
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setFixedSize(100, 35)
        self.btn_cancelar.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancelar)
        
        # Botão aceitar
        self.btn_aceitar = QPushButton("✅ Aceitar")
        self.btn_aceitar.setFixedSize(100, 35)
        self.btn_aceitar.setEnabled(False)
        self.btn_aceitar.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_aceitar)
        
        layout.addWidget(buttons_frame)
        
    def setup_styles(self):
        """Configura estilos"""
        BiodeskUIKit.apply_universal_button_style(self)
        
        # Estilos específicos para botões
        self.BiodeskUIKit.apply_universal_button_style(btn_limpar)
        
        self.BiodeskUIKit.apply_universal_button_style(btn_cancelar)
        
        self.BiodeskUIKit.apply_universal_button_style(btn_aceitar)
        
    def on_signature_changed(self, has_signature):
        """Callback quando assinatura muda"""
        self.btn_aceitar.setEnabled(has_signature)
        
    def limpar_assinatura(self):
        """Limpa a assinatura"""
        self.signature_widget.clear_signature()
        
    def get_signature_data(self):
        """Retorna dados da assinatura como bytes"""
        return self.signature_widget.get_signature_bytes()


class SignatureWidget(QFrame):
    """
    Widget personalizado para captura de assinatura
    """
    
    signature_changed = pyqtSignal(bool)
    
    def __init__(self, width=500, height=200):
        super().__init__()
        self.setFixedSize(width, height)
        self.canvas_width = width
        self.canvas_height = height
        
        # Estado do desenho
        self.drawing = False
        self.last_point = QPointF()
        self.paths = []
        self.current_path = QPainterPath()
        self.has_signature = False
        
        # Configurações de desenho
        self.pen_width = 2
        self.pen_color = QColor(0, 0, 0)
        
        # Estilo
        self.setStyleSheet("""
            SignatureWidget {
                background-color: #ffffff;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
            }
        """)
        
        # Cursor
        self.setCursor(Qt.CursorShape.CrossCursor)
        
    def mousePressEvent(self, event):
        """Inicia desenho da assinatura"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.position()
            self.current_path = QPainterPath()
            self.current_path.moveTo(self.last_point)
            
    def mouseMoveEvent(self, event):
        """Continua desenho da assinatura"""
        if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            current_point = event.position()
            self.current_path.lineTo(current_point)
            self.last_point = current_point
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Finaliza desenho da assinatura"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if not self.current_path.isEmpty():
                self.paths.append(self.current_path)
                self.has_signature = True
                self.signature_changed.emit(True)
                
    def paintEvent(self, event):
        """Desenha a assinatura"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Desenhar fundo com indicação
        if not self.has_signature:
            painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))
            painter.drawRect(10, 10, self.width() - 20, self.height() - 20)
            
            # Texto de indicação
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Normal))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "✍️ Clique e arraste para assinar"
            )
        
        # Desenhar assinatura
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, 
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Desenhar paths finalizados
        for path in self.paths:
            painter.drawPath(path)
            
        # Desenhar path atual (se desenhando)
        if self.drawing:
            painter.drawPath(self.current_path)
            
    def clear_signature(self):
        """Limpa a assinatura"""
        self.paths.clear()
        self.current_path = QPainterPath()
        self.has_signature = False
        self.signature_changed.emit(False)
        self.update()
        
    def get_signature_bytes(self):
        """Retorna assinatura como bytes (PNG)"""
        if not self.has_signature:
            return None
            
        # Criar pixmap com a assinatura
        pixmap = QPixmap(self.canvas_width, self.canvas_height)
        pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Desenhar assinatura
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        for path in self.paths:
            painter.drawPath(path)
            
        painter.end()
        
        # Converter para bytes
        byte_array = BytesIO()
        pixmap.save(byte_array, "PNG")
        byte_data = byte_array.getvalue()
        byte_array.close()
        
        return byte_data
        
    def get_signature_base64(self):
        """Retorna assinatura como string base64"""
        byte_data = self.get_signature_bytes()
        if byte_data:
            return base64.b64encode(byte_data).decode('utf-8')
        return None


# Exemplo de uso
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    canvas = AssinaturaCanvas()
    if canvas.exec() == canvas.DialogCode.Accepted:
        signature_data = canvas.get_signature_data()
        if signature_data:
            print(f"Assinatura capturada: {len(signature_data)} bytes")
        else:
            print("Nenhuma assinatura fornecida")
    
    sys.exit()
