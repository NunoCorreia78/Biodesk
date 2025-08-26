#!/usr/bin/env python3
"""
🔍 ANÁLISE SEGURA DO PROJETO BIODESK
====================================

Analisa o projeto sem modificar NADA.
Apenas reporta o que poderia ser otimizado.
"""

import os
from pathlib import Path
from datetime import datetime

class BiodeskAnalyzer:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.analysis = {
            'arquivos_vazios': [],
            'cache_python': [],
            'backups_obsoletos': [],
            'codigo_teste': [],
            'imports_desnecessarios': [],
            'duplicacoes': []
        }
    
    def analyze_empty_files(self):
        """Analisa arquivos vazios ou de teste"""
        print("🔍 Analisando arquivos vazios...")
        
        test_files = [
            "teste_botoes_main.py",
            "teste_ficha_completo.py", 
            "teste_ficha_corrigida.py",
            "teste_ficha_refatorada.py",
            "teste_integracao.py",
            "teste_performance_ficha.py",
            "teste_simples_ficha.py"
        ]
        
        for test_file in test_files:
            file_path = self.workspace_root / test_file
            if file_path.exists():
                size = file_path.stat().st_size
                self.analysis['arquivos_vazios'].append({
                    'arquivo': test_file,
                    'tamanho': size,
                    'status': 'vazio' if size == 0 else 'com_conteudo'
                })
    
    def analyze_cache(self):
        """Analisa cache Python"""
        print("🔍 Analisando cache Python...")
        
        for pycache_dir in self.workspace_root.rglob("__pycache__"):
            if pycache_dir.is_dir():
                size = sum(f.stat().st_size for f in pycache_dir.rglob("*") if f.is_file())
                files_count = len(list(pycache_dir.rglob("*.pyc")))
                self.analysis['cache_python'].append({
                    'diretorio': str(pycache_dir.relative_to(self.workspace_root)),
                    'tamanho': size,
                    'arquivos': files_count
                })
    
    def analyze_backups(self):
        """Analisa arquivos de backup"""
        print("🔍 Analisando backups...")
        
        backup_patterns = ["*.backup", "*.bak", "*.orig"]
        
        for pattern in backup_patterns:
            for backup_file in self.workspace_root.rglob(pattern):
                if backup_file.is_file():
                    size = backup_file.stat().st_size
                    self.analysis['backups_obsoletos'].append({
                        'arquivo': str(backup_file.relative_to(self.workspace_root)),
                        'tamanho': size,
                        'modificado': datetime.fromtimestamp(backup_file.stat().st_mtime)
                    })
    
    def analyze_test_code(self):
        """Analisa código de teste em produção"""
        print("🔍 Analisando código de teste...")
        
        test_keywords = ['teste', 'test', 'exemplo', 'demo']
        
        for py_file in self.workspace_root.rglob("*.py"):
            if py_file.is_file() and not str(py_file).startswith(str(self.workspace_root / "teste")):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    test_lines = []
                    for i, line in enumerate(content.split('\n'), 1):
                        if any(keyword in line.lower() for keyword in test_keywords):
                            if ('def ' in line or 'class ' in line or 'btn_' in line):
                                test_lines.append(f"Linha {i}: {line.strip()}")
                    
                    if test_lines:
                        self.analysis['codigo_teste'].append({
                            'arquivo': str(py_file.relative_to(self.workspace_root)),
                            'linhas_teste': test_lines[:5]  # Limita a 5 exemplos
                        })
                        
                except Exception:
                    pass  # Ignora arquivos que não conseguir ler
    
    def analyze_duplications(self):
        """Analisa possíveis duplicações"""
        print("🔍 Analisando duplicações...")
        
        # Verifica se existem arquivos similares
        similar_files = [
            ("ficha_paciente.py", "ficha_paciente_header.py"),
            ("biodesk_dialogs.py", "biodesk_styled_dialogs.py"),
        ]
        
        for file1, file2 in similar_files:
            path1 = self.workspace_root / file1
            path2 = self.workspace_root / file2
            
            if path1.exists() and path2.exists():
                self.analysis['duplicacoes'].append({
                    'arquivos': f"{file1} ↔ {file2}",
                    'status': 'Possível duplicação de funcionalidade'
                })
    
    def generate_analysis_report(self):
        """Gera relatório de análise"""
        print("\n" + "="*60)
        print("🔍 RELATÓRIO DE ANÁLISE BIODESK")
        print("="*60)
        
        # Arquivos vazios
        total_empty = len([f for f in self.analysis['arquivos_vazios'] if f['status'] == 'vazio'])
        total_empty_size = sum(f['tamanho'] for f in self.analysis['arquivos_vazios'] if f['status'] == 'vazio')
        print(f"📁 Arquivos de teste vazios: {total_empty}")
        
        # Cache
        total_cache_size = sum(c['tamanho'] for c in self.analysis['cache_python'])
        total_cache_files = sum(c['arquivos'] for c in self.analysis['cache_python'])
        print(f"🗂️ Cache Python: {len(self.analysis['cache_python'])} diretórios, {total_cache_files} arquivos, {total_cache_size:,} bytes")
        
        # Backups
        total_backup_size = sum(b['tamanho'] for b in self.analysis['backups_obsoletos'])
        print(f"💾 Backups obsoletos: {len(self.analysis['backups_obsoletos'])}, {total_backup_size:,} bytes")
        
        # Código de teste
        print(f"🧪 Arquivos com código de teste: {len(self.analysis['codigo_teste'])}")
        
        # Duplicações
        print(f"🔄 Possíveis duplicações: {len(self.analysis['duplicacoes'])}")
        
        print("="*60)
        
        # Salva relatório detalhado
        report_file = self.workspace_root / f"ANALISE_PROJETO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 🔍 ANÁLISE COMPLETA DO PROJETO BIODESK

