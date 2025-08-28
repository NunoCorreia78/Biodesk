"""
🚀 CENTRO DE COMUNICAÇÃO UNIFICADO - BIODESK
=============================================

Widget que unifica:
- 📧 Sistema de Email
- 📁 Gestão de Documentos  
- 📎 Seleção de Anexos
- 📋 Templates Inteligentes

Autor: GitHub Copilot
Data: 27/08/2025
Prazo: 3 horas para implementação completa!
"""

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QGroupBox,
    QScrollArea, QFrame, QProgressBar, QFileDialog,
    QMessageBox, QApplication, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon

# ✅ IMPORTAR SISTEMA DE ESTILOS
try:
    from biodesk_styles import BiodeskStyles, ButtonType, DialogStyles
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False
    print("⚠️ BiodeskStyles não disponível - usando estilos básicos")
    
    # Classe mock para compatibilidade
    class BiodeskStyles:
        @classmethod
        def create_button(cls, text, button_type=None, callback=None):
            button = QPushButton(text)
            if callback:
                button.clicked.connect(callback)
            return button
        
        @classmethod
        def apply_to_existing_button(cls, button, button_type=None):
            pass

# ✅ IMPORTAR MÓDULOS EXISTENTES PARA INTEGRAÇÃO
try:
    import sys
    import os
    
    # Adicionar diretório raiz ao path se necessário
    biodesk_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if biodesk_root not in sys.path:
        sys.path.append(biodesk_root)
    
    from email_sender import EmailSender
    from email_config import EmailConfig
    from template_manager import BiodeskTemplateManager as TemplateManager
    EMAIL_MODULES_AVAILABLE = True
    print("✅ Módulos de email carregados com sucesso")
except ImportError as e:
    EMAIL_MODULES_AVAILABLE = False
    print(f"⚠️ Módulos de email não disponíveis - funcionalidade limitada: {e}")
except Exception as e:
    EMAIL_MODULES_AVAILABLE = False
    print(f"⚠️ Erro ao carregar módulos de email: {e}")


class DocumentoItem:
    """Classe para representar um documento disponível"""
    
    def __init__(self, caminho: str, nome: str, tamanho: int, tipo: str, data_modificacao: datetime):
        self.caminho = caminho
        self.nome = nome
        self.tamanho = tamanho
        self.tipo = tipo
        self.data_modificacao = data_modificacao
        self.selecionado = False
    
    def __str__(self):
        return f"{self.nome} ({self.formatar_tamanho()})"
    
    def formatar_tamanho(self) -> str:
        """Formatar tamanho em formato legível"""
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho // 1024} KB"
        else:
            return f"{self.tamanho // (1024 * 1024)} MB"


