"""
FASE 5: Sistema de Relatórios e Documentação
===========================================

Geração de relatórios completos das sessões de análise e balanceamento
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict
import base64
from io import BytesIO

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QTabWidget, QGroupBox,
                            QTableWidget, QTableWidgetItem, QFileDialog,
                            QComboBox, QDateEdit, QSpinBox, QCheckBox,
                            QScrollArea, QGridLayout, QHeaderView,
                            QProgressBar, QSplitter)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from .resonance_analysis import ResonanceItem, ResonanceField
from .protocol_generator import TherapyProtocol, ProtocolStep, ProtocolType
from .resonance_interface import ModernWidget

class SessionData:
    """Dados completos de uma sessão"""
    
    def __init__(self):
        self.session_id = ""
        self.timestamp = datetime.now()
        self.patient_witness = {}
        self.field_used = ""
        self.analysis_results = []
        self.generated_protocols = []
        self.executed_protocol = None
        self.execution_log = []
        self.notes = ""
        self.metadata = {}
        
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável"""
        return {
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'patient_witness': self.patient_witness,
            'field_used': self.field_used,
            'analysis_results': [asdict(item) for item in self.analysis_results],
            'generated_protocols': [asdict(protocol) for protocol in self.generated_protocols],
            'executed_protocol': asdict(self.executed_protocol) if self.executed_protocol else None,
            'execution_log': self.execution_log,
            'notes': self.notes,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Cria instância a partir de dicionário"""
        session = cls()
        session.session_id = data.get('session_id', '')
        session.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        session.patient_witness = data.get('patient_witness', {})
        session.field_used = data.get('field_used', '')
        # Note: analysis_results e protocols precisariam de reconstrução completa
        # Para simplificar, apenas guardamos os dados básicos
        session.notes = data.get('notes', '')
        session.metadata = data.get('metadata', {})
        return session

class ReportGenerator:
    """Gerador de relatórios em diferentes formatos"""
    
    def __init__(self):
        self.template_dir = Path("templates/reports")
        self.output_dir = Path("reports")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Garante que diretórios existem"""
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_analysis_report(self, session_data: SessionData, 
                               format_type: str = "html") -> str:
        """Gera relatório de análise de ressonância"""
        if format_type == "html":
            return self._generate_html_analysis_report(session_data)
        elif format_type == "text":
            return self._generate_text_analysis_report(session_data)
        elif format_type == "csv":
            return self._generate_csv_analysis_report(session_data)
        else:
            raise ValueError(f"Formato não suportado: {format_type}")
    
    def _generate_html_analysis_report(self, session_data: SessionData) -> str:
        """Gera relatório HTML detalhado"""
        
        # Calcular estatísticas
        results = session_data.analysis_results
        if results:
            positive_count = len([r for r in results if r.resonance_value > 0])
            negative_count = len([r for r in results if r.resonance_value < 0])
            avg_resonance = sum(r.resonance_value for r in results) / len(results)
            
            # Itens mais ressonantes
            top_positive = sorted([r for r in results if r.resonance_value > 0], 
                                key=lambda x: x.resonance_value, reverse=True)[:5]
            top_negative = sorted([r for r in results if r.resonance_value < 0],
                                key=lambda x: abs(x.resonance_value), reverse=True)[:5]
        else:
            positive_count = negative_count = 0
            avg_resonance = 0
            top_positive = top_negative = []
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Análise de Ressonância - Biodesk</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 20px; 
            color: #2c3e50;
            line-height: 1.6;
        }}
        .header {{ 
            text-align: center; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{ 
            color: #2c3e50; 
            margin: 0;
            font-size: 28px;
        }}
        .header h2 {{ 
            color: #7f8c8d; 
            margin: 5px 0 0 0;
            font-weight: normal;
        }}
        .section {{ 
            margin: 30px 0; 
            padding: 20px;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            background-color: #f8f9fa;
        }}
        .section h3 {{ 
            color: #34495e; 
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin: 20px 0;
        }}
        .stat-card {{ 
            background: white; 
            padding: 15px; 
            border-radius: 6px; 
            text-align: center;
            border: 1px solid #ecf0f1;
        }}
        .stat-number {{ 
            font-size: 24px; 
            font-weight: bold; 
            color: #3498db;
        }}
        .stat-label {{ 
            color: #7f8c8d; 
            font-size: 14px;
        }}
        .resonance-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
        }}
        .resonance-table th, .resonance-table td {{ 
            border: 1px solid #ddd; 
            padding: 10px; 
            text-align: left;
        }}
        .resonance-table th {{ 
            background-color: #3498db; 
            color: white;
        }}
        .positive {{ color: #27ae60; font-weight: bold; }}
        .negative {{ color: #e74c3c; font-weight: bold; }}
        .neutral {{ color: #f39c12; }}
        .footer {{ 
            text-align: center; 
            margin-top: 40px; 
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 Relatório de Análise de Ressonância</h1>
        <h2>Sistema Biodesk - Medicina Informacional</h2>
        <p><strong>Data:</strong> {session_data.timestamp.strftime('%d/%m/%Y às %H:%M')}</p>
        <p><strong>ID da Sessão:</strong> {session_data.session_id}</p>
    </div>

    <div class="section">
        <h3>👤 Dados do Paciente</h3>
        <p><strong>Nome:</strong> {session_data.patient_witness.get('name', 'N/A')}</p>
        <p><strong>Data de Nascimento:</strong> {session_data.patient_witness.get('birth_date', 'N/A')}</p>
        <p><strong>Campo Analisado:</strong> {session_data.field_used}</p>
    </div>

    <div class="section">
        <h3>📊 Estatísticas Gerais</h3>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{len(results)}</div>
                <div class="stat-label">Total de Itens</div>
            </div>
            <div class="stat-card">
                <div class="stat-number positive">{positive_count}</div>
                <div class="stat-label">Ressonantes Positivos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number negative">{negative_count}</div>
                <div class="stat-label">Stressors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{avg_resonance:+.1f}</div>
                <div class="stat-label">Ressonância Média</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h3>✅ Top 5 Ressonantes Positivos</h3>
        <table class="resonance-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Categoria</th>
                    <th>Ressonância</th>
                    <th>Estabilidade</th>
                    <th>Confiança</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in top_positive:
            html_content += f"""
                <tr>
                    <td>{item.name}</td>
                    <td>{item.category}</td>
                    <td class="positive">{item.resonance_value:+d}</td>
                    <td>{item.stability:.2f}</td>
                    <td>{item.confidence:.2f}</td>
                </tr>
            """
        
        html_content += """
            </tbody>
        </table>
    </div>

    <div class="section">
        <h3>⚠️ Top 5 Stressors</h3>
        <table class="resonance-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Categoria</th>
                    <th>Ressonância</th>
                    <th>Estabilidade</th>
                    <th>Confiança</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in top_negative:
            html_content += f"""
                <tr>
                    <td>{item.name}</td>
                    <td>{item.category}</td>
                    <td class="negative">{item.resonance_value:+d}</td>
                    <td>{item.stability:.2f}</td>
                    <td>{item.confidence:.2f}</td>
                </tr>
            """
        
        html_content += f"""
            </tbody>
        </table>
    </div>

    <div class="section">
        <h3>📝 Observações</h3>
        <p>{session_data.notes if session_data.notes else 'Nenhuma observação registrada.'}</p>
    </div>

    <div class="footer">
        <p>Relatório gerado pelo Sistema Biodesk de Medicina Informacional</p>
        <p>Este relatório é para fins de pesquisa e apoio complementar</p>
        <p>Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _generate_text_analysis_report(self, session_data: SessionData) -> str:
        """Gera relatório em texto simples"""
        
        results = session_data.analysis_results
        positive_count = len([r for r in results if r.resonance_value > 0])
        negative_count = len([r for r in results if r.resonance_value < 0])
        
        report = f"""
================================================================================
                        RELATÓRIO DE ANÁLISE DE RESSONÂNCIA
                           Sistema Biodesk - Medicina Informacional
================================================================================

Data da Sessão: {session_data.timestamp.strftime('%d/%m/%Y às %H:%M')}
ID da Sessão: {session_data.session_id}

DADOS DO PACIENTE
================================================================================
Nome: {session_data.patient_witness.get('name', 'N/A')}
Data de Nascimento: {session_data.patient_witness.get('birth_date', 'N/A')}
Campo Analisado: {session_data.field_used}

ESTATÍSTICAS GERAIS
================================================================================
Total de Itens Analisados: {len(results)}
Ressonantes Positivos: {positive_count}
Stressors (Negativos): {negative_count}
        """
        
        if results:
            avg_resonance = sum(r.resonance_value for r in results) / len(results)
            report += f"Ressonância Média: {avg_resonance:+.1f}\n"
            
            # Top 5 positivos
            top_positive = sorted([r for r in results if r.resonance_value > 0], 
                                key=lambda x: x.resonance_value, reverse=True)[:5]
            
            if top_positive:
                report += "\nTOP 5 RESSONANTES POSITIVOS\n"
                report += "=" * 80 + "\n"
                for i, item in enumerate(top_positive, 1):
                    report += f"{i}. {item.name} ({item.category})\n"
                    report += f"   Ressonância: {item.resonance_value:+d} | "
                    report += f"Estabilidade: {item.stability:.2f} | "
                    report += f"Confiança: {item.confidence:.2f}\n\n"
            
            # Top 5 negativos
            top_negative = sorted([r for r in results if r.resonance_value < 0],
                                key=lambda x: abs(x.resonance_value), reverse=True)[:5]
            
            if top_negative:
                report += "\nTOP 5 STRESSORS\n"
                report += "=" * 80 + "\n"
                for i, item in enumerate(top_negative, 1):
                    report += f"{i}. {item.name} ({item.category})\n"
                    report += f"   Ressonância: {item.resonance_value:+d} | "
                    report += f"Estabilidade: {item.stability:.2f} | "
                    report += f"Confiança: {item.confidence:.2f}\n\n"
        
        if session_data.notes:
            report += f"\nOBSERVAÇÕES\n"
            report += "=" * 80 + "\n"
            report += f"{session_data.notes}\n"
        
        report += f"\n" + "=" * 80
        report += f"\nRelatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        report += f"\nSistema Biodesk de Medicina Informacional"
        
        return report
    
    def _generate_csv_analysis_report(self, session_data: SessionData) -> str:
        """Gera relatório em formato CSV"""
        
        csv_content = "Item,Categoria,Subcategoria,Ressonancia,Estabilidade,Confianca,Campo\n"
        
        for item in session_data.analysis_results:
            csv_content += f'"{item.name}","{item.category}","{item.subcategory}",'
            csv_content += f'{item.resonance_value},{item.stability:.3f},{item.confidence:.3f},'
            csv_content += f'"{session_data.field_used}"\n'
        
        return csv_content
    
    def generate_protocol_report(self, protocol: TherapyProtocol, 
                               execution_log: List = None) -> str:
        """Gera relatório de protocolo terapêutico"""
        
        duration_min = protocol.total_duration / 60
        effectiveness = self._calculate_protocol_effectiveness(protocol)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Relatório de Protocolo Terapêutico - Biodesk</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; color: #2c3e50; }}
        .header {{ text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #bdc3c7; border-radius: 6px; }}
        .protocol-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .protocol-table th, .protocol-table td {{ border: 1px solid #ddd; padding: 8px; }}
        .protocol-table th {{ background-color: #27ae60; color: white; }}
        .effectiveness {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
        .effectiveness div {{ background: #f8f9fa; padding: 10px; border-radius: 4px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚛️ Relatório de Protocolo Terapêutico</h1>
        <h2>{protocol.name}</h2>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    </div>

    <div class="section">
        <h3>📋 Informações do Protocolo</h3>
        <p><strong>Tipo:</strong> {protocol.protocol_type.value.title()}</p>
        <p><strong>Descrição:</strong> {protocol.description}</p>
        <p><strong>Duração Total:</strong> {duration_min:.1f} minutos</p>
        <p><strong>Número de Passos:</strong> {len(protocol.steps)}</p>
        <p><strong>Paciente:</strong> {protocol.patient_witness.get('name', 'N/A')}</p>
        <p><strong>Campo Usado:</strong> {protocol.field_used}</p>
    </div>

    <div class="section">
        <h3>📊 Eficácia Estimada</h3>
        <div class="effectiveness">
            <div>
                <strong>{effectiveness['strength']*100:.0f}%</strong><br>
                <small>Força</small>
            </div>
            <div>
                <strong>{effectiveness['balance']*100:.0f}%</strong><br>
                <small>Equilíbrio</small>
            </div>
            <div>
                <strong>{effectiveness['coherence']*100:.0f}%</strong><br>
                <small>Coerência</small>
            </div>
            <div>
                <strong>{effectiveness['overall']*100:.0f}%</strong><br>
                <small>Geral</small>
            </div>
        </div>
    </div>

    <div class="section">
        <h3>🔧 Passos do Protocolo</h3>
        <table class="protocol-table">
            <thead>
                <tr>
                    <th>Passo</th>
                    <th>Frequência</th>
                    <th>Amplitude</th>
                    <th>Duração</th>
                    <th>Tipo</th>
                    <th>Descrição</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, step in enumerate(protocol.steps, 1):
            step_min = step.duration / 60
            html_content += f"""
                <tr>
                    <td>{i}. {step.name}</td>
                    <td>{step.frequency:.1f} Hz</td>
                    <td>{step.amplitude:.1f} V</td>
                    <td>{step_min:.1f} min</td>
                    <td>{step.step_type}</td>
                    <td>{step.description}</td>
                </tr>
            """
        
        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _calculate_protocol_effectiveness(self, protocol: TherapyProtocol) -> Dict[str, float]:
        """Calcula eficácia do protocolo"""
        # Implementação simplificada
        return {
            'strength': 0.8,
            'balance': 0.7,
            'coherence': 0.75,
            'overall': 0.75
        }
    
    def save_report(self, content: str, filename: str, format_type: str) -> str:
        """Salva relatório em arquivo"""
        
        file_path = self.output_dir / f"{filename}.{format_type}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)

class ReportsInterface(ModernWidget):
    """Interface para geração e gestão de relatórios"""
    
    def __init__(self):
        super().__init__()
        self.report_generator = ReportGenerator()
        self.current_session_data = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("📊 SISTEMA DE RELATÓRIOS E DOCUMENTAÇÃO")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #f8f9fa, stop:0.5 #fff3cd, stop:1 #f8f9fa);
                border: 3px solid #ffc107;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Tabs para diferentes tipos de relatório
        self.tabs = QTabWidget()
        
        # Tab 1: Relatório de Análise
        self.analysis_tab = self.create_analysis_report_tab()
        self.tabs.addTab(self.analysis_tab, "🔮 Relatório de Análise")
        
        # Tab 2: Relatório de Protocolo
        self.protocol_tab = self.create_protocol_report_tab()
        self.tabs.addTab(self.protocol_tab, "⚛️ Relatório de Protocolo")
        
        # Tab 3: Histórico de Sessões
        self.history_tab = self.create_history_tab()
        self.tabs.addTab(self.history_tab, "📋 Histórico")
        
        layout.addWidget(self.tabs)
        
    def create_analysis_report_tab(self) -> QWidget:
        """Cria tab para relatórios de análise"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configurações do relatório
        config_group = QGroupBox("⚙️ Configurações do Relatório")
        config_layout = QGridLayout(config_group)
        
        # Formato
        config_layout.addWidget(QLabel("Formato:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HTML (Completo)", "Texto Simples", "CSV (Dados)"])
        config_layout.addWidget(self.format_combo, 0, 1)
        
        # Incluir seções
        config_layout.addWidget(QLabel("Incluir:"), 1, 0)
        sections_layout = QVBoxLayout()
        
        self.include_stats_check = QCheckBox("Estatísticas gerais")
        self.include_stats_check.setChecked(True)
        sections_layout.addWidget(self.include_stats_check)
        
        self.include_positive_check = QCheckBox("Top ressonantes positivos")
        self.include_positive_check.setChecked(True)
        sections_layout.addWidget(self.include_positive_check)
        
        self.include_negative_check = QCheckBox("Top stressors")
        self.include_negative_check.setChecked(True)
        sections_layout.addWidget(self.include_negative_check)
        
        self.include_full_data_check = QCheckBox("Dados completos (todos os itens)")
        sections_layout.addWidget(self.include_full_data_check)
        
        config_layout.addLayout(sections_layout, 1, 1)
        
        layout.addWidget(config_group)
        
        # Pré-visualização
        preview_group = QGroupBox("👁️ Pré-visualização")
        preview_layout = QVBoxLayout(preview_group)
        
        self.analysis_preview = QTextEdit()
        self.analysis_preview.setMaximumHeight(300)
        self.analysis_preview.setPlaceholderText("Pré-visualização do relatório aparecerá aqui...")
        preview_layout.addWidget(self.analysis_preview)
        
        layout.addWidget(preview_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.generate_analysis_btn = QPushButton("🔄 Gerar Pré-visualização")
        self.generate_analysis_btn.clicked.connect(self.generate_analysis_preview)
        
        self.save_analysis_btn = QPushButton("💾 Salvar Relatório")
        self.save_analysis_btn.clicked.connect(self.save_analysis_report)
        self.save_analysis_btn.setEnabled(False)
        
        self.print_analysis_btn = QPushButton("🖨️ Imprimir")
        self.print_analysis_btn.clicked.connect(self.print_analysis_report)
        self.print_analysis_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.generate_analysis_btn)
        buttons_layout.addWidget(self.save_analysis_btn)
        buttons_layout.addWidget(self.print_analysis_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        return widget
        
    def create_protocol_report_tab(self) -> QWidget:
        """Cria tab para relatórios de protocolo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Informações básicas
        info_group = QGroupBox("📋 Protocolo Selecionado")
        info_layout = QVBoxLayout(info_group)
        
        self.protocol_info_label = QLabel("Nenhum protocolo selecionado")
        info_layout.addWidget(self.protocol_info_label)
        
        layout.addWidget(info_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.generate_protocol_btn = QPushButton("📄 Gerar Relatório de Protocolo")
        self.generate_protocol_btn.setEnabled(False)
        
        self.save_protocol_btn = QPushButton("💾 Salvar")
        self.save_protocol_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.generate_protocol_btn)
        buttons_layout.addWidget(self.save_protocol_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        return widget
        
    def create_history_tab(self) -> QWidget:
        """Cria tab para histórico de sessões"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros
        filters_group = QGroupBox("🔍 Filtros")
        filters_layout = QGridLayout(filters_group)
        
        filters_layout.addWidget(QLabel("Data de:"), 0, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(self.date_from, 0, 1)
        
        filters_layout.addWidget(QLabel("Data até:"), 0, 2)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        filters_layout.addWidget(self.date_to, 0, 3)
        
        refresh_btn = QPushButton("🔄 Atualizar")
        filters_layout.addWidget(refresh_btn, 0, 4)
        
        layout.addWidget(filters_group)
        
        # Tabela de sessões
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Data", "Paciente", "Campo", "Resultados", "Ações"
        ])
        
        # Configurar colunas
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def set_session_data(self, session_data: SessionData):
        """Define dados da sessão atual"""
        self.current_session_data = session_data
        self.generate_analysis_btn.setEnabled(True)
        
    def generate_analysis_preview(self):
        """Gera pré-visualização do relatório de análise"""
        if not self.current_session_data:
            return
            
        try:
            format_map = {
                "HTML (Completo)": "html",
                "Texto Simples": "text", 
                "CSV (Dados)": "csv"
            }
            format_type = format_map[self.format_combo.currentText()]
            
            content = self.report_generator.generate_analysis_report(
                self.current_session_data, format_type
            )
            
            if format_type == "html":
                self.analysis_preview.setHtml(content)
            else:
                self.analysis_preview.setPlainText(content)
                
            self.save_analysis_btn.setEnabled(True)
            self.print_analysis_btn.setEnabled(True)
            
        except Exception as e:
            self.analysis_preview.setPlainText(f"Erro ao gerar relatório: {e}")
    
    def save_analysis_report(self):
        """Salva relatório de análise"""
        if not self.current_session_data:
            return
            
        try:
            # Diálogo para escolher arquivo
            format_map = {
                "HTML (Completo)": ("html", "Arquivos HTML (*.html)"),
                "Texto Simples": ("txt", "Arquivos de Texto (*.txt)"),
                "CSV (Dados)": ("csv", "Arquivos CSV (*.csv)")
            }
            
            format_type, file_filter = format_map[self.format_combo.currentText()]
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Salvar Relatório",
                f"relatorio_analise_{datetime.now().strftime('%Y%m%d_%H%M')}.{format_type}",
                file_filter
            )
            
            if filename:
                content = self.report_generator.generate_analysis_report(
                    self.current_session_data, format_type
                )
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # Mostrar confirmação (usando print por simplicidade)
                print(f"Relatório salvo em: {filename}")
                
        except Exception as e:
            print(f"Erro ao salvar relatório: {e}")
    
    def print_analysis_report(self):
        """Imprime relatório de análise"""
        # Implementação simplificada
        print("Função de impressão ainda não implementada")

class DocumentationWidget(ModernWidget):
    """Widget principal para documentação e relatórios"""
    
    def __init__(self):
        super().__init__()
        self.reports_interface = ReportsInterface()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.reports_interface)
    
    def set_analysis_data(self, results: List[ResonanceItem], 
                         patient_witness: Dict, field_used: str):
        """Define dados da análise"""
        session_data = SessionData()
        session_data.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data.patient_witness = patient_witness
        session_data.field_used = field_used
        session_data.analysis_results = results
        
        self.reports_interface.set_session_data(session_data)
    
    def set_protocol_data(self, protocol: TherapyProtocol):
        """Define dados do protocolo"""
        # Implementar quando necessário
        pass
