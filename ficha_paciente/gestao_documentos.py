import os
import sys
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
    import psutil
from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter
from services.styles import (
from biodesk_dialogs import BiodeskMessageBox
            import sqlite3
from biodesk_ui_kit import BiodeskUIKit
"""
MÓDULO: Gestão de Documentos
=============================

Sistema completo de gestão de documentos do paciente com:
- Upload e organização de documentos
- Visualização integrada 
- Assinatura digital de PDFs
- Controle de versões e backup
- Interface responsiva com lista categorizada

Extraído de ficha_paciente.py para modularização (Linhas 2948-4338 = ~1390 linhas)
"""


# Imports para verificação de processos
try:
except ImportError:
    psutil = None
    print("⚠️ psutil não disponível - funcionalidade limitada para detecção de arquivos em uso")

# PyQt6 imports
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QScrollArea,
    QFileDialog, QMenu, QApplication, QSplitter
)

# Imports locais
    estilizar_botao_principal, estilizar_botao_secundario, 
    estilizar_botao_perigo, estilizar_botao_sucesso
)


class GestaoDocumentosWidget(QWidget):
    """Widget especializado para gestão completa de documentos do paciente"""
    
    # Sinais para comunicação com o módulo principal
    documento_adicionado = pyqtSignal(str)  # Caminho do documento
    documento_removido = pyqtSignal(str)    # Caminho do documento
    documento_visualizado = pyqtSignal(str) # Caminho do documento
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.paciente_id = None
        self.documentos_data = {}
        
        # Configuração da interface
        self.init_ui()
        self.load_styles()
        
        # Timer para auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.atualizar_lista_documentos)
        
    def init_ui(self):
        """Inicializa a interface completa de gestão de documentos"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Cabeçalho da seção
        header_layout = QHBoxLayout()
        
        # Título principal
        title_label = QLabel("📂 Gestão de Documentos")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botão de atualizar
        btn_refresh = QPushButton("🔄 Atualizar")
        BiodeskUIKit.apply_universal_button_style(btn_refresh)
        btn_refresh.clicked.connect(self.atualizar_lista_documentos)
        header_layout.addWidget(btn_refresh)
        
        # Botão de upload
        btn_upload = QPushButton("📤 Adicionar Documento")
        btn_upload.setObjectName("btn_doc_upload")
        btn_upload.clicked.connect(self.adicionar_documento)
        
        # Aplicar estilo do botão upload
        estilizar_botao_principal(btn_upload)
        header_layout.addWidget(btn_upload)
        
        layout.addLayout(header_layout)
        
        # Área de status/estatísticas
        self.criar_area_estatisticas(layout)
        
        # Lista de documentos
        self.criar_lista_documentos(layout)
        
        # Área de ações dos documentos
        self.criar_area_acoes(layout)
        
    def criar_area_estatisticas(self, layout):
        """Cria área com estatísticas dos documentos"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                padding: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # Labels de estatísticas
        self.stats_total = QLabel("📄 Total: 0")
        self.stats_pdfs = QLabel("📋 PDFs: 0")
        self.stats_imagens = QLabel("🖼️ Imagens: 0")
        self.stats_outros = QLabel("📎 Outros: 0")
        
        for label in [self.stats_total, self.stats_pdfs, self.stats_imagens, self.stats_outros]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #495057;
                    padding: 5px 10px;
                    background-color: white;
                    border-radius: 4px;
                    margin: 2px;
                }
            """)
            stats_layout.addWidget(label)
        
        stats_layout.addStretch()
        layout.addWidget(stats_frame)
        
    def criar_lista_documentos(self, layout):
        """Cria a lista de documentos com scroll"""
        # Container com scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
        """)
        
        # ✅ LISTA DE DOCUMENTOS MELHORADA
        self.documentos_list = QListWidget()
        self.documentos_list.setMinimumHeight(300)
        self.documentos_list.setAlternatingRowColors(True)
        self.documentos_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.documentos_list.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)
        
        self.documentos_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                padding: 5px;
                outline: none;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                border-bottom: 1px solid #e9ecef;
                padding: 12px 15px;
                margin: 2px 0;
                border-radius: 6px;
                min-height: 20px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd !important;
                border: 1px solid #2196f3;
                transition: all 0.2s ease;
            }
            QListWidget::item:selected {
                background-color: #1976d2 !important;
                color: white !important;
                font-weight: bold;
                border: 2px solid #0d47a1;
            }
            QListWidget::item:selected:hover {
                background-color: #1565c0 !important;
                border: 2px solid #0d47a1;
            }
            QListWidget:focus {
                border: 2px solid #2196f3;
            }
        """)
        
        # ✅ CONFIGURAÇÕES DE INTERAÇÃO MELHORADAS
        # Menu contextual
        self.documentos_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.documentos_list.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        # Double-click para visualizar
        self.documentos_list.itemDoubleClicked.connect(self.visualizar_documento_selecionado)
        
        # ✅ EVENTOS DE SELEÇÃO ADICIONAIS
        self.documentos_list.itemClicked.connect(self.on_documento_selecionado)
        self.documentos_list.currentItemChanged.connect(self.on_selecao_mudou)
        
        scroll_area.setWidget(self.documentos_list)
        layout.addWidget(scroll_area, 1)  # Expansível
        
        # ✅ LABEL DE INFORMAÇÃO PARA FEEDBACK DE SELEÇÃO
        self.label_info = QLabel("📁 Nenhum documento selecionado")
        self.label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_info.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 13px;
                font-style: italic;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.label_info)
        
    def criar_area_acoes(self, layout):
        """Cria área com botões de ação"""
        acoes_frame = QFrame()
        acoes_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                padding: 10px;
            }
        """)
        acoes_layout = QHBoxLayout(acoes_frame)
        
        # Botões de ação
        btn_visualizar = QPushButton("👁️ Visualizar")
        btn_visualizar.clicked.connect(self.visualizar_documento_selecionado)
        
        btn_email = QPushButton("📧 Enviar Email")
        btn_email.clicked.connect(self.enviar_documento_email)
        
        btn_remover = QPushButton("🗑️ Remover")
        btn_remover.clicked.connect(self.remover_documento)
        
        # Aplicar estilos
        estilizar_botao_secundario(btn_visualizar)
        estilizar_botao_secundario(btn_email)
        estilizar_botao_perigo(btn_remover)
        
        # Adicionar botões
        acoes_layout.addWidget(btn_visualizar)
        acoes_layout.addWidget(btn_email)
        acoes_layout.addStretch()
        acoes_layout.addWidget(btn_remover)
        
        layout.addWidget(acoes_frame)
        
    def load_styles(self):
        """Carrega estilos específicos do módulo"""
        self.setStyleSheet("""
            GestaoDocumentosWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        
    def set_paciente_id(self, paciente_id):
        """Define o ID do paciente e carrega seus documentos"""
        self.paciente_id = paciente_id
        self.atualizar_lista_documentos()
        
    def get_pasta_documentos(self):
        """Retorna a pasta base do paciente com lógica inteligente de seleção."""
        if not self.paciente_id:
            return None

        base = Path("Documentos_Pacientes")
        base.mkdir(parents=True, exist_ok=True)

        # 1) Tenta pasta exacta {id}
        pasta_exacta = base / str(self.paciente_id)
        # 2) Tenta pasta com prefixo {id}_*
        candidatos = sorted(base.glob(f"{self.paciente_id}_*"))

        # Reunir todas as opções
        todas_opcoes = []
        if pasta_exacta.exists():
            todas_opcoes.append(pasta_exacta)
        todas_opcoes.extend(candidatos)

        if not todas_opcoes:
            # Cria {id} se nada existir
            pasta_exacta.mkdir(parents=True, exist_ok=True)
            return pasta_exacta

        # 🎯 LÓGICA INTELIGENTE DE SELEÇÃO:
        
        # 1º: Tentar correspondência exata com nome do paciente da BD
        nome_paciente_bd = self._obter_nome_paciente_bd()
        if nome_paciente_bd:
            nome_esperado = nome_paciente_bd.replace(' ', '_')
            pasta_esperada = f"{self.paciente_id}_{nome_esperado}"
            
            for pasta in todas_opcoes:
                if pasta.name == pasta_esperada:
                    # print(f"✅ Encontrada pasta exata: {pasta.name}")
                    return pasta
        
        # 2º: Priorizar pasta com documentos MAIS RECENTES (indica atividade atual)
        melhor_pasta = None
        melhor_score = -1
        
        for pasta in todas_opcoes:
            try:
                arquivos = [f for f in pasta.rglob("*") if f.is_file() and not f.name.endswith('.meta')]
                num_docs = len(arquivos)
                
                # Calcular data de modificação mais recente
                data_mais_recente = 0
                if arquivos:
                    data_mais_recente = max(f.stat().st_mtime for f in arquivos)
                
                # Score: priorizar atividade recente + quantidade de documentos
                # Normalizar timestamp para evitar overflow
                score_tempo = data_mais_recente / 1000000 if data_mais_recente > 0 else 0
                score_total = score_tempo + (num_docs * 0.1)  # Peso menor para quantidade
                
                print(f"📂 {pasta.name}: {num_docs} docs, score: {score_total:.2f}")
                
                if score_total > melhor_score:
                    melhor_score = score_total
                    melhor_pasta = pasta
                    
            except Exception as e:
                print(f"⚠️ Erro ao analisar {pasta.name}: {e}")
                continue
        
        # Fallback: usar primeira opção disponível
        if melhor_pasta is None:
            melhor_pasta = todas_opcoes[0]
            print(f"🔄 Usando fallback: {melhor_pasta.name}")

        print(f"🎯 Pasta selecionada: {melhor_pasta.name}")
        return melhor_pasta

    def _obter_nome_paciente_bd(self):
        """Obtém o nome do paciente da base de dados"""
        try:
            db_path = Path('pacientes.db')
            if not db_path.exists():
                return None
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM pacientes WHERE id = ?', (self.paciente_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            print(f"⚠️ Erro ao buscar nome na BD: {e}")
            return None

    def atualizar_lista_documentos(self):
        """Atualiza lista de documentos (recursivo) e mostra caminho relativo - OTIMIZADO."""
        # ✅ PRESERVAR SELEÇÃO ATUAL
        item_selecionado = self.documentos_list.currentItem()
        arquivo_selecionado = None
        if item_selecionado:
            arquivo_selecionado = item_selecionado.data(Qt.ItemDataRole.UserRole)
        
        # ⚡ BLOQUEAR SIGNALS DURANTE ATUALIZAÇÃO
        self.documentos_list.blockSignals(True)
        self.documentos_list.clear()
        
        if not self.paciente_id:
            self.documentos_list.blockSignals(False)
            return

        pasta_docs = self.get_pasta_documentos()
        if not pasta_docs or not pasta_docs.exists():
            self.documentos_list.blockSignals(False)
            return

        total_docs = total_pdfs = total_imagens = total_outros = 0
        
        # ⚡ OTIMIZAÇÃO: Usar list comprehension para coleta rápida
        try:
            # Cache de extensões para evitar conversões repetidas
            ext_cache = {}
            
            # Coletar arquivos de forma mais eficiente
            arquivos_data = []
            for arquivo in pasta_docs.rglob("*"):
                if not arquivo.is_file():
                    continue
                
                # Cache do stat para evitar múltiplas chamadas
                stat_info = arquivo.stat()
                ext = ext_cache.get(arquivo.name) or arquivo.suffix.lower()
                if arquivo.name not in ext_cache:
                    ext_cache[arquivo.name] = ext
                
                arquivos_data.append((arquivo, stat_info, ext))

            # ⚡ ORDENAÇÃO OTIMIZADA: usar key pré-computada
            arquivos_data.sort(key=lambda x: x[1].st_mtime, reverse=True)

            # ⚡ BATCH PROCESSING: Preparar todos os itens antes de adicionar
            itens_lista = []
            item_para_selecionar = None
            
            for arquivo, stat_info, ext in arquivos_data:
                total_docs += 1
                
                # Categorização otimizada
                if ext == ".pdf":
                    total_pdfs += 1; icon = "📋"
                elif ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}:
                    total_imagens += 1; icon = "🖼️"
                else:
                    total_outros += 1; icon = "📎"

                # Cálculos otimizados
                rel = arquivo.relative_to(pasta_docs)
                size_mb = stat_info.st_size / 1048576  # Divisão direta ao invés de (1024*1024)
                modified = datetime.fromtimestamp(stat_info.st_mtime)

                item = QListWidgetItem()
                item.setText(
                    f"{icon} {rel}\n"
                    f"   📏 {size_mb:.1f} MB  📅 {modified.strftime('%d/%m/%Y %H:%M')}"
                )
                item.setData(Qt.ItemDataRole.UserRole, str(arquivo))
                itens_lista.append(item)
                
                # ✅ MARCAR ITEM PARA RESELEÇÃO
                if arquivo_selecionado and str(arquivo) == arquivo_selecionado:
                    item_para_selecionar = item

            # ⚡ BATCH INSERT: Adicionar todos os itens de uma vez
            for item in itens_lista:
                self.documentos_list.addItem(item)

        except Exception as e:
            print(f"❌ Erro ao atualizar lista: {e}")
        finally:
            # ⚡ REATIVAR SIGNALS
            self.documentos_list.blockSignals(False)

        # Atualizar estatísticas
        self.stats_total.setText(f"📄 Total: {total_docs}")
        self.stats_pdfs.setText(f"📋 PDFs: {total_pdfs}")
        self.stats_imagens.setText(f"🖼️ Imagens: {total_imagens}")
        self.stats_outros.setText(f"📎 Outros: {total_outros}")
        
        # ✅ RESTAURAR SELEÇÃO ANTERIOR
        if item_para_selecionar:
            self.documentos_list.setCurrentItem(item_para_selecionar)
            
    def _atualizar_estatisticas_rapidas(self):
        """Atualiza apenas as estatísticas sem recarregar a lista - OTIMIZADO"""
        total_docs = self.documentos_list.count()
        total_pdfs = total_imagens = total_outros = 0
        
        # ⚡ CONTAGEM RÁPIDA pelos itens já na lista
        for i in range(total_docs):
            item = self.documentos_list.item(i)
            texto = item.text()
            if texto.startswith("📋"):
                total_pdfs += 1
            elif texto.startswith("🖼️"):
                total_imagens += 1
            else:
                total_outros += 1
        
        # Atualizar labels
        self.stats_total.setText(f"📄 Total: {total_docs}")
        self.stats_pdfs.setText(f"📋 PDFs: {total_pdfs}")
        self.stats_imagens.setText(f"🖼️ Imagens: {total_imagens}")
        self.stats_outros.setText(f"📎 Outros: {total_outros}")
            
    def adicionar_documento(self):
        """Abre diálogo para adicionar novo documento"""
        if not self.paciente_id:
            BiodeskMessageBox.warning(self, "Aviso", "⚠️ Selecione um paciente primeiro!")
            return
            
        # Diálogo de seleção de arquivo
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Documento",
            "",
            "Todos os Arquivos (*);;PDFs (*.pdf);;Imagens (*.jpg *.jpeg *.png *.gif *.bmp);;Documentos (*.doc *.docx *.txt)"
        )
        
        if not arquivo:
            return
            
        try:
            pasta_docs = self.get_pasta_documentos()
            arquivo_origem = Path(arquivo)
            arquivo_destino = pasta_docs / arquivo_origem.name
            
            # Verificar se já existe
            if arquivo_destino.exists():
                resposta = BiodeskMessageBox.question(
                    self, 
                    "Arquivo Existente",
                    f"📄 O arquivo '{arquivo_origem.name}' já existe.\n\n🔄 Deseja substituir?"
                )
                if not resposta:  # Se resposta for False (Não)
                    return
            
            # Copiar arquivo
            shutil.copy2(arquivo, arquivo_destino)
            
            # Atualizar lista
            self.atualizar_lista_documentos()
            
            # Emitir sinal
            self.documento_adicionado.emit(str(arquivo_destino))
            
            BiodeskMessageBox.information(
                self, 
                "Sucesso", 
                f"✅ Documento adicionado com sucesso!\n\n📁 {arquivo_destino.name}"
            )
            
        except Exception as e:
            BiodeskMessageBox.critical(
                self, 
                "Erro", 
                f"❌ Erro ao adicionar documento:\n\n{str(e)}"
            )
    
    def visualizar_documento_selecionado(self):
        """Visualiza o documento selecionado"""
        item = self.documentos_list.currentItem()
        if not item:
            BiodeskMessageBox.warning(self, "Aviso", "⚠️ Selecione um documento para visualizar!")
            return
            
        caminho_doc = item.data(Qt.ItemDataRole.UserRole)
        self.abrir_documento(item)
    
    # ✅ NOVOS MÉTODOS DE CALLBACK PARA MELHOR UX
    def on_documento_selecionado(self, item):
        """Callback quando um documento é clicado"""
        if item:
            nome_doc = item.text().split(' - ')[0]  # Nome do arquivo
            self.label_info.setText(f"📄 Documento selecionado: {nome_doc}")
            
            # Feedback visual adicional
            item.setToolTip(f"Documento: {nome_doc}\nDuplo-clique para visualizar")
    
    def on_selecao_mudou(self, atual, anterior):
        """Callback quando a seleção muda"""
        if atual:
            nome_doc = atual.text().split(' - ')[0]
            self.label_info.setText(f"📄 {nome_doc} selecionado")
        else:
            self.label_info.setText("📁 Nenhum documento selecionado")
        
    def abrir_documento(self, item):
        """Abre documento selecionado no visualizador apropriado"""
        if not item:
            return
            
        caminho_arquivo = item.data(Qt.ItemDataRole.UserRole)
        if not caminho_arquivo or not os.path.exists(caminho_arquivo):
            BiodeskMessageBox.warning(self, "Aviso", "⚠️ Arquivo não encontrado!")
            return
            
        try:
            # Emitir sinal
            self.documento_visualizado.emit(caminho_arquivo)
            
            # Abrir com aplicação padrão do sistema
            if sys.platform == "win32":
                os.startfile(caminho_arquivo)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{caminho_arquivo}'")
            else:  # Linux
                os.system(f"xdg-open '{caminho_arquivo}'")
                
        except Exception as e:
            BiodeskMessageBox.critical(
                self, 
                "Erro", 
                f"❌ Erro ao abrir documento:\n\n{str(e)}"
            )
    
    def enviar_documento_email(self):
        """Envia documento selecionado por email"""
        item = self.documentos_list.currentItem()
        if not item:
            BiodeskMessageBox.warning(self, "Aviso", "⚠️ Selecione um documento para enviar!")
            return
            
        caminho_doc = item.data(Qt.ItemDataRole.UserRole)
        
        # Aqui seria integrado com o sistema de email
        # Por enquanto, apenas uma mensagem informativa
        BiodeskMessageBox.information(
            self,
            "Email",
            f"📧 Função de email será integrada!\n\n📎 Arquivo: {Path(caminho_doc).name}"
        )
    
    def remover_documento(self):
        """Remove documento selecionado - OTIMIZADO E SEGURO"""
        item = self.documentos_list.currentItem()
        if not item:
            BiodeskMessageBox.warning(self, "Aviso", "⚠️ Selecione um documento para remover!")
            return
            
        # ⚡ CAPTURAR DADOS DO ITEM ANTES DE QUALQUER OPERAÇÃO
        try:
            caminho_doc = item.data(Qt.ItemDataRole.UserRole)
            lista_index = self.documentos_list.row(item)
            nome_arquivo = Path(caminho_doc).name
        except RuntimeError:
            BiodeskMessageBox.critical(self, "Erro", "❌ Item selecionado inválido!")
            return
        
        # Confirmação
        resposta = BiodeskMessageBox.question(
            self,
            "Confirmar Remoção Definitiva",
            f"🗑️ Deseja realmente remover DEFINITIVAMENTE o documento?\n\n📄 {nome_arquivo}\n\n⚠️ O arquivo será apagado permanentemente!\n❌ Esta ação NÃO pode ser desfeita!"
        )
        
        if resposta != True:  # BiodeskMessageBox.question retorna True/False
            return
            
        try:            
            # ✅ VERIFICAÇÃO RÁPIDA DE USO
            arquivo_em_uso = False
            try:
                # Teste rápido de acesso exclusivo
                with open(caminho_doc, 'r+b'):
                    pass
            except (IOError, OSError):
                arquivo_em_uso = True
            
            if arquivo_em_uso:
                BiodeskMessageBox.warning(
                    self,
                    "Arquivo em Uso",
                    f"📄 O arquivo está aberto em outro programa!\n\n"
                    f"Por favor, feche o arquivo e tente novamente.\n\n"
                    f"📁 {nome_arquivo}"
                )
                return
            
            # ⚡ REMOÇÃO OTIMIZADA: Tentativa única com fallback
            arquivo_removido = False
            try:
                # Tentar remoção direta primeiro
                if os.path.exists(caminho_doc):
                    os.remove(caminho_doc)
                    arquivo_removido = True
                else:
                    arquivo_removido = True  # Já não existe
                    
            except PermissionError:
                # Fallback: tentar alterar permissões e remover
                try:
                    os.chmod(caminho_doc, 0o777)
                    time.sleep(0.1)
                    os.remove(caminho_doc)
                    arquivo_removido = True
                except Exception:
                    pass
            
            if arquivo_removido:
                # ⚡ REMOÇÃO SEGURA DA LISTA: Verificar se item ainda existe
                try:
                    if lista_index >= 0 and lista_index < self.documentos_list.count():
                        self.documentos_list.takeItem(lista_index)
                except RuntimeError:
                    # Item já foi removido, recarregar lista completa
                    self.atualizar_lista_documentos()
                    return
                
                # ⚡ ATUALIZAR APENAS ESTATÍSTICAS (sem recarregar toda a lista)
                self._atualizar_estatisticas_rapidas()
                
                # Emitir sinal
                self.documento_removido.emit(caminho_doc)
                
                BiodeskMessageBox.information(
                    self,
                    "Sucesso",
                    f"✅ Documento removido definitivamente!\n\n📄 {nome_arquivo}"
                )
            else:
                # Se falhou, usar método completo como fallback
                self._remover_com_retry(caminho_doc)
                self.atualizar_lista_documentos()
                
                BiodeskMessageBox.information(
                    self,
                    "Sucesso",
                    f"✅ Documento removido definitivamente!\n\n📄 {nome_arquivo}"
                )
            
        except PermissionError as e:
            BiodeskMessageBox.critical(
                self,
                "Erro de Permissão",
                f"❌ Sem permissão para remover o arquivo!\n\n"
                f"Código: {e.errno}\n"
                f"Arquivo: {nome_arquivo}\n\n"
                f"💡 Execute como administrador ou verifique se o arquivo não está protegido."
            )
        except FileNotFoundError:
            # Arquivo já foi removido - remover da lista também
            self.documentos_list.takeItem(lista_index)
            self._atualizar_estatisticas_rapidas()
            BiodeskMessageBox.warning(
                self,
                "Arquivo Não Encontrado",
                f"⚠️ O arquivo já foi removido ou não existe:\n\n📄 {nome_arquivo}"
            )
        except Exception as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"❌ Erro inesperado ao remover documento:\n\n"
                f"Erro: {str(e)}\n"
                f"Tipo: {type(e).__name__}\n"
                f"Arquivo: {nome_arquivo}"
            )
            # Remover da lista mesmo assim
            self.atualizar_lista_documentos()
        except Exception as e:
            BiodeskMessageBox.critical(
                self,
                "Erro",
                f"❌ Erro inesperado ao remover documento:\n\n"
                f"Erro: {str(e)}\n"
                f"Tipo: {type(e).__name__}\n"
                f"Arquivo: {nome_arquivo}"
            )
            
            # Atualizar lista
            self.atualizar_lista_documentos()
    
    def _arquivo_em_uso(self, caminho_arquivo):
        """Verifica se arquivo está em uso por outro processo"""
        try:
            # Tentar abrir o arquivo para escrita exclusiva
            with open(caminho_arquivo, 'r+b'):
                pass
            return False
        except (IOError, OSError):
            return True
    
    def _fechar_arquivo_forcado(self, caminho_arquivo):
        """Tenta fechar arquivo em processos que podem estar usando"""
        if not psutil:
            print("⚠️ psutil não disponível - pulando verificação de processos")
            return
            
        try:
            # Procurar processos que podem ter o arquivo aberto
            nome_arquivo = Path(caminho_arquivo).name
            
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    if proc.info['open_files']:
                        for file_info in proc.info['open_files']:
                            if nome_arquivo in file_info.path:
                                print(f"⚠️ Arquivo aberto em: {proc.info['name']} (PID: {proc.info['pid']})")
                                # Não forçar fechamento - apenas avisar
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"⚠️ Erro ao verificar processos: {e}")
    
    def _remover_com_retry(self, caminho_arquivo):
        """Remove arquivo com múltiplas tentativas"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                if os.path.exists(caminho_arquivo):
                    # Remover atributos de proteção se existirem
                    try:
                        os.chmod(caminho_arquivo, 0o777)
                    except:
                        pass  # Ignorar se não conseguir alterar permissões
                        
                    time.sleep(0.1)  # Pequena pausa
                    
                    os.remove(caminho_arquivo)
                    print(f"✅ Arquivo removido na tentativa {tentativa + 1}")
                    return
                else:
                    print("⚠️ Arquivo já não existe")
                    return
                    
            except OSError as e:
                if tentativa < max_tentativas - 1:
                    print(f"⚠️ Tentativa {tentativa + 1} falhada, tentando novamente...")
                    time.sleep(1)  # Aguardar 1 segundo
                else:
                    raise e  # Re-lançar a exceção na última tentativa
    
    def mostrar_menu_contextual(self, posicao):
        """Mostra menu contextual com clique direito"""
        item = self.documentos_list.itemAt(posicao)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        
        menu = QMenu(self)
        
        action_visualizar = menu.addAction("👁️ Visualizar")
        action_visualizar.triggered.connect(self.visualizar_documento_selecionado)
        
        action_email = menu.addAction("📧 Enviar por Email")
        action_email.triggered.connect(self.enviar_documento_email)
        
        menu.addSeparator()
        
        action_remover = menu.addAction("🗑️ Remover")
        action_remover.triggered.connect(self.remover_documento)
        
        menu.exec(self.documentos_list.mapToGlobal(posicao))


# ===== FUNÇÃO DE TESTE =====
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Teste do widget
    widget = GestaoDocumentosWidget()
    widget.setWindowTitle("🧪 Teste - Gestão de Documentos")
    widget.resize(800, 600)
    widget.show()
    
    # Simular paciente para teste
    widget.set_paciente_id("TESTE_123")
    
    sys.exit(app.exec())
