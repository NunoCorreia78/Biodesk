#!/usr/bin/env python3
"""
🔧 CORRETOR AUTOMÁTICO DE DIÁLOGOS - BIODESK
===========================================

Script para corrigir automaticamente todas as inconsistências de diálogos
e padronizar para o sistema mostrar_* (biodesk_dialogs)
"""

import os
import re
import glob

def corrigir_arquivo(caminho_arquivo):
    """Corrige um arquivo específico"""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        conteudo_original = conteudo
        
        # 1. Adicionar import se necessário
        if '            # Procurar onde adicionar o import
            if 'from PyQt6.QtWidgets import' in conteudo:
                conteudo = conteudo.replace(
                    'from PyQt6.QtWidgets import',
                    '                )
            elif 'import sys' in conteudo:
                conteudo = conteudo.replace(
                    'import sys',
                    'import sys\n                )
        
        # 2. Substituições de BiodeskMessageBox
        substituicoes = [
            (r'BiodeskMessageBox\.information\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.information(\1, \2)'), (r'BiodeskMessageBox\.warning\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.warning(\1, \2)'), (r'BiodeskMessageBox\.critical\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.critical(\1, \2)'), (r'BiodeskMessageBox\.question\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.question(\1, \2)'), ]
        
        # 3. Substituições de QMessageBox
        substituicoes_q = [
            (r'QMessageBox\.information\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.information(\1, \2)'), (r'QMessageBox\.warning\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.warning(\1, \2)'), (r'QMessageBox\.critical\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.critical(\1, \2)'), (r'QMessageBox\.question\s*\([^,]+,\s*([^,]+),\s*([^)]+)\)', r'QMessageBox.question(\1, \2)'), ]
        
        # Aplicar substituições
        for padrao, substituicao in substituicoes + substituicoes_q:
            conteudo = re.sub(padrao, substituicao, conteudo, flags=re.MULTILINE | re.DOTALL)
        
        # Salvar se houve mudanças
        if conteudo != conteudo_original:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            print(f"✅ Corrigido: {caminho_arquivo}")
            return True
        else:
            print(f"⚪ Nenhuma alteração: {caminho_arquivo}")
            return False
            
    except Exception as e:
        print(f"❌ Erro em {caminho_arquivo}: {e}")
        return False

def main():
    """Função principal"""
    # Diretório base
    base_dir = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Arquivos Python para corrigir
    arquivos = []
    
    # Buscar todos os arquivos .py
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('fix_'):
                arquivos.append(os.path.join(root, file))
    
    print(f"🔍 Encontrados {len(arquivos)} arquivos Python")
    
    corrigidos = 0
    for arquivo in arquivos:
        if corrigir_arquivo(arquivo):
            corrigidos += 1
    
    print(f"\n🎉 RESULTADO: {corrigidos} arquivos corrigidos de {len(arquivos)}")

if __name__ == "__main__":
    main()
