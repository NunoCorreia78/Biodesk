"""
Estilos centralizados do Biodesk
Arquivo para unificar todos os estilos da aplicação
"""

def darken_color(hex_color, factor=0.2):
    """Escurece uma cor hex"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f"#{r:02x}{g:02x}{b:02x}"

BIODESK_BUTTON_STYLE = """
QPushButton {{
    background-color: #f8f9fa;
    color: #6c757d;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: bold;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {hover_color};
    color: white;
    border-color: {hover_color};
}}

QPushButton:pressed {{
    background-color: {pressed_color};
}}

QPushButton:disabled {{
    background-color: #e0e0e0;
    color: #6c757d;
    border-color: #e0e0e0;
}}
"""

def get_button_style(hover_color="#007bff", pressed_color=None):
    """Retorna estilo de botão com cores personalizadas"""
    if not pressed_color:
        pressed_color = darken_color(hover_color, 0.2)
    
    return BIODESK_BUTTON_STYLE.format(
        hover_color=hover_color,
        pressed_color=pressed_color
    )

BIODESK_DIALOG_STYLE = """
QDialog {
    background-color: #f8f9fa;
    border: 2px solid #dee2e6;
    border-radius: 12px;
}

QLabel {
    color: #2c3e50;
    font-size: 14px;
}

QPushButton {
    background-color: #f8f9fa;
    color: #6c757d;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: bold;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
}

QPushButton[role="accept"] {
    background-color: #28a745;
    color: white;
    border-color: #28a745;
}

QPushButton[role="accept"]:hover {
    background-color: #218838;
    border-color: #218838;
}

QPushButton[role="reject"] {
    background-color: #dc3545;
    color: white;
    border-color: #dc3545;
}

QPushButton[role="reject"]:hover {
    background-color: #c82333;
    border-color: #c82333;
}

QLineEdit, QTextEdit, QComboBox {
    border: 2px solid #e9ecef;
    border-radius: 6px;
    padding: 8px;
    font-size: 14px;
    background-color: white;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #007bff;
}
"""

def aplicar_estilo_biodesk(dialog):
    """Aplica o estilo padrão do Biodesk a um diálogo"""
    dialog.setStyleSheet(BIODESK_DIALOG_STYLE)
    
    # Centralizar o diálogo se tiver parent
    if dialog.parent():
        try:
            parent_rect = dialog.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - dialog.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog.height()) // 2
            dialog.move(x, y)
        except:
            pass  # Ignorar se houver erro na centralização

GLOBAL_HOVER_STYLE = """
QPushButton {
    background-color: #f8f9fa;
    color: #495057;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
    margin: 2px;
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

QPushButton:disabled {
    background-color: #e9ecef;
    color: #6c757d;
    border-color: #dee2e6;
}
"""

def aplicar_hover_global():
    """Aplica hover global em toda a aplicação com estilo consistente"""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        # Aplicar estilo limpo e simples
        app.setStyleSheet(GLOBAL_HOVER_STYLE)


# ========================================
# SISTEMA CENTRALIZADO DE BOTÕES BIODESK
# ========================================

class BiodeskButtonThemes:
    """Temas de cores para botões Biodesk"""
    PRIMARY = "#007bff"      # Azul principal
    SUCCESS = "#28a745"      # Verde sucesso  
    WARNING = "#ffc107"      # Amarelo aviso
    DANGER = "#dc3545"       # Vermelho perigo
    SECONDARY = "#6c757d"    # Cinza secundário
    INFO = "#17a2b8"         # Azul informação
    LIGHT = "#f8f9fa"        # Cinza claro
    DARK = "#343a40"         # Cinza escuro
    PURPLE = "#6f42c1"       # Roxo medicina quântica

def apply_biodesk_button_style(button, theme=BiodeskButtonThemes.SECONDARY, size="normal"):
    """
    Aplica estilo Biodesk centralizado a qualquer botão com CSS ultra-específico
    
    Args:
        button: QPushButton para estilizar
        theme: Cor do tema (usar BiodeskButtonThemes)
        size: "small", "normal", "large"
    """
    # Definir tamanhos
    sizes = {
        "tiny": {"padding": "4px 8px", "font_size": "10px", "min_height": "24px"},
        "small": {"padding": "6px 12px", "font_size": "11px", "min_height": "28px"},
        "normal": {"padding": "8px 16px", "font_size": "12px", "min_height": "32px"},
        "large": {"padding": "10px 20px", "font_size": "12px", "min_height": "32px"}  # Fonte menor, altura uniforme
    }
    
    size_config = sizes.get(size, sizes["normal"])
    pressed_color = darken_color(theme, 0.2)
    
    # CSS ULTRA-ESPECÍFICO para sobrepor qualquer outro estilo
    style = f"""
        QPushButton[objectName="{button.objectName()}"] {{
            background-color: #f8f9fa !important;
            color: #6c757d !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 6px !important;
            padding: {size_config['padding']} !important;
            font-size: {size_config['font_size']} !important;
            font-weight: bold !important;
            min-height: {size_config['min_height']} !important;
            max-height: {size_config['min_height']} !important;
            height: {size_config['min_height']} !important;
            margin: 2px !important;
        }}
        QPushButton[objectName="{button.objectName()}"]:hover {{
            background-color: {theme} !important;
            color: white !important;
            border-color: {theme} !important;
        }}
        QPushButton[objectName="{button.objectName()}"]:pressed {{
            background-color: {pressed_color} !important;
        }}
        QPushButton[objectName="{button.objectName()}"]:disabled {{
            background-color: #e0e0e0 !important;
            color: #6c757d !important;
            border-color: #e0e0e0 !important;
        }}
    """
    
    # Garantir que o botão tem um objectName único
    if not button.objectName():
        import uuid
        button.setObjectName(f"btn_{uuid.uuid4().hex[:8]}")
    
    button.setStyleSheet(style)

# Funções de conveniência para compatibilidade
def apply_primary_button_style(button, size="normal"):
    """Botão primário azul"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.PRIMARY, size)

def apply_success_button_style(button, size="normal"):
    """Botão verde de sucesso"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.SUCCESS, size)

def apply_danger_button_style(button, size="normal"):
    """Botão vermelho de perigo"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.DANGER, size)

def apply_secondary_button_style(button, size="normal"):
    """Botão cinza secundário"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.SECONDARY, size)

def apply_warning_button_style(button, size="normal"):
    """Botão amarelo de aviso"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.WARNING, size)

def apply_info_button_style(button, size="normal"):
    """Botão azul de informação"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.INFO, size)

def apply_purple_button_style(button, size="normal"):
    """Botão roxo para medicina quântica"""
    apply_biodesk_button_style(button, BiodeskButtonThemes.PURPLE, size)

def force_button_reset_and_style(button, theme=BiodeskButtonThemes.SECONDARY, size="normal"):
    """
    FUNÇÃO DE FORÇA BRUTA: Remove qualquer estilo existente e aplica o nosso
    Use esta função se os botões não estão respondendo ao estilo normal
    """
    # Reset total - limpar qualquer estilo existente
    button.setStyleSheet("")
    
    # Garantir objectName único
    if not button.objectName():
        import uuid
        button.setObjectName(f"btn_force_{uuid.uuid4().hex[:8]}")
    
    # Aplicar nosso estilo
    apply_biodesk_button_style(button, theme, size)
    
    # Forçar atualização visual
    button.update()
    button.repaint()
