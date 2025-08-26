"""
Biodesk - Validation Service
============================

Serviço para validações gerais da aplicação.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Validações de formulários
- Verificação de dados obrigatórios
- Validações específicas de domínio
- Mensagens de erro padronizadas

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

from typing import Dict, Any, List, Optional, Tuple
import re

from .email_service import EmailService
from .data_service import DataService
from ..utils import DateUtils


class ValidationService:
    """Serviço para validações gerais da aplicação"""
    
    @staticmethod
    def validar_dados_obrigatorios(dados: Dict[str, Any], 
                                 campos_obrigatorios: List[str]) -> Tuple[bool, List[str]]:
        """
        Valida se todos os campos obrigatórios estão preenchidos
        
        Args:
            dados: Dados a validar
            campos_obrigatorios: Lista de campos obrigatórios
            
        Returns:
            Tupla (é_válido, lista_de_erros)
        """
        erros = []
        
        if not dados:
            erros.append("Nenhum dado fornecido")
            return False, erros
        
        for campo in campos_obrigatorios:
            valor = dados.get(campo)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                nome_campo = campo.replace('_', ' ').title()
                erros.append(f"{nome_campo} é obrigatório")
        
        return len(erros) == 0, erros
    
    @staticmethod
    def validar_formulario_paciente(dados_paciente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validação completa de formulário de paciente
        
        Args:
            dados_paciente: Dados do formulário
            
        Returns:
            Resultado da validação com status e erros
        """
        resultado = {
            'valido': True,
            'erros': {},
            'avisos': {},
            'dados_normalizados': {}
        }
        
        # Normalizar dados primeiro
        dados_normalizados = DataService.normalizar_dados_paciente(dados_paciente)
        resultado['dados_normalizados'] = dados_normalizados
        
        # Validar dados obrigatórios
        erros_dados = DataService.validar_dados_paciente(dados_normalizados)
        if erros_dados:
            resultado['erros'].update(erros_dados)
            resultado['valido'] = False
        
        # Validações adicionais específicas
        
        # Validar comprimento do nome
        nome = dados_normalizados.get('nome', '')
        if nome and len(nome) > 100:
            if 'nome' not in resultado['erros']:
                resultado['erros']['nome'] = []
            resultado['erros']['nome'].append('Nome muito longo (máximo 100 caracteres)')
            resultado['valido'] = False
        
        # Validar formato de telefone português
        telefone = dados_normalizados.get('telefone', '')
        if telefone:
            if not ValidationService._validar_telefone_portugues(telefone):
                if 'telefone' not in resultado['avisos']:
                    resultado['avisos']['telefone'] = []
                resultado['avisos']['telefone'].append('Formato de telefone pode não ser português')
        
        return resultado
    
    @staticmethod
    def _validar_telefone_portugues(telefone: str) -> bool:
        """
        Valida se o telefone segue formato português
        
        Args:
            telefone: Número de telefone
            
        Returns:
            True se formato válido
        """
        if not telefone:
            return False
        
        # Remover espaços e caracteres especiais
        telefone_limpo = re.sub(r'[^\d+]', '', telefone)
        
        # Padrões portugueses comuns
        padroes = [
            r'^\+351\d{9}$',  # +351xxxxxxxxx
            r'^351\d{9}$',    # 351xxxxxxxxx
            r'^\d{9}$',       # xxxxxxxxx (9 dígitos)
            r'^2\d{8}$',      # Fixo (2xxxxxxxx)
            r'^9\d{8}$',      # Móvel (9xxxxxxxx)
        ]
        
        for padrao in padroes:
            if re.match(padrao, telefone_limpo):
                return True
        
        return False
    
    @staticmethod
    def validar_campos_email(destinatario: str, assunto: str, corpo: str) -> Tuple[bool, List[str]]:
        """
        Valida campos de email antes do envio
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo: Corpo do email
            
        Returns:
            Tupla (é_válido, lista_de_erros)
        """
        erros = []
        
        # Validar destinatário
        if not destinatario or not destinatario.strip():
            erros.append("Email do destinatário é obrigatório")
        elif not EmailService.validar_email(destinatario):
            erros.append("Email do destinatário tem formato inválido")
        
        # Validar assunto
        if not assunto or not assunto.strip():
            erros.append("Assunto é obrigatório")
        elif len(assunto.strip()) < 3:
            erros.append("Assunto deve ter pelo menos 3 caracteres")
        
        # Validar corpo
        if not corpo or not corpo.strip():
            erros.append("Corpo da mensagem é obrigatório")
        elif len(corpo.strip()) < 10:
            erros.append("Mensagem deve ter pelo menos 10 caracteres")
        
        return len(erros) == 0, erros
    
    @staticmethod
    def validar_arquivo_pdf(caminho_arquivo: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se o arquivo é um PDF válido
        
        Args:
            caminho_arquivo: Caminho do arquivo
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        import os
        
        if not caminho_arquivo:
            return False, "Caminho do arquivo não fornecido"
        
        if not os.path.exists(caminho_arquivo):
            return False, "Arquivo não encontrado"
        
        if not caminho_arquivo.lower().endswith('.pdf'):
            return False, "Arquivo deve ter extensão .pdf"
        
        # Verificar se arquivo não está vazio
        try:
            tamanho = os.path.getsize(caminho_arquivo)
            if tamanho == 0:
                return False, "Arquivo está vazio"
            elif tamanho > 50 * 1024 * 1024:  # 50MB
                return False, "Arquivo muito grande (máximo 50MB)"
        except:
            return False, "Erro ao verificar tamanho do arquivo"
        
        # Verificar header PDF básico
        try:
            with open(caminho_arquivo, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False, "Arquivo não é um PDF válido"
        except:
            return False, "Erro ao ler arquivo"
        
        return True, None
    
    @staticmethod
    def validar_data_range(data_inicio: str, data_fim: str) -> Tuple[bool, Optional[str]]:
        """
        Valida um intervalo de datas
        
        Args:
            data_inicio: Data de início
            data_fim: Data de fim
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        if not DateUtils.validar_data(data_inicio):
            return False, "Data de início inválida"
        
        if not DateUtils.validar_data(data_fim):
            return False, "Data de fim inválida"
        
        diferenca = DateUtils.diferenca_dias(data_inicio, data_fim)
        if diferenca is None:
            return False, "Erro ao calcular diferença entre datas"
        
        if diferenca < 0:
            return False, "Data de fim deve ser posterior à data de início"
        
        return True, None
    
    @staticmethod
    def gerar_resumo_validacao(resultado_validacao: Dict[str, Any]) -> str:
        """
        Gera resumo legível do resultado de validação
        
        Args:
            resultado_validacao: Resultado da validação
            
        Returns:
            Texto com resumo dos erros e avisos
        """
        linhas = []
        
        if resultado_validacao.get('valido', False):
            linhas.append("✅ Todos os dados estão válidos")
        else:
            linhas.append("❌ Foram encontrados erros:")
            
            erros = resultado_validacao.get('erros', {})
            for campo, lista_erros in erros.items():
                campo_nome = campo.replace('_', ' ').title()
                for erro in lista_erros:
                    linhas.append(f"  • {campo_nome}: {erro}")
        
        # Adicionar avisos se existirem
        avisos = resultado_validacao.get('avisos', {})
        if avisos:
            linhas.append("\n⚠️ Avisos:")
            for campo, lista_avisos in avisos.items():
                campo_nome = campo.replace('_', ' ').title()
                for aviso in lista_avisos:
                    linhas.append(f"  • {campo_nome}: {aviso}")
        
        return "\n".join(linhas)
