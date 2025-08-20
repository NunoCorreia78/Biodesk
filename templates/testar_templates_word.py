#!/usr/bin/env python3
"""
TESTE DO SISTEMA DE TEMPLATES WORD
"""

import sys
sys.path.append(r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\templates")

from adaptador_templates_word import detectar_templates_word, processar_template_word, obter_email_personalizado
from datetime import datetime

def testar_sistema():
    print("🧪 TESTANDO SISTEMA DE TEMPLATES WORD")
    print("=" * 40)
    
    # 1. Detectar templates
    print("📁 Detectando templates Word...")
    templates = detectar_templates_word()
    
    for categoria, lista in templates.items():
        if lista:
            print(f"\n📂 {categoria.upper()}:")
            for template in lista:
                print(f"  • {template['nome']} ({template['tipo']})")
    
    # 2. Testar configuração de email
    print("\n📧 Testando configurações de email...")
    
    arquivo_teste = r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\templates\orientacoes_word\protocolo_detox_hepatico.docx"
    
    if Path(arquivo_teste).exists():
        email_config = obter_email_personalizado(arquivo_teste)
        if email_config:
            print("✅ Configuração de email encontrada:")
            print(f"  • Assunto: {email_config['assunto']}")
            print(f"  • Corpo: {email_config['corpo'][:100]}...")
    
    print("\n✅ TESTE CONCLUÍDO!")

if __name__ == "__main__":
    from pathlib import Path
    testar_sistema()
