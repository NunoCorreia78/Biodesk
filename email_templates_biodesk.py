"""
Sistema de Templates de Email Personalizados - Biodesk
Gera textos de email personalizados com redes sociais e introdução generalista
"""

from datetime import datetime


def gerar_email_personalizado(nome_paciente, templates_anexados=None, tipo_comunicacao="templates"):
    """
    Gera email personalizado com introdução generalista e redes sociais
    
    Args:
        nome_paciente (str): Nome do paciente
        templates_anexados (list): Lista de nomes dos templates anexados
        tipo_comunicacao (str): Tipo de comunicação ("templates", "documento_word", "resultado_exame", etc.)
    
    Returns:
        dict: Contém 'assunto' e 'corpo' do email
    """
    
    # Dados profissionais
    dados_profissional = {
        "nome": "Nuno Correia",
        "especialidade": "Naturopatia • Osteopatia • Medicina Quântica",
        "clinica": "Nuno Correia - Terapias Naturais",
        "telefone": "+351 964 860 387",
        "email": "nunocorreiaterapiasnaturais@gmail.com",
        "instagram": "@nunocorreia.naturopata",
        "facebook": "@NunoCorreiaTerapiasNaturais",
        "data_atual": datetime.now().strftime("%d/%m/%Y")
    }
    
    # Assuntos personalizados
    assuntos = {
        "templates": f"Documentação Personalizada - {nome_paciente}",
        "documento_word": f"Documento Personalizado - {nome_paciente}",
        "resultado_exame": f"Resultados e Orientações - {nome_paciente}",
        "seguimento": f"Seguimento de Consulta - {nome_paciente}",
        "protocolo": f"Protocolo de Tratamento - {nome_paciente}"
    }
    
    # Saudação personalizada baseada na hora
    hora_atual = datetime.now().hour
    if 6 <= hora_atual < 12:
        saudacao = "Bom dia"
    elif 12 <= hora_atual < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    # Corpo do email base
    corpo_base = f"""{saudacao}, {nome_paciente}!

Espero que se encontre bem e com boa saúde.

"""
    
    # Conteúdo específico baseado no tipo
    if tipo_comunicacao == "templates" and templates_anexados:
        if len(templates_anexados) == 1:
            corpo_conteudo = f"""Conforme conversado na nossa consulta, envio em anexo a documentação personalizada para o seu plano de tratamento.

📄 **Documento anexado:**
• {templates_anexados[0]}

Este material foi preparado especificamente para si, tendo em conta as suas necessidades individuais e os objetivos terapêuticos definidos."""
        else:
            lista_templates = "\n".join([f"• {template}" for template in templates_anexados])
            corpo_conteudo = f"""Conforme conversado na nossa consulta, envio em anexo a documentação personalizada para o seu plano de tratamento.

📄 **Documentos anexados:**
{lista_templates}

Este material foi preparado especificamente para si, tendo em conta as suas necessidades individuais e os objetivos terapêuticos definidos."""
    
    elif tipo_comunicacao == "documento_word":
        corpo_conteudo = """Conforme conversado na nossa consulta, envio em anexo o documento personalizado que preparei especificamente para o seu caso.

📋 **Sobre este documento:**
• Criado com base na nossa análise detalhada
• Orientações personalizadas para as suas necessidades
• Plano de ação adaptado aos seus objetivos de saúde

Este material foi desenvolvido tendo em conta as suas características individuais e os resultados da nossa avaliação."""
    
    else:
        corpo_conteudo = """Conforme conversado na nossa consulta, envio em anexo a documentação personalizada para apoiar o seu processo de recuperação e bem-estar.

📋 **Informações importantes:**
• Todo o material foi preparado especificamente para si
• Siga as orientações de acordo com o cronograma sugerido
• Este plano pode ser ajustado conforme a sua evolução"""
    
    # Instruções de seguimento
    corpo_instrucoes = """

🎯 **Recomendações gerais:**
• Leia toda a documentação com atenção
• Siga as orientações de forma consistente
• Registe a sua evolução e sintomas (se aplicável)
• Mantenha uma alimentação equilibrada e hidratação adequada

📞 **Qualquer dúvida, não hesite em contactar-me:**
Estou sempre disponível para esclarecer qualquer questão ou ajustar o plano conforme necessário. O seu bem-estar e progresso são a minha prioridade."""
    
    # Rodapé com redes sociais e assinatura
    corpo_rodape = f"""

Com os melhores cumprimentos e votos de uma excelente recuperação,

**{dados_profissional['nome']}**
{dados_profissional['especialidade']}

---
🏥 **{dados_profissional['clinica']}**
📞 {dados_profissional['telefone']}
📧 {dados_profissional['email']}

📱 **Siga-me nas redes sociais:**
📸 Instagram: {dados_profissional['instagram']}
👥 Facebook: {dados_profissional['facebook']}

💚 *"Saúde Integral através da Medicina Natural"*"""
    
    # Montar email completo
    corpo_completo = corpo_base + corpo_conteudo + corpo_instrucoes + corpo_rodape
    
    return {
        "assunto": assuntos.get(tipo_comunicacao, f"Comunicação Importante - {nome_paciente}"),
        "corpo": corpo_completo
    }


