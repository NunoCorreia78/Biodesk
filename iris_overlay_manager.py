# Empty file after removing all content
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem, QGraphicsItemGroup, QGraphicsPolygonItem
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QPen, QPolygonF
from typing import Callable, Any
import json
import math

class SimpleCalibrationHandle(QGraphicsEllipseItem):
    """Handle simples e funcional para calibração com suporte a morphing individual"""
    
    def __init__(self, handle_type, angle, parent_manager):
        super().__init__(-8, -8, 16, 16)
        self.handle_type = handle_type  # 'center', 'pupil', 'iris'
        self.angle = angle
        self.parent_manager = parent_manager
        self.dragging = False
        self.individual_mode = False  # Novo: modo morphing individual
        self.original_angle = angle  # Armazena ângulo original
        
        # Configurações visuais
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(100)
        
        # Cores
        self.update_colors()
        
        self.setPen(QPen(Qt.GlobalColor.white, 2))
    
    def update_colors(self):
        """Atualiza cores baseado no modo e tipo"""
        # Verifica se é modo teste básico e handle central
        if (hasattr(self.parent_manager, '_calibracao_teste_basico') and 
            self.parent_manager._calibracao_teste_basico and 
            self.handle_type == 'center'):
            # Em modo teste básico, pega central fica cinza (desabilitada)
            self.setBrush(QBrush(QColor(150, 150, 150)))  # Cinza
            return
        
        if self.individual_mode:
            # Cores especiais para modo morphing individual
            if self.handle_type == 'center':
                self.setBrush(QBrush(QColor(0, 188, 212)))  # Cyan (mantém)
            elif self.handle_type == 'pupil':
                self.setBrush(QBrush(QColor(255, 152, 0)))  # Laranja para morphing
            else:  # iris
                self.setBrush(QBrush(QColor(156, 39, 176)))  # Roxo para morphing
        else:
            # Cores normais
            if self.handle_type == 'center':
                self.setBrush(QBrush(QColor(0, 188, 212)))  # Cyan
            elif self.handle_type == 'pupil':
                self.setBrush(QBrush(QColor(76, 175, 80)))  # Verde
            else:  # iris
                self.setBrush(QBrush(QColor(244, 67, 54)))  # Vermelho
    
    def set_individual_mode(self, enabled):
        """Ativa/desativa modo morphing individual"""
        self.individual_mode = enabled
        self.update_colors()
    
    def mousePressEvent(self, event):
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.setBrush(QBrush(QColor(255, 193, 7)))  # Amarelo quando arrastando
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            # Em modo teste básico: apenas handles de pupila e íris se movem
            # Pega central fica completamente desabilitada
            if (hasattr(self.parent_manager, '_calibracao_teste_basico') and 
                self.parent_manager._calibracao_teste_basico and 
                self.handle_type == 'center'):
                # Em modo teste básico, pega central NÃO se move (sem PAN)
                return
            
            # Handles de calibração podem se mover normalmente
            if hasattr(self, 'data') and self.data(0) == "HANDLE_CALIBRACAO":
                super().mouseMoveEvent(event)
                # Notifica o manager sobre a mudança
                self.parent_manager.handle_moved(self, self.individual_mode)
            else:
                # Item de fundo ou outro tipo - não move
                pass
    
    def mouseReleaseEvent(self, event):
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            # Restaura cor baseada no modo
            self.update_colors()
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        if not self.dragging:
            self.setBrush(QBrush(QColor(255, 193, 7)))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if not self.dragging:
            self.update_colors()
        super().hoverLeaveEvent(event)

