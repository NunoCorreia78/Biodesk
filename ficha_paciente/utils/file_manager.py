"""
Biodesk - File Manager
======================

Utilitários para gestão de arquivos e documentos.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Gestão de estrutura de pastas de pacientes
- Operações seguras com arquivos
- Validação de disponibilidade de arquivos
- Nomes de arquivo sanitizados

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

import os
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

from .date_utils import DateUtils
from .text_utils import TextUtils


class FileManager:
    """Utilitários para gestão de arquivos e documentos"""
    
    @staticmethod
    def criar_estrutura_paciente(paciente_data: Dict[str, Any]) -> str:
        """
        Cria a estrutura de pastas para um paciente
        
        Args:
            paciente_data: Dados do paciente com 'id' e 'nome'
            
        Returns:
            Caminho da pasta principal do paciente
        """
        try:
            paciente_id = paciente_data.get('id', 'sem_id')
            nome_paciente = paciente_data.get('nome', 'Paciente')
            
            # Sanitizar nome para uso em arquivo
            nome_sanitizado = TextUtils.formatar_nome_arquivo(nome_paciente)
            
            # Criar estrutura de pastas
            pasta_base = f"documentos/{paciente_id}_{nome_sanitizado}"
            pasta_consentimentos = os.path.join(pasta_base, "consentimentos")
            pasta_declaracoes = os.path.join(pasta_base, "declaracoes")
            pasta_iris = os.path.join(pasta_base, "iris")
            
            # Criar todas as pastas
            for pasta in [pasta_base, pasta_consentimentos, pasta_declaracoes, pasta_iris]:
                os.makedirs(pasta, exist_ok=True)
            
            return pasta_base
            
        except Exception as e:
            print(f"[ERRO] Erro ao criar estrutura do paciente: {e}")
            return "documentos/erro"
    
    @staticmethod
    def guardar_documento_paciente(arquivo_origem: str, arquivo_temp: str, 
                                 paciente_data: Dict[str, Any], 
                                 tipo_documento: str = "documento") -> bool:
        """
        Guarda um documento na pasta do paciente
        
        Args:
            arquivo_origem: Arquivo a ser copiado
            arquivo_temp: Arquivo temporário a ser removido
            paciente_data: Dados do paciente
            tipo_documento: Tipo do documento (consentimento, declaracao, etc.)
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Criar estrutura do paciente
            pasta_base = FileManager.criar_estrutura_paciente(paciente_data)
            
            # Determinar subpasta baseada no tipo
            if tipo_documento.lower() in ['consentimento', 'consentimentos']:
                subpasta = "consentimentos"
            elif tipo_documento.lower() in ['declaracao', 'declaracoes', 'declaração']:
                subpasta = "declaracoes"
            else:
                subpasta = "outros"
            
            pasta_destino = os.path.join(pasta_base, subpasta)
            os.makedirs(pasta_destino, exist_ok=True)
            
            # Gerar nome do arquivo
            timestamp = DateUtils.timestamp_arquivo()
            tipo_sanitizado = TextUtils.formatar_nome_arquivo(tipo_documento)
            nome_arquivo = f"{tipo_sanitizado}_ASSINADO_{timestamp}.pdf"
            caminho_final = os.path.join(pasta_destino, nome_arquivo)
            
            # Copiar arquivo
            shutil.copy2(arquivo_origem, caminho_final)
            print(f"[DEBUG] ✅ Documento guardado: {caminho_final}")
            
            # Remover arquivo temporário se existir
            if arquivo_temp and os.path.exists(arquivo_temp):
                try:
                    os.remove(arquivo_temp)
                    print(f"[DEBUG] 🗑️ Arquivo temporário removido: {arquivo_temp}")
                except Exception as e:
                    print(f"[AVISO] Não foi possível remover arquivo temporário: {e}")
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Erro ao guardar documento: {e}")
            return False
    
    @staticmethod
    def arquivo_disponivel(caminho: str) -> bool:
        """
        Verifica se um arquivo está disponível para leitura (não sendo usado)
        
        Args:
            caminho: Caminho do arquivo
            
        Returns:
            True se disponível, False caso contrário
        """
        try:
            if not os.path.exists(caminho):
                return False
                
            with open(caminho, 'rb') as f:
                f.read(1)  # Tentar ler 1 byte
            return True
        except Exception:
            return False
    
    @staticmethod
    def gerar_nome_arquivo_seguro(nome_base: str, extensao: str = "pdf") -> str:
        """
        Gera um nome de arquivo seguro com timestamp
        
        Args:
            nome_base: Nome base do arquivo
            extensao: Extensão do arquivo (sem ponto)
            
        Returns:
            Nome do arquivo com timestamp
        """
        nome_sanitizado = TextUtils.formatar_nome_arquivo(nome_base)
        timestamp = DateUtils.timestamp_arquivo()
        return f"{nome_sanitizado}_{timestamp}.{extensao}"
    
    @staticmethod
    def obter_pasta_temporaria() -> str:
        """
        Obtém o caminho da pasta temporária
        
        Returns:
            Caminho da pasta temp
        """
        pasta_temp = "temp"
        os.makedirs(pasta_temp, exist_ok=True)
        return pasta_temp
    
    @staticmethod
    def limpar_arquivos_temporarios(idade_dias: int = 7) -> int:
        """
        Remove arquivos temporários antigos
        
        Args:
            idade_dias: Arquivos mais antigos que N dias serão removidos
            
        Returns:
            Número de arquivos removidos
        """
        try:
            from datetime import datetime, timedelta
            
            pasta_temp = FileManager.obter_pasta_temporaria()
            if not os.path.exists(pasta_temp):
                return 0
            
            limite_data = datetime.now() - timedelta(days=idade_dias)
            arquivos_removidos = 0
            
            for arquivo in os.listdir(pasta_temp):
                caminho_arquivo = os.path.join(pasta_temp, arquivo)
                
                if os.path.isfile(caminho_arquivo):
                    # Verificar data de modificação
                    timestamp_arquivo = os.path.getmtime(caminho_arquivo)
                    data_arquivo = datetime.fromtimestamp(timestamp_arquivo)
                    
                    if data_arquivo < limite_data:
                        try:
                            os.remove(caminho_arquivo)
                            arquivos_removidos += 1
                        except Exception as e:
                            print(f"[AVISO] Não foi possível remover {arquivo}: {e}")
            
            print(f"[DEBUG] 🧹 Limpeza: {arquivos_removidos} arquivos temporários removidos")
            return arquivos_removidos
            
        except Exception as e:
            print(f"[ERRO] Erro na limpeza de temporários: {e}")
            return 0
    
    @staticmethod
    def validar_pdf(caminho: str) -> bool:
        """
        Validação básica se o arquivo é um PDF válido
        
        Args:
            caminho: Caminho do arquivo PDF
            
        Returns:
            True se parece ser um PDF válido
        """
        try:
            if not os.path.exists(caminho):
                return False
            
            # Verificar extensão
            if not caminho.lower().endswith('.pdf'):
                return False
            
            # Verificar header PDF
            with open(caminho, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
                
        except Exception:
            return False
