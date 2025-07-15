from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from utils import estilizar_botao

class IAChatWidget(QWidget):
    def __init__(self, paciente_contexto: dict = None, parent=None):
        super().__init__(parent)
        self.paciente_contexto = paciente_contexto or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.titulo = QLabel("Pergunta-me")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(self.titulo)

        self.historico = QListWidget()
        self.historico.setStyleSheet("font-size: 15px; background: #f4f7fa; border-radius: 8px; padding: 8px;")
        layout.addWidget(self.historico, 1)

        chat_row = QHBoxLayout()
        self.input = QTextEdit()
        self.input.setPlaceholderText("Pergunte algo à IA sobre este paciente...")
        self.input.setFixedHeight(48)
        self.btn_enviar = QPushButton("Enviar")
        estilizar_botao(self.btn_enviar, cor="#43a047", hover="#66bb6a")
        self.btn_enviar.setFixedWidth(100)
        self.btn_enviar.clicked.connect(self.enviar_mensagem)
        chat_row.addWidget(self.input, 1)
        chat_row.addWidget(self.btn_enviar)
        layout.addLayout(chat_row)
        print("✅ Chat IA com título e botão estilizados.")

    def enviar_mensagem(self):
        texto = self.input.toPlainText().strip()
        if texto:
            item = QListWidgetItem()
            item.setText(f"<b>Você:</b> {texto}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.historico.addItem(item)
            # Aqui será feita a chamada à API OpenAI, resposta simulada:
            resposta = self.gerar_resposta_simulada(texto)
            item_resp = QListWidgetItem()
            item_resp.setText(f"<b>IA:</b> {resposta}")
            item_resp.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.historico.addItem(item_resp)
            self.input.clear()

    def gerar_resposta_simulada(self, texto):
        # Simula resposta baseada no contexto do paciente
        nome = self.paciente_contexto.get('nome', 'Paciente')
        return f"Olá, {nome}! (resposta simulada para: '{texto}')" 