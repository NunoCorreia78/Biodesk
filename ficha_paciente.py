import sys
from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit, QComboBox, QTextEdit, QPushButton,
    QToolBar, QMenu, QListWidget, QListWidgetItem, QToolButton, QApplication, QSpacerItem, QSizePolicy, QFormLayout, QGridLayout, QSplitter, QDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, QPoint
from PyQt6.QtGui import QIcon, QTextCursor, QKeySequence, QAction, QTextCharFormat, QFont, QShortcut
from chat_ia import IAChatWidget
from db_manager import DBManager
import unicodedata
import json
from utils import estilizar_botao_iris, estilizar_botao
import os

def toggle_bold(text_edit):
    cursor = text_edit.textCursor()
    if not cursor.hasSelection():
        fmt = QTextCharFormat()
        current_weight = text_edit.fontWeight()
        if current_weight == QFont.Weight.Bold:
            fmt.setFontWeight(QFont.Weight.Normal)
        else:
            fmt.setFontWeight(QFont.Weight.Bold)
        text_edit.setCurrentCharFormat(fmt)
    else:
        fmt = cursor.charFormat()
        if fmt.fontWeight() == QFont.Weight.Bold:
            fmt.setFontWeight(QFont.Weight.Normal)
        else:
            fmt.setFontWeight(QFont.Weight.Bold)
        cursor.mergeCharFormat(fmt)
        text_edit.setTextCursor(cursor)

