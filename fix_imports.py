#!/usr/bin/env python3
"""
Correção dos imports duplicados e limpeza
"""

import re

def fix_imports(content):
    """Remove imports duplicados e adiciona import global"""
    
    # Remover todos os imports locais
    content = re.sub(r'\s*from biodesk_dialogs import BiodeskMessageBox\n', '', content)
    
    # Adicionar import global no topo, após imports do PyQt6
    pyqt_import_end = content.find('from PyQt6.QtGui import')
    if pyqt_import_end != -1:
        # Encontrar o fim da linha
        end_line = content.find('\n', pyqt_import_end)
        if end_line != -1:
            content = content[:end_line+1] + 'from biodesk_dialogs import BiodeskMessageBox\n' + content[end_line+1:]
    else:
        # Se não encontrar, adicionar no início
        content = 'from biodesk_dialogs import BiodeskMessageBox\n' + content
    
    return content

# Arquivos para corrigir
files = ['ficha_paciente.py', 'emails_agendados_manager.py']

for filename in files:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed_content = fix_imports(content)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ Corrigido: {filename}")
    
    except Exception as e:
        print(f"❌ Erro em {filename}: {e}")

print("✅ Correção concluída!")