class AdvancedCalibrationOverlay(QGraphicsItemGroup):
    """Overlay avançado de calibração da íris com 8 pegas por círculo"""
    
    def __init__(self, center_pos, pupil_radius=50, iris_radius=120):
        super().__init__()
        
        # Parâmetros iniciais
        self.center_pos = center_pos
        self.pupil_radius = pupil_radius
        self.iris_radius = iris_radius
        
        # Círculos de calibração
        self.pupil_circle = QGraphicsEllipseItem()
        self.iris_circle = QGraphicsEllipseItem()
        
        # Pegas de calibração
        self.center_handle = None
        self.pupil_handles = []
        self.iris_handles = []
        
        # Callback para atualização
        self.on_calibration_changed: Callable[[], None] | None = None
        
        # Configuração visual dos círculos
        self.setup_circles()
        self.setup_handles()
    
    def setup_circles(self):
        """Configura os círculos de pupila e íris"""
        # Círculo da pupila
        self.pupil_circle.setRect(
            -self.pupil_radius, -self.pupil_radius,
            self.pupil_radius * 2, self.pupil_radius * 2
        )
        self.pupil_circle.setPen(QPen(QColor(76, 175, 80), 2, Qt.PenStyle.DashLine))
        self.pupil_circle.setBrush(QBrush(Qt.GlobalColor.transparent))
        self.pupil_circle.setPos(self.center_pos)
        self.pupil_circle.setZValue(5)
        
        # Círculo da íris
        self.iris_circle.setRect(
            -self.iris_radius, -self.iris_radius,
            self.iris_radius * 2, self.iris_radius * 2
        )
        self.iris_circle.setPen(QPen(QColor(244, 67, 54), 2, Qt.PenStyle.DashLine))
        self.iris_circle.setBrush(QBrush(Qt.GlobalColor.transparent))
        self.iris_circle.setPos(self.center_pos)
        self.iris_circle.setZValue(5)
        
        # Adiciona ao grupo
        self.addToGroup(self.pupil_circle)
        self.addToGroup(self.iris_circle)
    
    def setup_handles(self):
        """Cria todas as pegas de calibração"""
        # Pega central
        self.center_handle = SimpleCalibrationHandle('center', 0, self)
        self.center_handle.setPos(self.center_pos)
        self.center_handle.setZValue(20)
        self.addToGroup(self.center_handle)
        
        # Ângulos para as 8 pegas (pontos cardeais + diagonais)
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        
        # Pegas da pupila
        for angle in angles:
            pos = self.calculate_handle_position(angle, self.pupil_radius)
            handle = SimpleCalibrationHandle('pupil', angle, self)
            handle.setPos(pos)
            handle.setZValue(15)
            self.pupil_handles.append(handle)
            self.addToGroup(handle)
        
        # Pegas da íris
        for angle in angles:
            pos = self.calculate_handle_position(angle, self.iris_radius)
            handle = SimpleCalibrationHandle('iris', angle, self)
            handle.setPos(pos)
            handle.setZValue(15)
            self.iris_handles.append(handle)
            self.addToGroup(handle)
    
    def calculate_handle_position(self, angle_deg, radius):
        """Calcula posição da pega baseada no ângulo e raio"""
        angle_rad = math.radians(angle_deg)
        x = self.center_pos.x() + radius * math.cos(angle_rad)
        y = self.center_pos.y() + radius * math.sin(angle_rad)
        return QPointF(x, y)
    
    def move_overlay(self, new_center_handle_pos):
        """Move todo o overlay para nova posição central (PAN)"""
        # A new_center_handle_pos é a posição do handle central
        # Calculamos a nova posição do centro baseada na posição do handle
        new_center = QPointF(new_center_handle_pos.x(), new_center_handle_pos.y())
        
        # Calcula o deslocamento
        delta_x = new_center.x() - self.center_pos.x()
        delta_y = new_center.y() - self.center_pos.y()
        
        # Atualiza centro
        self.center_pos = new_center
        
        # Move círculos para a nova posição
        self.pupil_circle.setPos(self.center_pos)
        self.iris_circle.setPos(self.center_pos)
        
        # Atualiza posições das pegas sem mudar os raios
        self.update_handle_positions()
        
        # Callback para atualização
        if self.on_calibration_changed:
            self.on_calibration_changed()
    
    def adjust_radius(self, circle_type, handle_pos, angle):
        """Ajusta raio baseado na posição da pega"""
        # Calcula novo raio baseado na distância ao centro
        distance = math.sqrt(
            (handle_pos.x() - self.center_pos.x()) ** 2 +
            (handle_pos.y() - self.center_pos.y()) ** 2
        )
        
        if circle_type == 'pupil':
            self.pupil_radius = max(10, distance)  # Raio mínimo
            self.update_pupil_circle()
            self.update_pupil_handles()
        elif circle_type == 'iris':
            self.iris_radius = max(20, distance)  # Raio mínimo
            self.update_iris_circle()
            self.update_iris_handles()
        
        # Callback para atualização
        if self.on_calibration_changed:
            self.on_calibration_changed()
    
    def update_pupil_circle(self):
        """Atualiza círculo da pupila"""
        self.pupil_circle.setRect(
            -self.pupil_radius, -self.pupil_radius,
            self.pupil_radius * 2, self.pupil_radius * 2
        )
    
    def update_iris_circle(self):
        """Atualiza círculo da íris"""
        self.iris_circle.setRect(
            -self.iris_radius, -self.iris_radius,
            self.iris_radius * 2, self.iris_radius * 2
        )
    
    def update_pupil_handles(self):
        """Atualiza posições das pegas da pupila"""
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for i, handle in enumerate(self.pupil_handles):
            pos = self.calculate_handle_position(angles[i], self.pupil_radius)
            handle.setPos(pos)
    
    def update_iris_handles(self):
        """Atualiza posições das pegas da íris"""
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for i, handle in enumerate(self.iris_handles):
            pos = self.calculate_handle_position(angles[i], self.iris_radius)
            handle.setPos(pos)
    
    def update_handle_positions(self):
        """Atualiza posições de todas as pegas"""
        self.update_pupil_handles()
        self.update_iris_handles()
    
    def reset_calibration(self, default_pupil=50, default_iris=120):
        """Reseta calibração para valores padrão"""
        self.pupil_radius = default_pupil
        self.iris_radius = default_iris
        
        self.update_pupil_circle()
        self.update_iris_circle()
        self.update_handle_positions()
        
        if self.on_calibration_changed:
            self.on_calibration_changed()
    
    def get_calibration_data(self):
        """Retorna dados de calibração atuais"""
        return {
            'center': (self.center_pos.x(), self.center_pos.y()),
            'pupil_radius': self.pupil_radius,
            'iris_radius': self.iris_radius
        }

