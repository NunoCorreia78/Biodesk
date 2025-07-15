from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QGraphicsView, QGraphicsScene, 
                            QFileDialog, QMessageBox, QGraphicsPolygonItem, QHBoxLayout, 
                            QLabel, QTextEdit, QSizePolicy, QFrame, QScrollArea, QGraphicsItem)
from PyQt6.QtGui import QPixmap, QPolygonF, QBrush, QPen, QColor
from PyQt6.QtCore import Qt, QPointF
import json
import math
import os
from iris_overlay_manager import IrisOverlayManager

# --- Função de morphing para converter pontos polares normalizados em coordenadas no canvas ---
def pontos_para_polygon(pontos_polares, cx, cy, raio_pupila, raio_anel):
    from PyQt6.QtGui import QPolygonF
    from PyQt6.QtCore import QPointF
    import math
    poly = QPolygonF()
    for angulo, raio_perc in pontos_polares:
        raio_absoluto = raio_pupila + (raio_anel - raio_pupila) * (raio_perc / 100)
        x = cx + raio_absoluto * math.cos(math.radians(angulo))
        y = cy - raio_absoluto * math.sin(math.radians(angulo))
        poly.append(QPointF(x, y))
    return poly

class ZonaReflexa(QGraphicsPolygonItem):
    def __init__(self, dados_zona, cx, cy, raio_pupila, raio_anel, parent=None):
        super().__init__(parent)
        self.dados_originais = dados_zona
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)  # Aceitar clique do botão esquerdo
        self.default_opacity = dados_zona['estilo'].get('opacity', 0.5)
        self.setOpacity(self.default_opacity)
        self.set_brush_pen(dados_zona['estilo'])
        self.atualizar_shape(cx, cy, raio_pupila, raio_anel)
        self.setToolTip(f"{dados_zona['nome']}: {dados_zona.get('descricao', '')}")
        
    def atualizar_shape(self, cx, cy, raio_pupila, raio_anel):
        nova_polygon = pontos_para_polygon(self.dados_originais['pontos'], cx, cy, raio_pupila, raio_anel)
        self.setPolygon(nova_polygon)

    def set_brush_pen(self, estilo):
        fill = QColor(estilo.get('fill', '#CCCCCC'))
        stroke = QColor(estilo.get('stroke', '#333333'))
        width = estilo.get('stroke-width', 1.0)
        self.setBrush(QBrush(fill))
        self.setPen(QPen(stroke, width))

    def hoverEnterEvent(self, event):
        # Aumentar a opacidade para destacar a zona
        self.setOpacity(1.0)
        
        # Encontrar o canvas que contém esta zona
        try:
            # Método mais direto para encontrar o widget que contém a cena
            scene = self.scene()
            if scene:
                views = scene.views()
                if views and len(views) > 0:
                    view = views[0]
                    if view and hasattr(view, 'parent'):
                        # Verificar se o parent tem o método que precisamos
                        parent_widget = view.parent()
                        if parent_widget and hasattr(parent_widget, 'atualizar_painel_zona'):
                            # Chamar o método diretamente, ignorando o aviso do Pylance
                            # mypy: ignore
                            getattr(parent_widget, 'atualizar_painel_zona')(self.dados_originais)
                            print(f"Hover ativado em {self.dados_originais.get('nome', 'zona')}")
        except Exception as e:
            print(f"Erro ao processar hover: {e}")
                
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Restaurar a opacidade original
        self.setOpacity(self.default_opacity)
        
        # Encontrar o canvas que contém esta zona
        try:
            # Método mais direto para encontrar o widget que contém a cena
            scene = self.scene()
            if scene:
                views = scene.views()
                if views and len(views) > 0:
                    view = views[0]
                    if view and hasattr(view, 'parent'):
                        parent_widget = view.parent()
                        if parent_widget and hasattr(parent_widget, 'limpar_painel_zona'):
                            # Chamar o método diretamente, ignorando o aviso do Pylance
                            # mypy: ignore
                            getattr(parent_widget, 'limpar_painel_zona')()
                            print("Hover desativado")
        except Exception as e:
            print(f"Erro ao processar hover leave: {e}")
                
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        # Quando uma zona for clicada, atualizar callback se disponível
        try:
            # Método mais direto para encontrar o widget que contém a cena
            scene = self.scene()
            if scene:
                views = scene.views()
                if views and len(views) > 0:
                    view = views[0]
                    if view and hasattr(view, 'parent'):
                        parent_widget = view.parent()
                        if parent_widget and hasattr(parent_widget, 'atualizar_painel_zona'):
                            # Chamar o método diretamente, ignorando o aviso do Pylance
                            # mypy: ignore
                            getattr(parent_widget, 'atualizar_painel_zona')(self.dados_originais)
                            print(f"Zona selecionada: {self.dados_originais.get('nome', 'zona')}")
        except Exception as e:
            print(f"Erro ao processar clique: {e}")
                
        super().mousePressEvent(event)

