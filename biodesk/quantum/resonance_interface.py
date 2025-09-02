"""
Interface de Análise de Ressonância - Estilo CoRe
================================================

Widget PyQt6 para análise de ressonância informacional
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTreeWidget, QTreeWidgetItem, QTableWidget,
                            QTableWidgetItem, QProgressBar, QComboBox, QSpinBox,
                            QGroupBox, QSplitter, QFrame, QTextEdit, QHeaderView,
                            QCheckBox, QLineEdit, QTabWidget, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush, QIcon, QPalette
import json
from datetime import datetime
from typing import Dict, List, Optional

from .resonance_analysis import (ResonanceAnalyzer, ResonanceDatabase, 
                               ResonanceItem, RESONANCE_FIELDS)

class ModernWidget(QWidget):
    """Widget base com estilo moderno"""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #34495e;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QComboBox, QSpinBox, QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 20px;
            }
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
                border-color: #3498db;
            }
            QTableWidget {
                gridline-color: #ecf0f1;
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)

class ResonanceControlPanel(ModernWidget):
    """Painel de controle da análise"""
    
    start_analysis = pyqtSignal(dict)  # parâmetros da análise
    stop_analysis = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Grupo: Campo de Análise
        field_group = QGroupBox("🔮 Campo de Análise")
        field_layout = QVBoxLayout(field_group)
        
        self.field_combo = QComboBox()
        for field in RESONANCE_FIELDS:
            self.field_combo.addItem(f"{field.name} ({field.description})", field.name)
        
        field_layout.addWidget(self.field_combo)
        layout.addWidget(field_group)
        
        # Grupo: Testemunho Digital
        witness_group = QGroupBox("🧬 Testemunho Digital")
        witness_layout = QVBoxLayout(witness_group)
        
        # Nome do paciente
        witness_layout.addWidget(QLabel("Nome do Paciente:"))
        self.patient_name = QLineEdit()
        self.patient_name.setPlaceholderText("Nome completo...")
        witness_layout.addWidget(self.patient_name)
        
        # Data de nascimento
        witness_layout.addWidget(QLabel("Data de Nascimento:"))
        birth_layout = QHBoxLayout()
        self.birth_day = QSpinBox()
        self.birth_day.setRange(1, 31)
        self.birth_month = QSpinBox()
        self.birth_month.setRange(1, 12)
        self.birth_year = QSpinBox()
        self.birth_year.setRange(1900, 2030)
        self.birth_year.setValue(1980)
        
        birth_layout.addWidget(self.birth_day)
        birth_layout.addWidget(QLabel("/"))
        birth_layout.addWidget(self.birth_month)
        birth_layout.addWidget(QLabel("/"))
        birth_layout.addWidget(self.birth_year)
        birth_layout.addStretch()
        
        witness_layout.addLayout(birth_layout)
        layout.addWidget(witness_group)
        
        # Grupo: Filtros de Ressonância
        filter_group = QGroupBox("⚖️ Filtros de Ressonância")
        filter_layout = QVBoxLayout(filter_group)
        
        # Threshold de ressonância
        filter_layout.addWidget(QLabel("Threshold de Ressonância:"))
        threshold_layout = QHBoxLayout()
        
        self.threshold_min = QSpinBox()
        self.threshold_min.setRange(-100, 100)
        self.threshold_min.setValue(-20)
        self.threshold_min.setSuffix(" min")
        
        self.threshold_max = QSpinBox()
        self.threshold_max.setRange(-100, 100)
        self.threshold_max.setValue(20)
        self.threshold_max.setSuffix(" max")
        
        threshold_layout.addWidget(self.threshold_min)
        threshold_layout.addWidget(QLabel("até"))
        threshold_layout.addWidget(self.threshold_max)
        threshold_layout.addStretch()
        
        filter_layout.addLayout(threshold_layout)
        
        # Mostrar apenas itens ressonantes
        self.only_resonant = QCheckBox("Mostrar apenas itens ressonantes")
        self.only_resonant.setChecked(True)
        filter_layout.addWidget(self.only_resonant)
        
        layout.addWidget(filter_group)
        
        # Botões de controle
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Iniciar Análise")
        self.start_btn.setStyleSheet("QPushButton { background-color: #27ae60; }")
        self.start_btn.clicked.connect(self.start_analysis_clicked)
        
        self.stop_btn = QPushButton("⏹️ Parar")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #e74c3c; }")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_analysis)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
    def start_analysis_clicked(self):
        """Emite sinal para iniciar análise com parâmetros"""
        if not self.patient_name.text().strip():
            return  # Validação básica
            
        params = {
            'field': self.field_combo.currentData(),
            'patient_witness': {
                'name': self.patient_name.text().strip(),
                'birth_date': f"{self.birth_day.value():02d}/{self.birth_month.value():02d}/{self.birth_year.value()}"
            },
            'threshold': (self.threshold_min.value(), self.threshold_max.value()),
            'only_resonant': self.only_resonant.isChecked()
        }
        
        self.start_analysis.emit(params)
        
    def set_analysis_running(self, running: bool):
        """Atualiza estado dos controles durante análise"""
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.field_combo.setEnabled(not running)
        self.patient_name.setEnabled(not running)
        self.birth_day.setEnabled(not running)
        self.birth_month.setEnabled(not running)
        self.birth_year.setEnabled(not running)

class CategoryTreeWidget(ModernWidget):
    """Árvore de categorias estilo CoRe"""
    
    category_selected = pyqtSignal(str, str)  # categoria, subcategoria
    
    def __init__(self):
        super().__init__()
        self.database = ResonanceDatabase()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Buscar:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para filtrar categorias...")
        self.search_input.textChanged.connect(self.filter_categories)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Árvore de categorias
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("📚 Categorias de Análise")
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        self.populate_tree()
        layout.addWidget(self.tree)
        
        # Estatísticas
        self.stats_label = QLabel()
        self.update_stats()
        layout.addWidget(self.stats_label)
        
    def populate_tree(self):
        """Popula árvore com categorias da base de dados"""
        self.tree.clear()
        categories = self.database.get_categories()
        
        for category, subcategories in categories.items():
            category_item = QTreeWidgetItem([f"📁 {category}"])
            category_item.setData(0, Qt.ItemDataRole.UserRole, ("category", category))
            
            for subcategory, items in subcategories.items():
                sub_item = QTreeWidgetItem([f"📋 {subcategory} ({len(items)} itens)"])
                sub_item.setData(0, Qt.ItemDataRole.UserRole, ("subcategory", category, subcategory))
                category_item.addChild(sub_item)
                
            self.tree.addTopLevelItem(category_item)
            
        self.tree.expandAll()
        
    def filter_categories(self, text: str):
        """Filtra categorias baseado no texto de busca"""
        # Implementar filtro de busca
        pass
        
    def on_item_clicked(self, item, column):
        """Handle clique em item da árvore"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and len(data) >= 2:
            if data[0] == "subcategory":
                self.category_selected.emit(data[1], data[2])
                
    def update_stats(self):
        """Atualiza estatísticas"""
        total_items = len(self.database.get_all_items())
        total_categories = len(self.database.get_categories())
        self.stats_label.setText(f"📊 {total_categories} categorias, {total_items} itens total")

