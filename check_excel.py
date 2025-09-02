import os
import sys

# Verificar se o arquivo existe
file_path = "assets/FrequencyList.xls"
if os.path.exists(file_path):
    print(f"✅ Arquivo encontrado: {file_path}")
    print(f"📏 Tamanho: {os.path.getsize(file_path)} bytes")
else:
    print(f"❌ Arquivo não encontrado: {file_path}")

# Tentar ler com xlrd (método mais básico)
try:
    import xlrd
    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_index(0)
    
    print(f"📊 Dimensões: {sheet.nrows} linhas x {sheet.ncols} colunas")
    
    # Ler primeira linha (cabeçalhos)
    if sheet.nrows > 0:
        headers = [sheet.cell_value(0, col) for col in range(min(15, sheet.ncols))]
        print(f"📋 Primeiros 15 cabeçalhos: {headers}")
    
    # Ler algumas linhas de dados
    if sheet.nrows > 1:
        print("🔍 Primeiras 3 linhas de dados:")
        for row in range(1, min(4, sheet.nrows)):
            row_data = [sheet.cell_value(row, col) for col in range(min(10, sheet.ncols))]
            print(f"   Linha {row}: {row_data}")

except ImportError:
    print("❌ xlrd não disponível")
except Exception as e:
    print(f"❌ Erro ao ler com xlrd: {e}")
