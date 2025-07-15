def estilizar_botao_iris(btn, cor="#166380", hover="#218fb0", font_size=17, largura=170):
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {cor};
            color: #fff;
            border-radius: 10px;
            padding: 10px 0;
            font-size: {font_size}px;
            font-weight: 600;
            border: none;
            min-width: {largura}px;
            max-width: {largura}px;
            min-height: 48px;
            max-height: 48px;
        }}
        QPushButton:hover {{
            background-color: {hover};
            color: #fff;
        }}
        QPushButton:pressed {{
            background: #124058;
        }}
    """)
def estilizar_botao(botao, cor="#4CAF50", hover="#66bb6a"):
    botao.setStyleSheet(f"""
        QPushButton {{
            background-color: {cor};
            color: white;
            padding: 8px 20px;
            border-radius: 8px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
    """)

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

def estilizar_botao_pequeno(botao, cor="#1976d2", hover="#42a5f5"):
    botao.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cor}, stop:1 #e3eafc);
            color: white;
            border-radius: 7px;
            padding: 5px 16px;
            font-size: 14px;
            font-weight: 500;
            min-width: 120px;
            min-height: 36px;
            max-height: 40px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {hover};
            color: #222;
        }}
    """)