class FichaPaciente(QWidget):
    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data or {}
        self.dirty = False
        self._ultima_zona_hover = None  # Inicializa o atributo para evitar erros de acesso
        self.init_ui()
        self.load_data()
        self._ligar_dirty()

    def _ligar_dirty(self):
        # Liga o flag dirty a todos os campos editáveis
        for w in [self.nome_edit, self.sexo_combo, self.nasc_edit, self.naturalidade_edit, self.profissao_edit,
                  self.estado_civil_combo, self.contacto_edit, self.email_edit, self.local_combo]:
            if hasattr(w, 'textChanged'):
                w.textChanged.connect(self._set_dirty)
            elif hasattr(w, 'currentTextChanged'):
                w.currentTextChanged.connect(self._set_dirty)
            elif hasattr(w, 'dateChanged'):
                w.dateChanged.connect(self._set_dirty)
        self.historico_edit.textChanged.connect(self._set_dirty)

    def _set_dirty(self, *args):
        self.dirty = True

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        self.tabs.setStyleSheet('font-size: 16px;')
        # Abas
        self.tab_dados = QWidget()
        self.tab_historico = QWidget()
        self.tab_iris = QWidget()
        self.tabs.addTab(self.tab_dados, 'Dados pessoais')
        self.tabs.addTab(self.tab_historico, 'Histórico clínico')
        self.tabs.addTab(self.tab_iris, 'Íris')
        main_layout.addWidget(self.tabs)
        # Atalho Ctrl+S
        shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut.activated.connect(self.guardar)
        self.init_tab_dados()
        self.init_tab_historico()
        self.init_tab_iris()
    def init_tab_iris(self):
        from iris_canvas import IrisCanvas
        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QFrame, QWidget, QTextEdit, QScrollArea
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(24)

        # Coluna esquerda: botões e galeria
        left_col = QVBoxLayout()
        left_col.setSpacing(12)
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_col.setContentsMargins(5, 8, 5, 8)

        self.btn_nova_iris = QPushButton("Nova íris")
        estilizar_botao_iris(self.btn_nova_iris, cor="#166380", hover="#218fb0")
        self.btn_nova_iris.setFixedSize(170, 48)
        left_col.addWidget(self.btn_nova_iris)

        self.btn_apagar_iris = QPushButton("Apagar íris")
        estilizar_botao_iris(self.btn_apagar_iris, cor="#c62828", hover="#e57373")
        self.btn_apagar_iris.setFixedSize(170, 48)
        left_col.addWidget(self.btn_apagar_iris)

        self.btn_selecionar_iris = QPushButton("Selecionar íris")
        estilizar_botao_iris(self.btn_selecionar_iris, cor="#218fb0", hover="#42b8d8")
        self.btn_selecionar_iris.setFixedSize(170, 48)
        left_col.addWidget(self.btn_selecionar_iris)

        left_col.addSpacing(18)

        galeria_frame = QFrame()
        galeria_frame.setFixedWidth(195)
        galeria_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dbe6ec;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        galeria_frame_layout = QVBoxLayout(galeria_frame)
        galeria_frame_layout.setContentsMargins(8, 8, 8, 8)
        galeria_frame_layout.setSpacing(6)

        self.galeria_widget = QWidget()
        self.galeria_layout = QVBoxLayout(self.galeria_widget)
        self.galeria_layout.setSpacing(6)
        self.galeria_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.galeria_layout.setContentsMargins(0, 0, 0, 0)

        self.galeria_scroll = QScrollArea()
        self.galeria_scroll.setWidgetResizable(True)
        self.galeria_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.galeria_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.galeria_scroll.setWidget(self.galeria_widget)
        galeria_frame_layout.addWidget(self.galeria_scroll)
        left_col.addWidget(galeria_frame, 1)

        left_panel = QFrame()
        left_panel.setLayout(left_col)
        left_panel.setFixedWidth(205)
        main_hbox.addWidget(left_panel)

        # Centro: canvas
        center_col = QVBoxLayout()
        center_col.setSpacing(18)
        # Removido: Botões centrais (Mostrar Mapa e Ajuste Mapa)
        self.iris_canvas = IrisCanvas(paciente_data=self.paciente_data)
        self.iris_canvas.setMinimumSize(540, 540)
        self.iris_canvas.setMaximumWidth(700)
        self.iris_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        center_col.addWidget(self.iris_canvas, stretch=1)
        main_hbox.addLayout(center_col, 3)

        # Direita: notas
        painel_vbox = QVBoxLayout()
        painel_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.btn_exportar_notas = QPushButton('Exportar para histórico clínico')
        estilizar_botao_iris(self.btn_exportar_notas, cor="#218450", hover="#38ba77", font_size=15, largura=220)
        self.btn_exportar_notas.setFixedSize(220, 48)
        painel_vbox.addWidget(self.btn_exportar_notas, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Botão Exportar para terapia quântica (mantém estilo antigo ou adapta se desejar)
        self.btn_exportar_terapia = QPushButton('Exportar para terapia quântica')
        estilizar_botao_iris(self.btn_exportar_terapia, cor="#8e24aa", hover="#ba68c8", font_size=15, largura=220)
        self.btn_exportar_terapia.setFixedSize(220, 48)
        self.btn_exportar_terapia.clicked.connect(self.exportar_para_terapia_quantica)
        painel_vbox.addWidget(self.btn_exportar_terapia, alignment=Qt.AlignmentFlag.AlignHCenter)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        sep1.setStyleSheet('margin: 10px 0;')
        painel_vbox.addWidget(sep1)
        self.notas_iris = QTextEdit()
        self.notas_iris.setPlaceholderText('Notas rápidas sobre a análise deste olho...')
        self.notas_iris.setFixedHeight(90)
        painel_vbox.addWidget(self.notas_iris)
        painel_vbox.addStretch()
        painel_widget = QWidget()
        painel_widget.setLayout(painel_vbox)
        painel_widget.setMinimumWidth(260)
        main_hbox.addWidget(painel_widget)

        layout = QVBoxLayout(self.tab_iris)
        layout.addLayout(main_hbox)
        self.tab_iris.setLayout(layout)

        # Eventos
        self.btn_exportar_notas.clicked.connect(self.exportar_notas_iris)
        self.btn_selecionar_iris.clicked.connect(self.selecionar_imagem_selecionada_galeria)
        self.btn_apagar_iris.clicked.connect(self.apagar_imagem_selecionada)
        self.btn_nova_iris.clicked.connect(self.adicionar_nova_iris)

        self.imagem_iris_selecionada = None
        self.atualizar_galeria_iris()

    def atualizar_galeria_iris(self):
        from PyQt6.QtWidgets import QLabel, QHBoxLayout, QPushButton, QWidget
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        while self.galeria_layout.count():
            item = self.galeria_layout.takeAt(0)
            if item is not None and hasattr(item, 'widget'):
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        paciente_id = self.paciente_data.get('id')
        if not paciente_id:
            return
        db = DBManager()
        imagens = db.get_imagens_por_paciente(paciente_id)
        if not imagens:
            label = QLabel('Nenhuma imagem de íris disponível.')
            self.galeria_layout.addWidget(label)
            self.iris_canvas.set_image(None, None)
            return
        self.galeria_containers = []
        for img in imagens:
            item_container = QWidget()
            item_container.setProperty('img_data', img)
            item_container.setStyleSheet("""
                QWidget {
                    background: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    margin: 2px;
                    padding: 8px;
                }
                QWidget:hover {
                    border-color: #1976d2;
                    background: #f8f9fa;
                }
            """)
            item_layout = QVBoxLayout(item_container)
            item_layout.setContentsMargins(6, 6, 6, 6)
            item_layout.setSpacing(4)
            top_row = QHBoxLayout()
            thumb = QLabel()
            pix = QPixmap(img['caminho_imagem'])
            thumb.setPixmap(pix.scaledToWidth(48))
            thumb.setFixedSize(52, 52)
            thumb.setStyleSheet("border: none; border-radius: 4px;")
            top_row.addWidget(thumb)
            nome = QLabel(f"{img['tipo'].upper()}\n{os.path.basename(img['caminho_imagem'])}")
            nome.setWordWrap(True)
            nome.setStyleSheet("font-size: 12px; color: #333; border: none; background: transparent;")
            top_row.addWidget(nome, 1)
            item_layout.addLayout(top_row)
            def mousePressEvent(a0, img=img):
                self.on_galeria_click(a0, img)
            def mouseDoubleClickEvent(a0, img=img):
                self.on_galeria_double_click(a0, img)
            item_container.mousePressEvent = mousePressEvent
            item_container.mouseDoubleClickEvent = mouseDoubleClickEvent
            self.galeria_layout.addWidget(item_container)
            self.galeria_containers.append(item_container)

    def on_galeria_click(self, event, img):
        self.atualizar_selecao_galeria(img)

    def on_galeria_double_click(self, event, img):
        self.selecionar_imagem_iris(img)

    def atualizar_selecao_galeria(self, img_selecionada):
        if not hasattr(self, 'galeria_containers'):
            return
        for container in self.galeria_containers:
            img_data = container.property('img_data') if hasattr(container, 'property') else None
            if img_data is not None:
                if img_data == img_selecionada:
                    container.setStyleSheet("""
                        QWidget {
                            background: #e3f2fd;
                            border: 2px solid #1976d2;
                            border-radius: 8px;
                            margin: 2px;
                            padding: 8px;
                        }
                        QWidget:hover {
                            border-color: #1565c0;
                            background: #e1f5fe;
                        }
                    """)
                else:
                    container.setStyleSheet("""
                        QWidget {
                            background: #ffffff;
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            margin: 2px;
                            padding: 8px;
                        }
                        QWidget:hover {
                            border-color: #1976d2;
                            background: #f8f9fa;
                        }
                    """)

    def selecionar_imagem_selecionada_galeria(self):
        if not hasattr(self, 'galeria_containers'):
            return
        for container in self.galeria_containers:
            img_data = container.property('img_data') if hasattr(container, 'property') else None
            if img_data is not None and container.styleSheet().find('#e3f2fd') != -1:
                self.selecionar_imagem_iris(img_data)
                return
        if hasattr(self, 'galeria_containers') and self.galeria_containers:
            primeiro_container = self.galeria_containers[0]
            img_data = primeiro_container.property('img_data') if hasattr(primeiro_container, 'property') else None
            if img_data is not None:
                self.selecionar_imagem_iris(img_data)

    def selecionar_imagem_iris(self, img):
        self.imagem_iris_selecionada = img
        self.iris_canvas.set_image(img['caminho_imagem'], img['tipo'])
        self.notas_iris.setPlainText("")
        self.atualizar_selecao_galeria(img)

    def apagar_imagem_selecionada(self):
        if not hasattr(self, 'galeria_containers'):
            return
        for container in self.galeria_containers:
            img_data = container.property('img_data') if hasattr(container, 'property') else None
            if img_data is not None and container.styleSheet().find('#e3f2fd') != -1:
                self.eliminar_imagem_iris(img_data)
                return

    def eliminar_imagem_iris(self, img):
        from PyQt6.QtWidgets import QMessageBox
        resposta = QMessageBox.question(self, "Eliminar imagem",
            f"Tem a certeza que quer eliminar a imagem {img['caminho_imagem']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                import os
                os.remove(img['caminho_imagem'])
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível eliminar ficheiro: {e}")
            db = DBManager()
            db.execute_query("DELETE FROM imagens_iris WHERE id = ?", (img['id'],))
            self.atualizar_galeria_iris()

    def adicionar_nova_iris(self):
        # Implemente aqui a lógica para adicionar nova imagem de íris
        pass

    def exportar_notas_iris(self):
        notas = self.notas_iris.toPlainText().strip()
        if not notas:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Notas vazias', 'Escreva alguma nota antes de exportar.')
            return
        html_antigo = self.historico_edit.toHtml()
        from datetime import datetime
        data = datetime.today().strftime('%d/%m/%Y')
        novo_html = f'<b>{data} - Análise de Íris:</b><br>{notas}<br><hr style="border: none; border-top: 1px solid #bbb; margin: 10px 6px;">' + html_antigo
        self.historico_edit.setHtml(novo_html)
        self.notas_iris.setPlainText("")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, 'Exportado', 'Notas exportadas para o histórico clínico!')

    def init_tab_dados(self):
        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(36)
        grid.setContentsMargins(24, 18, 24, 18)

        # Linha 1: Nome
        self.nome_edit = QLineEdit()
        self.nome_edit.setMinimumWidth(320)
        grid.addWidget(QLabel('Nome'), 0, 0)
        grid.addWidget(self.nome_edit, 0, 1, 1, 3)

        # Linha 2: Data de nascimento | Sexo
        self.nasc_edit = QDateEdit()
        self.nasc_edit.setCalendarPopup(True)
        self.nasc_edit.setDisplayFormat('dd/MM/yyyy')
        self.nasc_edit.setFixedWidth(180)
        self.nasc_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nasc_edit.setSpecialValueText("__/__/____")
        self.nasc_edit.setDate(QDate(1920, 1, 1))
        self.nasc_edit.setMinimumDate(QDate(1920, 1, 1))
        self.nasc_edit.setDateRange(QDate(1920, 1, 1), QDate.currentDate())
        self.nasc_edit.setStyleSheet("QDateEdit { padding: 12px 0; font-size: 17px; border-radius: 8px; background: #fff; border: 1px solid #cfd8dc; } QDateEdit::drop-down { width: 22px; } QDateEdit::down-arrow { width: 12px; height: 12px; } QDateEdit QAbstractItemView { font-size: 16px; }")

        # Customização do calendário popup
        calendar = self.nasc_edit.calendarWidget()
        if calendar:
            calendar.setNavigationBarVisible(True)
            calendar.setVerticalHeaderFormat(calendar.VerticalHeaderFormat.NoVerticalHeader)
            calendar.setStyleSheet("""
                QCalendarWidget { background: #fff; border-radius: 12px; border: 1px solid #cfd8dc; }
                QCalendarWidget QToolButton { background: #f5f5f5; border: none; font-size: 16px; padding: 6px 12px; border-radius: 6px; color: black; }
                QCalendarWidget QToolButton#qt_calendar_prevmonth, QCalendarWidget QToolButton#qt_calendar_nextmonth { font-size: 22px; color: #1976d2; }
                QCalendarWidget QMenu { font-size: 15px; }
                QCalendarWidget QWidget#qt_calendar_navigationbar { background: #f5f5f5; border-radius: 8px; }
                QCalendarWidget QAbstractItemView:enabled { font-size: 16px; color: #222; background: #fff; selection-background-color: #e3f2fd; selection-color: #1976d2; }
                QCalendarWidget QAbstractItemView:disabled { color: #bdbdbd; }
                QCalendarWidget QAbstractItemView:selected { background: #e3f2fd; color: #1976d2; border-radius: 6px; }
                QCalendarWidget QAbstractItemView { outline: none; }
                QCalendarWidget QWidget#qt_calendar_navigationbar QToolButton { min-width: 32px; }
            """)
            # Removido o seletor personalizado de décadas/anos para usar o comportamento nativo do QCalendarWidget
        self.sexo_combo = QComboBox()
        self.sexo_combo.addItems(['', 'Masculino', 'Feminino', 'Outro'])
        self.sexo_combo.setFixedWidth(180)
        grid.addWidget(QLabel('Data de nascimento'), 1, 0)
        grid.addWidget(self.nasc_edit, 1, 1)
        grid.addWidget(QLabel('Sexo'), 1, 2)
        grid.addWidget(self.sexo_combo, 1, 3)

        # Linha 3: Profissão | Naturalidade
        self.profissao_edit = QLineEdit()
        self.profissao_edit.setMinimumWidth(200)
        self.naturalidade_edit = QLineEdit()
        self.naturalidade_edit.setMinimumWidth(200)
        grid.addWidget(QLabel('Profissão'), 2, 0)
        grid.addWidget(self.profissao_edit, 2, 1)
        grid.addWidget(QLabel('Naturalidade'), 2, 2)
        grid.addWidget(self.naturalidade_edit, 2, 3)

        # Linha 4: Estado civil | Local habitual
        self.estado_civil_combo = QComboBox()
        self.estado_civil_combo.addItems(['', 'Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'União de facto', 'Outro'])
        self.estado_civil_combo.setFixedWidth(180)
        self.local_combo = QComboBox()
        self.local_combo.addItems(['', 'Chão de Lopes', 'Coruche', 'Campo Maior', 'Elvas', 'Cliniprata', 'Spazzio Vita', 'Samora Correia', 'Online', 'Outro'])
        self.local_combo.setFixedWidth(180)
        grid.addWidget(QLabel('Estado civil'), 3, 0)
        grid.addWidget(self.estado_civil_combo, 3, 1)
        grid.addWidget(QLabel('Local habitual'), 3, 2)
        grid.addWidget(self.local_combo, 3, 3)

        # Linha 5: Contacto | Email
        self.contacto_edit = QLineEdit()
        self.contacto_edit.setFixedWidth(180)
        self.contacto_edit.textChanged.connect(self.formatar_contacto)
        self.btn_sms = QPushButton("📨 Enviar SMS")
        estilizar_botao(self.btn_sms, cor="#1976d2", hover="#42a5f5")
        self.btn_sms.setFixedWidth(self.contacto_edit.width())
        self.btn_sms.clicked.connect(self.abrir_sms_dialogo)
        self.email_edit = QLineEdit()
        self.email_edit.setMinimumWidth(220)
        grid.addWidget(QLabel('Contacto'), 4, 0)
        grid.addWidget(self.contacto_edit, 4, 1)
        grid.addWidget(QLabel('Email'), 4, 2)
        grid.addWidget(self.email_edit, 4, 3)
        # Botão SMS abaixo do contacto, alinhado à esquerda
        grid.addWidget(self.btn_sms, 5, 1, 1, 1)

        layout.addLayout(grid)
        layout.addSpacing(36)
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Linha de botões no rodapé
        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        self.btn_terapia = QPushButton('✨ Terapia Quântica')
        estilizar_botao(self.btn_terapia, cor="#7b1fa2", hover="#ba68c8")
        self.btn_terapia.clicked.connect(self.abrir_terapia)
        btns_layout.addWidget(self.btn_terapia)
        btns_layout.addSpacing(16)
        layout.addLayout(btns_layout)

        self.tab_dados.setLayout(layout)

    def formatar_contacto(self, text):
        digits = ''.join(filter(str.isdigit, text))
        if len(digits) > 9:
            digits = digits[:9]
        formatted = ' '.join([digits[i:i+3] for i in range(0, len(digits), 3)])
        if text != formatted:
            self.contacto_edit.blockSignals(True)
            self.contacto_edit.setText(formatted)
            self.contacto_edit.blockSignals(False)

    def init_tab_historico(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        historico_widget = QWidget()
        hist_layout = QVBoxLayout(historico_widget)

        # Estado emocional e Biotipo lado a lado
        emo_bio_row = QHBoxLayout()
        self.estado_emo_combo = QComboBox()
        self.estado_emo_combo.addItems([
            '', 'calmo', 'ansioso', 'agitado', 'deprimido', 'indiferente', 'eufórico', 'apático', 'irritável', 'motivado', 'desmotivado', 'confuso', 'triste', 'alegre', 'preocupado', 'tenso', 'relaxado', 'culpado', 'esperançoso', 'pessimista', 'otimista', 'outro'
        ])
        self.estado_emo_combo.setCurrentIndex(0)
        self.estado_emo_combo.setFixedWidth(180)
        emo_bio_row.addWidget(QLabel('Estado emocional:'))
        emo_bio_row.addWidget(self.estado_emo_combo)
        self.biotipo_combo = QComboBox()
        self.biotipo_combo.addItems([
            '', 'Longilíneo', 'Brevilíneo', 'Normolíneo', 'Atlético', 'Outro'
        ])
        self.biotipo_combo.setFixedWidth(180)
        emo_bio_row.addSpacing(20)
        emo_bio_row.addWidget(QLabel('Biotipo:'))
        emo_bio_row.addWidget(self.biotipo_combo)
        emo_bio_row.addStretch()
        hist_layout.addLayout(emo_bio_row)
        # Legenda do biotipo
        self.biotipo_desc = QLabel(
            "Biotipos:<br>"
            "• Longilíneo – magro, esguio, estatura alta<br>"
            "  → Tendência para ansiedade, hiperatividade, digestão rápida<br>"
            "• Brevilíneo – baixo, robusto, arredondado<br>"
            "  → Propenso a retenção, congestão, metabolismo lento<br>"
            "• Normolíneo – equilibrado, proporcional<br>"
            "  → Regulação geral estável, adaptação moderada<br>"
            "• Atlético – musculado, estrutura firme<br>"
            "  → Boa resistência, recuperação rápida, resposta forte a terapias físicas"
        )
        self.biotipo_desc.setWordWrap(True)
        self.biotipo_desc.setStyleSheet('font-size: 12px; color: #555; margin-top: 2px; margin-bottom: 8px;')
        print("✅ Legenda do biotipo clara e alinhada.")
        hist_layout.addWidget(self.biotipo_desc)

        # Toolbar com margens e hover
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { margin-bottom: 8px; }
            QToolButton { margin-right: 6px; padding: 4px 8px; border-radius: 6px; }
            QToolButton:hover { background: #eaf3fa; }
        """)
        self.action_bold = QAction('B', self)
        self.action_bold.setShortcut('Ctrl+B')
        self.action_bold.triggered.connect(lambda: toggle_bold(self.historico_edit))
        self.action_italic = QAction('I', self)
        self.action_italic.setShortcut('Ctrl+I')
        self.action_italic.triggered.connect(lambda: self.format_text('italic'))
        self.action_underline = QAction('U', self)
        self.action_underline.setShortcut('Ctrl+U')
        self.action_underline.triggered.connect(lambda: self.format_text('underline'))
        self.action_date = QAction('📅', self)
        self.action_date.triggered.connect(self.inserir_data_negrito)
        self.toolbar.addAction(self.action_bold)
        self.toolbar.addAction(self.action_italic)
        self.toolbar.addAction(self.action_underline)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_date)
        hist_layout.addWidget(self.toolbar)

        # Editor de histórico
        self.historico_edit = QTextEdit()
        self.historico_edit.setPlaceholderText(
            "Descreva queixas, sintomas, evolução do caso ou aspetos emocionais relevantes..."
        )
        self.historico_edit.setStyleSheet("""
            QTextEdit {
                background-color: #fefefe;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 10px;
                font-size: 15px;
                line-height: 1.6;
            }
        """)
        hist_layout.addWidget(self.historico_edit)
        hist_layout.addStretch()

        # Rodapé com botão Guardar
        rodape = QHBoxLayout()
        rodape.addStretch()
        self.btn_guardar = QPushButton('💾 Guardar')
        estilizar_botao(self.btn_guardar)
        self.btn_guardar.setFixedWidth(140)
        self.btn_guardar.clicked.connect(self.guardar)
        rodape.addWidget(self.btn_guardar)
        hist_layout.addLayout(rodape)

        # Divisão visual entre editor e IA
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.VLine)
        frame.setLineWidth(2)
        frame.setStyleSheet("color: #e0e0e0; background: #e0e0e0; min-width: 2px;")
        splitter.addWidget(historico_widget)
        splitter.addWidget(frame)
        self.chat_widget = IAChatWidget(self.paciente_data)
        splitter.addWidget(self.chat_widget)
        splitter.setSizes([700, 10, 350])
        layout = QVBoxLayout(self.tab_historico)
        layout.addWidget(splitter)



    def format_text(self, fmt):
        cursor = self.historico_edit.textCursor()
        fmt_obj = self.historico_edit.currentCharFormat()
        if fmt == 'italic':
            fmt_obj.setFontItalic(not fmt_obj.fontItalic())
        elif fmt == 'underline':
            fmt_obj.setFontUnderline(not fmt_obj.fontUnderline())
        cursor.mergeCharFormat(fmt_obj)
        self.historico_edit.setTextCursor(cursor)

    def inserir_data_negrito(self):
        from datetime import datetime
        data = datetime.today().strftime('%d/%m/%Y')
        prefixo = f'<b>{data}</b><br><hr style="border: none; border-top: 1px solid #bbb; margin: 10px 6px;">'
        # Obter o HTML antigo
        html_antigo = self.historico_edit.toHtml()
        # Montar novo HTML, garantindo separação de blocos
        novo_html = f'{prefixo}<div></div>{html_antigo}'
        self.historico_edit.setHtml(novo_html)
        # Scroll para o topo
        v_scroll = self.historico_edit.verticalScrollBar()
        if v_scroll is not None:
            v_scroll.setValue(0)

    def json_richtext_to_html(self, json_list):
        html = ""
        current_block = ""
        last_bg = None
        for obj in json_list:
            char = obj.get("char", "")
            # Trata quebras de linha como novo bloco
            if char == "\n":
                if current_block:
                    html += current_block + "<br>"
                    current_block = ""
                continue
            style = ""
            bg = obj.get("background")
            if bg:
                style += f"background-color:{bg};"
            span = char
            if style:
                span = f"<span style='{style}'>{span}</span>"
            if obj.get("bold"):
                span = f"<b>{span}</b>"
            if obj.get("italic"):
                span = f"<i>{span}</i>"
            if obj.get("underline"):
                span = f"<u>{span}</u>"
            current_block += span
        if current_block:
            html += current_block
        return html

    def text_with_tags_to_html(self, text, tags):
        html = ""
        opens = []
        tags_sorted = sorted(tags, key=lambda t: float(t["start"]))
        i = 0
        while i < len(text):
            # Abre tags que começam aqui
            for tag in tags_sorted:
                if int(float(tag["start"])) == i:
                    if tag["tag"] == "negrito":
                        html += "<b>"
                        opens.append("b")
                    if tag["tag"] == "sel":
                        html += "<span style='background-color: #ffff00;'>"
                        opens.append("span")
            c = text[i]
            if c == "\n":
                html += "<br>"
            else:
                html += c
            # Fecha tags que terminam aqui
            for tag in tags_sorted:
                if int(float(tag["end"])) == i + 1:
                    if tag["tag"] == "negrito" and "b" in opens:
                        html += "</b>"
                        opens.remove("b")
                    if tag["tag"] == "sel" and "span" in opens:
                        html += "</span>"
                        opens.remove("span")
            i += 1
        # Fecha tags abertas
        for t in reversed(opens):
            html += f"</{t}>"
        return html

    def load_data(self):
        d = self.paciente_data
        self.nome_edit.setText(d.get('nome', ''))
        self.sexo_combo.setCurrentText(d.get('sexo', ''))
        nasc = d.get('data_nascimento')
        if nasc:
            try:
                self.nasc_edit.setDate(QDate.fromString(nasc, 'dd/MM/yyyy'))
            except:
                pass
        self.naturalidade_edit.setText(d.get('naturalidade', ''))
        self.profissao_edit.setText(d.get('profissao', ''))
        self.estado_civil_combo.setCurrentText(d.get('estado_civil', ''))
        self.contacto_edit.setText(d.get('contacto', ''))
        self.email_edit.setText(d.get('email', ''))
        self.local_combo.setCurrentText(d.get('local_habitual', ''))
        # Histórico clínico
        historico = d.get('historico', [])
        print('DEBUG HISTÓRICO:', type(historico), str(historico)[:120])
        # 1. Formato texto+tags
        if isinstance(historico, dict) and 'text' in historico and 'tags' in historico:
            print('Formato: texto+tags')
            html = self.text_with_tags_to_html(historico['text'], historico['tags'])
            self.historico_edit.setHtml(html)
        # 2. JSON rich text (lista de chars)
        elif isinstance(historico, str) and historico.strip().startswith('[{'):
            print('Formato: JSON rich text')
            try:
                historico_json = json.loads(historico)
                html = self.json_richtext_to_html(historico_json)
                self.historico_edit.setHtml(html)
            except Exception as e:
                print('Erro ao converter histórico JSON:', e)
                self.historico_edit.setPlainText(historico)
        # 3. HTML (tem tags <b>, <div>, etc.)
        elif isinstance(historico, str) and ('<' in historico and '>' in historico):
            print('Formato: HTML')
            self.historico_edit.setHtml(historico)
        # 4. Lista de dicts (ex: [{'data':..., 'texto':...}, ...])
        elif isinstance(historico, list) and all(isinstance(x, dict) for x in historico):
            print('Formato: lista de dicts')
            texto = ''
            for item in historico[-5:]:
                data = item.get('data', '')
                texto_item = item.get('texto', '')
                texto += f"""
                    <div style='margin-bottom: 18px; padding-bottom: 8px; border-bottom: 1px dashed #aaa;'>
                        <div style='font-weight: bold; font-size: 14px; color: #2a2a2a;'>{data}</div>
                        <div style='margin-top: 6px;'>{texto_item}</div>
                    </div>
                """
            self.historico_edit.setHtml(texto)
        # 5. Lista de strings
        elif isinstance(historico, list) and all(isinstance(x, str) for x in historico):
            print('Formato: lista de strings')
            self.historico_edit.setHtml('<br>'.join(historico))
        # 6. Texto simples
        elif isinstance(historico, str):
            print('Formato: texto simples')
            self.historico_edit.setPlainText(historico)
        # 7. Notas antigas migradas para histórico
        elif d.get('notas') and not self.historico_edit.toPlainText():
            print('Formato: notas antigas')
            self.historico_edit.setHtml(d.get('notas'))
        else:
            print('Formato desconhecido')
            self.historico_edit.setPlainText(str(historico))

    def guardar(self):
        from db_manager import DBManager
        dados = {
            'nome': self.nome_edit.text(),
            'sexo': self.sexo_combo.currentText(),
            'data_nascimento': self.nasc_edit.date().toString('dd/MM/yyyy'),
            'naturalidade': self.naturalidade_edit.text(),
            'profissao': self.profissao_edit.text(),
            'estado_civil': self.estado_civil_combo.currentText(),
            'contacto': self.contacto_edit.text(),
            'email': self.email_edit.text(),
            'local_habitual': self.local_combo.currentText(),
            'historico': self.historico_edit.toHtml()
        }
        if 'id' in self.paciente_data:
            dados['id'] = self.paciente_data['id']
        db = DBManager()
        # Prevenção de duplicação por nome + data_nascimento
        query = "SELECT * FROM pacientes WHERE nome = ? AND data_nascimento = ?"
        params = (dados['nome'], dados['data_nascimento'])
        duplicados = db.execute_query(query, params)
        if duplicados and (not ('id' in dados and duplicados[0].get('id') == dados['id'])):
            QMessageBox.warning(self, "Duplicado", "Já existe um paciente com este nome e data de nascimento.")
            return
        novo_id = db.save_or_update_paciente(dados)
        if novo_id != -1:
            self.paciente_data['id'] = novo_id
            self.setWindowTitle(dados['nome'])
            self.dirty = False
            QMessageBox.information(self, "Sucesso", "Paciente guardado com sucesso!")
        else:
            QMessageBox.critical(self, "Erro", "Erro ao guardar paciente.")

    @staticmethod
    def mostrar_seletor(callback):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMenu
        from PyQt6.QtCore import Qt, QPoint
        class SeletorDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle('Procurar paciente')
                self.setModal(True)
                self.resize(600, 480)
                self.db = DBManager()
                self.resultados = []
                layout = QVBoxLayout(self)
                # Filtros
                filtros_layout = QHBoxLayout()
                self.nome_edit = QLineEdit(); self.nome_edit.setPlaceholderText('Nome')
                self.nasc_edit = QLineEdit(); self.nasc_edit.setPlaceholderText('Data nascimento (dd/mm/aaaa)')
                self.contacto_edit = QLineEdit(); self.contacto_edit.setPlaceholderText('Contacto')
                self.email_edit = QLineEdit(); self.email_edit.setPlaceholderText('Email')
                for w in [self.nome_edit, self.nasc_edit, self.contacto_edit, self.email_edit]:
                    filtros_layout.addWidget(w)
                layout.addLayout(filtros_layout)
                # Botões
                btns = QHBoxLayout()
                self.btn_abrir = QPushButton('Abrir')
                estilizar_botao(self.btn_abrir)
                self.btn_abrir.clicked.connect(self.abrir)
                self.btn_eliminar = QPushButton('🗑️ Eliminar')
                estilizar_botao(self.btn_eliminar, cor="#c62828", hover="#e57373")
                self.btn_eliminar.clicked.connect(self.eliminar)
                btns.addStretch()
                btns.addWidget(self.btn_abrir)
                btns.addWidget(self.btn_eliminar)
                layout.addLayout(btns)
                # Resultados
                self.lista = QListWidget()
                self.lista.setStyleSheet("""
                    QListWidget {
                        font-size: 15px;
                        margin: 8px;
                        border-radius: 6px;
                        background: #f7f9fa;
                    }
                    QListWidget::item {
                        padding: 12px 8px;
                        border-bottom: 1px solid #e0e0e0;
                        min-height: 32px;
                    }
                    QListWidget::item:selected {
                        background: #eaf3fa;
                        color: #007ACC;
                    }
                """)
                self.lista.itemDoubleClicked.connect(self.abrir)
                self.lista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                self.lista.customContextMenuRequested.connect(self.menu_contexto)
                layout.addWidget(self.lista, 1)
                # Pesquisa ao escrever
                self.nome_edit.textChanged.connect(self.pesquisar)
                self.nasc_edit.textChanged.connect(self.pesquisar)
                self.contacto_edit.textChanged.connect(self.pesquisar)
                self.email_edit.textChanged.connect(self.pesquisar)
                self.pesquisar()
            def normalizar(self, s):
                if not s: return ''
                return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()
            def pesquisar(self):
                todos = self.db.get_all_pacientes()
                nome = self.normalizar(self.nome_edit.text())
                nasc = self.nasc_edit.text().strip()
                contacto = self.contacto_edit.text().replace(' ', '')
                email = self.normalizar(self.email_edit.text())
                self.lista.clear()
                self.resultados = []
                for p in todos:
                    if nome and nome not in self.normalizar(p.get('nome', '')):
                        continue
                    if nasc and nasc not in (p.get('data_nascimento') or ''):
                        continue
                    if contacto and contacto not in (p.get('contacto') or '').replace(' ', ''):
                        continue
                    if email and email not in self.normalizar(p.get('email', '')):
                        continue
                    self.resultados.append(p)
                    item = QListWidgetItem(f"{p.get('nome','')} | {p.get('data_nascimento','')} | {p.get('contacto','')}")
                    self.lista.addItem(item)
            def abrir(self):
                idx = self.lista.currentRow()
                if idx >= 0 and idx < len(self.resultados):
                    paciente = self.resultados[idx]
                    self.accept()
                    callback(paciente)
            def eliminar(self):
                idx = self.lista.currentRow()
                if idx >= 0 and idx < len(self.resultados):
                    paciente = self.resultados[idx]
                    from PyQt6.QtWidgets import QMessageBox
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Eliminar paciente")
                    msg.setText(f"Tem a certeza que deseja eliminar o paciente '{paciente.get('nome','')}'?")
                    btn_sim = msg.addButton("Sim", QMessageBox.ButtonRole.YesRole)
                    btn_nao = msg.addButton("Não", QMessageBox.ButtonRole.NoRole)
                    msg.setIcon(QMessageBox.Icon.Question)
                    msg.exec()
                    if msg.clickedButton() == btn_sim:
                        self.db.execute_query(f"DELETE FROM pacientes WHERE id = ?", (paciente['id'],))
                        self.pesquisar()
            def menu_contexto(self, pos: QPoint):
                idx = self.lista.indexAt(pos).row()
                if idx < 0 or idx >= len(self.resultados):
                    return
                menu = QMenu(self)
                menu.addAction('Abrir paciente', self.abrir)
                menu.addAction('🗑️ Eliminar', self.eliminar)
                menu.exec(self.lista.mapToGlobal(pos))
        dlg = SeletorDialog()
        dlg.exec()

    def closeEvent(self, event):
        if getattr(self, 'dirty', False):
            msg = QMessageBox(self)
            msg.setWindowTitle("Alterações por guardar")
            msg.setText("Existem alterações não guardadas. Deseja sair sem guardar?")
            btn_sim = msg.addButton("Sim", QMessageBox.ButtonRole.YesRole)
            btn_nao = msg.addButton("Não", QMessageBox.ButtonRole.NoRole)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.exec()
            if msg.clickedButton() == btn_nao:
                event.ignore()
                return
        event.accept()

    def abrir_terapia(self):
        try:
            from terapia_quantica import TerapiaQuantica
            self.terapia_window = TerapiaQuantica(paciente_data=self.paciente_data)
            self.terapia_window.showMaximized()
        except ImportError:
            QMessageBox.warning(self, 'Erro', 'Módulo Terapia Quântica não encontrado.')
            
    def exportar_para_terapia_quantica(self):
        """Exporta dados para o módulo de Terapia Quântica."""
        try:
            from terapia_quantica import TerapiaQuantica
            self.terapia_window = TerapiaQuantica(paciente_data=self.paciente_data)
            self.terapia_window.showMaximized()
        except ImportError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Exportar para terapia quântica", "Módulo em desenvolvimento")

    def abrir_terapia_com_iris(self, tipo_iris, caminho_imagem):
        """
        Abre o módulo de terapia quântica enviando os dados da íris.
        
        Args:
            tipo_iris: str - "esq" ou "drt" para indicar qual olho
            caminho_imagem: str - caminho para a imagem da íris
        """
        try:
            from terapia_quantica import TerapiaQuantica
            self.terapia_window = TerapiaQuantica(
                paciente_data=self.paciente_data,
                iris_data={
                    'tipo': tipo_iris,
                    'caminho': caminho_imagem
                }
            )
            self.terapia_window.showMaximized()
        except ImportError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Exportar para terapia quântica",
                "Módulo de Terapia Quântica em desenvolvimento."
            )

    def abrir_sms_dialogo(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QMessageBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Enviar SMS")
        layout = QVBoxLayout(dialog)

        numero_edit = QLineEdit()
        numero_edit.setText(self.contacto_edit.text())
        numero_edit.setPlaceholderText("Número de telemóvel (+351...)")

        mensagem_edit = QTextEdit()
        mensagem_edit.setPlaceholderText("Escreve aqui a mensagem a enviar...")

        btn_enviar = QPushButton("Enviar agora")
        estilizar_botao(btn_enviar, cor="#1976d2", hover="#42a5f5")
        btn_enviar.clicked.connect(lambda: QMessageBox.information(dialog, "SMS", "Mensagem enviada (simulado)"))

        btn_agendar = QPushButton("Agendar")
        btn_agendar.setEnabled(False)
        btn_agendar.setVisible(False)

        layout.addWidget(numero_edit)
        layout.addWidget(mensagem_edit)
        layout.addWidget(btn_enviar)
        layout.addWidget(btn_agendar)

        dialog.exec()







if __name__ == '__main__':
    app = QApplication(sys.argv)
    paciente = {
        'nome': 'Maria Silva',
        'sexo': 'Feminino',
        'data_nascimento': '12/05/1980',
        'naturalidade': 'Lisboa',
        'profissao': 'Enfermeira',
        'estado_civil': 'Casada',
        'contacto': '912345678',
        'email': 'maria@email.com',
        'local_habitual': 'Chão de Lopes',
        'historico': [
            {'data': '01/01/2024', 'texto': 'Consulta de rotina.'},
            {'data': '15/02/2024', 'texto': 'Queixas de dor lombar.'},
            {'data': '10/03/2024', 'texto': 'Melhoria significativa.'},
            {'data': '01/04/2024', 'texto': 'Nova medicação.'}
        ]
    }
    window = FichaPaciente(paciente)
    window.showMaximized()
    print("✅ Botões estilizados, histórico com inserção de sessão no topo, biotipos completos. Confirma se tudo está correto?")
    sys.exit(app.exec())