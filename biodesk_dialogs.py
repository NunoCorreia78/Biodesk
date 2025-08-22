from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon
    from biodesk_styles import aplicar_estilo_biodesk, BIODESK_DIALOG_STYLE
from biodesk_ui_kit import BiodeskUIKit
"""
🎨 BIODESK DIALOGS - Sistema unificado de caixas de diálogo estilizadas
=====================================================================
Centraliza TODAS as caixas de diálogo do Biodesk com estilo consistente
"""

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit,
    QMessageBox, QFileDialog, QInputDialog
)

# Importar estilos centralizados
try:
except ImportError:
    aplicar_estilo_biodesk = None
    BIODESK_DIALOG_STYLE = ""

class BiodeskMessageBox:
    """Classe estática para caixas de mensagem estilizadas"""
    
    @staticmethod
    def apply_style(msgbox):
        """Aplica estilo Biodesk a qualquer QMessageBox"""
        msgbox.setStyleSheet(BIODESK_DIALOG_STYLE)
        return msgbox
    
    @staticmethod
    def information(parent, title, text, buttons=None):
        """Caixa de informação estilizada com botão em português"""
        msgbox = QMessageBox(QMessageBox.Icon.Information, title, text, QMessageBox.StandardButton.NoButton, parent)
        btn_ok = msgbox.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msgbox.setDefaultButton(btn_ok)
        BiodeskMessageBox.apply_style(msgbox)
        return msgbox.exec()
    
    @staticmethod
    def warning(parent, title, text, buttons=None):
        """Caixa de aviso estilizada com botão em português"""
        msgbox = QMessageBox(QMessageBox.Icon.Warning, title, text, QMessageBox.StandardButton.NoButton, parent)
        btn_ok = msgbox.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msgbox.setDefaultButton(btn_ok)
        BiodeskMessageBox.apply_style(msgbox)
        return msgbox.exec()
    
    @staticmethod
    def critical(parent, title, text, buttons=None):
        """Caixa de erro estilizada com botão em português"""
        msgbox = QMessageBox(QMessageBox.Icon.Critical, title, text, QMessageBox.StandardButton.NoButton, parent)
        btn_ok = msgbox.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msgbox.setDefaultButton(btn_ok)
        BiodeskMessageBox.apply_style(msgbox)
        return msgbox.exec()
    
    @staticmethod
    def question(parent, title, text, buttons=None):
        """Caixa de pergunta estilizada com botões em português"""
        msgbox = QMessageBox(QMessageBox.Icon.Question, title, text, QMessageBox.StandardButton.NoButton, parent)
        
        # Adicionar botões personalizados em português
        btn_sim = msgbox.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msgbox.addButton("Não", QMessageBox.ButtonRole.NoRole)
        
        # Definir botão padrão
        msgbox.setDefaultButton(btn_sim)
        
        BiodeskMessageBox.apply_style(msgbox)
        result = msgbox.exec()
        
        # Retornar True se clicou em "Sim"
        return msgbox.clickedButton() == btn_sim

    @staticmethod  
    def getText(parent, title, label, text=""):
        """Input de texto estilizado"""
        result, ok = QInputDialog.getText(parent, title, label, text=text)
        return result, ok
        
    @staticmethod
    def getItem(parent, title, label, items, current=0, editable=False):
        """Seleção de item estilizada"""
        item, ok = QInputDialog.getItem(parent, title, label, items, current, editable)
        return item, ok

class BiodeskFileDialog:
    """Classe para diálogos de arquivo estilizados"""
    
    @staticmethod
    def getOpenFileName(parent=None, caption="", directory="", filter="", selectedFilter=""):
        """Diálogo para abrir arquivo estilizado"""
        dialog = QFileDialog()
        dialog.setStyleSheet(BIODESK_DIALOG_STYLE)
        return dialog.getOpenFileName(parent, caption, directory, filter, selectedFilter)
    
    @staticmethod
    def getSaveFileName(parent=None, caption="", directory="", filter="", selectedFilter=""):
        """Diálogo para salvar arquivo estilizado"""
        dialog = QFileDialog()
        dialog.setStyleSheet(BIODESK_DIALOG_STYLE)
        return dialog.getSaveFileName(parent, caption, directory, filter, selectedFilter)


class BiodeskDialog(QDialog):
    """Classe base para todos os diálogos da aplicação Biodesk"""
    
    def __init__(self, parent=None, title="Biodesk", width=450, height=300):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)
        self.resultado = None
        
        # ✅ APLICAR ESTILO CENTRALIZADO
        if aplicar_estilo_biodesk:
            aplicar_estilo_biodesk(self)
        else:
            # Fallback para estilo antigo se não conseguir importar
            BiodeskUIKit.apply_universal_button_style(self)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(25)
        self.layout.setContentsMargins(30, 30, 30, 30)


