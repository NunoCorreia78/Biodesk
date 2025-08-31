# -*- coding: utf-8 -*-
"""
PDFConsentimentosGenerator - Geração Especializada de PDFs
=========================================================

Gerador focado especificamente em PDFs de consentimento
com templates avançados e formatação profissional
"""

from pathlib import Path
from datetime import datetime
import tempfile
import os

class PDFConsentimentosGenerator:
    """Gerador especializado para PDFs de consentimento"""
    
    def __init__(self):
        self.output_dir = Path("Documentos_Pacientes")
        self.template_dir = Path("templates/consentimentos")
        
    def gerar_consentimento_simples(self, paciente_id, dados):
        """Gera PDF de consentimento simples"""
        try:
            # Template simples inline (fallback)
            html_content = self._gerar_html_simples(dados)
            
            # Salvar PDF
            output_path = self._obter_caminho_output(paciente_id, "consentimento_simples")
            
            # Aqui usaríamos uma biblioteca como reportlab ou weasyprint
            # Por agora, vamos simular
            self._salvar_pdf_simulado(html_content, output_path)
            
            return str(output_path)
            
        except Exception as e:
            print(f"Erro na geração simples: {e}")
            return None
    
    def gerar_consentimento_historico(self, paciente_id, dados):
        """Gera PDF de consentimento com histórico"""
        try:
            # Template com histórico
            html_content = self._gerar_html_historico(dados)
            
            # Salvar PDF
            output_path = self._obter_caminho_output(paciente_id, "consentimento_historico")
            self._salvar_pdf_simulado(html_content, output_path)
            
            return str(output_path)
            
        except Exception as e:
            print(f"Erro na geração com histórico: {e}")
            return None
    
    def _gerar_html_simples(self, dados):
        """Gera HTML para consentimento simples"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Consentimento Informado</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .content {{ line-height: 1.6; }}
                .signature {{ margin-top: 50px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CONSENTIMENTO INFORMADO</h1>
                <p>Data: {dados.get('data_atual', '')}</p>
            </div>
            
            <div class="content">
                <p>Eu, <strong>{dados.get('nome', '')}</strong>, 
                nascido(a) em {dados.get('data_nascimento', '')}, 
                declaro que:</p>
                
                <p>1. Fui devidamente informado(a) sobre os procedimentos;</p>
                <p>2. Compreendo os benefícios e riscos envolvidos;</p>
                <p>3. Autorizo a realização do tratamento proposto.</p>
            </div>
            
            <div class="signature">
                <p>_________________________________</p>
                <p>Assinatura do Paciente</p>
            </div>
        </body>
        </html>
        """
    
    def _gerar_html_historico(self, dados):
        """Gera HTML para consentimento com histórico"""
        historico_html = ""
        if dados.get('historico'):
            historico_html = "<h3>Histórico Clínico</h3><ul>"
            for item in dados['historico']:
                historico_html += f"<li>{item}</li>"
            historico_html += "</ul>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Consentimento com Histórico</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .content {{ line-height: 1.6; }}
                .historico {{ background: #f5f5f5; padding: 15px; margin: 20px 0; }}
                .signature {{ margin-top: 50px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CONSENTIMENTO INFORMADO COM HISTÓRICO</h1>
                <p>Data: {dados.get('data_atual', '')}</p>
            </div>
            
            <div class="content">
                <p>Paciente: <strong>{dados.get('nome', '')}</strong></p>
                <p>Data de Nascimento: {dados.get('data_nascimento', '')}</p>
                
                <div class="historico">
                    {historico_html}
                </div>
                
                <p>Declaro ter sido informado(a) e autorizo o tratamento.</p>
            </div>
            
            <div class="signature">
                <p>_________________________________</p>
                <p>Assinatura do Paciente</p>
                <p>Data: ___/___/_____</p>
            </div>
        </body>
        </html>
        """
    
    def _obter_caminho_output(self, paciente_id, tipo):
        """Obtém caminho para salvar o PDF"""
        patient_dir = self.output_dir / str(paciente_id)
        patient_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{tipo}_{timestamp}.pdf"
        
        return patient_dir / filename
    
    def _salvar_pdf_simulado(self, html_content, output_path):
        """Simula salvamento de PDF (placeholder)"""
        # Por agora, vamos salvar como HTML para demonstração
        html_path = output_path.with_suffix('.html')
        html_path.write_text(html_content, encoding='utf-8')
        
        # Em produção, aqui usaríamos:
        # - reportlab para gerar PDF nativo
        # - weasyprint para HTML->PDF
        # - pdfkit com wkhtmltopdf
        
        print(f"📄 PDF simulado salvo: {html_path}")
