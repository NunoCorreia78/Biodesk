
# ⚡ IMPORTS OTIMIZADOS - APENAS O ESSENCIAL NO STARTUP
from pathlib import Path

# PyQt6 - APENAS o básico para definir classes
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit, QPushButton, QScrollArea, QFrame, QFileDialog, QApplication, QDialog, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QShortcut, QKeySequence

# Imports essenciais para a classe principal
from db_manager import DBManager
from sistema_assinatura import abrir_dialogo_assinatura

# LAZY IMPORTS para módulos especializados com CACHE OTIMIZADO
_modulos_cache = {}
_import_stats = {'hits': 0, 'misses': 0, 'tempo_total': 0}

def importar_modulos_especializados():
    """Importa módulos especializados apenas quando necessário - COM CACHE OTIMIZADO"""
    import time
    start_time = time.time()
    
    if not _modulos_cache:
        _import_stats['misses'] += 1
        try:
            from ficha_paciente.dados_pessoais import DadosPessoaisWidget
            from ficha_paciente.historico_clinico import HistoricoClinicoWidget  
            from ficha_paciente.templates_manager import TemplatesManagerWidget
            from ficha_paciente.comunicacao_manager import ComunicacaoManagerWidget
            from ficha_paciente.gestao_documentos import GestaoDocumentosWidget
            from ficha_paciente.declaracao_saude import DeclaracaoSaudeWidget
            # Consentimentos integrados na declaração de saúde - módulo separado não necessário
            from ficha_paciente.pesquisa_pacientes import PesquisaPacientesManager
            
            _modulos_cache.update({
                'dados_pessoais': DadosPessoaisWidget,
                'historico_clinico': HistoricoClinicoWidget,
                'templates_manager': TemplatesManagerWidget,
                'comunicacao_manager': ComunicacaoManagerWidget,
                'gestao_documentos': GestaoDocumentosWidget,
                'declaracao_saude': DeclaracaoSaudeWidget,
                # 'consentimentos': ConsentimentosWidget,  # Não necessário - integrado na declaração
                'pesquisa_pacientes': PesquisaPacientesManager
            })
            import_time = time.time() - start_time
            _import_stats['tempo_total'] += import_time
            print(f"✅ Módulos especializados carregados no cache em {import_time:.3f}s")
        except ImportError as e:
            print(f"⚠️ Erro ao carregar módulo: {e}")
    else:
        _import_stats['hits'] += 1
        
    return (_modulos_cache.get('dados_pessoais'), _modulos_cache.get('historico_clinico'), 
            _modulos_cache.get('templates_manager'), _modulos_cache.get('comunicacao_manager'),
            _modulos_cache.get('gestao_documentos'), _modulos_cache.get('declaracao_saude'),
            None, _modulos_cache.get('pesquisa_pacientes'))  # consentimentos=None (integrado)

def obter_estatisticas_cache():
    """Retorna estatísticas do cache de módulos"""
    return {
        'modulos_em_cache': len(_modulos_cache),
        'cache_hits': _import_stats['hits'],
        'cache_misses': _import_stats['misses'],
        'tempo_total_imports': _import_stats['tempo_total'],
        'eficiencia_cache': (_import_stats['hits'] / max(1, _import_stats['hits'] + _import_stats['misses'])) * 100
    }

