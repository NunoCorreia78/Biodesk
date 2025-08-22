#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎨 MÓDULO UNIFICADO DE FORMATAÇÃO DE ASSINATURAS
===============================================

Este módulo centraliza a formatação de assinaturas para todos os tipos de documentos
mantendo um canvas comum e permitindo estruturas diferentes por tipo de documento.

ARQUITETURA PROPOSTA:
┌─────────────────────────────────────────────┐
│           CANVAS COMUM                      │
│      (sistema_assinatura.py)               │
│   ✅ 400x120px + linha guia                │
│   ✅ Sem scroll bars                        │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│       FORMATAÇÃO UNIFICADA                  │
│    (assinatura_formatter.py) - ESTE        │
│  📐 Espaçamento: compacto                  │
│  🎨 Visual: consistente                    │
│  🔄 Aplicação: todos os documentos        │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  DECLARAÇÃO     │    │  CONSENTIMENTOS │
│  HTML/CSS       │    │  ReportLab      │
│  QTextDocument  │    │  Canvas Direct  │
└─────────────────┘    └─────────────────┘
"""

from typing import Optional, Dict, Any, Tuple
import base64
import io
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QByteArray, QBuffer


class AssinaturaFormatter:
    """Formatador unificado para assinaturas em todos os tipos de documentos"""
    
    # Configurações unificadas
    CANVAS_SIZE = (400, 120)  # Tamanho otimizado do canvas
    SPACING_COMPACT = -15     # Espaçamento compacto (px)
    LINE_HEIGHT_COMPACT = 0.8  # Altura de linha compacta
    
    # Estilos CSS unificados
    CSS_SIGNATURE_CONTAINER = """
        text-align: center; 
        width: 100%;
    """
    
    CSS_SIGNATURE_BOX = """
        height: 50px; 
        border: 1px solid #ccc; 
        margin: 0 auto; 
        background: white; 
        border-radius: 4px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        width: 85%; 
        padding: 2px;
    """
    
    CSS_NAME_SECTION = f"""
        margin: {SPACING_COMPACT}px 0 0 0; 
        line-height: {LINE_HEIGHT_COMPACT}; 
        text-align: center;
    """
    
    @classmethod
    def format_html_signature_section(cls, 
                                    title: str, 
                                    signature_html: str, 
                                    name: str, 
                                    date: str,
                                    title_icon: str = "👤") -> str:
        """
        Gera seção HTML unificada para assinatura
        
        Args:
            title: Título da seção (ex: "ASSINATURA DO PACIENTE")
            signature_html: HTML da assinatura (Base64)
            name: Nome do assinante
            date: Data da assinatura
            title_icon: Ícone do título
            
        Returns:
            HTML formatado da seção de assinatura
        """
        return f"""
        <div style="{cls.CSS_SIGNATURE_CONTAINER}">
            <h4 style="margin: 0 0 5px 0; color: #1f2937; font-size: 14pt; font-weight: bold;">
                {title_icon} {title}
            </h4>
            <div style="{cls.CSS_SIGNATURE_BOX}">
                {signature_html}
            </div>
            <div style="{cls.CSS_NAME_SECTION}">
                <strong>{name}</strong><br>
                <span style="font-size: 10pt; color: #666;">{date}</span>
            </div>
        </div>
        """
    
    @classmethod
    def format_html_dual_signature_table(cls, 
                                        patient_data: Dict[str, Any],
                                        professional_data: Dict[str, Any]) -> str:
        """
        Gera tabela HTML com assinaturas lado a lado
        
        Args:
            patient_data: {'html': str, 'name': str, 'date': str}
            professional_data: {'html': str, 'name': str, 'date': str}
            
        Returns:
            HTML da tabela de assinaturas
        """
        patient_section = cls.format_html_signature_section(
            "ASSINATURA DO PACIENTE",
            patient_data['html'],
            patient_data['name'],
            patient_data['date'],
            "👤"
        )
        
        professional_section = cls.format_html_signature_section(
            "ASSINATURA DO PROFISSIONAL", 
            professional_data['html'],
            professional_data['name'],
            professional_data['date'],
            "👨‍⚕️"
        )
        
        return f"""
        <table style="width: 100%; border-collapse: collapse; margin: 15px auto 15px auto;">
            <tr>
                <td style="width: 50%; vertical-align: top; text-align: center; padding: 0 10px;">
                    {patient_section}
                </td>
                <td style="width: 50%; vertical-align: top; text-align: center; padding: 0 10px;">
                    {professional_section}
                </td>
            </tr>
        </table>
        """
    
    @classmethod
    def get_reportlab_table_style(cls):
        """
        Retorna configuração de estilo otimizada para tabelas ReportLab
        
        Returns:
            Lista de configurações de estilo para TableStyle
        """
        from reportlab.lib import colors
        
        return [
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            # ESPAÇAMENTO COMPACTO: assinatura e nome próximos
            ('TOPPADDING', (0, 1), (-1, 1), 2),     # Assinaturas: pouco espaço acima
            ('BOTTOMPADDING', (0, 1), (-1, 1), 0),  # Assinaturas: zero espaço abaixo  
            ('TOPPADDING', (0, 2), (-1, 2), 0),     # Nomes: zero espaço acima
            ('BOTTOMPADDING', (0, 2), (-1, 2), 8),  # Nomes: espaço normal abaixo
            # Espaço normal para labels e datas
            ('TOPPADDING', (0, 0), (-1, 0), 8),     # Labels
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 3), (-1, 3), 8),     # Datas  
            ('BOTTOMPADDING', (0, 3), (-1, 3), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]
    
    @classmethod
    def optimize_signature_canvas_settings(cls) -> Dict[str, Any]:
        """
        Retorna configurações otimizadas para o canvas de assinatura
        
        Returns:
            Dicionário com configurações do canvas
        """
        return {
            'width': cls.CANVAS_SIZE[0],
            'height': cls.CANVAS_SIZE[1], 
            'show_scrollbars': False,
            'show_guidance_line': True,
            'background_color': 'white',
            'pen_color': 'black',
            'pen_width': 2
        }
    
    @classmethod
    def signature_to_base64(cls, pixmap: QPixmap) -> str:
        """
        Converte QPixmap de assinatura para Base64 HTML
        
        Args:
            pixmap: QPixmap da assinatura
            
        Returns:
            String HTML com imagem Base64
        """
        if pixmap.isNull():
            return '<span style="color: #999; font-style: italic;">Sem assinatura</span>'
        
        # Converter para bytes
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        
        # Converter para Base64
        base64_string = base64.b64encode(byte_array.data()).decode('utf-8')
        
        return f'<img src="data:image/png;base64,{base64_string}" style="max-width: 100%; height: auto;">'


def demonstrar_uso():
    """Demonstração de como usar o formatador unificado"""
    print("🎨 FORMATADOR UNIFICADO DE ASSINATURAS")
    print("=" * 50)
    
    print("\n✅ FUNCIONALIDADES:")
    print("📐 Canvas otimizado: 400x120px")
    print("🎯 Espaçamento compacto: -15px")
    print("📄 HTML unificado para declarações")
    print("📊 ReportLab otimizado para consentimentos")
    print("🔄 Configurações centralizadas")
    
    print("\n🏗️ COMO USAR:")
    print("1. Import: from assinatura_formatter import AssinaturaFormatter")
    print("2. HTML: AssinaturaFormatter.format_html_signature_section(...)")
    print("3. ReportLab: AssinaturaFormatter.get_reportlab_table_style()")
    print("4. Canvas: AssinaturaFormatter.optimize_signature_canvas_settings()")


if __name__ == "__main__":
    demonstrar_uso()
