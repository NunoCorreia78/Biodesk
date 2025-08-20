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