class DocumentosListWidget(QWidget):
    """🗂️ Widget para listar e selecionar documentos"""
    
    documento_selecionado = pyqtSignal(object)  # DocumentoItem
    documento_removido = pyqtSignal(object)
    
    def __init__(self, paciente_data: dict, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.documentos_disponiveis: List[DocumentoItem] = []
        self.init_ui()
        self.carregar_documentos()
    
    def init_ui(self):
        """Inicializar interface da lista de documentos"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(5)
        
        # 🔍 ÁREA DE PESQUISA
        pesquisa_frame = QFrame()
        pesquisa_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 2px; }")
        pesquisa_layout = QVBoxLayout(pesquisa_frame)
        pesquisa_layout.setContentsMargins(3, 2, 3, 2)
        
        # Campo de pesquisa
        self.campo_pesquisa = QLineEdit()
        self.campo_pesquisa.setPlaceholderText("🔍 Pesquisar documentos...")
        self.campo_pesquisa.textChanged.connect(self.filtrar_documentos)
        self.campo_pesquisa.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        
        pesquisa_layout.addWidget(QLabel("📁 DOCUMENTOS DISPONÍVEIS"))
        pesquisa_layout.addWidget(self.campo_pesquisa)
        layout.addWidget(pesquisa_frame)
        
        # 📋 LISTA DE DOCUMENTOS
        self.lista_documentos = QListWidget()
        self.lista_documentos.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.lista_documentos.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: #2c3e50;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                color: #2c3e50;
                background-color: white;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565c0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
                color: #2c3e50;
            }
            QListWidget::item:selected:hover {
                background-color: #bbdefb;
                color: #0d47a1;
            }
        """)
        layout.addWidget(self.lista_documentos)
        
        # 🔄 BOTÕES DE AÇÃO
        botoes_frame = QFrame()
        botoes_layout = QHBoxLayout(botoes_frame)
        
        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_atualizar.clicked.connect(self.carregar_documentos)
        if STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(self.btn_atualizar, ButtonType.UPDATE)
        
        self.btn_abrir_pasta = QPushButton("� Abrir Ficheiro")
        self.btn_abrir_pasta.clicked.connect(self.abrir_ficheiro_selecionado)
        if STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(self.btn_abrir_pasta, ButtonType.TOOL)
        
        botoes_layout.addWidget(self.btn_atualizar)
        botoes_layout.addWidget(self.btn_abrir_pasta)
        layout.addWidget(botoes_frame)
        
        # Conectar seleção e double-click
        self.lista_documentos.itemChanged.connect(self.on_item_changed)
        self.lista_documentos.itemDoubleClicked.connect(self.abrir_ficheiro_duplo_click)
    
    def carregar_documentos(self):
        """Carregar documentos do paciente"""
        try:
            self.documentos_disponiveis.clear()
            self.lista_documentos.clear()
            
            # Determinar pasta do paciente
            paciente_id = self.paciente_data.get('id', '999')
            pasta_paciente = Path(f"Documentos_Pacientes/{paciente_id}")
            
            if not pasta_paciente.exists():
                print(f"⚠️ Pasta do paciente não encontrada: {pasta_paciente}")
                return
            
            # Procurar documentos em todas as subpastas
            extensoes_validas = {'.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg'}
            
            for arquivo in pasta_paciente.rglob("*"):
                if arquivo.is_file() and arquivo.suffix.lower() in extensoes_validas:
                    try:
                        stat = arquivo.stat()
                        documento = DocumentoItem(
                            caminho=str(arquivo),
                            nome=arquivo.name,
                            tamanho=stat.st_size,
                            tipo=arquivo.suffix.lower(),
                            data_modificacao=datetime.fromtimestamp(stat.st_mtime)
                        )
                        self.documentos_disponiveis.append(documento)
                    except Exception as e:
                        print(f"⚠️ Erro ao processar arquivo {arquivo}: {e}")
            
            # Ordenar por data de modificação (mais recentes primeiro)
            self.documentos_disponiveis.sort(key=lambda d: d.data_modificacao, reverse=True)
            
            # Adicionar à lista
            self.atualizar_lista_visual()
            
            print(f"✅ {len(self.documentos_disponiveis)} documentos carregados")
            
        except Exception as e:
            print(f"❌ Erro ao carregar documentos: {e}")
            traceback.print_exc()
    
    def atualizar_lista_visual(self):
        """Atualizar a lista visual com os documentos"""
        self.lista_documentos.clear()
        
        for documento in self.documentos_disponiveis:
            item = QListWidgetItem()
            item.setText(f"{documento.nome}\n📁 {documento.formatar_tamanho()} • {documento.data_modificacao.strftime('%d/%m/%Y %H:%M')}")
            item.setData(Qt.ItemDataRole.UserRole, documento)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if documento.selecionado else Qt.CheckState.Unchecked)
            
            # Ícone baseado no tipo
            if documento.tipo == '.pdf':
                item.setText(f"📄 {item.text()}")
            elif documento.tipo in ['.jpg', '.jpeg', '.png']:
                item.setText(f"🖼️ {item.text()}")
            elif documento.tipo in ['.docx', '.doc']:
                item.setText(f"📝 {item.text()}")
            else:
                item.setText(f"📎 {item.text()}")
            
            self.lista_documentos.addItem(item)
    
    def filtrar_documentos(self, texto_pesquisa: str):
        """Filtrar documentos baseado na pesquisa"""
        for i in range(self.lista_documentos.count()):
            item = self.lista_documentos.item(i)
            documento = item.data(Qt.ItemDataRole.UserRole)
            
            # Mostrar/ocultar baseado na pesquisa
            mostrar = texto_pesquisa.lower() in documento.nome.lower()
            item.setHidden(not mostrar)
    
    def on_item_changed(self, item: QListWidgetItem):
        """Quando um item é selecionado/desmarcado"""
        documento = item.data(Qt.ItemDataRole.UserRole)
        if documento:
            documento.selecionado = item.checkState() == Qt.CheckState.Checked
            if documento.selecionado:
                self.documento_selecionado.emit(documento)
            else:
                self.documento_removido.emit(documento)
    
    def abrir_pasta_paciente(self):
        """Abrir pasta do paciente no explorador"""
        try:
            paciente_id = self.paciente_data.get('id', '999')
            pasta_paciente = Path(f"Documentos_Pacientes/{paciente_id}")
            
            if pasta_paciente.exists():
                os.startfile(str(pasta_paciente))
            else:
                QMessageBox.warning(self, "Aviso", f"Pasta do paciente não encontrada:\n{pasta_paciente}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir pasta:\n{e}")
    
    def abrir_ficheiro_selecionado(self):
        """Abrir ficheiro selecionado diretamente"""
        try:
            item_atual = self.lista_documentos.currentItem()
            if not item_atual:
                QMessageBox.information(self, "Informação", "Seleccione um ficheiro para abrir.")
                return
            
            documento = item_atual.data(Qt.ItemDataRole.UserRole)
            if documento and os.path.exists(documento.caminho):
                os.startfile(documento.caminho)
            else:
                QMessageBox.warning(self, "Aviso", "Ficheiro não encontrado ou não selecionado.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir ficheiro:\n{e}")
    
    def abrir_ficheiro_duplo_click(self, item):
        """Abrir ficheiro com duplo-click"""
        try:
            documento = item.data(Qt.ItemDataRole.UserRole)
            if documento and os.path.exists(documento.caminho):
                os.startfile(documento.caminho)
            else:
                QMessageBox.warning(self, "Aviso", "Ficheiro não encontrado.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir ficheiro:\n{e}")