class ResonanceResultsTable(ModernWidget):
    """Tabela de resultados da análise"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.results = []
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título e estatísticas
        header_layout = QHBoxLayout()
        self.title_label = QLabel("📊 Resultados da Análise")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.stats_label = QLabel("Nenhuma análise executada")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Tabela de resultados
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # Configurar colunas
        columns = ["Item", "Categoria", "Subcategoria", "Ressonância", "Estabilidade", "Confiança", "Campo"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Ajustar largura das colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Item
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Categoria
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Subcategoria
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Ressonância
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Estabilidade
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Confiança
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Campo
        
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        
        layout.addWidget(self.table)
        
    def add_result(self, result: dict):
        """Adiciona resultado à tabela"""
        self.results.append(result)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Item
        self.table.setItem(row, 0, QTableWidgetItem(result['name']))
        
        # Categoria
        self.table.setItem(row, 1, QTableWidgetItem(result['category']))
        
        # Subcategoria
        self.table.setItem(row, 2, QTableWidgetItem(result['subcategory']))
        
        # Ressonância (com cor)
        resonance_item = QTableWidgetItem(f"{result['value']:+d}")
        resonance_value = result['value']
        
        if resonance_value > 50:
            resonance_item.setBackground(QBrush(QColor(39, 174, 96)))  # Verde forte
            resonance_item.setForeground(QBrush(QColor(255, 255, 255)))
        elif resonance_value > 20:
            resonance_item.setBackground(QBrush(QColor(46, 204, 113)))  # Verde médio
        elif resonance_value > 0:
            resonance_item.setBackground(QBrush(QColor(125, 206, 160)))  # Verde claro
        elif resonance_value > -20:
            resonance_item.setBackground(QBrush(QColor(255, 193, 7)))  # Amarelo
        elif resonance_value > -50:
            resonance_item.setBackground(QBrush(QColor(230, 126, 34)))  # Laranja
        else:
            resonance_item.setBackground(QBrush(QColor(231, 76, 60)))  # Vermelho
            resonance_item.setForeground(QBrush(QColor(255, 255, 255)))
            
        self.table.setItem(row, 3, resonance_item)
        
        # Estabilidade
        stability_item = QTableWidgetItem(f"{result['stability']:.2f}")
        if result['stability'] > 0.8:
            stability_item.setBackground(QBrush(QColor(46, 204, 113)))
        elif result['stability'] > 0.6:
            stability_item.setBackground(QBrush(QColor(241, 196, 15)))
        else:
            stability_item.setBackground(QBrush(QColor(231, 76, 60)))
            stability_item.setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(row, 4, stability_item)
        
        # Confiança
        confidence_item = QTableWidgetItem(f"{result['confidence']:.2f}")
        if result['confidence'] > 0.8:
            confidence_item.setBackground(QBrush(QColor(46, 204, 113)))
        elif result['confidence'] > 0.6:
            confidence_item.setBackground(QBrush(QColor(241, 196, 15)))
        else:
            confidence_item.setBackground(QBrush(QColor(231, 76, 60)))
            confidence_item.setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(row, 5, confidence_item)
        
        # Campo
        self.table.setItem(row, 6, QTableWidgetItem(result['field']))
        
        # Atualizar estatísticas
        self.update_stats()
        
    def clear_results(self):
        """Limpa todos os resultados"""
        self.table.setRowCount(0)
        self.results = []
        self.update_stats()
        
    def update_stats(self):
        """Atualiza estatísticas"""
        total = len(self.results)
        if total == 0:
            self.stats_label.setText("Nenhuma análise executada")
            return
            
        positive = len([r for r in self.results if r['value'] > 0])
        negative = len([r for r in self.results if r['value'] < 0])
        
        avg_resonance = sum(r['value'] for r in self.results) / total
        avg_stability = sum(r['stability'] for r in self.results) / total
        avg_confidence = sum(r['confidence'] for r in self.results) / total
        
        self.stats_label.setText(
            f"📊 {total} resultados | "
            f"➕{positive} | ➖{negative} | "
            f"Média: {avg_resonance:+.1f} | "
            f"Estab: {avg_stability:.2f} | "
            f"Conf: {avg_confidence:.2f}"
        )

class ResonanceAnalysisWidget(ModernWidget):
    """Widget principal da análise de ressonância"""
    
    def __init__(self):
        super().__init__()
        self.analyzer = ResonanceAnalyzer()
        self.database = ResonanceDatabase()
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo (controles + categorias)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Controles
        self.control_panel = ResonanceControlPanel()
        left_layout.addWidget(self.control_panel)
        
        # Categorias
        self.category_tree = CategoryTreeWidget()
        left_layout.addWidget(self.category_tree)
        
        left_widget.setMaximumWidth(400)
        
        # Painel direito (resultados + progresso)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Progresso
        progress_group = QGroupBox("🔄 Progresso da Análise")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Pronto para análise")
        progress_layout.addWidget(self.status_label)
        
        right_layout.addWidget(progress_group)
        
        # Resultados
        self.results_table = ResonanceResultsTable()
        right_layout.addWidget(self.results_table)
        
        # Adicionar ao splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([400, 800])
        
        layout.addWidget(main_splitter)
        
    def connect_signals(self):
        """Conecta sinais"""
        # Controles
        self.control_panel.start_analysis.connect(self.start_analysis)
        self.control_panel.stop_analysis.connect(self.analyzer.stop_analysis)
        
        # Analyzer
        self.analyzer.progress.connect(self.progress_bar.setValue)
        self.analyzer.item_analyzed.connect(self.results_table.add_result)
        self.analyzer.status_update.connect(self.status_label.setText)
        self.analyzer.analysis_complete.connect(self.on_analysis_complete)
        self.analyzer.started.connect(lambda: self.control_panel.set_analysis_running(True))
        self.analyzer.finished.connect(lambda: self.control_panel.set_analysis_running(False))
        
    def start_analysis(self, params: dict):
        """Inicia análise com parâmetros fornecidos"""
        # Obter todos os itens da base de dados
        items = self.database.get_all_items()
        
        if not items:
            self.status_label.setText("❌ Nenhum item encontrado na base de dados")
            return
            
        # Configurar analyzer
        self.analyzer.set_analysis_parameters(
            items=items,
            field=params['field'],
            patient_witness=params['patient_witness'],
            threshold=params['threshold']
        )
        
        # Limpar resultados anteriores
        self.results_table.clear_results()
        
        # Mostrar progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Iniciar análise
        self.analyzer.start()
        
    def on_analysis_complete(self, results: List[ResonanceItem]):
        """Callback quando análise termina"""
        self.progress_bar.setVisible(False)
        
        if results:
            self.status_label.setText(f"✅ Análise completa: {len(results)} itens ressonantes")
        else:
            self.status_label.setText("⚠️ Nenhum item ressonante encontrado com os filtros atuais")
