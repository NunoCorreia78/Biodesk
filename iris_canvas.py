from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsPolygonItem, QDialog, QHBoxLayout,
    QLabel, QTextEdit, QComboBox, QGroupBox, QFrame, QSizePolicy, QGraphicsItem,
    QToolTip
)
from PyQt6.QtGui import QPixmap, QPolygonF, QBrush, QPen, QColor, QWheelEvent, QMouseEvent
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
import json
import math
import os
from iris_overlay_manager import IrisOverlayManager
from biodesk_dialogs import BiodeskMessageBox

# 🎨 SISTEMA DE ESTILOS CENTRALIZADO
try:
    from biodesk_styles import BiodeskStyles, ButtonType
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False

try:
    from iris_analysis_config import IrisAnalysisConfig
except ImportError:
    IrisAnalysisConfig = None


# --- Função de morphing para converter pontos polares normalizados em coordenadas no canvas ---
def pontos_para_polygon(pontos_polares, cx, cy, raio_pupila, raio_anel):
    """
    Converte pontos polares normalizados [ângulo_graus, raio_0_1] para coordenadas cartesianas
    
    CORREÇÃO CRÍTICA: O sistema de coordenadas em iridologia:
    - 0° = direita (3h no relógio)
    - 90° = baixo (6h no relógio) 
    - 180° = esquerda (9h no relógio)
    - 270° = cima (12h no relógio)
    """
    
    poly = QPolygonF()
    
    print(f"🔧 Convertendo {len(pontos_polares)} pontos polares...")
    print(f"   Centro: ({cx:.1f}, {cy:.1f})")
    print(f"   Raio pupila: {raio_pupila:.1f}")
    print(f"   Raio íris: {raio_anel:.1f}")
    
    for i, ponto in enumerate(pontos_polares):
        # Verificar se é dicionário com coordenadas polares ou tupla
        if isinstance(ponto, dict):
            # Formato do marcador.py: {"angulo": ..., "raio": ...}
            angulo_graus = float(ponto['angulo'])
            raio_normalizado = float(ponto['raio'])
        else:
            # Formato antigo: (angulo, raio)
            angulo_graus, raio_normalizado = ponto
            angulo_graus = float(angulo_graus)
            raio_normalizado = float(raio_normalizado)
        
        # Converter ângulo de graus para radianos
        # CORREÇÃO: Sistema padrão de iridologia - sem rotação adicional
        angulo_rad = math.radians(angulo_graus)
        
        # Calcular raio absoluto baseado na posição normalizada entre pupila e íris
        raio_absoluto = raio_pupila + (raio_anel - raio_pupila) * raio_normalizado
        
        # Converter para coordenadas cartesianas (sistema padrão matemático)
        # 0° = direita, 90° = cima, 180° = esquerda, 270° = baixo
        x = cx + raio_absoluto * math.cos(angulo_rad)
        y = cy - raio_absoluto * math.sin(angulo_rad)  # Negativo porque Y cresce para baixo
        
        poly.append(QPointF(x, y))
        
        # Debug para os primeiros pontos
        if i < 3:
            print(f"   Ponto {i+1}: {angulo_graus:.1f}° r={raio_normalizado:.3f} → ({x:.1f}, {y:.1f})")
    
    return poly


