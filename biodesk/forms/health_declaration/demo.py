"""
Demonstração Completa do Sistema de Declarações de Saúde - Biodesk
═══════════════════════════════════════════════════════════════════════

Script de teste e demonstração do sistema completo de declarações de saúde,
incluindo renderização de formulários, validação e exportação para PDF.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt6.QtCore import pyqtSlot

# Configurar path para imports locais
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    # Imports absolutos dos módulos locais
    import renderer
    import export_pdf
    
    HealthDeclarationRenderer = renderer.HealthDeclarationRenderer
    HealthDeclarationPDFExporter = export_pdf.HealthDeclarationPDFExporter
    
    def create_health_declaration_system(form_spec_path):
        renderer_obj = HealthDeclarationRenderer(form_spec_path)
        exporter_obj = HealthDeclarationPDFExporter()
        return renderer_obj, exporter_obj
        
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    print("Certifique-se de que todos os arquivos estão no diretório correto")
    sys.exit(1)


class HealthDeclarationDemo(QMainWindow):
    """Demo principal do sistema de declarações"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Declarações de Saúde - Demo")
        self.resize(1000, 700)
        
        # Caminhos
        self.form_spec_path = Path(__file__).parent / "form_spec.json"
        self.output_dir = Path(__file__).parent / "demo_output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Verificar arquivos necessários
        if not self.form_spec_path.exists():
            QMessageBox.critical(
                self, "Erro",
                f"Arquivo de especificação não encontrado: {self.form_spec_path}"
            )
            sys.exit(1)
        
        self.setup_ui()
        self.setup_system()
    
    def setup_ui(self):
        """Configurar interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Título
        from PyQt6.QtWidgets import QLabel
        title = QLabel("🏥 Sistema de Declarações de Saúde - Demonstração")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Botões de demonstração
        btn_new_form = QPushButton("📝 Nova Declaração de Saúde")
        btn_new_form.clicked.connect(self.open_new_declaration)
        btn_new_form.setStyleSheet("padding: 10px; font-size: 14px;")
        layout.addWidget(btn_new_form)
        
        btn_sample_pdf = QPushButton("📄 Gerar PDF de Exemplo")
        btn_sample_pdf.clicked.connect(self.generate_sample_pdf)
        btn_sample_pdf.setStyleSheet("padding: 10px; font-size: 14px;")
        layout.addWidget(btn_sample_pdf)
        
        btn_test_validation = QPushButton("✅ Testar Validação")
        btn_test_validation.clicked.connect(self.test_validation)
        btn_test_validation.setStyleSheet("padding: 10px; font-size: 14px;")
        layout.addWidget(btn_test_validation)
        
        # Área para mostrar o formulário
        self.form_container = QWidget()
        layout.addWidget(self.form_container)
        
        # Status
        self.status_label = QLabel("Sistema iniciado. Selecione uma opção acima.")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 10px;")
        layout.addWidget(self.status_label)
    
    def setup_system(self):
        """Configurar sistema de declarações"""
        try:
            self.renderer, self.exporter = create_health_declaration_system(self.form_spec_path)
            self.status_label.setText("✅ Sistema carregado com sucesso")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar sistema: {e}")
            self.status_label.setText(f"❌ Erro: {e}")
    
    @pyqtSlot()
    def open_new_declaration(self):
        """Abrir nova declaração"""
        try:
            # Criar novo renderer
            new_renderer = HealthDeclarationRenderer(self.form_spec_path)
            
            # Conectar sinais
            new_renderer.form_completed.connect(self.on_form_completed)
            new_renderer.form_validated.connect(self.on_form_validated)
            
            # Mostrar em janela separada
            new_renderer.show()
            self.status_label.setText("📝 Nova declaração aberta")
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao abrir declaração: {e}")
    
    @pyqtSlot()
    def generate_sample_pdf(self):
        """Gerar PDF de exemplo"""
        try:
            # Dados de exemplo
            sample_data = {
                'nome_completo': 'Maria Silva Santos',
                'data_nascimento': '1985-05-15',
                'contacto_telefone': '+351 912345678',
                'contacto_email': 'maria.silva@email.com',
                'genero': 'Feminino',
                'profissao': 'Professora',
                'doencas_cronicas': ['Hipertensão arterial'],
                'medicamentos_atuais': ['Lisinopril 10mg'],
                'cirurgias_previas': ['Apendicectomia (2010)'],
                'alergias_conhecidas': ['Penicilina'],
                'dispositivos_implantados': ['nenhum'],
                'gravidez_atual': False,
                'sintomas_atuais': ['Ligeira cefaleia'],
                'nivel_dor': 2,
                'nivel_stress': 4,
                'qualidade_sono': 7,
                'decl_confirmo': True,
                'decl_autorizacao': True,
                'decl_responsabilidade': True,
                '_metadata': {
                    'submission_time': datetime.now().isoformat(),
                    'form_version': '1.0',
                    'validation_passed': True,
                    'demo_mode': True
                }
            }
            
            # Dados de assinatura fictícia
            sample_signature = [
                [[(50, 50), (100, 60)], [(100, 60), (150, 50)]],
                [[(60, 70), (140, 80)], [(140, 80), (120, 90)]]
            ]
            
            # Gerar PDF
            output_path = self.output_dir / f"declaracao_exemplo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            self.status_label.setText("🔄 Gerando PDF de exemplo...")
            QApplication.processEvents()
            
            success = self.exporter.export_declaration(
                form_data=sample_data,
                form_spec_path=self.form_spec_path,
                output_path=output_path,
                signature_data=sample_signature,
                include_timestamp=False
            )
            
            if success:
                QMessageBox.information(
                    self, "PDF Gerado",
                    f"✅ PDF de exemplo gerado com sucesso!\n\n📄 Arquivo: {output_path.name}\n📁 Local: {output_path.parent}"
                )
                self.status_label.setText(f"✅ PDF gerado: {output_path.name}")
            else:
                QMessageBox.warning(self, "Erro", "❌ Falha na geração do PDF")
                self.status_label.setText("❌ Erro na geração do PDF")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro inesperado: {e}")
            self.status_label.setText(f"❌ Erro: {e}")
    
    @pyqtSlot()
    def test_validation(self):
        """Testar sistema de validação"""
        try:
            from renderer import FormValidator
            
            # Carregar especificação
            with open(self.form_spec_path, 'r', encoding='utf-8') as f:
                form_spec = json.load(f)
            
            validator = FormValidator(form_spec)
            
            # Teste 1: Dados válidos
            valid_data = {
                'nome_completo': 'João Silva',
                'data_nascimento': '1980-01-01',
                'contacto_telefone': '+351 912345678',
                'doencas_cronicas': ['nenhuma'],
                'dispositivos_implantados': ['nenhum'],
                'sintomas_atuais': ['nenhum'],
                'decl_confirmo': True,
                'decl_autorizacao': True,
                'decl_responsabilidade': True
            }
            
            # Teste 2: Dados com contraindicação
            contraindicated_data = {
                'nome_completo': 'Ana Costa',
                'data_nascimento': '1990-01-01',
                'contacto_telefone': '+351 987654321',
                'doencas_cronicas': ['Epilepsia'],  # Contraindicação
                'dispositivos_implantados': ['Pacemaker'],  # Contraindicação
                'sintomas_atuais': ['Convulsões'],
                'decl_confirmo': True,
                'decl_autorizacao': True,
                'decl_responsabilidade': True
            }
            
            # Teste 3: Dados incompletos
            incomplete_data = {
                'nome_completo': '',  # Campo obrigatório vazio
                'contacto_telefone': '',  # Campo obrigatório vazio
                'decl_confirmo': False  # Consentimento obrigatório não dado
            }
            
            # Executar validações
            errors_valid = validator.validate_form(valid_data)
            errors_contraindicated = validator.validate_form(contraindicated_data)
            errors_incomplete = validator.validate_form(incomplete_data)
            
            # Resultados
            results = []
            results.append("TESTE DE VALIDAÇÃO\n" + "="*50)
            
            results.append(f"\n1. DADOS VÁLIDOS:")
            if not errors_valid:
                results.append("   ✅ Validação passou - Nenhum erro encontrado")
            else:
                results.append(f"   ❌ Erros encontrados: {errors_valid}")
            
            results.append(f"\n2. DADOS COM CONTRAINDICAÇÃO:")
            if errors_contraindicated:
                results.append("   ✅ Contraindicações detectadas corretamente:")
                for field, errs in errors_contraindicated.items():
                    results.append(f"      - {field}: {errs}")
            else:
                results.append("   ❌ FALHA: Contraindicações não foram detectadas!")
            
            results.append(f"\n3. DADOS INCOMPLETOS:")
            if errors_incomplete:
                results.append("   ✅ Campos obrigatórios validados corretamente:")
                for field, errs in errors_incomplete.items():
                    results.append(f"      - {field}: {errs}")
            else:
                results.append("   ❌ FALHA: Campos obrigatórios não foram validados!")
            
            results.append(f"\n4. TESTE DE CONTRAINDICAÇÕES CRÍTICAS:")
            has_critical = validator.has_critical_contraindications(contraindicated_data)
            if has_critical:
                results.append("   ✅ Contraindicações críticas detectadas corretamente")
            else:
                results.append("   ❌ FALHA: Contraindicações críticas não detectadas!")
            
            # Mostrar resultados
            QMessageBox.information(
                self, "Resultados da Validação",
                "\n".join(results)
            )
            
            self.status_label.setText("✅ Testes de validação concluídos")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro nos testes de validação: {e}")
            self.status_label.setText(f"❌ Erro nos testes: {e}")
    
    @pyqtSlot(dict)
    def on_form_completed(self, form_data):
        """Formulário foi completado"""
        self.status_label.setText("✅ Declaração submetida com sucesso")
        
        # Perguntar se quer gerar PDF
        reply = QMessageBox.question(
            self, "Gerar PDF",
            "Declaração submetida com sucesso!\n\nDeseja gerar o PDF?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.generate_pdf_from_data(form_data)
    
    @pyqtSlot(bool)
    def on_form_validated(self, is_valid):
        """Status de validação mudou"""
        if is_valid:
            self.status_label.setText("✅ Formulário válido")
        else:
            self.status_label.setText("⚠️ Formulário contém erros")
    
    def generate_pdf_from_data(self, form_data):
        """Gerar PDF a partir dos dados do formulário"""
        try:
            output_path = self.output_dir / f"declaracao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            success = self.exporter.export_declaration(
                form_data=form_data,
                form_spec_path=self.form_spec_path,
                output_path=output_path,
                signature_data=None,  # TODO: Capturar dados de assinatura do formulário
                include_timestamp=False
            )
            
            if success:
                QMessageBox.information(
                    self, "PDF Gerado",
                    f"PDF da declaração gerado com sucesso!\n\n📄 {output_path}"
                )
            else:
                QMessageBox.warning(self, "Erro", "Falha na geração do PDF")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro na geração do PDF: {e}")


def main():
    """Função principal da demonstração"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Criar aplicação
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema Declarações Saúde Demo")
    app.setApplicationVersion("1.0.0")
    
    # Verificar dependências
    print("🔄 Verificando dependências...")
    
    try:
        from PyQt6 import QtCore
        print("✅ PyQt6 disponível")
    except ImportError:
        print("❌ PyQt6 não encontrado")
        return 1
    
    try:
        import reportlab
        print("✅ ReportLab disponível - PDFs com funcionalidade completa")
    except ImportError:
        print("⚠️ ReportLab não encontrado - PDFs com funcionalidade limitada")
    
    # Criar e mostrar demo
    print("🚀 Iniciando demonstração...")
    
    demo = HealthDeclarationDemo()
    demo.show()
    
    print("✅ Sistema de declarações carregado com sucesso!")
    print("   Use a interface para testar as funcionalidades:")
    print("   • Nova Declaração: Abre formulário interativo")
    print("   • PDF de Exemplo: Gera documento com dados fictícios")
    print("   • Testar Validação: Executa testes automáticos")
    
    # Executar aplicação
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