def estilizar_botao_moderno(botao, cor="#1976d2", hover="#42a5f5"):
    botao.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cor}, stop:1 #e3eafc);
            color: white;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 16px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {hover};
            color: #222;
        }}
    """)

class IrisCanvas(QWidget):
    def __init__(self, paciente_data: dict | None = None, caminho_imagem: str | None = None, tipo: str | None = None, parent=None):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.caminho_imagem = caminho_imagem
        self.tipo = tipo
        titulo = (f"Análise de Íris – {paciente_data.get('nome', 'Paciente')}" 
                  if paciente_data else "Análise de Íris (sem paciente associado)")
        self.setWindowTitle(titulo)
        
        # ────────────── NOVO ESTADO DE CALIBRAÇÃO ──────────────
        # center_pan: vetor [dx,dy] que move todas as zonas (PAN)
        # pupil_radius & iris_radius: do modo coarse
        # fine_offsets: dict { ponto_id: QPointF(dx,dy) } para ajuste fino
        self.center_pan = QPointF(0, 0)
        self.pupil_radius = 50  # default_pupil_radius
        self.iris_radius = 120  # default_iris_radius
        self.fine_offsets = {}  # preenchido só se ajuste fino ON
        # flags de modo
        self.calibrating = False   # inicia OFF por defeito
        self.fine_tuning_mode = False
        
        self.init_ui()
        self.imagem_pixmap = None
        # Instancia o overlay manager para gerir zonas, morphing, etc
        self.overlay_manager = IrisOverlayManager(self.scene)
        # Parâmetros da íris
        self.centro_iris = None
        self.raio_pupila = None
        self.raio_anel = None
        self._info_zona_callback = None
        self._info_zona_callback = None
        # Se fornecido, carregar imagem e JSON correto
        if self.caminho_imagem and self.tipo:
            self.carregar_imagem_e_zonas(self.caminho_imagem, self.tipo)

    def init_ui(self):
        from PyQt6.QtWidgets import QHBoxLayout, QGraphicsScene, QVBoxLayout, QPushButton, QLabel

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Rótulo do olho (esquerdo/direito)
        self.side_label = QLabel("")
        self.side_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.side_label.setStyleSheet("font-weight: bold; font-size: 17px; margin-bottom: 6px;")
        main_layout.addWidget(self.side_label)

        # Barra de botões no topo
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 5, 10, 5)
        
        # Botão para calibração com PAN
        self.btn_calibracao = QPushButton("Calibração: OFF")
        self.btn_calibracao.setCheckable(True)
        self.btn_calibracao.setChecked(self.calibrating)  # Inicia OFF
        self.btn_calibracao.setStyleSheet("""
            QPushButton {
                background: #1976d2;
                color: #fff;
                border-radius: 10px;
                padding: 10px 0;
                font-size: 15px;
                font-weight: 600;
                border: none;
                min-width: 140px;
                max-width: 140px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton:hover {
                background-color: #42a5f5;
                color: #fff;
            }
            QPushButton:pressed {
                background: #124058;
            }
        """)
        self.btn_calibracao.clicked.connect(self.toggle_calibracao)
        btn_layout.addWidget(self.btn_calibracao)
        
        # Botão para ajuste fino
        self.btn_ajuste_fino = QPushButton("Ajuste Fino: OFF")
        self.btn_ajuste_fino.setCheckable(True)
        self.btn_ajuste_fino.setChecked(self.fine_tuning_mode)  # Inicia OFF
        self.btn_ajuste_fino.setStyleSheet("""
            QPushButton {
                background: #26a69a;
                color: #fff;
                border-radius: 10px;
                padding: 10px 0;
                font-size: 15px;
                font-weight: 600;
                border: none;
                min-width: 140px;
                max-width: 140px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton:hover {
                background-color: #4db6ac;
                color: #fff;
            }
            QPushButton:pressed {
                background: #124058;
            }
        """)
        self.btn_ajuste_fino.clicked.connect(self.toggle_ajuste_fino)
        btn_layout.addWidget(self.btn_ajuste_fino)
        
        # Botão para aplicar calibração (inicialmente oculto)
        self.btn_aplicar_calibracao = QPushButton("Aplicar Calibração")
        self.btn_aplicar_calibracao.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: #fff;
                border-radius: 10px;
                padding: 10px 0;
                font-size: 15px;
                font-weight: 600;
                border: none;
                min-width: 140px;
                max-width: 140px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton:hover {
                background-color: #66bb6a;
                color: #fff;
            }
            QPushButton:pressed {
                background: #124058;
            }
        """)
        self.btn_aplicar_calibracao.clicked.connect(self.aplicar_calibracao)
        self.btn_aplicar_calibracao.setVisible(self.calibrating)  # Só visível quando calibração está ativa
        btn_layout.addWidget(self.btn_aplicar_calibracao)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # Canvas central (IrisGraphicsView)
        self.view = IrisGraphicsView(self)
        self.scene = QGraphicsScene(self)  # Agora o canvas vira pai da scene
        self.view.setScene(self.scene)
        # Após criar a view e associar a scene, ative o mouse tracking:
        self.view.setMouseTracking(True)
        viewport = self.view.viewport()
        if viewport is not None:
            viewport.setMouseTracking(True)

        # Layout principal para canvas e painel lateral
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        # Adicionar view ao layout principal
        content_layout.addWidget(self.view, 1)  # ocupa todo o espaço
        # Inicializa zona_atual como None
        self.zona_atual = None
        # Criar painel lateral para informações de zonas
        self.painel_info = QFrame()
        self.painel_info.setFrameShape(QFrame.Shape.StyledPanel)
        self.painel_info.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 2px solid #1976d2;  /* Borda mais destacada */
                border-radius: 8px;
                margin: 8px;
            }
        """)
        self.painel_info.setFixedWidth(300)  # Largura fixa para o painel
        self.painel_info.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        # Layout do painel de informações
        painel_layout = QVBoxLayout(self.painel_info)
        painel_layout.setContentsMargins(15, 15, 15, 15)  # Margens internas
        # Título do painel
        self.info_titulo = QLabel("Informações da Zona")
        self.info_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; padding: 5px;")
        painel_layout.addWidget(self.info_titulo)
        # Nome da zona
        self.info_nome = QLabel()
        self.info_nome.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; padding: 5px;")
        painel_layout.addWidget(self.info_nome)
        # Descrição da zona
        self.info_descricao = QTextEdit()
        self.info_descricao.setReadOnly(True)
        self.info_descricao.setStyleSheet("font-size: 14px; color: #333; background-color: transparent; border: none;")
        painel_layout.addWidget(self.info_descricao)
        # Adicionar painel ao layout principal (inicialmente oculto)
        self.painel_info.setVisible(False)  # Começa oculto
        content_layout.addWidget(self.painel_info)
        # Configurar callback para informações de zona
        self.set_info_zona_callback(self.mostrar_info_zona)
        # Adicionar layout de conteúdo ao layout principal
        main_layout.addLayout(content_layout, 1)
        self.setLayout(main_layout)

    def terminar_calibragem(self):
        """Finaliza a calibração, remove handles e redesenha zonas com novos parâmetros."""
        # Remover círculos e handles
        if hasattr(self, 'ellipse_anel') and self.ellipse_anel:
            self.scene.removeItem(self.ellipse_anel)
            self.ellipse_anel = None
        if hasattr(self, 'ellipse_pupila') and self.ellipse_pupila:
            self.scene.removeItem(self.ellipse_pupila)
            self.ellipse_pupila = None
        if hasattr(self, 'handles'):
            for h in self.handles:
                self.scene.removeItem(h)
            self.handles = []
        # —> Reaplica centro/raios às zonas e redesenha os polígonos
        self.atualizar_todas_zonas()

    def set_side_label(self, tipo):
        if tipo is None:
            self.side_label.setText("")
        elif str(tipo).lower() == "esq":
            self.side_label.setText("Olho Esquerdo")
        elif str(tipo).lower() == "drt":
            self.side_label.setText("Olho Direito")
        else:
            self.side_label.setText(str(tipo))
        
    def controlar_visibilidade_botoes(self, tem_imagens=False):
        """Controla a visibilidade dos botões baseado na existência de imagens."""
        # Método mantido para compatibilidade, mas sem botões para controlar
        pass



    def atualizar_todas_zonas(self):
        """Atualiza todas as zonas reflexas com novos parâmetros de centro e raios."""
        if self.centro_iris and self.raio_pupila and self.raio_anel:
            print(f"Atualizando {len(self.overlay_manager.zonas)} zonas com:")
            print(f"  Centro: {self.centro_iris}")
            print(f"  Raio pupila: {self.raio_pupila}")
            print(f"  Raio íris: {self.raio_anel}")
            
            for zona in self.overlay_manager.zonas:
                # Atualiza a forma da zona baseada nos novos parâmetros
                zona.atualizar_shape(self.centro_iris[0], self.centro_iris[1], self.raio_pupila, self.raio_anel)
                
                # Garante que a zona está configurada para receber eventos de hover
                zona.setAcceptHoverEvents(True)
                
                # Define um z-index adequado para não ser ocultada por outros elementos
                zona.setZValue(20)  # Valor mais alto = mais próximo do topo
                
                # Garante que o item está visível
                zona.setVisible(True)
                
                # Define opacidade para ser visível
                zona.setOpacity(0.5)  # Começa com 50% de opacidade
                
                # Garante que o item não esteja sendo filtrado por nenhuma transformação
                zona.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)
        else:
            print("Erro: Não é possível atualizar zonas, parâmetros da íris não definidos.")
            print(f"  Centro: {self.centro_iris}")
            print(f"  Raio pupila: {self.raio_pupila}")
            print(f"  Raio íris: {self.raio_anel}")
    
    def limpar_galeria(self):
        """Remove todas as imagens da galeria - método mantido para compatibilidade"""
        # Limpa os arquivos temporários
        if hasattr(self, 'temp_files'):
            import os
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Erro ao remover arquivo temporário {temp_file}: {e}")
            self.temp_files = []
    
    def adicionar_imagem_a_galeria(self, caminho_imagem):
        """Método mantido para compatibilidade - agora apenas armazena o caminho"""
        # Apenas armazena o caminho da imagem para uso futuro
        if not hasattr(self, 'imagens_galeria'):
            self.imagens_galeria = []
        self.imagens_galeria.append(caminho_imagem)

    def abrir_imagem(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Abrir imagem da íris", 
            "", 
            "Imagens (*.png *.jpg *.jpeg)"
        )
        if filename:
            # Adiciona a imagem à galeria
            self.adicionar_imagem_a_galeria(filename)
            # Carrega a imagem no visualizador principal
            self.carregar_imagem_e_zonas(filename, self.tipo or 'drt')

    def capturar_imagem(self):
        try:
            import cv2
            import tempfile
            
            cap = cv2.VideoCapture(1)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Converte a imagem para RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Cria um arquivo temporário para a imagem
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # Salva a imagem temporariamente
                cv2.imwrite(temp_path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                
                # Adiciona a imagem à galeria
                self.adicionar_imagem_a_galeria(temp_path)
                
                # Carrega a imagem no visualizador principal
                self.carregar_imagem_e_zonas(temp_path, self.tipo or 'drt')
                
                # Armazena o caminho temporário para uso posterior
                if not hasattr(self, 'temp_files'):
                    self.temp_files = []
                self.temp_files.append(temp_path)
                
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível capturar imagem da câmara.")
                
        except ImportError:
            QMessageBox.warning(self, "Erro", "OpenCV não está instalado.")

    def carregar_zonas_json(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                zonas = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar zonas", str(e))
            return
        self.overlay_manager.load_zones_from_dict(zonas)

    def redesenhar_zonas(self):
        self.overlay_manager.draw_overlay()

    def carregar_imagem_e_zonas(self, caminho_imagem, tipo):
        """
        Carrega a imagem da íris no canvas, limpa o estado anterior e ajusta a visualização.
        """
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        # 1. Limpar totalmente a cena gráfica
        self.scene.clear()
        
        # 2. Resetar os parâmetros da íris
        self.centro_iris = None
        self.raio_pupila = None
        self.raio_anel = None

        # Carrega a nova imagem
        self.imagem_pixmap = QPixmap(caminho_imagem)
        if self.imagem_pixmap.isNull():
            QMessageBox.warning(self, "Erro de Imagem", f"Não foi possível carregar a imagem de: {caminho_imagem}")
            return

        # 3. Adicionar diretamente o pixmap (imagem original) ao QGraphicsScene
        item = self.scene.addPixmap(self.imagem_pixmap)
        
        # 4. Garantir que a imagem ocupa totalmente o canvas disponível
        self.view.fitInView(item, Qt.AspectRatioMode.KeepAspectRatio)

        # Define valores iniciais para as zonas da íris
        scene_rect = self.view.sceneRect()
        w, h = scene_rect.width(), scene_rect.height()
        # fallback para viewport se scene_rect for inválido
        if w == 0 or h == 0:
            viewport = self.view.viewport()
            if viewport:
                w, h = viewport.width(), viewport.height()
            else:
                w, h = 800, 600  # valores padrão seguros
        self.centro_iris = (w / 2, h / 2)
        self.raio_anel = min(w, h) * 0.45
        self.raio_pupila = self.raio_anel * 0.25
        
        # Garantir que o mouse tracking esteja ativado
        self.view.setMouseTracking(True)
        viewport = self.view.viewport()
        if viewport is not None:
            viewport.setMouseTracking(True)
        
        # Carregar o ficheiro JSON das zonas reflexas correspondente
        json_path = 'assets/iris_esq.json' if tipo == 'esq' else 'assets/iris_drt.json'
        if os.path.exists(json_path):
            # Carregar JSON das zonas
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    zonas = json.load(f)
                    self.overlay_manager.zonas_json = zonas
                    # Desenhar o overlay diretamente
                    self.overlay_manager.draw_overlay()
                    
                    # Certificar que o painel de info esteja pronto
                    self.set_side_label(tipo)
                    self.painel_info.setVisible(False)  # Inicialmente oculto
                    
                    print(f"✅ Imagem e {len(zonas)} zonas carregadas")
            except Exception as e:
                QMessageBox.warning(self, "Erro ao carregar zonas", str(e))
        else:
            QMessageBox.warning(self, "Ficheiro não encontrado", f"O ficheiro de zonas '{json_path}' não foi encontrado.")
            return



    def set_image(self, caminho_imagem, tipo):
        self.caminho_imagem = caminho_imagem
        self.tipo = tipo
        self.set_side_label(tipo)
        if caminho_imagem and tipo:
            self.carregar_imagem_e_zonas(caminho_imagem, tipo)
        else:
            self.scene.clear()
            self.set_side_label(None)

    def set_info_zona_callback(self, callback):
        # Store the callback for zone information display
        self._info_zona_callback = callback

    def atualizar_painel_zona(self, zona):
        """Exibe detalhes da zona no painel lateral usando o callback configurado"""
        # Armazena a zona atual para referência
        self.zona_atual = zona
        
        # Chama o callback configurado (geralmente self.mostrar_info_zona)
        if self._info_zona_callback is not None and callable(self._info_zona_callback):
            self._info_zona_callback(zona)

    def limpar_painel_zona(self):
        """Limpa o painel lateral de informações de zona"""
        # Limpa a referência para a zona atual
        self.zona_atual = None
        
        # Chama o callback com None para ocultar o painel
        if self._info_zona_callback is not None and callable(self._info_zona_callback):
            self._info_zona_callback(None)
    
    def mostrar_info_zona(self, zona_data):
        """Exibe informações detalhadas sobre a zona no painel lateral"""
        if zona_data is None:
            # Sem zona selecionada, oculta o painel
            self.painel_info.setVisible(False)
            print("Painel ocultado - sem dados")
            return
            
        # Exibe o painel - garante que seja realmente exibido
        self.painel_info.setVisible(True)
        self.painel_info.raise_()  # Traz para frente
        
        print(f"Exibindo painel para: {zona_data.get('nome', 'Zona Desconhecida')}")
        
        # Atualiza as informações da zona
        nome = zona_data.get('nome', 'Zona Desconhecida')
        descricao = zona_data.get('descricao', 'Sem descrição disponível.')
        
        # Define cor de fundo baseada na cor da zona (se disponível)
        cor_fundo = "#f8f8f8"  # cor padrão
        if 'estilo' in zona_data and 'fill' in zona_data['estilo']:
            cor = zona_data['estilo']['fill']
            # Aplica a cor com alta transparência
            if cor.startswith('#') and len(cor) >= 7:
                cor_fundo = f"{cor}15"  # 15 = 10% de opacidade em hex
        
        # Aplica estilo com a cor da zona
        self.painel_info.setStyleSheet(f"""
            QFrame {{
                background-color: {cor_fundo};
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 8px;
            }}
        """)
        
        # Atualiza os widgets com as informações da zona
        self.info_nome.setText(nome)
        
        # Formata o texto HTML para a descrição
        html_content = f"<p style='line-height: 1.5;'>{descricao}</p>"
        
        # Adiciona informações adicionais se disponíveis
        if 'orgaos_relacionados' in zona_data:
            orgaos = ", ".join(zona_data['orgaos_relacionados'])
            html_content += f"<p><b>Órgãos relacionados:</b> {orgaos}</p>"
            
        if 'sintomas' in zona_data:
            sintomas = ", ".join(zona_data['sintomas'])
            html_content += f"<p><b>Sintomas:</b> {sintomas}</p>"
        
        # Define o conteúdo HTML
        self.info_descricao.setHtml(html_content)

    def closeEvent(self, event):
        """Limpa os arquivos temporários ao fechar a janela"""
        if hasattr(self, 'temp_files'):
            import os
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Erro ao remover arquivo temporário {temp_file}: {e}")
        super().closeEvent(event)
        
    def toggle_calibracao(self):
        """Alterna o estado de calibração (ON/OFF)"""
        self.calibrating = self.btn_calibracao.isChecked()
        self.btn_calibracao.setText(f"Calibração: {'ON' if self.calibrating else 'OFF'}")
        
        # Controla visibilidade do botão de aplicar calibração
        self.btn_aplicar_calibracao.setVisible(self.calibrating)
        
        if self.calibrating:
            # Iniciar calibração
            self.overlay_manager.start_calibration(
                centro_iris=self.centro_iris,
                raio_pupila=self.pupil_radius,
                raio_anel=self.iris_radius,
                teste_pan=True  # Ativa modo PAN
            )
            print("🔄 Calibração ativada com PAN")
        else:
            # Finalizar calibração
            self.overlay_manager.finish_calibration()
            print("✅ Calibração finalizada")
            
    def toggle_ajuste_fino(self):
        """Alterna o modo de ajuste fino individual (ON/OFF)"""
        self.fine_tuning_mode = self.btn_ajuste_fino.isChecked()
        self.btn_ajuste_fino.setText(f"Ajuste Fino: {'ON' if self.fine_tuning_mode else 'OFF'}")
        
        # Atualiza o modo nos handles de calibração
        self.overlay_manager.set_individual_mode(self.fine_tuning_mode)
        
        if self.fine_tuning_mode:
            print("🔍 Modo ajuste fino ativado")
        else:
            print("🔍 Modo ajuste fino desativado")
            
    def aplicar_calibracao(self):
        """Aplica a calibração atual, redesenha as zonas e fornece feedback visual"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Aplica a calibração atual usando os valores do overlay manager
        dados_calibracao = self.overlay_manager.finish_calibration()
        
        if dados_calibracao:
            # Atualiza os valores internos com os dados finalizados
            self.centro_iris = dados_calibracao.get('center')
            self.raio_pupila = dados_calibracao.get('pupil_radius')
            self.raio_anel = dados_calibracao.get('iris_radius')
            
            # Limpa completamente a cena antes de redesenhar (remove qualquer sobreposição)
            self.overlay_manager.clear()
            
            # Chama terminar_calibragem para garantir que handles e círculos sejam removidos
            self.terminar_calibragem()
            
            # Redesenha as zonas com os novos parâmetros
            self.overlay_manager.draw_overlay()
            
            # Feedback visual - altera temporariamente o botão
            texto_original = self.btn_aplicar_calibracao.text()
            self.btn_aplicar_calibracao.setText("✅ Aplicado com Sucesso!")
            self.btn_aplicar_calibracao.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4caf50, stop:1 #a5d6a7);
                    color: white;
                    border-radius: 8px;
                    padding: 10px 18px;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                }
            """)
            
            # Restaura o estado original após 2 segundos
            from PyQt6.QtCore import QTimer
            timer = QTimer(self)
            timer.singleShot(2000, lambda: self._restaurar_botao_aplicar(texto_original))
            
            # Desativa o modo de calibração
            self.calibrating = False
            self.btn_calibracao.setChecked(False)
            self.btn_calibracao.setText("Calibração: OFF")
            
            # Oculta o botão após aplicação bem-sucedida
            QTimer.singleShot(2100, lambda: self.btn_aplicar_calibracao.setVisible(False))
            
            # Desativa também o modo de ajuste fino se estiver ativo
            if self.fine_tuning_mode:
                self.fine_tuning_mode = False
                self.btn_ajuste_fino.setChecked(False)
                self.btn_ajuste_fino.setText("Ajuste Fino: OFF")
                self.overlay_manager.set_individual_mode(False)
        else:
            # Feedback em caso de erro
            QMessageBox.warning(self, "Erro na Calibração", 
                                "Não foi possível aplicar a calibração. Tente novamente.")
    
    def _restaurar_botao_aplicar(self, texto_original):
        """Restaura o estado original do botão após feedback"""
        self.btn_aplicar_calibracao.setText(texto_original)
        estilizar_botao_moderno(self.btn_aplicar_calibracao, "#4caf50", "#66bb6a")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Apenas ajustar o view, não recarregar imagem automaticamente
        if hasattr(self, 'view'):
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def show_debug_panel(self):
        """Método para testar o painel lateral com dados de exemplo."""
        # Cria um objeto de dados de zona de exemplo
        dados_exemplo = {
            'nome': 'Zona de Teste',
            'descricao': 'Esta é uma zona de teste para verificar o funcionamento do painel lateral.',
            'estilo': {'fill': '#FF5722'},
            'orgaos_relacionados': ['Fígado', 'Intestino'],
            'sintomas': ['Dor', 'Inflamação', 'Desconforto']
        }
        
        # Chama o método para exibir as informações no painel
        self.mostrar_info_zona(dados_exemplo)
        
        # Exibe o painel (caso não esteja visível)
        self.painel_info.setVisible(True)
        
        print("Painel de debug exibido. Verifique se está visível.")
        
        # Retorna True para confirmar que o método foi executado
        return True
        

    
# --- Zoom e Pan fluido ---
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPointF, QEvent
from PyQt6.QtGui import QWheelEvent, QMouseEvent

class IrisGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._pan = False
        self._pan_start = QPointF()
        # Necessário para receber eventos de hover
        self.setMouseTracking(True)
        # Garante que tooltips em QGraphicsItem serão mostrados
        self.setInteractive(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # Desativar barras de rolagem - canvas estático
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event: QWheelEvent):
        # Desativamos o zoom para manter o canvas estático
        event.ignore()

    def mousePressEvent(self, event: QMouseEvent):
        # Ativar pan com o botão do meio ou Alt+clique esquerdo
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self._pan = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            # Processar seleção de zonas
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._pan:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            
            # Pan sem barras de rolagem - move a cena diretamente
            self.translate(delta.x(), delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._pan and (event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.AltModifier)):
            self._pan = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)



