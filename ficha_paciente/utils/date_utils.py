"""
Biodesk - Date Utils
====================

Utilitários para manipulação e formatação de datas.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Formatação de datas brasileiras
- Timestamps para base de dados
- Validação de datas
- Cálculos de idade e períodos

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from datetime import datetime, date
from typing import Optional, Union


class DateUtils:
    """Utilitários para manipulação e formatação de datas"""
    
    @staticmethod
    def data_atual() -> str:
        """
        Retorna a data atual formatada no padrão brasileiro
        
        Returns:
            Data no formato DD/MM/YYYY
        """
        return datetime.now().strftime('%d/%m/%Y')
    
    @staticmethod
    def data_atual_completa() -> str:
        """
        Retorna a data atual no formato completo para base de dados
        
        Returns:
            Data e hora no formato YYYY-MM-DD HH:MM:SS
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def timestamp_arquivo() -> str:
        """
        Gera timestamp para nomes de arquivo
        
        Returns:
            Timestamp no formato YYYYMMDD_HHMMSS
        """
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    @staticmethod
    def formatar_data_brasileira(data_input: Union[str, datetime, date]) -> str:
        """
        Converte uma data para o formato brasileiro DD/MM/YYYY
        
        Args:
            data_input: Data em diversos formatos
            
        Returns:
            Data formatada em DD/MM/YYYY
        """
        if isinstance(data_input, str):
            # Tentar diferentes formatos de entrada
            formatos = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']
            for formato in formatos:
                try:
                    data_obj = datetime.strptime(data_input, formato)
                    return data_obj.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            return data_input  # Retornar original se não conseguir converter
        elif isinstance(data_input, datetime):
            return data_input.strftime('%d/%m/%Y')
        elif isinstance(data_input, date):
            return data_input.strftime('%d/%m/%Y')
        else:
            return str(data_input)
    
    @staticmethod
    def formatar_data_bd(data_input: Union[str, datetime, date]) -> str:
        """
        Converte uma data para o formato de base de dados YYYY-MM-DD
        
        Args:
            data_input: Data em diversos formatos
            
        Returns:
            Data formatada em YYYY-MM-DD
        """
        if isinstance(data_input, str):
            # Tentar diferentes formatos de entrada
            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
            for formato in formatos:
                try:
                    data_obj = datetime.strptime(data_input, formato)
                    return data_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return data_input  # Retornar original se não conseguir converter
        elif isinstance(data_input, datetime):
            return data_input.strftime('%Y-%m-%d')
        elif isinstance(data_input, date):
            return data_input.strftime('%Y-%m-%d')
        else:
            return str(data_input)
    
    @staticmethod
    def calcular_idade(data_nascimento: Union[str, datetime, date]) -> Optional[int]:
        """
        Calcula a idade a partir da data de nascimento
        
        Args:
            data_nascimento: Data de nascimento em diversos formatos
            
        Returns:
            Idade em anos ou None se inválida
        """
        try:
            if isinstance(data_nascimento, str):
                # Tentar diferentes formatos
                formatos = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
                for formato in formatos:
                    try:
                        nascimento = datetime.strptime(data_nascimento, formato).date()
                        break
                    except ValueError:
                        continue
                else:
                    return None
            elif isinstance(data_nascimento, datetime):
                nascimento = data_nascimento.date()
            elif isinstance(data_nascimento, date):
                nascimento = data_nascimento
            else:
                return None
            
            hoje = date.today()
            idade = hoje.year - nascimento.year
            
            # Ajustar se ainda não fez aniversário este ano
            if hoje.month < nascimento.month or (hoje.month == nascimento.month and hoje.day < nascimento.day):
                idade -= 1
                
            return idade if idade >= 0 else None
            
        except Exception:
            return None
    
    @staticmethod
    def validar_data(data_str: str) -> bool:
        """
        Valida se uma string representa uma data válida
        
        Args:
            data_str: String da data a validar
            
        Returns:
            True se válida, False caso contrário
        """
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
        
        for formato in formatos:
            try:
                datetime.strptime(data_str, formato)
                return True
            except ValueError:
                continue
        
        return False
    
    @staticmethod
    def diferenca_dias(data1: Union[str, datetime, date], 
                      data2: Union[str, datetime, date]) -> Optional[int]:
        """
        Calcula a diferença em dias entre duas datas
        
        Args:
            data1: Primeira data
            data2: Segunda data
            
        Returns:
            Diferença em dias (positivo se data2 > data1) ou None se erro
        """
        try:
            def converter_para_date(data_input):
                if isinstance(data_input, str):
                    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
                    for formato in formatos:
                        try:
                            return datetime.strptime(data_input, formato).date()
                        except ValueError:
                            continue
                    return None
                elif isinstance(data_input, datetime):
                    return data_input.date()
                elif isinstance(data_input, date):
                    return data_input
                return None
            
            date1_obj = converter_para_date(data1)
            date2_obj = converter_para_date(data2)
            
            if date1_obj and date2_obj:
                return (date2_obj - date1_obj).days
            
            return None
            
        except Exception:
            return None
