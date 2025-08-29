"""
Classe principal da Ficha do Paciente
Responsável apenas pela orquestração dos componentes
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence

# Import robusto do DBManager: tenta import relativo (quando executado como package)
# e faz fallback para import absoluto quando executado como script.
try:
    # Preferir import relativo quando o pacote é executado com -m
    from ..db_manager import DBManager  # type: ignore
except Exception:
    try:
        # Fallback para execução direta a partir da raiz do repositório
        from db_manager import DBManager
    except Exception:
        # Última tentativa: adicionar a pasta pai ao sys.path e reimportar
        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from db_manager import DBManager
try:
    # Import relativo quando usado como pacote
    from .core.tab_manager import TabManager
    from .core.state_manager import StateManager
    from .services.pdf_service import PDFService
    from .services.email_service import EmailService
    from .services.database_service import DatabaseService
except Exception:
    # Fallback para import absoluto quando executado como script
    from ficha_paciente.core.tab_manager import TabManager  # type: ignore
    from ficha_paciente.core.state_manager import StateManager  # type: ignore
    from ficha_paciente.services.pdf_service import PDFService  # type: ignore
    from ficha_paciente.services.email_service import EmailService  # type: ignore
    from ficha_paciente.services.database_service import DatabaseService  # type: ignore


class FichaPaciente(QMainWindow):
    """Janela principal da ficha do paciente - versão otimizada"""

    # Sinais
    dados_alterados = pyqtSignal(dict)
    ficha_guardada = pyqtSignal(int)

    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)

        # Dados essenciais
        self.paciente_data = paciente_data or {}
        self.db = DBManager.get_instance()

        # Gerenciadores
        self.state_manager = StateManager()
        self.tab_manager = TabManager(self)

        # Serviços
        self.pdf_service = PDFService()
        self.email_service = EmailService()
        self.database_service = DatabaseService(self.db)

        # Configuração inicial
        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()

        # Carregar dados se disponíveis
        if self.paciente_data:
            self.carregar_dados()

    def _setup_window(self):
        """Configura a janela principal"""
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

    def _get_window_title(self):
        """Retorna título da janela baseado no paciente"""
        nome = self.paciente_data.get('nome', 'Novo Paciente')
        return f"📋 Ficha do Paciente - {nome}"

    def _setup_ui(self):
        """Configura interface principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Sistema de tabs
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Adicionar tabs (serão carregadas sob demanda)
        self._add_tabs()

    def _add_tabs(self):
        """Adiciona as tabs principais"""
        tab_config = [
            ('👤 DADOS PESSOAIS', 'dados_pessoais'),
            ('🏥 HISTÓRICO', 'historico'),
            ('👁️ IRISDIAGNOSE', 'irisdiagnose'),
            ('📧 COMUNICAÇÃO', 'comunicacao')
        ]

        for label, key in tab_config:
            widget = QWidget()
            widget.setObjectName(key)
            self.tabs.addTab(widget, label)

    def _setup_shortcuts(self):
        """Configura atalhos de teclado"""
        shortcuts = {
            'Ctrl+S': self.guardar,
            'Ctrl+N': self.novo_paciente,
            'Ctrl+O': self.abrir_paciente,
            'Ctrl+P': self.imprimir,
            'F5': self.atualizar
        }

        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)

    def _on_tab_changed(self, index):
        """Carrega tab sob demanda quando selecionada"""
        if not self.state_manager.is_tab_loaded(index):
            self.tab_manager.load_tab(index, self.tabs.widget(index), self.paciente_data)
            self.state_manager.mark_tab_loaded(index)

    # ========== MÉTODOS DE DADOS ==========

    def carregar_dados(self):
        """Carrega dados do paciente"""
        if not self.paciente_data:
            return

        self.setWindowTitle(self._get_window_title())

        # Notificar tabs carregadas
        self.tab_manager.update_all_tabs(self.paciente_data)

        # Resetar estado dirty
        self.state_manager.set_dirty(False)

    def guardar(self):
        """Guarda os dados do paciente"""
        if not self.state_manager.is_dirty():
            return

        # Coletar dados de todas as tabs
        dados = self.tab_manager.collect_all_data()
        dados['id'] = self.paciente_data.get('id')

        # Validar
        if not self._validar_dados(dados):
            return

        # Guardar na BD
        novo_id = self.database_service.save_patient(dados)

        if novo_id:
            self.paciente_data['id'] = novo_id
            self.paciente_data.update(dados)
            self.state_manager.set_dirty(False)
            self.ficha_guardada.emit(novo_id)
            self._mostrar_sucesso("Paciente guardado com sucesso!")
        else:
            self._mostrar_erro("Erro ao guardar paciente")

    def _validar_dados(self, dados):
        """Valida dados antes de guardar"""
        from .utils.validators import PatientValidator

        valido, erros = PatientValidator.validate(dados)
        if not valido:
            self._mostrar_erro("\n".join(erros))

        return valido

    # ========== MÉTODOS DE AÇÃO ==========

    def novo_paciente(self):
        """Cria novo paciente"""
        if self.state_manager.is_dirty():
            if not self._confirmar_acao("Existem alterações não guardadas. Continuar?"):
                return

        self.paciente_data = {}
        self.carregar_dados()

    def abrir_paciente(self):
        """Abre seletor de pacientes"""
        from .dialogs.patient_selector import PatientSelector

        dialog = PatientSelector(self)
        if dialog.exec():
            self.paciente_data = dialog.get_selected_patient()
            self.carregar_dados()

    def imprimir(self):
        """Imprime ficha atual"""
        tab_atual = self.tabs.currentIndex()
        self.tab_manager.print_current_tab(tab_atual)

    def atualizar(self):
        """Atualiza dados da tab atual"""
        tab_atual = self.tabs.currentIndex()
        self.tab_manager.refresh_tab(tab_atual)

    # ========== MÉTODOS AUXILIARES ==========

    def _mostrar_sucesso(self, mensagem):
        """Mostra mensagem de sucesso"""
        from .utils.dialogs import show_success
        show_success(self, mensagem)

    def _mostrar_erro(self, mensagem):
        """Mostra mensagem de erro"""
        from .utils.dialogs import show_error
        show_error(self, mensagem)

    def _confirmar_acao(self, mensagem):
        """Pede confirmação ao usuário"""
        from .utils.dialogs import confirm_action
        return confirm_action(self, mensagem)

    # ========== EVENTOS ==========

    def closeEvent(self, event):
        """Trata fechamento da janela"""
        if self.state_manager.is_dirty():
            if not self._confirmar_acao("Existem alterações não guardadas. Sair?"):
                event.ignore()
                return

        # Limpar recursos
        self.tab_manager.cleanup()
        event.accept()

    @staticmethod
    def mostrar_seletor(callback, parent=None):
        """
        Compatibilidade: interface estática usada pelo código legado.
        Encaminha para o gerenciador de pesquisa de pacientes.

        Uso: FichaPaciente.mostrar_seletor(callback=..., parent=...)
        """
        try:
            # Import local para evitar dependências circulares na importação do pacote
            from .pesquisa_pacientes import PesquisaPacientesManager
            PesquisaPacientesManager.mostrar_seletor(callback, parent)
        except Exception as e:
            # Em caso de erro, re-lançar para que o chamador trate/registre
            raise
