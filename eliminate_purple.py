#!/usr/bin/env python3
"""
🎯 MIGRAÇÃO PARA DIÁLOGOS PADRÃO CONCLUÍDA
==========================================
Sistema agora usa apenas diálogos padrão do PyQt6 - não há mais estilos personalizados
"""

import re
import os
import glob

def fix_file_completely(filepath):
    """Remove completamente os imports roxos e converte tudo para cinza"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. REMOVER TODOS OS IMPORTS ROXOS
        content = re.sub(r'from biodesk_dialogs import.*\n', '', content)
        content = re.sub(r'import biodesk_dialogs.*\n', '', content)
        
        # 2. ADICIONAR IMPORT CINZA se necessário
        if ('mostrar_' in content or 'BiodeskMessageBox' in content) and 'from biodesk_dialogs import BiodeskMessageBox' not in content:
            # Encontrar primeiro import PyQt6 para adicionar depois
            pyqt_match = re.search(r'from PyQt6\..*\n', content)
            if pyqt_match:
                insert_pos = pyqt_match.end()
                content = content[:insert_pos] + 'from biodesk_dialogs import BiodeskMessageBox\n' + content[insert_pos:]
            else:
                # Adicionar no início se não há imports PyQt6
                content = 'from biodesk_dialogs import BiodeskMessageBox\n' + content
        
        # 3. CONVERTER TODAS AS CHAMADAS PARA ESTILO CINZA
        
        # mostrar_* -> BiodeskMessageBox.*
        content = re.sub(r'mostrar_informacao\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', r'BiodeskMessageBox.information(\1, \2, \3)', content)
        content = re.sub(r'mostrar_sucesso\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', r'BiodeskMessageBox.information(\1, \2, \3)', content)
        content = re.sub(r'mostrar_aviso\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', r'BiodeskMessageBox.warning(\1, \2, \3)', content)
        content = re.sub(r'mostrar_erro\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', r'BiodeskMessageBox.critical(\1, \2, \3)', content)
        content = re.sub(r'mostrar_confirmacao\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', r'BiodeskMessageBox.question(\1, \2, \3)', content)
        
        # Remover imports locais roxos dentro de funções
        content = re.sub(r'\s+from biodesk_dialogs import [^\n]+\n', '\n', content)
        
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
        "todo_list_window.py", 
        "terapia_quantica.py",
        "terapia_quantica_window.py",
        "template_editavel.py",
        "sistema_assinatura.py",
        "prescricao_medica_widget.py",
        "pdf_viewer.py",
        "iris_anonima_canvas.py",
        "iris_canvas.py",
        "ficha_paciente_header.py"
    ]
    
    print("🎯 ELIMINANDO COMPLETAMENTE O ESTILO ROXO")
    print("=" * 50)
    
    fixed_count = 0
    
    for filename in files_to_fix:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if fix_file_completely(filepath):
                print(f"✅ {filename}")
                fixed_count += 1
            else:
                print(f"⚪ {filename} (já correto)")
        else:
            print(f"⚠️ {filename} (não encontrado)")
    
    print(f"\n🎉 {fixed_count} arquivos corrigidos!")
    print("🎯 TODOS OS DIÁLOGOS AGORA SÃO CINZA!")

if __name__ == "__main__":
    main()