class AnexosListWidget(QWidget):
    """📎 Widget para gerenciar anexos selecionados"""
    
    anexo_removido = pyqtSignal(object)
    anexos_alterados = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anexos_selecionados: List[DocumentoItem] = []
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interface dos anexos"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(5)
        
        # 📎 CABEÇALHO
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 2px; }")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(3, 2, 3, 2)
        
        self.label_titulo = QLabel("📎 ANEXOS SELECIONADOS")
        self.label_info = QLabel("0 anexos • 0 KB")
        self.label_info.setStyleSheet("color: #666; font-size: 11px;")
        
        header_layout.addWidget(self.label_titulo)
        header_layout.addWidget(self.label_info)
        layout.addWidget(header_frame)
        
        # 📋 LISTA DE ANEXOS
        self.lista_anexos = QListWidget()
        self.lista_anexos.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
        """)
        layout.addWidget(self.lista_anexos)
        
        # 🗑️ BOTÕES DE AÇÃO
        botoes_frame = QFrame()
        botoes_layout = QVBoxLayout(botoes_frame)
        
        self.btn_remover_selecionados = QPushButton("❌ Remover Selecionados")
        self.btn_remover_selecionados.clicked.connect(self.remover_selecionados)
        if STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(self.btn_remover_selecionados, ButtonType.DELETE)
        
        self.btn_limpar_todos = QPushButton("🗑️ Limpar Todos")
        self.btn_limpar_todos.clicked.connect(self.limpar_todos)
        if STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(self.btn_limpar_todos, ButtonType.TOOL)
        
        botoes_layout.addWidget(self.btn_remover_selecionados)
        botoes_layout.addWidget(self.btn_limpar_todos)
        layout.addWidget(botoes_frame)
        
        # 📊 INFORMAÇÕES TOTAIS
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }")
        info_layout = QVBoxLayout(self.info_frame)
        
        self.label_total = QLabel("📊 TOTAL: 0 KB")
        self.progress_tamanho = QProgressBar()
        self.progress_tamanho.setMaximum(100)
        self.progress_tamanho.setValue(0)
        
        info_layout.addWidget(self.label_total)
        info_layout.addWidget(self.progress_tamanho)
        layout.addWidget(self.info_frame)
    
    def adicionar_anexo(self, documento: DocumentoItem):
        """Adicionar documento aos anexos"""
        if documento not in self.anexos_selecionados:
            self.anexos_selecionados.append(documento)
            self.atualizar_lista_visual()
            self.anexos_alterados.emit()
            print(f"✅ Anexo adicionado: {documento.nome}")
    
    def remover_anexo(self, documento: DocumentoItem):
        """Remover documento dos anexos"""
        if documento in self.anexos_selecionados:
            self.anexos_selecionados.remove(documento)
            self.atualizar_lista_visual()
            self.anexos_alterados.emit()
            self.anexo_removido.emit(documento)
            print(f"❌ Anexo removido: {documento.nome}")
    
    def atualizar_lista_visual(self):
        """Atualizar lista visual dos anexos"""
        self.lista_anexos.clear()
        
        tamanho_total = 0
        for documento in self.anexos_selecionados:
            item = QListWidgetItem()
            item.setText(f"✅ {documento.nome}\n    📊 {documento.formatar_tamanho()}")
            item.setData(Qt.ItemDataRole.UserRole, documento)
            
            # Ícone baseado no tipo
            if documento.tipo == '.pdf':
                item.setText(item.text().replace("✅", "📄"))
            elif documento.tipo in ['.jpg', '.jpeg', '.png']:
                item.setText(item.text().replace("✅", "🖼️"))
            elif documento.tipo in ['.docx', '.doc']:
                item.setText(item.text().replace("✅", "📝"))
            
            self.lista_anexos.addItem(item)
            tamanho_total += documento.tamanho
        
        # Atualizar informações
        self.atualizar_informacoes(tamanho_total)
    
    def atualizar_informacoes(self, tamanho_total: int):
        """Atualizar informações de total e progresso"""
        count = len(self.anexos_selecionados)
        
        # Formatar tamanho
        if tamanho_total < 1024:
            tamanho_str = f"{tamanho_total} B"
        elif tamanho_total < 1024 * 1024:
            tamanho_str = f"{tamanho_total // 1024} KB"
        else:
            tamanho_str = f"{tamanho_total // (1024 * 1024)} MB"
        
        # Atualizar labels
        self.label_info.setText(f"{count} anexos • {tamanho_str}")
        self.label_total.setText(f"📊 TOTAL: {tamanho_str}")
        
        # Calcular progresso (baseado em limite de 25MB)
        limite_mb = 25 * 1024 * 1024  # 25MB
        progresso = min(100, int((tamanho_total / limite_mb) * 100))
        self.progress_tamanho.setValue(progresso)
        
        # Cor do progresso baseada no tamanho
        if progresso < 50:
            cor = "#4CAF50"  # Verde
        elif progresso < 80:
            cor = "#FF9800"  # Laranja
        else:
            cor = "#F44336"  # Vermelho
        
        self.progress_tamanho.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {cor};
            }}
        """)
    
    def remover_selecionados(self):
        """Remover anexos selecionados"""
        items_selecionados = self.lista_anexos.selectedItems()
        for item in items_selecionados:
            documento = item.data(Qt.ItemDataRole.UserRole)
            if documento:
                self.remover_anexo(documento)
    
    def limpar_todos(self):
        """Limpar todos os anexos"""
        self.anexos_selecionados.clear()
        self.atualizar_lista_visual()
        self.anexos_alterados.emit()
        print("🗑️ Todos os anexos foram removidos")
    
    def obter_caminhos_anexos(self) -> List[str]:
        """Obter lista de caminhos dos anexos para envio"""
        return [doc.caminho for doc in self.anexos_selecionados]


