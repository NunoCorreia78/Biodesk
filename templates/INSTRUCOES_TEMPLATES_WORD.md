# 📖 INSTRUÇÕES DE INTEGRAÇÃO - TEMPLATES WORD

## ✅ SISTEMA CRIADO COM SUCESSO!

### 📁 **ESTRUTURA FINAL:**
```
templates/
├── orientacoes_word/           ← SEUS DOCUMENTOS WORD AQUI
│   ├── protocolo_detox_hepatico.docx  ← Já movido!
│   └── README.md
├── exercicios_word/            ← Templates de exercícios
├── suplementos_word/           ← Templates de suplementação
├── dietas_word/               ← Templates de dietas
├── seguimento_word/           ← Templates de seguimento
├── exames_word/               ← Templates de exames
├── config_templates_word.json  ← Configurações
├── adaptador_templates_word.py ← Código de integração
└── testar_templates_word.py   ← Script de teste
```

## 🎯 **COMO USAR:**

### 1. **ADICIONAR NOVOS TEMPLATES:**
- Copie seus documentos Word (.docx) para a pasta apropriada
- Exemplo: `orientacoes_word/protocolo_diabetes.docx`
- Sistema detecta automaticamente

### 2. **PERSONALIZAÇÃO DE EMAILS:**
- Edite `config_templates_word.json` 
- Adicione configurações específicas por template
- Variáveis disponíveis: {{nome_paciente}}, {{data_hoje}}, etc.

### 3. **INTEGRAÇÃO COM SISTEMA PRINCIPAL:**
```python
# No arquivo principal, adicionar:
from templates.adaptador_templates_word import detectar_templates_word, processar_template_word

# Detectar templates disponíveis
templates_word = detectar_templates_word()

# Processar template específico
pdf_gerado = processar_template_word(arquivo_word, dados_paciente)
```

## 📧 **EMAILS AUTOMÁTICOS:**

### **Protocolo Detox Hepático:**
- **Assunto:** "Protocolo de Detox Hepático Personalizado - {{nome_paciente}}"
- **Corpo:** Email completo com instruções detalhadas
- **Anexo:** PDF convertido automaticamente

### **Templates Personalizados:**
- Sistema cria emails específicos para cada tipo
- Variáveis preenchidas automaticamente
- Contactos e instruções incluídos

## 🔧 **FUNCIONALIDADES:**

### ✅ **O QUE FUNCIONA:**
- Detecção automática de templates Word
- Conversão automática para PDF
- Email personalizado por tipo de template
- Preservação total da formatação original
- Logo e design mantidos 100%

### 🎨 **VANTAGENS:**
- **Formatação preservada:** Logo, cores, fontes exatamente iguais
- **Processo automático:** Sem edição manual necessária
- **Email inteligente:** Texto personalizado para cada tipo
- **Organização:** Pastas separadas por categoria

## 🧪 **TESTAR O SISTEMA:**

1. **Execute o teste:**
   ```
   python templates/testar_templates_word.py
   ```

2. **Verifique:**
   - Templates detectados
   - Configurações de email
   - Estrutura de pastas

## 📋 **PRÓXIMOS PASSOS:**

1. ✅ **Coloque mais documentos Word** nas pastas apropriadas
2. ✅ **Personalize emails** editando config_templates_word.json
3. ✅ **Teste com paciente real** para validar o fluxo completo
4. ✅ **Integre com sistema principal** usando o adaptador

---
**Criado em:** 14/08/2025 às 21:08
**Status:** ✅ Pronto para usar
**Localização:** `templates/orientacoes_word/protocolo_detox_hepatico.docx`
