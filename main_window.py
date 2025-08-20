import sys
import os
import traceback
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QToolButton,
    QGridLayout,
    QMenu,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QDialog,
)
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, QDateTime
from ficha_paciente import FichaPaciente

# Importar módulos de íris com tratamento de erro
try:
    from iris_canvas import IrisCanvas
except Exception as e:
    traceback.print_exc()
    IrisCanvas = None

try:
    from iris_anonima_canvas import IrisAnonimaCanvas        
except Exception as e:
    traceback.print_exc()
    IrisAnonimaCanvas = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Biodesk')
        self.setGeometry(100, 100, 900, 700)
        self.init_ui()
        self.load_styles()
        # Maximizar respeitando a barra de tarefas
        self.show_maximized_safe()
        # Painéis custom
        self._patients_panel = None
        
        # Inicializar e configurar timer para data/hora
        self.setup_datetime_display()
        
        # Carregar ícones das abas com fallbacks seguros
        self.carregar_icones_abas()
        
        # Configurar cursores apropriados
        self.configurar_cursores()

    def configurar_cursores(self):
        """Define cursores adequados para diferentes elementos da interface"""
        try:
            from PyQt6.QtWidgets import QCheckBox, QLineEdit, QTextEdit, QPushButton, QToolButton
            
            # Aplicar cursor de seta (padrão) para todas as checkboxes
            for checkbox in self.findChildren(QCheckBox):
                checkbox.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Aplicar cursor de texto para campos de entrada
            for field in self.findChildren(QLineEdit):
                field.setCursor(Qt.CursorShape.IBeamCursor)
            
            for text_edit in self.findChildren(QTextEdit):
                text_edit.setCursor(Qt.CursorShape.IBeamCursor)
            
            # Aplicar cursor de mão para botões
            for button in self.findChildren(QPushButton):
                button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            for tool_button in self.findChildren(QToolButton):
                tool_button.setCursor(Qt.CursorShape.PointingHandCursor)
                
            print("✓ Cursores configurados adequadamente")
        except Exception as e:
            print(f"Erro ao configurar cursores: {str(e)}")

    def carregar_icones_abas(self):
        """Carrega os ícones das abas com tratamento de erros robusto"""
        try:
            # Dicionário de ícones e seus caminhos de fallback
            icones = {
                "iris": {
                    "principal": os.path.join(os.path.dirname(__file__), 'assets', 'eye.png'),
                    "fallback_text": "👁️"  # Emoji como último recurso
                },
                "prescricao": {
                    "principal": os.path.join(os.path.dirname(__file__), 'assets', 'quantum.png'),
                    "fallback_text": "📝"  # Emoji como último recurso
                }
            }
            
            # Função auxiliar para carregar ícone com fallbacks
            def carregar_icone_seguro(config):
                # Tentar caminho principal
                if os.path.exists(config["principal"]):
                    return QIcon(config["principal"])
                
                # Criar ícone a partir de texto (último recurso)
                from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                font = QFont("Segoe UI", 16)
                painter.setFont(font)
                painter.setPen(QColor("#2E7D32"))
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, config["fallback_text"])
                painter.end()
                return QIcon(pixmap)
            
            # Verificar se existem widgets de abas para aplicar ícones
            # (Este método será chamado mas só aplicará se houver abas definidas)
            print("✓ Sistema de ícones inicializado com fallbacks seguros")
            
        except Exception as e:
            print(f"Erro ao carregar ícones: {str(e)}")

    def setup_datetime_display(self):
        """Configura e inicia o display de data/hora elegante"""
        # Configurar localização para português
        from PyQt6.QtCore import QLocale
        QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal))
        
        # Atualizar data/hora inicial
        self.update_datetime()
        
        # Timer para atualizar a hora a cada segundo
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)  # Atualiza a cada 1 segundo
    
    def update_datetime(self):
        """Atualiza os labels de data e hora em português"""
        current_datetime = QDateTime.currentDateTime()
        
        # Dicionários para tradução manual
        dias_semana = {
            1: "Segunda-feira", 2: "Terça-feira", 3: "Quarta-feira", 
            4: "Quinta-feira", 5: "Sexta-feira", 6: "Sábado", 7: "Domingo"
        }
        
        meses = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        
        # Obter componentes da data
        dia_semana = dias_semana[current_datetime.date().dayOfWeek()]
        dia = current_datetime.date().day()
        mes = meses[current_datetime.date().month()]
        
        # Formatar data em português (ex: "Domingo, 18 de Agosto")
        date_text = f"{dia_semana}, {dia} de {mes}"
        self.date_label.setText(date_text)
        
        # Formatar hora (ex: "09:50:30")
        time_text = current_datetime.toString("hh:mm:ss")
        self.time_label.setText(time_text)

    def mousePressEvent(self, event):
        """Fecha o painel de pacientes se clicar em qualquer lugar da janela principal"""
        if self._patients_panel and self._patients_panel.isVisible():
            self._patients_panel.hide()
        super().mousePressEvent(event)

    def init_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        # Fundo com gradiente verde-acinzentado profissional
        central.setStyleSheet("""
            QWidget#centralWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:0.5 #f8faf9, stop:1 #f0f5f3);
            }
        """)

        # Layouts principais: topo (barra), conteúdo (hero card), ações (botões)
        root = QVBoxLayout()
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(20)

        topbar = QHBoxLayout()
        topbar.setContentsMargins(0, 0, 0, 0)
        topbar.setSpacing(0)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(16)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(20)
        actions.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Botão To-Do List (estilo moderno da iridologia)
        btn_todo = QToolButton()
        btn_todo.setText('📝')
        btn_todo.setFixedSize(50, 50)
        btn_todo.setStyleSheet("""
            QToolButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #ffc107;
                color: white;
                border-color: #ffc107;
            }
            QToolButton:pressed {
                background-color: #e0a800;
                border-color: #e0a800;
            }
        """)
        btn_todo.setToolTip('📝 Lista de Tarefas')
        btn_todo.clicked.connect(self.abrir_todo_list)

        # Posicionar o botão no canto superior direito (barra superior)
        topbar.addStretch(1)
        topbar.addWidget(btn_todo, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Botão Pacientes com menu
        btn_pacientes = QToolButton()
        btn_pacientes.setText('Fichas de Pacientes')
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'user.png')
        if os.path.exists(icon_path):
            btn_pacientes.setIcon(QIcon(icon_path))
            btn_pacientes.setIconSize(QSize(72, 72))
        btn_pacientes.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_pacientes.setFixedSize(200, 200)
        # Estilo verde suave para Fichas de Pacientes
        btn_pacientes.setStyleSheet("""
            QToolButton {
                font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 18px;
                padding: 22px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #66BB6A, stop: 1 #4CAF50);
                margin: 8px;
                color: white;
                text-align: center;
            }
            QToolButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #81C784, stop: 1 #66BB6A);
            }
            QToolButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4CAF50, stop: 1 #388E3C);
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        btn_pacientes.setToolTip('Gerir utentes: ver e registar novos utentes')
        # Usar painel custom em vez de QMenu
        btn_pacientes.clicked.connect(lambda: self.show_pacientes_panel(btn_pacientes))

        # Adicionar sombra verde suave ao botão Pacientes
        shadow_pacientes = QGraphicsDropShadowEffect()
        shadow_pacientes.setBlurRadius(15)
        shadow_pacientes.setXOffset(0)
        shadow_pacientes.setYOffset(4)
        shadow_pacientes.setColor(QColor(76, 175, 80, 60))
        btn_pacientes.setGraphicsEffect(shadow_pacientes)

        # Adicionar ao grupo de ações
        actions.addWidget(btn_pacientes)

        # Botão Íris (acesso direto ao modo anónimo)
        btn_iris = QToolButton()
        btn_iris.setText('Íris')
        icon_path_iris = os.path.join(os.path.dirname(__file__), 'assets', 'eye.png')
        if os.path.exists(icon_path_iris):
            btn_iris.setIcon(QIcon(icon_path_iris))
            btn_iris.setIconSize(QSize(72, 72))
        btn_iris.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_iris.setFixedSize(200, 200)
        # Estilo verde-água para Íris
        btn_iris.setStyleSheet("""
            QToolButton {
                font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 18px;
                padding: 22px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #26A69A, stop: 1 #00796B);
                margin: 8px;
                color: white;
                text-align: center;
            }
            QToolButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4DB6AC, stop: 1 #26A69A);
            }
            QToolButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #00796B, stop: 1 #00695C);
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        btn_iris.setToolTip('Módulo de análise de íris')
        # Conectar diretamente à análise anónima (sem menu)
        btn_iris.clicked.connect(lambda: self.open_iris(modo_anonimo=True))
        
        # Adicionar sombra verde-água ao botão Íris
        shadow_iris = QGraphicsDropShadowEffect()
        shadow_iris.setBlurRadius(15)
        shadow_iris.setXOffset(0)
        shadow_iris.setYOffset(4)
        shadow_iris.setColor(QColor(38, 166, 154, 60))
        btn_iris.setGraphicsEffect(shadow_iris)
        
        actions.addWidget(btn_iris)

        # Botão Terapia
        btn_terapia = QToolButton()
        btn_terapia.setText('Terapia Quântica')
        icon_path_terapia = os.path.join(os.path.dirname(__file__), 'assets', 'quantum.png')
        if os.path.exists(icon_path_terapia):
            btn_terapia.setIcon(QIcon(icon_path_terapia))
            btn_terapia.setIconSize(QSize(72, 72))
        btn_terapia.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_terapia.setFixedSize(200, 200)
        # Estilo moderno (roxo) para Terapia
        btn_terapia.setStyleSheet("""
            QToolButton {
                font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 18px;
                padding: 22px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #558B2F, stop: 1 #33691E);
                margin: 8px;
                color: white;
                text-align: center;
            }
            QToolButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #689F38, stop: 1 #558B2F);
            }
            QToolButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #33691E, stop: 1 #1B5E20);
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        btn_terapia.clicked.connect(self.open_terapia)
        
        # Adicionar sombra verde musgo ao botão Terapia
        shadow_terapia = QGraphicsDropShadowEffect()
        shadow_terapia.setBlurRadius(15)
        shadow_terapia.setXOffset(0)
        shadow_terapia.setYOffset(4)
        shadow_terapia.setColor(QColor(85, 139, 47, 60))
        btn_terapia.setGraphicsEffect(shadow_terapia)
        
        actions.addWidget(btn_terapia)

        # Hero card com design clínico profissional
        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_card.setStyleSheet("""
            QFrame#heroCard {
                background: rgba(255,255,255,0.95);
                border-radius: 24px;
                border: 1px solid rgba(46,125,50,0.08);
                padding: 32px;
            }
        """)
        
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(24)

        # Logo à esquerda (tamanho duplicado para máxima visibilidade)
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'Biodesk.png')
        if os.path.exists(logo_path):
            logo = QLabel()
            pixmap = QPixmap(logo_path)
            logo.setPixmap(
                pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hero_layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Layout central com texto e data/hora abaixo
        center_layout = QVBoxLayout()
        
        # Texto de boas-vindas no topo
        text_layout = QVBoxLayout()
        welcome_title = QLabel("Bem-vindo ao Biodesk")
        welcome_title.setStyleSheet("""
            font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
            font-size: 26px; 
            font-weight: 600; 
            color: #2E7D32; 
            margin-bottom: 8px;
        """)
        
        welcome_subtitle = QLabel("Sistema integrado para gestão clínica e análise de íris")
        welcome_subtitle.setStyleSheet("""
            font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
            font-size: 14px; 
            color: #546E7A; 
            margin-bottom: 12px;
        """)
        
        welcome_instruction = QLabel("Escolha uma das opções abaixo para começar:")
        welcome_instruction.setStyleSheet("""
            font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
            font-size: 13px; 
            color: #455A64; 
            font-weight: 400;
        """)
        
        text_layout.addWidget(welcome_title)
        text_layout.addWidget(welcome_subtitle)
        text_layout.addSpacing(8)
        text_layout.addWidget(welcome_instruction)
        
        center_layout.addLayout(text_layout)
        center_layout.addSpacing(20)
        
        # Widget de data/hora elegante abaixo do texto
        datetime_container = QHBoxLayout()
        datetime_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Data atual
        self.date_label = QLabel()
        self.date_label.setStyleSheet("""
            font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: #2E7D32;
            background: rgba(46,125,50,0.08);
            border-radius: 8px;
            padding: 8px 16px;
            margin-right: 12px;
        """)
        
        # Hora atual (será atualizada)
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', 'Consolas', monospace;
            font-size: 16px;
            font-weight: 700;
            color: #00796B;
            background: rgba(0,121,107,0.08);
            border-radius: 8px;
            padding: 8px 16px;
        """)
        
        datetime_container.addWidget(self.date_label)
        datetime_container.addWidget(self.time_label)
        
        center_layout.addLayout(datetime_container)
        center_layout.addStretch()
        
        hero_layout.addLayout(center_layout, 1)
        
        # Adicionar sombra suave e profissional ao hero card
        hero_shadow = QGraphicsDropShadowEffect()
        hero_shadow.setBlurRadius(25)
        hero_shadow.setXOffset(0)
        hero_shadow.setYOffset(8)
        hero_shadow.setColor(QColor(46, 125, 50, 15))
        hero_card.setGraphicsEffect(hero_shadow)
        
        content.addWidget(hero_card, 0, Qt.AlignmentFlag.AlignHCenter)

        # Montar layout raiz
        root.addLayout(topbar)
        root.addLayout(content)
        root.addSpacing(8)
        root.addLayout(actions)

        central.setLayout(root)
        self.setCentralWidget(central)

    def open_iris(self, modo_anonimo=True, paciente_data=None):
        """
        Abre o módulo de análise de íris.
        - modo_anonimo=True: abre o módulo anónimo (sem paciente)
        - modo_anonimo=False: abre o módulo com dados do paciente
        """
        try:
            if modo_anonimo:
                if IrisAnonimaCanvas is None:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self,
                        "Erro de Importação",
                        "Não foi possível carregar o módulo IrisAnonimaCanvas.\n\n"
                        "Verifique se o arquivo iris_anonima_canvas.py está presente e sem erros."
                    )
                    return
                self.iris_window = IrisAnonimaCanvas()
            else:
                if IrisCanvas is None:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self,
                        "Erro de Importação",
                        "Não foi possível carregar o módulo IrisCanvas.\n\n"
                        "Verifique se o arquivo iris_canvas.py está presente e sem erros."
                    )
                    return
                self.iris_window = IrisCanvas(paciente_data=paciente_data)

            # Mostrar/maximizar de forma segura
            self.safe_maximize_window(self.iris_window)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Erro ao Abrir Módulo de Íris",
                f"Ocorreu um erro ao tentar abrir o módulo de íris:\n\n{str(e)}\n\n"
                "Verifique os logs no console para mais detalhes."
            )

    def load_styles(self):
        # Carregar QSS global se existir, mantendo estilos locais dos botões
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'assets', 'biodesk.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    qss = f.read()
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(qss)
        except Exception as e:
            pass  # Ignorar erros de carregamento de estilo

    def abrir_lista_pacientes(self):
        FichaPaciente.mostrar_seletor(callback=self.abrir_ficha_existente, parent=self)

    def abrir_ficha_nova(self):
        # ✨ MÉTODO ALTERNATIVO: Criar diretamente e mostrar imediatamente
        self.ficha_window = FichaPaciente(parent=self)
        self.ficha_window.setWindowTitle('Novo Utente')
        self.safe_maximize_window(self.ficha_window)
        self.ficha_window.show()
        self.ficha_window.raise_()
        self.ficha_window.activateWindow()

    def abrir_ficha_existente(self, paciente_data):
        # ✨ MÉTODO ALTERNATIVO: Criar diretamente e mostrar imediatamente
        self.ficha_window = FichaPaciente(paciente_data, parent=self)
        self.ficha_window.setWindowTitle(paciente_data.get('nome', 'Utente'))
        self.safe_maximize_window(self.ficha_window)
        self.ficha_window.show()
        self.ficha_window.raise_()
        self.ficha_window.activateWindow()

    def abrir_iris_paciente(self, paciente_data):
        """
        Abre o módulo de análise de íris com dados de um paciente específico
        """
        self.open_iris(modo_anonimo=False, paciente_data=paciente_data)

    def abrir_terapia_paciente(self, paciente_data):
        """
        Abre o módulo de terapia quântica com dados de um paciente específico
        """
        try:
            from terapia_quantica_window import TerapiaQuanticaWindow
            self.terapia_window = TerapiaQuanticaWindow(paciente_data=paciente_data)
            self.safe_maximize_window(self.terapia_window)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir terapia para paciente:\n\n{str(e)}\n\n"
                "Verifique o console para mais detalhes."
            )

    def abrir_todo_list(self):
        """Abre a janela de lista de tarefas"""
        try:
            from todo_list_window import TodoListWindow
            self.todo_window = TodoListWindow()
            self.todo_window.show()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir lista de tarefas:\n\n{str(e)}"
            )

    def show_pacientes_panel(self, anchor_btn: QToolButton):
        """Mostra um painel flutuante acima do botão de Pacientes."""
        try:
            if self._patients_panel is None:
                self._patients_panel = PatientsPanel(self)
                self._patients_panel.selectRequested.connect(self.abrir_lista_pacientes)
                self._patients_panel.newRequested.connect(self.abrir_ficha_nova)

            # Calcular posição usando coordenadas da janela principal diretamente
            btn_geom = anchor_btn.geometry()
            main_geom = self.geometry()
            panel_size = self._patients_panel.sizeHint()

            # Usar posição absoluta simples baseada na janela principal
            # O botão está no layout da janela, então usar suas coordenadas diretamente
            btn_center_x = main_geom.x() + btn_geom.x() + (btn_geom.width() // 2)
            btn_top_y = main_geom.y() + btn_geom.y()
            
            # Centralizar painel horizontalmente com o botão
            x = btn_center_x - (panel_size.width() // 2)
            
            # Posicionar painel 10px acima do botão para um espaço elegante
            y = btn_top_y - panel_size.height() - 1

            # Garantir que não saia da tela
            screen = QGuiApplication.primaryScreen()
            if screen:
                avail = screen.availableGeometry()
                x = max(avail.left() + 10, min(x, avail.right() - 10 - panel_size.width()))
                y = max(avail.top() + 30, min(y, avail.bottom() - 10 - panel_size.height()))

            self._patients_panel.move(QPoint(x, y))
            self._patients_panel.show()
            self._patients_panel.raise_()
            self._patients_panel.activateWindow()
        except Exception as e:
            print(f"[ERRO] Erro ao mostrar painel Pacientes: {e}")
            import traceback
            traceback.print_exc()

    def open_terapia(self):
        """Abre módulo de terapia quântica com HS3"""
        try:
            # Verificar se FrequencyList.xls existe
            import os
            frequency_file = os.path.join(os.path.dirname(__file__), 'assets', 'FrequencyList.xls')
            if not os.path.exists(frequency_file):
                from PyQt6.QtWidgets import QMessageBox, QFileDialog
                reply = QMessageBox.question(
                    self,
                    "FrequencyList.xls não encontrado",
                    f"O arquivo FrequencyList.xls não foi encontrado em:\n{frequency_file}\n\n"
                    "Deseja localizar o arquivo agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    file_path, _ = QFileDialog.getOpenFileName(
                        self,
                        "Selecionar FrequencyList.xls",
                        "",
                        "Excel files (*.xls *.xlsx)"
                    )
                    if file_path:
                        import shutil
                        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
                        os.makedirs(assets_dir, exist_ok=True)
                        shutil.copy(file_path, frequency_file)
                    else:
                        print("❌ Arquivo não selecionado")
                        return
                else:
                    return
            
            # Verificar/carregar frequências na primeira execução
            db_file = "frequencies.db"
            if not os.path.exists(db_file):
                from frequency_loader import FrequencyLoader
                loader = FrequencyLoader(frequency_file)
            
            # Abrir janela de terapia
            from terapia_quantica_window import TerapiaQuanticaWindow
            self.terapia_window = TerapiaQuanticaWindow(paciente_data=None)
            self.safe_maximize_window(self.terapia_window)
            
        except ImportError as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Módulo Indisponível",
                f"Erro ao importar módulo de terapia:\n\n{str(e)}\n\n"
                "Verifique se todas as dependências estão instaladas:\n"
                "• pip install pandas openpyxl xlrd\n"
                "• pip install pyqtgraph\n"
                "• pip install numpy scipy"
            )
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir terapia quântica:\n\n{str(e)}\n\n"
                "Verifique o console para mais detalhes."
            )
    
    def show_maximized_safe(self):
        """Maximiza a janela respeitando a barra de tarefas do Windows"""
        try:
            # Definir o estado de janela para maximizado antes de mostrar
            self.setWindowState(Qt.WindowState.WindowMaximized)
            
            # Garantir que a flag de maximização esteja ativada
            self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
            
            # Forçar a janela a permanecer maximizada
            screen = QGuiApplication.primaryScreen()
            if screen:
                available_geometry = screen.availableGeometry()
                self.setGeometry(available_geometry)
            
            # Verificação adicional de estado pós-configuração
            if not self.isMaximized():
                self.showMaximized()
        except Exception as e:
            print(f"Erro ao maximizar: {str(e)}")
            self.showMaximized()  # Fallback

    def safe_maximize_window(self, window):
        """Maximiza qualquer janela respeitando a barra de tarefas"""
        try:
            # Configurar o estado da janela para maximizado
            window.setWindowState(Qt.WindowState.WindowMaximized)
            
            # Garantir que esteja maximizada após exibição
            window.show()
            
            # Verificação adicional com delay para garantir maximização
            QTimer.singleShot(100, lambda: window.showMaximized() if not window.isMaximized() else None)
        except Exception as e:
            print(f"Erro ao maximizar janela: {str(e)}")
            try:
                window.showMaximized()
            except:
                window.show()


