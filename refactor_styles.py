"""
Script para identificar e remover todos os estilos inline
e substituir por BiodeskStyles
"""

import os
import re
from pathlib import Path
import shutil
from datetime import datetime

class StyleRefactorer:
    """Refatorador automático de estilos"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.files_to_process = []
        self.style_patterns = [
            # Padrões para identificar estilos inline
            (r'\.setStyleSheet\(["\'].*?["\']\)', 'setStyleSheet'),
            (r'QPushButton\s*\{.*?\}', 'QPushButton style'),
            (r'background-color:\s*#[0-9a-fA-F]+', 'background-color'),
            (r'BiodeskUIKit\.(create_\w+_button)', 'BiodeskUIKit'),
            (r'border:\s*\d+px\s+solid', 'border style'),
            (r'font-size:\s*\d+px', 'font-size'),
            (r'padding:\s*\d+px', 'padding'),
        ]
    
    def scan_project(self):
        """Escaneia o projeto por arquivos Python com estilos"""
        print("🔍 Escaneando projeto por estilos inline...")
        
        for py_file in self.project_root.rglob("*.py"):
            # Ignorar venv, __pycache__, e nossos novos arquivos
            if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'biodesk_styles.py', 'refactor_styles.py', 'backup_styles']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                found_styles = []
                for pattern, pattern_name in self.style_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                        found_styles.append(pattern_name)
                
                if found_styles:
                    self.files_to_process.append((py_file, found_styles))
                    print(f"  ⚠️ {py_file.name}: encontrado {', '.join(found_styles)}")
                    
            except Exception as e:
                print(f"  ❌ Erro ao ler {py_file.name}: {e}")
    
    def generate_report(self):
        """Gera relatório de arquivos a processar"""
        report_path = self.project_root / "STYLE_REFACTOR_REPORT.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 📊 RELATÓRIO DE REFATORAÇÃO DE ESTILOS\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"**Arquivos analisados:** {len(list(self.project_root.rglob('*.py')))}\n")
            f.write(f"**Arquivos com estilos:** {len(self.files_to_process)}\n\n")
            
            f.write("## 📋 ARQUIVOS IDENTIFICADOS\n\n")
            
            for file_path, pattern_types in self.files_to_process:
                f.write(f"### 📄 {file_path.name}\n")
                f.write(f"**Localização:** `{file_path.relative_to(self.project_root)}`\n")
                f.write(f"**Padrões encontrados:** {', '.join(pattern_types)}\n\n")
            
            f.write("## 📈 ESTATÍSTICAS\n\n")
            all_patterns = [pattern for _, patterns in self.files_to_process for pattern in patterns]
            pattern_counts = {}
            for pattern in all_patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{pattern}:** {count} arquivos\n")
            
            f.write("\n## 🎯 PRÓXIMOS PASSOS\n\n")
            f.write("1. ✅ **Backup criado** - arquivos originais preservados\n")
            f.write("2. 🔄 **Refatoração manual** - substituir por BiodeskStyles\n")
            f.write("3. 🧪 **Testes** - validar funcionamento\n")
            f.write("4. 🧹 **Limpeza** - remover arquivos obsoletos\n\n")
            
            f.write("## 🚀 COMANDOS PARA IMPLEMENTAÇÃO\n\n")
            f.write("```python\n")
            f.write("# Importar novo sistema\n")
            f.write("from biodesk_styles import BiodeskStyles, ButtonType, DialogStyles\n\n")
            f.write("# Criar botão padronizado\n")
            f.write("btn = BiodeskStyles.create_button('Guardar Dados')  # Auto-detecta SAVE\n\n")
            f.write("# Converter botão existente\n")
            f.write("BiodeskStyles.apply_to_existing_button(existing_button)\n\n")
            f.write("# Aplicar estilo profissional a diálogo\n")
            f.write("DialogStyles.apply_to_dialog(dialog)\n")
            f.write("```\n")
        
        print(f"\n✅ Relatório salvo em: {report_path}")
        return report_path
    
    def backup_files(self):
        """Cria backup dos arquivos antes da refatoração"""
        backup_dir = self.project_root / "backup_styles"
        
        if backup_dir.exists():
            # Remover backup anterior
            shutil.rmtree(backup_dir)
        
        backup_dir.mkdir(exist_ok=True)
        
        print(f"💾 Criando backup em: {backup_dir}")
        
        backup_count = 0
        for file_path, _ in self.files_to_process:
            try:
                relative_path = file_path.relative_to(self.project_root)
                backup_path = backup_dir / relative_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(file_path, backup_path)
                backup_count += 1
                
            except Exception as e:
                print(f"  ❌ Erro ao fazer backup de {file_path.name}: {e}")
        
        print(f"✅ Backup criado: {backup_count} arquivos copiados")
        return backup_dir
    
    def generate_priority_list(self):
        """Gera lista de arquivos por prioridade de refatoração"""
        priority_files = []
        
        # Definir prioridades baseadas no impacto
        high_priority = ['main_window.py', 'ficha_paciente.py']
        medium_priority = ['biodesk_ui_kit.py', 'biodesk_style_manager.py']
        
        for file_path, patterns in self.files_to_process:
            filename = file_path.name
            
            if filename in high_priority:
                priority = "🔥 ALTA"
            elif filename in medium_priority:
                priority = "⚠️ MÉDIA"
            elif 'dialog' in filename.lower():
                priority = "📱 DIÁLOGOS"
            elif any(mod in str(file_path) for mod in ['ficha_paciente/', 'widgets/', 'services/']):
                priority = "🧩 MÓDULOS"
            else:
                priority = "🔧 BAIXA"
            
            priority_files.append((priority, file_path, len(patterns)))
        
        # Ordenar por prioridade
        priority_order = ["🔥 ALTA", "⚠️ MÉDIA", "📱 DIÁLOGOS", "🧩 MÓDULOS", "🔧 BAIXA"]
        priority_files.sort(key=lambda x: (priority_order.index(x[0]), -x[2]))
        
        print("\n📋 LISTA DE PRIORIDADES PARA REFATORAÇÃO:")
        for priority, file_path, style_count in priority_files:
            print(f"  {priority} - {file_path.name} ({style_count} padrões)")
        
        return priority_files

# Executar o refatorador
if __name__ == "__main__":
    print("🎨 REFATORADOR DE ESTILOS BIODESK")
    print("=" * 50)
    
    project_path = r"C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
    
    if not Path(project_path).exists():
        print(f"❌ Caminho não encontrado: {project_path}")
        exit(1)
    
    refactorer = StyleRefactorer(project_path)
    
    # Executar análise completa
    refactorer.scan_project()
    
    if not refactorer.files_to_process:
        print("✅ Nenhum arquivo com estilos inline encontrado!")
        exit(0)
    
    # Gerar relatórios
    report_path = refactorer.generate_report()
    backup_dir = refactorer.backup_files()
    priority_list = refactorer.generate_priority_list()
    
    print(f"\n🎯 ANÁLISE COMPLETA:")
    print(f"   📊 Relatório: {report_path}")
    print(f"   💾 Backup: {backup_dir}")
    print(f"   📋 {len(refactorer.files_to_process)} arquivos para refatorar")
    
    print(f"\n🚀 PRÓXIMO PASSO:")
    print(f"   Abrir o relatório e iniciar refatoração pelos arquivos de ALTA prioridade")
