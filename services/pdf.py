"""
Módulo unificado para geração de PDFs no BIODESK
Centraliza toda a lógica de criação de documentos PDF
"""

from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF, QUrl
import os
from datetime import datetime


def configurar_printer_padrao(caminho_pdf, page_size=QPageSize.PageSizeId.A4, orientation=QPageLayout.Orientation.Portrait):
    """
    Configura um QPrinter com settings padrão para o BIODESK
    
    Args:
        caminho_pdf (str): Caminho onde salvar o PDF
        page_size: Tamanho da página (padrão A4)
        orientation: Orientação da página (padrão Portrait)
    
    Returns:
        QPrinter: Printer configurado
    """
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(caminho_pdf)
    printer.setPageSize(QPageSize(page_size))
    
    # Configurar layout de página
    page_layout = QPageLayout()
    page_layout.setPageSize(QPageSize(page_size))
    page_layout.setOrientation(orientation)
    page_layout.setMargins(QMarginsF(20, 20, 20, 20))  # Margens padrão 20mm
    page_layout.setUnits(QPageLayout.Unit.Millimeter)
    printer.setPageLayout(page_layout)
    
    return printer


def gerar_pdf_de_html(html_content, caminho_pdf, page_size=QPageSize.PageSizeId.A4, margens=None):
    """
    Gera um PDF a partir de conteúdo HTML
    
    Args:
        html_content (str): Conteúdo HTML a ser convertido
        caminho_pdf (str): Caminho onde salvar o PDF
        page_size: Tamanho da página (padrão A4)
        margens (QMarginsF): Margens personalizadas (padrão 20mm)
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(caminho_pdf), exist_ok=True)
        
        # Configurar printer
        printer = configurar_printer_padrao(caminho_pdf, page_size)
        
        # Aplicar margens personalizadas se fornecidas
        if margens:
            layout = printer.pageLayout()
            layout.setMargins(margens)
            printer.setPageLayout(layout)
        
        # Gerar PDF
        document = QTextDocument()
        document.setHtml(html_content)
        document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
        document.print(printer)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        return False


def gerar_pdf_declaracao(nome_paciente, data_nascimento, data_atual, template_html, 
                        assinatura_paciente_html="", assinatura_terapeuta_html="", 
                        caminho_pdf=None, logo_path=None):
    """
    Gera PDF de declaração de saúde com template padrão do BIODESK
    
    Args:
        nome_paciente (str): Nome do paciente
        data_nascimento (str): Data de nascimento
        data_atual (str): Data atual
        template_html (str): Template HTML do formulário
        assinatura_paciente_html (str): HTML da assinatura do paciente
        assinatura_terapeuta_html (str): HTML da assinatura do terapeuta
        caminho_pdf (str): Caminho de saída (auto-gerado se None)
        logo_path (str): Caminho do logo (opcional)
    
    Returns:
        str: Caminho do PDF gerado ou None se erro
    """
    try:
        # Gerar caminho se não fornecido
        if not caminho_pdf:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"Declaracao_Saude_{timestamp}.pdf"
            caminho_pdf = os.path.join("temp_pdf", nome_arquivo)
        
        # Processar logo
        logo_html = ""
        if logo_path and os.path.exists(logo_path):
            logo_url = QUrl.fromLocalFile(os.path.abspath(logo_path)).toString()
            logo_html = f'<img src="{logo_url}" width="80" height="80">'
        
        # Template HTML padrão BIODESK
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Calibri, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                    background-color: #ffffff;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding: 20px;
                    background: linear-gradient(135deg, #007bff, #28a745);
                    color: white;
                    border-radius: 12px;
                }}
                .content {{
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .patient-info {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    border-left: 5px solid #007bff;
                }}
                .signature-section {{
                    margin-top: 40px;
                    padding: 25px;
                    background-color: #f8f9fa;
                    border-radius: 12px;
                    border: 2px solid #dee2e6;
                }}
            </style>
        </head>
        <body>
            <!-- Cabeçalho -->
            <table style="width: 100%; border-bottom: 3px solid #4CAF50; padding-bottom: 15px; margin-bottom: 25px;">
                <tr>
                    <td style="text-align: left; vertical-align: middle;">
                        {logo_html}
                    </td>
                    <td style="text-align: center; vertical-align: middle;">
                        <h1 style="color: #4CAF50; margin: 0; font-size: 26pt;">🌿 DECLARAÇÃO DE ESTADO DE SAÚDE 🌿</h1>
                        <p style="color: #666; margin: 5px 0 0 0; font-size: 14pt; font-style: italic;">Naturopatia e Medicina Natural</p>
                    </td>
                    <td style="text-align: right; vertical-align: middle; width: 100px;">
                        <p style="font-size: 10pt; color: #666; margin: 0;">Data:<br><strong>{data_atual}</strong></p>
                    </td>
                </tr>
            </table>
            
            <!-- Informações do Paciente -->
            <div class="content">
                <div class="patient-info">
                    <h2 style="color: #007bff; margin-top: 0;">👤 Dados do Paciente</h2>
                    <p><strong>Nome:</strong> {nome_paciente}</p>
                    <p><strong>Data de Nascimento:</strong> {data_nascimento}</p>
                    <p><strong>Data da Declaração:</strong> {data_atual}</p>
                </div>
                
                <!-- Formulário de Saúde -->
                <div style="margin-bottom: 30px;">
                    <h2 style="color: #28a745;">📋 Declaração de Estado de Saúde</h2>
                    {template_html}
                </div>
            </div>
            
            <!-- Seção de Assinaturas -->
            <div class="signature-section">
                <h2 style="color: #333; text-align: center; margin-bottom: 30px;">✍️ Assinaturas</h2>
                <table style="width: 100%;">
                    <tr>
                        <!-- Assinatura do Paciente -->
                        <td style="width: 50%; text-align: center; vertical-align: top; padding: 0 20px;">
                            <div style="border: 2px solid #007bff; padding: 20px; background-color: #f8f9ff; min-height: 120px; border-radius: 8px;">
                                <h3 style="color: #007bff; margin-top: 0;">👤 Assinatura do Paciente</h3>
                                <div style="min-height: 80px; display: flex; align-items: center; justify-content: center;">
                                    {assinatura_paciente_html if assinatura_paciente_html else '<span style="color: #999; font-style: italic;">Sem assinatura</span>'}
                                </div>
                                <p style="margin: 15px 0 0 0; line-height: 1.6;">
                                    <strong style="color: #333; font-size: 14pt;">{nome_paciente}</strong><br>
                                    <span style="font-size: 12pt; color: #666;">{data_atual}</span><br>
                                    <span style="font-size: 10pt; color: #007bff; font-style: italic;">Assinado digitalmente</span>
                                </p>
                            </div>
                        </td>
                        
                        <!-- Assinatura do Naturopata -->
                        <td style="width: 50%; text-align: center; vertical-align: top; padding: 0 20px;">
                            <div style="border: 2px solid #28a745; padding: 20px; background-color: #f8fff8; min-height: 120px; border-radius: 8px;">
                                <h3 style="color: #28a745; margin-top: 0;">🌿 Assinatura do Naturopata</h3>
                                <div style="min-height: 80px; display: flex; align-items: center; justify-content: center;">
                                    {assinatura_terapeuta_html if assinatura_terapeuta_html else '<span style="color: #999; font-style: italic;">Sem assinatura</span>'}
                                </div>
                                <p style="margin: 15px 0 0 0; line-height: 1.6;">
                                    <strong style="color: #333; font-size: 14pt;">Nuno Correia</strong><br>
                                    <span style="font-size: 12pt; color: #666;">{data_atual}</span><br>
                                    <span style="font-size: 10pt; color: #28a745; font-style: italic;">Naturopata Certificado</span>
                                </p>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Rodapé -->
            <div style="margin-top: 40px; text-align: center; font-size: 10pt; color: #666; border-top: 1px solid #eee; padding-top: 15px;">
                🌿 BIODESK - Sistema de Gestão Naturopata | Documento gerado em {data_atual}<br>
                🌐 www.nunocorreia.pt | 📧 info@nunocorreia.pt
            </div>
        </body>
        </html>
        """
        
        # Gerar PDF
        sucesso = gerar_pdf_de_html(html_content, caminho_pdf)
        return caminho_pdf if sucesso else None
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF de declaração: {e}")
        return None


def criar_metadata_documento(caminho_pdf, categoria, descricao, nome_paciente, tipo_documento="declaracao_saude", dados_extras=None):
    """
    Cria arquivo de metadata para um documento PDF
    
    Args:
        caminho_pdf (str): Caminho do PDF
        categoria (str): Categoria do documento
        descricao (str): Descrição do documento
        nome_paciente (str): Nome do paciente
        tipo_documento (str): Tipo do documento
        dados_extras (dict): Dados adicionais para incluir
    """
    try:
        caminho_meta = caminho_pdf + '.meta'
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        with open(caminho_meta, 'w', encoding='utf-8') as f:
            f.write(f"Categoria: {categoria}\n")
            f.write(f"Descrição: {descricao}\n")
            f.write(f"Data: {data_atual}\n")
            f.write(f"Paciente: {nome_paciente}\n")
            f.write(f"Naturopata: Nuno Correia\n")
            f.write(f"Tipo: {tipo_documento}\n")
            
            if dados_extras:
                for chave, valor in dados_extras.items():
                    f.write(f"{chave}: {valor}\n")
                    
        print(f"✅ Metadata criada: {caminho_meta}")
        
    except Exception as e:
        print(f"⚠️ Erro ao criar metadata: {e}")
