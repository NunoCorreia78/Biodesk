
# Imports essenciais para startup
from pathlib import Path

# PyQt6 - APENAS o básico para definir classes
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit, QPushButton, QScrollArea, QFrame, QApplication, QDialog, QListWidget, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QShortcut, QKeySequence

# ✅ SISTEMA NOVO: BiodeskStyles v2.0 - Estilos centralizados
try:
    from biodesk_styles import BiodeskStyles, DialogStyles, ButtonType
    BIODESK_STYLES_AVAILABLE = True
except ImportError as e:
    BIODESK_STYLES_AVAILABLE = False

# Imports essenciais para a classe principal
from db_manager import DBManager
from sistema_assinatura import abrir_dialogo_assinatura

# 🔧 SERVIÇOS MODULARES - Arquitetura refatorada
from ficha_paciente.services.pdf_service_simple import PDFService, get_pdf_service
from ficha_paciente.managers.consentimentos_manager import criar_consentimentos_manager
from ficha_paciente.services.email_service import EmailService
from ficha_paciente.services.template_service import TemplateService
from ficha_paciente.services.document_service import DocumentService

# LAZY IMPORTS para módulos especializados
_modulos_cache = {}

def importar_modulos_especializados():
    """Importa módulos especializados apenas quando necessário"""
    if not _modulos_cache:
        try:
            from ficha_paciente.dados_pessoais import DadosPessoaisWidget
            from ficha_paciente.historico_clinico import HistoricoClinicoWidget  
            from ficha_paciente.templates_manager import TemplatesManagerWidget
            from ficha_paciente.comunicacao_manager import ComunicacaoManagerWidget
            from ficha_paciente.gestao_documentos import GestaoDocumentosWidget
            from ficha_paciente.declaracao_saude import DeclaracaoSaudeWidget
            from ficha_paciente.pesquisa_pacientes import PesquisaPacientesManager
            from ficha_paciente.centro_comunicacao_unificado import CentroComunicacaoUnificado
            
            _modulos_cache.update({
                'dados_pessoais': DadosPessoaisWidget,
                'historico_clinico': HistoricoClinicoWidget,
                'templates_manager': TemplatesManagerWidget,
                'comunicacao_manager': ComunicacaoManagerWidget,
                'gestao_documentos': GestaoDocumentosWidget,
                'declaracao_saude': DeclaracaoSaudeWidget,
                'pesquisa_pacientes': PesquisaPacientesManager,
                'centro_comunicacao_unificado': CentroComunicacaoUnificado
            })
        except ImportError:
            pass
        
    return (_modulos_cache.get('dados_pessoais'), _modulos_cache.get('historico_clinico'), 
            _modulos_cache.get('templates_manager'), _modulos_cache.get('comunicacao_manager'),
            _modulos_cache.get('gestao_documentos'), _modulos_cache.get('declaracao_saude'),
            None, _modulos_cache.get('pesquisa_pacientes'))

