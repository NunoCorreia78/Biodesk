"""
🩺 MÓDULO: Declaração de Saúde - Interface Profissional
Sistema completo para criação e assinatura de declarações de saúde.

Funcionalidades:
- ✅ Interface profissional e limpa
- ✅ Formulário estruturado por seções
- ✅ Sistema de assinatura integrado
- ✅ Geração PDF com formatação profissional
- ✅ Integração com gestor de documentos
- ✅ Tracking de alterações e versões
- ✅ Status visual de preenchimento
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
                             QPushButton, QTextEdit, QScrollArea, QLineEdit, QComboBox, QFormLayout,
                             QGroupBox, QGridLayout, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Importar componentes do Biodesk
from biodesk_dialogs import BiodeskMessageBox

# ✅ SISTEMA NOVO: BiodeskStyles v2.0 - Estilos centralizados
try:
    from biodesk_styles import BiodeskStyles, ButtonType
    BIODESK_STYLES_AVAILABLE = True
    print("✅ BiodeskStyles v2.0 carregado no declaracao_saude.py")
except ImportError as e:
    BIODESK_STYLES_AVAILABLE = False
    print(f"⚠️ BiodeskStyles não disponível em declaracao_saude.py: {e}")

from biodesk_ui_kit import BiodeskUIKit
from biodesk_dialogs import mostrar_erro, mostrar_sucesso, mostrar_aviso

# Importar sistema de assinatura de forma segura
try:
    from sistema_assinatura import abrir_dialogo_assinatura
    SISTEMA_ASSINATURA_DISPONIVEL = True
except ImportError:
    print("⚠️ Sistema de assinatura não disponível")
    SISTEMA_ASSINATURA_DISPONIVEL = False
    
    def abrir_dialogo_assinatura(parent, titulo, dados_paciente):
        """Fallback quando sistema de assinatura não está disponível"""
        from biodesk_dialogs import mostrar_aviso
        mostrar_aviso(parent, "Sistema Indisponível", 
                     "⚠️ Sistema de assinatura não está disponível.\n\n"
                     "PDF será gerado sem assinaturas.")
        return None

class DeclaracaoSaudeWidget(QWidget):
    """
    Widget profissional para declaração de saúde
    """
    # Sinais
    declaracao_assinada = pyqtSignal(dict)
    dados_atualizados = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.paciente_data = None
        
        # Tracking de alterações
        self._dados_originais = None
        self._primeira_criacao = None
        self._ultima_alteracao = None
        self._foi_assinado = False
        self._alterado = False
        
        self.init_ui()
        # self._conectar_sinais_alteracao()  # TODO: Implementar se necessário
        
    def init_ui(self):
        """Interface profissional com design limpo e compacto"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)  # Margens reduzidas
        layout.setSpacing(15)  # Espaçamento reduzido
        
        # ❌ BARRA AZUL REMOVIDA - economizar espaço
        
        # Layout principal horizontal: 75% formulário + 25% botões/status
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(15)  # Espaçamento reduzido
        
        # ÁREA ESQUERDA (75%): Formulário com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(600)  # Garantir largura mínima
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #f1f1f1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        formulario_widget = self._criar_formulario_profissional()
        scroll.setWidget(formulario_widget)
        main_horizontal_layout.addWidget(scroll, 3)  # 75% do espaço
        
        # ÁREA DIREITA (25%): Botões e status verticalmente
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(12)  # Espaçamento reduzido
        
        # Botões principais (verticalmente) - ESTILO BIODESK
        botoes_widget = self._criar_botoes_sidebar_biodesk()
        sidebar_layout.addWidget(botoes_widget)
        
        # Widget de status compacto
        status_widget = self._criar_widget_status_compacto()
        sidebar_layout.addWidget(status_widget)
        
        # Barra de progresso
        progress_widget = self._criar_barra_progresso()
        sidebar_layout.addWidget(progress_widget)
        
        # Espaçador para empurrar tudo para cima
        sidebar_layout.addStretch()
        
        # Container para a sidebar
        sidebar_container = QWidget()
        sidebar_container.setLayout(sidebar_layout)
        sidebar_container.setFixedWidth(280)  # Largura reduzida
        
        main_horizontal_layout.addWidget(sidebar_container, 1)  # 25% do espaço
        
        # Adicionar o layout horizontal ao layout principal
        layout.addLayout(main_horizontal_layout)
    
    def _criar_botoes_sidebar_biodesk(self):
        """Cria botões da sidebar com estilo Biodesk profissional"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(18)  # Aumentado para mais espaço entre botões
        
        # Botão Assinar e Guardar - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            btn_assinar = BiodeskStyles.create_button("📝 Assinar e Guardar", ButtonType.SAVE)
        else:
            btn_assinar = QPushButton("📝 Assinar e Guardar")
        btn_assinar.clicked.connect(self.assinar_e_guardar)
        layout.addWidget(btn_assinar)
        
        # Espaçamento extra
        layout.addSpacing(6)
        
        # Botão Guardar Rascunho - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            btn_rascunho = BiodeskStyles.create_button("💾 Guardar Rascunho", ButtonType.DRAFT)
        else:
            btn_rascunho = QPushButton("💾 Guardar Rascunho")
        btn_rascunho.clicked.connect(self.guardar_rascunho)
        layout.addWidget(btn_rascunho)
        
        # Espaçamento extra
        layout.addSpacing(6)
        
        # Botão Limpar - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            btn_limpar = BiodeskStyles.create_button("🗑️ Limpar Formulário", ButtonType.DELETE)
        else:
            btn_limpar = QPushButton("🗑️ Limpar Formulário")
        btn_limpar.clicked.connect(self.limpar_formulario)
        layout.addWidget(btn_limpar)
        
        # Espaçamento extra
        layout.addSpacing(6)
        
        # Botão Navegação Rápida - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            btn_navegacao = BiodeskStyles.create_button("🧭 Navegação Rápida", ButtonType.NAVIGATION)
        else:
            btn_navegacao = QPushButton("🧭 Navegação Rápida")
        # ✨ Estilo aplicado automaticamente pelo BiodeskStyleManager (tema WARNING)
        btn_navegacao.clicked.connect(self.abrir_navegacao_rapida)
        layout.addWidget(btn_navegacao)
        
        return container
    
    def _criar_widget_status_compacto(self):
        """Cria widget de status compacto"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        
        # ❌ REMOVIDO: Status "Não Preenchida" conforme solicitado
        # ❌ REMOVIDO: Data label "--/--/----" conforme solicitado
        
        return frame
    
    def _criar_barra_progresso(self):
        """Cria barra de progresso visual"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        
        # Título
        titulo = QLabel("📊 Progresso")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(titulo)
        
        # Barra de progresso
        from PyQt6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #f8f9fa;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 3px;
            }
        """)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Contador de campos
        self.contador_label = QLabel("0/0 campos preenchidos")
        self.contador_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #6c757d;
                text-align: center;
            }
        """)
        self.contador_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.contador_label)
        
        return frame

    def _criar_formulario_profissional(self):
        """Cria formulário completo da declaração de saúde - VERSÃO COMPACTA"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)  # Espaçamento reduzido
        
        # Instruções rápidas - COMPACTAS
        instrucoes = QLabel("📋 <b>Instruções:</b> Campos [Sim/Não] obrigatórios. Se Sim → preencha Detalhe. Campos (obrigatório) devem estar preenchidos antes da assinatura.")
        instrucoes.setWordWrap(True)
        instrucoes.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: #1976d2;
            }
        """)
        layout.addWidget(instrucoes)
        
        # Seção Identificação - COMPACTA
        self._criar_secao_identificacao_compacta(layout)
        
        # Seções médicas - COMPACTAS
        self._criar_secao_metabolicas_compacta(layout)
        self._criar_secao_cardiovasculares_compacta(layout)
        self._criar_secao_respiratorias_compacta(layout)
        self._criar_secao_gastrointestinais_compacta(layout)
        self._criar_secao_neurologicas_compacta(layout)
        self._criar_secao_musculoesqueleticas_compacta(layout)
        self._criar_secao_dermatologia_compacta(layout)
        self._criar_secao_alergias_compacta(layout)
        self._criar_secao_infecciosas_compacta(layout)
        self._criar_secao_oncologia_compacta(layout)
        self._criar_secao_reprodutiva_compacta(layout)
        self._criar_secao_cirurgias_compacta(layout)
        self._criar_secao_implantes_compacta(layout)
        self._criar_secao_medicacao_compacta(layout)
        self._criar_secao_estilo_vida_compacta(layout)
        self._criar_secao_exames_compacta(layout)
        self._criar_secao_red_flags_compacta(layout)
        self._criar_secao_outras_questoes_compacta(layout)
        self._criar_secao_preferencias_compacta(layout)
        self._criar_secao_consentimentos_compacta(layout)
        
        return widget
    
    # ====== MÉTODOS COMPACTOS - NOVA IMPLEMENTAÇÃO ======
    
    def _criar_secao_identificacao_compacta(self, layout):
        """Cria seção de identificação COMPLETA baseada no formulário real"""
        secao = self._criar_secao_profissional_compacta("👤 Identificação do Paciente", "#667eea")
        form = QFormLayout()
        
        # Nome completo - readonly (vem dos dados do paciente)
        self.nome_edit = QLineEdit()
        self.nome_edit.setReadOnly(True)
        self.nome_edit.setStyleSheet(self._estilo_campo_readonly_compacto())
        form.addRow("Nome completo (obrigatório):", self.nome_edit)
        
        # Data nascimento - readonly
        self.data_nasc_edit = QLineEdit()
        self.data_nasc_edit.setReadOnly(True)
        self.data_nasc_edit.setStyleSheet(self._estilo_campo_readonly_compacto())
        form.addRow("Data nascimento:", self.data_nasc_edit)
        
        # Contacto telemóvel
        self.contacto_telem = QLineEdit()
        self.contacto_telem.setPlaceholderText("Ex: 964 860 387")
        self.contacto_telem.setStyleSheet(self._estilo_campo_compacto())
        form.addRow("Contacto telemóvel:", self.contacto_telem)
        
        # Email
        self.email = QLineEdit()
        self.email.setPlaceholderText("exemplo@email.com")
        self.email.setStyleSheet(self._estilo_campo_compacto())
        form.addRow("Email:", self.email)
        
        # Profissão
        self.profissao_edit = QLineEdit()
        self.profissao_edit.setPlaceholderText("Ex: Enfermeiro, Professor, Reformado...")
        self.profissao_edit.setStyleSheet(self._estilo_campo_compacto())
        form.addRow("Profissão:", self.profissao_edit)
        
        # Esforço físico na profissão
        esforco_layout = QHBoxLayout()
        self.profissao_combo = QComboBox()
        self.profissao_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.profissao_combo.setStyleSheet(self._estilo_campo_compacto())
        self.profissao_detalhe = QLineEdit()
        self.profissao_detalhe.setPlaceholderText("Descreva o tipo de esforço físico...")
        self.profissao_detalhe.setStyleSheet(self._estilo_campo_compacto())
        esforco_layout.addWidget(self.profissao_combo, 1)
        esforco_layout.addWidget(self.profissao_detalhe, 2)
        form.addRow("Esforço físico na profissão:", esforco_layout)
        
        # ❌ CAMPO CONTACTO DE EMERGÊNCIA REMOVIDO CONFORME SOLICITADO
        
        # Motivo da consulta - área de texto maior
        self.motivo_consulta = QTextEdit()
        self.motivo_consulta.setMaximumHeight(80)  # Altura aumentada
        self.motivo_consulta.setPlaceholderText("Descreva o motivo principal da consulta...")
        self.motivo_consulta.setStyleSheet(self._estilo_campo_compacto())
        form.addRow("Motivo da consulta:", self.motivo_consulta)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_profissional_compacta(self, titulo, cor):
        """Cria seção profissional COMPACTA"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {cor};
                border-radius: 6px;
                margin: 8px 0px;
                padding: 0px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        
        # Título compacto
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(f"""
            QLabel {{
                color: {cor};
                font-size: 15px;
                font-weight: bold;
                padding: 6px 0px;
                margin: 0px;
            }}
        """)
        layout.addWidget(titulo_label)
        
        return frame
    
    def _estilo_campo_compacto(self):
        """Estilo para campos compactos"""
        return """
            QLineEdit, QComboBox {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
                min-height: 24px;
                max-height: 32px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #007bff;
            }
            QTextEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #007bff;
            }
        """
    
    def _estilo_campo_readonly_compacto(self):
        """Estilo para campos readonly compactos"""
        return """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-size: 13px;
                background-color: #f8f9fa;
                color: #6c757d;
                min-height: 24px;
                max-height: 32px;
            }
        """
        
        # Seção 2: Cardiovasculares
        self._criar_secao_cardiovasculares(layout)
        
        # Seção 3: Respiratórias
        self._criar_secao_respiratorias(layout)
        
        # Seção 4: Gastrointestinais
        self._criar_secao_gastrointestinais(layout)
        
        # Seção 5: Neurológicas / Psiquiátricas
        self._criar_secao_neurologicas(layout)
        
        # Seção 6: Músculo-esqueléticas
        self._criar_secao_musculoesqueleticas(layout)
        
        # Seção 7: Dermatologia / Feridas
        self._criar_secao_dermatologia(layout)
        
        # Seção 8: Alergias / Intolerâncias
        self._criar_secao_alergias(layout)
        
        # Seção 9: Infecciosas / Imunológicas
        self._criar_secao_infecciosas(layout)
        
        # Seção 10: Oncologia
        self._criar_secao_oncologia(layout)
        
        # Seção 11: Saúde Reprodutiva
        self._criar_secao_reprodutiva(layout)
        
        # Seção 12: Cirurgias / Internamentos / Traumas
        self._criar_secao_cirurgias(layout)
        
        # Seção 13: Implantes e Dispositivos
        self._criar_secao_implantes(layout)
        
        # Seção 14: Medicação e Suplementos
        self._criar_secao_medicacao(layout)
        
        # Seção 15: Estilo de Vida
        self._criar_secao_estilo_vida(layout)
        
        # Seção 16: Exames/Diagnósticos recentes
        self._criar_secao_exames(layout)
        
        # Seção 17: Red Flags atuais
        self._criar_secao_red_flags(layout)
        
        # Seção 18: Preferências / Limites de Tratamento
        self._criar_secao_preferencias(layout)
        
        # Seção de Consentimentos
        self._criar_secao_consentimentos(layout)
        
        return widget
    
    def _criar_secao_infecciosas(self, layout):
        """Cria seção 9: Infecciosas / Imunológicas"""
        secao = self._criar_secao_profissional("🦠 9) Infecciosas / Imunológicas", "#ff5722")
        form = QGridLayout()
        
        # Autoimunes
        form.addWidget(QLabel("Autoimunes (LES, AR, psoríase, tiroidite, etc.):"), 0, 0)
        self.autoimunes_combo = QComboBox()
        self.autoimunes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.autoimunes_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.autoimunes_combo, 0, 1)
        
        form.addWidget(QLabel("→ Fase/terapia:"), 1, 0)
        self.autoimunes_detalhe = QLineEdit()
        self.autoimunes_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.autoimunes_detalhe, 1, 1)
        
        # HIV / Hepatites / Tuberculose
        form.addWidget(QLabel("HIV / Hepatites / Tuberculose:"), 2, 0)
        self.hiv_hepatites_combo = QComboBox()
        self.hiv_hepatites_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.hiv_hepatites_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.hiv_hepatites_combo, 2, 1)
        
        form.addWidget(QLabel("→ Carga viral/estado:"), 3, 0)
        self.hiv_hepatites_detalhe = QLineEdit()
        self.hiv_hepatites_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.hiv_hepatites_detalhe, 3, 1)
        
        # Febre inexplicada / perda de peso / sudorese noturna
        form.addWidget(QLabel("Febre inexplicada / perda de peso / sudorese noturna (últ. 3 meses):"), 4, 0)
        self.febre_perda_peso_combo = QComboBox()
        self.febre_perda_peso_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.febre_perda_peso_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.febre_perda_peso_combo, 4, 1)
        
        form.addWidget(QLabel("→ Detalhe:"), 5, 0)
        self.febre_perda_peso_detalhe = QLineEdit()
        self.febre_perda_peso_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.febre_perda_peso_detalhe, 5, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_oncologia(self, layout):
        """Cria seção 10: Oncologia"""
        secao = self._criar_secao_profissional("🎗️ 10) Oncologia", "#673ab7")
        form = QGridLayout()
        
        # Cancro atual ou passado
        form.addWidget(QLabel("Cancro atual ou passado:"), 0, 0)
        self.cancro_combo = QComboBox()
        self.cancro_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.cancro_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.cancro_combo, 0, 1)
        
        form.addWidget(QLabel("→ Tipo, estadiamento, terapias, data:"), 1, 0)
        self.cancro_detalhe = QLineEdit()
        self.cancro_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.cancro_detalhe, 1, 1)
        
        # Tratamento oncológico ativo
        form.addWidget(QLabel("Tratamento oncológico ativo (quimio/RT/imuno):"), 2, 0)
        self.tratamento_oncologico_combo = QComboBox()
        self.tratamento_oncologico_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.tratamento_oncologico_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.tratamento_oncologico_combo, 2, 1)
        
        form.addWidget(QLabel("→ Detalhe:"), 3, 0)
        self.tratamento_oncologico_detalhe = QLineEdit()
        self.tratamento_oncologico_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.tratamento_oncologico_detalhe, 3, 1)
        
        # Linfedema / gânglios removidos
        form.addWidget(QLabel("Linfedema / gânglios removidos:"), 4, 0)
        self.linfedema_combo = QComboBox()
        self.linfedema_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.linfedema_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.linfedema_combo, 4, 1)
        
        form.addWidget(QLabel("→ Lado:"), 5, 0)
        self.linfedema_detalhe = QLineEdit()
        self.linfedema_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.linfedema_detalhe, 5, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_reprodutiva(self, layout):
        """Cria seção 11: Saúde Reprodutiva"""
        secao = self._criar_secao_profissional("👶 11) Saúde Reprodutiva", "#e91e63")
        form = QGridLayout()
        
        # Gravidez
        form.addWidget(QLabel("Gravidez:"), 0, 0)
        self.gravidez_combo = QComboBox()
        self.gravidez_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.gravidez_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.gravidez_combo, 0, 1)
        
        form.addWidget(QLabel("→ Semana • Risco?"), 1, 0)
        self.gravidez_detalhe = QLineEdit()
        self.gravidez_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.gravidez_detalhe, 1, 1)
        
        # Amamentação
        form.addWidget(QLabel("Amamentação:"), 2, 0)
        self.amamentacao_combo = QComboBox()
        self.amamentacao_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.amamentacao_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.amamentacao_combo, 2, 1)
        
        # Perturbações ginecológicas/urológicas
        form.addWidget(QLabel("Perturbações ginecológicas/urológicas:"), 3, 0)
        self.gineco_urologicas_combo = QComboBox()
        self.gineco_urologicas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.gineco_urologicas_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.gineco_urologicas_combo, 3, 1)
        
        form.addWidget(QLabel("→ Detalhe:"), 4, 0)
        self.gineco_urologicas_detalhe = QLineEdit()
        self.gineco_urologicas_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.gineco_urologicas_detalhe, 4, 1)
        
        # Dispositivo intrauterino/implantes
        form.addWidget(QLabel("Dispositivo intrauterino/implantes:"), 5, 0)
        self.dispositivo_intrauterino_combo = QComboBox()
        self.dispositivo_intrauterino_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dispositivo_intrauterino_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.dispositivo_intrauterino_combo, 5, 1)
        
        form.addWidget(QLabel("→ Tipo/data:"), 6, 0)
        self.dispositivo_intrauterino_detalhe = QLineEdit()
        self.dispositivo_intrauterino_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.dispositivo_intrauterino_detalhe, 6, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_cirurgias(self, layout):
        """Cria seção 12: Cirurgias / Internamentos / Traumas"""
        secao = self._criar_secao_profissional("🏥 12) Cirurgias / Internamentos / Traumas", "#455a64")
        form = QGridLayout()
        
        # Cirurgias
        form.addWidget(QLabel("Cirurgias:"), 0, 0)
        self.cirurgias_combo = QComboBox()
        self.cirurgias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.cirurgias_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.cirurgias_combo, 0, 1)
        
        form.addWidget(QLabel("→ Tipo, data, complicações:"), 1, 0)
        self.cirurgias_detalhe = QLineEdit()
        self.cirurgias_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.cirurgias_detalhe, 1, 1)
        
        # Internamentos relevantes
        form.addWidget(QLabel("Internamentos relevantes:"), 2, 0)
        self.internamentos_combo = QComboBox()
        self.internamentos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.internamentos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.internamentos_combo, 2, 1)
        
        form.addWidget(QLabel("→ Motivo, data:"), 3, 0)
        self.internamentos_detalhe = QLineEdit()
        self.internamentos_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.internamentos_detalhe, 3, 1)
        
        # Acidentes/traumatismos graves
        form.addWidget(QLabel("Acidentes/traumatismos graves (quedas altura/colisões):"), 4, 0)
        self.acidentes_combo = QComboBox()
        self.acidentes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.acidentes_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.acidentes_combo, 4, 1)
        
        form.addWidget(QLabel("→ Data/lesões:"), 5, 0)
        self.acidentes_detalhe = QLineEdit()
        self.acidentes_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.acidentes_detalhe, 5, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_implantes(self, layout):
        """Cria seção 13: Implantes e Dispositivos"""
        secao = self._criar_secao_profissional("⚙️ 13) Implantes e Dispositivos", "#3f51b5")
        form = QGridLayout()
        
        # Marcapasso/DAI/neuroestimulador/cochlear/bomba insulina
        form.addWidget(QLabel("Marcapasso/DAI/neuroestimulador/cochlear/bomba insulina:"), 0, 0)
        self.dispositivos_eletronicos_combo = QComboBox()
        self.dispositivos_eletronicos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dispositivos_eletronicos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.dispositivos_eletronicos_combo, 0, 1)
        
        form.addWidget(QLabel("→ Tipo, marca, data:"), 1, 0)
        self.dispositivos_eletronicos_detalhe = QLineEdit()
        self.dispositivos_eletronicos_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.dispositivos_eletronicos_detalhe, 1, 1)
        
        # Implantes metálicos
        form.addWidget(QLabel("Implantes metálicos (próteses/placas/parafusos):"), 2, 0)
        self.implantes_metalicos_combo = QComboBox()
        self.implantes_metalicos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.implantes_metalicos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.implantes_metalicos_combo, 2, 1)
        
        form.addWidget(QLabel("→ Local:"), 3, 0)
        self.implantes_metalicos_detalhe = QLineEdit()
        self.implantes_metalicos_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.implantes_metalicos_detalhe, 3, 1)
        
        # Tatuagens recentes
        form.addWidget(QLabel("Tatuagens recentes (< 6 semanas) na zona a tratar:"), 4, 0)
        self.tatuagens_combo = QComboBox()
        self.tatuagens_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.tatuagens_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.tatuagens_combo, 4, 1)
        
        form.addWidget(QLabel("→ Local:"), 5, 0)
        self.tatuagens_detalhe = QLineEdit()
        self.tatuagens_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.tatuagens_detalhe, 5, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_medicacao(self, layout):
        """Cria seção 14: Medicação e Suplementos"""
        secao = self._criar_secao_profissional("💊 14) Medicação e Suplementos", "#e53935")
        form = QGridLayout()
        
        # Anticoagulantes/antiagregantes
        form.addWidget(QLabel("Anticoagulantes/antiagregantes (varfarina, DOACs, AAS, clopidogrel):"), 0, 0)
        self.anticoagulantes_combo = QComboBox()
        self.anticoagulantes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.anticoagulantes_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.anticoagulantes_combo, 0, 1)
        
        form.addWidget(QLabel("→ Nome/dose • INR alvo (se aplicável):"), 1, 0)
        self.anticoagulantes_detalhe = QLineEdit()
        self.anticoagulantes_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.anticoagulantes_detalhe, 1, 1)
        
        # Imunossupressores/biológicos/corticoides crónicos
        form.addWidget(QLabel("Imunossupressores/biológicos/corticoides crónicos:"), 2, 0)
        self.imunossupressores_combo = QComboBox()
        self.imunossupressores_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.imunossupressores_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.imunossupressores_combo, 2, 1)
        
        form.addWidget(QLabel("→ Nome/dose:"), 3, 0)
        self.imunossupressores_detalhe = QLineEdit()
        self.imunossupressores_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.imunossupressores_detalhe, 3, 1)
        
        # Antidiabéticos/insulina
        form.addWidget(QLabel("Antidiabéticos/insulina:"), 4, 0)
        self.antidiabeticos_combo = QComboBox()
        self.antidiabeticos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.antidiabeticos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.antidiabeticos_combo, 4, 1)
        
        form.addWidget(QLabel("→ Regime:"), 5, 0)
        self.antidiabeticos_detalhe = QLineEdit()
        self.antidiabeticos_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.antidiabeticos_detalhe, 5, 1)
        
        # Psicotrópicos
        form.addWidget(QLabel("Psicotrópicos (ansiolíticos/antidepressivos/estabilizadores):"), 6, 0)
        self.psicotropicos_combo = QComboBox()
        self.psicotropicos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.psicotropicos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.psicotropicos_combo, 6, 1)
        
        # Fotossensibilizantes
        form.addWidget(QLabel("Fotossensibilizantes (doxiciclina/isotretinoína/tiazidas):"), 7, 0)
        self.fotossensibilizantes_combo = QComboBox()
        self.fotossensibilizantes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.fotossensibilizantes_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.fotossensibilizantes_combo, 7, 1)
        
        # Bifosfonatos/denosumab
        form.addWidget(QLabel("Bifosfonatos/denosumab:"), 8, 0)
        self.bifosfonatos_combo = QComboBox()
        self.bifosfonatos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.bifosfonatos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.bifosfonatos_combo, 8, 1)
        
        form.addWidget(QLabel("→ Tempo de uso:"), 9, 0)
        self.bifosfonatos_detalhe = QLineEdit()
        self.bifosfonatos_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.bifosfonatos_detalhe, 9, 1)
        
        # Suplementos/fitoterapia em curso
        form.addWidget(QLabel("Suplementos/fitoterapia em curso:"), 10, 0)
        self.suplementos_combo = QComboBox()
        self.suplementos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.suplementos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.suplementos_combo, 10, 1)
        
        form.addWidget(QLabel("→ Nome, dose, marca, horário:"), 11, 0)
        self.suplementos_detalhe = QLineEdit()
        self.suplementos_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.suplementos_detalhe, 11, 1)
        
        # Reações prévias a suplementos/plantas/mesoterapia
        form.addWidget(QLabel("Reações prévias a suplementos/plantas/mesoterapia:"), 12, 0)
        self.reacoes_previas_combo = QComboBox()
        self.reacoes_previas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.reacoes_previas_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.reacoes_previas_combo, 12, 1)
        
        form.addWidget(QLabel("→ Descrever:"), 13, 0)
        self.reacoes_previas_detalhe = QLineEdit()
        self.reacoes_previas_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.reacoes_previas_detalhe, 13, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_estilo_vida(self, layout):
        """Cria seção 15: Estilo de Vida"""
        secao = self._criar_secao_profissional("🌱 15) Estilo de Vida", "#689f38")
        form = QGridLayout()
        
        # Tabaco
        form.addWidget(QLabel("Tabaco:"), 0, 0)
        self.tabaco_combo = QComboBox()
        self.tabaco_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.tabaco_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.tabaco_combo, 0, 1)
        
        form.addWidget(QLabel("→ Maços-ano:"), 1, 0)
        self.tabaco_detalhe = QLineEdit()
        self.tabaco_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.tabaco_detalhe, 1, 1)
        
        # Álcool
        form.addWidget(QLabel("Álcool:"), 2, 0)
        self.alcool_combo = QComboBox()
        self.alcool_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alcool_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.alcool_combo, 2, 1)
        
        form.addWidget(QLabel("→ Frequência/quantidade:"), 3, 0)
        self.alcool_detalhe = QLineEdit()
        self.alcool_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.alcool_detalhe, 3, 1)
        
        # Drogas recreativas
        form.addWidget(QLabel("Drogas recreativas:"), 4, 0)
        self.drogas_combo = QComboBox()
        self.drogas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.drogas_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.drogas_combo, 4, 1)
        
        form.addWidget(QLabel("→ Quais:"), 5, 0)
        self.drogas_detalhe = QLineEdit()
        self.drogas_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.drogas_detalhe, 5, 1)
        
        # Atividade física
        form.addWidget(QLabel("Atividade física:"), 6, 0)
        self.atividade_fisica_combo = QComboBox()
        self.atividade_fisica_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.atividade_fisica_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.atividade_fisica_combo, 6, 1)
        
        form.addWidget(QLabel("→ Tipo/frequência:"), 7, 0)
        self.atividade_fisica_detalhe = QLineEdit()
        self.atividade_fisica_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.atividade_fisica_detalhe, 7, 1)
        
        # Sono
        form.addWidget(QLabel("Sono:"), 8, 0)
        self.sono_combo = QComboBox()
        self.sono_combo.addItems(["Selecionar...", "Bom", "Mau"])
        self.sono_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.sono_combo, 8, 1)
        
        form.addWidget(QLabel("→ Horas/noite:"), 9, 0)
        self.sono_detalhe = QLineEdit()
        self.sono_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.sono_detalhe, 9, 1)
        
        # Stress elevado
        form.addWidget(QLabel("Stress elevado (0–10):"), 10, 0)
        self.stress_combo = QComboBox()
        stress_opcoes = ["Selecionar..."] + [str(i) for i in range(11)]
        self.stress_combo.addItems(stress_opcoes)
        self.stress_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.stress_combo, 10, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_exames(self, layout):
        """Cria seção 16: Exames/Diagnósticos recentes"""
        secao = self._criar_secao_profissional("🔬 16) Exames/Diagnósticos recentes (≤ 12 meses)", "#795548")
        form = QGridLayout()
        
        # RM/TC/Ecografias/Análises relevantes
        form.addWidget(QLabel("RM/TC/Ecografias/Análises relevantes:"), 0, 0)
        self.exames_combo = QComboBox()
        self.exames_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.exames_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.exames_combo, 0, 1)
        
        form.addWidget(QLabel("→ Quais e datas (anexar se possível):"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.exames_detalhe = QTextEdit()
        self.exames_detalhe.setMaximumHeight(80)
        self.exames_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.exames_detalhe, 1, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_red_flags(self, layout):
        """Cria seção 17: Red Flags atuais"""
        secao = self._criar_secao_profissional("🚨 17) Red Flags atuais (triagem clínica)", "#d32f2f")
        form = QGridLayout()
        
        # Dor noturna progressiva
        form.addWidget(QLabel("Dor noturna progressiva:"), 0, 0)
        self.dor_noturna_combo = QComboBox()
        self.dor_noturna_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dor_noturna_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.dor_noturna_combo, 0, 1)
        
        # Défices neurológicos novos
        form.addWidget(QLabel("Défices neurológicos novos (força/sensibilidade):"), 1, 0)
        self.defices_neurologicos_combo = QComboBox()
        self.defices_neurologicos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.defices_neurologicos_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.defices_neurologicos_combo, 1, 1)
        
        # Incontinência urinária/fecal recente
        form.addWidget(QLabel("Incontinência urinária/fecal recente:"), 2, 0)
        self.incontinencia_combo = QComboBox()
        self.incontinencia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.incontinencia_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.incontinencia_combo, 2, 1)
        
        # Febre > 38ºC sem causa
        form.addWidget(QLabel("Febre > 38ºC sem causa:"), 3, 0)
        self.febre_sem_causa_combo = QComboBox()
        self.febre_sem_causa_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.febre_sem_causa_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.febre_sem_causa_combo, 3, 1)
        
        # Perda de peso > 5% em 3 meses
        form.addWidget(QLabel("Perda de peso > 5% em 3 meses:"), 4, 0)
        self.perda_peso_combo = QComboBox()
        self.perda_peso_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.perda_peso_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.perda_peso_combo, 4, 1)
        
        # Se algum "Sim": descrever brevemente
        form.addWidget(QLabel("→ Se algum \"Sim\": descrever brevemente:"), 5, 0, Qt.AlignmentFlag.AlignTop)
        self.red_flags_detalhe = QTextEdit()
        self.red_flags_detalhe.setMaximumHeight(80)
        self.red_flags_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.red_flags_detalhe, 5, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_preferencias(self, layout):
        """Cria seção 18: Preferências / Limites de Tratamento"""
        secao = self._criar_secao_profissional("⚙️ 18) Preferências / Limites de Tratamento", "#37474f")
        form = QGridLayout()
        
        # Aceito manipulação articular (HVLA)
        form.addWidget(QLabel("Aceito manipulação articular (HVLA):"), 0, 0)
        self.hvla_combo = QComboBox()
        self.hvla_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.hvla_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.hvla_combo, 0, 1)
        
        form.addWidget(QLabel("→ Restrições:"), 1, 0)
        self.hvla_detalhe = QLineEdit()
        self.hvla_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.hvla_detalhe, 1, 1)
        
        # Aceito mesoterapia (injeções superficiais)
        form.addWidget(QLabel("Aceito mesoterapia (injeções superficiais):"), 2, 0)
        self.mesoterapia_aceit_combo = QComboBox()
        self.mesoterapia_aceit_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.mesoterapia_aceit_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.mesoterapia_aceit_combo, 2, 1)
        
        form.addWidget(QLabel("→ Restrições:"), 3, 0)
        self.mesoterapia_aceit_detalhe = QLineEdit()
        self.mesoterapia_aceit_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.mesoterapia_aceit_detalhe, 3, 1)
        
        # Aceito terapias frequenciais/eletrónicas
        form.addWidget(QLabel("Aceito terapias frequenciais/eletrónicas:"), 4, 0)
        self.terapias_freq_combo = QComboBox()
        self.terapias_freq_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.terapias_freq_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.terapias_freq_combo, 4, 1)
        
        form.addWidget(QLabel("→ Restrições (implantes/zonas a evitar):"), 5, 0)
        self.terapias_freq_detalhe = QLineEdit()
        self.terapias_freq_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.terapias_freq_detalhe, 5, 1)
        
        # Aversão a agulhas/toque profundo
        form.addWidget(QLabel("Aversão a agulhas/toque profundo:"), 6, 0)
        self.aversao_agulhas_combo = QComboBox()
        self.aversao_agulhas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.aversao_agulhas_combo.setStyleSheet(self._estilo_campo())
        form.addWidget(self.aversao_agulhas_combo, 6, 1)
        
        form.addWidget(QLabel("→ Detalhe:"), 7, 0)
        self.aversao_agulhas_detalhe = QLineEdit()
        self.aversao_agulhas_detalhe.setStyleSheet(self._estilo_campo())
        form.addWidget(self.aversao_agulhas_detalhe, 7, 1)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_consentimentos(self, layout):
        """Cria seção de Consentimentos e RGPD"""
        secao = self._criar_secao_profissional("📋 Consentimentos e RGPD (versão completa)", "#1a237e")
        form = QVBoxLayout()
        
        # A) Declaração de veracidade
        declaracao_frame = QFrame()
        declaracao_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
        """)
        declaracao_layout = QVBoxLayout(declaracao_frame)
        
        declaracao_titulo = QLabel("<b>A) Declaração de veracidade e responsabilidade (obrigatório)</b>")
        declaracao_layout.addWidget(declaracao_titulo)
        
        declaracao_texto = QLabel("""Declaro que as informações prestadas são verdadeiras, completas e atualizadas. Qualquer omissão ou inexatidão pode comprometer a minha segurança, alterar a indicação terapêutica e isentar o profissional de responsabilidade por efeitos adversos decorrentes dessas omissões. Comprometo-me a informar de imediato alterações do meu estado de saúde, medicação, alergias, cirurgias, próteses/implantes (incl. pacemaker/DAI/neuroestimuladores) ou gravidez.""")
        declaracao_texto.setWordWrap(True)
        declaracao_texto.setStyleSheet("font-size: 14px; margin: 10px 0;")
        declaracao_layout.addWidget(declaracao_texto)
        
        # Checkbox para veracidade
        from PyQt6.QtWidgets import QCheckBox
        self.veracidade_checkbox = QCheckBox("Confirmo a veracidade das informações prestadas. (obrigatório)")
        self.veracidade_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                font-size: 14px;
                color: #d84315;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        declaracao_layout.addWidget(self.veracidade_checkbox)
        
        form.addWidget(declaracao_frame)
        
        # B) Consentimentos por modalidade
        consentimentos_frame = QFrame()
        consentimentos_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
        """)
        consentimentos_layout = QVBoxLayout(consentimentos_frame)
        
        consentimentos_titulo = QLabel("<b>B) Consentimentos por modalidade (obrigatório escolher em todas)</b>")
        consentimentos_layout.addWidget(consentimentos_titulo)
        
        consentimentos_intro = QLabel("Cada modalidade pode ser aceite/recusada parcialmente. Posso retirar o meu consentimento a qualquer momento, sem prejuízo do acompanhamento.")
        consentimentos_intro.setWordWrap(True)
        consentimentos_intro.setStyleSheet("font-size: 14px; margin: 10px 0; font-style: italic;")
        consentimentos_layout.addWidget(consentimentos_intro)
        
        # Naturopatia
        nat_layout = QHBoxLayout()
        nat_layout.addWidget(QLabel("Naturopatia / Fitoterapia / Suplementos →"))
        self.naturopatia_combo = QComboBox()
        self.naturopatia_combo.addItems(["Selecionar...", "Aceito", "Não aceito"])
        self.naturopatia_combo.setStyleSheet(self._estilo_campo())
        nat_layout.addWidget(self.naturopatia_combo)
        
        # Botão de informação para Naturopatia - usando BiodeskStyles v2.0
        if BIODESK_STYLES_AVAILABLE:
            btn_info_nat = BiodeskStyles.create_button("ℹ️", ButtonType.TOOL)
        else:
            btn_info_nat = QPushButton("ℹ️")
        
        btn_info_nat.setToolTip("Clique para saber mais sobre Naturopatia")
        btn_info_nat.clicked.connect(lambda: self._mostrar_explicacao_modalidade("naturopatia"))
        nat_layout.addWidget(btn_info_nat)
        consentimentos_layout.addLayout(nat_layout)
        
        # Osteopatia
        osteo_layout = QHBoxLayout()
        osteo_layout.addWidget(QLabel("Osteopatia / Técnicas manuais (incl. HVLA quando indicado) →"))
        self.osteopatia_combo = QComboBox()
        self.osteopatia_combo.addItems(["Selecionar...", "Aceito", "Não aceito"])
        self.osteopatia_combo.setStyleSheet(self._estilo_campo())
        osteo_layout.addWidget(self.osteopatia_combo)
        
        # Botão de informação para Osteopatia - ESTILO BIODESK
        btn_info_osteo = QPushButton("ℹ️")
        
        btn_assinar.clicked.connect(self.assinar_e_guardar)
        layout.addWidget(btn_assinar)
        
        # Botão Limpar
        btn_limpar = BiodeskUIKit.create_neutral_button("🗑️ Limpar Formulário")
        
        btn_limpar.clicked.connect(self.limpar_formulario)
        layout.addWidget(btn_limpar)
        
        layout.addStretch()
        
        return frame
    
    def assinar_e_guardar(self):
        """Abre sistema de assinatura e guarda PDF"""
        try:
            if not self.paciente_data:
                mostrar_aviso(self, "Aviso", "⚠️ Nenhum paciente selecionado.\n\nPor favor, selecione um paciente primeiro.")
                return
            
            # Validar se há dados preenchidos
            if not self._validar_formulario():
                return
            
            # Verificar se sistema de assinatura está disponível
            if not SISTEMA_ASSINATURA_DISPONIVEL:
                # Gerar PDF simples sem assinaturas
                mostrar_aviso(self, "Sistema Indisponível", 
                             "⚠️ Sistema de assinatura não disponível.\n\n"
                             "PDF será gerado sem assinaturas.")
                return self._gerar_pdf_sem_assinaturas()
            
            # Abrir diálogo de assinatura
            dados_assinaturas = abrir_dialogo_assinatura(
                self, 
                "Declaração de Saúde", 
                self.paciente_data
            )
            
            if dados_assinaturas:
                # Gerar PDF com assinaturas
                if self._gerar_pdf_com_assinaturas(dados_assinaturas):
                    # Atualizar progresso após assinatura
                    self._atualizar_progresso()
                    
                    # Emitir sinal de sucesso (manter formulário preenchido)
                    self.declaracao_assinada.emit({
                        'paciente_id': self.paciente_data.get('id'),
                        'dados': self._obter_dados_formulario(),
                        'assinaturas': dados_assinaturas
                    })
                    # Comentado: self.limpar_formulario() - para manter dados para consulta
                    print("✅ Declaração assinada com sucesso - dados mantidos visíveis")
            elif dados_assinaturas is None:
                # Usuário cancelou ou houve erro
                return
            else:
                # Fallback: gerar PDF sem assinaturas
                return self._gerar_pdf_sem_assinaturas()
            
        except Exception as e:
            print(f"❌ Erro ao processar assinatura: {e}")
            mostrar_erro(self, "Erro", f"❌ Erro ao processar assinatura:\n\n{str(e)}")
    
    def _validar_formulario(self):
        """Valida se há dados suficientes no formulário"""
        try:
            # Validar email se preenchido
            email = self.email.text().strip()
            if email and not self._validar_email(email):
                mostrar_aviso(self, "Email Inválido", 
                             f"⚠️ O email '{email}' não tem formato válido.\n\n"
                             "Exemplo de formato correto: nome@exemplo.com")
                return False
            
            # Validar telemóvel se preenchido
            telemovel = self.contacto_telem.text().strip()
            if telemovel and not self._validar_telemovel(telemovel):
                mostrar_aviso(self, "Telemóvel Inválido", 
                             f"⚠️ O número '{telemovel}' não tem formato válido.\n\n"
                             "Exemplos corretos: 912345678, +351912345678, 21 123 45 67")
                return False
            
            # Verificar checkboxes obrigatórios
            if not hasattr(self, 'veracidade_checkbox') or not self.veracidade_checkbox.isChecked():
                mostrar_aviso(self, "Formulário Incompleto", 
                             "⚠️ Deve confirmar a veracidade das informações prestadas.")
                return False
            
            if not hasattr(self, 'rgpd_checkbox') or not self.rgpd_checkbox.isChecked():
                mostrar_aviso(self, "Formulário Incompleto", 
                             "⚠️ Deve aceitar o tratamento de dados pessoais (RGPD).")
                return False
            
            # Verificar se pelo menos alguns consentimentos foram escolhidos
            consentimentos_preenchidos = 0
            if hasattr(self, 'naturopatia_combo') and self.naturopatia_combo.currentText() != "Selecionar...":
                consentimentos_preenchidos += 1
            if hasattr(self, 'osteopatia_combo') and self.osteopatia_combo.currentText() != "Selecionar...":
                consentimentos_preenchidos += 1
            if hasattr(self, 'mesoterapia_consent_combo') and self.mesoterapia_consent_combo.currentText() != "Selecionar...":
                consentimentos_preenchidos += 1
            if hasattr(self, 'medicina_quantica_combo') and self.medicina_quantica_combo.currentText() != "Selecionar...":
                consentimentos_preenchidos += 1
            
            if consentimentos_preenchidos == 0:
                mostrar_aviso(self, "Formulário Incompleto", 
                             "⚠️ Deve escolher pelo menos uma modalidade terapêutica (aceitar ou recusar).")
                return False
            
            # Verificar se há pelo menos algumas informações de saúde preenchidas
            campos_preenchidos = 0
            
            # Verificar motivo de consulta
            if hasattr(self, 'motivo_consulta') and self.motivo_consulta.toPlainText().strip():
                campos_preenchidos += 1
            
            # Verificar algumas condições principais
            campos_principais = [
                'diabetes_combo', 'hipertensao_combo', 'cardiaca_combo', 'asma_combo',
                'alergias_medicamentos_combo', 'gravidez_combo', 'anticoagulantes_combo',
                'tabaco_combo', 'alcool_combo'
            ]
            
            for campo in campos_principais:
                if hasattr(self, campo):
                    combo = getattr(self, campo)
                    if combo.currentText() != "Selecionar...":
                        campos_preenchidos += 1
            
            if campos_preenchidos < 3:
                mostrar_aviso(self, "Formulário Incompleto", 
                             "⚠️ Preencha pelo menos algumas informações de saúde antes de assinar.\n\n"
                             "Sugestões:\n"
                             "• Motivo da consulta\n"
                             "• Condições médicas principais\n"
                             "• Medicação atual\n"
                             "• Alergias conhecidas")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            mostrar_aviso(self, "Erro de Validação", f"❌ Erro ao validar formulário:\n{str(e)}")
            return False
    
    def limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        try:
            # Limpar combos - definir para primeiro item ("Selecionar...")
            combos = [
                # Identificação
                self.profissao_combo,
                
                # Metabólicas / Endócrinas
                self.diabetes_combo, self.hipertensao_combo, self.tireoide_combo, 
                self.dislipidemia_combo, self.hepatica_combo, self.renal_combo,
                
                # Cardiovasculares
                self.cardiaca_combo, self.avc_combo, self.trombose_combo, 
                self.aneurisma_combo, self.dor_toracica_combo, self.pacemaker_combo,
                
                # Respiratórias
                self.asma_combo, self.dpoc_combo, self.apneia_combo, self.infecao_resp_combo,
                
                # Gastrointestinais
                self.refluxo_combo, self.dii_combo, self.cirurgias_digest_combo,
                
                # Neurológicas / Psiquiátricas
                self.epilepsia_combo, self.desmielinizantes_combo, self.tce_combo,
                self.cefaleias_combo, self.psiquiatricas_combo, self.cauda_equina_combo,
                
                # Músculo-esqueléticas
                self.artrite_combo, self.osteoporose_combo, self.hernias_combo,
                self.escoliose_combo, self.fraturas_combo, self.quedas_combo,
                self.cirurgias_ortop_combo, self.proteses_combo, self.infiltracoes_combo,
                self.tecido_conjuntivo_combo,
                
                # Dermatologia / Feridas
                self.feridas_combo, self.queloides_combo, self.infecoes_cutaneas_combo,
                self.hemorragicas_combo, self.alergia_anestesicos_combo, self.alergia_adesivos_combo,
                
                # Alergias / Intolerâncias
                self.alergias_medicamentos_combo, self.alergias_alimentos_combo,
                self.alergias_plantas_combo, self.alergias_homeopaticos_combo, self.intolerancias_combo,
                
                # Infecciosas / Imunológicas
                self.autoimunes_combo, self.hiv_hepatites_combo, self.febre_perda_peso_combo,
                
                # Oncologia
                self.cancro_combo, self.tratamento_oncologico_combo, self.linfedema_combo,
                
                # Saúde Reprodutiva
                self.gravidez_combo, self.amamentacao_combo, self.gineco_urologicas_combo,
                self.dispositivo_intrauterino_combo,
                
                # Cirurgias / Internamentos / Traumas
                self.cirurgias_combo, self.internamentos_combo, self.acidentes_combo,
                
                # Implantes e Dispositivos
                self.dispositivos_eletronicos_combo, self.implantes_metalicos_combo, self.tatuagens_combo,
                
                # Medicação e Suplementos
                self.anticoagulantes_combo, self.imunossupressores_combo, self.antidiabeticos_combo,
                self.psicotropicos_combo, self.fotossensibilizantes_combo, self.bifosfonatos_combo,
                self.suplementos_combo, self.reacoes_previas_combo,
                
                # Estilo de Vida
                self.tabaco_combo, self.alcool_combo, self.drogas_combo,
                self.atividade_fisica_combo, self.sono_combo, self.stress_combo,
                
                # Exames
                self.exames_combo,
                
                # Red Flags
                self.dor_noturna_combo, self.defices_neurologicos_combo, self.incontinencia_combo,
                self.febre_sem_causa_combo, self.perda_peso_combo,
                
                # Preferências / Limites
                self.hvla_combo, self.mesoterapia_aceit_combo, self.terapias_freq_combo,
                self.aversao_agulhas_combo,
                
                # Consentimentos
                self.naturopatia_combo, self.osteopatia_combo, self.mesoterapia_consent_combo,
                self.medicina_quantica_combo, self.cabeca_combo, self.ombro_combo,
                self.anca_combo, self.palpacao_combo,
            ]
            
            for combo in combos:
                combo.setCurrentIndex(0)
            
            # Limpar line edits
            line_edits = [
                # Identificação
                self.contacto_telem, self.email, self.profissao_edit, self.profissao_detalhe,
                self.contacto_emergencia,
                
                # Metabólicas / Endócrinas
                self.diabetes_detalhe, self.hipertensao_detalhe, self.tireoide_detalhe,
                self.dislipidemia_detalhe, self.hepatica_detalhe, self.renal_detalhe,
                
                # Cardiovasculares
                self.cardiaca_detalhe, self.avc_detalhe, self.trombose_detalhe,
                self.aneurisma_detalhe, self.dor_toracica_detalhe, self.pacemaker_detalhe,
                
                # Respiratórias
                self.asma_detalhe, self.dpoc_detalhe, self.apneia_detalhe, self.infecao_resp_detalhe,
                
                # Gastrointestinais
                self.refluxo_detalhe, self.dii_detalhe, self.cirurgias_digest_detalhe,
                
                # Neurológicas / Psiquiátricas
                self.epilepsia_detalhe, self.desmielinizantes_detalhe, self.cefaleias_detalhe,
                self.psiquiatricas_detalhe, self.cauda_equina_detalhe,
                
                # Músculo-esqueléticas
                self.artrite_detalhe, self.osteoporose_detalhe, self.hernias_detalhe,
                self.escoliose_detalhe, self.fraturas_detalhe, self.quedas_detalhe,
                self.cirurgias_ortop_detalhe, self.proteses_detalhe, self.infiltracoes_detalhe,
                self.tecido_conjuntivo_detalhe,
                
                # Dermatologia / Feridas
                self.feridas_detalhe, self.queloides_detalhe, self.infecoes_cutaneas_detalhe,
                self.hemorragicas_detalhe, self.alergia_anestesicos_detalhe, self.alergia_adesivos_detalhe,
                
                # Alergias / Intolerâncias
                self.alergias_medicamentos_detalhe, self.alergias_alimentos_detalhe,
                self.alergias_plantas_detalhe, self.alergias_homeopaticos_detalhe, self.intolerancias_detalhe,
                
                # Infecciosas / Imunológicas
                self.autoimunes_detalhe, self.hiv_hepatites_detalhe, self.febre_perda_peso_detalhe,
                
                # Oncologia
                self.cancro_detalhe, self.tratamento_oncologico_detalhe, self.linfedema_detalhe,
                
                # Saúde Reprodutiva
                self.gravidez_detalhe, self.gineco_urologicas_detalhe, self.dispositivo_intrauterino_detalhe,
                
                # Cirurgias / Internamentos / Traumas
                self.cirurgias_detalhe, self.internamentos_detalhe, self.acidentes_detalhe,
                
                # Implantes e Dispositivos
                self.dispositivos_eletronicos_detalhe, self.implantes_metalicos_detalhe, self.tatuagens_detalhe,
                
                # Medicação e Suplementos
                self.anticoagulantes_detalhe, self.imunossupressores_detalhe, self.antidiabeticos_detalhe,
                self.bifosfonatos_detalhe, self.suplementos_detalhe, self.reacoes_previas_detalhe,
                
                # Estilo de Vida
                self.tabaco_detalhe, self.alcool_detalhe, self.drogas_detalhe,
                self.atividade_fisica_detalhe, self.sono_detalhe,
                
                # Preferências / Limites
                self.hvla_detalhe, self.mesoterapia_aceit_detalhe, self.terapias_freq_detalhe,
                self.aversao_agulhas_detalhe,
            ]
            
            for line_edit in line_edits:
                line_edit.clear()
            
            # Limpar text edits
            text_edits = [
                self.motivo_consulta, self.exames_detalhe, self.red_flags_detalhe,
            ]
            
            for text_edit in text_edits:
                text_edit.clear()
            
            # Limpar checkboxes
            checkboxes = [
                self.veracidade_checkbox, self.rgpd_checkbox, self.li_compreendi_checkbox,
                self.escolhi_modalidades_checkbox, self.assinalei_caixas_checkbox,
                self.questoes_respondidas_checkbox,
            ]
            
            for checkbox in checkboxes:
                checkbox.setChecked(False)
            
            # Mostrar mensagem de sucesso
            from biodesk_dialogs import mostrar_sucesso
            mostrar_sucesso(self, "Sucesso", "✅ Formulário limpo com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao limpar formulário: {e}")
            from biodesk_dialogs import mostrar_erro
            mostrar_erro(self, "Erro", f"Erro ao limpar formulário:\n{str(e)}")
    
    def _obter_dados_formulario(self):
        """Obtém dados estruturados do formulário completo"""
        return {
            # Identificação
            'nome': self.nome_edit.text(),
            'data_nascimento': self.data_nasc_edit.text(),
            'contacto_telem': self.contacto_telem.text(),
            'email': self.email.text(),
            'profissao_nome': self.profissao_edit.text(),
            'profissao_esforco': {
                'resposta': self.profissao_combo.currentText(),
                'detalhe': self.profissao_detalhe.text()
            },
            'contacto_emergencia': self.contacto_emergencia.text(),
            'motivo_consulta': self.motivo_consulta.toPlainText().strip(),
            
            # 1) Metabólicas / Endócrinas
            'diabetes': {
                'resposta': self.diabetes_combo.currentText(),
                'detalhe': self.diabetes_detalhe.text()
            },
            'hipertensao': {
                'resposta': self.hipertensao_combo.currentText(),
                'detalhe': self.hipertensao_detalhe.text()
            },
            'tireoide': {
                'resposta': self.tireoide_combo.currentText(),
                'detalhe': self.tireoide_detalhe.text()
            },
            'dislipidemia': {
                'resposta': self.dislipidemia_combo.currentText(),
                'detalhe': self.dislipidemia_detalhe.text()
            },
            'hepatica': {
                'resposta': self.hepatica_combo.currentText(),
                'detalhe': self.hepatica_detalhe.text()
            },
            'renal': {
                'resposta': self.renal_combo.currentText(),
                'detalhe': self.renal_detalhe.text()
            },
            
            # 2) Cardiovasculares
            'cardiaca': {
                'resposta': self.cardiaca_combo.currentText(),
                'detalhe': self.cardiaca_detalhe.text()
            },
            'avc': {
                'resposta': self.avc_combo.currentText(),
                'detalhe': self.avc_detalhe.text()
            },
            'trombose': {
                'resposta': self.trombose_combo.currentText(),
                'detalhe': self.trombose_detalhe.text()
            },
            'aneurisma': {
                'resposta': self.aneurisma_combo.currentText(),
                'detalhe': self.aneurisma_detalhe.text()
            },
            'dor_toracica': {
                'resposta': self.dor_toracica_combo.currentText(),
                'detalhe': self.dor_toracica_detalhe.text()
            },
            'pacemaker': {
                'resposta': self.pacemaker_combo.currentText(),
                'detalhe': self.pacemaker_detalhe.text()
            },
            
            # 3) Respiratórias
            'asma': {
                'resposta': self.asma_combo.currentText(),
                'detalhe': self.asma_detalhe.text()
            },
            'dpoc': {
                'resposta': self.dpoc_combo.currentText(),
                'detalhe': self.dpoc_detalhe.text()
            },
            'apneia': {
                'resposta': self.apneia_combo.currentText(),
                'detalhe': self.apneia_detalhe.text()
            },
            'infecao_resp': {
                'resposta': self.infecao_resp_combo.currentText(),
                'detalhe': self.infecao_resp_detalhe.text()
            },
            
            # 4) Gastrointestinais
            'refluxo': {
                'resposta': self.refluxo_combo.currentText(),
                'detalhe': self.refluxo_detalhe.text()
            },
            'dii': {
                'resposta': self.dii_combo.currentText(),
                'detalhe': self.dii_detalhe.text()
            },
            'cirurgias_digest': {
                'resposta': self.cirurgias_digest_combo.currentText(),
                'detalhe': self.cirurgias_digest_detalhe.text()
            },
            
            # 5) Neurológicas / Psiquiátricas
            'epilepsia': {
                'resposta': self.epilepsia_combo.currentText(),
                'detalhe': self.epilepsia_detalhe.text()
            },
            'desmielinizantes': {
                'resposta': self.desmielinizantes_combo.currentText(),
                'detalhe': self.desmielinizantes_detalhe.text()
            },
            'tce': {
                'resposta': self.tce_combo.currentText(),
                'detalhe': ''
            },
            'cefaleias': {
                'resposta': self.cefaleias_combo.currentText(),
                'detalhe': self.cefaleias_detalhe.text()
            },
            'psiquiatricas': {
                'resposta': self.psiquiatricas_combo.currentText(),
                'detalhe': self.psiquiatricas_detalhe.text()
            },
            'cauda_equina': {
                'resposta': self.cauda_equina_combo.currentText(),
                'detalhe': self.cauda_equina_detalhe.text()
            },
            
            # 6) Músculo-esqueléticas
            'artrite': {
                'resposta': self.artrite_combo.currentText(),
                'detalhe': self.artrite_detalhe.text()
            },
            'osteoporose': {
                'resposta': self.osteoporose_combo.currentText(),
                'detalhe': self.osteoporose_detalhe.text()
            },
            'hernias': {
                'resposta': self.hernias_combo.currentText(),
                'detalhe': self.hernias_detalhe.text()
            },
            'escoliose': {
                'resposta': self.escoliose_combo.currentText(),
                'detalhe': self.escoliose_detalhe.text()
            },
            'fraturas': {
                'resposta': self.fraturas_combo.currentText(),
                'detalhe': self.fraturas_detalhe.text()
            },
            'quedas': {
                'resposta': self.quedas_combo.currentText(),
                'detalhe': self.quedas_detalhe.text()
            },
            'cirurgias_ortop': {
                'resposta': self.cirurgias_ortop_combo.currentText(),
                'detalhe': self.cirurgias_ortop_detalhe.text()
            },
            'proteses': {
                'resposta': self.proteses_combo.currentText(),
                'detalhe': self.proteses_detalhe.text()
            },
            'infiltracoes': {
                'resposta': self.infiltracoes_combo.currentText(),
                'detalhe': self.infiltracoes_detalhe.text()
            },
            'tecido_conjuntivo': {
                'resposta': self.tecido_conjuntivo_combo.currentText(),
                'detalhe': self.tecido_conjuntivo_detalhe.text()
            },
            
            # 7) Dermatologia / Feridas
            'feridas': {
                'resposta': self.feridas_combo.currentText(),
                'detalhe': self.feridas_detalhe.text()
            },
            'queloides': {
                'resposta': self.queloides_combo.currentText(),
                'detalhe': self.queloides_detalhe.text()
            },
            'infecoes_cutaneas': {
                'resposta': self.infecoes_cutaneas_combo.currentText(),
                'detalhe': self.infecoes_cutaneas_detalhe.text()
            },
            'hemorragicas': {
                'resposta': self.hemorragicas_combo.currentText(),
                'detalhe': self.hemorragicas_detalhe.text()
            },
            'alergia_anestesicos': {
                'resposta': self.alergia_anestesicos_combo.currentText(),
                'detalhe': self.alergia_anestesicos_detalhe.text()
            },
            'alergia_adesivos': {
                'resposta': self.alergia_adesivos_combo.currentText(),
                'detalhe': self.alergia_adesivos_detalhe.text()
            },
            
            # 8) Alergias / Intolerâncias
            'alergias_medicamentos': {
                'resposta': self.alergias_medicamentos_combo.currentText(),
                'detalhe': self.alergias_medicamentos_detalhe.text()
            },
            'alergias_alimentos': {
                'resposta': self.alergias_alimentos_combo.currentText(),
                'detalhe': self.alergias_alimentos_detalhe.text()
            },
            'alergias_plantas': {
                'resposta': self.alergias_plantas_combo.currentText(),
                'detalhe': self.alergias_plantas_detalhe.text()
            },
            'alergias_homeopaticos': {
                'resposta': self.alergias_homeopaticos_combo.currentText(),
                'detalhe': self.alergias_homeopaticos_detalhe.text()
            },
            'intolerancias': {
                'resposta': self.intolerancias_combo.currentText(),
                'detalhe': self.intolerancias_detalhe.text()
            },
            
            # 9) Infecciosas / Imunológicas
            'autoimunes': {
                'resposta': self.autoimunes_combo.currentText(),
                'detalhe': self.autoimunes_detalhe.text()
            },
            'hiv_hepatites': {
                'resposta': self.hiv_hepatites_combo.currentText(),
                'detalhe': self.hiv_hepatites_detalhe.text()
            },
            'febre_perda_peso': {
                'resposta': self.febre_perda_peso_combo.currentText(),
                'detalhe': self.febre_perda_peso_detalhe.text()
            },
            
            # 10) Oncologia
            'cancro': {
                'resposta': self.cancro_combo.currentText(),
                'detalhe': self.cancro_detalhe.text()
            },
            'tratamento_oncologico': {
                'resposta': self.tratamento_oncologico_combo.currentText(),
                'detalhe': self.tratamento_oncologico_detalhe.text()
            },
            'linfedema': {
                'resposta': self.linfedema_combo.currentText(),
                'detalhe': self.linfedema_detalhe.text()
            },
            
            # 11) Saúde Reprodutiva
            'gravidez': {
                'resposta': self.gravidez_combo.currentText(),
                'detalhe': self.gravidez_detalhe.text()
            },
            'amamentacao': {
                'resposta': self.amamentacao_combo.currentText(),
                'detalhe': ''
            },
            'gineco_urologicas': {
                'resposta': self.gineco_urologicas_combo.currentText(),
                'detalhe': self.gineco_urologicas_detalhe.text()
            },
            'dispositivo_intrauterino': {
                'resposta': self.dispositivo_intrauterino_combo.currentText(),
                'detalhe': self.dispositivo_intrauterino_detalhe.text()
            },
            
            # 12) Cirurgias / Internamentos / Traumas
            'cirurgias': {
                'resposta': self.cirurgias_combo.currentText(),
                'detalhe': self.cirurgias_detalhe.text()
            },
            'internamentos': {
                'resposta': self.internamentos_combo.currentText(),
                'detalhe': self.internamentos_detalhe.text()
            },
            'acidentes': {
                'resposta': self.acidentes_combo.currentText(),
                'detalhe': self.acidentes_detalhe.text()
            },
            
            # 13) Implantes e Dispositivos
            'dispositivos_eletronicos': {
                'resposta': self.dispositivos_eletronicos_combo.currentText(),
                'detalhe': self.dispositivos_eletronicos_detalhe.text()
            },
            'implantes_metalicos': {
                'resposta': self.implantes_metalicos_combo.currentText(),
                'detalhe': self.implantes_metalicos_detalhe.text()
            },
            'tatuagens': {
                'resposta': self.tatuagens_combo.currentText(),
                'detalhe': self.tatuagens_detalhe.text()
            },
            
            # 14) Medicação e Suplementos
            'anticoagulantes': {
                'resposta': self.anticoagulantes_combo.currentText(),
                'detalhe': self.anticoagulantes_detalhe.text()
            },
            'imunossupressores': {
                'resposta': self.imunossupressores_combo.currentText(),
                'detalhe': self.imunossupressores_detalhe.text()
            },
            'antidiabeticos': {
                'resposta': self.antidiabeticos_combo.currentText(),
                'detalhe': self.antidiabeticos_detalhe.text()
            },
            'psicotropicos': {
                'resposta': self.psicotropicos_combo.currentText(),
                'detalhe': ''
            },
            'fotossensibilizantes': {
                'resposta': self.fotossensibilizantes_combo.currentText(),
                'detalhe': ''
            },
            'bifosfonatos': {
                'resposta': self.bifosfonatos_combo.currentText(),
                'detalhe': self.bifosfonatos_detalhe.text()
            },
            'suplementos': {
                'resposta': self.suplementos_combo.currentText(),
                'detalhe': self.suplementos_detalhe.text()
            },
            'reacoes_previas': {
                'resposta': self.reacoes_previas_combo.currentText(),
                'detalhe': self.reacoes_previas_detalhe.text()
            },
            
            # 15) Estilo de Vida
            'tabaco': {
                'resposta': self.tabaco_combo.currentText(),
                'detalhe': self.tabaco_detalhe.text()
            },
            'alcool': {
                'resposta': self.alcool_combo.currentText(),
                'detalhe': self.alcool_detalhe.text()
            },
            'drogas': {
                'resposta': self.drogas_combo.currentText(),
                'detalhe': self.drogas_detalhe.text()
            },
            'atividade_fisica': {
                'resposta': self.atividade_fisica_combo.currentText(),
                'detalhe': self.atividade_fisica_detalhe.text()
            },
            'sono': {
                'resposta': self.sono_combo.currentText(),
                'detalhe': self.sono_detalhe.text()
            },
            'stress': {
                'resposta': self.stress_combo.currentText(),
                'detalhe': ''
            },
            
            # 16) Exames/Diagnósticos recentes
            'exames': {
                'resposta': self.exames_combo.currentText(),
                'detalhe': self.exames_detalhe.toPlainText().strip()
            },
            
            # 17) Red Flags atuais
            'dor_noturna': {
                'resposta': self.dor_noturna_combo.currentText(),
                'detalhe': ''
            },
            'defices_neurologicos': {
                'resposta': self.defices_neurologicos_combo.currentText(),
                'detalhe': ''
            },
            'incontinencia': {
                'resposta': self.incontinencia_combo.currentText(),
                'detalhe': ''
            },
            'febre_sem_causa': {
                'resposta': self.febre_sem_causa_combo.currentText(),
                'detalhe': ''
            },
            'perda_peso': {
                'resposta': self.perda_peso_combo.currentText(),
                'detalhe': ''
            },
            'red_flags_descricao': self.red_flags_detalhe.toPlainText().strip(),
            
            # 18) Preferências / Limites de Tratamento
            'hvla': {
                'resposta': self.hvla_combo.currentText(),
                'detalhe': self.hvla_detalhe.text()
            },
            'mesoterapia_aceit': {
                'resposta': self.mesoterapia_aceit_combo.currentText(),
                'detalhe': self.mesoterapia_aceit_detalhe.text()
            },
            'terapias_freq': {
                'resposta': self.terapias_freq_combo.currentText(),
                'detalhe': self.terapias_freq_detalhe.text()
            },
            'aversao_agulhas': {
                'resposta': self.aversao_agulhas_combo.currentText(),
                'detalhe': self.aversao_agulhas_detalhe.text()
            },
            
            # Consentimentos e RGPD
            'veracidade': self.veracidade_checkbox.isChecked(),
            'naturopatia': self.naturopatia_combo.currentText(),
            'osteopatia': self.osteopatia_combo.currentText(),
            'mesoterapia_consent': self.mesoterapia_consent_combo.currentText(),
            'medicina_quantica': self.medicina_quantica_combo.currentText(),
            'toque_cabeca': self.cabeca_combo.currentText(),
            'toque_ombro': self.ombro_combo.currentText(),
            'toque_anca': self.anca_combo.currentText(),
            'toque_palpacao': self.palpacao_combo.currentText(),
            'rgpd': self.rgpd_checkbox.isChecked(),
            'li_compreendi': self.li_compreendi_checkbox.isChecked(),
            'escolhi_modalidades': self.escolhi_modalidades_checkbox.isChecked(),
            'assinalei_caixas': self.assinalei_caixas_checkbox.isChecked(),
            'questoes_respondidas': self.questoes_respondidas_checkbox.isChecked(),
        }
    
    def _salvar_assinaturas_para_pdf(self, dados_assinaturas):
        """Salva assinaturas como PNG para uso no PDF"""
        try:
            import os
            os.makedirs("temp", exist_ok=True)
            
            # Salvar assinatura do paciente
            if dados_assinaturas['paciente']['assinado'] and dados_assinaturas['paciente']['imagem']:
                caminho_paciente = os.path.abspath('temp/sig_declaracao_paciente.png')
                dados_assinaturas['paciente']['imagem'].save(caminho_paciente, 'PNG')
                print(f"✅ Assinatura do paciente salva: {caminho_paciente}")
            
            # Salvar assinatura do profissional
            if dados_assinaturas['profissional']['assinado'] and dados_assinaturas['profissional']['imagem']:
                caminho_profissional = os.path.abspath('temp/sig_declaracao_profissional.png')
                dados_assinaturas['profissional']['imagem'].save(caminho_profissional, 'PNG')
                print(f"✅ Assinatura do profissional salva: {caminho_profissional}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar assinaturas: {e}")

    def _gerar_pdf_com_assinaturas(self, dados_assinaturas):
        """Gera PDF profissional com assinaturas integradas"""
        try:
            # 🎯 Salvar assinaturas como PNG para integração no PDF
            self._salvar_assinaturas_para_pdf(dados_assinaturas)
            
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF
            
            # Obter dados do formulário
            dados = self._obter_dados_formulario()
            
            # Obter dados do paciente
            paciente_id = self.paciente_data.get('id')
            nome_paciente = self.paciente_data.get('nome', '[NOME_PACIENTE]')
            data_atual = datetime.now().strftime('%d/%m/%Y às %H:%M')
            
            print(f"📋 [PDF] Gerando PDF profissional para {nome_paciente}...")
            
            # Criar diretório
            pasta_paciente = f"Documentos_Pacientes/{paciente_id}_{nome_paciente.replace(' ', '_')}"
            pasta_declaracoes = f"{pasta_paciente}/declaracoes_saude"
            os.makedirs(pasta_declaracoes, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho_pdf = f"{pasta_declaracoes}/declaracao_saude_{timestamp}.pdf"
            
            # Construir HTML profissional
            html_content = self._construir_html_profissional(dados, dados_assinaturas, data_atual)
            
            # Configurar documento para máxima qualidade
            document = QTextDocument()
            document.setHtml(html_content)
            
            # Configurar impressora para PDF de alta qualidade
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageLayout(QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Portrait,
                QMarginsF(15, 15, 15, 15)  # Margens menores para aproveitar melhor o espaço
            ))
            
            # Configurações adicionais para qualidade
            printer.setResolution(600)  # Alta resolução para texto nítido
            
            # Imprimir com a máxima qualidade
            document.print(printer)
            
            # Registrar no gestor
            self._registrar_no_gestor_documentos(caminho_pdf)
            
            print(f"✅ [PDF] Declaração guardada: {caminho_pdf}")
            mostrar_sucesso(self, "Sucesso", 
                          f"✅ Declaração de saúde assinada e guardada com sucesso!\n\n"
                          f"📁 Localização: {caminho_pdf}\n\n"
                          f"🔹 Paciente: {dados_assinaturas['paciente']['assinado'] and '✓' or '✗'} Assinado\n"
                          f"🔹 Profissional: {dados_assinaturas['profissional']['assinado'] and '✓' or '✗'} Assinado")
            return True
                
        except Exception as e:
            print(f"❌ [PDF] Erro ao gerar PDF: {e}")
            mostrar_erro(self, "Erro", f"❌ Erro ao gerar PDF da declaração:\n\n{str(e)}")
            return False
    
    def _construir_html_profissional(self, dados, dados_assinaturas, data_atual):
        """Constrói HTML profissional para o PDF com os dados do novo formulário"""
        
        def obter_resposta(campo, tipo="combo"):
            """Função auxiliar para obter dados de forma segura"""
            if tipo == "combo":
                valor = dados.get(campo, {})
                if isinstance(valor, dict):
                    resposta = valor.get('resposta', 'Não respondido')
                    detalhe = valor.get('detalhe', '')
                    return resposta if resposta != "Selecionar..." else "Não respondido", detalhe
                else:
                    # Para campos salvos como string simples (consentimentos)
                    return valor if valor != "Selecionar..." else "Não respondido", ""
            else:
                # Para campos de texto, retornar valor direto
                valor = dados.get(campo, 'Não informado')
                if isinstance(valor, dict):
                    return valor.get('resposta', 'Não informado')
                return valor
        
        # Identificação
        nome = dados.get('nome', 'Não informado')
        data_nasc = dados.get('data_nascimento', 'Não informado') 
        contacto = dados.get('contacto_telem', 'Não informado')
        email = dados.get('email', 'Não informado')
        motivo = dados.get('motivo_consulta', 'Não informado')
        
        # Algumas condições principais para o PDF
        diabetes_resp, diabetes_det = obter_resposta('diabetes')
        hipertensao_resp, hipertensao_det = obter_resposta('hipertensao')
        cardiaca_resp, cardiaca_det = obter_resposta('cardiaca')
        alergias_med_resp, alergias_med_det = obter_resposta('alergias_medicamentos')
        
        # Obter TODOS os consentimentos com respostas
        naturopatia_resp, _ = obter_resposta('naturopatia')
        osteopatia_resp, _ = obter_resposta('osteopatia')
        mesoterapia_resp, _ = obter_resposta('mesoterapia_consent')
        medicina_quantica_resp, _ = obter_resposta('medicina_quantica')
        
        # Consentimentos adicionais para mostrar no PDF
        toque_cabeca_resp, _ = obter_resposta('toque_cabeca')
        toque_ombro_resp, _ = obter_resposta('toque_ombro') 
        toque_anca_resp, _ = obter_resposta('toque_anca')
        toque_palpacao_resp, _ = obter_resposta('toque_palpacao')
        
        # Verificar checkboxes de veracidade e RGPD
        veracidade = dados.get('veracidade', False)
        rgpd = dados.get('rgpd', False)
        
        # 🎯 INTEGRAÇÃO DAS ASSINATURAS REAIS DO CANVAS
        assinatura_paciente_html = ""
        assinatura_profissional_html = ""
        
        try:
            import base64
            import os
            
            # Caminho da assinatura do paciente
            sig_paciente_path = os.path.abspath('temp/sig_declaracao_paciente.png')
            if os.path.exists(sig_paciente_path):
                with open(sig_paciente_path, 'rb') as f:
                    assinatura_base64_paciente = base64.b64encode(f.read()).decode('utf-8')
                assinatura_paciente_html = f'<img src="data:image/png;base64,{assinatura_base64_paciente}" class="assinatura-imagem">'
            else:
                assinatura_paciente_html = '<div class="sem-assinatura">Assinatura não encontrada</div>'
            
            # Caminho da assinatura do profissional (se existir)
            sig_profissional_path = os.path.abspath('temp/sig_declaracao_profissional.png')
            if os.path.exists(sig_profissional_path):
                with open(sig_profissional_path, 'rb') as f:
                    assinatura_base64_profissional = base64.b64encode(f.read()).decode('utf-8')
                assinatura_profissional_html = f'<img src="data:image/png;base64,{assinatura_base64_profissional}" class="assinatura-imagem">'
            else:
                assinatura_profissional_html = '<div class="sem-assinatura">Aguardando assinatura</div>'
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar assinaturas: {e}")
            assinatura_paciente_html = '<div class="sem-assinatura">Erro ao carregar assinatura</div>'
            assinatura_profissional_html = '<div class="sem-assinatura">Erro ao carregar assinatura</div>'

        # Template HTML melhorado
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-PT">
        <head>
            <meta charset="UTF-8">
            <title>Declaração de Saúde - {nome}</title>
            <style>
                @page {{ size: A4; margin: 10mm; }}
                body {{ font-family: 'Segoe UI', sans-serif; 
                       line-height: 1.4; color: #000; margin: 0; padding: 0; font-size: 14px; }}
                .header {{ text-align: center; margin-bottom: 15px; 
                          border-bottom: 2px solid #2d5a27; padding-bottom: 10px; }}
                .header h1 {{ color: #2d5a27; margin: 0; font-size: 14px; font-weight: bold; 
                             text-decoration: underline; }}
                .header .subtitle {{ color: #000; font-size: 14px; margin-top: 5px; font-weight: bold; }}
                
                .section {{ margin-bottom: 8px; background: #f8f9fa; 
                           border-left: 3px solid #2d5a27; padding: 6px; border-radius: 4px; 
                           page-break-inside: avoid; }}
                .section h2 {{ color: #000; margin: 0 0 6px 0; font-size: 14px; font-weight: bold;
                              border-bottom: 1px solid #dee2e6; padding-bottom: 3px; }}
                
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px; }}
                .info-item {{ background: white; padding: 5px; border-radius: 3px; border: 1px solid #e9ecef; 
                             font-size: 14px; color: #000; }}
                .info-item strong {{ color: #000; font-weight: normal; }}
                
                .condition {{ margin-bottom: 4px; padding: 5px; background: white; 
                            border-radius: 3px; border-left: 2px solid #28a745; font-size: 14px; color: #000; }}
                .condition.sim {{ border-left-color: #dc3545; }}
                .condition-title {{ font-weight: normal; color: #000; }}
                .condition-response {{ color: #000; font-weight: normal; }}
                .condition-details {{ color: #000; font-style: normal; margin-top: 2px; }}
                
                .consent-section {{ background: #e8f5e8; border-left-color: #28a745; }}
                .consent-item {{ display: flex; justify-content: space-between; align-items: center; 
                               padding: 3px 6px; margin: 1px 0; background: white; border-radius: 3px; 
                               font-size: 14px; color: #000; }}
                .consent-response {{ font-weight: normal; padding: 2px 5px; border-radius: 2px; font-size: 14px; 
                                   color: #000; }}
                .consent-response.aceito {{ background: #d4edda; color: #000; }}
                .consent-response.nao-aceito {{ background: #f8d7da; color: #000; }}
                .consent-response.sim {{ background: #d4edda; color: #000; }}
                .consent-response.nao {{ background: #f8d7da; color: #000; }}
                
                .signatures {{ margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; 
                              page-break-inside: avoid; }}
                .signature-box {{ text-align: center; padding: 8px; border: 1px solid #ccc; 
                                border-radius: 5px; background: white; }}
                .signature-box h3 {{ margin: 0 0 6px 0; font-size: 14px; color: #000; font-weight: bold; }}
                .signature-line {{ width: 100%; height: 35px; border-bottom: 1px solid #333; 
                                  margin-bottom: 4px; display: flex; align-items: end; justify-content: center; }}
                .assinatura-imagem {{ max-width: 100%; max-height: 30px; }}
                .sem-assinatura {{ color: #000; font-style: normal; font-size: 14px; }}
                
                .footer {{ margin-top: 10px; text-align: center; color: #000; 
                          border-top: 1px solid #dee2e6; padding-top: 6px; font-size: 14px; }}
                
                .declaracoes {{ background: #fff3cd; border-left-color: #ffc107; }}
                .checkbox-item {{ display: flex; align-items: center; margin: 2px 0; font-size: 14px; color: #000; }}
                .checkbox {{ margin-right: 5px; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Declaração de Saúde do Paciente</h1>
                <div class="subtitle">Documento gerado em {data_atual}</div>
            </div>

            <div class="section">
                <h2>👤 Identificação</h2>
                <div class="info-grid">
                    <div class="info-item"><strong>Nome:</strong> {nome}</div>
                    <div class="info-item"><strong>Data Nascimento:</strong> {data_nasc}</div>
                    <div class="info-item"><strong>Contacto:</strong> {contacto}</div>
                    {f'<div class="info-item"><strong>Email:</strong> {email}</div>' if email != 'Não informado' else '<div class="info-item"><strong>Email:</strong> --</div>'}
                </div>
                {f'<div class="info-item" style="margin-top: 10px;"><strong>Motivo da consulta:</strong> {motivo}</div>' if motivo != 'Não informado' else ''}
            </div>

            <div class="section">
                <h2>🏥 Condições de Saúde Principais</h2>
                
                <div class="condition {('sim' if diabetes_resp == 'Sim' else '')}">
                    <div class="condition-title">Diabetes</div>
                    <div class="condition-response {('sim' if diabetes_resp == 'Sim' else '')}">{diabetes_resp}</div>
                    {f'<div class="condition-details">{diabetes_det}</div>' if diabetes_det else ''}
                </div>
                
                <div class="condition {('sim' if hipertensao_resp == 'Sim' else '')}">
                    <div class="condition-title">Hipertensão</div>
                    <div class="condition-response {('sim' if hipertensao_resp == 'Sim' else '')}">{hipertensao_resp}</div>
                    {f'<div class="condition-details">{hipertensao_det}</div>' if hipertensao_det else ''}
                </div>
                
                <div class="condition {('sim' if cardiaca_resp == 'Sim' else '')}">
                    <div class="condition-title">Doença Cardíaca</div>
                    <div class="condition-response {('sim' if cardiaca_resp == 'Sim' else '')}">{cardiaca_resp}</div>
                    {f'<div class="condition-details">{cardiaca_det}</div>' if cardiaca_det else ''}
                </div>
                
                <div class="condition {('sim' if alergias_med_resp == 'Sim' else '')}">
                    <div class="condition-title">Alergias a Medicamentos</div>
                    <div class="condition-response {('sim' if alergias_med_resp == 'Sim' else '')}">{alergias_med_resp}</div>
                    {f'<div class="condition-details">{alergias_med_det}</div>' if alergias_med_det else ''}
                </div>
            </div>

            <div class="section consent-section">
                <h2>📋 Consentimentos para Modalidades Terapêuticas</h2>
                
                <div class="consent-item">
                    <span><strong>🌿 Naturopatia / Fitoterapia / Suplementos</strong></span>
                    <span class="consent-response {('aceito' if naturopatia_resp == 'Aceito' else 'nao-aceito' if naturopatia_resp == 'Não aceito' else '')}">{naturopatia_resp}</span>
                </div>
                
                <div class="consent-item">
                    <span><strong>🤲 Osteopatia / Técnicas Manuais</strong></span>
                    <span class="consent-response {('aceito' if osteopatia_resp == 'Aceito' else 'nao-aceito' if osteopatia_resp == 'Não aceito' else '')}">{osteopatia_resp}</span>
                </div>
                
                <div class="consent-item">
                    <span><strong>💉 Mesoterapia Homeopática</strong></span>
                    <span class="consent-response {('aceito' if mesoterapia_resp == 'Aceito' else 'nao-aceito' if mesoterapia_resp == 'Não aceito' else '')}">{mesoterapia_resp}</span>
                </div>
                
                <div class="consent-item">
                    <span><strong>⚛️ Medicina Quântica / Frequencial</strong></span>
                    <span class="consent-response {('aceito' if medicina_quantica_resp == 'Aceito' else 'nao-aceito' if medicina_quantica_resp == 'Não aceito' else '')}">{medicina_quantica_resp}</span>
                </div>
            </div>

            <div class="section consent-section">
                <h2>🤝 Consentimentos para Toque Terapêutico</h2>
                
                <div class="consent-item">
                    <span><strong>🧠 Cabeça / Pescoço / Coluna</strong></span>
                    <span class="consent-response {('sim' if toque_cabeca_resp == 'Sim' else 'nao' if toque_cabeca_resp == 'Não' else '')}">{toque_cabeca_resp}</span>
                </div>
                
                <div class="consent-item">
                    <span><strong>💪 Ombro / Membros Superiores / Mãos</strong></span>
                    <span class="consent-response {('sim' if toque_ombro_resp == 'Sim' else 'nao' if toque_ombro_resp == 'Não' else '')}">{toque_ombro_resp}</span>
                </div>
                
                <div class="consent-item">
                    <span><strong>🦵 Anca / Membros Inferiores / Pés</strong></span>
                    <span class="consent-response {('sim' if toque_anca_resp == 'Sim' else 'nao' if toque_anca_resp == 'Não' else '')}">{toque_anca_resp}</span>
                </div>
                
                <div class="consent-item">
                    <span><strong>🩻 Palpação Externa (Tórax/Abdómen/Pélvis)</strong></span>
                    <span class="consent-response {('sim' if toque_palpacao_resp == 'Sim' else 'nao' if toque_palpacao_resp == 'Não' else '')}">{toque_palpacao_resp}</span>
                </div>
            </div>

            <div class="section declaracoes">
                <h2>📜 Declarações e Consentimentos RGPD</h2>
                
                <div class="checkbox-item">
                    <span><strong>Declaração de Veracidade:</strong> Confirmo que as informações prestadas são verdadeiras e completas {'✓ CONFIRMADO' if veracidade else '✗ NÃO CONFIRMADO'}</span>
                </div>
                
                <div class="checkbox-item">
                    <span><strong>Consentimento RGPD:</strong> Autorizo o tratamento dos meus dados pessoais e de saúde conforme regulamento {'✓ AUTORIZADO' if rgpd else '✗ NÃO AUTORIZADO'}</span>
                </div>
            </div>

            <div class="signatures">
                <div class="signature-box">
                    <h3>Assinatura do Paciente</h3>
                    <div class="signature-line">{assinatura_paciente_html}</div>
                    <div><strong>{nome}</strong></div>
                    <div>{data_atual}</div>
                </div>
                
                <div class="signature-box">
                    <h3>Assinatura do Profissional</h3>
                    <div class="signature-line">{assinatura_profissional_html}</div>
                    <div><strong>Profissional de Saúde</strong></div>
                    <div>{data_atual}</div>
                </div>
            </div>

            <div class="footer">
                <p><strong>BIODESK</strong> - Sistema de Gestão Clínica</p>
                <p>Este documento foi gerado digitalmente e contém informações confidenciais do paciente.</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def _registrar_no_gestor_documentos(self, caminho_pdf):
        """Registra no gestor de documentos e emite sinal para atualização"""
        try:
            # Emitir sinal para o widget pai atualizar o gestor de documentos
            self.declaracao_assinada.emit({
                'paciente_id': self.paciente_data.get('id'),
                'tipo': 'declaracao_saude',
                'caminho': caminho_pdf,
                'data_criacao': datetime.now().isoformat(),
                'titulo': f"Declaração de Saúde - {datetime.now().strftime('%d/%m/%Y')}"
            })
            
            # Tentar registrar também no DocumentManager se disponível
            try:
                from editor_documentos import DocumentManager
                
                doc_manager = DocumentManager()
                doc_manager.adicionar_documento({
                    'paciente_id': self.paciente_data.get('id'),
                    'tipo': 'declaracao_saude',
                    'caminho': caminho_pdf,
                    'data_criacao': datetime.now().isoformat(),
                    'titulo': f"Declaração de Saúde - {datetime.now().strftime('%d/%m/%Y')}"
                })
                print("📋 Documento registrado no DocumentManager")
                
            except ImportError:
                print("ℹ️ DocumentManager não disponível, usando apenas sinal")
            except Exception as e:
                print(f"⚠️ Erro ao registrar no DocumentManager: {e}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Erro ao registrar documento: {e}")
            return False

    def _gerar_pdf_sem_assinaturas(self):
        """Gera PDF simples sem assinaturas quando sistema não disponível"""
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
            from PyQt6.QtCore import QMarginsF
            
            # Obter dados do formulário
            dados = self._obter_dados_formulario()
            
            # Criar nome de arquivo
            nome_paciente = self.paciente_data.get('nome', 'Paciente')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"declaracao_saude_{nome_paciente.replace(' ', '_')}_{timestamp}.pdf"
            
            # Diretório de saída
            paciente_id = self.paciente_data.get('id', 'temp')
            diretorio_paciente = f"Documentos_Pacientes/{paciente_id}"
            os.makedirs(diretorio_paciente, exist_ok=True)
            caminho_pdf = os.path.join(diretorio_paciente, nome_arquivo)
            
            # Configurar impressora PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_pdf)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Configurar margens
            layout = QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Portrait,
                QMarginsF(20, 20, 20, 20),
                QPageLayout.Unit.Millimeter
            )
            printer.setPageLayout(layout)
            
            # Gerar HTML simplificado
            html_content = self._gerar_html_declaracao_sem_assinaturas(dados)
            
            # Criar documento e imprimir
            document = QTextDocument()
            document.setHtml(html_content)
            document.print_(printer)
            
            print(f"✅ PDF gerado sem assinaturas: {caminho_pdf}")
            
            # Mostrar sucesso
            mostrar_sucesso(self, "PDF Gerado", 
                          f"📄 Declaração salva com sucesso!\n\n"
                          f"Arquivo: {nome_arquivo}\n"
                          f"Local: {diretorio_paciente}")
            
            return True
            
        except Exception as e:
            mostrar_erro(self, "Erro na Geração", f"❌ Erro ao gerar PDF: {str(e)}")
            return False

    def _gerar_html_declaracao_sem_assinaturas(self, dados):
        """Gera HTML para PDF sem assinaturas"""
        # CSS para o PDF
        css_styles = """
        <style>
        body { 
            font-family: Arial, sans-serif; 
            font-size: 12pt; 
            line-height: 1.4; 
            margin: 0; 
            padding: 20px;
        }
        .header { 
            text-align: center; 
            border-bottom: 2px solid #2c5282; 
            padding-bottom: 15px; 
            margin-bottom: 20px; 
        }
        .title { 
            font-size: 18pt; 
            font-weight: bold; 
            color: #2c5282; 
            margin-bottom: 10px; 
        }
        .section { 
            margin-bottom: 15px; 
            padding: 10px; 
            border-left: 3px solid #e2e8f0; 
        }
        .section-title { 
            font-weight: bold; 
            color: #2d3748; 
            margin-bottom: 8px; 
            font-size: 13pt; 
        }
        .checkbox-item { 
            margin: 3px 0; 
            padding-left: 20px; 
        }
        .info-grid { 
            display: table; 
            width: 100%; 
            margin-bottom: 15px; 
        }
        .info-row { 
            display: table-row; 
        }
        .info-label { 
            display: table-cell; 
            font-weight: bold; 
            width: 30%; 
            padding: 3px 10px 3px 0; 
        }
        .info-value { 
            display: table-cell; 
            padding: 3px 0; 
        }
        .footer { 
            margin-top: 30px; 
            border-top: 1px solid #e2e8f0; 
            padding-top: 15px; 
            text-align: center; 
            font-size: 10pt; 
            color: #718096; 
        }
        </style>
        """
        
        # Gerar informações do paciente
        paciente_html = f"""
        <div class="info-grid">
            <div class="info-row">
                <div class="info-label">Nome:</div>
                <div class="info-value">{dados.get('nome_paciente', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Data de Nascimento:</div>
                <div class="info-value">{dados.get('data_nascimento', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Email:</div>
                <div class="info-value">{dados.get('email', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Telemóvel:</div>
                <div class="info-value">{dados.get('telemovel', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Profissão:</div>
                <div class="info-value">{dados.get('profissao_nome', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Esforço da Profissão:</div>
                <div class="info-value">{dados.get('profissao_esforco', 'N/A')}</div>
            </div>
        </div>
        """
        
        # Gerar seções médicas
        secoes_html = ""
        for secao, itens in dados.get('secoes_medicas', {}).items():
            if itens:  # Se há itens marcados nesta seção
                secoes_html += f"""
                <div class="section">
                    <div class="section-title">{secao.replace('_', ' ').title()}</div>
                """
                for item in itens:
                    secoes_html += f'<div class="checkbox-item">☑ {item}</div>'
                secoes_html += "</div>"
        
        # HTML completo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {css_styles}
        </head>
        <body>
            <div class="header">
                <div class="title">DECLARAÇÃO DE SAÚDE</div>
                <div>Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Informações do Paciente</div>
                {paciente_html}
            </div>
            
            {secoes_html}
            
            <div class="footer">
                <p>Documento gerado automaticamente pelo sistema Biodesk</p>
                <p>⚠️ Este documento foi gerado sem assinaturas digitais</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    # ====== FUNCIONALIDADES AVANÇADAS - NAVEGAÇÃO E AUTO-SAVE ======
    
    def abrir_navegacao_rapida(self):
        """Abre diálogo de navegação rápida entre seções"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🧭 Navegação Rápida")
            dialog.setFixedSize(400, 500)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            
            # Lista de seções
            lista = QListWidget()
            lista.setStyleSheet("""
                QListWidget {
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    background-color: white;
                    font-size: 13px;
                }
                QListWidgetItem {
                    padding: 8px 12px;
                    border-bottom: 1px solid #f8f9fa;
                }
                QListWidgetItem:hover {
                    background-color: #e3f2fd;
                }
                QListWidgetItem:selected {
                    background-color: #2196f3;
                    color: white;
                }
            """)
            
            secoes = [
                "👤 Identificação", "⚡ Metabólicas/Endócrinas", "❤️ Cardiovasculares",
                "🫁 Respiratórias", "🍽️ Gastrointestinais", "🧠 Neurológicas",
                "💪 Musculoesqueléticas", "🌟 Dermatologia", "🤧 Alergias",
                "🦠 Infecciosas", "🎗️ Oncologia", "👶 Reprodutiva",
                "🔪 Cirurgias", "⚕️ Implantes", "💊 Medicação",
                "🏃 Estilo de Vida", "📊 Exames", "🚨 Red Flags",
                "⚙️ Preferências", "📝 Consentimentos"
            ]
            
            for secao in secoes:
                item = QListWidgetItem(secao)
                lista.addItem(item)
            
            layout.addWidget(lista)
            
            # Botões
            botoes_layout = QHBoxLayout()
            
            if BIODESK_STYLES_AVAILABLE:
                btn_ir = BiodeskStyles.create_button("🎯 Ir para Seção", ButtonType.NAVIGATION)
            else:
                btn_ir = QPushButton("🎯 Ir para Seção")
            
            btn_ir.clicked.connect(lambda: self._navegar_para_secao(lista.currentRow(), dialog))
            
            if BIODESK_STYLES_AVAILABLE:
                btn_cancelar = BiodeskStyles.create_button("❌ Cancelar", ButtonType.DEFAULT)
            else:
                btn_cancelar = QPushButton("❌ Cancelar")
            
            btn_cancelar.clicked.connect(dialog.reject)
            
            botoes_layout.addWidget(btn_ir)
            botoes_layout.addWidget(btn_cancelar)
            layout.addLayout(botoes_layout)
            
            dialog.exec()
            
        except Exception as e:
            print(f"❌ Erro na navegação rápida: {e}")
    
    def _navegar_para_secao(self, index, dialog):
        """Navega para uma seção específica"""
        try:
            dialog.accept()
            
            # Scroll para a seção (implementação simplificada)
            scroll_area = self.parent().findChild(QScrollArea)
            if scroll_area:
                posicao = index * 100  # Estimativa
                scroll_area.verticalScrollBar().setValue(posicao)
                
            print(f"🎯 Navegando para seção {index}")
            
        except Exception as e:
            print(f"❌ Erro ao navegar: {e}")
    
    def guardar_rascunho(self):
        """Guarda rascunho automaticamente"""
        try:
            dados = self._obter_dados_formulario()
            
            # Marcar como rascunho
            dados['_status'] = 'rascunho'
            dados['_ultima_alteracao'] = datetime.now().isoformat()
            
            # Atualizar progresso
            self._atualizar_progresso()
            
            # Emitir sinal
            self.dados_atualizados.emit(dados)
            
            print("💾 Rascunho guardado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao guardar rascunho: {e}")
    
    def _atualizar_progresso(self):
        """Atualiza barra de progresso baseado nos campos preenchidos"""
        try:
            total_campos = 50  # Estimativa dos campos principais
            campos_preenchidos = 0
            
            # Contar campos preenchidos (implementação simplificada)
            if hasattr(self, 'nome_edit') and self.nome_edit.text().strip():
                campos_preenchidos += 1
            if hasattr(self, 'email') and self.email.text().strip():
                campos_preenchidos += 1
            if hasattr(self, 'contacto_telem') and self.contacto_telem.text().strip():
                campos_preenchidos += 1
            
            # Atualizar barra
            percentual = int((campos_preenchidos / total_campos) * 100)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(percentual)
                self.contador_label.setText(f"{campos_preenchidos}/{total_campos} campos preenchidos")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar progresso: {e}")
    
    # ====== SEÇÕES COMPACTAS - IMPLEMENTAÇÕES BÁSICAS ======
    
    def _criar_secao_metabolicas_compacta(self, layout):
        """1) Metabólicas / Endócrinas - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("⚡ 1) Metabólicas / Endócrinas", "#e91e63")
        form = QFormLayout()
        
        # Diabetes
        diabetes_layout = QHBoxLayout()
        self.diabetes_combo = QComboBox()
        self.diabetes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.diabetes_combo.setStyleSheet(self._estilo_campo_compacto())
        self.diabetes_detalhe = QLineEdit()
        self.diabetes_detalhe.setPlaceholderText("Tipo (1/2/gestacional), HbA1c média, hipoglicemias? tratamento")
        self.diabetes_detalhe.setStyleSheet(self._estilo_campo_compacto())
        diabetes_layout.addWidget(self.diabetes_combo, 1)
        diabetes_layout.addWidget(self.diabetes_detalhe, 3)
        form.addRow("Diabetes:", diabetes_layout)
        
        # Hipertensão
        hipertensao_layout = QHBoxLayout()
        self.hipertensao_combo = QComboBox()
        self.hipertensao_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.hipertensao_combo.setStyleSheet(self._estilo_campo_compacto())
        self.hipertensao_detalhe = QLineEdit()
        self.hipertensao_detalhe.setPlaceholderText("Valores médios, medicação")
        self.hipertensao_detalhe.setStyleSheet(self._estilo_campo_compacto())
        hipertensao_layout.addWidget(self.hipertensao_combo, 1)
        hipertensao_layout.addWidget(self.hipertensao_detalhe, 3)
        form.addRow("Hipertensão:", hipertensao_layout)
        
        # Disfunção tiroideia
        tireoide_layout = QHBoxLayout()
        self.tireoide_combo = QComboBox()
        self.tireoide_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.tireoide_combo.setStyleSheet(self._estilo_campo_compacto())
        self.tireoide_detalhe = QLineEdit()
        self.tireoide_detalhe.setPlaceholderText("Hipo/Hiper, cirurgia, medicação")
        self.tireoide_detalhe.setStyleSheet(self._estilo_campo_compacto())
        tireoide_layout.addWidget(self.tireoide_combo, 1)
        tireoide_layout.addWidget(self.tireoide_detalhe, 3)
        form.addRow("Disfunção tiroideia:", tireoide_layout)
        
        # Dislipidemia
        dislipidemia_layout = QHBoxLayout()
        self.dislipidemia_combo = QComboBox()
        self.dislipidemia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dislipidemia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.dislipidemia_detalhe = QLineEdit()
        self.dislipidemia_detalhe.setPlaceholderText("Valores recentes")
        self.dislipidemia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        dislipidemia_layout.addWidget(self.dislipidemia_combo, 1)
        dislipidemia_layout.addWidget(self.dislipidemia_detalhe, 3)
        form.addRow("Dislipidemia:", dislipidemia_layout)
        
        # Doença hepática
        hepatica_layout = QHBoxLayout()
        self.hepatica_combo = QComboBox()
        self.hepatica_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.hepatica_combo.setStyleSheet(self._estilo_campo_compacto())
        self.hepatica_detalhe = QLineEdit()
        self.hepatica_detalhe.setPlaceholderText("Esteatose/hepatite/cirrose - Detalhe")
        self.hepatica_detalhe.setStyleSheet(self._estilo_campo_compacto())
        hepatica_layout.addWidget(self.hepatica_combo, 1)
        hepatica_layout.addWidget(self.hepatica_detalhe, 3)
        form.addRow("Doença hepática:", hepatica_layout)
        
        # Doença renal
        renal_layout = QHBoxLayout()
        self.renal_combo = QComboBox()
        self.renal_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.renal_combo.setStyleSheet(self._estilo_campo_compacto())
        self.renal_detalhe = QLineEdit()
        self.renal_detalhe.setPlaceholderText("IRC/síndrome nefrótica - Estádio/clearance")
        self.renal_detalhe.setStyleSheet(self._estilo_campo_compacto())
        renal_layout.addWidget(self.renal_combo, 1)
        renal_layout.addWidget(self.renal_detalhe, 3)
        form.addRow("Doença renal:", renal_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_cardiovasculares_compacta(self, layout):
        """2) Cardiovasculares - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("❤️ 2) Cardiovasculares", "#f44336")
        form = QFormLayout()
        
        # Isquemia coronária
        isquemia_layout = QHBoxLayout()
        self.isquemia_combo = QComboBox()
        self.isquemia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.isquemia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.isquemia_detalhe = QLineEdit()
        self.isquemia_detalhe.setPlaceholderText("EAM/angina/stents - qual coronária?")
        self.isquemia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        isquemia_layout.addWidget(self.isquemia_combo, 1)
        isquemia_layout.addWidget(self.isquemia_detalhe, 3)
        form.addRow("Isquemia coronária:", isquemia_layout)
        
        # Insuficiência cardíaca
        ic_layout = QHBoxLayout()
        self.ic_combo = QComboBox()
        self.ic_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.ic_combo.setStyleSheet(self._estilo_campo_compacto())
        self.ic_detalhe = QLineEdit()
        self.ic_detalhe.setPlaceholderText("FEVE%, classe NYHA")
        self.ic_detalhe.setStyleSheet(self._estilo_campo_compacto())
        ic_layout.addWidget(self.ic_combo, 1)
        ic_layout.addWidget(self.ic_detalhe, 3)
        form.addRow("Insuficiência cardíaca:", ic_layout)
        
        # Arritmias
        arritmias_layout = QHBoxLayout()
        self.arritmias_combo = QComboBox()
        self.arritmias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.arritmias_combo.setStyleSheet(self._estilo_campo_compacto())
        self.arritmias_detalhe = QLineEdit()
        self.arritmias_detalhe.setPlaceholderText("FA/flutter/SVT - anticoagulado?")
        self.arritmias_detalhe.setStyleSheet(self._estilo_campo_compacto())
        arritmias_layout.addWidget(self.arritmias_combo, 1)
        arritmias_layout.addWidget(self.arritmias_detalhe, 3)
        form.addRow("Arritmias:", arritmias_layout)
        
        # Valvulopatias
        valvular_layout = QHBoxLayout()
        self.valvular_combo = QComboBox()
        self.valvular_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.valvular_combo.setStyleSheet(self._estilo_campo_compacto())
        self.valvular_detalhe = QLineEdit()
        self.valvular_detalhe.setPlaceholderText("Válvula e grau")
        self.valvular_detalhe.setStyleSheet(self._estilo_campo_compacto())
        valvular_layout.addWidget(self.valvular_combo, 1)
        valvular_layout.addWidget(self.valvular_detalhe, 3)
        form.addRow("Valvulopatias:", valvular_layout)
        
        # Doença vascular periférica
        vascular_layout = QHBoxLayout()
        self.vascular_combo = QComboBox()
        self.vascular_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.vascular_combo.setStyleSheet(self._estilo_campo_compacto())
        self.vascular_detalhe = QLineEdit()
        self.vascular_detalhe.setPlaceholderText("Varizes/TEP/TVP/arteriopatia")
        self.vascular_detalhe.setStyleSheet(self._estilo_campo_compacto())
        vascular_layout.addWidget(self.vascular_combo, 1)
        vascular_layout.addWidget(self.vascular_detalhe, 3)
        form.addRow("Doença vascular periférica:", vascular_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_respiratorias_compacta(self, layout):
        """3) Respiratórias - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🫁 3) Respiratórias", "#03a9f4")
        form = QFormLayout()
        
        # Asma
        asma_layout = QHBoxLayout()
        self.asma_combo = QComboBox()
        self.asma_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.asma_combo.setStyleSheet(self._estilo_campo_compacto())
        self.asma_detalhe = QLineEdit()
        self.asma_detalhe.setPlaceholderText("Grau controlo/medicação/desencadeantes")
        self.asma_detalhe.setStyleSheet(self._estilo_campo_compacto())
        asma_layout.addWidget(self.asma_combo, 1)
        asma_layout.addWidget(self.asma_detalhe, 3)
        form.addRow("Asma:", asma_layout)
        
        # DPOC
        dpoc_layout = QHBoxLayout()
        self.dpoc_combo = QComboBox()
        self.dpoc_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dpoc_combo.setStyleSheet(self._estilo_campo_compacto())
        self.dpoc_detalhe = QLineEdit()
        self.dpoc_detalhe.setPlaceholderText("Estadio GOLD/oxigenoterapia/exacerbações")
        self.dpoc_detalhe.setStyleSheet(self._estilo_campo_compacto())
        dpoc_layout.addWidget(self.dpoc_combo, 1)
        dpoc_layout.addWidget(self.dpoc_detalhe, 3)
        form.addRow("DPOC:", dpoc_layout)
        
        # Apneia do sono
        apneia_layout = QHBoxLayout()
        self.apneia_combo = QComboBox()
        self.apneia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.apneia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.apneia_detalhe = QLineEdit()
        self.apneia_detalhe.setPlaceholderText("CPAP/BiPAP - IAH médio")
        self.apneia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        apneia_layout.addWidget(self.apneia_combo, 1)
        apneia_layout.addWidget(self.apneia_detalhe, 3)
        form.addRow("Apneia do sono:", apneia_layout)
        
        # Outras doenças respiratórias
        outras_resp_layout = QHBoxLayout()
        self.outras_resp_combo = QComboBox()
        self.outras_resp_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.outras_resp_combo.setStyleSheet(self._estilo_campo_compacto())
        self.outras_resp_detalhe = QLineEdit()
        self.outras_resp_detalhe.setPlaceholderText("Pneumonia/embolia/fibrose")
        self.outras_resp_detalhe.setStyleSheet(self._estilo_campo_compacto())
        outras_resp_layout.addWidget(self.outras_resp_combo, 1)
        outras_resp_layout.addWidget(self.outras_resp_detalhe, 3)
        form.addRow("Outras doenças respiratórias:", outras_resp_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_gastrointestinais_compacta(self, layout):
        """4) Gastrointestinais - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🍽️ 4) Gastrointestinais", "#ff9800")
        form = QFormLayout()
        
        # DRGE / Úlcera péptica
        drge_layout = QHBoxLayout()
        self.drge_combo = QComboBox()
        self.drge_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.drge_combo.setStyleSheet(self._estilo_campo_compacto())
        self.drge_detalhe = QLineEdit()
        self.drge_detalhe.setPlaceholderText("IBP crónico? H. pylori?")
        self.drge_detalhe.setStyleSheet(self._estilo_campo_compacto())
        drge_layout.addWidget(self.drge_combo, 1)
        drge_layout.addWidget(self.drge_detalhe, 3)
        form.addRow("DRGE / Úlcera péptica:", drge_layout)
        
        # DII (Crohn / RCU)
        dii_layout = QHBoxLayout()
        self.dii_combo = QComboBox()
        self.dii_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dii_combo.setStyleSheet(self._estilo_campo_compacto())
        self.dii_detalhe = QLineEdit()
        self.dii_detalhe.setPlaceholderText("Qual? Atividade/localização/tratamento")
        self.dii_detalhe.setStyleSheet(self._estilo_campo_compacto())
        dii_layout.addWidget(self.dii_combo, 1)
        dii_layout.addWidget(self.dii_detalhe, 3)
        form.addRow("DII (Crohn / RCU):", dii_layout)
        
        # SII / Dispepsia funcional
        sii_layout = QHBoxLayout()
        self.sii_combo = QComboBox()
        self.sii_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.sii_combo.setStyleSheet(self._estilo_campo_compacto())
        self.sii_detalhe = QLineEdit()
        self.sii_detalhe.setPlaceholderText("Medicação sintomática")
        self.sii_detalhe.setStyleSheet(self._estilo_campo_compacto())
        sii_layout.addWidget(self.sii_combo, 1)
        sii_layout.addWidget(self.sii_detalhe, 3)
        form.addRow("SII / Dispepsia funcional:", sii_layout)
        
        # Intolerâncias alimentares
        intolerancias_layout = QHBoxLayout()
        self.intolerancias_combo = QComboBox()
        self.intolerancias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.intolerancias_combo.setStyleSheet(self._estilo_campo_compacto())
        self.intolerancias_detalhe = QLineEdit()
        self.intolerancias_detalhe.setPlaceholderText("Lactose/glúten/FODMAP")
        self.intolerancias_detalhe.setStyleSheet(self._estilo_campo_compacto())
        intolerancias_layout.addWidget(self.intolerancias_combo, 1)
        intolerancias_layout.addWidget(self.intolerancias_detalhe, 3)
        form.addRow("Intolerâncias alimentares:", intolerancias_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_neurologicas_compacta(self, layout):
        """5) Neurológicas/Psiquiátricas - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🧠 5) Neurológicas/Psiquiátricas", "#9c27b0")
        form = QFormLayout()
        
        # Epilepsia
        epilepsia_layout = QHBoxLayout()
        self.epilepsia_combo = QComboBox()
        self.epilepsia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.epilepsia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.epilepsia_detalhe = QLineEdit()
        self.epilepsia_detalhe.setPlaceholderText("Antiepilépticos/última crise/trigger")
        self.epilepsia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        epilepsia_layout.addWidget(self.epilepsia_combo, 1)
        epilepsia_layout.addWidget(self.epilepsia_detalhe, 3)
        form.addRow("Epilepsia:", epilepsia_layout)
        
        # AVC / AIT
        avc_layout = QHBoxLayout()
        self.avc_combo = QComboBox()
        self.avc_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.avc_combo.setStyleSheet(self._estilo_campo_compacto())
        self.avc_detalhe = QLineEdit()
        self.avc_detalhe.setPlaceholderText("Território/défices residuais/anticoagulação")
        self.avc_detalhe.setStyleSheet(self._estilo_campo_compacto())
        avc_layout.addWidget(self.avc_combo, 1)
        avc_layout.addWidget(self.avc_detalhe, 3)
        form.addRow("AVC / AIT:", avc_layout)
        
        # Enxaqueca
        enxaqueca_layout = QHBoxLayout()
        self.enxaqueca_combo = QComboBox()
        self.enxaqueca_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.enxaqueca_combo.setStyleSheet(self._estilo_campo_compacto())
        self.enxaqueca_detalhe = QLineEdit()
        self.enxaqueca_detalhe.setPlaceholderText("Frequência/preventivo/trigger")
        self.enxaqueca_detalhe.setStyleSheet(self._estilo_campo_compacto())
        enxaqueca_layout.addWidget(self.enxaqueca_combo, 1)
        enxaqueca_layout.addWidget(self.enxaqueca_detalhe, 3)
        form.addRow("Enxaqueca:", enxaqueca_layout)
        
        # Parkinson / Tremor
        parkinson_layout = QHBoxLayout()
        self.parkinson_combo = QComboBox()
        self.parkinson_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.parkinson_combo.setStyleSheet(self._estilo_campo_compacto())
        self.parkinson_detalhe = QLineEdit()
        self.parkinson_detalhe.setPlaceholderText("Tratamento/estádio")
        self.parkinson_detalhe.setStyleSheet(self._estilo_campo_compacto())
        parkinson_layout.addWidget(self.parkinson_combo, 1)
        parkinson_layout.addWidget(self.parkinson_detalhe, 3)
        form.addRow("Parkinson / Tremor:", parkinson_layout)
        
        # Demência
        demencia_layout = QHBoxLayout()
        self.demencia_combo = QComboBox()
        self.demencia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.demencia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.demencia_detalhe = QLineEdit()
        self.demencia_detalhe.setPlaceholderText("Alzheimer/vascular/Lewy - estadio")
        self.demencia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        demencia_layout.addWidget(self.demencia_combo, 1)
        demencia_layout.addWidget(self.demencia_detalhe, 3)
        form.addRow("Demência:", demencia_layout)
        
        # Depressão / Ansiedade
        psiquiatrica_layout = QHBoxLayout()
        self.psiquiatrica_combo = QComboBox()
        self.psiquiatrica_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.psiquiatrica_combo.setStyleSheet(self._estilo_campo_compacto())
        self.psiquiatrica_detalhe = QLineEdit()
        self.psiquiatrica_detalhe.setPlaceholderText("Medicação/psicoterapia/hospitalizações")
        self.psiquiatrica_detalhe.setStyleSheet(self._estilo_campo_compacto())
        psiquiatrica_layout.addWidget(self.psiquiatrica_combo, 1)
        psiquiatrica_layout.addWidget(self.psiquiatrica_detalhe, 3)
        form.addRow("Depressão / Ansiedade:", psiquiatrica_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_musculoesqueleticas_compacta(self, layout):
        """6) Músculo-esqueléticas - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("💪 6) Músculo-esqueléticas", "#795548")
        form = QFormLayout()
        
        # Artrite / Artrose
        artrite_layout = QHBoxLayout()
        self.artrite_combo = QComboBox()
        self.artrite_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.artrite_combo.setStyleSheet(self._estilo_campo_compacto())
        self.artrite_detalhe = QLineEdit()
        self.artrite_detalhe.setPlaceholderText("AR/artrose - articulações afetadas/DMARDs")
        self.artrite_detalhe.setStyleSheet(self._estilo_campo_compacto())
        artrite_layout.addWidget(self.artrite_combo, 1)
        artrite_layout.addWidget(self.artrite_detalhe, 3)
        form.addRow("Artrite / Artrose:", artrite_layout)
        
        # Osteoporose
        osteoporose_layout = QHBoxLayout()
        self.osteoporose_combo = QComboBox()
        self.osteoporose_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.osteoporose_combo.setStyleSheet(self._estilo_campo_compacto())
        self.osteoporose_detalhe = QLineEdit()
        self.osteoporose_detalhe.setPlaceholderText("T-score/medicação/fraturas")
        self.osteoporose_detalhe.setStyleSheet(self._estilo_campo_compacto())
        osteoporose_layout.addWidget(self.osteoporose_combo, 1)
        osteoporose_layout.addWidget(self.osteoporose_detalhe, 3)
        form.addRow("Osteoporose:", osteoporose_layout)
        
        # Fibromialgia
        fibromialgia_layout = QHBoxLayout()
        self.fibromialgia_combo = QComboBox()
        self.fibromialgia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.fibromialgia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.fibromialgia_detalhe = QLineEdit()
        self.fibromialgia_detalhe.setPlaceholderText("Medicação/qualidade sono")
        self.fibromialgia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        fibromialgia_layout.addWidget(self.fibromialgia_combo, 1)
        fibromialgia_layout.addWidget(self.fibromialgia_detalhe, 3)
        form.addRow("Fibromialgia:", fibromialgia_layout)
        
        # Hernias discais / Dor crónica
        hernias_layout = QHBoxLayout()
        self.hernias_combo = QComboBox()
        self.hernias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.hernias_combo.setStyleSheet(self._estilo_campo_compacto())
        self.hernias_detalhe = QLineEdit()
        self.hernias_detalhe.setPlaceholderText("Localização/cirurgia/analgésicos")
        self.hernias_detalhe.setStyleSheet(self._estilo_campo_compacto())
        hernias_layout.addWidget(self.hernias_combo, 1)
        hernias_layout.addWidget(self.hernias_detalhe, 3)
        form.addRow("Hernias discais / Dor crónica:", hernias_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_dermatologia_compacta(self, layout):
        """7) Dermatologia/Feridas - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🌟 7) Dermatologia/Feridas", "#ffeb3b")
        form = QFormLayout()
        
        # Feridas crónicas / Úlceras
        feridas_layout = QHBoxLayout()
        self.feridas_combo = QComboBox()
        self.feridas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.feridas_combo.setStyleSheet(self._estilo_campo_compacto())
        self.feridas_detalhe = QLineEdit()
        self.feridas_detalhe.setPlaceholderText("Úlceras venosas/arteriais/diabéticas - localização")
        self.feridas_detalhe.setStyleSheet(self._estilo_campo_compacto())
        feridas_layout.addWidget(self.feridas_combo, 1)
        feridas_layout.addWidget(self.feridas_detalhe, 3)
        form.addRow("Feridas crónicas / Úlceras:", feridas_layout)
        
        # Eczema / Psoríase
        eczema_layout = QHBoxLayout()
        self.eczema_combo = QComboBox()
        self.eczema_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.eczema_combo.setStyleSheet(self._estilo_campo_compacto())
        self.eczema_detalhe = QLineEdit()
        self.eczema_detalhe.setPlaceholderText("Localização/triggers/tratamento")
        self.eczema_detalhe.setStyleSheet(self._estilo_campo_compacto())
        eczema_layout.addWidget(self.eczema_combo, 1)
        eczema_layout.addWidget(self.eczema_detalhe, 3)
        form.addRow("Eczema / Psoríase:", eczema_layout)
        
        # Cicatrização anormal
        cicatrizacao_layout = QHBoxLayout()
        self.cicatrizacao_combo = QComboBox()
        self.cicatrizacao_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.cicatrizacao_combo.setStyleSheet(self._estilo_campo_compacto())
        self.cicatrizacao_detalhe = QLineEdit()
        self.cicatrizacao_detalhe.setPlaceholderText("Queloide/cicatrização lenta")
        self.cicatrizacao_detalhe.setStyleSheet(self._estilo_campo_compacto())
        cicatrizacao_layout.addWidget(self.cicatrizacao_combo, 1)
        cicatrizacao_layout.addWidget(self.cicatrizacao_detalhe, 3)
        form.addRow("Cicatrização anormal:", cicatrizacao_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_alergias_compacta(self, layout):
        """8) Alergias/Intolerâncias - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🤧 8) Alergias/Intolerâncias", "#8bc34a")
        form = QFormLayout()
        
        # Alergias medicamentosas
        alergia_med_layout = QHBoxLayout()
        self.alergias_medicamentos_combo = QComboBox()
        self.alergias_medicamentos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alergias_medicamentos_combo.setStyleSheet(self._estilo_campo_compacto())
        self.alergias_medicamentos_detalhe = QLineEdit()
        self.alergias_medicamentos_detalhe.setPlaceholderText("Penicilina/AINES/outros - reação")
        self.alergias_medicamentos_detalhe.setStyleSheet(self._estilo_campo_compacto())
        alergia_med_layout.addWidget(self.alergias_medicamentos_combo, 1)
        alergia_med_layout.addWidget(self.alergias_medicamentos_detalhe, 3)
        form.addRow("Alergias medicamentosas:", alergia_med_layout)
        
        # Alergias alimentares
        alergia_alim_layout = QHBoxLayout()
        self.alergias_alimentares_combo = QComboBox()
        self.alergias_alimentares_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alergias_alimentares_combo.setStyleSheet(self._estilo_campo_compacto())
        self.alergias_alimentares_detalhe = QLineEdit()
        self.alergias_alimentares_detalhe.setPlaceholderText("Marisco/frutos secos/outros")
        self.alergias_alimentares_detalhe.setStyleSheet(self._estilo_campo_compacto())
        alergia_alim_layout.addWidget(self.alergias_alimentares_combo, 1)
        alergia_alim_layout.addWidget(self.alergias_alimentares_detalhe, 3)
        form.addRow("Alergias alimentares:", alergia_alim_layout)
        
        # Alergias ambientais
        alergia_amb_layout = QHBoxLayout()
        self.alergias_ambientais_combo = QComboBox()
        self.alergias_ambientais_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alergias_ambientais_combo.setStyleSheet(self._estilo_campo_compacto())
        self.alergias_ambientais_detalhe = QLineEdit()
        self.alergias_ambientais_detalhe.setPlaceholderText("Pólen/ácaros/animais")
        self.alergias_ambientais_detalhe.setStyleSheet(self._estilo_campo_compacto())
        alergia_amb_layout.addWidget(self.alergias_ambientais_combo, 1)
        alergia_amb_layout.addWidget(self.alergias_ambientais_detalhe, 3)
        form.addRow("Alergias ambientais:", alergia_amb_layout)
        
        # Anafilaxia
        anafilaxia_layout = QHBoxLayout()
        self.anafilaxia_combo = QComboBox()
        self.anafilaxia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.anafilaxia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.anafilaxia_detalhe = QLineEdit()
        self.anafilaxia_detalhe.setPlaceholderText("Trigger/EpiPen")
        self.anafilaxia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        anafilaxia_layout.addWidget(self.anafilaxia_combo, 1)
        anafilaxia_layout.addWidget(self.anafilaxia_detalhe, 3)
        form.addRow("Anafilaxia:", anafilaxia_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_infecciosas_compacta(self, layout):
        """9) Infecciosas/Imunológicas - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🦠 9) Infecciosas/Imunológicas", "#607d8b")
        form = QFormLayout()
        
        # HIV / Hepatites
        hiv_hepatites_layout = QHBoxLayout()
        self.hiv_hepatites_combo = QComboBox()
        self.hiv_hepatites_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.hiv_hepatites_combo.setStyleSheet(self._estilo_campo_compacto())
        self.hiv_hepatites_detalhe = QLineEdit()
        self.hiv_hepatites_detalhe.setPlaceholderText("HIV/Hepatite B/C - carga viral/tratamento")
        self.hiv_hepatites_detalhe.setStyleSheet(self._estilo_campo_compacto())
        hiv_hepatites_layout.addWidget(self.hiv_hepatites_combo, 1)
        hiv_hepatites_layout.addWidget(self.hiv_hepatites_detalhe, 3)
        form.addRow("HIV / Hepatites:", hiv_hepatites_layout)
        
        # Tuberculose
        tuberculose_layout = QHBoxLayout()
        self.tuberculose_combo = QComboBox()
        self.tuberculose_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.tuberculose_combo.setStyleSheet(self._estilo_campo_compacto())
        self.tuberculose_detalhe = QLineEdit()
        self.tuberculose_detalhe.setPlaceholderText("Ativa/latente - tratamento completo?")
        self.tuberculose_detalhe.setStyleSheet(self._estilo_campo_compacto())
        tuberculose_layout.addWidget(self.tuberculose_combo, 1)
        tuberculose_layout.addWidget(self.tuberculose_detalhe, 3)
        form.addRow("Tuberculose:", tuberculose_layout)
        
        # Imunodeficiência
        imunodeficiencia_layout = QHBoxLayout()
        self.imunodeficiencia_combo = QComboBox()
        self.imunodeficiencia_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.imunodeficiencia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.imunodeficiencia_detalhe = QLineEdit()
        self.imunodeficiencia_detalhe.setPlaceholderText("Primária/secundária - infecções recorrentes")
        self.imunodeficiencia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        imunodeficiencia_layout.addWidget(self.imunodeficiencia_combo, 1)
        imunodeficiencia_layout.addWidget(self.imunodeficiencia_detalhe, 3)
        form.addRow("Imunodeficiência:", imunodeficiencia_layout)
        
        # Vacinas em atraso
        vacinas_layout = QHBoxLayout()
        self.vacinas_combo = QComboBox()
        self.vacinas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.vacinas_combo.setStyleSheet(self._estilo_campo_compacto())
        self.vacinas_detalhe = QLineEdit()
        self.vacinas_detalhe.setPlaceholderText("Quais vacinas em falta")
        self.vacinas_detalhe.setStyleSheet(self._estilo_campo_compacto())
        vacinas_layout.addWidget(self.vacinas_combo, 1)
        vacinas_layout.addWidget(self.vacinas_detalhe, 3)
        form.addRow("Vacinas em atraso:", vacinas_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_oncologia_compacta(self, layout):
        """10) Oncologia - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🎗️ 10) Oncologia", "#e91e63")
        form = QFormLayout()
        
        # História de cancro
        cancro_layout = QHBoxLayout()
        self.cancro_combo = QComboBox()
        self.cancro_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.cancro_combo.setStyleSheet(self._estilo_campo_compacto())
        self.cancro_detalhe = QLineEdit()
        self.cancro_detalhe.setPlaceholderText("Tipo/estadio/ano diagnóstico")
        self.cancro_detalhe.setStyleSheet(self._estilo_campo_compacto())
        cancro_layout.addWidget(self.cancro_combo, 1)
        cancro_layout.addWidget(self.cancro_detalhe, 3)
        form.addRow("História de cancro:", cancro_layout)
        
        # Quimioterapia / Radioterapia
        quimio_radio_layout = QHBoxLayout()
        self.quimio_radio_combo = QComboBox()
        self.quimio_radio_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.quimio_radio_combo.setStyleSheet(self._estilo_campo_compacto())
        self.quimio_radio_detalhe = QLineEdit()
        self.quimio_radio_detalhe.setPlaceholderText("Protocolo/área irradiada/sequelas")
        self.quimio_radio_detalhe.setStyleSheet(self._estilo_campo_compacto())
        quimio_radio_layout.addWidget(self.quimio_radio_combo, 1)
        quimio_radio_layout.addWidget(self.quimio_radio_detalhe, 3)
        form.addRow("Quimioterapia / Radioterapia:", quimio_radio_layout)
        
        # História familiar oncológica
        familia_onco_layout = QHBoxLayout()
        self.familia_onco_combo = QComboBox()
        self.familia_onco_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.familia_onco_combo.setStyleSheet(self._estilo_campo_compacto())
        self.familia_onco_detalhe = QLineEdit()
        self.familia_onco_detalhe.setPlaceholderText("Parentesco/tipo cancro/idade")
        self.familia_onco_detalhe.setStyleSheet(self._estilo_campo_compacto())
        familia_onco_layout.addWidget(self.familia_onco_combo, 1)
        familia_onco_layout.addWidget(self.familia_onco_detalhe, 3)
        form.addRow("História familiar oncológica:", familia_onco_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_reprodutiva_compacta(self, layout):
        """11) Saúde Reprodutiva - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("👶 11) Saúde Reprodutiva", "#ff5722")
        form = QFormLayout()
        
        # Gravidez / Amamentação
        gravidez_layout = QHBoxLayout()
        self.gravidez_combo = QComboBox()
        self.gravidez_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.gravidez_combo.setStyleSheet(self._estilo_campo_compacto())
        self.gravidez_detalhe = QLineEdit()
        self.gravidez_detalhe.setPlaceholderText("Semanas gestação/complicações/amamentação")
        self.gravidez_detalhe.setStyleSheet(self._estilo_campo_compacto())
        gravidez_layout.addWidget(self.gravidez_combo, 1)
        gravidez_layout.addWidget(self.gravidez_detalhe, 3)
        form.addRow("Gravidez / Amamentação:", gravidez_layout)
        
        # Contraceção hormonal
        contraceção_layout = QHBoxLayout()
        self.contraceção_combo = QComboBox()
        self.contraceção_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.contraceção_combo.setStyleSheet(self._estilo_campo_compacto())
        self.contraceção_detalhe = QLineEdit()
        self.contraceção_detalhe.setPlaceholderText("Pílula/DIU/implante - há quanto tempo")
        self.contraceção_detalhe.setStyleSheet(self._estilo_campo_compacto())
        contraceção_layout.addWidget(self.contraceção_combo, 1)
        contraceção_layout.addWidget(self.contraceção_detalhe, 3)
        form.addRow("Contraceção hormonal:", contraceção_layout)
        
        # Menopausa / THS
        menopausa_layout = QHBoxLayout()
        self.menopausa_combo = QComboBox()
        self.menopausa_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.menopausa_combo.setStyleSheet(self._estilo_campo_compacto())
        self.menopausa_detalhe = QLineEdit()
        self.menopausa_detalhe.setPlaceholderText("Idade/THS atual")
        self.menopausa_detalhe.setStyleSheet(self._estilo_campo_compacto())
        menopausa_layout.addWidget(self.menopausa_combo, 1)
        menopausa_layout.addWidget(self.menopausa_detalhe, 3)
        form.addRow("Menopausa / THS:", menopausa_layout)
        
        # Problemas reprodutivos
        problemas_repro_layout = QHBoxLayout()
        self.problemas_repro_combo = QComboBox()
        self.problemas_repro_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.problemas_repro_combo.setStyleSheet(self._estilo_campo_compacto())
        self.problemas_repro_detalhe = QLineEdit()
        self.problemas_repro_detalhe.setPlaceholderText("Infertilidade/SOP/endometriose")
        self.problemas_repro_detalhe.setStyleSheet(self._estilo_campo_compacto())
        problemas_repro_layout.addWidget(self.problemas_repro_combo, 1)
        problemas_repro_layout.addWidget(self.problemas_repro_detalhe, 3)
        form.addRow("Problemas reprodutivos:", problemas_repro_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_cirurgias_compacta(self, layout):
        """12) Cirurgias/Internamentos/Traumas - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🔪 12) Cirurgias/Internamentos/Traumas", "#009688")
        form = QFormLayout()
        
        # Cirurgias prévias
        self.cirurgias_combo = QComboBox()
        self.cirurgias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.cirurgias_combo.setStyleSheet(self._estilo_campo_compacto())
        self.cirurgias_detalhe = QLineEdit()
        self.cirurgias_detalhe.setPlaceholderText("Tipo/ano/complicações/anestesia")
        self.cirurgias_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        cirurgias_layout = QHBoxLayout()
        cirurgias_layout.addWidget(self.cirurgias_combo, 1)
        cirurgias_layout.addWidget(self.cirurgias_detalhe, 3)
        form.addRow("Cirurgias prévias:", cirurgias_layout)
        
        # Internamentos
        internamentos_layout = QHBoxLayout()
        self.internamentos_combo = QComboBox()
        self.internamentos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.internamentos_combo.setStyleSheet(self._estilo_campo_compacto())
        self.internamentos_detalhe = QLineEdit()
        self.internamentos_detalhe.setPlaceholderText("Motivo/duração/UCI")
        self.internamentos_detalhe.setStyleSheet(self._estilo_campo_compacto())
        internamentos_layout.addWidget(self.internamentos_combo, 1)
        internamentos_layout.addWidget(self.internamentos_detalhe, 3)
        form.addRow("Internamentos:", internamentos_layout)
        
        # Traumas / Fraturas
        traumas_layout = QHBoxLayout()
        self.traumas_combo = QComboBox()
        self.traumas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.traumas_combo.setStyleSheet(self._estilo_campo_compacto())
        self.traumas_detalhe = QLineEdit()
        self.traumas_detalhe.setPlaceholderText("TCE/fraturas/sequelas")
        self.traumas_detalhe.setStyleSheet(self._estilo_campo_compacto())
        traumas_layout.addWidget(self.traumas_combo, 1)
        traumas_layout.addWidget(self.traumas_detalhe, 3)
        form.addRow("Traumas / Fraturas:", traumas_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_implantes_compacta(self, layout):
        """13) Implantes e Dispositivos - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("⚕️ 13) Implantes e Dispositivos", "#3f51b5")
        form = QFormLayout()
        
        # Implantes metálicos
        self.implantes_metalicos_combo = QComboBox()
        self.implantes_metalicos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.implantes_metalicos_combo.setStyleSheet(self._estilo_campo_compacto())
        self.implantes_metalicos_detalhe = QLineEdit()
        self.implantes_metalicos_detalhe.setPlaceholderText("Placas/parafusos/próteses - localização")
        self.implantes_metalicos_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        implantes_layout = QHBoxLayout()
        implantes_layout.addWidget(self.implantes_metalicos_combo, 1)
        implantes_layout.addWidget(self.implantes_metalicos_detalhe, 3)
        form.addRow("Implantes metálicos:", implantes_layout)
        
        # Pacemaker / CDI / Resynchronizer
        pacemaker_layout = QHBoxLayout()
        self.pacemaker_combo = QComboBox()
        self.pacemaker_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.pacemaker_combo.setStyleSheet(self._estilo_campo_compacto())
        self.pacemaker_detalhe = QLineEdit()
        self.pacemaker_detalhe.setPlaceholderText("Tipo/modelo/última revisão")
        self.pacemaker_detalhe.setStyleSheet(self._estilo_campo_compacto())
        pacemaker_layout.addWidget(self.pacemaker_combo, 1)
        pacemaker_layout.addWidget(self.pacemaker_detalhe, 3)
        form.addRow("Pacemaker / CDI / Resynchronizer:", pacemaker_layout)
        
        # Válvulas cardíacas
        valvulas_layout = QHBoxLayout()
        self.valvulas_combo = QComboBox()
        self.valvulas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.valvulas_combo.setStyleSheet(self._estilo_campo_compacto())
        self.valvulas_detalhe = QLineEdit()
        self.valvulas_detalhe.setPlaceholderText("Mecânica/biológica - qual válvula")
        self.valvulas_detalhe.setStyleSheet(self._estilo_campo_compacto())
        valvulas_layout.addWidget(self.valvulas_combo, 1)
        valvulas_layout.addWidget(self.valvulas_detalhe, 3)
        form.addRow("Válvulas cardíacas:", valvulas_layout)
        
        # Outros dispositivos
        outros_dispositivos_layout = QHBoxLayout()
        self.outros_dispositivos_combo = QComboBox()
        self.outros_dispositivos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.outros_dispositivos_combo.setStyleSheet(self._estilo_campo_compacto())
        self.outros_dispositivos_detalhe = QLineEdit()
        self.outros_dispositivos_detalhe.setPlaceholderText("Stents/mesh/clips/DIU")
        self.outros_dispositivos_detalhe.setStyleSheet(self._estilo_campo_compacto())
        outros_dispositivos_layout.addWidget(self.outros_dispositivos_combo, 1)
        outros_dispositivos_layout.addWidget(self.outros_dispositivos_detalhe, 3)
        form.addRow("Outros dispositivos:", outros_dispositivos_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_medicacao_compacta(self, layout):
        """14) Medicação e Suplementos - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("💊 14) Medicação e Suplementos", "#2196f3")
        form = QFormLayout()
        
        # Anticoagulantes / Antiagregantes
        self.anticoagulantes_combo = QComboBox()
        self.anticoagulantes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.anticoagulantes_combo.setStyleSheet(self._estilo_campo_compacto())
        self.anticoagulantes_detalhe = QLineEdit()
        self.anticoagulantes_detalhe.setPlaceholderText("Varfarina/Sintrom/Eliquis/AAS - dose/INR")
        self.anticoagulantes_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        medicacao_layout = QHBoxLayout()
        medicacao_layout.addWidget(self.anticoagulantes_combo, 1)
        medicacao_layout.addWidget(self.anticoagulantes_detalhe, 3)
        form.addRow("Anticoagulantes / Antiagregantes:", medicacao_layout)
        
        # Corticoides
        corticoides_layout = QHBoxLayout()
        self.corticoides_combo = QComboBox()
        self.corticoides_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.corticoides_combo.setStyleSheet(self._estilo_campo_compacto())
        self.corticoides_detalhe = QLineEdit()
        self.corticoides_detalhe.setPlaceholderText("Prednisolona/hidrocortisona - dose/duração")
        self.corticoides_detalhe.setStyleSheet(self._estilo_campo_compacto())
        corticoides_layout.addWidget(self.corticoides_combo, 1)
        corticoides_layout.addWidget(self.corticoides_detalhe, 3)
        form.addRow("Corticoides:", corticoides_layout)
        
        # Imunossupressores
        imunossupressores_layout = QHBoxLayout()
        self.imunossupressores_combo = QComboBox()
        self.imunossupressores_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.imunossupressores_combo.setStyleSheet(self._estilo_campo_compacto())
        self.imunossupressores_detalhe = QLineEdit()
        self.imunossupressores_detalhe.setPlaceholderText("Metotrexato/biologicos - indicação")
        self.imunossupressores_detalhe.setStyleSheet(self._estilo_campo_compacto())
        imunossupressores_layout.addWidget(self.imunossupressores_combo, 1)
        imunossupressores_layout.addWidget(self.imunossupressores_detalhe, 3)
        form.addRow("Imunossupressores:", imunossupressores_layout)
        
        # Suplementos / Fitoterápicos
        suplementos_layout = QHBoxLayout()
        self.suplementos_combo = QComboBox()
        self.suplementos_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.suplementos_combo.setStyleSheet(self._estilo_campo_compacto())
        self.suplementos_detalhe = QLineEdit()
        self.suplementos_detalhe.setPlaceholderText("Vitaminas/minerais/ervas medicinais")
        self.suplementos_detalhe.setStyleSheet(self._estilo_campo_compacto())
        suplementos_layout.addWidget(self.suplementos_combo, 1)
        suplementos_layout.addWidget(self.suplementos_detalhe, 3)
        form.addRow("Suplementos / Fitoterápicos:", suplementos_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_estilo_vida_compacta(self, layout):
        """15) Estilo de Vida - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🏃 15) Estilo de Vida", "#4caf50")
        form = QFormLayout()
        
        # Tabaco
        self.tabaco_combo = QComboBox()
        self.tabaco_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.tabaco_combo.setStyleSheet(self._estilo_campo_compacto())
        self.tabaco_detalhe = QLineEdit()
        self.tabaco_detalhe.setPlaceholderText("Cigarros/dia - há quanto tempo/ex-fumador desde")
        self.tabaco_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        tabaco_layout = QHBoxLayout()
        tabaco_layout.addWidget(self.tabaco_combo, 1)
        tabaco_layout.addWidget(self.tabaco_detalhe, 3)
        form.addRow("Tabaco:", tabaco_layout)
        
        # Álcool
        alcool_layout = QHBoxLayout()
        self.alcool_combo = QComboBox()
        self.alcool_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alcool_combo.setStyleSheet(self._estilo_campo_compacto())
        self.alcool_detalhe = QLineEdit()
        self.alcool_detalhe.setPlaceholderText("Unidades/semana - tipo bebida")
        self.alcool_detalhe.setStyleSheet(self._estilo_campo_compacto())
        alcool_layout.addWidget(self.alcool_combo, 1)
        alcool_layout.addWidget(self.alcool_detalhe, 3)
        form.addRow("Álcool:", alcool_layout)
        
        # Drogas recreativas
        drogas_layout = QHBoxLayout()
        self.drogas_combo = QComboBox()
        self.drogas_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.drogas_combo.setStyleSheet(self._estilo_campo_compacto())
        self.drogas_detalhe = QLineEdit()
        self.drogas_detalhe.setPlaceholderText("Tipo/frequência")
        self.drogas_detalhe.setStyleSheet(self._estilo_campo_compacto())
        drogas_layout.addWidget(self.drogas_combo, 1)
        drogas_layout.addWidget(self.drogas_detalhe, 3)
        form.addRow("Drogas recreativas:", drogas_layout)
        
        # Exercício físico
        exercicio_layout = QHBoxLayout()
        self.exercicio_combo = QComboBox()
        self.exercicio_combo.addItems(["Selecionar...", "Regular", "Ocasional", "Sedentário"])
        self.exercicio_combo.setStyleSheet(self._estilo_campo_compacto())
        self.exercicio_detalhe = QLineEdit()
        self.exercicio_detalhe.setPlaceholderText("Tipo/frequência/intensidade")
        self.exercicio_detalhe.setStyleSheet(self._estilo_campo_compacto())
        exercicio_layout.addWidget(self.exercicio_combo, 1)
        exercicio_layout.addWidget(self.exercicio_detalhe, 3)
        form.addRow("Exercício físico:", exercicio_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_exames_compacta(self, layout):
        """16) Exames - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("📊 16) Exames", "#ffc107")
        form = QFormLayout()
        
        # Exames recentes relevantes
        exames_layout = QHBoxLayout()
        self.exames_combo = QComboBox()
        self.exames_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.exames_combo.setStyleSheet(self._estilo_campo_compacto())
        self.exames_detalhe = QLineEdit()
        self.exames_detalhe.setPlaceholderText("Análises/imagiologia/outros - data/resultados relevantes")
        self.exames_detalhe.setStyleSheet(self._estilo_campo_compacto())
        exames_layout.addWidget(self.exames_combo, 1)
        exames_layout.addWidget(self.exames_detalhe, 3)
        form.addRow("Exames recentes relevantes:", exames_layout)
        
        # Rastreios em atraso
        rastreios_layout = QHBoxLayout()
        self.rastreios_combo = QComboBox()
        self.rastreios_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.rastreios_combo.setStyleSheet(self._estilo_campo_compacto())
        self.rastreios_detalhe = QLineEdit()
        self.rastreios_detalhe.setPlaceholderText("Mamografia/colonoscopia/citologia - último")
        self.rastreios_detalhe.setStyleSheet(self._estilo_campo_compacto())
        rastreios_layout.addWidget(self.rastreios_combo, 1)
        rastreios_layout.addWidget(self.rastreios_detalhe, 3)
        form.addRow("Rastreios em atraso:", rastreios_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_red_flags_compacta(self, layout):
        """17) Red Flags - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("🚨 17) Red Flags", "#f44336")
        form = QFormLayout()
        
        # Perda de peso não intencional
        peso_layout = QHBoxLayout()
        self.peso_red_flag_combo = QComboBox()
        self.peso_red_flag_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.peso_red_flag_combo.setStyleSheet(self._estilo_campo_compacto())
        self.peso_red_flag_detalhe = QLineEdit()
        self.peso_red_flag_detalhe.setPlaceholderText("Quantos kg em quanto tempo")
        self.peso_red_flag_detalhe.setStyleSheet(self._estilo_campo_compacto())
        peso_layout.addWidget(self.peso_red_flag_combo, 1)
        peso_layout.addWidget(self.peso_red_flag_detalhe, 3)
        form.addRow("Perda de peso não intencional:", peso_layout)
        
        # Febre persistente
        febre_layout = QHBoxLayout()
        self.febre_combo = QComboBox()
        self.febre_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.febre_combo.setStyleSheet(self._estilo_campo_compacto())
        self.febre_detalhe = QLineEdit()
        self.febre_detalhe.setPlaceholderText("Duração/padrão/sintomas associados")
        self.febre_detalhe.setStyleSheet(self._estilo_campo_compacto())
        febre_layout.addWidget(self.febre_combo, 1)
        febre_layout.addWidget(self.febre_detalhe, 3)
        form.addRow("Febre persistente:", febre_layout)
        
        # Dor intensa não controlada
        dor_layout = QHBoxLayout()
        self.dor_intensa_combo = QComboBox()
        self.dor_intensa_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.dor_intensa_combo.setStyleSheet(self._estilo_campo_compacto())
        self.dor_intensa_detalhe = QLineEdit()
        self.dor_intensa_detalhe.setPlaceholderText("Localização/intensidade/início")
        self.dor_intensa_detalhe.setStyleSheet(self._estilo_campo_compacto())
        dor_layout.addWidget(self.dor_intensa_combo, 1)
        dor_layout.addWidget(self.dor_intensa_detalhe, 3)
        form.addRow("Dor intensa não controlada:", dor_layout)
        
        # Outros sintomas de alarme
        alarme_layout = QHBoxLayout()
        self.alarme_combo = QComboBox()
        self.alarme_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.alarme_combo.setStyleSheet(self._estilo_campo_compacto())
        self.alarme_detalhe = QLineEdit()
        self.alarme_detalhe.setPlaceholderText("Sangramento/dispneia/alterações neurológicas")
        self.alarme_detalhe.setStyleSheet(self._estilo_campo_compacto())
        alarme_layout.addWidget(self.alarme_combo, 1)
        alarme_layout.addWidget(self.alarme_detalhe, 3)
        form.addRow("Outros sintomas de alarme:", alarme_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_outras_questoes_compacta(self, layout):
        """18) Outras Questões Relevantes - NOVA SEÇÃO"""
        secao = self._criar_secao_profissional_compacta("📝 18) Outras Questões Relevantes", "#795548")
        form = QFormLayout()
        
        # Campo de texto livre para questões não abordadas
        self.outras_questoes_texto = QTextEdit()
        self.outras_questoes_texto.setMaximumHeight(120)
        self.outras_questoes_texto.setPlaceholderText(
            "Descreva qualquer condição médica, sintoma, preocupação ou informação relevante "
            "que não foi abordada nas seções anteriores deste questionário. "
            "Inclua detalhes sobre medicações não mencionadas, tratamentos alternativos, "
            "histórico familiar relevante ou qualquer outra questão que considere importante "
            "para o seu cuidado médico."
        )
        self.outras_questoes_texto.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                font-size: 11px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #795548;
                outline: none;
            }
        """)
        
        form.addRow("Informações adicionais:", self.outras_questoes_texto)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_preferencias_compacta(self, layout):
        """19) Preferências/Limites - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("⚙️ 19) Preferências/Limites", "#9e9e9e")
        form = QFormLayout()
        
        # Preferências terapêuticas
        preferencias_layout = QHBoxLayout()
        self.preferencias_combo = QComboBox()
        self.preferencias_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.preferencias_combo.setStyleSheet(self._estilo_campo_compacto())
        self.preferencias_detalhe = QLineEdit()
        self.preferencias_detalhe.setPlaceholderText("Medicina natural/evitar fármacos/preferências religiosas")
        self.preferencias_detalhe.setStyleSheet(self._estilo_campo_compacto())
        preferencias_layout.addWidget(self.preferencias_combo, 1)
        preferencias_layout.addWidget(self.preferencias_detalhe, 3)
        form.addRow("Preferências terapêuticas específicas:", preferencias_layout)
        
        # Limitações físicas/mobilidade
        limitacoes_layout = QHBoxLayout()
        self.limitacoes_combo = QComboBox()
        self.limitacoes_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.limitacoes_combo.setStyleSheet(self._estilo_campo_compacto())
        self.limitacoes_detalhe = QLineEdit()
        self.limitacoes_detalhe.setPlaceholderText("Cadeira rodas/andarilho/limitações específicas")
        self.limitacoes_detalhe.setStyleSheet(self._estilo_campo_compacto())
        limitacoes_layout.addWidget(self.limitacoes_combo, 1)
        limitacoes_layout.addWidget(self.limitacoes_detalhe, 3)
        form.addRow("Limitações físicas/mobilidade:", limitacoes_layout)
        
        # Cuidados especiais necessários
        cuidados_layout = QHBoxLayout()
        self.cuidados_combo = QComboBox()
        self.cuidados_combo.addItems(["Selecionar...", "Sim", "Não"])
        self.cuidados_combo.setStyleSheet(self._estilo_campo_compacto())
        self.cuidados_detalhe = QLineEdit()
        self.cuidados_detalhe.setPlaceholderText("Tradutor/acompanhante/cuidados especiais")
        self.cuidados_detalhe.setStyleSheet(self._estilo_campo_compacto())
        cuidados_layout.addWidget(self.cuidados_combo, 1)
        cuidados_layout.addWidget(self.cuidados_detalhe, 3)
        form.addRow("Cuidados especiais necessários:", cuidados_layout)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    def _criar_secao_consentimentos_compacta(self, layout):
        """20) Consentimentos e RGPD - FORMULÁRIO COMPLETO"""
        secao = self._criar_secao_profissional_compacta("📝 20) Consentimentos e RGPD", "#673ab7")
        form = QFormLayout()
        
        # A) Declaração de veracidade (obrigatório)
        veracidade_layout = QVBoxLayout()
        veracidade_texto = QLabel(
            "A) Declaro que as informações prestadas são verdadeiras, completas e atualizadas. "
            "Qualquer omissão ou inexatidão pode comprometer a minha segurança, alterar a indicação "
            "terapêutica e isentar o profissional de responsabilidade por efeitos adversos."
        )
        veracidade_texto.setWordWrap(True)
        veracidade_texto.setStyleSheet("font-size: 11px; color: #444; margin-bottom: 8px;")
        
        self.veracidade_check = QCheckBox("✓ Confirmo a veracidade das informações prestadas (obrigatório)")
        self.veracidade_check.setStyleSheet("font-weight: bold; color: #d32f2f;")
        
        veracidade_layout.addWidget(veracidade_texto)
        veracidade_layout.addWidget(self.veracidade_check)
        form.addRow("", veracidade_layout)
        
        # B) Consentimentos por modalidade
        modalidades_titulo = QLabel("B) Consentimentos por modalidade (obrigatório escolher em todas):")
        modalidades_titulo.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px; margin-bottom: 10px;")
        form.addRow("", modalidades_titulo)
        
        # Naturopatia
        naturo_layout = QHBoxLayout()
        # BOTÃO MELHORADO: Mais informativo e intuitivo
        naturo_info_btn = QPushButton("� Ler")
        naturo_info_btn.setMinimumWidth(140)
        naturo_info_btn.setMaximumWidth(140)
        naturo_info_btn.setToolTip("Clique para ler o consentimento informado sobre naturopatia, fitoterapia e suplementação")
        naturo_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f5e8;
                color: #2e7d32;
                border: 2px solid #a5d6a7;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2e7d32;
                color: white;
                border-color: #2e7d32;
            }
        """)
        naturo_info_btn.clicked.connect(lambda: self._mostrar_info_naturopatia())
        
        self.naturopatia_combo = QComboBox()
        self.naturopatia_combo.addItems(["Selecionar...", "Aceito", "Não aceito"])
        self.naturopatia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.naturopatia_detalhe = QLineEdit()
        self.naturopatia_detalhe.setPlaceholderText("Preferências: cafeína, iodo, histamina, FODMAP...")
        self.naturopatia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        naturo_layout.addWidget(naturo_info_btn)
        naturo_layout.addWidget(self.naturopatia_combo, 1)
        naturo_layout.addWidget(self.naturopatia_detalhe, 2)
        form.addRow("Naturopatia / Fitoterapia / Suplementos:", naturo_layout)
        
        # Osteopatia
        osteo_layout = QHBoxLayout()
        # BOTÃO MELHORADO: Mais informativo e intuitivo
        osteo_info_btn = QPushButton("� Ler")
        osteo_info_btn.setMinimumWidth(140)
        osteo_info_btn.setMaximumWidth(140)
        osteo_info_btn.setToolTip("Clique para ler o consentimento informado sobre osteopatia e técnicas manuais")
        osteo_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #fff3e0;
                color: #f57c00;
                border: 2px solid #ffcc02;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f57c00;
                color: white;
                border-color: #f57c00;
            }
        """)
        osteo_info_btn.clicked.connect(lambda: self._mostrar_info_osteopatia())
        
        self.osteopatia_combo = QComboBox()
        self.osteopatia_combo.addItems(["Selecionar...", "Aceito", "Não aceito"])
        self.osteopatia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.osteopatia_detalhe = QLineEdit()
        self.osteopatia_detalhe.setPlaceholderText("Limites: evitar manipulação cervical...")
        self.osteopatia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        osteo_layout.addWidget(osteo_info_btn)
        osteo_layout.addWidget(self.osteopatia_combo, 1)
        osteo_layout.addWidget(self.osteopatia_detalhe, 2)
        form.addRow("Osteopatia / Técnicas manuais (incl. HVLA):", osteo_layout)
        
        # Mesoterapia
        meso_layout = QHBoxLayout()
        # BOTÃO MELHORADO: Mais informativo e intuitivo
        meso_info_btn = QPushButton("� Ler")
        meso_info_btn.setMinimumWidth(140)
        meso_info_btn.setMaximumWidth(140)
        meso_info_btn.setToolTip("Clique para ler o consentimento informado sobre mesoterapia homeopática")
        meso_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #fce4ec;
                color: #c2185b;
                border: 2px solid #f8bbd9;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c2185b;
                color: white;
                border-color: #c2185b;
            }
        """)
        meso_info_btn.clicked.connect(lambda: self._mostrar_info_mesoterapia())
        
        self.mesoterapia_combo = QComboBox()
        self.mesoterapia_combo.addItems(["Selecionar...", "Aceito", "Não aceito"])
        self.mesoterapia_combo.setStyleSheet(self._estilo_campo_compacto())
        self.mesoterapia_detalhe = QLineEdit()
        self.mesoterapia_detalhe.setPlaceholderText("Locais a evitar / alergias anestésicos...")
        self.mesoterapia_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        meso_layout.addWidget(meso_info_btn)
        meso_layout.addWidget(self.mesoterapia_combo, 1)
        meso_layout.addWidget(self.mesoterapia_detalhe, 2)
        form.addRow("Mesoterapia (homeopática):", meso_layout)
        
        # Medicina quântica
        quantica_layout = QHBoxLayout()
        # BOTÃO MELHORADO: Mais informativo e intuitivo
        quantica_info_btn = QPushButton("� Ler")
        quantica_info_btn.setMinimumWidth(140)
        quantica_info_btn.setMaximumWidth(140)
        quantica_info_btn.setToolTip("Clique para ler o consentimento informado sobre medicina quântica e frequencial")
        quantica_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3e5f5;
                color: #7b1fa2;
                border: 2px solid #ce93d8;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
                color: white;
                border-color: #7b1fa2;
            }
        """)
        quantica_info_btn.clicked.connect(lambda: self._mostrar_info_medicina_quantica())
        
        self.medicina_quantica_combo = QComboBox()
        self.medicina_quantica_combo.addItems(["Selecionar...", "Aceito", "Não aceito"])
        self.medicina_quantica_combo.setStyleSheet(self._estilo_campo_compacto())
        self.medicina_quantica_detalhe = QLineEdit()
        self.medicina_quantica_detalhe.setPlaceholderText("Precauções: pacemaker/dispositivos...")
        self.medicina_quantica_detalhe.setStyleSheet(self._estilo_campo_compacto())
        
        quantica_layout.addWidget(quantica_info_btn)
        quantica_layout.addWidget(self.medicina_quantica_combo, 1)
        quantica_layout.addWidget(self.medicina_quantica_detalhe, 2)
        form.addRow("Medicina quântica / frequencial:", quantica_layout)
        
        # C) Toque terapêutico
        toque_titulo = QLabel("C) Toque terapêutico e privacidade:")
        toque_titulo.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px; margin-bottom: 8px;")
        form.addRow("", toque_titulo)
        
        toque_info = QLabel("O toque é profissional, proporcional e clinicamente justificado, com draping e exposição mínima.")
        toque_info.setWordWrap(True)
        toque_info.setStyleSheet("font-size: 10px; color: #666; margin-bottom: 8px;")
        form.addRow("", toque_info)
        
        # Áreas de toque
        areas_toque = [
            ("Cabeça/pescoço/coluna", "cabeca_combo"),
            ("Ombro/membros superiores/mãos", "ombros_combo"),
            ("Anca/membros inferiores/pés", "anca_combo"),
            ("Palpação externa tórax/abdómen/pélvis", "torax_combo")
        ]
        
        for area_nome, campo_nome in areas_toque:
            area_layout = QHBoxLayout()
            combo = QComboBox()
            combo.addItems(["Selecionar...", "Sim", "Não"])
            combo.setStyleSheet(self._estilo_campo_compacto())
            setattr(self, campo_nome, combo)
            area_layout.addWidget(combo, 1)
            form.addRow(f"{area_nome}:", area_layout)
        
        # D) RGPD
        rgpd_titulo = QLabel("D) Proteção de Dados (RGPD):")
        rgpd_titulo.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px; margin-bottom: 8px;")
        form.addRow("", rgpd_titulo)
        
        rgpd_texto = QLabel(
            "Responsável: Nuno Filipe de Jesus Possante Correia (Cédula 0300450)\n"
            "Email: nunocorreiaterapiasnaturais@gmail.com • Tel: 964 860 387\n"
            "Finalidades: avaliação/intervenção, marcações, faturação, obrigações legais.\n"
            "Conservação: até 10 anos após último atendimento ou período legal aplicável."
        )
        rgpd_texto.setWordWrap(True)
        rgpd_texto.setStyleSheet("font-size: 10px; color: #444; margin-bottom: 8px;")
        form.addRow("", rgpd_texto)
        
        self.rgpd_check = QCheckBox("✓ Autorizo o tratamento dos meus dados de saúde nos termos acima (obrigatório)")
        self.rgpd_check.setStyleSheet("font-weight: bold; color: #d32f2f;")
        form.addRow("", self.rgpd_check)
        
        secao.layout().addLayout(form)
        layout.addWidget(secao)
    
    # ====== MÉTODOS INFORMATIVOS DAS MODALIDADES ======
    
    def _mostrar_info_naturopatia(self):
        """Mostra informações sobre Naturopatia/Fitoterapia"""
        QMessageBox.information(self, "🌿 Naturopatia / Fitoterapia / Suplementos", 
            "📋 INFORMAÇÃO CLÍNICA:\n\n"
            "• Riscos/precauções: alergias/intolerâncias, queixas GI, alterações de sono/PA, "
            "interações com fármacos; restrições em gravidez/amamentação.\n\n"
            "• Responsabilidade do utente: declarar toda a medicação/suplementos, marcas e doses, "
            "e comunicar alterações.\n\n"
            "• Objetivo: suporte nutricional e fitoterapêutico personalizado para otimização da saúde.\n\n"
            "⚠️ Esta modalidade pode ser aceite ou recusada sem prejuízo do acompanhamento.")
    
    def _mostrar_info_osteopatia(self):
        """Mostra informações sobre Osteopatia"""
        QMessageBox.information(self, "🤲 Osteopatia / Técnicas Manuais", 
            "📋 INFORMAÇÃO CLÍNICA:\n\n"
            "• Riscos comuns: dor/rigidez transitória (24–48 h), tontura, cefaleia; "
            "raramente agravamento temporário.\n\n"
            "• Contraindicações: fratura, infeção ativa, tumor, osteoporose grave, "
            "instabilidade cervical, défices neurológicos agudos, anticoagulação descontrolada.\n\n"
            "• Alternativas: mobilizações, MET, técnicas de tecidos moles.\n\n"
            "• Inclui HVLA (manipulação articular) quando clinicamente indicado.\n\n"
            "⚠️ Pode limitar ou recusar qualquer técnica específica.")
    
    def _mostrar_info_mesoterapia(self):
        """Mostra informações sobre Mesoterapia"""
        QMessageBox.information(self, "💉 Mesoterapia (Homeopática)", 
            "📋 INFORMAÇÃO CLÍNICA:\n\n"
            "• Riscos: dor local, hematoma, infeção, reação alérgica/vasovagal; "
            "hiperpigmentação/eritema transitório; queloide em suscetíveis.\n\n"
            "• Contraindicações: coagulopatias, INR elevado/plaquetopenia, infeção cutânea ativa, "
            "alergias pertinentes, gravidez/lactação quando aplicável.\n\n"
            "• Cuidados pós: higiene local; evitar piscinas/saunas/banhos quentes 24–48 h; "
            "vigiar sinais de infeção.\n\n"
            "• Utiliza preparações homeopáticas em microinjeções superficiais.\n\n"
            "⚠️ Informe alergias a anestésicos, antissépticos ou adesivos.")
    
    def _mostrar_info_medicina_quantica(self):
        """Mostra informações sobre Medicina Quântica"""
        QMessageBox.information(self, "⚡ Medicina Quântica / Frequencial", 
            "📋 INFORMAÇÃO CLÍNICA:\n\n"
            "• Precauções: pacemaker/DAI, neuroestimuladores, bombas de insulina; "
            "evitar aplicação direta sobre dispositivos/feridas; atenção em gravidez.\n\n"
            "• Sensações possíveis: formigueiro, calor, relaxamento; "
            "pode ajustar/pausar a qualquer momento.\n\n"
            "• Método: aplicação de frequências terapêuticas para equilíbrio energético.\n\n"
            "• Totalmente não-invasivo e indolor.\n\n"
            "⚠️ Informe todos os dispositivos eletrónicos implantados.")
    
    def _estilo_botao_info_biodesk(self, cor="#007bff"):
        """Estilo Biodesk para botões informativos pequenos"""
        return f"""
            QPushButton {{
                background-color: #f8f9fa;
                color: {cor};
                border: 1px solid {cor};
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {cor};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {cor};
                border-color: {cor};
                color: white;
            }}
        """