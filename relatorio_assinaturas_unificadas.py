#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 RELATÓRIO DE UNIFICAÇÃO DAS ASSINATURAS
=========================================

PROBLEMA IDENTIFICADO:
- Havia 3 implementações diferentes do sistema de assinaturas
- Cada uma com CSS diferente para espaçamento
- Resultava em layouts inconsistentes

IMPLEMENTAÇÕES ENCONTRADAS:
1. declaracao_saude.py (linha ~1520)
2. services/pdf.py (linha ~200) 
3. ficha_paciente.py (linha ~8600)

SOLUÇÃO APLICADA:
- Padronizei TODAS as implementações para usar:
  * margin: -15px 0 0 0 (espaçamento compacto)
  * line-height: 0.8 (linhas mais próximas)
  * Mesmo structure HTML

RESULTADO:
✅ Sistema unificado em todas as partes
✅ Espaçamento consistente entre assinatura e nome
✅ Política de não redundância aplicada

ARQUIVOS CORRIGIDOS:
"""

import os

def verificar_implementacoes():
    """Verifica se todas as implementações estão padronizadas"""
    
    arquivos_alvo = [
        "ficha_paciente/declaracao_saude.py",
        "services/pdf.py", 
        "ficha_paciente.py"
    ]
    
    padrao_esperado = "margin: -15px 0 0 0; line-height: 0.8;"
    
    print("🔍 VERIFICAÇÃO DE PADRONIZAÇÃO:")
    print("=" * 50)
    
    for arquivo in arquivos_alvo:
        caminho = os.path.join(os.path.dirname(__file__), arquivo)
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            if padrao_esperado in conteudo:
                print(f"✅ {arquivo}: PADRONIZADO")
            else:
                print(f"❌ {arquivo}: PRECISA CORREÇÃO")
        else:
            print(f"⚠️  {arquivo}: NÃO ENCONTRADO")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Gerar novo PDF para testar")
    print("2. Verificar espaçamento compacto")
    print("3. Confirmar centralização correta")

if __name__ == "__main__":
    verificar_implementacoes()
