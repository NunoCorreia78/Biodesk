
import sys
import os
import traceback
# Lazy import do cv2 para evitar janela que pisca
# import cv2
import time
import threading
import unicodedata
import json
import socket
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timedelta
from db_manager import DBManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
# Lazy import do editor_documentos para evitar inicialização prematura do QWebEngine
# from editor_documentos import EditorDocumentos
from services.styles import (
    estilizar_botao_iris, estilizar_botao_principal, estilizar_botao_secundario,
    estilizar_botao_perigo, estilizar_botao_sucesso, estilizar_botao_fusao,
    lighten_color, darken_color, style_button, style_combo, style_input
)
from modern_date_widget import ModernDateWidget
from biodesk_styled_dialogs import BiodeskStyledDialog, BiodeskMessageBox


def send_followup_job_static(paciente_id, tipo_followup, dias_apos, attempt=1, max_attempts=3):
    """
    Função independente para envio de follow-up que pode ser serializada pelo APScheduler.
    Esta função não depende de instâncias de classe e pode ser guardada na BD.
    """
    try:
        # Verificar conectividade
        def is_online(timeout=3):
            try:
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=timeout)
                return True
            except Exception:
                return False

        # Inicializar BD
        db = DBManager()
        paciente = db.obter_paciente(paciente_id)

        if not paciente:
            print(f"❌ Paciente {paciente_id} não encontrado — abortando envio")
            return

        to_email = paciente.get('email', '').strip()
        if not to_email:
            print(f"❌ Paciente {paciente_id} sem email — abortando envio")
            return

        # Checar ligação à Internet
        if not is_online():
            print(f"⚠️ Sem internet — tentativa {attempt}/{max_attempts}. Reagendando...")
            
            # Sistema de retry mais inteligente
            if attempt < max_attempts:
                # Usar delay mais curto nas primeiras tentativas, depois delay maior
                if attempt <= 3:
                    delay_minutes = 2 * attempt  # 2, 4, 6 minutos
                else:
                    delay_minutes = 15  # 15 minutos para tentativas posteriores
                    
                run_at = datetime.now() + timedelta(minutes=delay_minutes)
            else:
                # Após máximo de tentativas, reagendar para verificar de hora a hora
                delay_minutes = 60  # Verificar de hora a hora
                run_at = datetime.now() + timedelta(minutes=delay_minutes)
                # Resetar contador para manter tentativas infinitas
                attempt = 1
                print(f"🔄 Modo standby: Verificando conectividade de hora a hora...")
                
            # Reinicializar scheduler para reagendar
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
                
                jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///followup_jobs.db')}
                scheduler = BackgroundScheduler(jobstores=jobstores)
                scheduler.start()
                
                job_id = f"followup_retry_{paciente_id}_{int(time.time())}"
                scheduler.add_job(
                    func=send_followup_job_static,
                    trigger='date',
                    run_date=run_at,
                    args=[paciente_id, tipo_followup, dias_apos, attempt + 1, max_attempts],
                    id=job_id,
                    replace_existing=False
                )
                print(f"📅 Reagendado para {run_at} (job_id={job_id})")
                scheduler.shutdown(wait=False)
            except Exception as e:
                print(f"❌ Erro ao reagendar: {e}")
            return

        # Gerar email usando o sistema de templates
        try:
            from email_templates_biodesk import gerar_email_followup
            email_data = gerar_email_followup(
                nome_paciente=paciente.get('nome', 'Paciente'),
                tipo_followup=tipo_followup,
                dias_apos=dias_apos
            )
            assunto = email_data['assunto']
            corpo = email_data['corpo']
        except ImportError:
            # Fallback se não conseguir importar
            assunto = f"Acompanhamento de Consulta - {paciente.get('nome', 'Paciente')}"
            corpo = f"Olá {paciente.get('nome', 'Paciente')},\n\nComo se tem sentido desde a nossa última consulta?\n\nCumprimentos,\nNuno Correia"

        # Enviar email
        try:
            from email_sender import EmailSender
            sender = EmailSender()
            sucesso, mensagem = sender.send_email(
                to_email=to_email,
                subject=assunto,
                body=corpo,
                nome_destinatario=paciente.get('nome', 'Paciente')
            )

            if sucesso:
                print(f"✅ Follow-up enviado a {to_email} (paciente {paciente_id})")
                # Registar envio no histórico do paciente
                try:
                    historico_txt = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Enviado follow-up automático: {tipo_followup}"
                    db.adicionar_historico(paciente_id, historico_txt)
                except Exception:
                    pass
            else:
                print(f"❌ Falha no envio follow-up: {mensagem} — tentativa {attempt}/{max_attempts}")
                if attempt < max_attempts:
                    # reagenda tentativa
                    delay_minutes = 3 * attempt
                    run_at = datetime.now() + timedelta(minutes=delay_minutes)
                    
                    try:
                        from apscheduler.schedulers.background import BackgroundScheduler
                        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
                        
                        jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///followup_jobs.db')}
                        scheduler = BackgroundScheduler(jobstores=jobstores)
                        scheduler.start()
                        
                        job_id = f"followup_retry_{paciente_id}_{int(time.time())}"
                        scheduler.add_job(
                            func=send_followup_job_static,
                            trigger='date',
                            run_date=run_at,
                            args=[paciente_id, tipo_followup, dias_apos, attempt + 1, max_attempts],
                            id=job_id,
                            replace_existing=False
                        )
                        print(f"📅 Reagendado para {run_at} (job_id={job_id})")
                        scheduler.shutdown(wait=False)
                    except Exception as e:
                        print(f"❌ Erro ao reagendar: {e}")
                else:
                    try:
                        db.registar_envio_falhado(paciente_id, assunto, corpo, str(datetime.now()), erro=mensagem)
                    except Exception:
                        pass

        except ImportError:
            print(f"❌ EmailSender não disponível — simulando envio de follow-up para {to_email}")
            # Registar como enviado mesmo assim (simulação)
            try:
                historico_txt = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Follow-up simulado: {tipo_followup}"
                db.adicionar_historico(paciente_id, historico_txt)
            except Exception:
                pass

    except Exception as e:
        print(f"❌ Erro no job de follow-up: {e}")
        import traceback
        traceback.print_exc()


class SignatureCanvas(QWidget):
    """
    Widget melhorado para capturar assinaturas com o mouse
    """
    def __init__(self, parent=None, aspect_ratio=3.5):
        super().__init__(parent)
        self.path = QPainterPath()
        self.drawing = False
        self.aspect_ratio = aspect_ratio
        
        # Definir tamanho baseado na proporção mais adequada para visualização
        width = 500  # Largura reduzida para melhor visualização
        height = int(width / aspect_ratio)
        
        self.setMinimumSize(width, height)
        self.setMaximumSize(width + 100, height + 50)  # Pequena margem para flexibilidade
        
        self.setStyleSheet("""
            SignatureCanvas {
                background-color: white;
                border: 2px solid #28a745;
                border-radius: 8px;
            }
        """)
        
        # Configurar cursor de caneta para melhor UX
        self.setCursor(Qt.CursorShape.CrossCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.path.moveTo(event.position())
            
    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            self.path.lineTo(event.position())
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fundo branco
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        
        # Desenhar linha guia (discreta) se não há assinatura
        if self.path.isEmpty():
            pen_guia = QPen(QColor("#e0e0e0"), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen_guia)
            y_center = self.height() // 2
            painter.drawLine(20, y_center, self.width() - 20, y_center)
            
            # Texto de instrução discreto
            painter.setPen(QColor("#999999"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Assine aqui")
        
        # Desenhar a assinatura
        pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine, 
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(self.path)
        
    def clear(self):
        """Limpa a assinatura"""
        self.path = QPainterPath()
        self.update()
        
    def clear_signature(self):
        """Alias para compatibilidade - limpa a assinatura"""
        self.clear()
        
    def isEmpty(self):
        """Verifica se há assinatura"""
        return self.path.isEmpty()
        
    def is_empty(self):
        """Alias para compatibilidade - verifica se há assinatura"""
        return self.isEmpty()
        
    def get_signature_image(self):
        """Retorna a imagem da assinatura como QPixmap"""
        return self.toPixmap()
        
    def toPixmap(self):
        """Converte a assinatura para QPixmap"""
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        painter.drawPath(self.path)
        painter.end()
        return pixmap
        
    def get_signature_bytes(self):
        """Converte a assinatura para bytes (compatibilidade)"""
        try:
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
            pixmap = self.toPixmap()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            return bytes(byte_array)
        except Exception:
            return None

class FichaPaciente(QMainWindow):
    def __init__(self, paciente_data=None, parent=None):
        # 🚫 RADICAL ANTI-FLICKERING: Inicialização MÍNIMA
        super().__init__(parent)
        
        # APENAS o essencial durante __init__
        self.paciente_data = paciente_data or {}
        self.dirty = False
        
        # ✅ USAR SINGLETON DO DBMANAGER para melhor performance
        self.db = DBManager.get_instance()
        
        # Flags de controle para lazy loading
        self._pdf_viewer_initialized = False
        self._webengine_available = None
        self._initialized = False
        
        # ANTI-FLICKERING: Remover chamada para _init_delayed
        # A UI será construída diretamente no __init__ de forma otimizada
        
        # ✅ CONSTRUÇÃO SIMPLES E DIRETA DA UI
        self._ultima_zona_hover = None
        
        # Configurar geometria adequada
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Inicializar scheduler para follow-ups (apenas uma instância global)
        self._init_scheduler_safe()
        
        # Configurar atualização automática dos dados (otimizada)
        self.setup_data_refresh()
        
        # Armazenar referências das assinaturas digitais
        self.signature_canvas_paciente = None
        self.signature_canvas_terapeuta = None
        
        # Armazenar assinaturas capturadas por tipo de consentimento
        self.assinaturas_por_tipo = {}  # {'rgpd': {'paciente': bytes, 'terapeuta': bytes}, ...}
        self.assinatura_paciente_data = None
        self.assinatura_terapeuta_data = None
        
        # Adicionar debounce para prevenção de cliques múltiplos
        self._ultimo_clique_data = 0
        
        # ✨ CONSTRUIR UI DIRETAMENTE - SEM COMPLICAÇÕES
        self.init_ui()
        self.load_data()
        self.inicializar_templates_padrao()
    
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
    
    def aplicar_estilo_global_hover(self):
        """Aplica estilo de hover globalmente em todos os botões"""
        try:
            from biodesk_styles import aplicar_hover_global
            aplicar_hover_global()
            # Hover global aplicado a todos os botões
        except ImportError:
            # Módulo biodesk_styles não encontrado
            pass
        except Exception as e:
            # Erro ao aplicar hover global
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
        
        self.tabs.addTab(self.tab_dados_documentos, '📁 DADOS & DOCUMENTOS')
        self.tabs.addTab(self.tab_clinico_comunicacao, '🩺 ÁREA CLÍNICA')
        
        main_layout.addWidget(self.tabs)
        
        # Atalho Ctrl+S
        shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut.activated.connect(self.guardar)
        
        self.init_tab_dados_documentos()
        self.init_tab_clinico_comunicacao()

    def init_tab_dados_documentos(self):
        """
        DADOS & DOCUMENTOS
        - Dados Pessoais
        - Declaração de Saúde  
        - Consentimentos (movido para cá)
        - Gestão de Documentos
        """
        main_layout = QVBoxLayout(self.tab_dados_documentos)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ====== SUB-ABAS DENTRO DE DADOS & DOCUMENTOS ======
        self.dados_documentos_tabs = QTabWidget()
        self.dados_documentos_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.dados_documentos_tabs.setStyleSheet("""
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
        
        # Sub-abas
        self.sub_dados_pessoais = QWidget()
        self.sub_declaracao_saude = QWidget()
        self.sub_consentimentos = QWidget()
        
        self.dados_documentos_tabs.addTab(self.sub_dados_pessoais, '👤 Dados Pessoais')
        self.dados_documentos_tabs.addTab(self.sub_declaracao_saude, '🩺 Declaração de Saúde')
        self.dados_documentos_tabs.addTab(self.sub_consentimentos, '📋 Consentimentos')
        
        main_layout.addWidget(self.dados_documentos_tabs)
        
        # Inicializar sub-abas
        self.init_sub_dados_pessoais()
        self.init_sub_declaracao_saude()
        self.init_sub_consentimentos()
        
        # Forçar aplicação de estilos modernos nos botões de assinatura
        self._aplicar_estilos_modernos_assinatura()

    def init_tab_clinico_comunicacao(self):
        """
        📊 CLÍNICO & COMUNICAÇÃO
        - Histórico Clínico
        - Templates & Prescrições
        - Email
        """
        main_layout = QVBoxLayout(self.tab_clinico_comunicacao)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ====== SUB-ABAS DENTRO DE CLÍNICO & COMUNICAÇÃO ======
        self.clinico_comunicacao_tabs = QTabWidget()
        self.clinico_comunicacao_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.clinico_comunicacao_tabs.setStyleSheet("""
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
                background-color: #28a745;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Sub-abas
        self.sub_historico_clinico = QWidget()
        self.sub_templates_prescricoes = QWidget()
        self.sub_centro_comunicacao = QWidget()
        self.sub_gestao_documentos = QWidget()
        self.sub_iris_analise = QWidget()
        
        self.clinico_comunicacao_tabs.addTab(self.sub_historico_clinico, '📝 Histórico Clínico')
        self.clinico_comunicacao_tabs.addTab(self.sub_iris_analise, '👁️ Análise de Íris')
        self.clinico_comunicacao_tabs.addTab(self.sub_templates_prescricoes, '📋 Modelos de Prescrição')
        self.clinico_comunicacao_tabs.addTab(self.sub_centro_comunicacao, '📧 Email')
        self.clinico_comunicacao_tabs.addTab(self.sub_gestao_documentos, '📂 Gestão de Documentos')
        
        main_layout.addWidget(self.clinico_comunicacao_tabs)
        
        # Inicializar sub-abas
        self.init_sub_historico_clinico()
        self.init_sub_templates_prescricoes()
        self.init_sub_iris_analise()
        self.init_sub_centro_comunicacao()
        self.init_sub_gestao_documentos()

    def init_sub_dados_pessoais(self):
        """Sub-aba: Dados Pessoais - Layout profissional otimizado"""
        layout = QVBoxLayout(self.sub_dados_pessoais)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Grid com larguras FIXAS para distâncias uniformes
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)  # Espaçamento FIXO de 20px entre colunas
        grid.setVerticalSpacing(18)    # Espaçamento vertical ligeiramente aumentado
        
        # LARGURAS FIXAS para garantir distâncias uniformes
        grid.setColumnMinimumWidth(0, 160)  # Coluna labels esquerda: FIXA 160px
        grid.setColumnMinimumWidth(1, 200)  # Coluna campos esquerda
        grid.setColumnMinimumWidth(2, 100)  # Coluna labels centro: FIXA 100px  
        grid.setColumnMinimumWidth(3, 200)  # Coluna campos centro
        grid.setColumnMinimumWidth(4, 100)  # Coluna labels direita: FIXA 100px
        grid.setColumnMinimumWidth(5, 200)  # Coluna campos direita
        
        # Stretch factors para ocupar espaço restante
        grid.setColumnStretch(1, 1)  # Campos: stretch
        grid.setColumnStretch(3, 1)  # Campos: stretch
        grid.setColumnStretch(5, 1)  # Campos: stretch
        
        # ========== SEÇÃO IDENTIFICAÇÃO ==========
        # Linha 1: Nome (span completo)
        nome_label = QLabel("Nome:")
        nome_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; min-width: 160px; }")
        nome_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(nome_label, 0, 0)
        
        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo do paciente")
        self.nome_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.nome_edit, 0, 1, 1, 5)  # Span 5 colunas
        
        # Linha 2: Data nascimento | Sexo | Estado civil
        data_label = QLabel("Data de nascimento:")
        data_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        data_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(data_label, 1, 0)
        
        self.nasc_edit = ModernDateWidget()
        self.nasc_edit.setDate(QDate(1990, 1, 1))
        # SEM setFixedWidth - deixar ajustar automaticamente
        grid.addWidget(self.nasc_edit, 1, 1)
        
        sexo_label = QLabel("Sexo:")
        sexo_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        sexo_label.setFixedWidth(100)  # LARGURA FIXA para alinhamento
        grid.addWidget(sexo_label, 1, 2)
        
        self.sexo_combo = QComboBox()
        self.sexo_combo.addItems(['', 'Masculino', 'Feminino', 'Outro'])
        self.sexo_combo.setMaximumWidth(130)  # LARGURA CONTROLADA
        self.sexo_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QComboBox:focus { border-color: #007bff; }
            QComboBox::drop-down { border: 0px; width: 25px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)
        grid.addWidget(self.sexo_combo, 1, 3)
        
        estado_label = QLabel("Estado civil:")
        estado_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        estado_label.setFixedWidth(100)  # LARGURA FIXA para alinhamento
        grid.addWidget(estado_label, 1, 4)
        
        self.estado_civil_combo = QComboBox()
        self.estado_civil_combo.addItems(['', 'Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'União de facto'])
        self.estado_civil_combo.setMaximumWidth(150)  # LARGURA CONTROLADA
        self.estado_civil_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QComboBox:focus { border-color: #007bff; }
            QComboBox::drop-down { border: 0px; width: 25px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)
        grid.addWidget(self.estado_civil_combo, 1, 5)
        
        # ========== SEÇÃO DADOS PESSOAIS ==========
        # Linha 3: Naturalidade | Profissão | NIF
        nat_label = QLabel("Naturalidade:")
        nat_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        nat_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(nat_label, 2, 0)
        
        self.naturalidade_edit = QLineEdit()
        self.naturalidade_edit.setPlaceholderText("Cidade de nascimento")
        # SEM setFixedWidth - deixar ajustar automaticamente
        self.naturalidade_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.naturalidade_edit, 2, 1)
        
        prof_label = QLabel("Profissão:")
        prof_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        prof_label.setFixedWidth(100)  # LARGURA FIXA para alinhamento
        grid.addWidget(prof_label, 2, 2)
        
        self.profissao_edit = QLineEdit()
        self.profissao_edit.setPlaceholderText("Ex: Enfermeira, Professor")
        # SEM setFixedWidth - deixar ajustar automaticamente
        self.profissao_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.profissao_edit, 2, 3)
        
        nif_label = QLabel("NIF:")
        nif_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        nif_label.setFixedWidth(100)  # LARGURA FIXA para alinhamento
        grid.addWidget(nif_label, 2, 4)
        
        self.nif_edit = QLineEdit()
        self.nif_edit.setPlaceholderText("123 456 789")
        self.nif_edit.setMaxLength(11)
        self.nif_edit.setMaximumWidth(130)  # LARGURA CONTROLADA
        self.nif_edit.textChanged.connect(self.formatar_nif)
        self.nif_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.nif_edit, 2, 5)
        
        # Linha 4: Contacto | Email
        cont_label = QLabel("Contacto:")
        cont_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        cont_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(cont_label, 3, 0)
        
        self.contacto_edit = QLineEdit()
        self.contacto_edit.setPlaceholderText("Ex: +351 912 345 678")
        self.contacto_edit.setMaximumWidth(180)  # LARGURA CONTROLADA
        self.contacto_edit.textChanged.connect(self.formatar_contacto)
        self.contacto_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.contacto_edit, 3, 1)
        
        email_label = QLabel("Email:")
        email_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        email_label.setFixedWidth(100)  # LARGURA FIXA para alinhamento
        grid.addWidget(email_label, 3, 2)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("exemplo@email.com")
        self.email_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        # ✅ CORREÇÃO: Conectar sinal para atualizar email automaticamente
        self.email_edit.textChanged.connect(self.atualizar_email_paciente_data)
        grid.addWidget(self.email_edit, 3, 3, 1, 3)  # Span 3 colunas
        
        # ========== SEÇÃO ORIGEM & REFERÊNCIA ==========
        # Linha 5: Local habitual
        local_label = QLabel("Local habitual:")
        local_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        local_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(local_label, 4, 0)
        
        self.local_combo = QComboBox()
        self.local_combo.addItems(['', 'Chão de Lopes', 'Coruche', 'Campo Maior', 'Elvas', 'Samora Correia', 'Cliniprata', 'Spazzio Vita', 'Online', 'Outro'])
        self.local_combo.setMaximumWidth(200)  # LARGURA CONTROLADA
        self.local_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QComboBox:focus { border-color: #007bff; }
            QComboBox::drop-down { border: 0px; width: 25px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)
        grid.addWidget(self.local_combo, 4, 1, 1, 2)  # Span 2 colunas
        
        # Linha 6: Como nos conheceu | Referenciado(a) por
        conheceu_label = QLabel("Como nos conheceu:")
        conheceu_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        conheceu_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(conheceu_label, 5, 0)
        
        self.conheceu_combo = QComboBox()
        self.conheceu_combo.addItems(['', 'Recomendação', 'Redes Sociais', 'Google', 'Folheto', 'Evento', 'Amigo/Familiar', 'Outro'])
        self.conheceu_combo.setMaximumWidth(180)  # LARGURA CONTROLADA
        self.conheceu_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QComboBox:focus { border-color: #007bff; }
            QComboBox::drop-down { border: 0px; width: 25px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)
        grid.addWidget(self.conheceu_combo, 5, 1)
        
        ref_label = QLabel("Referenciado(a) por:")
        ref_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        ref_label.setFixedWidth(100)  # LARGURA FIXA para alinhamento
        grid.addWidget(ref_label, 5, 2)
        
        self.referenciado_edit = QLineEdit()
        self.referenciado_edit.setPlaceholderText("Nome da pessoa que referenciou")
        self.referenciado_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.referenciado_edit, 5, 3, 1, 3)  # Span 3 colunas
        
        # ========== SEÇÃO OBSERVAÇÕES ==========
        # Linha 7: Observações (span completo)
        obs_label = QLabel("Observações:")
        obs_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; color: #333; }")
        obs_label.setFixedWidth(160)  # LARGURA FIXA para alinhamento
        grid.addWidget(obs_label, 6, 0)
        
        self.observacoes_edit = QLineEdit()
        self.observacoes_edit.setPlaceholderText("Observações sobre o paciente...")
        self.observacoes_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
                min-height: 14px;
                max-height: 32px;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        grid.addWidget(self.observacoes_edit, 6, 1, 1, 5)  # Span 5 colunas
        
        layout.addLayout(grid)
        layout.addSpacing(30)
        
        # Botão de guardar - ESTILO IRIS
        botao_layout = QHBoxLayout()
        botao_layout.addStretch()
        
        self.btn_guardar_dados = QPushButton("💾 Guardar Dados")
        self._style_modern_button(self.btn_guardar_dados, "#28a745")
        self.btn_guardar_dados.clicked.connect(self.guardar)
        botao_layout.addWidget(self.btn_guardar_dados)
        
        layout.addLayout(botao_layout)
        layout.addStretch()

    def init_sub_historico_clinico(self):
        """Sub-aba: Histórico Clínico (sem biotipo e estado emocional, sem Chat IA)"""
        layout = QVBoxLayout(self.sub_historico_clinico)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Toolbar com margens e hover
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { 
                margin-bottom: 8px; 
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 5px;
            }
            QToolButton { 
                margin-right: 6px; 
                padding: 8px 12px; 
                border-radius: 6px;
                font-weight: 600;
                min-width: 30px;
            }
            QToolButton:hover { 
                background: #e9ecef; 
            }
            QToolButton:pressed {
                background: #dee2e6;
            }
        """)
        
        self.action_bold = QAction('B', self)
        self.action_bold.setShortcut('Ctrl+B')
        self.action_bold.triggered.connect(lambda: self.toggle_bold())
        
        self.action_italic = QAction('I', self)
        self.action_italic.setShortcut('Ctrl+I')
        self.action_italic.triggered.connect(lambda: self.toggle_italic())
        
        self.action_underline = QAction('U', self)
        self.action_underline.setShortcut('Ctrl+U')
        self.action_underline.triggered.connect(lambda: self.toggle_underline())
        
        self.action_date = QAction('📅', self)
        self.action_date.triggered.connect(self.inserir_data_negrito)
        
        self.toolbar.addAction(self.action_bold)
        self.toolbar.addAction(self.action_italic)
        self.toolbar.addAction(self.action_underline)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_date)
        
        # Adicionar espaço expansível para empurrar o botão guardar para a direita
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Botão Guardar como QToolButton (melhor para toolbars)
        self.btn_guardar_historico = QToolButton()
        self.btn_guardar_historico.setText('💾 Guardar')
        self.btn_guardar_historico.clicked.connect(self.guardar)
        
        # Aplicar estilo moderno padrão (fundo branco, borda colorida)
        self.btn_guardar_historico.setStyleSheet("""
            QToolButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 60px;
            }
            QToolButton:hover {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #4CAF50;
            }
        """)
        
        self.toolbar.addWidget(self.btn_guardar_historico)
        
        layout.addWidget(self.toolbar)

        # Editor de histórico
        self.historico_edit = QTextEdit()
        self.historico_edit.setPlaceholderText(
            "Descreva queixas, sintomas, evolução do caso ou observações clínicas relevantes...\n\n"
            "💡 Dica: Use o botão 📅 para inserir automaticamente a data de hoje no formato correto."
        )
        self.historico_edit.setMinimumHeight(420)  # Aumentar altura já que não há botão em baixo
        self._style_text_edit(self.historico_edit)
        layout.addWidget(self.historico_edit)

    def init_sub_templates_prescricoes(self):
        """Sub-aba: Templates & Prescrições - Sistema Profissional"""
        from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QWidget, QPushButton, QListWidget, QTextEdit, QStackedWidget, QSplitter
        from PyQt6.QtCore import Qt
        
        layout = QVBoxLayout(self.sub_templates_prescricoes)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Layout horizontal principal: esquerda (categorias), centro (preview), direita (botões)
        main_horizontal = QHBoxLayout()
        
        # ====== ESQUERDA: CATEGORIAS COM TEMPLATES EMBAIXO ======
        categorias_frame = QFrame()
        categorias_frame.setFixedWidth(280)  # Reduzir largura para dar mais espaço ao preview
        categorias_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        categorias_layout = QVBoxLayout(categorias_frame)
        
        # Título das categorias mais compacto
        cat_titulo = QLabel("🩺 Protocolos Terapêuticos")
        cat_titulo.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            padding: 6px;
            background-color: #e9ecef;
            border-radius: 5px;
        """)
        cat_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        categorias_layout.addWidget(cat_titulo)
        
        # Scroll area para categorias e templates
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Guardar referência ao layout para uso no toggle
        self.categorias_scroll_layout = scroll_layout
        
        # Botões de categorias com área para templates - PROTOCOLOS TERAPÊUTICOS
        self.template_categories = [
            ("🏃", "Exercícios e Alongamentos", "exercicios", "#ffeaa7"),      
            ("🥗", "Nutrição & Dietética", "dietas", "#a8e6cf"),              
            ("💊", "Suplementação", "suplementos", "#ffd3e1"),    
            ("📋", "Autocuidado e Rotinas", "orientacoes", "#e6d7ff"),
            ("📚", "Guias Educativos", "educativos", "#e1f5fe"),
            ("🎯", "Específicos por Condição", "condicoes", "#f3e5f5")
        ]
        
        self.btn_categories = {}
        self.templates_areas = {}  # Para armazenar áreas de templates
        for emoji, nome, categoria, cor in self.template_categories:
            # Container para categoria + templates
            categoria_container = QWidget()
            categoria_container_layout = QVBoxLayout(categoria_container)
            categoria_container_layout.setContentsMargins(0, 0, 0, 5)
            
            # Botão da categoria
            btn = QPushButton(f"{emoji} {nome}")
            btn.setFixedHeight(35)
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px;
                    font-weight: 600;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 10px;
                    background-color: {cor};
                    color: #2c3e50;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(cor, 15)};
                    color: #2c3e50;
                }}
                QPushButton:pressed {{
                    background-color: {self._lighten_color(cor, 25)};
                    color: #2c3e50;
                }}
            """)
            
            # Área para templates (inicialmente oculta)
            templates_area = QWidget()
            templates_layout = QVBoxLayout(templates_area)
            templates_layout.setContentsMargins(15, 5, 0, 0)  # Indentado à direita
            templates_area.setVisible(False)
            
            self.templates_areas[categoria] = templates_area
            self.btn_categories[categoria] = btn
            
            # Conectar clique para expandir/colapsar
            btn.clicked.connect(lambda checked, cat=categoria: self.toggle_categoria_templates(cat))
            
            categoria_container_layout.addWidget(btn)
            categoria_container_layout.addWidget(templates_area)
            
            # ADICIONAR ESPAÇO ENTRE CATEGORIAS
            categoria_container_layout.addSpacing(15)  # 15px de espaço extra
            
            scroll_layout.addWidget(categoria_container)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        categorias_layout.addWidget(scroll_area)
        main_horizontal.addWidget(categorias_frame, 3)  # AUMENTAR: proporção 3 (era 2)
        
        # ====== CENTRO: PREVIEW AMPLO (SEM BARRA DE TÍTULO) ======
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #9C27B0;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        # Preview integrado - pode ser texto OU PDF
        from PyQt6.QtWidgets import QStackedWidget
        
        # Criar widget empilhado para alternar entre texto e PDF
        self.preview_stack = QStackedWidget()
        
        # Widget 1: Preview de texto (atual) - ALTURA ULTRA REDUZIDA
        self.template_preview = QTextEdit()
        self.template_preview.setMinimumHeight(250)  # ULTRA REDUZIDO: era 400→320, agora 250
        self.template_preview.setMaximumHeight(300)  # ULTRA REDUZIDO: era 450→380, agora 300
        self.template_preview.setPlaceholderText("""
📄 PREVIEW INTEGRADO - TEXTO E PDF

Selecione um template à esquerda para visualizar:

📝 TEMPLATES TEXTO: Mostram conteúdo formatado
📄 TEMPLATES PDF: Mostram conteúdo extraído do PDF

🩺 Cabeçalho com logo Dr. Nuno Correia
📋 Dados completos do paciente  
📝 Conteúdo do template formatado
✅ Orientações médicas
👨‍⚕️ Assinatura profissional

