🎨 MOCKUP VISUAL - CENTRO DE COMUNICAÇÃO
=======================================

## 📱 **LAYOUT ATUAL vs NOVO - COMPARAÇÃO VISUAL**

### 🔴 **SITUAÇÃO ATUAL:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BIODESK - Ficha do Paciente: João Silva                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ [📋 DOCUMENTAÇÃO CLÍNICA] [🩺 ÁREA CLÍNICA]                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                          🩺 ÁREA CLÍNICA                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [📝 Histórico] [👁️ Íris] [📋 Prescrições] [📧 Email]                    │ │
│ │                                                                         │ │
│ │                    📧 EMAIL (aba atual)                                 │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Para: [________________________]                                   │ │ │
│ │ │ Assunto: [____________________]                                     │ │ │
│ │ │                                                                     │ │ │
│ │ │ Template: [Selecionar ▼]                                            │ │ │
│ │ │                                                                     │ │ │
│ │ │ Mensagem:                                                           │ │ │
│ │ │ ┌─────────────────────────────────────────────────────────────────┐ │ │ │
│ │ │ │                                                                 │ │ │ │
│ │ │ │                                                                 │ │ │ │
│ │ │ │                                                                 │ │ │ │
│ │ │ └─────────────────────────────────────────────────────────────────┘ │ │ │
│ │ │                                                                     │ │ │
│ │ │ Anexos: (nenhum disponível)                                        │ │ │
│ │ │                                                                     │ │ │
│ │ │                                          [📧 Enviar Email]          │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

    ❌ PROBLEMA: Para anexar documentos, o usuário tem que:
    1. Ir à aba "📁 Gestão de Documentos" 
    2. Procurar o documento
    3. Voltar à aba "📧 Email"
    4. Não tem forma fácil de anexar!
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### ✅ **SITUAÇÃO NOVA - CENTRO DE COMUNICAÇÃO:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BIODESK - Ficha do Paciente: João Silva                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ [📋 DOCUMENTAÇÃO CLÍNICA] [🩺 ÁREA CLÍNICA]                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                          🩺 ÁREA CLÍNICA                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [📝 Histórico] [👁️ Íris] [📞 Centro de Comunicação]                    │ │
│ │                                                                         │ │
│ │                  📞 CENTRO DE COMUNICAÇÃO                               │ │
│ │ ┌─────────────┬───────────────────┬───────────────────────────────────┐ │ │
│ │ │📧 EMAIL     │📁 DOCUMENTOS      │📎 ANEXOS SELECIONADOS            │ │ │
│ │ │             │DISPONÍVEIS        │                                   │ │ │
│ │ ├─────────────┼───────────────────┼───────────────────────────────────┤ │ │
│ │ │Para:        │🔍 [Pesquisar...] │✅ Prescrição_27082025.pdf        │ │ │
│ │ │[__________] │                   │   (198 KB)                       │ │ │
│ │ │             │□ Prescrição_27... │                                   │ │ │
│ │ │Assunto:     │□ Exame_iris_20... │✅ Declaração_Saúde.pdf           │ │ │
│ │ │[__________] │□ Declaração_Sa... │   (156 KB)                       │ │ │
│ │ │             │□ Relatório_Lab... │                                   │ │ │
│ │ │Template:    │□ Plano_Terapeu... │┌─────────────────────────────────┐ │ │
│ │ │[Receita ▼] │□ Resultados_An... ││🖼️ Pré-visualização:              │ │ │
│ │ │             │□ Carta_Encami... ││                                 │ │ │
│ │ │Mensagem:    │                   ││[Prescrição_27082025.pdf]       │ │ │
│ │ │┌───────────┐│[🔄 Atualizar]     ││                                 │ │ │
│ │ ││           ││                   ││                                 │ │ │
│ │ ││Exmo. Sr.  ││                   │└─────────────────────────────────┘ │ │
│ │ ││João Silva,││                   │                                   │ │ │
│ │ ││           ││                   │[❌ Remover Selecionados]         │ │ │
│ │ ││Segue em   ││                   │                                   │ │ │
│ │ ││anexo...   ││                   │[📎 Adicionar Mais]               │ │ │
│ │ │└───────────┘│                   │                                   │ │ │
│ │ │             │                   │                                   │ │ │
│ │ │[📋Template] │                   │        [📧 ENVIAR EMAIL]          │ │ │
│ │ │[💾 Rascunho]│                   │        com 2 anexos               │ │ │
│ │ └─────────────┴───────────────────┴───────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

    ✅ VANTAGENS:
    1. Tudo numa tela só - sem mudança de abas
    2. Lista de documentos sempre visível  
    3. Seleção múltipla com checkboxes
    4. Pré-visualização dos anexos
    5. Templates inteligentes baseados nos anexos
    6. Drag & drop entre colunas
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 **LAYOUT DETALHADO - CENTRO DE COMUNICAÇÃO**

