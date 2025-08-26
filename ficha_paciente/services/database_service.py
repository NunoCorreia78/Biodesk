"""
Biodesk - Database Service
==========================

Serviço para operações de banco de dados centralizadas.
Extraído do monólito ficha_paciente.py para melhorar organização.

🎯 Funcionalidades:
- Conexões seguras com SQLite
- Operações CRUD padronizadas
- Gestão de transações
- Queries otimizadas para consentimentos e pacientes

📅 Criado em: Janeiro 2025
👨‍💻 Autor: Nuno Correia
"""

import sqlite3
import os
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager


class DatabaseService:
    """Serviço para operações centralizadas de banco de dados"""
    
    # Configurações de banco
    DEFAULT_DB_PATH = "pacientes.db"
    TIMEOUT_SECONDS = 30
    
    @staticmethod
    @contextmanager
    def obter_conexao(db_path: str = None):
        """
        Context manager para conexões seguras com SQLite
        
        Args:
            db_path: Caminho do banco (padrão: pacientes.db)
            
        Yields:
            Conexão SQLite
        """
        db_path = db_path or DatabaseService.DEFAULT_DB_PATH
        conn = None
        
        try:
            conn = sqlite3.connect(db_path, timeout=DatabaseService.TIMEOUT_SECONDS)
            conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def executar_query(query: str, 
                      params: tuple = None,
                      fetch_one: bool = False,
                      fetch_all: bool = False,
                      commit: bool = False) -> Any:
        """
        Executa query SQL com parâmetros seguros
        
        Args:
            query: Query SQL
            params: Parâmetros da query
            fetch_one: Se deve retornar um registro
            fetch_all: Se deve retornar todos os registros
            commit: Se deve fazer commit
            
        Returns:
            Resultado da query
        """
        with DatabaseService.obter_conexao() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if commit:
                conn.commit()
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.lastrowid if commit else None
    
    # === OPERAÇÕES DE CONSENTIMENTOS ===
    
    @staticmethod
    def buscar_consentimento_recente(paciente_id: str, 
                                   tipo_consentimento: str) -> Optional[Dict[str, Any]]:
        """
        Busca o consentimento mais recente de um paciente
        
        Args:
            paciente_id: ID do paciente
            tipo_consentimento: Tipo do consentimento
            
        Returns:
            Dados do consentimento ou None
        """
        query = '''
            SELECT id, assinatura_paciente, assinatura_terapeuta, nome_paciente, 
                   nome_terapeuta, status, data_assinatura, conteudo_texto, conteudo_html
            FROM consentimentos 
            WHERE paciente_id = ? AND tipo_consentimento = ? 
                  AND (status IS NULL OR status != 'anulado')
            ORDER BY data_assinatura DESC 
            LIMIT 1
        '''
        
        resultado = DatabaseService.executar_query(
            query, 
            (paciente_id, tipo_consentimento),
            fetch_one=True
        )
        
        if resultado:
            return {
                'id': resultado['id'],
                'assinatura_paciente': resultado['assinatura_paciente'],
                'assinatura_terapeuta': resultado['assinatura_terapeuta'],
                'nome_paciente': resultado['nome_paciente'],
                'nome_terapeuta': resultado['nome_terapeuta'],
                'status': resultado['status'],
                'data_assinatura': resultado['data_assinatura'],
                'conteudo_texto': resultado['conteudo_texto'],
                'conteudo_html': resultado['conteudo_html']
            }
        
        return None
    
    @staticmethod
    def verificar_consentimento_existe(paciente_id: str, 
                                     tipo_consentimento: str) -> Optional[int]:
        """
        Verifica se já existe consentimento para o paciente
        
        Args:
            paciente_id: ID do paciente
            tipo_consentimento: Tipo do consentimento
            
        Returns:
            ID do consentimento se existe, None caso contrário
        """
        query = '''
            SELECT id FROM consentimentos 
            WHERE paciente_id = ? AND tipo_consentimento = ?
            ORDER BY data_assinatura DESC 
            LIMIT 1
        '''
        
        resultado = DatabaseService.executar_query(
            query,
            (paciente_id, tipo_consentimento),
            fetch_one=True
        )
        
        return resultado['id'] if resultado else None
    
    @staticmethod
    def atualizar_consentimento(consentimento_id: int,
                              conteudo_html: str,
                              conteudo_texto: str,
                              data_assinatura: str) -> bool:
        """
        Atualiza consentimento existente
        
        Args:
            consentimento_id: ID do consentimento
            conteudo_html: Conteúdo HTML
            conteudo_texto: Conteúdo texto
            data_assinatura: Data da assinatura
            
        Returns:
            True se sucesso
        """
        query = '''
            UPDATE consentimentos 
            SET conteudo_html = ?, conteudo_texto = ?, data_assinatura = ?
            WHERE id = ?
        '''
        
        try:
            DatabaseService.executar_query(
                query,
                (conteudo_html, conteudo_texto, data_assinatura, consentimento_id),
                commit=True
            )
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao atualizar consentimento: {e}")
            return False
    
    @staticmethod
    def criar_consentimento(paciente_id: str,
                          tipo_consentimento: str,
                          conteudo_html: str,
                          conteudo_texto: str,
                          nome_paciente: str,
                          nome_terapeuta: str = "Dr. Nuno Correia",
                          status: str = "nao_assinado") -> Optional[int]:
        """
        Cria novo consentimento
        
        Args:
            paciente_id: ID do paciente
            tipo_consentimento: Tipo do consentimento
            conteudo_html: Conteúdo HTML
            conteudo_texto: Conteúdo texto
            nome_paciente: Nome do paciente
            nome_terapeuta: Nome do terapeuta
            status: Status inicial
            
        Returns:
            ID do novo consentimento ou None se falhou
        """
        from ..utils import DateUtils
        data_atual = DateUtils.data_atual_completa()
        
        query = '''
            INSERT INTO consentimentos 
            (paciente_id, tipo_consentimento, data_assinatura, conteudo_html, conteudo_texto, 
             nome_paciente, nome_terapeuta, status, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        try:
            consentimento_id = DatabaseService.executar_query(
                query,
                (paciente_id, tipo_consentimento, data_atual, conteudo_html, conteudo_texto,
                 nome_paciente, nome_terapeuta, status, data_atual),
                commit=True
            )
            return consentimento_id
        except Exception as e:
            print(f"[ERRO] Falha ao criar consentimento: {e}")
            return None
    
    @staticmethod
    def salvar_ou_atualizar_consentimento(paciente_data: Dict[str, Any],
                                        tipo_consentimento: str,
                                        conteudo_html: str,
                                        conteudo_texto: str) -> Tuple[bool, Optional[int]]:
        """
        Salva ou atualiza consentimento (operação combinada)
        
        Args:
            paciente_data: Dados do paciente
            tipo_consentimento: Tipo do consentimento
            conteudo_html: Conteúdo HTML
            conteudo_texto: Conteúdo texto
            
        Returns:
            Tupla (sucesso, consentimento_id)
        """
        paciente_id = paciente_data.get('id')
        nome_paciente = paciente_data.get('nome', 'Paciente')
        
        if not paciente_id:
            return False, None
        
        # Verificar se existe
        consentimento_id = DatabaseService.verificar_consentimento_existe(
            paciente_id, tipo_consentimento
        )
        
        from ..utils import DateUtils
        data_atual = DateUtils.data_atual_completa()
        
        if consentimento_id:
            # Atualizar existente
            sucesso = DatabaseService.atualizar_consentimento(
                consentimento_id, conteudo_html, conteudo_texto, data_atual
            )
            return sucesso, consentimento_id
        else:
            # Criar novo
            novo_id = DatabaseService.criar_consentimento(
                paciente_id, tipo_consentimento, conteudo_html, 
                conteudo_texto, nome_paciente
            )
            return novo_id is not None, novo_id
    
    @staticmethod
    def atualizar_assinaturas_consentimento(consentimento_id: int,
                                          assinatura_paciente: bytes = None,
                                          assinatura_terapeuta: bytes = None) -> bool:
        """
        Atualiza assinaturas de um consentimento
        
        Args:
            consentimento_id: ID do consentimento
            assinatura_paciente: Dados da assinatura do paciente
            assinatura_terapeuta: Dados da assinatura do terapeuta
            
        Returns:
            True se sucesso
        """
        updates = []
        params = []
        
        if assinatura_paciente is not None:
            updates.append("assinatura_paciente = ?")
            params.append(assinatura_paciente)
        
        if assinatura_terapeuta is not None:
            updates.append("assinatura_terapeuta = ?")
            params.append(assinatura_terapeuta)
        
        if not updates:
            return True  # Nada para atualizar
        
        params.append(consentimento_id)  # WHERE id = ?
        
        query = f'''
            UPDATE consentimentos 
            SET {', '.join(updates)}
            WHERE id = ?
        '''
        
        try:
            DatabaseService.executar_query(query, tuple(params), commit=True)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao atualizar assinaturas: {e}")
            return False
    
    @staticmethod
    def anular_consentimento(consentimento_id: int, motivo: str = "") -> bool:
        """
        Anula um consentimento
        
        Args:
            consentimento_id: ID do consentimento
            motivo: Motivo da anulação
            
        Returns:
            True se sucesso
        """
        from ..utils import DateUtils
        data_anulacao = DateUtils.data_atual_completa()
        
        query = '''
            UPDATE consentimentos 
            SET status = ?, motivo_anulacao = ?, data_anulacao = ?
            WHERE id = ?
        '''
        
        try:
            DatabaseService.executar_query(
                query,
                ("anulado", motivo, data_anulacao, consentimento_id),
                commit=True
            )
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao anular consentimento: {e}")
            return False
    
    # === OPERAÇÕES DE PACIENTES ===
    
    @staticmethod
    def buscar_paciente_por_id(paciente_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca paciente por ID
        
        Args:
            paciente_id: ID do paciente
            
        Returns:
            Dados do paciente ou None
        """
        query = '''
            SELECT * FROM pacientes WHERE id = ?
        '''
        
        resultado = DatabaseService.executar_query(
            query, 
            (paciente_id,),
            fetch_one=True
        )
        
        if resultado:
            return dict(resultado)
        
        return None
    
    @staticmethod
    def listar_consentimentos_paciente(paciente_id: str, 
                                     status_filtro: str = None) -> List[Dict[str, Any]]:
        """
        Lista consentimentos de um paciente
        
        Args:
            paciente_id: ID do paciente
            status_filtro: Filtro por status (opcional)
            
        Returns:
            Lista de consentimentos
        """
        query = '''
            SELECT id, tipo_consentimento, data_assinatura, status, nome_terapeuta
            FROM consentimentos 
            WHERE paciente_id = ?
        '''
        params = [paciente_id]
        
        if status_filtro:
            query += " AND status = ?"
            params.append(status_filtro)
        
        query += " ORDER BY data_assinatura DESC"
        
        resultados = DatabaseService.executar_query(
            query,
            tuple(params),
            fetch_all=True
        )
        
        return [dict(row) for row in resultados] if resultados else []
    
    @staticmethod
    def verificar_tabelas_existem() -> bool:
        """
        Verifica se as tabelas necessárias existem
        
        Returns:
            True se todas as tabelas existem
        """
        try:
            with DatabaseService.obter_conexao() as conn:
                cursor = conn.cursor()
                
                # Verificar tabela consentimentos
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='consentimentos'
                ''')
                
                if not cursor.fetchone():
                    return False
                
                # Verificar tabela pacientes
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='pacientes'
                ''')
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            print(f"[ERRO] Falha ao verificar tabelas: {e}")
            return False
    
    @staticmethod
    def obter_estatisticas_database() -> Dict[str, Any]:
        """
        Obtém estatísticas do banco de dados
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_pacientes': 0,
            'total_consentimentos': 0,
            'consentimentos_assinados': 0,
            'consentimentos_nao_assinados': 0,
            'consentimentos_anulados': 0,
            'tamanho_db_mb': 0
        }
        
        try:
            # Contar pacientes
            resultado = DatabaseService.executar_query(
                "SELECT COUNT(*) as total FROM pacientes",
                fetch_one=True
            )
            if resultado:
                stats['total_pacientes'] = resultado['total']
            
            # Contar consentimentos
            resultado = DatabaseService.executar_query(
                "SELECT COUNT(*) as total FROM consentimentos",
                fetch_one=True
            )
            if resultado:
                stats['total_consentimentos'] = resultado['total']
            
            # Contar por status
            for status, key in [
                ('assinado', 'consentimentos_assinados'),
                ('nao_assinado', 'consentimentos_nao_assinados'),
                ('anulado', 'consentimentos_anulados')
            ]:
                resultado = DatabaseService.executar_query(
                    "SELECT COUNT(*) as total FROM consentimentos WHERE status = ?",
                    (status,),
                    fetch_one=True
                )
                if resultado:
                    stats[key] = resultado['total']
            
            # Tamanho do arquivo de banco
            if os.path.exists(DatabaseService.DEFAULT_DB_PATH):
                tamanho_bytes = os.path.getsize(DatabaseService.DEFAULT_DB_PATH)
                stats['tamanho_db_mb'] = round(tamanho_bytes / (1024 * 1024), 2)
            
        except Exception as e:
            print(f"[ERRO] Falha ao obter estatísticas: {e}")
        
        return stats