class FichaPaciente(QMainWindow):
    def __init__(self, paciente_data=None, parent=None):
        # 🚫 RADICAL ANTI-FLICKERING: Inicialização MÍNIMA
        super().__init__(parent)
        
        # APENAS o essencial durante __init__
        # ✅ USAR DADOS FORNECIDOS OU CRIAR FICHA VAZIA
        self.paciente_data = paciente_data or {}
        self.dirty = False
        
        # ✅ USAR SINGLETON DO DBMANAGER para melhor performance
        self.db = DBManager.get_instance()
        
        # Flags de controle para lazy loading
        self._pdf_viewer_initialized = False
        self._webengine_available = None
        self._initialized = False
        
        # 🚀 CARREGAMENTO IMEDIATO: Carregar dados pessoais na inicialização
        self._tabs_loaded = {
            'dados_pessoais': False,  # Será carregado imediatamente
            'dados_documentos': False,
            'clinico_comunicacao': False,
            'historico_clinico': False,
            'templates_prescricoes': False,
            'centro_comunicacao': False,
            'iris_analise': False,
            'gestao_documentos': False,
            'declaracao_saude': False,
            # 'consentimentos': False,  # Integrado na declaração de saúde
            'terapia': False
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
            
            # Apenas carregar dados essenciais - tabs serão carregados sob demanda
            print(f"✅ Dados básicos carregados para: {nome}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
        finally:
            # Limpar flag de carregamento
            self._carregando_dados = False
    
    def _finalize_startup(self):
        """Finaliza a inicialização com monitoramento de performance"""
        import time
        
        # Marcar inicialização como completa
        self._initialized = True
        
        # Gerar relatório de startup
        relatorio = self.obter_relatorio_performance()
        
        print("🎯 === RELATÓRIO DE STARTUP OTIMIZADO ===")
        print(f"📊 Lazy Loading: {relatorio['lazy_loading']['tabs_carregados']} tabs carregados")
        print(f"💾 Cache Eficiência: {relatorio['cache_modulos']['eficiencia_cache']:.1f}%")
        print(f"🔒 Locks Ativos: {relatorio['lazy_loading']['locks_ativos']}")
        print(f"🚀 Sistema pronto para uso em alta performance!")
        print("=" * 45)
    
    # ====== CALLBACKS PARA MÓDULOS ESPECIALIZADOS ======
    def on_template_selecionado(self, template_data):
        """Callback quando template é selecionado no módulo especializado"""
        print(f"📄 Template selecionado: {template_data.get('nome', 'N/A')}")
    
    def on_followup_agendado(self, tipo_followup, dias):
        """Callback quando follow-up é agendado no módulo de comunicação"""
        print(f"📅 Follow-up agendado: {tipo_followup} em {dias} dias")
    
    def on_protocolo_adicionado(self, protocolo):
        """Callback quando protocolo é adicionado no módulo de templates"""
        print(f"📋 Protocolo adicionado: {protocolo}")
    
    def on_template_gerado(self, template_data):
        """Callback quando template é gerado no módulo de templates"""
        print(f"📄 Template gerado: {template_data.get('nome', 'N/A')}")
    
    def data_atual(self):
        """Retorna a data atual formatada"""
        from datetime import datetime
        return datetime.now().strftime('%d/%m/%Y')
    
    def selecionar_imagem_galeria(self, img):
        """Seleciona a imagem da galeria visual, atualiza canvas e aplica destaque visual"""
        if not img:
            return
        # Atualizar canvas
        if hasattr(self, 'iris_canvas'):
            caminho = img.get('caminho_imagem', '') or img.get('caminho', '')
            tipo = img.get('tipo', None)
            self.iris_canvas.set_image(caminho, tipo)
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
                        print(f"🔄 [DATA] Atualizando dados do paciente: {dados_atualizados.get('nome')}")
                        self.paciente_data = dados_atualizados
                        self.update_ui_with_new_data()
                        
        except Exception as e:
            print(f"⚠️ [DATA] Erro na atualização automática: {e}")

    def update_ui_with_new_data(self):
        """Atualiza interface com novos dados do paciente"""
        try:
            # Atualizar email na aba de comunicação
            if hasattr(self, 'carregar_dados_paciente_email'):
                self.carregar_dados_paciente_email()
            
            # Atualizar dados na declaração de saúde
            if hasattr(self, 'carregar_dados_paciente_declaracao'):
                self.carregar_dados_paciente_declaracao()
            
            # Atualizar título da janela
            if self.paciente_data.get('nome'):
                self.setWindowTitle(f"📋 Ficha do Paciente - {self.paciente_data.get('nome')}")
            
            print("✅ [DATA] Interface atualizada com novos dados")
            
        except Exception as e:
            print(f"❌ [DATA] Erro ao atualizar interface: {e}")
    
    def obter_relatorio_performance(self):
        """Gera relatório detalhado de performance do sistema lazy loading"""
        try:
            stats = obter_estatisticas_cache()
            tabs_carregados = sum(1 for loaded in self._tabs_loaded.values() if loaded)
            total_tabs = len(self._tabs_loaded)
            
            relatorio = {
                'lazy_loading': {
                    'tabs_carregados': f"{tabs_carregados}/{total_tabs}",
                    'percentual_nao_carregado': f"{((total_tabs - tabs_carregados) / total_tabs) * 100:.1f}%",
                    'locks_ativos': len(self._loading_locks),
                    'estado_tabs': self._tabs_loaded.copy()
                },
                'cache_modulos': stats,
                'memoria': {
                    'singleton_db': hasattr(self, 'db') and self.db is not None,
                    'flags_carregamento': bool(getattr(self, '_carregando_dados', False))
                }
            }
            
            return relatorio
            
        except Exception as e:
            return {'erro': f"Erro ao gerar relatório: {e}"}
    
    def resetar_tabs_para_teste(self):
        """MÉTODO DE DESENVOLVIMENTO: Reseta flags para testar lazy loading"""
        if hasattr(self, '_development_mode') and self._development_mode:
            # Resetar todos os flags (exceto os já carregados)
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
        
        # ====== NOVA ESTRUTURA: APENAS 2 SEPARADORES ======
        self.tabs = QTabWidget()
        self.tab_dados_documentos = QWidget()
        self.tab_clinico_comunicacao = QWidget()
        
        self.tabs.addTab(self.tab_dados_documentos, '� DOCUMENTAÇÃO CLÍNICA')
        self.tabs.addTab(self.tab_clinico_comunicacao, '🩺 ÁREA CLÍNICA')
        
        main_layout.addWidget(self.tabs)
        
    # ====== LAZY LOADING CALLBACKS OTIMIZADOS ======
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
            
            if index == 0 and not self._tabs_loaded.get('dados_documentos', False):
                print("🔄 Carregando tab DADOS & DOCUMENTOS...")
                self.init_tab_dados_documentos()
                self._tabs_loaded['dados_documentos'] = True
                
            elif index == 1 and not self._tabs_loaded.get('clinico_comunicacao', False):
                print("🔄 Carregando tab CLÍNICO & COMUNICAÇÃO...")
                self.init_tab_clinico_comunicacao()
                self._tabs_loaded['clinico_comunicacao'] = True
                # Nota: Histórico clínico será carregado automaticamente pelo init_tab_clinico_comunicacao
            
            load_time = time.time() - start_time
            if load_time > 0.1:  # Só reportar se demorar mais de 100ms
                print(f"⏱️ Tab principal carregado em {load_time:.2f}s")
                
        finally:
            self._loading_locks.discard(lock_key)

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
                
            elif index == 2 and not self._tabs_loaded.get('gestao_documentos', False):
                self.init_sub_gestao_documentos_modular()
                self._tabs_loaded['gestao_documentos'] = True
                
        except Exception as e:
            pass  # Erro não crítico

    def _on_tab_clinico_changed(self, index):
        """Carrega sub-tabs clínicos sob demanda"""
        import time
        start_time = time.time()
        
        try:
            if index == 0 and not self._tabs_loaded.get('historico_clinico', False):
                print("🔄 Carregando HISTÓRICO CLÍNICO...")
                self.init_sub_historico_clinico()
                self._tabs_loaded['historico_clinico'] = True
                
            elif index == 1 and not self._tabs_loaded.get('iris_analise', False):
                print("🔄 Carregando ANÁLISE DE ÍRIS...")
                self.init_sub_iris_analise()
                self._tabs_loaded['iris_analise'] = True
                
            elif index == 2 and not self._tabs_loaded.get('templates_prescricoes', False):
                print("🔄 Carregando TEMPLATES & PRESCRIÇÕES...")
                self.init_sub_templates_prescricoes()
                self._tabs_loaded['templates_prescricoes'] = True
                
            elif index == 3 and not self._tabs_loaded.get('centro_comunicacao', False):
                print("🔄 Carregando CENTRO DE COMUNICAÇÃO...")
                self.init_sub_centro_comunicacao()
                self._tabs_loaded['centro_comunicacao'] = True
                
            load_time = time.time() - start_time
            if load_time > 0.1:
                print(f"⏱️ Sub-tab clínico carregado em {load_time:.2f}s")
                
        except Exception as e:
            print(f"❌ Erro ao carregar sub-tab clínico: {e}")

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
        
        # ====== NOVA ESTRUTURA: APENAS 2 SEPARADORES ======
        self.tabs = QTabWidget()
        self.tab_dados_documentos = QWidget()
        self.tab_clinico_comunicacao = QWidget()
        
        self.tabs.addTab(self.tab_dados_documentos, '📋 DOCUMENTAÇÃO CLÍNICA')
        self.tabs.addTab(self.tab_clinico_comunicacao, '🩺 ÁREA CLÍNICA')
        
        main_layout.addWidget(self.tabs)
        
        # Conectar sinal para lazy loading das outras abas
        self.tabs.currentChanged.connect(self._on_main_tab_changed)
        
        # 🚀 CARREGAMENTO IMEDIATO: Inicializar primeira aba imediatamente
        self.init_tab_dados_documentos()
        self._tabs_loaded['dados_documentos'] = True
        
        # 🚀 LAZY LOADING: Conectar sinal para carregar tabs principais sob demanda
        self.tabs.currentChanged.connect(self._on_main_tab_changed)
        
        # Atalho Ctrl+S
        shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut.activated.connect(self.guardar)
        
        # 🚀 LAZY LOADING: NÃO inicializar tabs principais - carregar o primeiro sob demanda
        print("✅ Interface principal criada - lazy loading ativado")
        
        # Carregar apenas o primeiro tab por padrão
        self._on_main_tab_changed(0)

    def init_tab_dados_documentos(self):
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
        self.sub_gestao_documentos = QWidget()
        
        self.dados_documentos_tabs.addTab(self.sub_dados_pessoais, '👤 Dados Pessoais')
        self.dados_documentos_tabs.addTab(self.sub_declaracao_saude, '🩺 Declaração de Saúde')
        self.dados_documentos_tabs.addTab(self.sub_gestao_documentos, '� Gestão de Documentos')
        
        # 🚀 CARREGAMENTO IMEDIATO: Conectar sinal para carregar sub-tabs sob demanda  
        self.dados_documentos_tabs.currentChanged.connect(self._on_dados_tab_changed)
        
        main_layout.addWidget(self.dados_documentos_tabs)
        
        # 🚀 CARREGAMENTO IMEDIATO: Carregar dados pessoais na inicialização
        self.init_sub_dados_pessoais()
        self._tabs_loaded['dados_pessoais'] = True

    def init_tab_clinico_comunicacao(self):
        """
        🩺 ÁREA CLÍNICA
        - Histórico Clínico
        - Análise de Íris
        - Modelos de Prescrição
        - Email
        """
        main_layout = QVBoxLayout(self.tab_clinico_comunicacao)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ====== SUB-ABAS DENTRO DE CLÍNICO & COMUNICAÇÃO ======
        self.clinico_comunicacao_tabs = QTabWidget()
        self.clinico_comunicacao_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.clinico_comunicacao_tabs.setProperty('cssClass', 'tab-container')  # Usar estilo neutro
        
        # Sub-abas
        self.sub_historico_clinico = QWidget()
        self.sub_templates_prescricoes = QWidget()
        self.sub_centro_comunicacao = QWidget()
        self.sub_iris_analise = QWidget()
        
        self.clinico_comunicacao_tabs.addTab(self.sub_historico_clinico, '📝 Histórico Clínico')
        self.clinico_comunicacao_tabs.addTab(self.sub_iris_analise, '👁️ Análise de Íris')
        self.clinico_comunicacao_tabs.addTab(self.sub_templates_prescricoes, '📋 Modelos de Prescrição')
        self.clinico_comunicacao_tabs.addTab(self.sub_centro_comunicacao, '📧 Email')
        
        # Conectar sinal de mudança de aba para refresh automático
        self.clinico_comunicacao_tabs.currentChanged.connect(self._on_tab_clinico_changed)
        
        main_layout.addWidget(self.clinico_comunicacao_tabs)
        
        # 🚀 CORREÇÃO: Carregar automaticamente o HISTÓRICO CLÍNICO (primeiro tab) 
        # para evitar tela em branco
        print("✅ Tabs clínicos criados - carregando histórico automaticamente...")
        self._on_tab_clinico_changed(0)  # Força carregar o primeiro tab (histórico)
        
        print("✅ Área clínica inicializada com histórico visível")

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
            
            print("✅ Módulo de dados pessoais carregado com sucesso")
            
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
        """Sub-aba: Histórico Clínico - Agora usando módulo otimizado"""
        layout = QVBoxLayout(self.sub_historico_clinico)
        layout.setContentsMargins(0, 0, 0, 0)  # Zero margins para o widget ocupar tudo
        
        try:
            # 🚀 USAR MÓDULO OTIMIZADO via lazy loading
            _, HistoricoClinicoWidget, _, _, _, _, _, _ = importar_modulos_especializados()
            
            # Obter histórico atual se existe
            historico_atual = ""
            if hasattr(self, 'paciente_data') and self.paciente_data:
                historico_atual = self.paciente_data.get('historico_clinico', '')
            
            # Criar widget otimizado
            self.historico_widget = HistoricoClinicoWidget(historico_atual, self)
            
            # Conectar sinais
            self.historico_widget.historico_alterado.connect(self.on_historico_alterado)
            self.historico_widget.guardar_solicitado.connect(self.guardar)
            
            # Manter referência ao editor para compatibilidade
            self.historico_edit = self.historico_widget.historico_edit
            
            layout.addWidget(self.historico_widget)
            
            print("✅ Módulo HistoricoClinicoWidget carregado com sucesso")
            
        except ImportError as e:
            print(f"❌ ERRO CRÍTICO: Módulo historico_clinico não encontrado: {e}")
            # SEM FALLBACK - deve funcionar sempre
        except Exception as e:
            print(f"❌ ERRO no módulo historico_clinico: {e}")
            # SEM FALLBACK - deve funcionar sempre
    
    def on_historico_alterado(self, novo_historico):
        """Callback quando histórico é alterado PELO USUÁRIO"""
        # CORREÇÃO: Só marcar como dirty se não estiver carregando dados iniciais
        if not getattr(self, '_carregando_dados', False) and hasattr(self, 'paciente_data') and self.paciente_data:
            # Atualizar apenas o texto simples no paciente_data
            self.paciente_data['historico_clinico'] = novo_historico
            # Marcar como alterado
            self.dirty = True
    
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
            
            # Canvas de íris otimizado
            self.iris_canvas = IrisCanvas(self)
            layout.addWidget(self.iris_canvas)
            
            # Manager de overlays
            self.iris_overlay_manager = IrisOverlayManager(self.iris_canvas)
            
            print("✅ Módulo de análise de íris carregado")
            
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
        
        # ✅ BOTÕES NA LINHA "PARA" - ORDEM: Follow-up, Templates, Lista (MESMO TAMANHO)
        btn_followup = QPushButton("📅 Follow-up")
        btn_followup.setFixedHeight(45)
        btn_followup.setFixedWidth(120)  # TAMANHO UNIFICADO
        btn_followup.clicked.connect(self.schedule_followup_consulta)
        para_layout.addWidget(btn_followup)
        
        btn_template = QPushButton("📄 Templates")
        btn_template.setFixedHeight(45)
        btn_template.setFixedWidth(120)  # TAMANHO UNIFICADO
        btn_template.clicked.connect(self.abrir_templates_mensagem)
        para_layout.addWidget(btn_template)
        
        btn_listar_followups = QPushButton("📋 Lista")
        btn_listar_followups.setFixedHeight(45)
        btn_listar_followups.setFixedWidth(120)  # TAMANHO UNIFICADO
        btn_listar_followups.clicked.connect(self.listar_followups_agendados)
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
        
        # BOTÃO ENVIAR - LARGURA TOTAL dos 3 botões com MESMA MARGEM CSS
        btn_enviar_email = QPushButton("📧 Enviar")
        btn_enviar_email.setFixedHeight(45)
        btn_enviar_email.setFixedWidth(390)  # LARGURA AUMENTADA para 390px
        btn_enviar_email.clicked.connect(self.enviar_mensagem)
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
        
        btn_config_inferior = QPushButton("⚙️ Config")
        btn_config_inferior.setFixedHeight(35)
        btn_config_inferior.setFixedWidth(85)
        btn_config_inferior.clicked.connect(self.abrir_configuracoes_comunicacao)
        config_inferior_layout.addWidget(btn_config_inferior)
        
        layout.addLayout(config_inferior_layout)
        
        # ✅ SEM BOTÕES EM BAIXO - Como pedido na imagem (já estão na linha do "Para:")
        
        # Adicionar stretch no final para empurrar conteúdo para cima
        layout.addStretch()

        # Configurar canal e carregar dados
        
        btn_enviar = QPushButton("📧 Enviar Email")
        btn_enviar.setFixedHeight(50)  # Ligeiramente maior para destaque
        btn_enviar.setFixedWidth(200)  # Ligeiramente maior
        btn_enviar.clicked.connect(self.enviar_mensagem)
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
        """Carrega automaticamente o email do paciente atual"""
        # print(f"[EMAIL DEBUG] 🔍 Verificando paciente_data: {bool(self.paciente_data)}")
        # print(f"[EMAIL DEBUG] 📋 Dados disponíveis: {list(self.paciente_data.keys()) if self.paciente_data else 'Nenhum'}")
        
        if self.paciente_data:
            # Carregar email se disponível - PROTEGER CONTRA None
            email_raw = self.paciente_data.get('email', '')
            email_paciente = email_raw.strip() if email_raw else ''
            # print(f"[EMAIL DEBUG] 📧 Email encontrado: '{email_paciente}'")
            
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
        """Atualiza o email no paciente_data em tempo real e no separador Email"""
        novo_email = self.email_edit.text().strip()
        
        if hasattr(self, 'paciente_data') and self.paciente_data:
            # Atualizar email no paciente_data
            self.paciente_data['email'] = novo_email
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
            # print(f"[PDF DEBUG] 🔍 Verificando paciente_data: {bool(hasattr(self, 'paciente_data'))}")
            if hasattr(self, 'paciente_data'):
                # print(f"[PDF DEBUG] 📋 Dados do paciente: {bool(self.paciente_data)}")
                if self.paciente_data:
                    # print(f"[PDF DEBUG] 🗝️ Chaves disponíveis: {list(self.paciente_data.keys())}")
                    pass
            
            if not hasattr(self, 'paciente_data') or not self.paciente_data:
                from biodesk_styled_dialogs import BiodeskMessageBox
                BiodeskMessageBox.warning(self, "Aviso", "Selecione um paciente primeiro.")
                return
            
            # Verificar se há email configurado
            patient_email = self.paciente_data.get('email', '').strip()
            # print(f"[PDF DEBUG] 📧 Email do paciente: '{patient_email}'")
            
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

    # ====== MÉTODOS AUXILIARES PARA CORES ======
    def _lighten_color(self, hex_color, percent):
        """Clarifica uma cor hexadecimal - wrapper para services.styles"""
        from services.styles import lighten_color
        return lighten_color(hex_color, percent)
    
    def _darken_color(self, hex_color, percent):
        """Escurece uma cor hexadecimal - wrapper para services.styles"""
        from services.styles import darken_color
        return darken_color(hex_color, percent)

    # ====== MÉTODOS PARA CENTRO DE COMUNICAÇÃO ======
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
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setFixedHeight(40)
            
            btn_cancelar.clicked.connect(dialog.reject)
            
            btn_usar = QPushButton("✨ Usar Template Personalizado")
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
        """Abre diálogo para usar templates predefinidos"""
        try:
            templates = {
                "Consulta Inicial": "Obrigado por ter escolhido os nossos serviços...",
                "Follow-up": "Como tem estado desde a nossa última consulta?",
                "Agendamento": "Gostaria de agendar a sua próxima consulta..."
            }
            
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Usar Template")
            dialog.resize(650, 500)  # AUMENTADO: era 500x400, agora 650x500
            
            layout = QVBoxLayout()
            
            lista_templates = QListWidget()
            for nome in templates.keys():
                lista_templates.addItem(nome)
            layout.addWidget(lista_templates)
            
            preview = QTextEdit()
            preview.setReadOnly(True)
            layout.addWidget(preview)
            
            def atualizar_preview():
                item_atual = lista_templates.currentItem()
                if item_atual:
                    nome = item_atual.text()
                    preview.setPlainText(templates[nome])
            
            lista_templates.itemSelectionChanged.connect(atualizar_preview)
            
            def usar_template():
                item_atual = lista_templates.currentItem()
                if item_atual:
                    nome = item_atual.text()
                    self.mensagem_edit.setPlainText(templates[nome])
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Aviso", "Selecione um template primeiro.")
            
            # Botões do diálogo
            botoes_layout = QHBoxLayout()
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_usar = QPushButton("✅ Usar Template")
            
            btn_cancelar.clicked.connect(dialog.reject)
            btn_usar.clicked.connect(usar_template)
            
            botoes_layout.addStretch()
            botoes_layout.addWidget(btn_cancelar)
            botoes_layout.addWidget(btn_usar)
            layout.addLayout(botoes_layout)
            
            # Selecionar primeiro item por padrão
            if lista_templates.count() > 0:
                lista_templates.setCurrentRow(0)
                atualizar_preview()
            
            dialog.exec()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", f"Erro ao abrir templates: {str(e)}")
            print(f"[TEMPLATE] ❌ Erro: {e}")

    def enviar_mensagem(self):
        """Envia a mensagem através do email com template personalizado"""
        if not self.canal_atual or self.canal_atual != "email":
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Canal não disponível", "Apenas o canal de email está disponível.")
            return
        
        destinatario = self.destinatario_edit.text()
        mensagem = self.mensagem_edit.toPlainText()
        assunto = self.assunto_edit.text() or "Mensagem do Biodesk"
        
        if not destinatario or not mensagem:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Campos obrigatórios", "Preencha o destinatário e a mensagem.")
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

    # ====== MÉTODOS PARA SUB-ABAS ADICIONAIS ======
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
            layout = QVBoxLayout(self.sub_declaracao_saude)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.declaracao_saude_widget)
            
            # Carregar dados do paciente se disponível
            if hasattr(self, 'paciente_data') and self.paciente_data:
                self.declaracao_saude_widget.set_paciente_data(self.paciente_data)
            
            print("✅ Módulo DeclaracaoSaudeWidget carregado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar módulo DeclaracaoSaudeWidget: {e}")
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
        
        # Tentar atualizar também via método delegate se disponível
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
    
    # Método duplicado removido - usar apenas a versão otimizada na linha ~359

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
            
            print("✅ Módulo de Íris carregado com sucesso")
            
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
                    # CheckboxNotesWidget - método correto
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
        # através do método abrir_analise_sinais() no mousePressEvent

    def on_imagem_iris_selecionada(self, imagem_data):
        """Callback para quando uma imagem é selecionada na galeria"""
        print(f"🖼️ Imagem selecionada: {imagem_data}")
        # Processar seleção de imagem conforme necessário
        
    def on_notas_iris_exportadas(self, notas):
        """Callback para quando notas são exportadas"""
        print(f"📝 Notas exportadas: {len(notas)} itens")
        # Processar exportação de notas conforme necessário

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
        self.btn_abrir_terapia = QPushButton("⚡ Abrir Módulo de Terapia")
        self.btn_abrir_terapia.clicked.connect(self.abrir_terapia)
        botoes_layout.addWidget(self.btn_abrir_terapia)
        
        botoes_layout.addStretch()
        layout.addLayout(botoes_layout)
        
        # Espaçador
        layout.addStretch()
    
    # Método de teste removido - funcionalidade obsoleta

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
                    print("✅ Dados pessoais carregados no widget especializado")
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
        from db_manager import DBManager
        
        # Obter dados do widget de dados pessoais
        dados = {}
        if hasattr(self, 'dados_pessoais_widget'):
            try:
                dados_pessoais = self.dados_pessoais_widget.obter_dados()
                dados.update(dados_pessoais)
                print("✅ Dados pessoais obtidos do widget especializado")
            except Exception as e:
                print(f"❌ Erro ao obter dados pessoais: {e}")
        
        # Obter histórico clínico do widget especializado
        if hasattr(self, 'historico_widget'):
            try:
                historico = self.historico_widget.obter_historico()
                dados['historico'] = historico
                print("✅ Histórico clínico obtido do widget especializado")
            except Exception as e:
                print(f"❌ Erro ao obter histórico: {e}")
        
        # Todos os campos já vêm do widget dados_pessoais, não precisamos de campos adicionais
        
        if 'id' in self.paciente_data:
            dados['id'] = self.paciente_data['id']
        
        # Lazy import do DBManager
        from db_manager import DBManager
        db = DBManager()
        # Prevenção de duplicação por nome + data_nascimento
        query = "SELECT * FROM pacientes WHERE nome = ? AND data_nascimento = ?"
        params = (dados['nome'], dados['data_nascimento'])
        duplicados = db.execute_query(query, params)
        if duplicados and (not ('id' in dados and duplicados[0].get('id') == dados['id'])):
            from biodesk_styled_dialogs import BiodeskMessageBox
            BiodeskMessageBox.warning(self, "Duplicado", "Já existe um utente com este nome e data de nascimento.")
            return
        novo_id = db.save_or_update_paciente(dados)
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
            print("✅ Pesquisa de Pacientes carregada com sucesso")
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
        btn_ok = QPushButton("🔙 Entendido")
        
        btn_ok.clicked.connect(dialog.accept)
        
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
        
        # Obter TODOS os emails enviados do histórico (não apenas follow-ups)
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
            btn_cancelar = QPushButton("❌ Cancelar Selecionado")

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
            
        # Tab 3: TODOS os Outros Emails
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
        btn_fechar = QPushButton("🔙 Fechar")
        
        btn_fechar.clicked.connect(dialog.accept)
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
        
        # Botão Paciente - Compacto e bem formatado
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
        
        # Botão Terapeuta - Compacto e bem formatado
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
        btn_imprimir = QPushButton("🖨️\nImprimir")
        btn_imprimir.setFixedSize(100, 60)  # Reduzir largura
        self._style_modern_button(btn_imprimir, "#ff9800")
        btn_imprimir.clicked.connect(self.imprimir_consentimento)
        botoes_linha1.addWidget(btn_imprimir)
        
        btn_pdf = QPushButton("📄\nPDF")
        btn_pdf.setFixedSize(100, 60)  # Reduzir largura
        self._style_modern_button(btn_pdf, "#3498db")
        btn_pdf.clicked.connect(self.gerar_pdf_consentimento)
        botoes_linha1.addWidget(btn_pdf)
        
        acoes_layout.addLayout(botoes_linha1)
        
        # Segunda linha de botões
        botoes_linha2 = QHBoxLayout()
        botoes_linha2.setSpacing(10)
        
        btn_guardar = QPushButton("💾\nGuardar")
        btn_guardar.setFixedSize(100, 60)  # Reduzir largura
        self._style_modern_button(btn_guardar, "#27ae60")
        btn_guardar.clicked.connect(self.guardar_consentimento)
        botoes_linha2.addWidget(btn_guardar)
        
        btn_limpar = QPushButton("🗑️\nLimpar")
        btn_limpar.setFixedSize(100, 60)  # Reduzir largura
        self._style_modern_button(btn_limpar, "#e74c3c")
        btn_limpar.clicked.connect(self.limpar_consentimento)
        botoes_linha2.addWidget(btn_limpar)
        
        acoes_layout.addLayout(botoes_linha2)
        
        # Botão de histórico centralizado
        btn_historico = QPushButton("📋 Histórico")
        btn_historico.setFixedSize(210, 50)  # Mais largo para ocupar as duas colunas
        self._style_modern_button(btn_historico, "#9b59b6")
        btn_historico.clicked.connect(self.mostrar_historico_consentimentos)
        acoes_layout.addWidget(btn_historico)
        # Botão moderno para assinatura externa
        btn_assinatura_externa = QPushButton("📝 Assinar PDF Externamente")
        btn_assinatura_externa.setFixedSize(210, 50)
        
        btn_assinatura_externa.clicked.connect(self.gerar_pdf_para_assinatura_externa)
        acoes_layout.addWidget(btn_assinatura_externa)
        
        # Botão de importação manual (para casos onde a automação falha)
        btn_importar_manual_consent = QPushButton("📁 Importar Assinado")
        btn_importar_manual_consent.setFixedSize(210, 35)
        
        btn_importar_manual_consent.clicked.connect(self.importar_pdf_manual)
        acoes_layout.addWidget(btn_importar_manual_consent)
        
        # Botão de anular consentimento
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
                # print("[DEBUG] Paciente sem ID - status não pode ser carregado")  # Comentar para reduzir output
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
            
            # print(f"[DEBUG] Status dos consentimentos carregado para paciente {paciente_id}")  # Comentar para reduzir output
            
        except Exception as e:
            # print(f"[DEBUG] Erro ao carregar status de consentimentos: {e}")  # Comentar para reduzir output
            # Manter status padrão em caso de erro
            pass

    def atualizar_historico_consentimentos(self):
        """Atualiza a lista de histórico de consentimentos"""
        # TODO: Carregar do banco de dados
        # Por agora, exemplo estático
        if hasattr(self, 'lista_historico'):
            self.lista_historico.clear()
            self.lista_historico.addItem("📋 Consentimento Naturopatia - 01/08/2023")
            self.lista_historico.addItem("👁️ Consentimento Iridologia - 15/07/2023")

    def selecionar_tipo_consentimento(self, tipo):
        """Seleciona um tipo de consentimento e carrega o template correspondente"""
        # print(f"[DEBUG] Selecionando tipo de consentimento: {tipo}")  # Comentar para reduzir output
        
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
        
        # print(f"[DEBUG] Consentimento '{nome_tipo}' carregado com sucesso")  # Comentar para reduzir output

    def verificar_assinaturas_existentes(self, tipo):
        """Verifica se já existem assinaturas para este tipo de consentimento"""
        try:
            if not hasattr(self, 'paciente_data') or not self.paciente_data.get('id'):
                # Reset para estado inicial se não há paciente
                self.resetar_botoes_assinatura()
                return
            
            from consentimentos_manager import ConsentimentosManager
            manager = ConsentimentosManager()
            
            # Obter o consentimento mais recente deste tipo para este paciente
            paciente_id = self.paciente_data['id']
            
            import sqlite3
            try:
                conn = sqlite3.connect("pacientes.db")
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, assinatura_paciente, assinatura_terapeuta, nome_paciente, nome_terapeuta, status
                    FROM consentimentos 
                    WHERE paciente_id = ? AND tipo_consentimento = ? AND (status IS NULL OR status != 'anulado')
                    ORDER BY data_assinatura DESC 
                    LIMIT 1
                ''', (paciente_id, tipo))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    consentimento_id, assinatura_paciente, assinatura_terapeuta, nome_paciente, nome_terapeuta, status = resultado
                    
                    # Verificar se o consentimento não foi anulado
                    if status == 'anulado':
                        # Consentimento foi anulado - resetar botões
                        self.consentimento_ativo = None
                        self.resetar_botoes_assinatura()
                        print(f"[DEBUG] ℹ️ Consentimento {tipo} foi anulado - resetando botões")
                        return
                    
                    # Armazenar consentimento ativo para usar nas assinaturas
                    self.consentimento_ativo = {'id': consentimento_id, 'tipo': tipo}
                    
                    # Verificar e atualizar botão do paciente
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
                    
            finally:
                if conn:
                    conn.close()
                    
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

    def obter_template_consentimento(self, tipo):
        """Retorna o template HTML para o tipo de consentimento especificado"""
        nome_paciente = self.paciente_data.get('nome', '[NOME_PACIENTE]')
        data_nascimento = self.paciente_data.get('data_nascimento', '[DATA_NASCIMENTO]')
        data_atual = self.data_atual()
        
        # Calcular idade automaticamente
        idade = self.calcular_idade()
        
        # Obter outros dados disponíveis
        contacto = self.paciente_data.get('contacto', '[CONTACTO]')
        email = self.paciente_data.get('email', '[EMAIL]')
        morada = self.paciente_data.get('morada', '[MORADA]')
        
        templates = {
            'naturopatia': f"""
            <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">CONSENTIMENTO INFORMADO – NATUROPATIA</h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                <p style="margin: 5px 0;"><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                <p style="margin: 5px 0;"><strong>Idade:</strong> {idade} anos</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {data_atual}</p>
            </div>
            
            <p>Eu, <strong>{nome_paciente}</strong>, abaixo assinado(a), declaro que fui devidamente informado(a) sobre a natureza, objetivos, benefícios esperados e possíveis limitações da abordagem terapêutica naturopática que me será aplicada.</p>
            
            <p>Compreendo que a <strong>Naturopatia</strong> utiliza métodos naturais e não invasivos, tais como <strong>fitoterapia, homeopatia, suplementação nutricional, mudanças de estilo de vida, técnicas manuais e energéticas</strong>, visando a promoção da autorregulação e equilíbrio do organismo.</p>
            
            <p><strong>Declaro estar ciente de que:</strong></p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li><strong>Esta intervenção não substitui o acompanhamento médico convencional</strong>, exames clínicos, nem qualquer diagnóstico médico;</li>
                
                <li>Podem ocorrer <strong>reações naturais do organismo</strong>, como eliminação de toxinas, alterações do sono, humor ou trânsito intestinal;</li>
                
                <li>Existe a possibilidade de <strong>interações medicamentosas</strong>, caso eu esteja sob terapêutica farmacológica;</li>
                
                <li>É da <strong>minha responsabilidade comunicar condições médicas pré-existentes</strong>, histórico de doenças, gravidez, alergias conhecidas, medicamentos em uso ou qualquer informação relevante para a minha segurança;</li>
                
                <li><strong>Não será imputada responsabilidade ao terapeuta</strong> por reações adversas decorrentes de informações omissas, incompletas ou desconhecidas da minha parte;</li>
                
                <li>A terapêutica poderá incluir <strong>toques leves em zonas anatómicas específicas</strong>, estritamente com fins terapêuticos e respeitando sempre os princípios éticos e profissionais. Caso em algum momento me sinta desconfortável, <strong>posso interromper o procedimento de imediato</strong>;</li>
                
                <li>Entendo que <strong>não existe garantia de cura ou resultados específicos</strong>, variando de pessoa para pessoa.</li>
            </ul>
            
            <p style="margin-top: 20px;"><strong>Consinto de forma livre, esclarecida e voluntária</strong> na realização das intervenções naturopáticas propostas pelo terapeuta responsável, com pleno conhecimento dos seus objetivos e limites.</p>
            
            <p><strong>Tenho o direito de revogar este consentimento a qualquer momento</strong>, por via verbal ou escrita, sem necessidade de justificação e sem prejuízo para o acompanhamento posterior.</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #e8f5e9; border-radius: 8px;">
                <p style="margin: 0; font-size: 12px; color: #2e7d32;">
                    <strong>Data do consentimento:</strong> {data_atual}<br>
                    <strong>Paciente:</strong> {nome_paciente}
                </p>
            </div>
            """,
            
            'osteopatia': f"""
            <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">CONSENTIMENTO INFORMADO – OSTEOPATIA</h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                <p style="margin: 5px 0;"><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                <p style="margin: 5px 0;"><strong>Idade:</strong> {idade} anos</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {data_atual}</p>
            </div>
            
            <p>Eu, <strong>{nome_paciente}</strong>, abaixo assinado(a), declaro que fui devidamente informado(a) sobre a natureza, objetivos, técnicas e limitações da abordagem osteopática a que serei sujeito(a).</p>
            
            <p>A <strong>Osteopatia</strong> é uma terapêutica manual não invasiva que visa restaurar a mobilidade e o equilíbrio do corpo, através de <strong>técnicas específicas aplicadas a músculos, articulações, fáscias, vísceras e outras estruturas anatómicas</strong>, respeitando a fisiologia individual.</p>
            
            <p><strong>Compreendo que:</strong></p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li>As técnicas poderão envolver <strong>toque direto sobre o corpo</strong>, incluindo <strong>manipulações articulares, alongamentos, mobilizações, palpação e técnicas miofasciais ou craniossacrais</strong>;</li>
                
                <li>Em determinadas situações poderá ser necessário <strong>expor parcialmente zonas do corpo</strong> (ex: costas, pelve, abdómen), sendo sempre assegurada a <strong>minha privacidade, conforto e dignidade</strong>, com utilização de roupa adequada, toalhas ou lençóis;</li>
                
                <li>Todo o contacto físico será <strong>estritamente profissional e exclusivamente com finalidade terapêutica</strong>, sem qualquer cariz íntimo, sexual, invasivo ou impróprio;</li>
                
                <li>Foi-me explicado que poderão ocorrer, embora raramente, <strong>reações transitórias</strong> como sensibilidade muscular, fadiga, dores ligeiras ou desconforto nas horas ou dias seguintes à sessão;</li>
                
                <li>Devo informar previamente o terapeuta sobre <strong>qualquer doença diagnosticada, cirurgia, medicação, gravidez, condição cardiovascular, neurológica, oncológica</strong> ou qualquer sintoma incomum;</li>
                
                <li>A <strong>omissão de informações relevantes pode comprometer a eficácia e segurança da terapia</strong>, isentando o terapeuta de responsabilidade por consequências imprevistas;</li>
                
                <li><strong>Posso, em qualquer momento, interromper ou recusar qualquer manobra</strong> com a qual não me sinta confortável.</li>
            </ul>
            
            <p style="margin-top: 20px;"><strong>Declaro ter compreendido os riscos, benefícios e objetivos da prática osteopática</strong>, e que:</p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li><strong>Esta abordagem não substitui cuidados médicos convencionais</strong> nem isenta a necessidade de acompanhamento médico, exames complementares ou tratamentos hospitalares quando indicados;</li>
                
                <li><strong>Consinto livremente e de forma informada</strong> na realização das intervenções osteopáticas propostas, com plena liberdade para colocar questões, esclarecer dúvidas e acompanhar o plano terapêutico;</li>
                
                <li><strong>Tenho o direito de revogar este consentimento a qualquer momento</strong>, sem necessidade de justificar e sem que isso prejudique o meu acesso a outras formas de apoio terapêutico.</li>
            </ul>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #fff3e0; border-radius: 8px;">
                <p style="margin: 0; font-size: 12px; color: #ef6c00;">
                    <strong>Data do consentimento:</strong> {data_atual}<br>
                    <strong>Paciente:</strong> {nome_paciente}
                </p>
            </div>
            """,
            
            'quantica': f"""
            <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">CONSENTIMENTO INFORMADO – TERAPIA QUÂNTICA</h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                <p style="margin: 5px 0;"><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                <p style="margin: 5px 0;"><strong>Idade:</strong> {idade} anos</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {data_atual}</p>
            </div>
            
            <p>Eu, <strong>{nome_paciente}</strong>, abaixo assinado(a), declaro que fui devidamente informado(a) sobre a natureza, objetivos e limites da <strong>Terapia Quântica Informacional</strong> a que irei ser sujeito(a).</p>
            
            <p><strong>Compreendo que:</strong></p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li>A <strong>Terapia Quântica</strong> consiste na aplicação de <strong>frequências bioenergéticas, campos informacionais ou estímulos não invasivos</strong>, com o objetivo de harmonizar o campo energético e promover o equilíbrio do organismo;</li>
                
                <li><strong>Não existe qualquer contacto físico ou manipulação corporal direta</strong> durante a aplicação destas técnicas, salvo indicação prévia e consentimento específico para procedimentos auxiliares;</li>
                
                <li>Esta abordagem é considerada uma <strong>prática complementar e integrativa</strong>, não substituindo cuidados médicos convencionais, exames clínicos ou tratamentos prescritos por profissionais de saúde;</li>
                
                <li>Os <strong>efeitos e benefícios reportados podem variar individualmente</strong>, não sendo garantidos resultados específicos, nem cura de doenças diagnosticadas;</li>
                
                <li>Devo informar previamente o terapeuta sobre <strong>quaisquer condições de saúde relevantes, dispositivos médicos implantados (ex: pacemaker), gravidez ou hipersensibilidade conhecida a estímulos eletromagnéticos</strong>;</li>
                
                <li><strong>Não será imputada responsabilidade ao terapeuta</strong> por reações adversas resultantes de omissão ou desconhecimento de informações relevantes da minha parte.</li>
            </ul>
            
            <p style="margin-top: 20px;"><strong>Consinto livre e esclarecidamente na realização das sessões de Terapia Quântica</strong>, com a possibilidade de colocar questões, esclarecer dúvidas e interromper a sessão sempre que desejar.</p>
            
            <p><strong>Tenho o direito de revogar este consentimento em qualquer momento</strong>, por via verbal ou escrita, sem necessidade de justificação e sem qualquer prejuízo para o acompanhamento futuro.</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f3e5f5; border-radius: 8px;">
                <p style="margin: 0; font-size: 12px; color: #7b1fa2;">
                    <strong>Data do consentimento:</strong> {data_atual}<br>
                    <strong>Paciente:</strong> {nome_paciente}
                </p>
            </div>
            """,
            
            'geral': f"""
            <h3>CONSENTIMENTO INFORMADO GERAL</h3>
            <p><strong>Nome:</strong> {nome_paciente}<br>
            <strong>Data de Nascimento:</strong> {data_nascimento}<br>
            <strong>Data:</strong> {data_atual}</p>
            
            <p>Eu, <strong>{nome_paciente}</strong>, declaro ter sido informado(a) sobre os procedimentos terapêuticos que serão realizados.</p>
            
            <p>Compreendo a natureza dos tratamentos propostos e autorizo a sua realização.</p>
            
            <p>Declaro ter esclarecido todas as dúvidas sobre os procedimentos.</p>
            
            <p><strong>Tratamento de Dados Pessoais (RGPD):</strong><br>
            Consinto o tratamento dos meus dados pessoais e de saúde para os fins descritos, podendo revogar este consentimento a qualquer momento.</p>
            """,
            
            'iridologia': f"""
            <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">CONSENTIMENTO INFORMADO – IRIDOLOGIA</h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                <p style="margin: 5px 0;"><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                <p style="margin: 5px 0;"><strong>Idade:</strong> {idade} anos</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {data_atual}</p>
            </div>
            
            <p>Eu, <strong>{nome_paciente}</strong>, abaixo assinado(a), declaro que fui devidamente informado(a) sobre a natureza, objetivos e limites da <strong>avaliação iridológica</strong> a que serei submetido(a).</p>
            
            <p><strong>Compreendo que:</strong></p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li>A <strong>Iridologia</strong> consiste na observação e análise visual das estruturas da íris, com o objetivo de identificar <strong>padrões constitucionais, tendências ou desequilíbrios funcionais</strong>, não se destinando ao diagnóstico de doenças, nem à substituição de exames médicos convencionais;</li>
                
                <li>O procedimento pode envolver a utilização de <strong>dispositivos de ampliação e/ou fotografia digital dos olhos</strong>, assegurando sempre o máximo respeito pela minha privacidade e integridade;</li>
                
                <li><strong>Nenhum contacto físico invasivo é realizado</strong>, podendo, ocasionalmente, ser necessário um leve ajuste manual da pálpebra ou iluminação, sempre de modo profissional e respeitoso;</li>
                
                <li>Os <strong>dados recolhidos (imagens e observações) são tratados com total confidencialidade</strong> e não serão partilhados com terceiros sem o meu consentimento explícito;</li>
                
                <li>Devo informar previamente o terapeuta sobre <strong>condições oculares conhecidas (ex: glaucoma, cirurgias, infeções, alergias, uso de lentes de contacto ou outros antecedentes relevantes)</strong>, para garantir a minha segurança;</li>
                
                <li><strong>Não será imputada responsabilidade ao terapeuta</strong> por reações decorrentes de informações omissas, desconhecidas ou incompletas da minha parte;</li>
                
                <li>Estou ciente de que a <strong>Iridologia é uma ferramenta de avaliação complementar</strong>, não representa por si só diagnóstico médico nem prescrição de tratamentos farmacológicos.</li>
            </ul>
            
            <p style="margin-top: 20px;"><strong>Consinto de forma livre, informada e esclarecida na realização da avaliação iridológica proposta</strong>, podendo colocar questões ou recusar o exame, parcial ou totalmente, a qualquer momento.</p>
            
            <p><strong>Tenho o direito de revogar este consentimento em qualquer fase do processo</strong>, por via verbal ou escrita, sem necessidade de justificar e sem qualquer prejuízo para o meu acompanhamento posterior.</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #e8f6f3; border-radius: 8px;">
                <p style="margin: 0; font-size: 12px; color: #00695c;">
                    <strong>Data do consentimento:</strong> {data_atual}<br>
                    <strong>Paciente:</strong> {nome_paciente}
                </p>
            </div>
            """,
            
            'mesoterapia': f"""
            <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">CONSENTIMENTO INFORMADO – MESOTERAPIA HOMEOPÁTICA</h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                <p style="margin: 5px 0;"><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                <p style="margin: 5px 0;"><strong>Idade:</strong> {idade} anos</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {data_atual}</p>
            </div>
            
            <p>Eu, <strong>{nome_paciente}</strong>, abaixo assinado(a), declaro que fui devidamente informado(a) sobre a natureza, objetivos, procedimento e possíveis efeitos da <strong>Mesoterapia Homeopática</strong>.</p>
            
            <p><strong>Compreendo que:</strong></p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li>A <strong>Mesoterapia Homeopática</strong> consiste na administração de pequenas quantidades de <strong>substâncias naturais ou homeopáticas, por via intradérmica ou subcutânea</strong>, em pontos específicos da pele, com o objetivo de estimular a autorregulação do organismo;</li>
                
                <li>O procedimento implica <strong>toque e aplicação de microinjeções</strong>, realizados exclusivamente por profissional habilitado, garantindo total respeito pela minha privacidade, conforto e integridade física;</li>
                
                <li>Durante ou após a sessão podem surgir <strong>efeitos locais, geralmente transitórios</strong>, tais como: vermelhidão, pequeno hematoma, ligeiro ardor, prurido ou sensibilidade na zona tratada;</li>
                
                <li>É <strong>minha responsabilidade informar o terapeuta</strong> sobre doenças crónicas, histórico de alergias (nomeadamente a componentes utilizados), gravidez, infeções cutâneas, toma de medicação anticoagulante, imunossupressores ou outros fatores clínicos relevantes;</li>
                
                <li>Todos os <strong>materiais utilizados são estéreis e descartáveis</strong>, cumprindo as normas legais e de segurança em vigor;</li>
                
                <li>O procedimento é realizado de acordo com a <strong>melhor prática clínica</strong>, sem qualquer conotação não profissional ou fim que não seja estritamente terapêutico;</li>
                
                <li>A <strong>Mesoterapia Homeopática é uma prática complementar</strong>, não substitui diagnóstico, tratamento ou acompanhamento médico, nem é garantia de cura.</li>
            </ul>
            
            <p style="margin-top: 20px;"><strong>Consinto de forma livre, esclarecida e voluntária na realização do procedimento proposto</strong>, com possibilidade de colocar questões, recusar ou interromper a intervenção sempre que desejar.</p>
            
            <p><strong>Tenho o direito de revogar este consentimento a qualquer momento</strong>, por via verbal ou escrita, sem necessidade de justificar e sem prejuízo para o meu acesso a outros cuidados de saúde.</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 8px;">
                <p style="margin: 0; font-size: 12px; color: #1565c0;">
                    <strong>Data do consentimento:</strong> {data_atual}<br>
                    <strong>Paciente:</strong> {nome_paciente}
                </p>
            </div>
            """,
            
            'rgpd': f"""
            <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">CONSENTIMENTO PARA TRATAMENTO DE DADOS PESSOAIS (RGPD)</h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                <p style="margin: 5px 0;"><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                <p style="margin: 5px 0;"><strong>Idade:</strong> {idade} anos</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {data_atual}</p>
            </div>
            
            <p>Nos termos do <strong>Regulamento Geral sobre a Proteção de Dados (RGPD – Regulamento (UE) 2016/679)</strong>, autorizo o responsável técnico pela minha avaliação e acompanhamento clínico a <strong>recolher, registar, tratar e arquivar os meus dados pessoais e de saúde</strong>, para fins exclusivos de prestação de cuidados terapêuticos, gestão administrativa e cumprimento de obrigações legais.</p>
            
            <p><strong>Declaro estar ciente de que:</strong></p>
            
            <ul style="margin: 15px 0; padding-left: 25px; line-height: 1.6;">
                <li>Os meus dados serão tratados com <strong>estrita confidencialidade</strong>, não sendo partilhados com terceiros sem o meu consentimento expresso, salvo quando exigido por lei;</li>
                
                <li>Tenho o direito de <strong>aceder, retificar, limitar, opor-me ou solicitar o apagamento dos meus dados</strong>, mediante pedido escrito dirigido ao responsável pelo tratamento;</li>
                
                <li>Os dados poderão incluir: <strong>identificação, contactos, informações clínicas, imagens (incluindo fotografias da íris), histórico terapêutico e anotações decorrentes das consultas</strong>;</li>
                
                <li>Os meus dados serão <strong>conservados apenas pelo período necessário</strong> à finalidade para que foram recolhidos ou enquanto decorrer a relação terapêutica;</li>
                
                <li>Posso <strong>retirar o meu consentimento para o tratamento dos dados a qualquer momento</strong>, sem prejuízo da licitude do tratamento efetuado até à data da revogação.</li>
            </ul>
            
            <p style="margin-top: 20px;">Para qualquer dúvida sobre os meus direitos ou sobre o tratamento dos dados, posso <strong>contactar diretamente o terapeuta responsável</strong>.</p>
            
            <p style="margin-top: 20px;"><strong>Autorizo expressamente o tratamento dos meus dados pessoais</strong>, nos termos acima descritos.</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #ecf0f1; border-radius: 8px;">
                <p style="margin: 0; font-size: 12px; color: #2c3e50;">
                    <strong>Data do consentimento:</strong> {data_atual}<br>
                    <strong>Paciente:</strong> {nome_paciente}
                </p>
            </div>
            """,
        }
        
        return templates.get(tipo, templates['geral'])
    
    def calcular_idade(self):
        """Calcula a idade do paciente baseada na data de nascimento"""
        try:
            data_nasc_str = self.paciente_data.get('data_nascimento', '')
            if not data_nasc_str:
                return '[IDADE]'
            
            from datetime import datetime
            # Tentar diferentes formatos de data
            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
            
            for formato in formatos:
                try:
                    data_nasc = datetime.strptime(data_nasc_str, formato)
                    hoje = datetime.now()
                    idade = hoje.year - data_nasc.year
                    
                    # Ajustar se ainda não fez aniversário este ano
                    if hoje.month < data_nasc.month or (hoje.month == data_nasc.month and hoje.day < data_nasc.day):
                        idade -= 1
                    
                    return str(idade)
                except ValueError:
                    continue
            
            return '[IDADE]'
        except Exception as e:
            print(f"[DEBUG] Erro ao calcular idade: {e}")
            return '[IDADE]'

    def guardar_consentimento(self):
        """Guarda o consentimento atual na base de dados"""
        if not hasattr(self, 'tipo_consentimento_atual'):
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro.")
            return
        
        try:
            from consentimentos_manager import ConsentimentosManager
            
            # Verificar se temos ID do paciente
            paciente_id = self.paciente_data.get('id')
            if not paciente_id:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "Não é possível guardar o consentimento.\nPaciente precisa de ser guardado primeiro.")
                return
            
            # Obter conteúdo
            conteudo_html = self.editor_consentimento.toHtml()
            conteudo_texto = self.editor_consentimento.toPlainText()
            
            # Verificar se há conteúdo
            if not conteudo_texto.strip():
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "O consentimento está vazio.\nAdicione conteúdo antes de guardar.")
                return
            
            # Preparar assinaturas usando sistema modular
            assinatura_paciente = None
            assinatura_terapeuta = None
            
            if hasattr(self, 'assinatura_paciente_data') and self.assinatura_paciente_data:
                try:
                    assinatura_paciente = self.assinatura_paciente_data
                    print(f"[DEBUG] Assinatura paciente carregada: {len(assinatura_paciente)} bytes")
                except Exception as e:
                    print(f"[DEBUG] Erro ao processar assinatura do paciente: {e}")
            
            if hasattr(self, 'assinatura_terapeuta_data') and self.assinatura_terapeuta_data:
                try:
                    assinatura_terapeuta = self.assinatura_terapeuta_data
                    print(f"[DEBUG] Assinatura terapeuta carregada: {len(assinatura_terapeuta)} bytes")
                except Exception as e:
                    print(f"[DEBUG] Erro ao processar assinatura do terapeuta: {e}")
            else:
                print(f"[DEBUG] Assinatura terapeuta não disponível")
            
            # Obter nomes para as assinaturas
            nome_paciente = self.paciente_data.get('nome', 'Nome não disponível')
            nome_terapeuta = "Dr. Nuno Correia"  # Nome do terapeuta definido
            
            # Guardar na base de dados
            manager = ConsentimentosManager()
            sucesso = manager.guardar_consentimento(
                paciente_id=paciente_id,
                tipo_consentimento=self.tipo_consentimento_atual,
                conteudo_html=conteudo_html,
                conteudo_texto=conteudo_texto,
                assinatura_paciente=assinatura_paciente,
                assinatura_terapeuta=assinatura_terapeuta,
                nome_paciente=nome_paciente,
                nome_terapeuta=nome_terapeuta
            )
            
            if sucesso:
                # Atualizar status visual
                self.carregar_status_consentimentos()
                
                # Preparar informação sobre assinaturas
                assinaturas_info = []
                if assinatura_paciente:
                    assinaturas_info.append("👤 Paciente")
                if assinatura_terapeuta:
                    assinaturas_info.append("👨‍⚕️ Terapeuta")
                
                assinaturas_texto = "✅ " + " + ".join(assinaturas_info) if assinaturas_info else "❌ Nenhuma capturada"
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(
                    self, 
                    "Consentimento Guardado", 
                    f"✅ Consentimento '{self.tipo_consentimento_atual}' guardado com sucesso!\n\n"
                    f"👤 Paciente: {self.paciente_data.get('nome', 'N/A')}\n"
                    f"📄 Tipo: {self.tipo_consentimento_atual.title()}\n"
                    f"📅 Data: {self.data_atual()}\n"
                    f"✍️ Assinaturas: {assinaturas_texto}"
                )
                print(f"[DEBUG] Consentimento {self.tipo_consentimento_atual} guardado para paciente {paciente_id}")
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "Não foi possível guardar o consentimento.\nVerifique os logs para mais detalhes.")
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao guardar consentimento:\n\n{str(e)}")
            print(f"[DEBUG] Erro ao guardar consentimento: {e}")

    def guardar_consentimento_completo(self):
        """Guarda consentimento E adiciona automaticamente aos documentos do paciente"""
        if not hasattr(self, 'tipo_consentimento_atual'):
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "⚠️ Selecione um tipo de consentimento primeiro.")
            return
        
        if not self.paciente_data or not self.paciente_data.get('id'):
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", "❌ Paciente precisa de ser guardado primeiro.")
            return
        
        try:
            print(f"📄 [CONSENTIMENTO] Iniciando processo completo para: {self.tipo_consentimento_atual}")
            
            # 1. CAPTURAR ASSINATURAS do sistema por tipo
            assinatura_paciente = None
            assinatura_terapeuta = None
            
            print(f"📄 [CONSENTIMENTO] Verificando assinaturas para tipo: {self.tipo_consentimento_atual}")
            
            # Primeiro tentar obter do sistema por tipo
            if hasattr(self, 'assinaturas_por_tipo') and self.tipo_consentimento_atual in self.assinaturas_por_tipo:
                assinaturas_tipo = self.assinaturas_por_tipo[self.tipo_consentimento_atual]
                
                if 'paciente' in assinaturas_tipo:
                    assinatura_paciente = assinaturas_tipo['paciente']
                    print(f"✅ [CONSENTIMENTO] Assinatura paciente do tipo '{self.tipo_consentimento_atual}': {len(assinatura_paciente)} bytes")
                
                if 'terapeuta' in assinaturas_tipo:
                    assinatura_terapeuta = assinaturas_tipo['terapeuta']
                    print(f"✅ [CONSENTIMENTO] Assinatura terapeuta do tipo '{self.tipo_consentimento_atual}': {len(assinatura_terapeuta)} bytes")
            
            # Fallback para variáveis antigas (compatibilidade)
            if not assinatura_paciente and hasattr(self, 'assinatura_paciente_data') and self.assinatura_paciente_data:
                assinatura_paciente = self.assinatura_paciente_data
                print(f"✅ [CONSENTIMENTO] Assinatura paciente (fallback): {len(assinatura_paciente)} bytes")
            
            if not assinatura_terapeuta and hasattr(self, 'assinatura_terapeuta_data') and self.assinatura_terapeuta_data:
                assinatura_terapeuta = self.assinatura_terapeuta_data
                print(f"✅ [CONSENTIMENTO] Assinatura terapeuta (fallback): {len(assinatura_terapeuta)} bytes")
            
            # Debug final
            print(f"🔍 [RESUMO DEBUG] Paciente: {assinatura_paciente is not None}, Terapeuta: {assinatura_terapeuta is not None}")
            if hasattr(self, 'assinaturas_por_tipo'):
                print(f"🔍 [DEBUG] Tipos disponíveis: {list(self.assinaturas_por_tipo.keys())}")
            else:
                print("🔍 [DEBUG] Sistema assinaturas_por_tipo não inicializado")
            
            # 2. GUARDAR na base de dados diretamente aqui
            print(f"📄 [CONSENTIMENTO] Guardando na base de dados...")
            
            from consentimentos_manager import ConsentimentosManager
            paciente_id = self.paciente_data.get('id')
            conteudo_html = self.editor_consentimento.toHtml()
            conteudo_texto = self.editor_consentimento.toPlainText()
            
            if not conteudo_texto.strip():
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "O consentimento está vazio.\nAdicione conteúdo antes de guardar.")
                return
            
            nome_paciente = self.paciente_data.get('nome', 'Nome não disponível')
            nome_terapeuta = "Dr. Nuno Correia"
            
            manager = ConsentimentosManager()
            sucesso_bd = manager.guardar_consentimento(
                paciente_id=paciente_id,
                tipo_consentimento=self.tipo_consentimento_atual,
                conteudo_html=conteudo_html,
                conteudo_texto=conteudo_texto,
                assinatura_paciente=assinatura_paciente,
                assinatura_terapeuta=assinatura_terapeuta,
                nome_paciente=nome_paciente,
                nome_terapeuta=nome_terapeuta
            )
            
            if sucesso_bd:
                self.carregar_status_consentimentos()
                print(f"✅ [CONSENTIMENTO] Guardado na BD com assinaturas")
            
            # 3. GERAR PDF e guardar na pasta de documentos
            print(f"📄 [CONSENTIMENTO] Gerando PDF...")
            
            nome_paciente_ficheiro = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            
            # Criar pasta de documentos se não existir
            pasta_consentimentos = f"Documentos_Pacientes/{paciente_id}_{nome_paciente_ficheiro}/Consentimentos"
            import os
            os.makedirs(pasta_consentimentos, exist_ok=True)
            
            # Nome do arquivo PDF
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"consentimento_{self.tipo_consentimento_atual}_{timestamp}.pdf"
            caminho_pdf = os.path.join(pasta_consentimentos, nome_arquivo)
            
            # Dados para o template
            dados_pdf = {
                'nome_paciente': self.paciente_data.get('nome', ''),
                'data_nascimento': self.paciente_data.get('data_nascimento', ''),
                'contacto': self.paciente_data.get('contacto', ''),
                'email': self.paciente_data.get('email', ''),
                'tipo_consentimento': self.tipo_consentimento_atual.title(),
                'data_atual': datetime.now().strftime("%d/%m/%Y"),
                'assinatura_paciente': assinatura_paciente,
                'assinatura_terapeuta': assinatura_terapeuta
            }
            
            # Tentar gerar o PDF
            pdf_success = self._gerar_pdf_consentimento_simples(conteudo_html, caminho_pdf, dados_pdf, assinatura_paciente, assinatura_terapeuta)
            
            if not pdf_success:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro PDF", f"❌ Falha ao gerar PDF do consentimento.\n\nVerifique os logs para mais detalhes.")
                return
            
            # 4. CRIAR METADATA (apenas se PDF foi criado com sucesso)
            caminho_meta = caminho_pdf + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                f.write(f"Categoria: Consentimento\n")
                f.write(f"Descrição: Consentimento de {self.tipo_consentimento_atual.title()}\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write(f"Tipo: {self.tipo_consentimento_atual}\n")
            
            # 5. ATUALIZAR LISTA DE DOCUMENTOS (se a aba estiver ativa)
            print(f"📄 [CONSENTIMENTO] Atualizando lista de documentos...")
            if hasattr(self, 'documentos_list'):
                self.atualizar_lista_documentos()
            
            # 6. FEEDBACK DE SUCESSO
            assinaturas_info = []
            if assinatura_paciente:
                assinaturas_info.append("👤 Paciente")
            if assinatura_terapeuta:
                assinaturas_info.append("👨‍⚕️ Terapeuta")
            
            assinaturas_texto = " + ".join(assinaturas_info) if assinaturas_info else "Nenhuma"
            
            from biodesk_dialogs import mostrar_sucesso
            mostrar_sucesso(
                self,
                "Consentimento Completo",
                f"✅ Consentimento processado com sucesso!\n\n"
                f"📄 Tipo: {self.tipo_consentimento_atual.title()}\n"
                f"💾 Guardado na BD: Sim\n"
                f"✍️ Assinaturas: {assinaturas_texto}\n"
                f"📁 PDF criado: {nome_arquivo}\n"
                f"📂 Localização: Gestão de Documentos\n\n"
                f"💡 Próximos passos: Consulte o documento na aba 'Gestão de Documentos' da Área Clínica."
            )
            
            print(f"✅ [CONSENTIMENTO] Processo completo finalizado: {caminho_pdf}")
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(
                self, 
                "Erro no Processo",
                f"❌ Erro durante o processo completo:\n\n{str(e)}\n\n"
                f"💡 O consentimento pode ter sido parcialmente guardado."
            )
            print(f"❌ [CONSENTIMENTO] Erro no processo completo: {e}")

    def _gerar_pdf_consentimento_simples(self, conteudo_html, caminho_pdf, dados_pdf, assinatura_paciente=None, assinatura_terapeuta=None):
        """Gera PDF de consentimento de forma simplificada COM assinaturas"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm, inch
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            import textwrap
            import re
            import io
            
            # Configurar o documento
            doc = SimpleDocTemplate(
                caminho_pdf,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=25*mm,
                bottomMargin=25*mm
            )
            
            # Configurar estilos
            styles = getSampleStyleSheet()
            
            # Estilo personalizado para título
            titulo_style = ParagraphStyle(
                'TituloCustom',
                parent=styles['Title'],
                fontSize=16,
                textColor=colors.Color(0.2, 0.2, 0.2),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            # Estilo para info do paciente
            info_style = ParagraphStyle(
                'InfoCustom', 
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.Color(0.3, 0.3, 0.3),
                spaceAfter=15,
                leftIndent=10,
                rightIndent=10
            )
            
            story = []
            
            # CABEÇALHO
            titulo = Paragraph(
                f"<b>CONSENTIMENTO INFORMADO</b><br/><i>{dados_pdf['tipo_consentimento'].upper()}</i>",
                titulo_style
            )
            story.append(titulo)
            story.append(Spacer(1, 10))
            
            # DADOS DO PACIENTE
            info_paciente = f"""
            <b>Nome:</b> {dados_pdf['nome_paciente']}<br/>
            <b>Data de Nascimento:</b> {dados_pdf['data_nascimento']}<br/>
            <b>Contacto:</b> {dados_pdf['contacto']}<br/>
            <b>Email:</b> {dados_pdf['email']}<br/>
            <b>Data do Consentimento:</b> {dados_pdf['data_atual']}
            """
            
            para_info = Paragraph(info_paciente, info_style)
            story.append(para_info)
            story.append(Spacer(1, 20))
            
            # CONTEÚDO DO CONSENTIMENTO (limpar HTML adequadamente)
            # 1. Remover estilos CSS completos
            texto_limpo = re.sub(r'<style[^>]*>.*?</style>', '', conteudo_html, flags=re.DOTALL)
            
            # 2. Remover atributos de estilo inline
            texto_limpo = re.sub(r'style="[^"]*"', '', texto_limpo)
            
            # 3. Converter tags de formatação para texto
            texto_limpo = re.sub(r'<br[^>]*>', '\n', texto_limpo)
            texto_limpo = re.sub(r'<p[^>]*>', '\n', texto_limpo)
            texto_limpo = re.sub(r'</p>', '\n', texto_limpo)
            texto_limpo = re.sub(r'<div[^>]*>', '\n', texto_limpo)
            texto_limpo = re.sub(r'</div>', '', texto_limpo)
            
            # 4. Preservar formatação importante
            texto_limpo = re.sub(r'<b[^>]*>(.*?)</b>', r'<b>\1</b>', texto_limpo)
            texto_limpo = re.sub(r'<strong[^>]*>(.*?)</strong>', r'<b>\1</b>', texto_limpo)
            texto_limpo = re.sub(r'<i[^>]*>(.*?)</i>', r'<i>\1</i>', texto_limpo)
            texto_limpo = re.sub(r'<em[^>]*>(.*?)</em>', r'<i>\1</i>', texto_limpo)
            
            # 5. Remover todas as outras tags HTML
            texto_limpo = re.sub(r'<(?!/?[bi]>)[^>]+>', '', texto_limpo)
            
            # 6. Converter entidades HTML
            texto_limpo = texto_limpo.replace('&nbsp;', ' ')
            texto_limpo = texto_limpo.replace('&amp;', '&')
            texto_limpo = texto_limpo.replace('&lt;', '<')
            texto_limpo = texto_limpo.replace('&gt;', '>')
            texto_limpo = texto_limpo.replace('&quot;', '"')
            
            # 7. Limpar espaços e quebras de linha excessivas
            texto_limpo = re.sub(r'\n\s*\n\s*\n', '\n\n', texto_limpo)
            texto_limpo = re.sub(r'[ \t]+', ' ', texto_limpo)
            texto_limpo = texto_limpo.strip()
            
            # Dividir em parágrafos e adicionar ao PDF
            paragrafos = texto_limpo.split('\n')
            for paragrafo in paragrafos:
                if paragrafo.strip():
                    p = Paragraph(paragrafo.strip(), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 8))
            
            # ÁREA DE ASSINATURAS
            story.append(Spacer(1, 30))
            
            # Título da seção de assinaturas
            titulo_assinatura = Paragraph("<b>ASSINATURAS:</b>", styles['Heading3'])
            story.append(titulo_assinatura)
            story.append(Spacer(1, 20))
            
            # Verificar se há assinaturas capturadas
            tem_assinatura_paciente = assinatura_paciente and len(assinatura_paciente) > 0
            tem_assinatura_terapeuta = assinatura_terapeuta and len(assinatura_terapeuta) > 0
            
            print(f"📄 [PDF] Assinatura paciente: {'SIM' if tem_assinatura_paciente else 'NÃO'}")
            print(f"📄 [PDF] Assinatura terapeuta: {'SIM' if tem_assinatura_terapeuta else 'NÃO'}")
            
            # Criar tabela de assinaturas lado a lado
            try:
                from reportlab.platypus import Table, TableStyle, Image
                from reportlab.lib.colors import black
                import tempfile
                import os
                
                # Lista para rastrear arquivos temporários a limpar depois
                arquivos_temporarios = []
                
                # Preparar células da tabela
                linha_labels = [Paragraph("<b>Paciente:</b>", styles['Normal']), 
                               Paragraph("<b>Terapeuta:</b>", styles['Normal'])]
                linha_nomes = [Paragraph(dados_pdf['nome_paciente'], styles['Normal']),
                              Paragraph("Dr. Nuno Correia", styles['Normal'])]
                
                # Preparar assinaturas (digitais ou campos vazios)
                cel_paciente = ""
                cel_terapeuta = ""
                
                if tem_assinatura_paciente:
                    try:
                        # Salvar assinatura paciente temporariamente
                        temp_paciente = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        temp_paciente.write(assinatura_paciente)
                        temp_paciente.close()
                        arquivos_temporarios.append(temp_paciente.name)
                        
                        if os.path.exists(temp_paciente.name) and os.path.getsize(temp_paciente.name) > 0:
                            img_paciente = Image(temp_paciente.name, width=120, height=40)
                            cel_paciente = img_paciente
                            print(f"✅ [PDF] Assinatura paciente processada: {temp_paciente.name}")
                        else:
                            print(f"❌ [PDF] Arquivo de assinatura paciente inválido")
                            
                    except Exception as e:
                        print(f"❌ [PDF] Erro ao processar assinatura do paciente: {e}")
                
                if tem_assinatura_terapeuta:
                    try:
                        # Salvar assinatura terapeuta temporariamente
                        temp_terapeuta = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        temp_terapeuta.write(assinatura_terapeuta)
                        temp_terapeuta.close()
                        arquivos_temporarios.append(temp_terapeuta.name)
                        
                        if os.path.exists(temp_terapeuta.name) and os.path.getsize(temp_terapeuta.name) > 0:
                            img_terapeuta = Image(temp_terapeuta.name, width=120, height=40)
                            cel_terapeuta = img_terapeuta
                            print(f"✅ [PDF] Assinatura terapeuta processada: {temp_terapeuta.name}")
                        else:
                            print(f"❌ [PDF] Arquivo de assinatura terapeuta inválido")
                            
                    except Exception as e:
                        print(f"❌ [PDF] Erro ao processar assinatura do terapeuta: {e}")
                
                # Se não há assinaturas digitais, usar campos vazios
                if not cel_paciente:
                    cel_paciente = Paragraph("___________________________", styles['Normal'])
                if not cel_terapeuta:
                    cel_terapeuta = Paragraph("___________________________", styles['Normal'])
                
                linha_assinaturas = [cel_paciente, cel_terapeuta]
                linha_datas = [Paragraph(f"Data: {dados_pdf['data_atual']}", styles['Normal']),
                              Paragraph(f"Data: {dados_pdf['data_atual']}", styles['Normal'])]
                
                # Criar tabela COMPACTA - assinatura e nome próximos com melhor centralização
                dados_tabela = [linha_labels, linha_assinaturas, linha_nomes, linha_datas]
                tabela_assinaturas = Table(dados_tabela, colWidths=[3.2*inch, 3.2*inch])
                
                # Estilo da tabela OTIMIZADO
                estilo_tabela = TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    # COMPACTAR: Reduzir padding entre assinatura e nome
                    ('TOPPADDING', (0, 1), (-1, 1), 2),     # Assinaturas: pouco espaço acima
                    ('BOTTOMPADDING', (0, 1), (-1, 1), 0),  # Assinaturas: zero espaço abaixo
                    ('TOPPADDING', (0, 2), (-1, 2), 0),     # Nomes: zero espaço acima
                    ('BOTTOMPADDING', (0, 2), (-1, 2), 8),  # Nomes: espaço normal abaixo
                    # Manter espaço normal para labels e datas
                    ('TOPPADDING', (0, 0), (-1, 0), 8),     # Labels
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 3), (-1, 3), 8),     # Datas
                    ('BOTTOMPADDING', (0, 3), (-1, 3), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, black),
                ])
                
                tabela_assinaturas.setStyle(estilo_tabela)
                story.append(tabela_assinaturas)
                
                # Gerar PDF
                try:
                    doc.build(story)
                    print(f"✅ [PDF] Consentimento gerado com sucesso: {caminho_pdf}")
                    resultado = True
                    
                except Exception as e:
                    print(f"❌ [PDF] Erro ao gerar documento: {e}")
                    resultado = False
                
                # Limpar arquivos temporários depois de gerar o PDF
                for arquivo in arquivos_temporarios:
                    try:
                        if os.path.exists(arquivo):
                            os.unlink(arquivo)
                            print(f"🗑️ [PDF] Arquivo temporário removido: {arquivo}")
                    except Exception as e:
                        print(f"⚠️ [PDF] Erro ao remover arquivo temporário {arquivo}: {e}")
                
                return resultado
                
            except Exception as e:
                print(f"⚠️ [PDF] Erro ao criar tabela de assinaturas: {e}")
                # Fallback para formato simples
                assinatura_texto = f"""
                <b>Paciente:</b> {dados_pdf['nome_paciente']} _________________ <b>Data:</b> {dados_pdf['data_atual']}<br/><br/>
                <b>Terapeuta:</b> Dr. Nuno Correia _________________ <b>Data:</b> {dados_pdf['data_atual']}
                """
                para_assinatura = Paragraph(assinatura_texto, styles['Normal'])
                story.append(para_assinatura)
                
                # Gerar PDF com fallback
                try:
                    doc.build(story)
                    print(f"✅ [PDF] Consentimento gerado com fallback: {caminho_pdf}")
                    return True
                except Exception as e2:
                    print(f"❌ [PDF] Erro ao gerar documento com fallback: {e2}")
                    return False
                
        except Exception as e:
            print(f"❌ [PDF] Erro geral ao gerar consentimento: {e}")
            return False

    def obter_tipo_consentimento_atual(self):
        """Obtém o tipo de consentimento atualmente selecionado"""
        for tipo, btn in self.botoes_consentimento.items():
            if btn.isChecked():
                return tipo
        return None

    def anular_consentimento_click(self):
        """Anula/revoga o consentimento atual conforme direito RGPD - SISTEMA COMPLETO"""
        # Determinar tipo de consentimento atual
        tipo_atual = self.obter_tipo_consentimento_atual()
        
        if not tipo_atual:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro.")
            return
        
        try:
            from biodesk_dialogs import mostrar_informacao, mostrar_erro
            from PyQt6.QtCore import Qt
            
            # Verificar se temos ID do paciente
            paciente_id = self.paciente_data.get('id')
            if not paciente_id:
                mostrar_erro(self, "Erro", "Não é possível anular o consentimento.\nPaciente precisa de ser guardado primeiro.")
                return
            
            # Obter nome do tipo de consentimento
            tipos_nomes = {
                'naturopatia': 'Naturopatia',
                'osteopatia': 'Osteopatia', 
                'iridologia': 'Iridologia',
                'quantica': 'Medicina Quântica',
                'mesoterapia': 'Mesoterapia Homeopática',
                'rgpd': 'RGPD'
            }
            nome_tipo = tipos_nomes.get(tipo_atual, tipo_atual.title())
            nome_paciente = self.paciente_data.get('nome', 'N/A')
            
            # Diálogo de confirmação com input para motivo
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
            
            # Criar diálogo personalizado
            dialog = QDialog(self)
            dialog.setWindowTitle("Anular Consentimento")
            dialog.setModal(True)
            dialog.setFixedSize(600, 500)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            
            # Título
            titulo = QLabel(f"🗑️ ANULAÇÃO COMPLETA DE CONSENTIMENTO")
            titulo.setStyleSheet("""
                font-size: 16px; font-weight: bold; color: #dc3545;
                padding: 12px; background-color: #f8f9fa; border-radius: 8px;
                text-align: center; margin-bottom: 10px;
            """)
            layout.addWidget(titulo)
            
            # Informações ATUALIZADAS
            info = QLabel(f"""
👤 <b>Paciente:</b> {nome_paciente}
📋 <b>Tipo:</b> {nome_tipo}

⚠️ <b>Esta ação irá:</b>
• Marcar o consentimento como ANULADO na base de dados
• Gerar novo PDF com marca d'água vermelha "ANULADO"
• Substituir o documento original pelo anulado
• Resetar botões de assinatura (voltam a pedir assinatura)
• Atualizar gestão de documentos com "(ANULADO)"
• Registar data e motivo de revogação (RGPD)
            """)
            info.setStyleSheet("font-size: 11px; padding: 12px; background-color: #fff3cd; border-radius: 6px; line-height: 1.4;")
            layout.addWidget(info)
            
            # Campo para motivo
            label_motivo = QLabel("💬 <b>Motivo da anulação (obrigatório):</b>")
            label_motivo.setStyleSheet("font-size: 12px; font-weight: bold;")
            layout.addWidget(label_motivo)
            
            campo_motivo = QTextEdit()
            campo_motivo.setPlaceholderText("Descreva o motivo da revogação do consentimento...")
            campo_motivo.setMaximumHeight(80)
            campo_motivo.setStyleSheet("""
                border: 2px solid #ced4da; border-radius: 6px; padding: 8px;
                font-size: 11px; background-color: white;
            """)
            layout.addWidget(campo_motivo)
            
            # Botões
            botoes_layout = QHBoxLayout()
            botoes_layout.addStretch()
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setFixedSize(120, 40)
            
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            btn_anular = QPushButton("🗑️ Anular Completamente")
            btn_anular.setFixedSize(180, 40)

            def confirmar_anulacao():
                motivo = campo_motivo.toPlainText().strip()
                if not motivo:
                    from biodesk_dialogs import mostrar_aviso
                    mostrar_aviso(dialog, "Motivo Obrigatório", "Por favor, indique o motivo da anulação.")
                    return
                dialog.motivo_anulacao = motivo
                dialog.accept()
            
            btn_anular.clicked.connect(confirmar_anulacao)
            botoes_layout.addWidget(btn_anular)
            
            layout.addLayout(botoes_layout)
            
            # Mostrar diálogo
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
                
            motivo_anulacao = getattr(dialog, 'motivo_anulacao', 'Não especificado')
            
            # PROCESSO COMPLETO DE ANULAÇÃO
            from consentimentos_manager import ConsentimentosManager
            manager = ConsentimentosManager()
            
            print(f"🔄 [ANULAÇÃO] Iniciando anulação completa para {nome_tipo}...")
            
            # 1. Anular na base de dados
            sucesso_bd = manager.anular_consentimento(paciente_id, tipo_atual, motivo_anulacao)
            
            if not sucesso_bd:
                mostrar_erro(self, "Erro", "❌ Falha ao anular na base de dados.\n\nVerifique se existe um consentimento ativo.")
                return
            
            print(f"✅ [ANULAÇÃO] Base de dados atualizada")
            
            # 2. Gerar PDF com marca d'água "ANULADO"
            sucesso_pdf = self._gerar_pdf_anulado(paciente_id, tipo_atual, nome_tipo, motivo_anulacao)
            
            if sucesso_pdf:
                print(f"✅ [ANULAÇÃO] PDF anulado gerado e substituído")
            else:
                print(f"⚠️ [ANULAÇÃO] Falha ao gerar PDF anulado, mas anulação na BD foi bem-sucedida")
            
            # 3. Atualizar interface COMPLETAMENTE
            self._resetar_interface_apos_anulacao(tipo_atual)
            
            # 4. Atualizar lista de documentos se estiver aberta
            if hasattr(self, 'atualizar_lista_documentos'):
                # PROTEÇÃO: Só atualizar uma vez após anulação
                if not hasattr(self, '_anulacao_em_andamento'):
                    self._anulacao_em_andamento = True
                    self.atualizar_lista_documentos()
                    # Remover flag após pequeno delay
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(1000, lambda: delattr(self, '_anulacao_em_andamento') if hasattr(self, '_anulacao_em_andamento') else None)
            
            print(f"✅ [ANULAÇÃO] Interface atualizada")
            
            # 5. Mostrar confirmação final
            from datetime import datetime
            mostrar_informacao(
                self,
                "Consentimento Anulado Completamente",
                f"✅ ANULAÇÃO COMPLETA REALIZADA COM SUCESSO\n\n"
                f"👤 Paciente: {nome_paciente}\n"
                f"📋 Tipo: {nome_tipo}\n"
                f"🗑️ Data de anulação: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                f"💬 Motivo: {motivo_anulacao}\n\n"
                f"📄 Novo PDF gerado: {sucesso_pdf and 'SIM' or 'FALHA'}\n"
                f"🔄 Interface resetada: SIM\n"
                f"🗂️ Gestão de documentos: Atualizada\n\n"
                f"ℹ️ O consentimento foi completamente anulado.\n"
                f"Os botões de assinatura voltaram ao estado inicial."
            )
                    
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao anular consentimento:\n\n{str(e)}")
            print(f"❌ [ANULAÇÃO] Erro: {e}")

    def _gerar_pdf_anulado(self, paciente_id, tipo_consentimento, nome_tipo, motivo_anulacao):
        """Adiciona marca d'água ANULADO ao PDF original e substitui"""
        try:
            import os
            import shutil
            from datetime import datetime
            
            # Encontrar o documento original
            nome_paciente_ficheiro = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            pasta_consentimentos = f"Documentos_Pacientes/{paciente_id}_{nome_paciente_ficheiro}/Consentimentos"
            
            if not os.path.exists(pasta_consentimentos):
                print(f"⚠️ [PDF ANULADO] Pasta não encontrada: {pasta_consentimentos}")
                return False
            
            # Procurar arquivo PDF do tipo específico
            arquivo_original = None
            for arquivo in os.listdir(pasta_consentimentos):
                if arquivo.endswith('.pdf'):
                    # CORREÇÃO: Busca case-insensitive e mais flexível
                    nome_arquivo_lower = arquivo.lower()
                    tipo_lower = tipo_consentimento.lower()
                    
                    # Verificar se o tipo está no nome do arquivo E não é um arquivo já anulado
                    if (tipo_lower in nome_arquivo_lower or 
                        tipo_consentimento.lower().replace('_', ' ') in nome_arquivo_lower or
                        tipo_consentimento.lower().replace(' ', '_') in nome_arquivo_lower) and \
                       'anulado' not in nome_arquivo_lower:
                        arquivo_original = os.path.join(pasta_consentimentos, arquivo)
                        print(f"✅ [PDF ANULADO] Arquivo original encontrado: {arquivo}")
                        break
            
            if not arquivo_original:
                print(f"⚠️ [PDF ANULADO] Arquivo original não encontrado para {tipo_consentimento}")
                print(f"🔄 [PDF ANULADO] Gerando PDF de anulação placeholder...")
                
                # Gerar PDF de anulação mesmo sem original
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo_anulado = f"Consentimento_{nome_tipo}_ANULADO_{timestamp}.pdf"
                caminho_anulado = os.path.join(pasta_consentimentos, nome_arquivo_anulado)
                
                # Gerar PDF placeholder de anulação
                sucesso = self._gerar_pdf_anulacao_placeholder(caminho_anulado, nome_tipo, motivo_anulacao)
                if sucesso:
                    print(f"✅ [PDF ANULADO] Placeholder gerado com sucesso!")
                    return True
                else:
                    print(f"❌ [PDF ANULADO] Falha ao gerar placeholder")
                    return False
            
            print(f"📄 [PDF ANULADO] Arquivo original encontrado: {os.path.basename(arquivo_original)}")
            
            # Tentar usar PyPDF2 para manter o original intacto + marca d'água
            try:
                import PyPDF2
                from PyQt6.QtPrintSupport import QPrinter
                from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
                from PyQt6.QtCore import QMarginsF
                from PyQt6.QtWidgets import QApplication
                import tempfile
                
                # 1. Criar uma marca d'água temporal em PDF
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_watermark:
                    watermark_path = temp_watermark.name
                
                # Criar PDF apenas com a marca d'água
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(watermark_path)
                printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                
                page_layout = QPageLayout()
                page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                page_layout.setOrientation(QPageLayout.Orientation.Portrait)
                page_layout.setMargins(QMarginsF(0, 0, 0, 0))  # Sem margens para marca d'água
                page_layout.setUnits(QPageLayout.Unit.Millimeter)
                printer.setPageLayout(page_layout)
                
                # HTML apenas com marca d'água transparente
                data_anulacao = datetime.now().strftime('%d/%m/%Y %H:%M')
                watermark_html = f"""
                <html>
                <head><meta charset="UTF-8"></head>
                <body style="margin: 0; padding: 0; height: 100vh; position: relative;">
                    <!-- MARCA D'ÁGUA PRINCIPAL -->
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); 
                                font-size: 120px; font-weight: bold; color: rgba(220, 53, 69, 0.4); 
                                z-index: 1000; white-space: nowrap; font-family: Arial, sans-serif;">
                        ANULADO
                    </div>
                    
                    <!-- INFORMAÇÃO DE ANULAÇÃO SUPERIOR -->
                    <div style="position: absolute; top: 10px; left: 10px; right: 10px; 
                                background-color: rgba(248, 215, 218, 0.9); border: 2px solid #dc3545; 
                                border-radius: 8px; padding: 8px; font-size: 9pt; color: #721c24; text-align: center;">
                        <strong>🗑️ DOCUMENTO ANULADO em {data_anulacao}</strong><br>
                        <strong>Motivo:</strong> {motivo_anulacao}
                    </div>
                </body>
                </html>
                """
                
                document = QTextDocument()
                document.setHtml(watermark_html)
                document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
                document.print(printer)
                
                # 2. Aplicar marca d'água ao PDF original
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo_anulado = f"Consentimento_{nome_tipo}_ANULADO_{timestamp}.pdf"
                caminho_anulado = os.path.join(pasta_consentimentos, nome_arquivo_anulado)
                
                # Ler PDF original
                with open(arquivo_original, 'rb') as original_file:
                    original_reader = PyPDF2.PdfReader(original_file)
                    
                    # Ler marca d'água
                    with open(watermark_path, 'rb') as watermark_file:
                        watermark_reader = PyPDF2.PdfReader(watermark_file)
                        watermark_page = watermark_reader.pages[0]
                        
                        # Criar PDF final
                        writer = PyPDF2.PdfWriter()
                        
                        # Aplicar marca d'água a todas as páginas
                        for page in original_reader.pages:
                            # Manter página original e sobrepor marca d'água
                            page.merge_page(watermark_page)
                            writer.add_page(page)
                        
                        # Salvar PDF final
                        with open(caminho_anulado, 'wb') as output_file:
                            writer.write(output_file)
                
                # 3. Limpar arquivo temporário
                os.unlink(watermark_path)
                
                print(f"✅ [PDF ANULADO] PDF original preservado com marca d'água aplicada")
                
            except ImportError:
                print(f"⚠️ [PDF ANULADO] PyPDF2 não disponível, criando cópia simples com marca...")
                # Fallback: copiar e renomear
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo_anulado = f"Consentimento_{nome_tipo}_ANULADO_{timestamp}.pdf"
                caminho_anulado = os.path.join(pasta_consentimentos, nome_arquivo_anulado)
                shutil.copy2(arquivo_original, caminho_anulado)
                
            except Exception as e:
                print(f"⚠️ [PDF ANULADO] Erro com PyPDF2: {e}, usando cópia simples...")
                # Fallback: copiar e renomear
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo_anulado = f"Consentimento_{nome_tipo}_ANULADO_{timestamp}.pdf"
                caminho_anulado = os.path.join(pasta_consentimentos, nome_arquivo_anulado)
                shutil.copy2(arquivo_original, caminho_anulado)
            
            # 4. Remover arquivo original
            try:
                os.remove(arquivo_original)
                print(f"🗑️ [PDF ANULADO] Arquivo original removido: {os.path.basename(arquivo_original)}")
            except Exception as e:
                print(f"⚠️ [PDF ANULADO] Erro ao remover original: {e}")
            
            # 5. Criar metadata para o arquivo anulado
            caminho_meta = caminho_anulado + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                f.write(f"Categoria: 📄 Consentimento (ANULADO)\n")
                f.write(f"Descrição: {nome_tipo} - ANULADO\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y')}\n")
                f.write(f"Data_Anulacao: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write(f"Motivo: {motivo_anulacao}\n")
                f.write(f"Paciente: {self.paciente_data.get('nome', 'N/A')}\n")
                f.write(f"Tipo: consentimento_anulado\n")
            
            print(f"✅ [PDF ANULADO] Gerado com marca d'água: {os.path.basename(caminho_anulado)}")
            return True
            
        except Exception as e:
            print(f"❌ [PDF ANULADO] Erro: {e}")
            return False

    def _gerar_pdf_anulacao_placeholder(self, caminho_anulado, nome_tipo, motivo_anulacao):
        """Gera PDF de anulação quando não há original"""
        try:
            from datetime import datetime
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF, QUrl
            import os
            
            # Configurar printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_anulado)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(20, 20, 20, 20))
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # Dados
            nome_paciente = self.paciente_data.get('nome', 'N/A')
            data_anulacao = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            # Logo
            logo_html = ""
            for logo_file in ['logo.png', 'Biodesk.png']:
                logo_path = os.path.abspath(f'assets/{logo_file}')
                if os.path.exists(logo_path):
                    logo_url = QUrl.fromLocalFile(logo_path).toString()
                    logo_html = f'<img src="{logo_url}" width="80" height="80">'
                    break
            
            # HTML para PDF de anulação placeholder
            html_content = f"""
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Calibri, Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; position: relative;">
                
                <!-- MARCA D'ÁGUA ANULADO -->
                <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); 
                            font-size: 150px; font-weight: bold; color: rgba(220, 53, 69, 0.2); 
                            z-index: 1000; pointer-events: none; white-space: nowrap;">
                    ANULADO
                </div>
                
                <!-- Cabeçalho -->
                <table style="width: 100%; border-bottom: 3px solid #dc3545; padding-bottom: 15px; margin-bottom: 30px;">
                    <tr>
                        <td style="text-align: left; vertical-align: middle;">
                            {logo_html}
                        </td>
                        <td style="text-align: center; vertical-align: middle;">
                            <h1 style="color: #dc3545; margin: 0; font-size: 26pt;">CONSENTIMENTO ANULADO</h1>
                            <p style="color: #dc3545; margin: 5px 0 0 0; font-size: 16pt; font-weight: bold;">{nome_tipo}</p>
                        </td>
                        <td style="text-align: right; vertical-align: middle; width: 100px;">
                            <p style="font-size: 12pt; color: #dc3545; margin: 0; font-weight: bold;">ANULADO<br>{data_anulacao.split(' ')[0]}</p>
                        </td>
                    </tr>
                </table>
                
                <!-- Aviso Principal de Anulação -->
                <div style="background-color: #f8d7da; border: 3px solid #dc3545; border-radius: 10px; padding: 30px; margin-bottom: 30px; text-align: center;">
                    <h1 style="color: #721c24; margin: 0 0 20px 0; font-size: 28pt;">🗑️ DOCUMENTO ANULADO</h1>
                    <p style="margin: 15px 0; color: #721c24; font-size: 14pt; font-weight: bold;">Data de anulação: {data_anulacao}</p>
                    <p style="margin: 15px 0; color: #721c24; font-size: 14pt; font-weight: bold;">Motivo: {motivo_anulacao}</p>
                    <hr style="border: 1px solid #dc3545; margin: 20px 0;">
                    <p style="margin: 15px 0; color: #721c24; font-size: 12pt;">Este consentimento foi revogado pelo paciente conforme direito RGPD.</p>
                    <p style="margin: 15px 0; color: #721c24; font-size: 12pt;">O documento original foi removido e este registo mantém-se para fins de auditoria.</p>
                </div>
                
                <!-- Informações do Paciente -->
                <table style="width: 100%; background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                    <tr>
                        <td style="width: 50%; vertical-align: top; padding-right: 20px;">
                            <h3 style="color: #6c757d; margin-top: 0;">👤 Dados do Paciente:</h3>
                            <p style="margin: 8px 0;"><strong>Nome:</strong> {nome_paciente}</p>
                            <p style="margin: 8px 0;"><strong>Data de Nascimento:</strong> {self.paciente_data.get('data_nascimento', 'N/A')}</p>
                        </td>
                        <td style="width: 50%; vertical-align: top;">
                            <h3 style="color: #6c757d; margin-top: 0;">📋 Detalhes da Anulação:</h3>
                            <p style="margin: 8px 0;"><strong>Tipo de Consentimento:</strong> {nome_tipo}</p>
                            <p style="margin: 8px 0;"><strong>Estado:</strong> <span style="color: #dc3545; font-weight: bold;">ANULADO</span></p>
                        </td>
                    </tr>
                </table>
                
                <!-- Informação Legal -->
                <div style="border: 1px solid #6c757d; border-radius: 5px; padding: 20px; background-color: #f8f9fa;">
                    <h3 style="color: #495057; margin-top: 0;">ℹ️ Informação Legal</h3>
                    <p style="font-size: 11pt; color: #6c757d; line-height: 1.4;">
                        De acordo com o Regulamento Geral sobre a Proteção de Dados (RGPD), o paciente exerceu o seu direito 
                        de retirada do consentimento. O documento original foi removido do sistema, mantendo-se apenas este 
                        registo de anulação para fins de auditoria e cumprimento das obrigações legais.
                    </p>
                    <p style="font-size: 11pt; color: #6c757d; line-height: 1.4;">
                        <strong>Base Legal:</strong> Art.º 7º, n.º 3 do RGPD - Direito de retirada do consentimento
                    </p>
                </div>
                
                <!-- Rodapé -->
                <div style="margin-top: 50px; text-align: center; font-size: 10pt; color: #dc3545; 
                            border-top: 2px solid #dc3545; padding-top: 20px;">
                    <strong>🩺 BIODESK - Sistema de Gestão Clínica</strong><br>
                    <strong>DOCUMENTO ANULADO</strong> - {data_anulacao}<br>
                    Registo mantido para fins de auditoria e cumprimento legal
                </div>
                
            </body>
            </html>
            """
            
            # Gerar PDF
            document = QTextDocument()
            document.setHtml(html_content)
            document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            document.print(printer)
            
            # Criar metadata
            caminho_meta = caminho_anulado + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                f.write(f"Categoria: 📄 Consentimento (ANULADO)\n")
                f.write(f"Descrição: {nome_tipo} - ANULADO (Placeholder)\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y')}\n")
                f.write(f"Data_Anulacao: {data_anulacao}\n")
                f.write(f"Motivo: {motivo_anulacao}\n")
                f.write(f"Paciente: {nome_paciente}\n")
                f.write(f"Tipo: consentimento_anulado\n")
                f.write(f"Observacao: PDF gerado como placeholder - original não encontrado\n")
            
            print(f"✅ [PDF ANULADO] Placeholder gerado: {os.path.basename(caminho_anulado)}")
            return True
            
        except Exception as e:
            print(f"❌ [PDF ANULADO] Erro ao gerar placeholder: {e}")
            return False

    def _resetar_interface_apos_anulacao(self, tipo_consentimento):
        """Reseta completamente a interface após anulação"""
        try:
            print(f"🔄 [RESET] Iniciando reset completo para {tipo_consentimento}")
            
            # 1. Resetar dados das assinaturas armazenadas
            if hasattr(self, 'assinaturas_por_tipo') and tipo_consentimento in self.assinaturas_por_tipo:
                self.assinaturas_por_tipo[tipo_consentimento] = {
                    'paciente': None,
                    'terapeuta': None
                }
                print(f"🔄 [RESET] Assinaturas resetadas para {tipo_consentimento}")
            
            # 2. Resetar botões específicos do tipo (busca dinâmica)
            self._resetar_botoes_assinatura_especificos(tipo_consentimento)
            
            # 3. Atualizar labels gerais de status (se existirem)
            if hasattr(self, 'assinatura_paciente'):
                self.assinatura_paciente.setText("❌ Não assinado")
                self.assinatura_paciente.setStyleSheet("color: #dc3545; font-weight: bold;")
            
            if hasattr(self, 'assinatura_terapeuta'):
                self.assinatura_terapeuta.setText("❌ Não assinado") 
                self.assinatura_terapeuta.setStyleSheet("color: #dc3545; font-weight: bold;")
            
            # 4. Recarregar status de consentimentos (força atualização)
            if hasattr(self, 'carregar_status_consentimentos'):
                self.carregar_status_consentimentos()
            
            # 5. Ocultar botão de anular (já foi anulado)
            if hasattr(self, 'btn_anular') and self.btn_anular:
                self.btn_anular.setVisible(False)
                self.btn_anular.setEnabled(False)
            
            # 6. Limpar canvas de assinaturas
            self._limpar_canvas_assinaturas()
            
            # 7. Forçar atualização visual
            if hasattr(self, 'update'):
                self.update()
            
            print(f"✅ [RESET] Interface completamente resetada após anulação")
            
        except Exception as e:
            print(f"❌ [RESET] Erro ao resetar interface: {e}")

    def _resetar_botoes_assinatura_especificos(self, tipo_consentimento):
        """Resetar botões de assinatura específicos do tipo de consentimento"""
        try:
            # Buscar botões dinamicamente com diferentes padrões de nome
            padroes_botoes = [
                f'btn_assinar_paciente_{tipo_consentimento}',
                f'btn_assinar_terapeuta_{tipo_consentimento}',
                f'assinatura_paciente_{tipo_consentimento}',
                f'assinatura_terapeuta_{tipo_consentimento}',
                f'btn_paciente_{tipo_consentimento}',
                f'btn_terapeuta_{tipo_consentimento}'
            ]
            
            botoes_resetados = 0
            for padrao in padroes_botoes:
                if hasattr(self, padrao):
                    botao = getattr(self, padrao)
                    if botao and hasattr(botao, 'setText'):
                        botao.setText("❌ Não assinado")
                        botao.setStyleSheet("""
                            QPushButton {
                                background-color: #ffffff;
                                color: #dc3545;
                                border: 2px solid #dc3545;
                                border-radius: 8px;
                                padding: 8px;
                                font-weight: bold;
                            }
                        """)
                        if hasattr(botao, 'setChecked'):
                            botao.setChecked(False)
                        botoes_resetados += 1
                        print(f"🔄 [RESET] Botão resetado: {padrao}")
            
            print(f"✅ [RESET] {botoes_resetados} botões resetados para {tipo_consentimento}")
            
        except Exception as e:
            print(f"❌ [RESET] Erro ao resetar botões específicos: {e}")

    def _limpar_canvas_assinaturas(self):
        """Limpar todos os canvas de assinatura encontrados"""
        try:
            canvas_limpos = 0
            padroes_canvas = [
                # Sistema modular substituiu estes canvas individuais
                'canvas_assinatura_paciente',
                'canvas_assinatura_terapeuta',
                'canvas_paciente',
                'canvas_terapeuta'
            ]
            
            for padrao in padroes_canvas:
                if hasattr(self, padrao):
                    canvas = getattr(self, padrao)
                    if canvas and hasattr(canvas, 'clear'):
                        canvas.clear()
                        canvas_limpos += 1
                        print(f"🔄 [RESET] Canvas limpo: {padrao}")
            
            print(f"✅ [RESET] {canvas_limpos} canvas limpos")
            
        except Exception as e:
            print(f"❌ [RESET] Erro ao limpar canvas: {e}")

    def mostrar_historico_consentimentos(self):
        """Mostra o histórico de consentimentos do paciente atual"""
        try:
            from consentimentos_manager import ConsentimentosManager
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
            
            # Verificar se temos ID do paciente
            paciente_id = self.paciente_data.get('id')
            if not paciente_id:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Paciente precisa de ser guardado primeiro para ver o histórico.")
                return
            
            # Obter histórico
            manager = ConsentimentosManager()
            historico = manager.obter_historico_consentimentos(paciente_id)
            
            # Criar diálogo
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Histórico de Consentimentos - {self.paciente_data.get('nome', 'N/A')}")
            dialog.resize(750, 600)  # AUMENTADO: era 600x500, agora 750x600
            dialog.setModal(True)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            titulo = QLabel(f"📋 Histórico de Consentimentos\n👤 {self.paciente_data.get('nome', 'N/A')}")
            titulo.setStyleSheet("""
                font-size: 16px; 
                font-weight: 600; 
                color: #2c3e50; 
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                margin-bottom: 10px;
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Lista de consentimentos
            lista = QListWidget()
            lista.setStyleSheet("""
                QListWidget {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 5px;
                    font-size: 13px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                    border-radius: 4px;
                    margin: 2px;
                }
                QListWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QListWidget::item:hover {
                    background-color: #f5f5f5;
                }
            """)
            
            if historico:
                for item in historico:
                    # Criar texto mais detalhado incluindo assinaturas
                    texto = f"{item['nome_tipo']}\n📅 {item['data']}\n✍️ {item['assinaturas']}\n📊 Status: {item['status']}"
                    list_item = QListWidgetItem(texto)
                    list_item.setData(Qt.ItemDataRole.UserRole, item['id'])  # Guardar ID para possível visualização
                    
                    # Definir ícone baseado no status
                    if item['status'] == 'assinado':
                        list_item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
                    else:
                        list_item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogCancelButton))
                    
                    lista.addItem(list_item)
            else:
                item_vazio = QListWidgetItem("📝 Nenhum consentimento encontrado")
                item_vazio.setFlags(Qt.ItemFlag.NoItemFlags)  # Não selecionável
                lista.addItem(item_vazio)
            
            layout.addWidget(lista)
            
            # Botões
            botoes_layout = QHBoxLayout()
            
            btn_fechar = QPushButton("❌ Fechar")
            self._style_modern_button(btn_fechar, "#95a5a6")
            btn_fechar.clicked.connect(dialog.close)
            botoes_layout.addWidget(btn_fechar)
            
            botoes_layout.addStretch()
            
            if historico:
                btn_visualizar = QPushButton("👁️ Ver Selecionado")
                self._style_modern_button(btn_visualizar, "#3498db")
                btn_visualizar.clicked.connect(lambda: self._visualizar_consentimento_historico(lista, dialog))
                botoes_layout.addWidget(btn_visualizar)
            
            layout.addLayout(botoes_layout)
            
            dialog.exec()
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao mostrar histórico:\n\n{str(e)}")
            print(f"[DEBUG] Erro ao mostrar histórico: {e}")
    
    def _visualizar_consentimento_historico(self, lista, dialog_pai):
        """Gera e abre PDF do consentimento selecionado do histórico"""
        try:
            item_atual = lista.currentItem()
            if not item_atual:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(dialog_pai, "Aviso", "Selecione um consentimento para visualizar.")
                return
            
            consentimento_id = item_atual.data(Qt.ItemDataRole.UserRole)
            
            from consentimentos_manager import ConsentimentosManager
            manager = ConsentimentosManager()
            consentimento = manager.obter_consentimento_por_id(consentimento_id)
            
            if not consentimento:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(dialog_pai, "Erro", "Consentimento não encontrado.")
                return
            
            # Gerar e abrir PDF
            self._gerar_pdf_consentimento_historico(consentimento, dialog_pai)
            
        except Exception as e:
            print(f"❌ Erro ao visualizar consentimento: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(dialog_pai, "Erro", f"Erro ao visualizar consentimento:\n\n{str(e)}")
    
    def _gerar_pdf_consentimento_historico(self, consentimento, dialog_pai):
        """Gera PDF do consentimento do histórico e abre automaticamente"""
        try:
            import os
            import subprocess
            from datetime import datetime
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF, QUrl
            
            # Verificar se consentimento foi anulado para adicionar marca d'água
            status = consentimento.get('status', 'assinado')
            is_anulado = (status == 'anulado')
            data_anulacao = consentimento.get('data_anulacao', '')
            motivo_anulacao = consentimento.get('motivo_anulacao', 'Não especificado')
            
            # Criar pasta do paciente se não existir
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            pasta_paciente = f"pacientes/{nome_paciente}"
            os.makedirs(pasta_paciente, exist_ok=True)
            
            # Nome do arquivo PDF (distinguir se anulado)
            tipo_consentimento = consentimento.get('tipo', 'consentimento')
            data_consentimento = consentimento.get('data_assinatura', '').split(' ')[0].replace('-', '')
            
            if is_anulado:
                nome_arquivo = f"Consentimento_{tipo_consentimento}_{data_consentimento}_ANULADO.pdf"
            else:
                nome_arquivo = f"Consentimento_{tipo_consentimento}_{data_consentimento}.pdf"
                
            caminho_pdf = os.path.join(pasta_paciente, nome_arquivo)
            
            # Verificar se PDF já existe
            if os.path.exists(caminho_pdf):
                print(f"[DEBUG] PDF já existe: {caminho_pdf}")
                # Abrir PDF existente
                try:
                    os.startfile(caminho_pdf)  # Windows
                    print(f"[DEBUG] ✅ PDF aberto: {caminho_pdf}")
                    return
                except:
                    # Fallback para outros sistemas
                    subprocess.run(['xdg-open', caminho_pdf])
                    return
            
            # Configurar printer para gerar PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Configurar margens
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(20, 20, 20, 20))
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # Preparar dados
            nome_paciente_pdf = self.paciente_data.get('nome', 'N/A')
            tipo_consentimento_pdf = consentimento.get('tipo', 'CONSENTIMENTO').upper()
            data_documento = consentimento.get('data_assinatura', '').split(' ')[0]
            conteudo_texto = consentimento.get('conteudo_texto', 'Conteúdo não disponível')
            
            # Preparar assinaturas para PDF
            assinatura_paciente_html = ""
            assinatura_terapeuta_html = ""
            
            # Verificar se existem assinaturas BLOB
            assinatura_paciente_blob = consentimento.get('assinatura_paciente')
            assinatura_terapeuta_blob = consentimento.get('assinatura_terapeuta')
            
            if assinatura_paciente_blob and len(assinatura_paciente_blob) > 10:
                try:
                    os.makedirs('temp', exist_ok=True)
                    sig_path = os.path.abspath('temp/sig_paciente_historico.png')
                    with open(sig_path, 'wb') as f:
                        f.write(assinatura_paciente_blob)
                    sig_url = QUrl.fromLocalFile(sig_path).toString()
                    assinatura_paciente_html = f'<img src="{sig_url}" width="150" height="50">'
                    print("[DEBUG] Assinatura paciente carregada do histórico")
                except Exception as e:
                    print(f"[DEBUG] Erro ao carregar assinatura paciente: {e}")
            
            if assinatura_terapeuta_blob and len(assinatura_terapeuta_blob) > 10:
                try:
                    os.makedirs('temp', exist_ok=True)
                    sig_path = os.path.abspath('temp/sig_terapeuta_historico.png')
                    with open(sig_path, 'wb') as f:
                        f.write(assinatura_terapeuta_blob)
                    sig_url = QUrl.fromLocalFile(sig_path).toString()
                    assinatura_terapeuta_html = f'<img src="{sig_url}" width="150" height="50">'
                    print("[DEBUG] Assinatura terapeuta carregada do histórico")
                except Exception as e:
                    print(f"[DEBUG] Erro ao carregar assinatura terapeuta: {e}")
            
            # Logo
            logo_html = ""
            for logo_file in ['logo.png', 'Biodesk.png']:
                logo_path = os.path.abspath(f'assets/{logo_file}')
                if os.path.exists(logo_path):
                    logo_url = QUrl.fromLocalFile(logo_path).toString()
                    logo_html = f'<img src="{logo_url}" width="80" height="80">'
                    break
            
            # HTML do PDF (com marca d'água se anulado)
            marca_agua_html = ""
            if is_anulado:
                data_anulacao_formatada = data_anulacao.split(' ')[0] if data_anulacao else 'N/A'
                marca_agua_html = f"""
                <!-- MARCA D'ÁGUA ANULADO -->
                <div class="watermark">
                    <div class="watermark-content">
                        🗑️ ANULADO<br>
                        <span style="font-size: 24pt;">{data_anulacao_formatada}</span>
                    </div>
                </div>
                """
            
            html_content = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 15mm 20mm 15mm 20mm;
                    }}
                    
                    body {{
                        font-family: 'Calibri', 'Arial', sans-serif;
                        font-size: 11.5pt;
                        line-height: 1.4;
                        margin: 0;
                        padding: 0;
                        color: #2c3e50;
                        position: relative;
                    }}
                    
                    .watermark {{
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%) rotate(-45deg);
                        z-index: 1000;
                        opacity: 0.3;
                        pointer-events: none;
                    }}
                    
                    .watermark-content {{
                        border: 8px solid #dc3545;
                        background-color: rgba(220, 53, 69, 0.1);
                        padding: 20px 40px;
                        font-size: 48pt;
                        font-weight: bold;
                        color: #dc3545;
                        text-align: center;
                        border-radius: 15px;
                    }}
                    
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #2980b9;
                        padding-bottom: 12pt;
                        margin-bottom: 18pt;
                        page-break-inside: avoid;
                    }}
                    
                    .patient-info {{
                        background-color: #f8f9fa;
                        padding: 10pt;
                        margin-bottom: 18pt;
                        border: 1px solid #dee2e6;
                        border-radius: 4pt;
                        page-break-inside: avoid;
                    }}
                    
                    .content {{
                        line-height: 1.6;
                        text-align: justify;
                        margin: 18pt 0;
                        hyphens: auto;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                    }}
                    
                    .content p {{
                        margin: 8pt 0;
                        orphans: 2;
                        widows: 2;
                    }}
                    
                    .signatures-section {{
                        page-break-inside: avoid;
                        margin-top: 25pt;
                        min-height: 120pt;
                    }}
                    
                    .signatures-title {{
                        text-align: center;
                        color: #2c3e50;
                        margin-bottom: 15pt;
                        font-weight: bold;
                        font-size: 13pt;
                    }}
                    
                    .signature-container {{
                        display: table;
                        width: 80%;
                        margin: 10pt auto 0 auto;
                    }}
                    
                    .signature-box {{
                        display: table-cell;
                        width: 48%;
                        vertical-align: top;
                        text-align: center;
                        padding: 5pt;
                    }}
                    
                    .signature-box:first-child {{
                        border-right: 1px solid #eee;
                        padding-right: 15pt;
                    }}
                    
                    .signature-box:last-child {{
                        padding-left: 15pt;
                    }}
                    
                    .signature-label {{
                        font-weight: bold;
                        margin-bottom: 8pt;
                        font-size: 10pt;
                        color: #34495e;
                    }}
                    
                    .signature-area {{
                        height: 55pt;
                        border-bottom: 2px solid #2c3e50;
                        margin-bottom: 8pt;
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    
                    .signature-area img {{
                        max-width: 140pt;
                        max-height: 45pt;
                        object-fit: contain;
                    }}
                    
                    .signature-name {{
                        margin: 3pt 0;
                        font-size: 9.5pt;
                        font-weight: 500;
                        color: #2c3e50;
                    }}
                    
                    .signature-date {{
                        margin: 2pt 0;
                        font-size: 8.5pt;
                        color: #7f8c8d;
                    }}
                    
                    .footer {{
                        margin-top: 25pt;
                        text-align: center;
                        font-size: 8.5pt;
                        color: #7f8c8d;
                        border-top: 1px solid #ecf0f1;
                        padding-top: 8pt;
                        page-break-inside: avoid;
                    }}
                    
                    .separator {{
                        border: none;
                        border-top: 1px solid #bdc3c7;
                        margin: 20pt 0;
                    }}
                    
                    .anulacao-box {{
                        margin-top: 25pt;
                        padding: 12pt;
                        background-color: #f8d7da;
                        border: 2px solid #dc3545;
                        border-radius: 6pt;
                        page-break-inside: avoid;
                    }}
                    
                    .anulacao-title {{
                        color: #721c24;
                        text-align: center;
                        margin-bottom: 8pt;
                        font-size: 12pt;
                        font-weight: bold;
                    }}
                    
                    .anulacao-content {{
                        font-size: 10pt;
                        color: #721c24;
                    }}
                    
                    /* Garantir que títulos não fiquem órfãos */
                    h1, h2, h3, h4, h5, h6 {{
                        page-break-after: avoid;
                        orphans: 2;
                        widows: 2;
                    }}
                    
                    /* Melhor controle de quebras */
                    .no-break {{
                        page-break-inside: avoid;
                    }}
                </style>
            </head>
            <body>
                
                {marca_agua_html}
                
                <!-- CABEÇALHO -->
                <div class="header no-break">
                    {logo_html}
                    <h2 style="margin: 8pt 0 4pt 0; color: #2980b9; font-size: 15pt;">CONSENTIMENTO INFORMADO</h2>
                    <p style="margin: 0; color: #7f8c8d; font-size: 10pt;">{tipo_consentimento_pdf}</p>
                </div>
                
                <!-- INFORMAÇÕES DO PACIENTE -->
                <div class="patient-info no-break">
                    <p style="margin: 2pt 0;"><strong>Paciente:</strong> {nome_paciente_pdf}</p>
                    <p style="margin: 2pt 0;"><strong>Data:</strong> {data_documento}</p>
                    <p style="margin: 2pt 0;"><strong>Tipo:</strong> {tipo_consentimento_pdf}</p>
                </div>
                
                <!-- CONTEÚDO PRINCIPAL -->
                <div class="content">
                    {self._processar_texto_pdf(conteudo_texto)}
                </div>
                
                <!-- SEPARADOR -->
                <hr class="separator">
                
                <!-- SEÇÃO DE ASSINATURAS (sempre mantida junta) -->
                <div class="signatures-section no-break">
                    <div class="signatures-title">ASSINATURAS</div>
                    
                    <div class="signature-container">
                        <!-- Paciente -->
                        <div class="signature-box">
                            <div class="signature-label">PACIENTE</div>
                            <div class="signature-area">
                                {assinatura_paciente_html}
                            </div>
                            <div class="signature-name">{nome_paciente_pdf}</div>
                            <div class="signature-date">Data: {data_documento}</div>
                        </div>
                        
                        <!-- Terapeuta -->
                        <div class="signature-box">
                            <div class="signature-label">TERAPEUTA</div>
                            <div class="signature-area">
                                {assinatura_terapeuta_html}
                            </div>
                            <div class="signature-name">Dr. Nuno Correia</div>
                            <div class="signature-date">Data: {data_documento}</div>
                        </div>
                    </div>
                </div>
                
                <!-- INFORMAÇÕES DE ANULAÇÃO (se aplicável) -->"""
            
            if is_anulado:
                from datetime import datetime
                data_anulacao_formatada = data_anulacao.split(' ')[0] if data_anulacao else 'N/A'
                hora_anulacao = data_anulacao.split(' ')[1] if ' ' in data_anulacao else 'N/A'
                
                html_content += f"""
                <div class="anulacao-box no-break">
                    <div class="anulacao-title">🗑️ CONSENTIMENTO ANULADO</div>
                    <div class="anulacao-content">
                        <p style="margin: 4pt 0;"><strong>📅 Data de anulação:</strong> {data_anulacao_formatada} às {hora_anulacao}</p>
                        <p style="margin: 4pt 0;"><strong>💬 Motivo:</strong> {motivo_anulacao}</p>
                        <p style="margin: 4pt 0;"><strong>⚖️ Nota legal:</strong> Este documento encontra-se anulado conforme direito de revogação do paciente (RGPD).</p>
                        <p style="margin: 4pt 0;"><strong>📋 Validade:</strong> Este consentimento foi válido desde a data de assinatura até à data de anulação acima indicada.</p>
                    </div>
                </div>
                """
            
            html_content += f"""
                
                <!-- RODAPÉ -->
                <div class="footer no-break">
                    <p style="margin: 1pt 0; font-weight: bold; color: #2980b9;">🩺 BIODESK - Sistema de Gestão Clínica</p>
                    <p style="margin: 1pt 0;">Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>"""
            
            if is_anulado:
                html_content += f"""
                    <p style="margin: 2pt 0; color: #dc3545; font-weight: bold;">⚠️ DOCUMENTO DE CONSENTIMENTO ANULADO</p>"""
            
            html_content += """
                </div>
                
            </body>
            </html>
            """
            
            # 🖨️ GERAR PDF COM CONFIGURAÇÃO OTIMIZADA
            document = QTextDocument()
            document.setHtml(html_content)
            
            # Configurar propriedades avançadas do documento
            document.setUseDesignMetrics(True)
            document.setDocumentMargin(0)  # Margens já definidas no CSS
            
            # Ajustar tamanho da página corretamente
            from PyQt6.QtCore import QSizeF
            page_rect = printer.pageLayout().fullRectPoints()
            page_size = QSizeF(page_rect.width(), page_rect.height())
            document.setPageSize(page_size)
            
            # Renderizar com alta qualidade
            document.print(printer)
            
            # Limpar arquivos temporários
            try:
                for temp_file in ['temp/sig_paciente_historico.png', 'temp/sig_terapeuta_historico.png']:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            except:
                pass
            
            # Abrir PDF automaticamente
            print(f"[DEBUG] PDF gerado: {caminho_pdf}")
            try:
                os.startfile(caminho_pdf)  # Windows
                print(f"[DEBUG] ✅ PDF aberto automaticamente")
            except:
                # Fallback para outros sistemas
                subprocess.run(['xdg-open', caminho_pdf])
            
            # Fechar diálogo do histórico
            dialog_pai.accept()
            
            from biodesk_dialogs import mostrar_informacao
            
            if is_anulado:
                mostrar_informacao(
                    self,
                    "PDF Gerado - Consentimento Anulado",
                    f"⚠️ PDF do consentimento ANULADO gerado!\n\n"
                    f"📁 Localização: {caminho_pdf}\n"
                    f"📄 {tipo_consentimento_pdf}\n"
                    f"👤 {nome_paciente_pdf}\n"
                    f"🗑️ Anulado em: {data_anulacao_formatada if 'data_anulacao_formatada' in locals() else 'N/A'}\n\n"
                    f"ℹ️ Este documento contém marca d'água e informações de anulação."
                )
            else:
                mostrar_informacao(
                    self,
                    "PDF Gerado",
                    f"✅ PDF do consentimento gerado e aberto!\n\n"
                    f"📁 Localização: {caminho_pdf}\n"
                    f"📄 {tipo_consentimento_pdf}\n"
                    f"👤 {nome_paciente_pdf}"
                )
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(dialog_pai, "Erro", f"Erro ao gerar PDF:\n\n{str(e)}")
    
    def _reimprimir_consentimento(self, consentimento, dialog_pai):
        """Re-imprime um consentimento do histórico"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF, QUrl
            
            # Verificar se consentimento foi anulado para adicionar marca d'água
            status = consentimento.get('status', 'assinado')
            is_anulado = (status == 'anulado')
            data_anulacao = consentimento.get('data_anulacao', '')
            motivo_anulacao = consentimento.get('motivo_anulacao', 'Não especificado')
            
            # Escolher local para salvar (distinguir se anulado)
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            if is_anulado:
                nome_arquivo = f"Consentimento_{consentimento['tipo']}_{nome_paciente}_reimpressao_ANULADO.pdf"
            else:
                nome_arquivo = f"Consentimento_{consentimento['tipo']}_{nome_paciente}_reimpressao.pdf"
            
            arquivo, _ = QFileDialog.getSaveFileName(
                dialog_pai, "Guardar Re-impressão PDF", nome_arquivo, "PDF files (*.pdf)"
            )
            
            if not arquivo:
                return
            
            # Configurar printer (usando mesmo método da função original)
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(arquivo)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Configurar margens usando QPageLayout
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(20, 20, 20, 20))
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # Criar documento
            document = QTextDocument()
            
            # HTML para re-impressão (com marca d'água se anulado)
            marca_agua_html = ""
            if is_anulado:
                data_anulacao_formatada = data_anulacao.split(' ')[0] if data_anulacao else 'N/A'
                marca_agua_html = f"""
                <!-- MARCA D'ÁGUA ANULADO -->
                <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); 
                            z-index: 1000; opacity: 0.2; pointer-events: none;">
                    <div style="border: 6px solid #dc3545; background-color: rgba(220, 53, 69, 0.1); 
                                padding: 15px 30px; font-size: 36pt; font-weight: bold; color: #dc3545;
                                text-align: center; border-radius: 10px;">
                        🗑️ ANULADO<br>
                        <span style="font-size: 18pt;">{data_anulacao_formatada}</span>
                    </div>
                </div>
                """
            
            html_content = f"""
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Calibri, Arial, sans-serif; font-size: 12pt; position: relative;">
                
                {marca_agua_html}
                
                <div style="text-align: center; margin-bottom: 30pt;">
                    <h2 style="color: #2980b9;">CONSENTIMENTO INFORMADO (RE-IMPRESSÃO)</h2>
                    <p style="color: #666;">{consentimento['tipo'].upper()}</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 12pt; margin-bottom: 15pt;">
                    <p><strong>Paciente:</strong> {self.paciente_data.get('nome', 'N/A')}</p>
                    <p><strong>Data Original:</strong> {consentimento['data_assinatura']}</p>
                    <p><strong>Re-impressão:</strong> {self.data_atual()}</p>"""
            
            if is_anulado:
                html_content += f"""
                    <p style="color: #dc3545; font-weight: bold;"><strong>⚠️ STATUS:</strong> CONSENTIMENTO ANULADO</p>"""
            
            html_content += f"""
                </div>
                
                <div style="line-height: 1.6;">
                    {consentimento.get('conteudo_html', consentimento.get('conteudo_texto', 'Conteúdo não disponível'))}
                </div>"""
            
            if is_anulado:
                from datetime import datetime
                data_anulacao_formatada = data_anulacao.split(' ')[0] if data_anulacao else 'N/A'
                hora_anulacao = data_anulacao.split(' ')[1] if ' ' in data_anulacao else 'N/A'
                
                html_content += f"""
                
                <div style="margin-top: 30pt; padding: 15pt; background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 8px;">
                    <h3 style="color: #721c24; text-align: center; margin-bottom: 10pt;">🗑️ CONSENTIMENTO ANULADO</h3>
                    <div style="font-size: 11pt; color: #721c24;">
                        <p style="margin: 5pt 0;"><strong>📅 Data de anulação:</strong> {data_anulacao_formatada} às {hora_anulacao}</p>
                        <p style="margin: 5pt 0;"><strong>💬 Motivo:</strong> {motivo_anulacao}</p>
                        <p style="margin: 5pt 0;"><strong>⚖️ Nota legal:</strong> Este documento encontra-se anulado conforme direito de revogação do paciente (RGPD).</p>
                    </div>
                </div>"""
            
            html_content += f"""
                
                <hr style="margin: 30pt 0;">
                <p style="text-align: center; font-size: 10pt; color: #666;">
                    Este documento é uma re-impressão do consentimento original<br>"""
            
            if is_anulado:
                html_content += f"""
                    <span style="color: #dc3545; font-weight: bold;">⚠️ DOCUMENTO DE CONSENTIMENTO ANULADO</span><br>"""
            
            html_content += f"""
                    🩺 BIODESK - Sistema de Gestão Clínica
                </p>
            </body>
            </html>
            """
            
            document.setHtml(html_content)
            document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            document.print(printer)
            
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(
                dialog_pai,
                "Re-impressão Concluída",
                f"✅ Consentimento re-impresso com sucesso!\n\n📁 {arquivo}"
            )
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(dialog_pai, "Erro", f"Erro na re-impressão:\n\n{str(e)}")

    def abrir_assinatura_paciente_click(self):
        """Handler para botão de assinatura do paciente"""
        self.abrir_assinatura_paciente(None)
    
    def abrir_assinatura_terapeuta_click(self):
        """Handler para botão de assinatura do terapeuta"""
        self.abrir_assinatura_terapeuta(None)

    def abrir_assinatura_paciente(self, event):
        """Abre diálogo para assinatura digital do paciente usando sistema modular"""
        try:
            # Usar o sistema modular de assinaturas
            resultado = abrir_dialogo_assinatura(
                parent=self,
                titulo="Assinatura Digital - Paciente",
                nome_pessoa=self.paciente_data.get('nome', 'Paciente'),
                tipo_assinatura="paciente"
            )
            
            if resultado["confirmado"]:
                # Armazenar assinatura por tipo de consentimento
                tipo_atual = getattr(self, 'tipo_consentimento_atual', 'geral')
                if tipo_atual not in self.assinaturas_por_tipo:
                    self.assinaturas_por_tipo[tipo_atual] = {}
                
                self.assinaturas_por_tipo[tipo_atual]['paciente'] = resultado["assinatura_bytes"]
                self.assinatura_paciente_data = resultado["assinatura_bytes"]
                
                print(f"✅ [ASSINATURA] Paciente capturada para tipo '{tipo_atual}': {len(self.assinatura_paciente_data)} bytes")
                
                # Atualizar botão visual
                self.assinatura_paciente.setText("✅ Assinado")
                self.assinatura_paciente.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60 !important; color: white !important; border: none !important;
                        border-radius: 6px; padding: 8px 15px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #229954 !important; }
                """)
                
                # Salvar na base de dados se há consentimento ativo
                if hasattr(self, 'consentimento_ativo') and self.consentimento_ativo:
                    try:
                        from consentimentos_manager import ConsentimentosManager
                        manager = ConsentimentosManager()
                        
                        sucesso = manager.atualizar_assinatura_paciente(
                            self.consentimento_ativo['id'],
                            resultado["assinatura_bytes"],
                            self.paciente_data.get('nome', 'Paciente')
                        )
                        
                        if sucesso:
                            print(f"[DEBUG] ✅ Assinatura do paciente salva na BD")
                        else:
                            print(f"[ERRO] Falha ao salvar assinatura do paciente")
                    except Exception as e:
                        print(f"[ERRO] Erro ao salvar assinatura do paciente: {e}")
                
                print(f"[DEBUG] Assinatura do paciente confirmada: {self.paciente_data.get('nome', 'Paciente')}")
            
        except Exception as e:
            print(f"[ERRO] Erro na assinatura do paciente: {e}")
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
            """)

    def abrir_assinatura_terapeuta(self, event):
        """Abre diálogo para assinatura digital do terapeuta usando sistema modular"""
        try:
            # Usar o sistema modular de assinaturas
            resultado = abrir_dialogo_assinatura(
                parent=self,
                titulo="Assinatura Digital - Terapeuta",
                nome_pessoa="Dr. Nuno Correia",
                tipo_assinatura="terapeuta"
            )
            
            if resultado["confirmado"]:
                # Armazenar assinatura por tipo de consentimento
                tipo_atual = getattr(self, 'tipo_consentimento_atual', 'geral')
                if tipo_atual not in self.assinaturas_por_tipo:
                    self.assinaturas_por_tipo[tipo_atual] = {}
                
                self.assinaturas_por_tipo[tipo_atual]['terapeuta'] = resultado["assinatura_bytes"]
                self.assinatura_terapeuta_data = resultado["assinatura_bytes"]
                
                print(f"✅ [ASSINATURA] Terapeuta capturada para tipo '{tipo_atual}': {len(self.assinatura_terapeuta_data)} bytes")
                
                # Atualizar botão visual
                self.assinatura_terapeuta.setText("✅ Assinado")
                self.assinatura_terapeuta.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60 !important; color: white !important; border: none !important;
                        border-radius: 6px; padding: 8px 15px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #229954 !important; }
                """)
                
                # Salvar na base de dados se há consentimento ativo
                if hasattr(self, 'consentimento_ativo') and self.consentimento_ativo:
                    try:
                        from consentimentos_manager import ConsentimentosManager
                        manager = ConsentimentosManager()
                        
                        sucesso = manager.atualizar_assinatura_terapeuta(
                            self.consentimento_ativo['id'],
                            resultado["assinatura_bytes"],
                            "Dr. Nuno Correia"
                        )
                        
                        if sucesso:
                            print(f"[DEBUG] ✅ Assinatura do terapeuta salva na BD")
                        else:
                            print(f"[ERRO] Falha ao salvar assinatura do terapeuta")
                    except Exception as e:
                        print(f"[ERRO] Erro ao salvar assinatura do terapeuta: {e}")
                
                print("[DEBUG] Assinatura do terapeuta confirmada: Dr. Nuno Correia")
            
        except Exception as e:
            print(f"[ERRO] Erro na assinatura do terapeuta: {e}")

    def _processar_texto_pdf(self, texto):
        """
        Processa texto para PDF com quebras de linha adequadas e formatação otimizada
        """
        if not texto:
            return ""
        
        # Dividir em parágrafos
        paragrafos = texto.split('\n')
        paragrafos_processados = []
        
        for paragrafo in paragrafos:
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue
                
            # Remover quebras de linha inadequadas no meio de frases
            paragrafo = ' '.join(paragrafo.split())
            
            # Adicionar quebras automáticas para linhas muito longas (mais de 80 caracteres)
            if len(paragrafo) > 80:
                # Tentar quebrar em pontuação natural
                import re
                frases = re.split(r'([.!?]\s+)', paragrafo)
                paragrafo_quebrado = ""
                linha_atual = ""
                
                for i, frase in enumerate(frases):
                    if i % 2 == 0:  # Texto da frase
                        if len(linha_atual + frase) > 80 and linha_atual:
                            paragrafo_quebrado += linha_atual.strip() + "<br>"
                            linha_atual = frase
                        else:
                            linha_atual += frase
                    else:  # Pontuação
                        linha_atual += frase
                        
                paragrafo_quebrado += linha_atual
                paragrafo = paragrafo_quebrado
            
            paragrafos_processados.append(f"<p>{paragrafo}</p>")
        
        return "\n".join(paragrafos_processados)

    def gerar_pdf_consentimento(self):
        """Gera PDF do consentimento com formatação robusta e simples"""
        if not hasattr(self, 'tipo_consentimento_atual'):
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro.")
            return
        
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtWidgets import QFileDialog
            from PyQt6.QtCore import QMarginsF, QUrl
            import os
            
            # Escolher local para salvar
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            nome_arquivo = f"Consentimento_{self.tipo_consentimento_atual}_{nome_paciente}.pdf"
            
            arquivo, _ = QFileDialog.getSaveFileName(
                self, "Guardar Consentimento PDF", nome_arquivo, "PDF files (*.pdf)"
            )
            
            if not arquivo:
                return
            
            # Configurar printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(arquivo)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Configurar margens usando QPageLayout (método correto para PyQt6)
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(20, 20, 20, 20))
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # Preparar dados
            nome_paciente = self.paciente_data.get('nome', 'N/A')
            data_documento = self.data_atual()
            tipo_consentimento = self.tipo_consentimento_atual.upper()
            texto_consentimento = self.editor_consentimento.toPlainText()
            
            # 🎯 LOGO - Buscar e preparar caminho correto
            logo_html = ""
            for logo_file in ['logo.png', 'Biodesk.png']:
                logo_path = os.path.abspath(f'assets/{logo_file}')
                if os.path.exists(logo_path):
                    # Converter para URL válida do sistema
                    logo_url = QUrl.fromLocalFile(logo_path).toString()
                    logo_html = f'<img src="{logo_url}" width="80" height="80">'
                    print(f"[DEBUG] Logo encontrado: {logo_path}")
                    break
            
            # 📝 ASSINATURAS - Preparar imagens se existirem
            assinatura_paciente_html = ""
            assinatura_terapeuta_html = ""
            
            # Salvar assinaturas como arquivos temporários usando sistema modular
            if hasattr(self, 'assinatura_paciente_data') and self.assinatura_paciente_data:
                try:
                    os.makedirs('temp', exist_ok=True)
                    sig_path = os.path.abspath('temp/sig_paciente.png')
                    
                    # Salvar bytes da assinatura diretamente
                    with open(sig_path, 'wb') as f:
                        f.write(self.assinatura_paciente_data)
                    
                    sig_url = QUrl.fromLocalFile(sig_path).toString()
                    assinatura_paciente_html = f'<img src="{sig_url}" width="150" height="50">'
                    print(f"[DEBUG] Assinatura paciente salva: {sig_path}")
                except Exception as e:
                    print(f"[DEBUG] Erro assinatura paciente: {e}")
            else:
                print(f"[DEBUG] Assinatura paciente não disponível")
            
            if hasattr(self, 'assinatura_terapeuta_data') and self.assinatura_terapeuta_data:
                try:
                    os.makedirs('temp', exist_ok=True)
                    sig_path = os.path.abspath('temp/sig_terapeuta.png')
                    
                    # Salvar bytes da assinatura diretamente
                    with open(sig_path, 'wb') as f:
                        f.write(self.assinatura_terapeuta_data)
                    
                    sig_url = QUrl.fromLocalFile(sig_path).toString()
                    assinatura_terapeuta_html = f'<img src="{sig_url}" width="150" height="50">'
                    print(f"[DEBUG] Assinatura terapeuta salva: {sig_path}")
                except Exception as e:
                    print(f"[DEBUG] Erro assinatura terapeuta: {e}")
            
            # 🏗️ HTML PARA PDF OTIMIZADO (com controle de quebras de página)
            html_content_pdf = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 15mm 20mm 15mm 20mm;
                    }}
                    
                    body {{
                        font-family: 'Calibri', 'Arial', sans-serif;
                        font-size: 11.5pt;
                        line-height: 1.4;
                        margin: 0;
                        padding: 0;
                        color: #2c3e50;
                    }}
                    
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #2980b9;
                        padding-bottom: 12pt;
                        margin-bottom: 18pt;
                        page-break-inside: avoid;
                    }}
                    
                    .patient-info {{
                        background-color: #f8f9fa;
                        padding: 10pt;
                        margin-bottom: 18pt;
                        border: 1px solid #dee2e6;
                        border-radius: 4pt;
                        page-break-inside: avoid;
                    }}
                    
                    .content {{
                        line-height: 1.6;
                        text-align: justify;
                        margin: 18pt 0;
                        hyphens: auto;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                    }}
                    
                    .content p {{
                        margin: 8pt 0;
                        orphans: 2;
                        widows: 2;
                    }}
                    
                    .signatures-section {{
                        page-break-inside: avoid;
                        margin-top: 25pt;
                        min-height: 120pt;
                    }}
                    
                    .signatures-title {{
                        text-align: center;
                        color: #2c3e50;
                        margin-bottom: 15pt;
                        font-weight: bold;
                        font-size: 13pt;
                    }}
                    
                    .signature-container {{
                        display: table;
                        width: 80%;
                        margin: 10pt auto 0 auto;
                    }}
                    
                    .signature-box {{
                        display: table-cell;
                        width: 48%;
                        vertical-align: top;
                        text-align: center;
                        padding: 5pt;
                    }}
                    
                    .signature-box:first-child {{
                        border-right: 1px solid #eee;
                        padding-right: 15pt;
                    }}
                    
                    .signature-box:last-child {{
                        padding-left: 15pt;
                    }}
                    
                    .signature-label {{
                        font-weight: bold;
                        margin-bottom: 8pt;
                        font-size: 10pt;
                        color: #34495e;
                    }}
                    
                    .signature-area {{
                        height: 55pt;
                        border-bottom: 2px solid #2c3e50;
                        margin-bottom: 8pt;
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    
                    .signature-area img {{
                        max-width: 140pt;
                        max-height: 45pt;
                        object-fit: contain;
                    }}
                    
                    .signature-name {{
                        margin: 3pt 0;
                        font-size: 9.5pt;
                        font-weight: 500;
                        color: #2c3e50;
                    }}
                    
                    .signature-date {{
                        margin: 2pt 0;
                        font-size: 8.5pt;
                        color: #7f8c8d;
                    }}
                    
                    .footer {{
                        margin-top: 25pt;
                        text-align: center;
                        font-size: 8.5pt;
                        color: #7f8c8d;
                        border-top: 1px solid #ecf0f1;
                        padding-top: 8pt;
                        page-break-inside: avoid;
                    }}
                    
                    .separator {{
                        border: none;
                        border-top: 1px solid #bdc3c7;
                        margin: 20pt 0;
                    }}
                    
                    /* Garantir que títulos não fiquem órfãos */
                    h1, h2, h3, h4, h5, h6 {{
                        page-break-after: avoid;
                        orphans: 2;
                        widows: 2;
                    }}
                    
                    /* Melhor controle de quebras */
                    .no-break {{
                        page-break-inside: avoid;
                    }}
                </style>
            </head>
            <body>
                
                <!-- CABEÇALHO -->
                <div class="header no-break">
                    {logo_html}
                    <h2 style="margin: 8pt 0 4pt 0; color: #2980b9; font-size: 15pt;">CONSENTIMENTO INFORMADO</h2>
                    <p style="margin: 0; color: #7f8c8d; font-size: 10pt;">{tipo_consentimento}</p>
                </div>
                
                <!-- INFORMAÇÕES DO PACIENTE -->
                <div class="patient-info no-break">
                    <p style="margin: 2pt 0;"><strong>Paciente:</strong> {nome_paciente}</p>
                    <p style="margin: 2pt 0;"><strong>Data:</strong> {data_documento}</p>
                    <p style="margin: 2pt 0;"><strong>Tipo:</strong> {tipo_consentimento}</p>
                </div>
                
                <!-- CONTEÚDO PRINCIPAL -->
                <div class="content">
                    {self._processar_texto_pdf(texto_consentimento)}
                </div>
                
                <!-- SEPARADOR -->
                <hr class="separator">
                
                <!-- SEÇÃO DE ASSINATURAS (sempre mantida junta) -->
                <div class="signatures-section no-break">
                    <div class="signatures-title">ASSINATURAS</div>
                    
                    <div class="signature-container">
                        <!-- Paciente -->
                        <div class="signature-box">
                            <div class="signature-label">PACIENTE</div>
                            <div class="signature-area">
                                {assinatura_paciente_html}
                            </div>
                            <div class="signature-name">{nome_paciente}</div>
                            <div class="signature-date">Data: {data_documento}</div>
                        </div>
                        
                        <!-- Terapeuta -->
                        <div class="signature-box">
                            <div class="signature-label">TERAPEUTA</div>
                            <div class="signature-area">
                                {assinatura_terapeuta_html}
                            </div>
                            <div class="signature-name">Dr. Nuno Correia</div>
                            <div class="signature-date">Data: {data_documento}</div>
                        </div>
                    </div>
                </div>
                
                <!-- RODAPÉ -->
                <div class="footer no-break">
                    <p style="margin: 1pt 0; font-weight: bold; color: #2980b9;">🩺 BIODESK - Sistema de Gestão Clínica</p>
                    <p style="margin: 1pt 0;">Documento gerado digitalmente em {data_documento}</p>
                </div>
                
            </body>
            </html>
            """

            # 📄 HTML LIMPO (para armazenar na BD - SEM assinaturas visuais)
            html_content_clean = f"""
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body style="font-family: Calibri, Arial, sans-serif; font-size: 12pt; margin: 0; padding: 0;">
                
                <!-- CABEÇALHO -->
                <div style="text-align: center; border-bottom: 2px solid #2980b9; padding-bottom: 15pt; margin-bottom: 20pt;">
                    <h2 style="margin: 10pt 0 5pt 0; color: #2980b9; font-size: 16pt;">CONSENTIMENTO INFORMADO</h2>
                    <p style="margin: 0; color: #666; font-size: 11pt;">{tipo_consentimento}</p>
                </div>
                
                <!-- INFORMAÇÕES DO PACIENTE -->
                <div style="background-color: #f8f9fa; padding: 12pt; margin-bottom: 15pt; border: 1px solid #dee2e6;">
                    <p style="margin: 3pt 0;"><strong>Paciente:</strong> {nome_paciente}</p>
                    <p style="margin: 3pt 0;"><strong>Data:</strong> {data_documento}</p>
                    <p style="margin: 3pt 0;"><strong>Tipo:</strong> {tipo_consentimento}</p>
                </div>
                
                <!-- CONTEÚDO PRINCIPAL -->
                <div style="line-height: 1.6; text-align: justify; margin: 15pt 0;">
                    {texto_consentimento.replace(chr(10), '<br>')}
                </div>
                
            </body>
            </html>
            """
            
            # 🖨️ GERAR PDF COM CONFIGURAÇÃO OTIMIZADA
            document = QTextDocument()
            document.setHtml(html_content_pdf)
            
            # Configurar propriedades avançadas do documento
            document.setUseDesignMetrics(True)
            document.setDocumentMargin(0)  # Margens já definidas no CSS
            
            # Ajustar tamanho da página corretamente
            from PyQt6.QtCore import QSizeF
            page_rect = printer.pageLayout().fullRectPoints()
            page_size = QSizeF(page_rect.width(), page_rect.height())
            document.setPageSize(page_size)
            
            # Renderizar com alta qualidade
            document.print(printer)
            
            # 🧹 LIMPEZA - Remover arquivos temporários
            try:
                for temp_file in ['temp/sig_paciente.png', 'temp/sig_terapeuta.png']:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            except:
                pass
            
            # ✅ SUCESSO
            # Preparar informação sobre assinaturas incluídas
            assinaturas_pdf_info = []
            if assinatura_paciente_html:
                assinaturas_pdf_info.append("👤 Paciente")
            if assinatura_terapeuta_html:
                assinaturas_pdf_info.append("👨‍⚕️ Terapeuta")
            
            assinaturas_pdf_texto = "✅ " + " + ".join(assinaturas_pdf_info) if assinaturas_pdf_info else "❌ Nenhuma incluída"
            
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(
                self, 
                "PDF Gerado com Sucesso", 
                f"✅ Consentimento exportado!\n\n"
                f"📁 {arquivo}\n"
                f"📄 {tipo_consentimento}\n"
                f"👤 {nome_paciente}\n"
                f"🖼️ Logo: {'✅ Incluído' if logo_html else '❌ Não encontrado'}\n"
                f"✍️ Assinaturas: {assinaturas_pdf_texto}"
            )
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro na Geração PDF", f"Erro: {str(e)}")

    def imprimir_consentimento(self):
        """Imprime o consentimento atual"""
        if not hasattr(self, 'tipo_consentimento_atual'):
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro.")
            return
        
        try:
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            from PyQt6.QtGui import QTextDocument
            
            # Configurar impressora
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # Diálogo de impressão
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir Consentimento")
            
            if dialog.exec() == dialog.DialogCode.Accepted:
                # Criar documento com o conteúdo
                document = QTextDocument()
                html_content = self.editor_consentimento.toHtml()
                
                # Adicionar informações de assinatura ao final
                html_content = html_content.replace('</body>', f"""
                    <div style="margin-top: 50px; border-top: 1px solid #ccc; padding-top: 20px;">
                        <h3>Assinaturas</h3>
                        <table width="100%">
                            <tr>
                                <td width="50%" style="text-align: center; padding: 20px;">
                                    <strong>Paciente:</strong><br>
                                    {self.assinatura_paciente.text()}
                                </td>
                                <td width="50%" style="text-align: center; padding: 20px;">
                                    <strong>Terapeuta:</strong><br>
                                    {self.assinatura_terapeuta.text()}
                                </td>
                            </tr>
                        </table>
                    </div>
                </body>
                """)
                
                document.setHtml(html_content)
                document.print(printer)
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(self, "Sucesso", "Documento enviado para impressão!")
                
        except ImportError:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", "Funcionalidade de impressão não disponível.\nPrecisa de instalar: pip install PyQt6-PrintSupport")
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao imprimir:\n\n{str(e)}")

    def limpar_consentimento(self):
        """Limpa o consentimento atual"""
        self.editor_consentimento.clear()
        
        # Desmarcar botões
        for btn in self.botoes_consentimento.values():
            btn.setChecked(False)
        
        # Resetar botões de assinatura para o estado inicial
        self.resetar_botoes_assinatura()
        
        # Mostrar mensagem inicial e ocultar área de edição
        self.editor_consentimento.setVisible(False)
        self.mensagem_inicial.setVisible(True)
        
        # Ocultar botão de anulação
        self.btn_anular.setVisible(False)

    def atualizar_info_paciente_consentimento(self):
        """Atualiza as informações do paciente no aba de consentimentos"""
        if hasattr(self, 'label_paciente'):
            nome = self.paciente_data.get('nome', 'Nome não definido')
            self.label_paciente.setText(f"👤 {nome}")

    def salvar_consentimento_click(self):
        """Salva o consentimento editado na base de dados"""
        try:
            if not hasattr(self, 'tipo_consentimento_atual'):
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro.")
                return
            
            if not hasattr(self, 'paciente_data') or not self.paciente_data.get('id'):
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "É necessário ter um paciente selecionado para salvar o consentimento.")
                return
            
            print(f"[DEBUG] Salvando consentimento {self.tipo_consentimento_atual}...")
            
            # Obter dados do consentimento
            paciente_id = self.paciente_data['id']
            tipo = self.tipo_consentimento_atual
            conteudo_texto = self.editor_consentimento.toPlainText()
            data_atual = self.data_atual_completa()
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            
            # Gerar HTML limpo (SEM assinaturas) para armazenar na BD
            data_documento = self.data_atual()
            tipo_consentimento = tipo.upper()
            
            conteudo_html_limpo = f"""
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body style="font-family: Calibri, Arial, sans-serif; font-size: 12pt; margin: 0; padding: 0;">
                
                <!-- CABEÇALHO -->
                <div style="text-align: center; border-bottom: 2px solid #2980b9; padding-bottom: 15pt; margin-bottom: 20pt;">
                    <h2 style="margin: 10pt 0 5pt 0; color: #2980b9; font-size: 16pt;">CONSENTIMENTO INFORMADO</h2>
                    <p style="margin: 0; color: #666; font-size: 11pt;">{tipo_consentimento}</p>
                </div>
                
                <!-- INFORMAÇÕES DO PACIENTE -->
                <div style="background-color: #f8f9fa; padding: 12pt; margin-bottom: 15pt; border: 1px solid #dee2e6;">
                    <p style="margin: 3pt 0;"><strong>Paciente:</strong> {nome_paciente}</p>
                    <p style="margin: 3pt 0;"><strong>Data:</strong> {data_documento}</p>
                    <p style="margin: 3pt 0;"><strong>Tipo:</strong> {tipo_consentimento}</p>
                </div>
                
                <!-- CONTEÚDO PRINCIPAL -->
                <div style="line-height: 1.6; text-align: justify; margin: 15pt 0;">
                    {conteudo_texto.replace(chr(10), '<br>')}
                </div>
                
            </body>
            </html>
            """
            
            # Salvar na base de dados
            from consentimentos_manager import ConsentimentosManager
            manager = ConsentimentosManager()
            
            import sqlite3
            try:
                conn = sqlite3.connect("pacientes.db")
                cursor = conn.cursor()
                
                # Verificar se já existe consentimento deste tipo para este paciente
                cursor.execute('''
                    SELECT id FROM consentimentos 
                    WHERE paciente_id = ? AND tipo_consentimento = ?
                    ORDER BY data_assinatura DESC 
                    LIMIT 1
                ''', (paciente_id, tipo))
                
                consentimento_existente = cursor.fetchone()
                
                if consentimento_existente:
                    # Atualizar consentimento existente
                    cursor.execute('''
                        UPDATE consentimentos 
                        SET conteudo_html = ?, conteudo_texto = ?, data_assinatura = ?
                        WHERE id = ?
                    ''', (conteudo_html_limpo, conteudo_texto, data_atual, consentimento_existente[0]))
                    
                    consentimento_id = consentimento_existente[0]
                    print(f"[DEBUG] ✅ Consentimento {tipo} atualizado (ID: {consentimento_id})")
                    
                else:
                    # Criar novo consentimento
                    cursor.execute('''
                        INSERT INTO consentimentos 
                        (paciente_id, tipo_consentimento, data_assinatura, conteudo_html, conteudo_texto, 
                         nome_paciente, nome_terapeuta, status, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (paciente_id, tipo, data_atual, conteudo_html_limpo, conteudo_texto, 
                          nome_paciente, "Dr. Nuno Correia", "nao_assinado", data_atual))
                    
                    consentimento_id = cursor.lastrowid
                    print(f"[DEBUG] ✅ Novo consentimento {tipo} criado (ID: {consentimento_id})")
                
                conn.commit()
                
                # Armazenar referência para assinaturas
                self.consentimento_ativo = {'id': consentimento_id, 'tipo': tipo}
                
                # Resetar botões de assinatura (consentimento foi modificado)
                self.resetar_botoes_assinatura()
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(self, "Sucesso", f"Consentimento {tipo.title()} salvo com sucesso!")
                
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            print(f"[ERRO] Erro ao salvar consentimento: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao salvar consentimento:\n\n{str(e)}")

    def data_atual_completa(self):
        """Retorna a data atual no formato completo para a base de dados"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def gerar_pdf_click(self):
        """Gera PDF do consentimento atual"""
        try:
            print("[DEBUG] Gerando PDF do consentimento...")
            # Implementar lógica de geração de PDF aqui se necessário
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, "PDF", "Funcionalidade de PDF será implementada em breve!")
        except Exception as e:
            print(f"[ERRO] Erro ao gerar PDF: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao gerar PDF:\n\n{str(e)}")

    def gerar_pdf_para_assinatura_externa(self):
        """Gera PDF e abre automaticamente para assinatura com importação automática"""
        try:
            if not self.tipo_consentimento_atual:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "⚠️ Selecione um tipo de consentimento primeiro!")
                return
            
            if not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "⚠️ Nenhum paciente selecionado!")
                return
            
            # Obter conteúdo do editor
            conteudo_texto = self.editor_consentimento.toPlainText()
            if not conteudo_texto.strip():
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "⚠️ O consentimento está vazio! Digite o conteúdo primeiro.")
                return
            
            # Preparar paths organizados
            import os
            import shutil
            from datetime import datetime
            
            paciente_id = self.paciente_data.get('id', 'sem_id')
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            tipo_consentimento = self.tipo_consentimento_atual
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Criar estrutura de pastas organizadas
            pasta_paciente = f"documentos/{paciente_id}_{nome_paciente}"
            pasta_temp = f"{pasta_paciente}/temp"
            pasta_final = f"{pasta_paciente}/consentimentos"
            
            os.makedirs(pasta_temp, exist_ok=True)
            os.makedirs(pasta_final, exist_ok=True)
            
            # Caminhos dos arquivos
            arquivo_temp = f"{pasta_temp}/Consentimento_{tipo_consentimento}_{timestamp}_ASSINAR.pdf"
            arquivo_final = f"{pasta_final}/Consentimento_{tipo_consentimento}_{timestamp}.pdf"
            
            print(f"[DEBUG] 📁 Estrutura criada:")
            print(f"[DEBUG] 📄 Temp: {arquivo_temp}")
            print(f"[DEBUG] 📄 Final: {arquivo_final}")
            
            # Gerar PDF base para assinatura
            sucesso = self._gerar_pdf_base_externa(conteudo_texto, arquivo_temp)
            
            if sucesso:
                # Abrir no Adobe Reader
                self._abrir_pdf_assinatura(arquivo_temp, arquivo_final)
                
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Falha ao gerar o PDF!")
            
        except Exception as e:
            print(f"[ERRO] Erro no fluxo de assinatura: {e}")
            import traceback
            traceback.print_exc()
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro no processo:\n\n{str(e)}")

    def _abrir_pdf_assinatura(self, arquivo_temp, arquivo_final):
        """Abre PDF no Adobe Reader e gerencia o fluxo de assinatura"""
        try:
            import subprocess
            import shutil
            import platform
            import time
            
            print(f"[DEBUG] 🖥️ Abrindo PDF para assinatura...")
            
            # Tentar diferentes formas de abrir o Adobe Reader
            adobe_aberto = False
            
            if platform.system() == "Windows":
                # Tentar caminhos comuns do Adobe Reader
                caminhos_adobe = [
                    r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                    r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                    r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
                    r"C:\Program Files (x86)\Adobe\Acrobat DC\Acrobat\Acrobat.exe"
                ]
                
                for caminho in caminhos_adobe:
                    if os.path.exists(caminho):
                        try:
                            subprocess.Popen([caminho, arquivo_temp])
                            adobe_aberto = True
                            print(f"[DEBUG] ✅ Adobe Reader aberto: {caminho}")
                            break
                        except:
                            continue
                
                # Fallback para aplicação padrão
                if not adobe_aberto:
                    try:
                        os.startfile(arquivo_temp)
                        adobe_aberto = True
                        print(f"[DEBUG] ✅ PDF aberto com aplicação padrão")
                    except Exception as e:
                        print(f"[DEBUG] ❌ Erro ao abrir PDF: {e}")
            
            if adobe_aberto:
                # Mostrar dialog de instruções e aguardar confirmação
                self._mostrar_dialog_assinatura_simples(arquivo_temp, arquivo_final)
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Não foi possível abrir o PDF automaticamente.\nAbra manualmente o arquivo:\n" + arquivo_temp)
            
        except Exception as e:
            print(f"[ERRO] Erro ao abrir PDF: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao abrir PDF:\n\n{str(e)}")

    def _mostrar_dialog_assinatura_simples(self, arquivo_temp, arquivo_final):
        """Mostra dialog simplificado para confirmar assinatura"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
            from PyQt6.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Assinatura de Documento")
            dialog.setFixedSize(500, 300)
            dialog.setModal(True)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            
            # Ícone e título
            titulo = QLabel("📝 PDF ABERTO PARA ASSINATURA")
            titulo.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #2980b9;
                padding: 15px;
                text-align: center;
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Instruções
            instrucoes = QLabel("""
<div style='font-size: 14px; line-height: 1.6;'>
<b>📋 INSTRUÇÕES SIMPLES:</b><br><br>
1️⃣ <b>Assine</b> o documento no Adobe Reader/visualizador<br>
2️⃣ <b>Guarde</b> o documento (Ctrl+S ou File → Save)<br>
3️⃣ <b>Feche</b> o Adobe Reader<br>
4️⃣ <b>Clique "✅ Importar"</b> abaixo
</div>
            """)
            instrucoes.setStyleSheet("""
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #2980b9;
            """)
            layout.addWidget(instrucoes)
            
            # Localização do arquivo
            local = QLabel(f"📁 <b>Localização:</b> {arquivo_temp}")
            local.setStyleSheet("font-size: 11px; color: #666; padding: 10px;")
            local.setWordWrap(True)
            layout.addWidget(local)
            
            # Botões
            botoes_layout = QHBoxLayout()
            botoes_layout.addStretch()
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setFixedSize(120, 40)
            
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            btn_importar = QPushButton("✅ Importar Assinado")
            btn_importar.setFixedSize(160, 40)
            
            btn_importar.clicked.connect(lambda: self._executar_importacao_assinada(dialog, arquivo_temp, arquivo_final))
            botoes_layout.addWidget(btn_importar)
            
            layout.addLayout(botoes_layout)
            
            # Mostrar dialog
            dialog.exec()
            
        except Exception as e:
            print(f"[ERRO] Erro no dialog de assinatura: {e}")

    def _executar_importacao_assinada(self, dialog, arquivo_temp, arquivo_final):
        """Executa a importação do PDF assinado"""
        try:
            import shutil
            import os
            
            # Verificar se arquivo ainda existe
            if not os.path.exists(arquivo_temp):
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(dialog, "Erro", "❌ Arquivo não encontrado!\nVerifique se guardou o documento assinado.")
                return
            
            print(f"[DEBUG] 📁 Movendo arquivo:")
            print(f"[DEBUG] 📄 De: {arquivo_temp}")
            print(f"[DEBUG] 📄 Para: {arquivo_final}")
            
            # Mover arquivo para pasta final
            shutil.move(arquivo_temp, arquivo_final)
            
            # Atualizar base de dados
            self._guardar_documento_bd(arquivo_final)
            
            # Fechar dialog
            dialog.accept()
            
            # Atualizar interface
            self.carregar_status_consentimentos()
            
            # Mostrar confirmação
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(
                self,
                "✅ Documento Importado",
                f"📄 Documento assinado e guardado com sucesso!\n\n"
                f"📁 Localização: {arquivo_final}\n\n"
                f"✍️ Consentimento marcado como assinado"
            )
            
            print(f"[DEBUG] ✅ Importação concluída com sucesso!")
            
        except Exception as e:
            print(f"[ERRO] Erro na importação: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(dialog, "Erro", f"❌ Erro ao importar documento:\n\n{str(e)}")

    def _guardar_documento_bd(self, caminho_arquivo):
        """Guarda referência do documento na base de dados"""
        try:
            import sqlite3
            from datetime import datetime
            
            if not hasattr(self, 'consentimento_ativo') or not self.consentimento_ativo:
                # Criar novo registo se não existir
                self.guardar_consentimento()
                return
            
            conn = sqlite3.connect('pacientes.db')
            cursor = conn.cursor()
            
            # Atualizar status do consentimento
            data_assinatura = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE consentimentos 
                SET status = 'assinado', 
                    data_assinatura = ?,
                    arquivo_pdf = ?
                WHERE id = ?
            ''', (data_assinatura, caminho_arquivo, self.consentimento_ativo['id']))
            
            conn.commit()
            conn.close()
            
            print(f"[DEBUG] ✅ BD atualizada - Consentimento {self.tipo_consentimento_atual} marcado como assinado")
            
        except Exception as e:
            print(f"[ERRO] Erro ao atualizar BD: {e}")
            # Adicionar coluna se não existir
            try:
                conn = sqlite3.connect('pacientes.db')
                cursor = conn.cursor()
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN arquivo_pdf TEXT')
                conn.commit()
                conn.close()
                # Tentar novamente
                self._guardar_documento_bd(caminho_arquivo)
            except:
                pass  # Ignorar erro de coluna

    def _gerar_pdf_base_externa(self, conteudo_texto, caminho_arquivo):
        """Gera o PDF base para assinatura externa - SIMPLIFICADO"""
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF
            import os
            
            # Verificar se a pasta existe
            pasta_temp = os.path.dirname(caminho_arquivo)
            if not os.path.exists(pasta_temp):
                os.makedirs(pasta_temp, exist_ok=True)
                print(f"[DEBUG] 📁 Pasta criada: {pasta_temp}")
            
            # Configurar printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_arquivo)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            print(f"[DEBUG] 🖨️ Printer configurado para: {caminho_arquivo}")
            
            # Configurar margens profissionais
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(25, 25, 25, 25))  # 25mm de margem
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # Criar documento com CSS profissional
            document = QTextDocument()
            
            # Dados do documento
            nome_paciente = self.paciente_data.get('nome', '[Nome do Paciente]')
            tipo_consentimento = self.tipo_consentimento_atual.title()
            data_atual = self.data_atual()
            
            # HTML SIMPLIFICADO para máxima compatibilidade
            html_final = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 12pt;
                        line-height: 1.5;
                        color: #333;
                        margin: 20pt;
                        padding: 0;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30pt;
                        padding: 20pt;
                        background-color: #f5f5f5;
                        border: 2pt solid #2980b9;
                        border-radius: 8pt;
                    }}
                    .header h1 {{
                        color: #2980b9;
                        font-size: 18pt;
                        margin: 0 0 10pt 0;
                    }}
                    .info-box {{
                        background-color: #e8f4fd;
                        padding: 15pt;
                        margin: 20pt 0;
                        border-left: 4pt solid #2980b9;
                    }}
                    .conteudo {{
                        margin: 20pt 0;
                        text-align: justify;
                        white-space: pre-line;
                    }}
                    .assinatura-area {{
                        margin-top: 50pt;
                        padding: 20pt;
                        border: 2pt solid #ccc;
                        border-radius: 8pt;
                        background-color: #fafafa;
                    }}
                    .assinatura-linha {{
                        border-bottom: 2pt solid #333;
                        margin: 15pt 0 8pt 0;
                        height: 40pt;
                        width: 200pt;
                        display: inline-block;
                    }}
                    .rodape {{
                        text-align: center;
                        font-size: 10pt;
                        color: #666;
                        margin-top: 30pt;
                        border-top: 1pt solid #ccc;
                        padding-top: 15pt;
                    }}
                </style>
            </head>
            <body>
                
                <!-- CABEÇALHO -->
                <div class="header">
                    <h1>🩺 CONSENTIMENTO DE {tipo_consentimento.upper()}</h1>
                    <p><strong>BIODESK - Sistema de Gestão Clínica</strong></p>
                    <p>Dr. Nuno Correia - Naturopata</p>
                </div>
                
                <!-- INFORMAÇÕES DO PACIENTE -->
                <div class="info-box">
                    <p><strong>📋 Dados do Documento</strong></p>
                    <p><strong>Paciente:</strong> {nome_paciente}</p>
                    <p><strong>Data:</strong> {data_atual}</p>
                    <p><strong>Tipo:</strong> {tipo_consentimento}</p>
                </div>
                
                <!-- CONTEÚDO PRINCIPAL -->
                <div class="conteudo">
                    {conteudo_texto}
                </div>
                
                <!-- ÁREA DE ASSINATURAS -->
                <div class="assinatura-area">
                    <h3 style="color: #2980b9; margin-bottom: 20pt;">✍️ ASSINATURAS</h3>
                    
                    <table width="80%" style="margin: 0 auto;">
                        <tr>
                            <td width="50%" style="text-align: center; padding: 10pt;">
                                <p><strong>PACIENTE</strong></p>
                                <div class="assinatura-linha"></div>
                                <p style="margin-top: 5pt; font-size: 10pt;">
                                    {nome_paciente}<br>
                                    Data: {data_atual}
                                </p>
                            </td>
                            <td width="50%" style="text-align: center; padding: 10pt;">
                                <p><strong>TERAPEUTA</strong></p>
                                <div class="assinatura-linha"></div>
                                <p style="margin-top: 5pt; font-size: 10pt;">
                                    Dr. Nuno Correia<br>
                                    Data: {data_atual}
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <!-- RODAPÉ -->
                <div class="rodape">
                    <p><strong>🩺 BIODESK - Sistema de Gestão Clínica</strong></p>
                    <p>Documento gerado digitalmente em {data_atual}</p>
                    <p>Este documento requer assinatura eletrónica ou física para ser válido</p>
                </div>
                
            </body>
            </html>
            """
            
            print(f"[DEBUG] 📝 HTML preparado com {len(html_final)} caracteres")
            
            document.setHtml(html_final)
            document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            
            # Renderizar o PDF
            print(f"[DEBUG] 🖨️ Iniciando renderização...")
            document.print(printer)
            
            # Verificar se o arquivo foi criado
            if os.path.exists(caminho_arquivo):
                tamanho = os.path.getsize(caminho_arquivo)
                print(f"[DEBUG] ✅ PDF gerado com sucesso: {caminho_arquivo} ({tamanho} bytes)")
                return True
            else:
                print(f"[ERRO] ❌ Arquivo PDF não foi criado: {caminho_arquivo}")
                return False
            
        except Exception as e:
            print(f"[ERRO] ❌ Erro ao gerar PDF base: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _iniciar_monitorizacao_automatica(self, arquivo_original):
        """Inicia monitorização automática da pasta Downloads para PDFs assinados"""
        try:
            import threading
            import time
            from pathlib import Path
            
            # Obter pasta Downloads do utilizador
            pasta_downloads = str(Path.home() / "Downloads")
            nome_base = Path(arquivo_original).stem
            
            print(f"[DEBUG] 🔍 Iniciando monitorização automática...")
            print(f"[DEBUG] 📁 Pasta monitorizada: {pasta_downloads}")
            print(f"[DEBUG] 📄 Procurando arquivos com: {nome_base}")
            
            # Função de monitorização em thread separada
            def monitorizar():
                tempo_inicio = time.time()
                tempo_limite = 600  # 10 minutos
                
                arquivos_conhecidos = set()
                
                # Obter lista inicial de arquivos
                try:
                    for arquivo in os.listdir(pasta_downloads):
                        if arquivo.lower().endswith('.pdf'):
                            arquivos_conhecidos.add(arquivo)
                except:
                    pass
                
                print(f"[DEBUG] 📋 {len(arquivos_conhecidos)} PDFs iniciais na pasta Downloads")
                
                while (time.time() - tempo_inicio) < tempo_limite:
                    try:
                        # Verificar novos arquivos PDF
                        arquivos_atuais = set()
                        for arquivo in os.listdir(pasta_downloads):
                            if arquivo.lower().endswith('.pdf'):
                                arquivos_atuais.add(arquivo)
                        
                        # Detectar novos arquivos
                        novos_arquivos = arquivos_atuais - arquivos_conhecidos
                        
                        for novo_arquivo in novos_arquivos:
                            # Verificar se o nome contém parte do arquivo original
                            if any(parte in novo_arquivo.lower() for parte in [
                                nome_base.lower(),
                                'consentimento',
                                'assinado',
                                'signed'
                            ]):
                                caminho_completo = os.path.join(pasta_downloads, novo_arquivo)
                                
                                # Aguardar um pouco para garantir que o arquivo foi completamente salvo
                                time.sleep(2)
                                
                                # Verificar se o arquivo não está sendo usado
                                if self._arquivo_disponivel(caminho_completo):
                                    print(f"[DEBUG] 🎯 PDF assinado detectado: {novo_arquivo}")
                                    
                                    # Processar automaticamente
                                    self._processar_pdf_assinado_automatico(caminho_completo, arquivo_original)
                                    return  # Parar monitorização após sucesso
                        
                        arquivos_conhecidos = arquivos_atuais
                        time.sleep(2)  # Verificar a cada 2 segundos
                        
                    except Exception as e:
                        print(f"[ERRO] Erro na monitorização: {e}")
                        time.sleep(5)
                
                print(f"[DEBUG] ⏰ Monitorização automática expirou após 10 minutos")
            
            # Iniciar thread de monitorização
            thread_monitor = threading.Thread(target=monitorizar, daemon=True)
            thread_monitor.start()
            
        except Exception as e:
            print(f"[ERRO] Erro ao iniciar monitorização: {e}")

    def _arquivo_disponivel(self, caminho):
        """Verifica se um arquivo está disponível para leitura (não sendo usado)"""
        try:
            with open(caminho, 'rb') as f:
                f.read(1)
            return True
        except:
            return False

    def _processar_pdf_assinado_automatico(self, arquivo_assinado, arquivo_original):
        """Processa automaticamente o PDF assinado detectado"""
        try:
            from PyQt6.QtCore import QTimer
            
            def executar_processamento():
                try:
                    print(f"[DEBUG] 🚀 Processando PDF assinado automaticamente...")
                    
                    # Guardar documento na pasta do paciente
                    sucesso = self._guardar_documento_paciente(arquivo_assinado, arquivo_original)
                    
                    if sucesso:
                        # Marcar consentimento como assinado
                        self._marcar_consentimento_assinado()
                        
                        # Atualizar interface
                        self.carregar_status_consentimentos()
                        
                        # Mostrar notificação de sucesso
                        from biodesk_dialogs import mostrar_informacao
                        mostrar_informacao(
                            self,
                            "✅ PDF Importado Automaticamente",
                            f"🎉 **PROCESSO CONCLUÍDO COM SUCESSO!**\n\n"
                            f"✅ PDF assinado detectado e importado\n"
                            f"📁 Documento organizado na pasta do paciente\n"
                            f"✍️ Consentimento marcado como assinado\n"
                            f"🗂️ Status atualizado na interface\n\n"
                            f"📄 Arquivo: {os.path.basename(arquivo_assinado)}"
                        )
                        
                        # Remover arquivo original temporário
                        try:
                            if os.path.exists(arquivo_original):
                                os.remove(arquivo_original)
                                print(f"[DEBUG] 🗑️ Arquivo temporário removido")
                        except:
                            pass
                        
                    else:
                        print(f"[ERRO] Falha ao guardar documento do paciente")
                        
                except Exception as e:
                    print(f"[ERRO] Erro no processamento automático: {e}")
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(
                        self,
                        "Erro no Processamento Automático", 
                        f"❌ Erro ao processar PDF assinado:\n\n{str(e)}\n\n"
                        f"💡 Pode importar manualmente através do menu."
                    )
            
            # Usar QTimer para executar na thread principal do PyQt
            QTimer.singleShot(100, executar_processamento)
            
        except Exception as e:
            print(f"[ERRO] Erro no processamento automático: {e}")

    def _mostrar_dialog_importar_pdf(self, arquivo_temp):
        """Mostra dialog para importar PDF assinado"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Importar PDF Assinado")
            dialog.setFixedSize(450, 200)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            
            # Informação
            info_label = QLabel(
                "📄 Importe o PDF assinado para finalizar o processo:\n\n"
                "• Selecione o arquivo PDF que foi assinado\n"
                "• O documento será guardado na pasta do paciente\n"
                "• O consentimento ficará marcado como assinado"
            )
            info_label.setStyleSheet("font-size: 12px; padding: 15px; background-color: #f8f9fa; border-radius: 6px;")
            layout.addWidget(info_label)
            
            # Botões
            botoes_layout = QHBoxLayout()
            botoes_layout.addStretch()
            
            btn_importar = QPushButton("📁 Selecionar PDF Assinado")
            btn_importar.setFixedSize(180, 35)
            
            btn_importar.clicked.connect(lambda: self._selecionar_e_importar_pdf(dialog, arquivo_temp))
            botoes_layout.addWidget(btn_importar)
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setFixedSize(100, 35)
            
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            layout.addLayout(botoes_layout)
            
            dialog.exec()
            
        except Exception as e:
            print(f"[ERRO] Erro no dialog de importação: {e}")

    def _selecionar_e_importar_pdf(self, dialog, arquivo_temp):
        """Seleciona e importa o PDF assinado"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            # Selecionar arquivo PDF assinado
            arquivo_assinado, _ = QFileDialog.getOpenFileName(
                dialog,
                "Selecionar PDF Assinado",
                "",
                "PDF files (*.pdf)"
            )
            
            if arquivo_assinado:
                # Guardar documento na pasta do paciente
                sucesso = self._guardar_documento_paciente(arquivo_assinado, arquivo_temp)
                
                if sucesso:
                    dialog.accept()
                    
                    # Marcar consentimento como assinado na base de dados
                    self._marcar_consentimento_assinado()
                    
                    from biodesk_dialogs import mostrar_informacao
                    mostrar_informacao(
                        self,
                        "Importação Concluída",
                        f"✅ PDF assinado importado com sucesso!\n\n"
                        f"📁 O documento foi guardado na pasta do paciente\n"
                        f"✍️ Consentimento marcado como assinado"
                    )
                    
                    # Atualizar status visual
                    self.carregar_status_consentimentos()
                    
        except Exception as e:
            print(f"[ERRO] Erro ao importar PDF: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(dialog, "Erro", f"❌ Erro ao importar PDF:\n\n{str(e)}")

    def _guardar_documento_paciente(self, arquivo_assinado, arquivo_temp):
        """Guarda o documento assinado na pasta do paciente"""
        try:
            import os
            import shutil
            from datetime import datetime
            
            # Criar estrutura de pastas do paciente
            paciente_id = self.paciente_data.get('id', 'sem_id')
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            
            pasta_paciente = f"documentos/{paciente_id}_{nome_paciente}"
            pasta_consentimentos = os.path.join(pasta_paciente, "consentimentos")
            
            os.makedirs(pasta_consentimentos, exist_ok=True)
            
            # Nome final do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tipo_consentimento = self.tipo_consentimento_atual
            nome_final = f"Consentimento_{tipo_consentimento}_ASSINADO_{timestamp}.pdf"
            caminho_final = os.path.join(pasta_consentimentos, nome_final)
            
            # Copiar arquivo assinado
            shutil.copy2(arquivo_assinado, caminho_final)
            
            # Remover arquivo temporário
            if os.path.exists(arquivo_temp):
                os.remove(arquivo_temp)
            
            print(f"[DEBUG] ✅ Documento guardado: {caminho_final}")
            return True
            
        except Exception as e:
            print(f"[ERRO] Erro ao guardar documento: {e}")
            return False

    def _marcar_consentimento_assinado(self):
        """Marca o consentimento como assinado na base de dados"""
        try:
            if not hasattr(self, 'consentimento_ativo') or not self.consentimento_ativo:
                # Criar novo registo se não existir
                self.guardar_consentimento()
                return
            
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('pacientes.db')
            cursor = conn.cursor()
            
            # Atualizar status do consentimento
            data_assinatura = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE consentimentos 
                SET status = 'assinado', data_assinatura = ?
                WHERE id = ?
            ''', (data_assinatura, self.consentimento_ativo['id']))
            
            conn.commit()
            conn.close()
            
            print(f"[DEBUG] ✅ Consentimento {self.tipo_consentimento_atual} marcado como assinado")
            
        except Exception as e:
            print(f"[ERRO] Erro ao marcar consentimento como assinado: {e}")

    def importar_pdf_manual(self):
        """Permite importar manualmente um PDF assinado"""
        try:
            if not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "⚠️ Nenhum paciente selecionado!")
                return
            
            from PyQt6.QtWidgets import QFileDialog
            
            # Selecionar arquivo PDF assinado
            arquivo_assinado, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar PDF Assinado",
                str(Path.home() / "Downloads"),  # Iniciar na pasta Downloads
                "PDF files (*.pdf)"
            )
            
            if arquivo_assinado:
                # Processar o arquivo selecionado
                sucesso = self._guardar_documento_paciente(arquivo_assinado, "")
                
                if sucesso:
                    # Marcar consentimento como assinado
                    self._marcar_consentimento_assinado()
                    
                    # Atualizar interface
                    self.carregar_status_consentimentos()
                    
                    from biodesk_dialogs import mostrar_informacao
                    mostrar_informacao(
                        self,
                        "PDF Importado com Sucesso",
                        f"✅ **PDF IMPORTADO MANUALMENTE**\n\n"
                        f"📁 Documento organizado na pasta do paciente\n"
                        f"✍️ Consentimento marcado como assinado\n"
                        f"🗂️ Status atualizado na interface\n\n"
                        f"📄 Arquivo: {os.path.basename(arquivo_assinado)}"
                    )
                else:
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(self, "Erro", "❌ Erro ao importar o arquivo PDF.")
                    
        except Exception as e:
            print(f"[ERRO] Erro na importação manual: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao importar PDF:\n\n{str(e)}")

    # ========================================================================
    # MÉTODOS DA DECLARAÇÃO DE SAÚDE
    # ========================================================================
    
    def _criar_template_declaracao_saude(self):
        """Cria template da declaração de saúde simplificado com dropdowns"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Declaração de Saúde</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(135deg, #2e7d2e, #4CAF50);
                    color: white;
                    text-align: center;
                    padding: 30px;
                }
                
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: bold;
                }
                
                .content {
                    padding: 30px;
                }
                
                .section {
                    margin-bottom: 30px;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 20px;
                    background: #fafafa;
                }
                
                .section h2 {
                    color: #2e7d2e;
                    font-size: 18px;
                    margin: 0 0 15px 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e0e0e0;
                }
                
                .question {
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .question-text {
                    flex: 1;
                    font-weight: 500;
                    color: #333;
                }
                
                .dropdown {
                    min-width: 100px;
                    padding: 8px 12px;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    font-size: 14px;
                    background: white;
                    transition: border-color 0.3s;
                }
                
                .dropdown:focus {
                    border-color: #4CAF50;
                    outline: none;
                }
                
                .detail-input {
                    flex: 1;
                    padding: 8px 12px;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    font-size: 14px;
                    margin-left: 10px;
                }
                
                .detail-input:focus {
                    border-color: #4CAF50;
                    outline: none;
                }
                
                .declaration {
                    background: #fff3cd;
                    border: 2px solid #ffeaa7;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }
                
                .declaration h3 {
                    color: #856404;
                    margin: 0 0 15px 0;
                }
                
                .signature-area {
                    border: 2px dashed #ddd;
                    height: 60px;
                    border-radius: 8px;
                    margin: 10px 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #999;
                    cursor: pointer;
                }
                
                .buttons {
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    border-top: 1px solid #e0e0e0;
                }
                
                .btn {
                    padding: 12px 30px;
                    border: none;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    margin: 0 10px;
                    transition: all 0.3s;
                }
                
                .btn-save {
                    background: linear-gradient(135deg, #4CAF50, #45a049);
                    color: white;
                }
                
                .btn-save:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
                }
                
                .btn-cancel {
                    background: linear-gradient(135deg, #f44336, #da190b);
                    color: white;
                }
                
                .btn-cancel:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(244, 67, 54, 0.4);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 DECLARAÇÃO DE SAÚDE</h1>
                    <p>Questionário médico para consulta de naturopatia</p>
                </div>
                
                <div class="content">
                    <form id="declaracao-form">
                        
                        <!-- 1. Doenças Metabólicas -->
                        <div class="section">
                            <h2>🍯 Doenças Metabólicas</h2>
                            
                            <div class="question">
                                <span class="question-text">Diabetes:</span>
                                <select name="diabetes" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="diabetes-detalhe" class="detail-input" placeholder="Detalhe (tipo, medicação)">
                            </div>
                            
                            <div class="question">
                                <span class="question-text">Problemas da tiróide:</span>
                                <select name="tiroide" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="tiroide-detalhe" class="detail-input" placeholder="Detalhe">
                            </div>
                        </div>
                        
                        <!-- 2. Doenças Cardiovasculares -->
                        <div class="section">
                            <h2>❤️ Doenças Cardiovasculares</h2>
                            
                            <div class="question">
                                <span class="question-text">Hipertensão arterial:</span>
                                <select name="hipertensao" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="hipertensao-detalhe" class="detail-input" placeholder="Detalhe (valores, medicação)">
                            </div>
                            
                            <div class="question">
                                <span class="question-text">Doenças do coração:</span>
                                <select name="coracao" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="coracao-detalhe" class="detail-input" placeholder="Detalhe">
                            </div>
                        </div>
                        
                        <!-- 3. Alergias -->
                        <div class="section">
                            <h2>🚨 Alergias e Intolerâncias</h2>
                            
                            <div class="question">
                                <span class="question-text">Alergias a medicamentos:</span>
                                <select name="alergias-medicamentos" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="alergias-medicamentos-detalhe" class="detail-input" placeholder="Detalhe">
                            </div>
                            
                            <div class="question">
                                <span class="question-text">Alergias alimentares:</span>
                                <select name="alergias-alimentares" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="alergias-alimentares-detalhe" class="detail-input" placeholder="Detalhe">
                            </div>
                        </div>
                        
                        <!-- 4. Medicação Atual -->
                        <div class="section">
                            <h2>💊 Medicação Atual</h2>
                            
                            <div class="question">
                                <span class="question-text">Toma medicação atualmente:</span>
                                <select name="medicacao" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="medicacao-detalhe" class="detail-input" placeholder="Detalhe (nome, dose, frequência)">
                            </div>
                        </div>
                        
                        <!-- 5. Histórico Familiar -->
                        <div class="section">
                            <h2>👨‍👩‍👧‍👦 Histórico Familiar</h2>
                            
                            <div class="question">
                                <span class="question-text">Histórico familiar de diabetes:</span>
                                <select name="familiar-diabetes" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="familiar-diabetes-detalhe" class="detail-input" placeholder="Detalhe">
                            </div>
                            
                            <div class="question">
                                <span class="question-text">Histórico familiar de doenças cardíacas:</span>
                                <select name="familiar-cardio" class="dropdown">
                                    <option value="">Selecionar</option>
                                    <option value="sim">Sim</option>
                                    <option value="nao">Não</option>
                                </select>
                                <input type="text" name="familiar-cardio-detalhe" class="detail-input" placeholder="Detalhe">
                            </div>
                        </div>
                        
                        <!-- Declaração -->
                        <div class="declaration">
                            <h3>📝 Declaração</h3>
                            <p><strong>DECLARO</strong> que as informações prestadas são verdadeiras e completas, 
                            e assumo total responsabilidade pelas mesmas. Compreendo que a ocultação de informações 
                            relevantes pode prejudicar o meu tratamento.</p>
                            
                            <p><strong>AUTORIZO</strong> o profissional de saúde a utilizar as informações aqui fornecidas 
                            para fins terapêuticos e de acompanhamento.</p>
                            
                            <div style="margin-top: 20px;">
                                <label><strong>Data:</strong></label>
                                <input type="date" id="data-declaracao" style="margin-left: 10px; padding: 5px;">
                            </div>
                            
                            <div style="margin-top: 15px;">
                                <label><strong>Local:</strong></label>
                                <input type="text" id="local-declaracao" placeholder="Local da assinatura" 
                                       style="margin-left: 10px; padding: 5px; width: 200px;">
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <strong>Assinatura do Paciente:</strong>
                                <div id="assinatura-paciente" class="signature-area">
                                    Clique para assinar
                                </div>
                            </div>
                            
                            <div style="margin-top: 15px;">
                                <strong>Assinatura do Terapeuta:</strong>
                                <div id="assinatura-terapeuta" class="signature-area">
                                    Clique para assinar
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                
                <div class="buttons">
                    <button type="button" class="btn btn-save" onclick="submeterFormulario()">
                        💾 Guardar Declaração
                    </button>
                    <button type="button" class="btn btn-cancel" onclick="cancelarDeclaracao()">
                        ❌ Cancelar
                    </button>
                </div>
            </div>
            
            <script>
                // Configurar data atual
                document.getElementById('data-declaracao').value = new Date().toISOString().split('T')[0];
                
                // Função para capturar dados
                function capturarDados() {
                    const dados = {};
                    
                    // Capturar dropdowns
                    document.querySelectorAll('select').forEach(select => {
                        if(select.value) {
                            dados[select.name] = select.value;
                        }
                    });
                    
                    // Capturar inputs
                    document.querySelectorAll('input[type="text"], input[type="date"]').forEach(input => {
                        if(input.value.trim()) {
                            dados[input.id || input.name] = input.value;
                        }
                    });
                    
                    return dados;
                }
                
                // Submeter formulário
                function submeterFormulario() {
                    const dados = capturarDados();
                    const dataDeclaracao = document.getElementById('data-declaracao').value;
                    const localDeclaracao = document.getElementById('local-declaracao').value;
                    
                    if(!dataDeclaracao || !localDeclaracao) {
                        alert('Por favor, preencha a data e o local da declaração.');
                        return;
                    }
                    
                    // Verificar se algum campo foi preenchido
                    if(Object.keys(dados).length === 0) {
                        alert('Por favor, preencha pelo menos uma resposta antes de guardar.');
                        return;
                    }
                    
                    // Chamar função Python
                    if(window.pywebview && window.pywebview.api) {
                        window.pywebview.api.salvar_dados_declaracao(dados);
                    } else {
                        console.log('Dados capturados:', dados);
                        alert('Formulário preenchido com sucesso!');
                    }
                }
                
                function cancelarDeclaracao() {
                    if(confirm('Tem a certeza que quer cancelar? Todos os dados serão perdidos.')) {
                        if(window.pywebview && window.pywebview.api) {
                            window.pywebview.api.cancelar_declaracao();
                        } else {
                            window.close();
                        }
                    }
                }
                
                // Configurar áreas de assinatura
                document.getElementById('assinatura-paciente').onclick = function() {
                    this.style.backgroundColor = '#e8f5e8';
                    this.textContent = 'Assinatura do paciente capturada';
                    if(window.pywebview && window.pywebview.api) {
                        window.pywebview.api.abrir_assinatura_paciente();
                    }
                };
                
                document.getElementById('assinatura-terapeuta').onclick = function() {
                    this.style.backgroundColor = '#e8f5e8';
                    this.textContent = 'Assinatura do terapeuta capturada';
                    if(window.pywebview && window.pywebview.api) {
                        window.pywebview.api.abrir_assinatura_terapeuta();
                    }
                };
            </script>
        </body>
        </html>
        """
        return template

    def imprimir_declaracao_saude(self):
        """Imprime a declaração de estado de saúde"""
        try:
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            from PyQt6.QtGui import QTextDocument
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPrinter.Orientation.Portrait)
            
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir Declaração de Estado de Saúde")
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Criar documento
                document = QTextDocument()
                
                # Preparar HTML para impressão
                html_content = self.texto_declaracao_editor.toHtml()
                
                # Adicionar cabeçalho e rodapé
                html_final = f"""
                <html>
                <head><meta charset="UTF-8"></head>
                <body style="font-family: Calibri, Arial, sans-serif;">
                    {html_content}
                    
                    <hr style="margin: 30pt 0;">
                    <p style="text-align: center; font-size: 10pt; color: #666;">
                        🩺 BIODESK - Sistema de Gestão Clínica<br>
                        Declaração de Estado de Saúde - {self.data_atual()}
                    </p>
                </body>
                </html>
                """
                
                document.setHtml(html_final)
                document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
                document.print(printer)
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(
                    self,
                    "Impressão Enviada",
                    "✅ Declaração de Estado de Saúde enviada para impressão!"
                )
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao imprimir:\n\n{str(e)}")

    def assinar_e_guardar_declaracao_saude(self):
        """Função NOVA: Sistema completo de assinatura para Paciente + Terapeuta"""
        try:
            if not self.paciente_data:
                BiodeskMessageBox.warning(self, "Aviso", "⚠️ Nenhum paciente selecionado.")
                return
                
            # Imports necessários
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF, QUrl
            import os
            from datetime import datetime
            from consentimentos_manager import ConsentimentosManager
            
            # Obter dados do paciente
            paciente_id = self.paciente_data.get('id')
            nome_paciente = self.paciente_data.get('nome', '[NOME_PACIENTE]')
            data_nascimento = self.paciente_data.get('data_nascimento', '[DATA_NASCIMENTO]')
            data_atual = self.data_atual()
            
            # Gerar data por extenso
            try:
                meses = [
                    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
                ]
                agora = datetime.now()
                data_atual_por_extenso = f"{agora.day} de {meses[agora.month - 1]} de {agora.year}"
            except:
                data_atual_por_extenso = data_atual
            
            # Obter dados do formulário se disponíveis
            dados_formulario = getattr(self, 'dados_formulario_capturados', None) or globals().get('dados_formulario')
            
            # PROCESSAR DADOS DAS CHECKBOXES CAPTURADAS
            dados_formulario_html = ""
            if dados_formulario:
                print(f"[DEBUG] Processando dados do formulário")
                
                # Criar HTML formatado com os dados do formulário
                dados_formulario_html = "<div style='margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-radius: 8px;'>"
                dados_formulario_html += "<h3 style='color: #4CAF50; margin-top: 0;'>📋 Respostas do Formulário</h3>"
                
                # 1. PROCESSAR INPUTS COM TEXTO (detalhes importantes)
                if 'inputs' in dados_formulario:
                    inputs_preenchidos = {k: v for k, v in dados_formulario['inputs'].items() if v and v.strip()}
                    if inputs_preenchidos:
                        dados_formulario_html += "<h4 style='color: #2e7d2e; margin: 15px 0 10px 0;'>📝 Detalhes Fornecidos</h4>"
                        dados_formulario_html += "<ul style='margin: 5px 0 15px 20px;'>"
                        
                        for nome, valor in inputs_preenchidos.items():
                            # Mapear nomes técnicos para nomes legíveis
                            nomes_legveis = {
                                'detalhes-cirurgias': 'Detalhes das Cirurgias',
                                'detalhes-fraturas': 'Detalhes das Fraturas',
                                'detalhes-implantes': 'Detalhes dos Implantes',
                                'qual-anticoagulante': 'Qual Anticoagulante',
                                'semanas-gestacao': 'Semanas de Gestação'
                            }
                            nome_legivel = nomes_legveis.get(nome, nome.replace('-', ' ').replace('_', ' ').title())
                            dados_formulario_html += f"<li style='margin: 8px 0;'><strong>{nome_legivel}:</strong> {valor}</li>"
                        
                        dados_formulario_html += "</ul>"
                
                # 2. PROCESSAR TEXTAREAS
                if 'textareas' in dados_formulario:
                    textareas_preenchidas = {k: v for k, v in dados_formulario['textareas'].items() if v and v.strip()}
                    if textareas_preenchidas:
                        dados_formulario_html += "<h4 style='color: #2e7d2e; margin: 15px 0 10px 0;'>📄 Informações Adicionais</h4>"
                        
                        for nome, valor in textareas_preenchidas.items():
                            nomes_legveis = {
                                'detalhes-alergias': 'Detalhes das Alergias',
                                'expectativas': 'Expectativas do Tratamento',
                                'informacoes-relevantes': 'Informações Relevantes',
                                'medicacao-atual': 'Medicação Atual',
                                'medicacao-natural': 'Medicação Natural',
                                'motivo-consulta': 'Motivo da Consulta',
                                'objetivos-saude': 'Objetivos de Saúde',
                                'outras-condicoes': 'Outras Condições',
                                'restricoes-alimentares': 'Restrições Alimentares'
                            }
                            nome_legivel = nomes_legveis.get(nome, nome.replace('-', ' ').replace('_', ' ').title())
                            dados_formulario_html += f"<h5 style='color: #2e7d2e; margin: 10px 0 5px 0;'>{nome_legivel}:</h5>"
                            dados_formulario_html += f"<p style='background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #4CAF50; margin: 5px 0 15px 0;'>{valor}</p>"
                
                # 3. PROCESSAR CHECKBOXES MARCADAS
                if 'checkboxes' in dados_formulario:
                    checkboxes_marcadas = {k: v for k, v in dados_formulario['checkboxes'].items() if v}
                    if checkboxes_marcadas:
                        dados_formulario_html += "<h4 style='color: #2e7d2e; margin: 15px 0 10px 0;'>✅ Opções Selecionadas</h4>"
                        dados_formulario_html += "<ul style='margin: 5px 0 15px 20px;'>"
                        
                        for checkbox_name, checked in checkboxes_marcadas.items():
                            if checked:
                                # Limpar nome da checkbox para exibição
                                nome_limpo = checkbox_name.replace('[]', '').replace('-', ' ').replace('_', ' ')
                                nome_limpo = nome_limpo.replace('tomei conhecimento', 'Tomei Conhecimento dos Termos')
                                nome_limpo = nome_limpo.title()
                                dados_formulario_html += f"<li style='margin: 5px 0;'>✅ {nome_limpo}</li>"
                        
                        dados_formulario_html += "</ul>"
                
                # Se não há dados significativos, incluir resumo geral
                if not any([
                    dados_formulario.get('inputs', {}) and any(v.strip() for v in dados_formulario['inputs'].values() if v),
                    dados_formulario.get('textareas', {}) and any(v.strip() for v in dados_formulario['textareas'].values() if v),
                    dados_formulario.get('checkboxes', {}) and any(dados_formulario['checkboxes'].values())
                ]):
                    dados_formulario_html += "<p style='color: #666; font-style: italic; margin: 10px 0;'>📋 Declaração baseada no formulário interativo - dados específicos conforme preenchimento do paciente.</p>"
                
                # ADICIONAR DECLARAÇÃO DE CONSENTIMENTO
                dados_formulario_html += """
                <div style='margin-top: 30px; padding: 20px; background-color: #f8fff8; border: 2px solid #4CAF50; border-radius: 8px;'>
                    <h4 style='color: #2e7d2e; margin-top: 0; text-align: center;'>🌿 DECLARAÇÃO DE CONSENTIMENTO</h4>
                    <p style='text-align: justify; line-height: 1.6; margin: 15px 0;'>
                        O paciente declara ter fornecido informações verdadeiras e completas sobre o seu estado de saúde, 
                        compreende as limitações e benefícios das terapias naturais, e consente no tratamento naturopático 
                        proposto. Esta declaração foi preenchida de forma consciente e voluntária.
                    </p>
                    <ul style='margin: 15px 0; padding-left: 20px; line-height: 1.6;'>
                        <li>✅ Todas as informações prestadas são verdadeiras e completas</li>
                        <li>✅ Compreendo que a naturopatia é complementar ao acompanhamento médico</li>
                        <li>✅ Autorizo o tratamento dos dados pessoais conforme RGPD</li>
                        <li>✅ Comprometo-me a seguir as recomendações terapêuticas</li>
                        <li>✅ Comunicarei qualquer alteração no meu estado de saúde</li>
                    </ul>
                </div>
                """
                
                dados_formulario_html += "</div>"
            else:
                dados_formulario_html = """
                <div style='margin: 20px 0; padding: 20px; background-color: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;'>
                    <h4 style='color: #856404; margin-top: 0;'>📋 Declaração de Estado de Saúde</h4>
                    <p style='margin: 10px 0; color: #856404; line-height: 1.6;'>
                        Esta declaração foi preenchida através do formulário interativo. O paciente forneceu as informações 
                        necessárias sobre o seu estado de saúde, historial médico, medicação atual e expectativas para o 
                        tratamento naturopático.
                    </p>
                    <div style='margin-top: 20px; padding: 15px; background-color: #f8fff8; border: 2px solid #4CAF50; border-radius: 8px;'>
                        <h5 style='color: #2e7d2e; margin-top: 0;'>🌿 DECLARAÇÃO DE CONSENTIMENTO</h5>
                        <ul style='margin: 10px 0; padding-left: 20px; line-height: 1.6; color: #2e7d2e;'>
                            <li>✅ Todas as informações prestadas são verdadeiras e completas</li>
                            <li>✅ Compreendo que a naturopatia é complementar ao acompanhamento médico</li>
                            <li>✅ Autorizo o tratamento dos dados pessoais conforme RGPD</li>
                            <li>✅ Comprometo-me a seguir as recomendações terapêuticas</li>
                            <li>✅ Comunicarei qualquer alteração no meu estado de saúde</li>
                        </ul>
                    </div>
                </div>
                """
            
            # CRIAR PASTA DE DOCUMENTOS
            paciente_id = self.paciente_data.get('id', 'sem_id')
            nome_paciente_ficheiro = nome_paciente.replace(' ', '_').replace('/', '_').replace('\\', '_')
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente_ficheiro}"
            pasta_declaracoes = os.path.join(pasta_paciente, "declaracoes_saude")
            
            # Criar pastas se não existirem
            os.makedirs(pasta_declaracoes, exist_ok=True)
            
            # CRIAR FICHEIRO PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"Declaracao_Saude_Completa_{timestamp}.pdf"
            caminho_pdf = os.path.join(pasta_declaracoes, nome_arquivo)
            
            # Configurar impressão
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Configurar margens
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(20, 20, 20, 20))
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # LOGO
            logo_html = ""
            for logo_file in ['logo.png', 'Biodesk.png']:
                logo_path = os.path.abspath(f'assets/{logo_file}')
                if os.path.exists(logo_path):
                    logo_url = QUrl.fromLocalFile(logo_path).toString()
                    logo_html = f'<img src="{logo_url}" width="80" height="80">'
                    print(f"[DEBUG] Logo encontrado: {logo_path}")
                    break
            
            # OBTER AMBAS AS ASSINATURAS DA BASE DE DADOS
            manager = ConsentimentosManager()
            
            # Assinatura do paciente
            assinatura_paciente_bytes = manager.obter_assinatura(paciente_id, "declaracao_saude", "paciente")
            assinatura_paciente_html = ""
            
            if assinatura_paciente_bytes:
                try:
                    import base64
                    assinatura_base64_paciente = base64.b64encode(assinatura_paciente_bytes).decode('utf-8')
                    assinatura_paciente_html = f'<img src="data:image/png;base64,{assinatura_base64_paciente}" width="200" height="80">'
                    print(f"[DEBUG] Assinatura do paciente carregada ({len(assinatura_paciente_bytes)} bytes)")
                except Exception as e:
                    print(f"[DEBUG] Erro ao carregar assinatura do paciente: {e}")
            
            # Assinatura do terapeuta
            assinatura_terapeuta_bytes = manager.obter_assinatura(paciente_id, "declaracao_saude", "terapeuta")
            assinatura_terapeuta_html = ""
            
            if assinatura_terapeuta_bytes:
                try:
                    import base64
                    assinatura_base64_terapeuta = base64.b64encode(assinatura_terapeuta_bytes).decode('utf-8')
                    assinatura_terapeuta_html = f'<img src="data:image/png;base64,{assinatura_base64_terapeuta}" width="200" height="80">'
                    print(f"[DEBUG] Assinatura do terapeuta carregada ({len(assinatura_terapeuta_bytes)} bytes)")
                except Exception as e:
                    print(f"[DEBUG] Erro ao carregar assinatura do terapeuta: {e}")
            
            # OBTER TEMPLATE COMPLETO PARA PDF
            template_declaracao_pdf = self._obter_template_declaracao_para_pdf(dados_formulario)
            print(f"[DEBUG PDF] Template obtido, tamanho: {len(template_declaracao_pdf)}")
            
            # DEBUG: Verificar se as variáveis estão definidas corretamente
            print(f"[DEBUG PDF] Variáveis para substituição:")
            print(f"  - nome_paciente: '{nome_paciente}'")
            print(f"  - data_nascimento: '{data_nascimento}'")
            print(f"  - data_atual: '{data_atual}'")
            print(f"  - data_atual_por_extenso: '{data_atual_por_extenso}'")
            print(f"  - assinatura_paciente_html: {'Sim' if assinatura_paciente_html else 'Não'}")
            print(f"  - assinatura_terapeuta_html: {'Sim' if assinatura_terapeuta_html else 'Não'}")
            
            # HTML FINAL COMPLETO COM DADOS DAS CHECKBOXES E AMBAS AS ASSINATURAS
            html_content = f"""
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Calibri, Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px;">
                
                <!-- Cabeçalho -->
                <table style="width: 100%; border-bottom: 3px solid #4CAF50; padding-bottom: 15px; margin-bottom: 25px;">
                    <tr>
                        <td style="text-align: left; vertical-align: middle;">
                            {logo_html}
                        </td>
                        <td style="text-align: center; vertical-align: middle;">
                            <h1 style="color: #4CAF50; margin: 0; font-size: 26pt;">🌿 DECLARAÇÃO DE ESTADO DE SAÚDE 🌿</h1>
                            <p style="color: #666; margin: 5px 0 0 0; font-size: 14pt; font-style: italic;">Naturopatia e Medicina Natural</p>
                        </td>
                        <td style="text-align: right; vertical-align: middle; width: 100px;">
                            <p style="font-size: 10pt; color: #666; margin: 0;">Data:<br><strong>{data_atual}</strong></p>
                        </td>
                    </tr>
                </table>
                
                <!-- Informações do Paciente -->
                <table style="width: 100%; background-color: #f8fff8; border: 2px solid #4CAF50; border-radius: 8px; padding: 15px; margin-bottom: 25px;">
                    <tr>
                        <td style="width: 50%; vertical-align: top;">
                            <strong>👤 Nome do Paciente:</strong><br>
                            <span style="font-size: 16pt; color: #2e7d2e;">{nome_paciente}</span>
                        </td>
                        <td style="width: 25%; vertical-align: top;">
                            <strong>📅 Data de Nascimento:</strong><br>
                            {data_nascimento}
                        </td>
                        <td style="width: 25%; vertical-align: top;">
                            <strong>📋 Data da Declaração:</strong><br>
                            {data_atual}
                        </td>
                    </tr>
                </table>
                
                <!-- CONTEÚDO COMPLETO DA DECLARAÇÃO -->
                <div style="background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px;">
                    <h2 style="color: #4CAF50; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">📋 DECLARAÇÃO COMPLETA DE ESTADO DE SAÚDE</h2>
                    <p style="color: #666; font-style: italic; margin-bottom: 20px;">Esta declaração inclui todas as perguntas do formulário e as respostas fornecidas pelo paciente.</p>
                    
                    <!-- TEMPLATE COMPLETO DA DECLARAÇÃO (sem JavaScript, só conteúdo) -->
                    <div style="margin: 20px 0;">
                        {template_declaracao_pdf}
                    </div>
                    
                    <!-- DADOS DO FORMULÁRIO CAPTURADOS (resumo) -->
                    {dados_formulario_html}
                </div>
                
                <!-- Seção de Assinaturas DUPLAS -->
                <div style="border-top: 2px solid #4CAF50; padding-top: 30px;">
                    <h2 style="color: #4CAF50; text-align: center; margin-bottom: 30px;">✍️ ASSINATURAS</h2>
                    
                    <table style="width: 100%;">
                        <tr>
                            <!-- Assinatura do Paciente -->
                            <td style="width: 50%; text-align: center; vertical-align: top; padding: 0 20px;">
                                <div style="border: 2px solid #007bff; padding: 20px; background-color: #f8f9ff; min-height: 120px; border-radius: 8px;">
                                    <h3 style="color: #007bff; margin-top: 0;">👤 Assinatura do Paciente</h3>
                                    <div style="min-height: 80px; display: flex; align-items: center; justify-content: center;">
                                        {assinatura_paciente_html if assinatura_paciente_html else '<span style="color: #999; font-style: italic;">Sem assinatura</span>'}
                                    </div>
                                    <p style="margin: -15px 0 0 0; line-height: 0.8;">
                                        <strong style="color: #333; font-size: 14pt;">{nome_paciente}</strong><br>
                                        <span style="font-size: 12pt; color: #666;">{data_atual_por_extenso}</span><br>
                                        <span style="font-size: 10pt; color: #007bff; font-style: italic;">Assinado digitalmente</span>
                                    </p>
                                </div>
                            </td>
                            
                            <!-- Assinatura do Naturopata -->
                            <td style="width: 50%; text-align: center; vertical-align: top; padding: 0 20px;">
                                <div style="border: 2px solid #28a745; padding: 20px; background-color: #f8fff8; min-height: 120px; border-radius: 8px;">
                                    <h3 style="color: #28a745; margin-top: 0;">🌿 Assinatura do Naturopata</h3>
                                    <div style="min-height: 80px; display: flex; align-items: center; justify-content: center;">
                                        {assinatura_terapeuta_html if assinatura_terapeuta_html else '<span style="color: #999; font-style: italic;">Sem assinatura</span>'}
                                    </div>
                                    <p style="margin: -15px 0 0 0; line-height: 0.8;">
                                        <strong style="color: #333; font-size: 14pt;">Nuno Correia</strong><br>
                                        <span style="font-size: 12pt; color: #666;">{data_atual_por_extenso}</span><br>
                                        <span style="font-size: 10pt; color: #28a745; font-style: italic;">Naturopata Certificado</span>
                                    </p>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <!-- Rodapé -->
                <div style="margin-top: 40px; text-align: center; font-size: 10pt; color: #666; border-top: 1px solid #eee; padding-top: 15px;">
                    🌿 BIODESK - Sistema de Gestão Naturopata | Documento gerado em {data_atual}<br>
                    🌐 www.nunocorreia.pt | 📧 info@nunocorreia.pt
                </div>
                
            </body>
            </html>
            """
            
            # Gerar PDF COMPLETO
            document = QTextDocument()
            document.setHtml(html_content)
            document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            document.print(printer)
            
            # CRIAR METADATA
            caminho_meta = caminho_pdf + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                f.write(f"Categoria: 🌿 Declaração de Saúde Completa\n")
                f.write(f"Descrição: Declaração de Estado de Saúde com Assinaturas Duplas e Dados Capturados\n")
                f.write(f"Data: {data_atual}\n")
                f.write(f"Paciente: {nome_paciente}\n")
                f.write(f"Naturopata: Nuno Correia\n")
                f.write(f"Tipo: declaracao_saude_completa\n")
                f.write(f"Assinaturas: {'Paciente' if assinatura_paciente_html else 'Sem'} + {'Terapeuta' if assinatura_terapeuta_html else 'Sem'}\n")
                f.write(f"Dados_Formulario: {'Capturados' if dados_formulario else 'Template_Base'}\n")
            
            # Atualizar interface
            if hasattr(self, 'atualizar_lista_documentos'):
                try:
                    self.atualizar_lista_documentos()
                    print(f"✅ [GESTOR] Lista de documentos atualizada automaticamente")
                except Exception as e:
                    print(f"⚠️ [GESTOR] Erro ao atualizar lista: {e}")
            
            # Tentar também atualizar através da janela pai se existir
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'atualizar_lista_documentos'):
                try:
                    self.parent().atualizar_lista_documentos()
                    print(f"✅ [GESTOR] Lista de documentos atualizada via parent")
                except Exception as e:
                    print(f"⚠️ [GESTOR] Erro ao atualizar lista via parent: {e}")
            
            # Forçar refresh do widget se houver tabs
            try:
                if hasattr(self, 'dados_documentos_tabs'):
                    current_tab = self.dados_documentos_tabs.currentIndex()
                    self.dados_documentos_tabs.setCurrentIndex(0)
                    self.dados_documentos_tabs.setCurrentIndex(current_tab)
                    print(f"✅ [GESTOR] Tab refresh forçado")
            except Exception as e:
                print(f"⚠️ [GESTOR] Erro no tab refresh: {e}")
            
            # Mensagem de sucesso
            print(f"✅ [PDF COMPLETO] Gerado: {caminho_pdf}")
            print(f"✅ [ASSINATURAS] Incluídas: {'✅ 👤 Paciente' if assinatura_paciente_html else '❌ Paciente'} + {'✅ 🌿 Naturopata' if assinatura_terapeuta_html else '❌ Naturopata'}")
            if dados_formulario and 'checkboxes' in dados_formulario:
                print(f"✅ [DADOS] Checkboxes capturadas: {len(dados_formulario['checkboxes'])}")
            else:
                print(f"⚠️ [DADOS] Usando template base (checkboxes não capturadas)")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao gerar PDF:\n\n{str(e)}")

    def _obter_template_declaracao_para_pdf(self, dados_formulario):
        """Converte o template HTML interativo numa versão adequada para PDF - VERSÃO SIMPLIFICADA"""
        try:
            # Obter o template base
            template_base = self._criar_template_declaracao_saude()
            print(f"[DEBUG PDF] Template base obtido, tamanho: {len(template_base)}")
            
            # SUBSTITUIR PLACEHOLDERS PRIMEIRO
            nome_paciente = self.paciente_data.get('nome', 'N/A')
            data_nascimento = self.paciente_data.get('data_nascimento', 'N/A')
            data_atual = self.data_atual()
            
            template_base = template_base.replace('[NOME_PACIENTE]', nome_paciente)
            template_base = template_base.replace('[DATA_NASCIMENTO]', data_nascimento)
            template_base = template_base.replace('[DATA_ATUAL]', data_atual)
            
            # Remover scripts
            import re
            template_pdf = re.sub(r'<script.*?</script>', '', template_base, flags=re.DOTALL)
            
            # CONVERTER CHECKBOXES PARA SÍMBOLOS VISUAIS
            # QTextDocument não suporta <input>, então vamos converter para símbolos
            
            # Primeiro, identificar checkboxes marcadas se tivermos dados
            checkboxes_marcadas = set()
            if dados_formulario and 'checkboxes' in dados_formulario:
                for checkbox_name, is_checked in dados_formulario['checkboxes'].items():
                    if is_checked:
                        checkboxes_marcadas.add(checkbox_name)
                        print(f"[DEBUG PDF] Checkbox marcada: {checkbox_name}")
            
            # Converter TODAS as checkboxes para símbolos visuais
            def converter_checkbox(match):
                checkbox_html = match.group(0)
                
                # Extrair o name da checkbox
                name_match = re.search(r'name="([^"]*)"', checkbox_html)
                checkbox_name = name_match.group(1) if name_match else 'unknown'
                
                # Determinar se está marcada
                is_checked = checkbox_name in checkboxes_marcadas
                
                # USAR TEXTO MUITO SIMPLES QUE FUNCIONA SEMPRE EM PDF
                if is_checked:
                    # Checkbox marcada - texto claro
                    symbol_html = '<strong style="color: #4CAF50; font-size: 14px; margin-right: 10px; padding: 2px 6px; border: 2px solid #4CAF50; background-color: #e8f5e8;">[X] SIM</strong>'
                else:
                    # Checkbox vazia - texto simples
                    symbol_html = '<span style="color: #666; font-size: 14px; margin-right: 10px; padding: 2px 6px; border: 1px solid #ccc; background-color: #f9f9f9;">[ ] NÃO</span>'
                
                return symbol_html
            
            # Aplicar conversão a todas as checkboxes
            template_pdf = re.sub(r'<input[^>]*type="checkbox"[^>]*>', converter_checkbox, template_pdf)
            
            # Converter radio buttons também
            def converter_radio(match):
                radio_html = match.group(0)
                
                # Extrair informações do radio
                value_match = re.search(r'value="([^"]*)"', radio_html)
                radio_value = value_match.group(1) if value_match else 'Opção'
                
                # Radio não selecionado - usar texto simples
                return f'<span style="margin-right: 15px; padding: 2px 8px; border: 1px solid #ccc; border-radius: 3px; background-color: #f9f9f9; font-size: 13px;">( ) {radio_value}</span>'
            
            template_pdf = re.sub(r'<input[^>]*type="radio"[^>]*>', converter_radio, template_pdf)
            
            # Converter inputs de texto para spans se estiverem preenchidos
            if dados_formulario and 'inputs' in dados_formulario:
                for input_name, valor in dados_formulario['inputs'].items():
                    if valor and valor.strip():
                        print(f"[DEBUG PDF] Preenchendo input {input_name}: {valor}")
                        # Substituir input por span com valor
                        pattern = f'<input[^>]*name="{re.escape(input_name)}"[^>]*>'
                        replacement = f'<span style="background-color: #f0f8f0; padding: 4px; border: 1px solid #4CAF50; border-radius: 3px; font-weight: bold;">{valor}</span>'
                        template_pdf = re.sub(pattern, replacement, template_pdf)
            
            # Converter textareas preenchidas
            if dados_formulario and 'textareas' in dados_formulario:
                for textarea_name, valor in dados_formulario['textareas'].items():
                    if valor and valor.strip():
                        print(f"[DEBUG PDF] Preenchendo textarea {textarea_name}: {valor}")
                        pattern = f'<textarea[^>]*name="{re.escape(textarea_name)}"[^>]*>[^<]*</textarea>'
                        replacement = f'<div style="background-color: #f0f8f0; padding: 8px; border: 1px solid #4CAF50; border-radius: 3px; min-height: 40px; white-space: pre-wrap;">{valor}</div>'
                        template_pdf = re.sub(pattern, replacement, template_pdf)
            
            # Remover inputs e textareas vazios (substituir por espaços em branco)
            template_pdf = re.sub(r'<input[^>]*type="text"[^>]*>', '<span style="display: inline-block; width: 200px; height: 20px; border-bottom: 1px solid #ccc; margin: 0 5px;"></span>', template_pdf)
            template_pdf = re.sub(r'<textarea[^>]*>[^<]*</textarea>', '<div style="width: 100%; height: 60px; border: 1px solid #ccc; border-radius: 3px; background-color: #f9f9f9; margin: 5px 0;"></div>', template_pdf)
            
            # Estilos simplificados para PDF
            estilos_pdf_simples = """
            <style>
            body { 
                font-family: 'Calibri', Arial, sans-serif; 
                line-height: 1.5; 
                color: #333;
                font-size: 11pt;
                margin: 0;
                padding: 20px;
            }
            h1, h2, h3 { 
                color: #2e7d2e; 
                margin-top: 20px;
                margin-bottom: 10px;
            }
            h1 { font-size: 18pt; text-align: center; }
            h2 { font-size: 16pt; border-bottom: 2px solid #4CAF50; padding-bottom: 5px; }
            h3 { font-size: 14pt; }
            
            .container {
                max-width: 100%;
                background-color: white;
            }
            
            .form-group { 
                margin-bottom: 15px; 
                page-break-inside: avoid;
            }
            
            .checkbox-group {
                margin: 10px 0;
            }
            
            .checkbox-item {
                margin: 8px 0;
                padding: 5px 0;
                line-height: 1.6;
            }
            
            .patient-info {
                background-color: #f8fff8;
                padding: 15px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-bottom: 20px;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            
            .legal-text {
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #4CAF50;
                margin: 20px 0;
                line-height: 1.6;
            }
            
            .acknowledgment-section {
                background-color: #f8fff8;
                border: 2px solid #4CAF50;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }
            
            label {
                font-weight: normal;
                margin-left: 5px;
                cursor: default;
            }
            
            ul, ol {
                margin: 10px 0;
                padding-left: 25px;
            }
            
            li {
                margin: 5px 0;
                line-height: 1.4;
            }
            </style>
            """
            
            # Substituir estilos existentes ou adicionar
            if '<style>' in template_pdf:
                template_pdf = re.sub(r'<style>.*?</style>', estilos_pdf_simples, template_pdf, flags=re.DOTALL)
            else:
                template_pdf = estilos_pdf_simples + template_pdf
            
            print(f"[DEBUG PDF] Template processado, tamanho final: {len(template_pdf)}")
            print(f"[DEBUG PDF] Checkboxes convertidas para símbolos: {template_pdf.count('☐') + template_pdf.count('☑')}")
            
            return template_pdf
            
        except Exception as e:
            print(f"❌ [TEMPLATE PDF] Erro: {e}")
            import traceback
            traceback.print_exc()
            return "<p style='color: red;'>Erro ao processar template da declaração</p>"

    def guardar_declaracao_saude(self):
        """Guarda a declaração COM ASSINATURAS usando o sistema completo do 'gerar PDF final'"""
        try:
            if not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Nenhum paciente selecionado.")
                return
            
            from consentimentos_manager import ConsentimentosManager
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF, QUrl
            import os
            from datetime import datetime
            
            # Verificar se temos ID do paciente
            paciente_id = self.paciente_data.get('id')
            if not paciente_id:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "Paciente precisa de ser guardado primeiro.")
                return
            
            # Obter conteúdo (com preenchimento automático)
            conteudo_html = ""
            conteudo_texto = "Declaração de Saúde - Formulário Web Interativo"
            
            # Para QWebEngineView, não conseguimos extrair o texto diretamente
            # mas o formulário é válido se os dados do paciente existem
            try:
                # Tentar obter HTML do WebEngine (pode falhar)
                if hasattr(self.texto_declaracao_editor, 'toHtml'):
                    conteudo_html = self.texto_declaracao_editor.toHtml()
                else:
                    # Usar template como fallback
                    conteudo_html = self.template_declaracao
            except:
                conteudo_html = self.template_declaracao
            
            # Preencher automaticamente os dados do paciente
            nome_paciente = self.paciente_data.get('nome', '[NOME_PACIENTE]')
            data_nascimento = self.paciente_data.get('data_nascimento', '[DATA_NASCIMENTO]')
            data_atual = self.data_atual()
            
            # Gerar data por extenso
            from datetime import datetime
            try:
                meses = [
                    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
                ]
                agora = datetime.now()
                data_atual_por_extenso = f"{agora.day} de {meses[agora.month - 1]} de {agora.year}"
            except:
                data_atual_por_extenso = data_atual
            
            # Substituir variáveis no conteúdo
            conteudo_html = conteudo_html.replace('[NOME_PACIENTE]', nome_paciente)
            conteudo_html = conteudo_html.replace('[DATA_NASCIMENTO]', data_nascimento)
            conteudo_html = conteudo_html.replace('[DATA_ATUAL]', data_atual)
            
            conteudo_texto = conteudo_texto.replace('[NOME_PACIENTE]', nome_paciente)
            conteudo_texto = conteudo_texto.replace('[DATA_NASCIMENTO]', data_nascimento)
            conteudo_texto = conteudo_texto.replace('[DATA_ATUAL]', data_atual)
            
            # Atualizar o editor com os dados preenchidos
            self.texto_declaracao_editor.setHtml(conteudo_html)
            
            # Verificar se há conteúdo
            if not conteudo_texto.strip():
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "A declaração está vazia.\nAdicione conteúdo antes de guardar.")
                return
            
            # CRIAR PASTA DE DOCUMENTOS (estrutura CORRETA para gestão)
            paciente_id = self.paciente_data.get('id', 'sem_id')
            nome_paciente_ficheiro = nome_paciente.replace(' ', '_').replace('/', '_').replace('\\', '_')
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente_ficheiro}"
            pasta_declaracoes = os.path.join(pasta_paciente, "declaracoes_saude")
            
            # Criar pastas se não existirem
            os.makedirs(pasta_declaracoes, exist_ok=True)
            
            # CRIAR FICHEIRO PDF NA PASTA
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"Declaracao_Saude_{timestamp}.pdf"
            caminho_pdf = os.path.join(pasta_declaracoes, nome_arquivo)
            
            # ✅ USAR O SISTEMA COMPLETO COM ASSINATURAS (mesmo do "gerar PDF final")
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Configurar margens
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            page_layout.setMargins(QMarginsF(20, 20, 20, 20))
            page_layout.setUnits(QPageLayout.Unit.Millimeter)
            printer.setPageLayout(page_layout)
            
            # 🎯 LOGO - IGUAL aos consentimentos
            logo_html = ""
            for logo_file in ['logo.png', 'Biodesk.png']:
                logo_path = os.path.abspath(f'assets/{logo_file}')
                if os.path.exists(logo_path):
                    logo_url = QUrl.fromLocalFile(logo_path).toString()
                    logo_html = f'<img src="{logo_url}" width="80" height="80">'
                    print(f"[DEBUG] Logo encontrado: {logo_path}")
                    break
            
            # 📝 ASSINATURAS - IGUAL aos consentimentos (usando BD)
            assinatura_paciente_html = ""
            
            # Obter assinatura da base de dados (mesmo método dos consentimentos)
            manager = ConsentimentosManager()
            assinatura_paciente_bytes = manager.obter_assinatura(paciente_id, "declaracao_saude", "paciente")
            
            print(f"[DEBUG PDF] Paciente ID: {paciente_id}")
            print(f"[DEBUG PDF] Assinatura bytes: {'ENCONTRADA' if assinatura_paciente_bytes else 'NAO ENCONTRADA'}")
            if assinatura_paciente_bytes:
                print(f"[DEBUG PDF] Tamanho da assinatura: {len(assinatura_paciente_bytes)} bytes")
            
            if assinatura_paciente_bytes:
                try:
                    # MÉTODO 1: Converter bytes para arquivo temporário (IGUAL aos consentimentos)
                    os.makedirs('temp', exist_ok=True)
                    sig_path = os.path.abspath('temp/sig_declaracao_paciente.png')
                    with open(sig_path, 'wb') as f:
                        f.write(assinatura_paciente_bytes)
                    sig_url = QUrl.fromLocalFile(sig_path).toString()
                    
                    # MÉTODO 2: Converter para base64 (BACKUP caso o ficheiro não funcione)
                    import base64
                    assinatura_base64 = base64.b64encode(assinatura_paciente_bytes).decode('utf-8')
                    
                    # Usar base64 que é mais compatível com QTextDocument
                    assinatura_paciente_html = f'<img src="data:image/png;base64,{assinatura_base64}" width="188" height="63">'
                    
                    print(f"[DEBUG PDF] Assinatura declaração carregada da BD: {sig_path}")
                    print(f"[DEBUG PDF] URL da assinatura: {sig_url}")
                    print(f"[DEBUG PDF] Base64 (primeiros 50 chars): {assinatura_base64[:50]}...")
                    print(f"[DEBUG PDF] HTML da assinatura: {assinatura_paciente_html[:100]}...")
                except Exception as e:
                    print(f"[DEBUG PDF] Erro ao carregar assinatura da BD: {e}")
            else:
                print(f"[DEBUG PDF] Nenhuma assinatura encontrada na BD para declaracao_saude")
            
            # HTML FINAL COM ASSINATURAS (formatação semelhante aos consentimentos)
            html_content = f"""
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Calibri, Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px;">
                
                <!-- Cabeçalho -->
                <table style="width: 100%; border-bottom: 2px solid #2980b9; padding-bottom: 15px; margin-bottom: 25px;">
                    <tr>
                        <td style="text-align: left; vertical-align: middle;">
                            {logo_html}
                        </td>
                        <td style="text-align: center; vertical-align: middle;">
                            <h1 style="color: #2980b9; margin: 0; font-size: 24pt;">DECLARAÇÃO DE ESTADO DE SAÚDE</h1>
                            <p style="color: #666; margin: 5px 0 0 0; font-size: 12pt;">Sistema BIODESK</p>
                        </td>
                        <td style="text-align: right; vertical-align: middle; width: 100px;">
                            <p style="font-size: 10pt; color: #666; margin: 0;">Data:<br><strong>{data_atual}</strong></p>
                        </td>
                    </tr>
                </table>
                
                <!-- Informações do Paciente -->
                <table style="width: 100%; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin-bottom: 25px;">
                    <tr>
                        <td style="width: 33%; vertical-align: top;">
                            <strong>👤 Paciente:</strong><br>
                            {nome_paciente}
                        </td>
                        <td style="width: 33%; vertical-align: top;">
                            <strong>📅 Data de Nascimento:</strong><br>
                            {data_nascimento}
                        </td>
                        <td style="width: 34%; vertical-align: top;">
                            <strong>📋 Data do Documento:</strong><br>
                            {data_atual}
                        </td>
                    </tr>
                </table>
                
                <!-- Conteúdo da Declaração -->
                <div style="margin-bottom: 40px; text-align: justify;">
                    {conteudo_texto.replace(chr(10), '<br>')}
                </div>
                
                <!-- Assinatura CENTRALIZADA e SIMPLIFICADA -->
                <table style="width: 100%; border-top: 1px solid #dee2e6; padding-top: 25px;">
                    <tr>
                        <td style="text-align: center; width: 100%; padding: 30px 0;">
                            <!-- Container centralizado para assinatura -->
                            <div style="margin: 0 auto; width: 100%; text-align: center;">
                                <div style="border: 2px solid #28a745; padding: 20px; background-color: white; min-height: 120px; display: inline-block; margin: 0 auto; border-radius: 8px; width: 400px;">
                                    {assinatura_paciente_html if assinatura_paciente_html else '<span style="color: #999; font-style: italic;">Sem assinatura</span>'}
                                </div>
                                <p style="margin: 20px 0 0 0; text-align: center; line-height: 1.8;">
                                    <strong style="color: #333; font-size: 14pt;">{nome_paciente}</strong><br><br>
                                    <span style="font-size: 12pt; color: #666;">{data_atual_por_extenso}</span><br><br>
                                    <span style="font-size: 10pt; color: #28a745; font-style: italic;">Assinado digitalmente via BIODESK</span>
                                </p>
                            </div>
                        </td>
                    </tr>
                </table>
                
                <!-- Rodapé -->
                <div style="margin-top: 40px; text-align: center; font-size: 10pt; color: #666; border-top: 1px solid #eee; padding-top: 15px;">
                    🩺 BIODESK - Sistema de Gestão Clínica | Declaração gerada em {data_atual}
                </div>
                
            </body>
            </html>
            """
            
            # Gerar PDF COM ASSINATURAS
            document = QTextDocument()
            document.setHtml(html_content)
            document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            document.print(printer)
            
            # CRIAR METADATA
            caminho_meta = caminho_pdf + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                f.write(f"Categoria: 🩺 Declaração de Saúde\n")
                f.write(f"Descrição: Declaração de Estado de Saúde\n")
                f.write(f"Data: {data_atual}\n")
                f.write(f"Paciente: {nome_paciente}\n")
                f.write(f"Tipo: declaracao_saude\n")
            
            # Guardar na base de dados usando o sistema dos consentimentos
            sucesso = manager.guardar_consentimento(
                paciente_id=paciente_id,
                tipo_consentimento='declaracao_saude',
                conteudo_html=conteudo_html,
                conteudo_texto=conteudo_texto,
                assinatura_paciente=None,  # Assinatura será adicionada separadamente
                assinatura_terapeuta=None,  # Declaração só tem assinatura do paciente
                nome_paciente=nome_paciente,
                nome_terapeuta=None
            )
            
            if sucesso:
                # Preparar informação sobre assinaturas incluídas
                assinaturas_info = []
                if assinatura_paciente_html:
                    assinaturas_info.append("👤 Paciente")
                
                assinaturas_texto = "✅ " + " + ".join(assinaturas_info) if assinaturas_info else "❌ Nenhuma incluída"
                
                from biodesk_dialogs import mostrar_sucesso
                mostrar_sucesso(self, "Declaração Guardada", f"✅ Declaração de saúde guardada COM ASSINATURAS!\n\n📁 Ficheiro: {nome_arquivo}\n📂 Localização: {pasta_declaracoes}\n\n🖊️ Assinaturas: {assinaturas_texto}")
                
                # Atualizar status visual
                self.status_declaracao.setText("✅ Guardada")
                self.status_declaracao.setStyleSheet("""
                    QLabel {
                        color: #27ae60;
                        font-weight: bold;
                        font-size: 12px;
                        padding: 5px;
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 4px;
                    }
                """)
                
                # Atualizar lista de documentos se estiver na sub-aba gestão
                if hasattr(self, 'atualizar_lista_documentos'):
                    self.atualizar_lista_documentos()
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Erro ao guardar na base de dados.")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao guardar declaração:\n\n{str(e)}")
            print(f"❌ [DECLARAÇÃO] Erro: {e}")
            
            # Criar documento
            document = QTextDocument()
            
            # Preparar HTML para PDF
            html_content = self.texto_declaracao_editor.toHtml()
            
            # Adicionar cabeçalho com dados do paciente
            html_final = f"""
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Calibri, Arial, sans-serif;">
                <h1 style="text-align: center; color: #2980b9;">DECLARAÇÃO DE ESTADO DE SAÚDE</h1>
                
                <p><strong>Nome:</strong> {self.paciente_data.get('nome', '')}</p>
                <p><strong>Data de Nascimento:</strong> {self.paciente_data.get('data_nascimento', '')}</p>
                <p><strong>Data da Declaração:</strong> {datetime.now().strftime('%d/%m/%Y')}</p>
                
                <hr style="margin: 20pt 0;">
                
                {html_content}
                
                <div style="margin-top: 50pt;">
                    <p><strong>ASSINATURAS:</strong></p>
                    <p>Paciente: _________________________ Data: _______</p>
                    <p>Terapeuta: ________________________ Data: _______</p>
                </div>
                
                <hr style="margin: 30pt 0;">
                <p style="text-align: center; font-size: 10pt; color: #666;">
                    🩺 BIODESK - Sistema de Gestão Clínica<br>
                    Declaração de Estado de Saúde - {datetime.now().strftime('%d/%m/%Y %H:%M')}
                </p>
            </body>
            </html>
            """
            
            document.setHtml(html_final)
            document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            document.print(printer)
            
            # Criar metadata para gestão de documentos
            caminho_meta = caminho_pdf + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                f.write(f"Categoria: Declaração de Saúde\n")
                f.write(f"Descrição: Declaração de Estado de Saúde\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write(f"Paciente: {self.paciente_data.get('nome', '')}\n")
            
            # Atualizar também na base de dados
            conteudo_html = self.texto_declaracao_editor.toHtml()
            self.paciente_data['declaracao_saude_html'] = conteudo_html
            self.paciente_data['declaracao_saude_data'] = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            success = self.db.update_paciente(paciente_id, self.paciente_data)
            
            if success:
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(
                    self, 
                    "Declaração Guardada", 
                    f"✅ Declaração de Estado de Saúde guardada com sucesso!\n\n"
                    f"📁 Ficheiro: {nome_arquivo}\n"
                    f"📂 Localização: {pasta_declaracoes}\n\n"
                    f"💡 Consulte na Gestão de Documentos da Área Clínica."
                )
                
                self.status_declaracao.setText("💾 Guardada")
                self.status_declaracao.setStyleSheet("""
                    font-size: 14px; 
                    font-weight: 600;
                    color: #ffffff;
                    padding: 15px;
                    background-color: rgba(52, 152, 219, 0.8);
                    border-radius: 6px;
                """)
                
                # Atualizar lista de documentos se existir
                if hasattr(self, 'atualizar_lista_documentos'):
                    self.atualizar_lista_documentos()
                    
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Erro ao guardar declaração na base de dados.")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao guardar declaração:\n\n{str(e)}")

    def assinar_declaracao_saude(self):
        """Abre interface de assinatura da declaração - CLONADO EXATAMENTE dos consentimentos"""
        try:
            if not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Nenhum paciente selecionado.")
                return
            
            paciente_id = self.paciente_data.get('id')
            if not paciente_id:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "Paciente precisa de ser guardado primeiro.")
                return
            
            # Criar dados do documento (formato igual aos consentimentos)
            doc_data = {
                'nome': 'Declaração de Estado de Saúde',
                'tipo': '🩺 Declaração de Saúde',
                'tipo_documento': 'declaracao_saude',
                'paciente_id': paciente_id
            }
            
            # Usar EXATAMENTE o mesmo método dos consentimentos
            self.processar_assinatura_documento(doc_data, 'paciente', None)
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao assinar declaração:\n\n{str(e)}")
            print(f"❌ [DECLARAÇÃO] Erro: {e}")

    def gerar_pdf_declaracao_com_assinaturas(self):
        """Gera PDF da declaração usando o sistema dos consentimentos com assinaturas do paciente E terapeuta"""
        try:
            if not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Nenhum paciente selecionado.")
                return
            
            from PyQt6.QtWidgets import QFileDialog
            import os
            from consentimentos_manager import ConsentimentosManager
            
            # Verificar se há assinaturas na BD para declaração
            manager = ConsentimentosManager()
            paciente_id = self.paciente_data.get('id')
            
            # Buscar assinaturas específicas para declaração de saúde
            assinatura_paciente = manager.obter_assinatura(paciente_id, "declaracao_saude", "paciente")
            assinatura_terapeuta = manager.obter_assinatura(paciente_id, "declaracao_saude", "terapeuta")
            
            if not assinatura_paciente and not assinatura_terapeuta:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "⚠️ Nenhuma assinatura encontrada.\n\nPor favor, assine a declaração primeiro.")
                return
            
            # Escolher local para salvar
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            nome_arquivo = f"Declaracao_Saude_{nome_paciente}_{self.data_atual().replace('/', '-')}.pdf"
            
            arquivo, _ = QFileDialog.getSaveFileName(
                self, "Guardar Declaração de Saúde PDF", nome_arquivo, "PDF files (*.pdf)"
            )
            
            if not arquivo:
                return
            
            # Obter conteúdo HTML da declaração
            conteudo_html = self.texto_declaracao_editor.toHtml()
            
            # Aplicar substituição de variáveis para preenchimento automático
            conteudo_html = self.substituir_variaveis_template(conteudo_html)
            
            # Dados para o PDF (mesmo formato dos consentimentos)
            from datetime import datetime
            dados_pdf = {
                'nome_paciente': self.paciente_data.get('nome', ''),
                'data_nascimento': self.paciente_data.get('data_nascimento', ''),
                'contacto': self.paciente_data.get('contacto', ''),
                'email': self.paciente_data.get('email', ''),
                'tipo_consentimento': 'Declaração de Estado de Saúde',
                'data_atual': datetime.now().strftime("%d/%m/%Y")
            }
            
            # Usar o sistema unificado de geração de PDF COM assinaturas
            pdf_success = self._gerar_pdf_consentimento_simples(
                conteudo_html, arquivo, dados_pdf, assinatura_paciente, assinatura_terapeuta
            )
            
            if pdf_success:
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(
                    self,
                    "PDF Gerado",
                    f"✅ Declaração de Estado de Saúde gerada com sucesso!\n\n📁 {arquivo}\n\n✍️ Assinaturas incluídas: {'Paciente' if assinatura_paciente else ''}{' + Terapeuta' if assinatura_terapeuta else ''}"
                )
                print(f"✅ [DECLARAÇÃO] PDF gerado com assinaturas: {arquivo}")
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Erro ao gerar PDF da declaração.")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao gerar PDF:\n\n{str(e)}")
            print(f"❌ [DECLARAÇÃO] Erro: {e}")

    def abrir_janela_assinatura_declaracao(self):
        """Abre janela de assinatura moderna para declaração de saúde"""
        try:
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                       QLabel, QFrame, QGroupBox, QScrollArea)
            from PyQt6.QtCore import Qt
            
            # Criar diálogo principal
            dialog = QDialog(self)
            dialog.setWindowTitle("🩺 Assinatura Digital - Declaração de Estado de Saúde")
            dialog.setModal(True)
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            titulo = QLabel("✍️ Assinatura da Declaração de Estado de Saúde")
            titulo.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #2980b9;
                padding: 20px;
                text-align: center;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 15px;
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Informações do paciente
            info_frame = QFrame()
            info_frame.setStyleSheet("""
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            """)
            info_layout = QHBoxLayout(info_frame)
            
            info_paciente = QLabel(f"""
            <b>👤 Paciente:</b> {self.paciente_data.get('nome', 'N/A')}<br>
            <b>📅 Data:</b> {self.data_atual()}<br>
            <b>📄 Documento:</b> Declaração de Estado de Saúde
            """)
            info_paciente.setStyleSheet("font-size: 14px; color: #2c3e50;")
            info_layout.addWidget(info_paciente)
            layout.addWidget(info_frame)
            
            # Área de assinatura do paciente
            grupo_paciente = QGroupBox("👤 Assinatura do Paciente")
            grupo_paciente.setStyleSheet("""
                QGroupBox {
                    font-size: 14px;
                    font-weight: bold;
                    color: #27ae60;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                }
            """)
            layout_paciente = QVBoxLayout(grupo_paciente)
            
            # Usar sistema modular de assinaturas - removido canvas manual

            # Botões para assinatura paciente
            botoes_paciente = QHBoxLayout()
            
            btn_limpar_paciente = QPushButton("🗑️ Limpar")
            # Sistema modular substituirá funcionalidade do canvas
            
            botoes_paciente.addWidget(btn_limpar_paciente)
            
            botoes_paciente.addStretch()
            layout_paciente.addLayout(botoes_paciente)
            layout.addWidget(grupo_paciente)
            
            # Botões principais
            botoes_principais = QHBoxLayout()
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            
            botoes_principais.addWidget(btn_cancelar)
            
            botoes_principais.addStretch()
            
            btn_confirmar = QPushButton("✅ Confirmar e Finalizar")

            def confirmar_assinatura_declaracao():
                # Usar sistema modular - esta validação será feita pelo novo sistema
                # Finalizar declaração com assinatura
                self.finalizar_declaracao_com_assinatura_moderna()
                dialog.accept()
                
            btn_confirmar.clicked.connect(confirmar_assinatura_declaracao)
            botoes_principais.addWidget(btn_confirmar)
            
            layout.addLayout(botoes_principais)
            
            dialog.exec()
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao abrir janela de assinatura:\n\n{str(e)}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao iniciar assinatura:\n\n{str(e)}")

    def finalizar_declaracao_com_assinatura(self):
        """Finaliza a declaração com dados de assinatura"""
        try:
            # Obter conteúdo atual
            conteudo_html = self.texto_declaracao_editor.toHtml()
            
            # Adicionar dados de assinatura
            from datetime import datetime
            data_hora_assinatura = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
            
            # Atualizar o HTML com dados de assinatura
            conteudo_html = conteudo_html.replace(
                "[A preencher aquando da assinatura]", 
                data_hora_assinatura
            )
            
            # Marcar checkbox de concordância
            conteudo_html = conteudo_html.replace(
                "☐</span> <strong>Concordo e submeto o presente formulário</strong>",
                "☑️</span> <strong>Concordo e submeto o presente formulário</strong>"
            )
            
            # Atualizar editor
            self.texto_declaracao_editor.setHtml(conteudo_html)
            
            # Guardar com status de assinado
            paciente_id = self.paciente_data.get('id')
            self.paciente_data['declaracao_saude_html'] = conteudo_html
            self.paciente_data['declaracao_saude_assinada'] = True
            self.paciente_data['declaracao_saude_data_assinatura'] = data_hora_assinatura
            
            # Guardar na base de dados
            success = self.db.update_paciente(paciente_id, self.paciente_data)
            
            if success:
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(self, "Sucesso", f"✅ Declaração de Estado de Saúde assinada com sucesso!\n\n📅 {data_hora_assinatura}")
                
                # Atualizar status visual
                self.status_declaracao.setText("✅ Assinada")
                self.status_declaracao.setStyleSheet("""
                    font-size: 14px; 
                    font-weight: 600;
                    color: #ffffff;
                    padding: 15px;
                    background-color: rgba(46, 204, 113, 0.9);
                    border-radius: 6px;
                """)
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Erro ao guardar assinatura na base de dados.")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao finalizar assinatura:\n\n{str(e)}")

    def finalizar_declaracao_com_assinatura_moderna(self):
        """Finaliza a declaração com assinatura capturada usando sistema moderno"""
        try:
            # Usar dados de assinatura do sistema modular
            if hasattr(self, 'assinatura_paciente_data') and self.assinatura_paciente_data:
                assinatura_paciente_bytes = self.assinatura_paciente_data
                print(f"✅ [DECLARAÇÃO] Assinatura capturada: {len(assinatura_paciente_bytes)} bytes")
            else:
                assinatura_paciente_bytes = None
                print(f"❌ [DECLARAÇÃO] Assinatura não disponível")
            
            # Obter conteúdo atual e aplicar substituições
            conteudo_html = self.texto_declaracao_editor.toHtml()
            conteudo_html = self.substituir_variaveis_template(conteudo_html)
            
            # Adicionar dados de assinatura
            from datetime import datetime
            data_hora_assinatura = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
            
            # Marcar como assinado no HTML se aplicável
            if "[A preencher aquando da assinatura]" in conteudo_html:
                conteudo_html = conteudo_html.replace(
                    "[A preencher aquando da assinatura]", 
                    data_hora_assinatura
                )
            
            if "☐</span> <strong>Concordo e submeto o presente formulário</strong>" in conteudo_html:
                conteudo_html = conteudo_html.replace(
                    "☐</span> <strong>Concordo e submeto o presente formulário</strong>",
                    "☑️</span> <strong>Concordo e submeto o presente formulário</strong>"
                )
            
            # Atualizar editor
            self.texto_declaracao_editor.setHtml(conteudo_html)
            
            # Guardar na base de dados
            paciente_id = self.paciente_data.get('id')
            self.paciente_data['declaracao_saude_html'] = conteudo_html
            self.paciente_data['declaracao_saude_assinada'] = True
            self.paciente_data['declaracao_saude_data_assinatura'] = data_hora_assinatura
            
            # Se há assinatura, guardá-la também
            if assinatura_paciente_bytes:
                self.paciente_data['declaracao_saude_assinatura'] = assinatura_paciente_bytes
            
            success = self.db.update_paciente(paciente_id, self.paciente_data)
            
            if success:
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(
                    self, 
                    "Sucesso", 
                    f"✅ Declaração de Estado de Saúde assinada com sucesso!\n\n"
                    f"📅 {data_hora_assinatura}\n"
                    f"✍️ Assinatura: {'Capturada' if assinatura_paciente_bytes else 'Registro de data/hora'}"
                )
                
                # Atualizar status visual se existir
                if hasattr(self, 'status_declaracao'):
                    self.status_declaracao.setText("✅ Assinada")
                    self.status_declaracao.setStyleSheet("""
                        font-size: 14px; 
                        font-weight: 600;
                        color: #ffffff;
                        padding: 15px;
                        background-color: rgba(46, 204, 113, 0.9);
                        border-radius: 6px;
                    """)
                
                print(f"✅ [DECLARAÇÃO] Finalizada com sucesso: {data_hora_assinatura}")
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", "❌ Erro ao guardar assinatura na base de dados.")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao finalizar assinatura:\n\n{str(e)}")
            print(f"❌ [DECLARAÇÃO] Erro ao finalizar: {e}")

    def imprimir_declaracao_saude(self):
        """Imprime a declaração de estado de saúde"""
        try:
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            from PyQt6.QtGui import QTextDocument
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPrinter.Orientation.Portrait)
            
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir Declaração de Estado de Saúde")
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Criar documento
                document = QTextDocument()
                
                # Preparar HTML para impressão
                html_content = self.texto_declaracao_editor.toHtml()
                
                # Adicionar cabeçalho e rodapé
                html_final = f"""
                <html>
                <head><meta charset="UTF-8"></head>
                <body style="font-family: Calibri, Arial, sans-serif;">
                    {html_content}
                    
                    <hr style="margin: 30pt 0;">
                    <p style="text-align: center; font-size: 10pt; color: #666;">
                        🩺 BIODESK - Sistema de Gestão Clínica<br>
                        Declaração de Estado de Saúde - {self.data_atual()}
                    </p>
                </body>
                </html>
                """
                
                document.setHtml(html_final)
                document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
                document.print(printer)
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(
                    self,
                    "Impressão Enviada",
                    "✅ Declaração de Estado de Saúde enviada para impressão!"
                )
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao imprimir:\n\n{str(e)}")

    def limpar_declaracao_saude(self):
        """Limpa o conteúdo da declaração de saúde"""
        try:
            from biodesk_dialogs import mostrar_confirmacao
            
            resposta = mostrar_confirmacao(
                self,
                "Confirmar Limpeza",
                "⚠️ Tem certeza que deseja limpar toda a declaração?\n\nEsta ação não pode ser desfeita."
            )
            
            if resposta:
                # Recriar template limpo
                self.template_declaracao = self._criar_template_declaracao_saude()
                self.texto_declaracao_editor.setHtml(self.template_declaracao)
                
                # Resetar status
                self.status_declaracao.setText("❌ Não preenchida")
                self.status_declaracao.setStyleSheet("""
                    font-size: 14px; 
                    font-weight: 600;
                    color: #ffffff;
                    padding: 15px;
                    background-color: rgba(255,255,255,0.2);
                    border-radius: 6px;
                """)
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(self, "Sucesso", "✅ Declaração limpa com sucesso!")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao limpar declaração:\n\n{str(e)}")

    def _handle_mouse_click_declaracao(self, event):
        """Trata cliques no mouse no editor de declaração (alternar checkboxes)"""
        try:
            # Chamar o evento original primeiro
            QTextEdit.mousePressEvent(self.texto_declaracao_editor, event)
            
            # Obter cursor no ponto do clique
            cursor = self.texto_declaracao_editor.cursorForPosition(event.position().toPoint())
            cursor.select(cursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()
            
            # Se clicou num checkbox (☐), alternar para marcado (☑️) ou vice-versa
            if word == "☐":
                cursor.insertText("☑️")
            elif word == "☑️":
                cursor.insertText("☐")
                
        except Exception as e:
            print(f"[DEBUG] Erro ao tratar clique: {e}")

    def _handle_mouse_move_declaracao(self, event):
        """Trata movimento do mouse no editor de declaração (mostrar tooltips)"""
        try:
            # Obter cursor na posição do mouse  
            cursor = self.texto_declaracao_editor.cursorForPosition(event.position().toPoint())
            cursor.select(cursor.SelectionType.LineUnderCursor)
            linha = cursor.selectedText()
            
            # Se há checkbox na linha, mostrar tooltip simples
            if '☐' in linha or '☑' in linha:
                tooltip = "Clique para marcar/desmarcar esta opção"
                self.texto_declaracao_editor.setToolTip(tooltip)
            else:
                self.texto_declaracao_editor.setToolTip("")
                
        except Exception as e:
            print(f"[DEBUG] Erro ao tratar movimento: {e}")

    # ===== MÉTODOS DE ESTILO =====
    
    def _style_line_edit(self, line_edit, color="#3498db"):
        """Aplica estilo moderno a um QLineEdit"""
        line_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: white;
                color: #333;
                selection-background-color: {color};
            }}
            QLineEdit:focus {{
                border-color: {color};
                background-color: #fafafa;
            }}
            QLineEdit:hover {{
                border-color: #bdbdbd;
                background-color: #f9f9f9;
            }}
        """)

    def _style_text_edit(self, text_edit, color="#3498db"):
        """Aplica estilo moderno a um QTextEdit"""
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: white;
                color: #333;
                selection-background-color: {color};
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border-color: {color};
                background-color: #fafafa;
            }}
            QTextEdit:hover {{
                border-color: #bdbdbd;
                background-color: #f9f9f9;
            }}
        """)

    def _style_modern_button(self, button, color="#007bff"):
        """Estilo iris FORÇADO: fundo cinza claro → colorido sólido no hover"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #f8f9fa !important;
                color: #6c757d !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 6px !important;
                padding: 8px 16px !important;
                font-size: 14px !important;
                font-weight: bold !important;
                min-height: 32px !important;
                max-height: 38px !important;
                min-width: 140px !important;
            }}
            QPushButton:hover {{
                background-color: {color} !important;
                color: white !important;
                border-color: {color} !important;
            }}
            QPushButton:pressed {{
                background-color: {color} !important;
                color: white !important;
                border-color: {color} !important;
            }}
            QPushButton:disabled {{
                background-color: #e0e0e0;
                color: #6c757d;
                border-color: #e0e0e0;
            }}
        """)

    def _style_canal_button(self, button, color="#007bff"):
        """Estilo IGUAL aos templates: fundo colorido com hover mais claro"""
        button.setStyleSheet(f"""
            QPushButton {{
                font-size: 13px !important;
                font-weight: 600 !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 10px 15px !important;
                background-color: {color} !important;
                color: #2c3e50 !important;
                text-align: left !important;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color, 15)} !important;
                color: #2c3e50 !important;
            }}
            QPushButton:pressed {{
                background-color: {self._lighten_color(color, 25)} !important;
                color: #2c3e50 !important;
            }}
        """)
        button.setMinimumHeight(50)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _style_compact_button(self, button, color="#3498db"):
        """Aplica estilo compacto para botões pequenos com fonte menor"""
        try:
            estilizar_botao_fusao(
                button,
                cor=color,
                size_type="standard",
                radius=6,
                font_size=11,  # Fonte menor
                font_weight="bold",
                linha_central=True,
                usar_checked=False,
            )
        except Exception:
            # Fallback com estilo CSS compacto
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    filter: brightness(1.1);
                }}
                QPushButton:pressed {{
                    filter: brightness(0.9);
                }}
            """)

    def _style_combo_box(self, combo_box):
        """Aplica estilo moderno a um QComboBox"""
        combo_box.setStyleSheet("""
            QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: white;
                color: #333;
            }
            QComboBox:focus {
                border-color: #3498db;
                background-color: #fafafa;
            }
            QComboBox:hover {
                border-color: #bdbdbd;
                background-color: #f9f9f9;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #666;
                margin-right: 8px;
            }
        """)

    def _create_clean_label(self, text):
        """Cria um label simples e limpo - estilo íris"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #333333;
                margin: 0px;
                padding: 0px;
            }
        """)
        return label
    
    def _style_clean_input(self, edit):
        """Aplica estilo limpo aos inputs - estilo íris"""
        edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
    
    def _style_clean_combo(self, combo):
        """Aplica estilo limpo aos combos - estilo íris"""
        combo.setStyleSheet("""
            QComboBox {
                padding: 8px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
                color: #333;
                min-height: 15px;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
    
    def _style_clean_button(self, button, color):
        """Aplica estilo limpo aos botões - estilo íris"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: normal;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color, 0.1)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.2)};
            }}
        """)

    def _darken_color(self, hex_color, factor=0.1):
        """Escurece uma cor hexadecimal"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    def _create_modern_label(self, text, bold=False):
        """Cria um QLabel com estilo moderno"""
        label = QLabel(text)
        weight = "600" if bold else "normal"
        color = "#2c3e50" if bold else "#495057"
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-weight: {weight};
                color: {color};
                padding: 2px 0px;
                margin-bottom: 5px;
            }}
        """)
        return label

    def _style_modern_input(self, input_widget):
        """Aplica estilo moderno a campos de input"""
        input_widget.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background-color: #ffffff;
                color: #212529;
                selection-background-color: #007bff;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #f8f9fa;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #ced4da;
                background-color: #f8f9fa;
            }
            QLineEdit::placeholder {
                color: #6c757d;
                font-style: italic;
            }
        """)

    def _style_modern_combo(self, combo_widget):
        """Aplica estilo moderno a QComboBox"""
        combo_widget.setStyleSheet("""
            QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background-color: #ffffff;
                color: #212529;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QComboBox:hover {
                border-color: #ced4da;
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6c757d;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ced4da;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: white;
                outline: none;
            }
        """)

    def _create_label(self, text, bold=False):
        """Cria um QLabel com estilo consistente"""
        label = QLabel(text)
        weight = "bold" if bold else "normal"
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-weight: {weight};
                color: #333;
                padding: 4px 0px;
            }}
        """)
        return label