### **📐 ESPECIFICAÇÕES TÉCNICAS:**
```
┌─ CENTRO DE COMUNICAÇÃO ─────────────────────────────────────────────────────┐
│                                                                             │
│ ┌─ COLUNA 1: EMAIL ───┬─ COLUNA 2: DOCUMENTOS ─┬─ COLUNA 3: ANEXOS ────────┐│
│ │      35%            │         40%             │         25%               ││
│ │                     │                         │                           ││
│ │ 📧 ÁREA DE EMAIL    │ 📁 LISTA DE DOCUMENTOS  │ 📎 GESTÃO DE ANEXOS       ││
│ │ ┌─────────────────┐ │ ┌─────────────────────┐ │ ┌─────────────────────────┐││
│ │ │ Para:           │ │ │ 🔍 [Buscar docs...] │ │ │ ✅ ANEXOS SELECIONADOS: │││
│ │ │ [____________]  │ │ │                     │ │ │                         │││
│ │ │                 │ │ │ 📄 PDFs Recentes:   │ │ │ 📄 Prescrição.pdf       │││
│ │ │ Assunto:        │ │ │ □ Prescrição_27...  │ │ │    Size: 198 KB         │││
│ │ │ [____________]  │ │ │ □ Declaração_Sa...  │ │ │    ❌ [Remover]          │││
│ │ │                 │ │ │ □ Exame_iris_20...  │ │ │                         │││
│ │ │ 📋 Template:    │ │ │ □ Relatório_Lab...  │ │ │ 📋 Declaração.pdf       │││
│ │ │ [Consulta  ▼]   │ │ │                     │ │ │    Size: 156 KB         │││
│ │ │                 │ │ │ 📋 Templates:       │ │ │    ❌ [Remover]          │││
│ │ │ 💬 Mensagem:    │ │ │ □ Template_Rece...  │ │ │                         │││
│ │ │ ┌─────────────┐ │ │ │ □ Template_Rela...  │ │ │ ═══════════════════════ │││
│ │ │ │Prezado(a)   │ │ │ □ Template_Enca...  │ │ │                         │││
│ │ │ │Sr(a) João,  │ │ │                     │ │ │ 🖼️ PRÉ-VISUALIZAÇÃO:   │││
│ │ │ │             │ │ │ 📊 Relatórios:      │ │ │ ┌─────────────────────┐ │││
│ │ │ │Conforme nossa│ │ │ □ Relatório_Íris... │ │ │ │ [Prescrição.pdf]    │ │││
│ │ │ │consulta...  │ │ │ □ Análise_Comp...   │ │ │ │                     │ │││
│ │ │ │             │ │ │                     │ │ │ │  📄 Página 1 de 3   │ │││
│ │ │ └─────────────┘ │ │ │ [🔄 Atualizar]      │ │ │ │                     │ │││
│ │ │                 │ │ │ [📁 Abrir Pasta]    │ │ │ └─────────────────────┘ │││
│ │ │ ┌─────────────┐ │ │ │                     │ │ │                         │││
│ │ │ │📎 Ações:    │ │ │ FILTROS:            │ │ │ [📎 Adicionar Mais]     │││
│ │ │ │✓ Auto-anexar│ │ │ [📅 Data] [📋 Tipo] │ │ │                         │││
│ │ │ │✓ Auto-assign│ │ │                     │ │ │ ┌─────────────────────┐ │││
│ │ │ │○ Programar  │ │ │                     │ │ │ │  📧 ENVIAR EMAIL    │ │││
│ │ │ └─────────────┘ │ │ │                     │ │ │ │                     │ │││
│ │ │                 │ │ │                     │ │ │ │ ✅ 2 anexos prontos │ │││
│ │ │ [💾 Rascunho]   │ │ │                     │ │ │ │ 📊 Total: 354 KB    │ │││
│ │ │ [📧 ENVIAR]     │ │ │                     │ │ │ │                     │ │││
│ │ └─────────────────┘ │ └─────────────────────┘ │ └─────────────────────┘ │││
│ └─────────────────────┴─────────────────────────┴─────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎨 **FLUXO DE TRABALHO VISUAL:**

### **👆 INTERAÇÃO DO USUÁRIO:**
```
1. ABRIR CENTRO DE COMUNICAÇÃO
   ↓
