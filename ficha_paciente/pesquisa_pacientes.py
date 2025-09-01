"""
🔍 MÓDULO DE PESQUISA DE PACIENTES
Sistema modular de busca e seleção de pacientes com interface otimizada.
Extraído do monólito para melhor manutenibilidade e performance.
"""

import unicodedata
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem, QMenu, QHeaderView)
from PyQt6.QtCore import Qt, QPoint
from db_manager import DBManager
from biodesk_ui_kit import BiodeskUIKit


class PesquisaPacientesWidget(QDialog):
    """Widget especializado para pesquisa e seleção de pacientes"""
    
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setWindowTitle('🔍 Procurar utente')
        self.setModal(True)
        self.resize(1000, 700)  # Tamanho adequado para a tabela
        self.db = DBManager()
        self.resultados = []
        
        self.init_ui()
        self.setup_connections()
        self.pesquisar()  # Carregar todos inicialmente

    def init_ui(self):
        """Inicializa interface moderna de pesquisa"""
        # Estilo geral do diálogo (moderno da iridologia)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
            }
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 8px;
            }
            QLineEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 16px;
                margin: 4px;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #6c757d;
                font-style: italic;
                font-weight: normal;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Título elegante
        title_label = QLabel("👥 Selecionar Paciente")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #2c3e50;
                padding: 0 0 16px 0;
                border-bottom: 2px solid #e3f2fd;
                margin-bottom: 16px;
            }
        """)
        layout.addWidget(title_label)
        
        # Filtros organizados em grid
        filtros_label = QLabel("🔍 Filtros de Pesquisa")
        layout.addWidget(filtros_label)
        
        filtros_grid = QHBoxLayout()
        filtros_grid.setSpacing(12)
        
        # Coluna 1
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("👤 Nome:"))
        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Digite parte do nome...")
        col1.addWidget(self.nome_edit)
        
        col1.addWidget(QLabel("📅 Data Nasc:"))
        self.nasc_edit = QLineEdit()
        self.nasc_edit.setPlaceholderText("DD/MM/AAAA")
        col1.addWidget(self.nasc_edit)
        
        # Coluna 2
        col2 = QVBoxLayout()
        col2.addWidget(QLabel("📞 Contacto:"))
        self.contacto_edit = QLineEdit()
        self.contacto_edit.setPlaceholderText("Telefone...")
        col2.addWidget(self.contacto_edit)
        
        col2.addWidget(QLabel("📧 Email:"))
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email...")
        col2.addWidget(self.email_edit)
        
        filtros_grid.addLayout(col1)
        filtros_grid.addLayout(col2)
        layout.addLayout(filtros_grid)
        
        # Resultados
        resultados_label = QLabel("📋 Resultados da Pesquisa")
        layout.addWidget(resultados_label)
        
        # Tabela com estilo moderno
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(['👤 Nome', '📅 Nasc.', '📞 Contacto', '📧 Email'])
        
        # Ocultar cabeçalho da tabela para visual mais limpo
        self.tabela.horizontalHeader().setVisible(False)
        
        # Configurar tabela
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nome expandível
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                gridline-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border: none;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        
        # Menu de contexto
        self.tabela.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabela.customContextMenuRequested.connect(self.menu_contexto)
        
        layout.addWidget(self.tabela)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        
        # Botão "Novo" destacado à esquerda
        self.btn_novo = QPushButton("➕ Novo Paciente")
        self.btn_novo.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 24px;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.btn_novo.clicked.connect(self.criar_novo_paciente)
        
        self.btn_abrir = BiodeskUIKit.create_neutral_button("✅ Abrir Paciente")
        self.btn_abrir.clicked.connect(self.abrir)
        self.btn_abrir.setEnabled(False)
        
        btn_cancelar = BiodeskUIKit.create_neutral_button("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        botoes_layout.addWidget(self.btn_novo)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addWidget(self.btn_abrir)
        
        layout.addLayout(botoes_layout)

    def setup_connections(self):
        """Configura conectores e sinais"""
        # Duplo clique na tabela
        self.tabela.doubleClicked.connect(self.abrir)
        
        # Seleção da tabela
        self.tabela.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Pesquisa ao escrever
        self.nome_edit.textChanged.connect(self.pesquisar)
        self.nasc_edit.textChanged.connect(self.pesquisar)
        self.contacto_edit.textChanged.connect(self.pesquisar)
        self.email_edit.textChanged.connect(self.pesquisar)

    def normalizar(self, s):
        """Normaliza string para pesquisa (remove acentos)"""
        if not s: 
            return ''
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()

    def pesquisar(self):
        """Realiza pesquisa com filtros aplicados"""
        try:
            todos = self.db.get_all_pacientes()
            
            # Aplicar filtros
            nome = self.normalizar(self.nome_edit.text())
            nasc = self.nasc_edit.text().strip()
            contacto = self.contacto_edit.text().replace(' ', '')
            email = self.normalizar(self.email_edit.text())
            
            resultados_filtrados = []
            for p in todos:
                # Filtro por nome
                if nome and nome not in self.normalizar(p.get('nome', '')):
                    continue
                
                # Filtro por data nascimento
                if nasc and nasc not in str(p.get('data_nascimento', '')):
                    continue
                
                # Filtro por contacto
                if contacto and contacto not in p.get('contacto', '').replace(' ', ''):
                    continue
                
                # Filtro por email
                if email and email not in self.normalizar(p.get('email', '')):
                    continue
                
                resultados_filtrados.append(p)
            
            self.resultados = resultados_filtrados
            self.atualizar_tabela()
            
        except Exception as e:
            print(f"❌ Erro na pesquisa: {e}")

    def atualizar_tabela(self):
        """Atualiza a tabela com os resultados"""
        self.tabela.setRowCount(len(self.resultados))
        
        for row, p in enumerate(self.resultados):
            self.tabela.setItem(row, 0, QTableWidgetItem(p.get('nome', '')))
            self.tabela.setItem(row, 1, QTableWidgetItem(str(p.get('data_nascimento', ''))))
            self.tabela.setItem(row, 2, QTableWidgetItem(p.get('contacto', '')))
            self.tabela.setItem(row, 3, QTableWidgetItem(p.get('email', '')))

    def criar_novo_paciente(self):
        """Cria um novo paciente e fecha o diálogo"""
        try:
            # Fechar o diálogo de pesquisa
            self.accept()
            
            # Importar e criar nova ficha
            from ficha_paciente import FichaPaciente
            
            # Obter referência da janela principal
            parent = self.parent()
            if parent and hasattr(parent, 'abrir_ficha_nova'):
                parent.abrir_ficha_nova()
            else:
                # Fallback: criar diretamente
                nova_ficha = FichaPaciente(parent=parent)
                nova_ficha.setWindowTitle('Novo Utente')
                if parent and hasattr(parent, 'safe_maximize_window'):
                    parent.safe_maximize_window(nova_ficha)
                nova_ficha.show()
                nova_ficha.raise_()
                nova_ficha.activateWindow()
                
        except Exception as e:
            print(f"❌ Erro ao criar novo paciente: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao criar novo paciente: {str(e)}")

    def on_selection_changed(self):
        """Ativa/desativa botão quando há seleção"""
        tem_selecao = len(self.tabela.selectedItems()) > 0
        self.btn_abrir.setEnabled(tem_selecao)

    def abrir(self):
        """Abre o paciente selecionado"""
        row = self.tabela.currentRow()
        if row >= 0 and row < len(self.resultados):
            paciente = self.resultados[row]
            self.accept()
            self.callback(paciente)

    def eliminar(self):
        """Elimina o paciente selecionado"""
        row = self.tabela.currentRow()
        if row >= 0 and row < len(self.resultados):
            paciente = self.resultados[row]
            from biodesk_dialogs import mostrar_confirmacao
            if mostrar_confirmacao(
                self, 
                "Eliminar utente",
                f"Tem a certeza que deseja eliminar o utente '{paciente.get('nome','')}'?"
            ):
                self.db.execute_query("DELETE FROM pacientes WHERE id = ?", (paciente['id'],))
                self.pesquisar()  # Recarregar após eliminação

    def menu_contexto(self, pos: QPoint):
        """Menu de contexto com clique direito"""
        item = self.tabela.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        if row < 0 or row >= len(self.resultados):
            return
        
        menu = QMenu(self)
        menu.addAction('✅ Abrir utente', self.abrir)
        menu.addAction('🗑️ Eliminar', self.eliminar)
        menu.exec(self.tabela.mapToGlobal(pos))


class PesquisaPacientesManager:
    """Classe estática para integração com o sistema principal"""
    
    @staticmethod
    def mostrar_seletor(callback, parent=None):
        """Interface estática para manter compatibilidade"""
        dialog = PesquisaPacientesWidget(callback, parent)
        dialog.exec()