def gerar_email_editor_avancado(nome_paciente, nome_documento):
    """
    Gera email específico para documentos criados no Editor Avançado
    """
    return gerar_email_personalizado(
        nome_paciente=nome_paciente,
        templates_anexados=[nome_documento],
        tipo_comunicacao="documento_word"
    )


def gerar_email_multiplos_templates(nome_paciente, lista_templates):
    """
    Gera email para envio de múltiplos templates
    """
    return gerar_email_personalizado(
        nome_paciente=nome_paciente,
        templates_anexados=lista_templates,
        tipo_comunicacao="templates"
    )


def gerar_email_followup(nome_paciente, tipo_followup="padrao", dias_apos=3):
    """
    Gera emails de follow-up automático após consulta
    
    Args:
        nome_paciente (str): Nome do paciente
        tipo_followup (str): Tipo de follow-up ("padrao", "primeira_consulta", "tratamento", "resultado")
        dias_apos (int): Número de dias após a consulta
    
    Returns:
        dict: Contém 'assunto' e 'corpo' do email
    """
    
    # Dados profissionais
    dados_profissional = {
        "nome": "Nuno Correia",
        "especialidade": "Naturopatia • Osteopatia • Medicina Quântica",
        "clinica": "Nuno Correia - Terapias Naturais",
        "telefone": "+351 964 860 387",
        "email": "nunocorreiaterapiasnaturais@gmail.com",
        "instagram": "@nunocorreia.naturopata",
        "facebook": "@NunoCorreiaTerapiasNaturais",
        "data_atual": datetime.now().strftime("%d/%m/%Y")
    }
    
    # Saudação personalizada baseada na hora
    hora_atual = datetime.now().hour
    if 6 <= hora_atual < 12:
        saudacao = "Bom dia"
    elif 12 <= hora_atual < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    # Assuntos personalizados
    assuntos = {
        "padrao": f"Acompanhamento de Consulta - {nome_paciente}",
        "primeira_consulta": f"Como se sente após a nossa primeira consulta? - {nome_paciente}",
        "tratamento": f"Acompanhamento do Tratamento - {nome_paciente}",
        "resultado": f"Evolução e Próximos Passos - {nome_paciente}"
    }
    
    # Corpo base
    corpo_base = f"""{saudacao}, {nome_paciente}!

Espero que se encontre bem e com boa saúde.

"""
    
    # Conteúdo específico por tipo de follow-up
    if tipo_followup == "primeira_consulta":
        corpo_conteudo = f"""Passou algum tempo desde a nossa primeira consulta e gostaria de saber como se tem sentido.

🌟 **Como está a correr?**
• Como se sente desde a nossa consulta?
• Tem seguido as orientações que conversámos?
• Notou alguma melhoria ou mudança?
• Surgiu alguma dúvida ou dificuldade?

É completamente normal que nas primeiras semanas possa sentir algumas mudanças no seu organismo - isto faz parte do processo natural de reequilíbrio. O importante é manter a consistência e dar tempo ao seu corpo para se adaptar."""
        
    elif tipo_followup == "tratamento":
        corpo_conteudo = f"""Passou algum tempo desde a nossa última consulta e é importante acompanhar a sua evolução no tratamento.

📊 **Vamos fazer um ponto da situação:**
• Como tem evoluído os sintomas principais?
• Tem conseguido seguir o plano terapêutico?
• Alguma melhoria significativa que gostaria de partilhar?
• Precisa de algum ajuste ou esclarecimento adicional?

Lembre-se que cada pessoa responde de forma única ao tratamento. A sua experiência e feedback são fundamentais para otimizarmos o seu plano de recuperação."""
        
    elif tipo_followup == "resultado":
        corpo_conteudo = f"""Espero que tenha tido tempo para implementar as recomendações da nossa consulta.

🎯 **Próximos Passos:**
• Como se sente em relação aos objetivos definidos?
• Conseguiu implementar as mudanças sugeridas?
• Gostaria de agendar uma consulta de seguimento?
• Tem alguma questão específica que gostaria de abordar?

O seu comprometimento com o processo é fundamental para alcançarmos os melhores resultados. Estou aqui para apoiá-lo em cada etapa desta jornada."""
        
    else:  # padrao
        corpo_conteudo = f"""Passou algum tempo desde a nossa consulta e gostaria de saber como tem evoluído.

💚 **Acompanhamento da sua saúde:**
• Como se tem sentido desde a nossa última conversa?
• Tem conseguido seguir as orientações combinadas?
• Notou alguma melhoria ou mudança positiva?
• Precisa de algum esclarecimento adicional?

O seu bem-estar é a minha prioridade e é importante mantermos este acompanhamento próximo para garantir que está no caminho certo para uma saúde plena."""
    
    # Instruções gerais
    corpo_instrucoes = """

📞 **Como pode responder:**
• Responda diretamente a este email com as suas impressões
• Ligue-me se preferir uma conversa mais detalhada
• Marque uma consulta de seguimento se sentir necessidade

🌱 **Lembre-se:**
A recuperação é um processo e cada pequeno progresso é uma vitória. Não hesite em partilhar tanto as melhorias como as dificuldades - tudo faz parte do caminho para o seu bem-estar integral.

Qualquer dúvida, por menor que seja, não hesite em contactar-me. Estou aqui para apoiá-lo em cada passo desta jornada."""
    
    # Rodapé com redes sociais
    corpo_rodape = f"""

Com os melhores cumprimentos e votos de excelente saúde,

**{dados_profissional['nome']}**
{dados_profissional['especialidade']}

---
🏥 **{dados_profissional['clinica']}**
📞 {dados_profissional['telefone']}
📧 {dados_profissional['email']}

📱 **Siga-me nas redes sociais:**
📸 Instagram: {dados_profissional['instagram']}
👥 Facebook: {dados_profissional['facebook']}

💚 *"Saúde Integral através da Medicina Natural"*"""
    
    # Montar email completo
    corpo_completo = corpo_base + corpo_conteudo + corpo_instrucoes + corpo_rodape
    
    return {
        "assunto": assuntos.get(tipo_followup, f"Acompanhamento - {nome_paciente}"),
        "corpo": corpo_completo
    }