class LateralidadeDialog(BiodeskDialog):
    """Diálogo para seleção de lateralidade da íris"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "Biodesk - Lateralidade da Íris", 450, 300)
        self.setup_ui()
        
    def setup_ui(self):
        # Título principal
        titulo = QLabel("🔍 Lateralidade da Íris Capturada")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        self.layout.addWidget(titulo)
        
        # Pergunta
        pergunta = QLabel("Qual o lado da íris capturada?")
        pergunta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pergunta.setStyleSheet("""
            font-size: 16px;
            color: #495057;
            margin-bottom: 20px;
        """)
        self.layout.addWidget(pergunta)
        
        # Espaçamento
        self.layout.addSpacing(10)
        
        # Layout dos botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(20)
        
        # Botão Esquerda
        self.btn_esquerda = QPushButton("👁️ ESQUERDA")
        self.btn_esquerda.setObjectName("btn_info")
        self.btn_esquerda.clicked.connect(lambda: self.selecionar('esq'))
        botoes_layout.addWidget(self.btn_esquerda)
        
        # Botão Direita
        self.btn_direita = QPushButton("👁️ DIREITA")
        self.btn_direita.setObjectName("btn_success")
        self.btn_direita.clicked.connect(lambda: self.selecionar('drt'))
        botoes_layout.addWidget(self.btn_direita)
        
        self.layout.addLayout(botoes_layout)
        
        # Espaçamento inferior
        self.layout.addSpacing(10)
        
        # Nota informativa
        nota = QLabel("💡 Escolha o lado correspondente à íris fotografada")
        nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nota.setStyleSheet("""
            font-size: 12px;
            color: #6c757d;
            font-style: italic;
            margin-top: 10px;
        """)
        self.layout.addWidget(nota)
        
    def selecionar(self, tipo):
        self.resultado = tipo
        self.accept()


class ConfirmacaoDialog(BiodeskDialog):
    """Diálogo de confirmação modernizado"""
    
    def __init__(self, parent=None, titulo="Confirmação", mensagem="Tem a certeza?", 
                 btn_sim_texto="Sim", btn_nao_texto="Não"):
        super().__init__(parent, f"Biodesk - {titulo}", 550, 350)  # AUMENTADO: era 400x250, agora 550x350
        self.mensagem = mensagem
        self.btn_sim_texto = btn_sim_texto
        self.btn_nao_texto = btn_nao_texto
        self.setup_ui()
        
    def setup_ui(self):
        # Ícone de pergunta
        icone = QLabel("❓")
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 15px;
        """)
        self.layout.addWidget(icone)
        
        # Mensagem
        mensagem_label = QLabel(self.mensagem)
        mensagem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet("""
            font-size: 16px;
            color: #495057;
            margin-bottom: 20px;
            line-height: 1.4;
        """)
        self.layout.addWidget(mensagem_label)
        
        # Espaçamento
        self.layout.addSpacing(10)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(15)
        
        btn_sim = QPushButton(self.btn_sim_texto)
        btn_sim.setObjectName("btn_success")
        btn_sim.clicked.connect(self.accept)
        
        btn_nao = QPushButton(self.btn_nao_texto)
        btn_nao.setObjectName("btn_danger")
        btn_nao.clicked.connect(self.reject)
        
        botoes_layout.addWidget(btn_sim)
        botoes_layout.addWidget(btn_nao)
        
        self.layout.addLayout(botoes_layout)


class InformacaoDialog(BiodeskDialog):
    """Diálogo de informação modernizado"""
    
    def __init__(self, parent=None, titulo="Informação", mensagem="", tipo="info"):
        super().__init__(parent, f"Biodesk - {titulo}", 550, 350)  # AUMENTADO: era 400x250, agora 550x350
        self.mensagem = mensagem
        self.tipo = tipo
        self.setup_ui()
        
    def setup_ui(self):
        # Ícone baseado no tipo
        icones = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌"
        }
        
        icone = QLabel(icones.get(self.tipo, "ℹ️"))
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 15px;
        """)
        self.layout.addWidget(icone)
        
        # Mensagem
        mensagem_label = QLabel(self.mensagem)
        mensagem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet("""
            font-size: 16px;
            color: #495057;
            margin-bottom: 20px;
            line-height: 1.4;
        """)
        self.layout.addWidget(mensagem_label)
        
        # Espaçamento
        self.layout.addSpacing(10)
        
        # Botão OK
        btn_ok = QPushButton("OK")
        if self.tipo == "success":
            btn_ok.setObjectName("btn_success")
        elif self.tipo == "warning":
            btn_ok.setObjectName("btn_warning")
        elif self.tipo == "error":
            btn_ok.setObjectName("btn_danger")
        else:
            btn_ok.setObjectName("btn_primary")
            
        btn_ok.clicked.connect(self.accept)
        
        # Centralizar botão
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        self.layout.addLayout(btn_layout)


class AvisoDialog(BiodeskDialog):
    """Diálogo de aviso modernizado"""
    
    def __init__(self, parent=None, titulo="Aviso", mensagem=""):
        super().__init__(parent, f"Biodesk - {titulo}", 550, 350)  # AUMENTADO: era 400x250, agora 550x350
        self.mensagem = mensagem
        self.setup_ui()
        
    def setup_ui(self):
        # Ícone de aviso
        icone = QLabel("⚠️")
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 15px;
        """)
        self.layout.addWidget(icone)
        
        # Mensagem
        mensagem_label = QLabel(self.mensagem)
        mensagem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet("""
            font-size: 16px;
            color: #495057;
            margin-bottom: 20px;
            line-height: 1.4;
        """)
        self.layout.addWidget(mensagem_label)
        
        # Espaçamento
        self.layout.addSpacing(10)
        
        # Botão OK
        btn_ok = QPushButton("Entendi")
        btn_ok.setObjectName("btn_warning")
        btn_ok.clicked.connect(self.accept)
        
        # Centralizar botão
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        self.layout.addLayout(btn_layout)


