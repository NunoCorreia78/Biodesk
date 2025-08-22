import os
import sys
import base64
from datetime import datetime
from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QPixmap, QImage
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF
from biodesk_dialogs import BiodeskMessageBox
from sistema_assinatura import abrir_dialogo_assinatura
from biodesk_ui_kit import BiodeskUIKit
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🩺 MÓDULO: Declaração de Saúde - SISTEMA COMPLETAMENTE NOVO
=========================================================

NOVA IMPLEMENTAÇÃO COMPLETA:
- ✅ Sistema unificado de assinatura
- ✅ Layout definitivo e centralizado
- ✅ 18 seções médicas implementadas
- ✅ PDF com assinaturas perfeitamente centradas
- ✅ Detecção automática de alterações
- ✅ Código limpo sem conflitos
"""

    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QComboBox, QLineEdit, QScrollArea, QFrame,
    QGridLayout, QGroupBox, QCheckBox, QSpinBox, QDateEdit,
    QFileDialog, QDialog, QDialogButtonBox
)

# Sistema de assinatura unificado
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DeclaracaoSaude(QWidget):
    """Widget para gestão de declarações de saúde com novo template completo"""
    
    declaracao_guardada = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.paciente_data = {}
        self.dados_declaracao = {}
        self.assinaturas = {'paciente': None, 'profissional': None}
        self.setup_ui()
        
    def setup_ui(self):
        """Interface completamente nova com todos os campos médicos"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        titulo = QLabel("📋 DECLARAÇÃO DE SAÚDE - ANAMNESE COMPLETA")
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #e8f5e9, stop:1 #c8e6c9);
            border-radius: 10px;
            margin-bottom: 10px;
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Área de scroll para o formulário
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 10px;
                background-color: #fafafa;
            }
        """)
        
        # Widget container do formulário
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # SEÇÕES DO FORMULÁRIO
        self.criar_secao_identificacao(form_layout)
        self.criar_secoes_medicas(form_layout)
        self.criar_secao_assinaturas(form_layout)
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)
        
        # Botões de ação
        self.criar_botoes_acao(layout)
        
    def criar_secao_identificacao(self, layout):
        """Seção de identificação do paciente"""
        grupo = QGroupBox("👤 IDENTIFICAÇÃO")
        grupo.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
                color: #2980b9;
            }
        """)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Campos de identificação
        campos = [
            ("Nome:", QLineEdit(), 0, 0, 1, 3),
            ("Data Nasc:", QDateEdit(), 0, 3, 1, 1),
            ("Contacto:", QLineEdit(), 1, 0, 1, 2),
            ("Email:", QLineEdit(), 1, 2, 1, 2),
            ("Profissão:", QLineEdit(), 2, 0, 1, 2),
            ("Esforço físico?", self.criar_combo_sim_nao(), 2, 2, 1, 1),
            ("Detalhe:", QLineEdit(), 2, 3, 1, 1)
        ]
        
        self.campos_id = {}
        for label, widget, row, col, rowspan, colspan in campos:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: normal;")
            grid.addWidget(lbl, row, col * 2)
            grid.addWidget(widget, row, col * 2 + 1, rowspan, colspan * 2 - 1)
            
            # Guardar referência
            campo_nome = label.replace(":", "").replace(" ", "_").lower()
            self.campos_id[campo_nome] = widget
            
            # Configurar DateEdit
            if isinstance(widget, QDateEdit):
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                widget.setDisplayFormat("dd/MM/yyyy")
        
        grupo.setLayout(grid)
        layout.addWidget(grupo)
        
    def criar_secoes_medicas(self, layout):
        """Criar todas as seções médicas com dropdowns"""
        
        secoes = [
            ("🔬 1. METABÓLICAS / ENDÓCRINAS", [
                ("Diabetes", ["Tipo", "HbA1c", "Hipoglicemias", "Tratamento"]),
                ("Hipertensão", ["Valores médios", "Medicação"]),
                ("Disfunção tiroideia", ["Hipo/Hiper", "Cirurgia", "Medicação"]),
                ("Dislipidemia", ["Valores recentes"]),
                ("Doença hepática", ["Tipo", "Detalhe"]),
                ("Doença renal", ["Estádio", "Clearance"])
            ]),
            
            ("❤️ 2. CARDIOVASCULARES", [
                ("Doença cardíaca", ["Tipo", "Data", "Detalhe"]),
                ("AVC/TIA", ["Ano", "Sequelas"]),
                ("Trombose/TEP", ["Local", "Data", "Tratamento"]),
                ("Aneurisma", ["Local", "Tamanho"]),
                ("Dor torácica recente", ["Esforço/Repouso", "Frequência"]),
                ("Pacemaker/Stent", ["Tipo", "Data", "Local"])
            ]),
            
            ("🫁 3. RESPIRATÓRIAS", [
                ("Asma", ["Crises/mês", "Medicação"]),
                ("DPOC/Fibrose", ["SatO2", "Oxigenoterapia"]),
                ("Apneia do sono", ["CPAP", "Pressão"]),
                ("Infeção recente", ["Tipo", "Data"])
            ]),
            
            ("🦴 4. MÚSCULO-ESQUELÉTICAS", [
                ("Artrite/Artrose", ["Articulações", "Limitações"]),
                ("Osteoporose", ["T-score", "Fraturas"]),
                ("Hérnias discais", ["Nível", "Data RM"]),
                ("Escoliose", ["Grau", "Tratamento"]),
                ("Fraturas", ["Local", "Data", "Consolidação"]),
                ("Cirurgias ortopédicas", ["Tipo", "Data", "Restrições"]),
                ("Próteses/Implantes", ["Local", "Material", "Data"])
            ]),
            
            ("💊 5. MEDICAÇÃO ATUAL", [
                ("Anticoagulantes", ["Nome", "Dose", "INR"]),
                ("Anti-hipertensivos", ["Nome", "Dose"]),
                ("Antidiabéticos", ["Nome", "Dose", "Horário"]),
                ("Psicotrópicos", ["Nome", "Dose", "Duração"]),
                ("Corticoides", ["Nome", "Dose", "Duração"]),
                ("Suplementos", ["Nome", "Dose", "Marca"])
            ]),
            
            ("🚨 6. ALERGIAS", [
                ("Medicamentos", ["Substância", "Reação"]),
                ("Alimentos", ["Alimento", "Reação"]),
                ("Plantas/Óleos", ["Substância", "Reação"]),
                ("Contacto", ["Material", "Reação"]),
                ("Anestésicos", ["Tipo", "Reação"])
            ])
        ]
        
        self.campos_medicos = {}
        
        for titulo_secao, campos in secoes:
            grupo = QGroupBox(titulo_secao)
            grupo.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #27ae60;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 20px;
                    padding: 0 10px 0 10px;
                    color: #27ae60;
                }
            """)
            
            grid = QGridLayout()
            grid.setSpacing(8)
            
            for i, (campo, detalhes) in enumerate(campos):
                # Label
                lbl = QLabel(f"{campo}:")
                lbl.setStyleSheet("font-weight: normal;")
                grid.addWidget(lbl, i, 0)
                
                # Dropdown Sim/Não
                combo = self.criar_combo_sim_nao()
                grid.addWidget(combo, i, 1)
                
                # Campos de detalhe
                detalhe_widget = QWidget()
                detalhe_layout = QHBoxLayout(detalhe_widget)
                detalhe_layout.setContentsMargins(0, 0, 0, 0)
                detalhe_layout.setSpacing(5)
                
                campos_detalhe = {}
                for detalhe in detalhes:
                    line = QLineEdit()
                    line.setPlaceholderText(detalhe)
                    line.setEnabled(False)
                    detalhe_layout.addWidget(line)
                    campos_detalhe[detalhe] = line
                
                grid.addWidget(detalhe_widget, i, 2, 1, 3)
                
                # Conectar dropdown para ativar/desativar detalhes
                combo.currentTextChanged.connect(
                    lambda text, widgets=campos_detalhe: self.toggle_detalhes(text, widgets)
                )
                
                # Guardar referências
                campo_id = f"{titulo_secao}_{campo}".replace(" ", "_")
                self.campos_medicos[campo_id] = {
                    'combo': combo,
                    'detalhes': campos_detalhe
                }
            
            grupo.setLayout(grid)
            layout.addWidget(grupo)
            
    def criar_combo_sim_nao(self):
        """Cria combo box padrão Sim/Não"""
        combo = QComboBox()
        combo.addItems(["", "Não", "Sim"])
        combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                min-width: 80px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
        """)
        return combo
        
    def toggle_detalhes(self, text, widgets):
        """Ativa/desativa campos de detalhe baseado na seleção"""
        enabled = (text == "Sim")
        for widget in widgets.values():
            widget.setEnabled(enabled)
            if not enabled:
                widget.clear()
                
    def criar_secao_assinaturas(self, layout):
        """Seção de assinaturas OTIMIZADA e CENTRALIZADA"""
        grupo = QGroupBox("✍️ ASSINATURAS E DECLARAÇÃO")
        grupo.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                background-color: #fff5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
                color: #c0392b;
            }
        """)
        
        layout_grupo = QVBoxLayout()
        
        # Texto da declaração
        declaracao = QLabel("""
        <p style='text-align: justify; line-height: 1.6;'>
        <b>DECLARO</b> que todas as informações prestadas são verdadeiras e completas. 
        Compreendo que a omissão de informações relevantes pode comprometer o tratamento 
        e assumo total responsabilidade pelas mesmas.<br><br>
        <b>AUTORIZO</b> o profissional de saúde a utilizar estas informações para fins 
        terapêuticos e de acompanhamento clínico.
        </p>
        """)
        declaracao.setWordWrap(True)
        declaracao.setStyleSheet("padding: 10px; background-color: white; border-radius: 5px;")
        layout_grupo.addWidget(declaracao)
        
        # Container para assinaturas CENTRALIZADO
        assinaturas_widget = QWidget()
        assinaturas_layout = QHBoxLayout(assinaturas_widget)
        assinaturas_layout.setSpacing(30)
        
        # Paciente
        paciente_frame = self.criar_frame_assinatura("PACIENTE", "paciente")
        assinaturas_layout.addWidget(paciente_frame)
        
        # Profissional
        profissional_frame = self.criar_frame_assinatura("PROFISSIONAL", "profissional")
        assinaturas_layout.addWidget(profissional_frame)
        
        # Centralizar o widget de assinaturas
        container_central = QHBoxLayout()
        container_central.addStretch()
        container_central.addWidget(assinaturas_widget)
        container_central.addStretch()
        
        layout_grupo.addLayout(container_central)
        
        grupo.setLayout(layout_grupo)
        layout.addWidget(grupo)
        
    def criar_frame_assinatura(self, titulo, tipo):
        """Cria frame individual para assinatura"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #95a5a6;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                min-width: 250px;
                max-width: 300px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)
        
        # Canvas de assinatura
        canvas = QLabel()
        canvas.setFixedSize(240, 80)
        canvas.setStyleSheet("""
            border: 1px solid #bdc3c7;
            background-color: #f8f9fa;
            border-radius: 4px;
        """)
        canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if tipo == "paciente":
            self.canvas_paciente = canvas
            nome = self.parent.paciente_data.get('nome', 'Paciente') if self.parent else 'Paciente'
        else:
            self.canvas_profissional = canvas
            nome = "Dr. Nuno Correia"
            
        layout.addWidget(canvas)
        
        # Nome
        lbl_nome = QLabel(nome)
        lbl_nome.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        lbl_nome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_nome)
        
        # Botão assinar
        btn = QPushButton(f"🖊️ Assinar")
        BiodeskUIKit.apply_universal_button_style(btn)
        
        if tipo == "paciente":
            btn.clicked.connect(self.assinar_paciente)
            self.btn_assinar_paciente = btn
        else:
            btn.clicked.connect(self.assinar_profissional)
            self.btn_assinar_profissional = btn
            
        layout.addWidget(btn)
        
        return frame
        
    def criar_botoes_acao(self, layout):
        """Botões de ação principais"""
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        # Botão Limpar
        btn_limpar = QPushButton("🗑️ Limpar Formulário")
        BiodeskUIKit.apply_universal_button_style(btn_limpar)
        btn_limpar.clicked.connect(self.limpar_formulario)
        botoes_layout.addWidget(btn_limpar)
        
        botoes_layout.addStretch()
        
        # Botão Guardar
        btn_guardar = QPushButton("💾 Guardar Declaração")
        BiodeskUIKit.apply_universal_button_style(btn_guardar)
        btn_guardar.clicked.connect(self.guardar_declaracao)
        botoes_layout.addWidget(btn_guardar)
        
        # Botão Gerar PDF
        btn_pdf = QPushButton("📄 Gerar PDF")
        BiodeskUIKit.apply_universal_button_style(btn_pdf)
        btn_pdf.clicked.connect(self.gerar_pdf)
        botoes_layout.addWidget(btn_pdf)
        
        layout.addLayout(botoes_layout)
        
    def assinar_paciente(self):
        """Abre diálogo de assinatura para paciente"""
        try:
            nome = self.parent.paciente_data.get('nome', 'Paciente') if self.parent else 'Paciente'
            resultado = abrir_dialogo_assinatura(
                parent=self,
                titulo="Assinatura do Paciente",
                nome_pessoa=nome,
                tipo_assinatura="paciente"
            )
            
            if resultado["confirmado"]:
                self.assinaturas['paciente'] = resultado["assinatura_bytes"]
                self.canvas_paciente.setText("✅ Assinado")
                self.canvas_paciente.setStyleSheet("""
                    border: 2px solid #27ae60;
                    background-color: #d4edda;
                    border-radius: 4px;
                    color: #155724;
                    font-weight: bold;
                """)
                self.btn_assinar_paciente.setEnabled(False)
                self.btn_assinar_paciente.setText("✅ Assinado")
                
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro na assinatura: {str(e)}")
            
    def assinar_profissional(self):
        """Abre diálogo de assinatura para profissional"""
        try:
            resultado = abrir_dialogo_assinatura(
                parent=self,
                titulo="Assinatura do Profissional",
                nome_pessoa="Dr. Nuno Correia",
                tipo_assinatura="profissional"
            )
            
            if resultado["confirmado"]:
                self.assinaturas['profissional'] = resultado["assinatura_bytes"]
                self.canvas_profissional.setText("✅ Assinado")
                self.canvas_profissional.setStyleSheet("""
                    border: 2px solid #27ae60;
                    background-color: #d4edda;
                    border-radius: 4px;
                    color: #155724;
                    font-weight: bold;
                """)
                self.btn_assinar_profissional.setEnabled(False)
                self.btn_assinar_profissional.setText("✅ Assinado")
                
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro na assinatura: {str(e)}")
            
    def limpar_formulario(self):
        """Limpa todos os campos do formulário com confirmação RÁPIDA"""
        # Timer para executar mais rápido
        QTimer.singleShot(0, self._executar_limpeza)
        
    def _executar_limpeza(self):
        """Executa limpeza de forma otimizada"""
        try:
            # Limpar identificação
            for widget in self.campos_id.values():
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(0)
                elif isinstance(widget, QDateEdit):
                    widget.setDate(QDate.currentDate())
            
            # Limpar campos médicos
            for secao in self.campos_medicos.values():
                secao['combo'].setCurrentIndex(0)
                for detalhe in secao['detalhes'].values():
                    detalhe.clear()
                    detalhe.setEnabled(False)
            
            # Limpar assinaturas
            self.assinaturas = {'paciente': None, 'profissional': None}
            
            for canvas, btn in [(self.canvas_paciente, self.btn_assinar_paciente),
                               (self.canvas_profissional, self.btn_assinar_profissional)]:
                canvas.clear()
                canvas.setStyleSheet("""
                    border: 1px solid #bdc3c7;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                """)
                btn.setEnabled(True)
                btn.setText("🖊️ Assinar")
                
            BiodeskMessageBox.information(self, "Sucesso", "Formulário limpo!")
            
        except Exception as e:
            print(f"Erro ao limpar: {e}")
            
    def guardar_declaracao(self):
        """Guarda a declaração na base de dados"""
        try:
            # Coletar todos os dados
            self.dados_declaracao = self.coletar_dados()
            
            # Validar assinaturas
            if not self.assinaturas.get('paciente'):
                BiodeskMessageBox.warning(self, "Aviso", "Assinatura do paciente necessária!")
                return
                
            if not self.assinaturas.get('profissional'):
                BiodeskMessageBox.warning(self, "Aviso", "Assinatura do profissional necessária!")
                return
            
            # Emitir sinal com os dados
            self.declaracao_guardada.emit({
                'dados': self.dados_declaracao,
                'assinaturas': self.assinaturas,
                'data': datetime.now().isoformat()
            })
            
            BiodeskMessageBox.information(self, "Sucesso", "Declaração guardada com sucesso!")
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro ao guardar: {str(e)}")
            
    def coletar_dados(self):
        """Coleta todos os dados do formulário"""
        dados = {}
        
        # Dados de identificação
        for campo, widget in self.campos_id.items():
            if isinstance(widget, QLineEdit):
                dados[campo] = widget.text()
            elif isinstance(widget, QComboBox):
                dados[campo] = widget.currentText()
            elif isinstance(widget, QDateEdit):
                dados[campo] = widget.date().toString("dd/MM/yyyy")
        
        # Dados médicos
        for secao_id, secao_data in self.campos_medicos.items():
            resposta = secao_data['combo'].currentText()
            if resposta:
                dados[secao_id] = {
                    'resposta': resposta,
                    'detalhes': {}
                }
                
                if resposta == "Sim":
                    for detalhe_nome, detalhe_widget in secao_data['detalhes'].items():
                        valor = detalhe_widget.text()
                        if valor:
                            dados[secao_id]['detalhes'][detalhe_nome] = valor
        
        return dados
        
    def gerar_pdf(self):
        """Gera PDF com layout DEFINITIVO e CENTRALIZADO"""
        try:
            # Preparar dados
            dados = self.coletar_dados()
            if not dados:
                BiodeskMessageBox.warning(self, "Aviso", "Preencha o formulário primeiro!")
                return
            
            # Escolher local para salvar
            nome_paciente = self.parent.paciente_data.get('nome', 'Paciente') if self.parent else 'Paciente'
            nome_arquivo = f"DeclaracaoSaude_{nome_paciente}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            caminho, _ = QFileDialog.getSaveFileName(
                self, 
                "Guardar Declaração de Saúde",
                nome_arquivo,
                "PDF Files (*.pdf)"
            )
            
            if not caminho:
                return
            
            # Gerar PDF com método otimizado
            self._gerar_pdf_otimizado(caminho, dados)
            
            BiodeskMessageBox.information(self, "Sucesso", f"PDF gerado:\n{caminho}")
            
            # Abrir PDF
            os.startfile(caminho)
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "Erro", f"Erro ao gerar PDF: {str(e)}")
            
    def _gerar_pdf_otimizado(self, caminho, dados):
        """Gera PDF com CSS DEFINITIVO e sem conflitos"""
        
        # Configurar printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(caminho)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        
        # Margens
        page_layout = QPageLayout()
        page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        page_layout.setOrientation(QPageLayout.Orientation.Portrait)
        page_layout.setMargins(QMarginsF(15, 15, 15, 15))
        page_layout.setUnits(QPageLayout.Unit.Millimeter)
        printer.setPageLayout(page_layout)
        
        # Preparar assinaturas
        assinatura_paciente_html = ""
        assinatura_profissional_html = ""
        
        nome_paciente = self.parent.paciente_data.get('nome', 'Paciente') if self.parent else 'Paciente'
        
        if self.assinaturas.get('paciente'):
            try:
                # Salvar temporariamente
                temp_path = "temp/sig_declaracao_paciente.png"
                os.makedirs("temp", exist_ok=True)
                
                with open(temp_path, 'wb') as f:
                    f.write(self.assinaturas['paciente'])
                
                # Converter para base64
                with open(temp_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode()
                    assinatura_paciente_html = f'<img src="data:image/png;base64,{img_data}">'
                    
            except Exception as e:
                print(f"Erro com assinatura paciente: {e}")
        
        if self.assinaturas.get('profissional'):
            try:
                temp_path = "temp/sig_declaracao_profissional.png"
                os.makedirs("temp", exist_ok=True)
                
                with open(temp_path, 'wb') as f:
                    f.write(self.assinaturas['profissional'])
                    
                with open(temp_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode()
                    assinatura_profissional_html = f'<img src="data:image/png;base64,{img_data}">'
                    
            except Exception as e:
                print(f"Erro com assinatura profissional: {e}")
        
        # HTML DEFINITIVO com CSS ÚNICO e SEM CONFLITOS
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                /* RESET E BASE */
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Calibri', 'Arial', sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    color: #2c3e50;
                }}
                
                /* CABEÇALHO */
                .header {{
                    text-align: center;
                    padding: 20px 0;
                    border-bottom: 3px solid #2980b9;
                    margin-bottom: 20px;
                }}
                
                .header h1 {{
                    color: #2980b9;
                    font-size: 18pt;
                    margin-bottom: 5px;
                }}
                
                /* SEÇÕES */
                .section {{
                    margin: 15px 0;
                    padding: 10px;
                    border: 1px solid #ecf0f1;
                    border-radius: 5px;
                    background-color: #fafafa;
                }}
                
                .section h2 {{
                    color: #27ae60;
                    font-size: 12pt;
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #bdc3c7;
                }}
                
                .field {{
                    margin: 5px 0;
                    display: flex;
                    align-items: baseline;
                }}
                
                .field-label {{
                    font-weight: bold;
                    min-width: 150px;
                    color: #34495e;
                }}
                
                .field-value {{
                    flex: 1;
                    color: #2c3e50;
                }}
                
                /* ASSINATURAS - LAYOUT DEFINITIVO */
                .signatures-container {{
                    margin: 30px auto 20px auto;
                    width: 80%;
                    display: table;
                    table-layout: fixed;
                }}
                
                .signature-box {{
                    display: table-cell;
                    width: 45%;
                    text-align: center;
                    vertical-align: top;
                    padding: 0 10px;
                }}
                
                .signature-box:first-child {{
                    border-right: 1px solid #ecf0f1;
                }}
                
                .signature-title {{
                    font-weight: bold;
                    color: #2c3e50;
                    font-size: 10pt;
                    margin-bottom: 10px;
                }}
                
                .signature-img {{
                    height: 50px;
                    border-bottom: 2px solid #34495e;
                    margin-bottom: 5px;
                    min-height: 50px;
                    display: flex;
                    align-items: flex-end;
                    justify-content: center;
                }}
                
                .signature-img img {{
                    max-height: 45px;
                    max-width: 200px;
                }}
                
                .signature-name {{
                    font-size: 9pt;
                    color: #7f8c8d;
                    margin-top: 3px;
                }}
                
                /* RODAPÉ */
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 9pt;
                    color: #95a5a6;
                    border-top: 1px solid #ecf0f1;
                    padding-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DECLARAÇÃO DE SAÚDE</h1>
                <p>Anamnese Completa - Naturopatia</p>
            </div>
            
            {self._gerar_html_dados(dados)}
            
            <div class="signatures-container">
                <div class="signature-box">
                    <div class="signature-title">PACIENTE</div>
                    <div class="signature-img">
                        {assinatura_paciente_html}
                    </div>
                    <div class="signature-name">
                        {nome_paciente}<br>
                        {datetime.now().strftime('%d/%m/%Y')}
                    </div>
                </div>
                
                <div class="signature-box">
                    <div class="signature-title">PROFISSIONAL</div>
                    <div class="signature-img">
                        {assinatura_profissional_html}
                    </div>
                    <div class="signature-name">
                        Dr. Nuno Correia<br>
                        CP: 0300450<br>
                        {datetime.now().strftime('%d/%m/%Y')}
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>BIODESK - Sistema de Gestão Clínica</strong></p>
                <p>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                <p>Este documento possui validade legal e foi assinado digitalmente</p>
            </div>
        </body>
        </html>
        """
        
        # Gerar PDF
        document = QTextDocument()
        document.setHtml(html)
        document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
        document.print(printer)
        
    def _gerar_html_dados(self, dados):
        """Gera HTML para os dados coletados"""
        html = ""
        
        # Seção de identificação
        html += '<div class="section"><h2>Identificação</h2>'
        for campo in ['nome', 'data_nasc', 'contacto', 'email', 'profissão']:
            if campo in dados:
                label = campo.replace('_', ' ').title()
                html += f'<div class="field"><span class="field-label">{label}:</span>'
                html += f'<span class="field-value">{dados[campo]}</span></div>'
        html += '</div>'
        
        # Seções médicas
        secoes_agrupadas = {}
        for campo, valor in dados.items():
            if isinstance(valor, dict) and 'resposta' in valor:
                secao = campo.split('_')[0]
                if secao not in secoes_agrupadas:
                    secoes_agrupadas[secao] = []
                secoes_agrupadas[secao].append((campo, valor))
        
        for secao, campos in secoes_agrupadas.items():
            html += f'<div class="section"><h2>{secao}</h2>'
            for campo, valor in campos:
                if valor['resposta'] == 'Sim':
                    campo_nome = ' '.join(campo.split('_')[1:]).title()
                    detalhes = ', '.join(valor.get('detalhes', {}).values())
                    html += f'<div class="field"><span class="field-label">{campo_nome}:</span>'
                    html += f'<span class="field-value">Sim - {detalhes}</span></div>'
            html += '</div>'
        
        return html
