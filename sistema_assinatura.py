"""
🖋️ MÓDULO: Sistema de Assinatura Digital
Sistema reutilizável para assinatura de documentos (declarações, consentimentos, etc.)

Funcionalidades:
- ✅ Canvas duplo para paciente + profissional
- ✅ Interface profissional e limpa
- ✅ Botões de limpar individuais
- ✅ Validação de assinaturas
- ✅ Retorno de dados estruturados
"""

import os
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
                             QPushButton, QGraphicsView, QGraphicsScene, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QPixmap, QColor

from biodesk_ui_kit import BiodeskUIKit
from biodesk_dialogs import mostrar_erro, mostrar_sucesso

class CanvasAssinatura(QGraphicsView):
    """Canvas individual para desenhar assinatura"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        # ✅ CANVAS OTIMIZADO - 400x120 (tamanho ideal para assinatura confortável)
        self.setFixedSize(400, 120)
        self.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #667eea;
                border-radius: 8px;
                background-color: white;
            }
        """)
        
        # ✅ REMOVER BARRAS DE DESLOCAÇÃO
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # ✅ Política de redimensionamento flexível
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        self.drawing = False
        self.last_point = QPointF()
        self.pen = QPen(QColor(0, 0, 0), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        
        # ✅ CENA AJUSTADA para o novo tamanho - 396x116 (4px de margem para a borda)
        self.scene.setSceneRect(0, 0, 396, 116)
        
        # ✅ ADICIONAR LINHA DE ORIENTAÇÃO PARA ASSINATURA
        self._adicionar_linha_orientacao()
        
    def _adicionar_linha_orientacao(self):
        """Adiciona linha de orientação sutil para guiar a assinatura"""
        # Linha horizontal no centro vertical do canvas, com margem lateral
        margem_lateral = 40  # Espaço nas laterais
        y_centro = self.scene.height() / 2
        x_inicio = margem_lateral
        x_fim = self.scene.width() - margem_lateral
        
        # Criar linha de orientação sutil (cinza claro, tracejada)
        pen_orientacao = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine)
        self.linha_orientacao = self.scene.addLine(x_inicio, y_centro, x_fim, y_centro, pen_orientacao)
        
        # Marcar como linha de orientação para não ser incluída na verificação de assinatura
        self.linha_orientacao.setData(0, "linha_orientacao")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = self.mapToScene(event.position().toPoint())
            
    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            current_point = self.mapToScene(event.position().toPoint())
            self.scene.addLine(
                self.last_point.x(), self.last_point.y(),
                current_point.x(), current_point.y(),
                self.pen
            )
            self.last_point = current_point
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            
    def limpar(self):
        """Limpa o canvas preservando a linha de orientação"""
        # Remover todos os itens exceto a linha de orientação
        for item in self.scene.items():
            if item.data(0) != "linha_orientacao":
                self.scene.removeItem(item)
        
        # Se a linha de orientação foi removida acidentalmente, recriar
        if not any(item.data(0) == "linha_orientacao" for item in self.scene.items()):
            self._adicionar_linha_orientacao()
        
    def tem_assinatura(self):
        """Verifica se há assinatura no canvas (excluindo linha de orientação)"""
        # Contar apenas itens que não são linha de orientação
        itens_assinatura = [item for item in self.scene.items() 
                           if item.data(0) != "linha_orientacao"]
        return len(itens_assinatura) > 0
        
    def obter_imagem(self):
        """Obtém imagem da assinatura como pixmap"""
        if not self.tem_assinatura():
            return None
            
        pixmap = QPixmap(int(self.scene.width()), int(self.scene.height()))
        pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(pixmap)
        self.scene.render(painter)
        painter.end()
        return pixmap