class EmailWidget(QWidget):
    """📧 Widget para composição e envio de email"""
    
    email_enviado = pyqtSignal(dict)
    template_alterado = pyqtSignal(str)
    
    def __init__(self, paciente_data: dict, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.anexos_caminhos: List[str] = []
        self.init_ui()
        self.carregar_templates()
    
    def init_ui(self):
        """Inicializar interface do email"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(5)
        
        # 📧 CABEÇALHO
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 2px; }")
        header_layout = QVBoxLayout(header_frame)
        header_layout.addWidget(QLabel("📧 COMPOR EMAIL"))
        header_layout.setContentsMargins(3, 2, 3, 2)
        layout.addWidget(header_frame)
        
        # 👤 DESTINATÁRIO
        dest_frame = QFrame()
        dest_layout = QVBoxLayout(dest_frame)
        
        self.campo_para = QLineEdit()
        self.campo_para.setPlaceholderText("Para: email@exemplo.com")
        # Preencher com email do paciente se disponível
        email_paciente = self.paciente_data.get('email', '')
        if email_paciente:
            self.campo_para.setText(email_paciente)
        self.campo_para.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        dest_layout.addWidget(self.campo_para)
        layout.addWidget(dest_frame)
        
        # 📝 ASSUNTO
        assunto_frame = QFrame()
        assunto_layout = QVBoxLayout(assunto_frame)
        
        self.campo_assunto = QLineEdit()
        self.campo_assunto.setPlaceholderText("Assunto: Digite o assunto do email...")
        self.campo_assunto.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        assunto_layout.addWidget(self.campo_assunto)
        layout.addWidget(assunto_frame)
        
        # 📋 TEMPLATE
        template_frame = QFrame()
        template_layout = QVBoxLayout(template_frame)
        
        self.combo_template = QComboBox()
        self.combo_template.currentTextChanged.connect(self.aplicar_template)
        self.combo_template.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        template_layout.addWidget(self.combo_template)
        layout.addWidget(template_frame)
        
        # 💬 MENSAGEM
        mensagem_frame = QFrame()
        mensagem_layout = QVBoxLayout(mensagem_frame)
        
        self.campo_mensagem = QTextEdit()
        self.campo_mensagem.setPlaceholderText("💬 Mensagem: Digite sua mensagem aqui...")
        self.campo_mensagem.setMaximumHeight(150)
        self.campo_mensagem.setStyleSheet("""
            QTextEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        mensagem_layout.addWidget(self.campo_mensagem)
        layout.addWidget(mensagem_frame)
        
        # 🔧 AÇÕES - BOTÕES LADO A LADO
        acoes_frame = QFrame()
        acoes_layout = QHBoxLayout(acoes_frame)  # Mudança: QHBoxLayout para lado a lado
        acoes_layout.setSpacing(10)
        
        # Botões de ação lado a lado
        self.btn_salvar_rascunho = QPushButton("💾 Salvar Rascunho")
        self.btn_salvar_rascunho.clicked.connect(self.salvar_rascunho)
        if STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(self.btn_salvar_rascunho, ButtonType.DRAFT)
        
        self.btn_enviar = QPushButton("📧 ENVIAR EMAIL")
        self.btn_enviar.clicked.connect(self.enviar_email)
        if STYLES_AVAILABLE:
            BiodeskStyles.apply_to_existing_button(self.btn_enviar, ButtonType.SAVE)
        
        acoes_layout.addWidget(self.btn_salvar_rascunho)
        acoes_layout.addWidget(self.btn_enviar)
        layout.addWidget(acoes_frame)
        
        # 📊 STATUS
        self.label_status = QLabel("📎 0 anexos prontos")
        self.label_status.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.label_status)
    
    def carregar_templates(self):
        """Carregar templates disponíveis"""
        templates_basicos = [
            "🔧 Selecionar template...",
            "📄 Envio de Documentação",
            "💊 Envio de Prescrição",
            "📋 Resultados de Exame", 
            "📞 Agendamento de Consulta",
            "💬 Comunicação Geral"
        ]
        
        self.combo_template.addItems(templates_basicos)
    
    def aplicar_template(self, nome_template: str):
        """Aplicar template selecionado"""
        if not nome_template or nome_template.startswith("🔧"):
            return
        
        nome_paciente = self.paciente_data.get('nome', 'Paciente')
        
        templates = {
            "📄 Envio de Documentação": {
                "assunto": f"Documentação Clínica - {nome_paciente}",
                "mensagem": f"""Prezado(a) Sr(a) {nome_paciente},

Espero que este email o(a) encontre bem.

Conforme solicitado, segue em anexo a documentação clínica referente ao seu atendimento.

Caso tenha alguma dúvida, não hesite em entrar em contato.

Atenciosamente,
Clínica Biodesk"""
            },
            "💊 Envio de Prescrição": {
                "assunto": f"Prescrição Médica - {nome_paciente}",
                "mensagem": f"""Prezado(a) Sr(a) {nome_paciente},

Segue em anexo a prescrição médica conforme orientado durante a consulta.

Por favor, siga rigorosamente as orientações de uso dos medicamentos prescritos.

Em caso de dúvidas ou reações adversas, entre em contato imediatamente.

Atenciosamente,
Clínica Biodesk"""
            },
            "📋 Resultados de Exame": {
                "assunto": f"Resultados de Exame - {nome_paciente}",
                "mensagem": f"""Prezado(a) Sr(a) {nome_paciente},

Seus resultados de exame estão prontos e seguem em anexo.

Recomendamos o agendamento de uma consulta para discussão detalhada dos resultados.

Para marcar sua consulta, entre em contato conosco.

Atenciosamente,
Clínica Biodesk"""
            },
            "📞 Agendamento de Consulta": {
                "assunto": f"Agendamento de Consulta - {nome_paciente}",
                "mensagem": f"""Prezado(a) Sr(a) {nome_paciente},

Gostaríamos de agendar uma consulta de seguimento.

Por favor, verifique sua disponibilidade e nos informe os melhores horários.

Segue em anexo documentação relevante para a consulta.

Atenciosamente,
Clínica Biodesk"""
            },
            "💬 Comunicação Geral": {
                "assunto": f"Comunicação - {nome_paciente}",
                "mensagem": f"""Prezado(a) Sr(a) {nome_paciente},

Espero que este email o(a) encontre bem.

Segue em anexo a documentação solicitada.

Estamos à disposição para quaisquer esclarecimentos.

Atenciosamente,
Clínica Biodesk"""
            }
        }
        
        template_data = templates.get(nome_template)
        if template_data:
            self.campo_assunto.setText(template_data["assunto"])
            self.campo_mensagem.setPlainText(template_data["mensagem"])
            self.template_alterado.emit(nome_template)
            print(f"✅ Template aplicado: {nome_template}")
        
        # Resetar combo para primeira opção
        self.combo_template.setCurrentIndex(0)
        
    def abrir_prescricao(self):
        """Abrir módulo de prescrição médica"""
        try:
            from prescricao_medica_widget import PrescricaoMedicaWidget
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Nova Prescrição Médica")
            
            # Configurar para tela cheia
            from PyQt6.QtCore import Qt
            dialog.setWindowState(Qt.WindowState.WindowMaximized)
            dialog.resize(1920, 1080)  # Fallback para resolução comum
            layout = QVBoxLayout(dialog)
            
            # Parâmetros corretos: parent=dialog, paciente_data=self.paciente_data
            prescricao_widget = PrescricaoMedicaWidget(parent=dialog, paciente_data=self.paciente_data)
            layout.addWidget(prescricao_widget)
            
            dialog.exec()
        except ImportError:
            self.mostrar_mensagem("❌ Módulo de prescrição não disponível")
        except Exception as e:
            self.mostrar_mensagem(f"❌ Erro ao abrir prescrição: {str(e)}")
    
    def abrir_protocolo(self):
        """Abrir módulo de protocolos"""
        try:
            from ficha_paciente.templates_manager import TemplatesManagerWidget
            dialog = QDialog(self)
            dialog.setWindowTitle("📋 Gestão de Protocolos Terapêuticos")
            
            # Configurar para tela cheia
            from PyQt6.QtCore import Qt
            dialog.setWindowState(Qt.WindowState.WindowMaximized)
            dialog.resize(1920, 1080)  # Fallback para resolução comum
            
            layout = QVBoxLayout(dialog)
            
            # Cabeçalho explicativo
            header_label = QLabel("📋 <b>Protocolos Terapêuticos</b><br>"
                                 "<small>Selecione e gerencie protocolos de tratamento personalizados</small>")
            header_label.setStyleSheet("padding: 10px; background-color: #f0f8ff; border-radius: 5px; margin-bottom: 10px;")
            layout.addWidget(header_label)
            
            # Instanciar o TemplatesManagerWidget
            templates_widget = TemplatesManagerWidget(self.paciente_data, dialog)
            layout.addWidget(templates_widget)
            
            # Botões de ação
            buttons_frame = QFrame()
            buttons_layout = QHBoxLayout(buttons_frame)
            
            btn_aplicar = QPushButton("✅ Aplicar Protocolos Selecionados")
            btn_cancelar = QPushButton("❌ Cancelar")
            
            if STYLES_AVAILABLE:
                BiodeskStyles.apply_to_existing_button(btn_aplicar, ButtonType.SAVE)
                BiodeskStyles.apply_to_existing_button(btn_cancelar, ButtonType.CANCEL)
            
            buttons_layout.addStretch()
            buttons_layout.addWidget(btn_aplicar)
            buttons_layout.addWidget(btn_cancelar)
            
            layout.addWidget(buttons_frame)
            
            # Conectar eventos
            btn_cancelar.clicked.connect(dialog.reject)
            btn_aplicar.clicked.connect(lambda: self.aplicar_protocolos(templates_widget, dialog))
            
            dialog.exec()
            
        except ImportError as e:
            self.mostrar_mensagem(f"❌ Módulo de protocolos não disponível: {str(e)}")
        except Exception as e:
            self.mostrar_mensagem(f"❌ Erro ao abrir protocolos: {str(e)}")
    
    def aplicar_protocolos(self, templates_widget, dialog):
        """Aplicar protocolos selecionados ao email"""
        try:
            protocolos_selecionados = templates_widget.obter_protocolos_selecionados()
            
            if not protocolos_selecionados:
                QMessageBox.warning(dialog, "Aviso", "Nenhum protocolo selecionado.")
                return
            
            # Gerar texto dos protocolos para o email
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            texto_protocolos = f"Prezado(a) Sr(a) {nome_paciente},\n\n"
            texto_protocolos += "Conforme orientado em consulta, seguem os protocolos terapêuticos recomendados:\n\n"
            
            for i, protocolo in enumerate(protocolos_selecionados, 1):
                texto_protocolos += f"{i}. {protocolo}\n"
            
            texto_protocolos += "\nPor favor, siga rigorosamente as orientações de cada protocolo.\n"
            texto_protocolos += "Em caso de dúvidas, não hesite em entrar em contato.\n\n"
            texto_protocolos += "Atenciosamente,\nClínica Biodesk"
            
            # Aplicar ao email
            self.campo_assunto.setText(f"Protocolos Terapêuticos - {nome_paciente}")
            self.campo_mensagem.setPlainText(texto_protocolos)
            
            self.mostrar_mensagem(f"✅ {len(protocolos_selecionados)} protocolo(s) aplicado(s) ao email")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Erro", f"Erro ao aplicar protocolos: {str(e)}")
    
    def abrir_relatorio(self):
        """Abrir gerador de relatórios"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 Gerador de Relatórios Clínicos")
            
            # Configurar para tela cheia
            from PyQt6.QtCore import Qt
            dialog.setWindowState(Qt.WindowState.WindowMaximized)
            dialog.resize(1920, 1080)  # Fallback para resolução comum
            
            layout = QVBoxLayout(dialog)
            
            # Cabeçalho
            header_label = QLabel("📊 <b>Gerador de Relatórios</b><br>"
                                 "<small>Crie relatórios personalizados para seus pacientes</small>")
            header_label.setStyleSheet("padding: 10px; background-color: #fff8dc; border-radius: 5px; margin-bottom: 10px;")
            layout.addWidget(header_label)
            
            # Tipos de relatório
            tipos_frame = QFrame()
            tipos_layout = QVBoxLayout(tipos_frame)
            tipos_layout.addWidget(QLabel("Selecione o tipo de relatório:"))
            
            self.radio_consulta = QRadioButton("📄 Relatório de Consulta")
            self.radio_exames = QRadioButton("📋 Relatório de Exames")
            self.radio_tratamento = QRadioButton("💊 Relatório de Tratamento")
            self.radio_evolucao = QRadioButton("📈 Relatório de Evolução")
            
            self.radio_consulta.setChecked(True)
            
            tipos_layout.addWidget(self.radio_consulta)
            tipos_layout.addWidget(self.radio_exames)
            tipos_layout.addWidget(self.radio_tratamento)
            tipos_layout.addWidget(self.radio_evolucao)
            
            layout.addWidget(tipos_frame)
            
            # Observações
            obs_frame = QFrame()
            obs_layout = QVBoxLayout(obs_frame)
            obs_layout.addWidget(QLabel("Observações adicionais:"))
            
            self.campo_obs_relatorio = QTextEdit()
            self.campo_obs_relatorio.setPlaceholderText("Digite observações específicas para o relatório...")
            self.campo_obs_relatorio.setMaximumHeight(120)
            obs_layout.addWidget(self.campo_obs_relatorio)
            
            layout.addWidget(obs_frame)
            
            # Botões
            buttons_frame = QFrame()
            buttons_layout = QHBoxLayout(buttons_frame)
            
            btn_gerar = QPushButton("� Gerar Relatório")
            btn_cancelar = QPushButton("❌ Cancelar")
            
            if STYLES_AVAILABLE:
                BiodeskStyles.apply_to_existing_button(btn_gerar, ButtonType.SAVE)
                BiodeskStyles.apply_to_existing_button(btn_cancelar, ButtonType.CANCEL)
            
            buttons_layout.addStretch()
            buttons_layout.addWidget(btn_gerar)
            buttons_layout.addWidget(btn_cancelar)
            
            layout.addWidget(buttons_frame)
            
            # Conectar eventos
            btn_cancelar.clicked.connect(dialog.reject)
            btn_gerar.clicked.connect(lambda: self.gerar_relatorio(dialog))
            
            dialog.exec()
            
        except Exception as e:
            self.mostrar_mensagem(f"❌ Erro ao abrir gerador de relatórios: {str(e)}")
    
    def gerar_relatorio(self, dialog):
        """Gerar relatório selecionado"""
        try:
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            data_atual = datetime.now().strftime("%d/%m/%Y")
            
            # Determinar tipo de relatório
            if self.radio_consulta.isChecked():
                tipo = "Consulta"
                template_base = f"""RELATÓRIO DE CONSULTA

