#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def aggressive_fix_ficha_paciente():
    """Corrige agressivamente problemas de indentação do ficha_paciente.py"""
    file_path = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Se a linha está vazia, manter
        if line.strip() == '':
            cleaned_lines.append(line)
            continue
            
        # Calcular indentação
        line_indent = len(line) - len(line.lstrip())
        
        # Linhas que começam na coluna 0 (imports principais, classes, etc.)
        if line_indent == 0:
            cleaned_lines.append(line)
            continue
            
        # Linhas com indentação 4 (métodos de classe)
        if line_indent == 4 and (line.strip().startswith('def ') or 
                                 line.strip().startswith('class ') or
                                 line.strip().startswith('self.') or
                                 line.strip().startswith('return ') or
                                 line.strip().startswith('if ') or
                                 line.strip().startswith('else') or
                                 line.strip().startswith('elif ') or
                                 line.strip().startswith('for ') or
                                 line.strip().startswith('while ') or
                                 line.strip().startswith('try:') or
                                 line.strip().startswith('except') or
                                 line.strip().startswith('finally') or
                                 line.strip().startswith('with ') or
                                 line.strip().startswith('#') or
                                 'super().__init__' in line or
                                 'setWindowTitle' in line or
                                 'setMinimumSize' in line):
            cleaned_lines.append(line)
            continue
            
        # Linhas com indentação 8 (corpo de métodos)
        if line_indent == 8 and not (line.strip().startswith('from ') or 
                                    line.strip().startswith('import ')):
            cleaned_lines.append(line)
            continue
            
        # Linhas com indentação 12 (blocos if/for dentro de métodos)
        if line_indent == 12 and not (line.strip().startswith('from ') or 
                                     line.strip().startswith('import ')):
            cleaned_lines.append(line)
            continue
            
        # Remover tudo o resto (imports órfãos com indentação incorreta)
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            print(f"Removendo import órfão linha {i+1}: {line.strip()}")
            continue
            
        # Se chegou aqui e tem indentação estranha, remover
        if line_indent > 12:
            print(f"Removendo linha malformada {i+1}: {line.strip()}")
            continue
            
        # Manter linha se passou todos os testes
        cleaned_lines.append(line)
    
    # Escrever ficheiro limpo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
        
    print(f"Limpeza agressiva concluída. Ficheiro {file_path} foi corrigido.")

if __name__ == "__main__":
    aggressive_fix_ficha_paciente()
