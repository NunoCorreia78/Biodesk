"""
🔍 ANÁLISE: Como são formadas as assinaturas no PDF
===============================================

## 📋 DESCOBERTA IMPORTANTE:

As assinaturas são formadas por:

1. **IMAGENS PNG** - Convertidas do canvas QGraphicsScene
2. **HTML INLINE** - Com estilos diretos no HTML, não CSS separado
3. **ESTRUTURA TABLE** - Usando tabela para layout lado a lado

## 🎯 LOCALIZAÇÃO DO PROBLEMA:

**Arquivo**: ficha_paciente/declaracao_saude.py
**Linhas**: 1520-1530 (aproximadamente)

### Estrutura atual:
```html
<div style="margin-top: -15px; font-size: 11pt; color: #333; line-height: 0.8;">
    <strong>{nome}</strong><br>
    <span style="font-size: 10pt; color: #666;">{data}</span>
</div>
```

## ✅ CORREÇÃO APLICADA:

**Antes**: `margin-top: -8px`
**Depois**: `margin-top: -15px` ← ESTA É A LINHA QUE CONTROLA O ESPAÇAMENTO!

## 📊 COMO FUNCIONA:

1. **Canvas** → Desenha assinatura
2. **QPixmap** → Converte canvas para imagem
3. **PNG** → Salva como arquivo temp/sig_declaracao_*.png
4. **Base64** → Converte PNG para string base64
5. **HTML IMG** → Incorpora no HTML como data:image/png;base64,...
6. **QTextDocument** → Renderiza HTML para PDF

## 🧪 PARA TESTAR:

1. Criar nova declaração de saúde
2. Assinar (gera nova PNG)
3. O margin-top: -15px deve reduzir drasticamente o espaço
4. Se ainda não for suficiente, pode usar -20px ou -25px

## 🎯 VALOR RECOMENDADO:

Para espaçamento mínimo: `margin-top: -20px`
Para "colar" nome na assinatura: `margin-top: -25px`
"""

print("🔍 ANÁLISE COMPLETA DAS ASSINATURAS:")
print("")
print("✅ FORMATO: Imagens PNG convertidas do canvas")
print("✅ INCORPORAÇÃO: Base64 no HTML inline")  
print("✅ CONTROLE: margin-top inline (não CSS)")
print("✅ CORREÇÃO: -8px → -15px aplicada")
print("")
print("📍 Para espaçamento ainda menor:")
print("   • -20px = muito próximo")
print("   • -25px = quase colado")
print("   • -30px = sobreposto")
print("")
print("🧪 Teste criando nova declaração de saúde!")
