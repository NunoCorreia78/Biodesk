# -*- coding: utf-8 -*-
"""
Módulo unificado de estilos para BIODESK
Centraliza funções de manipulação de cores, estilos de componentes e utilitários CSS.
"""

def lighten_color(hex_color, percent):
    """Clarifica uma cor hexadecimal em uma percentagem"""
    # Remove # se presente
    hex_color = hex_color.lstrip('#')
    # Converte para RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    # Clarifica
    rgb_lighter = tuple(min(255, int(c + (255 - c) * percent / 100)) for c in rgb)
    # Converte de volta para hex
    return f"#{rgb_lighter[0]:02x}{rgb_lighter[1]:02x}{rgb_lighter[2]:02x}"

def darken_color(hex_color, percent):
    """Escurece uma cor hexadecimal em uma percentagem"""
    # Remove # se presente
    hex_color = hex_color.lstrip('#')
    # Converte para RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    # Escurece
    rgb_darker = tuple(max(0, int(c - c * percent / 100)) for c in rgb)
    # Converte de volta para hex
    return f"#{rgb_darker[0]:02x}{rgb_darker[1]:02x}{rgb_darker[2]:02x}"


# ===== CORES PADRÃO BIODESK =====
CORES_BIODESK = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'biodesk_green': '#4CAF50',
    'biodesk_blue': '#218fb0',
    'biodesk_hover': '#42b8d8'
}


def get_color(nome_cor):
    """Retorna uma cor padrão do BIODESK"""
    return CORES_BIODESK.get(nome_cor, '#007bff')


def style_button(widget, cor='primary', largura=200, altura=36):
    """
    Aplica estilo padrão BIODESK a um botão
    
    Args:
        widget: Widget QPushButton
        cor (str): Nome da cor ou código hex
        largura (int): Largura do botão
        altura (int): Altura do botão
    """
    cor_base = get_color(cor) if cor in CORES_BIODESK else cor
    cor_hover = lighten_color(cor_base, 15)
    cor_pressed = darken_color(cor_base, 15)
    
    widget.setStyleSheet(f"""
        QPushButton {{
            background-color: {cor_base};
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-height: {altura}px;
            min-width: {largura}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {cor_hover};
        }}
        QPushButton:pressed {{
            background-color: {cor_pressed};
        }}
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #666666;
        }}
    """)


def style_combo(widget, largura=200):
    """
    Aplica estilo padrão BIODESK a um QComboBox
    
    Args:
        widget: Widget QComboBox
        largura (int): Largura do combo
    """
    widget.setStyleSheet(f"""
        QComboBox {{
            background-color: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            min-width: {largura}px;
            min-height: 36px;
        }}
        QComboBox:hover {{
            border-color: {get_color('primary')};
        }}
        QComboBox:focus {{
            border-color: {get_color('primary')};
            outline: none;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEwLjUgMS41TDYgNkwxLjUgMS41IiBzdHJva2U9IiM2Yzc1N2QiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
            width: 12px;
            height: 8px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: white;
            selection-background-color: {lighten_color(get_color('primary'), 80)};
        }}
    """)


def style_input(widget, largura=200):
    """
    Aplica estilo padrão BIODESK a um QLineEdit
    
    Args:
        widget: Widget QLineEdit
        largura (int): Largura do input
    """
    widget.setStyleSheet(f"""
        QLineEdit {{
            background-color: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            min-width: {largura}px;
            min-height: 36px;
        }}
        QLineEdit:hover {{
            border-color: {get_color('primary')};
        }}
        QLineEdit:focus {{
            border-color: {get_color('primary')};
            outline: none;
        }}
        QLineEdit:disabled {{
            background-color: #f5f5f5;
            color: #666666;
            border-color: #cccccc;
        }}
    """)


def style_tab_widget(widget):
    """
    Aplica estilo padrão BIODESK a um QTabWidget
    
    Args:
        widget: Widget QTabWidget
    """
    widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: white;
        }}
        QTabBar::tab {{
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 12px 20px;
            margin-right: 2px;
            font-size: 14px;
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            background-color: white;
            border-bottom: 2px solid {get_color('primary')};
            color: {get_color('primary')};
            font-weight: 600;
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {lighten_color(get_color('primary'), 90)};
        }}
    """)


def get_card_style(cor_borda='#e0e0e0', cor_fundo='white', border_radius=12):
    """
    Retorna CSS para um card padrão BIODESK
    
    Args:
        cor_borda (str): Cor da borda
        cor_fundo (str): Cor de fundo
        border_radius (int): Raio da borda
    
    Returns:
        str: CSS do card
    """
    return f"""
        background-color: {cor_fundo};
        border: 1px solid {cor_borda};
        border-radius: {border_radius}px;
        padding: 20px;
        margin: 10px;
    """


def get_header_style(cor_fundo='#4CAF50', cor_texto='white'):
    """
    Retorna CSS para um cabeçalho padrão BIODESK
    
    Args:
        cor_fundo (str): Cor de fundo
        cor_texto (str): Cor do texto
    
    Returns:
        str: CSS do cabeçalho
    """
    return f"""
        background: linear-gradient(135deg, {cor_fundo}, {lighten_color(cor_fundo, 20)});
        color: {cor_texto};
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    """


def apply_biodesk_theme(widget):
    """
    Aplica tema geral BIODESK a um widget
    
    Args:
        widget: Widget principal (QWidget, QDialog, QMainWindow)
    """
    widget.setStyleSheet(f"""
        QWidget {{
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            color: #333333;
        }}
        QLabel {{
            color: #333333;
        }}
        QGroupBox {{
            font-weight: bold;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: {get_color('primary')};
        }}
    """)


# ===== UTILITÁRIOS DE COR =====

def rgb_to_hex(r, g, b):
    """Converte RGB para hexadecimal"""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color):
    """Converte hexadecimal para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def contrast_text_for(hex_color):
    """Retorna cor de texto ideal (preto ou branco) para uma cor de fundo"""
    r, g, b = hex_to_rgb(hex_color)
    # Calcular luminância
    luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#000000' if luminancia > 0.5 else '#FFFFFF'


