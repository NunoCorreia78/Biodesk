#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 BUSCA CÓDIGO CONFLITUANTE - SISTEMA DE ASSINATURAS
===================================================
"""

import os
import re

def buscar_codigo_conflituante():
    """Busca código relacionado a assinaturas e centralização em todo o workspace"""
    
    problemas = {
        'duplicacoes': [],
        'conflitos_css': [],
        'codigo_obsoleto': [],
        'centralizacao': []
    }
    
    # Padrões para buscar
    padroes = {
        'table_width': r'table.*width.*(?:100%|70%|85%)',
        'margin_negativo': r'margin.*-\d+px',
        'assinatura_css': r'\.assinatura|\.linha-assinatura|\.signature',
        'centralizacao': r'text-align.*center|margin.*auto',
        'pdf_generation': r'gerar_pdf|generate_pdf|QPrinter'
    }
    
    # Arquivos relevantes
    arquivos_alvo = [
        'ficha_paciente.py',
        'ficha_paciente/declaracao_saude.py', 
        'ficha_paciente/consentimentos.py',
        'services/pdf.py',
        'sistema_assinatura.py'
    ]
    
    for arquivo in arquivos_alvo:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
                # Verificar múltiplas definições de largura de tabela
                if arquivo.endswith('declaracao_saude.py'):
                    # Encontrar TODAS as definições de estilo
                    estilos = re.findall(r'<style[^>]*>.*?</style>', conteudo, re.DOTALL)
                    table_defs = re.findall(r'table\s*{[^}]*width:[^;]+;', conteudo)
                    
                    if len(table_defs) > 1:
                        problemas['duplicacoes'].append(f"{arquivo}: {len(table_defs)} definições de table width")
                    
                    # Verificar conflitos de margin
                    margin_negativos = re.findall(r'margin:\s*-?\d+px', conteudo)
                    if margin_negativos:
                        problemas['conflitos_css'].append(f"{arquivo}: margins conflitantes: {margin_negativos[:3]}")
    
    return problemas

# Executar busca
if __name__ == "__main__":
    problemas = buscar_codigo_conflituante()
    print("PROBLEMAS ENCONTRADOS:")
    for tipo, lista in problemas.items():
        if lista:
            print(f"\n{tipo.upper()}:")
            for item in lista:
                print(f"  - {item}")
    
    print("\n" + "="*50)
    print("ARQUIVOS DE TESTE OBSOLETOS IDENTIFICADOS:")
    arquivos_teste = [
        'teste_assinatura_otimizada.py',
        'teste_espacamento_pdf.py',
        'teste_sistema_assinaturas_final.py',
        'assinatura_formatter.py',
        'validacao_sistema_assinaturas.py'
    ]
    
    for arquivo in arquivos_teste:
        if os.path.exists(arquivo):
            print(f"  ❌ {arquivo}")
        else:
            print(f"  ✅ {arquivo} (já removido)")