✨ NOVO: PDFs integrados no canvas (sem janelas separadas)
        """)
        self.template_preview.setStyleSheet("""
            QTextEdit {
                background: white;
                border: none;
                border-radius: 5px;
                padding: 20px;
                font-family: 'Times New Roman', serif;
                font-size: 11px;
                color: #2c3e50;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: none;
                outline: none;
            }
        """)
        self.template_preview.setReadOnly(True)
        
        # Widget 2: Abertura Externa de PDFs (SEM PISCAR)
        # Removido QWebEngineView para eliminar janela que pisca
        self.pdf_preview = None
        self._webengine_available = False
        
        # Criar botão para abrir PDFs externamente
        from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout
        self.pdf_external_widget = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_external_widget)
        
        pdf_label = QLabel("📄 Visualização de PDFs")
        pdf_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #2c3e50;
            padding: 10px;
        """)
        
        self.btn_abrir_pdf_externo = QPushButton("🔍 Abrir PDF no Visualizador Externo")
        self.btn_abrir_pdf_externo.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.btn_abrir_pdf_externo.clicked.connect(self.abrir_pdf_atual_externo)
        self.btn_abrir_pdf_externo.setEnabled(False)  # Ativado quando há PDF
        
        info_label = QLabel("💡 Os PDFs serão abertos no seu visualizador padrão\n(Adobe Reader, Navegador, etc.)")
        info_label.setStyleSheet("""
            color: #6c757d;
            font-size: 12px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        """)
        
        pdf_layout.addWidget(pdf_label)
        pdf_layout.addWidget(self.btn_abrir_pdf_externo)
        pdf_layout.addWidget(info_label)
        pdf_layout.addStretch()
        
        self.pdf_external_widget.setMinimumHeight(350)
        self.pdf_external_widget.setMaximumHeight(400)
        
        # PDF viewer configurado para abertura externa
        
        # Adicionar ambos ao stack (PDF externo ao invés de placeholder)
        self.preview_stack.addWidget(self.template_preview)    # Índice 0: Texto
        self.preview_stack.addWidget(self.pdf_external_widget)  # Índice 1: PDF externo
        self.preview_stack.setCurrentIndex(0)  # Começar com texto
        
        # MELHORAR LAYOUT: Adicionar com proporção adequada
        preview_layout.addWidget(self.preview_stack, 1)  # Usar todo o espaço disponível
        
        # ✅ ADICIONAR BOTÃO PDF COM ESTILO PREFERIDO
        self.btn_pdf_preview = QPushButton("🔍 Abrir PDF Completo")
        self.btn_pdf_preview.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 600;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e91e63;
                color: white;
                border-color: #e91e63;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
                border-color: #dee2e6;
            }
        """)
        self.btn_pdf_preview.clicked.connect(self.abrir_pdf_atual_externo)
        self.btn_pdf_preview.setEnabled(False)  # Desativado até selecionar PDF
        self.btn_pdf_preview.setVisible(False)  # Invisível até selecionar PDF
        
        preview_layout.addWidget(self.btn_pdf_preview)
        
        # AJUSTAR PROPORÇÕES: Centro reduzido para dar espaço às categorias
        main_horizontal.addWidget(preview_frame, 2)   # REDUZIR MAIS: proporção 2 (era 3)
        
        # ====== DIREITA: BOTÕES DE AÇÃO VERTICAIS - MELHORADA ======
        botoes_frame = QFrame()
        # botoes_frame.setFixedWidth(200)  # REMOVER largura fixa para ser proporcional
        botoes_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #dee2e6;
                border-radius: 12px;
                padding: 20px;
                margin: 5px;
            }
        """)
        botoes_layout = QVBoxLayout(botoes_frame)
        botoes_layout.setSpacing(12)
        
        # ÁREA DE PROTOCOLOS SELECIONADOS - MELHORADA
        self.protocolos_selecionados = []
        protocolos_frame = QFrame()
        protocolos_frame.setMinimumHeight(130)  # Garantir altura mínima
        protocolos_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #fff3cd, stop:1 #ffeaa7);
                border: 2px solid #f0c14b;
                border-radius: 10px;
                padding: 12px;
                margin: 5px 0px;
            }
        """)
        protocolos_layout = QVBoxLayout(protocolos_frame)
        protocolos_layout.setSpacing(8)
        
        protocolos_titulo = QLabel("📋 Protocolos Selecionados")
        protocolos_titulo.setStyleSheet("""
            font-weight: bold; 
            color: #856404; 
            font-size: 11px;
            margin-bottom: 8px;
            padding: 4px;
            background-color: rgba(255,255,255,0.7);
            border-radius: 6px;
            text-align: center;
        """)
        protocolos_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        protocolos_layout.addWidget(protocolos_titulo)
        
        self.lista_protocolos = QLabel("Nenhum protocolo selecionado")
        self.lista_protocolos.setStyleSheet("""
            color: #856404; 
            font-size: 10px; 
            padding: 8px;
            background-color: rgba(255,255,255,0.9);
            border-radius: 6px;
            border: 1px solid #f0c14b;
        """)
        self.lista_protocolos.setWordWrap(True)
        self.lista_protocolos.setMinimumHeight(80)
        self.lista_protocolos.setAlignment(Qt.AlignmentFlag.AlignTop)
        protocolos_layout.addWidget(self.lista_protocolos)
        
        # Botão para limpar seleção - MELHORADO
        self.btn_limpar_protocolos = QPushButton("🗑️ Limpar")
        self.btn_limpar_protocolos.setFixedHeight(35)  # Aumentado de 28 para 35
        self.btn_limpar_protocolos.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #dc3545, stop:1 #c82333);
                color: white;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
                border: 1px solid #bd2130;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e74c3c, stop:1 #c0392b);
            }
            QPushButton:pressed { background-color: #a71e2a; }
        """)
        self.btn_limpar_protocolos.clicked.connect(self.limpar_protocolos_selecionados)
        protocolos_layout.addWidget(self.btn_limpar_protocolos)
        
        botoes_layout.addWidget(protocolos_frame)
        
        # BOTÃO PRINCIPAL: ENVIO DIRETO - ESTILO PREFERIDO
        self.btn_workflow_completo = QPushButton("🚀 Enviar\nProtocolos")
        self.btn_workflow_completo.setFixedHeight(75)
        self.btn_workflow_completo.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #28a745;
                color: white;
                border-color: #28a745;
            }
            QPushButton:pressed { 
                background-color: #1e7e34; 
                border-color: #1e7e34;
            }
        """)
        self.btn_workflow_completo.setToolTip("📧 ENVIO DIRETO:\n" +
                                            "• Enviar protocolos PDF selecionados\n" +
                                            "• Email personalizado automático\n" +
                                            "• Registar no histórico\n" +
                                            "• Sem conversões - envio imediato")
        self.btn_workflow_completo.clicked.connect(self.enviar_protocolos_direto)
        botoes_layout.addWidget(self.btn_workflow_completo)

        # ===== BOTÕES REMOVIDOS PARA SIMPLIFICAÇÃO =====
        # (Apenas mantemos os 3 botões principais)
        
        # SEPARADOR ELEGANTE
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("""
            color: #dee2e6; 
            margin: 15px 5px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 transparent, stop:0.5 #dee2e6, stop:1 transparent);
        """)
        botoes_layout.addWidget(separador)
        
        # BOTÃO 2: EDITOR AVANÇADO - ESTILO PREFERIDO
        self.btn_editor_avancado = QPushButton("⚙️ Editor\nAvançado")
        self.btn_editor_avancado.setFixedHeight(65)
        self.btn_editor_avancado.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #17a2b8;
                color: white;
                border-color: #17a2b8;
            }
            QPushButton:pressed { 
                background-color: #138496; 
                border-color: #138496;
            }
        """)
        self.btn_editor_avancado.setToolTip("🎯 EDITOR COMPLETO:\n" +
                                          "• Editar conteúdo dos protocolos\n" + 
                                          "• Personalizar para cada paciente\n" +
                                          "• Combinar múltiplos protocolos\n" +
                                          "• Criar documentos personalizados")
        self.btn_editor_avancado.clicked.connect(self.abrir_editor_avancado)
        botoes_layout.addWidget(self.btn_editor_avancado)
        
        # Espaçador para empurrar botões para o topo
        botoes_layout.addStretch()
        
        main_horizontal.addWidget(botoes_frame, 2)  # ADICIONAR proporção 2 para alargar
        
        layout.addLayout(main_horizontal, 1)
        
        # Inicializar templates padrão
        self.inicializar_templates_padrao()

    def init_sub_centro_comunicacao(self):
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
        btn_followup.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
            QPushButton:pressed {
                background-color: #0056b3;
                border-color: #0056b3;
            }
        """)
        btn_followup.clicked.connect(self.schedule_followup_consulta)
        para_layout.addWidget(btn_followup)
        
        btn_template = QPushButton("📄 Templates")
        btn_template.setFixedHeight(45)
        btn_template.setFixedWidth(120)  # TAMANHO UNIFICADO
        btn_template.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                margin-left: 5px;
            }
            QPushButton:hover {
                background-color: #6c757d;
                color: white;
                border-color: #6c757d;
            }
        """)
        btn_template.clicked.connect(self.abrir_templates_mensagem)
        para_layout.addWidget(btn_template)
        
        btn_listar_followups = QPushButton("📋 Lista")
        btn_listar_followups.setFixedHeight(45)
        btn_listar_followups.setFixedWidth(120)  # TAMANHO UNIFICADO
        btn_listar_followups.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                margin-left: 5px;
            }
            QPushButton:hover {
                background-color: #6f42c1;
                color: white;
                border-color: #6f42c1;
            }
            QPushButton:pressed {
                background-color: #5a34a3;
                border-color: #5a34a3;
            }
        """)
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
        btn_enviar_email.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #28a745;
                color: white;
                border-color: #28a745;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
                border-color: #1e7e34;
            }
        """)
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
        btn_config_inferior.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                margin-top: 10px;
                margin-right: 20px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #17a2b8;
                color: white;
                border-color: #17a2b8;
            }
        """)
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
        btn_enviar.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: 2px solid #4caf50;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #4caf50);
                border-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #45a049;
                border-color: #45a049;
            }
        """)
        btn_enviar.clicked.connect(self.enviar_mensagem)
        # REMOVIDO: botoes_layout.addWidget(btn_enviar) - código duplicado
        
        # REMOVIDO: botoes_layout.addStretch() - código duplicado
        
        # ✅ BOTÃO CENTRALIZADO E DESTACADO
        # REMOVIDO: layout.addLayout(botoes_layout) - código duplicado
        
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
            # Carregar email se disponível
            email_paciente = self.paciente_data.get('email', '').strip()
            # print(f"[EMAIL DEBUG] 📧 Email encontrado: '{email_paciente}'")
            
            if email_paciente:
                self.destinatario_edit.setText(email_paciente)
                # Email do paciente carregado
            else:
                # Paciente não tem email configurado
                pass
            
            # Carregar nome para personalização
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            self.nome_paciente = nome_paciente
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

    # ====== MÉTODOS PARA TEMPLATES ======
    def inicializar_templates_padrao(self):
        """Inicializa os templates padrão se não existirem"""
        templates_padrao = {
            "exercicios": [
                {
                    "nome": "Caminhada Diária",
                    "texto": "**Exercício recomendado: Caminhada**\n\n• Duração: 30-45 minutos\n• Frequência: Diariamente\n• Intensidade: Moderada\n• Observações: Manter ritmo constante, hidratação adequada"
                },
                {
                    "nome": "Alongamentos Matinais",
                    "texto": "**Rotina de Alongamentos Matinais**\n\n• Duração: 15-20 minutos\n• Frequência: Ao acordar\n• Focar: Coluna, pescoço, membros\n• Respiração: Profunda e controlada"
                }
            ],
            "dietas": [
                {
                    "nome": "Dieta Anti-inflamatória",
                    "texto": "**Plano Alimentar Anti-inflamatório**\n\n• Aumentar: Vegetais verdes, frutos vermelhos, peixes gordos\n• Reduzir: Açúcares, farinhas refinadas, carnes processadas\n• Hidratação: 2-3L água/dia\n• Suplementação: Conforme avaliação"
                },
                {
                    "nome": "Detox Hepático",
                    "texto": "**Protocolo de Detox Hepático**\n\n• Manhã: Água morna com limão\n• Evitar: Álcool, frituras, laticínios\n• Incluir: Chás depurativos, vegetais crucíferos\n• Duração: 7-14 dias"
                }
            ],
            "suplementos": [
                {
                    "nome": "Suporte Imunitário",
                    "texto": "**Protocolo Imunitário**\n\n• Vitamina C: 1000mg/dia\n• Vitamina D3: 2000UI/dia\n• Zinco: 15mg/dia\n• Probióticos: Conforme indicação\n• Duração: 30 dias, reavaliar"
                }
            ],
            "orientacoes": [
                {
                    "nome": "Higiene do Sono",
                    "texto": "**Orientações para Qualidade do Sono**\n\n• Horário regular: Deitar e levantar sempre na mesma hora\n• Ambiente: Quarto escuro, silencioso, temperatura amena\n• Evitar: Ecrãs 1h antes de dormir\n• Relaxamento: Técnicas de respiração ou meditação"
                }
            ]
        }
        
        # Criar diretório de templates se não existir
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        # Salvar templates padrão
        for categoria, templates in templates_padrao.items():
            categoria_file = templates_dir / f"{categoria}.json"
            if not categoria_file.exists():
                with open(categoria_file, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)

    def toggle_categoria_templates(self, categoria):
        """Mostra/esconde templates de uma categoria específica"""
        # print(f"🔘 [DEBUG] Botão clicado para categoria: {categoria}")
        try:
            # Verificar se existe área de templates para esta categoria
            if categoria not in self.templates_areas:
                # print(f"❌ [DEBUG] Área de templates não encontrada para categoria: {categoria}")
                # print(f"🔍 [DEBUG] Áreas disponíveis: {list(self.templates_areas.keys())}")
                return
            
            templates_area = self.templates_areas[categoria]
            # print(f"📦 [DEBUG] Área encontrada para {categoria}")
            
            # Toggle visibilidade
            was_visible = templates_area.isVisible()
            templates_area.setVisible(not was_visible)
            # print(f"👁️ [DEBUG] Visibilidade alterada: {was_visible} -> {not was_visible}")
            
            # Se está sendo mostrada, carregar templates
            if templates_area.isVisible():
                # print(f"🔄 [DEBUG] Carregando templates para área de {categoria}")
                self.carregar_templates_em_area_com_pdfs(categoria, templates_area)
            else:
                # print(f"🙈 [DEBUG] Área de {categoria} escondida")
                pass
                
        except Exception as e:
            # print(f"❌ [DEBUG] Erro em toggle_categoria_templates: {e}")
            pass

    def carregar_templates_em_area(self, categoria, templates_area):
        """Carrega templates de uma categoria na área específica"""
        try:
            # Limpar área atual
            layout = templates_area.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Carregar templates da categoria
            templates_file = Path("templates") / f"{categoria}.json"
            if templates_file.exists():
                try:
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                    
                    for template in templates:
                        template_btn = QPushButton(f"📄 {template['nome']}")
                        template_btn.setFixedHeight(30)
                        template_btn.setStyleSheet("""
                            QPushButton {
                                text-align: left;
                                padding: 8px 15px;
                                background-color: #ffffff;
                                border: 1px solid #dee2e6;
                                border-radius: 4px;
                                color: #495057;
                                font-size: 12px;
                            }
                            QPushButton:hover {
                                background-color: #e9ecef;
                                border-color: #9C27B0;
                            }
                            QPushButton:pressed {
                                background-color: #9C27B0;
                                color: white;
                            }
                        """)
                        template_btn.clicked.connect(lambda checked, t=template: self.selecionar_template_por_data(t))
                        layout.addWidget(template_btn)
                        
                except Exception as e:
                    print(f"Erro ao carregar templates: {e}")
                    error_label = QLabel("❌ Erro ao carregar templates")
                    error_label.setStyleSheet("color: #dc3545; padding: 10px; font-size: 12px;")
                    layout.addWidget(error_label)
            else:
                # Nenhum template encontrado
                empty_label = QLabel("📭 Nenhum template encontrado")
                empty_label.setStyleSheet("color: #6c757d; padding: 10px; font-style: italic; font-size: 12px;")
                layout.addWidget(empty_label)
                
        except Exception as e:
            print(f"Erro ao carregar templates em área: {e}")
            
    def carregar_templates_em_area_com_pdfs(self, categoria, templates_area):
        """Carrega APENAS PDFs - sistema simplificado conforme solicitado"""
        try:
            # print(f"🔄 [PDF-ONLY] Carregando PDFs para categoria: {categoria}")
            
            # Limpar área atual
            layout = templates_area.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            templates_adicionados = 0
            
            # APENAS PDFs - remover JSON e TXT completamente
            categoria_dir = Path("templates") / f"{categoria}_pdf"  # Usar diretório _pdf diretamente
            # print(f"� [PDF-ONLY] Procurando PDFs em: {categoria_dir}")
            
            if categoria_dir.exists():
                try:
                    pdf_count = 0
                    for arquivo in categoria_dir.iterdir():
                        if arquivo.suffix.lower() == '.pdf':
                            pdf_count += 1
                            
                            # USAR NOME REAL DO FICHEIRO (sem extensão)
                            nome_template = arquivo.stem.replace('_', ' ').replace('-', ' ')
                            
                            # Emoji simples baseado na categoria (sem texto extra)
                            if categoria == 'exercicios':
                                emoji = "🏃‍♂️"
                            elif categoria == 'dietas':
                                emoji = "🥗"
                            elif categoria == 'suplementos':
                                emoji = "💊"
                            elif categoria == 'orientacoes':
                                emoji = "📋"
                            elif categoria == 'educativos':
                                emoji = "📚"
                            elif categoria == 'condicoes':
                                emoji = "🎯"
                            else:
                                emoji = "📄"
                            
                            # BOTÃO LIMPO - emoji + nome do ficheiro
                            template_btn = QPushButton(f"{emoji} {nome_template}")
                            template_btn.setFixedHeight(32)  # Aumentar mais para mostrar labels
                            template_btn.setStyleSheet("""
                                QPushButton {
                                    text-align: left;
                                    padding: 6px 10px;
                                    background-color: #e3f2fd;
                                    border: 2px solid #1976d2;
                                    border-radius: 6px;
                                    margin: 2px 0px;
                                    color: #1565c0;
                                    font-weight: 600;
                                    font-size: 10px;
                                    min-height: 28px;
                                }
                                QPushButton:hover {
                                    background-color: #bbdefb;
                                    border-color: #1565c0;
                                    color: #0d47a1;
                                }
                                QPushButton:pressed {
                                    background-color: #1976d2;
                                    color: white;
                                }
                            """)
                            
                            # Dados do template PDF
                            template_data = {
                                'tipo': 'pdf',
                                'nome': nome_template,
                                'arquivo': str(arquivo),
                                'categoria': categoria,
                                'tamanho': self._obter_tamanho_arquivo_legivel(arquivo)
                            }
                            
                            # Conectar clique para seleção COM VISUALIZADOR AUTOMÁTICO
                            template_btn.clicked.connect(
                                lambda checked, data=template_data: self.selecionar_pdf_e_mostrar_visualizador(data)
                            )
                            
                            layout.addWidget(template_btn)
                            templates_adicionados += 1
                            print(f"  ✅ PDF: {nome_template} ({template_data['tamanho']})")
                    
                    # print(f"📄 [PDF-ONLY] PDFs encontrados: {pdf_count}")
                except Exception as e:
                    print(f"❌ [PDF-ONLY] Erro ao carregar PDFs: {e}")
            else:
                print(f"⚠️ [PDF-ONLY] Diretório não existe: {categoria_dir}")
                
                # Tentar diretório sem _pdf (fallback)
                categoria_dir_alt = Path("templates") / categoria
                if categoria_dir_alt.exists():
                    print(f"📂 [PDF-ONLY] Tentando diretório alternativo: {categoria_dir_alt}")
                    try:
                        for arquivo in categoria_dir_alt.iterdir():
                            if arquivo.suffix.lower() == '.pdf':
                                nome_template = arquivo.stem.replace('_', ' ').title()
                                
                                template_btn = QPushButton(f"📄 {nome_template}")
                                template_btn.setFixedHeight(32)
                                template_btn.setStyleSheet("""
                                    QPushButton {
                                        text-align: left;
                                        padding: 10px 15px;
                                        background-color: #e3f2fd;
                                        border: 2px solid #1976d2;
                                        border-radius: 6px;
                                        margin: 3px 0px;
                                        color: #1565c0;
                                        font-weight: 600;
                                        font-size: 12px;
                                    }
                                    QPushButton:hover {
                                        background-color: #bbdefb;
                                        border-color: #1565c0;
                                    }
                                """)
                                
                                template_data = {
                                    'tipo': 'pdf',
                                    'nome': nome_template,
                                    'arquivo': str(arquivo),
                                    'categoria': categoria,
                                    'tamanho': self._obter_tamanho_arquivo_legivel(arquivo)
                                }
                                
                                template_btn.clicked.connect(
                                    lambda checked, data=template_data: self.selecionar_template_pdf_melhorado(data)
                                )
                                
                                layout.addWidget(template_btn)
                                templates_adicionados += 1
                                print(f"  ✅ PDF (alt): {nome_template}")
                    except Exception as e:
                        print(f"❌ [PDF-ONLY] Erro no diretório alternativo: {e}")
            
            # Se não há PDFs
            if templates_adicionados == 0:
                empty_label = QLabel("📭 Nenhum PDF encontrado nesta categoria")
                empty_label.setStyleSheet("""
                    QLabel {
                        color: #666;
                        padding: 20px;
                        font-style: italic;
                        font-size: 14px;
                        text-align: center;
                        background-color: #f8f9fa;
                        border: 2px dashed #dee2e6;
                        border-radius: 8px;
                        margin: 10px 0px;
                    }
                """)
                layout.addWidget(empty_label)
                print("❌ [PDF-ONLY] Nenhum PDF encontrado")
            else:
                print(f"📊 [PDF-ONLY] Total de PDFs carregados: {templates_adicionados}")
                
                # ADICIONAR ESPAÇAMENTO EXTRA NO FINAL DOS PROTOCOLOS
                spacer = QWidget()
                spacer.setFixedHeight(25)  # Espaçamento de 25px
                layout.addWidget(spacer)
                
        except Exception as e:
            print(f"❌ [PDF-ONLY] Erro ao carregar PDFs: {e}")
            import traceback
            traceback.print_exc()

    def selecionar_template_por_data(self, template_data):
        """Seleciona um template pelos dados do template"""
        try:
            # Ocultar botão de PDF (apenas para PDFs)
            if hasattr(self, 'btn_mostrar_pdf'):
                self.btn_mostrar_pdf.setVisible(False)
                
            # Atualizar preview
            self.template_preview.setPlainText(template_data.get('conteudo', ''))
            self.template_selecionado = template_data
            print(f"Template selecionado: {template_data.get('nome', 'Sem nome')}")
        except Exception as e:
            print(f"Erro ao selecionar template: {e}")
            
    def selecionar_template_pdf_melhorado(self, template_data):
        """Seleciona um template PDF e mostra preview COMPLETO sem corte"""
        try:
            print(f"📄 [PDF-PREVIEW] PDF selecionado: {template_data.get('nome', 'Sem nome')}")
            
            # Atualizar preview com ALTURA MAIOR para mostrar PDF completo
            nome_paciente = self.paciente_data.get('nome', 'N/A') if self.paciente_data else 'N/A'
            data_atual = datetime.now().strftime('%d/%m/%Y')
            
            # Preview COMPLETO do PDF sem corte
            preview_pdf_completo = f"""
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
                      🩺 DOCUMENTO PDF MÉDICO                      
                                                                
       [LOGO]              Dr. Nuno Correia                     
      Biodesk           Medicina Integrativa                    
                      & Análise Iridológica                     
                                                                
  📧 geral@nunocorreia.pt       📞 (+351) 123 456 789           
  🌐 www.nunocorreia.pt                     Data: {data_atual}      
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌

📊 DADOS DO PACIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nome:       {nome_paciente}
Data Nasc:  {self.paciente_data.get('data_nascimento', 'N/A') if self.paciente_data else 'N/A'}
Email:      {self.paciente_data.get('email', 'N/A') if self.paciente_data else 'N/A'}
Contacto:   {self.paciente_data.get('contacto', 'N/A') if self.paciente_data else 'N/A'}

📄 DOCUMENTO PDF: {template_data['nome'].upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️ INFORMAÇÕES DO ARQUIVO:
• Nome: {template_data['nome']}
• Tipo: Protocolo/Orientação em PDF  
• Tamanho: {template_data.get('tamanho', 'N/A')}
• Categoria: {template_data.get('categoria', 'N/A').title()}
• Localização: {template_data.get('arquivo', 'N/A')}

📄 CONTEÚDO DO PDF:
Este documento PDF contém orientações médicas personalizadas
baseadas na sua consulta e análise iridológica realizada.

O protocolo inclui:
✓ Recomendações específicas para o seu caso
✓ Orientações dietéticas personalizadas  
✓ Suplementação natural adequada
✓ Cronograma de acompanhamento
✓ Instruções detalhadas de implementação

📋 AÇÕES DISPONÍVEIS:
• 👁️  Visualizar PDF no visualizador integrado
• 📧 Enviar por email ao paciente com texto personalizado
• 📝 Registar automaticamente no histórico clínico  
• 💾 Incluir no workflow completo (Word+PDF+Email)

⚡ PRÓXIMO PASSO RECOMENDADO:
   Clique "📧 Enviar e Registar" para:
   
   1️⃣ Abrir o PDF no visualizador para confirmação
   2️⃣ Enviar automaticamente por email personalizado
   3️⃣ Registar no histórico clínico com timestamp
   4️⃣ Manter cópia organizada no sistema

🔒 NOTA DE CONFIDENCIALIDADE:
Este documento médico é confidencial e personalizado exclusivamente 
para {nome_paciente}. Contém informações sigilosas da consulta 
médica e deve ser tratado com total confidencialidade.

🆘 SUPORTE E DÚVIDAS:
Em caso de dúvidas sobre este protocolo:
• Email: geral@nunocorreia.pt
• Instagram: @nunocorreia.naturopata  
• Facebook: @NunoCorreiaTerapiasNaturais
• Telefone: [Configurado no sistema]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🔒 Documento médico confidencial                
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            # Definir preview COMPLETO - sem corte
            self.template_preview.setPlainText(preview_pdf_completo)
            self.template_selecionado = template_data
            
            # ✅ ATIVAR BOTÃO PDF se o arquivo existir
            pdf_path = template_data.get('arquivo')
            if pdf_path and os.path.exists(pdf_path):
                self._ultimo_pdf_gerado = pdf_path
                
                # Ativar botão principal no preview
                if hasattr(self, 'btn_pdf_preview'):
                    self.btn_pdf_preview.setEnabled(True)
                    self.btn_pdf_preview.setVisible(True)
                    self.btn_pdf_preview.setText(f"🔍 Abrir: {os.path.basename(pdf_path)}")
                
                print(f"✅ [PDF] Botão ativado para: {os.path.basename(pdf_path)}")
            else:
                # Desativar botão se não há PDF
                if hasattr(self, 'btn_pdf_preview'):
                    self.btn_pdf_preview.setEnabled(False)
                    self.btn_pdf_preview.setVisible(False)
                
                print(f"⚠️ [PDF] Arquivo não encontrado: {pdf_path}")
            
            print(f"✅ [PDF-PREVIEW] Preview COMPLETO criado para: {template_data['nome']}")
            
        except Exception as e:
            print(f"❌ [PDF-PREVIEW] Erro ao criar preview: {e}")

    def carregar_templates_categoria(self, categoria):
        """Carrega templates de uma categoria específica, incluindo PDFs"""
        print(f"🔄 [DEBUG] Carregando categoria: {categoria}")
        
        self.categoria_selecionada = categoria.title()  # Guardar categoria atual
        self.templates_titulo.setText(f"📋 Templates: {categoria.title()}")
        self.lista_templates.clear()
        
        # 1. Carregar templates JSON tradicionais
        templates_file = Path("templates") / f"{categoria}.json"
        print(f"📁 [DEBUG] Procurando JSON: {templates_file}")
        
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                
                print(f"📝 [DEBUG] Templates JSON encontrados: {len(templates)}")
                for template in templates:
                    template['tipo'] = 'TXT'  # Marcar como TXT para compatibilidade com editor
                    # Adicionar conteúdo se não existir (para templates JSON antigos)
                    if 'conteudo' not in template and 'texto' in template:
                        template['conteudo'] = template['texto']
                    item = QListWidgetItem(f"📝 {template['nome']}")
                    item.setData(Qt.ItemDataRole.UserRole, template)
                    self.lista_templates.addItem(item)
                    print(f"  ✅ JSON: {template['nome']}")
            except Exception as e:
                print(f"❌ [DEBUG] Erro ao carregar JSON: {e}")
        
        # 2. Carregar PDFs da categoria
        categoria_dir = Path("templates") / categoria
        print(f"📂 [DEBUG] Procurando PDFs em: {categoria_dir}")
        
        if categoria_dir.exists():
            try:
                pdf_count = 0
                for arquivo in categoria_dir.iterdir():
                    if arquivo.suffix.lower() == '.pdf':
                        pdf_count += 1
                        # Criar template para PDF
                        nome_template = arquivo.stem
                        template_pdf = {
                            'nome': nome_template,
                            'tipo': 'pdf',
                            'arquivo': str(arquivo),
                            'categoria': categoria,
                            'tamanho': self._obter_tamanho_arquivo_legivel(arquivo)
                        }
                        
                        item = QListWidgetItem(f"📄 {nome_template}")
                        item.setData(Qt.ItemDataRole.UserRole, template_pdf)
                        self.lista_templates.addItem(item)
                        print(f"  ✅ PDF: {nome_template} ({template_pdf['tamanho']})")
                
                print(f"📄 [DEBUG] PDFs encontrados: {pdf_count}")
            except Exception as e:
                print(f"❌ [DEBUG] Erro ao carregar PDFs: {e}")
        else:
            print(f"⚠️ [DEBUG] Diretório não existe: {categoria_dir}")
        
        # 3. Carregar templates TXT
        if categoria_dir.exists():
            try:
                txt_count = 0
                for arquivo in categoria_dir.iterdir():
                    if arquivo.suffix.lower() == '.txt':
                        txt_count += 1
                        with open(arquivo, 'r', encoding='utf-8') as f:
                            conteudo = f.read()
                        
                        nome_template = arquivo.stem.replace('_', ' ').title()
                        template_txt = {
                            'nome': nome_template,
                            'texto': conteudo,
                            'tipo': 'texto',
                            'categoria': categoria
                        }
                        
                        item = QListWidgetItem(f"📝 {nome_template}")
                        item.setData(Qt.ItemDataRole.UserRole, template_txt)
                        self.lista_templates.addItem(item)
                        print(f"  ✅ TXT: {nome_template}")
                
                print(f"📝 [DEBUG] TXTs encontrados: {txt_count}")
            except Exception as e:
                print(f"❌ [DEBUG] Erro ao carregar TXT: {e}")
        
        # Total final
        total_items = self.lista_templates.count()
        print(f"📊 [DEBUG] Total de templates carregados: {total_items}")
        
        # Se não há nenhum template
        if total_items == 0:
            item = QListWidgetItem("Nenhum template encontrado para esta categoria")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.lista_templates.addItem(item)
            print("❌ [DEBUG] Nenhum template encontrado")
    
    def _obter_tamanho_arquivo_legivel(self, caminho):
        """Obtém tamanho do arquivo em formato legível"""
        try:
            tamanho_bytes = caminho.stat().st_size
            if tamanho_bytes < 1024:
                return f"{tamanho_bytes} B"
            elif tamanho_bytes < 1024 * 1024:
                return f"{tamanho_bytes / 1024:.1f} KB"
            else:
                return f"{tamanho_bytes / (1024 * 1024):.1f} MB"
        except:
            return "N/A"

    def selecionar_template(self, item):
        """Seleciona um template e mostra o preview limpo e elegante"""
        template_data = item.data(Qt.ItemDataRole.UserRole)
        if template_data:
            # Verificar se é PDF
            if template_data.get('tipo') == 'pdf':
                self._mostrar_preview_pdf(template_data)
            else:
                self._mostrar_preview_texto(template_data)
    
    def _mostrar_preview_pdf(self, template_data):
        """Mostra preview específico para PDFs"""
        nome_paciente = self.paciente_data.get('nome', 'N/A') if self.paciente_data else 'N/A'
        data_atual = datetime.now().strftime('%d/%m/%Y')
        
        preview_pdf = f"""
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
                    🩺 DOCUMENTO PDF MÉDICO                    
                                                          
     [LOGO]            Dr. Nuno Correia                   
    Biodesk         Medicina Integrativa                  
                  & Análise Iridológica                   
                                                          
📧 geral@nunocorreia.pt     📞 (+351) 123 456 789         
🌐 www.nunocorreia.pt                   Data: {data_atual}    
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌

📋 DADOS DO PACIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nome:       {nome_paciente}
Data Nasc:  {self.paciente_data.get('data_nascimento', 'N/A') if self.paciente_data else 'N/A'}
Email:      {self.paciente_data.get('email', 'N/A') if self.paciente_data else 'N/A'}
Contacto:   {self.paciente_data.get('contacto', 'N/A') if self.paciente_data else 'N/A'}

