#!/usr/bin/env python3
"""
🎯 CONVERSÃO PARA ESTILO PADRÃO PyQt6
===================================== 
Remove TODOS os estilos customizados e usa apenas QMessageBox padrão
"""

import re
import os

def convert_to_standard(filepath):
    """Converte todos os diálogos para QMessageBox padrão"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. REMOVER TODOS OS IMPORTS CUSTOMIZADOS
        content = re.sub(r'from biodesk_dialogs import.*\n', '', content)
        content = re.sub(r'from biodesk_styled_dialogs import.*\n', '', content)
        content = re.sub(r'import biodesk_dialogs.*\n', '', content)
        content = re.sub(r'import biodesk_styled_dialogs.*\n', '', content)
        
        # 2. ADICIONAR IMPORT QMessageBox se necessário
        if ('QMessageBox' not in content and 
            ('mostrar_' in content or 'BiodeskMessageBox' in content)):
            # Encontrar import PyQt6 para adicionar QMessageBox
            pyqt_match = re.search(r'from PyQt6\.QtWidgets import ([^\n]+)', content)
            if pyqt_match:
                current_imports = pyqt_match.group(1)
                if 'QMessageBox' not in current_imports:
                    new_imports = current_imports.rstrip() + ', QMessageBox'
                    content = content.replace(pyqt_match.group(0), f'from PyQt6.QtWidgets import {new_imports}')
            else:
                # Adicionar import se não existe
                content = 'from PyQt6.QtWidgets import QMessageBox\n' + content
        
        # 3. CONVERTER TODAS AS CHAMADAS PARA QMessageBox PADRÃO
        
        # BiodeskMessageBox.* -> QMessageBox.*
        content = re.sub(r'BiodeskMessageBox\.information\s*\(', 'QMessageBox.information(', content)
        content = re.sub(r'BiodeskMessageBox\.warning\s*\(', 'QMessageBox.warning(', content)
        content = re.sub(r'BiodeskMessageBox\.critical\s*\(', 'QMessageBox.critical(', content)
        content = re.sub(r'BiodeskMessageBox\.question\s*\(', 'QMessageBox.question(', content)
        
        # mostrar_* -> QMessageBox.*
        content = re.sub(r'mostrar_informacao\s*\(', 'QMessageBox.information(', content)
        content = re.sub(r'mostrar_sucesso\s*\(', 'QMessageBox.information(', content)
        content = re.sub(r'mostrar_aviso\s*\(', 'QMessageBox.warning(', content)
        content = re.sub(r'mostrar_erro\s*\(', 'QMessageBox.critical(', content)
        content = re.sub(r'mostrar_confirmacao\s*\(', 'QMessageBox.question(', content)
        
        # Remover imports locais dentro de funções
        content = re.sub(r'\s+from biodesk_[^\\n]+ import [^\\n]+\\n', '\\n', content)
        
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
    
    # Arquivos principais para corrigir
    files_to_fix = [
        "main_window.py",
        "ficha_paciente.py",
        "ficha_paciente/centro_comunicacao_unificado.py",
        "ficha_paciente/dados_pessoais.py", 
        "ficha_paciente/gestao_documentos.py",
        "ficha_paciente/historico_clinico.py",
        "ficha_paciente/iris_integration.py",
        "ficha_paciente/pesquisa_pacientes.py",
        "ficha_paciente/declaracao_saude.py"
    ]
    
    print("🎯 CONVERTENDO PARA ESTILO PADRÃO PyQt6")
    print("=" * 50)
    
    fixed_count = 0
    
    for filename in files_to_fix:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if convert_to_standard(filepath):
                print(f"✅ {filename}")
                fixed_count += 1
            else:
                print(f"⚪ {filename} (já padrão)")
        else:
            print(f"⚠️ {filename} (não encontrado)")
    
    print(f"\n🎉 {fixed_count} arquivos convertidos!")
    print("📦 TODOS OS DIÁLOGOS AGORA SÃO PADRÃO PyQt6!")

if __name__ == "__main__":
    main()
