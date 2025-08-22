import re
import ast

arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"

with open(arquivo, 'r', encoding='utf-8') as f:
    content = f.read()

# Remover emojis e caracteres especiais problemáticos
emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF\U00002600-\U000026FF\U0001F1F2\U0001F1F4\U0001F191-\U0001F251]+'

content_cleaned = re.sub(emoji_pattern, '', content)

# Remover outros caracteres especiais problemáticos (mantendo texto em português)
special_chars = ['🎯', '📊', '📄', '📤', '⚠️', '✅', '❌', '📝', '🔍', '🎨', '💾', '📋', '🖊️', '✍️', '📑', '🗂️', '📁', '📂', '🔧', '⚙️', '🎪', '🌟', '🎭']
for char in special_chars:
    content_cleaned = content_cleaned.replace(char, '')

# Limpar espaços extras deixados pelos emojis
content_cleaned = re.sub(r'\s+', ' ', content_cleaned)
content_cleaned = re.sub(r'^\s+', '', content_cleaned, flags=re.MULTILINE)

# Salvar arquivo limpo
with open(arquivo, 'w', encoding='utf-8') as f:
    f.write(content_cleaned)

print("✅ Emojis e caracteres especiais removidos!")

# Testar sintaxe
try:
    ast.parse(content_cleaned)
    print("✅ Sintaxe Python válida!")
except SyntaxError as e:
    print(f"❌ Erro de sintaxe na linha {e.lineno}: {e.msg}")
    if e.text:
        print(f"Texto: {e.text.strip()}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
