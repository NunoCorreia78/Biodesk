#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def fix_ficha_paciente_indentation():
    """Remove linhas com indentação incorreta do ficha_paciente.py"""
    file_path = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    inside_method = False
    method_indent = 0
    
    for i, line in enumerate(lines):
        # Detectar início de método ou classe
        if re.match(r'^\s*(def |class )', line):
            inside_method = True
            method_indent = len(line) - len(line.lstrip())
            cleaned_lines.append(line)
            continue
            
        # Se estamos dentro de um método
        if inside_method:
            line_indent = len(line) - len(line.lstrip())
            
            # Se a linha está vazia ou é apenas espaços em branco, manter
            if line.strip() == '':
                cleaned_lines.append(line)
                continue
                
            # Remover linhas com indentação excessiva que contêm imports órfãos
            if line_indent > method_indent + 8:  # Mais de 8 espaços além do método
                # Se contém import ou from, provavelmente é lixo
                if re.search(r'(from |import |^\s+from |^\s+import )', line):
                    print(f"Removendo linha {i+1}: {line.strip()}")
                    continue
                    
            # Detectar fim do método (próxima definição)
            if line_indent <= method_indent and line.strip() and not line.startswith('#'):
                inside_method = False
                
        cleaned_lines.append(line)
    
    # Escrever ficheiro limpo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
        
    print(f"Limpeza concluída. Ficheiro {file_path} foi corrigido.")

if __name__ == "__main__":
    fix_ficha_paciente_indentation()