def mix_colors(cor1, cor2, peso=0.5):
    """Mistura duas cores hex com um peso específico"""
    rgb1 = hex_to_rgb(cor1)
    rgb2 = hex_to_rgb(cor2)
    
    r = int(rgb1[0] * (1 - peso) + rgb2[0] * peso)
    g = int(rgb1[1] * (1 - peso) + rgb2[1] * peso)
    b = int(rgb1[2] * (1 - peso) + rgb2[2] * peso)
    
    return rgb_to_hex(r, g, b)


# ===== FUNÇÕES MIGRADAS DO UTILS.PY =====

def estilizar_botao_iris(btn, cor="#218fb0", hover="#42b8d8", font_size=17, largura=170):
    """Estiliza botão com o novo design system - cor principal azul-petróleo"""
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {cor};
            color: #fff;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: {font_size}px;
            font-weight: 600;
            border: none;
            min-width: {largura}px;
            max-width: {largura}px;
            min-height: 52px;
            max-height: 52px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background: #197592;
        }}
    """)


def estilizar_botao_principal(btn, largura=200):
    """Botão principal - azul suave harmonioso"""
    btn.setProperty("class", "primary")
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #5a9ab8;
            color: white;
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-height: 36px;
            min-width: {largura}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: #6db4d1;
        }}
        QPushButton:pressed {{
            background-color: #4a8099;
        }}
    """)


def estilizar_botao_secundario(btn, largura=180):
    """Botão secundário - cinza suave"""
    btn.setProperty("class", "secondary")
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #7a8a99;
            color: white;
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-height: 36px;
            min-width: {largura}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: #8da0b2;
        }}
        QPushButton:pressed {{
            background-color: #6a7987;
        }}
    """)


def estilizar_botao_perigo(btn, largura=200):
    """Botão de perigo - vermelho elegante"""
    btn.setProperty("class", "danger")
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #e74c3c;
            color: white;
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-height: 36px;
            min-width: {largura}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: #f56c5c;
        }}
        QPushButton:pressed {{
            background-color: #d73c2a;
        }}
    """)


def estilizar_botao_sucesso(btn, largura=200):
    """Botão de sucesso - verde harmonioso"""
    btn.setProperty("class", "success")
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #27ae60;
            color: white;
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-height: 36px;
            min-width: {largura}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: #2ecc71;
        }}
        QPushButton:pressed {{
            background-color: #1e8f47;
        }}
    """)


def estilizar_botao_fusao(btn, cor="#5a9ab8", size_type="standard", radius=8, 
                         font_size=None, font_weight=600, linha_central=True, 
                         usar_checked=True, fix_width=True):
    """
    Aplica estilo de botão fusão com fundo claro e linha decorativa
    
    Args:
        btn: QPushButton
        cor (str): cor base em hex
        size_type (str): "standard" ou "compact"
        radius (int): raio das bordas
        font_size (int): tamanho da fonte
        font_weight (int): peso da fonte
        linha_central (bool): linha decorativa
        usar_checked (bool): estilo para :checked
        fix_width (bool): largura fixa
    """
    # Configurações baseadas no tipo
    if size_type == "compact":
        width, height = 32, 32
        default_font_size = 13
    else:
        width, height = 120, 36
        default_font_size = 14
    
    font_size = font_size or default_font_size
    
    # Cores derivadas
    cor_clara = lighten_color(cor, 90)  # Fundo claro
    cor_hover = lighten_color(cor, 20)  # Hover mais claro
    cor_pressed = darken_color(cor, 20)  # Pressed mais escuro
    texto_contraste = contrast_text_for(cor)
    
    # Linha decorativa
    linha_style = f"""
        QPushButton::before {{
            content: "";
            position: absolute;
            top: 50%;
            left: 10%;
            right: 10%;
            height: 1px;
            background: {cor};
            opacity: 0.3;
        }}
    """ if linha_central else ""
    
    # Regra checked
    checked_rule = f"""
        QPushButton:checked {{
            background-color: {cor};
            color: {texto_contraste};
            border-color: {cor};
        }}
    """ if usar_checked else ""
    
    # Aplicar estilo
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {cor_clara};
            color: {cor};
            border: 2px solid {cor};
            border-radius: {radius}px;
            padding: 8px 16px;
            font-size: {font_size}px;
            font-weight: {font_weight};
            {'min-width: %dpx; min-height: %dpx;' % (width, height) if fix_width else ''}
        }}
        QPushButton:hover {{
            background-color: {cor_hover};
            color: {texto_contraste};
            border-color: {cor_hover};
        }}
        QPushButton:pressed {{
            background-color: {cor_pressed};
            color: {texto_contraste};
            border-color: {cor_pressed};
        }}
        QPushButton:disabled {{
            background-color: transparent;
            color: #9aa3a7;
            border-color: #cfd9de;
        }}
        {checked_rule}
        {linha_style}
    """)
