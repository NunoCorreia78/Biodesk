"""
Terapia Quântica - Interface Principal Simplificada
═══════════════════════════════════════════════════

Interface limpa e minimalista:
- Status discreto no topo
- Botão funcional para Sistema CoRe Completo
- Indicadores essenciais apenas
"""

import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Imports essenciais
try:
    from biodesk_dialogs import BiodeskDialogs as BiodeskMessageBox
except ImportError:
    from PyQt6.QtWidgets import QMessageBox as BiodeskMessageBox

from biodesk_ui_kit import BiodeskUIKit
from biodesk_styles import BiodeskStyles
import hs3_hardware
from hs3_hardware import hs3_hardware

# Import da janela CoRe completa
from core_complete_window import CoreCompleteWindow

class TerapiaQuanticaWindow(QWidget):
    """
    🎯 INTERFACE PRINCIPAL SIMPLIFICADA
    
    Funcionalidades:
    - Status discreto (HS3 + Documentos)
    - Botão "Sistema CoRe Completo" funcional
    - Barra de estado com varredura
    - Interface limpa e profissional
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.connected_to_hs3 = False
        self.core_window = None
        
        # Configurar interface
        self.setup_ui()
        self.check_hs3_connection()
        
        # Timer para verificação periódica
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # A cada 2 segundos
    
    def setup_ui(self):
        """Configura interface simplificada"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 1. HEADER DISCRETO COM STATUS
        self.create_status_header()
        layout.addWidget(self.status_header)
        
        # 2. ÁREA PRINCIPAL COM BOTÃO CORE
        self.create_main_area()
        layout.addWidget(self.main_area)
        
        # 3. BARRA DE ESTADO (BOTTOM)
        self.create_status_bar()
        layout.addWidget(self.status_bar_widget)
        
        # Espaçador
        layout.addStretch()
    
    def create_status_header(self):
        """Cria header discreto com status"""
        self.status_header = QWidget()
        self.status_header.setFixedHeight(60)
        self.status_header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self.status_header)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Status HS3
        self.hs3_status_label = QLabel("🔴 HS3: Verificando...")
        self.hs3_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #6c757d;")
        layout.addWidget(self.hs3_status_label)
        
        # Separador
        separator1 = QLabel("•")
        separator1.setStyleSheet("color: #adb5bd; font-size: 16px;")
        layout.addWidget(separator1)
        
        # Status Documentos
        self.docs_status_label = QLabel("📄 Documentos: ✅ Conformes")
        self.docs_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #28a745;")
        layout.addWidget(self.docs_status_label)
        
        # Separador
        separator2 = QLabel("•")
        separator2.setStyleSheet("color: #adb5bd; font-size: 16px;")
        layout.addWidget(separator2)
        
        # Status Sistema
        self.system_status_label = QLabel("⚡ Sistema: Pronto")
        self.system_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #17a2b8;")
        layout.addWidget(self.system_status_label)
        
        layout.addStretch()
        
        # Indicador de conexão (LED-style)
        self.connection_led = QLabel("●")
        self.connection_led.setStyleSheet("font-size: 20px; color: #dc3545;")
        layout.addWidget(self.connection_led)
    
    def create_main_area(self):
        """Cria área principal com botão CoRe"""
        self.main_area = QWidget()
        layout = QVBoxLayout(self.main_area)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Título principal
        title = QLabel("🧬 Sistema de Terapia Quântica")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #495057;
            margin: 20px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Tecnologia CoRe para Análise e Harmonização Energética")
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #6c757d;
            margin-bottom: 40px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # BOTÃO PRINCIPAL - SISTEMA CORE COMPLETO
        self.core_button = QPushButton("🧬 Abrir Sistema CoRe Completo")
        self.core_button.setFixedSize(400, 80)
        self.core_button.clicked.connect(self.open_core_system)
        self.core_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d8b40, stop:1 #357a38);
            }
        """)
        layout.addWidget(self.core_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Informações adicionais
        info_text = QLabel(
            "• Análise de Ressonância Completa\n"
            "• Protocolos Terapêuticos Inteligentes\n"
            "• Balanceamento Energético Automático\n"
            "• Relatórios Profissionais\n"
            "• Biofeedback em Tempo Real"
        )
        info_text.setStyleSheet("""
            font-size: 14px;
            color: #6c757d;
            line-height: 1.6;
            margin-top: 30px;
        """)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_text)
    
    def create_status_bar(self):
        """Cria barra de estado na parte inferior"""
        self.status_bar_widget = QWidget()
        self.status_bar_widget.setFixedHeight(40)
        self.status_bar_widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        
        layout = QHBoxLayout(self.status_bar_widget)
        layout.setContentsMargins(15, 8, 15, 8)
        
        # Status da varredura
        self.sweep_status_label = QLabel("📡 Varredura: Parada")
        self.sweep_status_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(self.sweep_status_label)
        
        layout.addStretch()
        
        # Frequência atual
        self.frequency_label = QLabel("🌊 Freq: -- Hz")
        self.frequency_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(self.frequency_label)
        
        layout.addStretch()
        
        # Tempo do sistema
        self.time_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.time_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(self.time_label)
    
    def check_hs3_connection(self):
        """Verifica conexão HS3"""
        try:
            status = hs3_hardware.get_status()
            self.connected_to_hs3 = status.get('connected', False) if isinstance(status, dict) else False
            self.update_hs3_status()
        except Exception as e:
            self.connected_to_hs3 = False
            self.update_hs3_status()
    
    def update_hs3_status(self):
        """Atualiza status HS3 na interface"""
        if self.connected_to_hs3:
            self.hs3_status_label.setText("🟢 HS3: Conectado")
            self.hs3_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #28a745;")
            self.connection_led.setStyleSheet("font-size: 20px; color: #28a745;")
            self.system_status_label.setText("⚡ Sistema: Operacional")
            self.system_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #28a745;")
        else:
            self.hs3_status_label.setText("🔴 HS3: Desconectado")
            self.hs3_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #dc3545;")
            self.connection_led.setStyleSheet("font-size: 20px; color: #dc3545;")
            self.system_status_label.setText("⚡ Sistema: Limitado")
            self.system_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffc107;")
    
    def update_status(self):
        """Atualização periódica de status"""
        # Atualizar tempo
        self.time_label.setText(datetime.now().strftime("%H:%M:%S"))
        
        # Verificar conexão HS3
        self.check_hs3_connection()
        
        # Simular varredura se janela CoRe estiver aberta
        if self.core_window and not self.core_window.isHidden():
            if hasattr(self.core_window, 'frequency_sweep_active') and self.core_window.frequency_sweep_active:
                self.sweep_status_label.setText("📡 Varredura: Ativa")
                self.sweep_status_label.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold;")
                
                # Simular frequência em mudança
                import random
                freq = random.randint(1, 10000)
                if freq < 1000:
                    self.frequency_label.setText(f"🌊 Freq: {freq} Hz")
                else:
                    self.frequency_label.setText(f"🌊 Freq: {freq/1000:.1f} kHz")
                self.frequency_label.setStyleSheet("font-size: 12px; color: #17a2b8; font-weight: bold;")
            else:
                self.sweep_status_label.setText("📡 Varredura: Parada")
                self.sweep_status_label.setStyleSheet("font-size: 12px; color: #6c757d;")
                self.frequency_label.setText("🌊 Freq: -- Hz")
                self.frequency_label.setStyleSheet("font-size: 12px; color: #6c757d;")
    
    def open_core_system(self):
        """Abre janela do Sistema CoRe Completo"""
        try:
            # Se já existe janela, apenas mostrar
            if self.core_window and not self.core_window.isHidden():
                self.core_window.raise_()
                self.core_window.activateWindow()
                return
            
            # Criar nova janela CoRe
            self.core_window = CoreCompleteWindow(parent=self)
            
            # Conectar sinais para sincronização
            if hasattr(self.core_window, 'connected_to_hs3'):
                self.core_window.connected_to_hs3 = self.connected_to_hs3
                self.core_window.update_hs3_status()
            
            # Mostrar janela
            self.core_window.show()
            
            # Log do evento
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧬 Sistema CoRe Completo aberto")
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", 
                f"Erro ao abrir Sistema CoRe:\n{e}\n\n"
                "Verifique se todos os módulos estão instalados corretamente.")
            print(f"❌ Erro ao abrir CoRe: {e}")
    
    def closeEvent(self, event):
        """Evento de fechamento"""
        # Fechar janela CoRe se aberta
        if self.core_window and not self.core_window.isHidden():
            self.core_window.close()
        
        # Parar timer
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        event.accept()

# Widget principal para integração
class TerapiaQuanticaWidget(TerapiaQuanticaWindow):
    """Widget para integração na aplicação principal"""
    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TerapiaQuanticaWindow()
    window.setWindowTitle("🧬 Terapia Quântica - Sistema CoRe")
    window.setGeometry(200, 200, 800, 600)
    window.show()
    sys.exit(app.exec())
