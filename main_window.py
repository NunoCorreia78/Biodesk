from iris_canvas import IrisCanvas
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QToolButton, QGridLayout, QMenu, QVBoxLayout
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize
from ficha_paciente import FichaPaciente


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Biodesk')
        self.setGeometry(100, 100, 900, 700)
        self.init_ui()
        self.load_styles()
        self.showMaximized()

    def init_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: white;")
        layout = QGridLayout()

        # Substituir o título por imagem maior e nítida
        logo_path = os.path.join('assets', 'Biodesk.png')
        if os.path.exists(logo_path):
            logo = QLabel()
            pixmap = QPixmap(logo_path)
            logo.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo, 0, 0, 1, 3)
        else:
            title = QLabel('🩺 Biodesk - Ambiente Clínico')
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet('font-size: 28px; margin-bottom: 30px;')
            layout.addWidget(title, 0, 0, 1, 3)

        # Botão Pacientes com menu
        btn_pacientes = QToolButton()
        btn_pacientes.setText('Pacientes')
        icon_path = os.path.join('assets', 'user.png')
        if os.path.exists(icon_path):
            btn_pacientes.setIcon(QIcon(icon_path))
            btn_pacientes.setIconSize(QSize(72, 72))
        btn_pacientes.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_pacientes.setFixedSize(200, 200)
        btn_pacientes.setStyleSheet('font-size: 16px;')
        # Tooltip ao passar o mouse sobre o botão Pacientes
        btn_pacientes.setToolTip('Gerenciar pacientes: ver e cadastrar novos pacientes')
        menu = QMenu()
        menu.setStyleSheet("QMenu { padding: 8px; border-radius: 8px; background-color: #f8f8f8; font-size: 17px; margin-top: 16px; } QMenu::item { padding: 6px 14px; padding-left: 28px; height: 28px; } QMenu::icon { padding-left: 6px; vertical-align: middle; } QMenu::item:selected { background-color: #d0eaff; }")
        menu.clear()
        action_ver = menu.addAction(QIcon(os.path.join('assets', 'user.png')), 'Ver paciente')
        action_novo = menu.addAction(QIcon(os.path.join('assets', 'novo_paciente.jpg')), 'Novo paciente')
        if action_ver is not None:
            action_ver.setIconVisibleInMenu(True)
            action_ver.triggered.connect(self.abrir_lista_pacientes)
        if action_novo is not None:
            action_novo.setIconVisibleInMenu(True)
            action_novo.triggered.connect(self.abrir_ficha_nova)
        btn_pacientes.setMenu(menu)
        btn_pacientes.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        layout.addWidget(btn_pacientes, 1, 0, Qt.AlignmentFlag.AlignCenter)

        # Botão Íris
        btn_iris = QToolButton()
        btn_iris.setText('Íris')
        icon_path_iris = os.path.join('assets', 'eye.png')
        if os.path.exists(icon_path_iris):
            btn_iris.setIcon(QIcon(icon_path_iris))
            btn_iris.setIconSize(QSize(72, 72))
        btn_iris.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_iris.setFixedSize(200, 200)
        btn_iris.setStyleSheet('font-size: 16px;')
        # Tooltip ao passar o mouse sobre o botão Íris
        btn_iris.setToolTip('Abrir módulo de análise de íris')
        btn_iris.clicked.connect(self.open_iris)
        layout.addWidget(btn_iris, 1, 1, Qt.AlignmentFlag.AlignCenter)

        # Botão Terapia
        btn_terapia = QToolButton()
        btn_terapia.setText('Terapia')
        icon_path_terapia = os.path.join('assets', 'quantum.png')
        if os.path.exists(icon_path_terapia):
            btn_terapia.setIcon(QIcon(icon_path_terapia))
            btn_terapia.setIconSize(QSize(72, 72))
        btn_terapia.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn_terapia.setFixedSize(200, 200)
        btn_terapia.setStyleSheet('font-size: 16px;')
        # Tooltip ao passar o mouse sobre o botão Terapia
        btn_terapia.setToolTip('Abrir módulo de terapia quântica')
        btn_terapia.clicked.connect(self.open_terapia)
        layout.addWidget(btn_terapia, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
        
    def open_iris(self):
        # Inicializa o IrisCanvas sem dados de paciente
        self.iris_window = IrisCanvas()
        
        # Garante que o mouse tracking está ativado (adicional)
        if hasattr(self.iris_window, 'view'):
            self.iris_window.view.setMouseTracking(True)
            viewport = self.iris_window.view.viewport()
            if viewport is not None:
                viewport.setMouseTracking(True)
                
        # Maximiza a janela
        self.iris_window.showMaximized()
        
        # Chama o método de debug para testar o painel lateral após 1 segundo
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.iris_window.show_debug_panel())

    def load_styles(self):
        qss_path = os.path.join('assets', 'biodesk.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def abrir_lista_pacientes(self):
        FichaPaciente.mostrar_seletor(callback=self.abrir_ficha_existente)

    def abrir_ficha_nova(self):
        # Abre ficha de paciente vazia
        self.ficha_window = FichaPaciente()
        self.ficha_window.setWindowTitle('Novo Paciente')
        self.ficha_window.showMaximized()

    def abrir_ficha_existente(self, paciente_data):
        self.ficha_window = FichaPaciente(paciente_data)
        self.ficha_window.setWindowTitle(paciente_data.get('nome', 'Paciente'))
        self.ficha_window.showMaximized()



    def open_terapia(self):
        print('Abrir módulo de terapia quântica')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("✅ Drop-up com ícones alinhados e modernos.")
    sys.exit(app.exec())
