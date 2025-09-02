"""
Integração do Sistema de Declarações de Saúde com Biodesk
═══════════════════════════════════════════════════════════════════════

Módulo de integração que conecta o sistema de declarações de saúde
com a interface principal da Terapia Quântica Biodesk.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QProgressBar, QGroupBox, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon

# Imports do sistema de declarações
try:
    from . import renderer, export_pdf
    HealthDeclarationRenderer = renderer.HealthDeclarationRenderer
    HealthDeclarationPDFExporter = export_pdf.HealthDeclarationPDFExporter
    FormValidator = renderer.FormValidator
except ImportError:
    # Fallback para desenvolvimento
    import renderer, export_pdf
    HealthDeclarationRenderer = renderer.HealthDeclarationRenderer
    HealthDeclarationPDFExporter = export_pdf.HealthDeclarationPDFExporter
    FormValidator = renderer.FormValidator


class HealthDeclarationIntegration:
    """Classe principal de integração com Biodesk"""
    
    def __init__(self, main_window, patient_manager=None, document_manager=None):
        """
        Inicializar integração
        
        Args:
            main_window: Janela principal do Biodesk
            patient_manager: Gestor de pacientes (opcional)
            document_manager: Gestor de documentos (opcional)
        """
        self.main_window = main_window
        self.patient_manager = patient_manager
        self.document_manager = document_manager
        self.logger = logging.getLogger("HealthDeclarationIntegration")
        
        # Configurações
        self.form_spec_path = Path(__file__).parent / "form_spec.json"
        self.declarations_dir = Path("Documentos_Pacientes") / "declaracoes_saude"
        self.declarations_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado
        self.current_patient = None
        self.current_declaration = None
        self.declaration_required = True
        
        # Componentes
        self.exporter = HealthDeclarationPDFExporter()
        self.setup_integration()
    
    def setup_integration(self):
        """Configurar integração com sistema principal"""
        try:
            # Verificar arquivos necessários
            if not self.form_spec_path.exists():
                self.logger.error(f"form_spec.json não encontrado em: {self.form_spec_path}")
                return False
            
            self.logger.info("✅ Sistema de declarações integrado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na integração: {e}")
            return False
    
    def check_patient_declaration_status(self, patient_id: str) -> Dict[str, Any]:
        """
        Verificar status da declaração de saúde do paciente
        
        Args:
            patient_id: ID do paciente
            
        Returns:
            Dict com status da declaração
        """
        try:
            patient_declarations_dir = self.declarations_dir / str(patient_id)
            
            # Procurar declarações existentes
            declarations = list(patient_declarations_dir.glob("declaracao_*.pdf"))
            
            if not declarations:
                return {
                    'status': 'missing',
                    'message': 'Declaração de saúde necessária',
                    'required': True,
                    'can_proceed': False
                }
            
            # Pegar declaração mais recente
            latest_declaration = max(declarations, key=lambda p: p.stat().st_mtime)
            age_days = (datetime.now().timestamp() - latest_declaration.stat().st_mtime) / (24 * 3600)
            
            if age_days > 90:  # Declaração expira em 90 dias
                return {
                    'status': 'expired',
                    'message': 'Declaração de saúde expirada (>90 dias)',
                    'required': True,
                    'can_proceed': False,
                    'last_declaration': latest_declaration,
                    'age_days': int(age_days)
                }
            
            return {
                'status': 'valid',
                'message': 'Declaração de saúde válida',
                'required': False,
                'can_proceed': True,
                'last_declaration': latest_declaration,
                'age_days': int(age_days)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar status da declaração: {e}")
            return {
                'status': 'error',
                'message': f'Erro na verificação: {e}',
                'required': True,
                'can_proceed': False
            }
    
    def require_health_declaration_for_therapy(self, patient_id: str, therapy_callback: Callable = None):
        """
        Exigir declaração de saúde antes de iniciar terapia
        
        Args:
            patient_id: ID do paciente
            therapy_callback: Função a chamar após declaração válida
        """
        self.current_patient = patient_id
        
        # Verificar status
        status = self.check_patient_declaration_status(patient_id)
        
        if status['can_proceed']:
            # Declaração válida, pode prosseguir
            self.logger.info(f"Declaração válida para paciente {patient_id}")
            if therapy_callback:
                therapy_callback()
            return
        
        # Precisa de nova declaração
        self.logger.info(f"Declaração necessária para paciente {patient_id}: {status['message']}")
        self.show_declaration_dialog(patient_id, therapy_callback, status)
    
    def show_declaration_dialog(self, patient_id: str, therapy_callback: Callable, status: Dict):
        """Mostrar dialog de declaração de saúde"""
        dialog = HealthDeclarationDialog(
            parent=self.main_window,
            patient_id=patient_id,
            form_spec_path=self.form_spec_path,
            status=status,
            integration=self
        )
        
        # Conectar callback de conclusão
        if therapy_callback:
            dialog.declaration_completed.connect(lambda: therapy_callback())
        
        dialog.exec()
    
    def save_patient_declaration(self, patient_id: str, form_data: Dict[str, Any], signature_data=None):
        """
        Salvar declaração do paciente
        
        Args:
            patient_id: ID do paciente
            form_data: Dados do formulário
            signature_data: Dados da assinatura
        """
        try:
            # Diretório do paciente
            patient_dir = self.declarations_dir / str(patient_id)
            patient_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = patient_dir / f"declaracao_{timestamp}.pdf"
            
            # Gerar PDF
            success = self.exporter.export_declaration(
                form_data=form_data,
                form_spec_path=self.form_spec_path,
                output_path=pdf_path,
                signature_data=signature_data,
                include_timestamp=False
            )
            
            if success:
                self.logger.info(f"Declaração salva: {pdf_path}")
                
                # Integração com gestor de documentos se disponível
                if self.document_manager:
                    self.document_manager.add_patient_document(
                        patient_id=patient_id,
                        document_type="declaracao_saude",
                        file_path=pdf_path,
                        metadata={
                            'generated_at': datetime.now().isoformat(),
                            'form_version': form_data.get('_metadata', {}).get('form_version', '1.0')
                        }
                    )
                
                return pdf_path
            else:
                self.logger.error("Falha ao gerar PDF da declaração")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar declaração: {e}")
            return None
    
    def validate_contraindications_for_therapy(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar contraindicações específicas para terapia
        
        Args:
            form_data: Dados da declaração
            
        Returns:
            Dict com resultado da validação
        """
        try:
            # Carregar especificação
            with open(self.form_spec_path, 'r', encoding='utf-8') as f:
                form_spec = json.load(f)
            
            validator = FormValidator(form_spec)
            
            # Validar
            errors = validator.validate_form(form_data)
            has_critical = validator.has_critical_contraindications(form_data)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'has_critical_contraindications': has_critical,
                'can_proceed_with_therapy': not has_critical,
                'message': self._get_validation_message(errors, has_critical)
            }
            
        except Exception as e:
            self.logger.error(f"Erro na validação: {e}")
            return {
                'valid': False,
                'errors': {'validation': [str(e)]},
                'has_critical_contraindications': True,
                'can_proceed_with_therapy': False,
                'message': f"Erro na validação: {e}"
            }
    
    def _get_validation_message(self, errors: Dict, has_critical: bool) -> str:
        """Gerar mensagem de validação"""
        if has_critical:
            return "❌ CONTRAINDICAÇÃO ABSOLUTA: Terapia não pode ser realizada"
        elif errors:
            return f"⚠️ Formulário contém erros ({len(errors)} campos)"
        else:
            return "✅ Declaração válida - Terapia pode prosseguir"


