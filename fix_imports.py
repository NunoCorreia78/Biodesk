import re

arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"

with open(arquivo, 'r', encoding='utf-8') as f:
    content = f.read()

# Corrigir imports colados
content = re.sub(r'import\s+(\w+)\s+import', r'import \1\nimport', content)
content = re.sub(r'from\s+([^\s]+)\s+import\s+([^\s,]+)\s+from', r'from \1 import \2\nfrom', content)

# Corrigir múltiplos imports na mesma linha
content = re.sub(r'(import [^,\n]+),\s*([A-Z]\w+)', r'\1\nfrom PyQt6.QtWidgets import \2', content)

# Separar declarações que foram coladas
content = re.sub(r'(\w+)\s+from\s+', r'\1\nfrom ', content)
content = re.sub(r'(\w+)\s+import\s+', r'\1\nimport ', content)

# Corrigir específicamente o início problemático
if content.startswith('import sys import'):
    lines = content.split(' ')
    imports = []
    current_import = ''
    
    for i, part in enumerate(lines):
        if part in ['import', 'from']:
            if current_import:
                imports.append(current_import.strip())
            current_import = part
        else:
            current_import += ' ' + part
            
        # Se encontrarmos def, paramos e juntamos o resto
        if part == 'def':
            if current_import:
                imports.append(current_import.strip())
            # Juntar o restante
            rest = ' '.join(lines[i:])
            break
    
    # Reconstruir o arquivo
    content = '\n'.join(imports) + '\n' + rest

# Normalizar espaços múltiplos
content = re.sub(r' +', ' ', content)

# Adicionar quebras de linha onde necessário
content = re.sub(r'(import [^\n]+)\s+(import|from)', r'\1\n\2', content)
content = re.sub(r'(from [^\n]+)\s+(import|from)', r'\1\n\2', content)

# Salvar arquivo corrigido
with open(arquivo, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Imports e estrutura corrigidos!")
