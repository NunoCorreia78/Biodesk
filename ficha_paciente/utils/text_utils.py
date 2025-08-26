"""
Biodesk - Text Utils
====================

Utilitários para processamento de texto e formatação.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Processamento de texto para PDF
- Formatação automática de parágrafos
- Quebras de linha inteligentes
- Otimização de layout

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

import re
from typing import Optional


class TextUtils:
    """Utilitários para processamento e formatação de texto"""
    
    @staticmethod
    def processar_texto_pdf(texto: Optional[str]) -> str:
        """
        Processa texto para PDF com quebras de linha adequadas e formatação otimizada
        
        Args:
            texto: Texto a ser processado
            
        Returns:
            Texto processado com formatação HTML para PDF
        """
        if not texto:
            return ""
        
        # Dividir em parágrafos
        paragrafos = texto.split('\n')
        paragrafos_processados = []
        
        for paragrafo in paragrafos:
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue
                
            # Remover quebras de linha inadequadas no meio de frases
            paragrafo = ' '.join(paragrafo.split())
            
            # Adicionar quebras automáticas para linhas muito longas (mais de 80 caracteres)
            if len(paragrafo) > 80:
                # Tentar quebrar em pontuação natural
                frases = re.split(r'([.!?]\s+)', paragrafo)
                paragrafo_quebrado = ""
                linha_atual = ""
                
                for i, frase in enumerate(frases):
                    if i % 2 == 0:  # Texto da frase
                        if len(linha_atual + frase) > 80 and linha_atual:
                            paragrafo_quebrado += linha_atual.strip() + "<br>"
                            linha_atual = frase
                        else:
                            linha_atual += frase
                    else:  # Pontuação
                        linha_atual += frase
                        
                paragrafo_quebrado += linha_atual
                paragrafo = paragrafo_quebrado
            
            paragrafos_processados.append(f"<p>{paragrafo}</p>")
        
        return "\n".join(paragrafos_processados)
    
    @staticmethod
    def limpar_texto(texto: Optional[str]) -> str:
        """
        Remove caracteres indesejados e normaliza o texto
        
        Args:
            texto: Texto a ser limpo
            
        Returns:
            Texto limpo e normalizado
        """
        if not texto:
            return ""
        
        # Remover espaços extras
        texto = ' '.join(texto.split())
        
        # Remover caracteres especiais problemáticos
        texto = texto.replace('\r', '\n')
        texto = re.sub(r'\n+', '\n', texto)
        
        return texto.strip()
    
    @staticmethod
    def formatar_nome_arquivo(nome: str) -> str:
        """
        Formata nome para uso em arquivos (remove caracteres especiais)
        
        Args:
            nome: Nome a ser formatado
            
        Returns:
            Nome formatado para arquivo
        """
        if not nome:
            return "arquivo"
        
        # Remover acentos e caracteres especiais
        nome = re.sub(r'[áàâãä]', 'a', nome, flags=re.IGNORECASE)
        nome = re.sub(r'[éèêë]', 'e', nome, flags=re.IGNORECASE)
        nome = re.sub(r'[íìîï]', 'i', nome, flags=re.IGNORECASE)
        nome = re.sub(r'[óòôõö]', 'o', nome, flags=re.IGNORECASE)
        nome = re.sub(r'[úùûü]', 'u', nome, flags=re.IGNORECASE)
        nome = re.sub(r'[ç]', 'c', nome, flags=re.IGNORECASE)
        
        # Remover caracteres não permitidos
        nome = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', nome)
        
        # Remover underscores múltiplos
        nome = re.sub(r'_+', '_', nome)
        
        return nome.strip('_')
    
    @staticmethod
    def truncar_texto(texto: str, max_length: int = 100, sufixo: str = "...") -> str:
        """
        Trunca texto mantendo palavras completas
        
        Args:
            texto: Texto a ser truncado
            max_length: Comprimento máximo
            sufixo: Sufixo a adicionar quando truncado
            
        Returns:
            Texto truncado
        """
        if not texto or len(texto) <= max_length:
            return texto
        
        # Truncar na última palavra completa
        truncado = texto[:max_length - len(sufixo)]
        ultima_espaco = truncado.rfind(' ')
        
        if ultima_espaco > 0:
            truncado = truncado[:ultima_espaco]
        
        return truncado + sufixo
    
    @staticmethod
    def processar_texto_pdf(texto: str) -> str:
        """
        Processa texto para uso em PDFs (formatação HTML)
        
        Args:
            texto: Texto a ser processado
            
        Returns:
            Texto formatado para PDF
        """
        if not texto:
            return ""
        
        # Limpar texto básico
        texto = TextUtils.limpar_texto(texto)
        
        # Converter quebras de linha para parágrafos HTML
        paragrafos = texto.split('\n')
        paragrafos_html = []
        
        for paragrafo in paragrafos:
            paragrafo = paragrafo.strip()
            if paragrafo:
                # Escapar caracteres HTML especiais
                paragrafo = paragrafo.replace('&', '&amp;')
                paragrafo = paragrafo.replace('<', '&lt;')
                paragrafo = paragrafo.replace('>', '&gt;')
                
                # Adicionar formatação
                paragrafos_html.append(f"<p>{paragrafo}</p>")
        
        return "\n".join(paragrafos_html)
