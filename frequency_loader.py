"""
Carregador de frequências do arquivo FrequencyList.xls
Converte dados do Excel para SQLite para uso no sistema
"""
import sqlite3
import json
import os
from pathlib import Path
import logging

# Imports opcionais para maior robustez
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
    print("✅ pandas disponível")
except ImportError:
    print("❌ pandas não disponível - funcionalidade limitada")
    PANDAS_AVAILABLE = False

class FrequencyLoader:
    """Carrega frequências do Excel para SQLite"""
    
    def __init__(self, excel_path="assets/FrequencyList.xls"):
        self.excel_path = excel_path
        self.db_path = "frequencies.db"
        self.init_db()
        
        # Tentar carregar automaticamente se o arquivo existir
        if os.path.exists(self.excel_path):
            self.load_from_excel()
    
    def init_db(self):
        """Cria base de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de condições e frequências
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frequency_protocols (
                id INTEGER PRIMARY KEY,
                condition_name TEXT NOT NULL,
                frequency REAL NOT NULL,
                description TEXT,
                source TEXT,
                category TEXT,
                amplitude REAL DEFAULT 3.0,
                duration INTEGER DEFAULT 5,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sessões de terapia
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS therapy_sessions (
                id INTEGER PRIMARY KEY,
                patient_id TEXT,
                protocol_name TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                frequencies_used TEXT,  -- JSON array
                amplitude REAL,
                duration INTEGER,
                notes TEXT,
                biofeedback_data TEXT  -- JSON
            )
        ''')
        
        # Tabela de protocolos personalizados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_protocols (
                id INTEGER PRIMARY KEY,
                protocol_name TEXT UNIQUE NOT NULL,
                frequencies TEXT NOT NULL,  -- JSON array
                description TEXT,
                created_by TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de dados inicializada")
    
    def load_from_excel(self):
        """Carrega dados do FrequencyList.xls"""
        if not PANDAS_AVAILABLE:
            print("❌ pandas não está disponível - impossível carregar Excel")
            # Carregar dados de exemplo se pandas não estiver disponível
            return self.load_sample_data()
        
        try:
            print(f"📥 Carregando frequências de {self.excel_path}...")
            
            # Verificar se arquivo existe
            if not os.path.exists(self.excel_path):
                print(f"❌ Arquivo não encontrado: {self.excel_path}")
                return self.load_sample_data()
            
            # Tentar diferentes engines para ler o Excel
            df = None
            for engine in ['xlrd', 'openpyxl']:
                try:
                    df = pd.read_excel(self.excel_path, engine=engine)
                    print(f"✅ Excel carregado com engine {engine}")
                    break
                except Exception as e:
                    print(f"⚠️ Tentativa com {engine} falhou: {e}")
                    continue
            
            if df is None:
                print("❌ Não foi possível carregar o Excel - usando dados de exemplo")
                return self.load_sample_data()
            
            print(f"📊 Excel carregado: {len(df)} linhas, {len(df.columns)} colunas")
            print(f"📋 Colunas disponíveis: {list(df.columns)}")
            
            # Limpar dados existentes
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM frequency_protocols WHERE source = "FrequencyList.xls"')
            
            # Processar cada linha do Excel
            loaded_count = 0
            for index, row in df.iterrows():
                try:
                    # Obter informações da condição
                    indicacao = str(row['Indikationen']).strip() if pd.notna(row['Indikationen']) else ""
                    disease = str(row['Disease']).strip() if pd.notna(row['Disease']) else ""
                    
                    # Usar Disease como nome da condição, fallback para Indikationen
                    condition_name = disease if disease and disease != 'nan' else indicacao
                    if not condition_name or condition_name == 'nan':
                        condition_name = f"Condição_{index}"
                    
                    # Processar todas as colunas de frequência (Freq 1 até Freq 254)
                    freq_columns = [col for col in df.columns if col.startswith('Freq ')]
                    
                    for freq_col in freq_columns:
                        try:
                            freq_value = row[freq_col]
                            
                            # Verificar se a frequência é válida
                            if pd.notna(freq_value) and freq_value > 0:
                                frequency = float(freq_value)
                                
                                # Filtro de frequências válidas (0.1Hz a 1MHz)
                                if 0.1 <= frequency <= 1000000:
                                    cursor.execute('''
                                        INSERT INTO frequency_protocols 
                                        (condition_name, frequency, description, source, category)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (condition_name, frequency, f"Frequência {frequency}Hz para {condition_name}", "FrequencyList.xls", "Rife"))
                                    
                                    loaded_count += 1
                        except (ValueError, TypeError):
                            # Ignorar valores que não podem ser convertidos para float
                            continue
                        
                except Exception as e:
                    print(f"⚠️ Erro na linha {index}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            print(f"✅ {loaded_count} frequências carregadas com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar Excel: {e}")
            return self.load_sample_data()
    
    def load_sample_data(self):
        """Carrega dados de exemplo quando o Excel não está disponível"""
        print("📥 Carregando dados de exemplo de frequências terapêuticas...")
        
        sample_frequencies = {
            "Relaxamento": [10, 7.83, 40, 100],
            "Energia": [20, 35, 95, 120],
            "Dor Geral": [95, 666, 727, 787, 880, 1550, 3000],
            "Stress": [432, 528, 664, 727, 787, 880, 1500, 1570, 10000],
            "Fadiga": [727, 776, 787, 802, 880, 1500, 1600, 1800, 2720],
            "Insónia": [3.59, 3, 7.83, 10, 802, 880, 1500, 1550],
            "Ansiedade": [0.5, 1.2, 2.5, 6.3, 727, 787, 802, 880, 10000],
            "Depressão": [0.5, 1.8, 10, 35, 7.83, 3176, 10000],
            "Concentração": [13, 30, 40, 100, 727, 787, 880],
            "Sistema Imunitário": [1500, 1550, 1862, 2170, 2720, 3176, 8000],
            "Circulação": [727, 787, 880, 1500, 1550, 2720],
            "Digestão": [727, 787, 880, 1550, 10000],
            "Respiração": [727, 787, 880, 1234, 1550],
            "Músculos": [120, 240, 300, 324, 727, 787, 880],
            "Articulações": [727, 776, 787, 802, 880, 1500, 1550],
            "Schumann 7.83Hz": [7.83],
            "Alpha 8-13Hz": [8, 9, 10, 11, 12, 13],
            "Beta 13-30Hz": [13, 15, 18, 20, 25, 30],
            "Gamma 30-100Hz": [30, 35, 40, 60, 80, 100],
            "Frequências Rife Base": [20, 95, 125, 225, 427, 440, 465, 727, 776, 787, 802, 880, 1550, 1600, 2127, 2170, 2720, 3176, 5000, 10000]
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Limpar dados existentes de exemplo
        cursor.execute('DELETE FROM frequency_protocols WHERE source = "Dados de Exemplo"')
        
        loaded_count = 0
        for condition, frequencies in sample_frequencies.items():
            for freq in frequencies:
                try:
                    cursor.execute('''
                        INSERT INTO frequency_protocols 
                        (condition_name, frequency, description, source, category)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (condition, freq, f"Frequência terapêutica {freq}Hz", "Dados de Exemplo", "Terapêutico"))
                    loaded_count += 1
                except Exception as e:
                    print(f"Erro ao inserir {condition} - {freq}Hz: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {loaded_count} frequências de exemplo carregadas!")
        return True
    
    def get_all_conditions(self):
        """Lista todas as condições disponíveis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT condition_name 
            FROM frequency_protocols 
            ORDER BY condition_name
        ''')
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_frequencies_by_condition(self, condition):
        """Busca frequências por condição"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT frequency, description, amplitude, duration 
            FROM frequency_protocols 
            WHERE condition_name LIKE ? 
            ORDER BY frequency
        ''', (f'%{condition}%',))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def search_frequencies(self, search_term):
        """Busca frequências por termo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT condition_name, frequency, description 
            FROM frequency_protocols 
            WHERE condition_name LIKE ? OR description LIKE ?
            ORDER BY condition_name, frequency
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_frequency_stats(self):
        """Estatísticas da base de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de frequências
        cursor.execute('SELECT COUNT(*) FROM frequency_protocols')
        total_frequencies = cursor.fetchone()[0]
        
        # Total de condições únicas
        cursor.execute('SELECT COUNT(DISTINCT condition_name) FROM frequency_protocols')
        total_conditions = cursor.fetchone()[0]
        
        # Range de frequências
        cursor.execute('SELECT MIN(frequency), MAX(frequency) FROM frequency_protocols')
        freq_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_frequencies': total_frequencies,
            'total_conditions': total_conditions,
            'frequency_range': freq_range
        }
    
    def save_custom_protocol(self, name, frequencies, description=""):
        """Salva protocolo personalizado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO custom_protocols 
                (protocol_name, frequencies, description)
                VALUES (?, ?, ?)
            ''', (name, json.dumps(frequencies), description))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar protocolo: {e}")
            conn.close()
            return False
    
    def get_custom_protocols(self):
        """Lista protocolos personalizados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT protocol_name, frequencies, description, created_date
            FROM custom_protocols 
            ORDER BY protocol_name
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'name': row[0],
                'frequencies': json.loads(row[1]),
                'description': row[2],
                'created_date': row[3]
            })
        
        conn.close()
        return results

# Teste da funcionalidade
if __name__ == "__main__":
    loader = FrequencyLoader()
    stats = loader.get_frequency_stats()
    print(f"📊 Estatísticas: {stats}")
    
    conditions = loader.get_all_conditions()[:10]  # Primeiras 10
    print(f"🔍 Primeiras condições: {conditions}")