## 📊 Resumo Executivo
- **Data**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- **Arquivos vazios**: {total_empty}
- **Cache Python**: {total_cache_files} arquivos ({total_cache_size:,} bytes)
- **Backups obsoletos**: {len(self.analysis['backups_obsoletos'])} ({total_backup_size:,} bytes)
- **Arquivos com código teste**: {len(self.analysis['codigo_teste'])}
- **Possíveis duplicações**: {len(self.analysis['duplicacoes'])}

## 📁 ARQUIVOS VAZIOS DETECTADOS
""")
            
            for file_info in self.analysis['arquivos_vazios']:
                status_icon = "🗑️" if file_info['status'] == 'vazio' else "📄"
                f.write(f"- {status_icon} `{file_info['arquivo']}` ({file_info['tamanho']} bytes)\n")
            
            f.write(f"\n## 🗂️ CACHE PYTHON\n")
            for cache_info in self.analysis['cache_python']:
                f.write(f"- 📂 `{cache_info['diretorio']}` - {cache_info['arquivos']} arquivos ({cache_info['tamanho']:,} bytes)\n")
            
            f.write(f"\n## 💾 ARQUIVOS DE BACKUP\n")
            for backup_info in self.analysis['backups_obsoletos']:
                f.write(f"- 🗃️ `{backup_info['arquivo']}` ({backup_info['tamanho']:,} bytes) - {backup_info['modificado'].strftime('%d/%m/%Y')}\n")
            
            f.write(f"\n## 🧪 CÓDIGO DE TESTE EM PRODUÇÃO\n")
            for test_info in self.analysis['codigo_teste']:
                f.write(f"- 🔬 `{test_info['arquivo']}`:\n")
                for linha in test_info['linhas_teste']:
                    f.write(f"  - {linha}\n")
            
            f.write(f"\n## 🔄 POSSÍVEIS DUPLICAÇÕES\n")
            for dup_info in self.analysis['duplicacoes']:
                f.write(f"- ⚠️ {dup_info['arquivos']}: {dup_info['status']}\n")
            
            f.write(f"""
## 🛡️ SEGURANÇA
- **Nenhum arquivo foi modificado**
- **Análise apenas de leitura**
- **Todos os dados estão seguros**

## 💡 RECOMENDAÇÕES
1. **SEMPRE SEGURO**: Remover cache Python (__pycache__)
2. **SEMPRE SEGURO**: Remover arquivos de teste vazios (0 bytes)
3. **SEMPRE SEGURO**: Remover backups .backup/.bak
4. **REVISAR**: Código de teste em arquivos de produção
5. **ANALISAR**: Possíveis duplicações antes de modificar

## 🚀 PRÓXIMOS PASSOS
Use o script `cleanup_otimizacao.py` no modo seguro para executar apenas limpezas 100% seguras.
""")
        
        print(f"📄 Análise completa salva em: {report_file.name}")
        print("\n✅ ANÁLISE CONCLUÍDA - NENHUM ARQUIVO FOI MODIFICADO")
    
    def run_analysis(self):
        """Executa análise completa"""
        print("🔍 INICIANDO ANÁLISE DO PROJETO BIODESK")
        print("🛡️ MODO APENAS LEITURA - NADA SERÁ MODIFICADO")
        print(f"📁 Workspace: {self.workspace_root}")
        
        try:
            self.analyze_empty_files()
            self.analyze_cache()
            self.analyze_backups()
            self.analyze_test_code()
            self.analyze_duplications()
            
            self.generate_analysis_report()
            
        except Exception as e:
            print(f"\n❌ ERRO durante análise: {e}")
            raise

def main():
    """Função principal"""
    workspace = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    print("🔍 BIODESK ANALYZER v1.0 - APENAS ANÁLISE")
    print("=" * 50)
    print("🛡️ GARANTIA: Nenhum arquivo será modificado!")
    print("📊 Apenas análise e relatório")
    print("=" * 50)
    
    analyzer = BiodeskAnalyzer(workspace)
    
    response = input("\n🤔 Executar análise segura? (s/N): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        analyzer.run_analysis()
    else:
        print("❌ Análise cancelada pelo usuário.")

if __name__ == "__main__":
    main()
