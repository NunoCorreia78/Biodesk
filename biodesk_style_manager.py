"""
🎨 BIODESK UNIVERSAL STYLE MANAGER v2.0
Sistema inteligente que automaticamente uniformiza TODOS os botões
CORRIGIDO: sem !important, sem polling, com event filter e cores por tema
"""

from PyQt6.QtWidgets import QApplication, QPushButton, QToolButton, QWidget
from PyQt6.QtCore import QObject, QEvent, Qt
import os


class BiodeskStyleManager(QObject):
    """Gestor universal corrigido que aplica estilos automaticamente"""
    
    # 🎨 PALETA BIODESK OFICIAL - CORES EXATAS
    THEMES = {
        'primary': '#007bff',    # Azul principal  
        'success': '#28a745',    # Verde sucesso
        'warning': '#ffc107',    # Amarelo aviso
        'danger': '#dc3545',     # Vermelho perigo
        'secondary': '#6c757d',  # Cinza neutro
        'info': '#17a2b8',       # Azul informação
        'purple': '#6f42c1',     # Roxo medicina
        'light': '#f8f9fa',      # Fundo padrão
        'dark': '#343a40',       # Texto escuro
        'border': '#e0e0e0',     # Borda padrão
        # 🟢 VERDES PROFISSIONAIS PARA MAIN WINDOW
        'green_forest': '#2d5430',    # Verde floresta (Pacientes)
        'green_teal': '#1f6156',      # Verde água (Íris)
        'green_olive': '#4a5d23'      # Verde oliva (Terapia)
    }
    
    # 🎯 MAPEAMENTO FORÇADO (sobrepõe heurística)
    FORCE_THEME = {
        'btn_guardar': 'success',
        'btn_remover': 'danger',
        'btn_adicionar': 'primary',
        'btn_cancelar': 'secondary',
        'btn_confirmar': 'success',
        'btn_info': 'info',
        'btn_terapia': 'warning'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._seen = set()
        
    @classmethod
    def initialize(cls):
        """Inicializa o gestor global de estilos - VERSÃO MÁXIMA AGRESSIVIDADE"""
        
        inst = cls()
        inst.apply_global_stylesheet()
        
        # � EVENT FILTER DESATIVADO - Para evitar delay visual
        # app = QApplication.instance()
        # if app:
        #     app.installEventFilter(inst)
        
        # � FORÇA BRUTA DESATIVADA - Para evitar coloração automática
        # try:
        #     inst._force_style_everything()
        # except Exception as e:
        #     pass
            
        # � TIMER AGRESSIVO DESATIVADO - User quer estilos estáveis
        # Removido para evitar re-aplicação constante de cores
        
        # Armazenar instância global para métodos estáticos
        cls._global_instance = inst
        return inst
    
    @classmethod
    def force_style_all_buttons(cls):
        """Método estático para forçar re-estilização de todos os botões"""
        if hasattr(cls, '_global_instance') and cls._global_instance:
            return cls._global_instance._force_style_everything()
        return 0
    
    @classmethod 
    def nuclear_option(cls):
        """Opção nuclear: re-aplicar estilos com máxima força"""
        if hasattr(cls, '_global_instance') and cls._global_instance:
            inst = cls._global_instance
            count = inst._force_style_everything()
            inst.apply_global_stylesheet()  # Re-aplicar CSS global também
            print(f"💥 NUCLEAR: {count} botões reprocessados")
            return count
        return 0
    
    def _aggressive_restyle(self):
        """Re-estilização agressiva a cada 3 segundos"""
        try:
            count = self._force_style_everything()
            if count > 0:
                pass  # Debug removido
        except Exception:
            pass  # Silencioso para não poluir logs
    
    def _force_style_everything(self):
        """💪 FORÇA aplicação em TODOS os botões da aplicação"""
        try:
            app = QApplication.instance()
            if not app:
                return 0
                
            styled_count = 0
            all_widgets = app.allWidgets()
            
            for widget in all_widgets:
                if isinstance(widget, (QPushButton, QToolButton)):
                    if self._force_style_single_widget(widget):
                        styled_count += 1
                        
            return styled_count
            
        except Exception as e:
            return 0
    
    def eventFilter(self, obj, event):
        """Event filter OTIMIZADO - Menos agressivo para evitar delay visual"""
        try:
            event_type = event.type()
            
            # 🎯 APENAS eventos essenciais para evitar delay visual
            # Removidos: Show, Paint, Resize (causavam delay)
            if event_type in (QEvent.Type.ChildAdded, QEvent.Type.Polish, QEvent.Type.Create):
                
                # Processar o objeto atual
                if isinstance(obj, (QPushButton, QToolButton)):
                    self._force_style_single_widget(obj)
                
                # Verificar filhos também
                if hasattr(obj, 'findChildren'):
                    try:
                        buttons = obj.findChildren((QPushButton, QToolButton))
                        for button in buttons:
                            self._force_style_single_widget(button)
                    except:
                        pass
                
                # Se ChildAdded, verificar o child também
                if event_type == QEvent.Type.ChildAdded:
                    child = event.child()
                    if isinstance(child, (QPushButton, QToolButton)):
                        self._force_style_single_widget(child)
                        
        except Exception as e:
            # Silencioso para não quebrar o app
            pass
        
        return False  # Nunca interceptar o evento
    
    def _force_style_single_widget(self, button):
        """💪 FORÇA aplicação de estilo NEUTRO com hover colorido"""
        try:
            # Verificar opt-out explícito
            if button.property("biodesk-autostyle") == "off":
                return False
                
            # Verificar se é botão principal da main window (estilos especiais)
            if self._is_main_window_button(button):
                return self._apply_main_window_style(button)
            
            # Detectar tema apenas para o hover (não para cor fixa)
            theme = self._detect_theme_enhanced(button)
            hover_color = self.THEMES.get(theme, self.THEMES['secondary'])
            pressed_color = self.darken_color(hover_color)
            
            # Definir propriedades
            button.setProperty("biodesk-theme", theme)
            button.setProperty("_biodeskStyled", True)
            
            # 🎯 ESTILO NEUTRO COM HOVER COLORIDO - EXATAMENTE O QUE O USER QUER
            neutral_style = f"""
            QPushButton {{
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
                font-size: 12px;
                padding: 8px 16px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                color: white;
                border-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                color: white;
                border-color: {pressed_color};
            }}
            QPushButton:disabled {{
                background-color: #f8f9fa;
                color: #adb5bd;
                border-color: #e0e0e0;
            }}
            """
            
            # Aplicar estilo neutro
            button.setStyleSheet(neutral_style)
            
            # FORÇAR refresh do estilo
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
            
            return True
            
        except Exception as e:
            return False
    
    def _is_main_window_button(self, button):
        """Detecta se é um dos 3 botões principais da main window"""
        if not isinstance(button, QToolButton):
            return False
            
        text = button.text().lower()
        return any(keyword in text for keyword in [
            'fichas de pacientes', 'íris', 'terapia quântica'
        ])
    
    def _apply_main_window_style(self, button):
        """Aplica estilos verdes profissionais específicos aos botões da main window"""
        try:
            text = button.text().lower()
            
            # Determinar cor verde específica
            if 'fichas de pacientes' in text or 'pacientes' in text:
                hover_color = self.THEMES['green_forest']  # Verde floresta
            elif 'íris' in text:
                hover_color = self.THEMES['green_teal']    # Verde água
            elif 'terapia quântica' in text or 'terapia' in text:
                hover_color = self.THEMES['green_olive']   # Verde oliva
            else:
                hover_color = self.THEMES['success']       # Verde padrão
            
            # Estilo específico para botões da main window
            main_style = f"""
            QToolButton {{
                background-color: rgba(248, 249, 250, 0.9) !important;
                color: #495057 !important;
                border: 2px solid #e9ecef !important;
                border-radius: 12px !important;
                font-family: 'Segoe UI', sans-serif !important;
                font-weight: 600 !important;
                font-size: 14px !important;
                padding: 12px !important;
            }}
            QToolButton:hover {{
                background-color: {hover_color} !important;
                color: white !important;
                border-color: {hover_color} !important;
            }}
            QToolButton:pressed {{
                background-color: {self.darken_color(hover_color)} !important;
                color: white !important;
                border-color: {self.darken_color(hover_color)} !important;
            }}
            """
            
            button.setStyleSheet(main_style)
            button.setProperty("_biodeskMainStyled", True)
            
            # FORÇAR refresh do estilo
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
            button.repaint()
            
            return True
            
        except Exception as e:
            return False
    
    def _detect_theme_enhanced(self, button):
        """Detecta tema com MÁXIMA precisão baseado no texto e objectName"""
        text = button.text().lower()
        object_name = button.objectName().lower()
        
        # 🎯 MAPEAMENTO FORÇADO (prioridade máxima)
        if object_name in self.FORCE_THEME:
            return self.FORCE_THEME[object_name]
        
        # 📊 HEURÍSTICA MELHORADA por texto
        # VERDE (success) - Ações positivas
        if any(word in text for word in [
            'guardar', 'salvar', 'confirmar', 'assinar', 'ok', 'enviar email',
            'adicionar documento', 'gerar prescrição', 'criar'
        ]):
            return "success"
        
        # VERMELHO (danger) - Ações destrutivas    
        elif any(word in text for word in [
            'remover', 'apagar', 'deletar', 'eliminar', 'limpar'
        ]) and 'filtro' not in text:  # Exceto "limpar filtros"
            return "danger"
        
        # AZUL (primary) - Ações principais
        elif any(word in text for word in [
            'adicionar', 'novo', 'criar', 'gerar', 'capturar', 'atualizar',
            'novo template'
        ]):
            return "primary"
        
        # AZUL CLARO (info) - Informações
        elif any(word in text for word in [
            'info', 'histórico', 'detalhes', 'lista', 'visualizar',
            'template', 'guardar rascunho'
        ]):
            return "info"
        
        # LARANJA (warning) - Ações especiais
        elif any(word in text for word in [
            'terapia', 'navegação', 'zoom', 'follow-up'
        ]):
            return "warning"
        
        # ROXO (purple) - Medicina especializada
        elif any(word in text for word in [
            'medicina', 'quântica', 'especial', 'prescrição'
        ]):
            return "purple"
        
        # CINZA (secondary) - Neutro/Cancelar
        else:
            return "secondary"
    
    def apply_global_stylesheet(self):
        """Aplica CSS global corrigido (sem !important, sem opacity)"""
        css = self._generate_corrected_css()
        
        app = QApplication.instance()
        if app:
            # Carregar QSS base se existir
            qss_path = os.path.join(os.path.dirname(__file__), 'assets', 'biodesk.qss')
            base_css = ""
            if os.path.exists(qss_path):
                try:
                    with open(qss_path, 'r', encoding='utf-8') as f:
                        base_css = f.read()
                except:
                    pass
            
            # Combinar CSS base + CSS corrigido
            final_css = base_css + "\n" + css
            app.setStyleSheet(final_css)
    
    def darken_color(self, hex_color, factor=0.22):
        """Calcula cor escurecida para :pressed"""
        hex_color = hex_color.lstrip('#')
        try:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#343a40"  # fallback
    
    def _generate_corrected_css(self):
        """CSS GLOBAL APENAS NEUTRO - SEM cores automáticas"""
        
        base_css = f"""
/* BIODESK BOTÕES NEUTROS COM HOVER COLORIDO */
QPushButton, QToolButton {{
    background-color: #f8f9fa;
    color: #6c757d;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 500;
    font-size: 12px;
    padding: 8px 16px;
    min-height: 32px;
}}

QPushButton:focus, QToolButton:focus {{
    border-color: {self.THEMES['primary']};
}}

QPushButton:disabled, QToolButton:disabled {{
    background-color: #f8f9fa;
    color: #adb5bd;
    border-color: #e0e0e0;
}}

/* HOVER COLORIDO POR TEXTO/FUNÇÃO */
QPushButton:hover, QToolButton:hover {{
    color: white;
}}

/* VERDE para Guardar, Confirmar, OK */
QPushButton:hover[text*="Guardar"], QPushButton:hover[text*="Salvar"], 
QPushButton:hover[text*="Confirmar"], QPushButton:hover[text*="OK"] {{
    background-color: {self.THEMES['success']};
    border-color: {self.THEMES['success']};
}}

/* VERMELHO para Remover, Apagar */
QPushButton:hover[text*="Remover"], QPushButton:hover[text*="Apagar"], 
QPushButton:hover[text*="Eliminar"] {{
    background-color: {self.THEMES['danger']};
    border-color: {self.THEMES['danger']};
}}

/* AZUL para Adicionar, Novo */
QPushButton:hover[text*="Adicionar"], QPushButton:hover[text*="Novo"], 
QPushButton:hover[text*="Criar"] {{
    background-color: {self.THEMES['primary']};
    border-color: {self.THEMES['primary']};
}}

/* AZUL CLARO para Gerar */
QPushButton:hover[text*="Gerar"] {{
    background-color: {self.THEMES['info']};
    border-color: {self.THEMES['info']};
}}

/* CINZA para resto */
QPushButton:hover, QToolButton:hover {{
    background-color: {self.THEMES['secondary']};
    border-color: {self.THEMES['secondary']};
}}

/* ESTILOS PARA TABS */
QTabWidget[cssClass="tab-container"] {{
    border: none;
}}

QTabWidget[cssClass="tab-container"]::pane {{
    border: 1px solid #dee2e6;
    border-radius: 8px;
    background-color: white;
}}

QTabWidget[cssClass="tab-container"] QTabBar::tab {{
    padding: 12px 20px;
    margin: 2px;
    border-radius: 6px 6px 0px 0px;
    background-color: #f8f9fa;
    color: #495057;
    font-weight: 600;
}}

QTabWidget[cssClass="tab-container"] QTabBar::tab:selected {{
    background-color: #007bff;
    color: white;
}}

QTabWidget[cssClass="tab-container"] QTabBar::tab:hover {{
    background-color: #e9ecef;
}}
"""
        
        return base_css
    
    def _is_main_screen_button(self, button):
        """Detecta botões da tela principal que devem manter estilo original"""
        text = button.text().lower()
        object_name = button.objectName().lower()
        
        # Botões principais a ignorar (APENAS os grandes da tela principal)
        main_buttons = [
            'fichas de pacientes', 'pacientes', 'iris', 'íris', 
            'terapia quântica', 'quantum', 'todo'
        ]
        
        # Verificar se é um dos botões grandes principais EXATOS
        if any(main_btn in text for main_btn in main_buttons):
            return True
            
        # REMOVIDO: Verificação de tamanho (estava capturando botões demais)
        # if button.size().width() > 150:
        #     return True
            
        return False
    
    def _auto_assign_properties(self, button):
        """Atribui propriedades baseado no texto/objectName"""
        text = button.text().lower()
        object_name = button.objectName().lower()
        
        # 🎯 MAPEAMENTO FORÇADO (prioridade)
        if object_name in self.FORCE_THEME:
            theme = self.FORCE_THEME[object_name]
        else:
            # Heurística por texto (melhorada)
            theme = "secondary"  # padrão
            
            if any(word in text for word in ['guardar', 'salvar', 'confirmar', 'assinar', 'ok']):
                theme = "success"
            elif any(word in text for word in ['remover', 'apagar', 'deletar', 'limpar']):
                # Cuidado: "Limpar filtros" vs "Limpar dados"
                if 'filtro' in text:
                    theme = "secondary"
                else:
                    theme = "danger"
            elif any(word in text for word in ['adicionar', 'novo', 'criar', 'gerar', 'capturar']):
                theme = "primary"
            elif any(word in text for word in ['info', 'histórico', 'detalhes', 'lista']):
                theme = "info"
            elif any(word in text for word in ['terapia', 'navegação', 'zoom']):
                theme = "warning"
            elif any(word in text for word in ['medicina', 'quântica', 'especial']):
                theme = "purple"
        
        # Detectar tamanho
        size = "normal"  # padrão (32px)
        
        if 'ler mais' in text:
            size = "tiny"
        elif len(text) < 6:  # Botões curtos
            size = "small"
        elif len(text) > 15:  # Botões longos
            size = "large"
        
        # Definir propriedades no botão
        button.setProperty("biodesk-theme", theme)
        button.setProperty("biodesk-size", size)
    
    def _detect_theme(self, button):
        """Detecta tema baseado no texto e objectName"""
        text = button.text().lower()
        object_name = button.objectName().lower()
        
        # 🎯 MAPEAMENTO FORÇADO (prioridade)
        if object_name in self.FORCE_THEME:
            return self.FORCE_THEME[object_name]
        
        # Heurística por texto
        if any(word in text for word in ['guardar', 'salvar', 'confirmar', 'assinar', 'ok']):
            return "success"
        elif any(word in text for word in ['remover', 'apagar', 'deletar']):
            return "danger"
        elif any(word in text for word in ['adicionar', 'novo', 'criar', 'gerar', 'capturar']):
            return "primary"
        elif any(word in text for word in ['info', 'histórico', 'detalhes', 'lista']):
            return "info"
        elif any(word in text for word in ['terapia', 'navegação', 'zoom']):
            return "warning"
        elif any(word in text for word in ['medicina', 'quântica', 'especial']):
            return "purple"
        else:
            return "secondary"
    
    def _detect_size(self, button):
        """Detecta tamanho baseado no contexto"""
        text = button.text().lower()
        
        if 'ler mais' in text:
            return "tiny"
        elif len(text) < 6:
            return "small"
        elif len(text) > 15:
            return "large"
        else:
            return "normal"

    @classmethod 
    def force_style_all_buttons(cls):
        """🚨 MÉTODO DE EMERGÊNCIA: Força estilo em TODOS os botões"""
        try:
            app = QApplication.instance()
            if not app:
                print("❌ Nenhuma aplicação QApplication encontrada")
                return 0
                
            styled_count = 0
            all_widgets = app.allWidgets()
            
            for widget in all_widgets:
                if isinstance(widget, (QPushButton, QToolButton)):
                    # Criar instância temporária para usar os métodos
                    temp_manager = cls()
                    
                    if temp_manager._force_style_single_widget(widget):
                        styled_count += 1
                        
            return styled_count
            
        except Exception as e:
            return 0
    
    @classmethod
    def nuclear_option(cls):
        """☢️ OPÇÃO NUCLEAR: Re-estiliza e força atualização de TUDO"""
        try:
            app = QApplication.instance()
            if not app:
                return 0
            
            # Primeiro, aplicar CSS global novamente
            temp_manager = cls()
            temp_manager.apply_global_stylesheet()
            
            # Depois forçar estilização individual
            styled_count = 0
            all_widgets = app.allWidgets()
            
            for widget in all_widgets:
                if isinstance(widget, (QPushButton, QToolButton)):
                    # Limpar propriedades antigas
                    widget.setProperty("_biodeskStyled", None)
                    
                    # Re-aplicar
                    if temp_manager._force_style_single_widget(widget):
                        styled_count += 1
                        
                    # FORÇA atualização visual
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
                    widget.repaint()
            
            return styled_count
            
        except Exception as e:
            return 0
        
        # Para QToolButton em toolbar, desativar auto-raise
        if isinstance(button, QToolButton):
            button.setAutoRaise(False)


# 🚀 FUNÇÕES DE CONVENIÊNCIA (OPCIONAIS)
def set_button_theme(button, theme, size="normal"):
    """Função manual para casos específicos"""
    button.setProperty("biodesk-theme", theme)
    button.setProperty("biodesk-size", size)
    button.style().unpolish(button)
    button.style().polish(button)
    button.update()

def set_opt_out(widget):
    """Marca widget para não ser estilizado automaticamente"""
    widget.setProperty("biodesk-autostyle", "off")
