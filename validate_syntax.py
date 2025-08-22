import re
import ast

# Ler o arquivo com encoding UTF-8
arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"

try:
    with open(arquivo, 'r', encoding='utf-8') as f:
        content = f.read()
    print("Arquivo lido com encoding UTF-8")
except UnicodeDecodeError:
    print("Erro de encoding UTF-8, tentando latin-1...")
    try:
        with open(arquivo, 'r', encoding='latin-1') as f:
            content = f.read()
        print("Arquivo lido com encoding latin-1")
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        exit(1)

# Limpar caracteres problemáticos
content_clean = content.encode('utf-8', errors='ignore').decode('utf-8')

# Verificar se houve limpeza
if len(content_clean) != len(content):
    print(f"Removidos {len(content) - len(content_clean)} caracteres problemáticos")
    
# Salvar arquivo limpo
with open(arquivo, 'w', encoding='utf-8') as f:
    f.write(content_clean)

print("Arquivo limpo e salvo com encoding UTF-8")

# Testar sintaxe
try:
    ast.parse(content_clean)
    print("✅ Sintaxe Python válida!")
except SyntaxError as e:
    print(f"❌ Erro de sintaxe na linha {e.lineno}: {e.msg}")
    if e.text:
        print(f"Texto: {e.text.strip()}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
