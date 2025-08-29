import sys
import os
import traceback
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QDialog,
)
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication, QColor
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, QDateTime
from ficha_paciente import FichaPaciente
from biodesk_dialogs import BiodeskMessageBox

# ✅ IMPORTAR NOVO SISTEMA DE ESTILOS
try:
    from biodesk_styles import BiodeskStyles, ButtonType, DialogStyles
    # print("✅ BiodeskStyles v2.0 carregado no main_window.py")
except ImportError as e:
    print(f"⚠️ BiodeskStyles não disponível: {e}")
    BiodeskStyles = None

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

# 📧 Importar sistema de agendamento de emails
try:
    from email_scheduler import get_email_scheduler
    from emails_agendados_manager import EmailsAgendadosWindow
    email_scheduler_disponivel = True
except ImportError as e:
    print(f"⚠️ Sistema de agendamento de emails não disponível: {e}")
    email_scheduler_disponivel = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Biodesk')
        
        # 🔒 JANELA SEMPRE MAXIMIZADA - NÃO PODE SER REDIMENSIONADA
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.setGeometry(100, 100, 900, 700)
        # Definir tamanho mínimo para evitar layout quebrado
        self.setMinimumSize(1200, 800)
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
        
        # ✅ SISTEMA NOVO: BiodeskStyles v2.0 (substitui hotkeys do BiodeskStyleManager)
        if BiodeskStyles:
            # print("✅ Sistema BiodeskStyles ativo - hotkeys obsoletos removidos")
            pass
        else:
            print("⚠️ BiodeskStyles não disponível - funcionalidade reduzida")
            pass
            
        # 📧 Inicializar sistema de agendamento de emails
        self.inicializar_sistema_emails()
    
    def showEvent(self, event):
        """Garantir que a janela fica sempre maximizada quando mostrada"""
        super().showEvent(event)
        # Usar QTimer para garantir que a maximização ocorre após o evento
        QTimer.singleShot(50, self._ensure_maximized)
    
    def _ensure_maximized(self):
        """Garante que a janela principal fica maximizada"""
        if not self.isMaximized():
            self.showMaximized()
        # Timer adicional para manter maximizado
        QTimer.singleShot(100, self._check_maximized)
    
    def _check_maximized(self):
        """Verifica se continua maximizada"""
        if not self.isMaximized():
            self.showMaximized()

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
                    
        except Exception as e:
            pass  # Cursores não são críticos
    
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
            
        except ImportError:
                pass  # Ícones não são críticos
                
        except Exception as e:
            pass  # Ícones não são críticos

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
        try:
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
            
        except Exception as e:
            # Em caso de erro, apenas continue sem crashar
            print(f"⚠️ Erro no timer de data/hora: {e}")
            pass

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

        # Botão To-Do List (usa BiodeskStyles v2.0)
        btn_todo = QToolButton()
        btn_todo.setText('📝')
        btn_todo.setFixedSize(50, 50)
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
        btn_pacientes.setToolTip('Gerir utentes: ver e registar novos utentes')
        # Usar painel custom em vez de QMenu
        btn_pacientes.clicked.connect(lambda: self.show_pacientes_panel(btn_pacientes))

        # 🎨 Estilo personalizado para botão Pacientes
        btn_pacientes.setStyleSheet("""
            QToolButton {
                background-color: #f8f9fa;
                border: none;
                border-radius: 15px;
                color: #2c3e50;
                font-family: "Segoe UI", sans-serif;
                font-size: 16px;
                font-weight: 600;
            }
            QToolButton:hover {
                background-color: #a0cf9c;
            }
            QToolButton:pressed {
                background-color: #8bb38a;
            }
        """)

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
        btn_iris.setToolTip('Módulo de análise de íris')
        # Conectar diretamente à análise anónima (sem menu)
        btn_iris.clicked.connect(lambda: self.open_iris(modo_anonimo=True))
        
        # 🎨 Estilo personalizado para botão Íris
        btn_iris.setStyleSheet("""
            QToolButton {
                background-color: #f8f9fa;
                border: none;
                border-radius: 15px;
                color: #2c3e50;
                font-family: "Segoe UI", sans-serif;
                font-size: 16px;
                font-weight: 600;
            }
            QToolButton:hover {
                background-color: #d6ffd2;
            }
            QToolButton:pressed {
                background-color: #b8e6b5;
            }
        """)
        
        actions.addWidget(btn_iris)

        # Botão Terapia
        btn_terapia = QToolButton()
        btn_terapia.setText('Terapia Quântica')
        btn_terapia.setToolTip('Módulo de terapia quântica e medicina energética')
        icon_path_terapia = os.path.join(os.path.dirname(__file__), 'assets', 'quantum.png')
        if os.path.exists(icon_path_terapia):
            btn_terapia.setIcon(QIcon(icon_path_terapia))
            btn_terapia.setIconSize(QSize(72, 72))
        btn_terapia.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_terapia.setFixedSize(200, 200)
        btn_terapia.clicked.connect(self.open_terapia)
        
        # 🎨 Estilo personalizado para botão Terapia
        btn_terapia.setStyleSheet("""
            QToolButton {
                background-color: #f8f9fa;
                border: none;
                border-radius: 15px;
                color: #2c3e50;
                font-family: "Segoe UI", sans-serif;
                font-size: 16px;
                font-weight: 600;
            }
            QToolButton:hover {
                background-color: #e4ffe1;
            }
            QToolButton:pressed {
                background-color: #c8e6c5;
            }
        """)
        
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
                    BiodeskMessageBox.critical(
                        self,
                        "Erro de Importação",
                        "Não foi possível carregar o módulo IrisAnonimaCanvas.\n\n"
                        "Verifique se o arquivo iris_anonima_canvas.py está presente e sem erros."
                    )
                    return
                self.iris_window = IrisAnonimaCanvas()
            else:
                if IrisCanvas is None:
                    BiodeskMessageBox.critical(
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
            BiodeskMessageBox.critical(
                self,
                "Erro ao Abrir Módulo de Íris",
                f"Ocorreu um erro ao tentar abrir o módulo de íris:\n\n{str(e)}\n\n"
                "Verifique os logs no console para mais detalhes."
            )

    def load_styles(self):
        """
        🔥 REVOLUÇÃO COMPLETA: BiodeskStyles v2.0 com QSS Global
        FORÇA todos os botões a ficarem bonitos SEM EXCEÇÃO!
        """
        try:
            if BiodeskStyles:
                # print("✅ Sistema BiodeskStyles v2.0 ativo - estilos centralizados")
                
                # 🔥 APLICAR QSS GLOBAL PARA FORÇAR TODOS OS BOTÕES
                BiodeskStyles.apply_global_qss()
                # print("✅ QSS global aplicado")
                
            else:
                print("⚠️ BiodeskStyles não disponível - problemas críticos!")
                    
        except Exception as e:
            print(f"❌ Erro ao carregar estilos: {e}")
        
        # ✅ Marcar que o sistema está ativo
        # print("✅ Sistema BiodeskStyles ativo - hotkeys obsoletos removidos")

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
            BiodeskMessageBox.critical(
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
            self.safe_maximize_window(self.todo_window)
        except Exception as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir lista de tarefas:\n\n{str(e)}"
            )
    
    def inicializar_sistema_emails(self):
        """Inicializar sistema de agendamento de emails"""
        try:
            if email_scheduler_disponivel:
                self.email_scheduler = get_email_scheduler()
                self.email_scheduler.iniciar()
                print("✅ Sistema de agendamento de emails iniciado")
            else:
                self.email_scheduler = None
                print("⚠️ Sistema de agendamento de emails não disponível")
        except Exception as e:
            print(f"❌ Erro ao inicializar sistema de emails: {e}")
            self.email_scheduler = None
    
    def abrir_gestao_emails_agendados(self):
        """Abrir janela de gestão de emails agendados"""
        try:
            if not email_scheduler_disponivel:
                BiodeskMessageBox.warning(
                    self,
                    "Sistema Indisponível",
                    "📧 Sistema de agendamento de emails não está disponível."
                )
                return
            
            from emails_agendados_manager import EmailsAgendadosWindow
            self.emails_window = EmailsAgendadosWindow(self)
            self.emails_window.show()
            
        except Exception as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir gestão de emails:\n\n{str(e)}"
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

            # Garantir que não saia da tela e evitar coordenadas negativas
            screen = QGuiApplication.primaryScreen()
            if screen:
                avail = screen.availableGeometry()
                # ⚠️ CORREÇÃO: Garantir coordenadas mínimas válidas
                x = max(avail.left() + 10, min(x, avail.right() - 10 - panel_size.width()))
                y = max(avail.top() + 30, min(y, avail.bottom() - 10 - panel_size.height()))
                
                # Verificação adicional para evitar valores negativos ou muito pequenos
                x = max(0, x)
                y = max(0, y)
                
                # Verificar se o tamanho é válido
                if panel_size.width() <= 0 or panel_size.height() <= 0:
                    print("⚠️ Tamanho de painel inválido detectado")
                    return

            self._patients_panel.move(QPoint(x, y))
            self._patients_panel.show()
            self._patients_panel.raise_()
            self._patients_panel.activateWindow()
        except Exception as e:
            pass  # Erro não crítico

    def open_terapia(self):
        """Abre módulo de terapia quântica com HS3"""
        try:
            # Verificar se FrequencyList.xls existe
            import os
            frequency_file = os.path.join(os.path.dirname(__file__), 'assets', 'FrequencyList.xls')
            if not os.path.exists(frequency_file):
                from PyQt6.QtWidgets import QFileDialog
                reply = BiodeskMessageBox.question(
                    self,
                    "FrequencyList.xls não encontrado",
                    f"O arquivo FrequencyList.xls não foi encontrado em:\n{frequency_file}\n\n"
                    "Deseja localizar o arquivo agora?"
                )
                
                if reply:
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
                        pass  # Arquivo não selecionado
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
            BiodeskMessageBox.critical(
                self,
                "Módulo Indisponível",
                f"Erro ao importar módulo de terapia:\n\n{str(e)}\n\n"
                "Verifique se todas as dependências estão instaladas:\n"
                "• pip install pandas openpyxl xlrd\n"
                "• pip install pyqtgraph\n"
                "• pip install numpy scipy"
            )
        except Exception as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir terapia quântica:\n\n{str(e)}\n\n"
                "Verifique o console para mais detalhes."
            )
    
    def show_maximized_safe(self):
        """Maximiza a janela respeitando a barra de tarefas do Windows - OTIMIZADO"""
        try:
            # ⚡ MÉTODO OTIMIZADO: Configuração única e direta
            screen = QGuiApplication.primaryScreen()
            if screen:
                # Usar availableGeometry para respeitar barra de tarefas
                available_rect = screen.availableGeometry()
                
                # Aplicar configurações de maximização em sequência otimizada
                self.setWindowState(Qt.WindowState.WindowNoState)  # Reset primeiro
                self.setGeometry(available_rect)
                self.setWindowState(Qt.WindowState.WindowMaximized)
                
                # Mostrar a janela
                self.show()
                
                # ⚡ ÚNICA verificação com delay mínimo
                QTimer.singleShot(100, self._verificar_maximizacao)
            else:
                # Fallback se não conseguir screen
                self.showMaximized()
                
        except Exception as e:
            pass  # Erro não crítico
            self.showMaximized()  # Fallback padrão
    
    def resizeEvent(self, event):
        """Intercepta eventos de resize para manter sempre maximizado"""
        # Garantir que a janela permanece sempre maximizada
        if self.windowState() != Qt.WindowState.WindowMaximized and self.windowState() != Qt.WindowState.WindowMinimized:
            QTimer.singleShot(0, self.showMaximized)
        super().resizeEvent(event)
    
    def changeEvent(self, event):
        """Intercepta mudanças de estado da janela"""
        if event.type() == event.Type.WindowStateChange:
            # Se não está maximizada nem minimizada, forçar maximização
            if self.windowState() == Qt.WindowState.WindowNoState:
                QTimer.singleShot(0, self.showMaximized)
        super().changeEvent(event)
    
    def _verificar_maximizacao(self):
        """Verificação única e final da maximização"""
        try:
            if not self.isMaximized():
                self.showMaximized()
                # Forçar repaint para evitar deformações
                self.repaint()
        except Exception:
            pass

    def safe_maximize_window(self, window):
        """Maximiza qualquer janela respeitando a barra de tarefas - OTIMIZADO"""
        try:
            # ⚡ CONFIGURAÇÃO DIRETA E OTIMIZADA
            screen = QGuiApplication.primaryScreen()
            if screen:
                available_rect = screen.availableGeometry()
                
                # Sequência otimizada para janelas filhas
                window.setWindowState(Qt.WindowState.WindowNoState)
                window.setGeometry(available_rect)
                window.setWindowState(Qt.WindowState.WindowMaximized)
                window.show()
                
                # ⚡ ÚNICA verificação necessária
                QTimer.singleShot(50, lambda: self._force_maximize_once(window))
            else:
                window.showMaximized()
                
        except Exception as e:
            pass  # Erro não crítico
            try:
                window.showMaximized()
            except:
                window.show()
    
    def _force_maximize_once(self, window):
        """Força maximização ÚNICA para evitar loops e deformações"""
        try:
            if hasattr(window, 'isMaximized') and hasattr(window, 'showMaximized'):
                if not window.isMaximized():
                    window.showMaximized()
                # Forçar repaint para layout correto
                if hasattr(window, 'repaint'):
                    window.repaint()
        except Exception:
            pass


