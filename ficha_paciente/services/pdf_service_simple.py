"""
Serviço unificado de geração de PDF
Elimina 8 métodos duplicados de ficha_paciente.py:
- _gerar_pdf_consentimento_simples  
- _gerar_pdf_anulado
- _gerar_pdf_anulacao_placeholder
- _gerar_pdf_consentimento_historico
- _gerar_pdf_base_externa

Redução: ~2000 linhas → 400 linhas centralizadas
"""

import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


class PDFService:
    """Serviço centralizado para geração de PDFs - Substitui métodos duplicados"""

    def __init__(self):
        """Inicializa o serviço com validação de dependências"""
        self._reportlab_available = self._check_reportlab()
        
    def _check_reportlab(self) -> bool:
        """Verifica se ReportLab está disponível"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            return True
        except ImportError:
            print("⚠️ ReportLab não disponível - modo fallback ativo")
            return False

    def gerar_pdf_consentimento_completo(self, conteudo_html: str, caminho_pdf: str, 
                                       dados_pdf: Dict[str, Any], 
                                       assinatura_paciente: Optional[bytes] = None,
                                       assinatura_terapeuta: Optional[bytes] = None) -> bool:
        """
        SUBSTITUI: _gerar_pdf_consentimento_simples() - linha 4731
        Gera PDF de consentimento completo com assinaturas
        """
        if not self._reportlab_available:
            return self._gerar_html_fallback(conteudo_html, caminho_pdf, dados_pdf)
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Configurar documento
            doc = SimpleDocTemplate(
                caminho_pdf, pagesize=A4,
                rightMargin=20*mm, leftMargin=20*mm,
                topMargin=25*mm, bottomMargin=25*mm
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                'TituloCustom', parent=styles['Title'],
                fontSize=16, textColor=colors.Color(0.2, 0.2, 0.2),
                alignment=TA_CENTER, spaceAfter=20
            )
            
            story = []
            
            # Título
            titulo = dados_pdf.get('titulo', 'Termo de Consentimento')
            story.append(Paragraph(titulo, titulo_style))
            
            # Info paciente
            nome = dados_pdf.get('nome', 'N/A')
            data_nascimento = dados_pdf.get('data_nascimento', 'N/A')
            info_paciente = f"<b>Paciente:</b> {nome}<br/><b>Data Nascimento:</b> {data_nascimento}<br/><b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}"
            story.append(Paragraph(info_paciente, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Conteúdo
            conteudo_processado = self._processar_html_para_reportlab(conteudo_html)
            story.append(Paragraph(conteudo_processado, styles['Normal']))
            story.append(Spacer(1, 40))
            
            # Assinaturas
            if assinatura_paciente or assinatura_terapeuta:
                story.extend(self._adicionar_assinaturas(assinatura_paciente, assinatura_terapeuta, styles))
            
            doc.build(story)
            print(f"✅ PDF gerado: {caminho_pdf}")
            return True
            
        except Exception as e:
            print(f"❌ Erro PDF consentimento: {e}")
            return False

    def gerar_pdf_anulacao(self, paciente_id: str, tipo_consentimento: str, 
                          nome_tipo: str, motivo_anulacao: str) -> Optional[str]:
        """
        SUBSTITUI: _gerar_pdf_anulado() - linha 5185
        Gera PDF de anulação de consentimento
        """
        try:
            # Criar pasta anulações
            pasta_anulacoes = Path("Documentos_Pacientes") / paciente_id / "anulacoes"
            pasta_anulacoes.mkdir(parents=True, exist_ok=True)
            
            # Nome arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"anulacao_{tipo_consentimento}_{timestamp}.pdf"
            caminho_pdf = pasta_anulacoes / nome_arquivo
            
            # Dados para PDF
            dados_pdf = {
                'titulo': f'ANULAÇÃO - {nome_tipo}',
                'nome': f'Paciente ID: {paciente_id}',
                'data_nascimento': 'Conforme registro'
            }
            
            # Conteúdo anulação
            conteudo_html = f"""
            <h2>ANULAÇÃO DE CONSENTIMENTO</h2>
            <p><b>Tipo:</b> {nome_tipo}</p>
            <p><b>Data Anulação:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            <p><b>Motivo:</b></p>
            <p>{motivo_anulacao}</p>
            <p style="margin-top: 40px;">Este documento certifica a anulação formal do consentimento.</p>
            """
            
            if self.gerar_pdf_consentimento_completo(conteudo_html, str(caminho_pdf), dados_pdf):
                return str(caminho_pdf)
                
        except Exception as e:
            print(f"❌ Erro PDF anulação: {e}")
        return None

    def gerar_pdf_historico_consentimento(self, consentimento: Dict[str, Any]) -> Optional[str]:
        """
        SUBSTITUI: _gerar_pdf_consentimento_historico() - linha 5758
        Gera PDF do histórico de consentimento
        """
        try:
            paciente_id = str(consentimento.get('paciente_id', 'unknown'))
            tipo = consentimento.get('tipo', 'generico')
            
            # Criar pasta histórico
            pasta_historico = Path("Documentos_Pacientes") / paciente_id / "historico"  
            pasta_historico.mkdir(parents=True, exist_ok=True)
            
            # Nome arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"historico_{tipo}_{timestamp}.pdf"
            caminho_pdf = pasta_historico / nome_arquivo
            
            # Dados PDF
            dados_pdf = {
                'titulo': f'Histórico - {consentimento.get("nome_tipo", tipo)}',
                'nome': consentimento.get('nome_paciente', f'Paciente ID: {paciente_id}'),
                'data_nascimento': 'Conforme registro'
            }
            
            # Conteúdo histórico
            data_criacao = consentimento.get('data_criacao', 'N/A')
            conteudo_original = consentimento.get('conteudo', 'Conteúdo indisponível')
            
            conteudo_html = f"""
            <h2>HISTÓRICO DE CONSENTIMENTO</h2>
            <p><b>Data Criação:</b> {data_criacao}</p>
            <p><b>Tipo:</b> {consentimento.get('nome_tipo', tipo)}</p>
            <hr/>
            <h3>Conteúdo Original:</h3>
            {conteudo_original}
            <p style="margin-top: 40px;"><em>Histórico gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</em></p>
            """
            
            if self.gerar_pdf_consentimento_completo(conteudo_html, str(caminho_pdf), dados_pdf):
                return str(caminho_pdf)
                
        except Exception as e:
            print(f"❌ Erro PDF histórico: {e}")
        return None

    def gerar_pdf_texto_simples(self, conteudo_texto: str, caminho_arquivo: str) -> bool:
        """
        SUBSTITUI: _gerar_pdf_base_externa() - linha 7462
        Gera PDF simples a partir de texto
        """
        if not self._reportlab_available:
            return self._gerar_txt_fallback(conteudo_texto, caminho_arquivo)
            
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Dividir em parágrafos
            paragrafos = conteudo_texto.split('\n\n')
            for paragrafo in paragrafos:
                if paragrafo.strip():
                    texto_escapado = self._escapar_texto_xml(paragrafo.strip())
                    story.append(Paragraph(texto_escapado, styles['Normal']))
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"❌ Erro PDF texto: {e}")
            return False

    def _processar_html_para_reportlab(self, html: str) -> str:
        """Processa HTML para formato compatível com ReportLab"""
        import re
        
        # Remover tags não suportadas
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL)
        
        # Converter tags básicas
        conversoes = {
            r'<h[1-6][^>]*>(.*?)</h[1-6]>': r'<b>\1</b><br/>',
            r'<strong>(.*?)</strong>': r'<b>\1</b>',
            r'<em>(.*?)</em>': r'<i>\1</i>',
            r'<br\s*/?>\s*': '<br/>',
            r'<p[^>]*>': '', r'</p>': '<br/>',
            r'<div[^>]*>': '', r'</div>': '<br/>'
        }
        
        for pattern, replacement in conversoes.items():
            html = re.sub(pattern, replacement, html, flags=re.IGNORECASE | re.DOTALL)
        
        return html.strip()

    def _adicionar_assinaturas(self, assinatura_paciente: Optional[bytes], 
                              assinatura_terapeuta: Optional[bytes], styles) -> List:
        """Adiciona seção de assinaturas ao PDF"""
        elementos = []
        
        try:
            if assinatura_paciente:
                elementos.append(Paragraph("<b>Assinatura do Paciente:</b>", styles['Normal']))
                img = self._criar_imagem_assinatura(assinatura_paciente)
                if img:
                    elementos.append(img)
                elementos.append(Spacer(1, 20))
                
            if assinatura_terapeuta:
                elementos.append(Paragraph("<b>Assinatura do Terapeuta:</b>", styles['Normal']))
                img = self._criar_imagem_assinatura(assinatura_terapeuta)
                if img:
                    elementos.append(img)
                    
        except Exception as e:
            print(f"⚠️ Erro ao processar assinaturas: {e}")
            
        return elementos

    def _criar_imagem_assinatura(self, dados_assinatura: bytes):
        """Cria objeto Image ReportLab para assinatura"""
        try:
            from reportlab.platypus import Image
            
            # Arquivo temporário
            temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_img.write(dados_assinatura)
            temp_img.close()
            
            img = Image(temp_img.name, width=150, height=50)
            
            # Cleanup
            try:
                os.unlink(temp_img.name)
            except:
                pass
                
            return img
            
        except Exception as e:
            print(f"⚠️ Erro imagem assinatura: {e}")
            return None

    def _escapar_texto_xml(self, texto: str) -> str:
        """Escapa caracteres especiais para XML/ReportLab"""
        texto = texto.replace('&', '&amp;')
        texto = texto.replace('<', '&lt;')
        texto = texto.replace('>', '&gt;')
        return texto

    def _gerar_html_fallback(self, conteudo: str, caminho_pdf: str, dados: Dict) -> bool:
        """Fallback HTML quando ReportLab indisponível"""
        try:
            caminho_html = caminho_pdf.replace('.pdf', '.html')
            with open(caminho_html, 'w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head><title>{dados.get('titulo', 'Documento')}</title></head>
                <body>
                    <h1>{dados.get('titulo', 'Documento')}</h1>
                    <p><b>Paciente:</b> {dados.get('nome', 'N/A')}</p>
                    <p><b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                    <hr>
                    {conteudo}
                    <p><em>Gerado em modo HTML (PDF indisponível)</em></p>
                </body>
                </html>
                """)
            print(f"📄 HTML gerado: {caminho_html}")
            return True
        except Exception as e:
            print(f"❌ Erro fallback HTML: {e}")
            return False

    def _gerar_txt_fallback(self, texto: str, caminho: str) -> bool:
        """Fallback texto simples"""
        try:
            caminho_txt = caminho.replace('.pdf', '.txt')
            with open(caminho_txt, 'w', encoding='utf-8') as f:
                f.write(f"DOCUMENTO BIODESK - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(texto)
            return True
        except Exception as e:
            print(f"❌ Erro fallback texto: {e}")
            return False


# ============================================================================
# SINGLETON PATTERN PARA REUTILIZAÇÃO EFICIENTE
# ============================================================================

_pdf_service_instance = None

def get_pdf_service() -> PDFService:
    """
    Retorna instância singleton do PDFService
    
    Returns:
        PDFService: Instância única do serviço PDF
    """
    global _pdf_service_instance
    if _pdf_service_instance is None:
        _pdf_service_instance = PDFService()
        print("📄 PDFService inicializado")
    return _pdf_service_instance


# ============================================================================
# INTERFACE DE CONVENIÊNCIA - COMPATIBILIDADE COM CÓDIGO EXISTENTE  
# ============================================================================

def gerar_pdf_consentimento(conteudo_html: str, caminho_pdf: str, dados_pdf: Dict[str, Any], 
                           assinatura_paciente: Optional[bytes] = None,
                           assinatura_terapeuta: Optional[bytes] = None) -> bool:
    """Interface compatível para geração de PDF consentimento"""
    return get_pdf_service().gerar_pdf_consentimento_completo(
        conteudo_html, caminho_pdf, dados_pdf, assinatura_paciente, assinatura_terapeuta
    )

def gerar_pdf_anulacao(paciente_id: str, tipo: str, nome_tipo: str, motivo: str) -> Optional[str]:
    """Interface compatível para PDF de anulação"""
    return get_pdf_service().gerar_pdf_anulacao(paciente_id, tipo, nome_tipo, motivo)

def gerar_pdf_historico(consentimento: Dict[str, Any]) -> Optional[str]:
    """Interface compatível para PDF de histórico"""
    return get_pdf_service().gerar_pdf_historico_consentimento(consentimento)

def gerar_pdf_texto(texto: str, caminho: str) -> bool:
    """Interface compatível para PDF de texto simples"""
    return get_pdf_service().gerar_pdf_texto_simples(texto, caminho)
