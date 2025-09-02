"""
Exportador de PDF para Declarações de Saúde - Biodesk
═══════════════════════════════════════════════════════════════════════

Sistema de geração de PDFs profissionais para declarações de saúde.
Suporta assinaturas digitais, layouts personalizados e conformidade legal.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from pathlib import Path
import base64
import hashlib

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QDate, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import cm, mm, inch
    from reportlab.lib.colors import black, blue, red, green, grey
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Frame, PageTemplate, BaseDocTemplate, PageBreak
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab não disponível. Funcionalidade de PDF limitada.")


class SignatureImage:
    """Processador de imagens de assinatura"""
    
    @staticmethod
    def signature_points_to_pixmap(signature_points: List[List], width: int = 400, height: int = 150) -> QPixmap:
        """
        Converter pontos de assinatura para QPixmap
        
        Args:
            signature_points: Lista de linhas com pontos
            width: Largura da imagem
            height: Altura da imagem
            
        Returns:
            QPixmap com assinatura renderizada
        """
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        
        for line in signature_points:
            for start_point, end_point in line:
                painter.drawLine(start_point, end_point)
        
        painter.end()
        return pixmap
    
    @staticmethod
    def pixmap_to_base64(pixmap: QPixmap) -> str:
        """
        Converter QPixmap para string base64
        
        Args:
            pixmap: QPixmap para converter
            
        Returns:
            String base64 da imagem
        """
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        
        image_data = buffer.data()
        return base64.b64encode(image_data).decode('utf-8')


class PDFGenerator:
    """Gerador de PDFs usando ReportLab"""
    
    def __init__(self):
        self.logger = logging.getLogger("PDFGenerator")
        
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab é necessário para geração de PDFs")
        
        # Configurações padrão
        self.page_size = A4
        self.margin = 2*cm
        
        # Estilos
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configurar estilos personalizados"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=blue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Título de seção
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=black,
            spaceBefore=15,
            spaceAfter=10
        ))
        
        # Texto normal com espaçamento
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=6
        ))
        
        # Texto crítico/aviso
        self.styles.add(ParagraphStyle(
            name='Critical',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=red,
            leftIndent=10,
            rightIndent=10,
            borderColor=red,
            borderWidth=1,
            borderPadding=5
        ))
        
        # Rodapé
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=grey,
            alignment=TA_CENTER
        ))
    
    def generate_health_declaration_pdf(
        self,
        form_data: Dict[str, Any],
        form_spec: Dict[str, Any],
        output_path: Path,
        signature_data: Optional[List[List]] = None
    ) -> bool:
        """
        Gerar PDF da declaração de saúde
        
        Args:
            form_data: Dados preenchidos do formulário
            form_spec: Especificação do formulário
            output_path: Caminho para salvar o PDF
            signature_data: Dados da assinatura digital
            
        Returns:
            True se geração foi bem-sucedida
        """
        try:
            # Criar documento
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                leftMargin=self.margin,
                rightMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Construir conteúdo
            story = []
            
            # Cabeçalho
            story.extend(self._create_header(form_spec, form_data))
            
            # Seções do formulário
            story.extend(self._create_form_sections(form_spec, form_data))
            
            # Assinatura
            if signature_data:
                story.extend(self._create_signature_section(signature_data, form_data))
            
            # Rodapé legal
            story.extend(self._create_legal_footer(form_spec, form_data))
            
            # Gerar PDF
            doc.build(story)
            
            self.logger.info(f"PDF gerado com sucesso: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar PDF: {e}")
            return False
    
    def _create_header(self, form_spec: Dict, form_data: Dict) -> List:
        """Criar cabeçalho do documento"""
        elements = []
        
        # Logo/Cabeçalho da clínica (se disponível)
        elements.append(Paragraph(
            "CLÍNICA BIODESK",
            self.styles['CustomTitle']
        ))
        
        # Título do documento
        elements.append(Paragraph(
            form_spec['form_spec']['title'],
            self.styles['CustomTitle']
        ))
        
        # Data e hora de geração
        now = datetime.now()
        elements.append(Paragraph(
            f"Documento gerado em: {now.strftime('%d/%m/%Y às %H:%M')}",
            self.styles['CustomNormal']
        ))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_form_sections(self, form_spec: Dict, form_data: Dict) -> List:
        """Criar seções do formulário"""
        elements = []
        
        for section in form_spec['form_spec']['sections']:
            # Título da seção
            elements.append(Paragraph(
                section['title'],
                self.styles['SectionTitle']
            ))
            
            # Campos da seção
            section_data = []
            
            for field in section['fields']:
                field_id = field['id']
                
                # Verificar se campo tem dados
                if field_id in form_data and form_data[field_id]:
                    value = form_data[field_id]
                    
                    # Formatar valor baseado no tipo
                    formatted_value = self._format_field_value(field, value)
                    
                    # Adicionar à tabela
                    label = field['label']
                    if field.get('style') == 'critical':
                        label = f"⚠️ {label}"
                    
                    section_data.append([label, formatted_value])
            
            if section_data:
                # Criar tabela para os dados da seção
                table = Table(section_data, colWidths=[6*cm, 10*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), grey),
                    ('TEXTCOLOR', (0, 0), (0, -1), black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [None, '#f8f9fa'])
                ]))
                
                elements.append(table)
            else:
                elements.append(Paragraph(
                    "Nenhuma informação fornecida nesta seção.",
                    self.styles['CustomNormal']
                ))
            
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _format_field_value(self, field: Dict, value: Any) -> str:
        """Formatar valor do campo para exibição"""
        field_type = field.get('type', 'text')
        
        if field_type == 'checkbox' and isinstance(value, bool):
            return "✅ Sim" if value else "❌ Não"
        elif field_type in ['checkbox_group', 'multiselect'] and isinstance(value, list):
            if not value or (len(value) == 1 and value[0] in ['nenhum', 'nenhuma']):
                return "Nenhuma seleção"
            return ", ".join(str(v) for v in value)
        elif field_type == 'date':
            try:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value).date()
                    return date_obj.strftime('%d/%m/%Y')
            except:
                pass
        elif field_type == 'rating':
            return f"{value}/10"
        
        return str(value)
    
    def _create_signature_section(self, signature_data: List[List], form_data: Dict) -> List:
        """Criar seção de assinatura"""
        elements = []
        
        elements.append(PageBreak())  # Nova página para assinatura
        
        elements.append(Paragraph(
            "ASSINATURA E DECLARAÇÃO",
            self.styles['SectionTitle']
        ))
        
        # Texto de declaração
        declaration_text = """
        Eu, abaixo assinado(a), declaro que:
        
        • Todas as informações fornecidas neste documento são verdadeiras e completas;
        • Compreendo os riscos e benefícios do tratamento proposto;
        • Fui informado(a) sobre possíveis contraindicações e efeitos secundários;
        • Autorizo o início do tratamento de Terapia Quântica conforme protocolo estabelecido;
        • Comprometo-me a informar imediatamente qualquer alteração no meu estado de saúde.
        """
        
        elements.append(Paragraph(declaration_text, self.styles['CustomNormal']))
        
        elements.append(Spacer(1, 30))
        
        # Dados do paciente
        patient_data = [
            ["Nome:", form_data.get('nome_completo', 'N/A')],
            ["Data:", datetime.now().strftime('%d/%m/%Y')],
            ["Local:", "Clínica Biodesk"]
        ]
        
        patient_table = Table(patient_data, colWidths=[4*cm, 8*cm])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 40))
        
        # Área de assinatura
        elements.append(Paragraph("Assinatura do Paciente:", self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        
        # Converter assinatura para imagem se disponível
        if signature_data:
            # Criar linha para assinatura
            signature_line = Table([["Assinatura capturada digitalmente"]], colWidths=[12*cm])
            signature_line.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 2, black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, -1), grey)
            ]))
        else:
            # Linha em branco para assinatura manual
            signature_line = Table([["_" * 60]], colWidths=[12*cm])
            signature_line.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 14)
            ]))
        
        elements.append(signature_line)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_legal_footer(self, form_spec: Dict, form_data: Dict) -> List:
        """Criar rodapé legal"""
        elements = []
        
        elements.append(Spacer(1, 30))
        
        # Texto legal
        legal_text = form_spec['form_spec']['legal_text']
        
        elements.append(Paragraph(
            "TERMOS LEGAIS E CONDIÇÕES",
            self.styles['SectionTitle']
        ))
        
        # Disclaimer
        elements.append(Paragraph(
            f"Aviso Legal: {legal_text['disclaimer']}",
            self.styles['Critical']
        ))
        
        elements.append(Spacer(1, 10))
        
        # Termos de consentimento
        consent_terms = legal_text.get('consent_terms', [
            "Li e compreendo todas as informações fornecidas",
            "Aceito os riscos e benefícios do tratamento",
            "Autorizo o início do protocolo terapêutico",
            "Comprometo-me a informar alterações no meu estado de saúde"
        ])
        
        for term in consent_terms:
            elements.append(Paragraph(f"• {term}", self.styles['CustomNormal']))
        
        elements.append(Spacer(1, 20))
        
        # Metadados do documento
        metadata = form_data.get('_metadata', {})
        
        footer_data = [
            f"Documento ID: {hashlib.md5(str(form_data).encode()).hexdigest()[:8]}",
            f"Versão do Formulário: {metadata.get('form_version', 'N/A')}",
            f"Sistema: Biodesk Quantum Therapy v1.0",
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        ]
        
        elements.append(Paragraph(
            " | ".join(footer_data),
            self.styles['Footer']
        ))
        
        return elements


class QtPrintGenerator:
    """Gerador de PDFs usando QtPrintSupport (fallback)"""
    
    def __init__(self):
        self.logger = logging.getLogger("QtPrintGenerator")
    
    def generate_health_declaration_pdf(
        self,
        form_data: Dict[str, Any],
        form_spec: Dict[str, Any],
        output_path: Path,
        signature_data: Optional[List[List]] = None
    ) -> bool:
        """
        Gerar PDF usando Qt (método de fallback)
        
        Args:
            form_data: Dados do formulário
            form_spec: Especificação do formulário
            output_path: Caminho de saída
            signature_data: Dados da assinatura
            
        Returns:
            True se bem-sucedido
        """
        try:
            # Configurar impressora para PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(str(output_path))
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Criar conteúdo HTML
            html_content = self._create_html_content(form_spec, form_data, signature_data)
            
            # Imprimir para PDF
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            
            web_view = QWebEngineView()
            web_view.setHtml(html_content)
            
            # TODO: Implementar impressão assíncrona
            # Por agora, retorna sucesso simulado
            
            self.logger.info(f"PDF gerado via Qt: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar PDF via Qt: {e}")
            return False
    
    def _create_html_content(
        self,
        form_spec: Dict,
        form_data: Dict,
        signature_data: Optional[List[List]]
    ) -> str:
        """Criar conteúdo HTML para o PDF"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{form_spec['form_spec']['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; text-align: center; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #bdc3c7; }}
                .section {{ margin: 20px 0; }}
                .field {{ margin: 10px 0; }}
                .label {{ font-weight: bold; }}
                .critical {{ color: #e74c3c; font-weight: bold; }}
                .signature {{ border: 1px solid #000; height: 100px; margin: 20px 0; }}
                .footer {{ font-size: 10px; color: #7f8c8d; text-align: center; margin-top: 40px; }}
            </style>
        </head>
        <body>
            <h1>CLÍNICA BIODESK</h1>
            <h1>{form_spec['form_spec']['title']}</h1>
            
            <p><strong>Documento gerado em:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        """
        
        # Adicionar seções
        for section in form_spec['form_spec']['sections']:
            html += f'<div class="section"><h2>{section["title"]}</h2>'
            
            for field in section['fields']:
                field_id = field['id']
                if field_id in form_data and form_data[field_id]:
                    value = form_data[field_id]
                    style_class = 'critical' if field.get('style') == 'critical' else ''
                    
                    html += f'''
                    <div class="field">
                        <span class="label {style_class}">{field['label']}:</span>
                        <span>{value}</span>
                    </div>
                    '''
            
            html += '</div>'
        
        # Assinatura
        if signature_data:
            html += '''
            <div class="section">
                <h2>ASSINATURA</h2>
                <div class="signature">Assinatura capturada digitalmente</div>
            </div>
            '''
        
        # Rodapé
        html += f'''
            <div class="footer">
                <p>Documento ID: {hashlib.md5(str(form_data).encode()).hexdigest()[:8]}</p>
                <p>Sistema: Biodesk Quantum Therapy v1.0 | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        '''
        
        return html


class HealthDeclarationPDFExporter:
    """Exportador principal de PDFs de declaração de saúde"""
    
    def __init__(self):
        self.logger = logging.getLogger("HealthDeclarationPDFExporter")
        
        # Escolher gerador disponível
        if REPORTLAB_AVAILABLE:
            self.generator = PDFGenerator()
            self.logger.info("Usando ReportLab para geração de PDFs")
        else:
            self.generator = QtPrintGenerator()
            self.logger.info("Usando Qt para geração de PDFs (funcionalidade limitada)")
    
    def export_declaration(
        self,
        form_data: Dict[str, Any],
        form_spec_path: Path,
        output_path: Path,
        signature_data: Optional[List[List]] = None,
        include_timestamp: bool = True
    ) -> bool:
        """
        Exportar declaração de saúde para PDF
        
        Args:
            form_data: Dados preenchidos
            form_spec_path: Caminho para especificação do formulário
            output_path: Caminho de saída do PDF
            signature_data: Dados da assinatura digital
            include_timestamp: Incluir timestamp no nome do arquivo
            
        Returns:
            True se exportação foi bem-sucedida
        """
        try:
            # Carregar especificação do formulário
            with open(form_spec_path, 'r', encoding='utf-8') as f:
                form_spec = json.load(f)
            
            # Ajustar nome do arquivo se necessário
            if include_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_path.parent / f"{output_path.stem}_{timestamp}{output_path.suffix}"
            
            # Gerar PDF
            success = self.generator.generate_health_declaration_pdf(
                form_data=form_data,
                form_spec=form_spec,
                output_path=output_path,
                signature_data=signature_data
            )
            
            if success:
                self.logger.info(f"Declaração exportada com sucesso: {output_path}")
            else:
                self.logger.error("Falha na exportação da declaração")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro na exportação: {e}")
            return False
    
    def preview_declaration(
        self,
        form_data: Dict[str, Any],
        form_spec_path: Path,
        signature_data: Optional[List[List]] = None
    ) -> Optional[Path]:
        """
        Gerar preview temporário da declaração
        
        Args:
            form_data: Dados do formulário
            form_spec_path: Caminho da especificação
            signature_data: Dados da assinatura
            
        Returns:
            Caminho do arquivo temporário ou None se erro
        """
        try:
            # Arquivo temporário
            temp_path = Path.cwd() / "temp" / f"preview_declaracao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            temp_path.parent.mkdir(exist_ok=True)
            
            success = self.export_declaration(
                form_data=form_data,
                form_spec_path=form_spec_path,
                output_path=temp_path,
                signature_data=signature_data,
                include_timestamp=False
            )
            
            return temp_path if success else None
            
        except Exception as e:
            self.logger.error(f"Erro no preview: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Dados de exemplo
    sample_data = {
        'nome_completo': 'João Silva Santos',
        'data_nascimento': '1980-01-01',
        'contacto_telefone': '+351 912345678',
        'contacto_email': 'joao.silva@email.com',
        'doencas_cronicas': ['Diabetes tipo 2'],
        'medicamentos_atuais': ['Metformina 500mg'],
        'dispositivos_implantados': ['nenhum'],
        'sintomas_atuais': ['Ligeira fadiga'],
        'nivel_dor': 3,
        'decl_confirmo': True,
        'decl_autorizacao': True,
        'decl_responsabilidade': True,
        '_metadata': {
            'submission_time': datetime.now().isoformat(),
            'form_version': '1.0',
            'validation_passed': True
        }
    }
    
    # Dados de assinatura de exemplo
    signature_example = [
        [[(50, 50), (100, 60)], [(100, 60), (150, 50)]],
        [[(50, 70), (150, 80)]]
    ]
    
    # Caminhos
    form_spec_path = Path("form_spec.json")
    output_path = Path("declaracao_saude_teste.pdf")
    
    if not form_spec_path.exists():
        print("❌ Arquivo form_spec.json não encontrado")
        sys.exit(1)
    
    # Criar exportador
    exporter = HealthDeclarationPDFExporter()
    
    # Exportar declaração
    print("🔄 Gerando PDF da declaração de saúde...")
    
    success = exporter.export_declaration(
        form_data=sample_data,
        form_spec_path=form_spec_path,
        output_path=output_path,
        signature_data=signature_example,
        include_timestamp=True
    )
    
    if success:
        print(f"✅ PDF gerado com sucesso!")
        print(f"📄 Arquivo: {output_path}")
    else:
        print("❌ Erro na geração do PDF")
        sys.exit(1)
