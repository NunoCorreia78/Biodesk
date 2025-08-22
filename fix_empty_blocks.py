import re
import os

# Caminho do arquivo
arquivo = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\ficha_paciente.py"

# Ler o arquivo
with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Padrões para detectar blocos vazios
padroes_vazios = [
    (r'^(\s*)(if\s+.*:)\s*$', r'\1\2\n\1    pass\n'),  # if vazio
    (r'^(\s*)(for\s+.*:)\s*$', r'\1\2\n\1    pass\n'),  # for vazio
    (r'^(\s*)(while\s+.*:)\s*$', r'\1\2\n\1    pass\n'),  # while vazio
    (r'^(\s*)(try\s*:)\s*$', r'\1\2\n\1    pass\n'),  # try vazio
    (r'^(\s*)(except.*:)\s*$', r'\1\2\n\1    pass\n'),  # except vazio
    (r'^(\s*)(else\s*:)\s*$', r'\1\2\n\1    pass\n'),  # else vazio
    (r'^(\s*)(elif\s+.*:)\s*$', r'\1\2\n\1    pass\n'),  # elif vazio
]

alterado = False
nova_linhas = []

i = 0
while i < len(linhas):
    linha = linhas[i]
    linha_alterada = False
    
    for padrao, substituicao in padroes_vazios:
        match = re.match(padrao, linha)
        if match:
            # Verificar se a próxima linha não tem indentação suficiente
            proxima_linha = linhas[i + 1] if i + 1 < len(linhas) else ""
            indentacao_atual = len(match.group(1))
            
            # Se a próxima linha não está indentada adequadamente ou está vazia
            if proxima_linha.strip() == "" or len(proxima_linha) - len(proxima_linha.lstrip()) <= indentacao_atual:
                # Aplicar substituição
                nova_linha = re.sub(padrao, substituicao, linha)
                nova_linhas.append(nova_linha)
                alterado = True
                linha_alterada = True
                print(f"Linha {i+1}: Adicionado 'pass' após: {linha.strip()}")
                break
    
    if not linha_alterada:
        nova_linhas.append(linha)
    
    i += 1

# Salvar as alterações se houve mudanças
if alterado:
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.writelines(nova_linhas)
    print(f"\n✅ Arquivo corrigido com sucesso!")
else:
    print("Nenhuma correção necessária.")
