"""
Biodesk - Email Service
=======================

Serviço para gestão de emails e comunicação.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Validação de emails
- Formatação de destinatários
- Integração com dados de pacientes
- Templates de email

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

import re
from typing import Optional, Dict, Any, List


class EmailService:
    """Serviço para gestão de emails e comunicação"""
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """
        Valida se o email tem formato correto
        
        Args:
            email: Email a validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not email or not isinstance(email, str):
            return False
        
        # Padrão básico de validação de email
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(padrao, email.strip()) is not None
    
    @staticmethod
    def formatar_destinatario(paciente_data: Dict[str, Any]) -> Optional[str]:
        """
        Extrai e valida o email do paciente
        
        Args:
            paciente_data: Dados do paciente
            
        Returns:
            Email formatado ou None se inválido
        """
        if not paciente_data:
            return None
        
        email = paciente_data.get('email', '').strip()
        
        if EmailService.validar_email(email):
            return email
        
        return None
    
    @staticmethod
    def gerar_assunto_automatico(tipo_documento: str, nome_paciente: str = "") -> str:
        """
        Gera assunto automático para emails
        
        Args:
            tipo_documento: Tipo do documento (consentimento, declaração, etc.)
            nome_paciente: Nome do paciente (opcional)
            
        Returns:
            Assunto formatado
        """
        if nome_paciente:
            return f"Biodesk - {tipo_documento.title()} - {nome_paciente}"
        else:
            return f"Biodesk - {tipo_documento.title()}"
    
    @staticmethod
    def gerar_corpo_email_padrao(tipo_documento: str, nome_paciente: str = "") -> str:
        """
        Gera corpo de email padrão
        
        Args:
            tipo_documento: Tipo do documento
            nome_paciente: Nome do paciente (opcional)
            
        Returns:
            Corpo do email formatado
        """
        saudacao = f"Caro(a) {nome_paciente}," if nome_paciente else "Caro(a) Paciente,"
        
        corpo = f"""{saudacao}

Segue em anexo o seu {tipo_documento.lower()} solicitado.

Se tiver alguma dúvida, não hesite em contactar-nos.

Cumprimentos,
Equipa Biodesk"""
        
        return corpo
    
    @staticmethod
    def extrair_emails_multiplos(texto: str) -> List[str]:
        """
        Extrai múltiplos emails de um texto
        
        Args:
            texto: Texto contendo emails
            
        Returns:
            Lista de emails válidos encontrados
        """
        if not texto:
            return []
        
        # Padrão para encontrar emails
        padrao = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails_encontrados = re.findall(padrao, texto)
        
        # Validar cada email encontrado
        emails_validos = []
        for email in emails_encontrados:
            if EmailService.validar_email(email):
                emails_validos.append(email.lower())
        
        # Remover duplicados mantendo ordem
        emails_unicos = list(dict.fromkeys(emails_validos))
        
        return emails_unicos
    
    @staticmethod
    def sanitizar_assunto(assunto: str) -> str:
        """
        Remove caracteres problemáticos do assunto
        
        Args:
            assunto: Assunto original
            
        Returns:
            Assunto sanitizado
        """
        if not assunto:
            return "Mensagem do Biodesk"
        
        # Remover caracteres problemáticos
        assunto = re.sub(r'[^\w\s\-\.\(\)àáâãäèéêëìíîïòóôõöùúûüç]', '', assunto, flags=re.IGNORECASE)
        
        # Limitar tamanho
        if len(assunto) > 78:  # RFC recomenda max 78 caracteres
            assunto = assunto[:75] + "..."
        
        return assunto.strip() or "Mensagem do Biodesk"
    
    @staticmethod
    def preparar_dados_email(paciente_data: Dict[str, Any], 
                           tipo_documento: str = "documento",
                           assunto_personalizado: str = "",
                           corpo_personalizado: str = "") -> Dict[str, str]:
        """
        Prepara todos os dados necessários para envio de email
        
        Args:
            paciente_data: Dados do paciente
            tipo_documento: Tipo do documento
            assunto_personalizado: Assunto personalizado (opcional)
            corpo_personalizado: Corpo personalizado (opcional)
            
        Returns:
            Dicionário com dados do email preparados
        """
        nome_paciente = paciente_data.get('nome', '') if paciente_data else ''
        destinatario = EmailService.formatar_destinatario(paciente_data)
        
        # Usar assunto personalizado ou gerar automático
        if assunto_personalizado:
            assunto = EmailService.sanitizar_assunto(assunto_personalizado)
        else:
            assunto = EmailService.gerar_assunto_automatico(tipo_documento, nome_paciente)
        
        # Usar corpo personalizado ou gerar automático
        if corpo_personalizado:
            corpo = corpo_personalizado
        else:
            corpo = EmailService.gerar_corpo_email_padrao(tipo_documento, nome_paciente)
        
        return {
            'destinatario': destinatario or '',
            'assunto': assunto,
            'corpo': corpo,
            'valido': bool(destinatario)
        }
