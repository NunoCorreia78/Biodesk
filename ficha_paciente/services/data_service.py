"""
Biodesk - Data Service
======================

Serviço para gestão e validação de dados de pacientes.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Validação de dados de pacientes
- Normalização de informações
- Atualização de dados em tempo real
- Formatação de campos

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Dict, Any, Optional, List
import re

from ..utils import DateUtils, TextUtils


class DataService:
    """Serviço para gestão e validação de dados de pacientes"""
    
    @staticmethod
    def validar_dados_paciente(paciente_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valida dados essenciais do paciente
        
        Args:
            paciente_data: Dados do paciente
            
        Returns:
            Dicionário com erros encontrados por campo
        """
        erros = {}
        
        if not paciente_data:
            erros['geral'] = ['Dados do paciente não fornecidos']
            return erros
        
        # Validar nome
        nome = paciente_data.get('nome', '').strip()
        if not nome:
            erros['nome'] = ['Nome é obrigatório']
        elif len(nome) < 2:
            erros['nome'] = ['Nome deve ter pelo menos 2 caracteres']
        
        # Validar email se fornecido
        email = paciente_data.get('email', '').strip()
        if email:
            from .email_service import EmailService
            if not EmailService.validar_email(email):
                erros['email'] = ['Email tem formato inválido']
        
        # Validar data de nascimento se fornecida
        data_nascimento = paciente_data.get('data_nascimento', '')
        if data_nascimento:
            if not DateUtils.validar_data(str(data_nascimento)):
                erros['data_nascimento'] = ['Data de nascimento inválida']
            else:
                idade = DateUtils.calcular_idade(data_nascimento)
                if idade is None:
                    erros['data_nascimento'] = ['Não foi possível calcular a idade']
                elif idade < 0:
                    erros['data_nascimento'] = ['Data de nascimento no futuro']
                elif idade > 150:
                    erros['data_nascimento'] = ['Idade muito avançada']
        
        # Validar telefone se fornecido
        telefone = paciente_data.get('telefone', '').strip()
        if telefone:
            telefone_limpo = re.sub(r'[^\d+]', '', telefone)
            if len(telefone_limpo) < 9:
                erros['telefone'] = ['Telefone deve ter pelo menos 9 dígitos']
        
        return erros
    
    @staticmethod
    def normalizar_dados_paciente(paciente_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza e limpa dados do paciente
        
        Args:
            paciente_data: Dados originais
            
        Returns:
            Dados normalizados
        """
        if not paciente_data:
            return {}
        
        dados_normalizados = paciente_data.copy()
        
        # Normalizar nome
        if 'nome' in dados_normalizados:
            nome = dados_normalizados['nome']
            if nome:
                # Capitalizar primeira letra de cada palavra
                dados_normalizados['nome'] = ' '.join(word.capitalize() for word in str(nome).split())
        
        # Normalizar email
        if 'email' in dados_normalizados:
            email = dados_normalizados['email']
            if email:
                dados_normalizados['email'] = str(email).strip().lower()
        
        # Normalizar telefone
        if 'telefone' in dados_normalizados:
            telefone = dados_normalizados['telefone']
            if telefone:
                # Manter apenas dígitos e +
                telefone_limpo = re.sub(r'[^\d+]', '', str(telefone))
                dados_normalizados['telefone'] = telefone_limpo
        
        # Normalizar data de nascimento
        if 'data_nascimento' in dados_normalizados:
            data = dados_normalizados['data_nascimento']
            if data:
                data_formatada = DateUtils.formatar_data_brasileira(data)
                dados_normalizados['data_nascimento'] = data_formatada
        
        return dados_normalizados
    
    @staticmethod
    def atualizar_campo_paciente(paciente_data: Dict[str, Any], 
                                campo: str, valor: Any) -> Dict[str, Any]:
        """
        Atualiza um campo específico do paciente com validação
        
        Args:
            paciente_data: Dados atuais do paciente
            campo: Nome do campo a atualizar
            valor: Novo valor
            
        Returns:
            Dados atualizados
        """
        if not paciente_data:
            paciente_data = {}
        
        dados_atualizados = paciente_data.copy()
        
        # Aplicar formatação específica por campo
        if campo == 'email' and valor:
            valor = str(valor).strip().lower()
        elif campo == 'nome' and valor:
            valor = str(valor).strip().title()
        elif campo == 'telefone' and valor:
            valor = re.sub(r'[^\d+]', '', str(valor))
        elif campo in ['data_nascimento'] and valor:
            valor = DateUtils.formatar_data_brasileira(valor)
        
        dados_atualizados[campo] = valor
        
        return dados_atualizados
    
    @staticmethod
    def obter_resumo_paciente(paciente_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera resumo formatado dos dados do paciente
        
        Args:
            paciente_data: Dados do paciente
            
        Returns:
            Resumo formatado
        """
        if not paciente_data:
            return {'erro': 'Dados não disponíveis'}
        
        resumo = {}
        
        # Nome
        nome = paciente_data.get('nome', 'N/A')
        resumo['nome'] = nome
        
        # Idade calculada
        data_nascimento = paciente_data.get('data_nascimento')
        if data_nascimento:
            idade = DateUtils.calcular_idade(data_nascimento)
            if idade is not None:
                resumo['idade'] = f"{idade} anos"
                resumo['data_nascimento'] = DateUtils.formatar_data_brasileira(data_nascimento)
            else:
                resumo['data_nascimento'] = str(data_nascimento)
        else:
            resumo['data_nascimento'] = 'N/A'
        
        # Email
        email = paciente_data.get('email', 'N/A')
        resumo['email'] = email if email else 'N/A'
        
        # Telefone
        telefone = paciente_data.get('telefone', 'N/A')
        resumo['telefone'] = telefone if telefone else 'N/A'
        
        # ID
        paciente_id = paciente_data.get('id', 'N/A')
        resumo['id'] = str(paciente_id)
        
        return resumo
    
    @staticmethod
    def verificar_dados_obrigatorios(paciente_data: Dict[str, Any], 
                                   campos_obrigatorios: List[str]) -> List[str]:
        """
        Verifica se todos os campos obrigatórios estão preenchidos
        
        Args:
            paciente_data: Dados do paciente
            campos_obrigatorios: Lista de campos que devem estar preenchidos
            
        Returns:
            Lista de campos em falta
        """
        if not paciente_data:
            return campos_obrigatorios.copy()
        
        campos_em_falta = []
        
        for campo in campos_obrigatorios:
            valor = paciente_data.get(campo)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                campos_em_falta.append(campo)
        
        return campos_em_falta
    
    @staticmethod
    def gerar_nome_arquivo_paciente(paciente_data: Dict[str, Any], 
                                   sufixo: str = "") -> str:
        """
        Gera nome de arquivo baseado nos dados do paciente
        
        Args:
            paciente_data: Dados do paciente
            sufixo: Sufixo adicional para o nome
            
        Returns:
            Nome de arquivo formatado
        """
        if not paciente_data:
            return f"paciente_desconhecido_{DateUtils.timestamp_arquivo()}"
        
        # Usar ID e nome se disponíveis
        paciente_id = paciente_data.get('id', 'sem_id')
        nome = paciente_data.get('nome', 'paciente')
        
        # Sanitizar nome
        nome_limpo = TextUtils.formatar_nome_arquivo(nome)
        
        # Construir nome do arquivo
        if sufixo:
            sufixo_limpo = TextUtils.formatar_nome_arquivo(sufixo)
            return f"{paciente_id}_{nome_limpo}_{sufixo_limpo}_{DateUtils.timestamp_arquivo()}"
        else:
            return f"{paciente_id}_{nome_limpo}_{DateUtils.timestamp_arquivo()}"
