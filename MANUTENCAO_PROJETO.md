# 🧹 MANUTENÇÃO AUTOMÁTICA DO PROJETO BIODESK

## Scripts de Limpeza Disponíveis

### 1. Limpeza Completa
```bash
python cleanup_redundant_files.py
```
Remove arquivos de teste, backups antigos, cache Python e arquivos vazios.

### 2. Limpeza Apenas de Cache
```bash
python -c "
import shutil
from pathlib import Path
for cache_dir in Path('.').rglob('__pycache__'):
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir)
        print(f'Removido: {cache_dir}')
"
```

### 3. Limpeza de Arquivos Temporários
```bash
# PowerShell
Get-ChildItem -Recurse -Include "*.tmp", "*.temp", "*.bak" | Remove-Item -Force
```

## 📋 Cronograma de Manutenção Recomendado

- **Semanal**: Limpeza de cache Python
- **Mensal**: Limpeza completa com o script
- **Antes de releases**: Verificação manual de arquivos desnecessários

## 🔍 Monitoramento de Espaço

Para verificar o crescimento do projeto:
```bash
# Total do projeto
python -c "
import os
from pathlib import Path
total = sum(f.stat().st_size for f in Path('.').rglob('*') if f.is_file())
print(f'Tamanho total: {total/1024/1024:.1f} MB')
"

# Apenas arquivos Python
python -c "
import os
from pathlib import Path
total = sum(f.stat().st_size for f in Path('.').rglob('*.py') if f.is_file())
print(f'Código Python: {total/1024:.1f} KB')
"
```

## ⚠️ Arquivos Protegidos

**NUNCA REMOVER:**
- `main_window.py` - Janela principal
- `ficha_paciente/` - Módulo principal de fichas
- `templates/` - Templates de documentos
- `assets/` - Recursos visuais
- `*.db` - Bases de dados
- `email_config.json` - Configurações de email

## 🎯 Arquivos Seguros para Remoção

**SEMPRE SEGUROS:**
- `__pycache__/` - Cache Python
- `*.pyc` - Bytecode compilado
- `*.tmp`, `*.temp` - Arquivos temporários
- `*backup*`, `*.bak` - Backups antigos
- `*test*`, `*exemplo*` - Arquivos de teste
- Arquivos com 0 bytes

## 📊 Última Limpeza

**Data**: 21 de Agosto de 2025
**Arquivos removidos**: 300 itens
**Espaço liberado**: 3.5 MB
**Status**: ✅ Concluída com sucesso
