"""
Biodesk - Widget de Histórico de Análises da Íris
==================================================

Widget especializado para exibir análises da íris de forma organizada.
Painel lateral que mostra análises por data com formatação clara.

🎯 Funcionalidades:
- Tabela organizada por data
- Quebra de linha automática para textos longos
- Interface limpa e profissional
- Fácil navegação por análises anteriores

📅 Criado em: Agosto 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Dict, Any, List
from PyQt6.QtWidgets import *
from biodesk_dialogs import BiodeskMessageBox
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime
import json
import os

from biodesk_ui_kit import BiodeskUIKit


class IrisHistoricoWidget(QWidget):
    """Widget especializado para histórico de análises da íris"""
    
    def __init__(self, paciente_id: str = None, parent=None):
        super().__init__(parent)
        
        self.paciente_id = paciente_id
        self.analises_file = f"historico_envios/iris_analises_{paciente_id}.json" if paciente_id else None
        
        # Dados das análises
        self.analises_dados = []
        
        # Inicializar interface
        self.init_ui()
        self.carregar_analises()
    
    def init_ui(self):
        """Inicializa interface do histórico de íris"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Cabeçalho
        self.criar_cabecalho(layout)
        
        # Tabela de análises
        self.criar_tabela_analises(layout)
        
        # Botões de ação
        self.criar_botoes_acao(layout)
    
    def criar_cabecalho(self, parent_layout):
        """Cria cabeçalho do painel"""
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BiodeskUIKit.COLORS['primary']}, 
                    stop:1 {BiodeskUIKit.COLORS['primary_dark']});
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Título
        titulo = QLabel("📊 Análises da Íris")
        titulo.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold; 
            color: white;
            background: transparent;
            margin: 0;
            padding: 0;
        """)
        header_layout.addWidget(titulo)
        
        # Subtítulo com estatísticas
        self.label_stats = QLabel("0 análises registradas")
        self.label_stats.setStyleSheet(f"""
            font-size: 12px; 
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
            margin: 0;
            padding: 0;
        """)
        header_layout.addWidget(self.label_stats)
        
        parent_layout.addWidget(header_widget)
    
    def criar_tabela_analises(self, parent_layout):
        """Cria tabela para exibir análises"""
        # Container com scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {BiodeskUIKit.COLORS['border']};
                border-radius: 6px;
                background-color: white;
            }}
            QScrollBar:vertical {{
                background-color: {BiodeskUIKit.COLORS['background_light']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BiodeskUIKit.COLORS['primary']};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)
        
        # Widget principal da tabela
        self.tabela_widget = QWidget()
        self.tabela_layout = QVBoxLayout(self.tabela_widget)
        self.tabela_layout.setContentsMargins(10, 10, 10, 10)
        self.tabela_layout.setSpacing(5)
        
        # Adicionar mensagem inicial
        self.label_vazio = QLabel("📋 Nenhuma análise registrada ainda.\n\nClique em zonas da íris e use o botão 'Histórico' para adicionar análises.")
        self.label_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_vazio.setStyleSheet(f"""
            color: {BiodeskUIKit.COLORS['text_secondary']};
            font-size: 14px;
            padding: 40px;
            border: 2px dashed {BiodeskUIKit.COLORS['border']};
            border-radius: 8px;
            background-color: {BiodeskUIKit.COLORS['background_light']};
        """)
        self.tabela_layout.addWidget(self.label_vazio)
        
        # Espaçador para empurrar conteúdo para cima
        self.tabela_layout.addStretch()
        
        scroll_area.setWidget(self.tabela_widget)
        parent_layout.addWidget(scroll_area)
    
    def criar_botoes_acao(self, parent_layout):
        """Cria botões de ação"""
        botoes_layout = QHBoxLayout()
        
        # Botão limpar histórico
        btn_limpar = QPushButton("🗑️ Limpar")
        btn_limpar.setStyleSheet(f"""
            QPushButton {{
                background-color: {BiodeskUIKit.COLORS['error']};
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BiodeskUIKit.COLORS['error_dark']};
            }}
        """)
        btn_limpar.clicked.connect(self.limpar_historico)
        
        # Botão exportar
        btn_exportar = QPushButton("📤 Exportar")
        btn_exportar.setStyleSheet(f"""
            QPushButton {{
                background-color: {BiodeskUIKit.COLORS['success']};
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BiodeskUIKit.COLORS['success_dark']};
            }}
        """)
        btn_exportar.clicked.connect(self.exportar_analises)
        
        botoes_layout.addWidget(btn_limpar)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_exportar)
        
        parent_layout.addLayout(botoes_layout)
    
    def adicionar_analise(self, zona: str, notas: str):
        """Adiciona nova análise ao histórico"""
        data_atual = datetime.now()
        
        nova_analise = {
            'data': data_atual.strftime('%d/%m/%Y'),
            'hora': data_atual.strftime('%H:%M'),
            'zona': zona,
            'notas': notas,
            'timestamp': data_atual.timestamp()
        }
        
        # Adicionar aos dados
        self.analises_dados.insert(0, nova_analise)  # Mais recente primeiro
        
        # Salvar no arquivo
        self.salvar_analises()
        
        # Atualizar interface
        self.atualizar_tabela()
        
        print(f"✅ Análise adicionada ao painel lateral: {zona}")
    
    def carregar_analises(self):
        """Carrega análises do arquivo"""
        if not self.analises_file or not os.path.exists(self.analises_file):
            return
        
        try:
            with open(self.analises_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.analises_dados = data.get('analises', [])
            
            # Ordenar por timestamp (mais recente primeiro)
            self.analises_dados.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            self.atualizar_tabela()
            
        except Exception as e:
            print(f"❌ Erro ao carregar análises da íris: {e}")
    
    def salvar_analises(self):
        """Salva análises no arquivo"""
        if not self.analises_file:
            return
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(self.analises_file), exist_ok=True)
        
        try:
            data = {
                'paciente_id': self.paciente_id,
                'ultima_atualizacao': datetime.now().isoformat(),
                'analises': self.analises_dados
            }
            
            with open(self.analises_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"❌ Erro ao salvar análises da íris: {e}")
    
    def atualizar_tabela(self):
        """Atualiza a exibição da tabela"""
        # Limpar layout existente
        while self.tabela_layout.count():
            child = self.tabela_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.analises_dados:
            # Mostrar mensagem vazia
            self.label_vazio = QLabel("📋 Nenhuma análise registrada ainda.\n\nClique em zonas da íris e use o botão 'Histórico' para adicionar análises.")
            self.label_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label_vazio.setStyleSheet(f"""
                color: {BiodeskUIKit.COLORS['text_secondary']};
                font-size: 14px;
                padding: 40px;
                border: 2px dashed {BiodeskUIKit.COLORS['border']};
                border-radius: 8px;
                background-color: {BiodeskUIKit.COLORS['background_light']};
            """)
            self.tabela_layout.addWidget(self.label_vazio)
        else:
            # Criar entradas para cada análise
            data_atual = None
            
            for analise in self.analises_dados:
                data_analise = analise['data']
                
                # Adicionar cabeçalho de data se mudou
                if data_analise != data_atual:
                    if data_atual is not None:
                        # Adicionar separador
                        separador = QFrame()
                        separador.setFrameShape(QFrame.Shape.HLine)
                        separador.setStyleSheet(f"color: {BiodeskUIKit.COLORS['border']};")
                        self.tabela_layout.addWidget(separador)
                    
                    # Cabeçalho da data
                    header_data = QLabel(f"📅 {data_analise}")
                    header_data.setStyleSheet(f"""
                        font-weight: bold;
                        font-size: 14px;
                        color: {BiodeskUIKit.COLORS['primary']};
                        padding: 10px 5px 5px 5px;
                        margin-top: 10px;
                    """)
                    self.tabela_layout.addWidget(header_data)
                    
                    data_atual = data_analise
                
                # Criar widget para esta análise
                analise_widget = self.criar_widget_analise(analise)
                self.tabela_layout.addWidget(analise_widget)
        
        # Adicionar espaçador
        self.tabela_layout.addStretch()
        
        # Atualizar estatísticas
        total = len(self.analises_dados)
        self.label_stats.setText(f"{total} análise{'s' if total != 1 else ''} registrada{'s' if total != 1 else ''}")
    
    def criar_widget_analise(self, analise: dict) -> QWidget:
        """Cria widget para uma análise individual"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {BiodeskUIKit.COLORS['border']};
                border-radius: 6px;
                margin: 2px 0px;
            }}
            QFrame:hover {{
                border-color: {BiodeskUIKit.COLORS['primary']};
                background-color: {BiodeskUIKit.COLORS['background_light']};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # Linha 1: Hora + Zona
        linha1_layout = QHBoxLayout()
        
        label_hora = QLabel(f"🕐 {analise['hora']}")
        label_hora.setStyleSheet(f"""
            font-size: 11px;
            color: {BiodeskUIKit.COLORS['text_secondary']};
            font-weight: 500;
        """)
        
        label_zona = QLabel(f"🔴 {analise['zona']}")
        label_zona.setStyleSheet(f"""
            font-size: 12px;
            color: {BiodeskUIKit.COLORS['primary']};
            font-weight: 600;
        """)
        
        linha1_layout.addWidget(label_hora)
        linha1_layout.addStretch()
        linha1_layout.addWidget(label_zona)
        
        layout.addLayout(linha1_layout)
        
        # Linha 2: Notas (com quebra de linha automática)
        if analise['notas'].strip():
            label_notas = QLabel(analise['notas'])
            label_notas.setWordWrap(True)  # Quebra automática
            label_notas.setStyleSheet(f"""
                font-size: 11px;
                color: {BiodeskUIKit.COLORS['text']};
                padding: 5px;
                background-color: {BiodeskUIKit.COLORS['background_light']};
                border-radius: 4px;
                border: 1px solid {BiodeskUIKit.COLORS['border']};
            """)
            layout.addWidget(label_notas)
        
        return widget
    
    def limpar_historico(self):
        """Limpa todo o histórico de análises"""
        reply = BiodeskMessageBox.question(
            self, 
            "Confirmar Limpeza",
            "Tem certeza que deseja limpar todo o histórico de análises da íris?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.analises_dados.clear()
            self.salvar_analises()
            self.atualizar_tabela()
            print("🗑️ Histórico de análises da íris limpo")
    
    def exportar_analises(self):
        """Exporta análises para arquivo"""
        if not self.analises_dados:
            BiodeskMessageBox.information(self, "Exportar", "Não há análises para exportar.")
            return
        
        # Diálogo para escolher arquivo
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Análises da Íris",
            f"analises_iris_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("HISTÓRICO DE ANÁLISES DA ÍRIS\n")
                    f.write("=" * 50 + "\n\n")
                    
                    data_atual = None
                    for analise in self.analises_dados:
                        if analise['data'] != data_atual:
                            if data_atual is not None:
                                f.write("\n" + "-" * 30 + "\n\n")
                            f.write(f"📅 {analise['data']}\n\n")
                            data_atual = analise['data']
                        
                        f.write(f"🕐 {analise['hora']} - 🔴 {analise['zona']}\n")
                        if analise['notas'].strip():
                            f.write(f"   {analise['notas']}\n")
                        f.write("\n")
                
                BiodeskMessageBox.information(self, "Exportar", f"Análises exportadas com sucesso para:\n{filename}")
                print(f"📤 Análises exportadas para: {filename}")
                
            except Exception as e:
                BiodeskMessageBox.critical(self, "Erro", f"Erro ao exportar análises:\n{str(e)}")
                print(f"❌ Erro ao exportar análises: {e}")
    
    def set_paciente_id(self, paciente_id: str):
        """Define o ID do paciente e recarrega dados"""
        self.paciente_id = paciente_id
        self.analises_file = f"historico_envios/iris_analises_{paciente_id}.json" if paciente_id else None
        self.analises_dados.clear()
        self.carregar_analises()
