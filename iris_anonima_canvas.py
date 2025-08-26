from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QHBoxLayout, 
                            QFileDialog, QLabel, QGraphicsView, QGraphicsScene,
                            QDialog, QSizePolicy, QFrame, QSlider)
from PyQt6.QtCore import Qt, QSize, QTimer, QPointF, QRectF, QEvent
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QPainterPath, QKeyEvent, QKeySequence
import cv2
import os
import numpy as np
import datetime
from iris_canvas import IrisCanvas
from biodesk_dialogs import BiodeskMessageBox

class IrisAnonimaCanvas(QWidget):
    """
    Janela de análise de íris anónima sem associação a utente.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Análise de Íris (modo anónimo)")
        
        # REMOVIDO: CSS do widget pai que estava a sobrepor o estilo individual dos botões
        # Agora cada botão tem o seu próprio estilo aplicado individualmente
        self.setObjectName("IrisAnonimaCanvas")
        
        self.setup_ui()

    def apply_pastel_style(self, button, pastel_color):
        """Aplica estilo pastel suave aos botões - DESATIVADO para usar BiodeskStyleManager"""
        # COMENTADO: Deixar o BiodeskStyleManager aplicar os estilos uniformes
        # button.setFixedHeight(45)
        # print(f"🎨 BiodeskStyleManager controla: {button.text()}")
        pass

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barra de botões alinhada da esquerda para direita
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 15, 20, 15)
        btn_layout.setSpacing(12)
        
        # Botão principal à esquerda - Capturar imagem (função primária)
        self.btn_capturar = QPushButton("📷 Capturar Imagem da Íris")
        self.btn_capturar.setMinimumSize(200, 45)
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_capturar, "#a8e6cf")  # Verde pastel suave
        self.btn_capturar.setToolTip("Abrir câmera para capturar imagem da íris em tempo real")
        btn_layout.addWidget(self.btn_capturar)
        
        # Espaço maior para separar visualmente a função principal das ferramentas
        btn_layout.addSpacing(40)
        
        # Botão para calibração
        self.btn_calibracao = QPushButton("Calibração: OFF")
        self.btn_calibracao.setCheckable(True)
        self.btn_calibracao.setChecked(False)
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_calibracao, "#dceefb")  # Azul pastel suave
        self.btn_calibracao.setToolTip("Ativar/desativar modo de calibração para ajustar centro e raios da íris")
        btn_layout.addWidget(self.btn_calibracao)
        
        # Botão para ajuste fino
        self.btn_ajuste_fino = QPushButton("Ajuste Fino: OFF")
        self.btn_ajuste_fino.setCheckable(True)
        self.btn_ajuste_fino.setChecked(False)
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_ajuste_fino, "#ffd3e1")  # Rosa pastel suave
        self.btn_ajuste_fino.setToolTip("Ativar/desativar ajuste fino (morphing) para deformar íris e pupila")
        btn_layout.addWidget(self.btn_ajuste_fino)
        
        # Botões de zoom
        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.setToolTip("Ampliar imagem")
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_zoom_in, "#ffeaa7")  # Amarelo pastel suave
        btn_layout.addWidget(self.btn_zoom_in)
        
        self.btn_zoom_out = QPushButton("🔍-")
        self.btn_zoom_out.setToolTip("Reduzir imagem")
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_zoom_out, "#ffeaa7")  # Amarelo pastel suave
        btn_layout.addWidget(self.btn_zoom_out)
        
        self.btn_zoom_fit = QPushButton("📐")
        self.btn_zoom_fit.setToolTip("Ajustar imagem à janela")
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_zoom_fit, "#e6d7ff")  # Roxo pastel suave
        btn_layout.addWidget(self.btn_zoom_fit)
        
        # Botão para ocultar/mostrar mapa
        self.btn_ocultar_mapa = QPushButton("👁️ Ver Mapa")
        self.btn_ocultar_mapa.setToolTip("Ocultar/mostrar o mapa da íris e todos os overlays")
        # DESATIVADO: Deixar BiodeskStyleManager aplicar estilos uniformes
        # self._style_modern_button(self.btn_ocultar_mapa, "#f8f9fa")  # Cinza muito claro
        btn_layout.addWidget(self.btn_ocultar_mapa)
        
        # Espaço flexível à direita
        btn_layout.addStretch()
        
        # Adicionar widgets ao layout principal
        layout.addLayout(btn_layout)
        
        # Adicionar uma linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #cccccc; margin: 0 10px;")
        layout.addWidget(separator)
        
        # Canvas SEM TOOLBAR (para evitar duplicação)
        self.iris_canvas = IrisCanvas(paciente_data=None, criar_toolbar=False)
        self.iris_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        if hasattr(self.iris_canvas, 'btn_layout'):
            self.iris_canvas.btn_layout.setParent(None)
            
        layout.addWidget(self.iris_canvas)
        
        # Conectar os botões às funções do canvas após a criação
        self.connect_toolbar_buttons()
        
        # Configurar a janela
        self.setMinimumSize(1000, 700)

    def connect_toolbar_buttons(self):
        """Conecta os botões da toolbar às funções do canvas"""
        try:
            # Conectar botões de calibração e ajuste fino
            if hasattr(self.iris_canvas, 'toggle_calibracao'):
                self.btn_calibracao.clicked.connect(self.iris_canvas.toggle_calibracao)
            if hasattr(self.iris_canvas, 'toggle_ajuste_fino'):
                self.btn_ajuste_fino.clicked.connect(self.iris_canvas.toggle_ajuste_fino)
            
            # Conectar botões de zoom
            if hasattr(self.iris_canvas, 'zoom_in'):
                self.btn_zoom_in.clicked.connect(self.iris_canvas.zoom_in)
            if hasattr(self.iris_canvas, 'zoom_out'):
                self.btn_zoom_out.clicked.connect(self.iris_canvas.zoom_out)
            if hasattr(self.iris_canvas, 'zoom_fit'):
                self.btn_zoom_fit.clicked.connect(self.iris_canvas.zoom_fit)
            
            # Conectar botão de ocultar mapa
            if hasattr(self.iris_canvas, 'toggle_mapa_visibilidade'):
                self.btn_ocultar_mapa.clicked.connect(self.iris_canvas.toggle_mapa_visibilidade)
        except Exception as e:
            print(f"[DEBUG] Erro ao conectar botões: {e}")

    def capturar_imagem(self):
        """Método simplificado para capturar imagem da câmera"""
        try:
            BiodeskMessageBox.information(self, "Captura de Imagem", "Função de captura em desenvolvimento.\nPor favor, carregue uma imagem usando o menu Arquivo > Abrir.")
        except Exception as e:
            print(f"[ERRO] Captura de imagem: {e}")
