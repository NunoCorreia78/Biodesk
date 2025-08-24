"""
Biodesk - UI Kit Centralizado
============================

Sistema centralizado de componentes de interface para garantir
consistência visual e facilitar manutenção de estilos.
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class BiodeskUIKit:
    """Kit de componentes de interface padronizados do Biodesk"""
    
    # Paleta de cores principal
    COLORS = {
        'primary': '#007bff',
        'primary_light': '#3395ff',
        'primary_dark': '#0056b3',
        'secondary': '#6c757d',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'light': '#f8f9fa',
        'dark': '#343a40',
        'white': '#ffffff',
        'border': '#dee2e6',
        'border_light': '#e9ecef',
        'text': '#212529',
        'text_muted': '#6c757d',
        'background': '#ffffff',
        'background_light': '#f8f9fa'
    }
    
    # Estilos de fonte
    FONTS = {
        'family': "'Segoe UI', system-ui, -apple-system, sans-serif",
        'size_small': '12px',
        'size_normal': '14px',
        'size_large': '16px',
        'size_xl': '18px'
    }
    
    @classmethod
    def create_primary_button(cls, text: str, icon: QIcon = None) -> QPushButton:
        """Cria botão primário padronizado - NEUTRO com hover colorido"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
        
        # 🎯 ESTILO NEUTRO - BiodeskStyleManager global aplica hover
        # SEM setStyleSheet - deixar o CSS global do BiodeskStyleManager controlar
        
        return button
    
    @classmethod
    def create_secondary_button(cls, text: str, icon: QIcon = None) -> QPushButton:
        """Cria botão secundário padronizado - NEUTRO com hover colorido"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
            
        # 🎯 ESTILO NEUTRO - BiodeskStyleManager global aplica hover
        # SEM setStyleSheet - deixar o CSS global do BiodeskStyleManager controlar
        
        return button
    
    @classmethod
    def create_neutral_button(cls, text: str, icon: QIcon = None) -> QPushButton:
        """Cria botão neutro UNIVERSAL Biodesk - Estilo Padrão"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
            
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                font-weight: 500;
                min-height: 18px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['primary']};
                color: white;
                border-color: {cls.COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {cls.COLORS['primary_dark']};
                border-color: {cls.COLORS['primary_dark']};
                color: white;
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #6c757d;
                border-color: #dee2e6;
            }}
        """)
        
        return button
    
    @classmethod
    def apply_universal_button_style(cls, button: QPushButton):
        """Aplica o estilo UNIVERSAL Biodesk a qualquer botão existente"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                font-weight: 500;
                min-height: 18px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['primary']};
                color: white;
                border-color: {cls.COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {cls.COLORS['primary_dark']};
                border-color: {cls.COLORS['primary_dark']};
                color: white;
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #6c757d;
                border-color: #dee2e6;
            }}
        """)
        return button
    
    @classmethod
    def get_universal_button_stylesheet(cls):
        """Retorna o CSS universal para TODOS os botões Biodesk (QPushButton e QToolButton)"""
        base_style = f"""
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                font-weight: 500;
                min-height: 18px;
                text-align: center;
        """
        
        hover_style = f"""
                background-color: {cls.COLORS['primary']};
                color: white;
                border-color: {cls.COLORS['primary']};
        """
        
        pressed_style = f"""
                background-color: {cls.COLORS['primary_dark']};
                border-color: {cls.COLORS['primary_dark']};
                color: white;
        """
        
        disabled_style = """
                background-color: #e9ecef;
                color: #6c757d;
                border-color: #dee2e6;
        """
        
        return f"""
            /* QPushButton Styles */
            QPushButton {{{base_style}}}
            QPushButton:hover {{{hover_style}}}
            QPushButton:pressed {{{pressed_style}}}
            QPushButton:disabled {{{disabled_style}}}
            
            /* QToolButton Styles - Same as QPushButton */
            QToolButton {{{base_style}}}
            QToolButton:hover {{{hover_style}}}
            QToolButton:pressed {{{pressed_style}}}
            QToolButton:disabled {{{disabled_style}}}
        """
    
    @classmethod
    def create_success_button(cls, text: str, icon: QIcon = None) -> QPushButton:
        """Cria botão de sucesso padronizado - NEUTRO com hover verde"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
            
        # 🎯 ESTILO NEUTRO - BiodeskStyleManager global aplica hover verde
        # SEM setStyleSheet - deixar o CSS global do BiodeskStyleManager controlar
        
        return button
    
    @classmethod
    def create_danger_button(cls, text: str, icon: QIcon = None) -> QPushButton:
        """Cria botão de perigo padronizado - NEUTRO com hover vermelho"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
            
        # 🎯 ESTILO NEUTRO - BiodeskStyleManager global aplica hover vermelho
        # SEM setStyleSheet - deixar o CSS global do BiodeskStyleManager controlar
        
        return button
    
    @classmethod
    def create_neutral_button(cls, text: str, hover_color: str = None, icon: QIcon = None) -> QPushButton:
        """Cria botão neutro com hover colorido padronizado"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
        
        # Cor de hover padrão é a cor primária se não especificada
        hover_color = hover_color or cls.COLORS['primary']
            
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {cls.COLORS['light']};
                color: {cls.COLORS['text']};
                border: 2px solid {cls.COLORS['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                font-weight: 600;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                color: {cls.COLORS['white']};
                border-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: {cls.COLORS['border_light']};
                color: {cls.COLORS['text_muted']};
                border-color: {cls.COLORS['border_light']};
            }}
        """)
        
        return button
    
    @classmethod
    def create_input_field(cls, placeholder: str = "") -> QLineEdit:
        """Cria campo de input padronizado"""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        
        input_field.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {cls.COLORS['border_light']};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                background-color: {cls.COLORS['white']};
                color: {cls.COLORS['text']};
                selection-background-color: {cls.COLORS['primary']};
            }}
            QLineEdit:focus {{
                border-color: {cls.COLORS['primary']};
                background-color: {cls.COLORS['background_light']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {cls.COLORS['border']};
                background-color: {cls.COLORS['background_light']};
            }}
            QLineEdit::placeholder {{
                color: {cls.COLORS['text_muted']};
                font-style: italic;
            }}
        """)
        
        return input_field
    
    @classmethod
    def create_combo_box(cls, items: list = None) -> QComboBox:
        """Cria combo box padronizado"""
        combo = QComboBox()
        if items:
            combo.addItems(items)
        
        combo.setStyleSheet(f"""
            QComboBox {{
                border: 2px solid {cls.COLORS['border_light']};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                background-color: {cls.COLORS['white']};
                color: {cls.COLORS['text']};
                min-height: 20px;
            }}
            QComboBox:focus {{
                border-color: {cls.COLORS['primary']};
                background-color: {cls.COLORS['background_light']};
            }}
            QComboBox:hover {{
                border-color: {cls.COLORS['border']};
                background-color: {cls.COLORS['background_light']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {cls.COLORS['text_muted']};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {cls.COLORS['border']};
                background-color: {cls.COLORS['white']};
                selection-background-color: {cls.COLORS['primary']};
                selection-color: white;
                outline: none;
            }}
        """)
        
        return combo
    
    @classmethod
    def create_label(cls, text: str, style: str = 'normal') -> QLabel:
        """Cria label padronizado"""
        label = QLabel(text)
        
        styles = {
            'normal': f"""
                font-size: {cls.FONTS['size_normal']};
                font-family: {cls.FONTS['family']};
                color: {cls.COLORS['text']};
                padding: 4px 0px;
            """,
            'title': f"""
                font-size: {cls.FONTS['size_xl']};
                font-family: {cls.FONTS['family']};
                font-weight: bold;
                color: {cls.COLORS['text']};
                padding: 8px 0px;
            """,
            'subtitle': f"""
                font-size: {cls.FONTS['size_large']};
                font-family: {cls.FONTS['family']};
                font-weight: 600;
                color: {cls.COLORS['text']};
                padding: 6px 0px;
            """,
            'muted': f"""
                font-size: {cls.FONTS['size_small']};
                font-family: {cls.FONTS['family']};
                color: {cls.COLORS['text_muted']};
                padding: 4px 0px;
            """
        }
        
        label.setStyleSheet(f"QLabel {{ {styles.get(style, styles['normal'])} }}")
        return label
    
    @classmethod
    def create_card_widget(cls) -> QFrame:
        """Cria widget card padronizado"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {cls.COLORS['white']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 12px;
                padding: 20px;
                margin: 8px;
            }}
            QFrame:hover {{
                border-color: {cls.COLORS['border']};
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)
        
        return card


class ThemeManager:
    """Gestor de temas para aplicação"""
    
    current_theme = 'light'
    
    @classmethod
    def apply_dark_theme(cls):
        """Aplica tema escuro"""
        cls.current_theme = 'dark'
        # Atualizar cores do UIKit para tema escuro
        BiodeskUIKit.COLORS.update({
            'background': '#2b2b2b',
            'background_light': '#3c3c3c',
            'text': '#ffffff',
            'text_muted': '#cccccc',
            'border': '#555555',
            'border_light': '#666666'
        })
    
    @classmethod 
    def apply_light_theme(cls):
        """Aplica tema claro"""
        cls.current_theme = 'light'
        # Restaurar cores originais
        BiodeskUIKit.COLORS.update({
            'background': '#ffffff',
            'background_light': '#f8f9fa',
            'text': '#212529',
            'text_muted': '#6c757d',
            'border': '#dee2e6',
            'border_light': '#e9ecef'
        })
    
    @classmethod
    def toggle_theme(cls):
        """Alterna entre tema claro e escuro"""
        if cls.current_theme == 'light':
            cls.apply_dark_theme()
        else:
            cls.apply_light_theme()
