#!/usr/bin/env python3
"""
Script para converter todos os diálogos PyQt6 para usar textos em português
"""

import os
import re
import glob

def converter_dialogo_para_pt(content):
    """Converte diálogos PyQt6 para português europeu"""
    
    # Padrão para QMessageBox.question - substituir por versão com botões portugueses
    pattern_question = r'QMessageBox\.question\s*\(\s*([^,]+),\s*([^,]+),\s*([^,]+)(?:,\s*[^)]+)?\s*\)'
    
    def replace_question(match):
        parent = match.group(1)
        title = match.group(2)
        text = match.group(3)
        
        return f"""QMessageBox.question(
            {parent},
            {title},
            {text},
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )"""
    
    content = re.sub(pattern_question, replace_question, content, flags=re.MULTILINE | re.DOTALL)
    
    # Padrão para QMessageBox.information - adicionar botão OK em português
    pattern_info = r'QMessageBox\.information\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\s*\)'
    
    def replace_info(match):
        parent = match.group(1)
        title = match.group(2)
        text = match.group(3)
        
        return f"""QMessageBox.information(
            {parent},
            {title},
            {text}
        
        )"""
    
    content = re.sub(pattern_info, replace_info, content, flags=re.MULTILINE | re.DOTALL)
    
    # Padrão para QMessageBox.warning
    pattern_warning = r'QMessageBox\.warning\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\s*\)'
    
    def replace_warning(match):
        parent = match.group(1)
        title = match.group(2) 
        text = match.group(3)
        
        return f"""QMessageBox.warning(
            {parent},
            {title},
            {text}
        
        )"""
    
    content = re.sub(pattern_warning, replace_warning, content, flags=re.MULTILINE | re.DOTALL)
    
    # Padrão para QMessageBox.critical
    pattern_critical = r'QMessageBox\.critical\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\s*\)'
    
    def replace_critical(match):
        parent = match.group(1)
        title = match.group(2)
        text = match.group(3)
        
        return f"""QMessageBox.critical(
            {parent},
            {title},
            {text}
        
        )"""
    
    content = re.sub(pattern_critical, replace_critical, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def processar_arquivo(filepath):
    """Processa um arquivo Python individual"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se tem QMessageBox
        if 'QMessageBox.' not in content:
            return False
            
        original_content = content
        content = converter_dialogo_para_pt(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Atualizado: {filepath}")
            return True
        else:
            print(f"➖ Sem mudanças: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Erro em {filepath}: {e}")
        return False

def main():
    """Função principal"""
    workspace = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Encontrar todos os arquivos Python
    pattern = os.path.join(workspace, '**', '*.py')
    arquivos = glob.glob(pattern, recursive=True)
    
    print(f"🔍 Encontrados {len(arquivos)} arquivos Python")
    
    atualizados = 0
    for arquivo in arquivos:
        if processar_arquivo(arquivo):
            atualizados += 1
    
    print(f"\n📊 Resumo:")
    print(f"   🔄 Arquivos processados: {len(arquivos)}")
    print(f"   ✅ Arquivos atualizados: {atualizados}")
    print(f"   ➖ Sem mudanças: {len(arquivos) - atualizados}")

if __name__ == "__main__":
    main()
