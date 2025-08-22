#!/usr/bin/env python3
"""
Script para remover TODOS os estilos personalizados de botões
e aplicar apenas o estilo universal Biodesk
"""

import os
import re
from pathlib import Path

def remove_button_styles_from_file(file_path):
    """Remove estilos personalizados de botões de um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Padrão para detectar setStyleSheet com QPushButton
        pattern = r'(\w+)\.setStyleSheet\s*\(\s*["\'"]{3}[^"\']*QPushButton[^"\']*["\'"]{3}\s*\)'
        
        # Substituir por aplicação do estilo universal
        def replace_style(match):
            button_name = match.group(1)
            return f"BiodeskUIKit.apply_universal_button_style({button_name})"
        
        content = re.sub(pattern, replace_style, content, flags=re.DOTALL)
        
        # Padrão para setStyleSheet com string simples
        pattern_simple = r'(\w+)\.setStyleSheet\s*\(\s*["\'][^"\']*QPushButton[^"\']*["\']\s*\)'
        content = re.sub(pattern_simple, replace_style, content)
        
        # Se houve mudanças, salvar
        if content != original_content:
            # Adicionar import do BiodeskUIKit se não existir
            if 'from biodesk_ui_kit import BiodeskUIKit' not in content and 'BiodeskUIKit' in content:
                # Encontrar onde adicionar o import
                import_lines = []
                other_lines = []
                for line in content.split('\n'):
                    if line.strip().startswith('from ') or line.strip().startswith('import '):
                        import_lines.append(line)
                    else:
                        other_lines.append(line)
                
                # Adicionar o import
                import_lines.append('from biodesk_ui_kit import BiodeskUIKit')
                content = '\n'.join(import_lines + other_lines)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Processado: {file_path.name}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {e}")
        return False

def main():
    """Processar todos os arquivos Python no diretório"""
    workspace_dir = Path(__file__).parent
    
    # Lista de arquivos Python para processar
    python_files = list(workspace_dir.glob('*.py'))
    python_files.extend(workspace_dir.glob('**/*.py'))
    
    # Excluir este script
    python_files = [f for f in python_files if f.name != 'remove_custom_button_styles.py']
    
    processed = 0
    for file_path in python_files:
        if remove_button_styles_from_file(file_path):
            processed += 1
    
    print(f"\n🎯 Processamento concluído: {processed} arquivos modificados")

if __name__ == "__main__":
    main()
