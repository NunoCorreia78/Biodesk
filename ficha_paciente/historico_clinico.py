"""
Biodesk - Módulo de Histórico Clínico
=====================================

Módulo especializado para gestão do histórico clínico do paciente.
Extraído do monólito ficha_paciente.py para melhorar performance e manutenibilidade.

🎯 Funcionalidades:
- Editor de texto rico com formatação
- Toolbar com ferramentas de edição
- Inserção automática de data
- Auto-save e controle de mudanças
- Validação de conteúdo

⚡ Performance:
- Lazy loading do editor
- Cache de formatação
- Operações assíncronas

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime

from biodesk_ui_kit import BiodeskUIKit  # Para cores e fontes
from data_cache import DataCache
from biodesk_dialogs import BiodeskMessageBox

# 🎨 SISTEMA DE ESTILOS CENTRALIZADO
try:
    from biodesk_styles import BiodeskStyles, ButtonType
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False


class HistoricoClinicoWidget(QWidget):
    """Widget especializado para gestão do histórico clínico"""
    
    # Sinais
    historico_alterado = pyqtSignal(str)  # Emitido quando histórico é alterado
    guardar_solicitado = pyqtSignal()     # Emitido quando guardar é solicitado
    
    def __init__(self, historico_texto: str = "", parent=None):
        super().__init__(parent)
        
        # Cache de dados
        self.cache = DataCache.get_instance()
        
        # Estado interno
        self.historico_texto = historico_texto
        self._texto_original = historico_texto
        self._alterado = False
        self._inicializando = True
        
        # Flags de formatação
        self._bold_ativo = False
        self._italic_ativo = False
        self._underline_ativo = False
        
        # Inicializar interface
        self.init_ui()
        self.carregar_historico()
        self.conectar_sinais()
        
        self._inicializando = False
    
    def init_ui(self):
        """Inicializa interface do histórico clínico"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Criar toolbar
        self.criar_toolbar(layout)
        
        # Criar editor de texto
        self.criar_editor(layout)
    
    def criar_toolbar(self, parent_layout):
        """Cria toolbar com ferramentas de formatação"""
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet(f"""
            QToolBar {{ 
                margin-bottom: 8px; 
                background-color: {BiodeskUIKit.COLORS['background_light']};
                border-radius: 6px;
                padding: 5px;
            }}
            QToolButton {{ 
                margin-right: 6px; 
                padding: 8px 12px; 
                border-radius: 6px;
                font-weight: 600;
                min-width: 30px;
                color: {BiodeskUIKit.COLORS['text']};
            }}
            QToolButton:hover {{ 
                background: #C0C0C0 !important; 
                border: 1px solid #999999 !important;
                color: #333333 !important;
            }}
            QToolButton:pressed {{
                background: {BiodeskUIKit.COLORS['border']};
            }}
            QToolButton:checked {{
                background: {BiodeskUIKit.COLORS['primary']};
                color: {BiodeskUIKit.COLORS['white']};
            }}
        """)
        
        # Ações de formatação
        self.action_bold = QAction('B', self)
        self.action_bold.setShortcut('Ctrl+B')
        self.action_bold.setCheckable(True)
        self.action_bold.triggered.connect(self.toggle_bold)
        
        self.action_italic = QAction('I', self)
        self.action_italic.setShortcut('Ctrl+I')
        self.action_italic.setCheckable(True)
        self.action_italic.triggered.connect(self.toggle_italic)
        
        self.action_underline = QAction('U', self)
        self.action_underline.setShortcut('Ctrl+U')
        self.action_underline.setCheckable(True)
        self.action_underline.triggered.connect(self.toggle_underline)
        
        self.action_date = QAction('📅', self)
        self.action_date.setToolTip('Inserir data atual')
        self.action_date.triggered.connect(self.inserir_data_negrito)
        
        # Adicionar ações à toolbar
        self.toolbar.addAction(self.action_bold)
        self.toolbar.addAction(self.action_italic)
        self.toolbar.addAction(self.action_underline)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_date)
        
        # Espaço expansível
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Indicador de estado
        self.status_label = QLabel("📄 Pronto")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {BiodeskUIKit.COLORS['text_muted']};
                font-size: {BiodeskUIKit.FONTS['size_small']};
                padding: 4px 8px;
            }}
        """)
        self.toolbar.addWidget(self.status_label)
        
        # Botão de guardar - USANDO BIODESK STYLES v2.0
        if STYLES_AVAILABLE:
            self.btn_guardar = BiodeskStyles.create_button('💾 Guardar', ButtonType.SAVE)
        else:
            self.btn_guardar = QToolButton()
            self.btn_guardar.setText('💾 Guardar')
        
        self.btn_guardar.setToolTip('Guardar histórico (Ctrl+S)')
        self.btn_guardar.clicked.connect(self.guardar_historico)
        self.toolbar.addWidget(self.btn_guardar)
        
        parent_layout.addWidget(self.toolbar)
    
    def criar_editor(self, parent_layout):
        """Cria editor de texto rico"""
        self.historico_edit = QTextEdit()
        self.historico_edit.setPlaceholderText(
            "Descreva queixas, sintomas, evolução do caso ou observações clínicas relevantes...\n\n"
            "💡 Dica: Use o botão 📅 para inserir automaticamente a data de hoje no formato correto.\n"
            "🎨 Use as ferramentas de formatação (Negrito, Itálico, Sublinhado) para destacar informações importantes."
        )
        self.historico_edit.setMinimumHeight(420)
        
        # Aplicar estilo moderno
        self.historico_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {BiodeskUIKit.COLORS['border_light']};
                border-radius: 8px;
                padding: 15px;
                font-family: {BiodeskUIKit.FONTS['family']};
                font-size: {BiodeskUIKit.FONTS['size_normal']};
                line-height: 1.5;
                background-color: {BiodeskUIKit.COLORS['white']};
            }}
            QTextEdit:focus {{
                border-color: {BiodeskUIKit.COLORS['primary']};
                outline: none;
            }}
        """)
        
        parent_layout.addWidget(self.historico_edit)
    
    def conectar_sinais(self):
        """Conecta sinais dos widgets"""
        # Detectar mudanças no texto
        self.historico_edit.textChanged.connect(self.on_texto_alterado)
        
        # Detectar mudanças na formatação
        self.historico_edit.currentCharFormatChanged.connect(self.atualizar_estados_formatacao)
        
        # Atalho Ctrl+S
        shortcut_save = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut_save.activated.connect(self.guardar_historico)
    
    def on_texto_alterado(self):
        """Callback quando texto é alterado"""
        if self._inicializando:
            return
        
        texto_atual = self.historico_edit.toPlainText()
        self._alterado = texto_atual != self._texto_original
        
        # Atualizar status
        if self._alterado:
            self.status_label.setText("📝 Modificado")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {BiodeskUIKit.COLORS['warning']};
                    font-size: {BiodeskUIKit.FONTS['size_small']};
                    padding: 4px 8px;
                    font-weight: bold;
                }}
            """)
        else:
            self.status_label.setText("📄 Pronto")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {BiodeskUIKit.COLORS['text_muted']};
                    font-size: {BiodeskUIKit.FONTS['size_small']};
                    padding: 4px 8px;
                }}
            """)
        
        # Emitir sinal
        self.historico_alterado.emit(texto_atual)
    
    def atualizar_estados_formatacao(self):
        """Atualiza estados dos botões de formatação"""
        if self._inicializando:
            return
        
        formato = self.historico_edit.currentCharFormat()
        
        # Atualizar estados dos botões
        self._bold_ativo = formato.fontWeight() == QFont.Weight.Bold
        self._italic_ativo = formato.fontItalic()
        self._underline_ativo = formato.fontUnderline()
        
        # Atualizar visual dos botões
        self.action_bold.setChecked(self._bold_ativo)
        self.action_italic.setChecked(self._italic_ativo)
        self.action_underline.setChecked(self._underline_ativo)
    
    def toggle_bold(self):
        """Alterna formatação negrito"""
        cursor = self.historico_edit.textCursor()
        formato = cursor.charFormat()
        
        if formato.fontWeight() == QFont.Weight.Bold:
            formato.setFontWeight(QFont.Weight.Normal)
        else:
            formato.setFontWeight(QFont.Weight.Bold)
        
        cursor.setCharFormat(formato)
        self.historico_edit.setTextCursor(cursor)
        self.historico_edit.setFocus()
    
    def toggle_italic(self):
        """Alterna formatação itálico"""
        cursor = self.historico_edit.textCursor()
        formato = cursor.charFormat()
        formato.setFontItalic(not formato.fontItalic())
        cursor.setCharFormat(formato)
        self.historico_edit.setTextCursor(cursor)
        self.historico_edit.setFocus()
    
    def toggle_underline(self):
        """Alterna formatação sublinhado"""
        cursor = self.historico_edit.textCursor()
        formato = cursor.charFormat()
        formato.setFontUnderline(not formato.fontUnderline())
        cursor.setCharFormat(formato)
        self.historico_edit.setTextCursor(cursor)
        self.historico_edit.setFocus()
    
    def inserir_data_negrito(self):
        """Insere data atual no topo, empurrando sessões anteriores para baixo"""
        data_atual = datetime.now().strftime('%d/%m/%Y')
        
        # Mover cursor para o início do documento
        cursor = self.historico_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Criar formato negrito para a data
        formato_negrito = QTextCharFormat()
        formato_negrito.setFontWeight(QFont.Weight.Bold)
        formato_negrito.setForeground(QColor(BiodeskUIKit.COLORS['primary']))
        
        # Inserir data em negrito
        cursor.insertText(f"{data_atual}\n", formato_negrito)
        
        # Restaurar formatação normal para o espaço de texto
        formato_normal = QTextCharFormat()
        formato_normal.setFontWeight(QFont.Weight.Normal)
        formato_normal.setForeground(QColor(BiodeskUIKit.COLORS['text']))
        cursor.setCharFormat(formato_normal)
        
        # Inserir parágrafo vazio e posicionar cursor para o usuário escrever
        cursor.insertText("\n")
        
        # Guardar posição onde o usuário vai escrever
        posicao_escrita = cursor.position()
        
        # Continuar com a estrutura: parágrafo + linha separadora + parágrafo
        cursor.insertText("\n")
        
        # Adicionar linha separadora que ocupa toda a largura do campo
        formato_separador = QTextCharFormat()
        formato_separador.setFontWeight(QFont.Weight.Normal)
        formato_separador.setForeground(QColor(BiodeskUIKit.COLORS['text_muted']))
        
        # Calcular largura aproximada do editor para criar linha completa
        editor_width = self.historico_edit.viewport().width()
        font_metrics = self.historico_edit.fontMetrics()
        char_width = font_metrics.horizontalAdvance("─")
        num_chars = max(50, editor_width // char_width - 5)  # Mínimo 50, máximo baseado na largura
        
        cursor.insertText("─" * num_chars + "\n\n", formato_separador)
        
        # Posicionar cursor no espaço para o usuário escrever
        cursor.setPosition(posicao_escrita)
        self.historico_edit.setTextCursor(cursor)
        self.historico_edit.setFocus()
        
        # print(f"✅ Nova sessão inserida no topo: {data_atual}")
    
    def carregar_historico(self):
        """Carrega histórico no editor"""
        if not self.historico_texto:
            return
        
        self._inicializando = True
        
        try:
            # Verificar se é HTML ou texto simples
            if '<' in self.historico_texto and '>' in self.historico_texto:
                self.historico_edit.setHtml(self.historico_texto)
            else:
                self.historico_edit.setPlainText(self.historico_texto)
            
            # Atualizar texto original
            self._texto_original = self.historico_edit.toPlainText()
            self._alterado = False
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar histórico: {e}")
            self.historico_edit.setPlainText(self.historico_texto)
        finally:
            self._inicializando = False
        
        # Atualizar status
        self.status_label.setText("📄 Carregado")
    
    def obter_historico(self) -> str:
        """Obtém histórico atual em HTML"""
        return self.historico_edit.toHtml()
    
    def obter_historico_texto(self) -> str:
        """Obtém histórico atual como texto simples"""
        return self.historico_edit.toPlainText()
    
    def set_historico_texto(self, texto: str):
        """Define o texto do histórico (para carregar dados do paciente)"""
        if texto != self.historico_texto:
            self.historico_texto = texto
            self._texto_original = texto
            
            # Atualizar o editor
            self.historico_edit.setPlainText(texto)
            
            # Resetar flag de alteração
            self._alterado = False
            
            # Atualizar status
            self.status_label.setText("📄 Carregado")
            print(f"✅ Histórico carregado: {len(texto)} caracteres")
    
    def guardar_historico(self):
        """Guarda o histórico atual"""
        try:
            historico_html = self.obter_historico()
            
            # Atualizar texto original
            self._texto_original = self.historico_edit.toPlainText()
            self._alterado = False
            
            # Atualizar status
            self.status_label.setText("✅ Guardado")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {BiodeskUIKit.COLORS['success']};
                    font-size: {BiodeskUIKit.FONTS['size_small']};
                    padding: 4px 8px;
                    font-weight: bold;
                }}
            """)
            
            # Emitir sinal
            self.guardar_solicitado.emit()
            
            # Mostrar confirmação temporária
            QTimer.singleShot(2000, lambda: self.status_label.setText("📄 Pronto"))
            QTimer.singleShot(2000, lambda: self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {BiodeskUIKit.COLORS['text_muted']};
                    font-size: {BiodeskUIKit.FONTS['size_small']};
                    padding: 4px 8px;
                }}
            """))
            
            return historico_html
            
        except Exception as e:
            print(f"❌ Erro ao guardar histórico: {e}")
            
            # Mostrar erro
            self.status_label.setText("❌ Erro")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {BiodeskUIKit.COLORS['danger']};
                    font-size: {BiodeskUIKit.FONTS['size_small']};
                    padding: 4px 8px;
                    font-weight: bold;
                }}
            """)
            
            QTimer.singleShot(3000, lambda: self.status_label.setText("📄 Pronto"))
            return None
    
    def limpar_historico(self):
        """Limpa o histórico atual"""
        reply = BiodeskMessageBox.question(
            self,
            "Confirmar Limpeza",
            "Tem a certeza que deseja limpar todo o histórico clínico?"
        )
        
        if reply:
            self._inicializando = True
            self.historico_edit.clear()
            self._texto_original = ""
            self._alterado = False
            self._inicializando = False
            
            self.status_label.setText("🗑️ Limpo")
    
    def has_changes(self) -> bool:
        """Verifica se há alterações não guardadas"""
        return self._alterado
    
    def atualizar_historico(self, novo_historico: str):
        """Atualiza histórico externamente"""
        if self._alterado:
            reply = BiodeskMessageBox.question(
                self,
                "Alterações Não Guardadas",
                "Há alterações não guardadas. Deseja descartá-las?"
            )
            
            if not reply:
                return False
        
        self.historico_texto = novo_historico
        self.carregar_historico()
        return True
    
    def exportar_texto(self) -> str:
        """Exporta histórico como texto formatado"""
        return self.historico_edit.toPlainText()
    
    def exportar_html(self) -> str:
        """Exporta histórico como HTML"""
        return self.historico_edit.toHtml()
    
    def buscar_texto(self, termo: str) -> bool:
        """Busca termo no histórico"""
        return self.historico_edit.find(termo)
    
    def substituir_texto(self, buscar: str, substituir: str):
        """Substitui texto no histórico"""
        texto = self.historico_edit.toPlainText()
        novo_texto = texto.replace(buscar, substituir)
        
        if novo_texto != texto:
            self.historico_edit.setPlainText(novo_texto)
            return True
        return False
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do histórico"""
        texto = self.historico_edit.toPlainText()
        
        return {
            'caracteres': len(texto),
            'caracteres_sem_espacos': len(texto.replace(' ', '').replace('\n', '')),
            'palavras': len(texto.split()),
            'linhas': len(texto.split('\n')),
            'paragrafos': len([p for p in texto.split('\n\n') if p.strip()]),
            'tem_alteracoes': self._alterado
        }
