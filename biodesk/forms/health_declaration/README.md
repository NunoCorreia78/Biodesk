# Sistema de Declarações de Saúde - Biodesk

Sistema completo para gestão de declarações de estado de saúde de pacientes, desenvolvido para a plataforma Biodesk de Terapia Quântica.

## 📋 Funcionalidades Principais

### ✅ **Formulários Dinâmicos**
- Interface gráfica responsiva com PyQt6
- Campos condicionais baseados em lógica `show_if`
- Validação em tempo real
- Suporte a múltiplos tipos de campo:
  - Texto, TextArea, Data, Número
  - Checkbox, Radio, Select, MultiSelect
  - Assinatura digital, Upload de arquivos
  - Escalas de avaliação (0-10)

### ✅ **Validação Inteligente**
- Campos obrigatórios
- Contraindicações críticas automáticas
- Validação de consentimentos obrigatórios
- Padrões regex personalizados

### ✅ **Exportação PDF Profissional**
- Documentos formatados com ReportLab
- Layout médico profissional
- Assinaturas digitais integradas
- Metadados e trilha de auditoria
- Fallback para QtPrintSupport

### ✅ **Conformidade Legal**
- Avisos legais automáticos
- Termos de consentimento
- Hash de integridade do documento
- Timestamp de submissão

## 🏗️ Arquitetura do Sistema

```
biodesk/forms/health_declaration/
├── form_spec.json          # Especificação do formulário médico
├── renderer.py             # Sistema de renderização PyQt6
├── export_pdf.py          # Geração de PDFs profissionais
├── demo.py                # Demonstração completa do sistema
├── __init__.py            # Módulo principal
└── README.md              # Esta documentação
```

### **Componentes Principais**

1. **`HealthDeclarationRenderer`** - Interface gráfica principal
2. **`FieldRenderer`** - Renderização de campos individuais
3. **`FormValidator`** - Sistema de validação avançado
4. **`HealthDeclarationPDFExporter`** - Exportação para PDF
5. **`SignatureWidget`** - Captura de assinaturas digitais

## 🚀 Início Rápido

### Pré-requisitos
```bash
pip install PyQt6>=6.0.0
pip install reportlab>=3.6.0  # Opcional, para PDFs avançados
```

### Exemplo Básico
```python
from pathlib import Path
from biodesk.forms.health_declaration import create_health_declaration_system

# Criar sistema completo
form_spec_path = Path("form_spec.json")
renderer, exporter = create_health_declaration_system(form_spec_path)

# Mostrar formulário
renderer.show()

# Conectar evento de conclusão
def on_form_completed(form_data):
    # Exportar para PDF automaticamente
    exporter.export_declaration(
        form_data=form_data,
        form_spec_path=form_spec_path,
        output_path=Path("declaracao.pdf")
    )

renderer.form_completed.connect(on_form_completed)
```

### Executar Demonstração
```bash
cd biodesk/forms/health_declaration
python demo.py
```

## 📝 Especificação do Formulário

O arquivo `form_spec.json` define a estrutura completa do formulário:

```json
{
  "form_spec": {
    "title": "Declaração de Estado de Saúde",
    "version": "1.0",
    "sections": [
      {
        "id": "dados_pessoais",
        "title": "Dados Pessoais",
        "fields": [
          {
            "id": "nome_completo",
            "type": "text",
            "label": "Nome Completo",
            "required": true,
            "maxLength": 100
          }
        ]
      }
    ],
    "validation_rules": {
      "critical_contraindications": {
        "fields": ["doencas_cronicas", "dispositivos_implantados"],
        "blocking_values": {
          "doencas_cronicas": ["Epilepsia", "Pacemaker", "Gravidez"],
          "dispositivos_implantados": ["Pacemaker", "Desfibrilhador"]
        }
      }
    }
  }
}
```

## 🎯 Tipos de Campo Suportados

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `text` | Campo de texto simples | Nome, telefone |
| `textarea` | Texto multilinha | Observações médicas |
| `date` | Seletor de data | Data de nascimento |
| `number` | Campo numérico | Idade, peso |
| `checkbox` | Checkbox simples ou múltipla | Aceitar termos |
| `radio` | Seleção única | Género (M/F) |
| `select` | Lista suspensa | País de origem |
| `multiselect` | Seleção múltipla | Doenças crónicas |
| `signature` | Assinatura digital | Consentimento |
| `file` | Upload de arquivo | Exames médicos |
| `rating` | Escala de avaliação | Nível de dor (0-10) |

## ⚡ Funcionalidades Avançadas

### **Campos Condicionais**
```json
{
  "id": "detalhes_gravidez",
  "type": "textarea",
  "label": "Detalhes da Gravidez",
  "show_if": {
    "field": "gravidez_atual",
    "value": true
  }
}
```

### **Validação Crítica**
O sistema detecta automaticamente contraindicações que impedem o tratamento:
- Epilepsia ativa
- Dispositivos implantados (pacemaker, desfibrilhador)
- Gravidez (dependendo do protocolo)
- Transtornos cardíacos graves

### **Assinatura Digital**
- Captura por mouse/touch
- Validação de presença obrigatória
- Integração no PDF final
- Conversão para base64 para armazenamento

