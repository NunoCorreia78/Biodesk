import sqlite3
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)

class DBManager:
    _instance = None
    _initialized = False
    
    def __new__(cls, db_path: str = 'pacientes.db'):
        """Implementa padrão singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = 'pacientes.db'):
        # Só inicializa uma vez
        if not self._initialized:
            self.db_path = db_path
            self._ensure_tables()
            self._initialized = True
    
    @classmethod
    def get_instance(cls, db_path: str = 'pacientes.db'):
        """Retorna a instância singleton do DBManager"""
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _ensure_tables(self):
        """Garante que todas as tabelas necessárias existem"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # Verificar se a tabela imagens_iris existe
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS imagens_iris (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        paciente_id INTEGER NOT NULL,
                        tipo TEXT NOT NULL,
                        caminho_imagem TEXT NOT NULL,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
                    )
                """)
                
                # ═══════════════ MIGRAÇÃO SEGURA: ANÁLISE DE ÍRIS ═══════════════
                # Adicionar novas colunas se não existirem (compatibilidade com BD antigas)
                self._add_column_if_not_exists(cursor, 'imagens_iris', 'constituicao', 'TEXT')
                self._add_column_if_not_exists(cursor, 'imagens_iris', 'sinais', 'TEXT')
                self._add_column_if_not_exists(cursor, 'imagens_iris', 'data_analise', 'TIMESTAMP')
                
                # ═══════════════ MIGRAÇÃO SEGURA: DECLARAÇÃO DE SAÚDE ═══════════════
                # Adicionar campos para declaração de estado de saúde na tabela pacientes
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_html', 'TEXT')
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_data', 'TEXT')
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_assinada', 'BOOLEAN DEFAULT 0')
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_data_assinatura', 'TEXT')
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_dados', 'TEXT')  # JSON dos dados do formulário
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_primeira_criacao', 'TEXT')  # Data primeiro preenchimento
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_ultima_alteracao', 'TEXT')  # Data última alteração
                self._add_column_if_not_exists(cursor, 'pacientes', 'declaracao_saude_hash', 'TEXT')  # Hash para detectar alterações
                
                # ═══════════════ MIGRAÇÃO SEGURA: OBSERVAÇÕES ═══════════════
                # Adicionar campo de observações na tabela pacientes
                self._add_column_if_not_exists(cursor, 'pacientes', 'observacoes', 'TEXT')
                
                # ═══════════════ MIGRAÇÃO SEGURA: COMO CONHECEU ═══════════════
                # Adicionar campo "como nos conheceu" na tabela pacientes
                self._add_column_if_not_exists(cursor, 'pacientes', 'conheceu', 'TEXT')
                
                # ═══════════════ MIGRAÇÃO SEGURA: CAMPOS ATUAIS DA INTERFACE ═══════════════
                # Apenas campos que EXISTEM na interface atual
                self._add_column_if_not_exists(cursor, 'pacientes', 'referenciado', 'TEXT')
                self._add_column_if_not_exists(cursor, 'pacientes', 'nif', 'TEXT')
                
                # ═══════════════ CAMPOS HISTÓRICOS (só compatibilidade) ═══════════════
                # Mantidos para não quebrar dados antigos, mas não usados na interface atual
                self._add_column_if_not_exists(cursor, 'pacientes', 'notas', 'TEXT')
                self._add_column_if_not_exists(cursor, 'pacientes', 'historico', 'TEXT')
                
                conn.commit()
        except Exception as e:
            logging.error(f"[ERRO ao criar tabelas] {e}")

    def _add_column_if_not_exists(self, cursor, table_name: str, column_name: str, column_type: str):
        """Adiciona uma coluna à tabela se ela não existir (migração segura)"""
        try:
            # Verificar se a coluna já existe
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        except Exception as e:
            pass  # Ignorar erros de migração

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logging.error(f"[ERRO BD] {e}")
            return []

    def execute_query_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        results = self.execute_query(query, params)
        return results[0] if results else None

    def get_all_pacientes(self) -> List[Dict[str, Any]]:
        return self.execute_query("SELECT * FROM pacientes")

    def search_pacientes(self, query: str) -> List[Dict[str, Any]]:
        return self.execute_query("SELECT * FROM pacientes WHERE nome LIKE ?", (f'%{query}%',))

    def get_paciente_by_id(self, paciente_id: int) -> Optional[Dict[str, Any]]:
        return self.execute_query_one("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))

    def save_or_update_paciente(self, paciente: dict) -> int:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                if 'id' in paciente and paciente['id']:
                    # Update
                    campos = [k for k in paciente.keys() if k != 'id']
                    sets = ', '.join([f'{k}=?' for k in campos])
                    values = [paciente[k] for k in campos] + [paciente['id']]
                    cur.execute(f'UPDATE pacientes SET {sets} WHERE id=?', values)
                else:
                    # Insert
                    campos = ', '.join(paciente.keys())
                    qs = ', '.join(['?'] * len(paciente))
                    values = [paciente[k] for k in paciente]
                    cur.execute(f'INSERT INTO pacientes ({campos}) VALUES ({qs})', values)
                    paciente['id'] = cur.lastrowid
                conn.commit()
                return paciente.get('id', -1)
        except Exception as e:
            logging.error(f'[ERRO ao guardar paciente] {e}')
            return -1

    def update_paciente(self, paciente_id: int, paciente_data: dict) -> bool:
        """Atualiza dados de um paciente específico"""
        try:
            # Garantir que o ID está nos dados
            paciente_data['id'] = paciente_id
            result = self.save_or_update_paciente(paciente_data)
            return result != -1
        except Exception as e:
            logging.error(f'[ERRO ao atualizar paciente] {e}')
            return False

    def get_imagens_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        return self.execute_query("SELECT * FROM imagens_iris WHERE paciente_id = ?", (paciente_id,))

    def adicionar_imagem_iris(self, paciente_id: int, tipo: str, caminho: str) -> None:
        """Adiciona uma nova imagem de íris à base de dados"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO imagens_iris (paciente_id, tipo, caminho_imagem) VALUES (?, ?, ?)", 
                    (paciente_id, tipo, caminho)
                )
                conn.commit()
                print(f"✅ Imagem de íris adicionada: {tipo} para paciente {paciente_id}")
        except Exception as e:
            logging.error(f"[ERRO ao adicionar imagem] {e}")
            print(f"❌ Erro ao adicionar imagem: {e}")
            raise

    # ═══════════════ NOVOS MÉTODOS: ANÁLISE DE ÍRIS ═══════════════
    
    def atualizar_analise_iris(self, imagem_id: int, constituicao: str = None, sinais: str = None) -> bool:
        """
        Atualiza os dados de análise de íris para uma imagem específica
        
        Args:
            imagem_id: ID da imagem na tabela imagens_iris
            constituicao: Tipo de constituição (ex: "Linfática", "Hematogénea", "Mista")
            sinais: Lista de sinais em formato JSON ou texto separado por vírgulas
        
        Returns:
            bool: True se atualização bem-sucedida
        """
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # Preparar campos para atualizar
                campos = []
                valores = []
                
                if constituicao is not None:
                    campos.append("constituicao = ?")
                    valores.append(constituicao)
                
                if sinais is not None:
                    campos.append("sinais = ?")
                    valores.append(sinais)
                
                if campos:
                    campos.append("data_analise = CURRENT_TIMESTAMP")
                    valores.append(imagem_id)
                    
                    query = f"UPDATE imagens_iris SET {', '.join(campos)} WHERE id = ?"
                    cursor.execute(query, valores)
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        print(f"✅ Análise de íris atualizada para imagem {imagem_id}")
                        return True
                    else:
                        print(f"⚠️ Nenhuma imagem encontrada com ID {imagem_id}")
                        return False
                else:
                    print("⚠️ Nenhum dado fornecido para atualizar")
                    return False
                    
        except Exception as e:
            logging.error(f"[ERRO ao atualizar análise] {e}")
            print(f"❌ Erro ao atualizar análise: {e}")
            return False

    def obter_analise_iris(self, imagem_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém os dados de análise de íris para uma imagem específica
        
        Args:
            imagem_id: ID da imagem na tabela imagens_iris
            
        Returns:
            Dict com constituicao, sinais, data_analise ou None se não encontrado
        """
        try:
            resultado = self.execute_query_one(
                "SELECT constituicao, sinais, data_analise FROM imagens_iris WHERE id = ?", 
                (imagem_id,)
            )
            
            if resultado:
                print(f"✅ Análise obtida para imagem {imagem_id}")
                return resultado
            else:
                print(f"ℹ️ Nenhuma análise encontrada para imagem {imagem_id}")
                return None
                
        except Exception as e:
            logging.error(f"[ERRO ao obter análise] {e}")
            print(f"❌ Erro ao obter análise: {e}")
            return None

    def obter_ultimas_analises_paciente(self, paciente_id: int, limite: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém as últimas análises de íris de um paciente
        
        Args:
            paciente_id: ID do paciente
            limite: Número máximo de análises a retornar
            
        Returns:
            Lista de análises ordenadas por data (mais recente primeiro)
        """
        try:
            return self.execute_query("""
                SELECT id, tipo, constituicao, sinais, data_analise, data_criacao
                FROM imagens_iris 
                WHERE paciente_id = ? AND (constituicao IS NOT NULL OR sinais IS NOT NULL)
                ORDER BY data_analise DESC, data_criacao DESC
                LIMIT ?
            """, (paciente_id, limite))
        except Exception as e:
            logging.error(f"[ERRO ao obter últimas análises] {e}")
            print(f"❌ Erro ao obter últimas análises: {e}")
            return []

    def adicionar_historico(self, paciente_id: int, novo_historico: str) -> bool:
        """
        Adiciona uma entrada ao histórico de um paciente
        
        Args:
            paciente_id: ID do paciente
            novo_historico: Texto do histórico a adicionar
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            # Obter histórico atual
            paciente = self.get_paciente_by_id(paciente_id)
            if not paciente:
                print(f"❌ Paciente {paciente_id} não encontrado")
                return False
                
            historico_atual = paciente.get('historico', '') or ''
            
            # Adicionar nova entrada
            if historico_atual:
                historico_atualizado = historico_atual + '\n' + novo_historico
            else:
                historico_atualizado = novo_historico
            
            # Atualizar na base de dados
            return self.update_paciente(paciente_id, {'historico': historico_atualizado})
            
        except Exception as e:
            logging.error(f"[ERRO ao adicionar histórico] {e}")
            print(f"❌ Erro ao adicionar histórico: {e}")
            return False

    def obter_paciente(self, paciente_id: int) -> Optional[Dict[str, Any]]:
        """
        Alias para get_paciente_by_id para compatibilidade
        """
        return self.get_paciente_by_id(paciente_id)

    def registar_envio_falhado(self, paciente_id: int, assunto: str, corpo: str, data_tentativa: str, erro: str = "") -> bool:
        """
        Regista um envio de email falhado no histórico do paciente
        
        Args:
            paciente_id: ID do paciente
            assunto: Assunto do email
            corpo: Primeiro texto do corpo (truncado)
            data_tentativa: Data da tentativa
            erro: Mensagem de erro (opcional)
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            corpo_truncado = corpo[:100] + "..." if len(corpo) > 100 else corpo
            erro_texto = f" (Erro: {erro})" if erro else ""
            historico_texto = f"[{data_tentativa}] ❌ FALHA envio email: {assunto} - {corpo_truncado}{erro_texto}"
            return self.adicionar_historico(paciente_id, historico_texto)
        except Exception as e:
            print(f"❌ Erro ao registar falha: {e}")
            return False
