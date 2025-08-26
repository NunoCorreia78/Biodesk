"""
Biodesk - PDF Service
=====================

Serviço para geração e manipulação de documentos PDF.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Geração de PDFs com formatação profissional
- Templates padronizados para documentos médicos
- Configuração de layout e margens
- Gestão de assinaturas e cabeçalhos

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..utils import DateUtils, TextUtils, FileManager


class PDFService:
    """Serviço para geração e manipulação de documentos PDF"""
    
    # Configurações padrão para PDFs médicos
    DEFAULT_CONFIG = {
        'page_size': 'A4',
        'margins': {'top': 25, 'bottom': 25, 'left': 25, 'right': 25},  # em mm
        'font_family': 'Arial, sans-serif',
        'font_size': '12pt',
        'line_height': 1.5,
        'header_color': '#2980b9',
        'border_color': '#e9ecef'
    }
    
    @staticmethod
    def validar_prerequisitos_pdf(paciente_data: Dict[str, Any], 
                                 tipo_documento: str,
                                 conteudo: str) -> tuple[bool, Optional[str]]:
        """
        Valida se todos os prerequisitos para gerar PDF estão presentes
        
        Args:
            paciente_data: Dados do paciente
            tipo_documento: Tipo do documento
            conteudo: Conteúdo do documento
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        if not paciente_data:
            return False, "Nenhum paciente selecionado"
        
        if not tipo_documento or not tipo_documento.strip():
            return False, "Tipo de documento não especificado"
        
        if not conteudo or not conteudo.strip():
            return False, "Conteúdo do documento está vazio"
        
        # Verificar dados essenciais do paciente
        nome = paciente_data.get('nome', '').strip()
        if not nome:
            return False, "Nome do paciente é obrigatório"
        
        return True, None
    
    @staticmethod
    def gerar_nome_arquivo_pdf(paciente_data: Dict[str, Any], 
                              tipo_documento: str) -> str:
        """
        Gera nome padronizado para arquivo PDF
        
        Args:
            paciente_data: Dados do paciente
            tipo_documento: Tipo do documento
            
        Returns:
            Nome do arquivo formatado
        """
        from ..services import DataService
        return DataService.gerar_nome_arquivo_paciente(
            paciente_data, f"{tipo_documento}_PDF"
        ) + ".pdf"
    
    @staticmethod
    def gerar_cabecalho_documento(tipo_documento: str, 
                                 paciente_data: Dict[str, Any]) -> str:
        """
        Gera cabeçalho padrão para documentos
        
        Args:
            tipo_documento: Tipo do documento
            paciente_data: Dados do paciente
            
        Returns:
            HTML do cabeçalho
        """
        nome_paciente = paciente_data.get('nome', '[Nome do Paciente]')
        data_atual = DateUtils.data_atual()
        
        return f"""
        <div class="header">
            <h1>📋 {tipo_documento.upper()}</h1>
            <div class="info-box">
                <p><strong>👤 Paciente:</strong> {nome_paciente}</p>
                <p><strong>📅 Data:</strong> {data_atual}</p>
            </div>
        </div>
        """
    
    @staticmethod
    def gerar_css_padrao() -> str:
        """
        Gera CSS padrão para documentos PDF
        
        Returns:
            CSS formatado
        """
        config = PDFService.DEFAULT_CONFIG
        
        return f"""
        <style>
            body {{
                font-family: {config['font_family']};
                font-size: {config['font_size']};
                line-height: {config['line_height']};
                color: #333;
                margin: {config['margins']['top']}pt;
                padding: 0;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30pt;
                padding: 20pt;
                background-color: #f8f9fa;
                border: 2pt solid {config['header_color']};
                border-radius: 8pt;
            }}
            .header h1 {{
                color: {config['header_color']};
                font-size: 18pt;
                margin: 0 0 15pt 0;
                font-weight: bold;
            }}
            .info-box {{
                background-color: #e8f4fd;
                padding: 15pt;
                margin: 20pt 0;
                border-left: 4pt solid {config['header_color']};
                border-radius: 4pt;
            }}
            .conteudo {{
                margin: 20pt 0;
                text-align: justify;
                line-height: {config['line_height']};
            }}
            .assinatura-area {{
                margin-top: 50pt;
                padding: 20pt;
                border: 2pt solid {config['border_color']};
                border-radius: 8pt;
                background-color: #fafafa;
            }}
            .assinatura-linha {{
                border-bottom: 2pt solid #333;
                margin: 15pt 0 8pt 0;
                height: 40pt;
                width: 200pt;
                display: inline-block;
            }}
            .rodape {{
                margin-top: 30pt;
                text-align: center;
                font-size: 10pt;
                color: #666;
                border-top: 1pt solid {config['border_color']};
                padding-top: 15pt;
            }}
            .destaque {{
                background-color: #fff3cd;
                border: 1pt solid #ffeaa7;
                padding: 10pt;
                margin: 15pt 0;
                border-radius: 4pt;
            }}
        </style>
        """
    
    @staticmethod
    def gerar_area_assinaturas(incluir_paciente: bool = True, 
                              incluir_terapeuta: bool = True) -> str:
        """
        Gera área de assinaturas para documentos
        
        Args:
            incluir_paciente: Se deve incluir área para assinatura do paciente
            incluir_terapeuta: Se deve incluir área para assinatura do terapeuta
            
        Returns:
            HTML da área de assinaturas
        """
        html = '<div class="assinatura-area">'
        html += '<h3>📝 ASSINATURAS</h3>'
        
        if incluir_paciente:
            html += '''
            <div style="margin: 20pt 0;">
                <p><strong>Paciente:</strong></p>
                <div class="assinatura-linha"></div>
                <p style="font-size: 10pt; margin-top: 5pt;">Assinatura do Paciente</p>
            </div>
            '''
        
        if incluir_terapeuta:
            html += '''
            <div style="margin: 20pt 0;">
                <p><strong>Terapeuta:</strong></p>
                <div class="assinatura-linha"></div>
                <p style="font-size: 10pt; margin-top: 5pt;">Assinatura do Terapeuta</p>
            </div>
            '''
        
        html += '</div>'
        return html
    
    @staticmethod
    def gerar_rodape_documento() -> str:
        """
        Gera rodapé padrão para documentos
        
        Returns:
            HTML do rodapé
        """
        data_geracao = DateUtils.data_atual_completa()
        
        return f"""
        <div class="rodape">
            <p>📄 Documento gerado automaticamente pelo Biodesk</p>
            <p>🕒 Gerado em: {data_geracao}</p>
            <p>⚡ Sistema de Gestão de Pacientes - Biodesk © 2025</p>
        </div>
        """
    
    @staticmethod
    def compilar_documento_html(tipo_documento: str,
                               paciente_data: Dict[str, Any],
                               conteudo: str,
                               incluir_assinaturas: bool = True) -> str:
        """
        Compila documento HTML completo para PDF
        
        Args:
            tipo_documento: Tipo do documento
            paciente_data: Dados do paciente
            conteudo: Conteúdo principal
            incluir_assinaturas: Se deve incluir área de assinaturas
            
        Returns:
            HTML completo formatado
        """
        # Processar conteúdo com TextUtils
        conteudo_processado = TextUtils.processar_texto_pdf(conteudo)
        
        # Montar documento completo
        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{tipo_documento} - {paciente_data.get('nome', 'Paciente')}</title>
            {PDFService.gerar_css_padrao()}
        </head>
        <body>
            {PDFService.gerar_cabecalho_documento(tipo_documento, paciente_data)}
            
            <div class="conteudo">
                {conteudo_processado}
            </div>
            
            {PDFService.gerar_area_assinaturas() if incluir_assinaturas else ''}
            
            {PDFService.gerar_rodape_documento()}
        </body>
        </html>
        """
        
        return html_completo
    
    @staticmethod
    def preparar_configuracao_impressao():
        """
        Prepara configuração padrão para impressão PDF
        
        Returns:
            Dicionário com configurações
        """
        return {
            'page_size': 'A4',
            'orientation': 'Portrait',
            'margins_mm': PDFService.DEFAULT_CONFIG['margins'],
            'high_resolution': True,
            'output_format': 'PDF'
        }
    
    @staticmethod
    def gerar_caminho_arquivo_temp(tipo_documento: str, 
                                  paciente_data: Dict[str, Any]) -> str:
        """
        Gera caminho para arquivo temporário
        
        Args:
            tipo_documento: Tipo do documento
            paciente_data: Dados do paciente
            
        Returns:
            Caminho completo do arquivo temporário
        """
        pasta_temp = FileManager.obter_pasta_temporaria()
        nome_arquivo = PDFService.gerar_nome_arquivo_pdf(paciente_data, tipo_documento)
        return os.path.join(pasta_temp, nome_arquivo)
    
    @staticmethod
    def validar_pdf_gerado(caminho_arquivo: str) -> tuple[bool, Optional[str]]:
        """
        Valida se o PDF foi gerado corretamente
        
        Args:
            caminho_arquivo: Caminho do arquivo PDF
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        from ..services import ValidationService
        return ValidationService.validar_arquivo_pdf(caminho_arquivo)
