#!/usr/bin/env python3
"""
Script para corrigir aspas inválidas em estilos CSS dentro de strings Python
"""

import os
import re

def fix_css_quotes(file_path):
    """Corrige aspas inválidas em estilos CSS"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Padrões para corrigir aspas em valores CSS dentro de strings Python
        patterns = [
            # Cores hex com aspas simples
            (r":\s*'(#[0-9a-fA-F]{3,6})';", r": \1;"),
            # Font families com aspas simples 
            (r"font-family:\s*'([^']*?)';", r"font-family: \1;"),
            # Outros valores CSS com aspas simples inválidas
            (r"border:\s*([^']*?)\s*'(#[0-9a-fA-F]{3,6})';", r"border: \1 \2;"),
            (r"border-color:\s*'(#[0-9a-fA-F]{3,6})';", r"border-color: \1;"),
            (r"background-color:\s*'(#[0-9a-fA-F]{3,6})';", r"background-color: \1;"),
            (r"color:\s*'(#[0-9a-fA-F]{3,6})';", r"color: \1;"),
        ]
        
        changes_made = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
                
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path} - corrigido")
            return True
        else:
            print(f"⏭️ {file_path} - não precisava de correção")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {e}")
        return False

def main():
    """Processar todos os arquivos Python para corrigir CSS"""
    
    base_dir = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    print("🎨 Iniciando correção de CSS...\n")
    
    fixed_count = 0
    
    # Processar todos os arquivos .py recursivamente
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_css_quotes(file_path):
                    fixed_count += 1
    
    print(f"\n🎉 Correção concluída! {fixed_count} arquivos corrigidos.")

if __name__ == "__main__":
    main()
