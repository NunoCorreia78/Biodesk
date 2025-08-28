from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import json
import os
import base64
from datetime import datetime
from biodesk_dialogs import BiodeskMessageBox
from db_manager import DBManager
import sqlite3

# 🎨 SISTEMA DE ESTILOS CENTRALIZADO
try:
    from biodesk_styles import BiodeskStyles, ButtonType
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False

class PrescricaoMedicaWidget(QWidget):
    """
    Widget para criação e edição de prescrições médicas
    Substitui o sistema de suplementos por um editor HTML completo
    Inclui assinatura digital, integração com BD e sistema de email
    """
    
    def __init__(self, parent=None, paciente_data=None):
        super().__init__(parent)
        self.parent = parent
        self.paciente_data = paciente_data or {}
        self.prescricao_data = {}
        
        self.init_ui()
        self.carregar_template_prescricao()
        self.configurar_assinatura_digital()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título e botões
        titulo_layout = QHBoxLayout()
        
        titulo = QLabel("🩺 Prescrição Médica")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2d4a3e;
                padding: 10px 0;
            }
        """)
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()
        
        # Botões de ação
        if STYLES_AVAILABLE:
            btn_salvar = BiodeskStyles.create_button("💾 Salvar", ButtonType.SAVE)
            btn_pdf = BiodeskStyles.create_button("📄 Salvar PDF", ButtonType.DEFAULT)
            btn_imprimir = BiodeskStyles.create_button("🖨️ Imprimir", ButtonType.DEFAULT)
            btn_limpar = BiodeskStyles.create_button("🗑️ Limpar", ButtonType.DELETE)
        else:
            btn_salvar = QPushButton("💾 Salvar")
            btn_pdf = QPushButton("📄 Salvar PDF")
            btn_imprimir = QPushButton("🖨️ Imprimir")
            btn_limpar = QPushButton("🗑️ Limpar")
        
        btn_salvar.clicked.connect(self.salvar_prescricao)
        btn_pdf.clicked.connect(self.salvar_como_pdf)
        btn_imprimir.clicked.connect(self.imprimir_prescricao)
        btn_limpar.clicked.connect(self.limpar_prescricao)
        
        titulo_layout.addWidget(btn_salvar)
        titulo_layout.addWidget(btn_pdf)
        titulo_layout.addWidget(btn_imprimir)
        titulo_layout.addWidget(btn_limpar)
        
        layout.addLayout(titulo_layout)
        
        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setFrameShadow(QFrame.Shadow.Sunken)
        separador.setStyleSheet("QFrame { color: #2d4a3e; }")
        layout.addWidget(separador)
        
        # WebEngine para o editor HTML
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(500)  # Reduzido de 800 para 500
        layout.addWidget(self.web_view)
    
    def carregar_template_prescricao(self):
        """Carrega o template HTML da prescrição"""
        template_path = os.path.join("templates", "prescricao_medica.html")
        
        if not os.path.exists(template_path):
            self.mostrar_erro("Template de prescrição não encontrado!")
            return
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Debug: Imprimir dados do paciente para verificação
            dados_paciente = self.paciente_data
            print(f"DEBUG: Dados do paciente: {dados_paciente}")  # Debug
            
            # Carregar no WebEngine (template agora é autocontido)
            self.web_view.setHtml(html_content)
            
            # Após carregar, preencher dados via JavaScript (aumentar delay)
            QTimer.singleShot(1500, self.preencher_dados_paciente)  # Aumentado de 1000 para 1500ms
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao carregar template: {str(e)}")
    
    def buscar_nome_paciente(self, paciente_id):
        """Busca nome do paciente na base de dados"""
        try:
            db_manager = DBManager.get_instance()
            conn = db_manager._connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT nome FROM pacientes WHERE id = ?", (paciente_id,))
            resultado = cursor.fetchone()
            conn.close()
            
            return resultado[0] if resultado else f"Paciente ID {paciente_id}"
        except Exception as e:
            print(f"Erro ao buscar nome do paciente: {e}")
            return f"Paciente ID {paciente_id}"
    
    def preencher_dados_paciente(self):
        """Preenche dados do paciente via JavaScript após carregamento"""
        # Tentar múltiplas chaves possíveis para o nome
        nome_paciente = (
            self.paciente_data.get('nome') or 
            self.paciente_data.get('Nome') or 
            self.paciente_data.get('NOME') or 
            self.paciente_data.get('name') or 
            ''
        )
        
        # Se não tem nome nos dados, tentar buscar na BD
        if not nome_paciente and 'id' in self.paciente_data:
            nome_paciente = self.buscar_nome_paciente(self.paciente_data['id'])
        
        # Escapar aspas simples e outras aspas no nome para evitar problemas no JavaScript
        nome_escapado = nome_paciente.replace("'", "\\'").replace('"', '\\"') if nome_paciente else ''
        
        # Carregar assinatura real do arquivo
        assinatura_base64 = self.carregar_assinatura_real()
        
        print(f"DEBUG: Dados completos do paciente: {self.paciente_data}")  # Debug completo
        print(f"DEBUG: Preenchendo nome do paciente: '{nome_escapado}'")  # Debug
        print(f"DEBUG: Assinatura carregada: {'Sim' if assinatura_base64 else 'Não'}")  # Debug
        
        script = f"""
        (function() {{
            console.log('Iniciando preenchimento dos dados do paciente...');
            
            // Preencher campo do nome do paciente
            var nomeInput = document.getElementById('nome');
            if (nomeInput) {{
                if ('{nome_escapado}') {{
                    nomeInput.value = '{nome_escapado}';
                    console.log('Nome do paciente preenchido:', '{nome_escapado}');
                }} else {{
                    console.log('Nome do paciente está vazio');
                }}
            }} else {{
                console.log('Campo nome não encontrado no DOM');
            }}
            
            // Carregar assinatura real se disponível
            var signImg = document.getElementById('signImg');
            if (signImg && '{assinatura_base64}') {{
                signImg.src = '{assinatura_base64}';
                // Atualizar status se função disponível
                if (typeof window.updateSignatureStatus === 'function') {{
                    window.updateSignatureStatus('Assinatura digital carregada', true);
                }}
                console.log('Assinatura real carregada');
            }} else {{
                // Atualizar status para assinatura padrão
                if (typeof window.updateSignatureStatus === 'function') {{
                    window.updateSignatureStatus('Usando assinatura padrão', false);
                }}
                console.log('Usando assinatura padrão do template');
            }}
            
            // Também salvar no localStorage como faz o template
            if ('{nome_escapado}') {{
                try {{
                    localStorage.setItem('nomePaciente', '{nome_escapado}');
                    console.log('Nome salvo no localStorage');
                }} catch(e) {{
                    console.log('Erro ao salvar no localStorage:', e);
                }}
            }}
        }})();
        """
        
        self.web_view.page().runJavaScript(script)
    
    def carregar_assinatura_real(self):
        """Carrega a assinatura real do arquivo PNG e converte para Base64"""
        try:
            import base64
            assinatura_path = os.path.join("assets", "assinatura.png")
            
            if os.path.exists(assinatura_path):
                with open(assinatura_path, "rb") as img_file:
                    img_data = img_file.read()
                    base64_string = base64.b64encode(img_data).decode('utf-8')
                    return f"data:image/png;base64,{base64_string}"
            else:
                print(f"Arquivo de assinatura não encontrado: {assinatura_path}")
                return ""
                
        except Exception as e:
            print(f"Erro ao carregar assinatura: {e}")
            return ""
    
    def mostrar_erro(self, mensagem):
        """Mostra diálogo de erro"""
        BiodeskMessageBox.critical(self, "Erro", mensagem)
    
    def salvar_prescricao(self):
        """Salva a prescrição atual"""
        script = """
        (function(){
            if (typeof window.prescricaoExportar === 'function') {
                return window.prescricaoExportar();
            }
            return null;
        })();
        """
        
        self.web_view.page().runJavaScript(script, self.callback_salvar_dados)
    
    def callback_salvar_dados(self, dados):
        """Callback para processar dados exportados do JavaScript"""
        if not dados:
            self.mostrar_erro("Erro ao exportar dados da prescrição!")
            return
        
        try:
            # Criar diretório de prescrições se não existir
            prescricoes_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "prescricoes")
            os.makedirs(prescricoes_dir, exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prescricao_{timestamp}.json"
            filepath = os.path.join(prescricoes_dir, filename)
            
            # Adicionar metadados
            dados_completos = {
                'paciente_id': self.paciente_data['id'],
                'paciente_nome': self.paciente_data.get('nome', ''),
                'data_criacao': datetime.now().isoformat(),
                'dados_prescricao': dados
            }
            
            # Salvar arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2)
            
            BiodeskMessageBox.information(
                self,
                "Prescrição Salva",
                f"Prescrição salva com sucesso!\n\nArquivo: {filename}"
            )
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao salvar prescrição: {str(e)}")
    
    def imprimir_prescricao(self):
        """Imprime a prescrição atual"""
        try:
            # Criar um diálogo de impressão
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            print_dialog = QPrintDialog(printer, self)
            print_dialog.setWindowTitle("Imprimir Prescrição")
            
            if print_dialog.exec() == QDialog.DialogCode.Accepted:
                # Usar printToPdf do WebEngine (método correto)
                self.web_view.page().printToPdf(self.callback_impressao_pdf)
            
        except Exception as e:
            # Fallback para impressão via JavaScript
            print(f"Erro na impressão avançada: {e}")
            script = """
            window.print();
            """
            self.web_view.page().runJavaScript(script)
            
            BiodeskMessageBox.information(
                self,
                "Impressão",
                "Comando de impressão enviado.\n\nSe não abriu o diálogo de impressão, verifique as configurações do navegador."
            )
    
    def callback_impressao_pdf(self, pdf_data):
        """Callback após geração de PDF para impressão"""
        if pdf_data:
            BiodeskMessageBox.information(
                self,
                "Impressão",
                "Prescrição preparada para impressão!"
            )
        else:
            BiodeskMessageBox.critical(
                self,
                "Erro de Impressão", 
                "Erro ao preparar prescrição para impressão."
            )
    
    def limpar_prescricao(self):
        """Limpa o formulário de prescrição"""
        resposta = BiodeskMessageBox.question(
            self,
            "Confirmar Limpeza",
            "Tem certeza que deseja limpar toda a prescrição?\n\nEsta ação não pode ser desfeita."
        )
        
        if resposta:
            self.carregar_template_prescricao()
    
    # ========== MÉTODOS PARA ASSINATURA DIGITAL ==========
    
    def configurar_assinatura_digital(self):
        """Configura callbacks para assinatura digital"""
        # Timer para aguardar carregamento do WebEngine
        QTimer.singleShot(1000, self._configurar_callback_assinatura)
    
    def _configurar_callback_assinatura(self):
        """Configura o callback JavaScript para assinatura"""
        script = """
        window.assinaturaConfirmada = function(signatureData) {
            console.log('Assinatura confirmada:', signatureData ? 'dados recebidos' : 'sem dados');
            // Callback será processado pelo Python
        };
        """
        self.web_view.page().runJavaScript(script)
    
    def assinatura_confirmada(self, signature_data):
        """Callback chamado quando assinatura é confirmada"""
        try:
            # Salvar assinatura com dados da prescrição
            self.salvar_prescricao_com_assinatura(signature_data)
            
            # Registrar na base de dados de pacientes
            self.registrar_prescricao_bd(signature_data)
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao processar assinatura: {str(e)}")
    
    def salvar_prescricao_com_assinatura(self, signature_data):
        """Salva a prescrição incluindo dados da assinatura digital"""
        script = """
        (function(){
            if (typeof window.prescricaoExportar === 'function') {
                return window.prescricaoExportar();
            }
            return null;
        })();
        """
        
        self.web_view.page().runJavaScript(script, 
            lambda dados: self.callback_salvar_com_assinatura(dados, signature_data))
    
    def callback_salvar_com_assinatura(self, dados, signature_data):
        """Callback para salvar prescrição com assinatura"""
        if not dados:
            self.mostrar_erro("Erro ao exportar dados da prescrição!")
            return
        
        try:
            # Criar diretório de prescrições se não existir
            prescricoes_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "prescricoes")
            os.makedirs(prescricoes_dir, exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prescricao_assinada_{timestamp}.json"
            filepath = os.path.join(prescricoes_dir, filename)
            
            # Adicionar metadados e assinatura
            dados_completos = {
                'paciente_id': self.paciente_data['id'],
                'paciente_nome': self.paciente_data.get('nome', ''),
                'data_criacao': datetime.now().isoformat(),
                'assinatura_digital': signature_data,
                'assinatura_timestamp': datetime.now().isoformat(),
                'status': 'assinada',
                'dados_prescricao': dados
            }
            
            # Salvar arquivo JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2)
            
            # Salvar imagem da assinatura separadamente
            self.salvar_imagem_assinatura(signature_data, timestamp)
            
            BiodeskMessageBox.information(
                self,
                "Prescrição Assinada",
                f"Prescrição assinada digitalmente e salva com sucesso!\n\nArquivo: {filename}"
            )
            
            # Perguntar se quer enviar por email
            self.perguntar_envio_email(filepath)
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao salvar prescrição assinada: {str(e)}")
    
    def salvar_imagem_assinatura(self, signature_data, timestamp):
        """Salva a imagem da assinatura como arquivo PNG"""
        try:
            # Remover prefixo data:image/png;base64,
            if signature_data.startswith('data:image/png;base64,'):
                signature_data = signature_data[22:]
            
            # Decodificar base64
            image_data = base64.b64decode(signature_data)
            
            # Caminho para salvar imagem
            assinaturas_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "assinaturas")
            os.makedirs(assinaturas_dir, exist_ok=True)
            
            image_path = os.path.join(assinaturas_dir, f"assinatura_{timestamp}.png")
            
            # Salvar arquivo
            with open(image_path, 'wb') as f:
                f.write(image_data)
                
        except Exception as e:
            print(f"Erro ao salvar imagem da assinatura: {e}")
    
    # ========== INTEGRAÇÃO COM BASE DE DADOS DE PACIENTES ==========
    
    def registrar_prescricao_bd(self, signature_data):
        """Registra a prescrição na base de dados de pacientes"""
        try:
            db_manager = DBManager.get_instance()
            conn = db_manager._connect()
            
            cursor = conn.cursor()
            
            # Verificar se existe tabela de prescrições
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prescricoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER,
                    data_prescricao TEXT,
                    status TEXT DEFAULT 'assinada',
                    arquivo_json TEXT,
                    assinatura_timestamp TEXT,
                    observacoes TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
                )
            """)
            
            # Inserir registro da prescrição
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO prescricoes 
                (paciente_id, data_prescricao, status, assinatura_timestamp, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.paciente_data['id'],
                timestamp,
                'assinada',
                timestamp,
                f"Prescrição médica assinada digitalmente em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao registrar prescrição na BD: {e}")
    
    # ========== FUNCIONALIDADE DE EMAIL ==========
    
    def perguntar_envio_email(self, filepath):
        """Pergunta se o usuário quer enviar a prescrição por email"""
        resposta = BiodeskMessageBox.question(
            self,
            "Enviar por Email",
            "Deseja enviar esta prescrição por email para o paciente?"
        )
        
        if resposta:
            self.abrir_dialog_email(filepath)
    
    def abrir_dialog_email(self, filepath):
        """Abre diálogo para configurar envio de email"""
        try:
            # Tentar importar sistema de email
            from email_sender import EmailSender
            from email_templates_biodesk import EmailTemplates
            
            # Carregar dados da prescrição
            with open(filepath, 'r', encoding='utf-8') as f:
                dados_prescricao = json.load(f)
            
            # Criar diálogo de email
            dialog = QDialog(self)
            dialog.setWindowTitle("📧 Enviar Prescrição por Email")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Campo de email do paciente
            email_layout = QHBoxLayout()
            email_layout.addWidget(QLabel("Email do Paciente:"))
            
            email_field = QLineEdit()
            email_field.setPlaceholderText("email@exemplo.com")
            
            # Tentar pré-preencher com email do paciente se disponível
            if 'email' in self.paciente_data:
                email_field.setText(self.paciente_data['email'])
            
            email_layout.addWidget(email_field)
            layout.addLayout(email_layout)
            
            # Campo de mensagem
            layout.addWidget(QLabel("Mensagem:"))
            mensagem_field = QTextEdit()
            
            # Template padrão de mensagem
            template_mensagem = f"""Caro(a) {self.paciente_data.get('nome', 'Paciente')},

Segue em anexo a sua prescrição médica assinada digitalmente.

Por favor, siga rigorosamente as instruções descritas na prescrição.

Em caso de dúvidas, não hesite em contactar.

Cumprimentos,
Dr(a). [Seu Nome]"""
            
            mensagem_field.setPlainText(template_mensagem)
            layout.addWidget(mensagem_field)
            
            # Botões
            botoes_layout = QHBoxLayout()
            btn_enviar = QPushButton("📧 Enviar")
            btn_cancelar = QPushButton("❌ Cancelar")
            
            btn_enviar.clicked.connect(lambda: self.enviar_email_prescricao(
                email_field.text(),
                mensagem_field.toPlainText(),
                filepath,
                dialog
            ))
            btn_cancelar.clicked.connect(dialog.close)
            
            botoes_layout.addWidget(btn_enviar)
            botoes_layout.addWidget(btn_cancelar)
            layout.addLayout(botoes_layout)
            
            dialog.exec()
            
        except ImportError:
            BiodeskMessageBox.information(
                self,
                "Sistema de Email",
                "Sistema de email não configurado.\nPor favor, configure o módulo de email primeiro."
            )
        except Exception as e:
            self.mostrar_erro(f"Erro ao abrir diálogo de email: {str(e)}")
    
    def enviar_email_prescricao(self, email_destino, mensagem, filepath, dialog):
        """Envia a prescrição por email"""
        if not email_destino or '@' not in email_destino:
            BiodeskMessageBox.critical(
                self,
                "Email Inválido",
                "Por favor, insira um endereço de email válido."
            )
            return
        
        try:
            from email_sender import EmailSender
            
            # Salvar dados para usar no callback do PDF
            self.email_dados = {
                'destinatario': email_destino,
                'mensagem': mensagem,
                'dialog': dialog
            }
            
            # Gerar PDF da prescrição (será processado no callback)
            BiodeskMessageBox.information(
                self,
                "Gerando PDF",
                "Gerando PDF da prescrição para envio por email..."
            )
            
            self.gerar_pdf_para_email()
            
        except ImportError:
            BiodeskMessageBox.information(
                self,
                "Sistema de Email",
                "Sistema de email não configurado.\nPor favor, configure o módulo de email primeiro."
            )
        except Exception as e:
            self.mostrar_erro(f"Erro ao enviar email: {str(e)}")
    
    def gerar_pdf_para_email(self):
        """Gera PDF especificamente para envio por email"""
        try:
            # Criar diretório de PDFs se não existir
            pdf_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "pdfs")
            os.makedirs(pdf_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.pdf_path_email = os.path.join(pdf_dir, f"prescricao_email_{timestamp}.pdf")
            
            # Usar printToPdf do WebEngine para email
            self.web_view.page().printToPdf(self.callback_pdf_email)
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao gerar PDF para email: {str(e)}")
    
    def callback_pdf_email(self, pdf_data):
        """Callback após geração de PDF para email"""
        try:
            if pdf_data and hasattr(self, 'pdf_path_email'):
                # Salvar os dados do PDF no arquivo
                with open(self.pdf_path_email, 'wb') as f:
                    f.write(pdf_data)
                
                # Verificar se arquivo foi criado
                if os.path.exists(self.pdf_path_email):
                    # Enviar email com PDF anexo
                    self.processar_envio_email()
                else:
                    self.mostrar_erro("PDF não foi criado para envio por email.")
            else:
                self.mostrar_erro("Erro ao gerar PDF para email - dados vazios.")
                
        except Exception as e:
            self.mostrar_erro(f"Erro ao processar PDF para email: {str(e)}")
    
    def processar_envio_email(self):
        """Processa o envio do email com o PDF gerado"""
        try:
            from email_sender import EmailSender
            
            if not hasattr(self, 'email_dados'):
                self.mostrar_erro("Dados de email não encontrados.")
                return
            
            # Configurar email
            sender = EmailSender()
            assunto = f"Prescrição Médica - {self.paciente_data.get('nome', 'Paciente')}"
            
            # Enviar email com anexo
            sucesso = sender.enviar_email(
                destinatario=self.email_dados['destinatario'],
                assunto=assunto,
                corpo=self.email_dados['mensagem'],
                anexos=[self.pdf_path_email]
            )
            
            if sucesso:
                BiodeskMessageBox.information(
                    self,
                    "Email Enviado",
                    f"Prescrição enviada com sucesso para {self.email_dados['destinatario']}"
                )
                self.email_dados['dialog'].close()
            else:
                BiodeskMessageBox.critical(
                    self,
                    "Erro no Envio",
                    "Erro ao enviar email. Verifique as configurações."
                )
                
        except Exception as e:
            self.mostrar_erro(f"Erro ao processar envio de email: {str(e)}")
    
    def gerar_pdf_prescricao(self, filepath=None):
        """Gera PDF da prescrição para anexar ao email ou salvar na ficha"""
        try:
            # Criar diretório de PDFs se não existir
            pdf_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "pdfs")
            os.makedirs(pdf_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.pdf_path = os.path.join(pdf_dir, f"prescricao_{timestamp}.pdf")
            
            # Usar printToPdf do WebEngine (método correto)
            self.web_view.page().printToPdf(self.callback_pdf)
            
            return self.pdf_path
            
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            self.mostrar_erro(f"Erro ao gerar PDF: {str(e)}")
            return None
    
    def callback_pdf(self, pdf_data):
        """Callback após geração de PDF"""
        try:
            if pdf_data and hasattr(self, 'pdf_path'):
                # Salvar os dados do PDF no arquivo
                with open(self.pdf_path, 'wb') as f:
                    f.write(pdf_data)
                
                # Verificar se arquivo foi criado
                if os.path.exists(self.pdf_path):
                    BiodeskMessageBox.information(
                        self,
                        "PDF Gerado",
                        f"PDF salvo com sucesso!\n\nLocalização: {self.pdf_path}"
                    )
                    
                    # Registrar na ficha do paciente
                    self.registrar_pdf_na_ficha(self.pdf_path)
                else:
                    self.mostrar_erro("PDF não foi criado corretamente.")
            else:
                self.mostrar_erro("Erro ao gerar PDF - dados vazios.")
                
        except Exception as e:
            self.mostrar_erro(f"Erro ao salvar PDF: {str(e)}")
    
    def registrar_pdf_na_ficha(self, pdf_path):
        """Registra o PDF na ficha do paciente"""
        try:
            db_manager = DBManager.get_instance()
            conn = db_manager._connect()
            cursor = conn.cursor()
            
            # Criar tabela de documentos se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documentos_paciente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER,
                    tipo_documento TEXT,
                    caminho_arquivo TEXT,
                    data_criacao TEXT,
                    observacoes TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
                )
            """)
            
            # Inserir registro do PDF
            cursor.execute("""
                INSERT INTO documentos_paciente 
                (paciente_id, tipo_documento, caminho_arquivo, data_criacao, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.paciente_data['id'],
                'prescricao_pdf',
                pdf_path,
                datetime.now().isoformat(),
                f"PDF de prescrição médica gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ))
            
            conn.commit()
            conn.close()
            
            print(f"PDF registrado na ficha do paciente: {pdf_path}")
            
        except Exception as e:
            print(f"Erro ao registrar PDF na ficha: {e}")
    
    def salvar_como_pdf(self):
        """Salva a prescrição atual como PDF"""
        pdf_path = self.gerar_pdf_prescricao()
        if pdf_path:
            print(f"Processo de PDF iniciado: {pdf_path}")
    
    # ========== GESTÃO DE HISTÓRICO E TEMPLATES ==========
    
    def listar_prescricoes_paciente(self):
        """Lista todas as prescrições salvas do paciente atual"""
        if not self.paciente_data.get('id'):
            return []
        
        prescricoes_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "prescricoes")
        
        if not os.path.exists(prescricoes_dir):
            return []
        
        prescricoes = []
        for filename in os.listdir(prescricoes_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(prescricoes_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    
                    prescricoes.append({
                        'filename': filename,
                        'filepath': filepath,
                        'data_criacao': dados.get('data_criacao', ''),
                        'utente': dados.get('dados_prescricao', {}).get('utente', '')
                    })
                except:
                    continue
        
        # Ordenar por data de criação (mais recente primeiro)
        prescricoes.sort(key=lambda x: x['data_criacao'], reverse=True)
        return prescricoes
    
    def carregar_prescricao_salva(self, filepath):
        """Carrega uma prescrição previamente salva"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dados_completos = json.load(f)
            
            dados = dados_completos.get('dados_prescricao', {})
            
            # Carregar template primeiro
            self.carregar_template_prescricao()
            
            # Aguardar carregamento e então importar dados
            QTimer.singleShot(1000, lambda: self.importar_dados_prescricao(dados))
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao carregar prescrição: {str(e)}")
    
    def importar_dados_prescricao(self, dados):
        """Importa dados para o formulário de prescrição"""
        script = f"""
        (function(){{
            if (typeof window.prescricaoImportar === 'function') {{
                window.prescricaoImportar({json.dumps(dados)});
                return true;
            }} else {{
                return false;
            }}
        }})();
        """
        
        self.web_view.page().runJavaScript(script)
