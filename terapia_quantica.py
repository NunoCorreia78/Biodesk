import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, 
    QGroupBox, QGridLayout, QSlider, QProgressBar, QComboBox, QSpinBox,
    QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
import os
import random
import time

def estilizar_botao_quantico(botao, cor="#4a148c", hover="#7b1fa2"):
    """Estiliza botões com tema quântico"""
    botao.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cor}, stop:1 #9c27b0);
            color: white;
            border-radius: 10px;
            padding: 12px 20px;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid transparent;
        }}
        QPushButton:hover {{
            background: {hover};
            border-color: #e1bee7;
        }}
        QPushButton:pressed {{
            background: #3f006f;
        }}
    """)

class TerapiaQuantica(QWidget):
    def __init__(self, paciente_data=None, iris_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.iris_data = iris_data  # dict com 'tipo' e 'caminho'
        self.setWindowTitle(f'Terapia Quântica - {paciente_data.get("nome", "Paciente") if paciente_data else "Sem Paciente"}')
        self.setStyleSheet("""
            QWidget {
                background-color: #f3e5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9c27b0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4a148c;
            }
        """)
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_energia)
        self.sessao_ativa = False
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = QLabel('🌟 Terapia Quântica Bioenergética 🌟')
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4a148c;
            margin: 20px;
            padding: 15px;
            background: white;
            border-radius: 15px;
            border: 3px solid #9c27b0;
        """)
        main_layout.addWidget(header)
        
        # Área de rolagem para o conteúdo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Painel de Informações do Paciente
        if self.paciente_data:
            info_group = QGroupBox("Informações do Paciente")
            info_layout = QGridLayout(info_group)
            
            info_layout.addWidget(QLabel("Nome:"), 0, 0)
            info_layout.addWidget(QLabel(self.paciente_data.get('nome', 'N/A')), 0, 1)
            
            info_layout.addWidget(QLabel("Idade:"), 1, 0)
            info_layout.addWidget(QLabel(str(self.paciente_data.get('idade', 'N/A'))), 1, 1)
            
            content_layout.addWidget(info_group)
        
        # Painel de Configurações Quânticas
        config_group = QGroupBox("Configurações de Frequência Quântica")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Frequência Base (Hz):"), 0, 0)
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 1000)
        self.freq_spin.setValue(432)
        config_layout.addWidget(self.freq_spin, 0, 1)
        
        config_layout.addWidget(QLabel("Intensidade:"), 1, 0)
        self.intensidade_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensidade_slider.setRange(1, 10)
        self.intensidade_slider.setValue(5)
        config_layout.addWidget(self.intensidade_slider, 1, 1)
        
        config_layout.addWidget(QLabel("Modalidade:"), 2, 0)
        self.modalidade_combo = QComboBox()
        self.modalidade_combo.addItems([
            "Harmonização Chakras",
            "Equilibrio Energético",
            "Limpeza Áurica",
            "Ativação Celular",
            "Cura Emocional"
        ])
        config_layout.addWidget(self.modalidade_combo, 2, 1)
        
        content_layout.addWidget(config_group)
        
        # Painel de Monitoramento
        monitor_group = QGroupBox("Monitoramento Energético")
        monitor_layout = QVBoxLayout(monitor_group)
        
        self.energia_label = QLabel("Nível de Energia: 0%")
        self.energia_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.energia_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a148c;")
        monitor_layout.addWidget(self.energia_label)
        
        self.energia_progress = QProgressBar()
        self.energia_progress.setRange(0, 100)
        self.energia_progress.setValue(0)
        self.energia_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #9c27b0;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f8f8;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9c27b0, stop:1 #e91e63);
                border-radius: 3px;
            }
        """)
        monitor_layout.addWidget(self.energia_progress)
        
        content_layout.addWidget(monitor_group)
        
        # Painel de Controle
        control_group = QGroupBox("Controle da Sessão")
        control_layout = QHBoxLayout(control_group)
        
        self.btn_iniciar = QPushButton("🚀 Iniciar Sessão")
        self.btn_parar = QPushButton("⏹️ Parar")
        self.btn_pausar = QPushButton("⏸️ Pausar")
        self.btn_relatorio = QPushButton("📊 Relatório")
        
        for btn in [self.btn_iniciar, self.btn_parar, self.btn_pausar, self.btn_relatorio]:
            estilizar_botao_quantico(btn)
            control_layout.addWidget(btn)
        
        self.btn_parar.setEnabled(False)
        self.btn_pausar.setEnabled(False)
        
        content_layout.addWidget(control_group)
        
        # Área de Notas
        notas_group = QGroupBox("Notas da Sessão")
        notas_layout = QVBoxLayout(notas_group)
        
        self.notas_edit = QTextEdit()
        self.notas_edit.setPlaceholderText("Observações durante a sessão de terapia quântica...")
        self.notas_edit.setMaximumHeight(150)
        notas_layout.addWidget(self.notas_edit)
        
        content_layout.addWidget(notas_group)
        
        # Configurar scroll area
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Conectar sinais
        self.btn_iniciar.clicked.connect(self.iniciar_sessao)
        self.btn_parar.clicked.connect(self.parar_sessao)
        self.btn_pausar.clicked.connect(self.pausar_sessao)
        self.btn_relatorio.clicked.connect(self.gerar_relatorio)
        
        # Adicionar visualização de íris se disponível
        if self.iris_data:
            iris_group = QGroupBox(f"Visualização da Íris - {'Olho Esquerdo' if self.iris_data.get('tipo') == 'esq' else 'Olho Direito'}")
            iris_layout = QVBoxLayout(iris_group)
            
            # Importar IrisCanvas para visualização
            from iris_canvas import IrisCanvas
            self.iris_view = IrisCanvas(
                paciente_data=self.paciente_data,
                caminho_imagem=self.iris_data.get('caminho'),
                tipo=self.iris_data.get('tipo')
            )
            
            # Configurando a visualização da íris para o contexto de terapia
            # Não precisamos fazer nada especial pois os botões de calibragem já foram removidos
            
            # Adicionando ao layout com altura fixa
            self.iris_view.setFixedHeight(400)
            iris_layout.addWidget(self.iris_view)
            content_layout.addWidget(iris_group)
        
    def iniciar_sessao(self):
        """Inicia uma sessão de terapia quântica"""
        self.sessao_ativa = True
        self.btn_iniciar.setEnabled(False)
        self.btn_parar.setEnabled(True)
        self.btn_pausar.setEnabled(True)
        
        # Registrar início da sessão
        modalidade = self.modalidade_combo.currentText()
        frequencia = self.freq_spin.value()
        intensidade = self.intensidade_slider.value()
        
        self.notas_edit.append(f"🟢 Sessão iniciada - {modalidade} (F:{frequencia}Hz, I:{intensidade}/10)")
        
        # Iniciar timer de monitoramento
        self.timer.start(1000)  # Atualiza a cada segundo
        
        QMessageBox.information(self, "Sessão Iniciada", 
                               f"Terapia Quântica iniciada com {modalidade}")
    
    def parar_sessao(self):
        """Para a sessão atual"""
        self.sessao_ativa = False
        self.timer.stop()
        self.btn_iniciar.setEnabled(True)
        self.btn_parar.setEnabled(False)
        self.btn_pausar.setEnabled(False)
        
        self.energia_progress.setValue(0)
        self.energia_label.setText("Nível de Energia: 0%")
        self.notas_edit.append("🔴 Sessão terminada")
        
        QMessageBox.information(self, "Sessão Terminada", "Sessão de terapia quântica finalizada")
    
    def pausar_sessao(self):
        """Pausa/retoma a sessão"""
        if self.timer.isActive():
            self.timer.stop()
            self.btn_pausar.setText("▶️ Retomar")
            self.notas_edit.append("⏸️ Sessão pausada")
        else:
            self.timer.start(1000)
            self.btn_pausar.setText("⏸️ Pausar")
            self.notas_edit.append("▶️ Sessão retomada")
    
    def atualizar_energia(self):
        """Atualiza o nível de energia simulado"""
        if self.sessao_ativa:
            # Simular variação de energia
            valor_atual = self.energia_progress.value()
            nova_energia = min(100, valor_atual + random.randint(1, 5))
            
            self.energia_progress.setValue(nova_energia)
            self.energia_label.setText(f"Nível de Energia: {nova_energia}%")
            
            # Verificar se chegou ao máximo
            if nova_energia >= 100:
                self.parar_sessao()
                QMessageBox.information(self, "Sessão Completa", 
                                       "Nível de energia máximo atingido! Sessão finalizada.")
    
    def gerar_relatorio(self):
        """Gera relatório da sessão"""
        if not self.paciente_data:
            QMessageBox.warning(self, "Erro", "Nenhum paciente associado para gerar relatório")
            return
        
        notas = self.notas_edit.toPlainText()
        modalidade = self.modalidade_combo.currentText()
        frequencia = self.freq_spin.value()
        intensidade = self.intensidade_slider.value()
        
        relatorio = f"""
        RELATÓRIO DE TERAPIA QUÂNTICA
        ===========================
        
        Paciente: {self.paciente_data.get('nome', 'N/A')}
        Data: {time.strftime('%d/%m/%Y %H:%M')}
        
        Configurações:
        - Modalidade: {modalidade}
        - Frequência: {frequencia} Hz
        - Intensidade: {intensidade}/10
        
        Observações:
        {notas}
        
        Status: Sessão {'Ativa' if self.sessao_ativa else 'Finalizada'}
        """
        
        QMessageBox.information(self, "Relatório Gerado", 
                               f"Relatório salvo para {self.paciente_data.get('nome', 'paciente')}")
        
        # Aqui poderia salvar o relatório em arquivo ou base de dados
        print(relatorio)  # Por agora apenas imprime