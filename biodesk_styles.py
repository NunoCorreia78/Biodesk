"""
Sistema Centralizado de Estilos do Biodesk
Versão: 2.0
Data: Janeiro 2025

Sistema unificado para padronização de TODOS os botões e diálogos do Biodesk.
Elimina estilos inline e centraliza manutenção em um único local.
"""

from PyQt6.QtWidgets import QPushButton, QDialog, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import QSize
from enum import Enum
from typing import Optional, Dict, Any

class ButtonType(Enum):
    """Tipos de botões categorizados por função"""
    SAVE = "save"           # Guardar dados (hover verde)
    DELETE = "delete"       # Limpar/Remover (hover vermelho)  
    DRAFT = "draft"         # Rascunho (hover verde claro)
    NAVIGATION = "nav"      # Navegação (hover bege)
    UPDATE = "update"       # Atualizar (hover azul claro)
    TOOL = "tool"           # Ferramentas (hover cinza)
    DIALOG = "dialog"       # Botões de diálogo (hover cinza claro)
    DEFAULT = "default"     # Padrão sem categoria

class BiodeskStyles:
    """Sistema centralizado de estilos do Biodesk"""
    
    # 🎨 ESTILO BASE UNIFICADO - BONITO COMO O TODO
    BASE_BUTTON_STYLE = """
        QPushButton {{
            font-family: "Segoe UI", "Inter", Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
            color: #495057;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f8f9fa, stop:1 #e9ecef);
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 10px 20px;
            min-height: 18px;
            text-align: center;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #ffffff, stop:1 #f8f9fa);
            border: 1px solid #adb5bd;
            color: #212529;
        }}
        
        QPushButton:pressed {{
            background: #e9ecef;
            border: 1px solid #6c757d;
        }}
        
        QPushButton:disabled {{
            background: #f5f6f7;
            color: #a8aeb3;
            border-color: #eceeef;
        }}
        
        QPushButton:hover {{
            background: {hover_color};
        }}
    """
    
    # Cores de hover por categoria
    HOVER_COLORS = {
        ButtonType.SAVE: "#77dd77",        # Verde suave para salvar
        ButtonType.DELETE: "#ff6961",      # Vermelho suave para deletar
        ButtonType.DRAFT: "#a3ffac",       # Verde claro suave para rascunho
        ButtonType.NAVIGATION: "#fdf9c4",  # Amarelo suave para navegação
        ButtonType.UPDATE: "#d8f8e1",      # Verde muito claro para atualizar
        ButtonType.TOOL: "#cdced0",        # Cinza suave para ferramentas
        ButtonType.DIALOG: "#c5c6c8",      # Cinza médio suave para diálogos
        ButtonType.DEFAULT: "#e2e6ea"      # Cinza padrão
    }
    
    # Mapeamento de textos para tipos automaticamente
    TEXT_TO_TYPE = {
        # SAVE
        "guardar dados": ButtonType.SAVE,
        "assinar e guardar": ButtonType.SAVE,
        "guardar": ButtonType.SAVE,
        "adicionar nova iris": ButtonType.SAVE,
        "enviar email": ButtonType.SAVE,
        "salvar": ButtonType.SAVE,
        
        # DELETE
        "limpar": ButtonType.DELETE,
        "limpar formulário": ButtonType.DELETE,
        "remover": ButtonType.DELETE,
        "remover iris selecionada": ButtonType.DELETE,
        "deletar": ButtonType.DELETE,
        "excluir": ButtonType.DELETE,
        
        # DRAFT
        "guardar rascunho": ButtonType.DRAFT,
        "rascunho": ButtonType.DRAFT,
        
        # NAVIGATION
        "navegação rápida": ButtonType.NAVIGATION,
        "visualizar": ButtonType.NAVIGATION,
        "histórico": ButtonType.NAVIGATION,
        "follow up": ButtonType.NAVIGATION,
        "templates": ButtonType.NAVIGATION,
        "lista": ButtonType.NAVIGATION,
        
        # UPDATE
        "atualizar": ButtonType.UPDATE,
        "adicionar documentos": ButtonType.UPDATE,
        "refresh": ButtonType.UPDATE,
        
        # TOOL
        "negrito": ButtonType.TOOL,
        "itálico": ButtonType.TOOL,
        "sublinhado": ButtonType.TOOL,
        "inserir data": ButtonType.TOOL,
        "calibração": ButtonType.TOOL,
        "calibrar": ButtonType.TOOL,
        "ajuste": ButtonType.TOOL,
        "ajustar": ButtonType.TOOL,
        "zoom in": ButtonType.TOOL,
        "zoom out": ButtonType.TOOL,
        "ocultar mapa": ButtonType.TOOL,
        "ver mapa": ButtonType.TOOL,
    }
    
    @classmethod
    def create_button(cls, text: str, button_type: Optional[ButtonType] = None, 
                     icon: Optional[QIcon] = None, custom_hover: Optional[str] = None) -> QPushButton:
        """
        Cria um botão padronizado do Biodesk
        
        Args:
            text: Texto do botão
            button_type: Tipo do botão (se None, detecta automaticamente)
            icon: Ícone opcional
            custom_hover: Cor de hover customizada (sobrescreve o tipo)
        
        Returns:
            QPushButton configurado com estilo apropriado
        """
        button = QPushButton(text)
        
        # Detectar tipo automaticamente se não fornecido
        if button_type is None:
            text_lower = text.lower()
            for key_text, btype in cls.TEXT_TO_TYPE.items():
                if key_text in text_lower:
                    button_type = btype
                    break
            
            if button_type is None:
                button_type = ButtonType.DEFAULT
        
        # Aplicar ícone se fornecido
        if icon:
            button.setIcon(icon)
            button.setIconSize(QSize(18, 18))
        
        # Determinar cor de hover
        hover_color = custom_hover or cls.HOVER_COLORS.get(button_type, cls.HOVER_COLORS[ButtonType.DEFAULT])
        
        # Aplicar estilo com hover específico
        button.setStyleSheet(cls.BASE_BUTTON_STYLE.format(hover_color=hover_color))
        
        # Garantir altura adequada para o texto
        button.setMinimumHeight(40)
        button.setMaximumHeight(50)  # Evitar altura excessiva
        
        # Adicionar sombra sutil
        cls._apply_shadow(button)
        
        # Armazenar tipo para referência futura
        button.setProperty("button_type", button_type.value)
        
        return button
    
    @classmethod
    def _apply_shadow(cls, widget):
        """Aplica sombra sutil ao widget"""
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 10))  # 4% opacidade
            widget.setGraphicsEffect(shadow)
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível aplicar sombra: {e}")
    
    @classmethod
    def _clean_css_for_qt(cls, css_string: str) -> str:
        """
        Limpa CSS removendo caracteres problemáticos para o Qt
        """
        import re
        
        # Remover caracteres nulos e de substituição
        css_string = css_string.replace('\x00', '').replace('\ufffd', '')
        
        # Remover ou substituir caracteres não-ASCII problemáticos
        # Manter apenas caracteres ASCII básicos para CSS
        try:
            # Tentar encoding/decoding para limpar
            css_string = css_string.encode('ascii', errors='ignore').decode('ascii')
        except:
            pass
        
        # Remover múltiplas linhas vazias
        css_string = re.sub(r'\n\s*\n\s*\n', '\n\n', css_string)
        
        # Verificar se ainda há caracteres problemáticos
        try:
            css_string.encode('ascii')
        except UnicodeEncodeError:
            # Ainda há problemas, fazer limpeza mais agressiva
            css_string = ''.join(char for char in css_string if ord(char) < 128)
        
        return css_string.strip()

    @classmethod
    def apply_global_qss(cls):
        """Aplica QSS global com cores hover específicas por tipo de botão"""
        from PyQt6.QtWidgets import QApplication
        
        # QSS base para todos os botões
        base_qss = """
        /* ESTILO GLOBAL PARA TODOS OS BOTOES */
        QPushButton {
            font-family: "Segoe UI", "Inter", Roboto, sans-serif !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            color: #495057 !important;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f8f9fa, stop:1 #e9ecef) !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 6px !important;
            padding: 10px 20px !important;
            min-height: 18px !important;
            text-align: center !important;
        }
        
        QPushButton:pressed {
            background: #e9ecef !important;
            border: 1px solid #6c757d !important;
        }
        
        QPushButton:disabled {
            background: #f8f9fa !important;
            color: #adb5bd !important;
            border: 1px solid #e9ecef !important;
        }
        """
        
        # Gerar QSS específico para cada tipo de botão baseado no texto
        specific_qss = ""
        
        # Para botões SAVE (cinza suave para evitar bordas indesejadas)
        save_keywords = ["guardar", "salvar", "confirmar", "nova", "novo", "adicionar", "inserir", "criar", "save", "add", "gerar"]
        for keyword in save_keywords:
            specific_qss += f"""
        QPushButton[text*="{keyword}" i]:hover,
        QWidget QPushButton[text*="{keyword}" i]:hover,
        QFrame QPushButton[text*="{keyword}" i]:hover {{
            background: #C0C0C0 !important;
            border: 1px solid #999999 !important;
            color: #333333 !important;
        }}
        """
        
        # Para botões DELETE (vermelho suave) - ALTA PRIORIDADE
        delete_keywords = ["limpar", "remover", "deletar", "anular", "apagar", "excluir", "delete", "clear", "remove"]
        for keyword in delete_keywords:
            specific_qss += f"""
        QPushButton[text*="{keyword}" i]:hover,
        QWidget QPushButton[text*="{keyword}" i]:hover,
        QFrame QPushButton[text*="{keyword}" i]:hover {{
            background: #ff6961 !important;
            border: 1px solid #d9534f !important;
            color: #ffffff !important;
        }}
        """
        
        # Para botões NAVIGATION (amarelo suave) - ALTA PRIORIDADE
        nav_keywords = ["selecionar", "ver", "visualizar", "histórico", "lista", "preview", "navegar", "select", "view", "list", "follow-up", "template", "capturar"]
        for keyword in nav_keywords:
            specific_qss += f"""
        QPushButton[text*="{keyword}" i]:hover,
        QWidget QPushButton[text*="{keyword}" i]:hover,
        QFrame QPushButton[text*="{keyword}" i]:hover {{
            background: #fdf9c4 !important;
            border: 1px solid #f0ad4e !important;
            color: #333333 !important;
        }}
        """
        
        # Para botões TOOL (cinza suave) - ALTA PRIORIDADE
        tool_keywords = ["imprimir", "pdf", "email", "atualizar", "zoom", "calibração", "ajuste", "print", "refresh", "tool", "info", "terapia"]
        for keyword in tool_keywords:
            specific_qss += f"""
        QPushButton[text*="{keyword}" i]:hover,
        QWidget QPushButton[text*="{keyword}" i]:hover,
        QFrame QPushButton[text*="{keyword}" i]:hover {{
            background: #cdced0 !important;
            border: 1px solid #999999 !important;
            color: #333333 !important;
        }}
        """
        
        # Para botões DEFAULT/CANCEL (cinza claro) - ALTA PRIORIDADE
        default_keywords = ["cancelar", "fechar", "voltar", "sair", "cancel", "close", "back", "exit"]
        for keyword in default_keywords:
            specific_qss += f"""
        QPushButton[text*="{keyword}" i]:hover,
        QWidget QPushButton[text*="{keyword}" i]:hover,
        QFrame QPushButton[text*="{keyword}" i]:hover {{
            background: #e2e6ea !important;
            border: 1px solid #adb5bd !important;
            color: #495057 !important;
        }}
        """
        
        # Para botões que contêm emojis específicos - ALTA PRIORIDADE
        emoji_rules = """
        QPushButton[text*="💾"]:hover, QPushButton[text*="✅"]:hover, QPushButton[text*="➕"]:hover, QPushButton[text*="📷"]:hover, QPushButton[text*="📸"]:hover,
        QWidget QPushButton[text*="💾"]:hover, QWidget QPushButton[text*="✅"]:hover, QWidget QPushButton[text*="➕"]:hover, QWidget QPushButton[text*="📷"]:hover, QWidget QPushButton[text*="📸"]:hover,
        QFrame QPushButton[text*="💾"]:hover, QFrame QPushButton[text*="✅"]:hover, QFrame QPushButton[text*="➕"]:hover, QFrame QPushButton[text*="📷"]:hover, QFrame QPushButton[text*="📸"]:hover {
            background: #77dd77 !important;
            border: 1px solid #5cb85c !important;
            color: #ffffff !important;
        }
        
        QPushButton[text*="🗑️"]:hover, QPushButton[text*="❌"]:hover, QPushButton[text*="✖"]:hover, QPushButton[text*="🧹"]:hover,
        QWidget QPushButton[text*="🗑️"]:hover, QWidget QPushButton[text*="❌"]:hover, QWidget QPushButton[text*="✖"]:hover, QWidget QPushButton[text*="🧹"]:hover,
        QFrame QPushButton[text*="🗑️"]:hover, QFrame QPushButton[text*="❌"]:hover, QFrame QPushButton[text*="✖"]:hover, QFrame QPushButton[text*="🧹"]:hover {
            background: #ff6961 !important;
            border: 1px solid #d9534f !important;
            color: #ffffff !important;
        }
        
        QPushButton[text*="🔍"]:hover, QPushButton[text*="👁️"]:hover, QPushButton[text*="📋"]:hover, QPushButton[text*="📅"]:hover, QPushButton[text*="📄"]:hover,
        QWidget QPushButton[text*="🔍"]:hover, QWidget QPushButton[text*="👁️"]:hover, QWidget QPushButton[text*="📋"]:hover, QWidget QPushButton[text*="📅"]:hover, QWidget QPushButton[text*="📄"]:hover,
        QFrame QPushButton[text*="🔍"]:hover, QFrame QPushButton[text*="👁️"]:hover, QFrame QPushButton[text*="📋"]:hover, QFrame QPushButton[text*="📅"]:hover, QFrame QPushButton[text*="📄"]:hover {
            background: #fdf9c4 !important;
            border: 1px solid #f0ad4e !important;
            color: #333333 !important;
        }
        
        QPushButton[text*="🖨️"]:hover, QPushButton[text*="�"]:hover, QPushButton[text*="🔄"]:hover, QPushButton[text*="ℹ️"]:hover,
        QWidget QPushButton[text*="🖨️"]:hover, QWidget QPushButton[text*="📧"]:hover, QWidget QPushButton[text*="🔄"]:hover, QWidget QPushButton[text*="ℹ️"]:hover,
        QFrame QPushButton[text*="🖨️"]:hover, QFrame QPushButton[text*="📧"]:hover, QFrame QPushButton[text*="🔄"]:hover, QFrame QPushButton[text*="ℹ️"]:hover {
            background: #cdced0 !important;
            border: 1px solid #999999 !important;
            color: #333333 !important;
        }
        """
        
        # Hover genérico para botões sem categoria específica (BAIXA PRIORIDADE)
        generic_hover = """
        QPushButton:hover {
            background: #e2e6ea !important;
            border: 1px solid #adb5bd !important;
            color: #495057 !important;
        }
        
        /* ALTA PRIORIDADE: Seletores mais específicos para garantir que funcionam */
        QWidget QPushButton:hover {
            background: #e2e6ea !important;
            border: 1px solid #adb5bd !important;
            color: #495057 !important;
        }
        
        QFrame QPushButton:hover {
            background: #e2e6ea !important;
            border: 1px solid #adb5bd !important;
            color: #495057 !important;
        }
        """
        
        # Combinar todos os estilos
        full_qss = base_qss + generic_hover + specific_qss + emoji_rules
        
        # ⚠️ CORREÇÃO: Limpar CSS antes de aplicar
        full_qss = cls._clean_css_for_qt(full_qss)
        
        app = QApplication.instance()
        if app:
            try:
                # ⚠️ CORREÇÃO: Validar CSS antes de aplicar
                if not full_qss.strip():
                    print("⚠️ CSS vazio após limpeza, pulando aplicação")
                    return
                
                app.setStyleSheet(full_qss)
                print("🎨 CSS global aplicado com sucesso (caracteres problemáticos removidos)")
                # print("✅ QSS global INTELIGENTE aplicado - cores hover por categoria!")
                # print("✅ Suporte para: SAVE(verde), DELETE(vermelho), NAVIGATION(amarelo), TOOL(cinza)")
                # print("✅ Suporte para emojis: 💾✅➕(verde), 🗑️❌✖(vermelho), 🔍👁️📋(amarelo), 🖨️📄📧🔄(cinza)")
                # print("✅ QToolButton grandes do main window também com hover verde!")
            except Exception as e:
                print(f"⚠️ Erro ao aplicar stylesheet global: {e}")
                print(f"⚠️ Tamanho do CSS: {len(full_qss)} caracteres")
                # Tentar aplicar um CSS básico como fallback
                try:
                    app.setStyleSheet("/* Fallback CSS */")
                except:
                    pass

    @classmethod
    def apply_to_existing_button(cls, button: QPushButton, button_type: Optional[ButtonType] = None):
        """
        Aplica estilo a um botão existente
        
        Args:
            button: Botão existente
            button_type: Tipo do botão (se None, detecta automaticamente pelo texto)
        """
        # Detectar tipo pelo texto se não fornecido
        if button_type is None:
            text_lower = button.text().lower()
            for key_text, btype in cls.TEXT_TO_TYPE.items():
                if key_text in text_lower:
                    button_type = btype
                    break
            
            if button_type is None:
                button_type = ButtonType.DEFAULT
        
        # Aplicar estilo
        hover_color = cls.HOVER_COLORS.get(button_type, cls.HOVER_COLORS[ButtonType.DEFAULT])
        button.setStyleSheet(cls.BASE_BUTTON_STYLE.format(hover_color=hover_color))
        cls._apply_shadow(button)
        button.setProperty("button_type", button_type.value)

    @staticmethod
    def get_terapia_quantica_style():
        """Estilo específico para a interface de Terapia Quântica"""
        return """
        /* Terapia Quântica - Estilo Principal */
        
        QWidget {
            background-color: #f5f5f5;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 12px;
        }
        
        #headerFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #4a90e2, stop:1 #357abd);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        
        #titleLabel {
            color: white;
            font-size: 18px;
            font-weight: bold;
        }
        
        #subtitleLabel {
            color: #e6f3ff;
            font-size: 12px;
        }
        
        #tabWidget {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
        }
        
        #tabWidget QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #f8f9fa, stop:1 #e9ecef);
            border: 1px solid #dee2e6;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 10px 16px;
            margin-right: 2px;
            color: #495057;
            font-weight: 500;
            min-width: 100px;
        }
        
        #tabWidget QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #ffffff, stop:1 #f8f9fa);
            border-bottom: 2px solid #4a90e2;
            color: #212529;
        }
        
        #tabWidget QTabBar::tab:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #ffffff, stop:1 #f0f0f0);
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #f8f9fa, stop:1 #e9ecef);
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 8px 16px;
            color: #495057;
            font-weight: 500;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #ffffff, stop:1 #f8f9fa);
            border: 1px solid #adb5bd;
            color: #212529;
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #e9ecef, stop:1 #dee2e6);
        }
        
        QPushButton:disabled {
            background: #f8f9fa;
            color: #6c757d;
            border: 1px solid #e9ecef;
        }
        
        QTextEdit, QPlainTextEdit {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 12px;
            color: #495057;
        }
        
        QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #4a90e2;
        }
        
        QLineEdit {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
            color: #495057;
        }
        
        QLineEdit:focus {
            border: 2px solid #4a90e2;
        }
        
        QComboBox {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 12px;
            color: #495057;
            min-height: 20px;
        }
        
        QComboBox:hover {
            border: 1px solid #adb5bd;
        }
        
        QComboBox:focus {
            border: 2px solid #4a90e2;
        }
        
        QComboBox::drop-down {
            border: none;
            background: transparent;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #6c757d;
            margin-top: 2px;
        }
        
        QLabel {
            color: #495057;
            font-size: 12px;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            margin: 10px 0;
            padding-top: 15px;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #495057;
        }
        
        QScrollArea {
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background-color: white;
        }
        
        QScrollBar:vertical {
            background: #f8f9fa;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background: #6c757d;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #495057;
        }
        
        QProgressBar {
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background-color: #f8f9fa;
            text-align: center;
            color: #495057;
            font-weight: bold;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #4a90e2, stop:1 #357abd);
            border-radius: 3px;
        }
        
        #resultFrame {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 10px;
            margin: 5px;
        }
        
        #statusFrame {
            background-color: #f0f0f0;
            border-top: 1px solid #e0e0e0;
            padding: 8px;
        }
        
        #infoLabel {
            background-color: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 6px;
            padding: 10px;
            color: #0c5460;
        }
        """