class SinalAnalysisPopup(QDialog):
    """
    Popup para análise interativa de sinais numa zona específica da íris.
    Implementa o fluxo de 3 passos: hover → clique → seleção de sinal → interpretação.
    """
    
    def __init__(self, zone_data, parent=None):
        super().__init__(parent)
        self.zone_data = zone_data
        self.setup_ui()
        self.setup_signals()
        
    def setup_ui(self):
        """Configura a interface do popup"""
        nome_zona = self.zone_data.get('nome', 'Zona')
        self.setWindowTitle(f'🔍 Análise de Sinais - {nome_zona}')
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Título da zona
        title_label = QLabel(f"📍 {nome_zona}")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Descrição da zona (se disponível)
        descricao = self.zone_data.get('descricao', '')
        if descricao:
            desc_label = QLabel(descricao)
            desc_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 15px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # Seleção de sinal
        signal_group = QGroupBox("🔬 Tipo de Sinal Observado")
        signal_layout = QVBoxLayout()
        
        self.signal_combo = QComboBox()
        self.signal_combo.addItem("-- Selecione o tipo de sinal --")
        
        # Popular com sinais da zona
        sinais = self.zone_data.get('sinais', {})
        for sinal_nome in sorted(sinais.keys()):
            self.signal_combo.addItem(sinal_nome)
            
        signal_layout.addWidget(self.signal_combo)
        signal_group.setLayout(signal_layout)
        layout.addWidget(signal_group)
        
        # Área de interpretação
        interpretation_group = QGroupBox("📋 Interpretação Clínica e Psicoemocional")
        interpretation_layout = QVBoxLayout()
        
        self.interpretation_text = QTextEdit()
        self.interpretation_text.setPlaceholderText(
            "Selecione um tipo de sinal para ver a interpretação...\n\n"
            "A interpretação incluirá:\n"
            "• Aspectos clínicos e fisiológicos\n"
            "• Interpretação psicoemocional (modelo Rayid)\n" 
            "• Recomendações terapêuticas"
        )
        self.interpretation_text.setMinimumHeight(200)
        interpretation_layout.addWidget(self.interpretation_text)
        
        interpretation_group.setLayout(interpretation_layout)
        layout.addWidget(interpretation_group)
        
        # Botões
        button_layout = QHBoxLayout()
        
        # 🎨 Aplicar sistema centralizado
        if STYLES_AVAILABLE:
            self.close_button = BiodeskStyles.create_button("Fechar", ButtonType.DEFAULT)
        else:
            self.close_button = QPushButton("Fechar")
        # ✨ Estilo aplicado automaticamente pelo BiodeskStyleManager
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Estilos aplicados individualmente via sistema centralizado
        
    def setup_signals(self):
        """Configura os sinais e eventos"""
        self.signal_combo.currentTextChanged.connect(self.on_signal_selected)
        
    def on_signal_selected(self, signal_name):
        """Processa a seleção de um sinal e mostra a interpretação"""
        if signal_name == "-- Selecione o tipo de sinal --":
            self.interpretation_text.clear()
            return
            
        sinais = self.zone_data.get('sinais', {})
        sinal_data = sinais.get(signal_name, {})
        
        if sinal_data:
            # Formatar texto usando os novos campos estruturados
            texto_formatado = self.format_interpretation_new_structure(signal_name, sinal_data)
            self.interpretation_text.setHtml(texto_formatado)
        else:
            self.interpretation_text.setPlainText(
                f"⚠️ Interpretação não disponível para '{signal_name}' nesta zona."
            )
    
    def format_interpretation_new_structure(self, signal_name, sinal_data):
        """Formata a interpretação usando a nova estrutura de dados dos sinais"""
        zona_nome = self.zone_data.get('nome', 'Zona')
        
        html = f"""
        <h3 style="color: #e74c3c; margin-bottom: 15px;">
            🔬 {signal_name} na zona {zona_nome}
        </h3>
        """
        
        # Descrição geral
        descricao = sinal_data.get('descricao', '')
        if descricao:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h4 style="color: #2c3e50; margin-bottom: 8px; border-bottom: 1px solid #2c3e50;">
                    📋 Descrição
                </h4>
                <p style="text-align: justify; line-height: 1.6; margin-left: 10px;">
                    {descricao}
                </p>
            </div>
            """
        
        # Interpretação clínica
        interpretacao_clinica = sinal_data.get('interpretação_clinica', '')
        if interpretacao_clinica:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h4 style="color: #3498db; margin-bottom: 8px; border-bottom: 1px solid #3498db;">
                    🏥 Interpretação Clínica
                </h4>
                <p style="text-align: justify; line-height: 1.6; margin-left: 10px;">
                    {interpretacao_clinica}
                </p>
            </div>
            """
        
        # Interpretação psicoemocional
        psicoemocional = sinal_data.get('psicoemocional', '')
        if psicoemocional:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h4 style="color: #9b59b6; margin-bottom: 8px; border-bottom: 1px solid #9b59b6;">
                    🧠 Interpretação Psicoemocional (Rayid)
                </h4>
                <p style="text-align: justify; line-height: 1.6; margin-left: 10px;">
                    {psicoemocional}
                </p>
            </div>
            """
        
        return html
    
    def format_interpretation(self, signal_name, interpretation):
        """Formata a interpretação para apresentação em HTML"""
        zona_nome = self.zone_data.get('nome', 'Zona')
        
        # Dividir interpretação em parágrafos
        paragrafos = interpretation.split('\n')
        
        # Agrupar parágrafos por tipo
        paragrafos_clinicos = []
        paragrafos_psicoemocionais = []
        
        for paragrafo in paragrafos:
            if paragrafo.strip():
                if "psicoemocional" in paragrafo.lower() or "rayid" in paragrafo.lower() or "emocional" in paragrafo.lower():
                    paragrafos_psicoemocionais.append(paragrafo.strip())
                else:
                    paragrafos_clinicos.append(paragrafo.strip())
        
        html = f"""
        <h3 style="color: #e74c3c; margin-bottom: 15px;">
            🔬 {signal_name} na zona {zona_nome}
        </h3>
        """
        
        # Adicionar seção clínica se houver parágrafos clínicos
        if paragrafos_clinicos:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h4 style="color: #3498db; margin-bottom: 8px; border-bottom: 1px solid #3498db;">
                    🏥 Análise Clínica
                </h4>
            """
            for paragrafo in paragrafos_clinicos:
                html += f"""
                <p style="text-align: justify; line-height: 1.6; margin-left: 10px; margin-bottom: 10px;">
                    {paragrafo}
                </p>
                """
            html += "</div>"
        
        # Adicionar seção psicoemocional se houver parágrafos psico-emocionais
        if paragrafos_psicoemocionais:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h4 style="color: #9b59b6; margin-bottom: 8px; border-bottom: 1px solid #9b59b6;">
                    🧠 Análise Psicoemocional
                </h4>
            """
            for paragrafo in paragrafos_psicoemocionais:
                html += f"""
                <p style="text-align: justify; line-height: 1.6; margin-left: 10px; margin-bottom: 10px;">
                    {paragrafo}
                </p>
                """
            html += "</div>"
        
        return html


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
        # Para armazenar referência ao IrisCanvas
        self.iris_canvas = None
        
        # Adicionar borda sutil para melhor visualização
        self.setPen(QPen(QColor(255, 255, 255, 50), 1))  # Branco com 50% de opacidade
        
        # Definir tooltip simples
        self.setToolTip(f"{dados_zona['nome']}: {dados_zona.get('descricao', '')}")
        
    def sceneEventFilter(self, watched, event):
        # Filtro de eventos da scene para debug opcional
        return super().sceneEventFilter(watched, event)
        
    def atualizar_shape(self, cx, cy, raio_pupila, raio_anel):
        # CORREÇÃO: Tratar as coordenadas como polares (ângulo, raio_normalizado)
        # Suportar formato novo e antigo
        
        pontos_dados = None
        if 'pontos' in self.dados_originais and self.dados_originais['pontos']:
            # Formato antigo
            pontos_dados = self.dados_originais['pontos']
        elif 'partes' in self.dados_originais and self.dados_originais['partes']:
            # Formato novo do marcador.py
            pontos_dados = self.dados_originais['partes'][0]  # Usar primeira parte
        
        if pontos_dados and len(pontos_dados) > 0:
            primeiro_ponto = pontos_dados[0]
            
            # Verificar se é dicionário (formato novo) ou tupla (formato antigo)
            if isinstance(primeiro_ponto, dict):
                # Formato do marcador.py: {"angulo": ..., "raio": ...}
                angulo = primeiro_ponto.get('angulo', 0)
                raio_norm = primeiro_ponto.get('raio', 0)
            elif isinstance(primeiro_ponto, (list, tuple)) and len(primeiro_ponto) == 2:
                # Formato antigo: [ângulo, raio_normalizado]
                angulo, raio_norm = primeiro_ponto
            else:
                # Formato desconhecido, tentar como polares
                nova_polygon = pontos_para_polygon(pontos_dados, cx, cy, raio_pupila, raio_anel)
                self.setPolygon(nova_polygon)
                return
                
            # Se o ângulo está em graus (0-360) e o raio é normalizado (0-1)
            if 0 <= angulo <= 360 and 0 <= raio_norm <= 1:
                # Coordenadas polares normalizadas - converter para cartesianas
                print(f"🔄 Convertendo coordenadas polares para zona: {self.dados_originais.get('nome', 'Desconhecida')}")
                nova_polygon = pontos_para_polygon(pontos_dados, cx, cy, raio_pupila, raio_anel)
                self.setPolygon(nova_polygon)
            else:
                # Coordenadas cartesianas - usar diretamente
                poly = QPolygonF()
                for ponto in pontos_dados:
                    if isinstance(ponto, dict):
                        # Se chegou aqui como dict, deve ser erro de formato
                        continue
                    x, y = ponto
                    poly.append(QPointF(x, y))
                self.setPolygon(poly)
        else:
            print("⚠️ Nenhum ponto encontrado na zona")

    def set_brush_pen(self, estilo):
        fill = QColor(estilo.get('fill', '#CCCCCC'))
        stroke = QColor(estilo.get('stroke', '#333333'))
        width = estilo.get('stroke-width', 1.0)
        
        # CORREÇÃO: Aumentar a opacidade para melhor visibilidade
        fill.setAlpha(150)  # Mais opaco para melhor visualização
        
        self.setBrush(QBrush(fill))
        self.setPen(QPen(stroke, width))
        
    def set_iris_canvas(self, canvas):
        """Define a referência direta ao IrisCanvas"""
        self.iris_canvas = canvas

    def hoverEnterEvent(self, event):
        print(f"🖱️  Hover ENTER na zona: {self.dados_originais.get('nome', 'Desconhecida')}")
        
        # Destaca a zona aumentando a opacidade
        self.setOpacity(1.0)
        
        # Mostra o tooltip com o nome da zona
        nome_zona = self.dados_originais.get('nome', 'Zona desconhecida')
        descricao = self.dados_originais.get('descricao', 'Sem descrição disponível')
        
        # Cria tooltip com formatação HTML
        tooltip_text = f"<b>{nome_zona}</b><br>{descricao}"
        self.setToolTip(tooltip_text)
        
        # Força a exibição do tooltip
        try:
            pos = event.screenPos()
            if hasattr(pos, 'toPoint'):
                tooltip_pos = pos.toPoint()
            else:
                tooltip_pos = pos  # Já é QPoint
            QToolTip.showText(tooltip_pos, tooltip_text)
        except Exception as e:
            print(f"❌ Erro ao mostrar tooltip: {e}")
        
        print(f"📝 Tooltip definido: {tooltip_text}")
        
        # (Chamadas ao painel_info removidas - funcionalidade de tooltip preservada)
                
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        print(f"🖱️  Hover LEAVE na zona: {self.dados_originais.get('nome', 'Desconhecida')}")
        
        # Restaura a opacidade original
        self.setOpacity(self.default_opacity)
        
        # Remove o tooltip e oculta
        self.setToolTip("")
        QToolTip.hideText()
            
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        # 🆕 Emitir sinal de zona clicada (apenas no modo normal, não anónimo)
        if (self.iris_canvas is not None and 
            hasattr(self.iris_canvas, 'zonaClicada') and 
            not getattr(self.iris_canvas, 'modo_anonimo', True)):
            nome_zona = self.dados_originais.get('nome', 'Zona desconhecida')
            print(f"[SINAL] Emitindo zonaClicada para: {nome_zona}")
            self.iris_canvas.zonaClicada.emit(nome_zona)
        
        # 🔍 Nova funcionalidade: Análise interativa de sinais
        if event.button() == Qt.MouseButton.LeftButton:
            self.abrir_analise_sinais()
                
        super().mousePressEvent(event)
    
    def abrir_analise_sinais(self):
        """
        Abre popup para análise interativa de sinais na zona clicada.
        """
        nome_zona = self.dados_originais.get('nome', 'Zona desconhecida')
        print(f"🔍 Abrindo análise de sinais para: {nome_zona}")
        
        # ✅ CORREÇÃO: Priorizar sinais embutidos nas zonas, fallback para ficheiro separado
        sinais_embutidos = self.dados_originais.get('sinais', {})
        
        if sinais_embutidos:
            # Usar sinais embutidos na zona (formato dict)
            print(f"✅ Usando sinais embutidos: {len(sinais_embutidos)} sinais encontrados")
            sinais = sinais_embutidos
        else:
            # Fallback: carregar do ficheiro separado (formato list)
            sinais_lista = self.carregar_sinais_zona(nome_zona)
            if sinais_lista:
                # Converter lista para dict
                sinais = {sinal.get('nome', f'Sinal {i}'): sinal for i, sinal in enumerate(sinais_lista)}
                print(f"✅ Usando sinais do ficheiro separado: {len(sinais)} sinais encontrados")
            else:
                sinais = {}
        
        if not sinais:
            # Se não há sinais definidos, apenas registar na consola - não mostrar popup
            print(f"⚠️ Zona '{nome_zona}' está mapeada mas ainda não tem sinais específicos definidos")
            return
        
        # Integrar sinais nos dados da zona
        dados_zona_com_sinais = self.dados_originais.copy()
        dados_zona_com_sinais['sinais'] = sinais
        
        # Criar e abrir popup de análise
        try:
            popup = SinalAnalysisPopup(dados_zona_com_sinais, parent=self.iris_canvas)
            popup.exec()
        except Exception as e:
            print(f"❌ Erro ao abrir popup de análise: {e}")
            BiodeskMessageBox.critical(
                None,
                "Erro",
                f"Erro ao abrir análise de sinais:\n\n{str(e)}"
            )
    
    def carregar_sinais_zona(self, nome_zona):
        """
        Carrega os sinais específicos de uma zona a partir dos ficheiros JSON de sinais.
        ✅ CORREÇÃO: Usar JSON correto para cada olho (esq → esq, drt → drt)
        """
        
        # Determinar o tipo de íris e usar o ficheiro correto
        tipo_iris = getattr(self.iris_canvas, 'tipo', 'drt') or 'drt'
        tipo_iris = tipo_iris.lower()
        
        # ✅ CORREÇÃO: Usar ficheiro correto para cada olho
        if tipo_iris.startswith('esq'):
            caminho_sinais = os.path.join('assets', 'sinais_esq.json')
        else:
            caminho_sinais = os.path.join('assets', 'sinais_drt.json')
        
        print(f"📁 Carregando sinais de: {caminho_sinais} para zona '{nome_zona}'")
        
        if not os.path.exists(caminho_sinais):
            print(f"❌ Ficheiro de sinais não encontrado: {caminho_sinais}")
            return []
        
        try:
            with open(caminho_sinais, 'r', encoding='utf-8') as f:
                dados_sinais = json.load(f)
            
            # Procurar sinais para esta zona específica
            sinais_zona = dados_sinais.get(nome_zona, [])
            print(f"✅ Carregados {len(sinais_zona)} sinais para zona '{nome_zona}' do ficheiro {caminho_sinais}")
            return sinais_zona
            
        except Exception as e:
            print(f"❌ Erro ao carregar sinais: {e}")
            return []

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
    # 🆕 Sinais Qt para comunicação com outros componentes
    zonaClicada = pyqtSignal(str)  # Emite o nome da zona clicada
    calibracao_mudou = pyqtSignal(bool)  # Emite quando calibração é ativada/desativada
    ajuste_fino_mudou = pyqtSignal(bool)  # Emite quando ajuste fino é ativado/desativado
    
    def redesenhar_zonas(self):
        # Apagar zonas antigas
        for item in self.scene.items():
            if isinstance(item, ZonaReflexa):
                self.scene.removeItem(item)

        cx, cy, r_anel, r_pupila = 0, 0, 0, 0
        if self.centro_iris and self.raio_anel and self.raio_pupila:
            cx, cy = self.centro_iris
            r_anel = self.raio_anel
            r_pupila = self.raio_pupila
        else:
            viewport = self.view.viewport()
            w, h = (viewport.width(), viewport.height()) if viewport else (800, 600)
            cx, cy = w / 2, h / 2
            r_anel = min(w, h) * 0.45
            r_pupila = r_anel * 0.25

        self.zonas = []
        for zona_data in getattr(self, 'zonas_json', []):
            # 🔥 CORREÇÃO: Renderizar TODAS as partes de uma zona
            partes = zona_data.get('partes', [])
            if not partes and zona_data.get('pontos'):
                # Formato antigo - apenas uma parte
                partes = [zona_data.get('pontos')]
            
            print(f"🔍 Zona '{zona_data.get('nome')}': {len(partes)} partes a renderizar")
            
            # Criar uma ZonaReflexa para cada parte da zona
            for i, pontos in enumerate(partes):
                if not pontos:
                    continue
                    
                # Criar dados para esta parte específica
                dados_parte = zona_data.copy()
                dados_parte['pontos'] = pontos  # Esta parte específica
                
                # Adicionar sufixo se há múltiplas partes (para debug)
                if len(partes) > 1:
                    dados_parte['nome_parte'] = f"{zona_data.get('nome')} (Parte {i+1})"
                    print(f"   Renderizando parte {i+1}/{len(partes)}")
                
                item = ZonaReflexa(dados_parte, cx, cy, r_pupila, r_anel)
                item.set_iris_canvas(self)  # garante ligação ao painel lateral
                self.scene.addItem(item)
                self.zonas.append(item)
                
        print(f"🔍 {len(self.zonas)} zonas/partes desenhadas no canvas.")
    def __init__(self, paciente_data: dict | None = None, caminho_imagem: str | None = None, tipo: str | None = None, parent=None, criar_toolbar=True):
        super().__init__(parent)
        self.paciente_data = paciente_data
        self.caminho_imagem = caminho_imagem
        self.tipo = tipo
        self.criar_toolbar = criar_toolbar  # Armazenar se deve criar toolbar própria
        
        # ✅ IMPLEMENTAÇÃO OBRIGATÓRIA: Detectar modo anônimo
        # Se não há paciente_data, estamos em modo anônimo
        self.modo_anonimo = paciente_data is None
        
        titulo = (f"Análise de Íris – {paciente_data.get('nome', 'Paciente')}" 
                  if paciente_data else "Análise de Íris (modo anónimo)")
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
        self.mapa_visivel = True   # mapa inicia visível por defeito
        
        self.init_ui()
        self.imagem_pixmap = None
        # Instancia o overlay manager para gerir zonas, morphing, etc
        self.overlay_manager = IrisOverlayManager(self.scene)
        # ✅ Definir referência ao IrisCanvas no overlay manager
        self.overlay_manager.iris_canvas = self
        # Parâmetros da íris
        self.centro_iris = None
        self.raio_pupila = None
        self.raio_anel = None
        
        # Backup das zonas JSON para preservar durante calibração
        self.zonas_json = []
        
        # Apenas carregar a imagem se um caminho e tipo válidos forem fornecidos
        if self.caminho_imagem and self.tipo:
            self.carregar_imagem_e_zonas(self.caminho_imagem, self.tipo)

    def carregar_imagem_e_zonas(self, caminho_imagem, tipo=None):
        """
        Carrega a imagem da íris no canvas, limpa o estado anterior e ajusta a visualização.
        Se tipo não for fornecido, tenta detectar automaticamente.
        """
        if not caminho_imagem or not os.path.exists(caminho_imagem):
            print(f"Aviso: Arquivo de imagem não encontrado: {caminho_imagem}")
            return

        # Se o tipo não for fornecido, tenta detectar automaticamente
        if tipo is None:
            tipo = self.detectar_tipo_imagem(caminho_imagem)
            if not tipo:
                print("Não foi possível determinar o tipo da imagem (esq/drt).")
                return

        # Limpa a cena antes de carregar nova imagem
        self.scene.clear()
        
        # Carrega a imagem
        self.imagem_pixmap = QPixmap(caminho_imagem)
        if self.imagem_pixmap.isNull():
            print(f"Erro ao carregar a imagem: {caminho_imagem}")
            return

        # Adiciona a imagem à cena
        self.scene.addPixmap(self.imagem_pixmap)
        self.view.setScene(self.scene)
        
        # Ajusta a visualização
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Define o tipo de imagem (esq/drt)
        self.tipo = tipo
        self.set_side_label(tipo)
        
        # Carrega as zonas reflexas correspondentes
        self.overlay_manager.carregar_zonas(tipo)
        
        # Garante que todas as zonas têm referência ao IrisCanvas
        self.garantir_referencias_iris_canvas()
        
        # Atualiza a visibilidade dos botões
        self.controlar_visibilidade_botoes(tem_imagens=True)
    
    def init_ui(self):

        # Primeiro configurar tracking e hover
        self.view = IrisGraphicsView(self)
        self.view.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.view.setMouseTracking(True)
        
        # CORREÇÃO: Configurar tooltip explicitamente
        self.view.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
        
        viewport = self.view.viewport()
        if viewport is not None:
            viewport.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            viewport.setMouseTracking(True)
            viewport.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)

        # Depois criar scene e configurar outros parâmetros
        self.scene = QGraphicsScene(self)  # Garante associação ao self
        self.view.setScene(self.scene)
        
        # Criar overlay manager e zonas
        self.overlay_manager = IrisOverlayManager(self.scene)
        self.overlay_manager.iris_canvas = self  # Adicionar referência ao IrisCanvas

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Rótulo do olho (esquerdo/direito)
        self.side_label = QLabel("")
        self.side_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.side_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 2px;")  # Margem reduzida
        self.side_label.hide()  # Ocultar por padrão até ter conteúdo
        main_layout.addWidget(self.side_label)

        # ═══════════════ TOOLBAR DE CALIBRAÇÃO E MORPHING ═══════════════
        # Só criar toolbar se criar_toolbar=True
        if self.criar_toolbar:
            toolbar_layout = QHBoxLayout()
            toolbar_layout.setContentsMargins(5, 2, 5, 2)  # Margens reduzidas
            toolbar_layout.setSpacing(8)  # Espaçamento reduzido

            # Botão para calibração - INFO (azul) detectado automaticamente
            if STYLES_AVAILABLE:
                self.btn_calibracao = BiodeskStyles.create_button("Calibrar", ButtonType.TOOL)
            else:
                self.btn_calibracao = QPushButton("Calibrar")
            self.btn_calibracao.setCheckable(True)
            self.btn_calibracao.setChecked(False)
            self.btn_calibracao.setToolTip("Ativar/desativar modo de calibração para ajustar centro e raios da íris")
            toolbar_layout.addWidget(self.btn_calibracao)

            # Botão para ajuste fino (morphing) - PRIMARY (cor principal) detectado automaticamente  
            if STYLES_AVAILABLE:
                self.btn_ajuste_fino = BiodeskStyles.create_button("Ajustar", ButtonType.TOOL)
            else:
                self.btn_ajuste_fino = QPushButton("Ajustar")
            self.btn_ajuste_fino.setCheckable(True)
            self.btn_ajuste_fino.setChecked(False)
            self.btn_ajuste_fino.setToolTip("Ativar/desativar ajuste fino (morphing) para deformar íris e pupila")
            toolbar_layout.addWidget(self.btn_ajuste_fino)

            # Botões de zoom - WARNING (amarelo) detectado automaticamente
            if STYLES_AVAILABLE:
                self.btn_zoom_in = BiodeskStyles.create_button("🔍+", ButtonType.TOOL)
            else:
                self.btn_zoom_in = QPushButton("🔍+")
            self.btn_zoom_in.setToolTip("Ampliar imagem")
            toolbar_layout.addWidget(self.btn_zoom_in)

            if STYLES_AVAILABLE:
                self.btn_zoom_out = BiodeskStyles.create_button("🔍-", ButtonType.TOOL)
            else:
                self.btn_zoom_out = QPushButton("🔍-")
            self.btn_zoom_out.setToolTip("Reduzir imagem")
            toolbar_layout.addWidget(self.btn_zoom_out)

            if STYLES_AVAILABLE:
                self.btn_zoom_fit = BiodeskStyles.create_button("📐", ButtonType.TOOL)
            else:
                self.btn_zoom_fit = QPushButton("📐")
            self.btn_zoom_fit.setToolTip("Ajustar imagem à janela")
            toolbar_layout.addWidget(self.btn_zoom_fit)

            # Botão para ocultar/mostrar mapa - SECONDARY (cinza) detectado automaticamente
            if STYLES_AVAILABLE:
                self.btn_ocultar_mapa = BiodeskStyles.create_button("👁️ Mapa", ButtonType.NAVIGATION)
            else:
                self.btn_ocultar_mapa = QPushButton("👁️ Mapa")
            self.btn_ocultar_mapa.setToolTip("Ocultar/mostrar o mapa da íris e todos os overlays")
            toolbar_layout.addWidget(self.btn_ocultar_mapa)

            # Espaço flexível à direita
            toolbar_layout.addStretch()

            # Adicionar toolbar ao layout principal
            main_layout.addLayout(toolbar_layout)
        else:
            # Quando toolbar não deve ser criada (ex: dentro do IrisAnonimaCanvas)
            print("[DEBUG] Toolbar omitida - criar_toolbar=False")
            self.btn_calibracao = None
            self.btn_ajuste_fino = None
            self.btn_zoom_in = None
            self.btn_zoom_out = None
            self.btn_zoom_fit = None
            self.btn_ocultar_mapa = None

        # Layout principal para canvas (painel lateral removido)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.view, 1)  # Canvas de íris ocupa todo o espaço disponível
        
        # Inicializa zona_atual como None
        self.zona_atual = None
        
        # Placeholder para futuros controles (oculto por padrão)
        self.placeholder_frame = QFrame()
        self.placeholder_frame.setFixedWidth(120)
        self.placeholder_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.placeholder_frame.hide()
        content_layout.addWidget(self.placeholder_frame)
        
        # Adicionar o layout de conteúdo (apenas canvas) ao layout principal
        main_layout.addLayout(content_layout, 1)
        self.setLayout(main_layout)

        # ═══════════════ CONECTAR BOTÕES DA TOOLBAR ═══════════════
        # Só conectar se os botões foram criados
        if self.criar_toolbar and hasattr(self, 'btn_calibracao') and self.btn_calibracao:
            self.btn_calibracao.clicked.connect(self.toggle_calibracao)
            self.btn_ajuste_fino.clicked.connect(self.toggle_ajuste_fino)
            self.btn_zoom_in.clicked.connect(self.zoom_in)
            self.btn_zoom_out.clicked.connect(self.zoom_out)
            self.btn_zoom_fit.clicked.connect(self.zoom_fit)
            self.btn_ocultar_mapa.clicked.connect(self.toggle_mapa_visibilidade)

    def _on_analise_alterada(self, constituicao: str, sinais: list):
        """Callback quando análise de íris é alterada"""
        print(f"[ANÁLISE] Constituição: {constituicao}, Sinais: {sinais}")
        # Pode ser usado para atualizar outros componentes se necessário
    
    def _on_analise_guardada(self, dados: dict):
        """Callback quando análise é guardada"""
        print(f"[ANÁLISE GUARDADA] {dados}")
        # Aqui podemos integrar com histórico ou outros módulos
        self._integrar_analise_com_historico(dados)
    
    def _integrar_analise_com_historico(self, dados: dict):
        """Integra análise guardada com o histórico do paciente"""
        if not self.paciente_data or not dados:
            return
            
        try:
            
            # Criar resumo para histórico
            resumo = IrisAnalysisConfig.criar_resumo_analise(
                dados.get('constituicao'),
                dados.get('sinais', [])
            )
            
            # Aqui pode integrar com sistema de histórico se existir
            print(f"[HISTÓRICO] Adicionado: {resumo}")
            
        except Exception as e:
            print(f"[ERRO] Falha ao integrar com histórico: {e}")

    def definir_imagem_atual(self, imagem_id: int):
        """Define a imagem atual para análise"""
        if hasattr(self, 'widget_analise'):
            self.widget_analise.set_imagem_id(imagem_id)
            print(f"[ANÁLISE] Imagem definida para análise: ID {imagem_id}")

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
            self.side_label.hide()  # Ocultar quando vazio
        elif str(tipo).lower() == "esq":
            self.side_label.setText("Olho Esquerdo")
            self.side_label.show()  # Mostrar quando tem conteúdo
        elif str(tipo).lower() == "drt":
            self.side_label.setText("Olho Direito")
            self.side_label.show()  # Mostrar quando tem conteúdo
        else:
            self.side_label.setText(str(tipo))
            self.side_label.show()  # Mostrar quando tem conteúdo
        
    def controlar_visibilidade_botoes(self, tem_imagens=False):
        """
        Controla a visibilidade dos botões baseado na existência de imagens.
        ✅ IMPLEMENTAÇÃO OBRIGATÓRIA: Não mostrar menus de exportação/gravação no modo anónimo.
        """
        # ❌ No modo anônimo, não há funcionalidades de exportação/gravação
        if self.modo_anonimo:
            print("🔒 Modo anónimo: funcionalidades de gravação/exportação desabilitadas")
            # Ocultar botões de exportação se existirem
            if hasattr(self, 'btn_exportar'):
                self.btn_exportar.setVisible(False)
            if hasattr(self, 'btn_gravar'):
                self.btn_gravar.setVisible(False)
            if hasattr(self, 'btn_salvar'):
                self.btn_salvar.setVisible(False)
    
    def pode_exportar_gravar(self):
        """
        Verifica se funcionalidades de exportação/gravação estão permitidas.
        ✅ IMPLEMENTAÇÃO OBRIGATÓRIA: Retorna False no modo anónimo e no separador Íris.
        """
        return not self.modo_anonimo



    def garantir_referencias_iris_canvas(self):
        """Garante que todas as zonas têm referência ao IrisCanvas"""
        for i, zona in enumerate(self.overlay_manager.zonas):
            if zona.iris_canvas is None:
                zona.set_iris_canvas(self)
                
        # CORREÇÃO: Garantir configurações de hover após definir referências
        self.configurar_hover_zonas()
    
    def configurar_hover_zonas(self):
        """Configura os eventos de hover para todas as zonas"""
        print(f"🔧 Configurando hover para {len(self.overlay_manager.zonas)} zonas...")
        
        # CORREÇÃO: Garantir que o mouse tracking está ativo na view e viewport
        self.view.setMouseTracking(True)
        self.view.viewport().setMouseTracking(True)
        self.view.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.view.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.view.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
        self.view.viewport().setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
        
        for i, zona in enumerate(self.overlay_manager.zonas):
            # Garantir que a zona aceita eventos de hover
            zona.setAcceptHoverEvents(True)
            
            # CORREÇÃO: Garantir Z-value alto para ficar acima da imagem
            zona.setZValue(100 + i)  # Muito acima da imagem (que está em 0)
            
            # Definir um tooltip simples como fallback
            nome = zona.dados_originais.get('nome', f'Zona {i+1}')
            descricao = zona.dados_originais.get('descricao', 'Sem descrição')
            zona.setToolTip(f"{nome}: {descricao}")
            
            # Garantir que está visível e interativo
            zona.setVisible(True)
            zona.setEnabled(True)
            
            # CORREÇÃO: Definir opacidade mais alta para melhor visualização
            zona.setOpacity(0.7)  # Aumentado de 0.4 para 0.7
            
            # CORREÇÃO: Garantir que eventos de mouse são aceitos
            zona.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
            
            print(f"   ✅ Zona {i+1}: {nome} - Hover configurado (Z:{100+i})")
        
        print(f"✅ Sistema de hover totalmente configurado para {len(self.overlay_manager.zonas)} zonas")

    def atualizar_todas_zonas(self):
        """Atualiza todas as zonas reflexas com novos parâmetros de centro e raios."""
        if self.centro_iris and self.raio_pupila and self.raio_anel:
            print(f"🔄 Atualizando {len(self.overlay_manager.zonas)} zonas com calibração...")
            
            for i, zona in enumerate(self.overlay_manager.zonas):
                # Atualiza a forma da zona baseada nos novos parâmetros
                zona.atualizar_shape(self.centro_iris[0], self.centro_iris[1], self.raio_pupila, self.raio_anel)
                
                # CORREÇÃO CRÍTICA: Reconfigurar completamente os eventos de hover
                zona.setAcceptHoverEvents(True)
                zona.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
                
                # Garantir referência ao IrisCanvas
                if zona.iris_canvas is None:
                    zona.set_iris_canvas(self)
                
                # Configurar Z-value para ficar acima da imagem
                zona.setZValue(100 + i)
                
                # Garantir visibilidade e interatividade
                zona.setVisible(True)
                zona.setEnabled(True)
                
                # Restaurar opacidade padrão
                zona.setOpacity(zona.default_opacity)
                
                # Reconfigurar tooltip
                nome = zona.dados_originais.get('nome', f'Zona {i+1}')
                descricao = zona.dados_originais.get('descricao', 'Sem descrição')
                zona.setToolTip(f"{nome}: {descricao}")
                
                # Garantir que não há transformações que impeçam interação
                zona.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)
                
                print(f"   ✅ Zona {i+1}: {nome} - Hover reconfigurado")
            
            # CORREÇÃO: Forçar reconfiguração completa do hover
            print("🔧 Reconfigurando sistema de hover...")
            self.configurar_hover_zonas()
            
            print(f"✅ Todas as {len(self.overlay_manager.zonas)} zonas atualizadas e hover preservado")

    def detectar_tipo_imagem(self, caminho_imagem):
        """Detecta se a imagem é do olho esquerdo ou direito baseado no nome"""
        nome_arquivo = os.path.basename(caminho_imagem).lower()
        
        # Palavras-chave para olho esquerdo
        palavras_esq = ['esq', 'left', 'esquerdo', 'e_', '_e_', 'lft']
        
        # Palavras-chave para olho direito  
        palavras_drt = ['drt', 'right', 'direito', 'd_', '_d_', 'rgt']
        
        for palavra in palavras_esq:
            if palavra in nome_arquivo:
                return 'esq'
                
        for palavra in palavras_drt:
            if palavra in nome_arquivo:
                return 'drt'
                
        # Se não conseguir detectar, assume esquerdo por padrão
        return 'esq'

    def carregar_imagem_e_zonas(self, caminho_imagem, tipo=None):
        """
        Carrega a imagem da íris no canvas, limpa o estado anterior e ajusta a visualização.
        
        ⚠️ IMPLEMENTAÇÃO OBRIGATÓRIA: 
        - O JSON é carregado preservando as coordenadas polares originais [ângulo, raio_normalizado]
        - A calibracao_inicial do JSON é usada como "base estática"
        - A calibração do utilizador serve apenas para ajustar visualmente a sobreposição
        - As coordenadas polares são convertidas dinamicamente para cartesianas usando a calibração atual
        """
        
        # Se tipo não foi especificado, detectar automaticamente
        if tipo is None:
            tipo = self.detectar_tipo_imagem(caminho_imagem)
        
        # 1. Limpar totalmente a cena gráfica
        self.scene.clear()
        
        # 2. Resetar os parâmetros da íris
        self.centro_iris = None
        self.raio_pupila = None
        self.raio_anel = None

        # Carrega a nova imagem
        self.imagem_pixmap = QPixmap(caminho_imagem)
        if self.imagem_pixmap.isNull():
            print(f"❌ Erro ao carregar imagem: {caminho_imagem}")
            return

        # 3. Adicionar diretamente o pixmap (imagem original) ao QGraphicsScene
        item = self.scene.addPixmap(self.imagem_pixmap)
        
        # Define Z-Value para imagem ficar abaixo das zonas (se não for None)
        if item is not None:
            item.setZValue(0)  # Imagem fica na camada mais baixa
        
        # 4. CORREÇÃO: Configurar a scene com o tamanho correto da imagem
        image_rect = self.imagem_pixmap.rect()
        # CORREÇÃO: Converter QRect para QRectF para compatibilidade
        scene_rect = QRectF(image_rect)
        self.scene.setSceneRect(scene_rect)
        
        # 5. CORREÇÃO: Garantir que a view mostra a imagem em tamanho adequado
        # Primeiro ajustar a view para mostrar toda a cena
        self.view.setScene(self.scene)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # 6. CORREÇÃO: Configurar zoom mínimo para garantir visibilidade adequada
        view_size = self.view.viewport().size()
        scene_size = self.scene.sceneRect().size()
        
        # Calcular fator de escala para garantir tamanho mínimo adequado
        scale_x = view_size.width() / scene_size.width() if scene_size.width() > 0 else 1.0
        scale_y = view_size.height() / scene_size.height() if scene_size.height() > 0 else 1.0
        
        # Usar o menor fator para manter proporção, mas garantir tamanho mínimo
        scale_factor = min(scale_x, scale_y)
        if scale_factor < 0.5:  # Se muito pequeno, definir tamanho mínimo
            scale_factor = 0.8  # 80% do viewport
            
        self.view.resetTransform()
        self.view.scale(scale_factor, scale_factor)
        
        # Debug: Informações sobre a visualização
        print(f"📊 Imagem original: {image_rect.width()}x{image_rect.height()}")
        print(f"📊 View viewport: {view_size.width()}x{view_size.height()}")
        print(f"📊 Fator de escala aplicado: {scale_factor:.2f}")
        print(f"📊 Scene rect: {self.scene.sceneRect()}")
        print(f"📊 Item rect: {item.boundingRect()}")

        # Carregar o ficheiro JSON das zonas reflexas correspondente
        print(f"🔄 Carregando zonas para tipo: {tipo}")
        tipo = (tipo or "").lower()
        if tipo.startswith("esq"):
            json_path = 'assets/iris_esq.json'
            sinais_path = 'assets/iris_esq.json'  # ✅ CORREÇÃO: Sinais do esquerdo para esquerdo
        else:
            json_path = 'assets/iris_drt.json'
            sinais_path = 'assets/iris_drt.json'  # ✅ CORREÇÃO: Sinais do direito para direito
        
        print(f"📁 Tentando carregar zonas: {json_path}")
        print(f"📁 Sinais serão carregados de: {sinais_path}")
        
        # 🔥 CARREGAR SINAIS SEPARADAMENTE do iris_esq.json
        sinais_data = {}
        if os.path.exists(sinais_path):
            try:
                with open(sinais_path, 'r', encoding='utf-8') as f:
                    sinais_json = json.load(f)
                    
                if isinstance(sinais_json, dict) and 'zonas' in sinais_json:
                    for zona in sinais_json['zonas']:
                        nome_zona = zona.get('nome', '')
                        sinais_zona = zona.get('sinais', {})
                        if nome_zona and sinais_zona:
                            sinais_data[nome_zona] = sinais_zona
                    print(f"✅ Carregados sinais para {len(sinais_data)} zonas")
                else:
                    print("❌ Formato de sinais não reconhecido")
            except Exception as e:
                print(f"❌ Erro ao carregar sinais: {e}")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # ✅ IMPLEMENTAÇÃO OBRIGATÓRIA: Verificar formato do JSON
                if isinstance(data, list):
                    # Formato novo: JSON é uma lista de zonas diretamente (sem calibração inicial)
                    calibracao_inicial = {}
                    metadata = {}
                    print(f"📋 JSON formato novo: lista com {len(data)} zonas")
                elif isinstance(data, dict):
                    # Formato antigo: JSON é um dict com 'zonas' e 'calibracao_inicial'
                    calibracao_inicial = data.get('calibracao_inicial', {})
                    metadata = data.get('metadata', {})
                    print(f"📋 JSON formato antigo: dict com chaves {list(data.keys())}")
                else:
                    print(f"❌ Formato JSON não reconhecido: {type(data)}")
                    return
                
                if calibracao_inicial:
                    # Obter calibração original do JSON
                    centro_json = calibracao_inicial.get('centro', [400, 300])
                    raio_pupila_json = calibracao_inicial.get('raio_pupila', 50)
                    raio_iris_json = calibracao_inicial.get('raio_iris', 120)
                    
                    # Obter dimensões esperadas vs reais
                    resolucao_esperada = metadata.get('resolucao', [image_rect.width(), image_rect.height()])
                    resolucao_real = [image_rect.width(), image_rect.height()]
                    
                    print(f"📏 Resolução esperada (JSON): {resolucao_esperada[0]}x{resolucao_esperada[1]}")
                    print(f"📏 Resolução real (imagem): {resolucao_real[0]}x{resolucao_real[1]}")
                    
                    # CORREÇÃO AUTOMÁTICA: Calcular fator de escala se necessário
                    if resolucao_esperada != resolucao_real:
                        scale_x = resolucao_real[0] / resolucao_esperada[0] if resolucao_esperada[0] > 0 else 1.0
                        scale_y = resolucao_real[1] / resolucao_esperada[1] if resolucao_esperada[1] > 0 else 1.0
                        
                        print(f"⚠️  Incompatibilidade detectada! Aplicando correção automática:")
                        print(f"   Fator de escala: {scale_x:.3f} x {scale_y:.3f}")
                        
                        # Ajustar calibração para a imagem atual
                        centro_corrigido = (centro_json[0] * scale_x, centro_json[1] * scale_y)
                        raio_pupila_corrigido = raio_pupila_json * min(scale_x, scale_y)
                        raio_iris_corrigido = raio_iris_json * min(scale_x, scale_y)
                        
                        print(f"   Centro original: ({centro_json[0]:.1f}, {centro_json[1]:.1f})")
                        print(f"   Centro corrigido: ({centro_corrigido[0]:.1f}, {centro_corrigido[1]:.1f})")
                        print(f"   Raio pupila: {raio_pupila_json:.1f} → {raio_pupila_corrigido:.1f}")
                        print(f"   Raio íris: {raio_iris_json:.1f} → {raio_iris_corrigido:.1f}")
                        
                        self.centro_iris = centro_corrigido
                        self.raio_pupila = raio_pupila_corrigido
                        self.raio_anel = raio_iris_corrigido
                    else:
                        print("✅ Dimensões compatíveis - usando calibração original")
                        self.centro_iris = tuple(centro_json)
                        self.raio_pupila = raio_pupila_json
                        self.raio_anel = raio_iris_json
                    
                    print(f"✅ Calibração final aplicada:")
                    print(f"   Centro: {self.centro_iris}")
                    print(f"   Raio pupila: {self.raio_pupila}")
                    print(f"   Raio íris: {self.raio_anel}")
                else:
                    # Fallback se não houver calibração inicial
                    img_rect = self.imagem_pixmap.rect()
                    w, h = img_rect.width(), img_rect.height()
                    if w == 0 or h == 0:
                        w, h = 800, 600
                    
                    # ✅ CORREÇÃO: Valores fallback mais apropriados para íris
                    # A íris tipicamente ocupa 60-80% da menor dimensão da imagem
                    self.centro_iris = (w / 2, h / 2)
                    self.raio_anel = min(w, h) * 0.36  # Cerca de 72% da menor dimensão
                    self.raio_pupila = self.raio_anel * 0.20  # Pupila é cerca de 20% da íris
                    
                    print(f"⚠️  Usando valores fallback melhorados para calibração:")
                    print(f"   Imagem: {w}x{h}")
                    print(f"   Centro: {self.centro_iris}")
                    print(f"   Raio íris: {self.raio_anel:.1f}")
                    print(f"   Raio pupila: {self.raio_pupila:.1f}")
                
                # Definir valores de referência para o overlay manager
                if hasattr(self, 'overlay_manager'):
                    self.overlay_manager.centro_original = self.centro_iris
                    self.overlay_manager.raio_x_original = self.raio_anel
                    self.overlay_manager.raio_y_original = self.raio_anel
                    self.overlay_manager.centro_iris = self.centro_iris
                    self.overlay_manager.raio_anel = self.raio_anel
                    self.overlay_manager.raio_pupila = self.raio_pupila
                    # ✅ CORREÇÃO: Garantir referência ao IrisCanvas no overlay manager
                    self.overlay_manager.iris_canvas = self
                
                # ✅ Carregar zonas sem qualquer conversão (coordenadas polares em formato original)
                if isinstance(data, dict):
                    zonas_raw = data.get('zonas_reflexas') or data.get('zonas') or []
                elif isinstance(data, list):
                    # Formato novo: JSON é uma lista de zonas diretamente
                    zonas_raw = data
                else:
                    zonas_raw = []
                
                # CORREÇÃO: Manter formato original do JSON (coordenadas polares)
                zonas = []
                for zona_raw in zonas_raw:
                    # Suporte a diferentes formatos de polígonos
                    lista_poligonos = []
                    
                    # Formato novo: 'partes' contém lista de polígonos
                    if 'partes' in zona_raw:
                        lista_poligonos.extend(zona_raw['partes'])
                    # Formato antigo: 'pontos' ou 'compound_polygons'
                    elif 'pontos' in zona_raw:
                        lista_poligonos.append(zona_raw['pontos'])
                    elif 'compound_polygons' in zona_raw:
                        lista_poligonos.extend(zona_raw['compound_polygons'])

                    print(f"🔍 Zona '{zona_raw.get('nome', 'Sem nome')}': {len(lista_poligonos)} polígonos")

                    # 🔥 CORREÇÃO: Criar UMA zona com TODAS as partes
                    if lista_poligonos:  # Só processar se há polígonos
                        nome_zona = zona_raw.get('nome', 'Zona sem nome')
                        
                        # 🔥 USAR sinais do JSON correto para cada olho
                        sinais_zona = sinais_data.get(nome_zona, {})
                        print(f"🔍 Zona '{nome_zona}': {len(sinais_zona)} sinais encontrados")
                        
                        zona_convertida = {
                            'nome': nome_zona,
                            'descricao': zona_raw.get('descricao', ''),
                            'pontos': lista_poligonos[0] if lista_poligonos else [],  # Primeira parte para compatibilidade
                            'partes': lista_poligonos,  # 🔥 TODAS as partes da zona
                            'sinais': sinais_zona,  # 🔥 CORREÇÃO: Usar sinais do iris_esq sempre!
                            'estilo': zona_raw.get('estilo', {
                                'fill': '#CCCCCC',
                                'stroke': '#333333',
                                'stroke-width': 1.0,
                                'opacity': 0.4
                            })
                        }
                        zonas.append(zona_convertida)
                
                print(f"✅ {len(zonas)} zonas carregadas com coordenadas polares originais do JSON")
                
                # Armazenar zonas em ambos os locais para preservar durante calibração
                self.zonas_json = zonas  # Backup local para preservar durante calibração
                self.overlay_manager.zonas_json = zonas
                self.overlay_manager.draw_overlay()
                self.garantir_referencias_iris_canvas()
            
            except Exception as e:
                print(f"❌ Erro ao carregar zonas: {e}")
                traceback.print_exc()
        else:
            print(f"❌ Ficheiro não encontrado: {json_path}")
            
        # Certificar que o painel de info esteja pronto
        self.set_side_label(tipo)



    def set_image(self, caminho_imagem, tipo):
        self.caminho_imagem = caminho_imagem
        self.tipo = tipo
        self.set_side_label(tipo)
        if caminho_imagem and tipo:
            self.carregar_imagem_e_zonas(caminho_imagem, tipo)
        else:
            self.scene.clear()
            self.set_side_label(None)

    def closeEvent(self, event):
        """Limpa os arquivos temporários ao fechar a janela"""
        if hasattr(self, 'temp_files'):
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Erro ao remover arquivo temporário {temp_file}: {e}")
        super().closeEvent(event)
        
    def toggle_calibracao(self):
        """
        Alterna o estado de calibração (ON/OFF).
        
        ✅ IMPLEMENTAÇÃO OBRIGATÓRIA:
        A calibração serve APENAS para ajustar visualmente a sobreposição do mapa à realidade da íris.
        Não modifica as zonas do JSON nem gera novo JSON. Mantém topologia e geometria original.
        """
        self.calibrating = not self.calibrating
        
        print(f"🎯 Calibração {'ATIVADA' if self.calibrating else 'DESATIVADA'}")
        if self.calibrating:
            print("   → Modo: Ajuste visual da sobreposição (não modifica JSON)")
        else:
            print("   → Modo: Visualização das zonas originais do JSON")
        
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
        
        # Atualizar botão
        self.atualizar_botao_calibracao(self.calibrating)
        
        # Emitir sinal para outros componentes
        self.calibracao_mudou.emit(self.calibrating)
            
    def toggle_ajuste_fino(self):
        """Alterna o modo de ajuste fino individual (ON/OFF)"""
        self.fine_tuning_mode = not self.fine_tuning_mode
        
        # Atualiza o modo nos handles de calibração
        self.overlay_manager.set_individual_mode(self.fine_tuning_mode)
        
        if self.fine_tuning_mode:
            print("🔍 Modo ajuste fino ativado")
        else:
            print("🔍 Modo ajuste fino desativado")
        
        # Atualizar botão
        self.atualizar_botao_ajuste_fino(self.fine_tuning_mode)
        
        # Emitir sinal para outros componentes
        self.ajuste_fino_mudou.emit(self.fine_tuning_mode)

    def toggle_mapa_visibilidade(self):
        """
        ⭐ FUNCIONALIDADE MELHORADA: Oculta/mostra apenas os elementos visuais do mapa
        
        MANTÉM ATIVOS:
        - ✅ Tooltips das zonas (informações continuam disponíveis)
        - ✅ Área de detecção de hover para tooltips
        - ✅ Funcionalidade de interação
        
        OCULTA APENAS:
        - 🔹 Elementos visuais (brush/fill das zonas)
        - 🔹 Bordas e contornos
        - 🔹 Círculos de calibração
        - 🔹 Handles visuais
        """
        self.mapa_visivel = not self.mapa_visivel
        
        print(f"👁️ {'Mostrando' if self.mapa_visivel else 'Ocultando esqueleto visual do'} mapa da íris...")
        print(f"💡 Tooltips permanecem {'ativos' if not self.mapa_visivel else 'normais'}")
        
        # Controlar visibilidade INTELIGENTE das zonas reflexas
        zonas_processadas = 0
        elementos_calibracao_ocultados = 0
        
        if hasattr(self, 'scene') and self.scene:
            for item in self.scene.items():
                # ⭐ ZONAS REFLEXAS: Ocultar apenas elementos visuais, manter tooltips
                if hasattr(item, '__class__') and 'ZonaReflexa' in str(item.__class__):
                    if self.mapa_visivel:
                        # Mostrar: restaurar visualização normal
                        item.setVisible(True)
                        # Restaurar opacidade e brush originais
                        if hasattr(item, 'default_opacity'):
                            item.setOpacity(item.default_opacity)
                        # Restaurar brush se foi removido
                        self._restaurar_brush_zona(item)
                    else:
                        # Ocultar elementos visuais mas manter tooltips:
                        # Manter visível para preservar área de detecção de tooltips
                        item.setVisible(True)
                        # Remover apenas os elementos visuais (brush e pen)
                        self._remover_brush_zona(item)
                    
                    zonas_processadas += 1
                
                # Handles de calibração: ocultar completamente (não precisam de tooltip)
                elif hasattr(item, 'handle_type'):
                    item.setVisible(self.mapa_visivel)
                    elementos_calibracao_ocultados += 1
                
                # Círculos de calibração: ocultar completamente
                elif isinstance(item, QGraphicsEllipseItem):
                    pen = item.pen()
                    if pen and pen.style() == Qt.PenStyle.DashLine:
                        item.setVisible(self.mapa_visivel)
                        elementos_calibracao_ocultados += 1
                
                # Grupos de calibração: ocultar completamente
                elif hasattr(item, 'childItems') and item.childItems():
                    item.setVisible(self.mapa_visivel)
                    elementos_calibracao_ocultados += 1
        
        # Controlar overlays do manager
        if hasattr(self, 'overlay_manager') and self.overlay_manager:
            try:
                if hasattr(self.overlay_manager, 'calibration_overlay'):
                    overlay = self.overlay_manager.calibration_overlay
                    if overlay and hasattr(overlay, 'setVisible'):
                        overlay.setVisible(self.mapa_visivel)
                        elementos_calibracao_ocultados += 1
            except Exception as e:
                print(f"⚠️ Aviso ao controlar overlay de calibração: {e}")
        
        # Log de status detalhado
        print(f"✅ Estado: {'Mapa visível' if self.mapa_visivel else 'Apenas tooltips ativos'}")
        print(f"   - Zonas processadas: {zonas_processadas}")
        print(f"   - Elementos de calibração: {elementos_calibracao_ocultados}")
        
        if not self.mapa_visivel:
            print("💡 Dica: Passe o mouse sobre as áreas para ver tooltips das zonas!")
        
        # Forçar atualização da scene
        if hasattr(self, 'scene'):
            self.scene.update()
        
        # Atualizar botão
        self.atualizar_botao_mapa(self.mapa_visivel)
    
    def _remover_brush_zona(self, zona_item):
        """Remove o brush (preenchimento) da zona mas mantém a área de detecção para tooltips"""
        try:
            if hasattr(zona_item, '_brush_original'):
                return  # Já foi processado
            
            # Salvar brush e pen originais
            zona_item._brush_original = zona_item.brush()
            zona_item._pen_original = zona_item.pen()
            
            # Remover preenchimento (tornar transparente)
            zona_item.setBrush(QBrush(Qt.GlobalColor.transparent))
            
            # Manter borda completamente transparente mas presente (para área de detecção)
            # Usar pen transparente com largura 0 para manter a geometria
            zona_item.setPen(QPen(QColor(0, 0, 0, 0), 0))  # Transparente, largura 0
            
            print(f"🔹 Zona ocultada visualmente (tooltips ativos): {zona_item.toolTip()[:30]}...")
        except Exception as e:
            print(f"⚠️ Erro ao remover brush da zona: {e}")
    
    def _restaurar_brush_zona(self, zona_item):
        """Restaura o brush e pen originais da zona"""
        try:
            if hasattr(zona_item, '_brush_original'):
                zona_item.setBrush(zona_item._brush_original)
                delattr(zona_item, '_brush_original')
                
            if hasattr(zona_item, '_pen_original'):
                zona_item.setPen(zona_item._pen_original)
                delattr(zona_item, '_pen_original')
            else:
                # Fallback: restaurar pen padrão
                zona_item.setPen(QPen(QColor(255, 255, 255, 50), 1))
                
            print(f"🔹 Zona restaurada: {zona_item.toolTip()[:30]}...")
        except Exception as e:
            print(f"⚠️ Erro ao restaurar brush da zona: {e}")

    def zoom_in(self):
        """Ampliar a imagem"""
        self.view.scale(1.25, 1.25)
        print("🔍+ Imagem ampliada")
        
    def zoom_out(self):
        """Reduzir a imagem"""
        self.view.scale(0.8, 0.8)
        print("🔍- Imagem reduzida")
        
    def zoom_fit(self):
        """Ajustar imagem à janela"""
        if not self.scene.sceneRect().isEmpty():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            print("📐 Imagem ajustada à janela")

    def atualizar_botao_calibracao(self, ativo):
        """Atualiza o texto e estado do botão de calibração"""
        if hasattr(self, 'btn_calibracao'):
            self.btn_calibracao.setChecked(ativo)
            self.btn_calibracao.setText("✓ Calibrar" if ativo else "Calibrar")
            print(f"🎯 Botão calibração atualizado: {'ON' if ativo else 'OFF'}")

    def atualizar_botao_ajuste_fino(self, ativo):
        """Atualiza o texto e estado do botão de ajuste fino"""
        if hasattr(self, 'btn_ajuste_fino'):
            self.btn_ajuste_fino.setChecked(ativo)
            self.btn_ajuste_fino.setText("✓ Ajustar" if ativo else "Ajustar")
            print(f"🔍 Botão ajuste fino atualizado: {'ON' if ativo else 'OFF'}")

    def atualizar_botao_mapa(self, visivel):
        """Atualiza o texto do botão de visibilidade do mapa"""
        if hasattr(self, 'btn_ocultar_mapa'):
            self.btn_ocultar_mapa.setText(f"👁️ {'Ocultar' if visivel else 'Mostrar'} Mapa")
            print(f"👁️ Botão mapa atualizado: {'Ocultar' if visivel else 'Mostrar'}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # CORREÇÃO: Reajustar a visualização quando a janela for redimensionada
        if hasattr(self, 'view') and hasattr(self, 'scene'):
            if not self.scene.sceneRect().isEmpty():
                # Manter a imagem visível e bem dimensionada
                self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
                
                # Garantir zoom mínimo adequado
                view_size = self.view.viewport().size()
                scene_size = self.scene.sceneRect().size()
                
                if scene_size.width() > 0 and scene_size.height() > 0:
                    scale_x = view_size.width() / scene_size.width()
                    scale_y = view_size.height() / scene_size.height()
                    scale_factor = min(scale_x, scale_y)
                    
                    # Garantir tamanho mínimo adequado
                    if scale_factor < 0.3:
                        self.view.resetTransform()
                        self.view.scale(0.6, 0.6)  # 60% do viewport como mínimo

    def _preservar_ajuste_fino(self):
        """
        ⭐ NOVA FUNCIONALIDADE: Preserva o ajuste fino após aplicar calibração
        
        Captura os deslocamentos realizados no modo de ajuste fino e aplica-os como 
        offsets permanentes nas zonas antes de desligar o ajuste fino.
        Assim, mesmo após aplicar a calibração, as zonas permanecem na posição deformada.
        """
        if not self.overlay_manager or not hasattr(self.overlay_manager, 'zonas_json'):
            print("❌ Overlay manager ou zonas_json não disponível")
            return
            
        print("🔧 Capturando ajuste fino para preservação...")
        zonas_processadas = 0
        pontos_processados = 0
        
        try:
            # Para cada zona e cada ponto, calcula posição final (fina) e posição base (simétrica)
            for idx_zona, zona in enumerate(self.overlay_manager.zonas_json):
                # Suportar ambos os formatos de dados
                pontos = None
                if 'partes' in zona and zona['partes']:
                    pontos = zona['partes'][0]  # Formato novo do marcador.py
                elif 'pontos' in zona:
                    pontos = zona['pontos']     # Formato antigo
                
                if not pontos:
                    continue
                    
                for idx_ponto, p_original in enumerate(pontos):
                    try:
                        # Coordenada resultante com ajuste fino
                        x_fino, y_fino = self.overlay_manager.calculate_fine_tuning_transform(p_original)
                        
                        # Coordenada resultante *sem* ajuste fino (somente calibração simétrica)
                        x_base, y_base = self.overlay_manager.morph_ponto_livre(
                            p_original,
                            self.overlay_manager.centro_original,
                            self.overlay_manager.centro_iris,
                            self.overlay_manager.raio_x_original,
                            self.overlay_manager.raio_y_original,
                            self.overlay_manager.raio_anel,  # raio_x_atual (assumindo círculo)
                            self.overlay_manager.raio_anel,  # raio_y_atual
                            (0, 0)  # sem deslocamento
                        )
                        
                        # Calcula deslocamento e armazena
                        dx = x_fino - x_base
                        dy = y_fino - y_base
                        
                        # Só armazenar se houver deslocamento significativo (> 1 pixel)
                        if abs(dx) > 1.0 or abs(dy) > 1.0:
                            self.overlay_manager.deslocamentos_pontos[(idx_zona, idx_ponto)] = (dx, dy)
                            pontos_processados += 1
                            
                    except Exception as e:
                        print(f"⚠️ Erro ao processar ponto {idx_ponto} da zona {idx_zona}: {e}")
                        continue
                        
                zonas_processadas += 1
                
            print(f"✅ Ajuste fino preservado: {pontos_processados} pontos em {zonas_processadas} zonas")
            
        except Exception as e:
            print(f"❌ Erro ao preservar ajuste fino: {e}")
            traceback.print_exc()
        

    
# --- Zoom e Pan fluido ---

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
        # CORREÇÃO: Ativar zoom com roda do mouse para resolver problema de imagem pequena
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # Salvar a cena pos apontada pelo mouse
        old_pos = self.mapToScene(event.position().toPoint())
        
        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)
        
        # Obter nova posição
        new_pos = self.mapToScene(event.position().toPoint())
        
        # Mover cena para manter o ponto sob o mouse
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
        event.accept()

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

    def atualizar_referencias_zonas(self):
        """Atualiza todas as zonas reflexas com referência correta ao IrisCanvas.
        Deve ser chamado após qualquer operação que recria ou atualiza as zonas."""
        print("Atualizando referências ao IrisCanvas nas zonas reflexas...")
        
        # Verifica se o parent tem overlay_manager
        parent = self.parent()
        if parent and hasattr(parent, 'overlay_manager'):
            overlay_manager = getattr(parent, 'overlay_manager')
            if overlay_manager and hasattr(overlay_manager, 'zonas'):
                # Itera por todas as zonas e define a referência direta
                for zona in overlay_manager.zonas:
                    if hasattr(zona, 'set_iris_canvas'):
                        zona.set_iris_canvas(parent)
                
                print(f"✅ {len(overlay_manager.zonas)} zonas atualizadas com referência correta.")
                
                # CORREÇÃO: Chama o método garantir_referencias_iris_canvas do parent
                if hasattr(parent, 'garantir_referencias_iris_canvas'):
                    parent.garantir_referencias_iris_canvas()
                
                return
        
        print("❌ IrisCanvas ou Overlay manager não encontrado.")