# PRESCRIÇÕES MÉDICAS - NOVO SISTEMA

## 📋 Descrição
Sistema moderno de prescrições médicas que substitui o antigo sistema de suplementos.

## ✨ Funcionalidades

### 🎯 Editor HTML Interativo
- Interface moderna baseada em HTML/CSS
- Campos editáveis em tempo real
- Tabela dinâmica para medicamentos/suplementos
- Sistema de posologia avançado

### 💾 Gestão de Dados
- Salvamento automático em JSON
- Histórico de prescrições por paciente
- Templates predefinidos
- Importação/exportação de dados

### 🖨️ Impressão
- Layout otimizado para impressão
- Formato A4 profissional
- Cabeçalho com dados do terapeuta
- Rodapé com locais de atendimento

## 🔧 Arquivos Principais

```
templates/
├── prescricao_medica.html          # Template HTML principal
└── prescricao/                     # Diretório para templates salvos

prescricao_medica_widget.py         # Widget principal do sistema
ficha_paciente/templates_manager.py  # Integração com sistema existente
```

## 📝 Como Usar

1. **Acesso**: Na aba "Modelos de Prescrição", clicar em "🩺 Prescrição"
2. **Edição**: O editor HTML abre automaticamente com dados do paciente
3. **Preenchimento**: 
   - Nome do utente (auto-preenchido)
   - Data atual (auto-preenchida)
   - Duração do tratamento
   - Medicamentos/suplementos na tabela
   - Instruções e observações
4. **Ações**:
   - **Salvar**: Grava prescrição em JSON
   - **Imprimir**: Abre diálogo de impressão
   - **Limpar**: Reset completo do formulário

## 🔄 Migração do Sistema Anterior

### Mudanças Principais:
- ❌ **Removido**: Botão "Suplementos" com subcategorias
- ✅ **Adicionado**: Botão "Prescrição" que abre editor direto
- ✅ **Melhorado**: Interface mais profissional e funcional

### Compatibilidade:
- Dados antigos de suplementos podem ser migrados manualmente
- Templates antigos ainda funcionam nas outras categorias
- Sistema novo não interfere com funcionalidades existentes

## 📁 Estrutura de Dados

### Arquivo de Prescrição (JSON):
```json
{
  "paciente_id": 123,
  "paciente_nome": "Nome do Paciente",
  "data_criacao": "2025-08-27T10:30:00",
  "dados_prescricao": {
    "utente": "Nome do Paciente",
    "data": "27/08/2025",
    "duracao": "30 dias",
    "notas": "Instruções especiais...",
    "prescricoes": [
      {
        "suplemento": "Vitamina D3",
        "apresentacao": "Gotas 1000UI",
        "posologia": "10 gotas 1x/dia",
        "opcoes": ["antes"],
        "tempo": "30 min"
      }
    ]
  }
}
```

## 🚀 Funcionalidades Avançadas

### Templates Rápidos:
- Suplementação Básica
- Protocolo Imunidade
- Detox Completo
- Protocolos personalizados

### Histórico:
- Lista todas as prescrições do paciente
- Carregamento de prescrições anteriores
- Exclusão segura com confirmação

### Auto-salvamento:
- Backup automático a cada 30 segundos
- Recuperação em caso de erro
- Persistência de dados entre sessões

## 📋 Requisitos Técnicos

### Dependências:
- PyQt6 (QWebEngineView)
- JSON para persistência
- HTML/CSS/JavaScript para interface

### Compatibilidade:
- Windows 10/11
- Python 3.8+
- Resolução mínima: 1024x768

## 🔧 Manutenção

### Backup:
Os arquivos de prescrição ficam em:
`Documentos_Pacientes/{paciente_id}/prescricoes/`

### Personalização:
- Editar `templates/prescricao_medica.html` para layout
- Modificar `prescricao_medica_widget.py` para funcionalidades
- Adicionar templates em `templates/prescricao/`

---

**Data de Implementação**: 27/08/2025  
**Versão**: 1.0  
**Autor**: Sistema Biodesk