class ErroDialog(BiodeskDialog):
    """Diálogo de erro modernizado"""
    
    def __init__(self, parent=None, titulo="Erro", mensagem=""):
        super().__init__(parent, f"Biodesk - {titulo}", 550, 380)  # AUMENTADO: era 450x300, agora 550x380
        self.mensagem = mensagem
        self.setup_ui()
        
    def setup_ui(self):
        # Ícone de erro
        icone = QLabel("❌")
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 15px;
        """)
        self.layout.addWidget(icone)
        
        # Título do erro
        titulo_erro = QLabel("Ocorreu um Erro")
        titulo_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_erro.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #dc3545;
            margin-bottom: 15px;
        """)
        self.layout.addWidget(titulo_erro)
        
        # Mensagem
        mensagem_label = QLabel(self.mensagem)
        mensagem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet("""
            font-size: 14px;
            color: #495057;
            margin-bottom: 20px;
            line-height: 1.4;
        """)
        self.layout.addWidget(mensagem_label)
        
        # Espaçamento
        self.layout.addSpacing(10)
        
        # Botão OK
        btn_ok = QPushButton("Fechar")
        btn_ok.setObjectName("btn_danger")
        btn_ok.clicked.connect(self.accept)
        
        # Centralizar botão
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        self.layout.addLayout(btn_layout)


# Funções de conveniência para uso fácil em toda a aplicação
def mostrar_confirmacao(parent, titulo, mensagem, btn_sim="Sim", btn_nao="Não"):
    """Mostra diálogo de confirmação modernizado"""
    dialog = ConfirmacaoDialog(parent, titulo, mensagem, btn_sim, btn_nao)
    return dialog.exec() == QDialog.DialogCode.Accepted


def mostrar_informacao(parent, titulo, mensagem, tipo="info"):
    """Mostra diálogo de informação modernizado - FUNÇÃO ATUALIZADA"""
    return BiodeskMessageBox.information(parent, titulo, mensagem)


def mostrar_informacao_com_callback(parent, titulo, mensagem, callback_ok=None, tipo="info"):
    """Mostra diálogo de informação modernizado com callback"""
    result = BiodeskMessageBox.information(parent, titulo, mensagem)
    if result == QMessageBox.StandardButton.Ok and callback_ok:
        callback_ok()


def mostrar_aviso(parent, titulo, mensagem):
    """Mostra diálogo de aviso modernizado - FUNÇÃO ATUALIZADA"""
    return BiodeskMessageBox.warning(parent, titulo, mensagem)


def mostrar_erro(parent, titulo, mensagem):
    """Mostra diálogo de erro modernizado - FUNÇÃO ATUALIZADA"""
    return BiodeskMessageBox.critical(parent, titulo, mensagem)


def mostrar_sucesso(parent, titulo, mensagem):
    """Mostra diálogo de sucesso modernizado"""
    return BiodeskMessageBox.information(parent, titulo, mensagem)


def perguntar_confirmacao(parent, titulo, mensagem):
    """Pergunta confirmação ao utilizador - FUNÇÃO ATUALIZADA"""
    return BiodeskMessageBox.question(parent, titulo, mensagem)  # Já retorna True/False


def fazer_pergunta(parent, titulo, mensagem):
    """Função de compatibilidade para perguntas"""
    return BiodeskMessageBox.question(parent, titulo, mensagem)


def escolher_lateralidade(parent):
    """Mostra diálogo para escolher lateralidade da íris"""
    dialog = LateralidadeDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.resultado
    return None
