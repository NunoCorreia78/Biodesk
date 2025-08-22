#!/usr/bin/env python3
"""
SCRIPT DE LIMPEZA DE ARQUIVOS REDUNDANTES E DESNECESSÁRIOS
=========================================================

Este script remove arquivos identificados como redundantes, de teste,
backup antigos e cache desnecessário do projeto Biodesk.

⚠️ ATENÇÃO: Execute com cuidado! Alguns arquivos serão removidos permanentemente.
"""

import os
import shutil
from pathlib import Path

class BiodeskCleanup:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.removed_files = []
        self.total_size_saved = 0
        
    def get_file_size(self, filepath):
        """Obtém tamanho do arquivo em bytes"""
        try:
            return filepath.stat().st_size
        except:
            return 0
    
    def remove_file(self, filepath, reason=""):
        """Remove arquivo e registra a ação"""
        try:
            size = self.get_file_size(filepath)
            filepath.unlink()
            self.removed_files.append((str(filepath), size, reason))
            self.total_size_saved += size
            print(f"✅ Removido: {filepath.name} ({size} bytes) - {reason}")
            return True
        except Exception as e:
            print(f"❌ Erro ao remover {filepath}: {e}")
            return False
    
    def remove_directory(self, dirpath, reason=""):
        """Remove diretório e registra a ação"""
        try:
            size = sum(self.get_file_size(f) for f in dirpath.rglob('*') if f.is_file())
            shutil.rmtree(dirpath)
            self.removed_files.append((str(dirpath), size, reason))
            self.total_size_saved += size
            print(f"✅ Removido diretório: {dirpath.name} ({size} bytes) - {reason}")
            return True
        except Exception as e:
            print(f"❌ Erro ao remover diretório {dirpath}: {e}")
            return False
    
    def clean_test_files(self):
        """Remove arquivos de teste e desenvolvimento"""
        print("\n🗑️ REMOVENDO ARQUIVOS DE TESTE E DESENVOLVIMENTO...")
        
        test_files = [
            "exemplo_integracao.py",
            "investigar_coincidencia.py", 
            "exemplo_pacientes.csv",
            "exemplo_template_externo.json",
            "templates/testar_templates_word.py",
            "templates/orientacoes/exemplo_autopreenchimento.txt",
            "templates/exercicios_pdf/exemplo_alongamentos_matinais.txt"
        ]
        
        for file_path in test_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                self.remove_file(full_path, "Arquivo de teste/desenvolvimento")
    
    def clean_backup_files(self):
        """Remove arquivos de backup antigos"""
        print("\n💾 REMOVENDO ARQUIVOS DE BACKUP...")
        
        backup_files = [
            "assets/iris_esq.json.backup_antes_correcao",
            "assets/iris_esq.json.backup_antes_calibracao", 
            "assets/iris_esq.json.backup_20250803_185700",
            "assets/iris_drt.json.backup_20250803_185701"
        ]
        
        for file_path in backup_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                self.remove_file(full_path, "Backup antigo")
    
    def clean_cache_files(self):
        """Remove cache Python (__pycache__)"""
        print("\n🐍 REMOVENDO CACHE PYTHON...")
        
        for pycache_dir in self.base_path.rglob("__pycache__"):
            if pycache_dir.is_dir():
                self.remove_directory(pycache_dir, "Cache Python")
    
    def clean_empty_files(self):
        """Remove arquivos vazios"""
        print("\n📄 REMOVENDO ARQUIVOS VAZIOS...")
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and self.get_file_size(file_path) == 0:
                self.remove_file(file_path, "Arquivo vazio")
    
    def generate_report(self):
        """Gera relatório da limpeza"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE LIMPEZA CONCLUÍDA")
        print("="*60)
        
        if not self.removed_files:
            print("ℹ️ Nenhum arquivo foi removido.")
            return
        
        print(f"📁 Total de itens removidos: {len(self.removed_files)}")
        print(f"💾 Espaço total liberado: {self.total_size_saved / 1024:.1f} KB ({self.total_size_saved / (1024*1024):.1f} MB)")
        
        print("\n📋 DETALHES DOS ARQUIVOS REMOVIDOS:")
        for filepath, size, reason in self.removed_files:
            print(f"  • {Path(filepath).name} ({size} bytes) - {reason}")
    
    def run_cleanup(self, include_cache=True, include_backups=True, include_tests=True, include_empty=True):
        """Executa limpeza completa"""
        print("🧹 INICIANDO LIMPEZA DE ARQUIVOS REDUNDANTES")
        print(f"📍 Diretório base: {self.base_path}")
        print("="*60)
        
        if include_tests:
            self.clean_test_files()
            
        if include_backups:
            self.clean_backup_files()
            
        if include_cache:
            self.clean_cache_files()
            
        if include_empty:
            self.clean_empty_files()
        
        self.generate_report()


def main():
    """Função principal"""
    print("⚠️ AVISO: Este script irá remover arquivos permanentemente!")
    print("📋 Arquivos que serão removidos:")
    print("  • Arquivos de teste e desenvolvimento")
    print("  • Backups antigos de configuração")
    print("  • Cache Python (__pycache__)")
    print("  • Arquivos vazios")
    
    resposta = input("\n❓ Deseja continuar? (s/N): ").lower().strip()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        cleanup = BiodeskCleanup()
        cleanup.run_cleanup()
        
        print(f"\n✅ Limpeza concluída! Espaço liberado: {cleanup.total_size_saved / (1024*1024):.1f} MB")
    else:
        print("❌ Operação cancelada pelo usuário.")


if __name__ == "__main__":
    main()
