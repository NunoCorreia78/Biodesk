import re
import ast

arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"

with open(arquivo, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corrigir indentação de funções que estão aninhadas incorretamente
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Se encontramos uma linha com uma função mal indentada (com mais de 4 espaços antes de def)
    match = re.match(r'^(\s{8,})def\s+', line)
    if match:
        # Esta função está aninhada incorretamente, vamos movê-la para o nível de classe
        # Função deve ter apenas 4 espaços (nível de classe)
        corrected_line = re.sub(r'^(\s{8,})', '    ', line)
        fixed_lines.append(corrected_line)
        print(f"Linha {i+1}: Corrigida indentação de função: {line.strip()}")
    else:
        fixed_lines.append(line)
    
    i += 1

# Salvar arquivo corrigido
with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Indentação de funções corrigida!")

# Testar sintaxe
try:
    with open(arquivo, 'r', encoding='utf-8') as f:
        content = f.read()
    ast.parse(content)
    print("✅ Sintaxe Python válida!")
except SyntaxError as e:
    print(f"❌ Erro de sintaxe na linha {e.lineno}: {e.msg}")
    if e.text:
        print(f"Texto: {e.text.strip()}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