2. SELECIONAR DOCUMENTOS (coluna do meio)
   ☑️ Prescrição_27082025.pdf
   ☑️ Declaração_Saúde.pdf
   ↓
3. DOCUMENTOS APARECEM NA COLUNA DIREITA
   ✅ Prescrição.pdf (198 KB) [❌]
   ✅ Declaração.pdf (156 KB) [❌]
   ↓
4. ESCOLHER TEMPLATE BASEADO NOS ANEXOS
   Template: [Envio de Documentos ▼]
   ↓
5. TEMPLATE AUTO-PREENCHE O EMAIL
   "Prezado(a) Sr(a) João Silva,
   Segue em anexo a prescrição e declaração 
   conforme solicitado..."
   ↓
6. REVISAR E ENVIAR
   [📧 ENVIAR EMAIL com 2 anexos]
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📱 **RESPONSIVIDADE E ADAPTAÇÃO:**

### **🖥️ EM TELAS GRANDES (>1400px):**
```
[35% Email] [40% Documentos] [25% Anexos]
Máxima produtividade com 3 colunas visíveis
```

### **💻 EM TELAS MÉDIAS (1000-1400px):**
```
[40% Email] [35% Documentos] [25% Anexos]
Colunas ajustadas mas todas visíveis
```

### **📱 EM TELAS PEQUENAS (<1000px):**
```
Tabs dinâmicos:
[📧 Email] [📁 Docs] [📎 Anexos]
Com transferência rápida entre tabs
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 **FUNCIONALIDADES SMART:**

### **🧠 TEMPLATES INTELIGENTES:**
```
Anexos Detectados → Template Sugerido
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Prescrição.pdf → "Envio de Receita Médica"
📋 Exame.pdf → "Resultados de Exame"  
📊 Relatório.pdf → "Relatório de Consulta"
📝 Múltiplos → "Envio de Documentação Completa"
```

### **⚡ AÇÕES RÁPIDAS:**
```
🔄 Drag & Drop: Documentos → Anexos
⌨️ Ctrl+A: Selecionar todos os documentos
🔍 Pesquisa inteligente: "prescrição agosto"
📎 Anexar por data: "Últimos 7 dias"
💾 Auto-salvar rascunhos a cada 30 segundos
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ✨ **PREVIEW EM AÇÃO:**

```
👤 USUÁRIO QUER ENVIAR PRESCRIÇÃO + DECLARAÇÃO:

ANTES (atual): 7 cliques, 3 abas
┌─ [📁 Gestão Docs] → Encontrar prescrição → Voltar
├─ [📁 Gestão Docs] → Encontrar declaração → Voltar  
└─ [📧 Email] → Escrever email → Enviar (sem anexos!)

DEPOIS (novo): 3 cliques, 1 aba
┌─ [📞 Centro] → ☑️ Prescrição ☑️ Declaração 
└─ Template auto → [📧 Enviar]

💡 RESULTADO: 60% MENOS CLIQUES, 100% MAIS EFICIENTE!
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎨 **ESTILO VISUAL (BiodeskStyles v2.0):**

### **🎨 CORES E TEMAS:**
```
📧 Email: Azul suave (#E3F2FD)
📁 Documentos: Verde menta (#E8F5E8)  
📎 Anexos: Laranja claro (#FFF3E0)
✅ Selecionados: Verde confirmação (#4CAF50)
❌ Remover: Vermelho suave (#F44336)
```

### **🖱️ INTERAÇÕES:**
```
Hover: Destaque suave com sombra
Click: Animação de feedback
Drag: Cursor de movimento + preview
Drop: Zona destacada + confirmação
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚀 **PRONTO PARA IMPLEMENTAR!**

O mockup mostra um centro de comunicação moderno, intuitivo e altamente produtivo.

**Quer que implemente este layout?** 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
