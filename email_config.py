#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração de Email para Biodesk
"""

import json
import os
from typing import Dict, Any

class EmailConfig:
    """Gestor de configuração de email"""
    
    def __init__(self):
        self.config_file = "email_config.json"
        self.default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "email": "",
            "password": "",
            "nome_clinica": "Clínica Biodesk",
            "telefone": "+351 XXX XXX XXX",
            "endereco": "Rua Example, 123, 1000-000 Lisboa",
            "horario_semana": "9:00 - 18:00",
            "horario_sabado": "9:00 - 13:00",
            "whatsapp": "+351 XXX XXX XXX",
            "assinatura": """
Com os melhores cumprimentos,
Equipa {nome_clinica}
📞 {telefone} | 📧 {email}
📍 {endereco}
"""
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carrega configuração do ficheiro"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return {**self.default_config, **json.load(f)}
            except Exception:
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """Guarda configuração no ficheiro"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao guardar configuração: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Obtém valor de configuração"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Define valor de configuração"""
        self.config[key] = value
    
    def is_configured(self) -> bool:
        """Verifica se o email está configurado"""
        return bool(self.config.get("email") and self.config.get("password"))
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """Retorna configuração SMTP"""
        return {
            "server": self.config["smtp_server"],
            "port": self.config["smtp_port"],
            "use_tls": self.config["use_tls"],
            "email": self.config["email"],
            "password": self.config["password"]
        }
    
    def format_template(self, template: str, nome: str = "") -> str:
        """Formata template com dados da configuração"""
        return template.format(
            nome=nome,
            nome_clinica=self.config["nome_clinica"],
            telefone=self.config["telefone"],
            email=self.config["email"],
            endereco=self.config["endereco"],
            horario_semana=self.config["horario_semana"],
            horario_sabado=self.config["horario_sabado"],
            whatsapp=self.config["whatsapp"]
        )

# Instância global
email_config = EmailConfig()
