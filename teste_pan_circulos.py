#!/usr/bin/env python3
"""
Teste específico para PAN dos círculos de calibração
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget, QLabel, QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
from iris_overlay_manager import IrisOverlayManager
import math

class TestePanCirculos(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔄 Teste PAN dos Círculos")
        self.setGeometry(100, 100, 1000, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Instruções
        instructions = QLabel("""
        <b>🔄 Teste PAN dos Círculos:</b><br><br>
        
        <b>FUNDO ESTÁTICO:</b><br>
        • Íris marrom: NÃO se move<br>
        • Pupila preta: NÃO se move<br><br>
        
        <b>CALIBRAÇÃO COM PAN:</b><br>
        • Pega central ciano: MOVE círculos<br>
        • Círculos tracejados: SE MOVEM com PAN<br>
        • Pegas verdes/vermelhas: SE MOVEM com PAN<br><br>
        
        <b>✅ Fundo deve permanecer fixo!</b><br>
        <b>🔄 Círculos devem se mover com PAN!</b>
        """)
        instructions.setStyleSheet("""
            QLabel { 
                background-color: #e8f5e8; 
                padding: 15px; 
                border-radius: 8px; 
                font-size: 11px; 
            }
        """)
        layout.addWidget(instructions)
        
        # Scene e view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Desabilita scrollbars
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Desabilita drag/scroll com mouse
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        # NÃO desabilitar interatividade, para permitir PAN dos círculos
        layout.addWidget(self.view)
        
        # Overlay manager
        self.overlay_manager = IrisOverlayManager(self.scene)

        # Botão para ajuste fino
        from PyQt6.QtWidgets import QPushButton
        self.btn_ajuste_fino = QPushButton("Ajuste Fino: OFF")
        self.btn_ajuste_fino.setCheckable(True)
        self.btn_ajuste_fino.setStyleSheet("font-size: 14px; padding: 8px; margin-bottom: 8px;")
        self.btn_ajuste_fino.clicked.connect(self.toggle_ajuste_fino)
        layout.addWidget(self.btn_ajuste_fino)

        # Configura teste
        self.create_background()
        # Remove elipses/círculos extra da cena (exceto fundo)
        for item in self.scene.items():
            if isinstance(item, QGraphicsEllipseItem) and not (hasattr(item, 'data') and item.data(0) == "FUNDO_ESTATICO"):
                self.scene.removeItem(item)

        self.setup_calibration()
        # Após iniciar a calibração, remove qualquer círculo extra que não seja:
        # - fundo estático (íris/pupila)
        # - círculos de calibração (devem ter atributo especial ou z-value)
        # - handles (devem ser QGraphicsEllipseItem mas com data ou z-value específico)
        for item in self.scene.items():
            # Mantém apenas fundo estático e overlays de calibração/handles
            if isinstance(item, QGraphicsEllipseItem):
                # Mantém fundo estático
                if hasattr(item, 'data') and item.data(0) == "FUNDO_ESTATICO":
                    continue
                # Mantém handles/círculos de calibração (z > 0 ou data especial)
                if hasattr(item, 'data') and item.data(0) in ("HANDLE_CALIB", "CIRCULO_CALIB"):
                    continue
                if hasattr(item, 'zValue') and item.zValue() >= 0:
                    continue
                # Remove qualquer outro círculo
                self.scene.removeItem(item)

        # Centraliza a view no fundo
        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self.view.centerOn(self.iris_bg)

    def toggle_ajuste_fino(self):
        enabled = self.btn_ajuste_fino.isChecked()
        self.overlay_manager.set_individual_mode(enabled)
        self.btn_ajuste_fino.setText(f"Ajuste Fino: {'ON' if enabled else 'OFF'}")
        # self.overlay_manager.redraw_spline_circles()  # Method does not exist, removed to avoid AttributeError
        
        print("🔄 === TESTE PAN DOS CÍRCULOS ===")
        print("✅ Fundo estático criado")
        print("🔄 Calibração com PAN habilitada")
        print("🎯 Teste: PAN move círculos, fundo permanece fixo!")
        
    def create_background(self):
        """Cria fundo estático que NÃO deve se mover"""
        # Íris (marrom)
        self.iris_bg = QGraphicsEllipseItem(250, 150, 300, 300)
        self.iris_bg.setBrush(QBrush(QColor(139, 69, 19, 100)))
        self.iris_bg.setPen(QPen(QColor(101, 67, 33), 2))
        self.iris_bg.setZValue(-10)
        self.iris_bg.setData(0, "FUNDO_ESTATICO")
        self.scene.addItem(self.iris_bg)
        
        # Pupila (preta)
        self.pupil_bg = QGraphicsEllipseItem(350, 250, 100, 100)
        self.pupil_bg.setBrush(QBrush(QColor(0, 0, 0, 150)))
        self.pupil_bg.setPen(QPen(QColor(50, 50, 50), 2))
        self.pupil_bg.setZValue(-5)
        self.pupil_bg.setData(0, "FUNDO_ESTATICO")
        self.scene.addItem(self.pupil_bg)
        
        print(f"🎨 Fundo estático criado:")
        print(f"   Íris: {self.iris_bg.rect()}")
        print(f"   Pupila: {self.pupil_bg.rect()}")
        print(f"   ⚠️  ESTES ELEMENTOS NÃO DEVEM SE MOVER!")
        
    def setup_calibration(self):
        """Inicia calibração com PAN habilitado"""
        # Inicia calibração em modo teste (PAN dos círculos, fundo protegido)
        self.overlay_manager.start_calibration(teste_pan=True)

        # Timer para verificar posições
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_positions)
        self.timer.start(1000)  # Verifica a cada 1 segundo

        # Posições iniciais do fundo
        self.initial_iris_pos = self.iris_bg.rect()
        self.initial_pupil_pos = self.pupil_bg.rect()

        # Redesenha círculos como spline se ajuste fino estiver ativo
        self.overlay_manager.redraw_spline_circles()
        
    def check_positions(self):
        """Verifica se o fundo se moveu"""
        current_iris = self.iris_bg.rect()
        current_pupil = self.pupil_bg.rect()
        
        if (current_iris != self.initial_iris_pos or 
            current_pupil != self.initial_pupil_pos):
            print("🚨 ERRO: FUNDO SE MOVEU!")
            print(f"   Íris inicial: {self.initial_iris_pos}")
            print(f"   Íris atual: {current_iris}")
            print(f"   Pupila inicial: {self.initial_pupil_pos}")
            print(f"   Pupila atual: {current_pupil}")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestePanCirculos()
    window.show()
    sys.exit(app.exec())
