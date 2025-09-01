#!/usr/bin/env python3
"""
🔧 SCRIPT PARA PADRONIZAR TODOS OS DIÁLOGOS - VERSÃO SIMPLES
=============================================================
Converte TODOS os diálogos para QMessageBox padrão do PyQt6
"""

import os
import re
import glob

def fix_dialogs_in_file(filepath):
    """Padroniza todos os diálogos de um arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Remover imports customizados
        content = re.sub(r'        content = re.sub(r'        content = re.sub(r'        
        # 2. Adicionar import padrão se não existir
        if 'from PyQt6.QtWidgets import' in content and 'QMessageBox' not in content:
            content = content.replace(
                'from PyQt6.QtWidgets import',
                'from PyQt6.QtWidgets import QMessageBox,'
            )
        elif 'QMessageBox' not in content:
            # Adicionar no início
            content = 'from PyQt6.QtWidgets import QMessageBox\n' + content
        
        # 3. Converter todas as chamadas para QMessageBox padrão
        
        # Confirmações -> QMessageBox.question
        patterns_confirmation = [
            r'mostrar_confirmacao\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox\.question\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)(?:,\s*[^)]+)?\)',
        ]
        for pattern in patterns_confirmation:
            content = re.sub(pattern, r'QMessageBox.question(\1, \2, \3)', content)
        
        # Informações -> QMessageBox.information
        patterns_info = [
            r'mostrar_sucesso\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'mostrar_informacao\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox\.information\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)(?:,\s*[^)]+)?\)',
        ]
        for pattern in patterns_info:
            content = re.sub(pattern, r'QMessageBox.information(\1, \2, \3)', content)
        
        # Avisos -> QMessageBox.warning
        patterns_warning = [
            r'mostrar_aviso\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox\.warning\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)(?:,\s*[^)]+)?\)',
        ]
        for pattern in patterns_warning:
            content = re.sub(pattern, r'QMessageBox.warning(\1, \2, \3)', content)
        
        # Erros -> QMessageBox.critical
        patterns_error = [
            r'mostrar_erro\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox\.critical\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)(?:,\s*[^)]+)?\)',
        ]
        for pattern in patterns_error:
            content = re.sub(pattern, r'QMessageBox.critical(\1, \2, \3)', content)
        
        # Salvar se houve mudanças
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filepath}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Erro em {filepath}: {e}")
        return False

def main():
    """Execução principal"""
    base_dir = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Arquivos principais para corrigir
    target_files = [
        "main_window.py",
        "ficha_paciente.py",
        "ficha_paciente/*.py",
        "*.py"
    ]
    
    files_fixed = 0
    
    for pattern in target_files:
        full_pattern = os.path.join(base_dir, pattern)
        for filepath in glob.glob(full_pattern):
            if filepath.endswith('.py') and '__pycache__' not in filepath:
                if fix_dialogs_in_file(filepath):
                    files_fixed += 1
    
    print(f"\n🎉 Concluído! {files_fixed} arquivos corrigidos")

if __name__ == "__main__":
    main()
