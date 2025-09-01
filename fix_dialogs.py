from PyQt6.QtWidgets import QMessageBox
#!/usr/bin/env python3
"""
Script para padronizar todas as caixas de diálogo BiodeskMessageBox
para usar as funções padrão do biodesk_dialogs
"""

import re
import os

def fix_dialogs_in_file(filepath):
    """Corrige os diálogos em um arquivo específico"""
    
    if not os.path.exists(filepath):
        print(f"Arquivo não encontrado: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Substituir BiodeskMessageBox.information
    content = re.sub(
        r'BiodeskMessageBox\.information\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
        r'QMessageBox.information(\1, \2, \3)',
        content
    )
    
    # Substituir BiodeskMessageBox.warning
    content = re.sub(
        r'BiodeskMessageBox\.warning\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
        r'QMessageBox.warning(\1, \2, \3)',
        content
    )
    
    # Substituir BiodeskMessageBox.critical
    content = re.sub(
        r'BiodeskMessageBox\.critical\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
        r'QMessageBox.critical(\1, \2, \3)',
        content
    )
    
    # Substituir BiodeskMessageBox.question
    content = re.sub(
        r'BiodeskMessageBox\.question\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
        r'QMessageBox.question(\1, \2, \3)',
        content
    )
    
    # Adicionar imports se necessário
    if 'mostrar_sucesso' in content or 'mostrar_erro' in content or 'mostrar_aviso' in content or 'mostrar_confirmacao' in content:
        if '            # Adicionar imports no início
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    lines.insert(i, '                    break
            content = '\n'.join(lines)
    
    # Salvar apenas se houve mudanças
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Corrigido: {filepath}")
        return True
    else:
        print(f"ℹ️ Sem alterações: {filepath}")
        return False

# Lista de arquivos para corrigir
files_to_fix = [
    r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente\iris_integration.py"
]

print("🔧 Corrigindo caixas de diálogo...")
total_fixed = 0

for filepath in files_to_fix:
    if fix_dialogs_in_file(filepath):
        total_fixed += 1

print(f"\n✅ Concluído! {total_fixed} arquivo(s) corrigido(s).")
