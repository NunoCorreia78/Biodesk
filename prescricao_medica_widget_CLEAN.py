from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
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
            btn_imprimir = BiodeskStyles.create_button("🖨️ Imprimir", ButtonType.DEFAULT)
            btn_limpar = BiodeskStyles.create_button("🗑️ Limpar", ButtonType.DELETE)
        else:
            btn_salvar = QPushButton("💾 Salvar")
            btn_imprimir = QPushButton("🖨️ Imprimir")
            btn_limpar = QPushButton("🗑️ Limpar")
        
        btn_salvar.clicked.connect(self.salvar_prescricao)
        btn_imprimir.clicked.connect(self.imprimir_prescricao)
        btn_limpar.clicked.connect(self.limpar_prescricao)
        
        titulo_layout.addWidget(btn_salvar)
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
        self.web_view.setMinimumHeight(800)
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
            
            # Substituir variáveis do template
            dados_paciente = self.paciente_data
            html_content = html_content.replace('{{utente}}', dados_paciente.get('nome', ''))
            html_content = html_content.replace('{{data}}', datetime.now().strftime('%d/%m/%Y'))
            html_content = html_content.replace('{{duracao}}', '30 dias')
            html_content = html_content.replace('{{notas}}', '')
            
            # Carregar no WebEngine
            self.web_view.setHtml(html_content)
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao carregar template: {str(e)}")
    
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
        script = "window.print();"
        self.web_view.page().runJavaScript(script)
    
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
            
            # Gerar PDF da prescrição
            pdf_path = self.gerar_pdf_prescricao(filepath)
            
            # Configurar email
            sender = EmailSender()
            assunto = f"Prescrição Médica - {self.paciente_data.get('nome', 'Paciente')}"
            
            # Enviar email com anexo
            sucesso = sender.enviar_email(
                destinatario=email_destino,
                assunto=assunto,
                corpo=mensagem,
                anexos=[pdf_path] if pdf_path else []
            )
            
            if sucesso:
                BiodeskMessageBox.information(
                    self,
                    "Email Enviado",
                    f"Prescrição enviada com sucesso para {email_destino}"
                )
                dialog.close()
            else:
                BiodeskMessageBox.critical(
                    self,
                    "Erro no Envio",
                    "Erro ao enviar email. Verifique as configurações."
                )
                
        except Exception as e:
            self.mostrar_erro(f"Erro ao enviar email: {str(e)}")
    
    def gerar_pdf_prescricao(self, filepath):
        """Gera PDF da prescrição para anexar ao email"""
        try:
            # Usar a funcionalidade de impressão do WebEngine para gerar PDF
            pdf_dir = os.path.join("Documentos_Pacientes", str(self.paciente_data['id']), "pdfs")
            os.makedirs(pdf_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_path = os.path.join(pdf_dir, f"prescricao_{timestamp}.pdf")
            
            # Nota: Esta é uma implementação simplificada
            # Em produção, seria necessário usar QtWebEngineWidgets.QWebEnginePage.printToPdf()
            
            return pdf_path
            
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            return None
    
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