# Função de teste
if __name__ == "__main__":
    # Testar os templates
    print("=" * 60)
    print("TESTE - EMAIL TEMPLATE ÚNICO")
    print("=" * 60)
    
    email1 = gerar_email_personalizado("João Silva", ["Protocolo Detox Hepático"])
    print(f"Assunto: {email1['assunto']}")
    print(f"\n{email1['corpo']}")
    
    print("\n" + "=" * 60)
    print("TESTE - EMAIL MÚLTIPLOS TEMPLATES")
    print("=" * 60)
    
    email2 = gerar_email_multiplos_templates("Maria Santos", [
        "Plano Alimentar Personalizado",
        "Protocolo de Exercícios",
        "Suplementação Específica"
    ])
    print(f"Assunto: {email2['assunto']}")
    print(f"\n{email2['corpo']}")
    
    print("\n" + "=" * 60)
    print("TESTE - EMAIL FOLLOW-UP PRIMEIRA CONSULTA")
    print("=" * 60)
    
    email3 = gerar_email_followup("Ana Costa", "primeira_consulta", 3)
    print(f"Assunto: {email3['assunto']}")
    print(f"\n{email3['corpo']}")
    
    print("\n" + "=" * 60)
    print("TESTE - EMAIL FOLLOW-UP TRATAMENTO")
    print("=" * 60)
    
    email4 = gerar_email_followup("Carlos Mendes", "tratamento", 7)
    print(f"Assunto: {email4['assunto']}")
    print(f"\n{email4['corpo']}")
