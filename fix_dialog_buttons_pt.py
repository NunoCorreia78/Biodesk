#!/usr/bin/env python3
"""
Script para converter todos os QMessageBox diretos para usar botões em português
"""

import os
import re

def fix_qmessagebox_calls(content):
    """
    Substitui chamadas diretas QMessageBox por versões com botões em português
    """
    
    # Substituir QMessageBox.information
    pattern = r'QMessageBox\.information\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)'
    def replace_information(match):
        parent, title, message = match.groups()
        return f'''msg = QMessageBox({parent.strip()})
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle({title.strip()})
        msg.setText({message.strip()})
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        msg.exec()'''
    
    content = re.sub(pattern, replace_information, content)
    
    # Substituir QMessageBox.warning
    pattern = r'QMessageBox\.warning\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)'
    def replace_warning(match):
        parent, title, message = match.groups()
        return f'''msg = QMessageBox({parent.strip()})
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle({title.strip()})
        msg.setText({message.strip()})
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        msg.exec()'''
    
    content = re.sub(pattern, replace_warning, content)
    
    # Substituir QMessageBox.critical
    pattern = r'QMessageBox\.critical\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)'
    def replace_critical(match):
        parent, title, message = match.groups()
        return f'''msg = QMessageBox({parent.strip()})
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle({title.strip()})
        msg.setText({message.strip()})
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        msg.exec()'''
    
    content = re.sub(pattern, replace_critical, content)
    
    # Substituir QMessageBox.question
    pattern = r'QMessageBox\.question\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)'
    def replace_question(match):
        parent, title, message = match.groups()
        return f'''msg = QMessageBox({parent.strip()})
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle({title.strip()})
        msg.setText({message.strip()})
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("Sim")
        msg.button(QMessageBox.StandardButton.No).setText("Não")
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.exec()'''
    
    content = re.sub(pattern, replace_question, content)
    
    return content

def process_file(filepath):
    """Processa um arquivo Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se o arquivo contém QMessageBox
        if 'QMessageBox.' not in content:
            return False
        
        original_content = content
        content = fix_qmessagebox_calls(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Atualizado: {filepath}")
            return True
        else:
            print(f"⚪ Sem alterações: {filepath}")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao processar {filepath}: {e}")
        return False

def main():
    """Função principal"""
    current_dir = os.getcwd()
    files_processed = 0
    files_changed = 0
    
    print("🔄 Iniciando conversão de QMessageBox para português...")
    
    # Processar todos os arquivos .py
    for root, dirs, files in os.walk(current_dir):
        # Ignorar __pycache__ e .venv
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.venv', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                files_processed += 1
                
                if process_file(filepath):
                    files_changed += 1
    
    print(f"\n📊 Resumo:")
    print(f"   • Arquivos processados: {files_processed}")
    print(f"   • Arquivos alterados: {files_changed}")
    print(f"✅ Conversão concluída!")

if __name__ == "__main__":
    main()
