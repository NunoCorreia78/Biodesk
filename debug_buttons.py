"""
Teste SIMPLES para debug do dimensionamento de botões
"""

import sys
import os
sys.path.insert(0, r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk")

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

try:
    from biodesk_styles import BiodeskStyles, ButtonType
except ImportError as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)

class SimpleTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Debug - Dimensionamento de Botões")
        self.setGeometry(100, 100, 800, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Teste 1: Botão PyQt normal
        normal_btn = QPushButton("💾 Botão PyQt Normal")
        layout.addWidget(normal_btn)
        
        # Teste 2: Botão BiodeskStyles
        biodesk_btn = BiodeskStyles.create_button("💾 Guardar Dados", ButtonType.SAVE)
        layout.addWidget(biodesk_btn)
        
        # Teste 3: Botão com texto longo
        long_btn = BiodeskStyles.create_button("🔍 Navegação Rápida com Texto Muito Longo Para Testar", ButtonType.NAVIGATION)
        layout.addWidget(long_btn)
        
        # Teste 4: Botão simples
        simple_btn = BiodeskStyles.create_button("OK", ButtonType.DIALOG)
        layout.addWidget(simple_btn)
        
        # Teste 5: Botão só com CSS básico
        css_btn = QPushButton("🔧 Botão CSS Básico")
        css_btn.setStyleSheet("""
            QPushButton {
                font-family: "Segoe UI";
                font-size: 13px;
                padding: 12px 20px;
                background: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        layout.addWidget(css_btn)
        
        layout.addStretch()
        
        print("🔍 Compare os botões:")
        print("1. Normal PyQt")
        print("2. BiodeskStyles")
        print("3. Texto longo")
        print("4. Texto curto")
        print("5. CSS básico")

def main():
    app = QApplication(sys.argv)
    window = SimpleTestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
