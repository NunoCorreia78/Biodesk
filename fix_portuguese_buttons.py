#!/usr/bin/env python3
"""
🇵🇹 CONVERSÃO PARA BOTÕES EM PORTUGUÊS
======================================
Converte todas as chamadas diretas QMessageBox.* para BiodeskMessageBox.* (com botões PT)
"""

import re
import os

def fix_portuguese_buttons(filepath):
    """Converte QMessageBox direto para BiodeskMessageBox (botões PT)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Adicionar import se necessário
        if 'QMessageBox.' in content and 'from biodesk_styled_dialogs import BiodeskMessageBox' not in content:
            # Encontrar primeiro import PyQt6 para adicionar depois
            pyqt_match = re.search(r'from PyQt6\..*\n', content)
            if pyqt_match:
                insert_pos = pyqt_match.end()
                content = content[:insert_pos] + 'from biodesk_styled_dialogs import BiodeskMessageBox\n' + content[insert_pos:]
        
        # Converter todas as chamadas diretas QMessageBox.* para BiodeskMessageBox.*
        content = re.sub(r'QMessageBox\.information\s*\(', 'BiodeskMessageBox.information(', content)
        content = re.sub(r'QMessageBox\.warning\s*\(', 'BiodeskMessageBox.warning(', content)
        content = re.sub(r'QMessageBox\.critical\s*\(', 'BiodeskMessageBox.critical(', content)
        content = re.sub(r'QMessageBox\.question\s*\(', 'BiodeskMessageBox.question(', content)
        
        # Salvar se houve mudanças
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"❌ Erro em {filepath}: {e}")
        return False

def main():
    """Execução principal"""
    base_dir = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Arquivos para corrigir
    files_to_fix = [
        "ficha_paciente.py",
        "ficha_paciente/centro_comunicacao_unificado.py",
        "ficha_paciente/dados_pessoais.py",
        "ficha_paciente/gestao_documentos.py",
        "ficha_paciente/historico_clinico.py",
        "ficha_paciente/iris_integration.py",
        "ficha_paciente/pesquisa_pacientes.py",
        "ficha_paciente/declaracao_saude.py"
    ]
    
    print("🇵🇹 CONVERTENDO BOTÕES PARA PORTUGUÊS")
    print("=" * 50)
    
    fixed_count = 0
    
    for filename in files_to_fix:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if fix_portuguese_buttons(filepath):
                print(f"✅ {filename}")
                fixed_count += 1
            else:
                print(f"⚪ {filename} (já correto)")
        else:
            print(f"⚠️ {filename} (não encontrado)")
    
    print(f"\n🎉 {fixed_count} arquivos corrigidos!")
    print("🇵🇹 TODOS OS BOTÕES AGORA EM PORTUGUÊS!")

if __name__ == "__main__":
    main()
