#!/usr/bin/env python3
"""Script para corrigir indentações excessivas"""

import re

def fix_indentation(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir indentações excessivas (mais de 16 espaços) para indentação normal
    content = re.sub(r'^(\s{20,})QMessageBox', r'                QMessageBox', content, flags=re.MULTILINE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Indentações corrigidas")

if __name__ == "__main__":
    fix_indentation(r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py")
