#!/usr/bin/env python3
"""
Script para corrigir todas as importações do biodesk_ui_kit e outros módulos da raiz
"""

import os
import sys
import re

def fix_file_imports(file_path):
    """
    Adiciona configuração de sys.path no início do arquivo se houver importações dos módulos da raiz
    """
    
    # Módulos da raiz que precisam do path configurado
    root_modules = [
        'biodesk_ui_kit',
        'biodesk_styles', 
        'biodesk_dialogs',
        'biodesk_styled_dialogs',
        'modern_date_widget',
        'data_cache'
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verificar se já tem configuração de sys.path
        if 'sys.path.insert' in content or 'sys.path.append' in content:
            print(f"🔄 {file_path} - já tem configuração de path")
            return False
            
        # Verificar se importa algum módulo da raiz
        needs_fix = False
        for module in root_modules:
            if f'from {module}' in content or f'import {module}' in content:
                needs_fix = True
                break
                
        if not needs_fix:
            print(f"⏭️ {file_path} - não precisa de correção")
            return False
            
        # Encontrar a primeira linha de import
        lines = content.split('\n')
        import_line_index = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or stripped.startswith('from ')) and not stripped.startswith('#'):
                import_line_index = i
                break
                
        if import_line_index == -1:
            print(f"⚠️ {file_path} - não encontrou linhas de import")
            return False
            
        # Inserir configuração do path antes dos imports
        path_config = [
            "# Configurar path para importações da raiz",
            "import sys",
            "import os",
            "if os.path.dirname(os.path.dirname(__file__)) not in sys.path:",
            "    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))",
            ""
        ]
        
        # Verificar se já tem import sys/os
        has_sys = any('import sys' in line for line in lines[:import_line_index])
        has_os = any('import os' in line for line in lines[:import_line_index])
        
        if has_sys:
            path_config.remove("import sys")
        if has_os:
            path_config.remove("import os")
            
        # Inserir as linhas
        for j, config_line in enumerate(path_config):
            lines.insert(import_line_index + j, config_line)
            
        # Reescrever o arquivo
        new_content = '\n'.join(lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ {file_path} - corrigido")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {e}")
        return False

def main():
    """Processar todos os arquivos Python que precisam de correção"""
    
    base_dir = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Arquivos específicos que sabemos que precisam de correção
    files_to_fix = [
        "ficha_paciente/dados_pessoais.py",
        "ficha_paciente/historico_clinico.py", 
        "ficha_paciente/templates_manager.py",
        "ficha_paciente/comunicacao_manager.py",
        "ficha_paciente/gestao_documentos.py",
        "ficha_paciente/iris_integration.py",
        "prescricao_medica_widget.py",
        "ficha_paciente/declaracao_saude.py",
        "ficha_paciente/core/button_manager.py",
        "ficha_paciente/centro_comunicacao_unificado.py"
    ]
    
    print("🔧 Iniciando correção das importações...\n")
    
    fixed_count = 0
    for file_rel_path in files_to_fix:
        file_path = os.path.join(base_dir, file_rel_path)
        if os.path.exists(file_path):
            if fix_file_imports(file_path):
                fixed_count += 1
        else:
            print(f"⚠️ Arquivo não encontrado: {file_path}")
    
    print(f"\n🎉 Correção concluída! {fixed_count} arquivos corrigidos.")

if __name__ == "__main__":
    main()
