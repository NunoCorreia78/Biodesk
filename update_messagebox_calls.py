#!/usr/bin/env python3
"""
Atualização simples: importar BiodeskMessageBox ao invés de QMessageBox direto
"""

import os
import re

def update_imports_and_calls(content):
    """Atualiza imports e chamadas para usar BiodeskMessageBox"""
    
    # Verificar se já tem o import correto
    if 'from biodesk_dialogs import BiodeskMessageBox' not in content:
        # Adicionar import após outros imports do PyQt6
        pyqt_import_pattern = r'(from PyQt6\.QtWidgets import[^\n]*)'
        if re.search(pyqt_import_pattern, content):
            content = re.sub(
                pyqt_import_pattern,
                r'\1\nfrom biodesk_dialogs import BiodeskMessageBox',
                content,
                count=1
            )
        else:
            # Se não encontrar imports do PyQt6, adicionar no início
            content = 'from biodesk_dialogs import BiodeskMessageBox\n' + content
    
    # Substituir chamadas QMessageBox por BiodeskMessageBox
    content = re.sub(r'QMessageBox\.information\s*\(', 'BiodeskMessageBox.information(', content)
    content = re.sub(r'QMessageBox\.warning\s*\(', 'BiodeskMessageBox.warning(', content)
    content = re.sub(r'QMessageBox\.critical\s*\(', 'BiodeskMessageBox.critical(', content)
    content = re.sub(r'QMessageBox\.question\s*\(', 'BiodeskMessageBox.question(', content)
    
    return content

def process_file(filepath):
    """Processa um arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'QMessageBox.' not in content:
            return False
        
        original_content = content
        content = update_imports_and_calls(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Atualizado: {os.path.basename(filepath)}")
            return True
        else:
            return False
    
    except Exception as e:
        print(f"❌ Erro em {filepath}: {e}")
        return False

# Lista de arquivos para processar
files_to_process = [
    'ficha_paciente.py',
    'emails_agendados_manager.py',
    'ficha_paciente/declaracao_saude.py',
    'ficha_paciente/iris_historico_widget.py',
    'ficha_paciente/centro_comunicacao_unificado.py'
]

print("🔄 Atualizando chamadas QMessageBox para BiodeskMessageBox...")

for file_path in files_to_process:
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        process_file(full_path)
    else:
        print(f"⚠️  Arquivo não encontrado: {file_path}")

print("✅ Atualização concluída!")
