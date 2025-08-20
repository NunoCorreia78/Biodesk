#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Envio de Email para Biodesk
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Tuple, Optional
import logging
from email_config import email_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    """Sistema de envio de emails"""
    
    def __init__(self):
        self.config = email_config
    
    def test_connection(self) -> Tuple[bool, str]:
        """Testa conexão com o servidor SMTP"""
        if not self.config.is_configured():
            return False, "Email e senha não configurados"
        
        try:
            smtp_config = self.config.get_smtp_config()
            
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
                if smtp_config["use_tls"]:
                    server.starttls()
                server.login(smtp_config["email"], smtp_config["password"])
                
            return True, "Conexão SMTP bem-sucedida"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Erro de autenticação - verifique email e senha"
        except smtplib.SMTPException as e:
            return False, f"Erro SMTP: {str(e)}"
        except Exception as e:
            return False, f"Erro de conexão: {str(e)}"
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   nome_destinatario: str = "") -> Tuple[bool, str]:
        """Envia um email"""
        
        if not self.config.is_configured():
            return False, "Email não configurado"
        
        try:
            smtp_config = self.config.get_smtp_config()
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = smtp_config["email"]
            msg['To'] = to_email
            msg['Subject'] = self.config.format_template(subject, nome_destinatario)
            
            # Formatar corpo do email
            body_formatted = self.config.format_template(body, nome_destinatario)
            
            # Adicionar assinatura se não estiver presente
            if not any(keyword in body_formatted.lower() for keyword in ["cumprimentos", "atenciosamente", "equipa"]):
                assinatura = self.config.format_template(self.config.get("assinatura"), nome_destinatario)
                body_formatted += "\n\n" + assinatura
            
            msg.attach(MIMEText(body_formatted, 'plain', 'utf-8'))
            
            # Enviar email
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
                if smtp_config["use_tls"]:
                    server.starttls()
                server.login(smtp_config["email"], smtp_config["password"])
                server.send_message(msg)
            
            logger.info(f"Email enviado com sucesso para {to_email}")
            return True, "Email enviado com sucesso"
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "Erro de autenticação - verifique as credenciais"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPRecipientsRefused:
            error_msg = f"Email de destino inválido: {to_email}"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"Erro SMTP: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_batch_emails(self, emails_data: list, on_progress=None) -> Tuple[int, int]:
        """
        Envia emails em lote
        emails_data: lista de dicts com 'email', 'subject', 'body', 'nome'
        on_progress: callback(current, total, nome, success, error_msg)
        """
        sucessos = 0
        erros = 0
        
        for i, email_data in enumerate(emails_data):
            nome = email_data.get('nome', '')
            email = email_data.get('email', '')
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')
            
            sucesso, mensagem = self.send_email(email, subject, body, nome)
            
            if sucesso:
                sucessos += 1
            else:
                erros += 1
            
            # Callback de progresso
            if on_progress:
                on_progress(i + 1, len(emails_data), nome, sucesso, mensagem)
        
        return sucessos, erros

    def send_email_with_attachment(self, to_email: str, subject: str, body: str, 
                                 attachment_path: str, nome_destinatario: str = "") -> Tuple[bool, str]:
        """Envia um email com anexo (compatibilidade - usa send_email_with_attachments)"""
        return self.send_email_with_attachments(to_email, subject, body, [attachment_path], nome_destinatario)

    def send_email_with_attachments(self, to_email: str, subject: str, body: str, 
                                   attachment_paths: list, nome_destinatario: str = "") -> Tuple[bool, str]:
        """Envia um email com múltiplos anexos"""
        
        if not self.config.is_configured():
            error_msg = "Email não configurado"
            logger.error(error_msg)
            return False, error_msg
        
        # Verificar se todos os anexos existem
        missing_files = []
        for attachment_path in attachment_paths:
            if not os.path.exists(attachment_path):
                missing_files.append(attachment_path)
        
        if missing_files:
            error_msg = f"Arquivos de anexo não encontrados: {', '.join(missing_files)}"
            logger.error(error_msg)
            return False, error_msg
        
        try:
            smtp_config = self.config.get_smtp_config()
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = smtp_config["email"]
            msg['To'] = to_email
            msg['Subject'] = self.config.format_template(subject, nome_destinatario)
            
            # Formatar corpo do email
            body_formatted = self.config.format_template(body, nome_destinatario)
            
            # Adicionar assinatura se não estiver presente
            if not any(keyword in body_formatted.lower() for keyword in ["cumprimentos", "atenciosamente", "equipa"]):
                assinatura = self.config.format_template(self.config.get("assinatura"), nome_destinatario)
                body_formatted += "\n\n" + assinatura
            
            msg.attach(MIMEText(body_formatted, 'plain', 'utf-8'))
            
            # Adicionar múltiplos anexos
            anexos_adicionados = []
            for attachment_path in attachment_paths:
                try:
                    with open(attachment_path, "rb") as attachment:
                        # Determinar o tipo MIME correto baseado na extensão
                        if attachment_path.lower().endswith('.pdf'):
                            part = MIMEBase('application', 'pdf')
                        elif attachment_path.lower().endswith(('.doc', '.docx')):
                            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document')
                        else:
                            part = MIMEBase('application', 'octet-stream')
                            
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    
                    # Obter nome do arquivo
                    filename = os.path.basename(attachment_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{filename}"',  # Adicionar aspas ao nome
                    )
                    
                    msg.attach(part)
                    anexos_adicionados.append(filename)
                    logger.info(f"Anexo adicionado: {filename}")
                    
                except Exception as e:
                    logger.warning(f"Erro ao adicionar anexo {attachment_path}: {str(e)}")
                    continue
            
            if not anexos_adicionados:
                error_msg = "Nenhum anexo válido foi adicionado"
                logger.error(error_msg)
                return False, error_msg
            
            # Enviar email
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
                if smtp_config["use_tls"]:
                    server.starttls()
                server.login(smtp_config["email"], smtp_config["password"])
                server.send_message(msg)
            
            success_msg = f"Email com {len(anexos_adicionados)} anexo(s) enviado para {to_email}: {', '.join(anexos_adicionados)}"
            logger.info(success_msg)
            return True, success_msg
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "Erro de autenticação - verifique email e senha"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPRecipientsRefused:
            error_msg = f"Email de destino inválido: {to_email}"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"Erro SMTP: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Instância global
email_sender = EmailSender()
