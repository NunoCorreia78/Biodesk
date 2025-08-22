"""
Biodesk - Módulo de Integração com Íris
=======================================

Módulo especializado para análise de íris extraído do monólito ficha_paciente.py.
Contém TODA a funcionalidade relacionada com captura, análise e gestão de imagens de íris.

🎯 Funcionalidades:
- Interface completa de análise de íris
- Galeria visual com miniaturas ESQ/DRT
- Captura de imagens com iridoscópio
- Sistema de notas interativo
- Exportação para histórico clínico
- Integração com terapia quântica

⚡ Performance:
- Lazy loading do IrisCanvas
- Cache inteligente de imagens
- Gestão otimizada de memória

📅 Extraído em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

import os
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import QMessageBox  # Para StandardButton
from biodesk_dialogs import BiodeskMessageBox

from biodesk_ui_kit import BiodeskUIKit
from data_cache import DataCache


class IrisIntegrationWidget(QWidget):
    """Widget especializado para análise de íris"""
    
    # Sinais para comunicação
    zona_clicada = pyqtSignal(str)  # nome da zona clicada
    imagem_selecionada = pyqtSignal(dict)  # dados da imagem selecionada
    notas_exportadas = pyqtSignal(str)  # notas exportadas
    
    def __init__(self, paciente_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        # Cache de dados
        self.cache = DataCache.get_instance()
        
        # Dados do paciente
        self.paciente_data = paciente_data or {}
        
        # Estado interno
        self.imagem_iris_selecionada = None
        self.iris_canvas = None
        self.notas_iris = None
        self._miniaturas_iris = {}
        self.galeria_containers = []
        
        # Inicializar interface
        self.init_ui()
        
        # Carregar dados se paciente disponível
        if self.paciente_data.get('id'):
            self.atualizar_galeria_iris()
    
    def init_ui(self):
        """Inicializa interface completa de análise de íris"""
        # Layout principal horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)
        
        # === GALERIA VISUAL DUPLA (ESQUERDA) ===
        self.criar_galeria_visual(main_layout)
        
        # === CANVAS OTIMIZADO (CENTRO) ===
        self.criar_canvas_iris(main_layout)
        
        # === NOTAS FUNCIONAIS (DIREITA) ===
        self.criar_painel_notas(main_layout)
    
    def criar_galeria_visual(self, parent_layout):
        """Cria galeria visual com botões e miniaturas ESQ/DRT"""
        galeria_frame = QFrame()
        galeria_frame.setFixedWidth(220)
        galeria_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)
        galeria_layout = QVBoxLayout(galeria_frame)
        galeria_layout.setContentsMargins(6, 6, 6, 6)
        galeria_layout.setSpacing(8)
        
        # Título da galeria
        titulo_galeria = QLabel("📷 Galeria de Íris")
        titulo_galeria.setStyleSheet(f"""
            QLabel {{
                font-size: {BiodeskUIKit.FONTS['size_normal']};
                font-weight: bold;
                color: {BiodeskUIKit.COLORS['primary']};
                padding: 8px;
                text-align: center;
            }}
        """)
        galeria_layout.addWidget(titulo_galeria)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(8)
        
        self.btn_adicionar_iris = QPushButton("📷")
        self.btn_adicionar_iris.setFixedSize(85, 28)
        self.btn_adicionar_iris.setToolTip("Adicionar nova íris")
        self.BiodeskUIKit.apply_universal_button_style(btn_adicionar_iris)
        self.btn_adicionar_iris.clicked.connect(self.adicionar_nova_iris)
        
        self.btn_remover_iris = QPushButton("🗑️")
        self.btn_remover_iris.setFixedSize(85, 28)
        self.btn_remover_iris.setToolTip("Remover íris selecionada")
        self.BiodeskUIKit.apply_universal_button_style(btn_remover_iris)
        self.btn_remover_iris.clicked.connect(self.apagar_imagem_selecionada)
        
        botoes_layout.addWidget(self.btn_adicionar_iris)
        botoes_layout.addWidget(self.btn_remover_iris)
        galeria_layout.addLayout(botoes_layout)
        galeria_layout.addSpacing(12)
        
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
        self.galeria_layout_principal.setSpacing(8)
        self.galeria_layout_principal.setContentsMargins(4, 4, 4, 4)
        
        # Layout horizontal para 2 colunas
        self.colunas_layout = QHBoxLayout()
        self.colunas_layout.setSpacing(8)
        
        # Coluna ESQ
        self.col_esq_layout = QVBoxLayout()
        self.col_esq_layout.setSpacing(8)
        self.col_esq_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Coluna DRT
        self.col_drt_layout = QVBoxLayout()
        self.col_drt_layout.setSpacing(8)
        self.col_drt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.colunas_layout.addLayout(self.col_esq_layout)
        self.colunas_layout.addLayout(self.col_drt_layout)
        self.galeria_layout_principal.addLayout(self.colunas_layout)
        self.galeria_layout_principal.addStretch()
        
        self.scroll_area_imagens.setWidget(self.galeria_widget)
        galeria_layout.addWidget(self.scroll_area_imagens, 1)
        
        parent_layout.addWidget(galeria_frame)
    
    def criar_canvas_iris(self, parent_layout):
        """Cria canvas para visualização de íris"""
        canvas_frame = QFrame()
        canvas_frame.setFixedWidth(654)  # 650px da imagem + 4px de margem
        canvas_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(2, 2, 2, 2)
        canvas_layout.setSpacing(0)
        
        # Tentar carregar IrisCanvas
        try:
            from iris_canvas import IrisCanvas
            self.iris_canvas = IrisCanvas(paciente_data=self.paciente_data)
            self.iris_canvas.setMinimumSize(650, 550)
            self.iris_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Conectar sinais para análise de zonas
            if hasattr(self.iris_canvas, 'zonaClicada'):
                self.iris_canvas.zonaClicada.connect(self.on_zona_clicada)
            
            canvas_layout.addWidget(self.iris_canvas, 1)
            # print("✅ IrisCanvas carregado com funcionalidade de análise")
            
        except ImportError as e:
            # Fallback para placeholder
            canvas_placeholder = QLabel("Canvas da Íris\\n(Módulo não disponível)")
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
            print(f"⚠️ Erro ao importar IrisCanvas: {e}")
        
        parent_layout.addWidget(canvas_frame)
    
    def criar_painel_notas(self, parent_layout):
        """Cria painel de notas funcionais"""
        notas_frame = QFrame()
        notas_frame.setFixedWidth(380)
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
        
        # Título do painel
        titulo_notas = QLabel("📝 Notas de Análise")
        titulo_notas.setStyleSheet(f"""
            QLabel {{
                font-size: {BiodeskUIKit.FONTS['size_normal']};
                font-weight: bold;
                color: {BiodeskUIKit.COLORS['success']};
                padding: 8px;
                text-align: center;
            }}
        """)
        notas_layout.addWidget(titulo_notas)
        
        # Widget de notas
        try:
            from checkbox_notes_widget import CheckboxNotesWidget
            self.notas_iris = CheckboxNotesWidget()
            self.notas_iris.setMinimumHeight(350)
            notas_layout.addWidget(self.notas_iris, 1)
        except ImportError:
            self.notas_iris = QTextEdit()
            self.notas_iris.setPlaceholderText("Notas da análise...")
            self.notas_iris.setMinimumHeight(350)
            notas_layout.addWidget(self.notas_iris, 1)
        
        # Botões de ação
        self.btn_exportar_notas = QPushButton("📋 Histórico")
        self.btn_exportar_notas.setFixedHeight(36)
        self.BiodeskUIKit.apply_universal_button_style(btn_exportar_notas)
        self.btn_exportar_notas.clicked.connect(self.exportar_notas_iris)
        
        self.btn_exportar_terapia = QPushButton("⚡ Terapia")
        self.btn_exportar_terapia.setFixedHeight(36)
        self.BiodeskUIKit.apply_universal_button_style(btn_exportar_terapia)
        self.btn_exportar_terapia.clicked.connect(self.exportar_para_terapia_quantica)
        
        btn_limpar_notas = QPushButton("🧹 Limpar")
        btn_limpar_notas.setFixedHeight(36)
        BiodeskUIKit.apply_universal_button_style(btn_limpar_notas)
        btn_limpar_notas.clicked.connect(self.limpar_notas_iris)
        
        notas_layout.addWidget(self.btn_exportar_notas)
        notas_layout.addWidget(self.btn_exportar_terapia)
        notas_layout.addWidget(btn_limpar_notas)
        
        parent_layout.addWidget(notas_frame)
    
    def on_zona_clicada(self, nome_zona):
        """Processa clique numa zona da íris e adiciona nota"""
        print(f"🔍 Zona clicada para análise: {nome_zona}")
        
        # Adicionar nota automaticamente
        if hasattr(self, 'notas_iris') and self.notas_iris:
            try:
                if hasattr(self.notas_iris, 'adicionar_linha'):
                    self.notas_iris.adicionar_linha(f"🎯 Análise: {nome_zona}")
                    print(f"✅ Nota adicionada para zona: {nome_zona}")
                elif hasattr(self.notas_iris, 'setPlainText'):
                    texto_atual = self.notas_iris.toPlainText()
                    if texto_atual:
                        texto_atual += f"\\n🎯 Análise: {nome_zona}"
                    else:
                        texto_atual = f"🎯 Análise: {nome_zona}"
                    self.notas_iris.setPlainText(texto_atual)
                    print(f"✅ Nota adicionada para zona: {nome_zona}")
            except Exception as e:
                print(f"❌ Erro ao adicionar nota: {e}")
        
        # Emitir sinal
        self.zona_clicada.emit(nome_zona)
    
    def atualizar_galeria_iris(self):
        """Atualiza galeria com miniaturas das imagens de íris"""
        # Limpar galeria atual
        if hasattr(self, 'col_esq_layout') and hasattr(self, 'col_drt_layout'):
            for lay in (self.col_esq_layout, self.col_drt_layout):
                for i in reversed(range(lay.count())):
                    item = lay.itemAt(i)
                    w = item.widget()
                    if w:
                        w.setParent(None)
        
        paciente_id = self.paciente_data.get('id')
        if not paciente_id:
            return
        
        try:
            from db_manager import DBManager
            db = DBManager()
            imagens = db.get_imagens_por_paciente(paciente_id)
        except Exception as e:
            print(f"❌ Erro ao carregar imagens: {e}")
            return
        
        if not imagens:
            label = QLabel("Nenhuma imagem")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet('color: #888; padding: 8px; font-size: 11px;')
            self.col_esq_layout.addWidget(label)
            if self.iris_canvas:
                self.iris_canvas.set_image(None, None)
            return
        
        # Processar e organizar imagens
        self._processar_imagens_galeria(imagens)
    
    def _processar_imagens_galeria(self, imagens):
        """Processa e organiza imagens na galeria por tipo ESQ/DRT"""
        # Inicializar estruturas
        self._miniaturas_iris = {}
        self.galeria_containers = []
        
        # Agrupar por tipo e ordenar
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
        
        # Ordenar cada grupo
        for k in grupos:
            grupos[k] = sorted(grupos[k], key=_ord_key)
        
        # Criar etiquetas e processar
        ordem_tipos = [t for t in ['ESQ', 'DRT', 'IMG'] if t in grupos]
        for tipo in ordem_tipos:
            for idx, img in enumerate(grupos[tipo], start=1):
                label_calc = f"{tipo}{idx:03d}"
                self._criar_miniatura(img, label_calc, tipo)
    
    def _criar_miniatura(self, img, label_text, tipo_calc):
        """Cria miniatura individual para a galeria"""
        thumb_path = img.get('caminho_imagem', '') or img.get('caminho', '')
        
        thumb_container = QFrame()
        thumb_container.setFixedSize(75, 85)
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
        
        # Imagem da miniatura
        thumb_label = QLabel()
        thumb_label.setFixedSize(70, 50)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet(
            "QLabel { border: 1px solid #ddd; border-radius: 8px; background: #f5f5f5; }"
        )
        
        if thumb_path and os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            if not pix.isNull():
                thumb_label.setPixmap(
                    pix.scaled(
                        68, 48,
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
        
        # Etiqueta de texto
        texto_label = QLabel(label_text)
        texto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        texto_label.setStyleSheet(
            "font-size: 10px; color: #424242; font-weight: 600; background: transparent; padding: 0px;"
        )
        
        # Adicionar ao layout
        thumb_layout.addWidget(thumb_label)
        thumb_layout.addWidget(texto_label)
        
        # Tooltip informativo
        tooltip_partes = [f"Etiqueta: {label_text}"]
        dt = img.get('data_analise') or img.get('data')
        if dt:
            tooltip_partes.append(f"Data: {dt}")
        tooltip_partes.append(f"Tipo: {img.get('tipo', '-')}")
        tooltip_partes.append(f"ID: {img.get('id', '-')}")
        thumb_container.setToolTip("\\n".join(tooltip_partes))
        
        # Configurar clique
        thumb_container.mousePressEvent = lambda e, img=img: self.selecionar_imagem_galeria(img)
        thumb_container.setProperty('img_data', img)
        
        # Armazenar referências
        self.galeria_containers.append(thumb_container)
        if img.get('id') is not None:
            self._miniaturas_iris[img.get('id')] = thumb_container
        
        # Adicionar à coluna apropriada
        if tipo_calc == 'ESQ':
            self.col_esq_layout.addWidget(thumb_container)
        elif tipo_calc == 'DRT':
            self.col_drt_layout.addWidget(thumb_container)
        else:
            self.col_esq_layout.addWidget(thumb_container)
    
    def selecionar_imagem_galeria(self, img):
        """Seleciona imagem da galeria e atualiza visualização"""
        print(f"🖱️ Imagem selecionada: {img.get('caminho_imagem', 'N/A')}")
        
        # Atualizar estado
        self.imagem_iris_selecionada = img
        
        # Atualizar canvas
        if self.iris_canvas:
            self.iris_canvas.set_image(img['caminho_imagem'], img['tipo'])
        
        # Limpar notas
        if hasattr(self.notas_iris, 'limpar_todas'):
            self.notas_iris.limpar_todas()
        elif hasattr(self.notas_iris, 'clear'):
            self.notas_iris.clear()
        
        # Configurar análise se disponível
        if self.iris_canvas and hasattr(self.iris_canvas, 'definir_imagem_atual'):
            self.iris_canvas.definir_imagem_atual(img['id'])
            print(f"🔍 Imagem {img['id']} configurada para análise")
        
        # Atualizar seleção visual
        self._atualizar_selecao_galeria(img)
        
        # Emitir sinal
        self.imagem_selecionada.emit(img)
    
    def _atualizar_selecao_galeria(self, img_selecionada):
        """Atualiza destaque visual na galeria"""
        for container in self.galeria_containers:
            img_data = container.property('img_data')
            if img_data:
                is_selected = img_data == img_selecionada
                container.setProperty('selecionado', is_selected)
                
                if is_selected:
                    container.setStyleSheet(container.property('style_base_selecionado'))
                else:
                    container.setStyleSheet(container.property('style_base_normal'))
    
    def adicionar_nova_iris(self):
        """Captura nova imagem usando iridoscópio"""
        if not self.paciente_data or 'id' not in self.paciente_data:
            BiodeskMessageBox.warning(
                self, 
                "Paciente Necessário", 
                "É necessário ter um paciente selecionado para capturar imagens."
            )
            return
        
        try:
            # Classe de preview inline para captura
            from PyQt6.QtWidgets import QDialog
            
            class IridoscopioPreview(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Iridoscópio - Captura")
                    self.setFixedSize(800, 600)
                    self.setModal(True)
                    self.frame = None
                    self.setup_ui()
                    self.start_camera()
                
                def setup_ui(self):
                    layout = QVBoxLayout(self)
                    
                    self.video_label = QLabel()
                    self.video_label.setMinimumSize(640, 480)
                    self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.video_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #9C27B0;
                            border-radius: 8px;
                            background-color: #000000;
                        }
                    """)
                    layout.addWidget(self.video_label)
                    
                    instrucoes = QLabel("📹 Posicione o olho e clique 'Capturar'")
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
                    
                    self.btn_capturar = QPushButton("📸 Capturar")
                    self.BiodeskUIKit.apply_universal_button_style(btn_capturar)
                    self.btn_capturar.clicked.connect(self.capturar_imagem)
                    
                    self.btn_cancelar = QPushButton("❌ Cancelar")
                    self.BiodeskUIKit.apply_universal_button_style(btn_cancelar)
                    self.btn_cancelar.clicked.connect(self.reject)
                    
                    botoes_layout.addWidget(self.btn_capturar)
                    botoes_layout.addWidget(self.btn_cancelar)
                    layout.addLayout(botoes_layout)
                
                def start_camera(self):
                    import cv2
                    from PyQt6.QtCore import QTimer
                    
                    # Tentar iridoscópio (câmera 1) depois padrão (câmera 0)
                    self.cap = cv2.VideoCapture(1)
                    if not self.cap.isOpened():
                        self.cap = cv2.VideoCapture(0)
                        if not self.cap.isOpened():
                            self.video_label.setText("❌ Câmera não disponível")
                            return
                    
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    
                    self.timer = QTimer()
                    self.timer.timeout.connect(self.update_frame)
                    self.timer.start(30)
                
                def update_frame(self):
                    import cv2
                    
                    if self.cap and self.cap.isOpened():
                        ret, frame = self.cap.read()
                        if ret:
                            self.current_frame = frame.copy()
                            
                            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = rgb_image.shape
                            bytes_per_line = ch * w
                            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                            
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
                
                def closeEvent(self, event):
                    if hasattr(self, 'timer') and self.timer.isActive():
                        self.timer.stop()
                    if hasattr(self, 'cap') and self.cap:
                        self.cap.release()
                    event.accept()
            
            # Capturar imagem
            preview = IridoscopioPreview(parent=self)
            if preview.exec() != QDialog.DialogCode.Accepted or not preview.frame is not None:
                return
            
            # Escolher lateralidade
            lateralidade, ok = BiodeskMessageBox.getItem(
                self, 
                "Lateralidade", 
                "Selecione o olho:",
                ['Esquerdo', 'Direito'], 
                0, 
                False
            )
            if not ok:
                return
            
            tipo = 'ESQ' if lateralidade == 'Esquerdo' else 'DRT'
            
            # Salvar imagem
            self._salvar_imagem_capturada(preview.frame, tipo)
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro na captura: {str(e)}")
    
    def _salvar_imagem_capturada(self, frame, tipo):
        """Salva imagem capturada no sistema"""
        try:
            import cv2
            from datetime import datetime
            from db_manager import DBManager
            
            # Criar diretório se necessário
            imagens_dir = os.path.join(os.path.dirname(__file__), "..", "imagens_iris", str(self.paciente_data['id']))
            os.makedirs(imagens_dir, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tipo}_{timestamp}.jpg"
            caminho = os.path.join(imagens_dir, filename)
            
            # Salvar arquivo
            success = cv2.imwrite(caminho, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if not success:
                raise Exception("Falha ao salvar arquivo")
            
            # Atualizar BD
            db = DBManager()
            db.adicionar_imagem_iris(self.paciente_data['id'], tipo, caminho)
            
            # Atualizar interface
            self.atualizar_galeria_iris()
            if self.iris_canvas:
                self.iris_canvas.set_image(caminho, tipo)
            
            BiodeskMessageBox.information(
                self, 
                "Sucesso", 
                f"✅ Imagem {tipo} capturada e guardada!\\n\\nArquivo: {filename}"
            )
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")
    
    def apagar_imagem_selecionada(self):
        """Remove imagem selecionada"""
        # Procurar imagem selecionada
        container_selecionado = None
        img_data_selecionada = None
        
        for container in self.galeria_containers:
            if container.property('selecionado'):
                container_selecionado = container
                img_data_selecionada = container.property('img_data')
                break
        
        if not img_data_selecionada:
            BiodeskMessageBox.warning(
                self, 
                "Seleção Necessária", 
                "Selecione uma imagem na galeria para remover."
            )
            return
        
        # Confirmar remoção
        reply = BiodeskMessageBox.question(
            self, 
            "Confirmar Remoção",
            f"Remover a imagem {img_data_selecionada.get('caminho_imagem', 'N/A')}?"
        )
        
        if reply:  # BiodeskMessageBox.question retorna True/False
            self._remover_imagem(img_data_selecionada)
    
    def _remover_imagem(self, img_data):
        """Remove imagem do sistema"""
        try:
            from db_manager import DBManager
            
            # Remover arquivo
            caminho = img_data.get('caminho_imagem')
            if caminho and os.path.exists(caminho):
                os.remove(caminho)
            
            # Remover do BD
            db = DBManager()
            db.execute_query("DELETE FROM imagens_iris WHERE id = ?", (img_data['id'],))
            
            # Atualizar galeria
            self.atualizar_galeria_iris()
            
            BiodeskMessageBox.information(self, "Sucesso", "✅ Imagem removida com sucesso!")
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro ao remover: {str(e)}")
    
    def limpar_notas_iris(self):
        """Limpa todas as notas de análise"""
        reply = BiodeskMessageBox.question(
            self,
            "Confirmar Limpeza",
            "⚠️ Limpar todas as notas de análise?\\n\\nEsta ação não pode ser desfeita."
        )
        
        if reply:  # BiodeskMessageBox.question retorna True/False
            if hasattr(self.notas_iris, 'limpar_todas'):
                self.notas_iris.limpar_todas()
            elif hasattr(self.notas_iris, 'clear'):
                self.notas_iris.clear()
            
            self._atualizar_textos_botoes()
            BiodeskMessageBox.information(self, "Sucesso", "✅ Notas limpas!")
    
    def exportar_notas_iris(self):
        """Exporta notas selecionadas para histórico clínico"""
        if not hasattr(self.notas_iris, 'get_linhas_selecionadas'):
            BiodeskMessageBox.warning(
                self, 
                "Função Indisponível", 
                "Exportação de notas não disponível com este widget."
            )
            return
        
        linhas_selecionadas = self.notas_iris.get_linhas_selecionadas()
        
        if not linhas_selecionadas:
            BiodeskMessageBox.warning(
                self, 
                'Nenhuma Nota Selecionada', 
                'Selecione pelo menos uma nota para exportar.'
            )
            return
        
        # Formatar notas
        notas = '\\n'.join(linhas_selecionadas)
        
        # Emitir sinal para o módulo principal processar
        self.notas_exportadas.emit(notas)
        
        # Remover linhas exportadas
        if hasattr(self.notas_iris, 'remover_linhas_selecionadas'):
            self.notas_iris.remover_linhas_selecionadas()
        
        self._atualizar_textos_botoes()
        
        BiodeskMessageBox.information(
            self, 
            'Exportado', 
            f'✅ {len(linhas_selecionadas)} nota(s) exportada(s) para o histórico!'
        )
    
    def exportar_para_terapia_quantica(self):
        """Exporta dados para terapia quântica"""
        if not self.imagem_iris_selecionada:
            BiodeskMessageBox.warning(
                self, 
                "Imagem Necessária", 
                "Selecione uma imagem de íris primeiro."
            )
            return
        
        try:
            # Obter dados da íris
            dados_iris = {
                'tipo': self.imagem_iris_selecionada.get('tipo'),
                'caminho': self.imagem_iris_selecionada.get('caminho_imagem'),
                'id': self.imagem_iris_selecionada.get('id')
            }
            
            # Tentar abrir terapia quântica
            from terapia_quantica_window import TerapiaQuanticaWindow
            
            terapia_window = TerapiaQuanticaWindow(
                paciente_data=self.paciente_data,
                iris_data=dados_iris,
                parent=self
            )
            terapia_window.show()
            
            BiodeskMessageBox.information(
                self, 
                "Terapia Quântica", 
                "✅ Dados exportados para Terapia Quântica!"
            )
            
        except ImportError:
            BiodeskMessageBox.warning(
                self, 
                "Módulo Indisponível", 
                "Módulo de Terapia Quântica não disponível."
            )
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")
    
    def _atualizar_textos_botoes(self):
        """Atualiza textos dos botões com contadores"""
        if not hasattr(self.notas_iris, 'count_total'):
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
            print(f"[DEBUG] Erro ao atualizar textos: {e}")
    
    def atualizar_dados_paciente(self, novos_dados: Dict[str, Any]):
        """Atualiza dados do paciente e recarrega galeria"""
        self.paciente_data.update(novos_dados)
        
        # Atualizar canvas se disponível
        if self.iris_canvas and hasattr(self.iris_canvas, 'paciente_data'):
            self.iris_canvas.paciente_data = self.paciente_data
        
        # Recarregar galeria
        if self.paciente_data.get('id'):
            self.atualizar_galeria_iris()
    
    def get_imagem_selecionada(self) -> Optional[Dict]:
        """Retorna dados da imagem atualmente selecionada"""
        return self.imagem_iris_selecionada
    
    def set_imagem_selecionada(self, img_data: Dict):
        """Define imagem selecionada programaticamente"""
        if img_data:
            self.selecionar_imagem_galeria(img_data)
