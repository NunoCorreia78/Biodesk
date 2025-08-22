import re
import ast

arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"

with open(arquivo, 'r', encoding='utf-8') as f:
    content = f.read()

# Corrigir padrões problemáticos específicos
fixes = [
    # Bloco try incompleto
    (r'try:\s*\n\s*\"\"\"\s*\n\s*\n\s*\n\s*except Exception as e:\s*\n\s*pass', 
     'try:\n                pass\n            except Exception as e:\n                pass'),
    
    # String soltas que causam problemas
    (r'^\s*\"\"\"\s*$', ''),
    
    # Múltiplas linhas vazias consecutivas
    (r'\n\s*\n\s*\n\s*\n+', '\n\n'),
]

for pattern, replacement in fixes:
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Salvar arquivo corrigido
with open(arquivo, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Arquivo final corrigido!")

# Testar sintaxe
try:
    ast.parse(content)
    print("✅ Sintaxe Python válida!")
except SyntaxError as e:
    print(f"❌ Erro de sintaxe na linha {e.lineno}: {e.msg}")
    if e.text:
        print(f"Texto: {e.text.strip()}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
