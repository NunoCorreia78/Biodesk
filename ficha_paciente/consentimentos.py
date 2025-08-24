"""
🩺 MÓDULO DE CONSENTIMENTOS - Biodesk
======================================

Widget especializado para gestão de consentimentos médicos com interface intuitiva,
sistema de assinaturas digitais e geração automática de PDFs.

Funcionalidades:
- Interface de seleção por tipos de consentimento
- Editor de texto com templates pré-definidos
- Sistema de assinaturas paciente/terapeuta
- Geração automática de PDFs
- Integração com sistema de documentos

Autor: Sistema Biodesk
Versão: 2.0 (Modular)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QLabel, QTextEdit, QPushButton, QFrame, QScrollArea,
                           QLineEdit, QComboBox, QSpinBox, QCheckBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPainter, QPen, QColor

from services.styles import style_button, lighten_color
from biodesk_dialogs import mostrar_sucesso, mostrar_erro, mostrar_aviso

class ConsentimentosWidget(QWidget):
    """Widget especializado para gestão de consentimentos médicos"""
    
    # Sinais para comunicação com o módulo principal
    consentimento_guardado = pyqtSignal(str, str)  # tipo, caminho_pdf
    consentimento_assinado = pyqtSignal(str, str)  # tipo, tipo_assinatura
    template_carregado = pyqtSignal(str)  # tipo
    
    def __init__(self, paciente_data=None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.parent_window = parent
        self.tipo_selecionado = None
        
        # Dicionários para componentes
        self.botoes_consentimento = {}
        self.labels_status = {}
        
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface do widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ====== LAYOUT HORIZONTAL PRINCIPAL ======
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)
        
        # ====== 1. ESQUERDA: PAINEL DE STATUS COMPACTO ======
        status_frame = QFrame()
        status_frame.setFixedWidth(300)
        status_frame.setMinimumHeight(400)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(12)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Título da seção
        status_titulo = QLabel("📋 Tipos de Consentimentos")
        status_titulo.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600; 
            color: #2c3e50; 
            margin-bottom: 10px;
            padding: 15px;
            background-color: #e9ecef;
            border-radius: 8px;
        """)
        status_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(status_titulo)
        
        # Scroll area para os consentimentos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 8, 8, 8)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Tipos de consentimento com cores pastéis elegantes
        tipos_consentimento = [
            ("🌿 Naturopatia", "naturopatia", "#81c784"),
            ("👁️ Iridologia", "iridologia", "#4fc3f7"),
            ("🦴 Osteopatia", "osteopatia", "#ffb74d"),
            ("⚡ Medicina Quântica", "quantica", "#ba68c8"),
            ("💉 Mesoterapia", "mesoterapia", "#f06292"),
            ("🛡️ RGPD", "rgpd", "#90a4ae")
        ]
        
        for nome, tipo, cor in tipos_consentimento:
            btn = QPushButton(nome)
            btn.setCheckable(True)
            btn.setFixedSize(220, 45)
            
            btn.clicked.connect(lambda checked, t=tipo: self.selecionar_tipo_consentimento(t))
            self.botoes_consentimento[tipo] = btn
            scroll_layout.addWidget(btn)
        
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
        header_centro.setFixedHeight(85)
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
        
        # Mensagem inicial
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
        
        # Editor de texto principal
        self.editor_consentimento = QTextEdit()
        self.editor_consentimento.setMinimumHeight(300)
        self.editor_consentimento.setMaximumHeight(400)
        self.editor_consentimento.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
        """)
        self.editor_consentimento.setPlaceholderText("Selecione um tipo de consentimento para editar o texto...")
        self.editor_consentimento.setVisible(False)
        centro_layout.addWidget(self.editor_consentimento)
        
        # ====== BOTÕES DE ASSINATURA CENTRADOS E COMPACTOS ======
        assinaturas_layout = QVBoxLayout()
        assinaturas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        assinaturas_layout.setSpacing(10)   # Espaçamento menor
        
        # Layout horizontal para os dois botões
        botoes_assinatura_layout = QHBoxLayout()
        botoes_assinatura_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        botoes_assinatura_layout.setSpacing(20)  # Espaço entre botões
        
        # Botão Paciente - mais compacto
        self.assinatura_paciente = QPushButton("📝 Paciente")
        self.assinatura_paciente.setFixedSize(120, 40)  # Reduzido de 140x45
        style_button(self.assinatura_paciente, "#2196F3")
        self.assinatura_paciente.clicked.connect(self.abrir_assinatura_paciente)
        botoes_assinatura_layout.addWidget(self.assinatura_paciente)
        
        # Botão Terapeuta - mais compacto
        self.assinatura_terapeuta = QPushButton("👨‍⚕️ Terapeuta")
        self.assinatura_terapeuta.setFixedSize(120, 40)  # Reduzido de 140x45
        style_button(self.assinatura_terapeuta, "#4CAF50")
        self.assinatura_terapeuta.clicked.connect(self.abrir_assinatura_terapeuta)
        botoes_assinatura_layout.addWidget(self.assinatura_terapeuta)
        
        assinaturas_layout.addLayout(botoes_assinatura_layout)
        centro_layout.addLayout(assinaturas_layout)
        main_horizontal_layout.addWidget(centro_frame, 1)
        
        # ====== 3. DIREITA: BOTÕES DE AÇÃO ======
        acoes_layout = QVBoxLayout()
        acoes_layout.setContentsMargins(15, 10, 15, 10)
        acoes_layout.setSpacing(8)
        acoes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Botão Guardar
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedSize(160, 30)
        btn_guardar.setToolTip("Guardar Consentimento e Adicionar aos Documentos")
        style_button(btn_guardar, "#28a745")
        btn_guardar.clicked.connect(self.guardar_consentimento_completo)
        acoes_layout.addWidget(btn_guardar)
        
        acoes_layout.addSpacing(15)
        
        # Botão Limpar
        btn_limpar = QPushButton("🗑️ Limpar")
        btn_limpar.setFixedSize(160, 30)
        btn_limpar.setToolTip("Limpar Consentimento")
        style_button(btn_limpar, "#dc3545")
        btn_limpar.clicked.connect(self.limpar_consentimento)
        acoes_layout.addWidget(btn_limpar)
        
        # Botão Anular
        self.btn_anular = QPushButton("❌ Anular")
        self.btn_anular.setFixedSize(160, 30)
        self.btn_anular.setToolTip("Anular Consentimento")
        style_button(self.btn_anular, "#dc3545")
        self.btn_anular.clicked.connect(self.anular_consentimento)
        self.btn_anular.setVisible(False)
        acoes_layout.addWidget(self.btn_anular)
        
        acoes_layout.addStretch()
        main_horizontal_layout.addLayout(acoes_layout)
        main_horizontal_layout.addSpacing(20)
        
        layout.addLayout(main_horizontal_layout, 1)
        
        # Carregar dados iniciais
        self.carregar_status_consentimentos()
        self.atualizar_info_paciente_consentimento()
    
    def data_atual(self):
        """Retorna data atual formatada"""
        return QDate.currentDate().toString('dd/MM/yyyy')
    
    def selecionar_tipo_consentimento(self, tipo):
        """Seleciona um tipo de consentimento e carrega o template"""
        self.tipo_selecionado = tipo
        
        # Desmarcar outros botões
        for t, btn in self.botoes_consentimento.items():
            btn.setChecked(t == tipo)
        
        # Atualizar interface
        tipos_nomes = {
            'naturopatia': '🌿 Naturopatia',
            'osteopatia': '🦴 Osteopatia',
            'iridologia': '👁️ Iridologia',
            'quantica': '⚡ Medicina Quântica',
            'mesoterapia': '💉 Mesoterapia Homeopática',
            'rgpd': '🛡️ RGPD'
        }
        
        nome_tipo = tipos_nomes.get(tipo, tipo.title())
        self.label_tipo_atual.setText(f"✍️ {nome_tipo}")
        
        # Mostrar editor e ocultar mensagem inicial
        self.mensagem_inicial.setVisible(False)
        self.editor_consentimento.setVisible(True)
        
        # Carregar template do consentimento
        template = self.obter_template_consentimento(tipo)
        self.editor_consentimento.setHtml(template)
        
        # Emitir sinal
        self.template_carregado.emit(tipo)
        
        print(f"✅ Template de consentimento carregado: {nome_tipo}")
    
    def obter_template_consentimento(self, tipo):
        """Retorna o template HTML para o tipo de consentimento"""
        if not self.paciente_data:
            nome_paciente = "[NOME DO PACIENTE]"
            data_nascimento = "[DATA DE NASCIMENTO]"
        else:
            nome_paciente = self.paciente_data.get('nome', '[NOME DO PACIENTE]')
            data_nascimento = self.paciente_data.get('data_nascimento', '[DATA DE NASCIMENTO]')
        
        data_atual = self.data_atual()
        
        templates = {
            'naturopatia': f"""
            <h2 style="color: #27ae60; text-align: center;">🌿 CONSENTIMENTO INFORMADO - NATUROPATIA</h2>
            
            <p><strong>Paciente:</strong> {nome_paciente}</p>
            <p><strong>Data de Nascimento:</strong> {data_nascimento}</p>
            <p><strong>Data:</strong> {data_atual}</p>
            
            <h3>INFORMAÇÃO SOBRE O TRATAMENTO</h3>
            <p>A Naturopatia é uma medicina natural que utiliza métodos terapêuticos baseados em elementos naturais...</p>
            
            <h3>CONSENTIMENTO</h3>
            <p>Declaro que fui informado(a) sobre os procedimentos e dou o meu consentimento para o tratamento.</p>
            """,
            
            'iridologia': f"""
            <h2 style="color: #3498db; text-align: center;">👁️ CONSENTIMENTO INFORMADO - IRIDOLOGIA</h2>
            
            <p><strong>Paciente:</strong> {nome_paciente}</p>
            <p><strong>Data de Nascimento:</strong> {data_nascimento}</p>
            <p><strong>Data:</strong> {data_atual}</p>
            
            <h3>INFORMAÇÃO SOBRE A ANÁLISE</h3>
            <p>A Iridologia é um método de análise que estuda a íris do olho para avaliar o estado de saúde...</p>
            
            <h3>CONSENTIMENTO</h3>
            <p>Autorizo a realização da análise iridológica e fotografia dos olhos para fins terapêuticos.</p>
            """,
            
            'quantica': f"""
            <h2 style="color: #9b59b6; text-align: center;">⚡ CONSENTIMENTO INFORMADO - MEDICINA QUÂNTICA</h2>
            
            <p><strong>Paciente:</strong> {nome_paciente}</p>
            <p><strong>Data de Nascimento:</strong> {data_nascimento}</p>
            <p><strong>Data:</strong> {data_atual}</p>
            
            <h3>INFORMAÇÃO SOBRE O TRATAMENTO</h3>
            <p>A Medicina Quântica utiliza frequências energéticas para promover o equilíbrio do organismo...</p>
            
            <h3>CONSENTIMENTO</h3>
            <p>Compreendo os procedimentos e autorizo o tratamento com medicina quântica.</p>
            """,
            
            'rgpd': f"""
            <h2 style="color: #95a5a6; text-align: center;">🛡️ CONSENTIMENTO RGPD - PROTEÇÃO DE DADOS</h2>
            
            <p><strong>Paciente:</strong> {nome_paciente}</p>
            <p><strong>Data de Nascimento:</strong> {data_nascimento}</p>
            <p><strong>Data:</strong> {data_atual}</p>
            
            <h3>PROTEÇÃO DE DADOS PESSOAIS</h3>
            <p>Autorizo o tratamento dos meus dados pessoais para fins terapêuticos, conforme o RGPD...</p>
            
            <h3>CONSENTIMENTO</h3>
            <p>Dou o meu consentimento expresso para o tratamento dos dados pessoais.</p>
            """
        }
        
        return templates.get(tipo, f"""
        <h2>Consentimento - {tipo.title()}</h2>
        <p><strong>Paciente:</strong> {nome_paciente}</p>
        <p><strong>Data:</strong> {data_atual}</p>
        <p>Template para {tipo} em desenvolvimento...</p>
        """)
    
    def carregar_status_consentimentos(self):
        """Carrega e atualiza o status dos consentimentos"""
        # Implementar lógica de verificação de status
        print("📋 Status dos consentimentos carregado")
    
    def atualizar_info_paciente_consentimento(self):
        """Atualiza informações do paciente no consentimento"""
        if self.paciente_data:
            nome = self.paciente_data.get('nome', 'Paciente')
            print(f"👤 Dados do paciente definidos no módulo Consentimentos: {nome}")
    
    def abrir_assinatura_paciente(self):
        """Abre canvas de assinatura para o paciente"""
        if not self.tipo_selecionado:
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro!")
            return
        
        print(f"📝 Abrindo assinatura do paciente para: {self.tipo_selecionado}")
        self.consentimento_assinado.emit(self.tipo_selecionado, "paciente")
    
    def abrir_assinatura_terapeuta(self):
        """Abre canvas de assinatura para o terapeuta"""
        if not self.tipo_selecionado:
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro!")
            return
        
        print(f"👨‍⚕️ Abrindo assinatura do terapeuta para: {self.tipo_selecionado}")
        self.consentimento_assinado.emit(self.tipo_selecionado, "terapeuta")
    
    def guardar_consentimento_completo(self):
        """Guarda o consentimento completo com PDF"""
        if not self.tipo_selecionado:
            mostrar_aviso(self, "Aviso", "Selecione um tipo de consentimento primeiro!")
            return
        
        # Obter conteúdo do editor
        conteudo = self.editor_consentimento.toHtml()
        
        # Gerar PDF (implementar lógica)
        caminho_pdf = self.gerar_pdf_consentimento(self.tipo_selecionado, conteudo)
        
        if caminho_pdf:
            mostrar_sucesso(self, "Sucesso", f"✅ Consentimento guardado com sucesso!\n\nPDF: {caminho_pdf}")
            self.consentimento_guardado.emit(self.tipo_selecionado, caminho_pdf)
        else:
            mostrar_erro(self, "Erro", "❌ Erro ao guardar consentimento!")
    
    def gerar_pdf_consentimento(self, tipo, conteudo):
        """Gera PDF do consentimento"""
        try:
            import os
            from datetime import datetime
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument
            
            if not self.paciente_data:
                return None
            
            # Criar diretório
            paciente_id = self.paciente_data.get('id')
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente}/Consentimentos"
            os.makedirs(pasta_paciente, exist_ok=True)
            
            # Nome do arquivo
            data_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"consentimento_{tipo}_{data_str}.pdf"
            caminho_pdf = os.path.join(pasta_paciente, nome_arquivo)
            
            # Gerar PDF
            document = QTextDocument()
            document.setHtml(conteudo)
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            
            document.print(printer)
            
            print(f"✅ PDF do consentimento gerado: {caminho_pdf}")
            return caminho_pdf
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            return None
    
    def limpar_consentimento(self):
        """Limpa o consentimento atual"""
        if self.tipo_selecionado:
            template = self.obter_template_consentimento(self.tipo_selecionado)
            self.editor_consentimento.setHtml(template)
            print(f"🗑️ Consentimento limpo: {self.tipo_selecionado}")
    
    def anular_consentimento(self):
        """Anula o consentimento atual"""
        if self.tipo_selecionado:
            print(f"❌ Consentimento anulado: {self.tipo_selecionado}")
            # Implementar lógica de anulação
    
    def definir_paciente_data(self, paciente_data):
        """Define os dados do paciente"""
        self.paciente_data = paciente_data
        self.atualizar_info_paciente_consentimento()
        
        # Recarregar template se um tipo estiver selecionado
        if self.tipo_selecionado:
            template = self.obter_template_consentimento(self.tipo_selecionado)
            self.editor_consentimento.setHtml(template)