📄 DOCUMENTO PDF: {template_data['nome'].upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 INFORMAÇÕES DO ARQUIVO:
• Nome: {template_data['nome']}
• Tipo: Protocolo/Orientação em PDF
• Tamanho: {template_data.get('tamanho', 'N/A')}
• Categoria: {template_data.get('categoria', 'N/A').title()}

📋 AÇÕES DISPONÍVEIS:
• 👁️  Visualizar PDF no visualizador integrado
• 📧 Enviar por email ao paciente  
• 📝 Registar no histórico clínico
• 💾 Guardar cópia no sistema

⚡ PRÓXIMO PASSO:
   Clica "📤 Enviar e Registar" para abrir o PDF
   no visualizador integrado e enviar ao paciente.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              🔒 Documento confidencial e personalizado              
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.template_preview.setPlainText(preview_pdf)
        print(f"[PDF] ✅ Preview PDF criado para: {template_data['nome']}")
    
    def _mostrar_preview_texto(self, template_data):
        """Mostra preview para templates de texto"""
        # Mostrar preview limpo e profissional
        try:
            # Tentar usar o sistema de templates externos primeiro
            try:
                from template_manager import BiodeskTemplateManager
                template_manager = BiodeskTemplateManager()
                preview = template_manager.create_template_preview(template_data, self.paciente_data)
                self.template_preview.setPlainText(preview)
                print(f"[TEMPLATE] ✅ Preview criado com template manager")
            except ImportError:
                # Fallback para sistema de preview limpo
                nome_paciente = self.paciente_data.get('nome', 'N/A') if self.paciente_data else 'N/A'
                template_texto = template_data.get('texto', '')
                nome_template = template_data.get('nome', 'Template')
                data_atual = datetime.now().strftime('%d/%m/%Y')
                
                # Preview limpo e elegante
                preview_limpo = f"""
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
                    🩺 PRESCRIÇÃO MÉDICA                    
                                                          
     [LOGO]            Dr. Nuno Correia                   
    Biodesk         Medicina Integrativa                  
                  & Análise Iridológica                   
                                                          
📧 geral@nunocorreia.pt     📞 (+351) 123 456 789         
🌐 www.nunocorreia.pt                   Data: {data_atual}    
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌

📋 DADOS DO PACIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nome:       {nome_paciente}
Data Nasc:  {self.paciente_data.get('data_nascimento', 'N/A') if self.paciente_data else 'N/A'}
Email:      {self.paciente_data.get('email', 'N/A') if self.paciente_data else 'N/A'}
Contacto:   {self.paciente_data.get('contacto', 'N/A') if self.paciente_data else 'N/A'}

📝 PRESCRIÇÃO: {nome_template.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 CONTEÚDO:
{template_texto[:300]}{'...' if len(template_texto) > 300 else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍⚕️ Dr. Nuno Correia - Medicina Integrativa
Documento gerado pelo Sistema Biodesk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                
                self.template_preview.setPlainText(preview_limpo)
                print(f"[TEMPLATE] ✅ Preview criado com sistema fallback")
                
            except Exception as e:
                # Fallback final - preview muito simples
                print(f"[DEBUG] Erro ao criar preview: {e}")
                
                nome_paciente = self.paciente_data.get('nome', 'N/A') if self.paciente_data else 'N/A'
                preview_simples = f"""
══════════════════════════════════════════════════════════════════════
                     🩺 PRESCRIÇÃO MÉDICA
                        Dr. Nuno Correia
                     Medicina Integrativa
══════════════════════════════════════════════════════════════════════

PACIENTE: {nome_paciente}
TEMPLATE: {template_data.get('nome', 'N/A')}

CONTEÚDO:
{template_data['texto'][:150]}{'...' if len(template_data['texto']) > 150 else ''}

Dr. Nuno Correia - Medicina Integrativa
                """.strip()
                self.template_preview.setPlainText(preview_simples)
            
        except Exception as e:
            # Fallback final se tudo falhar
            print(f"[DEBUG] Erro crítico no preview: {e}")
            self.template_preview.setPlainText("Erro ao carregar preview do template")
            
        # Guardar informações do template atual para uso nas anotações
        self.nome_template_atual = template_data.get('nome', item.text())
        self.categoria_template_atual = getattr(self, 'categoria_selecionada', 'Template')

    def _inserir_na_sessao_do_dia(self, conteudo):
        """Insere conteúdo na sessão do dia atual, criando uma se necessário"""
        from datetime import datetime
        
        data_hoje = datetime.today().strftime('%d/%m/%Y')
        
        # Verificar se já existe sessão hoje
        existe, _ = self._data_ja_existe_no_historico(data_hoje)
        
        if not existe:
            # Criar nova sessão do dia (como se premisse o botão 📅)
            prefixo = f'<b>{data_hoje}</b><br><hr style="border: none; border-top: 1px solid #bbb; margin: 10px 6px;">'
            html_atual = self.historico_edit.toHtml()
            novo_html = f'{prefixo}<div></div>{html_atual}'
            self.historico_edit.setHtml(novo_html)
            
            # Scroll para o topo
            v_scroll = self.historico_edit.verticalScrollBar()
            if v_scroll is not None:
                v_scroll.setValue(0)
        
        # Inserir o conteúdo DENTRO da sessão atual (após a data, mas antes da próxima linha separadora)
        cursor = self.historico_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Encontrar a primeira data (hoje) e posicionar logo após ela
        cursor.movePosition(QTextCursor.MoveOperation.Down)  # Linha da data
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)  # Final da linha da data
        
        # Inserir o conteúdo logo após a data, DENTRO da sessão
        cursor.insertHtml(f"<br>{conteudo}")
        self.historico_edit.setTextCursor(cursor)

    def aplicar_template_historico(self):
        """Aplica o template selecionado ao histórico clínico com data/hora"""
        template_texto = self.template_preview.toPlainText()
        if not template_texto:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um template primeiro!")
            return
            
        # Obter informações do template atual
        categoria_atual = getattr(self, 'categoria_template_atual', 'Template')
        nome_template = getattr(self, 'nome_template_atual', 'Sem nome')
        
        # Criar anotação com data/hora em HTML limpo
        from datetime import datetime
        agora = datetime.now()
        hora = agora.strftime("%H:%M")
        
        # Formato HTML limpo com itálico para diferenciar
        anotacao = f"<p><strong><em>📋 [{hora}] Prescrito: {categoria_atual} - {nome_template}</em></strong></p>"
        anotacao += f"<p><em>{template_texto.replace(chr(10), '<br>')}</em></p>"
        
        # Inserir na sessão do dia atual
        self._inserir_na_sessao_do_dia(anotacao)
        
        from biodesk_dialogs import mostrar_informacao
        mostrar_informacao(self, "Template Anotado", f"Template '{nome_template}' anotado na sessão de hoje!")

    def enviar_e_anotar_template(self):
        """Nova função: Enviar template ao paciente com PDF anexo E anotar no histórico"""
        template_texto = self.template_preview.toPlainText()
        if not template_texto or "Selecione um template" in template_texto:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um template primeiro!")
            return
            
        # Verificar se há paciente carregado
        if not hasattr(self, 'paciente_data') or not self.paciente_data:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Selecione um paciente primeiro!")
            return
            
        # Verificar se paciente tem email
        patient_email = self.paciente_data.get('email', '').strip()
        if not patient_email:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Paciente não tem email configurado.\n\nPor favor, adicione um email na ficha do paciente.")
            return
        
        # Obter template selecionado atualmente
        item_atual = self.lista_templates.currentItem()
        if not item_atual:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Nenhum template selecionado!")
            return
        
        template_data = item_atual.data(Qt.ItemDataRole.UserRole)
        if not template_data:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Dados do template inválidos!")
            return
        
        # Verificar se é PDF
        if template_data.get('tipo') == 'pdf':
            self._enviar_pdf_template(template_data)
        else:
            self._enviar_texto_template(template_data)
    
    def _enviar_pdf_template(self, template_data):
        """Envia template PDF"""
        try:
            from pdf_viewer import mostrar_pdf
            import os
            from biodesk_dialogs import mostrar_confirmacao, mostrar_sucesso, mostrar_erro
            
            pdf_path = template_data.get('arquivo')
            nome_template = template_data.get('nome')
            
            if not pdf_path or not os.path.exists(pdf_path):
                mostrar_erro(self, "❌ Erro", f"Arquivo PDF não encontrado:\n{pdf_path}")
                return
            
            # Confirmar envio
            confirmacao = mostrar_confirmacao(self, "📧 Confirmar Envio PDF", 
                                            f"Enviar PDF '{nome_template}' ao paciente?\n\n"
                                            f"👤 Paciente: {self.paciente_data.get('nome')}\n"
                                            f"📧 Email: {self.paciente_data.get('email')}\n"
                                            f"📄 Arquivo: {os.path.basename(pdf_path)}\n"
                                            f"📊 Tamanho: {template_data.get('tamanho', 'N/A')}")
            
            if confirmacao:
                # 1. Mostrar PDF no visualizador integrado
                print(f"📄 [PDF] Abrindo no visualizador: {pdf_path}")
                mostrar_pdf(pdf_path)
                
                # 2. Enviar por email (simulação por enquanto)
                # TODO: Implementar envio real
                
                # 3. Registar no histórico
                self._registar_pdf_historico(template_data)
                
                mostrar_sucesso(self, "✅ Sucesso", 
                              f"PDF '{nome_template}' processado com sucesso!\n\n"
                              f"✅ Visualizador aberto\n"
                              f"✅ Registado no histórico\n"
                              f"📧 Email preparado (implementar envio)")
        
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "❌ Erro", f"Erro ao processar PDF:\n{e}")
    
    def _enviar_texto_template(self, template_data):
        """Envia template de texto (método original)"""
        # Obter informações do template atual
        categoria_atual = getattr(self, 'categoria_template_atual', 'Template')
        nome_template = template_data.get('nome', 'Sem nome')
        
        # Verificar se há múltiplos templates selecionados para anexo
        templates_selecionados = self.get_templates_selecionados_para_anexo()
        
        if templates_selecionados:
            # Mostrar confirmação com informação sobre múltiplos PDFs
            num_templates = len(templates_selecionados)
            from biodesk_dialogs import mostrar_confirmacao
            if mostrar_confirmacao(self, "Confirmar Envio com Múltiplos PDFs", 
                                 f"Confirma o envio de {num_templates} template(s) ao paciente?\n\n"
                                 f"📧 Será enviado para: {patient_email}\n"
                                 f"📄 Inclui {num_templates} PDF(s) profissional(is) anexo(s)\n"
                                 f"📝 Será anotado no histórico clínico",
                                 "✅ Enviar PDFs", "❌ Cancelar"):
                
                try:
                    # Gerar múltiplos PDFs e enviar email
                    self.enviar_multiplos_templates_pdf(templates_selecionados)
                    
                    # Anotar no histórico
                    self._anotar_templates_enviados_sessao(templates_selecionados, com_pdf=True)
                    
                    from biodesk_dialogs import mostrar_sucesso
                    mostrar_sucesso(self, "Sucesso Completo!", 
                                   f"✅ {num_templates} template(s) enviado(s) com PDF(s) anexo(s)!\n\n"
                                   f"📧 Email enviado para: {patient_email}\n"
                                   f"📄 {num_templates} PDF(s) profissional(is) anexado(s)\n"
                                   f"📝 Anotado no histórico clínico")
                    
                except Exception as e:
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(self, "Erro no Envio", f"❌ Erro ao enviar templates com PDFs:\n\n{str(e)}")
                    print(f"[DEBUG] Erro envio múltiplos PDFs: {e}")
        else:
            # Envio de template único (comportamento original)
            from biodesk_dialogs import mostrar_confirmacao
            if mostrar_confirmacao(self, "Confirmar Envio com PDF & Anotação", 
                                 f"Confirma o envio do template '{nome_template}' ao paciente?\n\n"
                                 f"📧 Será enviado para: {patient_email}\n"
                                 f"📄 Inclui PDF profissional anexo\n"
                                 f"📝 Será anotado no histórico clínico",
                                 "✅ Enviar com PDF", "❌ Cancelar"):
                
                try:
                    # 1. Gerar e enviar PDF único
                    self.enviar_prescricao_pdf()
                    
                    # 2. Anotar no histórico como "enviado com PDF" (na sessão do dia)
                    self._anotar_template_enviado_sessao(categoria_atual, nome_template, template_texto, com_pdf=True)
                    
                    from biodesk_dialogs import mostrar_sucesso
                    mostrar_sucesso(self, "Sucesso Completo!", 
                                   f"✅ Template '{nome_template}' enviado com PDF anexo!\n\n"
                                   f"📧 Email enviado para: {patient_email}\n"
                                   f"📄 PDF profissional anexado\n"
                                   f"📝 Anotado no histórico clínico")
                    
                except Exception as e:
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(self, "Erro no Envio", f"❌ Erro ao enviar template com PDF:\n\n{str(e)}")
                    print(f"[DEBUG] Erro envio PDF: {e}")
    
    def get_templates_selecionados_para_anexo(self):
        """Retorna lista de templates selecionados para anexo múltiplo"""
        # Por enquanto retorna lista vazia - esta funcionalidade pode ser implementada
        # no futuro com checkboxes na interface para selecionar múltiplos templates
        return []
    
    def enviar_multiplos_templates_pdf(self, templates_list):
        """Gera múltiplos PDFs e envia como anexos"""
        try:
            import tempfile
            import os
            from datetime import datetime
            from pdf_template_professional import BiodeskPDFTemplate
            
            # Verificar se paciente tem email
            patient_email = self.paciente_data.get('email', '').strip()
            if not patient_email:
                raise Exception("Paciente não tem email configurado")
            
            # Criar diretório temporário para PDFs
            temp_dir = tempfile.mkdtemp()
            pdf_paths = []
            
            try:
                # Gerar PDF para cada template
                for template_info in templates_list:
                    categoria = template_info['categoria']
                    nome = template_info['nome']
                    conteudo = template_info['conteudo']
                    
                    # Nome do arquivo PDF
                    nome_arquivo = f"{categoria}_{nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    pdf_path = os.path.join(temp_dir, nome_arquivo)
                    
                    # Gerar PDF profissional
                    pdf_generator = BiodeskPDFTemplate(self.paciente_data)
                    pdf_generator.gerar_prescricao(conteudo, pdf_path)
                    
                    pdf_paths.append(pdf_path)
                
                # ✅ USAR NOVO SISTEMA DE EMAIL PERSONALIZADO
                try:
                    from email_templates_biodesk import gerar_email_personalizado
                    
                    # Preparar conteúdo específico para múltiplas prescrições
                    nome_paciente = self.paciente_data.get('nome', 'Paciente')
                    
                    # Lista das prescrições
                    lista_prescricoes = chr(10).join([f"• {t['categoria']} - {t['nome']}" for t in templates_list])
                    nomes_templates_anexados = [t['nome'] for t in templates_list]
                    
                    conteudo_multiplas = f"""Seguem em anexo suas prescrições médicas conforme análise realizada:

{lista_prescricoes}

📄 Total de documentos: {len(templates_list)} PDFs profissionais
🩺 Baseado na sua avaliação clínica detalhada

Por favor, siga todas as orientações descritas nos documentos anexos. Cada protocolo foi cuidadosamente personalizado para as suas necessidades específicas.

Em caso de dúvidas sobre qualquer uma das prescrições, não hesite em contactar-me."""
                    
                    # Gerar email personalizado
                    email_personalizado = gerar_email_personalizado(
                        nome_paciente=nome_paciente,
                        templates_anexados=nomes_templates_anexados,
                        tipo_comunicacao="templates"
                    )
                    
                    # Usar email personalizado
                    assunto = email_personalizado['assunto']
                    corpo = email_personalizado['corpo']
                    
                    print(f"✅ [MÚLTIPLOS] Email personalizado gerado para {len(templates_list)} templates")
                    
                except ImportError:
                    # Fallback para email simples se sistema personalizado não disponível
                    print(f"⚠️ [MÚLTIPLOS] Sistema personalizado não disponível, usando email padrão")
                    
                    assunto = f"Prescrições Médicas - {self.paciente_data.get('nome', 'Paciente')}"
                    corpo = f"""Prezado(a) {self.paciente_data.get('nome', 'Paciente')},

Seguem em anexo suas prescrições médicas conforme análise realizada:

{chr(10).join([f"• {t['categoria']} - {t['nome']}" for t in templates_list])}

Por favor, siga todas as orientações descritas nos documentos.

Atenciosamente,
Dr. Nuno Correia
Medicina Integrativa"""
                
                # Enviar email com múltiplos anexos
                from email_sender import EmailSender
                email_sender = EmailSender()
                
                sucesso, mensagem = email_sender.send_email_with_attachments(
                    to_email=patient_email,
                    subject=assunto,
                    body=corpo,
                    attachment_paths=pdf_paths,
                    nome_destinatario=self.paciente_data.get('nome', 'Paciente')
                )
                
                if not sucesso:
                    raise Exception(f"Erro no envio do email: {mensagem}")
                
                # Mostrar PDF gerado (apenas o primeiro)
                if pdf_paths:
                    self.mostrar_pdf_gerado(pdf_paths[0])
                
            finally:
                # Limpar arquivos temporários após delay
                import threading
                def cleanup():
                    import time
                    time.sleep(5)  # Aguardar 5 segundos
                    try:
                        for pdf_path in pdf_paths:
                            if os.path.exists(pdf_path):
                                os.remove(pdf_path)
                        os.rmdir(temp_dir)
                    except:
                        pass
                
                threading.Thread(target=cleanup, daemon=True).start()
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao enviar múltiplos templates: {str(e)}")
    
    def mostrar_pdf_gerado(self, pdf_path):
        """Configura PDF para abertura externa (SEM PISCAR)"""
        try:
            import os
            if os.path.exists(pdf_path):
                # Guardar caminho do PDF e ativar botão
                self._ultimo_pdf_gerado = pdf_path
                
                if hasattr(self, 'btn_abrir_pdf_externo'):
                    self.btn_abrir_pdf_externo.setEnabled(True)
                    self.btn_abrir_pdf_externo.setText(f"🔍 Abrir: {os.path.basename(pdf_path)}")
                
                # Mostrar widget de PDF externo
                if hasattr(self, 'preview_stack'):
                    self.preview_stack.setCurrentIndex(1)  # Mostrar widget PDF externo
                
                print(f"✅ [PDF] Configurado para abertura externa: {os.path.basename(pdf_path)}")
            else:
                print(f"❌ [PDF] Arquivo não encontrado: {pdf_path}")
                
        except Exception as e:
            print(f"❌ [PDF] Erro ao configurar: {e}")
            
    def _anotar_template_enviado_sessao(self, categoria, nome, conteudo, com_pdf=False):
        """Anota no histórico que o template foi enviado ao paciente (na sessão do dia)"""
        from datetime import datetime
        agora = datetime.now()
        hora = agora.strftime("%H:%M")
        
        # Formato HTML limpo com itálico para diferenciar
        if com_pdf:
            anotacao = f"<p><strong><em>📤📄 [{hora}] Enviado ao paciente com PDF anexo: {categoria} - {nome}</em></strong></p>"
        else:
            anotacao = f"<p><strong><em>📤 [{hora}] Enviado ao paciente: {categoria} - {nome}</em></strong></p>"
        
        anotacao += f"<p><em>{conteudo.replace(chr(10), '<br>')}</em></p>"
        
        # Inserir na sessão do dia atual
        self._inserir_na_sessao_do_dia(anotacao)
        
    def _anotar_templates_enviados_sessao(self, templates_list, com_pdf=False):
        """Anota no histórico que múltiplos templates foram enviados ao paciente"""
        from datetime import datetime
        agora = datetime.now()
        hora = agora.strftime("%H:%M")
        
        # Formato HTML limpo para múltiplos templates
        if com_pdf:
            anotacao = f"<p><strong><em>📤📄 [{hora}] Enviados {len(templates_list)} template(s) ao paciente com PDFs anexos:</em></strong></p>"
        else:
            anotacao = f"<p><strong><em>📤 [{hora}] Enviados {len(templates_list)} template(s) ao paciente:</em></strong></p>"
        
        anotacao += "<ul>"
        for template in templates_list:
            categoria = template.get('categoria', 'Template')
            nome = template.get('nome', 'Sem nome')
            anotacao += f"<li><em>{categoria} - {nome}</em></li>"
        anotacao += "</ul>"
        
        # Inserir na sessão do dia atual
        self._inserir_na_sessao_do_dia(anotacao)
        
    def _preparar_envio_comunicacao(self, categoria, nome, conteudo):
        """Prepara o template para envio na aba Centro de Comunicação"""
        # Mudar para a aba Centro de Comunicação
        self.clinico_comunicacao_tabs.setCurrentWidget(self.sub_centro_comunicacao)
        
        # Preparar o texto para envio
        assunto = f"Prescrição: {categoria} - {nome}"
        mensagem = f"Olá!\n\nSegue a sua prescrição de {categoria.lower()}:\n\n"
        mensagem += f"📋 {nome}\n\n"
        mensagem += conteudo + "\n\n"
        mensagem += "Cumprimentos,\n[Seu Nome]"
        
        # Preencher os campos na aba de comunicação
        if hasattr(self, 'assunto_edit'):
            self.assunto_edit.setText(assunto)
        if hasattr(self, 'mensagem_edit'):
            self.mensagem_edit.setPlainText(mensagem)
            
        # Destacar que foi preenchido automaticamente
        from biodesk_dialogs import mostrar_informacao
        mostrar_informacao(self, "Template Preparado", 
                         f"Template transferido para o Centro de Comunicação!\n\n"
                         f"Assunto: {assunto}\n\n"
                         f"Pode agora enviar por email.")

    def _simular_envio_template(self, categoria, nome, conteudo):
        """Simula o envio do template (futuramente integrar com email)"""
        # Esta função pode ser removida ou usada para logging
        print(f"📤 Template preparado para envio: {categoria} - {nome}")
        
    def _anotar_template_enviado(self, categoria, nome, conteudo):
        """Função antiga - substituída por _anotar_template_enviado_sessao"""
        # Mantida para compatibilidade, mas agora chama a nova função
        self._anotar_template_enviado_sessao(categoria, nome, conteudo)

    def importar_template_externo(self):
        """Importa um template de arquivo externo"""
        try:
            from template_manager import BiodeskTemplateManager
            from PyQt6.QtWidgets import QFileDialog
            from biodesk_dialogs import mostrar_sucesso, mostrar_erro, mostrar_aviso
            
            # Abrir diálogo para selecionar arquivo
            arquivo, _ = QFileDialog.getOpenFileName(
                self,
                "Importar Template",
                "",
                "Arquivos de Template (*.json);;Todos os Arquivos (*)"
            )
            
            if arquivo:
                template_manager = BiodeskTemplateManager()
                sucesso = template_manager.import_template_from_file(arquivo)
                
                if sucesso:
                    mostrar_sucesso(self, "Template Importado", 
                                  f"Template importado com sucesso de:\n{arquivo}")
                    # Recarregar lista de templates
                    self.carregar_templates()
                else:
                    mostrar_erro(self, "Erro na Importação", 
                               "Não foi possível importar o template.\nVerifique se o arquivo é válido.")
                    
        except ImportError:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Sistema Indisponível", 
                        "Sistema de importação de templates não disponível.")
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro na Importação", f"Erro ao importar template:\n{e}")
    
    def exportar_template_selecionado(self):
        """Exporta o template selecionado para arquivo"""
        try:
            from biodesk_dialogs import mostrar_sucesso, mostrar_erro, mostrar_aviso
            
            item_atual = self.lista_templates.currentItem()
            if not item_atual:
                mostrar_aviso(self, "Nenhum Template Selecionado", 
                            "Por favor, selecione um template para exportar.")
                return
            
            template_data = item_atual.data(Qt.ItemDataRole.UserRole)
            if not template_data:
                mostrar_erro(self, "Erro nos Dados", "Dados do template não encontrados.")
                return
            
            from template_manager import BiodeskTemplateManager
            from PyQt6.QtWidgets import QFileDialog
            
            # Criar nome sugerido do arquivo
            nome_template = template_data.get('nome', 'template')
            nome_arquivo_sugerido = f"{nome_template.replace(' ', '_').lower()}_template.json"
            
            # Abrir diálogo para salvar arquivo
            arquivo, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Template",
                nome_arquivo_sugerido,
                "Arquivos de Template (*.json);;Todos os Arquivos (*)"
            )
            
            if arquivo:
                template_manager = BiodeskTemplateManager()
                sucesso = template_manager.export_template_to_file(template_data, arquivo)
                
                if sucesso:
                    mostrar_sucesso(self, "Template Exportado", 
                                  f"Template exportado com sucesso para:\n{arquivo}")
                else:
                    mostrar_erro(self, "Erro na Exportação", 
                               "Não foi possível exportar o template.")
                    
        except ImportError:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Sistema Indisponível", 
                        "Sistema de exportação de templates não disponível.")
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro na Exportação", f"Erro ao exportar template:\n{e}")

    def editar_template(self):
        """Edita o template selecionado"""
        from biodesk_dialogs import mostrar_informacao
        mostrar_informacao(self, "Editar Template", "Funcionalidade em desenvolvimento")

    def duplicar_template(self):
        """Duplica o template selecionado"""
        from biodesk_dialogs import mostrar_informacao
        mostrar_informacao(self, "Duplicar Template", "Funcionalidade em desenvolvimento")

    def apagar_template(self):
        """Apaga o template selecionado"""
        from biodesk_dialogs import mostrar_informacao
        mostrar_informacao(self, "Apagar Template", "Funcionalidade em desenvolvimento")

    def criar_novo_template(self):
        """Abre o editor para criar um novo template editável"""
        try:
            from template_editavel import abrir_editor_template
            
            # Verificar se há paciente selecionado
            if not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "⚠️ Aviso", "Selecione um paciente para criar o template.")
                return
            
            # Abrir editor de template
            resultado = abrir_editor_template(self, self.paciente_data)
            
            if resultado:  # Se o template foi criado
                # Recarregar templates da categoria suplementos
                self.carregar_templates_categoria('suplementos')
                
                from biodesk_dialogs import mostrar_sucesso
                mostrar_sucesso(self, "✅ Sucesso", "Template criado com sucesso!")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "❌ Erro", f"Erro ao criar template:\n{e}")

    def gerar_pdf_template_personalizado(self, titulo, conteudo):
        """Gera PDF personalizado do template editável"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import cm
            import os
            from datetime import datetime
            
            # Nome do arquivo
            paciente_nome = self.paciente_data.get('nome', 'paciente').replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prescricao_{paciente_nome}_{timestamp}.pdf"
            pdf_path = os.path.join("documentos", filename)
            
            # Garantir que o diretório existe
            os.makedirs("documentos", exist_ok=True)
            
            # Criar PDF
            doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=2*cm)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Centrado
            )
            
            # Título
            title = Paragraph(titulo, title_style)
            story.append(title)
            story.append(Spacer(1, 0.5*cm))
            
            # Conteúdo (converter quebras de linha)
            linhas = conteudo.split('\n')
            for linha in linhas:
                if linha.strip():
                    para = Paragraph(linha, styles['Normal'])
                    story.append(para)
                else:
                    story.append(Spacer(1, 0.2*cm))
            
            # Construir PDF
            doc.build(story)
            
            # Mostrar PDF no visualizador integrado
            self.mostrar_pdf_gerado(pdf_path)
            
            return pdf_path
            
        except Exception as e:
            raise Exception(f"Erro ao gerar PDF: {e}")

    def _registar_pdf_historico(self, template_data):
        """Registra PDF no histórico do paciente"""
        try:
            nome_template = template_data.get('nome')
            categoria = template_data.get('categoria', 'orientacoes')
            
            # Criar entrada de histórico
            data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            entrada_historico = f"[{data_atual}] 📄 PDF: {nome_template} (Categoria: {categoria.title()})"
            
            # Adicionar ao histórico (implementação específica do sistema)
            print(f"📝 [HISTÓRICO] {entrada_historico}")
            
            # TODO: Implementar salvamento real no histórico do paciente
            
        except Exception as e:
            print(f"❌ Erro ao registar PDF no histórico: {e}")

    def testar_pdf_detox(self):
        """Testa o PDF de detox hepático diretamente"""
        try:
            from pdf_viewer import mostrar_pdf
            import os
            from biodesk_dialogs import mostrar_informacao, mostrar_erro
            
            # Caminho do PDF
            pdf_path = "templates/orientacoes/PROTOCOLO DE DETOX HEPÁTICO.pdf"
            
            if os.path.exists(pdf_path):
                print(f"🧪 [TESTE] Abrindo PDF: {pdf_path}")
                
                # Testar visualizador integrado
                mostrar_pdf(pdf_path)
                
                mostrar_informacao(self, "🧪 Teste PDF", 
                                 f"PDF testado com sucesso!\n\n"
                                 f"📄 Arquivo: PROTOCOLO DE DETOX HEPÁTICO\n"
                                 f"📁 Localização: {pdf_path}\n"
                                 f"📊 Tamanho: {os.path.getsize(pdf_path)} bytes\n\n"
                                 f"✅ Visualizador QtWebEngine executado!")
            else:
                mostrar_erro(self, "❌ Erro", 
                           f"PDF não encontrado!\n\n"
                           f"📁 Esperado em: {pdf_path}\n\n"
                           f"💡 Coloca o arquivo 'PROTOCOLO DE DETOX HEPÁTICO.pdf'\n"
                           f"na pasta templates/orientacoes/")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "❌ Erro no Teste", f"Erro ao testar PDF:\n{e}")

    def abrir_editor_avancado(self):
        """Abre o editor avançado de documentos com template atual carregado"""
        try:
            # Preparar dados do paciente
            dados_paciente = {}
            
            if hasattr(self, 'paciente_data') and self.paciente_data:
                dados_paciente = {
                    'nome': self.paciente_data.get('nome', ''),
                    'idade': self.paciente_data.get('idade', ''),
                    'data_nascimento': self.paciente_data.get('data_nascimento', ''),
                    'telefone': self.paciente_data.get('contacto', ''),  # Corrigido: 'contacto' em vez de 'telefone'
                    'email': self.paciente_data.get('email', ''),
                    'peso': self.paciente_data.get('peso', ''),
                    'altura': self.paciente_data.get('altura', ''),
                    'imc': self.paciente_data.get('imc', ''),
                    'pressao_arterial': self.paciente_data.get('pressao_arterial', ''),
                }
            
            # Verificar se há template selecionado
            template_atual = None
            if hasattr(self, 'template_selecionado') and self.template_selecionado:
                template_atual = self.template_selecionado
                print(f"📝 [EDITOR] Template atual para carregar: {template_atual.get('nome', 'Sem nome')}")
                print(f"🔍 [EDITOR] Dados completos do template: {template_atual}")
            else:
                print("⚠️ [EDITOR] Nenhum template selecionado encontrado")
            
            # Abrir editor com template pré-carregado
            print("📝 [DEBUG] Abrindo Editor Avançado de Documentos")
            # Import lazy para evitar inicialização prematura do QWebEngine
            from editor_documentos import EditorDocumentos
            editor = EditorDocumentos(dados_paciente, self, template_inicial=template_atual)
            
            # Maximizar janela do editor
            editor.showMaximized()
            print("🖥️ [EDITOR] Janela maximizada")
            
            # Manter referência para evitar garbage collection
            if not hasattr(self, 'editores_abertos'):
                self.editores_abertos = []
            self.editores_abertos.append(editor)
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            print(f"❌ [DEBUG] Erro ao abrir editor: {e}")
            import traceback
            traceback.print_exc()
            mostrar_erro(self, "❌ Erro", f"Erro ao abrir editor avançado:\n{e}")

    def mostrar_pdf_selecionado(self):
        """Mostra o PDF selecionado no visualizador integrado"""
        try:
            if not hasattr(self, 'template_selecionado') or not self.template_selecionado:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "⚠️ Aviso", "Nenhum template selecionado.")
                return
                
            template_data = self.template_selecionado
            
            # Verificar se é um PDF
            if template_data.get('tipo') != 'pdf':
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "⚠️ Aviso", "O template selecionado não é um PDF.")
                return
                
            arquivo_pdf = template_data.get('arquivo')
            if not arquivo_pdf:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "❌ Erro", "Caminho do arquivo PDF não encontrado.")
                return
                
            # Verificar se o arquivo existe
            from pathlib import Path
            if not Path(arquivo_pdf).exists():
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "❌ Erro", f"Arquivo PDF não encontrado:\n{arquivo_pdf}")
                return
                
            print(f"👁️ [DEBUG] Abrindo PDF: {arquivo_pdf}")
            
            # Mostrar PDF no visualizador integrado
            from pdf_viewer import mostrar_pdf
            mostrar_pdf(arquivo_pdf)
            
            print(f"✅ [DEBUG] PDF aberto com sucesso: {template_data.get('nome')}")
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            print(f"❌ [DEBUG] Erro ao mostrar PDF: {e}")
            import traceback
            traceback.print_exc()
            mostrar_erro(self, "❌ Erro", f"Erro ao abrir PDF:\n{e}")

    def gerar_documento_word(self):
        """Gera documento Word editável com dados do paciente"""
        try:
            # Verificar se há paciente selecionado
            if not hasattr(self, 'paciente_data') or not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "⚠️ Aviso", "Selecione um paciente primeiro.")
                return
                
            print("📝 [DEBUG] Iniciando geração de documento Word")
            
            # Preparar dados do paciente
            dados_paciente = {
                'nome': self.paciente_data.get('nome', '[Nome do Paciente]'),
                'idade': self.paciente_data.get('idade', '[Idade]'),
                'peso': self.paciente_data.get('peso', '[Peso]'),
                'altura': self.paciente_data.get('altura', '[Altura]'),
                'telefone': self.paciente_data.get('contacto', '[Telefone]'),
                'email': self.paciente_data.get('email', '[Email]'),
            }
            
            # Verificar se há template PDF selecionado para personalizar
            tipo_documento = "detox_hepatico"  # Padrão
            nome_base = "Protocolo_Detox_Hepatico"
            
            if hasattr(self, 'template_selecionado') and self.template_selecionado:
                template_data = self.template_selecionado
                if template_data.get('tipo') == 'pdf':
                    # Usar nome do PDF como base
                    nome_pdf = template_data.get('nome', 'Documento')
                    nome_base = nome_pdf.replace(' ', '_')
                    print(f"📄 [DEBUG] Baseado no PDF: {nome_pdf}")
            
            # Gerar documento Word
            from gerador_word import gerar_protocolo_detox
            from datetime import datetime
            
            # Nome do arquivo
            nome_paciente_limpo = dados_paciente['nome'].replace(' ', '_').replace('[', '').replace(']', '')
            data_str = datetime.now().strftime('%Y%m%d_%H%M')
            nome_arquivo = f"{nome_base}_{nome_paciente_limpo}_{data_str}.docx"
            
            print(f"📄 [DEBUG] Gerando arquivo: {nome_arquivo}")
            
            # Gerar documento
            arquivo_criado = gerar_protocolo_detox(dados_paciente, nome_arquivo)
            
            if arquivo_criado:
                # Perguntar o que fazer com o arquivo
                from PyQt6.QtWidgets import QMessageBox
                
                resposta = QMessageBox.question(
                    self,
                    "📝 Documento Word Criado",
                    f"Documento criado com sucesso!\n\n"
                    f"📄 Arquivo: {arquivo_criado}\n\n"
                    f"O que deseja fazer?",
                    QMessageBox.StandardButton.Open | 
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Open
                )
                
                if resposta == QMessageBox.StandardButton.Open:
                    # Abrir documento
                    try:
                        import os
                        os.startfile(arquivo_criado)
                        print(f"📂 [DEBUG] Documento aberto: {arquivo_criado}")
                    except Exception as e:
                        print(f"❌ [DEBUG] Erro ao abrir documento: {e}")
                        
                elif resposta == QMessageBox.StandardButton.Save:
                    # Salvar em local específico
                    from PyQt6.QtWidgets import QFileDialog
                    
                    novo_local, _ = QFileDialog.getSaveFileName(
                        self,
                        "💾 Salvar Documento Word",
                        arquivo_criado,
                        "Documentos Word (*.docx);;Todos os Arquivos (*)"
                    )
                    
                    if novo_local and novo_local != arquivo_criado:
                        import shutil
                        shutil.copy2(arquivo_criado, novo_local)
                        print(f"💾 [DEBUG] Documento salvo em: {novo_local}")
                
                from biodesk_dialogs import mostrar_sucesso
                mostrar_sucesso(
                    self,
                    "✅ Documento Word Criado",
                    f"Documento personalizado criado!\n\n"
                    f"📋 Paciente: {dados_paciente['nome']}\n"
                    f"📄 Arquivo: {arquivo_criado}\n\n"
                    f"💡 Agora pode:\n"
                    f"• Editar no Word\n"
                    f"• Salvar como PDF\n"
                    f"• Enviar por email\n"
                    f"• Imprimir diretamente"
                )
                
            else:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "❌ Erro", "Erro ao gerar documento Word.")
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            print(f"❌ [DEBUG] Erro ao gerar Word: {e}")
            import traceback
            traceback.print_exc()
            mostrar_erro(self, "❌ Erro", f"Erro ao gerar documento Word:\n{e}")

    def enviar_e_registrar_completo(self):
        """Workflow completo: Gerar Word → Converter PDF → Enviar Email → Registrar Histórico"""
        import os
        from datetime import datetime
        from PyQt6.QtCore import Qt
        
        # Definir cursor de carregamento no início
        self.setCursor(Qt.CursorShape.WaitCursor)
        
        try:
            print("🔄 [WORKFLOW] Iniciando processo completo")
            
            # Verificar se há paciente selecionado
            if not hasattr(self, 'paciente_data') or not self.paciente_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "⚠️ Aviso", "Selecione um paciente primeiro.")
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return
                
            # Verificar se há template selecionado
            if not hasattr(self, 'template_selecionado') or not self.template_selecionado:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "⚠️ Aviso", "Selecione um template primeiro.")
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return
                
            # 1. GERAR DOCUMENTO WORD
            print("📝 [WORKFLOW] Passo 1: Gerando documento Word")
            
            dados_paciente = {
                'nome': self.paciente_data.get('nome', '[Nome do Paciente]'),
                'idade': self.paciente_data.get('idade', '[Idade]'),
                'peso': self.paciente_data.get('peso', '[Peso]'),
                'altura': self.paciente_data.get('altura', '[Altura]'),
                'telefone': self.paciente_data.get('contacto', '[Telefone]'),
                'email': self.paciente_data.get('email', '[Email]'),
            }
            
            # Gerar documento Word
            from gerador_word import gerar_protocolo_detox
            from datetime import datetime
            import tempfile
            import os
            from pathlib import Path
            
            # ===== SISTEMA DE ORGANIZAÇÃO POR PACIENTE =====
            # Criar estrutura de pastas organizada por paciente
            nome_paciente_limpo = dados_paciente['nome'].replace(' ', '_').replace('[', '').replace(']', '')
            
            # Criar pasta base para documentos de pacientes
            pasta_pacientes = Path("Documentos_Pacientes")
            pasta_pacientes.mkdir(exist_ok=True)
            
            # Criar pasta específica do paciente
            pasta_paciente = pasta_pacientes / nome_paciente_limpo
            pasta_paciente.mkdir(exist_ok=True)
            
            # Criar subpastas organizadas
            (pasta_paciente / "Word").mkdir(exist_ok=True)
            (pasta_paciente / "PDF").mkdir(exist_ok=True)
            (pasta_paciente / "Emails").mkdir(exist_ok=True)
            
            print(f"📁 [ORGANIZAÇÃO] Estrutura criada: {pasta_paciente}")
            
            # Gerar nome do arquivo com timestamp
            data_str = datetime.now().strftime('%Y%m%d_%H%M')
            template_nome = self.template_selecionado.get('nome', 'Documento')
            nome_base = template_nome.replace(' ', '_')
            
            # Arquivo Word na pasta específica do paciente
            arquivo_word = pasta_paciente / "Word" / f"{nome_base}_{data_str}.docx"
            arquivo_criado = gerar_protocolo_detox(dados_paciente, str(arquivo_word))
            
            if not arquivo_criado:
                raise Exception("Erro ao gerar documento Word")
                
            print(f"✅ [WORKFLOW] Documento Word criado: {arquivo_criado}")
            
            # 2. CONVERTER PARA PDF
            print("📄 [WORKFLOW] Passo 2: Convertendo para PDF")
            
            # PDF na pasta específica do paciente
            arquivo_pdf = pasta_paciente / "PDF" / f"{nome_base}_{data_str}.pdf"
            pdf_convertido = False
            
            try:
                # Método 1: Tentar conversão usando win32com (se Word estiver instalado)
                print("🔄 [PDF] Tentando conversão com Microsoft Word...")
                from gerador_word import GeradorDocumentosWord
                gerador = GeradorDocumentosWord()
                pdf_convertido = gerador.converter_para_pdf(arquivo_criado, str(arquivo_pdf))
                
                if pdf_convertido:
                    print(f"✅ [PDF] Conversão bem-sucedida com Word: {pdf_convertido}")
                    arquivo_pdf = Path(pdf_convertido)  # Manter como Path object
                else:
                    raise Exception("Word não conseguiu converter")
                    
            except Exception as word_error:
                print(f"⚠️ [PDF] Word falhou: {word_error}")
                
                try:
                    # Método 2: Tentar com docx2pdf (biblioteca Python)
                    print("🔄 [PDF] Tentando conversão com docx2pdf...")
                    
                    # Verificar se docx2pdf está disponível
                    try:
                        from docx2pdf import convert
                        convert(arquivo_criado, str(arquivo_pdf))
                        
                        if arquivo_pdf.exists():
                            print(f"✅ [PDF] Conversão bem-sucedida com docx2pdf: {arquivo_pdf}")
                            pdf_convertido = True
                        else:
                            raise Exception("PDF não foi criado")
                            
                    except ImportError:
                        print("📦 [PDF] docx2pdf não encontrado - usando arquivo Word")
                        raise Exception("docx2pdf não instalado")
                            
                except Exception as pdf_error:
                    print(f"❌ [PDF] Conversão docx2pdf falhou: {pdf_error}")
                    
                    # Método 3: Fallback - NÃO usar arquivo Word, mostrar erro
                    print("❌ [WORKFLOW] Conversão para PDF falhou completamente")
                    
                    # Mostrar aviso ao usuário
                    from biodesk_styled_dialogs import BiodeskMessageBox
                    resposta = BiodeskMessageBox.question(
                        self, 
                        "⚠️ Problema na Conversão PDF", 
                        "Não foi possível converter o documento para PDF.\n\n"
                        "Deseja enviar o documento Word em vez do PDF?\n"
                        "Nota: O destinatário poderá editar o documento Word."
                    )
                    
                    if resposta:
                        arquivo_pdf = Path(arquivo_criado)
                        print("⚠️ [WORKFLOW] Usuário escolheu enviar arquivo Word")
                    else:
                        print("🚫 [WORKFLOW] Usuário cancelou envio - só PDF é aceitável")
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                        return
            
            if pdf_convertido and str(arquivo_pdf).endswith('.pdf'):
                print(f"🎉 [PDF] Documento convertido para PDF: {arquivo_pdf}")
            else:
                print(f"📝 [DOC] Usando documento Word: {arquivo_pdf}")
                
            # Log da organização final
            print(f"📂 [ORGANIZAÇÃO] Arquivo salvo em: {arquivo_pdf.parent}")
            print(f"📄 [ORGANIZAÇÃO] Nome final: {arquivo_pdf.name}")
                
            # 3. CONFIGURAR E ENVIAR EMAIL
            print("✉️ [WORKFLOW] Passo 3: Preparando email")
            
            # Verificar se há dados de email
            email_destino = self.paciente_data.get('email')
            email_enviado_sucesso = False
            
            if email_destino:
                try:
                    print(f"📧 [WORKFLOW] Enviando email para: {email_destino}")
                    
                    # Verificar se o arquivo existe antes de enviar
                    if not arquivo_pdf.exists():
                        raise Exception(f"Arquivo não encontrado: {arquivo_pdf}")
                        
                    # Verificar tamanho do arquivo
                    tamanho_arquivo = arquivo_pdf.stat().st_size
                    print(f"📏 [WORKFLOW] Tamanho do arquivo: {tamanho_arquivo:,} bytes ({tamanho_arquivo/1024:.1f} KB)")
                    
                    # ✅ USAR NOVO SISTEMA DE EMAIL PERSONALIZADO
                    try:
                        from email_templates_biodesk import gerar_email_personalizado
                        
                        # Preparar conteúdo específico para protocolo de tratamento
                        nome_paciente = dados_paciente['nome']
                        
                        conteudo_protocolo = f"""Em anexo encontra o seu protocolo de tratamento personalizado.

📋 Template aplicado: {template_nome}
📅 Data de criação: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
📄 Formato: {'PDF' if str(arquivo_pdf).endswith('.pdf') else 'Word'} anexo

Este documento foi gerado automaticamente pelo sistema Biodesk com base na sua análise clínica. Por favor, siga todas as orientações descritas no protocolo.

Em caso de dúvidas sobre o protocolo, não hesite em contactar-me."""
                        
                        # Gerar email personalizado
                        email_personalizado = gerar_email_personalizado(
                            nome_paciente=nome_paciente,
                            conteudo_principal=conteudo_protocolo,
                            assunto=f"Protocolo de Tratamento - {nome_paciente}"
                        )
                        
                        # Usar email personalizado
                        assunto = email_personalizado['assunto']
                        mensagem = email_personalizado['corpo']
                        
                        print(f"✅ [WORKFLOW] Email personalizado gerado com redes sociais")
                        
                    except ImportError:
                        # Fallback para email simples se sistema personalizado não disponível
                        print(f"⚠️ [WORKFLOW] Sistema personalizado não disponível, usando email padrão")
                        
                        assunto = f"Protocolo de Tratamento - {dados_paciente['nome']}"
                        mensagem = f"""
Caro(a) {dados_paciente['nome']},

Em anexo encontra o seu protocolo de tratamento personalizado.

Template: {template_nome}
Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Este documento foi gerado automaticamente pelo sistema Biodesk.

Cumprimentos,
Equipa Biodesk
                        """.strip()
                    
                    print(f"📝 [WORKFLOW] Assunto: {assunto}")
                    print(f"📄 [WORKFLOW] Arquivo a anexar: {arquivo_pdf.name}")
                    
                    # Importar e usar o sistema de email
                    from email_sender import EmailSender
                    email_sender = EmailSender()
                    
                    # Verificar configuração primeiro
                    if not email_sender.config.is_configured():
                        raise Exception("Sistema de email não configurado")
                    
                    # Enviar email com anexo
                    print("📤 [WORKFLOW] Iniciando envio...")
                    resultado, mensagem_result = email_sender.send_email_with_attachment(
                        to_email=email_destino,
                        subject=assunto,
                        body=mensagem,
                        attachment_path=str(arquivo_pdf)  # Converter para string
                    )
                    
                    print(f"📊 [WORKFLOW] Resultado do envio: {resultado}")
                    print(f"📋 [WORKFLOW] Detalhes: {mensagem_result}")
                    
                    if resultado:
                        email_enviado_sucesso = True
                        print("✅ [WORKFLOW] Email enviado com sucesso!")
                        print(f"ℹ️ [WORKFLOW] Detalhes: {mensagem_result}")
                        
                        # Criar log do email enviado
                        log_email = pasta_paciente / "Emails" / f"email_log_{data_str}.txt"
                        with open(log_email, 'w', encoding='utf-8') as f:
                            f.write(f"EMAIL ENVIADO - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                            f.write("=" * 50 + "\n")
                            f.write(f"Para: {email_destino}\n")
                            f.write(f"Assunto: {assunto}\n")
                            f.write(f"Anexo: {arquivo_pdf.name}\n")
                            f.write(f"Tamanho: {tamanho_arquivo:,} bytes\n")
                            f.write(f"Tipo: {'PDF' if str(arquivo_pdf).endswith('.pdf') else 'Word'}\n")
                            f.write(f"Status: {mensagem_result}\n")
                            f.write("\nMensagem:\n")
                            f.write(mensagem)
                        
                        print(f"📝 [EMAIL] Log criado: {log_email}")
                    else:
                        print("❌ [WORKFLOW] Falha no envio do email")
                        print(f"❌ [WORKFLOW] Erro: {mensagem_result}")
                        
                        # Mostrar erro detalhado ao usuário
                        from biodesk_styled_dialogs import BiodeskMessageBox
                        BiodeskMessageBox.warning(
                            self, 
                            "⚠️ Problema no Email", 
                            f"O email não foi enviado:\n{mensagem_result}\n\nO documento foi criado mas não foi enviado por email."
                        )
                        
                except Exception as e:
                    print(f"❌ [WORKFLOW] Erro ao enviar email: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                from biodesk_dialogs import mostrar_aviso
                resposta = mostrar_aviso(self, "⚠️ Email não encontrado", 
                                       "O paciente não tem email cadastrado.\n"
                                       "Deseja continuar apenas registrando no histórico?")
                if not resposta:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return
                
            # 4. REGISTRAR NO HISTÓRICO
            print("📋 [WORKFLOW] Passo 4: Registrando no histórico")
            
            try:
                # Criar entrada no histórico
                historico_entrada = {
                    'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'tipo': 'Documento Enviado',
                    'template': template_nome,
                    'arquivo': str(arquivo_pdf),  # Converter para string
                    'paciente': dados_paciente['nome'],
                    'email_enviado': email_enviado_sucesso,
                    'email_destino': email_destino or 'N/A'
                }
                
                # Adicionar ao histórico do paciente (implementar conforme necessário)
                self.registrar_documento_no_historico(historico_entrada)
                
                print("✅ [WORKFLOW] Registrado no histórico")
                
            except Exception as e:
                print(f"⚠️ [WORKFLOW] Erro ao registrar no histórico: {e}")
                
            # 5. MOSTRAR RESULTADO
            from biodesk_styled_dialogs import BiodeskMessageBox
            
            mensagem_resultado = f"""🎉 WORKFLOW COMPLETADO COM SUCESSO!

📋 Paciente: {dados_paciente['nome']}
📄 Template: {template_nome}
📁 Pasta: {pasta_paciente}
📝 Documento Word: {Path(arquivo_criado).name}
📄 Arquivo Final: {arquivo_pdf.name}

✅ Ações realizadas:
• Documento Word gerado com dados preenchidos
• Arquivo organizado na pasta do paciente
• {"PDF convertido automaticamente" if str(arquivo_pdf).endswith('.pdf') else "Arquivo Word preparado"}
• {"Email enviado com sucesso" if email_enviado_sucesso else "Email não enviado" if email_destino else "Email não disponível"}
• Registrado no histórico clínico

💡 Próximos passos:
• Arquivo está pronto para envio/impressão
• Registro adicionado ao histórico do paciente
• Documentos organizados por paciente"""
            
            # Mostrar mensagem de sucesso com estilo Biodesk
            BiodeskMessageBox.success(
                parent=self,
                title="🎉 Workflow Completo", 
                message="Processo completado com sucesso!",
                details=mensagem_resultado
            )
            
            # Perguntar se quer abrir o arquivo
            from biodesk_styled_dialogs import BiodeskMessageBox
            resposta = BiodeskMessageBox.question(
                parent=self,
                title="📂 Abrir Arquivo", 
                message="Deseja abrir o documento gerado?",
                details=f"📄 Arquivo: {arquivo_pdf.name}\n📁 Local: {arquivo_pdf.parent}"
            )
            
            if resposta:
                os.startfile(str(arquivo_pdf))
                
        except Exception as e:
            from biodesk_styled_dialogs import BiodeskMessageBox
            print(f"❌ [WORKFLOW] Erro no processo completo: {e}")
            import traceback
            traceback.print_exc()
            BiodeskMessageBox.critical(self, "❌ Erro no Workflow", f"Erro no processo completo:\n{e}")
        
        finally:
            # Restaurar cursor normal SEMPRE
            self.setCursor(Qt.CursorShape.ArrowCursor)
            print("🔄 [WORKFLOW] Cursor restaurado - processo finalizado")
            
    def registrar_documento_no_historico(self, entrada):
        """Registra documento no histórico do paciente"""
        try:
            print(f"📋 [HISTÓRICO] Registrando: {entrada}")
            
            # Integrar com sistema de histórico existente
            if hasattr(self, 'db') and self.db and hasattr(self, 'paciente_data'):
                paciente_id = self.paciente_data.get('id')
                if paciente_id:
                    # Formatear entrada para o histórico
                    texto_historico = f"""📄 DOCUMENTO ENVIADO
📋 Template: {entrada['template']}
📁 Arquivo: {entrada['arquivo']}
📧 Email: {'Enviado para ' + entrada['email_destino'] if entrada['email_enviado'] else 'Não enviado'}
📅 Data: {entrada['data']}"""
                    
                    # Adicionar ao histórico do paciente
                    self.db.adicionar_historico(paciente_id, texto_historico)
                    print(f"✅ [HISTÓRICO] Registrado na base de dados para paciente ID: {paciente_id}")
                else:
                    print("⚠️ [HISTÓRICO] ID do paciente não encontrado")
            else:
                print("⚠️ [HISTÓRICO] Sistema de BD não disponível")
            
        except Exception as e:
            print(f"❌ [HISTÓRICO] Erro ao registrar: {e}")
            import traceback
            traceback.print_exc()

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
            btn_cancelar.setStyleSheet("""
                QPushButton {
                    background: linear-gradient(135deg, #6c757d, #495057);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: linear-gradient(135deg, #495057, #343a40);
                }
            """)
            btn_cancelar.clicked.connect(dialog.reject)
            
            btn_usar = QPushButton("✨ Usar Template Personalizado")
            btn_usar.setFixedHeight(40)
            btn_usar.setStyleSheet("""
                QPushButton {
                    background: linear-gradient(135deg, #9C27B0, #7B1FA2);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: linear-gradient(135deg, #7B1FA2, #6A1B9A);
                }
            """)
            
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
    def init_sub_declaracao_saude(self):
        """Sub-aba: Declaração de Saúde (SISTEMA ORIGINAL RESTAURADO E CORRIGIDO)"""
        # Layout principal da sub-aba
        layout = QVBoxLayout(self.sub_declaracao_saude)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ====== CABEÇALHO ======
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2980b9;
                border-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        titulo_declaracao = QLabel("🩺 Declaração de Estado de Saúde")
        titulo_declaracao.setStyleSheet("""
            font-size: 18px; 
            font-weight: 700; 
            color: #ffffff;
            padding: 20px 15px;
        """)
        header_layout.addWidget(titulo_declaracao)
        
        header_layout.addStretch()
        
        # Status da declaração
        self.status_declaracao = QLabel("❌ Não preenchida")
        self.status_declaracao.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600;
            color: #ffffff;
            padding: 15px;
            background-color: rgba(255,255,255,0.2);
            border-radius: 6px;
        """)
        header_layout.addWidget(self.status_declaracao)
        
        layout.addWidget(header_frame)
        
        # ====== ÁREA PRINCIPAL DIVIDIDA ======
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        
        # ====== ESQUERDA: FORMULÁRIO ======
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(10)
        
        # ====== TEMPLATE HTML DA DECLARAÇÃO ======
        self.template_declaracao = self._criar_template_declaracao_saude()
        
        # WebEngine para a declaração com formulários interativos
        self.texto_declaracao_editor = QWebEngineView()
        self.texto_declaracao_editor.setMinimumHeight(400)
        self.texto_declaracao_editor.setMaximumHeight(600)
        self.texto_declaracao_editor.setHtml(self.template_declaracao)
        
        form_layout.addWidget(self.texto_declaracao_editor)
        
        main_layout.addWidget(form_frame, 2)
        
        # ====== DIREITA: AÇÕES ======
        acoes_frame = QFrame()
        acoes_frame.setFixedWidth(250)
        acoes_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
        """)
        acoes_layout = QVBoxLayout(acoes_frame)
        acoes_layout.setContentsMargins(20, 20, 20, 20)
        acoes_layout.setSpacing(12)
        acoes_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título das ações
        acoes_titulo = QLabel("⚡ Ações")
        acoes_titulo.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600; 
            color: #2c3e50; 
            margin-bottom: 10px;
            padding: 15px;
            background-color: #e9ecef;
            border-radius: 8px;
        """)
        acoes_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        acoes_layout.addWidget(acoes_titulo)
        
        # ====== BOTÕES CORRIGIDOS ======
        botoes_principais_layout = QVBoxLayout()
        botoes_principais_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        botoes_principais_layout.setSpacing(15)
        
        # Botão Assinar e Guardar (principal)
        btn_assinar_guardar_declaracao = QPushButton("✍️ Assinar e Guardar")
        btn_assinar_guardar_declaracao.setFixedSize(200, 50)
        btn_assinar_guardar_declaracao.setToolTip("Abre canvas de assinatura e gera PDF automaticamente")
        btn_assinar_guardar_declaracao.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        btn_assinar_guardar_declaracao.clicked.connect(self.assinar_e_guardar_declaracao_saude)
        botoes_principais_layout.addWidget(btn_assinar_guardar_declaracao)
        
        # Nota informativa
        nota_label = QLabel("� Use o botão acima para preencher, assinar e guardar a declaração automaticamente")
        nota_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 11px;
                font-style: italic;
                padding: 10px;
                text-align: center;
            }
        """)
        nota_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nota_label.setWordWrap(True)
        botoes_principais_layout.addWidget(nota_label)
        
        acoes_layout.addLayout(botoes_principais_layout)
        acoes_layout.addStretch()
        
        main_layout.addWidget(acoes_frame, 1)
        
        layout.addLayout(main_layout, 1)
        
        # Carregar dados existentes
        self.carregar_declaracao_saude()

    def carregar_declaracao_saude(self):
        """Carrega declaração de saúde - VERSÃO SIMPLIFICADA"""
        if not self.paciente_data:
            return
            
        try:
            # Aplicar sempre o novo template simplificado
            self.template_declaracao = self._criar_template_declaracao_saude()
            self.texto_declaracao_editor.setHtml(self.template_declaracao)
            
            # Status padrão
            self.status_declaracao.setText("❌ Não preenchida")
            self.status_declaracao.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 5px;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                }
            """)
            
            print("✅ Template simplificado aplicado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao carregar declaração: {e}")
            # Em caso de erro, criar template mínimo
            template_minimo = """
            <html><body style='font-family: Arial; padding: 20px;'>
            <h1 style='color: #4a9f4a; text-align: center;'>🌿 Declaração de Saúde 🌿</h1>
            <p style='text-align: center;'>Template simplificado carregado.</p>
            </body></html>
            """
            self.texto_declaracao_editor.setHtml(template_minimo)
            self.status_declaracao.setText("❌ Erro ao carregar")

    def _criar_template_declaracao_saude(self):
        """Cria template HTML SIMPLIFICADO com dropdowns"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Declaração de Saúde Simplificada</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f9f9f9; 
                    line-height: 1.6;
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }
                h1 { 
                    text-align: center; 
                    color: #2e7d2e; 
                    margin-bottom: 30px; 
                    font-size: 28px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                }
                h2 { 
                    color: #4a9f4a; 
                    border-bottom: 2px solid #4a9f4a; 
                    padding-bottom: 8px; 
                    margin-top: 30px; 
                }
                .patient-info { 
                    background-color: #f0f8f0; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin-bottom: 25px; 
                    border-left: 5px solid #4a9f4a;
                }
                .form-group { 
                    margin-bottom: 20px; 
                }
                .form-group label { 
                    display: block; 
                    margin-bottom: 8px; 
                    font-weight: bold; 
                    color: #2e7d2e; 
                }
                select, textarea, input[type="text"] { 
                    width: 100%; 
                    padding: 12px; 
                    border: 2px solid #4a9f4a; 
                    border-radius: 8px; 
                    font-size: 14px; 
                    box-sizing: border-box;
                    background-color: #fafcfa;
                }
                select:focus, textarea:focus, input:focus { 
                    border-color: #2e7d2e; 
                    outline: none; 
                    background-color: white;
                }
                .legal-text { 
                    background-color: #fff8dc; 
                    border: 2px solid #4a9f4a; 
                    border-radius: 10px; 
                    padding: 25px; 
                    margin: 30px 0; 
                    font-size: 14px; 
                    line-height: 1.8;
                }
                .signature-section { 
                    margin-top: 40px; 
                    border-top: 3px solid #4a9f4a; 
                    padding-top: 25px; 
                }
                .signature-row { 
                    display: grid; 
                    grid-template-columns: 1fr 1fr; 
                    gap: 40px; 
                    margin-top: 25px; 
                }
                .signature-box { 
                    text-align: center; 
                    border-bottom: 2px solid #2e7d2e; 
                    padding-bottom: 10px; 
                    margin-bottom: 10px; 
                    min-height: 50px; 
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌿 DECLARAÇÃO DE SAÚDE SIMPLIFICADA 🌿</h1>
                
                <div class="patient-info">
                    <div><strong>👤 Nome:</strong> [NOME_PACIENTE]</div>
                    <div><strong>📅 Data de Nascimento:</strong> [DATA_NASCIMENTO]</div>
                    <div><strong>📋 Data da Declaração:</strong> [DATA_ATUAL]</div>
                    <div><strong>🏥 Consultório:</strong> BioDesk Natural Health</div>
                </div>

                <h2>🌱 Histórico Médico</h2>
                
                <div class="form-group">
                    <label for="consulta-anterior">Já consultou algum naturopata anteriormente?</label>
                    <select id="consulta-anterior" name="consulta-anterior">
                        <option value="">Selecione...</option>
                        <option value="sim">Sim</option>
                        <option value="nao">Não</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="condicoes-saude">Tem alguma condição de saúde importante?</label>
                    <select id="condicoes-saude" name="condicoes-saude">
                        <option value="">Selecione...</option>
                        <option value="sim">Sim</option>
                        <option value="nao">Não</option>
                        <option value="nao-sei">Não sei</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="medicacao">Toma alguma medicação regularmente?</label>
                    <select id="medicacao" name="medicacao">
                        <option value="">Selecione...</option>
                        <option value="sim">Sim</option>
                        <option value="nao">Não</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="alergias">Tem alergias conhecidas?</label>
                    <select id="alergias" name="alergias">
                        <option value="">Selecione...</option>
                        <option value="sim">Sim</option>
                        <option value="nao">Não</option>
                        <option value="desconheco">Desconheço</option>
                    </select>
                </div>

                <h2>🍃 Estilo de Vida</h2>
                
                <div class="form-group">
                    <label for="exercicio">Pratica exercício físico regularmente?</label>
                    <select id="exercicio" name="exercicio">
                        <option value="">Selecione...</option>
                        <option value="sim-frequente">Sim, frequentemente</option>
                        <option value="sim-ocasional">Sim, ocasionalmente</option>
                        <option value="nao">Não</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="stress">Como avalia o seu nível de stress?</label>
                    <select id="stress" name="stress">
                        <option value="">Selecione...</option>
                        <option value="baixo">Baixo</option>
                        <option value="moderado">Moderado</option>
                        <option value="alto">Alto</option>
                        <option value="muito-alto">Muito Alto</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="sono">Como é a qualidade do seu sono?</label>
                    <select id="sono" name="sono">
                        <option value="">Selecione...</option>
                        <option value="excelente">Excelente</option>
                        <option value="bom">Bom</option>
                        <option value="regular">Regular</option>
                        <option value="mau">Mau</option>
                    </select>
                </div>

                <h2>💭 Informações Adicionais</h2>
                
                <div class="form-group">
                    <label for="motivo">Principal motivo da consulta:</label>
                    <textarea id="motivo" name="motivo" rows="3" placeholder="Descreva brevemente o que o trouxe à consulta..."></textarea>
                </div>

                <div class="form-group">
                    <label for="objetivos">O que espera alcançar com as terapias naturais?</label>
                    <textarea id="objetivos" name="objetivos" rows="3" placeholder="Descreva os seus objetivos..."></textarea>
                </div>

                <div class="form-group">
                    <label for="observacoes">Outras informações relevantes:</label>
                    <textarea id="observacoes" name="observacoes" rows="3" placeholder="Qualquer outra informação importante..."></textarea>
                </div>

                <div class="legal-text">
                    <h3 style="color: #2e7d2e; margin-top: 0;">🌿 DECLARAÇÃO E CONSENTIMENTO</h3>
                    <p><strong>DECLARO QUE:</strong></p>
                    <ul>
                        <li>Todas as informações prestadas são verdadeiras e completas</li>
                        <li>Compreendo que a naturopatia é complementar ao acompanhamento médico</li>
                        <li>Informarei imediatamente sobre alterações no meu estado de saúde</li>
                        <li>Autorizo o tratamento dos meus dados pessoais para fins terapêuticos (RGPD)</li>
                    </ul>
                </div>

                <div class="signature-section">
                    <h3>✍️ Assinaturas</h3>
                    <div class="signature-row">
                        <div>
                            <div class="signature-box"></div>
                            <p style="text-align: center; margin: 10px 0;"><strong>Assinatura do Paciente</strong></p>
                            <p style="text-align: center; margin: 0; font-size: 12px;">Data: [DATA_ATUAL]</p>
                        </div>
                        <div>
                            <div class="signature-box"></div>
                            <p style="text-align: center; margin: 10px 0;"><strong>Assinatura do Naturopata</strong></p>
                            <p style="text-align: center; margin: 0; font-size: 12px;">Data: [DATA_ATUAL]</p>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def guardar_declaracao_saude_completa(self):
        """Gera PDF completo da declaração de saúde com assinaturas"""
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF
            import os
            from datetime import datetime
            
            print(f"📋 [PDF] Gerando PDF da declaração de saúde...")
            
            # Obter dados do paciente
            if not self.paciente_data:
                BiodeskMessageBox.warning(self, "Aviso", "⚠️ Nenhum paciente selecionado.")
                return False
                
            paciente_id = self.paciente_data.get('id')
            nome_paciente = self.paciente_data.get('nome', 'N/A')
            data_nascimento = self.paciente_data.get('data_nascimento', 'N/A')
            
            # Criar diretório se não existir
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente.replace(' ', '_')}"
            os.makedirs(pasta_paciente, exist_ok=True)
            
            # Nome do arquivo PDF
            data_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"Declaracao_Saude_{nome_paciente.replace(' ', '_')}_{data_str}.pdf"
            caminho_pdf = os.path.join(pasta_paciente, nome_arquivo)
            
            # Criar documento para PDF
            document = QTextDocument()
            
            # Gerar HTML do template com dados do paciente
            html_content = self._criar_template_declaracao_saude()
            html_content = html_content.replace('[NOME_PACIENTE]', nome_paciente)
            html_content = html_content.replace('[DATA_NASCIMENTO]', str(data_nascimento))
            html_content = html_content.replace('[DATA_ATUAL]', datetime.now().strftime('%d/%m/%Y'))
            
            # Capturar dados do formulário se estiver preenchido
            try:
                # Tentar capturar dados via JavaScript se o WebView estiver ativo
                def processar_dados_form(dados):
                    nonlocal html_content  # Permitir modificação da variável externa
                    if dados:
                        # Adicionar dados preenchidos ao HTML
                        for campo, valor in dados.items():
                            if valor and valor != "":
                                # Substituir no HTML os valores selecionados
                                html_content = html_content.replace(
                                    f'<option value="{valor}">',
                                    f'<option value="{valor}" selected>'
                                )
                    
                    # Definir conteúdo do documento
                    document.setHtml(html_content)
                    
                    # Configurar impressora/PDF
                    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                    printer.setOutputFileName(caminho_pdf)
                    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                    printer.setPageLayout(QPageLayout(
                        QPageSize(QPageSize.PageSizeId.A4),
                        QPageLayout.Orientation.Portrait,
                        QMarginsF(15, 15, 15, 15)  # margens em mm
                    ))
                    
                    # Gerar PDF
                    document.print(printer)
                    
                    print(f"✅ [PDF] Declaração guardada: {caminho_pdf}")
                    BiodeskMessageBox.information(self, "Sucesso", 
                                                f"✅ Declaração de saúde guardada com sucesso!\n\n📁 {caminho_pdf}")
                    return True
                
                # Tentar capturar dados do formulário
                if hasattr(self, 'texto_declaracao_editor'):
                    js_code = """
                    function capturarDados() {
                        var dados = {};
                        var selects = document.querySelectorAll('select');
                        for(var i = 0; i < selects.length; i++) {
                            var sel = selects[i];
                            if(sel.value) dados[sel.name || sel.id] = sel.value;
                        }
                        var textareas = document.querySelectorAll('textarea');
                        for(var i = 0; i < textareas.length; i++) {
                            var ta = textareas[i];
                            if(ta.value) dados[ta.name || ta.id] = ta.value;
                        }
                        return dados;
                    }
                    capturarDados();
                    """
                    self.texto_declaracao_editor.page().runJavaScript(js_code, processar_dados_form)
                else:
                    # Fallback: gerar PDF sem dados específicos
                    processar_dados_form({})
                    
            except Exception as e:
                print(f"⚠️ [PDF] Erro ao capturar dados do formulário: {e}")
                # Gerar PDF básico mesmo sem dados
                document.setHtml(html_content)
                
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(caminho_pdf)
                printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                
                document.print(printer)
                print(f"✅ [PDF] Declaração básica guardada: {caminho_pdf}")
                BiodeskMessageBox.information(self, "Sucesso", 
                                            f"✅ Declaração de saúde guardada!\n\n📁 {caminho_pdf}")
                return True
                
        except Exception as e:
            print(f"❌ [PDF] Erro ao gerar PDF: {e}")
            BiodeskMessageBox.critical(self, "Erro", f"❌ Erro ao gerar PDF da declaração:\n\n{str(e)}")
            return False

    def init_sub_consentimentos(self):
        """Sub-aba: Consentimentos (CÓDIGO COMPLETO MIGRADO)"""
        # Usar exatamente o mesmo código excelente que já existia
        layout = QVBoxLayout(self.sub_consentimentos)
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
        scroll_layout.setSpacing(8)  # Espaçamento adequado entre consentimentos
        scroll_layout.setContentsMargins(0, 8, 8, 8)  # Margem esquerda removida para alinhamento
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Alinhar à esquerda
        
        # Tipos de consentimento com cores pastéis elegantes
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
            
            # Botão direto no layout - ESTILO IGUAL AOS TEMPLATES
            btn = QPushButton(nome)
            btn.setCheckable(True)
            btn.setFixedSize(220, 45)  # Largura reduzida para permitir alinhamento à esquerda
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 13px !important;
                    font-weight: 600 !important;
                    border: none !important;
                    border-radius: 8px !important;
                    padding: 10px 15px !important;
                    background-color: {cor} !important;
                    color: #2c3e50 !important;
                    text-align: left !important;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(cor, 15)} !important;
                    color: #2c3e50 !important;
                }}
                QPushButton:checked {{
                    background-color: {self._lighten_color(cor, 25)} !important;
                    color: #2c3e50 !important;
                }}
            """)
            btn.clicked.connect(lambda checked, t=tipo: self.selecionar_tipo_consentimento(t))
            self.botoes_consentimento[tipo] = btn
            scroll_layout.addWidget(btn)
        
        # Adicionar stretch ao final para alinhamento superior
        scroll_layout.addStretch()
        
        # Conectar o scroll_widget ao scroll_area
        scroll_area.setWidget(scroll_widget)
        
        # Adicionar o scroll_area ao status_layout
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
        self._style_text_edit(self.editor_consentimento)
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

        main_horizontal_layout.addWidget(centro_frame, 1)  # Expandir no centro
        
        # ====== 3. DIREITA: BOTÕES DE AÇÃO (SEM FRAME) ======
        # Layout vertical para botões diretamente no layout principal
        acoes_layout = QVBoxLayout()
        acoes_layout.setContentsMargins(15, 10, 15, 10)  # Margens externas
        acoes_layout.setSpacing(8)  # Espaçamento reduzido entre botões
        acoes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # ====== BOTÕES DE AÇÕES UNIFORMES ======
        # Todos os botões com ícone + texto, tamanho uniforme
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedSize(160, 30)
        btn_guardar.setToolTip("Guardar Consentimento e Adicionar aos Documentos")
        self._style_modern_button(btn_guardar, "#28a745")  # Verde (sucesso)
        btn_guardar.clicked.connect(self.guardar_consentimento_completo)  # Nova função integrada
        acoes_layout.addWidget(btn_guardar)
        
        # Separador visual
        acoes_layout.addSpacing(15)
        
        btn_limpar = QPushButton("🗑️ Limpar")
        btn_limpar.setFixedSize(160, 30)
        btn_limpar.setToolTip("Limpar Consentimento")
        self._style_modern_button(btn_limpar, "#dc3545")  # Vermelho (danger)
        btn_limpar.clicked.connect(self.limpar_consentimento)
        acoes_layout.addWidget(btn_limpar)
        
        # Botão de anular consentimento
        self.btn_anular = QPushButton("❌ Anular")
        self.btn_anular.setFixedSize(160, 30)
        self.btn_anular.setToolTip("Anular Consentimento")
        self._style_modern_button(self.btn_anular, "#dc3545")
        self.btn_anular.clicked.connect(self.anular_consentimento_click)
        self.btn_anular.setVisible(False)  # Inicialmente oculto
        acoes_layout.addWidget(self.btn_anular)
        
        acoes_layout.addStretch()
        main_horizontal_layout.addLayout(acoes_layout)  # Adicionar layout diretamente
        
        # Pequena margem direita
        main_horizontal_layout.addSpacing(20)
        
        # Adicionar layout horizontal ao layout principal
        layout.addLayout(main_horizontal_layout, 1)
        
        # Carregar status dos consentimentos
        self.carregar_status_consentimentos()
        
        # Atualizar informações do paciente
        self.atualizar_info_paciente_consentimento()

    def init_sub_gestao_documentos(self):
        """Sub-aba: Gestão de Documentos - Sistema completo de documentos do paciente"""
        layout = QVBoxLayout(self.sub_gestao_documentos)
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
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e91e63;
                color: white;
                border-color: #e91e63;
            }
            QPushButton:pressed {
                background-color: #c1185b;
                border-color: #c1185b;
            }
        """)
        btn_refresh.clicked.connect(self.atualizar_lista_documentos)
        header_layout.addWidget(btn_refresh)
        
        # Botão de upload
        btn_upload = QPushButton("📤 Adicionar Documento")
        btn_upload.setObjectName("btn_doc_upload")  # Para identificação específica se necessário
        btn_upload.clicked.connect(self.adicionar_documento)
        header_layout.addWidget(btn_upload)
        
        layout.addLayout(header_layout)
        
        # Estatísticas rápidas
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        self.stats_total = QLabel("📄 Total: 0")
        self.stats_total.setStyleSheet("font-weight: bold; color: #495057; font-size: 14px;")
        
        self.stats_consentimentos = QLabel("📋 Consentimentos: 0")
        self.stats_consentimentos.setStyleSheet("font-weight: bold; color: #28a745; font-size: 14px;")
        
        self.stats_prescricoes = QLabel("💊 Prescrições: 0")
        self.stats_prescricoes.setStyleSheet("font-weight: bold; color: #007bff; font-size: 14px;")
        
        self.stats_outros = QLabel("📁 Outros: 0")
        self.stats_outros.setStyleSheet("font-weight: bold; color: #6c757d; font-size: 14px;")
        
        stats_layout.addWidget(self.stats_total)
        stats_layout.addStretch()
        stats_layout.addWidget(self.stats_consentimentos)
        stats_layout.addStretch()
        stats_layout.addWidget(self.stats_prescricoes)
        stats_layout.addStretch()
        stats_layout.addWidget(self.stats_outros)
        
        layout.addWidget(stats_frame)
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("🔍 Filtrar por:")
        filter_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 14px;")
        filter_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "📄 Todos os Documentos",
            "📋 Consentimentos", 
            "💊 Prescrições",
            "👁️ Análises de Íris",
            "📧 Emails Enviados",
            "📁 Documentos Externos"
        ])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self.filtrar_documentos)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        
        # Campo de pesquisa
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Pesquisar documentos...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        self.search_edit.textChanged.connect(self.pesquisar_documentos)
        filter_layout.addWidget(self.search_edit)
        
        layout.addLayout(filter_layout)
        
        # Lista de documentos
        self.documentos_list = QListWidget()
        self.documentos_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #007bff;
                selection-color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        self.documentos_list.setAlternatingRowColors(True)
        self.documentos_list.itemDoubleClicked.connect(self.abrir_documento)
        self.documentos_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.documentos_list.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        layout.addWidget(self.documentos_list)
        
        # Painel de ações na parte inferior
        actions_layout = QHBoxLayout()
        
        btn_visualizar = QPushButton("👁️ Visualizar")
        btn_visualizar.setObjectName("btn_doc_visualizar")
        btn_visualizar.clicked.connect(self.visualizar_documento_selecionado)
        btn_visualizar.setEnabled(False)
        
        # ❌ BOTÃO ASSINAR REMOVIDO - deixou de fazer sentido conforme solicitado
        # self.btn_assinar_doc = QPushButton("✍️ Assinar")
        # self.btn_assinar_doc.setObjectName("btn_doc_assinar")
        # self.btn_assinar_doc.clicked.connect(self.assinar_documento_selecionado)
        # self.btn_assinar_doc.setEnabled(False)
        
        btn_enviar = QPushButton("📧 Enviar por Email")
        btn_enviar.setObjectName("btn_doc_enviar")
        btn_enviar.clicked.connect(self.enviar_documento_email)
        btn_enviar.setEnabled(False)
        
        btn_remover = QPushButton("🗑️ Remover")
        btn_remover.setObjectName("btn_doc_remover")
        btn_remover.clicked.connect(self.remover_documento)
        btn_remover.setEnabled(False)
        
        # Conectar seleção da lista para habilitar/desabilitar botões
        self.documentos_list.itemSelectionChanged.connect(
            lambda: self.atualizar_estado_botoes([btn_visualizar, btn_enviar, btn_remover])
        )
        
        actions_layout.addWidget(btn_visualizar)
        actions_layout.addWidget(btn_enviar)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_remover)
        
        layout.addLayout(actions_layout)
        
        # Carregar documentos na inicialização
        self.atualizar_lista_documentos()

    def atualizar_estado_botoes(self, botoes):
        """Atualiza o estado dos botões baseado na seleção"""
        tem_selecao = len(self.documentos_list.selectedItems()) > 0
        
        for botao in botoes:
            botao.setEnabled(tem_selecao)

    def atualizar_lista_documentos(self):
        """Carrega e atualiza a lista de documentos do paciente"""
        # PROTEÇÃO CONTRA LOOP INFINITO
        if hasattr(self, '_atualizando_lista') and self._atualizando_lista:
            print("⚠️ [DOCUMENTOS] Já está atualizando, ignorando chamada...")
            return
            
        self._atualizando_lista = True
        
        try:
            from PyQt6.QtCore import Qt as QtCore
            from PyQt6.QtGui import QColor
            
            self.documentos_list.clear()
            
            if not self.paciente_data:
                # Mostrar mensagem quando não há paciente selecionado
                item = QListWidgetItem("⚠️ Nenhum paciente selecionado")
                item.setData(QtCore.ItemDataRole.UserRole, None)
                self.documentos_list.addItem(item)
                self.atualizar_estatisticas(0, 0, 0, 0)
                return
            
            paciente_id = self.paciente_data.get('id', 'sem_id')
            nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
            
            # CORREÇÃO: Caminho exato do paciente atual
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente}"
            
            documentos = []
            total = 0
            consentimentos = 0
            prescricoes = 0
            outros = 0
            
            # CORREÇÃO: Verificar apenas a pasta EXATA deste paciente
            import os
            if not os.path.exists(pasta_paciente):
                print(f"📁 [DOCUMENTOS] Pasta não encontrada: {pasta_paciente}")
                # Mostrar mensagem quando pasta não existe
                item = QListWidgetItem("📭 Pasta de documentos não encontrada")
                item.setData(QtCore.ItemDataRole.UserRole, None)
                self.documentos_list.addItem(item)
                self.atualizar_estatisticas(0, 0, 0, 0)
                return
            
            print(f"🔍 [DOCUMENTOS] Verificando pasta: {pasta_paciente}")
            
            # Função para escanear uma pasta (sem duplicações)
            def escanear_pasta(pasta, tipo_default="Documento", icone_default="📄"):
                docs_encontrados = []
                if os.path.exists(pasta):
                    print(f"  📂 Escaneando: {pasta}")
                    arquivos = os.listdir(pasta)
                    print(f"  📊 Arquivos encontrados: {len(arquivos)}")
                    
                    for arquivo in arquivos:
                        caminho_completo = os.path.abspath(os.path.join(pasta, arquivo))
                        if os.path.isfile(caminho_completo) and not arquivo.endswith('.meta'):
                            # Verificar extensões suportadas
                            extensoes_suportadas = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.txt']
                            if any(arquivo.lower().endswith(ext) for ext in extensoes_suportadas):
                                
                                # Ler metadados se existirem
                                meta_file = f"{caminho_completo}.meta"
                                categoria_meta = tipo_default
                                descricao = ""
                                
                                if os.path.exists(meta_file):
                                    try:
                                        with open(meta_file, 'r', encoding='utf-8') as f:
                                            linhas = f.readlines()
                                            for linha in linhas:
                                                if linha.startswith('Categoria:'):
                                                    categoria_meta = linha.replace('Categoria:', '').strip()
                                                elif linha.startswith('Descrição:'):
                                                    descricao = linha.replace('Descrição:', '').strip()
                                    except:
                                        pass
                                
                                doc_info = {
                                    'nome': arquivo,
                                    'tipo': categoria_meta,
                                    'icone': self.obter_icone_por_tipo(categoria_meta, arquivo),
                                    'caminho': caminho_completo,
                                    'data': self.obter_data_arquivo(caminho_completo),
                                    'descricao': descricao
                                }
                                docs_encontrados.append(doc_info)
                                print(f"    ✅ Arquivo: {arquivo}")
                                
                return docs_encontrados
            
            # CORREÇÃO: Escanear APENAS a pasta principal (sem subpastas automáticas)
            # Removi o scan da pasta principal para evitar duplicações
            
            # CORREÇÃO: Escanear apenas subpastas válidas (sem duplicação maiúscula/minúscula)
            subpastas_candidatas = [
                (f"{pasta_paciente}/Consentimentos", "📋 Consentimento", "📋"),
                (f"{pasta_paciente}/consentimentos", "📋 Consentimento", "📋"),
                (f"{pasta_paciente}/declaracoes_saude", "🩺 Declaração de Saúde", "🩺"),
                (f"{pasta_paciente}/exames", "🧪 Exame/Análise", "🧪"),
                (f"{pasta_paciente}/correspondencia", "📧 Correspondência", "📧"),
                (f"{pasta_paciente}/analises_iris", "👁️ Relatório de Íris", "👁️")
            ]
            
            # CORREÇÃO: Verificar qual pasta de consentimentos existe (evitar duplicação)
            pasta_consentimentos_encontrada = None
            for pasta, tipo, icone in subpastas_candidatas:
                if "onsentimento" in pasta:  # maiúscula ou minúscula
                    if os.path.exists(pasta):
                        if pasta_consentimentos_encontrada is None:
                            pasta_consentimentos_encontrada = (pasta, tipo, icone)
                            documentos.extend(escanear_pasta(pasta, tipo, icone))
                            print(f"✅ [CONSENTIMENTOS] Usando pasta: {pasta}")
                        else:
                            print(f"⚠️ [CONSENTIMENTOS] Ignorando pasta duplicada: {pasta}")
                else:
                    # Outras pastas normalmente
                    documentos.extend(escanear_pasta(pasta, tipo, icone))
            
            # Escanear pasta principal para arquivos soltos (mas evitar duplicações de subpastas)
            arquivos_pasta_principal = escanear_pasta(pasta_paciente)
            for doc in arquivos_pasta_principal:
                # Apenas adicionar se não estiver em subpasta já escaneada
                arquivo_em_subpasta = False
                for subpasta, _, _ in subpastas_candidatas:
                    if os.path.exists(subpasta) and doc['caminho'].startswith(subpasta):
                        arquivo_em_subpasta = True
                        break
                
                if not arquivo_em_subpasta:
                    documentos.append(doc)
                    print(f"📄 [PRINCIPAL] Arquivo: {doc['nome']}")
            
            # Categorizar e contar
            for doc in documentos:
                total += 1
                tipo = doc['tipo']
                
                if 'Consentimento' in tipo:
                    consentimentos += 1
                elif any(palavra in tipo.lower() for palavra in ['prescrição', 'protocolo', 'suplementação']):
                    prescricoes += 1
                else:
                    outros += 1
            
            # CORREÇÃO: Remover duplicações baseadas no caminho completo
            documentos_unicos = []
            caminhos_vistos = set()
            
            for doc in documentos:
                if doc['caminho'] not in caminhos_vistos:
                    documentos_unicos.append(doc)
                    caminhos_vistos.add(doc['caminho'])
                else:
                    print(f"🗑️ [DUPLICAÇÃO] Removido: {doc['nome']}")
            
            documentos = documentos_unicos
            
            # Ordenar por data (mais recente primeiro)
            documentos.sort(key=lambda x: x['data'], reverse=True)
            
            # Adicionar itens à lista
            if not documentos:
                item = QListWidgetItem("📭 Nenhum documento encontrado para este paciente")
                item.setData(QtCore.ItemDataRole.UserRole, None)
                self.documentos_list.addItem(item)
            else:
                for doc in documentos:
                    from datetime import datetime
                    data_formatada = doc['data'].strftime('%d/%m/%Y %H:%M')
                    
                    # Texto principal
                    texto = f"{doc['icone']} {doc['nome']}\n    📅 {data_formatada} | 📁 {doc['tipo']}"
                    
                    # NOVO: Verificar status para declarações de saúde
                    if doc['tipo'] == "🩺 Declaração de Saúde" and "Declaracao_Saude_" in doc['nome']:
                        try:
                            from consentimentos_manager import ConsentimentosManager
                            consent_manager = ConsentimentosManager()
                            status_info = consent_manager.verificar_status_declaracao_por_arquivo(
                                paciente_id, doc['nome']
                            )
                            
                            if status_info and status_info['status'] == 'alterada':
                                data_alteracao = status_info['data_alteracao']
                                # Converter data de alteração para formato legível
                                try:
                                    dt_alteracao = datetime.strptime(data_alteracao, '%Y-%m-%d %H:%M:%S')
                                    data_alt_formatada = dt_alteracao.strftime('%d/%m/%Y')
                                    texto += f"\n    ⚠️ SEM EFEITO desde {data_alt_formatada}"
                                    # Alterar cor para cinzento/laranja para indicar status alterado
                                    doc['status_alterado'] = True
                                except:
                                    texto += f"\n    ⚠️ SEM EFEITO (declaração alterada)"
                                    doc['status_alterado'] = True
                        except Exception as e:
                            print(f"❌ Erro ao verificar status da declaração: {e}")
                    
                    # Adicionar descrição se existir
                    if doc['descricao']:
                        texto += f"\n    💬 {doc['descricao'][:50]}{'...' if len(doc['descricao']) > 50 else ''}"
                    
                    item = QListWidgetItem(texto)
                    item.setData(QtCore.ItemDataRole.UserRole, doc)
                    
                    # NOVO: Aplicar cor diferente para declarações alteradas
                    if doc.get('status_alterado', False):
                        item.setForeground(QColor(150, 150, 150))  # Cinzento para indicar sem efeito
                    
                    self.documentos_list.addItem(item)
            
            # Atualizar estatísticas
            self.atualizar_estatisticas(total, consentimentos, prescricoes, outros)
            print(f"🔄 [DOCUMENTOS] Lista atualizada para paciente: {nome_paciente} (Total: {total})")
            
        finally:
            self._atualizando_lista = False

    def obter_icone_por_tipo(self, tipo, nome_arquivo=""):
        """Retorna ícone apropriado baseado no tipo ou nome do arquivo"""
        tipo_lower = tipo.lower()
        nome_lower = nome_arquivo.lower()
        
        if 'consentimento' in tipo_lower:
            return '📋'
        elif any(palavra in tipo_lower for palavra in ['prescrição', 'protocolo', 'suplementação']):
            return '💊'
        elif any(palavra in tipo_lower for palavra in ['exame', 'análise', 'laboratório']):
            return '🧪'
        elif 'correspondência' in tipo_lower or 'email' in tipo_lower:
            return '📧'
        elif 'íris' in tipo_lower:
            return '👁️'
        elif 'relatório' in tipo_lower:
            return '📊'
        elif any(ext in nome_lower for ext in ['.jpg', '.jpeg', '.png']):
            return '🖼️'
        elif '.pdf' in nome_lower:
            return '📄'
        elif any(ext in nome_lower for ext in ['.docx', '.doc']):
            return '📝'
        else:
            return '📄'

    def obter_data_arquivo(self, caminho):
        """Obtém a data de modificação do arquivo"""
        import os
        from datetime import datetime
        try:
            timestamp = os.path.getmtime(caminho)
            return datetime.fromtimestamp(timestamp)
        except:
            return datetime.now()

    def atualizar_estatisticas(self, total, consentimentos, prescricoes, outros):
        """Atualiza os contadores de estatísticas"""
        self.stats_total.setText(f"📄 Total: {total}")
        self.stats_consentimentos.setText(f"📋 Consentimentos: {consentimentos}")
        self.stats_prescricoes.setText(f"💊 Prescrições: {prescricoes}")
        self.stats_outros.setText(f"📁 Outros: {outros}")

    def filtrar_documentos(self):
        """Filtra documentos por categoria"""
        filtro = self.filter_combo.currentText()
        
        for i in range(self.documentos_list.count()):
            item = self.documentos_list.item(i)
            doc_data = item.data(Qt.ItemDataRole.UserRole)
            
            if doc_data is None:
                continue
                
            mostrar = True
            if "Consentimentos" in filtro and doc_data['tipo'] != 'Consentimento':
                mostrar = False
            elif "Prescrições" in filtro and doc_data['tipo'] != 'Prescrição':
                mostrar = False
            elif "Documentos Externos" in filtro and doc_data['tipo'] != 'Documento':
                mostrar = False
            
            item.setHidden(not mostrar)

    def pesquisar_documentos(self):
        """Pesquisa documentos por nome"""
        texto_busca = self.search_edit.text().lower()
        
        for i in range(self.documentos_list.count()):
            item = self.documentos_list.item(i)
            doc_data = item.data(Qt.ItemDataRole.UserRole)
            
            if doc_data is None:
                continue
                
            mostrar = texto_busca in doc_data['nome'].lower()
            item.setHidden(not mostrar)

    def adicionar_documento(self):
        """Permite adicionar um novo documento com categorização automática"""
        if not self.paciente_data:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "⚠️ Selecione um paciente primeiro!")
            return
        
        # Diálogo melhorado para seleção de arquivo
        from PyQt6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit
        
        # Primeiro, seletor de arquivo
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "📎 Anexar Documento à Ficha do Paciente",
            "",
            "Documentos PDF (*.pdf);;Documentos Word (*.docx *.doc);;Imagens (*.jpg *.jpeg *.png);;Todos os arquivos (*.*)"
        )
        
        if not arquivo:
            return
        
        # Diálogo para categorizar o documento
        dialog = QDialog(self)
        dialog.setWindowTitle("📂 Categorizar Documento")
        dialog.setModal(True)
        dialog.resize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        titulo = QLabel("📎 Anexar Documento ao Paciente")
        titulo.setStyleSheet("font-size: 18px; color: #27ae60; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Info do arquivo
        import os
        nome_arquivo = os.path.basename(arquivo)
        tamanho = os.path.getsize(arquivo) / 1024 / 1024  # MB
        
        info_arquivo = QLabel(f"📄 <b>Arquivo:</b> {nome_arquivo}<br>📏 <b>Tamanho:</b> {tamanho:.1f} MB")
        info_arquivo.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 14px;")
        layout.addWidget(info_arquivo)
        
        # Seleção de categoria
        categoria_layout = QHBoxLayout()
        categoria_label = QLabel("📁 Categoria:")
        categoria_label.setStyleSheet("font-size: 14px; min-width: 100px;")
        categoria_layout.addWidget(categoria_label)
        
        categoria_combo = QComboBox()
        categoria_combo.addItems([
            "📋 Consentimento",
            "💊 Prescrição/Protocolo", 
            "🧪 Exame/Análise",
            "📧 Correspondência",
            "👁️ Relatório de Íris",
            "📊 Relatório Médico",
            "📄 Documento Geral"
        ])
        categoria_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
        """)
        categoria_layout.addWidget(categoria_combo)
        layout.addLayout(categoria_layout)
        
        # Campo de descrição/observações
        desc_label = QLabel("📝 Descrição/Observações (opcional):")
        desc_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(desc_label)
        
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("Ex: Análises clínicas do laboratório XYZ, enviadas por email em 17/08/2025...")
        desc_edit.setMaximumHeight(80)
        desc_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
        """)
        layout.addWidget(desc_edit)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_cancelar.clicked.connect(dialog.reject)
        
        btn_anexar = QPushButton("📎 Anexar Documento")
        btn_anexar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_anexar.clicked.connect(dialog.accept)
        
        buttons_layout.addWidget(btn_cancelar)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_anexar)
        layout.addLayout(buttons_layout)
        
        # Executar diálogo
        if dialog.exec() == QDialog.DialogCode.Accepted:
            categoria_selecionada = categoria_combo.currentText()
            descricao = desc_edit.toPlainText().strip()
            
            self.importar_documento_categorizado(arquivo, categoria_selecionada, descricao)

    def importar_documento_categorizado(self, caminho_origem, categoria, descricao=""):
        """Importa um documento para a pasta do paciente com categorização"""
        import os
        import shutil
        from datetime import datetime
        
        paciente_id = self.paciente_data.get('id', 'sem_id')
        nome_paciente = self.paciente_data.get('nome', 'Paciente').replace(' ', '_')
        pasta_base = f"Documentos_Pacientes/{paciente_id}_{nome_paciente}"
        
        # Determinar pasta de destino baseada na categoria
        pasta_destino = pasta_base
        if "Consentimento" in categoria:
            pasta_destino = f"{pasta_base}/consentimentos"
        elif "Exame" in categoria or "Análise" in categoria:
            pasta_destino = f"{pasta_base}/exames"
        elif "Correspondência" in categoria:
            pasta_destino = f"{pasta_base}/correspondencia"
        elif "Íris" in categoria:
            pasta_destino = f"{pasta_base}/analises_iris"
        
        # Criar pasta se não existir
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Preparar nome do arquivo
        nome_original = os.path.basename(caminho_origem)
        nome_base, extensao = os.path.splitext(nome_original)
        
        # Adicionar timestamp para evitar conflitos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_final = f"{nome_base}_{timestamp}{extensao}"
        caminho_destino = f"{pasta_destino}/{nome_final}"
        
        # Verificar se já existe (precaução extra)
        contador = 1
        caminho_final = caminho_destino
        while os.path.exists(caminho_final):
            nome_final = f"{nome_base}_{timestamp}_{contador}{extensao}"
            caminho_final = f"{pasta_destino}/{nome_final}"
            contador += 1
        
        try:
            # Copiar arquivo
            shutil.copy2(caminho_origem, caminho_final)
            
            # Criar arquivo de metadados (opcional)
            if descricao:
                meta_file = f"{caminho_final}.meta"
                with open(meta_file, 'w', encoding='utf-8') as f:
                    f.write(f"Categoria: {categoria}\n")
                    f.write(f"Data de Anexação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write(f"Arquivo Original: {nome_original}\n")
                    f.write(f"Descrição: {descricao}\n")
            
            # Mensagem de sucesso detalhada
            from biodesk_dialogs import mostrar_sucesso
            mostrar_sucesso(
                self, 
                "✅ Documento Anexado", 
                f"📎 <b>Documento anexado com sucesso!</b><br><br>"
                f"📄 <b>Arquivo:</b> {nome_original}<br>"
                f"📁 <b>Categoria:</b> {categoria}<br>"
                f"📂 <b>Localização:</b> {os.path.basename(pasta_destino)}<br>"
                f"🕒 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                + (f"<br>📝 <b>Descrição:</b> {descricao}" if descricao else "")
            )
            
            # Atualizar lista
            self.atualizar_lista_documentos()
            
            # Log para debug
            print(f"✅ [GESTÃO DOCS] Documento anexado:")
            print(f"   📄 Original: {caminho_origem}")
            print(f"   📁 Destino: {caminho_final}")
            print(f"   🏷️ Categoria: {categoria}")
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(
                self, 
                "❌ Erro ao Anexar", 
                f"Não foi possível anexar o documento:<br><br>"
                f"<b>Erro:</b> {str(e)}<br><br>"
                f"📄 <b>Arquivo:</b> {nome_original}<br>"
                f"📁 <b>Destino:</b> {pasta_destino}"
            )

    def abrir_documento(self, item):
        """Abre documento com duplo clique"""
        self.visualizar_documento_selecionado()

    def visualizar_documento_selecionado(self):
        """Visualiza o documento selecionado diretamente - SEM janelas intermediárias"""
        item = self.documentos_list.currentItem()
        if not item:
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, "Aviso", "⚠️ Selecione um documento primeiro!")
            return
            
        doc_data = item.data(Qt.ItemDataRole.UserRole)
        if not doc_data:
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, "Aviso", "⚠️ Dados do documento não encontrados!")
            return
        
        import os
        
        # Garantir caminho absoluto
        caminho = doc_data['caminho']
        if not os.path.isabs(caminho):
            caminho = os.path.abspath(caminho)
        
        # Verificar se arquivo existe
        if not os.path.exists(caminho):
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(
                self, 
                "Arquivo Não Encontrado", 
                f"❌ O arquivo não foi localizado:\n\n📄 {doc_data['nome']}\n📁 {caminho}\n\n💡 Verifique se o arquivo não foi movido ou excluído."
            )
            return
        
        # Abrir DIRETAMENTE - sem janelas intermediárias
        try:
            print(f"📄 [GESTÃO DOCS] Abrindo diretamente: {doc_data['nome']}")
            print(f"📁 [GESTÃO DOCS] Caminho: {caminho}")
            
            # Método mais direto no Windows
            if os.name == 'nt':
                os.startfile(caminho)
                print(f"✅ [GESTÃO DOCS] Documento aberto externamente: {doc_data['nome']}")
            else:
                # Para outros sistemas operacionais
                import subprocess
                if os.uname().sysname == 'Darwin':  # macOS
                    subprocess.run(['open', caminho], check=True)
                else:  # Linux
                    subprocess.run(['xdg-open', caminho], check=True)
                print(f"✅ [GESTÃO DOCS] Documento aberto externamente: {doc_data['nome']}")
                
        except Exception as e:
            print(f"⚠️ [GESTÃO DOCS] Erro ao abrir externamente: {str(e)}")
            from biodesk_dialogs import mostrar_erro  
            mostrar_erro(
                self,
                "Erro ao Abrir Documento",
                f"❌ Não foi possível abrir o documento:\n\n"
                f"📄 <b>Arquivo:</b> {doc_data['nome']}\n"
                f"📁 <b>Local:</b> {caminho}\n"
                f"🚫 <b>Erro:</b> {str(e)}\n\n"
                f"💡 <b>Dica:</b> Verifique se tem uma aplicação associada a este tipo de arquivo."
            )

    def enviar_documento_email(self):
        """Envia documento por email"""
        item = self.documentos_list.currentItem()
        if not item:
            return
            
        doc_data = item.data(Qt.ItemDataRole.UserRole)
        if not doc_data:
            return
        
        # Mudar para aba Email e pré-configurar anexo
        self.clinico_comunicacao_tabs.setCurrentWidget(self.sub_centro_comunicacao)
        
        # TODO: Implementar pré-configuração do email com anexo
        from biodesk_dialogs import mostrar_informacao
        mostrar_informacao(
            self, 
            "Email", 
            f"📧 Redirecionado para aba Email\n\n"
            f"📎 Documento a anexar:\n{doc_data['nome']}\n\n"
            f"💡 Configure o email e anexe manualmente o documento localizado em:\n"
            f"{doc_data['caminho']}"
        )

    def remover_documento(self):
        """Remove documento selecionado - versão melhorada com limpeza completa"""
        item = self.documentos_list.currentItem()
        if not item:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Nenhum documento selecionado para remover.")
            return
            
        doc_data = item.data(Qt.ItemDataRole.UserRole)
        if not doc_data:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Aviso", "Documento sem dados válidos.")
            return
        
        from biodesk_dialogs import perguntar_confirmacao
        if perguntar_confirmacao(
            self,
            "Confirmar Remoção", 
            f"❌ Tem certeza que deseja remover este documento?\n\n"
            f"📄 {doc_data['nome']}\n\n"
            f"⚠️ Esta ação remove o documento permanentemente do sistema!\n"
            f"Isso inclui:\n"
            f"• Arquivo físico\n"
            f"• Registros da base de dados\n"
            f"• Histórico de assinaturas\n\n"
            f"Esta ação não pode ser desfeita!"
        ):
            try:
                import os
                
                # 1. Remover arquivo físico se existir
                doc_caminho = doc_data.get('caminho', '')
                if doc_caminho and os.path.exists(doc_caminho):
                    os.remove(doc_caminho)
                    print(f"✅ Arquivo físico removido: {doc_caminho}")
                
                # 2. Remover registros relacionados da base de dados
                if self.paciente_data and 'id' in self.paciente_data:
                    paciente_id = self.paciente_data['id']
                    doc_nome = doc_data.get('nome', '')
                    
                    # Conectar à base de dados
                    from db_manager import DBManager
                    db = DBManager()
                    conn = db._connect()
                    if conn:
                        cursor = conn.cursor()
                        
                        # Remover da tabela consentimentos (declarações de saúde, termos, etc.)
                        cursor.execute("""
                            DELETE FROM consentimentos 
                            WHERE paciente_id = ? AND (
                                conteudo_texto LIKE ? OR
                                tipo_consentimento LIKE ?
                            )
                        """, (paciente_id, f"%{doc_nome}%", f"%declaracao%"))
                        
                        # Confirmação da remoção
                        linhas_removidas = cursor.rowcount
                        
                        conn.commit()
                        conn.close()
                        
                        if linhas_removidas > 0:
                            print(f"✅ {linhas_removidas} registro(s) da base de dados removidos para: {doc_nome}")
                        else:
                            print(f"ℹ️ Nenhum registro encontrado na base de dados para: {doc_nome}")
                
                # 3. Atualizar interface
                BiodeskMessageBox.success(self, "Sucesso", f"🗑️ Documento '{doc_nome}' removido completamente do sistema!")
                self.atualizar_lista_documentos()
                
                # 4. Atualizar status se for declaração de saúde
                if hasattr(self, 'atualizar_status_declaracao_saude'):
                    self.atualizar_status_declaracao_saude()
                
            except Exception as e:
                from biodesk_dialogs import mostrar_erro
                mostrar_erro(self, "Erro", f"❌ Erro ao remover documento:\n\n{str(e)}")
                print(f"❌ Erro detalhado na remoção: {e}")
                import traceback
                traceback.print_exc()

    def assinar_documento_selecionado(self):
        """Abre diálogo de assinatura para o documento selecionado"""
        try:
            # Verificar se há documento selecionado
            item = self.documentos_list.currentItem()
            if not item:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Nenhum documento selecionado.")
                return
            
            # Obter dados do documento
            doc_data = item.data(Qt.ItemDataRole.UserRole)
            if not doc_data:
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Aviso", "Documento sem dados válidos.")
                return
            
            doc_tipo = doc_data.get('tipo', '')
            doc_nome = doc_data.get('nome', '')
            doc_caminho = doc_data.get('caminho', '')
            
            print(f"🔍 [ASSINATURA] Documento selecionado: {doc_nome}")
            print(f"🔍 [ASSINATURA] Tipo: {doc_tipo}")
            
            # Determinar tipo de assinatura baseado no documento
            if 'Consentimento' in doc_tipo:
                self.assinar_consentimento_documento(doc_data)
            elif 'Declaração' in doc_tipo:
                self.assinar_declaracao_documento(doc_data)
            else:
                # Documento genérico - apenas assinatura do paciente
                self.assinar_documento_generico(doc_data)
                
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao iniciar assinatura:\n\n{str(e)}")

    def assinar_consentimento_documento(self, doc_data):
        """Abre diálogo de assinatura para consentimentos (paciente + terapeuta)"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
            from PyQt6.QtCore import Qt
            
            # Criar diálogo específico para consentimentos
            dialog = QDialog(self)
            dialog.setWindowTitle("Assinatura Digital - Consentimento")
            dialog.setModal(True)
            dialog.resize(500, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            titulo = QLabel(f"✍️ Assinatura do Consentimento")
            titulo.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #2980b9;
                padding: 15px;
                text-align: center;
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Informações do documento
            info_label = QLabel(f"📄 {doc_data.get('nome', 'Documento')}")
            info_label.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
            layout.addWidget(info_label)
            
            # Botões de assinatura
            botoes_layout = QVBoxLayout()
            botoes_layout.setSpacing(10)
            
            # Botão Paciente
            btn_paciente = QPushButton("👤 Assinar como Paciente")
            btn_paciente.setFixedHeight(50)
            btn_paciente.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            btn_paciente.clicked.connect(lambda: self.processar_assinatura_documento(doc_data, 'paciente', dialog))
            
            # Botão Terapeuta
            btn_terapeuta = QPushButton("👨‍⚕️ Assinar como Terapeuta")
            btn_terapeuta.setFixedHeight(50)
            btn_terapeuta.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            btn_terapeuta.clicked.connect(lambda: self.processar_assinatura_documento(doc_data, 'terapeuta', dialog))
            
            botoes_layout.addWidget(btn_paciente)
            botoes_layout.addWidget(btn_terapeuta)
            layout.addLayout(botoes_layout)
            
            # Botão Cancelar
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            layout.addWidget(btn_cancelar)
            
            dialog.exec()
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro na assinatura de consentimento:\n\n{str(e)}")

    def assinar_declaracao_documento(self, doc_data):
        """Abre diálogo de assinatura para declarações de saúde (apenas paciente)"""
        try:
            # Usar o método existente mas adaptado para documento específico
            self.processar_assinatura_documento(doc_data, 'paciente', None)
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro na assinatura de declaração:\n\n{str(e)}")

    def assinar_documento_generico(self, doc_data):
        """Abre diálogo de assinatura para documentos genéricos (apenas paciente)"""
        try:
            self.processar_assinatura_documento(doc_data, 'paciente', None)
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro na assinatura de documento:\n\n{str(e)}")

    def processar_assinatura_documento(self, doc_data, tipo_assinatura, parent_dialog=None):
        """Processa a assinatura do documento com canvas"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
            from PyQt6.QtCore import Qt
            
            # Fechar diálogo pai se existir
            if parent_dialog:
                parent_dialog.accept()
            
            # Criar diálogo de assinatura
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Canvas de Assinatura - {tipo_assinatura.title()}")
            dialog.setModal(True)
            dialog.resize(600, 450)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            emoji = "👤" if tipo_assinatura == 'paciente' else "👨‍⚕️"
            titulo = QLabel(f"{emoji} Assinatura Digital - {tipo_assinatura.title()}")
            titulo.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #2980b9;
                padding: 15px;
                text-align: center;
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Informações do documento
            info_text = f"📄 {doc_data.get('nome', 'Documento')}\n📁 {doc_data.get('tipo', 'Tipo desconhecido')}"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
            layout.addWidget(info_label)
            
            # Canvas de assinatura com dimensões controladas
            signature_canvas = SignatureCanvas()
            signature_canvas.setMinimumHeight(150)
            signature_canvas.setMaximumHeight(250)
            signature_canvas.setMinimumWidth(400)
            signature_canvas.setMaximumWidth(600)
            layout.addWidget(signature_canvas)
            
            # Instruções
            instrucoes = QLabel("✍️ Assine no campo acima usando o mouse ou toque")
            instrucoes.setStyleSheet("color: #6c757d; text-align: center; padding: 5px;")
            instrucoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(instrucoes)
            
            # Botões
            botoes_layout = QHBoxLayout()
            
            btn_limpar = QPushButton("🗑️ Limpar")
            btn_limpar.clicked.connect(signature_canvas.clear)
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            
            btn_confirmar = QPushButton("✅ Confirmar Assinatura")
            btn_confirmar.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            def confirmar_assinatura():
                try:
                    if signature_canvas.is_empty():
                        from biodesk_dialogs import mostrar_aviso
                        mostrar_aviso(dialog, "Assinatura Vazia", "Por favor, assine no campo antes de confirmar.")
                        return
                    
                    # Guardar assinatura na base de dados para declarações de saúde
                    tipo_documento = doc_data.get('tipo_documento', '')
                    if tipo_documento == 'declaracao_saude':
                        try:
                            # Converter assinatura para bytes
                            signature_pixmap = signature_canvas.toPixmap()
                            from PyQt6.QtCore import QBuffer, QIODevice
                            buffer = QBuffer()
                            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                            signature_pixmap.save(buffer, 'PNG')
                            signature_data = buffer.data().data()
                            
                            # Guardar na base de dados
                            from consentimentos_manager import ConsentimentosManager
                            manager = ConsentimentosManager()
                            paciente_id = self.paciente_data.get('id')
                            nome_pessoa = self.paciente_data.get('nome', '') if tipo_assinatura == 'paciente' else 'Terapeuta'
                            
                            sucesso_bd = manager.guardar_assinatura_declaracao(
                                paciente_id, 'declaracao_saude', tipo_assinatura, 
                                signature_data, nome_pessoa
                            )
                            
                            if sucesso_bd:
                                print(f"✅ Assinatura {tipo_assinatura} guardada na BD para declaração de saúde")
                                
                                # Atualizar status visual da declaração se for paciente
                                if tipo_assinatura == 'paciente' and hasattr(self, 'status_declaracao'):
                                    self.status_declaracao.setText("✅ Assinada")
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
                                
                                from biodesk_dialogs import mostrar_sucesso
                                mostrar_sucesso(dialog, "Sucesso", f"✅ Assinatura de {tipo_assinatura} guardada com sucesso!")
                                dialog.accept()
                                return
                            else:
                                print(f"❌ Falha ao guardar assinatura {tipo_assinatura} na BD")
                                
                        except Exception as e:
                            print(f"❌ Erro ao guardar assinatura na BD: {e}")
                    
                    # Para outros documentos, inserir assinatura no PDF
                    sucesso = self.inserir_assinatura_no_pdf(doc_data, signature_canvas, tipo_assinatura)
                    
                    if sucesso:
                        from biodesk_dialogs import mostrar_sucesso
                        mostrar_sucesso(dialog, "Sucesso", f"✅ Assinatura de {tipo_assinatura} inserida com sucesso!")
                        dialog.accept()
                        
                        # Atualizar lista de documentos
                        self.atualizar_lista_documentos()
                    else:
                        from biodesk_dialogs import mostrar_erro
                        mostrar_erro(dialog, "Erro", "❌ Erro ao inserir assinatura no documento.")
                        
                except Exception as e:
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(dialog, "Erro", f"❌ Erro ao confirmar assinatura:\n\n{str(e)}")
            
            btn_confirmar.clicked.connect(confirmar_assinatura)
            
            botoes_layout.addWidget(btn_limpar)
            botoes_layout.addStretch()
            botoes_layout.addWidget(btn_cancelar)
            botoes_layout.addWidget(btn_confirmar)
            
            layout.addLayout(botoes_layout)
            
            # Mostrar diálogo
            dialog.exec()
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro no processamento de assinatura:\n\n{str(e)}")

    def inserir_assinatura_no_pdf(self, doc_data, signature_canvas, tipo_assinatura):
        """Insere a assinatura diretamente no PDF existente"""
        try:
            import os
            import tempfile
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from PyQt6.QtCore import QBuffer, QIODevice
            
            doc_caminho = doc_data.get('caminho', '')
            
            if not os.path.exists(doc_caminho):
                print(f"❌ [ASSINATURA] Arquivo não encontrado: {doc_caminho}")
                return False
            
            print(f"🔄 [ASSINATURA] Inserindo assinatura de {tipo_assinatura} em: {doc_caminho}")
            
            # Converter assinatura para imagem temporária
            signature_pixmap = signature_canvas.toPixmap()
            
            # Converter pixmap para bytes PNG
            from PyQt6.QtCore import QBuffer, QIODevice
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            signature_pixmap.save(buffer, "PNG")
            signature_bytes = buffer.data()
            buffer.close()
            
            # Salvar como ficheiro temporário para debug
            temp_sig_path = tempfile.mktemp(suffix='.png')
            with open(temp_sig_path, 'wb') as f:
                f.write(signature_bytes)
            
            print(f"📁 [ASSINATURA] Ficheiro temporário criado: {temp_sig_path}")
            print(f"📊 [ASSINATURA] Tamanho da imagem: {len(signature_bytes)} bytes")
            
            # Criar backup do original
            backup_path = doc_caminho + '.backup'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(doc_caminho, backup_path)
                print(f"💾 [ASSINATURA] Backup criado: {backup_path}")
            
            # Inserir assinatura no PDF usando ReportLab + PyPDF2
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.utils import ImageReader
                import PyPDF2
                import io
                
                # Ler o PDF original
                with open(doc_caminho, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    
                    # Criar novo PDF com assinatura
                    packet = io.BytesIO()
                    c = canvas.Canvas(packet, pagesize=letter)
                    
                    # Posição da assinatura (canto inferior direito)
                    signature_width = 150
                    signature_height = 75
                    x_pos = 450  # Margem direita
                    y_pos = 50   # Margem inferior
                    
                    # Adicionar imagem da assinatura usando o ficheiro temporário
                    from reportlab.lib.utils import ImageReader
                    image_reader = ImageReader(temp_sig_path)
                    c.drawImage(image_reader, x_pos, y_pos, 
                              width=signature_width, height=signature_height, 
                              mask='auto', preserveAspectRatio=True)
                    
                    # Adicionar texto informativo
                    c.setFont("Helvetica", 8)
                    c.drawString(x_pos, y_pos - 15, f"Assinado: {tipo_assinatura}")
                    c.drawString(x_pos, y_pos - 25, f"Data: {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm')}")
                    
                    c.save()
                    
                    # Mover para o início do buffer
                    packet.seek(0)
                    signature_pdf = PyPDF2.PdfReader(packet)
                    
                    # Criar PDF de saída
                    output_pdf = PyPDF2.PdfWriter()
                    
                    # Adicionar cada página do original com a assinatura na primeira página
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        
                        # Na primeira página, adicionar a assinatura
                        if page_num == 0:
                            signature_page = signature_pdf.pages[0]
                            page.merge_page(signature_page)
                        
                        output_pdf.add_page(page)
                    
                    # Escrever o PDF modificado
                    with open(doc_caminho, 'wb') as output_file:
                        output_pdf.write(output_file)
                    
                    print(f"✅ [ASSINATURA] PDF modificado com assinatura de {tipo_assinatura}")
                    
            except ImportError as e:
                print(f"⚠️ [ASSINATURA] Biblioteca em falta: {e}")
                print("💡 [ASSINATURA] Para inserir assinaturas nos PDFs, instale: pip install PyPDF2")
                return False
            except Exception as e:
                print(f"❌ [ASSINATURA] Erro ao modificar PDF: {e}")
                # Restaurar backup em caso de erro
                if os.path.exists(backup_path):
                    import shutil
                    shutil.copy2(backup_path, doc_caminho)
                    print(f"🔄 [ASSINATURA] PDF restaurado do backup")
                return False
            
            # Limpar ficheiro temporário
            try:
                os.unlink(temp_sig_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ [ASSINATURA] Erro ao inserir assinatura: {e}")
            return False

    def mostrar_menu_contextual(self, posicao):
        """Mostra menu contextual com clique direito"""
        item = self.documentos_list.itemAt(posicao)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        
        action_visualizar = menu.addAction("👁️ Visualizar")
        action_visualizar.triggered.connect(self.visualizar_documento_selecionado)
        
        action_email = menu.addAction("📧 Enviar por Email")
        action_email.triggered.connect(self.enviar_documento_email)
        
        menu.addSeparator()
        
        action_remover = menu.addAction("🗑️ Remover")
        action_remover.triggered.connect(self.remover_documento)
        
        menu.exec(self.documentos_list.mapToGlobal(posicao))

    def init_sub_iris_analise(self):
        """✅ Análise de Íris - Layout ULTRA-OTIMIZADO com galeria dupla funcional"""
        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QLabel, QScrollArea, QWidget, QSizePolicy
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap

        # Layout principal horizontal
        main_layout = QHBoxLayout(self.sub_iris_analise)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # === GALERIA VISUAL DUPLA (ESQUERDA) ===
        galeria_frame = QFrame()
        galeria_frame.setFixedWidth(220)  # Largura aumentada para melhor visualização
        galeria_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)
        galeria_layout = QVBoxLayout(galeria_frame)
        galeria_layout.setContentsMargins(6, 6, 6, 6)  # Mais margem
        galeria_layout.setSpacing(8)  # Mais espaçamento

        # Botões com design uniforme + hover colorido
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(8)  # Mais espaço entre botões
        
        self.btn_adicionar_iris = QPushButton("📷")  # Ícone moderno de câmera
        self.btn_adicionar_iris.setFixedSize(85, 28)
        self.btn_adicionar_iris.setToolTip("Adicionar nova íris")
        self.btn_adicionar_iris.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #28a745;
                color: white;
                border-color: #28a745;            }
        """)
        self.btn_adicionar_iris.clicked.connect(self.adicionar_nova_iris)

        self.btn_remover_iris = QPushButton("🗑️")  # Ícone de lixeira
        self.btn_remover_iris.setFixedSize(85, 28)
        self.btn_remover_iris.setToolTip("Remover íris selecionada")
        self.btn_remover_iris.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #dc3545;
                color: white;
                border-color: #dc3545;            }
        """)
        self.btn_remover_iris.clicked.connect(self.apagar_imagem_selecionada)

        botoes_layout.addWidget(self.btn_adicionar_iris)
        botoes_layout.addWidget(self.btn_remover_iris)
        galeria_layout.addLayout(botoes_layout)
        
        # Espaçador para separar botões dos ícones das íris
        galeria_layout.addSpacing(12)  # Espaço adicional para evitar sobreposição

        # Área de scroll com 2 colunas para ESQ/DRT
        self.scroll_area_imagens = QScrollArea()
        self.scroll_area_imagens.setWidgetResizable(True)
        self.scroll_area_imagens.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area_imagens.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.galeria_widget = QWidget()
        self.galeria_layout_principal = QVBoxLayout(self.galeria_widget)
        self.galeria_layout_principal.setSpacing(8)  # Mais espaçamento vertical
        self.galeria_layout_principal.setContentsMargins(4, 4, 4, 4)
        
        # Layout horizontal para 2 colunas
        self.colunas_layout = QHBoxLayout()
        self.colunas_layout.setSpacing(8)  # Mais espaço entre colunas ESQ/DRT
        
        # Coluna ESQ
        self.col_esq_layout = QVBoxLayout()
        self.col_esq_layout.setSpacing(8)  # Mais espaço vertical entre ícones
        self.col_esq_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Coluna DRT  
        self.col_drt_layout = QVBoxLayout()
        self.col_drt_layout.setSpacing(8)  # Mais espaço vertical entre ícones
        self.col_drt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.colunas_layout.addLayout(self.col_esq_layout)
        self.colunas_layout.addLayout(self.col_drt_layout)
        self.galeria_layout_principal.addLayout(self.colunas_layout)
        self.galeria_layout_principal.addStretch()

        self.scroll_area_imagens.setWidget(self.galeria_widget)
        galeria_layout.addWidget(self.scroll_area_imagens, 1)

        main_layout.addWidget(galeria_frame)

        # === CANVAS OTIMIZADO (CENTRO) - Coluna apenas 4px mais larga que a imagem ===
        canvas_frame = QFrame()
        canvas_frame.setFixedWidth(654)  # 650px da imagem + 4px de margem total
        canvas_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(2, 2, 2, 2)  # Margens mínimas (4px total horizontal)
        canvas_layout.setSpacing(0)

        # Canvas sem decorações
        try:
            from iris_canvas import IrisCanvas
            self.iris_canvas = IrisCanvas(paciente_data=self.paciente_data)
            self.iris_canvas.setMinimumSize(650, 550)  # Tamanho ligeiramente aumentado
            self.iris_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # ✅ CONECTAR SINAIS PARA ANÁLISE DE ZONAS
            if hasattr(self.iris_canvas, 'zonaClicada'):
                self.iris_canvas.zonaClicada.connect(self.on_zona_clicada)
            
            canvas_layout.addWidget(self.iris_canvas, 1)
            
            # IrisCanvas carregado com funcionalidade de análise de sinais ativa
            
        except ImportError as e:
            canvas_placeholder = QLabel("Canvas da Íris\n(Módulo não disponível)")
            canvas_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            canvas_placeholder.setMinimumSize(450, 380)
            canvas_placeholder.setStyleSheet("""
                QLabel {
                    background: #f8f8f8;
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    font-size: 16px;
                    color: #666;
                }
            """)
            canvas_layout.addWidget(canvas_placeholder, 1)
            print(f"[AVISO] Erro ao importar IrisCanvas: {e}")

        main_layout.addWidget(canvas_frame)  # Sem expansão, largura fixa

        # === NOTAS FUNCIONAIS (DIREITA) ===
        notas_frame = QFrame()
        notas_frame.setFixedWidth(380)  # Largura aumentada para melhor organização das notas
        notas_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)
        notas_layout = QVBoxLayout(notas_frame)
        notas_layout.setContentsMargins(8, 8, 8, 8)
        notas_layout.setSpacing(6)

        # Widget de notas
        try:
            from checkbox_notes_widget import CheckboxNotesWidget
            self.notas_iris = CheckboxNotesWidget()
            self.notas_iris.setMinimumHeight(350)  # Reduzido para mostrar botões
            notas_layout.addWidget(self.notas_iris, 1)
        except ImportError:
            from PyQt6.QtWidgets import QTextEdit
            self.notas_iris = QTextEdit()
            self.notas_iris.setPlaceholderText("Notas da análise...")
            self.notas_iris.setMinimumHeight(350)
            notas_layout.addWidget(self.notas_iris, 1)

        # Botões com design uniforme + hover específico
        self.btn_exportar_notas = QPushButton("📋 Histórico")  # Ícone de prancheta
        self.btn_exportar_notas.setFixedHeight(36)
        self.btn_exportar_notas.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px;
            }
            QPushButton:hover { 
                background-color: #007bff;
                color: white;
                border-color: #007bff;            }
        """)
        self.btn_exportar_notas.clicked.connect(self.exportar_notas_iris)

        self.btn_exportar_terapia = QPushButton("⚡ Terapia")  # Ícone de raio
        self.btn_exportar_terapia.setFixedHeight(36)
        self.btn_exportar_terapia.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px;
            }
            QPushButton:hover { 
                background-color: #6f42c1;
                color: white;
                border-color: #6f42c1;            }
        """)
        self.btn_exportar_terapia.clicked.connect(self.exportar_para_terapia_quantica)

        btn_limpar_notas = QPushButton("🧹 Limpar")  # Ícone moderno de limpeza
        btn_limpar_notas.setFixedHeight(36)
        btn_limpar_notas.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px;
            }
            QPushButton:hover { 
                background-color: #dc3545;
                color: white;
                border-color: #dc3545;            }
        """)
        btn_limpar_notas.clicked.connect(self.limpar_notas_iris)

        notas_layout.addWidget(self.btn_exportar_notas)
        notas_layout.addWidget(self.btn_exportar_terapia)
        notas_layout.addWidget(btn_limpar_notas)

        main_layout.addWidget(notas_frame)

        # Carregar imagens existentes
        if hasattr(self, "atualizar_galeria_iris"):
            self.atualizar_galeria_iris()

        # Layout da íris ULTRA-LIMPO aplicado - sem poluição visual!

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

    def limpar_notas_iris(self):
        """Limpa todas as notas de análise de íris"""
        try:
            from biodesk_dialogs import mostrar_confirmacao
            
            resposta = mostrar_confirmacao(
                self,
                "Confirmar Limpeza",
                "⚠️ Tem certeza que deseja limpar todas as notas de análise?\n\nEsta ação não pode ser desfeita."
            )
            
            if resposta and hasattr(self, 'notas_iris') and self.notas_iris:
                self.notas_iris.limpar_todas()
                self.atualizar_textos_botoes()
                
                from biodesk_dialogs import mostrar_informacao
                mostrar_informacao(self, "Sucesso", "✅ Notas de análise limpas com sucesso!")
                
        except Exception as e:
            print(f"[ERRO] Erro ao limpar notas: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao limpar notas:\n\n{str(e)}")

    def atualizar_galeria_iris(self):
        """Atualiza a galeria de íris para mostrar miniaturas visuais clicáveis (versão compacta)"""
        from PyQt6.QtWidgets import QLabel, QFrame
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        from db_manager import DBManager
        import os

        # Limpar galeria visual (colunas ESQ/DRT se existirem)
        if hasattr(self, 'col_esq_layout') and hasattr(self, 'col_drt_layout'):
            for lay in (self.col_esq_layout, self.col_drt_layout):
                for i in reversed(range(lay.count())):
                    item = lay.itemAt(i)
                    w = item.widget()
                    if w:
                        w.setParent(None)
        elif hasattr(self, 'galeria_layout'):
            for i in reversed(range(self.galeria_layout.count())):
                widget = self.galeria_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        else:
            return

        paciente_id = self.paciente_data.get('id')
        if not paciente_id:
            return

        db = DBManager()
        imagens = db.get_imagens_por_paciente(paciente_id)

        if not imagens:
            label = QLabel("Nenhuma imagem")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet('color: #888; padding: 8px; font-size: 11px;')
            if hasattr(self, 'galeria_layout'):
                self.galeria_layout.addWidget(label)
            if hasattr(self, 'iris_canvas'):
                self.iris_canvas.set_image(None, None)
            return

        # Inicializar mapa de miniaturas (para estado selecionado)
        self._miniaturas_iris = {}
        
        # Inicializar lista de containers da galeria
        if not hasattr(self, 'galeria_containers'):
            self.galeria_containers = []
        else:
            self.galeria_containers.clear()

        # Agrupar imagens por tipo (ESQ / DRT) e ordenar cada grupo por data/ID
        def _ord_key(im):
            return im.get('data_analise') or im.get('data') or im.get('id') or 0

        grupos = {}
        for im in imagens:
            tipo = (im.get('tipo') or 'IMG').strip().upper()
            if tipo.startswith('E'):
                tipo_norm = 'ESQ'
            elif tipo.startswith('D'):
                tipo_norm = 'DRT'
            else:
                tipo_norm = 'IMG'
            grupos.setdefault(tipo_norm, []).append(im)

        # Ordenar internamente cada grupo
        for k in grupos:
            grupos[k] = sorted(grupos[k], key=_ord_key)

        # Construir lista final preservando ordem ESQ, DRT, IMG
        ordem_tipos = [t for t in ['ESQ', 'DRT', 'IMG'] if t in grupos]
        imagens_processadas = []
        etiqueta_map = {}
        for tipo in ordem_tipos:
            for idx, im in enumerate(grupos[tipo], start=1):
                label_calc = f"{tipo}{idx:03d}"
                etiqueta_map[im.get('id')] = label_calc
                imagens_processadas.append(im)

        # Adicionar miniaturas
        for img in imagens_processadas:
            thumb_path = img.get('caminho_imagem', '') or img.get('caminho', '')
            tipo_id = img.get('id')
            label_text = etiqueta_map.get(tipo_id, 'IMG')

            thumb_container = QFrame()
            thumb_container.setFixedSize(75, 85)  # Menor para caber em 2 colunas
            style_normal = (
                "QFrame {"
                "background: white;"
                "border: 2px solid #e0e0e0;"
                "border-radius: 12px;"
                "padding: 4px;"
                "}"
                "QFrame:hover {"
                "border: 2px solid #2196F3;"
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8fcff, stop:1 #e3f2fd);"
                "}"
            )
            style_selecionado = (
                "QFrame {"
                "background: #e8f3ff;"
                "border: 3px solid #1976D2;"
                "border-radius: 12px;"
                "padding: 3px;"
                "}"
                "QFrame:hover {"
                "border: 3px solid #1565C0;"
                "background: #e2f0ff;"
                "}"
            )
            thumb_container.setStyleSheet(style_normal)
            thumb_container.setProperty('style_base_normal', style_normal)
            thumb_container.setProperty('style_base_selecionado', style_selecionado)

            thumb_layout = QVBoxLayout(thumb_container)
            thumb_layout.setContentsMargins(4, 4, 4, 4)
            thumb_layout.setSpacing(6)
            thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            thumb_label = QLabel()
            thumb_label.setFixedSize(70, 50)  # Ajustado proporcionalmente
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_label.setStyleSheet(
                "QLabel { border: 1px solid #ddd; border-radius: 8px; background: #f5f5f5; }"
            )
            if thumb_path and os.path.exists(thumb_path):
                pix = QPixmap(thumb_path)
                if not pix.isNull():
                    thumb_label.setPixmap(
                        pix.scaled(
                            68,
                            48,  # Ajustado proporcionalmente
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                else:
                    thumb_label.setText('❌')
                    thumb_label.setStyleSheet(thumb_label.styleSheet() + 'color: #f44336; font-size: 20px;')
            else:
                thumb_label.setText('📷')
                thumb_label.setStyleSheet(thumb_label.styleSheet() + 'color: #666; font-size: 24px;')

            texto_label = QLabel(label_text)
            texto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            texto_label.setStyleSheet(
                "font-size: 10px; color: #424242; font-weight: 600; background: transparent; padding: 0px;"
            )

            from PyQt6.QtWidgets import QSpacerItem, QSizePolicy as _SP
            spacer = QSpacerItem(0, 2, _SP.Policy.Minimum, _SP.Policy.Fixed)
            thumb_layout.addWidget(thumb_label)
            thumb_layout.addItem(spacer)
            thumb_layout.addWidget(texto_label)

            tooltip_partes = [f"Etiqueta: {label_text}"]
            dt = img.get('data_analise') or img.get('data')
            if dt:
                tooltip_partes.append(f"Data: {dt}")
            tooltip_partes.append(f"Tipo original: {img.get('tipo','-')}")
            tooltip_partes.append(f"ID: {img.get('id','-')}")
            tooltip_partes.append(
                f"Caminho: {thumb_path if thumb_path else 'Sem ficheiro'}"
            )
            thumb_container.setToolTip("\n".join(tooltip_partes))
            thumb_container.mousePressEvent = lambda e, img=img: self.selecionar_imagem_galeria(img)
            
            # IMPORTANTE: Adicionar a propriedade img_data para a função de apagar funcionar
            thumb_container.setProperty('img_data', img)
            
            # Adicionar à lista de containers da galeria
            self.galeria_containers.append(thumb_container)

            if img.get('id') is not None:
                self._miniaturas_iris[img.get('id')] = thumb_container

            tipo_calc = 'OUTRO'
            if label_text.startswith('ESQ'):
                tipo_calc = 'ESQ'
            elif label_text.startswith('DRT'):
                tipo_calc = 'DRT'
            
            # Adicionar às colunas ESQ/DRT organizadamente
            if tipo_calc == 'ESQ':
                self.col_esq_layout.addWidget(thumb_container)
            elif tipo_calc == 'DRT':
                self.col_drt_layout.addWidget(thumb_container)
            else:
                # Se não for ESQ nem DRT, adiciona à primeira coluna
                self.col_esq_layout.addWidget(thumb_container)

    def on_galeria_item_clicked(self, item):
        """Callback quando um item da galeria é clicado"""
        img_data = item.data(Qt.ItemDataRole.UserRole)
        if img_data and hasattr(self, 'iris_canvas'):
            self.iris_canvas.set_image(img_data['caminho_imagem'], img_data['tipo'])
            self.imagem_iris_selecionada = img_data

    def on_galeria_click(self, event, img):
        self.atualizar_selecao_galeria(img)

    def on_galeria_double_click(self, event, img):
        self.selecionar_imagem_iris(img)

    def atualizar_selecao_galeria(self, img_selecionada):
        if not hasattr(self, 'galeria_containers'):
            return
        for container in self.galeria_containers:
            img_data = container.property('img_data') if hasattr(container, 'property') else None
            if img_data is not None:
                if img_data == img_selecionada:
                    container.setStyleSheet("""
                        QWidget {
                            background: #e3f2fd;
                            border: 2px solid #1976d2;
                            border-radius: 8px;
                            margin: 2px;
                            padding: 8px;
                        }
                        QWidget:hover {
                            border-color: #1565c0;
                            background: #e1f5fe;
                        }
                    """)
                else:
                    container.setStyleSheet("""
                        QWidget {
                            background: #ffffff;
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            margin: 2px;
                            padding: 8px;
                        }
                        QWidget:hover {
                            border-color: #1976d2;
                            background: #f8f9fa;
                        }
                    """)

    def selecionar_imagem_selecionada_galeria(self):
        if not hasattr(self, 'galeria_containers'):
            return
        for container in self.galeria_containers:
            img_data = container.property('img_data') if hasattr(container, 'property') else None
            if img_data is not None and container.styleSheet().find('#e3f2fd') != -1:
                self.selecionar_imagem_iris(img_data)
                return
        if hasattr(self, 'galeria_containers') and self.galeria_containers:
            primeiro_container = self.galeria_containers[0]
            img_data = primeiro_container.property('img_data') if hasattr(primeiro_container, 'property') else None
            if img_data is not None:
                self.selecionar_imagem_iris(img_data)

    def selecionar_imagem_iris(self, img):
        self.imagem_iris_selecionada = img
        self.iris_canvas.set_image(img['caminho_imagem'], img['tipo'])
        self.notas_iris.limpar_todas_linhas()  # Limpar todas as linhas com checkboxes
        
        # ═══════════════ INTEGRAÇÃO: ANÁLISE DE ÍRIS ═══════════════
        # Definir imagem atual para análise (se widget existir)
        if hasattr(self.iris_canvas, 'definir_imagem_atual'):
            self.iris_canvas.definir_imagem_atual(img['id'])
            print(f"[FICHA] Imagem {img['id']} definida para análise de íris")
        
        self.atualizar_selecao_galeria(img)

    def apagar_imagem_selecionada(self):
        """Apaga a imagem de íris selecionada na galeria"""
        print("[DEBUG] Tentando apagar imagem selecionada")
        
        # Debug adicional para entender o estado da galeria
        print(f"[DEBUG] hasattr galeria_containers: {hasattr(self, 'galeria_containers')}")
        
        if hasattr(self, 'galeria_containers'):
            print(f"[DEBUG] galeria_containers length: {len(self.galeria_containers)}")
        else:
            print("[DEBUG] galeria_containers não existe - criando...")
            self.galeria_containers = []
        
        # Se não há containers, tentar procurar na interface diretamente
        if not hasattr(self, 'galeria_containers') or len(self.galeria_containers) == 0:
            print("[DEBUG] Lista galeria_containers vazia - buscando na interface...")
            
            # Tentar buscar diretamente no scroll area
            if hasattr(self, 'scroll_area_imagens') and self.scroll_area_imagens:
                widget = self.scroll_area_imagens.widget()
                if widget and widget.layout():
                    print(f"[DEBUG] Scroll area widget found, layout items: {widget.layout().count()}")
                    
                    # Debug: Analisar cada item do layout
                    self.galeria_containers = []
                    for i in range(widget.layout().count()):
                        item = widget.layout().itemAt(i)
                        if item and item.widget():
                            w = item.widget()
                            print(f"[DEBUG] Layout item {i}: {type(w).__name__} - objectName: '{w.objectName()}'")
                            
                            # Verificar se é um layout (col_esq_layout ou col_drt_layout)
                            if hasattr(w, 'layout') and w.layout():
                                sub_layout = w.layout()
                                print(f"[DEBUG]   Sub-layout com {sub_layout.count()} items")
                                
                                # Buscar nos containers do sub-layout
                                for j in range(sub_layout.count()):
                                    sub_item = sub_layout.itemAt(j)
                                    if sub_item and sub_item.widget():
                                        sub_w = sub_item.widget()
                                        print(f"[DEBUG]     Sub-item {j}: {type(sub_w).__name__} - Has img_data: {hasattr(sub_w, 'property') and sub_w.property('img_data') is not None}")
                                        
                                        if hasattr(sub_w, 'property') and sub_w.property('img_data'):
                                            self.galeria_containers.append(sub_w)
                                            img_data = sub_w.property('img_data')
                                            print(f"[DEBUG]     ✅ Container encontrado: {img_data.get('caminho_imagem', 'N/A')}")
                            
                            # Também verificar o próprio widget
                            if hasattr(w, 'property') and w.property('img_data'):
                                self.galeria_containers.append(w)
                                img_data = w.property('img_data')
                                print(f"[DEBUG] ✅ Container direto encontrado: {img_data.get('caminho_imagem', 'N/A')}")
                    
                    # Buscar recursivamente todos os filhos também
                    all_children = widget.findChildren(QWidget)
                    print(f"[DEBUG] Total de widgets filhos encontrados: {len(all_children)}")
                    
                    for child in all_children:
                        if hasattr(child, 'property') and child.property('img_data') and child not in self.galeria_containers:
                            self.galeria_containers.append(child)
                            img_data = child.property('img_data')
                            print(f"[DEBUG] ✅ Container adicional encontrado via findChildren: {img_data.get('caminho_imagem', 'N/A')}")
            
            # Se ainda não encontrou, mostrar aviso
            if len(self.galeria_containers) == 0:
                print("[DEBUG] Nenhuma galeria encontrada")
                from biodesk_dialogs import mostrar_aviso
                mostrar_aviso(self, "Galeria Vazia", "Nenhuma imagem na galeria para apagar.")
                return
        
        print(f"[DEBUG] Verificando {len(self.galeria_containers)} containers")
        
        # Procurar container selecionado usando métodos mais robustos
        container_selecionado = None
        img_data_selecionada = None
        
        for i, container in enumerate(self.galeria_containers):
            if hasattr(container, 'property'):
                # Verificar se tem dados da imagem
                img_data = container.property('img_data')
                if img_data:
                    # Verificar se está selecionado pela propriedade 'selecionado'
                    is_selected = container.property('selecionado') == True
                    
                    # Debug adicional
                    style = container.styleSheet()
                    selecionado_prop = container.property('selecionado')
                    
                    print(f"[DEBUG] Container {i}: {img_data.get('caminho_imagem', 'N/A')}")
                    print(f"[DEBUG] Propriedade 'selecionado': {selecionado_prop}")
                    print(f"[DEBUG] Style: {style[:100]}...")  # Primeiros 100 chars
                    print(f"[DEBUG] Container {i} selecionado: {is_selected}")
                    
                    if is_selected:
                        container_selecionado = container
                        img_data_selecionada = img_data
                        print(f"[DEBUG] ✅ Container selecionado encontrado: {img_data.get('caminho_imagem', 'N/A')}")
                        break
        
        if container_selecionado and img_data_selecionada:
            print(f"[DEBUG] Eliminando imagem: {img_data_selecionada.get('caminho_imagem', 'N/A')}")
            self.eliminar_imagem_iris(img_data_selecionada)
        else:
            # Se chegou aqui, nenhuma imagem estava selecionada
            print("[DEBUG] ❌ Nenhuma imagem selecionada detectada")
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Seleção Necessária", "Por favor, clique em uma imagem da galeria para selecioná-la antes de apagar.")

    def eliminar_imagem_iris(self, img):
        from biodesk_dialogs import mostrar_confirmacao, mostrar_erro
        
        if mostrar_confirmacao(
            self, 
            "Eliminar imagem",
            f"Tem a certeza que quer eliminar a imagem {img['caminho_imagem']}?"
        ):
            try:
                import os
                os.remove(img['caminho_imagem'])
            except Exception as e:
                mostrar_erro(self, "Erro", f"Não foi possível eliminar ficheiro: {e}")
            db = DBManager()
            db.execute_query("DELETE FROM imagens_iris WHERE id = ?", (img['id'],))
            self.atualizar_galeria_iris()

    def adicionar_nova_iris(self):
        """Captura nova imagem de íris usando a câmera e salva automaticamente"""
        print("[DEBUG] adicionar_nova_iris chamado")
        
        # Importações necessárias
        from biodesk_dialogs import escolher_lateralidade, mostrar_aviso, mostrar_informacao, mostrar_erro
        
        try:
            # Verificar se existe um paciente carregado
            if not self.paciente_data or 'id' not in self.paciente_data:
                mostrar_aviso(
                    self, 
                    "Paciente Necessário", 
                    "É necessário ter um paciente selecionado para capturar e salvar imagens de íris."
                )
                return
            
            # Importar dependências necessárias
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel, 
                                       QHBoxLayout, QApplication)
            from PyQt6.QtCore import QTimer, pyqtSignal
            from PyQt6.QtGui import QImage, QPixmap
            # cv2 importado quando necessário
            import os
            from datetime import datetime
            from db_manager import DBManager
            
            # Criar classe de preview inline
            class IridoscopioPreview(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Iridoscópio - Preview ao Vivo")
                    self.setFixedSize(800, 600)
                    self.setModal(True)
                    
                    self.cap = None
                    self.frame = None
                    self.timer = QTimer()
                    self.timer.timeout.connect(self.update_frame)
                    
                    self.setup_ui()
                    self.start_camera()
                
                def setup_ui(self):
                    layout = QVBoxLayout(self)
                    
                    # Label para mostrar video
                    self.video_label = QLabel()
                    self.video_label.setMinimumSize(640, 480)
                    self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centralizar imagem
                    self.video_label.setScaledContents(False)  # Não esticar a imagem
                    self.video_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #9C27B0;
                            border-radius: 8px;
                            background-color: #000000;
                        }
                    """)
                    layout.addWidget(self.video_label)
                    
                    # Instruções
                    instrucoes = QLabel("📹 Posicione o olho e ajuste o foco. Clique 'Capturar' quando estiver pronto.")
                    instrucoes.setStyleSheet("""
                        QLabel {
                            padding: 10px;
                            background-color: #e3f2fd;
                            border-radius: 6px;
                            color: #1976d2;
                            font-weight: bold;
                        }
                    """)
                    layout.addWidget(instrucoes)
                    
                    # Botões
                    botoes_layout = QHBoxLayout()
                    
                    self.btn_capturar = QPushButton("📸 Capturar Imagem")
                    self.btn_capturar.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                    """)
                    self.btn_capturar.clicked.connect(self.capturar_imagem)
                    
                    self.btn_cancelar = QPushButton("❌ Cancelar")
                    self.btn_cancelar.setStyleSheet("""
                        QPushButton {
                            background-color: #f44336;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #da190b;
                        }
                    """)
                    self.btn_cancelar.clicked.connect(self.reject)
                    
                    botoes_layout.addWidget(self.btn_capturar)
                    botoes_layout.addWidget(self.btn_cancelar)
                    layout.addLayout(botoes_layout)
                
                def start_camera(self):
                    # Import lazy do cv2 apenas quando necessário
                    import cv2
                    # Tentar iridoscópio primeiro (câmera 1)
                    self.cap = cv2.VideoCapture(1)
                    if not self.cap.isOpened():
                        # Fallback para câmera 0
                        self.cap = cv2.VideoCapture(0)
                        if not self.cap.isOpened():
                            self.video_label.setText("❌ Erro: Não foi possível acessar nenhuma câmera")
                            return
                        else:
                            print("⚠️ Usando câmera padrão - iridoscópio não encontrado")
                    else:
                        print("✅ Iridoscópio conectado")
                    
                    # Configurar resolução
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    
                    # Iniciar timer para atualização
                    self.timer.start(30)  # 30ms = ~33 FPS
                
                def update_frame(self):
                    if self.cap and self.cap.isOpened():
                        ret, frame = self.cap.read()
                        if ret:
                            self.current_frame = frame.copy()
                            
                            # Converter para QImage e exibir
                            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = rgb_image.shape
                            bytes_per_line = ch * w
                            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                            
                            # Redimensionar para caber no label
                            pixmap = QPixmap.fromImage(qt_image)
                            scaled_pixmap = pixmap.scaled(
                                self.video_label.size(), 
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                            self.video_label.setPixmap(scaled_pixmap)
                
                def capturar_imagem(self):
                    if hasattr(self, 'current_frame') and self.current_frame is not None:
                        self.frame = self.current_frame.copy()
                        self.accept()
                    else:
                        self.video_label.setText("❌ Erro: Nenhuma imagem disponível para captura")
                
                def closeEvent(self, event):
                    self.stop_camera()
                    event.accept()
                
                def stop_camera(self):
                    if self.timer.isActive():
                        self.timer.stop()
                    if self.cap:
                        self.cap.release()
            
            # 1. Abrir preview do iridoscópio
            preview = IridoscopioPreview(parent=self)
            if preview.exec() == QDialog.DialogCode.Accepted and preview.frame is not None:
                frame = preview.frame
            else:
                print("[INFO] Captura cancelada pelo usuário")
                return
            
            if frame is None:
                mostrar_erro(self, "Erro de Captura", "Não foi possível capturar imagem da câmera.")
                return
            
            try:
                # 2. Determinar olho (esquerdo/direito) com diálogo moderno
                tipo = escolher_lateralidade(self)
                if not tipo:
                    return  # Usuário cancelou
                
                # 3. Salvar imagem em arquivo permanente
                imagens_dir = os.path.join(os.path.dirname(__file__), "imagens_iris", str(self.paciente_data['id']))
                os.makedirs(imagens_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{tipo}_{timestamp}.jpg"
                caminho = os.path.join(imagens_dir, filename)
                
                # Salvar com qualidade alta
                success = cv2.imwrite(caminho, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                if not success:
                    raise Exception("Falha ao salvar a imagem no disco")
                
                print(f"✅ Imagem salva: {caminho}")
                
                # 4. Atualizar BD
                db = DBManager()
                db.adicionar_imagem_iris(self.paciente_data['id'], tipo, caminho)
                print(f"✅ Registro adicionado ao BD: paciente={self.paciente_data['id']}, tipo={tipo}")
                
                # 5. Atualizar UI
                self.atualizar_galeria_iris()
                print("✅ Galeria atualizada")
                
                # 6. Exibir imagem no canvas
                self.iris_canvas.set_image(caminho, tipo)
                self.notas_iris.limpar_todas_linhas()  # Limpar todas as linhas com checkboxes
                print("✅ Imagem carregada no canvas")
                
                # 7. Informar sucesso
                tipo_nome = "Esquerda" if tipo == 'esq' else "Direita"
                mostrar_informacao(
                    self, 
                    "Sucesso", 
                    f"Imagem capturada e guardada com sucesso!\n\n"
                    f"📁 Arquivo: {filename}\n"
                    f"👁️ Lateralidade: Íris {tipo_nome}\n"
                    f"👤 Paciente: {self.paciente_data.get('nome', 'N/A')}\n\n"
                    "A imagem foi automaticamente adicionada à galeria e está pronta para análise.",
                    "success"
                )
                
            except Exception as e:
                print(f"❌ Erro ao processar a imagem: {e}")
                import traceback
                traceback.print_exc()
                mostrar_erro(
                    self, 
                    "Erro", 
                    f"Erro ao processar a imagem:\n\n{str(e)}"
                )
            else:
                print("[INFO] Captura cancelada pelo usuário")
                
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            mostrar_erro(
                self, 
                "Erro de Módulo", 
                "Não foi possível carregar o módulo da câmera.\n\n"
                "Verifique se o arquivo iris_anonima_canvas.py está presente."
            )
        except Exception as e:
            print(f"❌ Erro geral em adicionar_nova_iris: {e}")
            import traceback
            traceback.print_exc()
            mostrar_erro(
                self, 
                "Erro na Captura", 
                f"Ocorreu um erro ao tentar capturar a imagem:\n\n{str(e)}"
            )

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
        
        # Botão de teste - mesmo do botão principal
        btn_teste = QPushButton("🧪 Teste do Sistema Zero")
        btn_teste.clicked.connect(self.teste_zero_separador)
        btn_teste.setStyleSheet("""
            QPushButton {
                background: #4a148c;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 25px;
                border-radius: 8px;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background: #4a148caa;
            }
            QPushButton:pressed {
                background: #4a148c77;
            }
        """)
        botoes_layout.addWidget(btn_teste)
        
        # Botão abrir módulo
        self.btn_abrir_terapia = QPushButton("⚡ Abrir Módulo de Terapia")
        self.btn_abrir_terapia.clicked.connect(self.abrir_terapia)
        self.btn_abrir_terapia.setStyleSheet("""
            QPushButton {
                background: #7b1fa2;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 25px;
                border-radius: 8px;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background: #7b1fa2aa;
            }
            QPushButton:pressed {
                background: #7b1fa277;
            }
        """)
        botoes_layout.addWidget(self.btn_abrir_terapia)
        
        botoes_layout.addStretch()
        layout.addLayout(botoes_layout)
        
        # Espaçador
        layout.addStretch()
    
    def teste_zero_separador(self):
        """Teste do sistema zero no separador - mesma mensagem do botão principal"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Construir mensagem igual à da classe TerapiaQuantica
        mensagem = "✅ TERAPIA QUÂNTICA - VERSÃO ZERO FUNCIONANDO!\n\n"
        
        if self.paciente_data:
            mensagem += f"👤 Paciente: {self.paciente_data.get('nome', 'N/A')}\n"
            if 'idade' in self.paciente_data:
                mensagem += f"🎂 Idade: {self.paciente_data.get('idade', 'N/A')} anos\n"
        else:
            mensagem += "👤 Modo sem paciente selecionado\n"
        
        mensagem += """
🎯 Base mínima carregada com sucesso
🔧 Pronto para desenvolvimento do zero
🌟 Interface limpa e funcional

💡 Agora você pode começar a implementar
   suas funcionalidades de medicina quântica!"""
        
        QMessageBox.information(
            self,
            "Sistema Zero Funcionando",
            mensagem
        )

    def exportar_notas_iris(self):
        # Obter apenas as linhas selecionadas
        linhas_selecionadas = self.notas_iris.get_linhas_selecionadas()
        
        if not linhas_selecionadas:
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, 'Nenhuma nota selecionada', 
                         'Selecione pelo menos uma nota para exportar para o histórico.')
            return
        
        # Criar texto formatado das linhas selecionadas
        notas = '\n'.join(linhas_selecionadas)
        
        from datetime import datetime
        data_hoje = datetime.today().strftime('%d/%m/%Y')
        
        print(f"[DEBUG] Exportando notas para data: {data_hoje}")
        print(f"[DEBUG] Número de linhas selecionadas: {len(linhas_selecionadas)}")
        
        # Usar a mesma verificação robusta que o botão de data usa
        existe, tipo = self._data_ja_existe_no_historico(data_hoje)
        
        print(f"[DEBUG] Data existe no histórico: {existe}, tipo: {tipo}")
        
        if not existe:
            # Se não existe data de hoje, avisar o utilizador
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(
                self, 
                'Data não encontrada', 
                f'Não foi encontrada uma entrada para hoje ({data_hoje}) no histórico.\n\n'
                'Use o botão 📅 para inserir a data primeiro.'
            )
            return
        
        # Formatar as notas
        notas_formatadas = self._formatar_notas_para_exportacao(notas)
        
        # Método mais robusto para encontrar e inserir após a data
        sucesso = self._inserir_notas_apos_data(data_hoje, notas_formatadas)
        
        if sucesso:
            # Remover as linhas exportadas do widget
            self._remover_linhas_selecionadas()
            
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, 'Exportado', 
                             f'✅ {len(linhas_selecionadas)} nota(s) adicionada(s) ao histórico clínico!')
        else:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(
                self, 
                'Erro ao localizar data', 
                f'Não foi possível localizar a data {data_hoje} no histórico para inserir as notas.'
            )
    
    def _remover_linhas_selecionadas(self):
        """Remove as linhas que estão marcadas (após exportação)"""
        # Obter widgets das linhas selecionadas
        linhas_para_remover = []
        for linha_data in self.notas_iris.linhas_notas:
            if linha_data['checkbox'].isChecked():
                linhas_para_remover.append(linha_data['widget'])
        
        # Remover cada linha
        for linha_widget in linhas_para_remover:
            self.notas_iris.remover_linha(linha_widget)
        
        # Atualizar textos dos botões
        self.atualizar_textos_botoes()
    
    def data_atual(self):
        """Retorna a data atual formatada"""
        from datetime import datetime
        return datetime.today().strftime('%d/%m/%Y')

    def _formatar_notas_para_exportacao(self, notas):
        """
        Formata as notas da íris para exportação com parágrafos e vírgulas adequadas
        """
        # Dividir as notas em linhas
        linhas = [linha.strip() for linha in notas.split('\n') if linha.strip()]

        if not linhas:
            return ""

        linhas_formatadas = []
        for i, linha in enumerate(linhas):
            if i == 0:
                linhas_formatadas.append(linha)
            else:
                linhas_formatadas.append(f"<b>{linha}</b>")

        resultado = '<br>'.join(linhas_formatadas)
        return resultado

    def _adicionar_nota_zona(self, nome_zona):
        """
        Slot chamado ao clicar numa zona da íris; adiciona uma linha na caixa de notas.
        """
        texto = f"Alteração na área reflexa: {nome_zona}"
        print(f"[NOTA] Adicionando nota para zona: {nome_zona}")
        
        # Adiciona a linha no widget com checkbox
        self.notas_iris.adicionar_linha(texto)
        
        # Feedback visual opcional
        print(f"✅ Nota adicionada: {texto}")

    def init_tab_dados(self):
        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(28)
        grid.setContentsMargins(24, 18, 24, 18)

        # Linha 1: Nome
        self.nome_edit = QLineEdit()
        self.nome_edit.setMinimumWidth(320)
        self._style_line_edit(self.nome_edit)
        grid.addWidget(self._create_label('Nome'), 0, 0)
        grid.addWidget(self.nome_edit, 0, 1, 1, 3)

        # Linha 2: Data de nascimento | Sexo (Widget moderno)
        self.nasc_edit = ModernDateWidget()
        self.nasc_edit.setDate(QDate(1920, 1, 1))
        
        self.sexo_combo = QComboBox()
        self.sexo_combo.addItems(['', 'Masculino', 'Feminino', 'Outro'])
        self.sexo_combo.setFixedWidth(200)
        self._style_combo_box(self.sexo_combo)
        
        grid.addWidget(self._create_label('Data de nascimento'), 1, 0)
        grid.addWidget(self.nasc_edit, 1, 1, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self._create_label('Sexo'), 1, 2)
        grid.addWidget(self.sexo_combo, 1, 3)

        # Linha 3: Profissão | Naturalidade
        self.profissao_edit = QLineEdit()
        self.profissao_edit.setMinimumWidth(200)
        self._style_line_edit(self.profissao_edit)
        
        self.naturalidade_edit = QLineEdit()
        self.naturalidade_edit.setMinimumWidth(200)
        self._style_line_edit(self.naturalidade_edit)
        
        grid.addWidget(self._create_label('Profissão'), 2, 0)
        grid.addWidget(self.profissao_edit, 2, 1)
        grid.addWidget(self._create_label('Naturalidade'), 2, 2)
        grid.addWidget(self.naturalidade_edit, 2, 3)

        # Linha 4: Estado civil | Local habitual
        self.estado_civil_combo = QComboBox()
        self.estado_civil_combo.addItems(['', 'Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'União de facto', 'Outro'])
        self.estado_civil_combo.setFixedWidth(200)
        self._style_combo_box(self.estado_civil_combo)
        
        self.local_combo = QComboBox()
        self.local_combo.addItems(['', 'Chão de Lopes', 'Coruche', 'Campo Maior', 'Elvas', 'Cliniprata', 'Spazzio Vita', 'Samora Correia', 'Online', 'Outro'])
        self.local_combo.setFixedWidth(200)
        self._style_combo_box(self.local_combo)
        
        grid.addWidget(self._create_label('Estado civil'), 3, 0)
        grid.addWidget(self.estado_civil_combo, 3, 1)
        grid.addWidget(self._create_label('Local habitual'), 3, 2)
        grid.addWidget(self.local_combo, 3, 3)

        # Linha 5: Contacto | Email
        self.contacto_edit = QLineEdit()
        self.contacto_edit.setFixedWidth(200)
        self.contacto_edit.textChanged.connect(self.formatar_contacto)
        self._style_line_edit(self.contacto_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setMinimumWidth(220)
        self._style_line_edit(self.email_edit)
        
        grid.addWidget(self._create_label('Contacto'), 4, 0)
        grid.addWidget(self.contacto_edit, 4, 1)
        grid.addWidget(self._create_label('Email'), 4, 2)
        grid.addWidget(self.email_edit, 4, 3)

        layout.addLayout(grid)
        layout.addSpacing(36)
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.tab_dados.setLayout(layout)

    def formatar_contacto(self, text):
        digits = ''.join(filter(str.isdigit, text))
        if len(digits) > 9:
            digits = digits[:9]
        formatted = ' '.join([digits[i:i+3] for i in range(0, len(digits), 3)])
        if text != formatted:
            self.contacto_edit.blockSignals(True)
            self.contacto_edit.setText(formatted)
            self.contacto_edit.blockSignals(False)

    def formatar_data(self, text):
        """Formata a data no formato dd/mm/aaaa"""
        # Remove caracteres não numéricos exceto barras
        digits = ''.join(filter(lambda x: x.isdigit() or x == '/', text))
        
        # Remove barras para trabalhar apenas com dígitos
        only_digits = ''.join(filter(str.isdigit, digits))
        
        # Limita a 8 dígitos
        if len(only_digits) > 8:
            only_digits = only_digits[:8]
        
        # Formata conforme o número de dígitos
        if len(only_digits) <= 2:
            formatted = only_digits
        elif len(only_digits) <= 4:
            formatted = only_digits[:2] + '/' + only_digits[2:]
        elif len(only_digits) <= 8:
            formatted = only_digits[:2] + '/' + only_digits[2:4] + '/' + only_digits[4:]
        else:
            formatted = text
        
        # Atualiza o campo se necessário
        if text != formatted:
            self.nasc_edit.blockSignals(True)
            self.nasc_edit.setText(formatted)
            self.nasc_edit.blockSignals(False)

    def formatar_nif(self, text):
        """Formata o NIF no formato 123 456 789"""
        # Remove caracteres não numéricos
        digits = ''.join(filter(str.isdigit, text))
        
        # Limita a 9 dígitos
        if len(digits) > 9:
            digits = digits[:9]
        
        # Formata conforme o número de dígitos
        if len(digits) <= 3:
            formatted = digits
        elif len(digits) <= 6:
            formatted = digits[:3] + ' ' + digits[3:]
        elif len(digits) <= 9:
            formatted = digits[:3] + ' ' + digits[3:6] + ' ' + digits[6:]
        else:
            formatted = text
        
        # Atualiza o campo se necessário
        if text != formatted:
            self.nif_edit.blockSignals(True)
            self.nif_edit.setText(formatted)
            self.nif_edit.blockSignals(False)

    def init_tab_historico(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        historico_widget = QWidget()
        hist_layout = QVBoxLayout(historico_widget)

        # Estado emocional e Biotipo lado a lado
        emo_bio_row = QHBoxLayout()
        self.estado_emo_combo = QComboBox()
        self.estado_emo_combo.addItems([
            '', 'calmo', 'ansioso', 'agitado', 'deprimido', 'indiferente', 'eufórico', 'apático', 'irritável', 'motivado', 'desmotivado', 'confuso', 'triste', 'alegre', 'preocupado', 'tenso', 'relaxado', 'culpado', 'esperançoso', 'pessimista', 'otimista', 'outro'
        ])
        self.estado_emo_combo.setCurrentIndex(0)
        self.estado_emo_combo.setFixedWidth(200)
        self._style_combo_box(self.estado_emo_combo)
        
        emo_bio_row.addWidget(self._create_label('Estado emocional:'))
        emo_bio_row.addWidget(self.estado_emo_combo)
        
        self.biotipo_combo = QComboBox()
        self.biotipo_combo.addItems([
            '', 'Longilíneo', 'Brevilíneo', 'Normolíneo', 'Atlético', 'Outro'
        ])
        self.biotipo_combo.setFixedWidth(200)
        self._style_combo_box(self.biotipo_combo)
        
        emo_bio_row.addSpacing(20)
        emo_bio_row.addWidget(self._create_label('Biotipo:'))
        emo_bio_row.addWidget(self.biotipo_combo)
        emo_bio_row.addStretch()
        hist_layout.addLayout(emo_bio_row)
        # Legenda do biotipo
        self.biotipo_desc = QLabel(
            "Biotipos:<br>"
            "• Longilíneo – magro, esguio, estatura alta<br>"
            "  → Tendência para ansiedade, hiperatividade, digestão rápida<br>"
            "• Brevilíneo – baixo, robusto, arredondado<br>"
            "  → Propenso a retenção, congestão, metabolismo lento<br>"
            "• Normolíneo – equilibrado, proporcional<br>"
            "  → Regulação geral estável, adaptação moderada<br>"
            "• Atlético – musculado, estrutura firme<br>"
            "  → Boa resistência, recuperação rápida, resposta forte a terapias físicas"
        )
        self.biotipo_desc.setWordWrap(True)
        self.biotipo_desc.setStyleSheet('font-size: 12px; color: #555; margin-top: 2px; margin-bottom: 8px;')
        print("✅ Legenda do biotipo clara e alinhada.")
        hist_layout.addWidget(self.biotipo_desc)

        # Toolbar com margens e hover
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { margin-bottom: 8px; }
            QToolButton { margin-right: 6px; padding: 4px 8px; border-radius: 6px; }
            QToolButton:hover { background: #eaf3fa; }
        """)
        self.action_bold = QAction('B', self)
        self.action_bold.setShortcut('Ctrl+B')
        self.action_bold.triggered.connect(lambda: self.toggle_bold())
        self.action_italic = QAction('I', self)
        self.action_italic.setShortcut('Ctrl+I')
        self.action_italic.triggered.connect(lambda: self.toggle_italic())
        self.action_underline = QAction('U', self)
        self.action_underline.setShortcut('Ctrl+U')
        self.action_underline.triggered.connect(lambda: self.toggle_underline())
        self.action_date = QAction('📅', self)
        self.action_date.triggered.connect(self.inserir_data_negrito)
        self.toolbar.addAction(self.action_bold)
        self.toolbar.addAction(self.action_italic)
        self.toolbar.addAction(self.action_underline)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_date)
        hist_layout.addWidget(self.toolbar)

        # Editor de histórico
        self.historico_edit = QTextEdit()
        self.historico_edit.setPlaceholderText(
            "Descreva queixas, sintomas, evolução do caso ou aspetos emocionais relevantes..."
        )
        self.historico_edit.setMinimumHeight(250)  # Altura reduzida para não sobrepor botão guardar
        self.historico_edit.setMaximumHeight(300)  # Altura máxima para controlar melhor
        self._style_text_edit(self.historico_edit)
        hist_layout.addWidget(self.historico_edit)
        hist_layout.addStretch()

        # Rodapé com botão Guardar
        rodape = QHBoxLayout()
        rodape.addStretch()
        self.btn_guardar = QPushButton('💾 Guardar')
        self._style_modern_button(self.btn_guardar, "#4CAF50")
        self.btn_guardar.setFixedWidth(140)
        self.btn_guardar.clicked.connect(self.guardar)
        rodape.addWidget(self.btn_guardar)
        hist_layout.addLayout(rodape)

        # Divisão visual entre editor e IA
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.VLine)
        frame.setLineWidth(2)
        frame.setStyleSheet("color: #e0e0e0; background: #e0e0e0; min-width: 2px;")
        splitter.addWidget(historico_widget)
        splitter.addWidget(frame)
        self.chat_widget = IAChatWidget(self.paciente_data)
        splitter.addWidget(self.chat_widget)
        splitter.setSizes([700, 10, 350])
        layout = QVBoxLayout(self.tab_historico)
        layout.addWidget(splitter)



    def format_text(self, fmt):
        cursor = self.historico_edit.textCursor()
        fmt_obj = self.historico_edit.currentCharFormat()
        if fmt == 'italic':
            fmt_obj.setFontItalic(not fmt_obj.fontItalic())
        elif fmt == 'underline':
            fmt_obj.setFontUnderline(not fmt_obj.fontUnderline())
        cursor.mergeCharFormat(fmt_obj)
        self.historico_edit.setTextCursor(cursor)

    def _data_ja_existe_no_historico(self, data_procurada):
        """
        Verifica de forma robusta se uma data já existe no histórico clínico.
        Retorna: (existe, tipo) onde tipo pode ser 'simples', 'iris' ou None
        """
        # Obter texto puro para verificação mais confiável
        texto_puro = self.historico_edit.toPlainText()
        
        # Verificar se já existe qualquer entrada para esta data
        # Procurar por diferentes padrões no texto
        linhas = texto_puro.split('\n')
        
        for linha in linhas:
            linha_limpa = linha.strip()
            
            # Verificar se é uma linha de data exata
            if linha_limpa == data_procurada:
                return (True, 'simples')
            
            # Verificar se é uma linha de análise de íris
            if linha_limpa.startswith(f'{data_procurada} - Análise de Íris'):
                return (True, 'iris')
        
        return (False, None)

    def _inserir_notas_apos_data(self, data_procurada, notas):
        """
        Método robusto para inserir notas após uma data específica no histórico.
        Trata tanto texto puro quanto HTML formatado.
        
        Args:
            data_procurada (str): Data no formato dd/mm/yyyy
            notas (str): Texto das notas a inserir (pode conter HTML)
            
        Returns:
            bool: True se conseguiu inserir, False caso contrário
        """
        try:
            # Método 1: Procurar na representação HTML
            html_content = self.historico_edit.toHtml()
            
            # Padrões de busca para a data em HTML
            data_patterns = [
                f'<b>{data_procurada}</b>',
                f'<strong>{data_procurada}</strong>',
                data_procurada
            ]
            
            for pattern in data_patterns:
                if pattern in html_content:
                    # Encontrar posição do padrão
                    pos = html_content.find(pattern)
                    if pos != -1:
                        # Encontrar o final do padrão
                        fim_pattern = pos + len(pattern)
                        
                        # Se for tag HTML, pular para depois da tag de fecho
                        if pattern.startswith('<b>'):
                            fim_pattern = html_content.find('</b>', pos) + 4
                        elif pattern.startswith('<strong>'):
                            fim_pattern = html_content.find('</strong>', pos) + 9
                        
                        # Preparar as notas para inserção em HTML
                        if '<br>' in notas or '<b>' in notas:
                            # Já está formatado em HTML
                            notas_html = f'<br>{notas}<br>'
                        else:
                            # Converter texto puro para HTML
                            notas_html = f'<br>{notas.replace(chr(10), "<br>")}<br>'
                        
                        # Inserir as notas
                        novo_html = html_content[:fim_pattern] + notas_html + html_content[fim_pattern:]
                        self.historico_edit.setHtml(novo_html)
                        
                        # Mover cursor para o final
                        cursor = self.historico_edit.textCursor()
                        cursor.movePosition(QTextCursor.MoveOperation.End)
                        self.historico_edit.setTextCursor(cursor)
                        
                        return True
            
            # Método 2: Busca usando find() do QTextEdit
            self.historico_edit.moveCursor(QTextCursor.MoveOperation.Start)
            encontrou = self.historico_edit.find(data_procurada)
            
            if encontrou:
                cursor = self.historico_edit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                
                # Inserir as notas usando insertHtml se contiver HTML
                if '<br>' in notas or '<b>' in notas:
                    cursor.insertHtml(f'<br>{notas}<br>')
                else:
                    cursor.insertText(f'\n{notas}\n')
                
                return True
            
            # Método 3: Busca manual por linhas de texto puro
            texto_puro = self.historico_edit.toPlainText()
            linhas = texto_puro.split('\n')
            
            for i, linha in enumerate(linhas):
                if data_procurada in linha.strip():
                    # Posicionar cursor na linha da data
                    cursor = self.historico_edit.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.Start)
                    
                    # Mover para a linha correta
                    for _ in range(i):
                        cursor.movePosition(QTextCursor.MoveOperation.Down)
                    
                    # Mover para o final da linha
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                    
                    # Inserir as notas
                    if '<br>' in notas or '<b>' in notas:
                        cursor.insertHtml(f'<br>{notas}<br>')
                    else:
                        cursor.insertText(f'\n{notas}\n')
                    
                    return True
            
            print(f"[DEBUG] Não foi possível encontrar a data '{data_procurada}' no histórico")
            return False
            
        except Exception as e:
            print(f"[ERRO] Erro ao inserir notas após data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def toggle_bold(self):
        """Aplica/remove formatação de negrito no texto selecionado"""
        try:
            cursor = self.historico_edit.textCursor()
            if cursor.hasSelection():
                # Texto selecionado - aplicar/remover negrito
                format = cursor.charFormat()
                current_weight = format.fontWeight()
                if current_weight == QFont.Weight.Bold:
                    # Remover negrito
                    format.setFontWeight(QFont.Weight.Normal)
                    print("[DEBUG] Negrito removido")
                else:
                    # Aplicar negrito
                    format.setFontWeight(QFont.Weight.Bold)
                    print("[DEBUG] Negrito aplicado")
                cursor.mergeCharFormat(format)
                # Manter seleção ativa para visual feedback
                self.historico_edit.setTextCursor(cursor)
            else:
                # Nenhuma seleção - alternar estado para próxima digitação
                format = self.historico_edit.currentCharFormat()
                current_weight = format.fontWeight()
                if current_weight == QFont.Weight.Bold:
                    format.setFontWeight(QFont.Weight.Normal)
                    print("[DEBUG] Modo negrito desativado")
                else:
                    format.setFontWeight(QFont.Weight.Bold)
                    print("[DEBUG] Modo negrito ativado")
                self.historico_edit.setCurrentCharFormat(format)
        except Exception as e:
            print(f"[DEBUG] Erro toggle_bold: {e}")
    
    def toggle_italic(self):
        """Aplica/remove formatação de itálico no texto selecionado"""
        try:
            cursor = self.historico_edit.textCursor()
            if cursor.hasSelection():
                format = cursor.charFormat()
                current_italic = format.fontItalic()
                format.setFontItalic(not current_italic)
                cursor.mergeCharFormat(format)
                self.historico_edit.setTextCursor(cursor)
                print(f"[DEBUG] Itálico {'removido' if current_italic else 'aplicado'}")
            else:
                format = self.historico_edit.currentCharFormat()
                current_italic = format.fontItalic()
                format.setFontItalic(not current_italic)
                self.historico_edit.setCurrentCharFormat(format)
                print(f"[DEBUG] Modo itálico {'desativado' if current_italic else 'ativado'}")
        except Exception as e:
            print(f"[DEBUG] Erro toggle_italic: {e}")
    
    def toggle_underline(self):
        """Aplica/remove formatação de sublinhado no texto selecionado"""
        try:
            cursor = self.historico_edit.textCursor()
            if cursor.hasSelection():
                format = cursor.charFormat()
                current_underline = format.fontUnderline()
                format.setFontUnderline(not current_underline)
                cursor.mergeCharFormat(format)
                self.historico_edit.setTextCursor(cursor)
                print(f"[DEBUG] Sublinhado {'removido' if current_underline else 'aplicado'}")
            else:
                format = self.historico_edit.currentCharFormat()
                current_underline = format.fontUnderline()
                format.setFontUnderline(not current_underline)
                self.historico_edit.setCurrentCharFormat(format)
                print(f"[DEBUG] Modo sublinhado {'desativado' if current_underline else 'ativado'}")
        except Exception as e:
            print(f"[DEBUG] Erro toggle_underline: {e}")

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
        d = self.paciente_data
        self.nome_edit.setText(d.get('nome', ''))
        self.sexo_combo.setCurrentText(d.get('sexo', ''))
        nasc = d.get('data_nascimento')
        if nasc:
            try:
                self.nasc_edit.setDate(QDate.fromString(nasc, 'dd/MM/yyyy'))
            except:
                pass
        self.naturalidade_edit.setText(d.get('naturalidade', ''))
        self.profissao_edit.setText(d.get('profissao', ''))
        self.estado_civil_combo.setCurrentText(d.get('estado_civil', ''))
        self.contacto_edit.setText(d.get('contacto', ''))
        self.email_edit.setText(d.get('email', ''))
        
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
        
        # REMOVIDO: Campos biotipo e estado emocional não existem mais na nova interface
        # self.estado_emo_combo.setCurrentText(d.get('estado_emocional', ''))
        # self.biotipo_combo.setCurrentText(d.get('biotipo', ''))
        
        # Histórico clínico
        historico = d.get('historico', [])
        # print('DEBUG HISTÓRICO:', type(historico), str(historico)[:120])  # Comentar para reduzir output
        # 1. Formato texto+tags
        if isinstance(historico, dict) and 'text' in historico and 'tags' in historico:
            print('Formato: texto+tags')
            html = self.text_with_tags_to_html(historico['text'], historico['tags'])
            self.historico_edit.setHtml(html)
        # 2. JSON rich text (lista de chars)
        elif isinstance(historico, str) and historico.strip().startswith('[{'):
            print('Formato: JSON rich text')
            try:
                historico_json = json.loads(historico)
                html = self.json_richtext_to_html(historico_json)
                self.historico_edit.setHtml(html)
            except Exception as e:
                print('Erro ao converter histórico JSON:', e)
                self.historico_edit.setPlainText(historico)
        # 3. HTML (tem tags <b>, <div>, etc.)
        elif isinstance(historico, str) and ('<' in historico and '>' in historico):
            print('Formato: HTML')
            self.historico_edit.setHtml(historico)
        # 4. Lista de dicts (ex: [{'data':..., 'texto':...}, ...])
        elif isinstance(historico, list) and all(isinstance(x, dict) for x in historico):
            print('Formato: lista de dicts')
            texto = ''
            for item in historico[-5:]:
                data = item.get('data', '')
                texto_item = item.get('texto', '')
                texto += f"""
                    <div style='margin-bottom: 18px; padding-bottom: 8px; border-bottom: 1px dashed #aaa;'>
                        <div style='font-weight: bold; font-size: 14px; color: #2a2a2a;'>{data}</div>
                        <div style='margin-top: 6px;'>{texto_item}</div>
                    </div>
                """
            self.historico_edit.setHtml(texto)
        # 5. Lista de strings
        elif isinstance(historico, list) and all(isinstance(x, str) for x in historico):
            print('Formato: lista de strings')
            self.historico_edit.setHtml('<br>'.join(historico))
        # 6. Texto simples
        elif isinstance(historico, str):
            print('Formato: texto simples')
            self.historico_edit.setPlainText(historico)
        # 7. Notas antigas migradas para histórico
        elif d.get('notas') and not self.historico_edit.toPlainText():
            print('Formato: notas antigas')
            self.historico_edit.setHtml(d.get('notas'))
        else:
            print('Formato desconhecido')
            self.historico_edit.setPlainText(str(historico))
        
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

    def guardar(self):
        """Guarda os dados do utente na base de dados"""
        from db_manager import DBManager
        dados = {
            'nome': self.nome_edit.text(),
            'sexo': self.sexo_combo.currentText(),
            'data_nascimento': self.nasc_edit.date().toString('dd/MM/yyyy'),  # Volta para QDate
            'naturalidade': self.naturalidade_edit.text(),
            'profissao': self.profissao_edit.text(),
            'estado_civil': self.estado_civil_combo.currentText(),
            'contacto': self.contacto_edit.text(),
            'email': self.email_edit.text(),
            'local_habitual': getattr(self, 'local_combo', None) and self.local_combo.currentText() or '',
            # APENAS campos que EXISTEM na interface atual
            'observacoes': getattr(self, 'observacoes_edit', None) and self.observacoes_edit.text() or '',
            'conheceu': getattr(self, 'conheceu_combo', None) and self.conheceu_combo.currentText() or '',
            'referenciado': getattr(self, 'referenciado_edit', None) and self.referenciado_edit.text() or '',
            'nif': getattr(self, 'nif_edit', None) and self.nif_edit.text() or '',
            # CORREÇÃO URGENTE: Adicionar histórico clínico!
            'historico': getattr(self, 'historico_edit', None) and self.historico_edit.toHtml() or ''
            # REMOVIDOS: cc, emergencia, parentesco - NÃO existem na interface!
        }
        if 'id' in self.paciente_data:
            dados['id'] = self.paciente_data['id']
        db = DBManager()
        # Prevenção de duplicação por nome + data_nascimento
        query = "SELECT * FROM pacientes WHERE nome = ? AND data_nascimento = ?"
        params = (dados['nome'], dados['data_nascimento'])
        duplicados = db.execute_query(query, params)
        if duplicados and (not ('id' in dados and duplicados[0].get('id') == dados['id'])):
            from biodesk_dialogs import mostrar_aviso
            mostrar_aviso(self, "Duplicado", "Já existe um utente com este nome e data de nascimento.")
            return
        novo_id = db.save_or_update_paciente(dados)
        if novo_id != -1:
            self.paciente_data['id'] = novo_id
            self.setWindowTitle(dados['nome'])
            self.dirty = False
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(self, "Sucesso", "Utente guardado com sucesso!")
        else:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", "Erro ao guardar utente.")

    @staticmethod
    def mostrar_seletor(callback, parent=None):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMenu, QHeaderView
        from PyQt6.QtCore import Qt, QPoint
        
        class SeletorDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle('🔍 Procurar utente')
                self.setModal(True)
                self.resize(1000, 700)  # Tamanho adequado para a tabela
                self.db = DBManager()
                self.resultados = []
                
                # Estilo geral do diálogo (moderno da iridologia)
                self.setStyleSheet("""
                    QDialog {
                        background-color: #ffffff;
                        border-radius: 16px;
                    }
                    QLabel {
                        font-size: 16px;
                        font-weight: 600;
                        color: #2c3e50;
                        margin-bottom: 8px;
                    }
                    QLineEdit {
                        background-color: #f8f9fa;
                        color: #2c3e50;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 12px 16px;
                        margin: 4px;
                    }
                    QLineEdit:focus {
                        border-color: #007bff;
                        background-color: #ffffff;
                    }
                    QLineEdit::placeholder {
                        color: #6c757d;
                        font-style: italic;
                        font-weight: normal;
                    }
                """)
                
                layout = QVBoxLayout(self)
                layout.setContentsMargins(24, 24, 24, 24)
                layout.setSpacing(20)
                
                # Título elegante
                title_label = QLabel("👥 Selecionar Paciente")
                title_label.setStyleSheet("""
                    QLabel {
                        font-size: 20px;
                        font-weight: 700;
                        color: #2c3e50;
                        padding: 0 0 16px 0;
                        border-bottom: 2px solid #e3f2fd;
                        margin-bottom: 16px;
                    }
                """)
                layout.addWidget(title_label)
                
                # Filtros organizados em grid
                filtros_label = QLabel("🔍 Filtros de Pesquisa")
                layout.addWidget(filtros_label)
                
                filtros_grid = QHBoxLayout()
                filtros_grid.setSpacing(12)
                
                self.nome_edit = QLineEdit()
                self.nome_edit.setPlaceholderText('Nome do paciente')
                
                self.nasc_edit = QLineEdit()
                self.nasc_edit.setPlaceholderText('Data nascimento (dd/mm/aaaa)')
                
                self.contacto_edit = QLineEdit()
                self.contacto_edit.setPlaceholderText('Contacto telefónico')
                
                self.email_edit = QLineEdit()
                self.email_edit.setPlaceholderText('Email')
                
                for w in [self.nome_edit, self.nasc_edit, self.contacto_edit, self.email_edit]:
                    filtros_grid.addWidget(w)
                layout.addLayout(filtros_grid)
                
                # Botões com estilo moderno da iridologia
                btns = QHBoxLayout()
                btns.setSpacing(12)
                
                self.btn_abrir = QPushButton('✅  Abrir Paciente')
                self.btn_abrir.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #28a745;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 12px 20px;
                        min-height: 20px;
                    }
                    QPushButton:hover {
                        background-color: #28a745;
                        color: white;
                        border-color: #28a745;                    }
                    QPushButton:pressed {
                        background-color: #1e7e34;
                        border-color: #1e7e34;
                    }
                """)
                self.btn_abrir.clicked.connect(self.abrir)
                
                self.btn_eliminar = QPushButton('🗑️  Eliminar')
                self.btn_eliminar.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #dc3545;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 12px 20px;
                        min-height: 20px;
                    }
                    QPushButton:hover {
                        background-color: #dc3545;
                        color: white;
                        border-color: #dc3545;                    }
                    QPushButton:pressed {
                        background-color: #c82333;
                        border-color: #c82333;
                    }
                """)
                self.btn_eliminar.clicked.connect(self.eliminar)
                
                btns.addStretch()
                btns.addWidget(self.btn_abrir)
                btns.addWidget(self.btn_eliminar)
                layout.addLayout(btns)
                
                # Lista de resultados modernizada com colunas
                resultados_label = QLabel("📋 Resultados da Pesquisa")
                layout.addWidget(resultados_label)
                
                self.tabela = QTableWidget()
                self.tabela.setColumnCount(4)
                self.tabela.setHorizontalHeaderLabels(["Nome", "Data Nascimento", "Contacto", "Email"])
                
                # Configurar larguras das colunas
                header = self.tabela.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nome expandir
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Data fixa
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Contacto fixo
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Email expandir
                self.tabela.setColumnWidth(1, 160)  # Data nascimento (aumentada)
                self.tabela.setColumnWidth(2, 120)  # Contacto
                
                # Estilo moderno da tabela
                self.tabela.setStyleSheet("""
                    QTableWidget {
                        background-color: #f8f9fa;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        font-size: 14px;
                        gridline-color: #e9ecef;
                    }
                    QTableWidget::item {
                        background-color: white;
                        color: #2c3e50;
                        padding: 12px 8px;
                        border-bottom: 1px solid #e9ecef;
                        font-weight: 500;
                    }
                    QTableWidget::item:hover {
                        background-color: #007bff;
                        color: white;
                    }
                    QTableWidget::item:selected {
                        background-color: #0056b3;
                        color: white;
                        font-weight: bold;
                    }
                    QHeaderView::section {
                        background-color: #e9ecef;
                        color: #495057;
                        border: 1px solid #dee2e6;
                        padding: 8px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QHeaderView::section:hover {
                        background-color: #007bff;
                        color: white;
                    }
                """)
                
                # Configurações da tabela
                self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                self.tabela.setAlternatingRowColors(False)
                self.tabela.verticalHeader().setVisible(False)
                self.tabela.setSortingEnabled(True)
                
                # Eventos
                self.tabela.itemDoubleClicked.connect(self.abrir)
                self.tabela.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                self.tabela.customContextMenuRequested.connect(self.menu_contexto)
                layout.addWidget(self.tabela, 1)
                
                # Pesquisa ao escrever
                self.nome_edit.textChanged.connect(self.pesquisar)
                self.nasc_edit.textChanged.connect(self.pesquisar)
                self.contacto_edit.textChanged.connect(self.pesquisar)
                self.email_edit.textChanged.connect(self.pesquisar)
                self.pesquisar()
            def normalizar(self, s):
                if not s: return ''
                return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()
            def pesquisar(self):
                todos = self.db.get_all_pacientes()
                nome = self.normalizar(self.nome_edit.text())
                nasc = self.nasc_edit.text().strip()
                contacto = self.contacto_edit.text().replace(' ', '')
                email = self.normalizar(self.email_edit.text())
                
                # Limpar tabela
                self.tabela.setRowCount(0)
                self.resultados = []
                
                for p in todos:
                    if nome and nome not in self.normalizar(p.get('nome', '')):
                        continue
                    if nasc and nasc not in (p.get('data_nascimento') or ''):
                        continue
                    if contacto and contacto not in (p.get('contacto') or '').replace(' ', ''):
                        continue
                    if email and email not in self.normalizar(p.get('email', '')):
                        continue
                    
                    # Adicionar à tabela
                    self.resultados.append(p)
                    row = self.tabela.rowCount()
                    self.tabela.insertRow(row)
                    
                    # Preencher colunas
                    self.tabela.setItem(row, 0, QTableWidgetItem(p.get('nome', '')))
                    self.tabela.setItem(row, 1, QTableWidgetItem(p.get('data_nascimento', '')))
                    self.tabela.setItem(row, 2, QTableWidgetItem(p.get('contacto', '')))
                    self.tabela.setItem(row, 3, QTableWidgetItem(p.get('email', '')))
            def abrir(self):
                row = self.tabela.currentRow()
                if row >= 0 and row < len(self.resultados):
                    paciente = self.resultados[row]
                    self.accept()
                    callback(paciente)
            def eliminar(self):
                row = self.tabela.currentRow()
                if row >= 0 and row < len(self.resultados):
                    paciente = self.resultados[row]
                    from biodesk_dialogs import mostrar_confirmacao
                    if mostrar_confirmacao(
                        self, 
                        "Eliminar utente",
                        f"Tem a certeza que deseja eliminar o utente '{paciente.get('nome','')}'?"
                    ):
                        self.db.execute_query(f"DELETE FROM pacientes WHERE id = ?", (paciente['id'],))
                        self.pesquisar()
            def menu_contexto(self, pos: QPoint):
                item = self.tabela.itemAt(pos)
                if not item:
                    return
                row = item.row()
                if row < 0 or row >= len(self.resultados):
                    return
                menu = QMenu(self)
                menu.addAction('Abrir utente', self.abrir)
                menu.addAction('🗑️ Eliminar', self.eliminar)
                menu.exec(self.tabela.mapToGlobal(pos))
        dlg = SeletorDialog(parent)
        dlg.exec()

    # ========================================================================
    # SISTEMA DE FOLLOW-UP AUTOMÁTICO
    # ========================================================================
    
    def _init_scheduler_safe(self):
        """Inicializa APScheduler de forma segura, evitando múltiplas instâncias."""
        try:
            # Verificar se já existe uma instância global do scheduler
            if not hasattr(FichaPaciente, '_global_scheduler') or FichaPaciente._global_scheduler is None:
                jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///followup_jobs.db')}
                executors = {'default': ThreadPoolExecutor(10)}  # Reduzido de 20 para 10
                job_defaults = {'coalesce': False, 'max_instances': 2}  # Reduzido de 3 para 2
                
                FichaPaciente._global_scheduler = BackgroundScheduler(
                    jobstores=jobstores,
                    executors=executors,
                    job_defaults=job_defaults
                )
                FichaPaciente._global_scheduler.start()
                # Scheduler de follow-up iniciado
            
            # Usar a instância global
            self.scheduler = FichaPaciente._global_scheduler
            
        except Exception as e:
            print(f"⚠️ Erro ao iniciar scheduler de follow-up: {e}")
            self.scheduler = None
    
    def _init_scheduler(self):
        """Inicializa APScheduler com jobstore SQLite (persistente)."""
        try:
            jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///followup_jobs.db')}
            executors = {'default': ThreadPoolExecutor(20)}
            job_defaults = {'coalesce': False, 'max_instances': 3}
            
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults
            )
            self.scheduler.start()
            # Scheduler de follow-up iniciado
        except Exception as e:
            print(f"⚠️ Erro ao iniciar scheduler de follow-up: {e}")
            self.scheduler = None
    
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
        """Abre dialog para agendar follow-up após consulta."""
        if not self.paciente_data or not self.paciente_data.get('nome'):
            QMessageBox.warning(self, "Aviso", "Por favor, carregue um paciente primeiro.")
            return
            
        dialog = FollowUpDialog(self.paciente_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Dialog retorna os dados do agendamento
            followup_data = dialog.get_followup_data()
            self._agendar_followup(followup_data)

    def _agendar_followup(self, followup_data):
        """Agenda um follow-up com os dados fornecidos."""
        try:
            when_dt = followup_data['quando']
            tipo = followup_data['tipo']
            is_custom = followup_data.get('is_custom', False)
            
            # Ajustar para horário comercial (11h-17h) APENAS se NÃO for personalizado
            if not is_custom:
                when_dt = self._adjust_to_business_hours(when_dt)
            
            if when_dt <= datetime.now():
                QMessageBox.warning(self, "Erro", "A data/hora deve ser no futuro.")
                return
                
            paciente_id = self.paciente_data.get('id')
            job_id = f"followup_{paciente_id}_{tipo}_{int(when_dt.timestamp())}"
            
            if hasattr(self, 'scheduler') and self.scheduler:
                self.scheduler.add_job(
                    func=send_followup_job_static,
                    trigger='date',
                    run_date=when_dt,
                    args=[paciente_id, tipo, followup_data.get('dias_apos', 3)],
                    id=job_id,
                    replace_existing=True
                )
                
                # Registar no histórico
                historico_txt = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Follow-up agendado: {tipo} para {when_dt.strftime('%d/%m/%Y %H:%M')}"
                self.db.adicionar_historico(paciente_id, historico_txt)
                
                # Criar dialog personalizado de confirmação
                self._show_followup_confirmation(tipo, when_dt)
                
                print(f"📅 Follow-up agendado: {when_dt} (job_id={job_id})")
            else:
                QMessageBox.warning(self, "Erro", "Sistema de agendamento não disponível.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao agendar follow-up: {e}")
            print(f"❌ Erro ao agendar follow-up: {e}")

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
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
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
            btn_cancelar.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            
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
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
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
            from biodesk_dialogs import mostrar_confirmacao
            if not mostrar_confirmacao(
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

    def abrir_terapia_com_iris(self, tipo_iris, caminho_imagem):
        """
        Abre o módulo de terapia quântica enviando os dados da íris.
        
        Args:
            tipo_iris: str - "esq" ou "drt" para indicar qual olho
            caminho_imagem: str - caminho para a imagem da íris
        """
        try:
            from terapia_quantica import TerapiaQuantica
            self.terapia_window = TerapiaQuantica(
                paciente_data=self.paciente_data,
                iris_data={
                    'tipo': tipo_iris,
                    'caminho': caminho_imagem
                }
            )
            self.terapia_window.show_maximized_safe()  # Usar maximização segura
        except ImportError:
            from biodesk_dialogs import mostrar_informacao
            mostrar_informacao(
                self,
                "Exportar para terapia quântica",
                "Módulo de Terapia Quântica em desenvolvimento."
            )



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
        # self.init_sub_aba_declaracao_saude()  # REMOVIDO - evitar duplicação

    def init_sub_aba_declaracao_saude(self):
        """Inicializa a sub-aba de Declaração de Estado de Saúde"""
        # Usar exatamente o mesmo layout da função principal
        layout = QVBoxLayout(self.tab_declaracao_saude)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ====== CABEÇALHO ======
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2980b9;
                border-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        titulo_declaracao = QLabel("🩺 Declaração de Estado de Saúde")
        titulo_declaracao.setStyleSheet("""
            font-size: 20px; 
            font-weight: 700; 
            color: white; 
            margin: 0px;
        """)
        header_layout.addWidget(titulo_declaracao)
        
        header_layout.addStretch()
        
        # Status da declaração
        self.status_declaracao = QLabel("❌ Não preenchida")
        self.status_declaracao.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600;
            color: #ffffff;
            padding: 15px;
            background-color: rgba(255,255,255,0.2);
            border-radius: 6px;
        """)
        header_layout.addWidget(self.status_declaracao)
        
        layout.addWidget(header_frame)
        
        # ====== ÁREA PRINCIPAL DIVIDIDA ======
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        
        # ====== ESQUERDA: FORMULÁRIO ======
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(10)
        
        # ====== TEMPLATE HTML DA DECLARAÇÃO ======
        self.template_declaracao = self._criar_template_declaracao_saude()
        
        # WebEngine para a declaração com formulários interativos
        self.texto_declaracao_editor = QWebEngineView()
        self.texto_declaracao_editor.setMinimumHeight(400)
        self.texto_declaracao_editor.setMaximumHeight(600)
        self.texto_declaracao_editor.setHtml(self.template_declaracao)
        
        # Adicionar editor diretamente ao layout principal
        form_layout.addWidget(self.texto_declaracao_editor)
        
        main_layout.addWidget(form_frame, 2)  # 2/3 do espaço
        
        # ====== DIREITA: AÇÕES ======
        acoes_frame = QFrame()
        acoes_frame.setFixedWidth(250)
        acoes_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
        """)
        acoes_layout = QVBoxLayout(acoes_frame)
        acoes_layout.setContentsMargins(15, 15, 15, 15)
        acoes_layout.setSpacing(15)
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
        
        # ====== BOTÕES MINI COM CSS DIRETO FORÇADO ======
        # Primeira linha: Imprimir + PDF
        linha1_layout = QHBoxLayout()
        linha1_layout.setSpacing(8)
        
        btn_imprimir_declaracao = QPushButton("🖨️")
        btn_imprimir_declaracao.setFixedSize(65, 28)
        btn_imprimir_declaracao.setToolTip("Imprimir Declaração")
        btn_imprimir_declaracao.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        btn_imprimir_declaracao.clicked.connect(self.imprimir_declaracao_saude)
        linha1_layout.addWidget(btn_imprimir_declaracao)
        
        btn_pdf_declaracao = QPushButton("📄")
        btn_pdf_declaracao.setFixedSize(65, 28)
        btn_pdf_declaracao.setToolTip("Gerar PDF")
        btn_pdf_declaracao.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_pdf_declaracao.clicked.connect(self.gerar_pdf_declaracao_saude)
        linha1_layout.addWidget(btn_pdf_declaracao)
        
        acoes_layout.addLayout(linha1_layout)
        
        # Segunda linha: Guardar + Limpar
        linha2_layout = QHBoxLayout()
        linha2_layout.setSpacing(8)
        
        btn_guardar_declaracao = QPushButton("💾")
        btn_guardar_declaracao.setFixedSize(65, 28)
        btn_guardar_declaracao.setToolTip("Guardar Declaração")
        btn_guardar_declaracao.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_guardar_declaracao.clicked.connect(self.guardar_declaracao_saude)
        linha2_layout.addWidget(btn_guardar_declaracao)
        
        btn_limpar_declaracao = QPushButton("🗑️")
        btn_limpar_declaracao.setFixedSize(65, 28)
        btn_limpar_declaracao.setToolTip("Limpar Declaração")
        btn_limpar_declaracao.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_limpar_declaracao.clicked.connect(self.limpar_declaracao_saude)
        linha2_layout.addWidget(btn_limpar_declaracao)
        
        acoes_layout.addLayout(linha2_layout)
        
        # Separador visual
        acoes_layout.addSpacing(8)
        
        # Botão de assinatura (texto compacto)
        btn_assinar_declaracao = QPushButton("✍️ Assinar")
        btn_assinar_declaracao.setFixedSize(146, 32)
        btn_assinar_declaracao.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        btn_assinar_declaracao.clicked.connect(self.assinar_declaracao_saude)
        acoes_layout.addWidget(btn_assinar_declaracao)
        
        # Botão de importação (secundário)
        btn_importar_manual = QPushButton("📁 Importar")
        btn_importar_manual.setFixedSize(146, 28)
        btn_importar_manual.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_importar_manual.clicked.connect(self.importar_pdf_manual)
        acoes_layout.addWidget(btn_importar_manual)
        
        acoes_layout.addStretch()
        main_layout.addWidget(acoes_frame)
        
        # Pequena margem direita para não ir até o extremo
        main_layout.addSpacing(20)
        
        # Adicionar layout horizontal ao layout principal
        layout.addLayout(main_layout, 1)
        
        # Atualizar informações do paciente na declaração
        self.atualizar_info_paciente_declaracao()

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
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 13px !important;
                    font-weight: 600 !important;
                    border: none !important;
                    border-radius: 8px !important;
                    padding: 10px 15px !important;
                    background-color: {cor} !important;
                    color: #2c3e50 !important;
                    text-align: left !important;
                    min-width: 220px !important;
                    max-width: 220px !important;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(cor, 15)} !important;
                    color: #2c3e50 !important;
                }}
                QPushButton:checked {{
                    background-color: {self._lighten_color(cor, 25)} !important;
                    color: #2c3e50 !important;
                }}
            """)
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
        self._style_text_edit(self.editor_consentimento)
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
        btn_assinatura_externa.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 18px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        btn_assinatura_externa.clicked.connect(self.gerar_pdf_para_assinatura_externa)
        acoes_layout.addWidget(btn_assinatura_externa)
        
        # Botão de importação manual (para casos onde a automação falha)
        btn_importar_manual_consent = QPushButton("📁 Importar Assinado")
        btn_importar_manual_consent.setFixedSize(210, 35)
        btn_importar_manual_consent.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
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
            
            # Preparar assinaturas (se existirem)
            assinatura_paciente = None
            assinatura_terapeuta = None
            
            if hasattr(self, 'signature_canvas_paciente') and self.signature_canvas_paciente:
                try:
                    # Verificar se assinatura não está vazia
                    if not self.signature_canvas_paciente.is_empty():
                        # Converter assinatura para bytes
                        pixmap = self.signature_canvas_paciente.get_signature_image()
                        # Converter QPixmap para QImage e depois para bytes
                        image = pixmap.toImage()
                        from PyQt6.QtCore import QByteArray, QBuffer
                        
                        byte_array = QByteArray()
                        buffer = QBuffer(byte_array)
                        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                        image.save(buffer, "PNG")
                        assinatura_paciente = byte_array.data()
                        print(f"[DEBUG] Assinatura paciente capturada: {len(assinatura_paciente)} bytes")
                    else:
                        print(f"[DEBUG] Assinatura paciente está vazia - ignorada")
                except Exception as e:
                    print(f"[DEBUG] Erro ao processar assinatura do paciente: {e}")
            
            if hasattr(self, 'signature_canvas_terapeuta') and self.signature_canvas_terapeuta:
                try:
                    # Verificar se assinatura não está vazia
                    if not self.signature_canvas_terapeuta.is_empty():
                        # Converter assinatura para bytes
                        pixmap = self.signature_canvas_terapeuta.get_signature_image()
                        # Converter QPixmap para QImage e depois para bytes
                        image = pixmap.toImage()
                        from PyQt6.QtCore import QByteArray, QBuffer
                        
                        byte_array = QByteArray()
                        buffer = QBuffer(byte_array)
                        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                        image.save(buffer, "PNG")
                        assinatura_terapeuta = byte_array.data()
                        print(f"[DEBUG] Assinatura terapeuta capturada: {len(assinatura_terapeuta)} bytes")
                    else:
                        print(f"[DEBUG] Assinatura terapeuta está vazia - ignorada")
                except Exception as e:
                    print(f"[DEBUG] Erro ao processar assinatura do terapeuta: {e}")
            
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
                
                # Criar tabela
                dados_tabela = [linha_labels, linha_nomes, linha_assinaturas, linha_datas]
                tabela_assinaturas = Table(dados_tabela, colWidths=[4*inch, 4*inch])
                
                # Estilo da tabela
                estilo_tabela = TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
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
            btn_cancelar.setStyleSheet("""
                QPushButton { background-color: #6c757d; color: white; border: none; 
                              border-radius: 6px; font-weight: bold; font-size: 12px; }
                QPushButton:hover { background-color: #5a6268; }
            """)
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            btn_anular = QPushButton("🗑️ Anular Completamente")
            btn_anular.setFixedSize(180, 40)
            btn_anular.setStyleSheet("""
                QPushButton { background-color: #dc3545; color: white; border: none; 
                              border-radius: 6px; font-weight: bold; font-size: 12px; }
                QPushButton:hover { background-color: #c82333; }
            """)
            
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
                'signature_canvas_paciente',
                'signature_canvas_terapeuta', 
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
                        width: 100%;
                        margin-top: 10pt;
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
        """Abre diálogo para assinatura digital do paciente com canvas interativo"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
            
            # Criar diálogo de assinatura
            dialog = QDialog(self)
            dialog.setWindowTitle("Assinatura Digital - Paciente")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            titulo = QLabel(f"✍️ Assinatura do Paciente: {self.paciente_data.get('nome', 'N/A')}")
            titulo.setStyleSheet("font-size: 16px; font-weight: 600; color: #2c3e50; padding: 10px;")
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Instruções
            instrucoes = QLabel("🖊️ Assine abaixo:")
            instrucoes.setStyleSheet("font-size: 12px; color: #7f8c8d; padding: 5px;")
            instrucoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(instrucoes)
            
            # Canvas de assinatura
            signature_canvas = SignatureCanvas()
            signature_canvas.setMinimumHeight(200)
            layout.addWidget(signature_canvas)
            
            # Armazenar referência para uso no PDF
            self.signature_canvas_paciente = signature_canvas
            
            # Botões
            botoes_layout = QHBoxLayout()
            
            btn_limpar = QPushButton("🗑️ Limpar")
            self._style_modern_button(btn_limpar, "#e74c3c")
            btn_limpar.clicked.connect(signature_canvas.clear_signature)
            botoes_layout.addWidget(btn_limpar)
            
            botoes_layout.addStretch()
            
            btn_cancelar = QPushButton("❌ Cancelar")
            self._style_modern_button(btn_cancelar, "#95a5a6")
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            btn_confirmar = QPushButton("✅ Confirmar Assinatura")
            self._style_modern_button(btn_confirmar, "#27ae60")
            
            def confirmar_assinatura_paciente():
                """Captura assinatura antes de fechar o diálogo"""
                try:
                    if not signature_canvas.is_empty():
                        # Capturar assinatura imediatamente
                        pixmap = signature_canvas.get_signature_image()
                        image = pixmap.toImage()
                        from PyQt6.QtCore import QByteArray, QBuffer
                        byte_array = QByteArray()
                        buffer = QBuffer(byte_array)
                        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                        image.save(buffer, "PNG")
                        
                        # Armazenar por tipo de consentimento atual
                        tipo_atual = getattr(self, 'tipo_consentimento_atual', 'geral')
                        if tipo_atual not in self.assinaturas_por_tipo:
                            self.assinaturas_por_tipo[tipo_atual] = {}
                        self.assinaturas_por_tipo[tipo_atual]['paciente'] = byte_array.data()
                        
                        # Também guardar na variável atual (compatibilidade)
                        self.assinatura_paciente_data = byte_array.data()
                        
                        print(f"✅ [ASSINATURA] Paciente capturada para tipo '{tipo_atual}': {len(self.assinatura_paciente_data)} bytes")
                        
                        # Atualizar botão visual - FORÇAR ATUALIZAÇÃO
                        self.assinatura_paciente.setText("✅ Assinado")
                        self.assinatura_paciente.setStyleSheet("""
                            QPushButton {
                                background-color: #27ae60 !important; color: white !important; border: none !important;
                                border-radius: 6px; padding: 8px 15px; font-weight: bold;
                            }
                            QPushButton:hover { background-color: #229954 !important; }
                        """)
                        
                        # Força refresh visual
                        self.assinatura_paciente.update()
                        self.assinatura_paciente.repaint()
                        
                        # DEBUG - Verificar estado
                        print(f"🔍 [DEBUG] Botão paciente texto após atualização: '{self.assinatura_paciente.text()}'")
                        print(f"🔍 [DEBUG] Assinatura paciente data definida: {self.assinatura_paciente_data is not None}")
                        print(f"🔍 [DEBUG] Assinaturas por tipo: {list(self.assinaturas_por_tipo.keys())}")
                        
                        dialog.accept()
                    else:
                        from biodesk_dialogs import mostrar_aviso
                        mostrar_aviso(dialog, "Assinatura Vazia", "Por favor, assine no campo antes de confirmar.")
                except Exception as e:
                    print(f"❌ [ASSINATURA] Erro ao capturar paciente: {e}")
                    dialog.reject()
            
            btn_confirmar.clicked.connect(confirmar_assinatura_paciente)
            botoes_layout.addWidget(btn_confirmar)
            
            layout.addLayout(botoes_layout)
            
            # Mostrar diálogo
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Salvar assinatura na base de dados se há um consentimento ativo
                if hasattr(self, 'consentimento_ativo') and self.consentimento_ativo:
                    try:
                        # Obter dados da assinatura
                        if not signature_canvas.is_empty():
                            signature_pixmap = signature_canvas.toPixmap()
                            # Converter QPixmap para bytes
                            from PyQt6.QtCore import QBuffer, QIODevice
                            buffer = QBuffer()
                            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                            signature_pixmap.save(buffer, 'PNG')
                            signature_data = buffer.data().data()
                        else:
                            signature_data = None
                            
                        if signature_data:
                            from consentimentos_manager import ConsentimentosManager
                            manager = ConsentimentosManager()
                            
                            # Atualizar consentimento com assinatura do paciente
                            sucesso = manager.atualizar_assinatura_paciente(
                                self.consentimento_ativo['id'],
                                signature_data,
                                self.paciente_data.get('nome', 'Paciente')
                            )
                            
                            if sucesso:
                                print(f"[DEBUG] ✅ Assinatura do paciente salva na BD")
                                # Atualizar visual do botão
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
                            else:
                                print(f"[ERRO] Falha ao salvar assinatura do paciente")
                        else:
                            print(f"[AVISO] Assinatura vazia - não foi salva")
                    except Exception as e:
                        print(f"[ERRO] Erro ao salvar assinatura do paciente: {e}")
                
                # Sempre atualizar visual (mesmo sem BD)
                nome_paciente = self.paciente_data.get('nome', 'Paciente')
                print(f"[DEBUG] Assinatura do paciente confirmada: {nome_paciente}")
            
        except Exception as e:
            print(f"[ERRO] Erro na assinatura do paciente: {e}")
            # Fallback simples
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            self.assinatura_paciente.setText(f"✅ {nome_paciente}")
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
        """Abre diálogo para assinatura digital do terapeuta com canvas interativo"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
            
            # Criar diálogo de assinatura
            dialog = QDialog(self)
            dialog.setWindowTitle("Assinatura Digital - Terapeuta")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            titulo = QLabel("✍️ Assinatura do Terapeuta: Dr. Nuno Correia")
            titulo.setStyleSheet("font-size: 16px; font-weight: 600; color: #2c3e50; padding: 10px;")
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Instruções
            instrucoes = QLabel("🖊️ Assine abaixo:")
            instrucoes.setStyleSheet("font-size: 12px; color: #7f8c8d; padding: 5px;")
            instrucoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(instrucoes)
            
            # Canvas de assinatura
            signature_canvas = SignatureCanvas()
            signature_canvas.setMinimumHeight(200)
            layout.addWidget(signature_canvas)
            
            # Armazenar referência para uso no PDF
            self.signature_canvas_terapeuta = signature_canvas
            
            # Botões
            botoes_layout = QHBoxLayout()
            
            btn_limpar = QPushButton("🗑️ Limpar")
            self._style_modern_button(btn_limpar, "#e74c3c")
            btn_limpar.clicked.connect(signature_canvas.clear_signature)
            botoes_layout.addWidget(btn_limpar)
            
            botoes_layout.addStretch()
            
            btn_cancelar = QPushButton("❌ Cancelar")
            self._style_modern_button(btn_cancelar, "#95a5a6")
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            btn_confirmar = QPushButton("✅ Confirmar Assinatura")
            self._style_modern_button(btn_confirmar, "#27ae60")
            
            def confirmar_assinatura_terapeuta():
                """Captura assinatura antes de fechar o diálogo"""
                try:
                    if not signature_canvas.is_empty():
                        # Capturar assinatura imediatamente
                        pixmap = signature_canvas.get_signature_image()
                        image = pixmap.toImage()
                        from PyQt6.QtCore import QByteArray, QBuffer
                        byte_array = QByteArray()
                        buffer = QBuffer(byte_array)
                        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                        image.save(buffer, "PNG")
                        
                        # Armazenar por tipo de consentimento atual
                        tipo_atual = getattr(self, 'tipo_consentimento_atual', 'geral')
                        if tipo_atual not in self.assinaturas_por_tipo:
                            self.assinaturas_por_tipo[tipo_atual] = {}
                        self.assinaturas_por_tipo[tipo_atual]['terapeuta'] = byte_array.data()
                        
                        # Também guardar na variável atual (compatibilidade)
                        self.assinatura_terapeuta_data = byte_array.data()
                        
                        print(f"✅ [ASSINATURA] Terapeuta capturada para tipo '{tipo_atual}': {len(self.assinatura_terapeuta_data)} bytes")
                        
                        # Atualizar botão visual - FORÇAR ATUALIZAÇÃO
                        self.assinatura_terapeuta.setText("✅ Assinado")
                        self.assinatura_terapeuta.setStyleSheet("""
                            QPushButton {
                                background-color: #27ae60 !important; color: white !important; border: none !important;
                                border-radius: 6px; padding: 8px 15px; font-weight: bold;
                            }
                            QPushButton:hover { background-color: #229954 !important; }
                        """)
                        
                        # Força refresh visual
                        self.assinatura_terapeuta.update()
                        self.assinatura_terapeuta.repaint()
                        
                        # DEBUG - Verificar estado
                        print(f"🔍 [DEBUG] Botão terapeuta texto após atualização: '{self.assinatura_terapeuta.text()}'")
                        print(f"🔍 [DEBUG] Assinatura terapeuta data definida: {self.assinatura_terapeuta_data is not None}")
                        print(f"🔍 [DEBUG] Assinaturas por tipo: {list(self.assinaturas_por_tipo.keys())}")
                        
                        dialog.accept()
                    else:
                        from biodesk_dialogs import mostrar_aviso
                        mostrar_aviso(dialog, "Assinatura Vazia", "Por favor, assine no campo antes de confirmar.")
                except Exception as e:
                    print(f"❌ [ASSINATURA] Erro ao capturar terapeuta: {e}")
                    dialog.reject()
            
            btn_confirmar.clicked.connect(confirmar_assinatura_terapeuta)
            botoes_layout.addWidget(btn_confirmar)
            
            layout.addLayout(botoes_layout)
            
            # Mostrar diálogo
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Salvar assinatura na base de dados se há um consentimento ativo
                if hasattr(self, 'consentimento_ativo') and self.consentimento_ativo:
                    try:
                        # Obter dados da assinatura
                        if not signature_canvas.is_empty():
                            signature_pixmap = signature_canvas.toPixmap()
                            # Converter QPixmap para bytes
                            from PyQt6.QtCore import QBuffer, QIODevice
                            buffer = QBuffer()
                            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                            signature_pixmap.save(buffer, 'PNG')
                            signature_data = buffer.data().data()
                        else:
                            signature_data = None
                            
                        if signature_data:
                            from consentimentos_manager import ConsentimentosManager
                            manager = ConsentimentosManager()
                            
                            # Atualizar consentimento com assinatura do terapeuta
                            sucesso = manager.atualizar_assinatura_terapeuta(
                                self.consentimento_ativo['id'],
                                signature_data,
                                "Dr. Nuno Correia"
                            )
                            
                            if sucesso:
                                print(f"[DEBUG] ✅ Assinatura do terapeuta salva na BD")
                                # Atualizar visual do botão
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
                            else:
                                print(f"[ERRO] Falha ao salvar assinatura do terapeuta")
                        else:
                            print(f"[AVISO] Assinatura vazia - não foi salva")
                    except Exception as e:
                        print(f"[ERRO] Erro ao salvar assinatura do terapeuta: {e}")
                
                # Sempre atualizar visual (mesmo sem BD)
                print("[DEBUG] Assinatura do terapeuta confirmada: Dr. Nuno Correia")
            
        except Exception as e:
            print(f"[ERRO] Erro na assinatura do terapeuta: {e}")
            # Fallback simples
            self.assinatura_terapeuta.setText("✅ Dr. Nuno Correia")
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
            """)
            self.assinatura_terapeuta.setStyleSheet("""
                QLabel {
                    border: 2px solid #27ae60;
                    border-radius: 8px;
                    background-color: #e8f5e8;
                    font-size: 11px;
                    color: #2e7d32;
                    text-align: center;
                    padding: 10px;
                    font-weight: 600;
                }
            """)

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
            
            # Salvar assinaturas como arquivos temporários
            if hasattr(self, 'signature_canvas_paciente') and self.signature_canvas_paciente:
                try:
                    # Verificar se assinatura não está vazia antes de salvar
                    if not self.signature_canvas_paciente.is_empty():
                        os.makedirs('temp', exist_ok=True)
                        sig_path = os.path.abspath('temp/sig_paciente.png')
                        # Converter QPixmap para QImage antes de salvar
                        pixmap = self.signature_canvas_paciente.get_signature_image()
                        image = pixmap.toImage()
                        image.save(sig_path)
                        sig_url = QUrl.fromLocalFile(sig_path).toString()
                        assinatura_paciente_html = f'<img src="{sig_url}" width="150" height="50">'
                        print(f"[DEBUG] Assinatura paciente salva: {sig_path}")
                    else:
                        print(f"[DEBUG] Assinatura paciente vazia - não incluída no PDF")
                except Exception as e:
                    print(f"[DEBUG] Erro assinatura paciente: {e}")
            
            if hasattr(self, 'signature_canvas_terapeuta') and self.signature_canvas_terapeuta:
                try:
                    # Verificar se assinatura não está vazia antes de salvar
                    if not self.signature_canvas_terapeuta.is_empty():
                        os.makedirs('temp', exist_ok=True)
                        sig_path = os.path.abspath('temp/sig_terapeuta.png')
                        # Converter QPixmap para QImage antes de salvar
                        pixmap = self.signature_canvas_terapeuta.get_signature_image()
                        image = pixmap.toImage()
                        image.save(sig_path)
                        sig_url = QUrl.fromLocalFile(sig_path).toString()
                        assinatura_terapeuta_html = f'<img src="{sig_url}" width="150" height="50">'
                        print(f"[DEBUG] Assinatura terapeuta salva: {sig_path}")
                    else:
                        print(f"[DEBUG] Assinatura terapeuta vazia - não incluída no PDF")
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
                        width: 100%;
                        margin-top: 10pt;
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
            btn_cancelar.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            btn_cancelar.clicked.connect(dialog.reject)
            botoes_layout.addWidget(btn_cancelar)
            
            btn_importar = QPushButton("✅ Importar Assinado")
            btn_importar.setFixedSize(160, 40)
            btn_importar.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
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
                        width: 250pt;
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
                    
                    <table width="100%">
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
            btn_importar.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
            btn_importar.clicked.connect(lambda: self._selecionar_e_importar_pdf(dialog, arquivo_temp))
            botoes_layout.addWidget(btn_importar)
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setFixedSize(100, 35)
            btn_cancelar.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
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
                                    <p style="margin: 15px 0 0 0; line-height: 1.6;">
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
                                    <p style="margin: 15px 0 0 0; line-height: 1.6;">
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
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Assinatura - Declaração de Saúde")
            dialog.setModal(True)
            dialog.resize(600, 450)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            titulo = QLabel("✍️ Assinatura da Declaração de Saúde")
            titulo.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #2980b9;
                padding: 15px;
                text-align: center;
            """)
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)
            
            # Info do paciente
            nome_paciente = self.paciente_data.get('nome', 'N/A')
            info_label = QLabel(f"👤 Paciente: {nome_paciente}")
            info_label.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
            layout.addWidget(info_label)
            
            # Canvas de assinatura
            signature_canvas = SignatureCanvas()
            signature_canvas.setMinimumHeight(200)
            layout.addWidget(signature_canvas)
            
            # Instruções
            instrucoes = QLabel("✍️ Assine no campo acima usando o mouse ou toque")
            instrucoes.setStyleSheet("color: #6c757d; text-align: center; padding: 5px;")
            instrucoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(instrucoes)
            
            # Botões
            botoes_layout = QHBoxLayout()
            
            btn_limpar = QPushButton("🗑️ Limpar")
            btn_limpar.clicked.connect(signature_canvas.clear)
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            
            btn_confirmar = QPushButton("✅ Confirmar e Guardar")
            btn_confirmar.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            def confirmar_assinatura():
                try:
                    if signature_canvas.is_empty():
                        from biodesk_dialogs import mostrar_aviso
                        mostrar_aviso(dialog, "Assinatura Vazia", "Por favor, assine no campo antes de confirmar.")
                        return
                    
                    # Converter assinatura para bytes
                    signature_pixmap = signature_canvas.toPixmap()
                    from PyQt6.QtCore import QBuffer, QIODevice
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    signature_pixmap.save(buffer, 'PNG')
                    signature_data = buffer.data().data()
                    
                    # Guardar diretamente na base de dados
                    from consentimentos_manager import ConsentimentosManager
                    manager = ConsentimentosManager()
                    
                    sucesso = manager.guardar_assinatura_declaracao(
                        paciente_id, 'declaracao_saude', 'paciente', 
                        signature_data, nome_paciente
                    )
                    
                    if sucesso:
                        # Atualizar status visual
                        self.status_declaracao.setText("✅ Assinada")
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
                        
                        from biodesk_dialogs import mostrar_sucesso
                        mostrar_sucesso(dialog, "Sucesso", "✅ Declaração assinada com sucesso!")
                        dialog.accept()
                    else:
                        from biodesk_dialogs import mostrar_erro
                        mostrar_erro(dialog, "Erro", "❌ Erro ao guardar assinatura.")
                        
                except Exception as e:
                    from biodesk_dialogs import mostrar_erro
                    mostrar_erro(dialog, "Erro", f"❌ Erro ao processar assinatura:\n\n{str(e)}")
                    print(f"❌ [DECLARAÇÃO] Erro ao confirmar: {e}")
            
            btn_confirmar.clicked.connect(confirmar_assinatura)
            
            botoes_layout.addWidget(btn_limpar)
            botoes_layout.addStretch()
            botoes_layout.addWidget(btn_cancelar)
            botoes_layout.addWidget(btn_confirmar)
            
            layout.addLayout(botoes_layout)
            
            # Mostrar diálogo
            dialog.exec()
            
        except Exception as e:
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"❌ Erro ao iniciar assinatura:\n\n{str(e)}")
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
            
            # Canvas de assinatura paciente usando o mesmo sistema
            from centro_comunicacao_widget import SignatureCanvas
            self.canvas_paciente_declaracao = SignatureCanvas()
            self.canvas_paciente_declaracao.setMinimumSize(700, 150)
            layout_paciente.addWidget(self.canvas_paciente_declaracao)
            
            # Botões para assinatura paciente
            botoes_paciente = QHBoxLayout()
            
            btn_limpar_paciente = QPushButton("🗑️ Limpar")
            btn_limpar_paciente.clicked.connect(self.canvas_paciente_declaracao.clear)
            btn_limpar_paciente.setStyleSheet("""
                QPushButton {
                    padding: 8px 15px;
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            botoes_paciente.addWidget(btn_limpar_paciente)
            
            botoes_paciente.addStretch()
            layout_paciente.addLayout(botoes_paciente)
            layout.addWidget(grupo_paciente)
            
            # Botões principais
            botoes_principais = QHBoxLayout()
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            btn_cancelar.setStyleSheet("""
                QPushButton {
                    padding: 12px 25px;
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #5a6268; }
            """)
            botoes_principais.addWidget(btn_cancelar)
            
            botoes_principais.addStretch()
            
            btn_confirmar = QPushButton("✅ Confirmar e Finalizar")
            btn_confirmar.setStyleSheet("""
                QPushButton {
                    padding: 12px 25px;
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #219a52; }
            """)
            
            def confirmar_assinatura_declaracao():
                if not self.canvas_paciente_declaracao.has_signature():
                    from biodesk_dialogs import mostrar_aviso
                    mostrar_aviso(dialog, "Aviso", "Por favor, desenhe a sua assinatura antes de confirmar.")
                    return
                
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
            # Obter assinatura do canvas
            if hasattr(self, 'canvas_paciente_declaracao') and self.canvas_paciente_declaracao.has_signature():
                # Capturar assinatura como bytes PNG
                from PyQt6.QtCore import QBuffer, QByteArray
                from PyQt6.QtGui import QPixmap
                
                signature_image = self.canvas_paciente_declaracao.get_signature_image()
                if signature_image:
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                    signature_image.save(buffer, "PNG")
                    assinatura_paciente_bytes = byte_array.data()
                    
                    print(f"✅ [DECLARAÇÃO] Assinatura capturada: {len(assinatura_paciente_bytes)} bytes")
                else:
                    assinatura_paciente_bytes = None
                    print(f"⚠️ [DECLARAÇÃO] Falha ao capturar imagem da assinatura")
            else:
                assinatura_paciente_bytes = None
                print(f"❌ [DECLARAÇÃO] Canvas não disponível ou sem assinatura")
            
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
                # REMOVIDO: Deixar CSS controlar os cursores
            else:
                self.texto_declaracao_editor.setToolTip("")
                # REMOVIDO: Deixar CSS controlar os cursores
                
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

    def _aplicar_estilos_modernos_assinatura(self):
        """Força a aplicação de estilos modernos nos botões de assinatura após inicialização"""
        try:
            # Aplicar estilo moderno aos botões de assinatura se existirem
            if hasattr(self, 'assinatura_paciente'):
                self._style_modern_button(self.assinatura_paciente, "#2196F3")
            if hasattr(self, 'assinatura_terapeuta'):
                self._style_modern_button(self.assinatura_terapeuta, "#4CAF50")
        except Exception as e:
            print(f"[AVISO] Erro ao aplicar estilos modernos: {e}")

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

    def _style_text_edit(self, text_edit):
        """Aplica estilo moderno a um QTextEdit"""
        text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: white;
                color: #333;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #3498db;
                background-color: #fafafa;
            }
            QTextEdit:hover {
                border-color: #bdbdbd;
                background-color: #f9f9f9;
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

    def _create_iris_label(self, text):
        """Cria label com design iris - typography moderna"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #6c757d;
                padding: 2px 0px;
                margin-bottom: 3px;
            }
        """)
        return label

    def _style_iris_input(self, input_widget):
        """Aplica estilo iris aos campos de input - bordas suaves"""
        input_widget.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 14px;
                background-color: #ffffff;
                color: #495057;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                outline: none;
            }
            QLineEdit:hover {
                border: 1px solid #6c757d;
            }
        """)

    def _style_iris_combo(self, combo_widget):
        """Aplica estilo iris aos comboboxes - bordas suaves"""
        combo_widget.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 14px;
                background-color: #ffffff;
                color: #495057;
                min-height: 18px;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
                outline: none;
            }
            QComboBox:hover {
                border: 1px solid #6c757d;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6c757d;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: white;
                padding: 4px;
            }
        """)

    def _style_iris_button(self, button, hover_color):
        """Design de botões iris - base neutra + hover colorido (sem transform)"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                color: white;
                border: 1px solid {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(hover_color, 0.1)};
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
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        
        btn_agendar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
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
    import sys
    sys.exit(1)
