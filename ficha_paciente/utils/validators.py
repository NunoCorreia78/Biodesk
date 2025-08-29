"""
Validadores centralizados para o módulo ficha_paciente
"""

import re
from typing import Tuple, List, Dict
from datetime import datetime


class EmailValidator:
    """Validador de emails"""

    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @staticmethod
    def validate(email: str) -> bool:
        """Valida formato de email"""
        if not email:
            return True  # Campo opcional
        return bool(EmailValidator.EMAIL_PATTERN.match(email.strip()))


class PhoneValidator:
    """Validador de telefones portugueses"""

    PHONE_PATTERNS = [
        re.compile(r'^9\d{8}$'),  # 912345678
        re.compile(r'^2\d{8}$'),  # 212345678
        re.compile(r'^\+351\d{9}$'),  # +351912345678
        re.compile(r'^00351\d{9}$'),  # 00351912345678
    ]

    @staticmethod
    def validate(phone: str) -> bool:
        """Valida formato de telefone"""
        if not phone:
            return True  # Campo opcional

        # Remover espaços e traços
        clean_phone = re.sub(r'[\s\-]', '', phone.strip())

        # Verificar se corresponde a algum padrão
        for pattern in PhoneValidator.PHONE_PATTERNS:
            if pattern.match(clean_phone):
                return True
        return False


class PatientValidator:
    """Validador de dados de paciente"""

    @staticmethod
    def validate(data: Dict) -> Tuple[bool, List[str]]:
        """
        Valida dados completos do paciente

        Returns:
            Tuple[bool, List[str]]: (válido, lista de erros)
        """
        errors = []

        # Validações obrigatórias
        if not data.get('nome', '').strip():
            errors.append("Nome é obrigatório")

        # Validações condicionais
        email = data.get('email', '').strip()
        if email and not EmailValidator.validate(email):
            errors.append("Email tem formato inválido")

        contacto = data.get('contacto', '').strip()
        if contacto and not PhoneValidator.validate(contacto):
            errors.append("Telefone tem formato inválido")

        # Validação de datas
        data_nasc = data.get('data_nascimento', '').strip()
        if data_nasc:
            try:
                datetime.strptime(data_nasc, '%d/%m/%Y')
            except ValueError:
                errors.append("Data de nascimento tem formato inválido (DD/MM/YYYY)")

        # Validação de NIF (se fornecido)
        nif = data.get('nif', '').strip()
        if nif and not PatientValidator._validate_nif(nif):
            errors.append("NIF inválido")

        return len(errors) == 0, errors

    @staticmethod
    def _validate_nif(nif: str) -> bool:
        """Valida NIF português"""
        if not nif or len(nif) != 9 or not nif.isdigit():
            return False

        # Algoritmo de validação NIF
        total = 0
        for i, digit in enumerate(nif[:-1]):
            total += int(digit) * (9 - i)

        resto = total % 11
        check_digit = 0 if resto < 2 else 11 - resto

        return check_digit == int(nif[-1])