# Estilo para diálogos profissionais e sóbrios
class DialogStyles:
    """Estilos para caixas de diálogo profissionais"""
    
    PROFESSIONAL_DIALOG = """
        QDialog {
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 12px;
        }
        
        QLabel {
            font-family: "Segoe UI", "Inter", Roboto, sans-serif;
            font-size: 13px;
            color: #24292e;
            line-height: 1.5;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            font-family: "Segoe UI", "Inter", Roboto, sans-serif;
            font-size: 13px;
            padding: 8px 12px;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            background-color: #fafbfc;
            color: #24292e;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
            border-color: #0366d6;
            background-color: #ffffff;
            outline: none;
        }
        
        /* Títulos de seção */
        QLabel#section_title {
            font-size: 16px;
            font-weight: 600;
            color: #24292e;
            padding: 8px 0px;
        }
        
        /* Subtítulos */
        QLabel#subtitle {
            font-size: 14px;
            color: #586069;
            padding: 4px 0px;
        }
        
        /* Groupbox profissional */
        QGroupBox {
            font-family: "Segoe UI", "Inter", Roboto, sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: #24292e;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0px 8px;
            background-color: #ffffff;
        }
        
        /* ScrollArea limpa */
        QScrollArea {
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            background-color: #fafbfc;
        }
        
        /* TabWidget profissional */
        QTabWidget::pane {
            border: 1px solid #e1e4e8;
            background-color: #ffffff;
            border-radius: 0px 8px 8px 8px;
        }
        
        QTabBar::tab {
            background-color: #fafbfc;
            color: #586069;
            padding: 8px 16px;
            margin-right: 4px;
            border: 1px solid #e1e4e8;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #24292e;
            font-weight: 600;
        }
        
        QTabBar::tab:hover {
            background-color: #f6f8fa;
        }
    """
    
    @classmethod
    def apply_to_dialog(cls, dialog: QDialog):
        """Aplica estilo profissional ao diálogo"""
        dialog.setStyleSheet(cls.PROFESSIONAL_DIALOG)
        # Adicionar sombra ao diálogo
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 30))
            dialog.setGraphicsEffect(shadow)
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível aplicar sombra ao diálogo: {e}")

    @staticmethod
    def get_terapia_quantica_style():
        """Estilo específico para a interface de Terapia Quântica"""
        return """
        /* Terapia Quântica - Estilo Principal */
        
        QWidget {
            background-color: #f5f5f5;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 12px;
        }
        
        #headerFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #4a90e2, stop:1 #357abd);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        
        #titleLabel {
            color: white;
            font-size: 18px;
            font-weight: bold;
        }
        
        #statusLabel {
            color: white;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        #mainTabs::pane {
            border: 1px solid #c0c0c0;
            border-radius: 8px;
            background-color: white;
        }
        
        #mainTabs::tab-bar {
            alignment: center;
        }
        
        QTabBar::tab {
            background: #e0e0e0;
            border: 1px solid #c0c0c0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background: #4a90e2;
            color: white;
        }
        
        QTabBar::tab:hover {
            background: #b0c4de;
        }
        
        #controlFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 10px;
            margin: 5px;
        }
        
        #sectionTitle {
            font-size: 14px;
            font-weight: bold;
            color: #4a90e2;
            margin-bottom: 10px;
        }
        
        QPushButton {
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #357abd;
        }
        
        QPushButton:pressed {
            background-color: #2a5a8a;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QTableWidget {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            gridline-color: #f0f0f0;
            background-color: white;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        QTableWidget::item:selected {
            background-color: #e3f2fd;
        }
        
        QHeaderView::section {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            padding: 8px;
            font-weight: bold;
        }
        
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            border: 1px solid #c0c0c0;
            border-radius: 4px;
            padding: 6px;
            background-color: white;
        }
        
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #4a90e2;
        }
        
        QProgressBar {
            border: 1px solid #c0c0c0;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4a90e2;
            border-radius: 3px;
        }
        
        #statusFrame {
            background-color: #f0f0f0;
            border-top: 1px solid #e0e0e0;
            padding: 8px;
        }
        
        #infoLabel {
            background-color: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 6px;
            padding: 10px;
            color: #0c5460;
        }
        """

# Utility functions para migração gradual
def convert_button_to_biodesk_style(button: QPushButton):
    """
    Converte um botão existente para o estilo Biodesk
    Função utilitária para migração gradual
    """
    BiodeskStyles.apply_to_existing_button(button)

def create_biodesk_button(text: str, callback=None, button_type: Optional[ButtonType] = None, icon=None):
    """
    Função helper para criação rápida de botões
    """
    button = BiodeskStyles.create_button(text, button_type, icon)
    if callback:
        button.clicked.connect(callback)
    return button

# Versão do sistema
__version__ = "2.0.0"
__author__ = "Biodesk Team"
__date__ = "Janeiro 2025"

# print(f"✅ BiodeskStyles v{__version__} carregado com sucesso!")
