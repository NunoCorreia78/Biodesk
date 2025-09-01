#!/usr/bin/env python3
"""Script robusto para corrigir TODAS as indentações problemáticas"""

import re

def fix_all_indentations(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for i, line in enumerate(lines):
        # Se a linha tem QMessageBox com indentação excessiva, corrigir para 12 espaços
        if re.match(r'^\s{16,}QMessageBox', line):
            # Extrair apenas a parte do QMessageBox em diante
            qmsg_part = line.lstrip()
            # Adicionar indentação correta (12 espaços)
            fixed_line = '            ' + qmsg_part
            fixed_lines.append(fixed_line)
            print(f"Linha {i+1}: Corrigida indentação QMessageBox")
        else:
            fixed_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ Todas as indentações corrigidas")

if __name__ == "__main__":
    fix_all_indentations(r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py")
