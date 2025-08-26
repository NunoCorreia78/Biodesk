from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import json
import os
from biodesk_dialogs import BiodeskMessageBox
from datetime import datetime
from biodesk_ui_kit import BiodeskUIKit

# 🎨 SISTEMA DE ESTILOS CENTRALIZADO
try:
    from biodesk_styles import BiodeskStyles, ButtonType
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False

"""
Sistema de Templates Editáveis para Prescrições
Permite criar templates com campos personalizáveis e variáveis automáticas
"""

class TemplateEditavel(QDialog):
    def __init__(self, parent=None, paciente_data=None):
        super().__init__(parent)
        self.parent = parent
        self.paciente_data = paciente_data or {}
        self.template_path = None
        
        self.setWindowTitle("🔧 Editor de Template de Prescrição")
        self.setModal(True)
        self.resize(800, 600)
        
        # Aplicar estilo
        BiodeskUIKit.apply_universal_button_style(self)
        
        self.init_ui()
        self.carregar_variaveis_automaticas()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Container principal
        container = QWidget()
        container.setStyleSheet("background-color: white; border-radius: 12px; padding: 20px;")
        container_layout = QVBoxLayout(container)
        
        # Título
        titulo = QLabel("✏️ Editor de Template de Prescrição")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(titulo)
        
        # Nome do template
        nome_layout = QHBoxLayout()
        nome_layout.addWidget(QLabel("📝 Nome do Template:"))
        self.nome_template = QLineEdit()
        self.nome_template.setPlaceholderText("Ex: Prescrição Vitamínica, Protocolo Anti-inflamatório...")
        nome_layout.addWidget(self.nome_template)
        container_layout.addLayout(nome_layout)
        
        # Variáveis disponíveis
        info_variaveis = QLabel("💡 Variáveis disponíveis: {nome_paciente}, {data_atual}, {medico}")
        info_variaveis.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        container_layout.addWidget(info_variaveis)
        
        # Editor de conteúdo
        container_layout.addWidget(QLabel("📄 Conteúdo da Prescrição:"))
        self.editor_conteudo = QTextEdit()
        self.editor_conteudo.setPlaceholderText(self.get_template_exemplo())
        container_layout.addWidget(self.editor_conteudo)
        
        # Preview
        preview_group = QGroupBox("👁️ Preview com Dados do Paciente")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setMaximumHeight(150)
        self.preview_area.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6;")
        preview_layout.addWidget(self.preview_area)
        container_layout.addWidget(preview_group)
        
        # Botões
        botoes_layout = QHBoxLayout()
        
        if STYLES_AVAILABLE:
            btn_preview = BiodeskStyles.create_button("👁️ Atualizar Preview", ButtonType.NAVIGATION)
        else:
            btn_preview = QPushButton("👁️ Atualizar Preview")
        btn_preview.clicked.connect(self.atualizar_preview)
        
        if STYLES_AVAILABLE:
            btn_salvar = BiodeskStyles.create_button("💾 Salvar Template", ButtonType.SAVE)
        else:
            btn_salvar = QPushButton("💾 Salvar Template")
        btn_salvar.clicked.connect(self.salvar_template)
        
        if STYLES_AVAILABLE:
            btn_pdf = BiodeskStyles.create_button("📄 Gerar PDF", ButtonType.NAVIGATION)
        else:
            btn_pdf = QPushButton("📄 Gerar PDF")
        btn_pdf.clicked.connect(self.gerar_pdf)
        
        if STYLES_AVAILABLE:
            btn_cancelar = BiodeskStyles.create_button("❌ Cancelar", ButtonType.DEFAULT)
        else:
            btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        botoes_layout.addWidget(btn_preview)
        botoes_layout.addWidget(btn_salvar)
        botoes_layout.addWidget(btn_pdf)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_cancelar)
        
        container_layout.addLayout(botoes_layout)
        layout.addWidget(container)
        
        # Conectar mudanças para preview automático
        self.editor_conteudo.textChanged.connect(self.atualizar_preview)
        self.nome_template.textChanged.connect(self.atualizar_preview)
    
    def get_template_exemplo(self):
        return """PRESCRIÇÃO MÉDICA

Paciente: {nome_paciente}
Data: {data_atual}
Médico: {medico}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROTOCOLO TERAPÊUTICO:

🔸 Suplemento A
   • Dosagem: 1 cápsula/dia
   • Horário: Manhã, com pequeno-almoço
   • Duração: 30 dias

🔸 Suplemento B
   • Dosagem: 2 comprimidos/dia
   • Horário: Almoço e jantar
   • Duração: 60 dias

ORIENTAÇÕES GERAIS:
• Manter hidratação adequada (2L água/dia)
• Evitar álcool durante o tratamento
• Retorno em 30 dias para reavaliação

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dr. {medico}
Medicina Integrativa
"""
    
    def carregar_variaveis_automaticas(self):
        """Carrega as variáveis que serão substituídas automaticamente"""
        self.variaveis = {
            'nome_paciente': self.paciente_data.get('nome', '[Nome do Paciente]'),
            'data_atual': datetime.now().strftime('%d/%m/%Y'),
            'medico': 'Dr. Nuno Correia'
        }
    
    def atualizar_preview(self):
        """Atualiza o preview com as variáveis substituídas"""
        conteudo = self.editor_conteudo.toPlainText()
        
        # Substituir variáveis
        preview = conteudo
        for variavel, valor in self.variaveis.items():
            preview = preview.replace(f'{{{variavel}}}', valor)
        
        self.preview_area.setPlainText(preview)
    
    def salvar_template(self):
        """Salva o template editável"""
        nome = self.nome_template.text().strip()
        conteudo = self.editor_conteudo.toPlainText().strip()
        
        if not nome or not conteudo:
            BiodeskMessageBox.warning(self, "⚠️ Aviso", "Por favor, preencha o nome e conteúdo do template.")
            return
        
        # Salvar no diretório de templates
        templates_dir = "templates/suplementos"
        os.makedirs(templates_dir, exist_ok=True)
        
        # Nome do arquivo
        nome_arquivo = nome.replace(' ', '_').lower() + '.txt'
        caminho_arquivo = os.path.join(templates_dir, nome_arquivo)
        
        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            # Atualizar também o JSON para compatibilidade
            self.atualizar_json_templates(nome, conteudo)
            
            BiodeskMessageBox.information(self, "✅ Sucesso", 
                                  f"Template '{nome}' salvo com sucesso!\n\n"
                                  f"Arquivo: {caminho_arquivo}")
            
            # Atualizar a interface principal se existir
            if hasattr(self.parent, 'carregar_templates_categoria'):
                self.parent.carregar_templates_categoria('suplementos')
            
            self.accept()
            
        except Exception as e:
            BiodeskMessageBox.critical(self, "❌ Erro", f"Erro ao salvar template:\n{e}")
    
    def atualizar_json_templates(self, nome, conteudo):
        """Atualiza o arquivo JSON para compatibilidade"""
        json_path = "templates/suplementos.json"
        
        try:
            # Carregar templates existentes
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            else:
                templates = []
            
            # Adicionar ou atualizar template
            template_existente = None
            for i, template in enumerate(templates):
                if template['nome'] == nome:
                    template_existente = i
                    break
            
            novo_template = {
                "nome": nome,
                "texto": conteudo
            }
            
            if template_existente is not None:
                templates[template_existente] = novo_template
            else:
                templates.append(novo_template)
            
            # Salvar de volta
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Aviso: Erro ao atualizar JSON: {e}")
    
    def gerar_pdf(self):
        """Gera PDF do template com dados do paciente"""
        if not self.editor_conteudo.toPlainText().strip():
            BiodeskMessageBox.warning(self, "⚠️ Aviso", "Por favor, adicione conteúdo ao template.")
            return
        
        try:
            # Conteúdo com variáveis substituídas
            conteudo = self.preview_area.toPlainText()
            
            # Gerar PDF usando o sistema existente
            if hasattr(self.parent, 'gerar_pdf_template_personalizado'):
                pdf_path = self.parent.gerar_pdf_template_personalizado(
                    titulo=self.nome_template.text() or "Prescrição",
                    conteudo=conteudo
                )
                
                BiodeskMessageBox.information(self, "✅ PDF Gerado", 
                                      f"PDF criado com sucesso!\n\n{pdf_path}")
            else:
                BiodeskMessageBox.information(self, "ℹ️ Info", 
                                      "Funcionalidade de PDF será implementada na próxima versão.")
                
        except Exception as e:
            BiodeskMessageBox.critical(self, "❌ Erro", f"Erro ao gerar PDF:\n{e}")

def abrir_editor_template(parent=None, paciente_data=None):
    """Função para abrir o editor de template"""
    editor = TemplateEditavel(parent, paciente_data)
    return editor.exec()
