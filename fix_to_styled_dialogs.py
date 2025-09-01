#!/usr/bin/env python3
"""
🎯 PADRONIZAÇÃO PARA O ESTILO CORRETO
====================================
Converte TODOS os diálogos para biodesk_styled_dialogs.BiodeskMessageBox
(estilo da imagem - cinza, clean, sem roxo)
"""

import os
import re

def fix_dialogs_to_styled(filepath):
    """Converte todos os diálogos para o estilo correto"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Garantir import correto
        if 'from biodesk_styled_dialogs import BiodeskMessageBox' not in content:
            # Remover imports antigos
            content = re.sub(r'from biodesk_dialogs import.*\n', '', content)
            
            # Adicionar import correto
            if 'from PyQt6.QtWidgets import' in content:
                content = content.replace(
                    'from PyQt6.QtWidgets import',
                    'from biodesk_styled_dialogs import BiodeskMessageBox\nfrom PyQt6.QtWidgets import'
                )
            else:
                content = 'from biodesk_styled_dialogs import BiodeskMessageBox\n' + content
        
        # 2. Converter chamadas para estilo correto
        
        # Confirmações
        content = re.sub(
            r'mostrar_confirmacao\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox.question(\1, \2, \3)',
            content
        )
        
        # Informações/Sucesso
        patterns_info = [
            r'mostrar_sucesso\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'mostrar_informacao\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
        ]
        for pattern in patterns_info:
            content = re.sub(pattern, r'BiodeskMessageBox.information(\1, \2, \3)', content)
        
        # Avisos
        content = re.sub(
            r'mostrar_aviso\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox.warning(\1, \2, \3)',
            content
        )
        
        # Erros
        content = re.sub(
            r'mostrar_erro\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'BiodeskMessageBox.critical(\1, \2, \3)',
            content
        )
        
        # QMessageBox → BiodeskMessageBox
        content = re.sub(r'QMessageBox\.question\s*\(', 'BiodeskMessageBox.question(', content)
        content = re.sub(r'QMessageBox\.information\s*\(', 'BiodeskMessageBox.information(', content)
        content = re.sub(r'QMessageBox\.warning\s*\(', 'BiodeskMessageBox.warning(', content)
        content = re.sub(r'QMessageBox\.critical\s*\(', 'BiodeskMessageBox.critical(', content)
        
        # Salvar se houve mudanças
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {os.path.basename(filepath)}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Erro em {filepath}: {e}")
        return False

def main():
    """Execução principal"""
    base_dir = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Arquivos principais
    target_files = [
        "main_window.py",
        "ficha_paciente.py",
        "ficha_paciente/dados_pessoais.py",
        "ficha_paciente/historico_clinico.py",
        "ficha_paciente/gestao_documentos.py",
        "ficha_paciente/centro_comunicacao_unificado.py",
        "ficha_paciente/iris_integration.py",
    ]
    
    files_fixed = 0
    
    for filename in target_files:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if fix_dialogs_to_styled(filepath):
                files_fixed += 1
    
    print(f"\n🎉 {files_fixed} arquivos convertidos para o estilo correto!")

if __name__ == "__main__":
    main()
