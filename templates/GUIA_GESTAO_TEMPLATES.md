# 📖 GUIA DE GESTÃO DE TEMPLATES BIODESK

## 🎯 Como Usar Este Sistema

### 1. **ESTRUTURA DE PASTAS**
```
templates/
├── orientacoes/          # Protocolos terapêuticos
│   ├── imagens/         # Imagens para orientações
│   └── *.txt + *_meta.json
├── exercicios/          # Programas de exercícios
│   ├── imagens/         # Fotos de alongamentos/exercícios
│   └── *.txt + *_meta.json
├── suplementos/         # Protocolos de suplementação
├── dietas/              # Planos alimentares
├── seguimento/          # Consultas de seguimento
├── exames/              # Requisições
└── outros/              # Outros protocolos
```

### 2. **COMO CRIAR UM NOVO TEMPLATE**

#### Passo 1: Escolher a Categoria
- `orientacoes` - Para protocolos terapêuticos gerais
- `exercicios` - Para programas de movimento/alongamentos
- `suplementos` - Para prescrições vitamínicas
- `dietas` - Para planos alimentares
- `seguimento` - Para consultas de revisão
- `exames` - Para requisições laboratoriais

#### Passo 2: Copiar Template Base
1. Vá para `templates/[categoria]/`
2. Copie um template exemplo (ex: `protocolo_detox_personalizado.txt`)
3. Renomeie para o seu novo template
4. Copie também o arquivo `*_meta.json` e renomeie

#### Passo 3: Editar Conteúdo
1. Abra o arquivo `.txt`
2. **COLE SEU CONTEÚDO** nas seções marcadas com `[COLE AQUI...]`
3. Mantenha as variáveis `{{nome_paciente}}`, `{{data_hoje}}`, etc.

#### Passo 4: Adicionar Imagens (Opcional)
1. Coloque as imagens na pasta `templates/[categoria]/imagens/`
2. Use `{{imagem_1}}`, `{{imagem_2}}`, etc. no template
3. Nomes recomendados: `exercicio1.jpg`, `alongamento1.png`

### 3. **VARIÁVEIS DISPONÍVEIS**

#### **📊 Dados do Paciente**
- `{{nome_paciente}}` - Nome completo
- `{{idade_paciente}}` - Idade atual
- `{{telefone_paciente}}` - Contacto

#### **📅 Data e Hora**
- `{{data_hoje}}` - Data atual (14/08/2025)
- `{{hora_atual}}` - Hora atual (15:30)
- `{{saudacao}}` - Bom dia/Boa tarde/Boa noite
- `{{proxima_consulta}}` - Data da próxima consulta

#### **👨‍⚕️ Profissional**
- `{{nome_profissional}}` - Seu nome
- `{{especialidade_profissional}}` - Sua especialidade
- `{{email_profissional}}` - Seu email

#### **🏥 Clínica**
- `{{nome_clinica}}` - Nome da clínica
- `{{telefone_clinica}}` - Telefone principal
- `{{email_clinica}}` - Email da clínica

#### **🖼️ Imagens**
- `{{imagem_1}}`, `{{imagem_2}}`, `{{imagem_3}}` - Imagens de referência

### 4. **EXEMPLOS PRÁTICOS**

#### **Template de Exercícios:**
```
## 🏃‍♂️ PROGRAMA DE ALONGAMENTOS

**Paciente:** {{nome_paciente}}
**Data:** {{data_hoje}}

### Exercício 1: Alongamento Cervical
{{imagem_1}}
- Duração: 30 segundos
- Repetições: 3x

### Exercício 2: Alongamento Lombar  
{{imagem_2}}
- Duração: 45 segundos
- Repetições: 2x
```

#### **Template de Dieta:**
```
## 🥗 PLANO ALIMENTAR ANTI-INFLAMATÓRIO

**Paciente:** {{nome_paciente}}
**Início:** {{data_hoje}}

### Pequeno-almoço (8h00)
- Aveia com frutos vermelhos
- Chá verde

### Lanche (10h30)
- Frutos secos (30g)
```

### 5. **DICAS IMPORTANTES**

✅ **Sempre mantenha** as variáveis `{{}}` para autopreenchimento
✅ **Use títulos claros** com emojis para melhor visualização  
✅ **Organize imagens** na pasta correspondente
✅ **Teste sempre** o template no sistema antes de usar
✅ **Faça backup** dos templates personalizados

### 6. **RESOLUÇÃO DE PROBLEMAS**

❌ **Template não aparece no sistema?**
- Verifique se está na pasta correta
- Confirme se tem arquivo `.txt` e `_meta.json`

❌ **Variáveis não funcionam?**
- Use exatamente `{{nome_variavel}}`
- Sem espaços dentro das chaves

❌ **Imagens não aparecem?**
- Coloque na pasta `templates/[categoria]/imagens/`
- Use nomes simples (sem espaços especiais)

---
**Sistema criado em:** 14/08/2025
**Versão:** 1.0 - Nuno Correia Biodesk
