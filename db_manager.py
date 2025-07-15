import sqlite3
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)

class DBManager:
    def __init__(self, db_path: str = 'pacientes.db'):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

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

    def get_imagens_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        return self.execute_query("SELECT * FROM imagens_iris WHERE paciente_id = ?", (paciente_id,))

    def adicionar_imagem_iris(self, paciente_id: int, tipo: str, caminho: str) -> None:
        self.execute_query("INSERT INTO imagens_iris (paciente_id, tipo, caminho_imagem) VALUES (?, ?, ?)", (paciente_id, tipo, caminho))
