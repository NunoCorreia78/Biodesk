"""
Módulo para gestão de consentimentos na base de dados
Compatível com o sistema Biodesk e RGPD
"""

import sqlite3
import os
from datetime import datetime
import json


class ConsentimentosManager:
    def __init__(self, db_path="pacientes.db"):
        self.db_path = db_path
        self.criar_tabela_consentimentos()
    
    def criar_tabela_consentimentos(self):
        """Cria a tabela de consentimentos se não existir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela de consentimentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consentimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER NOT NULL,
                    tipo_consentimento TEXT NOT NULL,
                    data_assinatura TEXT NOT NULL,
                    conteudo_html TEXT,
                    conteudo_texto TEXT,
                    assinatura_paciente BLOB,
                    assinatura_terapeuta BLOB,
                    nome_paciente TEXT,
                    nome_terapeuta TEXT,
                    status TEXT DEFAULT 'assinado',
                    data_criacao TEXT NOT NULL,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
                )
            ''')
            
            # Adicionar colunas de nomes se não existirem (para compatibilidade)
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN nome_paciente TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
                
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN nome_terapeuta TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
            
            # Adicionar colunas de anulação se não existirem
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN data_anulacao TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
                
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN motivo_anulacao TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
                
            # Adicionar coluna para dados do formulário (declaração de saúde)
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN dados_formulario TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
                
            # Adicionar coluna para dados do formulário (novo sistema declaração)
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN dados_formulario TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
                
            # Adicionar coluna para dados de formulário (novo sistema de declaração)
            try:
                cursor.execute('ALTER TABLE consentimentos ADD COLUMN dados_formulario TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
            
            conn.commit()
            
        except Exception as e:
            pass  # Ignorar erros de criação
        finally:
            if conn:
                conn.close()
    
    def obter_status_consentimentos(self, paciente_id):
        """
        Obtém o status de todos os tipos de consentimento para um paciente
        
        Returns:
            dict: {tipo: {'status': 'assinado'|'anulado'|'nao_assinado', 'data': '05/08/2024', 'data_anulacao': '06/08/2024'}}
        """
        tipos_consentimento = [
            'naturopatia', 'osteopatia', 'iridologia', 
            'quantica', 'mesoterapia', 'rgpd'
        ]
        
        status = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for tipo in tipos_consentimento:
                # Buscar o consentimento mais recente deste tipo
                cursor.execute('''
                    SELECT data_assinatura, status, data_anulacao 
                    FROM consentimentos 
                    WHERE paciente_id = ? AND tipo_consentimento = ?
                    ORDER BY data_assinatura DESC 
                    LIMIT 1
                ''', (paciente_id, tipo))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    data_assinatura, status_db, data_anulacao = resultado
                    
                    # Converter data para formato português
                    try:
                        dt = datetime.strptime(data_assinatura, '%Y-%m-%d %H:%M:%S')
                        data_formatada = dt.strftime('%d/%m/%Y')
                    except:
                        data_formatada = data_assinatura
                    
                    # Converter data de anulação se existir
                    data_anulacao_formatada = None
                    if data_anulacao:
                        try:
                            dt_anulacao = datetime.strptime(data_anulacao, '%Y-%m-%d %H:%M:%S')
                            data_anulacao_formatada = dt_anulacao.strftime('%d/%m/%Y')
                        except:
                            data_anulacao_formatada = data_anulacao
                    
                    # Determinar status final
                    status_final = status_db if status_db in ['assinado', 'anulado'] else 'nao_assinado'
                    
                    status[tipo] = {
                        'status': status_final,
                        'data': data_formatada,
                        'data_anulacao': data_anulacao_formatada
                    }
                else:
                    status[tipo] = {
                        'status': 'nao_assinado',
                        'data': None,
                        'data_anulacao': None
                    }
            
        except Exception as e:
            print(f"❌ Erro ao obter status de consentimentos: {e}")
            # Retornar status padrão em caso de erro
            for tipo in tipos_consentimento:
                status[tipo] = {'status': 'nao_assinado', 'data': None, 'data_anulacao': None}
        
        finally:
            if conn:
                conn.close()
        
        return status
    
    def guardar_consentimento(self, paciente_id, tipo_consentimento, conteudo_html, 
                            conteudo_texto, assinatura_paciente=None, assinatura_terapeuta=None,
                            nome_paciente=None, nome_terapeuta=None, dados_formulario=None):
        """
        Guarda um novo consentimento na base de dados
        
        Args:
            paciente_id (int): ID do paciente
            tipo_consentimento (str): Tipo do consentimento
            conteudo_html (str): Conteúdo HTML do consentimento
            conteudo_texto (str): Conteúdo em texto simples
            assinatura_paciente (bytes): Dados da assinatura do paciente
            assinatura_terapeuta (bytes): Dados da assinatura do terapeuta
            nome_paciente (str): Nome do paciente que assinou
            nome_terapeuta (str): Nome do terapeuta que assinou
            dados_formulario (str): Dados JSON do formulário (para declaração de saúde)
        
        Returns:
            bool: True se guardado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO consentimentos 
                (paciente_id, tipo_consentimento, data_assinatura, conteudo_html, 
                 conteudo_texto, assinatura_paciente, assinatura_terapeuta, 
                 nome_paciente, nome_terapeuta, status, data_criacao, dados_formulario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                paciente_id, tipo_consentimento, data_atual, conteudo_html,
                conteudo_texto, assinatura_paciente, assinatura_terapeuta,
                nome_paciente, nome_terapeuta, 'assinado', data_atual, dados_formulario
            ))
            
            conn.commit()
            print(f"✅ Consentimento '{tipo_consentimento}' guardado para paciente {paciente_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao guardar consentimento: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def obter_historico_consentimentos(self, paciente_id):
        """
        Obtém o histórico completo de consentimentos de um paciente
        
        Returns:
            list: Lista de dicionários com dados dos consentimentos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, tipo_consentimento, data_assinatura, status,
                       nome_paciente, nome_terapeuta
                FROM consentimentos 
                WHERE paciente_id = ?
                ORDER BY data_assinatura DESC
            ''', (paciente_id,))
            
            resultados = cursor.fetchall()
            historico = []
            
            for resultado in resultados:
                id_consentimento, tipo, data, status, nome_paciente, nome_terapeuta = resultado
                
                # Converter data para formato português
                try:
                    dt = datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
                    data_formatada = dt.strftime('%d/%m/%Y às %H:%M')
                except:
                    data_formatada = data
                
                # Mapear tipos para nomes amigáveis
                nomes_tipos = {
                    'naturopatia': '🌿 Naturopatia',
                    'osteopatia': '🦴 Osteopatia',
                    'iridologia': '👁️ Iridologia',
                    'quantica': '⚡ Medicina Quântica',
                    'mesoterapia': '💉 Mesoterapia',
                    'rgpd': '🛡️ RGPD'
                }
                
                # Criar informação de assinaturas
                assinaturas_info = []
                if nome_paciente:
                    assinaturas_info.append(f"👤 Paciente: {nome_paciente}")
                if nome_terapeuta:
                    assinaturas_info.append(f"👨‍⚕️ Terapeuta: {nome_terapeuta}")
                
                assinaturas_texto = " • ".join(assinaturas_info) if assinaturas_info else "Sem assinaturas registadas"
                
                historico.append({
                    'id': id_consentimento,
                    'tipo': tipo,
                    'nome_tipo': nomes_tipos.get(tipo, tipo.title()),
                    'data': data_formatada,
                    'status': status,
                    'nome_paciente': nome_paciente,
                    'nome_terapeuta': nome_terapeuta,
                    'assinaturas': assinaturas_texto
                })
            
            return historico
            
        except Exception as e:
            print(f"❌ Erro ao obter histórico de consentimentos: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def obter_consentimento_por_id(self, consentimento_id):
        """
        Obtém um consentimento específico pelo ID
        
        Returns:
            dict: Dados completos do consentimento
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, paciente_id, tipo_consentimento, data_assinatura,
                       conteudo_html, conteudo_texto, status, nome_paciente, nome_terapeuta,
                       assinatura_paciente, assinatura_terapeuta, data_anulacao, motivo_anulacao
                FROM consentimentos 
                WHERE id = ?
            ''', (consentimento_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    'id': resultado[0],
                    'paciente_id': resultado[1],
                    'tipo': resultado[2],
                    'data_assinatura': resultado[3],
                    'conteudo_html': resultado[4],
                    'conteudo_texto': resultado[5],
                    'status': resultado[6],
                    'nome_paciente': resultado[7],
                    'nome_terapeuta': resultado[8],
                    'assinatura_paciente': resultado[9],
                    'assinatura_terapeuta': resultado[10],
                    'data_anulacao': resultado[11],
                    'motivo_anulacao': resultado[12]
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erro ao obter consentimento por ID: {e}")
            return None
        
        finally:
            if conn:
                conn.close()

    def atualizar_assinatura_paciente(self, consentimento_id, assinatura_blob, nome_paciente):
        """
        Atualiza a assinatura do paciente num consentimento existente
        
        Args:
            consentimento_id (int): ID do consentimento
            assinatura_blob (bytes): Dados binários da assinatura
            nome_paciente (str): Nome do paciente
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE consentimentos 
                SET assinatura_paciente = ?, nome_paciente = ?
                WHERE id = ?
            ''', (assinatura_blob, nome_paciente, consentimento_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Assinatura do paciente atualizada (ID: {consentimento_id})")
                return True
            else:
                print(f"❌ Consentimento não encontrado (ID: {consentimento_id})")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar assinatura do paciente: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def atualizar_assinatura_terapeuta(self, consentimento_id, assinatura_blob, nome_terapeuta):
        """
        Atualiza a assinatura do terapeuta num consentimento existente
        
        Args:
            consentimento_id (int): ID do consentimento
            assinatura_blob (bytes): Dados binários da assinatura
            nome_terapeuta (str): Nome do terapeuta
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE consentimentos 
                SET assinatura_terapeuta = ?, nome_terapeuta = ?
                WHERE id = ?
            ''', (assinatura_blob, nome_terapeuta, consentimento_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Assinatura do terapeuta atualizada (ID: {consentimento_id})")
                return True
            else:
                print(f"❌ Consentimento não encontrado (ID: {consentimento_id})")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar assinatura do terapeuta: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def verificar_assinaturas_completas(self, consentimento_id):
        """
        Verifica se um consentimento tem ambas as assinaturas
        
        Args:
            consentimento_id (int): ID do consentimento
            
        Returns:
            dict: {'paciente': bool, 'terapeuta': bool, 'completo': bool}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT assinatura_paciente, assinatura_terapeuta
                FROM consentimentos 
                WHERE id = ?
            ''', (consentimento_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                assinatura_paciente, assinatura_terapeuta = resultado
                
                tem_paciente = assinatura_paciente is not None and len(assinatura_paciente) > 0
                tem_terapeuta = assinatura_terapeuta is not None and len(assinatura_terapeuta) > 0
                
                return {
                    'paciente': tem_paciente,
                    'terapeuta': tem_terapeuta,
                    'completo': tem_paciente and tem_terapeuta
                }
            else:
                return {'paciente': False, 'terapeuta': False, 'completo': False}
                
        except Exception as e:
            print(f"❌ Erro ao verificar assinaturas: {e}")
            return {'paciente': False, 'terapeuta': False, 'completo': False}
        finally:
            if conn:
                conn.close()

    def obter_assinatura(self, paciente_id, tipo_documento, tipo_assinatura):
        """
        Obtém assinatura específica de um documento
        
        Args:
            paciente_id (int): ID do paciente
            tipo_documento (str): Tipo do documento (ex: 'declaracao_saude', 'termo_medicamentos')
            tipo_assinatura (str): Tipo da assinatura ('paciente' ou 'terapeuta')
            
        Returns:
            bytes or None: Dados binários da assinatura ou None se não encontrada
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Determinar coluna da assinatura
            coluna_assinatura = f"assinatura_{tipo_assinatura}"
            
            cursor.execute(f'''
                SELECT {coluna_assinatura}
                FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = ? AND {coluna_assinatura} IS NOT NULL
                ORDER BY data_criacao DESC
                LIMIT 1
            ''', (paciente_id, tipo_documento))
            
            resultado = cursor.fetchone()
            
            if resultado and resultado[0]:
                print(f"✅ Assinatura encontrada: {tipo_assinatura} para {tipo_documento}")
                return resultado[0]
            else:
                print(f"❌ Assinatura não encontrada: {tipo_assinatura} para {tipo_documento}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao obter assinatura: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def guardar_assinatura_declaracao(self, paciente_id, tipo_documento, tipo_assinatura, assinatura_blob, nome_pessoa):
        """
        Guarda assinatura para documentos como declaração de saúde - VERSÃO CORRIGIDA
        
        Args:
            paciente_id (int): ID do paciente
            tipo_documento (str): Tipo do documento (ex: 'declaracao_saude')
            tipo_assinatura (str): Tipo da assinatura ('paciente' ou 'terapeuta')
            assinatura_blob (bytes): Dados binários da assinatura
            nome_pessoa (str): Nome da pessoa que assinou
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se já existe um registo para este documento (pegar o mais recente)
            cursor.execute('''
                SELECT id FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = ?
                ORDER BY data_criacao DESC
                LIMIT 1
            ''', (paciente_id, tipo_documento))
            
            resultado = cursor.fetchone()
            
            if resultado:
                # Atualizar registo existente - fazer inline para evitar dupla conexão
                consentimento_id = resultado[0]
                coluna_assinatura = f"assinatura_{tipo_assinatura}"
                coluna_nome = f"nome_{tipo_assinatura}"
                
                cursor.execute(f'''
                    UPDATE consentimentos 
                    SET {coluna_assinatura} = ?, {coluna_nome} = ?
                    WHERE id = ?
                ''', (assinatura_blob, nome_pessoa, consentimento_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"✅ Assinatura {tipo_assinatura} atualizada para {tipo_documento} (ID: {consentimento_id})")
                    return True
                else:
                    print(f"❌ Falha ao atualizar assinatura {tipo_assinatura} para {tipo_documento}")
                    return False
            else:
                # Criar novo registo
                data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Preparar colunas para inserção
                if tipo_assinatura == 'paciente':
                    cursor.execute('''
                        INSERT INTO consentimentos 
                        (paciente_id, tipo_consentimento, data_assinatura, data_criacao, 
                         conteudo_html, conteudo_texto, assinatura_paciente, nome_paciente)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (paciente_id, tipo_documento, data_atual, data_atual, '', '', assinatura_blob, nome_pessoa))
                else:
                    cursor.execute('''
                        INSERT INTO consentimentos 
                        (paciente_id, tipo_consentimento, data_assinatura, data_criacao, 
                         conteudo_html, conteudo_texto, assinatura_terapeuta, nome_terapeuta)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (paciente_id, tipo_documento, data_atual, data_atual, '', '', assinatura_blob, nome_pessoa))
                
                conn.commit()
                consentimento_id = cursor.lastrowid
                
                print(f"✅ Nova assinatura {tipo_assinatura} criada para {tipo_documento} (ID: {consentimento_id})")
                return True
                    
        except Exception as e:
            print(f"❌ Erro ao guardar assinatura da declaração: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def anular_consentimento(self, paciente_id, tipo_consentimento, motivo_anulacao):
        """
        Anula um consentimento existente
        
        Args:
            paciente_id (int): ID do paciente
            tipo_consentimento (str): Tipo do consentimento a anular
            motivo_anulacao (str): Motivo da anulação
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar consentimento ativo mais recente
            cursor.execute('''
                SELECT id, data_assinatura 
                FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = ? AND status != 'anulado'
                ORDER BY data_assinatura DESC 
                LIMIT 1
            ''', (paciente_id, tipo_consentimento))
            
            consentimento = cursor.fetchone()
            
            if not consentimento:
                print(f"❌ Nenhum consentimento ativo encontrado para anular: {tipo_consentimento}")
                return False
            
            consentimento_id = consentimento[0]
            
            # Anular o consentimento
            data_anulacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE consentimentos 
                SET status = 'anulado', 
                    data_anulacao = ?,
                    motivo_anulacao = ?
                WHERE id = ?
            ''', (data_anulacao, motivo_anulacao, consentimento_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Consentimento {tipo_consentimento} anulado com sucesso (ID: {consentimento_id})")
                return True
            else:
                print(f"❌ Falha ao anular consentimento {tipo_consentimento}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao anular consentimento: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def obter_consentimento_para_anulacao(self, paciente_id, tipo_consentimento):
        """Obtém dados do consentimento para gerar PDF anulado"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT conteudo_html, conteudo_texto, nome_paciente, nome_terapeuta, data_assinatura
                FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = ? AND status != 'anulado'
                ORDER BY data_criacao DESC
                LIMIT 1
            ''', (paciente_id, tipo_consentimento))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    'conteudo_html': resultado[0] or '',
                    'conteudo_texto': resultado[1] or '',
                    'nome_paciente': resultado[2] or '',
                    'nome_terapeuta': resultado[3] or '',
                    'data_assinatura': resultado[4] or ''
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erro ao obter consentimento para anulação: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def obter_declaracao_anterior(self, paciente_id, tipo_documento='declaracao_saude'):
        """
        Obtém a declaração anterior mais recente para comparação
        
        Args:
            paciente_id (int): ID do paciente
            tipo_documento (str): Tipo do documento
            
        Returns:
            dict or None: Dados da declaração anterior ou None se não existir
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, conteudo_texto, data_criacao, status, conteudo_html, dados_formulario 
                FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = ?
                ORDER BY data_criacao DESC
                LIMIT 1
            ''', (paciente_id, tipo_documento))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    'id': resultado[0],
                    'conteudo_texto': resultado[1] or '',
                    'data_criacao': resultado[2],
                    'status': resultado[3] or 'assinado',
                    'conteudo_html': resultado[4] or '',
                    'dados_formulario': resultado[5] or ''
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao obter declaração anterior: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def marcar_declaracao_como_alterada(self, declaracao_id):
        """
        Marca uma declaração como alterada/anulada
        
        Args:
            declaracao_id (int): ID da declaração a marcar
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_alteracao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE consentimentos 
                SET status = ?, data_assinatura = ?
                WHERE id = ?
            ''', (f'alterada_em_{data_alteracao}', data_alteracao, declaracao_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Declaração {declaracao_id} marcada como alterada")
                return True
            else:
                print(f"❌ Falha ao marcar declaração {declaracao_id} como alterada")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao marcar declaração como alterada: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def criar_nova_declaracao_com_conteudo(self, paciente_id, conteudo_texto, tipo_documento='declaracao_saude', conteudo_html=None):
        """
        Cria uma nova declaração com conteúdo específico
        
        Args:
            paciente_id (int): ID do paciente
            conteudo_texto (str): Conteúdo da declaração (texto simples)
            tipo_documento (str): Tipo do documento
            conteudo_html (str): Conteúdo HTML da declaração (opcional)
            
        Returns:
            int or None: ID da nova declaração criada ou None se erro
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO consentimentos 
                (paciente_id, tipo_consentimento, data_assinatura, data_criacao, 
                 conteudo_texto, conteudo_html, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (paciente_id, tipo_documento, data_atual, data_atual, conteudo_texto, conteudo_html, 'pendente_assinatura'))
            
            conn.commit()
            consentimento_id = cursor.lastrowid
            
            print(f"✅ Nova declaração criada com ID: {consentimento_id}")
            return consentimento_id
            
        except Exception as e:
            print(f"❌ Erro ao criar nova declaração: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def verificar_status_declaracao_por_arquivo(self, paciente_id, nome_arquivo):
        """
        Verifica se uma declaração (por nome de arquivo) foi alterada
        LÓGICA CORRIGIDA: Apenas a mais recente fica ativa, as antigas ficam "sem efeito"
        
        Args:
            paciente_id (int): ID do paciente
            nome_arquivo (str): Nome do arquivo PDF (ex: "Declaracao_Saude_20250818_222629.pdf")
            
        Returns:
            dict or None: {'status': 'ativa'/'alterada', 'data_alteracao': datetime} ou None se não encontrado
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extrair timestamp do nome do arquivo
            import re
            match = re.search(r'(\d{8}_\d{6})', nome_arquivo)
            if not match:
                return None
                
            timestamp = match.group(1)
            # Converter para formato da BD: "YYYY-MM-DD HH:MM:SS"
            ano = timestamp[:4]
            mes = timestamp[4:6]
            dia = timestamp[6:8]
            hora = timestamp[9:11]
            minuto = timestamp[11:13]
            segundo = timestamp[13:15]
            data_arquivo = f"{ano}-{mes}-{dia} {hora}:{minuto}:{segundo}"
            
            # 1. PRIMEIRO: Obter a declaração MAIS RECENTE do paciente (apenas ativas)
            cursor.execute('''
                SELECT data_assinatura, status 
                FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = 'declaracao_saude'
                AND (status = 'assinado' OR status IS NULL OR status = 'pendente_assinatura')
                ORDER BY data_assinatura DESC
                LIMIT 1
            ''', (paciente_id,))
            
            declaracao_mais_recente = cursor.fetchone()
            
            if not declaracao_mais_recente:
                # Não há declarações, então esta é a primeira
                return {'status': 'ativa', 'data_alteracao': None}
            
            data_mais_recente = declaracao_mais_recente[0]
            
            # 2. SEGUNDO: Comparar se este arquivo corresponde à declaração mais recente
            # Buscar declaração próxima a esta data (margem de 5 segundos para resolver discrepâncias)
            cursor.execute('''
                SELECT status, data_assinatura 
                FROM consentimentos 
                WHERE paciente_id = ? AND tipo_consentimento = 'declaracao_saude'
                AND ABS(strftime('%s', data_assinatura) - strftime('%s', ?)) <= 5
                ORDER BY ABS(strftime('%s', data_assinatura) - strftime('%s', ?))
                LIMIT 1
            ''', (paciente_id, data_arquivo, data_arquivo))
            
            declaracao_encontrada = cursor.fetchone()
            
            if not declaracao_encontrada:
                return None
            
            data_assinatura_encontrada = declaracao_encontrada[1]
            status_encontrado = declaracao_encontrada[0] or 'assinado'
            
            # 3. TERCEIRO: Determinar se é a mais recente
            if data_assinatura_encontrada == data_mais_recente:
                # Esta É a declaração mais recente = ATIVA
                return {'status': 'ativa', 'data_alteracao': None}
            else:
                # Esta NÃO é a mais recente = SEM EFEITO
                if status_encontrado.startswith('alterada_em_'):
                    # Extrair data de alteração
                    data_alteracao = status_encontrado.replace('alterada_em_', '')
                    return {
                        'status': 'alterada',
                        'data_alteracao': data_alteracao
                    }
                else:
                    # Foi substituída por uma mais recente
                    return {
                        'status': 'alterada',
                        'data_alteracao': data_mais_recente  # Data da mais recente que a substituiu
                    }
            
        except Exception as e:
            print(f"❌ Erro ao verificar status da declaração: {e}")
            return None
        finally:
            if conn:
                conn.close()


def teste_manager():
    """Função de teste para verificar o funcionamento do manager"""
    print("🧪 Testando ConsentimentosManager...")
    
    manager = ConsentimentosManager()
    
    # Teste com paciente ID fictício
    paciente_id = 1
    
    # Obter status atual
    status = manager.obter_status_consentimentos(paciente_id)
    print("📊 Status atual dos consentimentos:")
    for tipo, info in status.items():
        emoji_status = "✅" if info['status'] == 'assinado' else "❌"
        data_text = info['data'] if info['data'] else "Não assinado"
        print(f"   {tipo}: {emoji_status} {data_text}")
    
    print("✅ Teste concluído!")


if __name__ == "__main__":
    teste_manager()