class PatientsPanel(QDialog):
    from PyQt6.QtCore import pyqtSignal
    selectRequested = pyqtSignal()
    newRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ⚠️ CORREÇÃO: Configurações de janela com transparência ativada por padrão
        try:
            # Verificar se transparência deve ser desativada (agora padrão: ATIVADA)
            import os, sys
            disable_transparency = False  # PADRÃO: Ativar transparência
            if os.environ.get('BIODESK_DISABLE_TRANSPARENCY', 'false').lower() == 'true':
                disable_transparency = True
                print("🔧 Transparência desativada via variável de ambiente")
            
            # Usar configurações melhoradas (sem Popup para evitar problemas)
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
            
            # Ativar transparência com verificações de segurança
            if not disable_transparency:
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                print("✨ Transparência ativada com melhorias de segurança")
            else:
                print("🔧 Transparência desativada para evitar erros Windows")
                
        except Exception as e:
            print(f"⚠️ Erro ao configurar janela: {e}")
            # Fallback para janela normal
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # ✅ APLICAR ESTILO PROFISSIONAL se disponível
        if BiodeskStyles and DialogStyles:
            try:
                DialogStyles.apply_to_dialog(self)
            except Exception as e:
                print(f"⚠️ Erro ao aplicar DialogStyles: {e}")

        # Container principal com design pill (cilíndrico)
        container = QFrame()
        container.setObjectName("patientsPanel")
        
        # ⚠️ ESTILO: Otimizado para transparência
        base_style = """
            QFrame#patientsPanel {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(46,125,50,0.2);
                border-radius: 25px;
                min-width: 360px;
                max-width: 360px;
            }
            """
        
        try:
            container.setStyleSheet(base_style)
        except Exception as e:
            print(f"⚠️ Erro ao aplicar estilo do painel: {e}")
            # Fallback para estilo simples
            container.setStyleSheet("QFrame { background: white; border: 1px solid gray; border-radius: 10px; }")

        # Layout horizontal para os dois pills lado a lado com mais espaçamento
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Pill 1: Selecionar Paciente - usando BiodeskStyles
        if BiodeskStyles:
            btn_select = BiodeskStyles.create_button("🔍 Selecionar", ButtonType.NAVIGATION)
        else:
            btn_select = QPushButton("🔍\nSelecionar")

        # Pill 2: Novo Paciente - usando BiodeskStyles
        if BiodeskStyles:
            btn_new = BiodeskStyles.create_button("➕ Novo", ButtonType.SAVE)
        else:
            btn_new = QPushButton("➕\nNovo")
        
        # Conectar sinais
        btn_select.clicked.connect(self.selectRequested.emit)
        btn_new.clicked.connect(self.newRequested.emit)
        
        # Fechar painel após clique com pequeno delay para melhor UX
        btn_select.clicked.connect(lambda: self.close_with_delay())
        btn_new.clicked.connect(lambda: self.close_with_delay())

        layout.addWidget(btn_select)
        layout.addWidget(btn_new)

        # Sombra elegante para transparência
        try:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(20)  # Sombra suave
            shadow.setColor(QColor(46, 125, 50, 60))  # Verde suave Biodesk
            shadow.setOffset(0, 4)  # Sombra discreta
            container.setGraphicsEffect(shadow)
        except Exception as e:
            print(f"⚠️ Erro ao aplicar sombra: {e}")
            # Continuar sem sombra se houver problemas

        # Layout principal
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

        # ⚠️ CORREÇÃO: Verificar problemas de transparência no Windows
        self._check_transparency_issues()

    def _check_transparency_issues(self):
        """
        Verifica se há problemas com transparência e desativa se necessário
        """
        try:
            import sys
            if sys.platform == "win32":
                # Tentar uma operação de update para detectar problemas
                self.update()
                # Se chegou até aqui sem erro, transparência funciona
                return True
        except Exception as e:
            print(f"⚠️ Problema de transparência detectado, desativando: {e}")
            try:
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
                self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
                return False
            except:
                pass
        return True

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
