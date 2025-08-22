import re

# Ler o arquivo
arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"
with open(arquivo, 'r', encoding='utf-8') as f:
    content = f.read()

# Padrão para encontrar blocos try...pass seguidos de código solto até encontrar except
pattern = r'(\s*try:\s*\n\s*pass\s*\n)(.*?)(\s*except[^\n]*:\s*\n\s*pass)'

def fix_try_block(match):
    try_part = match.group(1)
    middle_content = match.group(2)
    except_part = match.group(3)
    
    # Se o conteúdo do meio tem código que não seja apenas espaços/comentários
    if middle_content.strip() and not all(line.strip().startswith('#') or line.strip() == '' for line in middle_content.split('\n')):
        # Reindenta o conteúdo do meio para ficar dentro do try
        lines = middle_content.split('\n')
        indented_lines = []
        for line in lines:
            if line.strip():  # Se a linha não está vazia
                # Adiciona 4 espaços de indentação extra
                indented_lines.append('    ' + line)
            else:
                indented_lines.append(line)
        
        middle_content = '\n'.join(indented_lines)
        return try_part.replace('pass', middle_content.strip()) + '\n' + except_part
    else:
        return match.group(0)  # Retorna sem mudanças se não há código real

# Aplicar a correção
new_content = re.sub(pattern, fix_try_block, content, flags=re.DOTALL)

# Salvar apenas se houve mudanças
if new_content != content:
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Blocos try corrigidos com sucesso!")
else:
    print("Nenhuma correção de try/except necessária.")
