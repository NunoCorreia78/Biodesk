#!/usr/bin/env python3
"""
🔧 VERIFICAÇÃO PREVENTIVA DE ERROS DE SINTAXE
==============================================
Verifica todos os arquivos Python modificados para detectar erros antes de executar
"""

import ast
import os
import glob

def check_syntax(filepath):
    """Verifica sintaxe de um arquivo Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Tentar parsear o código
        ast.parse(source)
        return True, None
        
    except SyntaxError as e:
        return False, f"Linha {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Erro: {str(e)}"

def main():
    """Verificação principal"""
    base_dir = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    # Arquivos principais para verificar
    files_to_check = [
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
    
    print("🔍 VERIFICAÇÃO DE SINTAXE")
    print("=" * 50)
    
    errors_found = 0
    
    for file_pattern in files_to_check:
        filepath = os.path.join(base_dir, file_pattern)
        
        if os.path.exists(filepath):
            is_valid, error_msg = check_syntax(filepath)
            
            if is_valid:
                print(f"✅ {file_pattern}")
            else:
                print(f"❌ {file_pattern}: {error_msg}")
                errors_found += 1
        else:
            print(f"⚠️ {file_pattern}: Arquivo não encontrado")
    
    print("\n" + "=" * 50)
    if errors_found == 0:
        print("🎉 TODOS OS ARQUIVOS ESTÃO CORRETOS!")
    else:
        print(f"❌ {errors_found} ARQUIVOS COM ERROS ENCONTRADOS!")
    
    return errors_found == 0

if __name__ == "__main__":
    main()