class FichaPaciente(QMainWindow):
    def __init__(self, paciente_data=None, parent=None):
        # Inicialização mínima
        super().__init__(parent)
        
        # APENAS o essencial durante __init__
        # ✅ USAR DADOS FORNECIDOS OU CRIAR FICHA VAZIA
        self.paciente_data = paciente_data or {}
        self.dirty = False
        
        # Usar singleton do DBManager
        self.db = DBManager.get_instance()
        
        # Flags de controle para lazy loading
        self._pdf_viewer_initialized = False
        self._webengine_available = None
        self._initialized = False
        
        # 🚀 CARREGAMENTO IMEDIATO: Carregar dados pessoais na inicialização
        self._tabs_loaded = {
            'dados_pessoais': False,  # Será carregado imediatamente
            'historico': False,
            'irisdiagnose': False,
            'centro_comunicacao': False
        }
        
        # Prevenção de carregamentos múltiplos simultâneos
        self._loading_locks = set()
        
        # Flag para indicar que está carregando dados iniciais
        self._carregando_dados = False
        
        # ANTI-FLICKERING: Remover chamada para _init_delayed
        # A UI será construída diretamente no __init__ de forma otimizada
        
        # ✅ CONSTRUÇÃO SIMPLES E DIRETA DA UI
        self._ultima_zona_hover = None
        
        # Configurar geometria adequada
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Configurar atualização automática dos dados (otimizada)
        self.setup_data_refresh()
        
        # Sistema modular de assinaturas
        # Armazenar assinaturas capturadas por tipo de consentimento
        self.assinaturas_por_tipo = {}  # {'rgpd': {'paciente': bytes, 'terapeuta': bytes}, ...}
        self.assinatura_paciente_data = None
        self.assinatura_terapeuta_data = None
        
        # 🔧 INICIALIZAR SERVIÇOS MODULARES
        self._init_services()
        
        # Adicionar debounce para prevenção de cliques múltiplos
        self._ultimo_clique_data = 0
        
        # ✨ CONSTRUIR UI DIRETAMENTE - SEM COMPLICAÇÕES
        self.init_ui()
        self.load_data()
        
        # 📊 FINALIZAR INICIALIZAÇÃO COM MONITORAMENTO
        self._finalize_startup()
        
    def load_data(self):
        """Carrega dados do paciente de forma otimizada"""
        if not self.paciente_data:
            return
        
        # Marcar que está carregando dados para evitar dirty flags
        self._carregando_dados = True
        
        try:
            # Configurar título da janela
            nome = self.paciente_data.get('nome', 'Novo Paciente')
            self.setWindowTitle(f"📋 Ficha do Paciente - {nome}")
            
            # 🔄 CARREGAR DADOS NOS WIDGETS JÁ INICIALIZADOS
            self._atualizar_widgets_com_dados()
            
        except Exception as e:
            pass
        finally:
            # Limpar flag de carregamento
            self._carregando_dados = False

    def _init_services(self):
        """Inicializa serviços modulares com lazy loading"""
        self._pdf_service = None
        self._email_service = None
        self._template_service = None
        self._document_service = None

    def _get_pdf_service(self):
        """Obtém instância do PDFService (lazy loading)"""
        if self._pdf_service is None:
            self._pdf_service = get_pdf_service()
        return self._pdf_service

    def _get_email_service(self):
        """Obtém instância do EmailService (lazy loading)"""
        if self._email_service is None:
            self._email_service = EmailService()
        return self._email_service

    def _get_template_service(self):
        """Obtém instância do TemplateService (lazy loading)"""
        if self._template_service is None:
            self._template_service = TemplateService()
        return self._template_service

    def _get_document_service(self):
        """Obtém instância do DocumentService (lazy loading)"""
        if self._document_service is None:
            self._document_service = DocumentService(self.paciente_data)
        return self._document_service
    
    def _atualizar_widgets_com_dados(self):
        """Atualiza widgets já inicializados com os novos dados do paciente"""
        try:
            # Atualizar dados pessoais se já carregado
            if hasattr(self, 'dados_pessoais_widget') and self.dados_pessoais_widget:
                if hasattr(self.dados_pessoais_widget, 'set_paciente_data'):
                    self.dados_pessoais_widget.set_paciente_data(self.paciente_data)
                elif hasattr(self.dados_pessoais_widget, 'carregar_dados_paciente'):
                    self.dados_pessoais_widget.carregar_dados_paciente(self.paciente_data)
            
            # Atualizar histórico clínico se já carregado
            if hasattr(self, 'historico_widget') and self.historico_widget:
                historico_texto = self.paciente_data.get('historico', '')
                self.historico_widget.set_historico_texto(historico_texto)
            
            # Atualizar outros widgets conforme necessário
            if hasattr(self, 'declaracao_widget') and self.declaracao_widget:
                self.declaracao_widget.carregar_dados(self.paciente_data)
                
            if hasattr(self, 'gestao_documentos_widget') and self.gestao_documentos_widget:
                self.gestao_documentos_widget.atualizar_paciente(self.paciente_data)
                
            print("🔄 Widgets atualizados com novos dados do paciente")
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar widgets: {e}")
    
    def _finalize_startup(self):
        """Finaliza a inicialização com monitoramento de performance"""
        import time
        
        # Marcar inicialização como completa
        self._initialized = True
        
    # ====== CALLBACKS PARA MÓDULOS ESPECIALIZADOS ======
    def on_template_selecionado(self, template_data):
        """Callback quando template é selecionado no módulo especializado"""
        pass
    
    def on_followup_agendado(self, tipo_followup, dias):
        """Callback quando follow-up é agendado no módulo de comunicação"""
        pass
    
    def on_protocolo_adicionado(self, protocolo):
        """Callback quando protocolo é adicionado no módulo de templates"""
        pass
    
    def on_template_gerado(self, template_data):
        """Callback quando template é gerado no módulo de templates"""
        pass
    
    def data_atual(self):
        """MÉTODO REFATORADO - usa DateUtils"""
        from ficha_paciente.utils import DateUtils
        return DateUtils.data_atual()
    
    def selecionar_imagem_galeria(self, img):
        """Seleciona a imagem da galeria visual, atualiza canvas e aplica destaque visual"""
        if not img:
            return
        # Atualizar canvas com verificação de segurança
        if hasattr(self, 'iris_canvas') and self.iris_canvas is not None:
            caminho = img.get('caminho_imagem', '') or img.get('caminho', '')
            tipo = img.get('tipo', None)
            try:
                self.iris_canvas.set_image(caminho, tipo)
            except Exception as e:
                print(f"⚠️ Erro ao carregar imagem na iris: {e}")
                # Não fazer crash - continuar execução
        # Guardar seleção
        self.imagem_iris_selecionada = img
        # Atualizar destaque visual das miniaturas
        if hasattr(self, '_miniaturas_iris'):
            selecionado_id = img.get('id')
            for mid, frame in self._miniaturas_iris.items():
                if not frame:
                    continue
                if mid == selecionado_id:
                    frame.setProperty('selecionado', True)
                    frame.setStyleSheet(frame.property('style_base_selecionado'))
                else:
                    frame.setProperty('selecionado', False)
                    frame.setStyleSheet(frame.property('style_base_normal'))

    # Função removida - usar apenas a versão otimizada abaixo

    def setup_data_refresh(self):
        """Configura sistema de atualização automática de dados (otimizada)"""
        try:
            # Sistema de refresh sob demanda (mais eficiente que timer automático)
            # Timer automático desabilitado para melhor performance
            self.refresh_timer = None
            # Sistema de atualização sob demanda configurado
        except Exception as e:
            # Erro ao configurar atualização
            pass

    def refresh_patient_data(self):
        """Atualiza dados do paciente se necessário"""
        try:
            # Verificar se ainda temos referência ao paciente
            if not self.paciente_data or not self.paciente_data.get('id'):
                return
                
            # Recarregar dados do BD se disponível
            if hasattr(self, 'db') and self.db:
                paciente_id = self.paciente_data.get('id')
                dados_atualizados = self.db.obter_paciente(paciente_id)
                
                if dados_atualizados:
                    # Atualizar apenas se há mudanças significativas
                    campos_importantes = ['nome', 'email', 'contacto', 'peso', 'altura']
                    mudou = False
                    
                    for campo in campos_importantes:
                        if dados_atualizados.get(campo) != self.paciente_data.get(campo):
                            mudou = True
                            break
                    
                    if mudou:
                        self.paciente_data = dados_atualizados
                        self.update_ui_with_new_data()
                        
        except Exception as e:
            pass

    def update_ui_with_new_data(self):
        """Atualiza interface com novos dados do paciente"""
        try:
            # Atualizar email na aba de comunicação
            if hasattr(self, 'carregar_dados_paciente_email'):
                self.carregar_dados_paciente_email()
            
            # Atualizar dados na declaração de saúde
            if hasattr(self, 'declaracao_saude_widget') and self.declaracao_saude_widget:
                if hasattr(self.declaracao_saude_widget, 'set_paciente_data'):
                    self.declaracao_saude_widget.set_paciente_data(self.paciente_data)
            
            # Atualizar título da janela
            if self.paciente_data.get('nome'):
                self.setWindowTitle(f"📋 Ficha do Paciente - {self.paciente_data.get('nome')}")
            
        except Exception as e:
            pass
    
    def resetar_tabs_para_teste(self):
        """MÉTODO DE DESENVOLVIMENTO: Reseta flags para testar lazy loading"""
        if hasattr(self, '_development_mode') and self._development_mode:
            for key in self._tabs_loaded:
                if key not in ['dados_pessoais', 'dados_documentos']:
                    self._tabs_loaded[key] = False
            
            self._loading_locks.clear()
            print("🔄 Flags de lazy loading resetados para teste")
            return True
        return False
        
    def aplicar_estilo_global_hover(self):
        """Aplica estilo de hover globalmente em todos os botões"""
        # ✨ Hover global aplicado automaticamente pelo BiodeskStyleManager
        pass
        
    def _on_dados_tab_changed(self, index):
        """Carrega sub-tabs de dados & documentos sob demanda"""
        import time
        start_time = time.time()
        
        try:
            if index == 0 and not self._tabs_loaded.get('dados_pessoais', False):
                self.init_sub_dados_pessoais()
                self._tabs_loaded['dados_pessoais'] = True
                
            elif index == 1 and not self._tabs_loaded.get('declaracao_saude', False):
                self.init_sub_declaracao_saude_modular()
                self._tabs_loaded['declaracao_saude'] = True
                
        except Exception as e:
            pass  # Erro não crítico

    def init_ui(self):
        """Inicialização da interface principal"""
        # ✅ APLICAR ESTILO GLOBAL DE HOVER
        self.aplicar_estilo_global_hover()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ====== NOVA ESTRUTURA SIMPLIFICADA: 4 ABAS PRINCIPAIS ======
        self.tabs = QTabWidget()
        self.tab_dados_pessoais = QWidget()
        self.tab_historico = QWidget()
        self.tab_irisdiagnose = QWidget()
        self.tab_centro_comunicacao = QWidget()
        
        self.tabs.addTab(self.tab_dados_pessoais, '👤 DADOS PESSOAIS')
        self.tabs.addTab(self.tab_historico, '🏥 HISTÓRICO')
        self.tabs.addTab(self.tab_irisdiagnose, '👁️ IRISDIAGNOSE')
        self.tabs.addTab(self.tab_centro_comunicacao, '📧 CENTRO DE COMUNICAÇÃO')
        
        main_layout.addWidget(self.tabs)
        
        # Conectar sinal para lazy loading das outras abas
        self.tabs.currentChanged.connect(self._on_main_tab_changed)
        
        # 🚀 CARREGAMENTO IMEDIATO: Inicializar primeira aba imediatamente
        self.init_tab_dados_pessoais()
        self._tabs_loaded['dados_pessoais'] = True
        
        # 🚀 LAZY LOADING: Conectar sinal para carregar tabs principais sob demanda
        self.tabs.currentChanged.connect(self._on_main_tab_changed)
        
        # Atalho Ctrl+S
        shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut.activated.connect(self.guardar)
        
        # 🚀 LAZY LOADING: NÃO inicializar tabs principais - carregar o primeiro sob demanda
        # Carregar apenas o primeiro tab por padrão
        self._on_main_tab_changed(0)

    def _on_main_tab_changed(self, index):
        """Carrega tabs principais sob demanda com medição de performance"""
        import time
        start_time = time.time()
        
        # Prevenção de carregamentos múltiplos
        lock_key = f"main_tab_{index}"
        if lock_key in self._loading_locks:
            return
        
        try:
            self._loading_locks.add(lock_key)
            
            if index == 0 and not self._tabs_loaded.get('dados_pessoais', False):
                print("🔄 Carregando tab DADOS PESSOAIS...")
                self.init_tab_dados_pessoais()
                self._tabs_loaded['dados_pessoais'] = True
                
            elif index == 1 and not self._tabs_loaded.get('historico', False):
                print("🔄 [DEBUG LAZY] Carregando tab HISTÓRICO...")
                self.init_tab_historico()
                self._tabs_loaded['historico'] = True
                
            elif index == 2 and not self._tabs_loaded.get('irisdiagnose', False):
                self.init_tab_irisdiagnose()
                self._tabs_loaded['irisdiagnose'] = True
                
            elif index == 3 and not self._tabs_loaded.get('centro_comunicacao', False):
                self.init_tab_centro_comunicacao()
                self._tabs_loaded['centro_comunicacao'] = True
            
            load_time = time.time() - start_time
            if load_time > 0.1:  # Só reportar se demorar mais de 100ms
                print(f"⏱️ Tab principal carregado em {load_time:.2f}s")
                
        finally:
            self._loading_locks.discard(lock_key)

    def init_tab_dados_pessoais(self):
        """👤 DADOS PESSOAIS - Aba dedicada aos dados do paciente"""
        layout = QVBoxLayout(self.tab_dados_pessoais)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Usar lazy loading para Dados Pessoais Widget
        _, _, _, _, _, _, _, _ = importar_modulos_especializados()
        DadosPessoaisWidget = _modulos_cache.get('dados_pessoais')
        
        if DadosPessoaisWidget:
            self.dados_pessoais_widget = DadosPessoaisWidget(self.paciente_data, self)
            layout.addWidget(self.dados_pessoais_widget)
        else:
            placeholder = QLabel("⚠️ Módulo de dados pessoais não disponível")
            layout.addWidget(placeholder)

    def init_tab_historico(self):
        """🏥 HISTÓRICO - Histórico clínico com popups integrados"""
        layout = QVBoxLayout(self.tab_historico)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Cabeçalho com botões de ação
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("🏥 <b>Histórico Clínico</b>")
        title_label.setStyleSheet("font-size: 16px; color: #2c3e50; margin: 5px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botões de ação rápida
        btn_declaracao = QPushButton("📋 Declaração de Saúde")
        btn_prescricao = QPushButton("💊 Nova Prescrição")
        btn_protocolo = QPushButton("📋 Protocolos")
        
        if BIODESK_STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(btn_declaracao, ButtonType.DEFAULT)
            BiodeskStyles.apply_to_existing_button(btn_prescricao, ButtonType.SAVE)
            BiodeskStyles.apply_to_existing_button(btn_protocolo, ButtonType.DEFAULT)
        
        btn_declaracao.clicked.connect(self.abrir_declaracao_popup)
        btn_prescricao.clicked.connect(self.abrir_prescricao_popup)
        btn_protocolo.clicked.connect(self.abrir_protocolo_popup)
        
        header_layout.addWidget(btn_declaracao)
        header_layout.addWidget(btn_prescricao)
        header_layout.addWidget(btn_protocolo)
        
        layout.addWidget(header_frame)
        
        # Histórico clínico principal
        _, HistoricoClinicoWidget, _, _, _, _, _, _ = importar_modulos_especializados()
        
        if HistoricoClinicoWidget:
            # Extrair texto do histórico dos dados do paciente
            historico_texto = self.paciente_data.get('historico', '')
            if isinstance(historico_texto, dict):
                # Se for dict, tentar extrair texto ou usar string vazia
                historico_texto = historico_texto.get('texto', '') or historico_texto.get('historico', '') or ''
            elif not isinstance(historico_texto, str):
                # Se não for string nem dict, converter para string
                historico_texto = str(historico_texto) if historico_texto else ''
            
            print(f"🔍 [DEBUG HISTÓRICO] Criando widget com {len(historico_texto)} chars")
            self.historico_widget = HistoricoClinicoWidget(historico_texto, self)
            
            # ✅ CONECTAR SINAIS AQUI TAMBÉM
            self.historico_widget.historico_alterado.connect(self.on_historico_alterado)
            self.historico_widget.guardar_solicitado.connect(self.guardar)
            print(f"🔍 [DEBUG HISTÓRICO] Sinais conectados")
            
            layout.addWidget(self.historico_widget)
            print(f"🔍 [DEBUG HISTÓRICO] Widget criado e adicionado ao layout")
        else:
            placeholder = QLabel("⚠️ Módulo de histórico clínico não disponível")
            layout.addWidget(placeholder)
        
        print("✅ Histórico clínico carregado com popups integrados")

    def init_tab_irisdiagnose(self):
        """👁️ IRISDIAGNOSE - Análise de íris completa"""
        # Carregar módulo de íris automaticamente
        self.carregar_modulo_iris_completo()
    
    def carregar_modulo_iris_completo(self):
        """Carrega módulo completo de análise de íris"""
        try:
            print("🔄 Tentando importar módulo IrisIntegrationWidget...")
            # Importar módulo de íris
            from ficha_paciente.iris_integration import IrisIntegrationWidget
            print("✅ IrisIntegrationWidget importado com sucesso!")
            
            # Verificar se já existe layout
            layout = self.tab_irisdiagnose.layout()
            if layout:
                # Limpar layout existente
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                print("🧹 Layout existente limpo")
            else:
                # Criar novo layout apenas se não existir
                layout = QVBoxLayout(self.tab_irisdiagnose)
                layout.setContentsMargins(4, 4, 4, 4)
                layout.setSpacing(6)
                print("✅ Novo layout criado")
            
            print("🔄 Criando widget de íris integrado...")
            # Criar widget de íris integrado - PASSAR DADOS CORRETAMENTE
            self.iris_widget = IrisIntegrationWidget(self.paciente_data)
            print("✅ Widget de íris criado!")
            
            # Conectar sinais
            if hasattr(self.iris_widget, 'zona_clicada'):
                self.iris_widget.zona_clicada.connect(self.on_zona_iris_clicada)
                print("✅ Sinal zona_clicada conectado!")
            
            # ✅ CONECTAR SINAL DE EXPORTAÇÃO DE NOTAS PARA HISTÓRICO
            if hasattr(self.iris_widget, 'notas_exportadas'):
                self.iris_widget.notas_exportadas.connect(self.on_notas_iris_exportadas)
                print("✅ Sinal notas_exportadas conectado!")
            else:
                print("⚠️ Widget de íris não tem sinal notas_exportadas")
            
            layout.addWidget(self.iris_widget)
            print("✅ Widget adicionado ao layout!")
            
            print("✅ Módulo de íris completo carregado com sucesso!")
            
        except ImportError as e:
            print(f"❌ Erro ao importar módulo de íris: {e}")
            self.criar_placeholder_iris_simples()
        except Exception as e:
            print(f"❌ Erro geral ao carregar íris: {e}")
            import traceback
            print(traceback.format_exc())
            self.criar_placeholder_iris_simples()
    
    def criar_placeholder_iris_simples(self):
        """Cria placeholder simples quando módulo completo não está disponível"""
        layout = self.tab_irisdiagnose.layout()
        if not layout:
            layout = QVBoxLayout(self.tab_irisdiagnose)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
        
        # Cabeçalho
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("👁️ <b>Análise de Íris</b>")
        title_label.setStyleSheet("font-size: 16px; color: #2c3e50; margin: 5px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botão para tentar carregar novamente
        btn_carregar_iris = QPushButton("🔄 Tentar Carregar Novamente")
        if BIODESK_STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(btn_carregar_iris, ButtonType.DEFAULT)
        
        btn_carregar_iris.clicked.connect(self.carregar_modulo_iris_completo)
        header_layout.addWidget(btn_carregar_iris)
        
        layout.addWidget(header_frame)
        
        # Área de placeholder
        placeholder = QLabel("👁️ <b>Análise de Íris</b><br><br>"
                            "⚠️ Módulo completo não disponível<br>"
                            "🔄 Clique em 'Tentar Carregar Novamente' para recarregar<br>"
                            "💡 Verifique se o arquivo iris_integration.py está presente")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            font-size: 14px; 
            color: #666; 
            padding: 50px;
            background-color: #fff3cd;
            border: 2px dashed #ffc107;
            border-radius: 8px;
        """)
        layout.addWidget(placeholder)
    
    def on_zona_iris_clicada(self, zona):
        """Callback quando uma zona da íris é clicada"""
        print(f"🎯 Zona da íris clicada: {zona}")
        # Aqui pode adicionar lógica específica para zonas da íris
        print(f"✅ Processamento da zona {zona} concluído")
        
        print("✅ Irisdiagnose interface criada (carregamento sob demanda)")
    
    def init_tab_centro_comunicacao(self):
        """📧 CENTRO DE COMUNICAÇÃO - Email e documentos"""
        layout = QVBoxLayout(self.tab_centro_comunicacao)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Carregar Centro de Comunicação Unificado
        _, _, _, _, _, _, _, _ = importar_modulos_especializados()
        CentroComunicacaoUnificado = _modulos_cache.get('centro_comunicacao_unificado')
        
        if CentroComunicacaoUnificado:
            self.centro_comunicacao_widget = CentroComunicacaoUnificado(self.paciente_data, self)
            layout.addWidget(self.centro_comunicacao_widget)
        else:
            placeholder = QLabel("📧 <b>Centro de Comunicação</b><br><br>⚠️ Módulo não disponível")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("font-size: 14px; color: #666; padding: 50px;")
            layout.addWidget(placeholder)
        
        print("✅ Centro de Comunicação carregado")
    
    # ====== POPUPS INTEGRADOS NO HISTÓRICO ======
    def abrir_declaracao_popup(self):
        """Abrir declaração de saúde como popup"""
        try:
            _, _, _, _, _, DeclaracaoSaudeWidget, _, _ = importar_modulos_especializados()
            
            if DeclaracaoSaudeWidget:
                dialog = QDialog(self)
                dialog.setWindowTitle("📋 Declaração de Saúde")
                dialog.setModal(True)
                
                # Configurar para tela cheia
                from PyQt6.QtCore import Qt
                dialog.setWindowState(Qt.WindowState.WindowMaximized)
                dialog.resize(1920, 1080)  # Fallback para resolução comum
                
                layout = QVBoxLayout(dialog)
                declaracao_widget = DeclaracaoSaudeWidget(dialog)
                # Carregar dados do paciente na declaração - CORRIGIDO
                if hasattr(declaracao_widget, 'set_paciente_data'):
                    declaracao_widget.set_paciente_data(self.paciente_data)
                    print(f"✅ Dados do paciente carregados na declaração de saúde")
                elif hasattr(declaracao_widget, 'carregar_dados'):
                    declaracao_widget.carregar_dados(self.paciente_data)
                    print(f"✅ Dados do paciente carregados (método alternativo)")
                layout.addWidget(declaracao_widget)
                
                # Botões
                buttons_frame = QFrame()
                buttons_layout = QHBoxLayout(buttons_frame)
                
                btn_salvar = QPushButton("💾 Salvar")
                btn_fechar = QPushButton("❌ Fechar")
                
                if BIODESK_STYLES_AVAILABLE:
                    BiodeskStyles.apply_to_existing_button(btn_salvar, ButtonType.SAVE)
                    BiodeskStyles.apply_to_existing_button(btn_fechar, ButtonType.DEFAULT)
                
                buttons_layout.addStretch()
                buttons_layout.addWidget(btn_salvar)
                buttons_layout.addWidget(btn_fechar)
                
                layout.addWidget(buttons_frame)
                
                btn_fechar.clicked.connect(dialog.reject)
                btn_salvar.clicked.connect(lambda: self.salvar_declaracao(declaracao_widget, dialog))
                
                dialog.exec()
            else:
                QMessageBox.warning(self, "Aviso", "Módulo de declaração de saúde não disponível")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir declaração: {str(e)}")
    
    def abrir_prescricao_popup(self):
        """Abrir prescrição médica como popup"""
        try:
            from prescricao_medica_widget import PrescricaoMedicaWidget
            
            dialog = QDialog(self)
            dialog.setWindowTitle("💊 Nova Prescrição Médica")
            dialog.setModal(True)
            
            # Configurar para maximizar como as outras janelas
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QScreen
            
            # Maximizar a janela para ocupar toda a tela disponível (excluindo barra de tarefas)
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            # Definir tamanho exato da área disponível da tela
            dialog.setGeometry(screen_geometry)
            
            # Garantir que a janela está no estado maximizado
            dialog.setWindowState(Qt.WindowState.WindowMaximized)
            
            # Layout otimizado
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(5, 5, 5, 5)  # Margens mínimas
            layout.setSpacing(3)
            
            prescricao_widget = PrescricaoMedicaWidget(parent=dialog, paciente_data=self.paciente_data)
            layout.addWidget(prescricao_widget, 1)  # stretch factor para ocupar todo espaço
            
            dialog.exec()
            
        except ImportError:
            QMessageBox.warning(self, "Aviso", "Módulo de prescrição médica não disponível")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir prescrição: {str(e)}")
    
    def abrir_protocolo_popup(self):
        """Abrir protocolos como popup"""
        try:
            from ficha_paciente.templates_manager import TemplatesManagerWidget
            
            dialog = QDialog(self)
            dialog.setWindowTitle("📋 Gestão de Protocolos")
            dialog.setModal(True)
            
            # Configurar para tela cheia
            from PyQt6.QtCore import Qt
            dialog.setWindowState(Qt.WindowState.WindowMaximized)
            dialog.resize(1920, 1080)  # Fallback para resolução comum
            
            layout = QVBoxLayout(dialog)
            
            # Cabeçalho
            header_label = QLabel("📋 <b>Protocolos Terapêuticos</b><br>"
                                 "<small>Gerencie e aplique protocolos de tratamento</small>")
            header_label.setStyleSheet("padding: 10px; background-color: #f0f8ff; border-radius: 5px; margin-bottom: 10px;")
            layout.addWidget(header_label)
            
            templates_widget = TemplatesManagerWidget(self.paciente_data, dialog)
            layout.addWidget(templates_widget)
            
            # Botões
            buttons_frame = QFrame()
            buttons_layout = QHBoxLayout(buttons_frame)
            
            btn_aplicar = QPushButton("✅ Aplicar ao Histórico")
            btn_fechar = QPushButton("❌ Fechar")
            
            if BIODESK_STYLES_AVAILABLE:
                BiodeskStyles.apply_to_existing_button(btn_aplicar, ButtonType.SAVE)
                BiodeskStyles.apply_to_existing_button(btn_fechar, ButtonType.DEFAULT)
            
            buttons_layout.addStretch()
            buttons_layout.addWidget(btn_aplicar)
            buttons_layout.addWidget(btn_fechar)
            
            layout.addWidget(buttons_frame)
            
            btn_fechar.clicked.connect(dialog.reject)
            btn_aplicar.clicked.connect(lambda: self.aplicar_protocolo_historico(templates_widget, dialog))
            
            dialog.exec()
            
        except ImportError:
            QMessageBox.warning(self, "Aviso", "Módulo de protocolos não disponível")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir protocolos: {str(e)}")
    
    def salvar_declaracao(self, declaracao_widget, dialog):
        """Salvar declaração de saúde"""
        try:
            # Implementar lógica de salvamento
            QMessageBox.information(dialog, "Sucesso", "Declaração de saúde salva com sucesso!")
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(dialog, "Erro", f"Erro ao salvar declaração: {str(e)}")
    
    def aplicar_protocolo_historico(self, templates_widget, dialog):
        """Aplicar protocolos selecionados ao histórico"""
        try:
            protocolos = templates_widget.obter_protocolos_selecionados()
            if protocolos and hasattr(self, 'historico_widget'):
                # Adicionar protocolos ao histórico
                texto_protocolos = "PROTOCOLOS APLICADOS:\n" + "\n".join([f"- {p}" for p in protocolos])
                if hasattr(self.historico_widget, 'adicionar_entrada'):
                    self.historico_widget.adicionar_entrada(texto_protocolos)
                
                QMessageBox.information(dialog, "Sucesso", f"{len(protocolos)} protocolo(s) aplicado(s) ao histórico!")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Aviso", "Nenhum protocolo selecionado ou histórico não disponível")
        except Exception as e:
            QMessageBox.critical(dialog, "Erro", f"Erro ao aplicar protocolos: {str(e)}")
        """
        📋 DOCUMENTAÇÃO CLÍNICA
        - Dados Pessoais
        - Declaração de Saúde (com consentimentos integrados)
        - Gestão de Documentos
        """
        main_layout = QVBoxLayout(self.tab_dados_documentos)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ====== SUB-ABAS DENTRO DE DADOS & DOCUMENTOS ======
        self.dados_documentos_tabs = QTabWidget()
        self.dados_documentos_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.dados_documentos_tabs.setProperty('cssClass', 'tab-container')  # Usar estilo centralizado
        
        # Sub-abas
        self.sub_dados_pessoais = QWidget()
        self.sub_declaracao_saude = QWidget()
        
        self.dados_documentos_tabs.addTab(self.sub_dados_pessoais, '👤 Dados Pessoais')
        self.dados_documentos_tabs.addTab(self.sub_declaracao_saude, '🩺 Declaração de Saúde')
        
        # 🚀 CARREGAMENTO IMEDIATO: Conectar sinal para carregar sub-tabs sob demanda  
        self.dados_documentos_tabs.currentChanged.connect(self._on_dados_tab_changed)
        
        main_layout.addWidget(self.dados_documentos_tabs)
        
        # 🚀 CARREGAMENTO IMEDIATO: Carregar dados pessoais na inicialização
        self.init_sub_dados_pessoais()
        self._tabs_loaded['dados_pessoais'] = True

    def init_sub_dados_pessoais(self):
        """Sub-aba: Dados Pessoais - MÓDULO OTIMIZADO"""
        try:
            # ✅ USAR MÓDULO OTIMIZADO DE DADOS PESSOAIS via lazy loading
            DadosPessoaisWidget, _, _, _, _, _, _, _ = importar_modulos_especializados()
            
            layout = QVBoxLayout(self.sub_dados_pessoais)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Criar widget modular
            self.dados_pessoais_widget = DadosPessoaisWidget(
                self.paciente_data, 
                self,  # parent 
                self   # ficha_paciente (referência direta)
            )
            
            # Conectar sinais para sincronização
            self.dados_pessoais_widget.dados_alterados.connect(self.on_dados_pessoais_alterados)
            self.dados_pessoais_widget.validacao_alterada.connect(self.on_validacao_dados_pessoais)
            
            layout.addWidget(self.dados_pessoais_widget)
            
            # print("✅ Módulo de dados pessoais carregado com sucesso")
            
        except ImportError as e:
            print(f"❌ ERRO CRÍTICO: Módulo dados_pessoais não encontrado: {e}")
            # SEM FALLBACK - deve funcionar sempre
    
    def on_dados_pessoais_alterados(self, dados):
        """Callback quando dados pessoais são alterados PELO USUÁRIO"""
        # CORREÇÃO: Só marcar como dirty se não estiver carregando dados iniciais
        if not getattr(self, '_carregando_dados', False) and dados:
            # Atualizar dados do paciente
            self.paciente_data.update(dados)
            self.dirty = True
            
            # Atualizar título da janela se nome mudou
            if 'nome' in dados and dados['nome']:
                self.setWindowTitle(f"📋 Ficha do Paciente - {dados['nome']}")
    
    def on_validacao_dados_pessoais(self, valido):
        """Callback quando validação dos dados pessoais muda"""
        # Pode ser usado para ativar/desativar botões de guardar
        pass

    def init_sub_historico_clinico(self):
        """OBSOLETO: Redirecionado para sistema principal"""
        # O sistema principal usa init_tab_historico() que é o correto
        print("� [AVISO] init_sub_historico_clinico é OBSOLETO - sistema principal ativo")
        
        # O widget correto já foi criado pelo sistema principal
        if hasattr(self, 'historico_widget') and self.historico_widget is not None:
            print("🔍 [DEBUG SUB-HISTÓRICO] Widget principal já existe - ignorando")
            return
            
        # Se chegou aqui, algo está errado - usar sistema principal
        print("� [ERRO] Widget não existe - chamando sistema principal")
        self.init_tab_historico()
    
    def on_historico_alterado(self, novo_historico):
        """Callback quando histórico é alterado PELO USUÁRIO"""
        print(f"🔍 [DEBUG HISTÓRICO] Callback alteração: {len(novo_historico)} chars, carregando={getattr(self, '_carregando_dados', False)}")
        # CORREÇÃO: Só marcar como dirty se não estiver carregando dados iniciais
        if not getattr(self, '_carregando_dados', False) and hasattr(self, 'paciente_data') and self.paciente_data:
            # Atualizar usando a coluna correta da base de dados
            self.paciente_data['historico'] = novo_historico
            # Marcar como alterado
            self.dirty = True
            print(f"🔍 [DEBUG HISTÓRICO] Marcado como dirty - dados atualizados")
    
    def init_sub_templates_prescricoes(self):
        """Sub-aba: Templates & Prescrições - Usando módulo especializado"""
        try:
            # Usar lazy loading para Templates Manager
            _, _, TemplatesManagerWidget, _, _, _, _, _ = importar_modulos_especializados()
            
            # Criar widget especializado
            self.templates_widget = TemplatesManagerWidget(self.paciente_data, self)
            
            # Layout simples para integração
            layout = QVBoxLayout(self.sub_templates_prescricoes)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.templates_widget)
            
            # Conectar sinais
            self.templates_widget.template_selecionado.connect(self.on_template_selecionado)
            self.templates_widget.protocolo_adicionado.connect(self.on_protocolo_adicionado)
            self.templates_widget.template_gerado.connect(self.on_template_gerado)
            
            # Aplicação de estilos personalizada será feita pelos próprios widgets
            
            print("✅ Templates Manager carregado com sucesso")
            
        except ImportError as e:
            print(f"❌ ERRO CRÍTICO: Templates Manager não encontrado: {e}")
            # SEM FALLBACK - deve funcionar sempre
        except Exception as e:
            print(f"❌ ERRO no Templates Manager: {e}")
            # SEM FALLBACK - deve funcionar sempre
    
    def init_sub_centro_comunicacao(self):
        """Sub-aba: Email - Usando módulo especializado"""
        try:
            # Usar lazy loading para Comunicação Manager
            _, _, _, ComunicacaoManagerWidget, _, _, _, _ = importar_modulos_especializados()
            
            # Criar widget especializado
            self.comunicacao_widget = ComunicacaoManagerWidget(self.paciente_data, self)
            
            # Layout simples para integração
            layout = QVBoxLayout(self.sub_centro_comunicacao)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.comunicacao_widget)
            
            # Conectar sinais
            self.comunicacao_widget.email_enviado.connect(self.on_email_enviado)
            self.comunicacao_widget.followup_agendado.connect(self.on_followup_agendado)
            self.comunicacao_widget.template_aplicado.connect(self.on_template_aplicado)
            
            # Aplicação de estilos personalizada será feita pelos próprios widgets
            
            print("✅ Comunicação Manager carregado com sucesso")
            
        except ImportError as e:
            print(f"❌ ERRO CRÍTICO: Comunicação Manager não encontrado: {e}")
            # SEM FALLBACK - deve funcionar sempre
        except Exception as e:
            print(f"❌ ERRO no Comunicação Manager: {e}")
            # SEM FALLBACK - deve funcionar sempre
    
    def on_email_enviado(self, destinatario, assunto, corpo):
        """Callback quando email é enviado"""
        print(f"📤 Email enviado para: {destinatario}")
        # Aqui pode registrar no histórico, etc.
    
    def on_template_aplicado(self, nome_template):
        """Callback quando template é aplicado"""
        print(f"📄 Template aplicado: {nome_template}")

    def init_sub_iris_analise(self):
        """Sub-aba: Análise de Íris - Carregamento otimizado"""
        try:
            # Lazy import para módulos de íris
            print("🔄 Carregando módulo de análise de íris...")
            from iris_canvas import IrisCanvas
            from iris_overlay_manager import IrisOverlayManager
            
            layout = QVBoxLayout(self.sub_iris_analise)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            
            # Título da seção
            titulo_iris = QLabel("👁️ Análise Iridológica")
            titulo_iris.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 10px;
                    background-color: #ecf0f1;
                    border-radius: 8px;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(titulo_iris)
            
            # ✅ CORREÇÃO CRÍTICA: Canvas de íris com verificação de QApplication
            try:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app is not None:
                    self.iris_canvas = IrisCanvas(self)
                    layout.addWidget(self.iris_canvas)
                    
                    # Manager de overlays
                    self.iris_overlay_manager = IrisOverlayManager(self.iris_canvas.scene)
                    print("✅ Módulo de análise de íris carregado com segurança")
                else:
                    print("⚠️ QApplication não disponível - iris será carregada posteriormente")
                    # Placeholder temporário
                    placeholder = QLabel("👁️ Carregando módulo de íris...")
                    placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    placeholder.setStyleSheet("color: #6c757d; font-size: 14px; padding: 50px;")
                    layout.addWidget(placeholder)
                    self.iris_canvas = None
                    self.iris_overlay_manager = None
                    
            except Exception as iris_error:
                print(f"❌ Erro protegido na criação da iris: {iris_error}")
                # Fallback seguro
                placeholder = QLabel("⚠️ Módulo de íris temporariamente indisponível")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setStyleSheet("color: #dc3545; font-size: 14px; padding: 50px;")
                layout.addWidget(placeholder)
                self.iris_canvas = None
                self.iris_overlay_manager = None
            
        except ImportError as e:
            print(f"⚠️ Módulo de íris não encontrado: {e}")
            # Fallback simples
            layout = QVBoxLayout(self.sub_iris_analise)
            placeholder = QLabel("👁️ Módulo de Íris será carregado em breve...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #6c757d; font-size: 14px; padding: 50px;")
            layout.addWidget(placeholder)
        except Exception as e:
            print(f"❌ Erro ao carregar análise de íris: {e}")

    def init_sub_centro_comunicacao_fallback(self):
        """Sub-aba: Email - Interface limpa sem barras"""
        layout = QVBoxLayout(self.sub_centro_comunicacao)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Campo Para + Botões na mesma linha - EXATAMENTE como na imagem
        para_layout = QHBoxLayout()
        para_layout.setSpacing(15)
        
        lbl_para = QLabel("Para:")
        lbl_para.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        lbl_para.setFixedWidth(80)
        para_layout.addWidget(lbl_para)
        
        self.destinatario_edit = QLineEdit()
        self.destinatario_edit.setPlaceholderText("email@exemplo.com")
        self.destinatario_edit.setFixedHeight(45)
        self.destinatario_edit.setMinimumWidth(500)  # Aumentado de 400 para 500
        self.destinatario_edit.setMaximumWidth(600)  # Mais espaço ainda
        self.destinatario_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        para_layout.addWidget(self.destinatario_edit)
        
        # ✅ BOTÕES NA LINHA "PARA" - USANDO BUTTON MANAGER CENTRALIZADO
        from ficha_paciente.core.button_manager import ButtonManager
        
        btn_followup = ButtonManager.followup_button(self, self.schedule_followup_consulta)
        btn_followup.setFixedHeight(45)
        btn_followup.setFixedWidth(120)  # TAMANHO UNIFICADO
        para_layout.addWidget(btn_followup)
        
        btn_template = ButtonManager.template_button(self, self.abrir_templates_mensagem)
        btn_template.setFixedHeight(45)
        btn_template.setFixedWidth(120)  # TAMANHO UNIFICADO
        para_layout.addWidget(btn_template)
        
        btn_listar_followups = ButtonManager.lista_followups_button(self, self.listar_followups_agendados)
        btn_listar_followups.setFixedHeight(45)
        btn_listar_followups.setFixedWidth(120)  # TAMANHO UNIFICADO
        para_layout.addWidget(btn_listar_followups)
        
        para_layout.addStretch()  # Empurra tudo para a esquerda
        layout.addLayout(para_layout)
        
        # Campo Assunto - Layout horizontal com BOTÃO ENVIAR CENTRADO
        assunto_layout = QHBoxLayout()
        assunto_layout.setSpacing(15)
        
        lbl_assunto = QLabel("Assunto:")
        lbl_assunto.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        lbl_assunto.setFixedWidth(80)
        assunto_layout.addWidget(lbl_assunto)
        
        self.assunto_edit = QLineEdit()
        self.assunto_edit.setPlaceholderText("Assunto do email")
        self.assunto_edit.setFixedHeight(45)
        self.assunto_edit.setMinimumWidth(500)  # MESMO TAMANHO que o campo "Para"
        self.assunto_edit.setMaximumWidth(600)  # MESMO TAMANHO que o campo "Para"
        self.assunto_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        assunto_layout.addWidget(self.assunto_edit)
        
        # BOTÃO ENVIAR - USANDO BUTTON MANAGER CENTRALIZADO
        btn_enviar_email = ButtonManager.email_button(self, self.enviar_mensagem)
        btn_enviar_email.setFixedHeight(45)
        btn_enviar_email.setFixedWidth(390)  # LARGURA AUMENTADA para 390px
        assunto_layout.addWidget(btn_enviar_email)
        
        assunto_layout.addStretch()  # Empurra tudo para a esquerda
        layout.addLayout(assunto_layout)
        
        # ✅ SEÇÃO DE ANEXOS - Sempre presente no lado direito, alinhada com campo de texto
        self.anexos_frame = QFrame()
        self.anexos_frame.setFixedWidth(250)  # Largura adequada para coluna direita
        self.anexos_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 0px;
            }
        """)
        
        anexos_layout = QVBoxLayout(self.anexos_frame)
        anexos_layout.setContentsMargins(15, 10, 15, 10)
        
        # Título da seção melhorado
        lbl_anexos = QLabel("📎 Anexos:")
        lbl_anexos.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057; margin-bottom: 8px;")
        anexos_layout.addWidget(lbl_anexos)
        
        # Lista de anexos com altura adequada
        self.lista_anexos = QListWidget()
        self.lista_anexos.setMinimumHeight(80)
        self.lista_anexos.setMaximumHeight(120)  # Altura controlada
        self.lista_anexos.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            QListWidgetItem {
                padding: 4px 6px;
                border-bottom: 1px solid #f8f9fa;
                color: #495057;
                border-radius: 3px;
                margin: 1px 0px;
            }
            QListWidgetItem:hover {
                background-color: #f8f9fa;
            }
        """)
        anexos_layout.addWidget(self.lista_anexos)
        
        # Texto informativo quando não há anexos
        info_anexos = QLabel("📎 Nenhum anexo selecionado\n💡 Protocolos aparecerão aqui automaticamente")
        info_anexos.setStyleSheet("font-size: 11px; color: #6c757d; font-style: italic; margin-top: 5px; text-align: center;")
        info_anexos.setWordWrap(True)
        info_anexos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        anexos_layout.addWidget(info_anexos)

        # Campo Mensagem + Anexos - Layout horizontal EXATO da imagem
        conteudo_layout = QHBoxLayout()
        conteudo_layout.setSpacing(15)
        
        # Coluna esquerda: Mensagem (ocupa mais espaço)
        mensagem_layout = QVBoxLayout()
        
        lbl_msg = QLabel("Mensagem:")
        lbl_msg.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 5px; margin-top: 15px;")
        mensagem_layout.addWidget(lbl_msg)
        
        self.mensagem_edit = QTextEdit()
        self.mensagem_edit.setPlaceholderText("Digite aqui a sua mensagem...")
        self.mensagem_edit.setMinimumHeight(300)  # Altura como na imagem
        
        self.mensagem_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.mensagem_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mensagem_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.mensagem_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                background-color: white;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
            QTextEdit QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border: none;
                border-radius: 4px;
                margin: 0;
            }
            QTextEdit QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                min-height: 20px;
                margin: 2px;
            }
            QTextEdit QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.2);
            }
            QTextEdit QScrollBar::add-line:vertical,
            QTextEdit QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QTextEdit QScrollBar::add-page:vertical,
            QTextEdit QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        mensagem_layout.addWidget(self.mensagem_edit)
        
        # Coluna direita: Anexos alinhados EXATAMENTE com o campo de texto
        direita_layout = QVBoxLayout()
        
        # ✅ ESPAÇO PARA ALINHAR PERFEITAMENTE: Label "Mensagem:" + margens + início do campo
        # Calculado: font-size 14px + margin-top 15px + margin-bottom 5px + padding do campo ≈ 50px
        direita_layout.addSpacing(50)
        
        # Seção de anexos - SEMPRE PRESENTE mesmo sem anexos
        self.anexos_frame.show()
        direita_layout.addWidget(self.anexos_frame)
        
        # Adicionar stretch para empurrar tudo para cima
        direita_layout.addStretch()
        
        # Adicionar as duas colunas ao layout horizontal
        conteudo_layout.addLayout(mensagem_layout, 3)  # 3/4 do espaço para mensagem
        conteudo_layout.addLayout(direita_layout, 1)   # 1/4 do espaço para anexos
        
        # Layout principal
        layout.addLayout(conteudo_layout)
        
        # ✅ BOTÃO CONFIG EMAIL - Canto inferior direito da sub-aba
        config_inferior_layout = QHBoxLayout()
        config_inferior_layout.addStretch()  # Empurra para a direita
        
        btn_config_inferior = ButtonManager.config_button(self, self.abrir_configuracoes_comunicacao)
        btn_config_inferior.setFixedHeight(35)
        btn_config_inferior.setFixedWidth(85)
        config_inferior_layout.addWidget(btn_config_inferior)
        
        layout.addLayout(config_inferior_layout)
        
        # ✅ SEM BOTÕES EM BAIXO - Como pedido na imagem (já estão na linha do "Para:")
        
        # Adicionar stretch no final para empurrar conteúdo para cima
        layout.addStretch()

        # Configurar canal e carregar dados
        
        btn_enviar = ButtonManager.email_button(self, self.enviar_mensagem)
        btn_enviar.setFixedHeight(50)  # Ligeiramente maior para destaque
        btn_enviar.setFixedWidth(200)  # Ligeiramente maior
        # REMOVIDO: botoes_layout.addWidget(btn_enviar) - código duplicado
        
        # REMOVIDO: botoes_layout.addStretch() - código duplicado
        
        # Adicionar stretch no final para empurrar conteúdo para cima
        layout.addStretch()

        # Configurar canal e carregar dados
        self.canal_atual = "email"
        self.carregar_dados_paciente_email()
        
        # ✅ INICIALIZAR VISIBILIDADE DOS ANEXOS
        self.atualizar_visibilidade_anexos()

    def atualizar_visibilidade_anexos(self):
        """Mantém a seção de anexos sempre visível - como solicitado"""
        if hasattr(self, 'anexos_frame'):
            # ✅ SEMPRE PRESENTE - Campo de anexos sempre visível
            self.anexos_frame.show()

    def carregar_dados_paciente_email(self):
        """MÉTODO REFATORADO - usa EmailService"""
        from ficha_paciente.services import EmailService
        
        if self.paciente_data:
            # Usar EmailService para obter email formatado
            email_paciente = EmailService.formatar_destinatario(self.paciente_data) or ''
            
            if email_paciente:
                # Só preencher se o campo existir (módulo de comunicação carregado)
                if hasattr(self, 'destinatario_edit'):
                    self.destinatario_edit.setText(email_paciente)
                # Email do paciente carregado
            else:
                # Paciente não tem email configurado
                pass
            
            # Carregar nome para personalização - PROTEGER CONTRA None
            nome_raw = self.paciente_data.get('nome', 'Paciente')
            self.nome_paciente = nome_raw if nome_raw else 'Paciente'
            # Nome do paciente carregado
        else:
            self.nome_paciente = "Paciente"
            # Nenhum paciente carregado

    def atualizar_email_paciente_data(self):
        """MÉTODO REFATORADO - usa DataService"""
        from ficha_paciente.services import DataService
        
        novo_email = self.email_edit.text().strip()
        
        if hasattr(self, 'paciente_data') and self.paciente_data:
            # Usar DataService para atualizar dados
            self.paciente_data = DataService.atualizar_campo_paciente(
                self.paciente_data, 'email', novo_email
            )
            print(f"[EMAIL] 🔄 Email atualizado em tempo real: '{novo_email}'")
            
            # Atualizar campo de email no separador Email, se existir
            if hasattr(self, 'destinatario_edit'):
                self.destinatario_edit.setText(novo_email)
                print(f"[EMAIL] ✅ Campo de destinatário atualizado automaticamente")
        else:
            print(f"[EMAIL] ⚠️ paciente_data não disponível para atualização")

    def enviar_prescricao_pdf(self):
        """Cria e envia prescrição em PDF como anexo"""
        try:
            # Verificar se há dados do paciente carregados
            if not hasattr(self, 'paciente_data') or not self.paciente_data:
                from biodesk_styled_dialogs import BiodeskMessageBox
                BiodeskMessageBox.warning(self, "Aviso", "Selecione um paciente primeiro.")
                return
            
            # Verificar se há email configurado
            patient_email = self.paciente_data.get('email', '').strip()
            
            if not patient_email:
                from biodesk_styled_dialogs import BiodeskMessageBox
                BiodeskMessageBox.warning(self, "Aviso", "Paciente não tem email configurado.\n\nPor favor, adicione um email na ficha do paciente.")
                return
            
            # Obter dados da prescrição
            template_texto = self.template_preview.toPlainText()
            if not template_texto or "Selecione um template" in template_texto:
                from biodesk_styled_dialogs import BiodeskMessageBox
                BiodeskMessageBox.warning(self, "Aviso", "Selecione um template de prescrição primeiro.")
                return
            
            # Usar sistema PDF profissional
            try:
                from pdf_template_professional import BiodeskPDFTemplate
                import tempfile
                import os
                from datetime import datetime
                
                # Criar PDF com template profissional
                pdf_generator = BiodeskPDFTemplate(self.paciente_data)
                
                # Gerar PDF temporário
                temp_dir = tempfile.gettempdir()
                pdf_filename = f"prescricao_{self.paciente_data.get('nome', 'paciente').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)
                
                # Extrair conteúdo do template para prescrição
                nome_template = getattr(self, 'nome_template_atual', 'Template selecionado')
                categoria_template = getattr(self, 'categoria_template_atual', 'Prescrição')
                
                conteudo_prescricao = f"""
{categoria_template} - {nome_template}

{template_texto}

Orientações gerais:
• Seguir rigorosamente as indicações acima
• Manter acompanhamento conforme orientação
• Em caso de dúvidas, contactar a clínica
• Retorno conforme agendamento
                """.strip()
                
                # Gerar PDF profissional
                pdf_path = pdf_generator.gerar_prescricao(conteudo_prescricao, pdf_path)
                
                print(f"[PDF] ✅ PDF profissional gerado: {pdf_path}")
                
            except Exception as e:
                print(f"[PDF] ❌ Erro ao gerar PDF profissional: {e}")
                # Fallback para sistema anterior
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                import tempfile
                import os
                from datetime import datetime
                
                # Criar PDF temporário (sistema anterior como backup)
                temp_dir = tempfile.gettempdir()
                pdf_filename = f"prescricao_{self.paciente_data.get('nome', 'paciente').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)
                
                # Gerar PDF básico
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                
                # Cabeçalho
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "PRESCRIÇÃO MÉDICA")
                
                # Dados do paciente
                c.setFont("Helvetica", 12)
                y_pos = height - 100
                c.drawString(50, y_pos, f"Paciente: {self.paciente_data.get('nome', 'N/A')}")
                y_pos -= 20
                c.drawString(50, y_pos, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
                y_pos -= 40
                
                # Prescrição
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y_pos, "PRESCRIÇÃO:")
                y_pos -= 30
                
                c.setFont("Helvetica", 11)
                linhas_prescricao = template_texto.split('\n')
                for linha in linhas_prescricao[:10]:  # Limitar linhas
                    if linha.strip():
                        c.drawString(70, y_pos, f"• {linha[:70]}")
                        y_pos -= 20
                
                # Rodapé
                c.setFont("Helvetica", 10)
                c.drawString(50, 50, f"Documento gerado automaticamente pelo Biodesk - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
                c.save()
            
            # ✅ USAR NOVO SISTEMA DE EMAIL PERSONALIZADO
            try:
                from email_templates_biodesk import gerar_email_personalizado
                
                # Gerar email personalizado para prescrição
                nome_paciente = self.paciente_data.get('nome', 'Paciente')
                
                # Conteúdo específico para prescrição
                conteudo_prescricao = f"""Segue em anexo sua prescrição médica conforme análise realizada.

📋 Template aplicado: {nome_template}
📂 Categoria: {categoria_template}

Por favor, siga todas as orientações descritas no documento anexo.

Em caso de dúvidas sobre a prescrição, não hesite em contactar-me."""
                
                email_personalizado = gerar_email_personalizado(
                    nome_paciente=nome_paciente,
                    templates_anexados=[nome_template],
                    tipo_comunicacao="prescricao"
                )
                
                # Usar email personalizado
                assunto = email_personalizado['assunto']
                corpo = email_personalizado['corpo']
                
                print(f"[PDF] ✅ Email personalizado gerado para prescrição")
                
            except ImportError:
                # Fallback para email simples se sistema personalizado não disponível
                print(f"[PDF] ⚠️ Sistema personalizado não disponível, usando email padrão")
                
                assunto = f"Prescrição - {self.paciente_data.get('nome', 'Paciente')}"
                corpo = f"""Prezado(a) {self.paciente_data.get('nome', 'Paciente')},

Segue em anexo sua prescrição médica conforme análise realizada.

Por favor, siga todas as orientações descritas no documento.

Atenciosamente,
Equipe Médica"""
            
            # Preencher campos da interface
            self.destinatario_edit.setText(patient_email)
            self.assunto_edit.setText(assunto)
            self.mensagem_edit.setPlainText(corpo)
            
            # Criar sender de email
            from email_sender import EmailSender
            
            email_sender = EmailSender()
            
            # Enviar email com anexo
            sucesso, mensagem = email_sender.send_email_with_attachment(
                to_email=patient_email,
                subject=assunto,
                body=corpo,
                attachment_path=pdf_path,
                nome_destinatario=self.paciente_data.get('nome', 'Paciente')
            )
            
            if sucesso:
                from biodesk_styled_dialogs import BiodeskMessageBox
                BiodeskMessageBox.information(self, "Sucesso", "✅ Prescrição enviada com sucesso!\n\nO PDF profissional foi enviado para o email do paciente.")
                
                # Mostrar PDF gerado no visualizador integrado
                self.mostrar_pdf_gerado(pdf_path)
                
                # Limpar arquivo temporário após delay
                import threading
                def cleanup():
                    import time
                    time.sleep(10)  # Aguardar 10 segundos para visualização
                    try:
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                    except:
                        pass
                
                threading.Thread(target=cleanup, daemon=True).start()
            else:
                from biodesk_styled_dialogs import BiodeskMessageBox
                BiodeskMessageBox.critical(self, "Erro", f"❌ Erro ao enviar prescrição:\n\n{mensagem}")
                
        except ImportError:
            from biodesk_styled_dialogs import BiodeskMessageBox
            BiodeskMessageBox.warning(self, "Dependência", "📦 Biblioteca reportlab não encontrada.\n\n▶️ Instale com: pip install reportlab")
        except Exception as e:
            from biodesk_styled_dialogs import BiodeskMessageBox
            BiodeskMessageBox.critical(self, "Erro", f"❌ Erro inesperado ao enviar prescrição:\n\n{str(e)}")
            print(f"[ERRO] Erro ao enviar prescrição: {e}")

    def _lighten_color(self, hex_color, percent):
        """Clarifica uma cor hexadecimal - wrapper para services.styles"""
        from services.styles import lighten_color
        return lighten_color(hex_color, percent)
    
    def _darken_color(self, hex_color, percent):
        """Escurece uma cor hexadecimal - wrapper para services.styles"""
        from services.styles import darken_color
        return darken_color(hex_color, percent)

    def selecionar_canal(self, canal):
        """Método mantido para compatibilidade - email já está sempre selecionado"""
        self.canal_atual = "email"
        
        # Preencher automaticamente com dados do paciente
        if self.paciente_data and self.paciente_data.get('email'):
            self.destinatario_edit.setText(self.paciente_data['email'])

    def abrir_templates_mensagem(self):
        """Abre diálogo para selecionar template de mensagem com sistema personalizado"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, QPushButton, QLabel, QListWidgetItem, QMessageBox
            from PyQt6.QtCore import Qt
            from biodesk_styled_dialogs import BiodeskDialog
            
            # Obter nome do paciente
            nome_paciente = getattr(self, 'nome_paciente', self.paciente_data.get('nome', 'Paciente') if self.paciente_data else 'Paciente')
            
            # ✅ NOVOS TEMPLATES COM SISTEMA PERSONALIZADO
            templates_base = {
                "📧 Envio de Prescrição": f"Segue em anexo a sua prescrição médica personalizada conforme nossa consulta realizada.\n\nPor favor, siga rigorosamente as orientações descritas no documento.\n\nPara qualquer esclarecimento adicional, estou à inteira disposição.",
                
                "🔄 Consulta de Seguimento": f"Espero que esteja bem e seguindo as recomendações prescritas.\n\nGostaria de agendar uma consulta de seguimento para avaliar o seu progresso e ajustar o tratamento se necessário.\n\nAguardo o seu contacto para marcarmos a próxima consulta.",
                
                "📋 Resultados de Análise": f"Os resultados da sua análise iridológica já estão disponíveis.\n\nGostaria de agendar uma consulta para discutir detalhadamente os achados e definir o plano terapêutico mais adequado.\n\nFico à disposição para esclarecimentos.",
                
                "⏰ Lembrete de Consulta": f"Este é um lembrete da sua consulta marcada para [DATA] às [HORA].\n\nSolicitamos que chegue 10 minutos antes do horário agendado.\n\nCaso necessite remarcar, contacte-nos com antecedência.",
                
                "🙏 Agradecimento": f"Gostaria de expressar o meu sincero agradecimento pela confiança depositada nos nossos serviços de medicina integrativa.\n\nFoi um prazer acompanhá-lo/a no seu processo de bem-estar e saúde.\n\nEstamos sempre à disposição para futuros acompanhamentos.",
                
                "💌 Template Personalizado Completo": "EXEMPLO: Este template será automaticamente personalizado com saudação, redes sociais e assinatura profissional."
            }
            
            # Usar diálogo estilizado do Biodesk
            dialog = BiodeskDialog(self)
            dialog.setWindowTitle("📝 Templates de Email Personalizados")
            dialog.setFixedSize(1000, 800)  # AUMENTADO: era 900x700, agora 1000x800
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Título com informação sobre personalização
            titulo = QLabel("✨ Templates com Personalização Automática")
            titulo.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: 700;
                    color: #9C27B0;
                    padding: 15px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f8f9fa, stop:0.5 #E1BEE7, stop:1 #f8f9fa);
                    border: 2px solid #9C27B0;
                    border-radius: 10px;
                    margin-bottom: 10px;
                }
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Info sobre personalização automática
            info_label = QLabel("🔧 Cada template será automaticamente personalizado com:\n• Saudação baseada na hora\n• Nome do paciente\n• Redes sociais (Instagram/Facebook)\n• Assinatura profissional")
            info_label.setStyleSheet("""
                QLabel {
                    background-color: #d1ecf1;
                    color: #0c5460;
                    padding: 10px;
                    border-radius: 6px;
                    border: 1px solid #bee5eb;
                    font-size: 12px;
                }
            """)
            layout.addWidget(info_label)
            
            # Layout horizontal para lista e preview
            horizontal_layout = QHBoxLayout()
            
            # Lista de templates
            lista_frame = QLabel("📝 Templates Disponíveis:")
            lista_frame.setStyleSheet("font-weight: bold; color: #6c757d; margin-bottom: 5px;")
            layout.addWidget(lista_frame)
            
            self.lista_templates = QListWidget()
            self.lista_templates.setFixedWidth(300)
            self.lista_templates.setStyleSheet("""
                QListWidget {
                    border: 2px solid #9C27B0;
                    border-radius: 8px;
                    background-color: #ffffff;
                    font-size: 12px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 12px;
                    border-bottom: 1px solid #e9ecef;
                    border-radius: 4px;
                    margin: 2px;
                }
                QListWidget::item:hover {
                    background-color: #E1BEE7;
                    color: #9C27B0;
                }
                QListWidget::item:selected {
                    background-color: #9C27B0;
                    color: white;
                }
            """)
            
            for nome_template in templates_base.keys():
                item = QListWidgetItem(nome_template)
                self.lista_templates.addItem(item)
            
            # Preview do template PERSONALIZADO
            preview_frame = QVBoxLayout()
            preview_label = QLabel("👁️ Preview com Personalização Completa:")
            preview_label.setStyleSheet("font-weight: bold; color: #6c757d; margin-bottom: 5px;")
            preview_frame.addWidget(preview_label)
            
            preview_text = QTextEdit()
            preview_text.setReadOnly(True)
            preview_text.setMinimumHeight(400)
            preview_text.setStyleSheet("""
                QTextEdit {
                    border: 2px solid #9C27B0;
                    border-radius: 8px;
                    background-color: #fefefe;
                    font-family: 'Times New Roman', serif;
                    font-size: 11px;
                    padding: 15px;
                    line-height: 1.4;
                }
            """)
            preview_frame.addWidget(preview_text)
            
            horizontal_layout.addWidget(self.lista_templates)
            horizontal_layout.addLayout(preview_frame)
            layout.addLayout(horizontal_layout)
            
            # ✅ ATUALIZAR PREVIEW COM SISTEMA PERSONALIZADO
            def atualizar_preview():
                item_atual = self.lista_templates.currentItem()
                if item_atual:
                    nome = item_atual.text()
                    conteudo_base = templates_base[nome]
                    
                    # Se é o template de exemplo, mostrar preview completo
                    if "Template Personalizado Completo" in nome:
                        try:
                            from email_templates_biodesk import gerar_email_personalizado
                            
                            # Gerar preview personalizado de exemplo
                            exemplo_personalizado = gerar_email_personalizado(
                                nome_paciente=nome_paciente,
                                templates_anexados=["Template de Exemplo"],  # ✅ Parâmetro correto
                                tipo_comunicacao="templates"  # ✅ Parâmetro correto
                            )
                            
                            preview_text.setPlainText(f"ASSUNTO: {exemplo_personalizado['assunto']}\n\n{exemplo_personalizado['corpo']}")
                            
                        except ImportError:
                            preview_text.setPlainText("Sistema de personalização não disponível - usando template básico.")
                    else:
                        # Para outros templates, mostrar como ficará personalizado
                        try:
                            from email_templates_biodesk import gerar_email_personalizado
                            
                            preview_personalizado = gerar_email_personalizado(
                                nome_paciente=nome_paciente,
                                templates_anexados=[nome],  # ✅ Usar nome do template em vez de path
                                tipo_comunicacao="templates"  # ✅ Parâmetro correto
                            )
                            
                            preview_text.setPlainText(f"ASSUNTO: {preview_personalizado['assunto']}\n\n{preview_personalizado['corpo']}")
                            
                        except ImportError:
                            # Fallback simples se sistema não disponível
                            preview_text.setPlainText(f"Exm./a Sr./a {nome_paciente},\n\n{conteudo_base}\n\nCom os melhores cumprimentos,\nDr. Nuno Correia")
            
            self.lista_templates.itemSelectionChanged.connect(atualizar_preview)
            
            # Botões
            botoes_layout = QHBoxLayout()
            botoes_layout.setSpacing(15)
            
            btn_cancelar = ButtonManager.cancelar_button(dialog, dialog.reject)
            btn_cancelar.setFixedHeight(40)
            
            btn_usar = ButtonManager.template_personalizado_button(dialog, None)  # callback será definido abaixo
            btn_usar.setFixedHeight(40)

            # ✅ FUNÇÃO PARA USAR TEMPLATE PERSONALIZADO
            def usar_template():
                item_atual = self.lista_templates.currentItem()
                if item_atual:
                    nome = item_atual.text()
                    conteudo_base = templates_base[nome]
                    
                    # Se é template de exemplo, usar conteudo genérico
                    if "Template Personalizado Completo" in nome:
                        conteudo_base = "Espero que esteja bem. Este email foi gerado automaticamente com personalização completa."
                    
                    # Aplicar personalização automática
                    try:
                        from email_templates_biodesk import gerar_email_personalizado
                        
                        # Gerar email personalizado completo (corrigir parâmetros)
                        email_personalizado = gerar_email_personalizado(
                            nome_paciente=nome_paciente,
                            templates_anexados=[template_nome],
                            tipo_comunicacao="templates"
                        )
                        
                        # Aplicar aos campos da interface
                        self.assunto_edit.setText(email_personalizado['assunto'])
                        self.mensagem_edit.setPlainText(email_personalizado['corpo'])
                        
                        print(f"✅ [TEMPLATES] Template personalizado aplicado: {nome}")
                        
                    except ImportError:
                        # Fallback simples
                        self.mensagem_edit.setPlainText(f"Exm./a Sr./a {nome_paciente},\n\n{conteudo_base}\n\nCom os melhores cumprimentos,\nDr. Nuno Correia")
                        print(f"⚠️ [TEMPLATES] Sistema personalizado indisponível, usando template simples")
                    
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Aviso", "Selecione um template primeiro.")
            
            btn_usar.clicked.connect(usar_template)
            
            botoes_layout.addStretch()
            botoes_layout.addWidget(btn_cancelar)
            botoes_layout.addWidget(btn_usar)
            layout.addLayout(botoes_layout)
            
            # Selecionar primeiro item por padrão
            if self.lista_templates.count() > 0:
                self.lista_templates.setCurrentRow(0)
                atualizar_preview()
            
            dialog.exec()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", f"Erro ao abrir templates: {str(e)}")
            print(f"❌ [TEMPLATES] Erro: {e}")

    def selecionar_pdf_e_mostrar_visualizador(self, template_data):
        """Seleciona PDF, mostra no canvas E adiciona à lista de protocolos selecionados"""
        try:
            import os
            from datetime import datetime
            from PyQt6.QtCore import QUrl
            
            nome_protocolo = template_data.get('nome', 'Sem nome')
            print(f"📄 [PDF INTEGRADO] Selecionado: {nome_protocolo}")
            
            # ADICIONAR À LISTA DE PROTOCOLOS SELECIONADOS
            if template_data not in self.protocolos_selecionados:
                self.protocolos_selecionados.append(template_data)
                self.atualizar_lista_protocolos()
                print(f"✅ [PROTOCOLOS] Adicionado à seleção: {nome_protocolo}")
            else:
                print(f"ℹ️ [PROTOCOLOS] Já selecionado: {nome_protocolo}")
            
            pdf_path = template_data.get('arquivo')
            
            # Abrir PDF externamente para evitar janela que pisca
            if pdf_path and os.path.exists(pdf_path):
                try:
                    # Mostrar texto extraído do PDF no preview
                    self.mostrar_pdf_como_texto_integrado(template_data)
                    print(f"📄 [PDF] Preview de texto carregado: {template_data.get('nome')}")
                except Exception as e:
                    print(f"⚠️ [PDF] Erro ao extrair texto: {e}")
                    traceback.print_exc()
                    # Fallback para texto
                    self.mostrar_pdf_como_texto_integrado(template_data)
            else:
                print(f"❌ [PDF INTEGRADO] Arquivo não encontrado: {pdf_path}")
                self.mostrar_erro_pdf_integrado(template_data, "Arquivo PDF não encontrado")
            
            # Guardar template selecionado
            self.template_selecionado = template_data
                
        except Exception as e:
            print(f"❌ [PDF INTEGRADO] Erro geral: {e}")
            self.mostrar_erro_pdf_integrado(template_data, str(e))
            import traceback
            traceback.print_exc()
    
    def atualizar_lista_protocolos(self):
        """Atualiza a visualização da lista de protocolos selecionados"""
        if not self.protocolos_selecionados:
            self.lista_protocolos.setText("Nenhum protocolo selecionado")
            return
        
        # Criar lista formatada
        lista_texto = []
        for i, protocolo in enumerate(self.protocolos_selecionados, 1):
            nome = protocolo.get('nome', 'Sem nome')
            categoria = protocolo.get('categoria', 'N/A')
            lista_texto.append(f"{i}. {nome}")
        
        texto_final = "\n".join(lista_texto)
        if len(self.protocolos_selecionados) > 1:
            texto_final += f"\n\n📊 Total: {len(self.protocolos_selecionados)} protocolos"
        
        self.lista_protocolos.setText(texto_final)
        print(f"📋 [PROTOCOLOS] Lista atualizada: {len(self.protocolos_selecionados)} itens")
    
    def limpar_protocolos_selecionados(self):
        """Limpa a lista de protocolos selecionados"""
        self.protocolos_selecionados.clear()
        self.atualizar_lista_protocolos()
        print("🗑️ [PROTOCOLOS] Lista de protocolos limpa")
    
    def enviar_protocolos_direto(self):
        """NOVO: Envio direto dos protocolos PDF selecionados sem conversão"""
        try:
            print("🚀 [ENVIO DIRETO] Iniciando envio dos protocolos selecionados...")
            
            if not self.protocolos_selecionados:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Selecione pelo menos um protocolo antes de enviar!")
                return
            
            # Verificar dados do paciente
            if not self.paciente_data or not self.paciente_data.get('email'):
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Paciente não tem email cadastrado!")
                return
            
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            email_paciente = self.paciente_data.get('email')
            
            print(f"📧 [ENVIO DIRETO] Destinatário: {nome_paciente} - {email_paciente}")
            print(f"📋 [ENVIO DIRETO] Protocolos: {len(self.protocolos_selecionados)} itens")
            
            # Preparar lista de anexos
            anexos = []
            nomes_protocolos = []
            
            for protocolo in self.protocolos_selecionados:
                arquivo_pdf = protocolo.get('arquivo')
                if arquivo_pdf and os.path.exists(arquivo_pdf):
                    anexos.append(arquivo_pdf)
                    nomes_protocolos.append(protocolo.get('nome', 'Protocolo'))
                    print(f"📎 [ANEXO] {protocolo.get('nome')} - {arquivo_pdf}")
                else:
                    print(f"❌ [ANEXO PERDIDO] {protocolo.get('nome')} - arquivo não encontrado: {arquivo_pdf}")
            
            if not anexos:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "Nenhum arquivo PDF válido encontrado!")
                return
            
            # Criar email personalizado
            lista_protocolos = "\n".join([f"• {nome}" for nome in nomes_protocolos])
            
            assunto = f"Protocolos Terapêuticos - {nome_paciente}"
            corpo = f"""Exm./a Sr./a {nome_paciente},

Espero que se encontre bem.

Conforme combinado na consulta, anexo os seguintes protocolos terapêuticos personalizados:

{lista_protocolos}

Estes protocolos foram cuidadosamente selecionados tendo em conta o seu perfil específico e objetivos de saúde.

Por favor, leia atentamente as orientações e não hesite em contactar-me caso tenha alguma dúvida.

Com os melhores cumprimentos,

Dr. Nuno Correia
Naturopata | Osteopata | Medicina Quântica
📧 Email: [seu email]
📱 Contacto: [seu contacto]"""

            # Aplicar ao interface de email
            self.assunto_edit.setText(assunto)
            self.mensagem_edit.setPlainText(corpo)
            
            # ✅ ATUALIZAR LISTA DE ANEXOS VISUALMENTE
            if hasattr(self, 'lista_anexos'):
                self.lista_anexos.clear()
                for i, protocolo in enumerate(nomes_protocolos, 1):
                    item_texto = f"📄 {i}. {protocolo}"
                    self.lista_anexos.addItem(item_texto)
            
            # ✅ ATUALIZAR VISIBILIDADE DA SEÇÃO DE ANEXOS
            self.atualizar_visibilidade_anexos()
            
            # Simular envio (aqui integraria com sistema real de email)
            print(f"✅ [ENVIO DIRETO] Email preparado com {len(anexos)} anexos")
            print(f"📧 [ENVIO DIRETO] Assunto: {assunto}")
            
            # Registar no histórico
            from datetime import datetime
            historico_entry = {
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'paciente': nome_paciente,
                'email': email_paciente,
                'tipo': 'protocolos_direto',
                'protocolos': nomes_protocolos,
                'status': 'preparado'
            }
            
            # Feedback visual - ESTILO BIODESK
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, "Sucesso", 
                             f"Email preparado com sucesso!\n\n" +
                             f"Destinatário: {nome_paciente}\n" +
                             f"Protocolos: {len(anexos)} anexos\n\n" +
                             f"Use a aba 'Email' para revisar e enviar.",
                             tipo="sucesso")
            
            print("🎯 [ENVIO DIRETO] Processo concluído - email preparado para envio")
            
        except Exception as e:
            print(f"❌ [ENVIO DIRETO] Erro: {e}")
            import traceback
            traceback.print_exc()
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro no envio direto: {str(e)}")
    
    def mostrar_pdf_como_texto_integrado(self, template_data):
        """Mostra PDF como texto extraído no preview integrado"""
        try:
            import os
            from datetime import datetime
            
            nome_paciente = self.paciente_data.get('nome', 'N/A') if self.paciente_data else 'N/A'
            data_atual = datetime.now().strftime('%d/%m/%Y')
            pdf_path = template_data.get('arquivo')
            conteudo_pdf = ""
            
            if pdf_path and os.path.exists(pdf_path):
                try:
                    # Extrair texto do PDF
                    import PyPDF2
                    with open(pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        conteudo_pdf = ""
                        for page_num, page in enumerate(pdf_reader.pages[:3]):  # Primeiras 3 páginas
                            conteudo_pdf += f"\n--- PÁGINA {page_num + 1} ---\n"
                            conteudo_pdf += page.extract_text()
                            conteudo_pdf += "\n"
                        
                        if len(pdf_reader.pages) > 3:
                            conteudo_pdf += f"\n... (mais {len(pdf_reader.pages) - 3} páginas no documento completo) ..."
                            
                except Exception as e:
                    conteudo_pdf = f"❌ Erro ao ler PDF: {str(e)}\n\nPDF existe mas conteúdo não pode ser extraído automaticamente."
            else:
                conteudo_pdf = "❌ Arquivo PDF não encontrado."
            
            # PREVIEW INTEGRADO COM CONTEÚDO DO PDF
            info_integrada = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🩺 DOCUMENTO PDF - CONTEÚDO EXTRAÍDO                    ║
║                            Dr. Nuno Correia                                 ║
║                         Medicina Integrativa                                ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 PACIENTE: {nome_paciente}
📅 DATA: {data_atual}

📄 DOCUMENTO: {template_data['nome'].upper()}
📁 Categoria: {template_data.get('categoria', 'N/A').title()}
📏 Tamanho: {template_data.get('tamanho', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 CONTEÚDO DO PDF (INTEGRADO - SEM JANELAS SEPARADAS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{conteudo_pdf}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 EMAIL PERSONALIZADO PRONTO:
• Saudação personalizada baseada na hora
• Nome do paciente: {nome_paciente}
• Redes sociais: @nunocorreia.naturopata (Instagram)
• Redes sociais: @NunoCorreiaTerapiasNaturais (Facebook)
• Assinatura profissional completa

🎯 PRÓXIMO PASSO:
   Clique "🚀 Enviar e Registar" para enviar este PDF ao paciente
   com email personalizado e registar no histórico.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            🔗 PDF TOTALMENTE INTEGRADO NO CANVAS (SEM JANELAS EXTERNAS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            # ✅ MOSTRAR PRIMEIRO o texto extraído
            self.template_preview.setPlainText(info_integrada)
            self.preview_stack.setCurrentIndex(0)  # Mostrar texto primeiro
            
            # ✅ CONFIGURAR o botão PDF externo
            if pdf_path and os.path.exists(pdf_path):
                self._ultimo_pdf_gerado = pdf_path
                
                # Ativar botão principal no preview
                if hasattr(self, 'btn_pdf_preview'):
                    self.btn_pdf_preview.setEnabled(True)
                    self.btn_pdf_preview.setVisible(True)
                    self.btn_pdf_preview.setText(f"🔍 Abrir: {os.path.basename(pdf_path)}")
                
                # Ativar botão no widget PDF externo (se existir)
                if hasattr(self, 'btn_abrir_pdf_externo'):
                    self.btn_abrir_pdf_externo.setEnabled(True)
                    self.btn_abrir_pdf_externo.setText(f"🔍 Ver PDF Completo: {os.path.basename(pdf_path)}")
                    
                    # ✅ ADICIONAR botão ao preview de texto para acesso rápido
                    texto_com_botao = info_integrada + f"""

🔗 AÇÃO DISPONÍVEL:
   📄 Use o botão "🔍 Abrir PDF Completo" abaixo para ver
   o documento com formatação original no visualizador externo.
   
   📁 Arquivo: {os.path.basename(pdf_path)}
"""
                    self.template_preview.setPlainText(texto_com_botao)
            else:
                # Desativar botão se não há PDF
                if hasattr(self, 'btn_pdf_preview'):
                    self.btn_pdf_preview.setEnabled(False)
                    self.btn_pdf_preview.setVisible(False)
            
            print(f"✅ [PDF INTEGRADO] Texto + botão configurados: {template_data.get('nome')}")
            
        except Exception as e:
            self.mostrar_erro_pdf_integrado(template_data, str(e))
    
    def mostrar_erro_pdf_integrado(self, template_data, erro):
        """Mostra erro no preview integrado"""
        nome_paciente = self.paciente_data.get('nome', 'N/A') if self.paciente_data else 'N/A'
        
        info_erro = f"""
📄 PDF SELECIONADO: {template_data.get('nome', 'Sem nome')}

❌ Erro: {erro}

📋 INFORMAÇÕES:
• Paciente: {nome_paciente}
• Categoria: {template_data.get('categoria', 'N/A').title()}
• Tamanho: {template_data.get('tamanho', 'N/A')}

💡 O PDF existe mas não pode ser visualizado diretamente no canvas.
   Use "🚀 Enviar e Registar" para processar e enviar ao paciente.

📧 Email personalizado será enviado normalmente com o PDF anexo:
   • Com redes sociais integradas
   • Assinatura profissional
   • Conteúdo personalizado
"""
        self.template_preview.setPlainText(info_erro)
        self.preview_stack.setCurrentIndex(0)  # Mostrar texto
        self.template_selecionado = template_data

    def usar_template_dialog(self):
        """Abre diálogo para usar templates predefinidos - REFATORADO"""
        try:
            from ficha_paciente.dialogs.template_dialog import TemplateDialog
            
            def aplicar_template(template_texto):
                """Callback para aplicar o template selecionado"""
                if hasattr(self, 'mensagem_edit'):
                    self.mensagem_edit.setPlainText(template_texto)
            
            # Abrir diálogo usando a nova classe extraída
            TemplateDialog.abrir_dialog(callback=aplicar_template, parent=self)
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", f"Erro ao abrir templates: {str(e)}")
            print(f"[TEMPLATE] ❌ Erro: {e}")

    def enviar_mensagem(self):
        """MÉTODO REFATORADO - usa ValidationService"""
        from ficha_paciente.services import ValidationService
        
        if not self.canal_atual or self.canal_atual != "email":
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Canal não disponível", "Apenas o canal de email está disponível.")
            return
        
        destinatario = self.destinatario_edit.text()
        mensagem = self.mensagem_edit.toPlainText()
        assunto = self.assunto_edit.text() or "Mensagem do Biodesk"
        
        # Usar ValidationService para validar campos
        valido, erros = ValidationService.validar_campos_email(destinatario, assunto, mensagem)
        if not valido:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Campos inválidos", "\n".join(erros))
            return
        
        # Obter nome do paciente atual
        nome_paciente = self.paciente_data.get('nome', 'Paciente') if self.paciente_data else 'Paciente'
        
        try:
            # ✅ USAR NOVO SISTEMA DE EMAIL PERSONALIZADO
            from email_templates_biodesk import gerar_email_personalizado
            
            # Preparar lista dos protocolos selecionados (se houver)
            protocolos_anexados = []
            if hasattr(self, 'protocolos_selecionados') and self.protocolos_selecionados:
                protocolos_anexados = [p.get('nome', 'Protocolo') for p in self.protocolos_selecionados]
            
            # Gerar email personalizado com redes sociais
            email_personalizado = gerar_email_personalizado(
                nome_paciente=nome_paciente,
                templates_anexados=protocolos_anexados,
                tipo_comunicacao="mensagem"
            )
            
            # Usar o novo sistema de email
            from email_sender import EmailSender
            from email_config import EmailConfig
            
            config = EmailConfig()
            if not config.is_configured():
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Email não configurado", 
                             "Configure o email nas configurações primeiro.")
                return
            
            email_sender = EmailSender()
            
            # Preparar anexos se houver protocolos selecionados
            import os
            anexos = []
                
            if hasattr(self, 'protocolos_selecionados') and self.protocolos_selecionados:
                for protocolo in self.protocolos_selecionados:
                    arquivo_pdf = protocolo.get('arquivo')
                    if arquivo_pdf and os.path.exists(arquivo_pdf):
                        anexos.append(arquivo_pdf)
            
            # Enviar com email personalizado E ANEXOS (se houver)
            if anexos:
                success, error_msg = email_sender.send_email_with_attachments(
                    destinatario, 
                    email_personalizado['assunto'], 
                    email_personalizado['corpo'],
                    anexos
                )
            else:
                # Enviar sem anexos se não houver protocolos
                success, error_msg = email_sender.send_email(
                    destinatario, 
                    email_personalizado['assunto'], 
                    email_personalizado['corpo']
                )
            
            # Mostrar resultado
            if success:
                # Limpar campos apenas se enviou com sucesso
                self.mensagem_edit.clear()
                self.assunto_edit.clear()
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(self, "✅ Email Enviado", 
                                 f"Email personalizado enviado para {destinatario} com sucesso!\n\n"
                                 f"✅ Saudação personalizada incluída\n"
                                 f"✅ Redes sociais incluídas\n"
                                 f"✅ Assinatura profissional aplicada")
                print(f"[COMUNICAÇÃO] ✅ EMAIL PERSONALIZADO enviado para {destinatario}")
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "❌ Erro no Envio", 
                           f"Falha ao enviar email:\n\n{error_msg}")
                print(f"[COMUNICAÇÃO] ❌ Erro EMAIL: {error_msg}")
                
        except ImportError:
            print("[COMUNICAÇÃO] ⚠️ Sistema personalizado não disponível, usando sistema padrão")
            # Fallback para sistema anterior se o novo não estiver disponível
            try:
                from email_sender import EmailSender
                from email_config import EmailConfig
                
                config = EmailConfig()
                if not config.is_configured():
                    from biodesk_dialogs import mostrar_aviso
                    mostrar_aviso(self, "Email não configurado", 
                                 "Configure o email nas configurações primeiro.")
                    return
                
                email_sender = EmailSender()
                success, error_msg = email_sender.send_email(destinatario, assunto, mensagem)
                
                if success:
                    self.mensagem_edit.clear()
                    self.assunto_edit.clear()
                    
                    from biodesk_dialogs import mostrar_informacao
                    mostrar_informacao(self, "✅ Email Enviado", 
                                     f"Email enviado para {destinatario} com sucesso!")
                    print(f"[COMUNICAÇÃO] ✅ EMAIL (padrão) enviado para {destinatario}")
                else:
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(self, "❌ Erro no Envio", 
                               f"Falha ao enviar email:\n\n{error_msg}")
                    print(f"[COMUNICAÇÃO] ❌ Erro EMAIL: {error_msg}")
                    
            except Exception as e:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "❌ Erro do Sistema", 
                           f"Erro no sistema de email:\n\n{str(e)}")
                print(f"[COMUNICAÇÃO] ❌ Erro sistema EMAIL: {e}")
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "❌ Erro do Sistema", 
                       f"Erro no sistema de email:\n\n{str(e)}")
            print(f"[COMUNICAÇÃO] ❌ Erro sistema EMAIL: {e}")

    def abrir_configuracoes_comunicacao(self):
        """Abre a janela de configurações de email"""
        try:
            from email_config_window import EmailConfigWindow
            
            # Criar e mostrar janela de configuração de email
            self.config_window = EmailConfigWindow()
            self.config_window.show()
            
            print("[COMUNICAÇÃO] ⚙️ Janela de configurações de email aberta")
            
        except ImportError as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Módulo não encontrado", 
                       f"Não foi possível carregar as configurações de email.\n\n"
                       f"Erro: {e}\n\n"
                       f"Verifique se o arquivo email_config_window.py existe.")
            print(f"[COMUNICAÇÃO] ❌ Erro ao abrir configurações: {e}")
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao abrir configurações:\n{str(e)}")
            print(f"[COMUNICAÇÃO] ❌ Erro inesperado: {e}")

    def init_sub_declaracao_saude_modular(self):
        """Sub-aba: Declaração de Saúde - VERSÃO MODULAR"""
        try:
            # Import lazy do módulo especializado
            _, _, _, _, _, DeclaracaoSaudeWidget, _, _ = importar_modulos_especializados()
            
            # Criar widget especializado
            self.declaracao_saude_widget = DeclaracaoSaudeWidget(self)
            
            # Conectar sinais
            self.declaracao_saude_widget.declaracao_assinada.connect(self.on_declaracao_assinada)
            self.declaracao_saude_widget.dados_atualizados.connect(self.on_declaracao_dados_atualizados)
            
            # Layout para o widget modular
            if not self.sub_declaracao_saude.layout():
                layout = QVBoxLayout(self.sub_declaracao_saude)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.declaracao_saude_widget)
            else:
                self.sub_declaracao_saude.layout().addWidget(self.declaracao_saude_widget)
            
            # Carregar dados do paciente se disponível
            if hasattr(self, 'paciente_data') and self.paciente_data:
                if hasattr(self.declaracao_saude_widget, 'set_paciente_data'):
                    self.declaracao_saude_widget.set_paciente_data(self.paciente_data)
                elif hasattr(self.declaracao_saude_widget, 'carregar_dados_paciente'):
                    self.declaracao_saude_widget.carregar_dados_paciente(self.paciente_data)
            
            return True
            
        except Exception as e:
            return self.init_sub_declaracao_saude_fallback()
    
    def init_sub_declaracao_saude_fallback(self):
        """Fallback para declaração de saúde caso o módulo falhe"""
        layout = QVBoxLayout(self.sub_declaracao_saude)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("❌ Módulo de Declaração de Saúde indisponível")
        label.setStyleSheet("color: #e74c3c; font-size: 16px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        print("⚠️ Usando fallback para DeclaracaoSaudeWidget")
        return False
    
    # Callbacks para o módulo de declaração de saúde
    def on_declaracao_assinada(self, dados):
        """Callback quando declaração é assinada"""
        print(f"✅ Declaração assinada para paciente {dados.get('paciente_id')}")
        
        # Atualizar lista de documentos no gestor
        if hasattr(self, 'gestao_documentos_widget'):
            try:
                print("🔄 Atualizando lista de documentos...")
                self.gestao_documentos_widget.atualizar_lista_documentos()
                print("✅ Lista de documentos atualizada")
            except Exception as e:
                print(f"⚠️ Erro ao atualizar gestor de documentos: {e}")
        
        try:
            self.atualizar_lista_documentos()
            print("✅ Lista atualizada via delegate")
        except Exception as e:
            print(f"ℹ️ Delegate não disponível: {e}")
    
    def on_declaracao_dados_atualizados(self, dados):
        """Callback quando dados da declaração são atualizados"""
        print(f"📄 Dados da declaração atualizados: {dados}")

    def init_sub_gestao_documentos_modular(self):
        """Sub-aba: Gestão de Documentos - MÓDULO OTIMIZADO"""
        # ✅ USAR MÓDULO OTIMIZADO DE GESTÃO DE DOCUMENTOS
        from ficha_paciente.gestao_documentos import GestaoDocumentosWidget
        
        # Criar layout principal
        layout = QVBoxLayout(self.sub_gestao_documentos)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Criar widget especializado
        self.gestao_documentos_widget = GestaoDocumentosWidget(self)
        
        # Definir ID do paciente
        if self.paciente_data and 'id' in self.paciente_data:
            self.gestao_documentos_widget.set_paciente_id(self.paciente_data['id'])
        elif self.paciente_data and 'nome' in self.paciente_data:
            # Se não houver ID, usar nome como fallback
            self.gestao_documentos_widget.set_paciente_id(self.paciente_data['nome'])
        
        # Conectar sinais para comunicação
        self.gestao_documentos_widget.documento_adicionado.connect(self.on_documento_adicionado)
        self.gestao_documentos_widget.documento_removido.connect(self.on_documento_removido)
        self.gestao_documentos_widget.documento_visualizado.connect(self.on_documento_visualizado)
        
        # Adicionar ao layout
        layout.addWidget(self.gestao_documentos_widget)
        
        print("✅ Gestão de Documentos carregado com sucesso")
    
    # Callbacks para integração com o módulo especializado
    def on_documento_adicionado(self, caminho_documento):
        """Callback quando documento é adicionado"""
        print(f"📄 Documento adicionado: {caminho_documento}")
    
    def on_documento_removido(self, caminho_documento):
        """Callback quando documento é removido"""
        print(f"🗑️ Documento removido: {caminho_documento}")
    
    def on_documento_visualizado(self, caminho_documento):
        """Callback quando documento é visualizado"""
        print(f"👁️ Documento visualizado: {caminho_documento}")
    
    def on_documento_assinado(self, caminho_documento):
        """Callback quando documento é assinado"""
        print(f"✍️ Documento assinado: {caminho_documento}")
    
    def atualizar_lista_documentos(self):
        """Delegado para atualizar a lista no Gestor de Documentos."""
        try:
            if hasattr(self, "gestao_documentos_widget") and self.gestao_documentos_widget:
                # Garantir que está a usar o ID atual
                pid = self.paciente_data.get("id") or self.paciente_data.get("nome")
                if pid:
                    self.gestao_documentos_widget.set_paciente_id(pid)
                self.gestao_documentos_widget.atualizar_lista_documentos()
                print("🔄 [DOCUMENTOS] Refresh pedido pela FichaPaciente")
        except Exception as e:
            print(f"❌ [DOCUMENTOS] Erro no refresh delegado: {e}")

    def _on_dados_tab_changed(self, idx):
        """🚀 LAZY LOADING: Carrega sub-tab de dados/documentos sob demanda"""
        try:
            tab_names = ['dados_pessoais', 'declaracao_saude', 'gestao_documentos']
            
            if 0 <= idx < len(tab_names):
                tab_name = tab_names[idx]
                
                # Carregar tab apenas se ainda não foi carregado
                if not self._tabs_loaded.get(tab_name, False):
                    print(f"🚀 [LAZY] Carregando sub-tab '{tab_name}' sob demanda...")
                    
                    # Carregar tab específico
                    if tab_name == 'dados_pessoais':
                        self.init_sub_dados_pessoais()
                    elif tab_name == 'declaracao_saude':
                        self.init_sub_declaracao_saude_modular()
                    elif tab_name == 'gestao_documentos':
                        self.init_sub_gestao_documentos_modular()
                    
                    # Marcar como carregado
                    self._tabs_loaded[tab_name] = True
                    print(f"✅ [LAZY] Sub-tab '{tab_name}' carregado com sucesso")
                else:
                    print(f"♻️ [LAZY] Sub-tab '{tab_name}' já carregado - reutilizando")
                    
        except Exception as e:
            print(f"❌ [LAZY] Erro ao carregar sub-tab: {e}")

    def init_sub_iris_analise(self):
        """Análise de Íris - Módulo Otimizado"""
        try:
            from ficha_paciente.iris_integration import IrisIntegrationWidget
            
            layout = QVBoxLayout(self.sub_iris_analise)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Usar módulo especializado
            self.iris_widget = IrisIntegrationWidget(self.paciente_data, self)
            layout.addWidget(self.iris_widget)
            
            # Conectar sinais
            self.iris_widget.zona_clicada.connect(self.on_zona_clicada)
            self.iris_widget.imagem_selecionada.connect(self.on_imagem_iris_selecionada)
            self.iris_widget.notas_exportadas.connect(self.on_notas_iris_exportadas)
            
            # print("✅ Módulo de Íris carregado com sucesso")
            
        except ImportError as e:
            print(f"❌ Erro ao carregar módulo de íris: {e}")
            self.init_sub_iris_analise_fallback()

    def on_zona_clicada(self, nome_zona):
        """
        ✅ FUNCIONALIDADE RESTAURADA: Análise interativa de sinais de íris
        Processa clique numa zona da íris e abre popup de análise de sinais
        """
        print(f"🔍 Zona clicada para análise: {nome_zona}")
        
        # Adicionar nota automaticamente na área de notas
        if hasattr(self, 'notas_iris'):
            try:
                if hasattr(self.notas_iris, 'adicionar_linha'):
                    self.notas_iris.adicionar_linha(f"🎯 Análise: {nome_zona}")
                    print(f"✅ Nota adicionada para zona: {nome_zona}")
                elif hasattr(self.notas_iris, 'setPlainText'):
                    # QTextEdit simples
                    texto_atual = self.notas_iris.toPlainText()
                    if texto_atual:
                        texto_atual += f"\n🎯 Análise: {nome_zona}"
                    else:
                        texto_atual = f"🎯 Análise: {nome_zona}"
                    self.notas_iris.setPlainText(texto_atual)
                    print(f"✅ Nota adicionada para zona: {nome_zona}")
                else:
                    print(f"⚠️ Widget de notas não suporta adição automática de texto")
                    
            except Exception as e:
                print(f"❌ Erro ao adicionar nota: {e}")
        
        # O popup de análise detalhada é aberto automaticamente pelo próprio ZonaReflexa

    def on_imagem_iris_selecionada(self, imagem_data):
        """Callback para quando uma imagem é selecionada na galeria"""
        print(f"🖼️ Imagem selecionada: {imagem_data}")
        # Processar seleção de imagem conforme necessário
        
    def on_notas_iris_exportadas(self, nota_zona):
        """Callback para quando uma zona é exportada da íris para o painel dedicado"""
        from datetime import datetime
        
        print(f"📝 Recebida zona da íris: {nota_zona}")
        
        # ✅ GARANTIR QUE O HISTÓRICO ESTÁ CARREGADO ANTES DE ADICIONAR NOTAS
        if not hasattr(self, 'historico_widget') or not self.historico_widget:
            print("🔄 Histórico não carregado ainda, carregando agora...")
            # Forçar carregamento do histórico se ainda não existe
            if not self._tabs_loaded.get('historico', False):
                self.init_tab_historico()
                self._tabs_loaded['historico'] = True
        
        # ✅ CORRIGIDO: Processar cada zona individualmente
        if hasattr(self, 'historico_widget') and self.historico_widget:
            try:
                # Verificar se o widget tem o método para adicionar análises de íris
                if hasattr(self.historico_widget, 'adicionar_analise_iris'):
                    # Limpar texto (remover prefixos como "Análise: ")
                    zona_limpa = nota_zona.replace('Análise: ', '').strip()
                    
                    # Adicionar zona individual
                    self.historico_widget.adicionar_analise_iris(zona_limpa)
                    
                    print(f"✅ Zona '{zona_limpa}' adicionada ao painel dedicado")
                else:
                    print("⚠️ Método adicionar_analise_iris não encontrado no widget de histórico")
            except Exception as e:
                print(f"❌ Erro ao adicionar análise ao painel de íris: {e}")
        else:
            print("⚠️ Widget de histórico ainda não disponível após carregamento")
            
            # Marcar como alterado para salvar
            self.dirty = True
            print("✅ Dados do paciente atualizados com notas da íris")

    def atualizar_textos_botoes(self, texto_linha=None):
        """Atualiza os textos dos botões mostrando quantas linhas estão selecionadas"""
        if not hasattr(self, 'notas_iris') or not self.notas_iris:
            return
            
        try:
            total = self.notas_iris.count_total()
            selecionadas = self.notas_iris.count_selecionadas()
            
            if total == 0:
                self.btn_exportar_notas.setText('📤 Histórico')
                self.btn_exportar_terapia.setText('⚡ Terapia')
            else:
                self.btn_exportar_notas.setText(f'📤 Histórico ({selecionadas}/{total})')
                self.btn_exportar_terapia.setText(f'⚡ Terapia ({selecionadas}/{total})')
        except Exception as e:
            print(f"[DEBUG] Erro ao atualizar textos dos botões: {e}")

    def init_sub_centro_comunicacao_unificado(self):
        """
        🚀 CENTRO DE COMUNICAÇÃO UNIFICADO
        ==================================
        
        Substitui as abas separadas de:
        - Email
        - Gestão de Documentos  
        - Templates/Prescrições
        
        Por uma interface unificada em 3 colunas
        """
        try:
            print("🚀 Carregando Centro de Comunicação Unificado...")
            
            # Limpar layout existente
            layout = QVBoxLayout(self.sub_centro_comunicacao)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Importar e instanciar o Centro de Comunicação
            from ficha_paciente.centro_comunicacao_unificado import CentroComunicacaoUnificado
            
            # Criar widget com dados do paciente
            self.centro_comunicacao_widget = CentroComunicacaoUnificado(self.paciente_data, self)
            
            # Conectar sinais
            if hasattr(self.centro_comunicacao_widget, 'comunicacao_realizada'):
                self.centro_comunicacao_widget.comunicacao_realizada.connect(self.on_comunicacao_realizada)
            
            # Adicionar ao layout
            layout.addWidget(self.centro_comunicacao_widget)
            
            print("✅ Centro de Comunicação Unificado carregado com sucesso!")
            
        except ImportError as e:
            print(f"❌ Erro ao importar Centro de Comunicação: {e}")
            self.init_sub_centro_comunicacao_fallback()
            
        except Exception as e:
            print(f"❌ Erro geral ao carregar Centro de Comunicação: {e}")
            import traceback
            traceback.print_exc()
            self.init_sub_centro_comunicacao_fallback()
    
    def on_comunicacao_realizada(self, comunicacao_data):
        """Callback quando uma comunicação é realizada no centro unificado"""
        try:
            print(f"📧 Comunicação realizada: {comunicacao_data.get('assunto', 'N/A')}")
            
            # Aqui poderia integrar com sistema de auditoria
            
        except Exception as e:
            print(f"⚠️ Erro no callback de comunicação: {e}")

    def init_tab_terapia(self):
        """Inicializa a aba de terapia quântica - Interface Zero"""
        layout = QVBoxLayout(self.tab_terapia)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Título principal - mesmo estilo do botão principal
        titulo = QLabel("🌟 TERAPIA QUÂNTICA 🌟")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #4a148c;
            padding: 25px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #e1bee7, stop:0.5 white, stop:1 #e1bee7);
            border-radius: 15px;
            border: 3px solid #9c27b0;
            margin-bottom: 20px;
        """)
        layout.addWidget(titulo)
        
        # Informações do paciente
        if self.paciente_data:
            info_paciente = QLabel(f"👤 Paciente: {self.paciente_data.get('nome', 'N/A')}")
            info_paciente.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_paciente.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #666;
                padding: 10px;
                background: #f8f8f8;
                border-radius: 8px;
                margin-bottom: 20px;
            """)
            layout.addWidget(info_paciente)

        # Área de desenvolvimento - mesma mensagem do botão principal
        area_dev = QLabel("""
        🔬 ÁREA COMPLETAMENTE VAZIA PARA DESENVOLVIMENTO
        
        Esta é uma tela em branco onde você pode:
        
        ✨ Implementar análise de frequências
        ✨ Criar protocolos terapêuticos
        ✨ Desenvolver biofeedback
        ✨ Adicionar análise de íris
        ✨ Criar seu próprio sistema de medicina quântica
        
        🎯 COMECE AQUI O SEU CÓDIGO!
        """)
        area_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_dev.setStyleSheet("""
            font-size: 16px;
            color: #444;
            padding: 40px;
            background: white;
            border: 3px dashed #9c27b0;
            border-radius: 15px;
            margin: 20px 0;
        """)
        layout.addWidget(area_dev)
        
        # Botões de ação - mesmo estilo
        botoes_layout = QHBoxLayout()
        # Botão de teste removido - funcionalidade obsoleta
        
        # Botão abrir módulo
        self.btn_abrir_terapia = ButtonManager.abrir_terapia_button(self, self.abrir_terapia)
        botoes_layout.addWidget(self.btn_abrir_terapia)
        
        botoes_layout.addStretch()
        layout.addLayout(botoes_layout)
        
        # Espaçador
        layout.addStretch()

    def inserir_data_negrito(self):
        import time
        from datetime import datetime
        
        # ✅ Debounce: prevenir cliques múltiplos acidentais (500ms)
        agora = time.time()
        if agora - self._ultimo_clique_data < 0.5:  # 500ms
            print("[DEBUG] Clique ignorado devido ao debounce")
            return
        self._ultimo_clique_data = agora
        
        data_hoje = datetime.today().strftime('%d/%m/%Y')
        
        # Usar verificação robusta de data existente
        existe, tipo = self._data_ja_existe_no_historico(data_hoje)
        
        if existe:
            from biodesk_dialogs import mostrar_informacao
            if tipo == 'iris':
                mostrar_informacao(
                    self, 
                    'Data já existe', 
                    f'Já existe um registo de análise de íris para hoje ({data_hoje}).\n\n'
                    'Pode continuar a adicionar conteúdo ao registo existente ou '
                    'usar a função "Exportar" na aba Íris para adicionar mais notas.'
                )
            else:
                mostrar_informacao(
                    self, 
                    'Data já existe', 
                    f'Já existe uma entrada para hoje ({data_hoje}) no histórico.\n\n'
                    'Pode continuar a escrever no registo existente.'
                )
            return
        
        prefixo = f'<b>{data_hoje}</b><br><hr style="border: none; border-top: 1px solid #bbb; margin: 10px 6px;">'
        # Montar novo HTML, garantindo separação de blocos
        html_atual = self.historico_edit.toHtml()
        novo_html = f'{prefixo}<div></div>{html_atual}'
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
        """Carrega os dados do paciente nos widgets especializados"""
        # CORREÇÃO: Prevenir callbacks de marcar como dirty durante carregamento
        self._carregando_dados = True
        
        try:
            d = self.paciente_data
            
            # Carregar dados pessoais no widget especializado
            if hasattr(self, 'dados_pessoais_widget'):
                try:
                    # O widget usa self.paciente_data internamente
                    self.dados_pessoais_widget.paciente_data = d
                    self.dados_pessoais_widget.carregar_dados()
                    # print("✅ Dados pessoais carregados no widget especializado")
                except Exception as e:
                    print(f"❌ Erro ao carregar dados pessoais: {e}")
            
            # Carregar histórico clínico no widget especializado  
            if hasattr(self, 'historico_widget'):
                try:
                    historico = d.get('historico_clinico', '') or d.get('historico', '')
                    # O widget usa self.historico_texto internamente
                    self.historico_widget.historico_texto = historico
                    self.historico_widget.carregar_historico()
                    print("✅ Histórico clínico carregado no widget especializado")
                except Exception as e:
                    print(f"❌ Erro ao carregar histórico: {e}")
            
            # Carregar outros dados que ainda não foram modularizados
            
            # Carregar novos campos se existirem
            if hasattr(self, 'observacoes_edit'):
                self.observacoes_edit.setText(d.get('observacoes', ''))
            if hasattr(self, 'conheceu_combo'):
                self.conheceu_combo.setCurrentText(d.get('conheceu', ''))
            if hasattr(self, 'referenciado_edit'):
                self.referenciado_edit.setText(d.get('referenciado', ''))
            if hasattr(self, 'nif_edit'):
                self.nif_edit.setText(d.get('nif', ''))
            if hasattr(self, 'local_combo'):
                self.local_combo.setCurrentText(d.get('local_habitual', ''))
        
            # ✅ CORREÇÃO: Carregar dados do email automaticamente
            if hasattr(self, 'carregar_dados_paciente_email'):
                self.carregar_dados_paciente_email()
                
            # ✅ NOVO: Carregar dados da declaração de saúde
            if hasattr(self, 'carregar_dados_paciente_declaracao'):
                self.carregar_dados_paciente_declaracao()
                # Dados do email recarregados automaticamente
            
            # ✅ CORREÇÃO: Atualizar lista de documentos quando o paciente é carregado
            if hasattr(self, 'atualizar_lista_documentos'):
                try:
                    self.atualizar_lista_documentos()
                    print(f"🔄 [DOCUMENTOS] Lista atualizada para paciente: {d.get('nome', 'Sem nome')}")
                except Exception as e:
                    print(f"❌ [DOCUMENTOS] Erro ao atualizar lista: {e}")
        
        finally:
            # CORREÇÃO: Reativar callbacks após carregamento completo
            self._carregando_dados = False
            # Resetar estado dirty após carregamento inicial
            self.dirty = False

    def guardar(self):
        """Guarda os dados do utente na base de dados usando widgets especializados"""
        print("🔍 [DEBUG GUARDAR] === INÍCIO DA FUNÇÃO GUARDAR ===")
        from db_manager import DBManager
        
        # Obter dados do widget de dados pessoais
        dados = {}
        if hasattr(self, 'dados_pessoais_widget'):
            try:
                dados_pessoais = self.dados_pessoais_widget.obter_dados()
                dados.update(dados_pessoais)
            except Exception as e:
                print(f"❌ Erro ao obter dados pessoais: {e}")
        
        # Obter histórico clínico do widget especializado
        if hasattr(self, 'historico_widget'):
            try:
                historico = self.historico_widget.obter_historico()
                dados['historico'] = historico
                print(f"🔍 [DEBUG HISTÓRICO] Obtido histórico com {len(historico)} caracteres")
                print(f"🔍 [DEBUG HISTÓRICO] Primeiros 200 chars: {historico[:200]}")
            except Exception as e:
                print(f"❌ Erro ao obter histórico: {e}")
        else:
            print("⚠️ [DEBUG HISTÓRICO] Widget de histórico não disponível")
        
        # Incluir ID se existir
        if 'id' in self.paciente_data:
            dados['id'] = self.paciente_data['id']
        
        # Salvar na base de dados
        from db_manager import DBManager
        db = DBManager()
        
        print(f"🔍 [DEBUG GUARDAR] Dados a guardar: {list(dados.keys())}")
        if 'historico' in dados:
            print(f"🔍 [DEBUG GUARDAR] Histórico tem {len(dados['historico'])} caracteres")
        
        # Prevenção de duplicação por nome + data_nascimento
        query = "SELECT * FROM pacientes WHERE nome = ? AND data_nascimento = ?"
        params = (dados['nome'], dados['data_nascimento'])
        duplicados = db.execute_query(query, params)
        if duplicados and (not ('id' in dados and duplicados[0].get('id') == dados['id'])):
            from biodesk_styled_dialogs import BiodeskMessageBox
            BiodeskMessageBox.warning(self, "Duplicado", "Já existe um utente com este nome e data de nascimento.")
            return
            
        novo_id = db.save_or_update_paciente(dados)
        
        print(f"🔍 [DEBUG GUARDAR] Resultado DB: novo_id={novo_id}")
        
        if novo_id != -1:
            self.paciente_data['id'] = novo_id
            # Atualizar dados do paciente para reflexão na interface
            self.paciente_data.update(dados)
            self.setWindowTitle(dados['nome'])
            self.dirty = False
            from biodesk_styled_dialogs import BiodeskMessageBox
            BiodeskMessageBox.information(self, "Sucesso", "Utente guardado com sucesso!")
        else:
            from biodesk_styled_dialogs import BiodeskMessageBox
            BiodeskMessageBox.warning(self, "Erro", "Erro ao guardar utente.")

    @staticmethod
    def mostrar_seletor(callback, parent=None):
        """Interface modular de pesquisa de pacientes"""
        try:
            # Usar módulo especializado
            _, _, _, _, _, _, _, PesquisaPacientesManager = importar_modulos_especializados()
            PesquisaPacientesManager.mostrar_seletor(callback, parent)
            # print("✅ Pesquisa de Pacientes carregada com sucesso")
        except Exception as e:
            print(f"❌ Erro no módulo de pesquisa: {e}")
            # Fallback básico em caso de erro
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(parent, "Erro", f"Erro no sistema de pesquisa: {str(e)}")
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMenu, QHeaderView
        from PyQt6.QtCore import Qt, QPoint
        from db_manager import DBManager
        
    # ========================================================================
    # SISTEMA DE FOLLOW-UP AUTOMÁTICO - REMOVIDO
    # Código movido para comunicacao_manager.py para melhor performance de startup
    # ========================================================================
    
    def abrir_pdf_atual_externo(self):
        """Abre o PDF atual no visualizador externo padrão"""
        if hasattr(self, '_ultimo_pdf_gerado') and self._ultimo_pdf_gerado:
            try:
                from PyQt6.QtGui import QDesktopServices
                from PyQt6.QtCore import QUrl
                import os
                
                if os.path.exists(self._ultimo_pdf_gerado):
                    url = QUrl.fromLocalFile(os.path.abspath(self._ultimo_pdf_gerado))
                    QDesktopServices.openUrl(url)
                    print(f"✅ [PDF] Aberto externamente: {os.path.basename(self._ultimo_pdf_gerado)}")
                else:
                    print("❌ [PDF] Arquivo não encontrado")
                    
            except Exception as e:
                print(f"❌ [PDF] Erro ao abrir: {e}")
        else:
            print("⚠️ [PDF] Nenhum PDF disponível para abrir")

    def _is_online(self, timeout=3):
        """Verifica conectividade básica (DNS/Google) antes de tentar enviar."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            return True
        except Exception:
            return False

    def schedule_followup_consulta(self):
        """REMOVIDO: Agendamento de follow-up movido para comunicacao_manager.py"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Follow-up", 
                              "O sistema de follow-up foi integrado no Centro de Comunicação.\n"
                              "Use a aba 'Comunicação' para agendar follow-ups.")
        return

    def _show_followup_confirmation(self, tipo, when_dt):
        """Mostra uma caixa de confirmação estilizada para follow-up agendado."""
        dialog = QDialog(self)
        dialog.setWindowTitle("✅ Follow-up Agendado")
        dialog.setFixedSize(400, 200)
        dialog.setModal(True)
        
        # Centralizar
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 400) // 2
        y = (screen.height() - 200) // 2
        dialog.move(x, y)
        
        # Estilo moderno
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 2px solid #28a745;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Ícone e título
        title_layout = QHBoxLayout()
        
        icon_label = QLabel("✅")
        icon_label.setStyleSheet("""
            font-size: 32px;
            color: #28a745;
            margin-right: 10px;
        """)
        
        title_label = QLabel("Follow-up Agendado com Sucesso!")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Informações do agendamento
        tipo_display = tipo.replace('_', ' ').title()
        info_text = f"""
📧 <b>Tipo:</b> {tipo_display}
📅 <b>Data:</b> {when_dt.strftime('%d/%m/%Y')}
🕐 <b>Hora:</b> {when_dt.strftime('%H:%M')}
📋 <b>Paciente:</b> {self.paciente_data.get('nome', 'N/A')}
        """.strip()
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                color: #495057;
                line-height: 1.4;
            }
        """)
        info_label.setWordWrap(True)
        
        layout.addWidget(info_label)
        
        # Botão OK estilizado
        btn_ok = ButtonManager.entendido_button(dialog, dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def _adjust_to_business_hours(self, when_dt):
        """
        Ajusta a data/hora para horário comercial (11h-17h).
        Se estiver fora do horário, ajusta para o próximo horário válido.
        """
        from datetime import time
        
        # Extrair componentes
        target_date = when_dt.date()
        target_time = when_dt.time()
        
        # Horário comercial: 11h às 17h
        business_start = time(11, 0)
        business_end = time(17, 0)
        
        # Se está no horário comercial, manter
        if business_start <= target_time <= business_end:
            return when_dt
        
        # Se é antes das 11h, ajustar para 11h do mesmo dia
        if target_time < business_start:
            # Escolher horário aleatório entre 11h-17h
            import random
            random_hour = random.randint(11, 16)
            random_minute = random.randint(0, 59)
            new_time = time(random_hour, random_minute)
            return datetime.combine(target_date, new_time)
        
        # Se é depois das 17h, ajustar para 11h-17h do dia seguinte
        else:
            import random
            next_date = target_date + timedelta(days=1)
            random_hour = random.randint(11, 16)
            random_minute = random.randint(0, 59)
            new_time = time(random_hour, random_minute)
            return datetime.combine(next_date, new_time)

    def listar_followups_agendados(self):
        """Lista todos os follow-ups agendados e enviados para este paciente."""
        if not hasattr(self, 'scheduler') or not self.scheduler:
            QMessageBox.warning(self, "Erro", "Sistema de agendamento não disponível.")
            return
            
        paciente_id = self.paciente_data.get('id')
        if not paciente_id:
            return
            
        # Primeiro, recarregar dados do paciente da BD para ter histórico atualizado
        try:
            if hasattr(self, 'db') and self.db:
                paciente_atualizado = self.db.get_paciente_by_id(paciente_id)
                if paciente_atualizado:
                    self.paciente_data.update(paciente_atualizado)
        except Exception as e:
            print(f"⚠️ Erro ao recarregar dados do paciente: {e}")
            
        # Obter follow-ups agendados
        jobs_agendados = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith(f"followup_{paciente_id}_"):
                jobs_agendados.append({
                    'id': job.id,
                    'data': job.next_run_time,
                    'tipo': job.id.split('_')[2] if len(job.id.split('_')) > 2 else 'padrao',
                    'status': 'agendado'
                })
        
        historico_completo = self.paciente_data.get('historico', '') or ''
        followups_enviados = []
        emails_enviados = []
        
        import re
        for linha in historico_completo.split('\n'):
            # Follow-ups automáticos
            if 'follow-up automático' in linha.lower() or 'follow-up simulado' in linha.lower():
                try:
                    match = re.search(r'\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\]', linha)
                    if match:
                        data_str = match.group(1)
                        data_envio = datetime.strptime(data_str, '%d/%m/%Y %H:%M')
                        
                        # Extrair tipo do follow-up
                        tipo = 'padrao'
                        if 'primeira_consulta' in linha:
                            tipo = 'primeira_consulta'
                        elif 'tratamento' in linha:
                            tipo = 'tratamento'
                        elif 'resultado' in linha:
                            tipo = 'resultado'
                            
                        followups_enviados.append({
                            'data': data_envio,
                            'tipo': tipo,
                            'status': 'enviado',
                            'texto': linha.strip(),
                            'categoria': 'Follow-up Automático'
                        })
                except Exception:
                    continue
            
            # Outros emails enviados (templates, documentos, etc.)
            elif any(termo in linha.lower() for termo in ['email enviado', 'enviado email', 'template enviado', 'documento enviado']):
                try:
                    match = re.search(r'\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\]', linha)
                    if match:
                        data_str = match.group(1)
                        data_envio = datetime.strptime(data_str, '%d/%m/%Y %H:%M')
                        
                        # Determinar categoria do email
                        categoria = 'Email Manual'
                        if 'template' in linha.lower():
                            categoria = 'Template/Protocolo'
                        elif 'documento' in linha.lower():
                            categoria = 'Documento'
                        elif 'ficha' in linha.lower():
                            categoria = 'Ficha Paciente'
                            
                        emails_enviados.append({
                            'data': data_envio,
                            'status': 'enviado',
                            'texto': linha.strip(),
                            'categoria': categoria
                        })
                except Exception:
                    continue
        
        # Verificar se há dados para mostrar
        total_emails = len(followups_enviados) + len(emails_enviados)
        if not jobs_agendados and total_emails == 0:
            QMessageBox.information(self, "📧 Emails & Follow-ups", 
                "Não há follow-ups agendados nem emails enviados para este paciente.")
            return
            
        # Criar dialog melhorado
        dialog = QDialog(self)
        dialog.setWindowTitle("📧 Emails & Follow-ups - Histórico Completo")
        dialog.setMinimumSize(700, 500)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Info do paciente
        info_label = QLabel(f"📋 Paciente: {self.paciente_data.get('nome', 'N/A')}")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Tabs para separar diferentes tipos
        tab_widget = QTabWidget()
        
        # Tab 1: Follow-ups Agendados
        tab_agendados = QWidget()
        layout_agendados = QVBoxLayout(tab_agendados)
        
        if jobs_agendados:
            lista_agendados = QListWidget()
            for job in jobs_agendados:
                tipo_display = job['tipo'].replace('_', ' ').title()
                item_text = f"📅 {tipo_display} - {job['data'].strftime('%d/%m/%Y às %H:%M')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, job['id'])
                lista_agendados.addItem(item)
            
            layout_agendados.addWidget(lista_agendados)
            
            # Botão para cancelar
            btn_cancelar = ButtonManager.cancelar_selecionado_button(dialog, None)  # callback será definido abaixo

            def cancelar_job():
                item = lista_agendados.currentItem()
                if item:
                    job_id = item.data(Qt.ItemDataRole.UserRole)
                    try:
                        self.scheduler.remove_job(job_id)
                        lista_agendados.takeItem(lista_agendados.row(item))
                        QMessageBox.information(dialog, "✅ Sucesso", "Follow-up cancelado com sucesso.")
                        
                        # Se não há mais jobs, atualizar label
                        if lista_agendados.count() == 0:
                            lista_agendados.addItem("✅ Nenhum follow-up agendado")
                            btn_cancelar.setEnabled(False)
                            
                    except Exception as e:
                        QMessageBox.warning(dialog, "❌ Erro", f"Erro ao cancelar: {e}")
            
            btn_cancelar.clicked.connect(cancelar_job)
            layout_agendados.addWidget(btn_cancelar)
        else:
            label_vazio = QLabel("✅ Nenhum follow-up agendado para este paciente.")
            label_vazio.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
            layout_agendados.addWidget(label_vazio)
        
        # Tab 2: Follow-ups Enviados
        tab_followups = QWidget()
        layout_followups = QVBoxLayout(tab_followups)
        
        if followups_enviados:
            lista_followups = QListWidget()
            # Ordenar por data (mais recente primeiro)
            followups_enviados.sort(key=lambda x: x['data'], reverse=True)
            
            for envio in followups_enviados:
                tipo_display = envio['tipo'].replace('_', ' ').title()
                item_text = f"🤖 {tipo_display} - Enviado em {envio['data'].strftime('%d/%m/%Y às %H:%M')}"
                item = QListWidgetItem(item_text)
                item.setToolTip(envio['texto'])  # Mostrar texto completo no tooltip
                lista_followups.addItem(item)
            
            layout_followups.addWidget(lista_followups)
            
            # Label informativo
            info_followups = QLabel(f"🤖 Total de follow-ups automáticos: {len(followups_enviados)}")
            info_followups.setStyleSheet("color: #17a2b8; font-weight: bold; padding: 5px;")
            layout_followups.addWidget(info_followups)
        else:
            label_vazio = QLabel("📭 Nenhum follow-up automático foi enviado ainda.")
            label_vazio.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
            layout_followups.addWidget(label_vazio)
            
        tab_emails = QWidget()
        layout_emails = QVBoxLayout(tab_emails)
        
        if emails_enviados:
            lista_emails = QListWidget()
            # Ordenar por data (mais recente primeiro)
            emails_enviados.sort(key=lambda x: x['data'], reverse=True)
            
            # Agrupar por categoria para melhor visualização
            categorias_icons = {
                'Email Manual': '📧',
                'Template/Protocolo': '📋',
                'Documento': '📄',
                'Ficha Paciente': '👤'
            }
            
            for envio in emails_enviados:
                icon = categorias_icons.get(envio['categoria'], '📧')
                item_text = f"{icon} {envio['categoria']} - Enviado em {envio['data'].strftime('%d/%m/%Y às %H:%M')}"
                item = QListWidgetItem(item_text)
                item.setToolTip(envio['texto'])  # Mostrar texto completo no tooltip
                lista_emails.addItem(item)
            
            layout_emails.addWidget(lista_emails)
            
            # Estatísticas por categoria
            categorias_count = {}
            for envio in emails_enviados:
                cat = envio['categoria']
                categorias_count[cat] = categorias_count.get(cat, 0) + 1
            
            stats_text = "📊 Resumo: " + " • ".join([f"{cat}: {count}" for cat, count in categorias_count.items()])
            info_emails = QLabel(stats_text)
            info_emails.setStyleSheet("color: #28a745; font-weight: bold; padding: 5px; font-size: 12px;")
            info_emails.setWordWrap(True)
            layout_emails.addWidget(info_emails)
        else:
            label_vazio = QLabel("📭 Nenhum email manual foi enviado ainda.")
            label_vazio.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
            layout_emails.addWidget(label_vazio)
        
        # Adicionar tabs
        tab_widget.addTab(tab_agendados, f"📅 Agendados ({len(jobs_agendados)})")
        tab_widget.addTab(tab_followups, f"🤖 Follow-ups ({len(followups_enviados)})")
        tab_widget.addTab(tab_emails, f"📧 Outros Emails ({len(emails_enviados)})")
        
        layout.addWidget(tab_widget)
        
        # Botão fechar
        btn_fechar = ButtonManager.fechar_button(dialog, dialog.accept)
        layout.addWidget(btn_fechar)
        
        dialog.exec()

    def closeEvent(self, event):
        # Fechar scheduler se estiver ativo
        try:
            if hasattr(self, 'scheduler') and self.scheduler:
                self.scheduler.shutdown(wait=False)
        except Exception:
            pass
            
        if getattr(self, 'dirty', False):
            from biodesk_styled_dialogs import BiodeskMessageBox
            if not BiodeskMessageBox.question(
                self,
                "Alterações por guardar",
                "Existem alterações não guardadas. Deseja sair sem guardar?"
            ):
                event.ignore()
                return
        event.accept()

    def abrir_terapia(self):
        """Abre o módulo de terapia quântica com dados do paciente"""
        try:
            from terapia_quantica_window import TerapiaQuanticaWindow
            
            # Criar janela com dados do paciente
            self.terapia_window = TerapiaQuanticaWindow(paciente_data=self.paciente_data)
            self.terapia_window.show()
            
            print(f"[DEBUG] ✅ Terapia Quântica aberta para paciente: {self.paciente_data.get('nome', 'N/A')}")
            
        except ImportError as e:
            print(f"[ERRO] Módulo não encontrado: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, 'Erro', 'Módulo Terapia Quântica não encontrado.')
        except Exception as e:
            print(f"[ERRO] Erro ao abrir terapia: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, 'Erro', f'Erro ao abrir terapia quântica:\n{str(e)}')
            
    def exportar_para_terapia_quantica(self):
        """Exporta dados selecionados para o módulo de Terapia Quântica."""
        # Obter apenas as linhas selecionadas
        linhas_selecionadas = self.notas_iris.get_linhas_selecionadas()
        
        if not linhas_selecionadas:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, 'Nenhuma nota selecionada', 
                         'Selecione pelo menos uma nota para enviar para a terapia quântica.')
            return
        
        try:
            from terapia_quantica_window import TerapiaQuanticaWindow
            
            # Preparar dados das notas selecionadas para a terapia
            dados_iris = {
                'notas_selecionadas': linhas_selecionadas,
                'total_notas': len(linhas_selecionadas),
                'data_analise': self.data_atual(),
                'olho_analisado': getattr(self, 'ultimo_tipo_iris', 'esq')  # Padrão esquerdo
            }
            
            # Usar a mesma interface da versão zero
            self.terapia_window = TerapiaQuanticaWindow(
                paciente_data=self.paciente_data,
                iris_data=dados_iris
            )
            self.terapia_window.show()
            
            # Informar sobre o envio
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, 'Enviado para Terapia', 
                             f'✅ {len(linhas_selecionadas)} nota(s) enviada(s) para a terapia quântica!')
            
            print(f"[DEBUG] ✅ {len(linhas_selecionadas)} nota(s) de íris enviada(s) para terapia quântica")
                
        except ImportError as e:
            print(f"[ERRO] Módulo não encontrado: {e}")
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, "Exportar para terapia quântica", "Módulo em desenvolvimento")
        except Exception as e:
            print(f"[ERRO] Erro ao exportar para terapia: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, 'Erro', f'Erro ao exportar para terapia quântica:\n{str(e)}')

    def atualizar_status_hs3(self, conectado=False):
        """Função mantida para compatibilidade - não faz nada na interface zero"""
        pass

    def atualizar_status_sessao(self, ativa=False, info=""):
        """Função mantida para compatibilidade - não faz nada na interface zero"""
        pass

    def verificar_status_hs3_inicial(self):
        """Função mantida para compatibilidade - não faz nada na interface zero"""
        pass
    def init_tab_consentimentos(self):
        """Inicializa a aba de consentimentos"""
        layout = QVBoxLayout(self.tab_consentimentos)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ====== SUB-ABAS DENTRO DE CONSENTIMENTOS ======
        self.consentimentos_tabs = QTabWidget()
        self.consentimentos_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.consentimentos_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 12px 20px;
                margin: 2px;
                border-radius: 6px 6px 0px 0px;
                background-color: #f8f9fa;
                color: #495057;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Sub-aba 1: Consentimentos de Tratamento
        self.tab_consentimentos_tratamento = QWidget()
        self.consentimentos_tabs.addTab(self.tab_consentimentos_tratamento, '📋 Consentimentos de Tratamento')
        
        # Sub-aba 2: Declaração de Estado de Saúde - REMOVIDA PARA EVITAR DUPLICAÇÃO
        # A Declaração de Saúde está APENAS na aba "DADOS DOCUMENTOS"
        # self.tab_declaracao_saude = QWidget()
        # self.consentimentos_tabs.addTab(self.tab_declaracao_saude, '🩺 Declaração de Estado de Saúde')
        print("🚫 Sistema duplicado da Declaração de Saúde foi removido da aba CONSENTIMENTOS")
        
        # Adicionar as sub-abas ao layout principal
        layout.addWidget(self.consentimentos_tabs)
        
        # Inicializar cada sub-aba
        self.init_sub_aba_consentimentos_tratamento()

    def init_sub_aba_consentimentos_tratamento(self):
        """Inicializa a sub-aba de Consentimentos de Tratamento (conteúdo original)"""
        # Layout principal da sub-aba
        layout = QVBoxLayout(self.tab_consentimentos_tratamento)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ====== LAYOUT HORIZONTAL PRINCIPAL ======
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)  # Aumentar espaçamento entre colunas
        
        # ====== 1. ESQUERDA: PAINEL DE STATUS COMPACTO ======
        status_frame = QFrame()
        status_frame.setFixedWidth(300)  # Aumentar largura para melhor organização
        status_frame.setMinimumHeight(400)  # Garantir altura mínima adequada
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(12)  # Aumentar espaçamento entre elementos
        status_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Título da seção
        status_titulo = QLabel("📋 Status dos Consentimentos")
        status_titulo.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #2c3e50; 
            margin-bottom: 15px;
            padding: 8px;
            background-color: #e9ecef;
            border-radius: 6px;
        """)
        status_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(status_titulo)
        
        # Scroll area para os consentimentos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }

        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)  # Espaçamento adequado entre consentimentos
        scroll_layout.setContentsMargins(0, 8, 8, 8)  # Margem esquerda removida para alinhamento
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Alinhar à esquerda
        
        # Tipos de consentimento com cores pastéis elegantes (tratamento)
        tipos_consentimento = [
            ("🌿 Naturopatia", "naturopatia", "#81c784"),     # Verde suave
            ("👁️ Iridologia", "iridologia", "#4fc3f7"),      # Azul céu
            ("🦴 Osteopatia", "osteopatia", "#ffb74d"),       # Laranja suave
            ("⚡ Medicina Quântica", "quantica", "#ba68c8"),  # Roxo elegante
            ("💉 Mesoterapia", "mesoterapia", "#f06292"),     # Rosa vibrante (mudei do azul)
            ("🛡️ RGPD", "rgpd", "#90a4ae")                   # Cinza azulado
        ]
        
        self.botoes_consentimento = {}
        self.labels_status = {}
        
        for nome, tipo, cor in tipos_consentimento:
            # Cores pastéis predefinidas para cada tipo de consentimento
            cores_pastel = {
                "#81c784": "#e8f5e8",  # Verde suave para verde claro
                "#4fc3f7": "#e3f2fd",  # Azul céu para azul claro
                "#ffb74d": "#fff3e0",  # Laranja suave para laranja claro
                "#ba68c8": "#f3e5f5",  # Roxo elegante para roxo claro
                "#64b5f6": "#e3f2fd",  # Azul sereno para azul claro
                "#90a4ae": "#f5f5f5"   # Cinza azulado para cinza claro
            }
            
            cor_pastel = cores_pastel.get(cor, "#f5f5f5")
            
            # Container para botão + status
            item_widget = QWidget()
            item_widget.setFixedHeight(60)  # Altura compacta
            item_widget.setStyleSheet("background-color: transparent;")  # Remover fundo branco
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 5, 5, 5)
            item_layout.setSpacing(2)
            
            # Botão principal - ESTILO IGUAL AOS TEMPLATES
            if BIODESK_STYLES_AVAILABLE:
                btn = BiodeskStyles.create_button(nome, ButtonType.DEFAULT)
                btn.setCheckable(True)
            else:
                btn = QPushButton(nome)
                btn.setCheckable(True)
                btn.setFixedHeight(45)  # Altura igual aos templates
            
            btn.clicked.connect(lambda checked, t=tipo: self.selecionar_tipo_consentimento(t))
            self.botoes_consentimento[tipo] = btn
            item_layout.addWidget(btn)
            
            # Label de status (menor)
            status_label = QLabel("❌ Não assinado")
            status_label.setStyleSheet("""
                font-size: 10px;
                color: #666;
                padding-left: 8px;
                margin: 0;
            """)
            self.labels_status[tipo] = status_label
            item_layout.addWidget(status_label)
            
            scroll_layout.addWidget(item_widget)
        
        # Adicionar stretch ao final
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        status_layout.addWidget(scroll_area)
        
        main_horizontal_layout.addWidget(status_frame)
        
        # ====== 2. CENTRO: ÁREA GRANDE DE TEXTO ======
        centro_frame = QFrame()
        centro_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        centro_layout = QVBoxLayout(centro_frame)
        centro_layout.setContentsMargins(15, 15, 15, 15)
        centro_layout.setSpacing(10)
        
        # Cabeçalho do centro
        header_centro = QFrame()
        header_centro.setFixedHeight(85)  # Aumentar altura para o texto ficar ainda mais visível
        header_centro.setStyleSheet("""
            QFrame {
                background-color: #2980b9;
                border-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_centro)
        
        self.label_tipo_atual = QLabel("👈 Selecione um tipo de consentimento")
        self.label_tipo_atual.setStyleSheet("""
            font-size: 16px; 
            font-weight: 700; 
            color: #ffffff;
            padding: 20px 15px;
        """)
        header_layout.addWidget(self.label_tipo_atual)
        
        header_layout.addStretch()
        
        self.label_data_consentimento = QLabel(f"📅 {self.data_atual()}")
        self.label_data_consentimento.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600;
            color: #ffffff;
            padding: 15px;
        """)
        header_layout.addWidget(self.label_data_consentimento)
        
        centro_layout.addWidget(header_centro)
        
        # Mensagem inicial (quando nenhum tipo está selecionado)
        self.mensagem_inicial = QLabel("👈 Selecione um tipo de consentimento")
        self.mensagem_inicial.setStyleSheet("""
            font-size: 18px;
            color: #7f8c8d;
            padding: 80px;
            border: 2px dashed #bdc3c7;
            border-radius: 10px;
            background-color: #f8f9fa;
        """)
        self.mensagem_inicial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        centro_layout.addWidget(self.mensagem_inicial)
        
        # Editor de texto principal com altura controlada
        self.editor_consentimento = QTextEdit()
        self.editor_consentimento.setMinimumHeight(300)  # Altura aumentada
        self.editor_consentimento.setMaximumHeight(400)  # Altura máxima aumentada
        # Aplicar estilo básico
        self.editor_consentimento.setStyleSheet("QTextEdit { border: 2px solid #e0e0e0; border-radius: 8px; padding: 12px; font-size: 14px; background-color: white; }")
        self.editor_consentimento.setPlaceholderText("Selecione um tipo de consentimento para editar o texto...")
        self.editor_consentimento.setVisible(False)  # Inicialmente oculto
        centro_layout.addWidget(self.editor_consentimento)
        
        # ====== BOTÕES DE ASSINATURA COMPACTOS ======
        assinaturas_layout = QHBoxLayout()
        assinaturas_layout.setContentsMargins(20, 15, 20, 15)
        assinaturas_layout.setSpacing(25)
        
        # Espaçador esquerdo
        assinaturas_layout.addStretch()
        
        # Botão Paciente - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            self.assinatura_paciente = BiodeskStyles.create_button("📝 Paciente", ButtonType.DIALOG)
        else:
            self.assinatura_paciente = QPushButton("📝 Paciente")
            self.assinatura_paciente.setFixedSize(140, 45)
            self.assinatura_paciente.setStyleSheet("""
                QPushButton {
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                    background-color: #e3f2fd;
                    font-size: 12px;
                    color: #1976d2;
                    font-weight: 600;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                    border-color: #1976d2;
                }
                QPushButton:pressed {
                    background-color: #90caf9;
                    border-color: #0d47a1;
                }
            """)
        self.assinatura_paciente.clicked.connect(self.abrir_assinatura_paciente_click)
        assinaturas_layout.addWidget(self.assinatura_paciente)
        
        # Botão Terapeuta - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            self.assinatura_terapeuta = BiodeskStyles.create_button("👨‍⚕️ Terapeuta", ButtonType.SAVE)
        else:
            self.assinatura_terapeuta = QPushButton("👨‍⚕️ Terapeuta")
            self.assinatura_terapeuta.setFixedSize(140, 45)
            self.assinatura_terapeuta.setStyleSheet("""
                QPushButton {
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    background-color: #e8f5e8;
                    font-size: 12px;
                    color: #2e7d32;
                    font-weight: 600;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #c8e6c9;
                    border-color: #388e3c;
                }
                QPushButton:pressed {
                    background-color: #a5d6a7;
                    border-color: #1b5e20;
                }
            """)
        self.assinatura_terapeuta.clicked.connect(self.abrir_assinatura_terapeuta_click)
        assinaturas_layout.addWidget(self.assinatura_terapeuta)
        
        # Espaçador direito
        assinaturas_layout.addStretch()
        
        # Adicionar layout de assinaturas ao centro
        centro_layout.addLayout(assinaturas_layout)

        main_horizontal_layout.addWidget(centro_frame, 1)  # Expandir no centro        # ====== 3. DIREITA: BOTÕES DE AÇÃO ======
        acoes_frame = QFrame()
        # Remover largura fixa para que se estenda até quase o limite da tela
        acoes_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        acoes_layout = QVBoxLayout(acoes_frame)
        acoes_layout.setSpacing(15)  # Aumentar espaçamento vertical
        acoes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Título das ações
        acoes_titulo = QLabel("⚡ Ações")
        acoes_titulo.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600; 
            color: #2c3e50; 
            margin-bottom: 15px;
            padding: 12px;
            background-color: #e9ecef;
            border-radius: 6px;
        """)
        acoes_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        acoes_layout.addWidget(acoes_titulo)
        
        # Layout horizontal para os botões (em linha)
        botoes_linha1 = QHBoxLayout()
        botoes_linha1.setSpacing(10)
        
        # Botões de ação (mais largos devido ao espaço disponível)
        if BIODESK_STYLES_AVAILABLE:
            btn_imprimir = BiodeskStyles.create_button("🖨️ Imprimir", ButtonType.TOOL)
        else:
            btn_imprimir = QPushButton("🖨️\nImprimir")
            btn_imprimir.setFixedSize(100, 60)  # Reduzir largura
            self._style_modern_button(btn_imprimir, "#ff9800")
        btn_imprimir.clicked.connect(self.imprimir_consentimento)
        botoes_linha1.addWidget(btn_imprimir)
        
        if BIODESK_STYLES_AVAILABLE:
            btn_pdf = BiodeskStyles.create_button("📄 PDF", ButtonType.TOOL)
        else:
            btn_pdf = QPushButton("📄\nPDF")
            btn_pdf.setFixedSize(100, 60)  # Reduzir largura
            self._style_modern_button(btn_pdf, "#3498db")
        btn_pdf.clicked.connect(self.gerar_pdf_consentimento)
        botoes_linha1.addWidget(btn_pdf)
        
        acoes_layout.addLayout(botoes_linha1)
        
        # Segunda linha de botões
        botoes_linha2 = QHBoxLayout()
        botoes_linha2.setSpacing(10)
        
        if BIODESK_STYLES_AVAILABLE:
            btn_guardar = BiodeskStyles.create_button("💾 Guardar", ButtonType.SAVE)
        else:
            btn_guardar = QPushButton("💾\nGuardar")
            btn_guardar.setFixedSize(100, 60)  # Reduzir largura
            self._style_modern_button(btn_guardar, "#27ae60")
        btn_guardar.clicked.connect(self.guardar_consentimento)
        botoes_linha2.addWidget(btn_guardar)
        
        if BIODESK_STYLES_AVAILABLE:
            btn_limpar = BiodeskStyles.create_button("🗑️ Limpar", ButtonType.DELETE)
        else:
            btn_limpar = QPushButton("🗑️\nLimpar")
            btn_limpar.setFixedSize(100, 60)  # Reduzir largura
            self._style_modern_button(btn_limpar, "#e74c3c")
        btn_limpar.clicked.connect(self.limpar_consentimento)
        botoes_linha2.addWidget(btn_limpar)
        
        acoes_layout.addLayout(botoes_linha2)
        
        # Botão de histórico centralizado
        if BIODESK_STYLES_AVAILABLE:
            btn_historico = BiodeskStyles.create_button("📋 Histórico", ButtonType.NAVIGATION)
        else:
            btn_historico = QPushButton("📋 Histórico")
            btn_historico.setFixedSize(210, 50)  # Mais largo para ocupar as duas colunas
            self._style_modern_button(btn_historico, "#9b59b6")
        btn_historico.clicked.connect(self.mostrar_historico_consentimentos)
        acoes_layout.addWidget(btn_historico)
        
        # Botão moderno para assinatura externa
        if BIODESK_STYLES_AVAILABLE:
            btn_assinatura_externa = BiodeskStyles.create_button("📝 Assinar PDF Externamente", ButtonType.TOOL)
        else:
            btn_assinatura_externa = QPushButton("📝 Assinar PDF Externamente")
            btn_assinatura_externa.setFixedSize(210, 50)
        btn_assinatura_externa.clicked.connect(self.gerar_pdf_para_assinatura_externa)
        acoes_layout.addWidget(btn_assinatura_externa)
        
        # Botão de importação manual (para casos onde a automação falha)
        if BIODESK_STYLES_AVAILABLE:
            btn_importar_manual_consent = BiodeskStyles.create_button("📁 Importar Assinado", ButtonType.TOOL)
        else:
            btn_importar_manual_consent = QPushButton("📁 Importar Assinado")
            btn_importar_manual_consent.setFixedSize(210, 35)
        btn_importar_manual_consent.clicked.connect(self.importar_pdf_manual)
        acoes_layout.addWidget(btn_importar_manual_consent)
        
        # Botão de anular consentimento
        if BIODESK_STYLES_AVAILABLE:
            self.btn_anular = BiodeskStyles.create_button("🗑️ Anular", ButtonType.DELETE)
        else:
            self.btn_anular = QPushButton("🗑️ Anular")
            self.btn_anular.setFixedSize(210, 50)
            self._style_modern_button(self.btn_anular, "#6c757d")
        self.btn_anular.clicked.connect(self.anular_consentimento_click)
        self.btn_anular.setVisible(False)  # Inicialmente oculto
        acoes_layout.addWidget(self.btn_anular)
        
        acoes_layout.addStretch()
        main_horizontal_layout.addWidget(acoes_frame)
        
        # Pequena margem direita para não ir até o extremo
        main_horizontal_layout.addSpacing(20)
        
        # Adicionar layout horizontal ao layout principal
        layout.addLayout(main_horizontal_layout, 1)
        
        # Carregar status dos consentimentos
        self.carregar_status_consentimentos()
        
        # Atualizar informações do paciente
        self.atualizar_info_paciente_consentimento()

    def carregar_status_consentimentos(self):
        """Carrega e atualiza o status visual dos consentimentos"""
        try:
            from consentimentos_manager import ConsentimentosManager
            
            # Verificar se temos ID do paciente
            paciente_id = self.paciente_data.get('id')
            if not paciente_id:
                return
            
            manager = ConsentimentosManager()
            status_dict = manager.obter_status_consentimentos(paciente_id)
            
            # Atualizar labels de status
            for tipo, info in status_dict.items():
                if tipo in self.labels_status:
                    status = info.get('status', 'nao_assinado')
                    data = info.get('data')
                    data_anulacao = info.get('data_anulacao')
                    
                    if status == 'assinado':
                        emoji = "✅"
                        texto = f"✅ {data}"
                        cor = "#27ae60"
                    elif status == 'anulado':
                        emoji = "🗑️"
                        texto = f"🗑️ Anulado {data_anulacao}"
                        cor = "#e74c3c"
                    else:
                        emoji = "❌"
                        texto = "❌ Não assinado"
                        cor = "#6c757d"
                    
                    self.labels_status[tipo].setText(texto)
                    self.labels_status[tipo].setStyleSheet(f"""
                        font-size: 10px;
                        color: {cor};
                        padding-left: 8px;
                        margin: 0;
                        font-weight: 500;
                    """)

        except Exception as e:
            # Manter status padrão em caso de erro
            pass

    def atualizar_historico_consentimentos(self):
        """Atualiza a lista de histórico de consentimentos"""
        # Por agora, exemplo estático
        if hasattr(self, 'lista_historico'):
            self.lista_historico.clear()
            self.lista_historico.addItem("📋 Consentimento Naturopatia - 01/08/2023")
            self.lista_historico.addItem("👁️ Consentimento Iridologia - 15/07/2023")

    def selecionar_tipo_consentimento(self, tipo):
        """Seleciona um tipo de consentimento e carrega o template correspondente"""
        
        # Desmarcar outros botões e marcar o atual
        for t, btn in self.botoes_consentimento.items():
            btn.setChecked(t == tipo)
        
        # Atualizar label do tipo atual
        tipos_nomes = {
            'naturopatia': '🌿 Naturopatia',
            'osteopatia': '🦴 Osteopatia',
            'iridologia': '👁️ Iridologia',
            'quantica': '⚡ Medicina Quântica', 
            'mesoterapia': '💉 Mesoterapia Homeopática',
            'rgpd': '🛡️ RGPD'
        }
        
        nome_tipo = tipos_nomes.get(tipo, tipo.title())
        self.label_tipo_atual.setText(nome_tipo)
        
        # Carregar template do consentimento com substituição automática
        template = self.obter_template_consentimento(tipo)
        template_preenchido = self.substituir_variaveis_template(template)
        self.editor_consentimento.setHtml(template_preenchido)
        
        # Guardar tipo atual
        self.tipo_consentimento_atual = tipo
        
        # VERIFICAR SE JÁ EXISTE CONSENTIMENTO ASSINADO PARA ESTE TIPO
        self.verificar_assinaturas_existentes(tipo)
        
        # MOSTRAR a área de edição e OCULTAR mensagem inicial
        self.mensagem_inicial.setVisible(False)
        self.editor_consentimento.setVisible(True)
        
        # MOSTRAR botão de anulação no painel lateral (apenas se consentimento já foi assinado)
        from consentimentos_manager import ConsentimentosManager
        paciente_id = self.paciente_data.get('id')
        if paciente_id:
            manager = ConsentimentosManager()
            status_dict = manager.obter_status_consentimentos(paciente_id)
            if tipo in status_dict and status_dict[tipo].get('status') == 'assinado':
                self.btn_anular.setVisible(True)
            else:
                self.btn_anular.setVisible(False)
        else:
            self.btn_anular.setVisible(False)

    def verificar_assinaturas_existentes(self, tipo):
        """Verifica se já existem assinaturas para este tipo de consentimento"""
        try:
            if not hasattr(self, 'paciente_data') or not self.paciente_data.get('id'):
                # Reset para estado inicial se não há paciente
                self.resetar_botoes_assinatura()
                return
            
            from consentimentos_manager import ConsentimentosManager
            manager = ConsentimentosManager()
            
            # Obter o consentimento mais recente deste tipo para este paciente usando DatabaseService
            paciente_id = self.paciente_data['id']
            
            try:
                from ficha_paciente.services.database_service import DatabaseService
                
                # Buscar consentimento usando DatabaseService
                consentimento = DatabaseService.buscar_consentimento_recente(paciente_id, tipo)
                
                if consentimento:
                    # Verificar se o consentimento não foi anulado
                    if consentimento['status'] == 'anulado':
                        # Consentimento foi anulado - resetar botões
                        self.consentimento_ativo = None
                        self.resetar_botoes_assinatura()
                        print(f"[DEBUG] ℹ️ Consentimento {tipo} foi anulado - resetando botões")
                        return
                    
                    # Armazenar consentimento ativo para usar nas assinaturas
                    self.consentimento_ativo = {'id': consentimento['id'], 'tipo': tipo}
                    
                    # Verificar e atualizar botão do paciente
                    assinatura_paciente = consentimento['assinatura_paciente']
                    if assinatura_paciente and len(assinatura_paciente) > 0:
                        self.assinatura_paciente.setText("✅ Assinado")
                        self.assinatura_paciente.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #27ae60;
                                border-radius: 8px;
                                background-color: #d4edda;
                                font-size: 12px;
                                color: #155724;
                                font-weight: bold;
                                padding: 8px;
                            }
                            QPushButton:hover {
                                background-color: #c3e6cb;
                            }
                        """)
                        print(f"[DEBUG] ✅ Assinatura do paciente encontrada para {tipo}")
                    else:
                        self.resetar_botao_paciente()
                    
                    # Verificar e atualizar botão do terapeuta
                    assinatura_terapeuta = consentimento['assinatura_terapeuta']
                    if assinatura_terapeuta and len(assinatura_terapeuta) > 0:
                        self.assinatura_terapeuta.setText("✅ Assinado")
                        self.assinatura_terapeuta.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #27ae60;
                                border-radius: 8px;
                                background-color: #d4edda;
                                font-size: 12px;
                                color: #155724;
                                font-weight: bold;
                                padding: 8px;
                            }
                            QPushButton:hover {
                                background-color: #c3e6cb;
                            }
                        """)
                        print(f"[DEBUG] ✅ Assinatura do terapeuta encontrada para {tipo}")
                    else:
                        self.resetar_botao_terapeuta()
                else:
                    # Não há consentimento deste tipo - resetar botões
                    self.consentimento_ativo = None
                    self.resetar_botoes_assinatura()
                    print(f"[DEBUG] ℹ️ Nenhum consentimento {tipo} encontrado para este paciente")
                    
            except ImportError:
                print(f"[AVISO] DatabaseService não encontrado, usando fallback")
                self.resetar_botoes_assinatura()
            except Exception as e:
                print(f"[ERRO] Erro ao buscar consentimento: {e}")
                self.resetar_botoes_assinatura()
                
        except Exception as e:
            print(f"[ERRO] Erro ao verificar assinaturas existentes: {e}")
            self.resetar_botoes_assinatura()

    def resetar_botoes_assinatura(self):
        """Reset dos botões de assinatura para estado inicial"""
        self.resetar_botao_paciente()
        self.resetar_botao_terapeuta()
        
        # Resetar também as assinaturas capturadas
        self.assinatura_paciente_data = None
        self.assinatura_terapeuta_data = None
        print("🔄 [ASSINATURA] Assinaturas resetadas")
        
    def resetar_botao_paciente(self):
        """Reset do botão de assinatura do paciente"""
        self.assinatura_paciente.setText("📝 Paciente")
        self.assinatura_paciente.setStyleSheet("""
            QPushButton {
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: #e3f2fd;
                font-size: 12px;
                color: #1976d2;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
                border-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #90caf9;
                border-color: #0d47a1;
            }
        """)
        
    def resetar_botao_terapeuta(self):
        """Reset do botão de assinatura do terapeuta"""
        self.assinatura_terapeuta.setText("👨‍⚕️ Terapeuta")
        self.assinatura_terapeuta.setStyleSheet("""
            QPushButton {
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #e8f5e8;
                font-size: 12px;
                color: #2e7d32;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
                border-color: #388e3c;
            }
            QPushButton:pressed {
                background-color: #a5d6a7;
                border-color: #1b5e20;
            }
        """)

    def substituir_variaveis_template(self, template_html):
        """Substitui automaticamente variáveis no template com dados do paciente"""
        from datetime import datetime
        
        # Obter dados do paciente
        nome_paciente = self.paciente_data.get('nome', '[NOME DO PACIENTE]')
        data_nascimento = self.paciente_data.get('data_nascimento', '[DATA DE NASCIMENTO]')
        contacto = self.paciente_data.get('contacto', '[CONTACTO]')
        email = self.paciente_data.get('email', '[EMAIL]')
        data_atual = datetime.now().strftime('%d/%m/%Y')
        idade = self.calcular_idade()
        
        # Dicionário de substituições
        substituicoes = {
            '{nome_paciente}': nome_paciente,
            '{NOME_PACIENTE}': nome_paciente,
            '{{NOME_PACIENTE}}': nome_paciente,
            '[NOME_PACIENTE]': nome_paciente,
            
            '{data_nascimento}': data_nascimento,
            '{DATA_NASCIMENTO}': data_nascimento,
            '{{DATA_NASCIMENTO}}': data_nascimento,
            '[DATA_NASCIMENTO]': data_nascimento,
            
            '{contacto}': contacto,
            '{CONTACTO}': contacto,
            '{{CONTACTO}}': contacto,
            '[CONTACTO]': contacto,
            
            '{email}': email,
            '{EMAIL}': email,
            '{{EMAIL}}': email,
            '[EMAIL]': email,
            
            '{data_atual}': data_atual,
            '{DATA_ATUAL}': data_atual,
            '{{DATA_ATUAL}}': data_atual,
            '[DATA_ATUAL]': data_atual,
            
            '{idade}': str(idade),
            '{IDADE}': str(idade),
            '{{IDADE}}': str(idade),
            '[IDADE]': str(idade),
            
            # Placeholders comuns
            '________________________________': nome_paciente,
            '__________': data_atual,
            '___________': data_atual,
        }
        
        # Aplicar todas as substituições
        template_preenchido = template_html
        for placeholder, valor in substituicoes.items():
            template_preenchido = template_preenchido.replace(placeholder, valor)
        
        return template_preenchido

            