class DialogoAssinatura(QDialog):
    """
    Diálogo profissional para captura de assinaturas lado a lado
    """
    assinaturas_capturadas = pyqtSignal(dict)  # Sinal com dados das assinaturas
    
    def __init__(self, parent=None, titulo_documento="Documento"):
        super().__init__(parent)
        self.titulo_documento = titulo_documento
        self.paciente_data = None
        
        self.init_ui()
        
    def init_ui(self):
        """Interface profissional com layout centrado"""
        self.setWindowTitle(f"✍️ Assinatura Digital - {self.titulo_documento}")
        self.setModal(True)
        self.resize(1100, 480)  # Janela ligeiramente maior para acomodar canvas maiores
        
        # Estilo geral
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # Espaçamento reduzido
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Título
        titulo = QLabel(f"📋 Assinatura Digital - {self.titulo_documento}")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                text-align: center;
                padding: 12px;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # ✅ ÁREA DE ASSINATURAS CENTRADA E COMPACTA
        assinaturas_layout = QVBoxLayout()
        assinaturas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        assinaturas_layout.setSpacing(20)  # Espaçamento menor entre seções
        
        # Layout horizontal para as duas assinaturas lado a lado
        assinaturas_horizontal = QHBoxLayout()
        assinaturas_horizontal.setSpacing(30)  # Espaço entre paciente e terapeuta
        assinaturas_horizontal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # ✅ SEÇÃO PACIENTE - Layout vertical centrado
        frame_paciente = self._criar_frame_assinatura_centrado("Assinatura do Paciente", "#667eea")
        self.canvas_paciente = CanvasAssinatura()
        btn_limpar_paciente = BiodeskUIKit.create_neutral_button("🗑️ Limpar")
        btn_limpar_paciente.clicked.connect(self.canvas_paciente.limpar)
        
        # Layout vertical para assinatura do paciente
        layout_paciente = QVBoxLayout()
        layout_paciente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_paciente.setSpacing(8)  # Espaçamento menor entre canvas e nome
        
        layout_paciente.addWidget(self.canvas_paciente, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Nome do paciente por baixo da assinatura
        nome_paciente_label = QLabel("____________________\nPaciente")
        nome_paciente_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nome_paciente_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #667eea;
                font-weight: bold;
                margin-top: 3px;
            }
        """)
        layout_paciente.addWidget(nome_paciente_label)
        layout_paciente.addWidget(btn_limpar_paciente)
        
        frame_paciente.setLayout(layout_paciente)
        assinaturas_horizontal.addWidget(frame_paciente)
        
        # ✅ SEÇÃO TERAPEUTA - Layout vertical centrado  
        frame_profissional = self._criar_frame_assinatura_centrado("Assinatura do Profissional", "#28a745")
        self.canvas_profissional = CanvasAssinatura()
        btn_limpar_profissional = BiodeskUIKit.create_neutral_button("🗑️ Limpar")
        btn_limpar_profissional.clicked.connect(self.canvas_profissional.limpar)
        
        # Layout vertical para assinatura do profissional
        layout_profissional = QVBoxLayout()
        layout_profissional.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_profissional.setSpacing(8)  # Espaçamento menor entre canvas e nome
        
        layout_profissional.addWidget(self.canvas_profissional, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Nome do profissional por baixo da assinatura
        nome_profissional_label = QLabel("____________________\nProfissional")
        nome_profissional_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nome_profissional_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #28a745;
                font-weight: bold;
                margin-top: 3px;
            }
        """)
        layout_profissional.addWidget(nome_profissional_label)
        layout_profissional.addWidget(btn_limpar_profissional)
        
        frame_profissional.setLayout(layout_profissional)
        assinaturas_horizontal.addWidget(frame_profissional)
        
        assinaturas_layout.addLayout(assinaturas_horizontal)
        layout.addLayout(assinaturas_layout)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        
        btn_cancelar = BiodeskUIKit.create_neutral_button("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        btn_confirmar = BiodeskUIKit.create_primary_button("✅ Confirmar Assinaturas")
        btn_confirmar.clicked.connect(self.confirmar_assinaturas)
        
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_confirmar)
        
        layout.addLayout(botoes_layout)
        
    def _criar_frame_assinatura_centrado(self, titulo, cor):
        """Cria frame centrado para uma assinatura"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {cor};
                border-radius: 12px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        frame.setFixedWidth(450)  # Largura aumentada para acomodar canvas maior (400px + padding)
        
        return frame
        
    def _criar_frame_assinatura(self, titulo, cor):
        """Cria frame para uma assinatura (método original mantido para compatibilidade)"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {cor};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {cor};
                text-align: center;
                padding: 10px;
                margin-bottom: 10px;
            }}
        """)
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_label)
        
        return frame
        
    def set_paciente_data(self, dados):
        """Define dados do paciente"""
        self.paciente_data = dados
        
    def confirmar_assinaturas(self):
        """Valida e confirma as assinaturas"""
        # Verificar se há pelo menos uma assinatura
        tem_paciente = self.canvas_paciente.tem_assinatura()
        tem_profissional = self.canvas_profissional.tem_assinatura()
        
        if not tem_paciente and not tem_profissional:
            mostrar_erro(self, "Erro", "⚠️ É necessária pelo menos uma assinatura!")
            return
            
        # Capturar imagens
        dados_assinaturas = {
            'paciente': {
                'assinado': tem_paciente,
                'imagem': self.canvas_paciente.obter_imagem() if tem_paciente else None,
                'nome': self.paciente_data.get('nome', '') if self.paciente_data else '',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M')
            },
            'profissional': {
                'assinado': tem_profissional,
                'imagem': self.canvas_profissional.obter_imagem() if tem_profissional else None,
                'nome': 'Nuno Filipe Correia (Naturopata CP 0300450)',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M')
            },
            'documento': self.titulo_documento,
            'timestamp': datetime.now().isoformat()
        }
        
        # Emitir sinal com dados
        self.assinaturas_capturadas.emit(dados_assinaturas)
        self.accept()

def abrir_dialogo_assinatura(parent, titulo_documento="Documento", paciente_data=None):
    """
    Função utilitária para abrir diálogo de assinatura
    
    Returns:
        dict: Dados das assinaturas ou None se cancelado
    """
    dialogo = DialogoAssinatura(parent, titulo_documento)
    if paciente_data:
        dialogo.set_paciente_data(paciente_data)
    
    dados_resultado = None
    
    def capturar_dados(dados):
        nonlocal dados_resultado
        dados_resultado = dados
    
    dialogo.assinaturas_capturadas.connect(capturar_dados)
    
    if dialogo.exec() == QDialog.DialogCode.Accepted:
        return dados_resultado
    return None
