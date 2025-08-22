#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 SCRIPT DE LIMPEZA DO WORKSPACE
===============================
Remove arquivos temporários e obsoletos do workspace
"""

import os
import shutil
from datetime import datetime

def limpar_workspace():
    """Remove arquivos temporários e obsoletos do workspace"""
    
    limpezas = {
        'arquivos_temp': [],
        'backups_antigos': [],
        'codigo_obsoleto': []
    }
    
    # 1. Limpar pasta temp
    if os.path.exists('temp'):
        for arquivo in os.listdir('temp'):
            if arquivo.startswith('sig_') and arquivo.endswith('.png'):
                caminho = os.path.join('temp', arquivo)
                try:
                    os.remove(caminho)
                    limpezas['arquivos_temp'].append(arquivo)
                except:
                    pass
    
    # 2. Remover arquivos de backup antigos
    pastas_backup = ['backup_declaracoes', 'backup_temp_assinaturas', 'backup_consentimentos']
    for pasta in pastas_backup:
        if os.path.exists(pasta):
            try:
                shutil.rmtree(pasta)
                limpezas['backups_antigos'].append(pasta)
            except:
                pass
    
    # 3. Remover arquivos Python obsoletos/teste
    arquivos_obsoletos = [
        'teste_assinatura_otimizada.py',
        'analise_assinaturas.py',
        'assinatura_formatter.py',
        'teste_pdf_assinatura.py',
        'teste_espacamento_pdf.py',
        'teste_sistema_assinaturas_final.py',
        'validacao_sistema_assinaturas.py'
    ]
    
    for arquivo in arquivos_obsoletos:
        if os.path.exists(arquivo):
            try:
                os.remove(arquivo)
                limpezas['codigo_obsoleto'].append(arquivo)
            except:
                pass
    
    # 4. Criar estrutura limpa
    pastas_necessarias = ['temp', 'documentos', 'Documentos_Pacientes']
    for pasta in pastas_necessarias:
        os.makedirs(pasta, exist_ok=True)
    
    # Relatório
    print("=" * 50)
    print("LIMPEZA DO WORKSPACE CONCLUÍDA")
    print("=" * 50)
    
    total = 0
    for categoria, arquivos in limpezas.items():
        if arquivos:
            print(f"\n{categoria.upper()}:")
            for arquivo in arquivos:
                print(f"  ✓ {arquivo}")
                total += 1
    
    print(f"\nTotal de itens removidos: {total}")
    print(f"Workspace limpo em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    return limpezas

if __name__ == "__main__":
    limpar_workspace()
