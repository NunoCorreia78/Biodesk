#!/usr/bin/env python3
"""
Script para verificar dados do paciente e pastas de documentos
"""

import sqlite3
from pathlib import Path

def verificar_paciente_63():
    """Verificar dados do paciente 63"""
    db_path = Path('pacientes.db')
    if not db_path.exists():
        print('❌ Base de dados não encontrada')
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Buscar paciente com ID 63
        cursor.execute('SELECT id, nome FROM pacientes WHERE id = 63')
        result = cursor.fetchone()
        
        if result:
            id_pac, nome_pac = result
            print(f'🔍 Paciente ID {id_pac}: "{nome_pac}"')
            
            # Simular criação da pasta como no código
            nome_limpo = nome_pac.replace(' ', '_')
            pasta_esperada = f'Documentos_Pacientes/{id_pac}_{nome_limpo}'
            print(f'📁 Pasta que seria criada: {pasta_esperada}')
            
            # Verificar se existe
            if Path(pasta_esperada).exists():
                print(f'✅ Pasta existe')
                # Verificar subpasta declaracoes_saude
                decl_pasta = Path(pasta_esperada) / 'declaracoes_saude'
                if decl_pasta.exists():
                    pdfs = list(decl_pasta.glob('*.pdf'))
                    print(f'   📄 {len(pdfs)} PDFs em declaracoes_saude/')
                    for pdf in pdfs[-2:]:  # últimos 2
                        print(f'      - {pdf.name}')
            else:
                print(f'❌ Pasta NÃO existe')
                print(f'   Verificando pastas similares...')
                base = Path('Documentos_Pacientes')
                similar = list(base.glob(f'{id_pac}*'))
                for pasta in similar:
                    print(f'   📂 Encontrada: {pasta.name}')
        else:
            print('❌ Paciente ID 63 não encontrado na base de dados')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Erro ao verificar base de dados: {e}')

def analisar_todas_pastas_63():
    """Analisar todas as pastas relacionadas ao paciente 63"""
    print('\n📊 Análise de todas as pastas do paciente 63:')
    base = Path('Documentos_Pacientes')
    if not base.exists():
        print('❌ Pasta Documentos_Pacientes não existe')
        return
    
    pastas_63 = sorted(base.glob('63*'))
    for pasta in pastas_63:
        arquivos = [f for f in pasta.rglob('*') if f.is_file() and not f.name.endswith('.meta')]
        print(f'📂 {pasta.name}: {len(arquivos)} documentos total')
        
        # Verificar subpasta declaracoes_saude
        decl_folder = pasta / 'declaracoes_saude'
        if decl_folder.exists():
            decl_pdfs = list(decl_folder.glob('*.pdf'))
            print(f'   ├── declaracoes_saude/: {len(decl_pdfs)} PDFs')
            # Mostrar os mais recentes
            if decl_pdfs:
                recent = sorted(decl_pdfs, key=lambda x: x.stat().st_mtime, reverse=True)[:2]
                for pdf in recent:
                    print(f'   │   └── {pdf.name}')
        
        # Verificar outras subpastas
        subpastas = [d for d in pasta.iterdir() if d.is_dir()]
        for sub in subpastas:
            if sub.name != 'declaracoes_saude':
                sub_files = list(sub.glob('*.pdf'))
                if sub_files:
                    print(f'   ├── {sub.name}/: {len(sub_files)} PDFs')

if __name__ == '__main__':
    print("🔍 Investigando problema das declarações de saúde...\n")
    verificar_paciente_63()
    analisar_todas_pastas_63()