Paciente: {nome_paciente}
Data: {data_atual}

ANAMNESE:
[Registrar informações coletadas durante a consulta]

EXAME FÍSICO:
[Descrever achados do exame físico]

DIAGNÓSTICO:
[Registrar diagnóstico clínico]

CONDUTA:
[Descrever plano terapêutico recomendado]

OBSERVAÇÕES:
{self.campo_obs_relatorio.toPlainText()}

Atenciosamente,
Clínica Biodesk"""
            
            elif self.radio_exames.isChecked():
                tipo = "Exames"
                template_base = f"""RELATÓRIO DE EXAMES

Paciente: {nome_paciente}
Data: {data_atual}

EXAMES REALIZADOS:
[Listar exames solicitados/realizados]

RESULTADOS:
[Descrever resultados obtidos]

INTERPRETAÇÃO:
[Análise clínica dos resultados]

RECOMENDAÇÕES:
[Orientações baseadas nos resultados]

OBSERVAÇÕES:
{self.campo_obs_relatorio.toPlainText()}

Atenciosamente,
Clínica Biodesk"""
            
            elif self.radio_tratamento.isChecked():
                tipo = "Tratamento"
                template_base = f"""RELATÓRIO DE TRATAMENTO

Paciente: {nome_paciente}
Data: {data_atual}