class PatientsPanel(QDialog):
    from PyQt6.QtCore import pyqtSignal
    selectRequested = pyqtSignal()
    newRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Container principal com design pill (cilíndrico)
        container = QFrame()
        container.setObjectName("patientsPanel")
        container.setStyleSheet(
            """
            QFrame#patientsPanel {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(46,125,50,0.15);
                border-radius: 25px;
                min-width: 360px;
                max-width: 360px;
            }
            """
        )

        # Layout horizontal para os dois pills lado a lado com mais espaçamento
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Pill 1: Selecionar Paciente (forma oval verde-água)
        btn_select = QPushButton("🔍\nSelecionar")
        btn_select.setStyleSheet("""
            QPushButton {
                font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #E0F2F1, stop: 1 #B2DFDB);
                color: #00796B;
                border: 1px solid rgba(0,121,107,0.2);
                border-radius: 22px;
                font-size: 12px;
                font-weight: 500;
                padding: 16px 8px;
                text-align: center;
                min-width: 140px;
                max-width: 140px;
                min-height: 44px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #26A69A, stop: 1 #00796B);
                color: white;
                border-color: #00796B;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: #00695C;
                border-color: #00695C;
            }
        """)

        # Pill 2: Novo Paciente (forma oval verde suave)
        btn_new = QPushButton("➕\nNovo")
        btn_new.setStyleSheet("""
            QPushButton {
                font-family: 'Segoe UI', 'Inter', 'Open Sans', 'Roboto', sans-serif;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #F1F8E9, stop: 1 #C8E6C9);
                color: #4CAF50;
                border: 1px solid rgba(76,175,80,0.2);
                border-radius: 22px;
                font-size: 12px;
                font-weight: 500;
                padding: 16px 8px;
                text-align: center;
                min-width: 140px;
                max-width: 140px;
                min-height: 44px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #66BB6A, stop: 1 #4CAF50);
                color: white;
                border-color: #4CAF50;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: #388E3C;
                border-color: #388E3C;
            }
        """)
        
        # Conectar sinais
        btn_select.clicked.connect(self.selectRequested.emit)
        btn_new.clicked.connect(self.newRequested.emit)
        
        # Fechar painel após clique com pequeno delay para melhor UX
        btn_select.clicked.connect(lambda: self.close_with_delay())
        btn_new.clicked.connect(lambda: self.close_with_delay())

        layout.addWidget(btn_select)
        layout.addWidget(btn_new)

        # Sombra suave que complementa o design pill
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(46, 125, 50, 40))
        shadow.setOffset(0, 6)
        container.setGraphicsEffect(shadow)

        # Layout principal
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

    def close_with_delay(self):
        """Fecha o painel com um pequeno delay para melhor UX"""
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(150, self.hide)  # 150ms delay

    def showEvent(self, event):
        """Animação sutil ao mostrar o painel"""
        super().showEvent(event)
        # Opcional: adicionar animação de fade-in ou scale
        
    def mousePressEvent(self, event):
        """Fecha o painel se clicar fora dele"""
        if not self.rect().contains(event.pos()):
            self.hide()
        super().mousePressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Maximizar ANTES de mostrar a janela
    window.setWindowState(Qt.WindowState.WindowMaximized)
    window.show()
    
    sys.exit(app.exec())