class HealthDeclarationDialog(QDialog):
    """Dialog para captura da declaração de saúde"""
    
    declaration_completed = pyqtSignal()
    
    def __init__(self, parent, patient_id: str, form_spec_path: Path, status: Dict, integration):
        super().__init__(parent)
        self.patient_id = patient_id
        self.form_spec_path = form_spec_path
        self.status = status
        self.integration = integration
        
        self.setup_ui()
        self.setup_form()
    
    def setup_ui(self):
        """Configurar interface do dialog"""
        self.setWindowTitle("Declaração de Estado de Saúde - Obrigatória")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Cabeçalho de aviso
        header = self._create_header()
        layout.addWidget(header)
        
        # Área do formulário
        self.form_container = QVBoxLayout()
        layout.addLayout(self.form_container)
        
        # Rodapé com status e botões
        footer = self._create_footer()
        layout.addWidget(footer)
    
    def _create_header(self) -> QGroupBox:
        """Criar cabeçalho de aviso"""
        header = QGroupBox("⚠️ DECLARAÇÃO OBRIGATÓRIA")
        header.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #c0392b;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin: 10px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(header)
        
        # Mensagem de status
        status_msg = QLabel(self.status['message'])
        status_msg.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(status_msg)
        
        # Aviso legal
        legal_text = QLabel(
            "Por razões de segurança, é OBRIGATÓRIO preencher e assinar a declaração "
            "de estado de saúde antes de iniciar qualquer protocolo de Terapia Quântica.\n\n"
            "Esta declaração permite identificar possíveis contraindicações e garantir "
            "que o tratamento é seguro para o seu caso específico."
        )
        legal_text.setWordWrap(True)
        legal_text.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(legal_text)
        
        return header
    
    def _create_footer(self) -> QGroupBox:
        """Criar rodapé com controles"""
        footer = QGroupBox()
        layout = QHBoxLayout(footer)
        
        # Status de validação
        self.status_label = QLabel("📝 Preencha o formulário abaixo")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Botão cancelar
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("padding: 10px; background-color: #bdc3c7;")
        layout.addWidget(cancel_btn)
        
        # Botão continuar (desabilitado inicialmente)
        self.continue_btn = QPushButton("✅ Continuar com Terapia")
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self.on_continue_therapy)
        self.continue_btn.setStyleSheet("""
            QPushButton:enabled {
                padding: 10px;
                background-color: #27ae60;
                color: white;
                font-weight: bold;
            }
            QPushButton:disabled {
                padding: 10px;
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.continue_btn)
        
        return footer
    
    def setup_form(self):
        """Configurar formulário de declaração"""
        try:
            # Criar renderer
            self.form_renderer = HealthDeclarationRenderer(self.form_spec_path)
            
            # Conectar sinais
            self.form_renderer.form_completed.connect(self.on_form_completed)
            self.form_renderer.form_validated.connect(self.on_form_validated)
            
            # Adicionar ao container
            self.form_container.addWidget(self.form_renderer)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar formulário: {e}")
            self.reject()
    
    @pyqtSlot(dict)
    def on_form_completed(self, form_data):
        """Formulário foi completado"""
        try:
            # Validar contraindicações
            validation = self.integration.validate_contraindications_for_therapy(form_data)
            
            if validation['has_critical_contraindications']:
                # Contraindicação absoluta
                QMessageBox.critical(
                    self, "Contraindicação Absoluta",
                    "❌ ATENÇÃO: Foram identificadas contraindicações absolutas.\n\n"
                    "Por razões de segurança, a Terapia Quântica NÃO pode ser realizada.\n\n"
                    "Consulte o seu médico para alternativas terapêuticas seguras."
                )
                self.status_label.setText("❌ Terapia bloqueada por contraindicações")
                self.continue_btn.setEnabled(False)
                return
            
            if not validation['valid']:
                # Erros no formulário
                error_msg = "Formulário contém erros:\n\n"
                for field, errors in validation['errors'].items():
                    error_msg += f"• {field}: {', '.join(errors)}\n"
                
                QMessageBox.warning(self, "Formulário Inválido", error_msg)
                return
            
            # Salvar declaração
            pdf_path = self.integration.save_patient_declaration(
                patient_id=self.patient_id,
                form_data=form_data,
                signature_data=None  # TODO: Capturar assinatura do formulário
            )
            
            if pdf_path:
                self.status_label.setText("✅ Declaração válida - Pode prosseguir")
                self.continue_btn.setEnabled(True)
                
                QMessageBox.information(
                    self, "Declaração Aceite",
                    f"✅ Declaração de saúde submetida com sucesso!\n\n"
                    f"📄 Documento salvo: {pdf_path.name}\n\n"
                    "A Terapia Quântica pode agora prosseguir com segurança."
                )
            else:
                QMessageBox.warning(self, "Erro", "Erro ao salvar declaração")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no processamento: {e}")
    
    @pyqtSlot(bool)
    def on_form_validated(self, is_valid):
        """Status de validação mudou"""
        if is_valid:
            self.status_label.setText("✅ Formulário válido")
        else:
            self.status_label.setText("⚠️ Formulário contém erros")
    
    @pyqtSlot()
    def on_continue_therapy(self):
        """Continuar com terapia"""
        self.declaration_completed.emit()
        self.accept()


# ═══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE INTEGRAÇÃO PARA USO NO SISTEMA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

def setup_health_declaration_integration(main_window, patient_manager=None, document_manager=None):
    """
    Configurar integração do sistema de declarações de saúde
    
    Args:
        main_window: Janela principal do Biodesk
        patient_manager: Gestor de pacientes (opcional)
        document_manager: Gestor de documentos (opcional)
        
    Returns:
        HealthDeclarationIntegration configurada
    """
    integration = HealthDeclarationIntegration(
        main_window=main_window,
        patient_manager=patient_manager,
        document_manager=document_manager
    )
    
    return integration


def require_health_declaration_before_therapy(integration, patient_id: str, therapy_start_callback: Callable):
    """
    Função helper para exigir declaração antes da terapia
    
    Args:
        integration: Instância HealthDeclarationIntegration
        patient_id: ID do paciente
        therapy_start_callback: Função a chamar após declaração válida
    """
    integration.require_health_declaration_for_therapy(patient_id, therapy_start_callback)


# ═══════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO NO SISTEMA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Exemplo de como integrar no sistema principal Biodesk:
    
    # No arquivo principal (main_window.py ou therapy_tab.py):
    
    from biodesk.forms.health_declaration.integration import (
        setup_health_declaration_integration,
        require_health_declaration_before_therapy
    )
    
    class TherapyMainWindow:
        def __init__(self):
            # ... código existente ...
            
            # Configurar integração de declarações
            self.health_declaration = setup_health_declaration_integration(
                main_window=self,
                patient_manager=self.patient_manager,
                document_manager=self.document_manager
            )
        
        def start_therapy_for_patient(self, patient_id):
            # Exigir declaração antes de iniciar
            require_health_declaration_before_therapy(
                integration=self.health_declaration,
                patient_id=patient_id,
                therapy_start_callback=lambda: self._actually_start_therapy(patient_id)
            )
        
        def _actually_start_therapy(self, patient_id):
            # Iniciar terapia após declaração válida
            print(f"✅ Iniciando terapia para paciente {patient_id}")
            # ... código da terapia ...
    """
    print("✅ Módulo de integração carregado")
    print("📖 Veja os comentários no final do arquivo para exemplo de uso")
