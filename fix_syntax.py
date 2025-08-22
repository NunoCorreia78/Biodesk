#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import re

def fix_syntax_errors():
    """Corrige erros de sintaxe no ficha_paciente.py"""
    file_path = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tentar compilar e encontrar erros
    try:
        compile(content, file_path, 'exec')
        print("✅ Ficheiro já está sintaticamente correto!")
        return
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe na linha {e.lineno}: {e.msg}")
        lines = content.split('\n')
        
        if e.lineno and e.lineno <= len(lines):
            problem_line = lines[e.lineno - 1]
            print(f"Linha problemática: {problem_line}")
            
            # Corrigir problema específico
            if "expected an indented block" in e.msg:
                # Adicionar pass onde falta
                if e.lineno < len(lines):
                    next_line_indent = len(lines[e.lineno]) - len(lines[e.lineno].lstrip())
                    if next_line_indent > 0:
                        lines.insert(e.lineno - 1, " " * (next_line_indent) + "pass")
                        print(f"Adicionado 'pass' na linha {e.lineno}")
            
            # Escrever conteúdo corrigido
            fixed_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("Tentando corrigir...")
            # Tentar novamente
            fix_syntax_errors()

if __name__ == "__main__":
    fix_syntax_errors()
