"""
Janela de Terapia Quântica - Versão Zero
Interface mínima para começar do zero
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os
from biodesk_dialogs import BiodeskMessageBox

# Import da classe base mínima
from terapia_quantica import TerapiaQuantica

class TerapiaQuanticaWindow(QMainWindow):
    """
    Janela mínima para Terapia Quântica
    Versão zero - para começar do zero
    """
    
    def __init__(self, paciente_data=None, iris_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.iris_data = iris_data
        
        # Configuração
        nome = paciente_data.get("nome", "Sem Paciente") if paciente_data else "Sem Paciente"
        self.setWindowTitle(f'🌟 Terapia Quântica - {nome}')
        self.setMinimumSize(800, 600)
        
        # Ícone se existir
        icon_path = os.path.join("assets", "quantum.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Interface
        self.init_ui()
    
    def init_ui(self):
        """Interface mínima"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título principal
        titulo = QLabel("🌟 TERAPIA QUÂNTICA - VERSÃO ZERO 🌟")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #4a148c;
            padding: 25px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #e1bee7, stop:0.5 white, stop:1 #e1bee7);
            border-radius: 15px;
            border: 3px solid #9c27b0;
            margin-bottom: 20px;
        """)
        layout.addWidget(titulo)
        
        # Informações do paciente
        if self.paciente_data:
            info_paciente = QLabel(f"👤 Paciente: {self.paciente_data.get('nome', 'N/A')}")
            info_paciente.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_paciente.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #666;
                padding: 10px;
                background: #f8f8f8;
                border-radius: 8px;
                margin-bottom: 20px;
            """)
            layout.addWidget(info_paciente)
        
        # Área de desenvolvimento vazia
        area_dev = QLabel("""
        🔬 ÁREA COMPLETAMENTE VAZIA PARA DESENVOLVIMENTO
        
        Esta é uma tela em branco onde você pode:
        
        ✨ Implementar análise de frequências
        ✨ Criar protocolos terapêuticos
        ✨ Desenvolver biofeedback
        ✨ Adicionar análise de íris
        ✨ Criar seu próprio sistema de medicina quântica
        
        🎯 COMECE AQUI O SEU CÓDIGO!
        """)
        area_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_dev.setStyleSheet("""
            font-size: 16px;
            color: #444;
            padding: 40px;
            background: white;
            border: 3px dashed #9c27b0;
            border-radius: 15px;
            margin: 20px 0;
        """)
        layout.addWidget(area_dev)
        
        # Botões básicos
        botoes_layout = self.criar_botoes()
        layout.addLayout(botoes_layout)
        
        # Espaçador
        layout.addStretch()
    
    def criar_botoes(self):
        """Cria botões básicos"""
        from PyQt6.QtWidgets import QHBoxLayout
        
        layout = QHBoxLayout()
        
        # Botão de teste
        btn_teste = QPushButton("🧪 Teste do Sistema Zero")
        btn_teste.clicked.connect(self.teste_zero)
        self.estilizar_botao(btn_teste, "#4a148c")
        layout.addWidget(btn_teste)
        
        # Espaçador
        layout.addStretch()
        
        # Botão fechar
        btn_fechar = QPushButton("❌ Fechar")
        btn_fechar.clicked.connect(self.close)
        self.estilizar_botao(btn_fechar, "#d32f2f")
        layout.addWidget(btn_fechar)
        
        return layout
    
    def estilizar_botao(self, botao, cor):
        """Estilo básico para botões"""
        botao.setStyleSheet(f"""
            QPushButton {{
                background: {cor};
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 25px;
                border-radius: 8px;
                border: none;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background: {cor}aa;
            }}
            QPushButton:pressed {{
                background: {cor}77;
            }}
        """)
    
    def teste_zero(self):
        """Teste da versão zero"""
        BiodeskMessageBox.information(
            self,
            "Sistema Zero Funcionando",
            """✅ TERAPIA QUÂNTICA - VERSÃO ZERO FUNCIONANDO!
            
🎯 Base mínima carregada com sucesso
🔧 Pronto para desenvolvimento do zero
🌟 Interface limpa e funcional

💡 Agora você pode começar a implementar
   suas funcionalidades de medicina quântica!"""
        )

# Compatibilidade com main_window.py
def criar_janela_terapia_quantica(paciente_data=None, iris_data=None):
    """Função de compatibilidade"""
    return TerapiaQuanticaWindow(paciente_data, iris_data)