class FollowUpDialog(QDialog):
    """Dialog para configurar follow-ups automáticos."""
    
    def __init__(self, paciente_data, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("📅 Agendar Follow-up Automático")
        self.setFixedSize(500, 650)  # Tamanho fixo maior para evitar cortes
        self.setModal(True)
        
        # Centralizar a janela mais alta no ecrã
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 500) // 2
        y = max(50, (screen.height() - 700) // 2)  # Mínimo 50px do topo
        self.move(x, y)
        
        # Estilo geral do dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info do paciente
        info_label = QLabel(f"📋 Paciente: {self.paciente_data.get('nome', 'N/A')}")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: bold; 
                color: #2c3e50; 
                background-color: #ffffff;
                padding: 10px;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout.addWidget(info_label)
        
        # Tipo de follow-up
        tipo_label = QLabel("Tipo de Follow-up:")
        tipo_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057; margin-top: 5px;")
        layout.addWidget(tipo_label)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
                color: #212529;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
                margin-right: 5px;
            }
        """)
        
        # Adicionar itens individualmente com dados associados
        self.combo_tipo.addItem("📧 Follow-up Padrão", "padrao")
        self.combo_tipo.addItem("🆕 Primeira Consulta", "primeira_consulta")
        self.combo_tipo.addItem("💊 Acompanhamento de Tratamento", "tratamento")
        self.combo_tipo.addItem("📊 Evolução e Resultados", "resultado")
        
        self.combo_tipo.setCurrentIndex(0)
        layout.addWidget(self.combo_tipo)
        
        # Quando enviar - opções predefinidas
        quando_label = QLabel("Quando enviar:")
        quando_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057; margin-top: 15px;")
        layout.addWidget(quando_label)
        
        self.radio_group = QButtonGroup()
        self.radio_3_dias = QRadioButton("📅 Em 3 dias")
        self.radio_7_dias = QRadioButton("📅 Em 1 semana")
        self.radio_14_dias = QRadioButton("📅 Em 2 semanas")
        self.radio_custom = QRadioButton("🗓️ Data/hora personalizada")
        
        # Estilo dos radio buttons
        radio_style = """
            QRadioButton {
                font-size: 13px;
                color: #495057;
                padding: 5px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #6c757d;
                border-radius: 9px;
                background-color: #ffffff;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #007bff;
                border-radius: 9px;
                background-color: #007bff;
            }
            QRadioButton::indicator:checked::after {
                content: "";
                width: 6px;
                height: 6px;
                border-radius: 3px;
                background-color: #ffffff;
                margin: 4px;
            }
        """
        
        self.radio_3_dias.setStyleSheet(radio_style)
        self.radio_7_dias.setStyleSheet(radio_style)
        self.radio_14_dias.setStyleSheet(radio_style)
        self.radio_custom.setStyleSheet(radio_style)
        
        self.radio_3_dias.setChecked(True)  # Default
        
        self.radio_group.addButton(self.radio_3_dias, 0)
        self.radio_group.addButton(self.radio_7_dias, 1)
        self.radio_group.addButton(self.radio_14_dias, 2)
        self.radio_group.addButton(self.radio_custom, 3)
        
        layout.addWidget(self.radio_3_dias)
        layout.addWidget(self.radio_7_dias)
        layout.addWidget(self.radio_14_dias)
        layout.addWidget(self.radio_custom)
        
        # Data/hora personalizada
        custom_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate().addDays(3))
        self.time_edit = QTimeEdit(QTime(10, 0))  # 10:00 por default
        
        # Estilo para date/time edits
        datetime_style = """
            QDateEdit, QTimeEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                background-color: #ffffff;
                color: #212529;
                min-height: 18px;
            }
            QDateEdit:focus, QTimeEdit:focus {
                border-color: #007bff;
            }
            QDateEdit:disabled, QTimeEdit:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """
        
        self.date_edit.setStyleSheet(datetime_style)
        self.time_edit.setStyleSheet(datetime_style)
        self.date_edit.setEnabled(False)
        self.time_edit.setEnabled(False)
        
        data_label = QLabel("Data:")
        data_label.setStyleSheet("font-size: 13px; color: #495057; font-weight: 500;")
        hora_label = QLabel("Hora:")
        hora_label.setStyleSheet("font-size: 13px; color: #495057; font-weight: 500;")
        
        custom_layout.addWidget(data_label)
        custom_layout.addWidget(self.date_edit)
        custom_layout.addWidget(hora_label)
        custom_layout.addWidget(self.time_edit)
        layout.addLayout(custom_layout)
        
        # Conectar radio button para habilitar/desabilitar campos
        self.radio_custom.toggled.connect(self._toggle_custom_datetime)
        
        # Preview
        preview_label = QLabel("👀 Preview do agendamento:")
        preview_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057; margin-top: 15px;")
        layout.addWidget(preview_label)
        
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', monospace;
                font-size: 12px;
                color: #495057;
                line-height: 1.4;
            }
        """)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        # Conectar sinais para atualizar preview
        self.combo_tipo.currentTextChanged.connect(self._update_preview)
        self.radio_group.buttonClicked.connect(self._update_preview)
        self.date_edit.dateChanged.connect(self._update_preview)
        self.time_edit.timeChanged.connect(self._update_preview)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_agendar = QPushButton("✅ Agendar Follow-up")
        
        btn_cancelar.clicked.connect(self.reject)
        btn_agendar.clicked.connect(self.accept)
        
        # Estilos dos botões modernos

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_agendar)
        layout.addLayout(btn_layout)
        
        # Atualizar preview inicial
        self._update_preview()
        
    def _toggle_custom_datetime(self, checked):
        """Habilita/desabilita campos de data/hora personalizada."""
        self.date_edit.setEnabled(checked)
        self.time_edit.setEnabled(checked)
        
    def _update_preview(self):
        """Atualiza o preview do agendamento."""
        tipo = self.combo_tipo.currentData() or "padrao"
        
        # Calcular quando será enviado
        if self.radio_3_dias.isChecked():
            quando = datetime.now() + timedelta(days=3)
            dias_apos = 3
        elif self.radio_7_dias.isChecked():
            quando = datetime.now() + timedelta(days=7)
            dias_apos = 7
        elif self.radio_14_dias.isChecked():
            quando = datetime.now() + timedelta(days=14)
            dias_apos = 14
        else:  # custom
            date = self.date_edit.date().toPyDate()
            time = self.time_edit.time().toPyTime()
            quando = datetime.combine(date, time)
            hoje = datetime.now().date()
            dias_apos = (date - hoje).days
            
        # Simular ajuste para horário comercial se não for personalizado
        when_adjusted = quando
        is_custom = self.radio_custom.isChecked()
        
        if not is_custom:
            when_adjusted = self._simulate_business_hours_adjust(quando)
            
        if is_custom:
            preview_text = f"""📧 Tipo: {tipo.replace('_', ' ').title()}
📅 Enviar em: {quando.strftime('%d/%m/%Y às %H:%M')}
⚡ Horário: PERSONALIZADO (mantém hora exata)
⏱️ Daqui a: {dias_apos} dia(s)
📋 Para: {self.paciente_data.get('email', 'Email não definido')}
🌐 Sistema: Retry automático se sem internet"""
        else:
            preview_text = f"""📧 Tipo: {tipo.replace('_', ' ').title()}
📅 Enviar em: {when_adjusted.strftime('%d/%m/%Y às %H:%M')}
⏰ Horário: Entre 11h-17h (horário comercial)
⏱️ Daqui a: {dias_apos} dia(s)
📋 Para: {self.paciente_data.get('email', 'Email não definido')}
🌐 Sistema: Retry automático se sem internet"""
        
        self.preview_label.setText(preview_text)
        
    def _simulate_business_hours_adjust(self, when_dt):
        """Simula o ajuste para horário comercial no preview."""
        import random
        from datetime import time
        target_date = when_dt.date()
        
        # Gerar horário aleatório entre 11h-17h para preview
        random_hour = random.randint(11, 16)
        random_minute = random.randint(0, 59)
        new_time = time(random_hour, random_minute)
        
        return datetime.combine(target_date, new_time)
        
    def get_followup_data(self):
        """Retorna os dados do follow-up configurado."""
        # Determinar tipo usando currentData()
        tipo = self.combo_tipo.currentData() or "padrao"
        is_custom = self.radio_custom.isChecked()
            
        # Calcular quando
        if self.radio_3_dias.isChecked():
            quando = datetime.now() + timedelta(days=3)
            dias_apos = 3
        elif self.radio_7_dias.isChecked():
            quando = datetime.now() + timedelta(days=7)
            dias_apos = 7
        elif self.radio_14_dias.isChecked():
            quando = datetime.now() + timedelta(days=14)
            dias_apos = 14
        else:  # custom
            from datetime import time
            date = self.date_edit.date().toPyDate()
            time_selected = self.time_edit.time().toPyTime()
            quando = datetime.combine(date, time_selected)
            hoje = datetime.now().date()
            dias_apos = (date - hoje).days
            
        return {
            'tipo': tipo,
            'quando': quando,
            'dias_apos': dias_apos,
            'is_custom': is_custom
        }

# NOTA: Este módulo deve ser importado pelo main_window.py
# Não executa aplicação independente para evitar conflitos
if __name__ == '__main__':
    print("⚠️  Este módulo deve ser executado através do main_window.py")
    print("🚀 Execute: python main_window.py")
    exit(1)