class IrisOverlayManager:
    def redraw_spline_circles(self):
        """Desenha curvas Catmull-Rom (splines) apenas se individual_mode estiver ativo"""
        from PyQt6.QtGui import QPainterPath, QPen, QColor
        from PyQt6.QtWidgets import QGraphicsPathItem
        # Remove splines anteriores
        if hasattr(self, '_spline_items'):
            for item in self._spline_items:
                if item in self.scene.items():
                    self.scene.removeItem(item)
        self._spline_items = []

        if not getattr(self, 'individual_mode', False):
            return  # Só desenha splines no ajuste fino

        def catmull_rom_spline(points, samples=8):
            if len(points) < 3:
                return points
            pts = points[:]
            pts = [pts[-1]] + pts + [pts[0], pts[1]]
            result = []
            for i in range(1, len(pts)-2):
                p0, p1, p2, p3 = pts[i-1], pts[i], pts[i+1], pts[i+2]
                for t in [j/samples for j in range(samples)]:
                    t2 = t*t
                    t3 = t2*t
                    x = 0.5 * ((2*p1.x()) + (-p0.x()+p2.x())*t + (2*p0.x()-5*p1.x()+4*p2.x()-p3.x())*t2 + (-p0.x()+3*p1.x()-3*p2.x()+p3.x())*t3)
                    y = 0.5 * ((2*p1.y()) + (-p0.y()+p2.y())*t + (2*p0.y()-5*p1.y()+4*p2.y()-p3.y())*t2 + (-p0.y()+3*p1.y()-3*p2.y()+p3.y())*t3)
                    result.append((x, y))
            return result

        # Spline para pupila
        pupil_handles = [h for h in getattr(self, '_calib_handles', []) if h.handle_type == 'pupil']
        if len(pupil_handles) >= 3:
            pts = [h.pos() for h in pupil_handles]
            spline_pts = catmull_rom_spline(pts, samples=12)
            path = QPainterPath()
            if spline_pts:
                path.moveTo(spline_pts[0][0], spline_pts[0][1])
                for x, y in spline_pts[1:]:
                    path.lineTo(x, y)
                path.closeSubpath()
            item = QGraphicsPathItem(path)
            item.setPen(QPen(QColor(76, 175, 80), 3, Qt.PenStyle.SolidLine))
            item.setZValue(10)
            self.scene.addItem(item)
            self._spline_items.append(item)

        # Spline para íris
        iris_handles = [h for h in getattr(self, '_calib_handles', []) if h.handle_type == 'iris']
        if len(iris_handles) >= 3:
            pts = [h.pos() for h in iris_handles]
            spline_pts = catmull_rom_spline(pts, samples=12)
            path = QPainterPath()
            if spline_pts:
                path.moveTo(spline_pts[0][0], spline_pts[0][1])
                for x, y in spline_pts[1:]:
                    path.lineTo(x, y)
                path.closeSubpath()
            item = QGraphicsPathItem(path)
            item.setPen(QPen(QColor(244, 67, 54), 3, Qt.PenStyle.SolidLine))
            item.setZValue(10)
            self.scene.addItem(item)
            self._spline_items.append(item)
    def exemplo_callback_hover(self, zona_data):
        """Exemplo de callback para hover: mostra nome/descrição da zona no terminal (ou pode ser adaptado para label/tooltip)."""
        if zona_data:
            print(f"Zona: {zona_data.get('nome', '')} - {zona_data.get('descricao', '')}")
        else:
            print("(fora de zona)")
    def start_calibration(self, centro_iris=None, raio_pupila=None, raio_anel=None, teste_basico=False, teste_pan=False):
        """Inicia calibração limpa: só fundo estático, círculos tracejados, handles e (opcional) splines"""
        print("🎯 Iniciando calibração...")
        self._calibracao_teste_basico = teste_basico
        self._calibracao_teste_pan = teste_pan
        # Remove todos os overlays antigos (exceto fundo estático)
        for item in list(self.scene.items()):
            if isinstance(item, QGraphicsEllipseItem) and not (hasattr(item, 'data') and item.data(0) == "FUNDO_ESTATICO"):
                self.scene.removeItem(item)
            # Remove splines antigos
            if hasattr(item, 'zValue') and item.zValue() == 10:
                self.scene.removeItem(item)
        self.clear_calibration()
        # Usa valores existentes se não forem fornecidos
        if centro_iris is not None:
            self.centro_iris = centro_iris
        if raio_pupila is not None:
            self.raio_pupila = raio_pupila
        if raio_anel is not None:
            self.raio_anel = raio_anel
        if self.centro_iris is None:
            self.centro_iris = [400, 300]
        if self.raio_pupila is None:
            self.raio_pupila = 50
        if self.raio_anel is None:
            self.raio_anel = 120
        # Inicializa arrays de calibração
        self._calib_items = []  # Não usamos círculos tracejados - mantemos o array para compatibilidade
        self._calib_handles = []
        cx, cy = self.centro_iris
        # Handle central
        center_handle = SimpleCalibrationHandle('center', 0, self)
        center_handle.setPos(cx, cy)
        center_handle.setData(0, "HANDLE_CALIBRACAO")
        self.scene.addItem(center_handle)
        self._calib_handles.append(center_handle)
        # 8 Handles para pupila
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for angle in angles:
            angle_rad = math.radians(angle)
            px = cx + self.raio_pupila * math.cos(angle_rad)
            py = cy + self.raio_pupila * math.sin(angle_rad)
            handle = SimpleCalibrationHandle('pupil', angle, self)
            handle.setPos(px, py)
            handle.setData(0, "HANDLE_CALIBRACAO")
            self.scene.addItem(handle)
            self._calib_handles.append(handle)
        # 8 Handles para íris
        for angle in angles:
            angle_rad = math.radians(angle)
            ix = cx + self.raio_anel * math.cos(angle_rad)
            iy = cy + self.raio_anel * math.sin(angle_rad)
            handle = SimpleCalibrationHandle('iris', angle, self)
            handle.setPos(ix, iy)
            handle.setData(0, "HANDLE_CALIBRACAO")
            self.scene.addItem(handle)
            self._calib_handles.append(handle)
        # Atualiza cores dos handles
        for handle in self._calib_handles:
            handle.update_colors()
        print(f"✅ Calibração iniciada com {len(self._calib_handles)} handles")
        print(f"   Centro: ({cx}, {cy})")
        print(f"   Pupila: {self.raio_pupila}px")
        print(f"   Íris: {self.raio_anel}px")
        if self._calibracao_teste_basico:
            print("🔧 Modo teste básico: pega central DESABILITADA (sem PAN)")
        if self._calibracao_teste_pan:
            print("🔧 Modo teste PAN: Pega central HABILITADA para mover o overlay")
    
    def is_background_item(self, item):
        """Verifica se um item é elemento de fundo estático"""
        if hasattr(item, 'data'):
            data = item.data(0)
            if data in ["FUNDO_ESTATICO", "FUNDO_INDEPENDENTE"]:
                return True
        return False
    
    def protect_background_items(self):
        """Protege elementos de fundo contra qualquer modificação"""
        for item in self.scene.items():
            if self.is_background_item(item):
                # Força flags de proteção MÁXIMA
                item.setFlag(item.GraphicsItemFlag.ItemIsMovable, False)
                item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, False)
                item.setFlag(item.GraphicsItemFlag.ItemIgnoresTransformations, True)
                
                # Se é fundo independente, força posição original específica
                if hasattr(item, 'data') and item.data(0) == "FUNDO_INDEPENDENTE":
                    # Não altera posição de elementos independentes
                    pass
                elif hasattr(item, 'data') and item.data(0) == "FUNDO_ESTATICO":
                    # Para elementos estáticos, força posição 0,0
                    item.setPos(0, 0)
                    
                    # Força também o rect para posição original se for elipse
                    if isinstance(item, QGraphicsEllipseItem):
                        current_rect = item.rect()
                        # Força posição do rect também
                        if current_rect.x() != 250 or current_rect.y() != 150:  # Íris
                            if current_rect.width() == 300:  # É a íris
                                item.setRect(250, 150, 300, 300)
                        elif current_rect.x() != 350 or current_rect.y() != 250:  # Pupila
                            if current_rect.width() == 100:  # É a pupila
                                item.setRect(350, 250, 100, 100)

    def handle_moved(self, handle, individual_mode=False):
        """Chamado quando um handle é movido"""
        if not hasattr(self, '_calib_handles') or handle not in self._calib_handles:
            return

        # PROTEGE elementos de fundo ANTES de qualquer operação
        if self._calibracao_teste_pan:
            self.protect_background_items()

        # Verifica se é um handle de calibração válido
        if hasattr(handle, 'data') and handle.data(0) != "HANDLE_CALIBRACAO":
            return

        pos = handle.pos()


        # PAN do overlay
        if handle.handle_type == 'center':
            if self.centro_iris is None: self.centro_iris = [0, 0]
            old_cx, old_cy = self.centro_iris
            new_cx, new_cy = pos.x(), pos.y()
            self.centro_iris = [new_cx, new_cy]
            dx, dy = new_cx - old_cx, new_cy - old_cy
            for h in self._calib_handles:
                if h != handle:
                    h.setPos(h.pos().x() + dx, h.pos().y() + dy)
            self.update_calibration_circles()
            self.redraw_spline_circles()  # Atualiza splines em tempo real
            if self._calibracao_teste_pan:
                self.protect_background_items()

        # Morphing individual: só move o handle, não recalcula raio global
        elif handle.handle_type in ('pupil', 'iris') and self.individual_mode:
            self.redraw_spline_circles()
            self.update_calibration_circles()  # Atualiza círculos tracejados em tempo real

        # Modo normal: recalcula raio global
        elif handle.handle_type == 'pupil':
            if self.centro_iris is None: self.centro_iris = [400, 300]
            cx, cy = self.centro_iris
            distance = math.sqrt((pos.x() - cx)**2 + (pos.y() - cy)**2)
            self.raio_pupila = max(10, distance)
            angles = [h.original_angle for h in self._calib_handles if h.handle_type == 'pupil']
            pupil_handles = [h for h in self._calib_handles if h.handle_type == 'pupil']
            for i, h in enumerate(pupil_handles):
                angle_rad = math.radians(angles[i])
                px = cx + self.raio_pupila * math.cos(angle_rad)
                py = cy + self.raio_pupila * math.sin(angle_rad)
                h.setPos(px, py)
            self.update_calibration_circles()
            self.redraw_spline_circles()

        elif handle.handle_type == 'iris':
            if self.centro_iris is None: self.centro_iris = [400, 300]
            cx, cy = self.centro_iris
            distance = math.sqrt((pos.x() - cx)**2 + (pos.y() - cy)**2)
            self.raio_anel = max(20, distance)
            angles = [h.original_angle for h in self._calib_handles if h.handle_type == 'iris']
            iris_handles = [h for h in self._calib_handles if h.handle_type == 'iris']
            for i, h in enumerate(iris_handles):
                angle_rad = math.radians(angles[i])
                ix = cx + self.raio_anel * math.cos(angle_rad)
                iy = cy + self.raio_anel * math.sin(angle_rad)
                h.setPos(ix, iy)
            self.update_calibration_circles()
            self.redraw_spline_circles()

        # Recalcula zonas em tempo real se não for um teste
        if not self._calibracao_teste_basico and not self._calibracao_teste_pan:
            if hasattr(self, 'zonas_json') and self.zonas_json:
                self.recalculate_zones()

    def update_individual_pupil_shape(self):
        """
        Atualiza a forma da pupila quando em modo morphing individual.
        Apenas mantém as posições atuais dos handles de pupila e atualiza o círculo de calibração para se ajustar à nova forma.
        """
        # Atualiza o círculo da pupila para se ajustar ao novo formato (opcional: pode desenhar um polígono ou elipse ajustada)
        # Aqui, apenas atualiza o círculo para englobar os handles atuais
        pupil_handles = [h for h in self._calib_handles if h.handle_type == 'pupil']
        if not pupil_handles:
            return

        xs = [h.pos().x() for h in pupil_handles]
        ys = [h.pos().y() for h in pupil_handles]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        rx = (max_x - min_x) / 2
        ry = (max_y - min_y) / 2

        # Atualiza centro e raios
        self.centro_iris = [cx, cy]
        self.raio_pupila = max(rx, ry)

        # Atualiza círculo de calibração
        self.update_calibration_circles()

    def update_individual_iris_shape(self):
        """
        Atualiza a forma da íris quando em modo morphing individual.
        Permite que cada handle da íris seja movido independentemente.
        """
        iris_handles = [h for h in self._calib_handles if h.handle_type == 'iris']
        if not iris_handles:
            return

        xs = [h.pos().x() for h in iris_handles]
        ys = [h.pos().y() for h in iris_handles]
        
        # Calcula centro baseado nas posições dos handles
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        
        # Calcula raio médio das distâncias dos handles ao centro
        distances = [math.sqrt((x - cx)**2 + (y - cy)**2) for x, y in zip(xs, ys)]
        avg_radius = sum(distances) / len(distances)
        
        # Atualiza raio da íris
        self.raio_anel = max(20, avg_radius)
        
        # Atualiza círculo de calibração
        self.update_calibration_circles()

    def set_individual_mode(self, enabled):
        """Ativa/desativa modo morphing individual"""
        self.individual_mode = enabled
        
        # Atualiza cores de todos os handles
        for handle in getattr(self, '_calib_handles', []):
            handle.set_individual_mode(enabled)
        
        if enabled:
            print("🔧 Modo morphing individual ATIVADO")
        else:
            print("🔧 Modo morphing individual DESATIVADO")
            
    def update_calibration_circles(self):
        """Método mantido para compatibilidade - não mostramos mais círculos tracejados"""
        # Não fazemos nada - removemos os círculos tracejados como solicitado
        pass
    def _on_calibration_changed(self):
        """Callback chamado quando calibração muda em tempo real"""
        # Atualizada automaticamente pelo handle_moved
        pass
    
    def finish_calibration(self):
        """Finaliza calibração e recalcula zonas"""
        if hasattr(self, '_calib_handles') and self._calib_handles:
            data = {
                'center': self.centro_iris,
                'pupil_radius': self.raio_pupila,
                'iris_radius': self.raio_anel
            }
            
            print(f"🎯 Finalizando calibração:")
            print(f"   Centro: {data['center']}")
            print(f"   Pupila: {data['pupil_radius']}")
            print(f"   Íris: {data['iris_radius']}")
            
            # Remove overlay de calibração
            self.clear_calibration()
            
            # Verifica se não é teste antes de limpar flag
            eh_teste = getattr(self, '_calibracao_teste', False)
            
            # Limpa flag de teste
            self._calibracao_teste = False
            
            # Recalcula e redesenha zonas (apenas se não for teste)
            if not eh_teste and not getattr(self, '_calibracao_teste_pan', False):
                self.draw_overlay()
            
            return data
        return None
    
    def reset_calibration_to_default(self):
        """Reseta calibração para valores padrão"""
        if hasattr(self, '_calib_handles') and self._calib_handles:
            print("🔄 Resetando calibração para padrão...")
            
            # Preserva se é teste básico
            eh_teste_basico = getattr(self, '_calibracao_teste_basico', False)
            eh_teste_pan = getattr(self, '_calibracao_teste_pan', False)
            
            # Define valores padrão
            self.centro_iris = [400, 300]
            self.raio_pupila = 50
            self.raio_anel = 120
            
            # Reinicia calibração com valores padrão (preservando se é teste)
            self.start_calibration(teste_basico=eh_teste_basico, teste_pan=eh_teste_pan)
    
    def cancel_calibration(self):
        """Cancela calibração sem aplicar mudanças"""
        print("❌ Cancelando calibração...")
        self.clear_calibration()
        
        # Limpa flags de teste
        self._calibracao_teste_basico = False
        self._calibracao_teste_pan = False
    
    def clear_calibration(self):
        """Remove todos os handles e círculos de calibração."""
        # Remove handles de calibração
        for h in getattr(self, '_calib_handles', []):
            if h in self.scene.items():
                self.scene.removeItem(h)
        
        # Remove itens de calibração (círculos tracejados)
        for i in getattr(self, '_calib_items', []):
            if i in self.scene.items():
                self.scene.removeItem(i)
        
        # Limpa listas
        self._calib_handles = []
        self._calib_items = []
    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
        self.zonas = []
        self.zonas_json = []
        self.centro_iris = None
        self.raio_pupila = None
        self.raio_anel = None
        
        # Handles e estado de calibração
        self.handles = []
        self._calib_handles = []
        self._calib_items = []
        
        # Modo morphing individual
        self.individual_mode = False
        self.individual_pupil_positions = {}  # {handle: (x, y)}
        self.individual_iris_positions = {}   # {handle: (x, y)}
        
        # Armazenamento para os deslocamentos manuais dos handles
        self.deslocamentos_pontos = {}  # formato: {(zona_idx, ponto_idx): (dx, dy)}
        
        # Valores originais (usados como referência para morphing)
        self.centro_original = None
        self.raio_x_original = None
        self.raio_y_original = None
    
    def morph_ponto_livre(self, p_original, centro_original, centro_atual, 
                         raio_x_original, raio_y_original, 
                         raio_x_atual, raio_y_atual, 
                         deslocamento_handle=(0,0)):
        """
        Aplica morphing em um ponto, combinando escala proporcional com ajuste livre.
        
        Args:
            p_original: ponto original do JSON (x, y)
            centro_original: centro usado no JSON
            centro_atual: novo centro calibrado
            raio_x/y_original: raios originais
            raio_x/y_atual: raios calibrados (pode ser diferentes, para elipse)
            deslocamento_handle: (dx, dy) deslocamento feito pelo utilizador no handle deste ponto
        
        Returns:
            Tuplo (novo_x, novo_y) com as coordenadas atualizadas
        """
        # Normalização para percentagens relativas ao centro e raios originais
        frac_x = (p_original[0] - centro_original[0]) / raio_x_original if raio_x_original else 0
        frac_y = (p_original[1] - centro_original[1]) / raio_y_original if raio_y_original else 0

        # Morphing proporcional + livre (aplica o movimento do handle)
        novo_x = centro_atual[0] + frac_x * raio_x_atual + deslocamento_handle[0]
        novo_y = centro_atual[1] + frac_y * raio_y_atual + deslocamento_handle[1]
        return (novo_x, novo_y)

    def load_zones(self, json_path: str):
        """Carrega zonas a partir de um ficheiro JSON."""
        with open(json_path, 'r', encoding='utf-8') as f:
            self.zonas_json = json.load(f)
        self.draw_overlay()

    def load_zones_from_dict(self, zonas_dict: list[dict]):
        """Carrega zonas a partir de um dicionário já carregado."""
        self.zonas_json = zonas_dict
        
        # Armazena valores originais para referência no morphing
        # Usa valores padrão se não estiverem definidos
        if self.centro_original is None:
            viewport_width, viewport_height = 800, 600
            self.centro_original = (viewport_width / 2, viewport_height / 2)
            
        if self.raio_x_original is None:
            self.raio_x_original = min(viewport_width, viewport_height) * 0.45
            
        if self.raio_y_original is None:
            self.raio_y_original = self.raio_x_original  # Por padrão, usa raio circular
        
        # Reseta os deslocamentos
        self.deslocamentos_pontos = {}
        
        # Inicializa os deslocamentos para cada ponto como (0,0)
        for idx_zona, zona_data in enumerate(self.zonas_json):
            pontos = zona_data.get('pontos', [])
            for idx_ponto in range(len(pontos)):
                self.deslocamentos_pontos[(idx_zona, idx_ponto)] = (0, 0)
                
        self.draw_overlay()

    def draw_overlay(self):
        """Redesenha todos os polígonos/zonas usando self.zonas_json e aplicando morphing livre."""
        from PyQt6.QtWidgets import QGraphicsPolygonItem
        from PyQt6.QtGui import QPolygonF, QColor, QBrush, QPen
        from PyQt6.QtCore import QPointF
        self.clear()
        self._hover_callback = None
        self._item_to_zonadata = {}
        
        # Obter os valores atuais de centro e raio
        centro_atual = self.centro_iris
        raio_x_atual = self.raio_anel  # Assumindo raio circular por enquanto
        raio_y_atual = self.raio_anel
        
        # Se não temos valores originais, usar os atuais
        if self.centro_original is None:
            self.centro_original = centro_atual
        if self.raio_x_original is None:
            self.raio_x_original = raio_x_atual
        if self.raio_y_original is None:
            self.raio_y_original = raio_y_atual
        
        for idx_zona, zona_data in enumerate(self.zonas_json):
            if not isinstance(zona_data, dict):
                print(f"[IrisOverlayManager] Ignorando zona inválida: {zona_data}")
                continue
                
            # Aplicar morphing a cada ponto da zona
            pontos_originais = zona_data.get('pontos', [])
            pontos_morphed = []
            
            for idx_ponto, ponto_original in enumerate(pontos_originais):
                # Verifica se já existe um deslocamento para este ponto
                chave_ponto = (idx_zona, idx_ponto)
                if chave_ponto not in self.deslocamentos_pontos:
                    self.deslocamentos_pontos[chave_ponto] = (0, 0)
                
                # Aplica morphing (proporcional + livre)
                x, y = self.morph_ponto_livre(
                    ponto_original,
                    self.centro_original,
                    centro_atual,
                    self.raio_x_original,
                    self.raio_y_original,
                    raio_x_atual,
                    raio_y_atual,
                    self.deslocamentos_pontos[chave_ponto]
                )
                
                pontos_morphed.append(QPointF(x, y))
            
            # Importa a classe ZonaReflexa para criar os polígonos
            from iris_canvas import ZonaReflexa, pontos_para_polygon
            
            # Extrair parâmetros para criar ZonaReflexa
            cx, cy = centro_atual if centro_atual else (0, 0)
            raio_pupila = self.raio_pupila if hasattr(self, 'raio_pupila') else 50
            raio_anel = raio_x_atual if raio_x_atual else 120
            
            # Criar uma instância de ZonaReflexa com os dados da zona
            zona_data_completa = zona_data.copy()  # Copia para não modificar o original
            
            # Garantir que temos um dicionário de estilo
            if 'estilo' not in zona_data_completa:
                zona_data_completa['estilo'] = {}
                
            # Adicionar pontos morphed como pontos da zona
            zona_data_completa['pontos'] = [(p.x(), p.y()) for p in pontos_morphed]
            
            # Criar a zona reflexa que já terá os eventos de hover implementados
            item = ZonaReflexa(zona_data_completa, cx, cy, raio_pupila, raio_anel)
            
            # Armazena referência à zona original em dicionário auxiliar
            self._item_to_zonadata[item] = zona_data_completa
            
            # Eventos de hover serão conectados em enable_hover_tooltip
            self.scene.addItem(item)
            self.zonas.append(item)

    def enable_hover_tooltip(self, callback: Callable[[Any], None]):
        """Armazena callback para hover, mas não sobrescreve os métodos da ZonaReflexa.
        A classe ZonaReflexa já tem implementação de hover que chama atualizar_painel_zona diretamente."""
        # Apenas armazena o callback para usos futuros se necessário
        self._hover_callback = callback
        # Não sobrescreve os métodos de hover da ZonaReflexa

    def start_morph(self):
        """Cria handles para ajustar cada ponto da zona (fine-tuning) com suporte a morphing livre."""
        from PyQt6.QtWidgets import QGraphicsEllipseItem
        from PyQt6.QtGui import QBrush, QColor
        from PyQt6.QtCore import QRectF
        self.clear_handles()
        handle_size = 10
        self.handles = []
        self._handle_to_indices = {}  # dicionário auxiliar para evitar atributos dinâmicos
        
        # Obter os valores atuais de centro e raio
        centro_atual = self.centro_iris
        raio_x_atual = self.raio_anel  # Assumindo raio circular por enquanto
        raio_y_atual = self.raio_anel
        
        # Se não temos valores originais, usar os atuais
        if self.centro_original is None:
            self.centro_original = centro_atual
        if self.raio_x_original is None:
            self.raio_x_original = raio_x_atual
        if self.raio_y_original is None:
            self.raio_y_original = raio_y_atual
            
        for idx_zona, zona_data in enumerate(self.zonas_json):
            if not isinstance(zona_data, dict):
                print(f"[IrisOverlayManager] Ignorando zona inválida: {zona_data}")
                continue
            pontos = zona_data.get('pontos', [])
            for idx_ponto, ponto_original in enumerate(pontos):
                # Verifica se já existe um deslocamento para este ponto
                chave_ponto = (idx_zona, idx_ponto)
                if chave_ponto not in self.deslocamentos_pontos:
                    self.deslocamentos_pontos[chave_ponto] = (0, 0)
                
                # Calcula posição atual com morphing + deslocamento livre
                deslocamento = self.deslocamentos_pontos[chave_ponto]
                x, y = self.morph_ponto_livre(
                    ponto_original, 
                    self.centro_original,
                    centro_atual, 
                    self.raio_x_original, 
                    self.raio_y_original,
                    raio_x_atual, 
                    raio_y_atual, 
                    deslocamento
                )
                
                # Cria handle na posição calculada
                handle = QGraphicsEllipseItem(QRectF(x-handle_size/2, y-handle_size/2, handle_size, handle_size))
                handle.setBrush(QBrush(QColor('#ff9800')))
                handle.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
                handle.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
                handle.setZValue(20)
                
                # Armazena índices e posição original no dicionário auxiliar
                self._handle_to_indices[handle] = (idx_zona, idx_ponto)
                
                # Closure para atualizar ponto ao mover
                def make_item_change(handle, p_original, idx_z, idx_p):
                    pos_inicial = None
                    
                    def itemChange(change, value):
                        from PyQt6.QtWidgets import QGraphicsItem
                        nonlocal pos_inicial
                        
                        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
                            pos = value
                            nova_x = pos.x() + handle_size/2
                            nova_y = pos.y() + handle_size/2
                            
                            # Calcular a posição sem o deslocamento (apenas morphing proporcional)
                            pos_proportional = self.morph_ponto_livre(
                                p_original,
                                self.centro_original,
                                centro_atual,
                                self.raio_x_original,
                                self.raio_y_original,
                                raio_x_atual,
                                raio_y_atual,
                                (0, 0)  # sem deslocamento
                            )
                            
                            # O deslocamento é a diferença entre a posição atual e a proporcional
                            dx = nova_x - pos_proportional[0]
                            dy = nova_y - pos_proportional[1]
                            
                            # Atualizar o deslocamento deste ponto
                            self.deslocamentos_pontos[(idx_z, idx_p)] = (dx, dy)
                            
                            # Redimensionar todas as zonas com os novos deslocamentos
                            self.draw_overlay()
                            self.start_morph()  # redesenha handles
                        
                        return value
                    return itemChange
                
                handle.itemChange = make_item_change(handle, ponto_original, idx_zona, idx_ponto)
                self.scene.addItem(handle)
                self.handles.append(handle)

    def clear_handles(self):
        """Remove todos os handles de ajuste livre de pontos."""
        # Remove objetos gráficos dos handles
        for h in getattr(self, 'handles', []):
            self.scene.removeItem(h)
        
        # Limpa as listas e dicionários de handles
        self.handles = []
        if hasattr(self, '_handle_to_indices'):
            self._handle_to_indices = {}

    def apply_morph(self, novo_json: list[dict]):
        """Atualiza self.zonas_json e redesenha, preservando os deslocamentos dos pontos."""
        # Verifica se a estrutura do novo JSON é compatível com os deslocamentos existentes
        deslocamentos_compatíveis = {}
        
        for idx_zona, zona_data in enumerate(novo_json):
            if idx_zona < len(self.zonas_json): # Só mapeia se zona existir no JSON anterior
                pontos_novos = zona_data.get('pontos', [])
                pontos_antigos = self.zonas_json[idx_zona].get('pontos', [])
                
                # Mapeia pontos que existem em ambos os JSONs
                for idx_ponto in range(min(len(pontos_novos), len(pontos_antigos))):
                    chave_antiga = (idx_zona, idx_ponto)
                    if chave_antiga in self.deslocamentos_pontos:
                        deslocamentos_compatíveis[chave_antiga] = self.deslocamentos_pontos[chave_antiga]
        
        # Atualiza JSON e deslocamentos
        self.zonas_json = novo_json
        self.deslocamentos_pontos = deslocamentos_compatíveis
        
        # Para novos pontos, inicializa deslocamentos como (0,0)
        for idx_zona, zona_data in enumerate(self.zonas_json):
            pontos = zona_data.get('pontos', [])
            for idx_ponto in range(len(pontos)):
                chave_ponto = (idx_zona, idx_ponto)
                if chave_ponto not in self.deslocamentos_pontos:
                    self.deslocamentos_pontos[chave_ponto] = (0, 0)
        
        # Redesenha com os novos dados
        self.draw_overlay()

    def clear(self):
        """Limpa todos os itens do scene relacionados ao overlay."""
        for item in self.zonas:
            self.scene.removeItem(item)
        self.zonas = []
        # Remove handles e limpa dicionário auxiliar
        for h in getattr(self, 'handles', []):
            self.scene.removeItem(h)
        self.handles = []
        if hasattr(self, '_handle_to_indices'):
            self._handle_to_indices.clear()
    
    def reset_deslocamentos(self):
        """Reinicia todos os deslocamentos manuais, voltando ao morphing puramente proporcional."""
        # Reiniciar todos os deslocamentos para (0,0)
        for chave in self.deslocamentos_pontos:
            self.deslocamentos_pontos[chave] = (0, 0)
        
        # Redesenhar overlay e handles
        self.draw_overlay()
        if self.handles:  # Se os handles estão ativos, recriá-los
            self.start_morph()
    
    def recalculate_zones(self):
        """Recalcula todas as zonas poligonais baseadas na calibração atual"""
        if not self.centro_iris or not self.raio_pupila or not self.raio_anel:
            return
        
        # Recalcula zonas usando os novos parâmetros
        self.draw_overlay()
        
        # Não é necessário chamar enable_hover_tooltip pois a classe ZonaReflexa já
        # tem sua própria implementação de hover que atualiza o painel_zona
    
    def get_calibration_info(self):
        """Retorna informações atuais da calibração"""
        return {
            'center': self.centro_iris,
            'pupil_radius': self.raio_pupila,
            'iris_radius': self.raio_anel
        }
    
    def is_calibrating(self):
        """Verifica se está em modo de calibração"""
        return hasattr(self, '_calib_handles') and len(self._calib_handles) > 0
