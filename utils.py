# ===== Estilo híbrido: outline -> sólido no hover (com opcional linha central) =====
def estilizar_botao_outline(
    btn,
    cor="#5a9ab8",
    altura=40,
    radius=10,
    font_size=14,
    font_weight=600,
    border_width=2,
    linha_central=False,
    usar_checked=False,
):
    """Aplica estilo outline que fica sólido no hover/checked.

    Args:
        btn (QPushButton): botão alvo
        cor (str): cor base (hex tipo #RRGGBB)
        altura (int): altura fixa do botão
        radius (int): raio da borda
        font_size (int): tamanho da fonte
        font_weight (int): peso da fonte (400-700)
        border_width (int): largura da borda
        linha_central (bool): se True, desenha uma linha horizontal subtil (consentimentos)
        usar_checked (bool): se True, aplica estado sólido também quando :checked
    """

    def _hex_to_rgb(h: str):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"

    def _lighten(h, pct):
        r, g, b = _hex_to_rgb(h)
        r = min(255, int(r + (255 - r) * pct / 100))
        g = min(255, int(g + (255 - g) * pct / 100))
        b = min(255, int(b + (255 - b) * pct / 100))
        return _rgb_to_hex(r, g, b)

    def _darken(h, pct):
        r, g, b = _hex_to_rgb(h)
        r = max(0, int(r - r * pct / 100))
        g = max(0, int(g - g * pct / 100))
        b = max(0, int(b - b * pct / 100))
        return _rgb_to_hex(r, g, b)

    def _ideal_text(h):
        r, g, b = _hex_to_rgb(h)
        # luminância relativa aproximada
        lumin = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "#000000" if lumin > 180 else "#ffffff"

    cor_hover = _lighten(cor, 10)
    cor_pressed = _darken(cor, 12)
    txt_hover = _ideal_text(cor)

    # Linha central opcional via gradiente estreito
    r, g, b = _hex_to_rgb(cor)
    linha_bg = (
        f"background: qlineargradient(x1:0, y1:0.5, x2:1, y2:0.5, "
        f"stop:0 rgba({r},{g},{b},0), stop:0.495 rgba({r},{g},{b},0), "
        f"stop:0.5 rgba({r},{g},{b},0.35), stop:0.505 rgba({r},{g},{b},0), "
        f"stop:1 rgba({r},{g},{b},0));"
    ) if linha_central else "background-color: transparent;"

    checked_rule = (
        f"""
        QPushButton:checked {{
            background-color: {cor};
            color: {txt_hover};
            border-color: {cor_pressed};
        }}
        QPushButton:checked:hover {{
            background-color: {cor_hover};
        }}
        """
    ) if usar_checked else ""

# =========================
# Botão outline -> sólido no hover/checked
# =========================

def _hex_to_rgb(hex_color):
    """Converte cor hex (#RRGGBB ou RRG) em tupla (r, g, b)."""
    if not isinstance(hex_color, str):
        return (33, 143, 176)
    c = hex_color.strip().lstrip('#')
    if len(c) == 3:
        c = ''.join([ch * 2 for ch in c])
    try:
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except Exception:
        return (33, 143, 176)

def _rgb_to_hex(r, g, b):
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02X}{g:02X}{b:02X}"

def _mix(a, b, t):
    return int(round(a + (b - a) * t))

def _lighten(hex_color, percent):
    r, g, b = _hex_to_rgb(hex_color)
    t = max(0.0, min(1.0, (percent or 0) / 100.0))
    return _rgb_to_hex(_mix(r, 255, t), _mix(g, 255, t), _mix(b, 255, t))

def _darken(hex_color, percent):
    r, g, b = _hex_to_rgb(hex_color)
    t = max(0.0, min(1.0, (percent or 0) / 100.0))
    return _rgb_to_hex(_mix(r, 0, t), _mix(g, 0, t), _mix(b, 0, t))

def _contrast_text_for(hex_color):
    """Retorna #FFFFFF ou #000000 consoante luminância (aproximação WCAG)."""
    r, g, b = _hex_to_rgb(hex_color)
    def srgb_ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    L = 0.2126 * srgb_ch(r) + 0.7152 * srgb_ch(g) + 0.0722 * srgb_ch(b)
    return "#000000" if L > 0.58 else "#FFFFFF"

def _rgba_str(hex_color, alpha_float):
    r, g, b = _hex_to_rgb(hex_color)
    a = int(max(0, min(1, alpha_float)) * 255)
    return f"rgba({r}, {g}, {b}, {a})"

def estilizar_botao_outline(
    btn,
    cor="#5a9ab8",
    largura=None,
    altura=36,
    radius=10,
    font_size=14,
    font_weight=600,
    linha_central=True,
    usar_checked=True,
):
    """Aplica o estilo 'outline' que fica sólido no hover/pressed/checked.

    - Normal: fundo transparente, borda + texto na cor.
    - Hover/Checked: fundo sólido e texto com contraste automático.
    - Linha central: detalhe subtil inspirado nos botões de consentimento.
    """

    cor_hex = cor
    cor_hover = cor_hex
    cor_press = _darken(cor_hex, 12)
    texto_hover = _contrast_text_for(cor_hover)
    texto_press = _contrast_text_for(cor_press)

    bg_line = ""
    if linha_central:
        line_col = _rgba_str(_lighten(cor_hex, 35), 0.35)
        trans = _rgba_str(cor_hex, 0.0)
        bg_line = (
            "background: qlineargradient(x1:0, y1:0.5, x2:1, y2:0.5, "
            f"stop:0 {trans}, stop:0.49 {trans}, stop:0.5 {line_col}, stop:0.51 {trans}, stop:1 {trans});"
        )

    width_rules = ""
    if largura:
        width_rules = f"min-width: {largura}px; max-width: {largura}px;"

    checked_rule = ""
    if usar_checked:
        checked_rule = (
            f"QPushButton:checked {{ background-color: {cor_hover}; color: {texto_hover}; border-color: {cor_hover}; }}"
        )