## 📄 Geração de PDFs

### **Estrutura do Documento**
1. **Cabeçalho** - Logo da clínica, título, data
2. **Seções de Dados** - Tabelas organizadas por seção
3. **Assinatura** - Área dedicada com declaração legal
4. **Rodapé Legal** - Termos, condições e metadados

### **Metadados Incluídos**
- Hash MD5 do documento para integridade
- Timestamp de geração
- Versão do formulário utilizada
- IP e user agent (se aplicável)
- ID único do documento

### **Exemplo de Exportação**
```python
# Exportar com assinatura
exporter = HealthDeclarationPDFExporter()
success = exporter.export_declaration(
    form_data=patient_data,
    form_spec_path=Path("form_spec.json"),
    output_path=Path("declaracao_joao_silva.pdf"),
    signature_data=signature_points,
    include_timestamp=True
)
```

## 🔒 Conformidade e Segurança

### **Proteção de Dados**
- Validação de entrada rigorosa
- Sanitização de dados antes do PDF
- Hash de integridade para detecção de alterações

### **Conformidade Legal**
- Avisos obrigatórios sobre contraindicações
- Termos de consentimento explícitos
- Declaração de responsabilidade do paciente
- Trilha de auditoria completa

### **Contraindicações Críticas**
Sistema implementa bloqueio automático para:
- **Epilepsia**: Risco de convulsões induzidas
- **Dispositivos Cardíacos**: Interferência com pacemakers/desfibrilhadores
- **Gravidez**: Proteção materno-fetal
- **Condições Cardíagas Graves**: Arritmias, insuficiência cardíaca severa

## 🧪 Testes e Validação

### **Executar Testes**
```bash
python demo.py
# Selecionar "Testar Validação" na interface
```

### **Cenários de Teste**
1. **Dados Válidos** - Formulário completo sem contraindicações
2. **Contraindicações** - Detecção de condições bloqueantes
3. **Campos Obrigatórios** - Validação de preenchimento
4. **Consentimentos** - Verificação de aceites obrigatórios

## 🛠️ Desenvolvimento e Extensão

### **Adicionar Novo Tipo de Campo**
1. Implementar em `FieldRenderer._create_[tipo]_field()`
2. Adicionar lógica de coleta em `_collect_form_data()`
3. Implementar formatação em `PDFGenerator._format_field_value()`

### **Personalizar Validação**
```python
class CustomValidator(FormValidator):
    def _validate_custom_rule(self, form_data, errors):
        # Sua lógica personalizada
        pass
```

### **Styling Personalizado**
- Modificar estilos CSS em `renderer.py`
- Customizar layout PDF em `export_pdf.py`
- Ajustar cores e fontes conforme marca

## 📊 Integração com Biodesk

### **Integração com Terapia Quântica**
```python
# No módulo principal de terapia
from biodesk.forms.health_declaration import HealthDeclarationRenderer

class TherapyMainWindow:
    def before_therapy_start(self):
        # Exigir declaração de saúde
        declaration = HealthDeclarationRenderer(self.form_spec_path)
        declaration.form_completed.connect(self.on_health_declaration_complete)
        declaration.show()
    
    def on_health_declaration_complete(self, form_data):
        if self.has_contraindications(form_data):
            self.block_therapy("Contraindicações detectadas")
        else:
            self.proceed_with_therapy()
```

### **Armazenamento de Dados**
- Dados sensíveis apenas em PDF local
- Metadados não-sensíveis no banco de dados
- Hash do documento para referência

## 🐛 Solução de Problemas

### **Erro: ReportLab não encontrado**
```bash
pip install reportlab
# Ou use funcionalidade limitada com QtPrintSupport
```

### **Problema: Assinatura não aparece no PDF**
- Verificar se `signature_data` não está vazio
- Confirmar formato correto dos pontos de assinatura
- Testar com dados de exemplo

### **Interface não responsiva**
- Verificar versão do PyQt6 (>=6.0.0)
- Testar com resolução de tela diferente
- Verificar aplicação de estilos CSS

## 📈 Roadmap Futuro

- [ ] **Campos Avançados**: Upload múltiplo, câmera para fotos
- [ ] **Integração Digital**: Assinatura com certificado digital
- [ ] **Multi-idioma**: Suporte português/inglês/espanhol
- [ ] **Offline Mode**: Funcionamento sem internet
- [ ] **Backup Automático**: Sincronização com cloud
- [ ] **Relatórios**: Dashboard de declarações submetidas

## 🤝 Contribuição

Para contribuir com o desenvolvimento:

1. **Fork** o repositório
2. **Criar** branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. **Push** para o branch (`git push origin feature/nova-funcionalidade`)
5. **Criar** Pull Request

## 📄 Licença

Este software é propriedade da **Biodesk** e destina-se exclusivamente ao uso interno da plataforma de Terapia Quântica.

---

## 💬 Suporte

Para suporte técnico ou dúvidas:
- **Email**: suporte@biodesk.com
- **Documentação**: `/docs/health_declarations/`
- **Issues**: Sistema interno de tickets

**Desenvolvido com ❤️ pela equipe Biodesk**
