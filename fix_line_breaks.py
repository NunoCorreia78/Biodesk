#!/usr/bin/env python3
"""
Corrige problemas de quebras de linha
"""

import re

def fix_line_breaks(content):
    """Corrige quebras de linha perdidas"""
    
    # Padrão: código:espaços_opcionaisBiodeskMessageBox -> código:\n                BiodeskMessageBox
    pattern = r'(\S+:)\s*(BiodeskMessageBox\.[a-zA-Z_]+\()'
    replacement = r'\1\n                \2'
    content = re.sub(pattern, replacement, content)
    
    # Padrão: else:BiodeskMessageBox -> else:\n            BiodeskMessageBox
    pattern = r'(else:)\s*(BiodeskMessageBox\.[a-zA-Z_]+\()'
    replacement = r'\1\n            \2'
    content = re.sub(pattern, replacement, content)
    
    # Padrão: except ImportError:BiodeskMessageBox -> except ImportError:\n            BiodeskMessageBox
    pattern = r'(except [^:]+:)\s*(BiodeskMessageBox\.[a-zA-Z_]+\()'
    replacement = r'\1\n            \2'
    content = re.sub(pattern, replacement, content)
    
    return content

# Corrigir ficha_paciente.py
try:
    with open('ficha_paciente.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixed_content = fix_line_breaks(content)
    
    with open('ficha_paciente.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Corrigido: ficha_paciente.py")

except Exception as e:
    print(f"❌ Erro: {e}")

print("✅ Correção concluída!")