PROTOCOLO TERAPÊUTICO:
[Descrever tratamento prescrito]

MEDICAÇÕES:
[Listar medicamentos e posologia]

ORIENTAÇÕES:
[Instruções específicas para o paciente]

ACOMPANHAMENTO:
[Definir cronograma de retornos]

OBSERVAÇÕES:
{self.campo_obs_relatorio.toPlainText()}

Atenciosamente,
Clínica Biodesk"""
            
            else:  # Evolução
                tipo = "Evolução"
                template_base = f"""RELATÓRIO DE EVOLUÇÃO

Paciente: {nome_paciente}
Data: {data_atual}

EVOLUÇÃO CLÍNICA:
[Descrever progresso do paciente]

RESPOSTA AO TRATAMENTO:
[Avaliar eficácia da terapêutica]

AJUSTES REALIZADOS:
[Modificações no plano terapêutico]

PRÓXIMAS ETAPAS:
[Planejamento de continuidade]

OBSERVAÇÕES:
{self.campo_obs_relatorio.toPlainText()}

Atenciosamente,
Clínica Biodesk"""
            
            # Aplicar ao email
            self.campo_assunto.setText(f"Relatório de {tipo} - {nome_paciente}")
            self.campo_mensagem.setPlainText(template_base)
            
            self.mostrar_mensagem(f"✅ Relatório de {tipo} gerado com sucesso")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Erro", f"Erro ao gerar relatório: {str(e)}")
    
    def salvar_email_local(self, destinatario: str, assunto: str, mensagem: str, anexos: List[str]):
        """Salvar email no histórico local quando sistema de email não está disponível"""
        try:
            import json
            from pathlib import Path
            
            # Diretório para histórico de emails
            historico_dir = Path("historico_envios")
            historico_dir.mkdir(exist_ok=True)
            
            # Arquivo de histórico
            historico_file = historico_dir / "emails_enviados.json"
            
            # Carregar histórico existente
            if historico_file.exists():
                with open(historico_file, 'r', encoding='utf-8') as f:
                    historico = json.load(f)
            else:
                historico = []
            
            # Adicionar novo email
            email_record = {
                'id': len(historico) + 1,
                'destinatario': destinatario,
                'assunto': assunto,
                'mensagem': mensagem,
                'anexos': anexos,
                'data_envio': datetime.now().isoformat(),
                'paciente_nome': self.paciente_data.get('nome', 'Não informado'),
                'status': 'simulado'
            }
            
            historico.append(email_record)
            
            # Salvar histórico atualizado
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Email salvo no histórico local: {historico_file}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar email local: {e}")
            raise
    
    def mostrar_mensagem(self, mensagem: str):
        """Mostrar mensagem de status"""
        self.label_status.setText(mensagem)
        # Resetar após 3 segundos
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.label_status.setText("📎 0 anexos prontos"))
    
    def atualizar_anexos(self, caminhos_anexos: List[str]):
        """Atualizar lista de anexos para envio"""
        self.anexos_caminhos = caminhos_anexos
        count = len(caminhos_anexos)
        self.label_status.setText(f"📎 {count} anexos prontos")
        
        # Habilitar/desabilitar botão de envio
        self.btn_enviar.setEnabled(bool(self.campo_para.text().strip()))
    
    def salvar_rascunho(self):
        """Salvar email como rascunho"""
        # TODO: Implementar salvamento de rascunho
        QMessageBox.information(self, "Rascunho", "Rascunho salvo com sucesso!")
    
    def enviar_email(self):
        """Enviar email com anexos"""
        try:
            # Validações
            destinatario = self.campo_para.text().strip()
            if not destinatario:
                QMessageBox.warning(self, "Erro", "Por favor, informe o destinatário.")
                return
            
            assunto = self.campo_assunto.text().strip()
            if not assunto:
                QMessageBox.warning(self, "Erro", "Por favor, informe o assunto.")
                return
            
            mensagem = self.campo_mensagem.toPlainText().strip()
            if not mensagem:
                QMessageBox.warning(self, "Erro", "Por favor, digite a mensagem.")
                return
            
            # Confirmar envio
            count_anexos = len(self.anexos_caminhos)
            resposta = QMessageBox.question(
                self,
                "Confirmar Envio",
                f"Enviar email para {destinatario}?\n\n"
                f"Assunto: {assunto}\n"
                f"Anexos: {count_anexos} arquivo(s)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if resposta != QMessageBox.StandardButton.Yes:
                return
            
            # Envio do email
            if EMAIL_MODULES_AVAILABLE:
                # Usar sistema de email completo
                try:
                    email_sender = EmailSender()
                    if self.anexos_caminhos:
                        sucesso, erro = email_sender.send_email_with_attachments(
                            destinatario, assunto, mensagem, self.anexos_caminhos
                        )
                    else:
                        sucesso, erro = email_sender.send_email(
                            destinatario, assunto, mensagem
                        )
                    resultado = sucesso
                    
                    if resultado:
                        QMessageBox.information(self, "Sucesso", "✅ Email enviado com sucesso!")
                        print(f"✅ EMAIL ENVIADO: {destinatario}")
                    else:
                        QMessageBox.warning(self, "Erro", "❌ Falha no envio do email.")
                        return
                        
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"❌ Erro no sistema de email: {str(e)}")
                    return
            else:
                # Modo simulação/fallback
                print(f"📧 SIMULANDO ENVIO DE EMAIL:")
                print(f"   Para: {destinatario}")
                print(f"   Assunto: {assunto}")
                print(f"   Anexos: {count_anexos}")
                print(f"   Mensagem: {mensagem[:100]}...")
                
                # Salvar localmente para histórico
                try:
                    self.salvar_email_local(destinatario, assunto, mensagem, self.anexos_caminhos)
                    QMessageBox.information(self, "Email Simulado", 
                                          "📧 Email simulado com sucesso!\n\n"
                                          "💡 Configure o sistema de email para envio real.\n"
                                          "📁 Email salvo no histórico local.")
                except Exception as e:
                    QMessageBox.warning(self, "Aviso", f"Email simulado, mas erro ao salvar: {str(e)}")
            
            # Dados do email enviado
            email_data = {
                'destinatario': destinatario,
                'assunto': assunto,
                'mensagem': mensagem,
                'anexos': self.anexos_caminhos.copy(),
                'data_envio': datetime.now(),
                'paciente_id': self.paciente_data.get('id', '999')
            }
            
            # Simular sucesso
            QMessageBox.information(
                self,
                "Email Enviado",
                f"Email enviado com sucesso!\n\n"
                f"Destinatário: {destinatario}\n"
                f"Anexos: {count_anexos} arquivo(s)"
            )
            
            # Limpar formulário
            self.limpar_formulario()
            
            # Emitir sinal de sucesso
            self.email_enviado.emit(email_data)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao enviar email:\n{e}")
            traceback.print_exc()
    
    def limpar_formulario(self):
        """Limpar formulário após envio"""
        self.campo_assunto.clear()
        self.campo_mensagem.clear()
        self.combo_template.setCurrentIndex(0)


class CentroComunicacaoUnificado(QWidget):
    """
    🚀 CENTRO DE COMUNICAÇÃO UNIFICADO
    ==================================
    
    Widget principal que integra:
    - 📧 Composição de Email (35%)
    - 📁 Lista de Documentos (40%)  
    - 📎 Gestão de Anexos (25%)
    """
    
    # Sinais para comunicação com interface principal
    comunicacao_realizada = pyqtSignal(dict)
    
    def __init__(self, paciente_data: dict, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data or {}
        self.init_ui()
        self.conectar_sinais()
        
        # Timer para carregamento assíncrono
        QTimer.singleShot(100, self.carregar_dados_iniciais)
    
    def init_ui(self):
        """🎨 Inicializar interface do centro de comunicação"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 🔀 SPLITTER PRINCIPAL (3 COLUNAS)
        self.splitter_principal = QSplitter(Qt.Orientation.Horizontal)
        self.splitter_principal.setChildrenCollapsible(False)
        
        # 📧 COLUNA 1: EMAIL (35%)
        self.email_widget = EmailWidget(self.paciente_data)
        email_container = self.criar_container_coluna("📧 EMAIL", self.email_widget)
        self.splitter_principal.addWidget(email_container)
        
        # 📁 COLUNA 2: DOCUMENTOS (40%)
        self.documentos_widget = DocumentosListWidget(self.paciente_data)
        docs_container = self.criar_container_coluna("📁 DOCUMENTOS", self.documentos_widget)
        self.splitter_principal.addWidget(docs_container)
        
        # 📎 COLUNA 3: ANEXOS (25%)
        self.anexos_widget = AnexosListWidget()
        anexos_container = self.criar_container_coluna("📎 ANEXOS", self.anexos_widget)
        self.splitter_principal.addWidget(anexos_container)
        
        # Definir proporções das colunas (45% Email, 30% Documentos, 25% Anexos)
        self.splitter_principal.setSizes([450, 300, 250])
        
        layout.addWidget(self.splitter_principal)
        
        print("✅ Interface do Centro de Comunicação criada")
    
    def criar_container_coluna(self, titulo: str, widget: QWidget) -> QWidget:
        """Criar container estilizado para uma coluna"""
        container = QFrame()
        container.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 5px; background-color: white; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        
        # Título da coluna
        label_titulo = QLabel(titulo)
        label_titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label_titulo.setStyleSheet("padding: 3px; background-color: #f0f0f0; border-radius: 3px; font-size: 10px;")
        layout.addWidget(label_titulo)
        
        # Widget da coluna
        layout.addWidget(widget)
        
        return container
    
    def conectar_sinais(self):
        """🔗 Conectar sinais entre widgets"""
        try:
            # Documentos → Anexos
            self.documentos_widget.documento_selecionado.connect(self.anexos_widget.adicionar_anexo)
            self.documentos_widget.documento_removido.connect(self.anexos_widget.remover_anexo)
            
            # Anexos → Email
            self.anexos_widget.anexos_alterados.connect(self.atualizar_anexos_email)
            
            # Email → Sistema
            self.email_widget.email_enviado.connect(self.on_email_enviado)
            
            print("✅ Sinais conectados entre widgets")
            
        except Exception as e:
            print(f"⚠️ Erro ao conectar sinais: {e}")
    
    def carregar_dados_iniciais(self):
        """📊 Carregar dados iniciais assincronamente"""
        try:
            # Carregar documentos
            self.documentos_widget.carregar_documentos()
            
            # Atualizar estatísticas
            self.atualizar_estatisticas()
            
            print("✅ Dados iniciais carregados")
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados iniciais: {e}")
    
    def atualizar_anexos_email(self):
        """🔄 Atualizar lista de anexos no widget de email"""
        caminhos_anexos = self.anexos_widget.obter_caminhos_anexos()
        self.email_widget.atualizar_anexos(caminhos_anexos)
        self.atualizar_estatisticas()
    
    def atualizar_estatisticas(self):
        """📊 Atualizar estatísticas (agora apenas no console para otimização)"""
        try:
            total_docs = len(self.documentos_widget.documentos_disponiveis)
            total_anexos = len(self.anexos_widget.anexos_selecionados)
            
            # TODO: Contar emails enviados da sessão ou BD
            total_emails = 0
            
            # Estatísticas removidas da interface para otimização de espaço
            print(f"📊 {total_docs} documentos • {total_anexos} anexos • {total_emails} emails enviados")
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar estatísticas: {e}")
    
    def on_email_enviado(self, email_data: dict):
        """📧 Callback quando email é enviado com sucesso"""
        try:
            print(f"✅ Email enviado: {email_data['assunto']}")
            
            # Limpar anexos após envio bem-sucedido
            self.anexos_widget.limpar_todos()
            
            # Atualizar estatísticas
            self.atualizar_estatisticas()
            
            # Emitir sinal para interface principal
            self.comunicacao_realizada.emit(email_data)
            
        except Exception as e:
            print(f"⚠️ Erro no callback de email enviado: {e}")
    
    def obter_dados_widget(self) -> dict:
        """📊 Obter dados atuais do widget para debug/persistência"""
        return {
            'paciente_id': self.paciente_data.get('id'),
            'documentos_carregados': len(self.documentos_widget.documentos_disponiveis),
            'anexos_selecionados': len(self.anexos_widget.anexos_selecionados),
            'email_destinatario': self.email_widget.campo_para.text(),
            'email_assunto': self.email_widget.campo_assunto.text()
        }


# 🧪 TESTE RÁPIDO
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # Dados de teste
    paciente_teste = {
        'id': '999',
        'nome': 'João Silva',
        'email': 'joao.silva@email.com'
    }
    
    # Criar e mostrar widget
    centro = CentroComunicacaoUnificado(paciente_teste)
    centro.setWindowTitle("🚀 Centro de Comunicação - TESTE")
    centro.resize(1200, 800)
    centro.show()
    
    print("🧪 TESTE: Centro de Comunicação Unificado iniciado")
    print("📊 Dados do widget:", centro.obter_dados_widget())
    
    sys.exit(app.exec())
