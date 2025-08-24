from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QTextEdit, 
    QLabel, QFrame, QPushButton, QApplication, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
from biodesk_ui_kit import BiodeskUIKit
"""
Widget de Notas com Checkboxes Seletivos - Biodesk
==================================================

Este widget substitui o QTextEdit simples por uma interface com checkboxes
que permite selecionar exatamente quais linhas enviar para histórico/terapia.

Funcionalidades:
✅ Checkbox para cada linha de nota
✅ Checkbox "Selecionar Todos" 
✅ Exportação seletiva para histórico
✅ Exportação seletiva para terapia
✅ Interface moderna e intuitiva
"""


class CheckboxNotesWidget(QWidget):
    """
    Widget de notas com checkboxes para seleção individual de linhas
    """
    
    # Sinais para comunicar com o widget pai
    linhaAdicionada = pyqtSignal(str)  # Emitido quando uma nova linha é adicionada
    selecaoMudou = pyqtSignal()        # Emitido quando a seleção muda
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.linhas_notas = []  # Lista de dicionários: {'texto': str, 'checkbox': QCheckBox}
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Cabeçalho com checkbox "Selecionar Todos" e botão limpar alinhados
        header_row = QHBoxLayout()
        self.check_selecionar_todos = QCheckBox("Selecionar Todos")
        self.check_selecionar_todos.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.check_selecionar_todos.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #4CAF50;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                image: url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" fill=\"white\"><path d=\"M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z\"/></svg>');
            }
            QCheckBox::indicator:indeterminate {
                background-color: #81C784;
                border: 1px solid #4CAF50;
                image: url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" fill=\"white\"><path d=\"M19 13H5v-2h14v2z\"/></svg>');
            }
            QCheckBox::indicator:hover {
                border-color: #66BB6A;
            }
        """)
        self.check_selecionar_todos.setTristate(True)
        self.check_selecionar_todos.stateChanged.connect(self.toggle_todos_checkboxes)
        header_row.addWidget(self.check_selecionar_todos)
        header_row.addStretch()
        self.btn_limpar_tudo = QPushButton("🧹")
        self.btn_limpar_tudo.setFixedSize(80, 28)
        self.btn_limpar_tudo.setToolTip("Limpar todas as notas")
        BiodeskUIKit.apply_universal_button_style(self.btn_limpar_tudo)
        self.btn_limpar_tudo.clicked.connect(self.limpar_todas_linhas)
        header_row.addWidget(self.btn_limpar_tudo, 0, Qt.AlignmentFlag.AlignTop)  # Alinhar no topo
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)
        layout.addLayout(header_row)
        
        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #ddd; margin: 2px 0;")
        layout.addWidget(sep)
        
        # Área de scroll para as linhas de notas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #f0f0f0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #ccc;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #aaa;
            }
        """)
        
        # Widget container para as linhas
        self.linhas_container = QWidget()
        self.linhas_layout = QVBoxLayout(self.linhas_container)
        self.linhas_layout.setContentsMargins(8, 8, 8, 8)
        self.linhas_layout.setSpacing(6)
        self.linhas_layout.addStretch()  # Empurra as linhas para o topo
        
        # Placeholder quando não há linhas
        self.placeholder_label = QLabel("Clique nas zonas da íris para adicionar notas...")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-style: italic;
                padding: 20px;
                background-color: transparent;
            }
        """)
        self.linhas_layout.addWidget(self.placeholder_label)
        
        self.scroll_area.setWidget(self.linhas_container)
        layout.addWidget(self.scroll_area)
        
        # Área de entrada de texto manual (opcional) alinhada com botão
        input_row = QHBoxLayout()
        self.entrada_texto = QTextEdit()
        self.entrada_texto.setPlaceholderText("Digite uma nota manual...")
        self.entrada_texto.setFixedHeight(60)
        self.entrada_texto.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.btn_adicionar = QPushButton("📝")
        self.btn_adicionar.setFixedSize(60, 60)  # Tamanho TOP que você adorou!
        self.btn_adicionar.setToolTip("Adicionar nota manual")
        BiodeskUIKit.apply_universal_button_style(self.btn_adicionar)
        self.btn_adicionar.clicked.connect(self.adicionar_nota_manual)
        input_row.addWidget(self.entrada_texto, 1)
        input_row.addWidget(self.btn_adicionar, 0)
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(8)
        layout.addLayout(input_row)
        
        # Espaçamento entre área de input e os botões externos
        layout.addSpacing(15)  # Separação visual importante
        
    def adicionar_linha(self, texto):
        """Adiciona uma nova linha de nota com checkbox"""
        if not texto.strip():
            return
            
        # Ocultar placeholder se for a primeira linha
        if len(self.linhas_notas) == 0:
            self.placeholder_label.hide()
            
        # Criar container para a linha
        linha_widget = QWidget()
        linha_layout = QHBoxLayout(linha_widget)
        linha_layout.setContentsMargins(4, 4, 4, 4)
        linha_layout.setSpacing(8)
        
        # Checkbox para a linha
        checkbox = QCheckBox()
        checkbox.setChecked(True)  # Por padrão, novas linhas ficam marcadas
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #4CAF50;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>');
            }
            QCheckBox::indicator:hover {
                border-color: #66BB6A;
            }
        """)
        checkbox.stateChanged.connect(self.atualizar_checkbox_todos)
        checkbox.stateChanged.connect(self.emitir_mudanca_selecao)
        
        # Label com o texto da nota
        label_texto = QLabel(texto)
        label_texto.setWordWrap(True)
        label_texto.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 2px;
                background-color: transparent;
            }
        """)
        
        # Botão para remover a linha
        btn_remover = QPushButton("✖")
        btn_remover.setFixedSize(20, 20)
        btn_remover.setToolTip("Remover esta linha")
        BiodeskUIKit.apply_universal_button_style(btn_remover)
        
        # Conectar remoção
        def criar_remocao(widget):
            return lambda: self.remover_linha(widget)
        btn_remover.clicked.connect(criar_remocao(linha_widget))
        
        linha_layout.addWidget(checkbox)
        linha_layout.addWidget(label_texto, 1)  # Stretch para ocupar espaço disponível
        linha_layout.addWidget(btn_remover)
        
        # Adicionar ao layout principal (no topo, após o cabeçalho)
        self.linhas_layout.insertWidget(0, linha_widget)  # Inserir no início para ordem de cima para baixo
        
        # Guardar referência
        self.linhas_notas.append({
            'texto': texto,
            'checkbox': checkbox,
            'widget': linha_widget,
            'label': label_texto
        })
        
        # Scroll para o topo para mostrar a nova linha
        self.scroll_area.verticalScrollBar().setValue(0)
        
        # Atualizar estado do checkbox "todos"
        self.atualizar_checkbox_todos()
        
        # Emitir sinal
        self.linhaAdicionada.emit(texto)
        
    def adicionar_nota_manual(self):
        """Adiciona nota digitada manualmente"""
        texto = self.entrada_texto.toPlainText().strip()
        if texto:
            self.adicionar_linha(texto)
            self.entrada_texto.clear()
            
    def remover_linha(self, linha_widget):
        """Remove uma linha específica"""
        # Encontrar e remover da lista
        for i, linha_data in enumerate(self.linhas_notas):
            if linha_data['widget'] == linha_widget:
                self.linhas_notas.pop(i)
                break
                
        # Remover do layout
        linha_widget.setParent(None)
        linha_widget.deleteLater()
        
        # Mostrar placeholder se não houver mais linhas
        if len(self.linhas_notas) == 0:
            self.placeholder_label.show()
            
        self.atualizar_checkbox_todos()
        self.emitir_mudanca_selecao()
        
    def limpar_todas_linhas(self):
        """Remove todas as linhas"""
        for linha_data in self.linhas_notas[:]:  # Cópia da lista
            self.remover_linha(linha_data['widget'])
        
        self.emitir_mudanca_selecao()
            
    def toggle_todos_checkboxes(self, estado):
        """Marca/desmarca todos os checkboxes baseado no estado do checkbox principal"""
        if not self.linhas_notas:
            return
            
        # Determinar o novo estado baseado no checkbox principal
        if estado == Qt.CheckState.Unchecked.value:
            novo_estado = False  # Desmarcar todos
        elif estado == Qt.CheckState.Checked.value:
            novo_estado = True   # Marcar todos
        else:  # PartiallyChecked - marcar todos
            novo_estado = True
            
        # Aplicar o estado a todos os checkboxes
        for linha_data in self.linhas_notas:
            linha_data['checkbox'].blockSignals(True)
            linha_data['checkbox'].setChecked(novo_estado)
            linha_data['checkbox'].blockSignals(False)
            
        # Atualizar o widget pai se necessário
        if hasattr(self, 'parent') and hasattr(self.parent(), 'atualizar_textos_botoes'):
            self.parent().atualizar_textos_botoes()
            
    def atualizar_checkbox_todos(self):
        """Atualiza o estado do checkbox 'Selecionar Todos'"""
        if not self.linhas_notas:
            self.check_selecionar_todos.blockSignals(True)
            self.check_selecionar_todos.setChecked(False)
            self.check_selecionar_todos.blockSignals(False)
            return
            
        marcados = sum(1 for linha in self.linhas_notas if linha['checkbox'].isChecked())
        total = len(self.linhas_notas)
        
        # Bloquear sinais para evitar loops
        self.check_selecionar_todos.blockSignals(True)
        
        if marcados == 0:
            self.check_selecionar_todos.setCheckState(Qt.CheckState.Unchecked)
        elif marcados == total:
            self.check_selecionar_todos.setCheckState(Qt.CheckState.Checked)
        else:
            self.check_selecionar_todos.setCheckState(Qt.CheckState.PartiallyChecked)
            
        # Reativar sinais
        self.check_selecionar_todos.blockSignals(False)
        
    def emitir_mudanca_selecao(self):
        """Emite sinal quando a seleção muda"""
        self.selecaoMudou.emit()
            
    def get_linhas_selecionadas(self):
        """Retorna lista com os textos das linhas marcadas"""
        return [
            linha['texto'] 
            for linha in self.linhas_notas 
            if linha['checkbox'].isChecked()
        ]
        
    def get_todas_linhas(self):
        """Retorna lista com todos os textos (independente da seleção)"""
        return [linha['texto'] for linha in self.linhas_notas]
        
    def tem_linhas_selecionadas(self):
        """Verifica se há pelo menos uma linha selecionada"""
        return any(linha['checkbox'].isChecked() for linha in self.linhas_notas)
        
    def count_selecionadas(self):
        """Retorna o número de linhas selecionadas"""
        return sum(1 for linha in self.linhas_notas if linha['checkbox'].isChecked())
        
    def count_total(self):
        """Retorna o número total de linhas"""
        return len(self.linhas_notas)


if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    # Teste do widget
    widget = CheckboxNotesWidget()
    widget.setWindowTitle("Teste - Notas com Checkboxes")
    widget.setGeometry(100, 100, 400, 600)
    
    # Adicionar algumas linhas de teste
    widget.adicionar_linha("Alteração na área reflexa: Estômago")
    widget.adicionar_linha("Manchas escuras observadas na zona intestinal")
    widget.adicionar_linha("Padrão radial irregular na área hepática")
    widget.adicionar_linha("Possível processo inflamatório na zona renal")
    
    widget.show()
    sys.exit(app.exec())
