# 📧 Sistema de Email - Biodesk

## Visão Geral

O novo sistema de comunicação do Biodesk é **exclusivamente por email**, proporcionando uma forma profissional e confiável de comunicar com os pacientes.

## 🎯 Funcionalidades

### ✅ **O que TEMOS:**
- 📧 **Envio de emails individual e em massa**
- 🎨 **Templates profissionais personalizáveis**
- ⚙️ **Configuração completa de SMTP**
- 📊 **Histórico e estatísticas detalhadas**
- 🔒 **Modo simulação para testes**
- 📝 **Assinaturas automáticas**
- 📋 **Suporte a CSV para envio em massa**

### ❌ **O que REMOVEMOS:**
- ~~WhatsApp~~
- ~~SMS~~
- ~~Toda a complexidade Node.js~~

## 🚀 Como Usar

### 1. **Configuração Inicial**

1. Abra o **Centro de Comunicação**
2. Clique em **"⚙️ Configurar Email"**
3. Configure os dados:
   - **Servidor SMTP** (ex: smtp.gmail.com)
   - **Email e senha** (use App Password para Gmail)
   - **Dados da clínica**
   - **Assinatura personalizada**

### 2. **Para Gmail (Recomendado)**

1. **Ative autenticação de 2 fatores** na sua conta Google
2. Vá a **Google Account → Segurança → App passwords**
3. Gere uma **App Password** para "Email"
4. Use essa senha no Biodesk (não a senha normal)

### 3. **Envio Individual**

1. Na aba **"📤 Envio Rápido"**:
   - Preencha nome, email e mensagem
   - Use templates prontos ou personalize
   - Clique **"🚀 Enviar Mensagem"**

### 4. **Envio em Massa**

1. Prepare um **CSV** com colunas:
   ```csv
   nome,email,telefone
   João Silva,joao@email.com,+351912345678
   ```

2. Na aba **"📋 Envio em Massa"**:
   - Selecione o arquivo CSV
   - Defina assunto e mensagem
   - Escolha entre **modo simulação** ou **envio real**
   - Clique **"🚀 Processar Envios"**

## 📝 Templates Disponíveis

### 📅 **Lembrete de Consulta**
- Assunto: "Lembrete de Consulta - {nome}"
- Inclui data, hora, médico e instruções

### 📋 **Resultado de Exame**
- Assunto: "Resultados de Exame Disponíveis - {nome}"
- Instruções para recolha e marcação de consulta

### 👋 **Boas-vindas**
- Assunto: "Bem-vindo(a) à {nome_clinica} - {nome}"
- Informações completas da clínica e dicas importantes

## 🔧 Configurações SMTP Comuns

### **Gmail:**
- Servidor: `smtp.gmail.com`
- Porta: `587`
- TLS: ✅ Ativado
- Email: `seu.email@gmail.com`
- Senha: `App Password` (16 caracteres)

### **Outlook/Hotmail:**
- Servidor: `smtp.office365.com`
- Porta: `587`
- TLS: ✅ Ativado

### **Yahoo:**
- Servidor: `smtp.mail.yahoo.com`
- Porta: `587` ou `465`
- TLS: ✅ Ativado

## 💡 Dicas Importantes

### ✅ **Boas Práticas:**
- Use sempre o **modo simulação** para testar
- Teste a configuração SMTP antes do primeiro envio
- Personalize os templates com dados da sua clínica
- Mantenha uma lista de emails atualizada

### ⚠️ **Evitar:**
- Envios excessivos (pode ser considerado spam)
- Emails sem assunto claro
- Mensagens muito longas
- Usar senha normal do Gmail (use App Password)

### 🔒 **Segurança:**
- Use App Passwords em vez de senhas normais
- Mantenha as credenciais seguras
- Verifique sempre os destinatários antes do envio

## 📊 Monitorização

### **Histórico:**
- Visualize todos os envios realizados
- Estatísticas de sucessos e erros
- Data e hora de cada envio

### **Estados dos Emails:**
- ✅ **Enviado** - Email enviado com sucesso
- ❌ **Erro** - Falha no envio
- 🔄 **Simulado** - Teste realizado

## 🆘 Resolução de Problemas

### **"Erro de autenticação"**
- Verifique email e senha
- Para Gmail, use App Password
- Confirme se 2FA está ativo

### **"Servidor SMTP não encontrado"**
- Verifique configurações do servidor
- Confirme porta e TLS
- Teste conexão à internet

### **"Email não configurado"**
- Clique em "⚙️ Configurar Email"
- Preencha todos os campos obrigatórios
- Teste a configuração

### **CSV não carrega**
- Verifique formato: `nome,email,telefone`
- Confirme codificação UTF-8
- Remova caracteres especiais

## 📈 Vantagens do Novo Sistema

### ✅ **Simplicidade:**
- Uma única forma de comunicação
- Configuração simples e direta
- Interface limpa e intuitiva

### ✅ **Profissionalismo:**
- Emails sempre bem formatados
- Assinaturas personalizadas
- Templates profissionais

### ✅ **Confiabilidade:**
- Sem dependências externas complexas
- Funciona com qualquer provedor SMTP
- Histórico completo de envios

### ✅ **Segurança:**
- Protocolo SMTP padrão da indústria
- Suporte a TLS/SSL
- Controlo total sobre os dados

---

## 🎉 Conclusão

O novo sistema de email do Biodesk é **simples, profissional e eficaz**. 

**Menos complexidade, mais resultados!** 📧✨
