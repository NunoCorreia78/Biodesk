"""
Gestão de Sessões Terapêuticas
═══════════════════════════════════════════════════════════════════════

Módulo para criar, gerir e gravar sessões de terapia quântica.
Integra dados de pacientes, protocolos e histórico de tratamentos.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal

from frequency_generator import GenerationSession, FrequencyStep
from hs3_config import hs3_config

@dataclass
class PatientInfo:
    """Informações do paciente"""
    patient_id: str
    name: str
    birth_date: str
    gender: str
    notes: str = ""

@dataclass
class TherapyProtocol:
    """Protocolo terapêutico"""
    protocol_id: str
    name: str
    description: str
    category: str
    steps: List[FrequencyStep]
    created_by: str
    created_at: datetime
    iris_based: bool = False
    iris_data: Optional[Dict] = None

@dataclass
class SessionRecord:
    """Registo de sessão terapêutica"""
    session_id: str
    patient_info: PatientInfo
    protocol: TherapyProtocol
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # "completed", "interrupted", "error"
    notes: str
    biofeedback_data: Optional[List[Dict]] = None
    results: Optional[Dict] = None

class TherapySessionManager(QObject):
    """
    Gestor de sessões terapêuticas com persistência em base de dados
    """
    
    # Sinais
    session_created = pyqtSignal(str)    # ID da sessão
    session_saved = pyqtSignal(str)      # ID da sessão
    protocol_created = pyqtSignal(str)   # ID do protocolo
    
    def __init__(self, db_path: str = "therapy_sessions.db"):
        super().__init__()
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa base de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de protocolos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS therapy_protocols (
                protocol_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                steps_json TEXT NOT NULL,
                created_by TEXT,
                created_at TIMESTAMP,
                iris_based BOOLEAN DEFAULT 0,
                iris_data_json TEXT,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabela de sessões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS therapy_sessions (
                session_id TEXT PRIMARY KEY,
                patient_id TEXT,
                patient_name TEXT,
                protocol_id TEXT,
                protocol_name TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT,
                notes TEXT,
                biofeedback_data_json TEXT,
                results_json TEXT,
                FOREIGN KEY (protocol_id) REFERENCES therapy_protocols (protocol_id)
            )
        ''')
        
        # Tabela de dados de biofeedback (opcional)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS biofeedback_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                frequency REAL,
                amplitude REAL,
                offset REAL,
                measured_values_json TEXT,
                FOREIGN KEY (session_id) REFERENCES therapy_sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Criar protocolos padrão se não existirem
        self._create_default_protocols()
    
    def create_protocol_from_iris(self, iris_data: Dict, patient_name: str) -> TherapyProtocol:
        """
        Cria protocolo terapêutico baseado em análise de íris
        """
        try:
            # Extrair condições das notas de íris
            conditions = self._extract_conditions_from_iris(iris_data)
            
            # Usar biblioteca de protocolos para criar protocolo personalizado
            from therapy_protocols import TherapyProtocols
            
            protocol = TherapyProtocols.create_iris_protocol(conditions, patient_name)
            
            # Adicionar dados específicos desta análise
            protocol.iris_data.update({
                'source_iris_data': iris_data,
                'analysis_date': datetime.now().isoformat(),
                'extracted_conditions': conditions
            })
            
            # Gravar na base de dados
            self.save_protocol(protocol)
            
            return protocol
            
        except Exception as e:
            raise Exception(f"Erro ao criar protocolo de íris: {e}")
    
    def _extract_conditions_from_iris(self, iris_data: Dict) -> List[str]:
        """
        Extrai condições terapêuticas dos dados de íris
        Análise mais sofisticada das notas iridológicas
        """
        conditions = []
        
        # Obter notas selecionadas
        notas_selecionadas = iris_data.get('notas_selecionadas', [])
        
        # Mapeamento de palavras-chave para condições
        keyword_mapping = {
            # Sistema nervoso
            'stress': 'sistema_nervoso',
            'tensão': 'sistema_nervoso', 
            'ansiedade': 'ansiedade',
            'nervoso': 'sistema_nervoso',
            'irritabilidade': 'ansiedade',
            'fadiga': 'fadiga',
            'cansaço': 'fadiga',
            'depressão': 'depressao',
            'insónia': 'insonia',
            'sono': 'insonia',
            
            # Sistema digestivo
            'digestão': 'digestao',
            'intestino': 'intestinos',
            'estômago': 'digestao',
            'fígado': 'figado',
            'vesícula': 'figado',
            'pâncreas': 'pancreas',
            'diabetes': 'pancreas',
            
            # Sistema circulatório
            'circulação': 'circulacao',
            'coração': 'coracao',
            'pressão': 'pressao_arterial',
            'vascular': 'circulacao',
            
            # Sistema respiratório
            'pulmão': 'pulmoes',
            'respiração': 'respiracao',
            'asma': 'pulmoes',
            'bronquite': 'pulmoes',
            
            # Sistema reprodutor
            'reprodutor': 'reprodutor',
            'hormonal': 'hormonios',
            'hormônio': 'hormonios',
            'menstrual': 'hormonios',
            'próstata': 'reprodutor',
            
            # Sistema músculo-esquelético
            'músculo': 'musculos',
            'articulação': 'articulacoes',
            'osso': 'ossos',
            'artrite': 'articulacoes',
            'reumatismo': 'articulacoes',
            
            # Sistema imunitário
            'imunidade': 'imunidade',
            'defesa': 'imunidade',
            'linfático': 'linfatico',
            'alergia': 'imunidade',
            
            # Órgãos específicos
            'tiróide': 'tiroide',
            'tiróidea': 'tiroide',
            'rim': 'rins',
            'renal': 'rins',
            'bexiga': 'bexiga',
            'supra-renal': 'supra_renais',
            'adrenal': 'supra_renais',
            
            # Condições gerais
            'inflamação': 'inflamacao',
            'dor': 'dor',
            'energia': 'energia',
            'vitalidade': 'vitalidade',
            'equilíbrio': 'equilibrio',
            'detox': 'detox',
            'purificação': 'purificacao'
        }
        
        # Analisar cada nota
        for nota in notas_selecionadas:
            texto_nota = nota.get('texto', '').lower()
            setor = nota.get('setor', '').lower()
            
            # Procurar palavras-chave no texto
            for keyword, condition in keyword_mapping.items():
                if keyword in texto_nota or keyword in setor:
                    if condition not in conditions:
                        conditions.append(condition)
            
            # Análise específica por setor anatómico
            sector_conditions = self._analyze_iris_sector(setor, texto_nota)
            for condition in sector_conditions:
                if condition not in conditions:
                    conditions.append(condition)
        
        # Se não encontrou condições específicas, usar condições gerais
        if not conditions:
            conditions = ['equilibrio', 'energia', 'harmonizacao']
        
        # Limitar número de condições para protocolo focado
        return conditions[:8]  # Máximo 8 condições
    
    def _analyze_iris_sector(self, setor: str, texto: str) -> List[str]:
        """
        Análise específica por setor anatómico da íris
        """
        sector_map = {
            # Setores digestivos
            'estômago': ['digestao'],
            'duodeno': ['digestao'],
            'intestino delgado': ['intestinos'],
            'cólon': ['intestinos'],
            'fígado': ['figado'],
            'vesícula': ['figado'],
            'pâncreas': ['pancreas'],
            
            # Setores endócrinos
            'hipófise': ['hormonios'],
            'tiróide': ['tiroide'],
            'paratiróide': ['tiroide'],
            'supra-renais': ['supra_renais'],
            'ovários': ['reprodutor', 'hormonios'],
            'testículos': ['reprodutor', 'hormonios'],
            
            # Setores circulatórios
            'coração': ['coracao'],
            'aorta': ['circulacao'],
            'veia cava': ['circulacao'],
            
            # Setores respiratórios
            'pulmão': ['pulmoes'],
            'brônquios': ['pulmoes'],
            'traqueia': ['respiracao'],
            
            # Setores urinários
            'rim': ['rins'],
            'ureter': ['rins'],
            'bexiga': ['bexiga'],
            
            # Sistema nervoso
            'cérebro': ['sistema_nervoso'],
            'cerebelo': ['sistema_nervoso'],
            'medula': ['sistema_nervoso'],
            
            # Membros
            'braço': ['musculos', 'articulacoes'],
            'perna': ['musculos', 'articulacoes'],
            'coluna': ['ossos', 'musculos']
        }
        
        conditions = []
        
        for sector_name, sector_conditions in sector_map.items():
            if sector_name in setor:
                conditions.extend(sector_conditions)
        
        return conditions
    
    def create_custom_protocol(self, name: str, description: str, 
                             frequencies: List[float], amplitude: float = 2.0,
                             step_duration: int = 5, category: str = "Personalizado") -> TherapyProtocol:
        """
        Cria protocolo personalizado
        """
        try:
            # Validar parâmetros
            if not frequencies:
                raise ValueError("Lista de frequências não pode estar vazia")
            
            # Criar passos
            steps = []
            for i, freq in enumerate(frequencies):
                # Usar configurações seguras
                safe_params = hs3_config.get_safe_parameters(amplitude, 0.0, freq, step_duration)
                
                step = FrequencyStep(
                    frequency=safe_params['frequency'],
                    amplitude=safe_params['amplitude'],
                    offset=safe_params['offset'],
                    duration_seconds=safe_params['duration'] * 60,
                    description=f"Frequência {freq}Hz - Passo {i+1}"
                )
                steps.append(step)
            
            # Criar protocolo
            protocol = TherapyProtocol(
                protocol_id=str(uuid.uuid4()),
                name=name,
                description=description,
                category=category,
                steps=steps,
                created_by="Utilizador",
                created_at=datetime.now(),
                iris_based=False
            )
            
            # Gravar
            self.save_protocol(protocol)
            
            return protocol
            
        except Exception as e:
            raise Exception(f"Erro ao criar protocolo personalizado: {e}")
    
    def save_protocol(self, protocol: TherapyProtocol) -> bool:
        """Grava protocolo na base de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serializar passos
            steps_json = json.dumps([asdict(step) for step in protocol.steps])
            iris_data_json = json.dumps(protocol.iris_data) if protocol.iris_data else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO therapy_protocols
                (protocol_id, name, description, category, steps_json, 
                 created_by, created_at, iris_based, iris_data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                protocol.protocol_id,
                protocol.name,
                protocol.description,
                protocol.category,
                steps_json,
                protocol.created_by,
                protocol.created_at.isoformat(),
                protocol.iris_based,
                iris_data_json
            ))
            
            conn.commit()
            conn.close()
            
            self.protocol_created.emit(protocol.protocol_id)
            return True
            
        except Exception as e:
            print(f"Erro ao gravar protocolo: {e}")
            return False
    
    def load_protocol(self, protocol_id: str) -> Optional[TherapyProtocol]:
        """Carrega protocolo da base de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM therapy_protocols WHERE protocol_id = ? AND active = 1
            ''', (protocol_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Deserializar dados
            steps_data = json.loads(row[4])  # steps_json
            steps = [FrequencyStep(**step_data) for step_data in steps_data]
            
            iris_data = json.loads(row[8]) if row[8] else None  # iris_data_json
            
            return TherapyProtocol(
                protocol_id=row[0],
                name=row[1],
                description=row[2],
                category=row[3],
                steps=steps,
                created_by=row[5],
                created_at=datetime.fromisoformat(row[6]),
                iris_based=bool(row[7]),
                iris_data=iris_data
            )
            
        except Exception as e:
            print(f"Erro ao carregar protocolo: {e}")
            return None
    
    def list_protocols(self, category: str = None) -> List[Dict]:
        """Lista protocolos disponíveis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT protocol_id, name, description, category, created_at, iris_based FROM therapy_protocols WHERE active = 1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            protocols = []
            for row in rows:
                protocols.append({
                    'protocol_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'category': row[3],
                    'created_at': row[4],
                    'iris_based': bool(row[5])
                })
            
            return protocols
            
        except Exception as e:
            print(f"Erro ao listar protocolos: {e}")
            return []
    
    def create_session(self, patient_data: Dict, protocol_id: str, notes: str = "") -> Optional[GenerationSession]:
        """
        Cria nova sessão terapêutica
        """
        try:
            # Carregar protocolo
            protocol = self.load_protocol(protocol_id)
            if not protocol:
                raise Exception(f"Protocolo {protocol_id} não encontrado")
            
            # Criar informações do paciente
            patient_info = PatientInfo(
                patient_id=patient_data.get('id', str(uuid.uuid4())),
                name=patient_data.get('nome', 'Paciente'),
                birth_date=patient_data.get('data_nascimento', ''),
                gender=patient_data.get('sexo', ''),
                notes=patient_data.get('notas', '')
            )
            
            # Calcular duração total
            total_duration = sum(step.duration_seconds for step in protocol.steps)
            
            # Criar sessão
            session = GenerationSession(
                session_id=str(uuid.uuid4()),
                patient_name=patient_info.name,
                protocol_name=protocol.name,
                steps=protocol.steps,
                total_duration=total_duration,
                created_at=datetime.now(),
                notes=notes
            )
            
            # Criar registo
            session_record = SessionRecord(
                session_id=session.session_id,
                patient_info=patient_info,
                protocol=protocol,
                start_time=datetime.now(),
                end_time=None,
                status="created",
                notes=notes
            )
            
            # Gravar registo inicial
            self._save_session_record(session_record)
            
            self.session_created.emit(session.session_id)
            
            return session
            
        except Exception as e:
            print(f"Erro ao criar sessão: {e}")
            return None
    
    def complete_session(self, session_id: str, biofeedback_data: List[Dict] = None, 
                        results: Dict = None, notes: str = "") -> bool:
        """
        Marca sessão como completa e grava dados finais
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Atualizar sessão
            cursor.execute('''
                UPDATE therapy_sessions 
                SET end_time = ?, status = ?, biofeedback_data_json = ?, 
                    results_json = ?, notes = ?
                WHERE session_id = ?
            ''', (
                datetime.now().isoformat(),
                "completed",
                json.dumps(biofeedback_data) if biofeedback_data else None,
                json.dumps(results) if results else None,
                notes,
                session_id
            ))
            
            conn.commit()
            conn.close()
            
            self.session_saved.emit(session_id)
            return True
            
        except Exception as e:
            print(f"Erro ao completar sessão: {e}")
            return False
    
    def get_session_history(self, patient_id: str = None, limit: int = 50) -> List[Dict]:
        """Obtém histórico de sessões"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT session_id, patient_name, protocol_name, start_time, 
                       end_time, status, notes
                FROM therapy_sessions
            '''
            params = []
            
            if patient_id:
                query += " WHERE patient_id = ?"
                params.append(patient_id)
            
            query += " ORDER BY start_time DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'patient_name': row[1],
                    'protocol_name': row[2],
                    'start_time': row[3],
                    'end_time': row[4],
                    'status': row[5],
                    'notes': row[6]
                })
            
            return sessions
            
        except Exception as e:
            print(f"Erro ao obter histórico: {e}")
            return []
    
    # Métodos privados
    def _analyze_iris_data(self, iris_data: Dict) -> List[Dict]:
        """
        Analisa dados de íris e sugere frequências terapêuticas
        TODO: Implementar algoritmo completo baseado em literatura científica
        """
        frequencies = []
        
        # Análise básica baseada nas notas selecionadas
        notas_selecionadas = iris_data.get('notas_selecionadas', [])
        
        # Mapeamento básico de condições para frequências (baseado em research)
        frequency_map = {
            'stress': [7.83, 40, 432, 528],
            'fadiga': [727, 787, 880, 1500],
            'digestão': [727, 787, 880, 1550],
            'sistema nervoso': [3.59, 7.83, 10, 40],
            'circulação': [727, 787, 880, 1500, 2720],
            'sistema imunitário': [1500, 1550, 1862, 2170],
            'relaxamento': [7.83, 10, 40, 100],
            'energia': [20, 35, 95, 120]
        }
        
        # Frequências base sempre incluídas
        base_frequencies = [
            {'frequency': 7.83, 'description': 'Frequência Schumann - Equilíbrio Natural', 'duration': 300},
            {'frequency': 528, 'description': 'Frequência de Cura - DNA Repair', 'duration': 300}
        ]
        
        frequencies.extend(base_frequencies)
        
        # Analisar notas e adicionar frequências específicas
        for nota in notas_selecionadas:
            texto_nota = nota.get('texto', '').lower()
            
            # Identificar condições mencionadas
            for condition, freqs in frequency_map.items():
                if condition in texto_nota:
                    for freq in freqs[:2]:  # Máximo 2 frequências por condição
                        frequencies.append({
                            'frequency': freq,
                            'description': f'Tratamento {condition.title()} - {freq}Hz',
                            'duration': 240  # 4 minutos
                        })
        
        # Limitar total de frequências (máximo 10 para sessão razoável)
        if len(frequencies) > 10:
            frequencies = frequencies[:10]
        
        return frequencies
    
    def _save_session_record(self, record: SessionRecord) -> bool:
        """Grava registo de sessão"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO therapy_sessions
                (session_id, patient_id, patient_name, protocol_id, protocol_name,
                 start_time, end_time, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.session_id,
                record.patient_info.patient_id,
                record.patient_info.name,
                record.protocol.protocol_id,
                record.protocol.name,
                record.start_time.isoformat(),
                record.end_time.isoformat() if record.end_time else None,
                record.status,
                record.notes
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao gravar registo de sessão: {e}")
            return False
    
    def _create_default_protocols(self):
        """Cria protocolos padrão se não existirem"""
        try:
            # Verificar se já existem protocolos
            existing = self.list_protocols()
            if existing:
                return  # Já tem protocolos
            
            # Importar biblioteca de protocolos
            from therapy_protocols import TherapyProtocols
            
            # Carregar protocolos básicos
            basic_protocols = TherapyProtocols.get_basic_protocols()
            for protocol in basic_protocols:
                self.save_protocol(protocol)
            
            # Carregar protocolos especializados
            specialized_protocols = TherapyProtocols.get_specialized_protocols()
            for protocol in specialized_protocols:
                self.save_protocol(protocol)
            
            # Carregar protocolos rápidos
            quick_protocols = TherapyProtocols.get_quick_protocols()
            for protocol in quick_protocols:
                self.save_protocol(protocol)
            
            total_protocols = len(basic_protocols) + len(specialized_protocols) + len(quick_protocols)
            print(f"✅ {total_protocols} protocolos padrão criados")
            
        except Exception as e:
            print(f"⚠️ Erro ao criar protocolos padrão: {e}")
            # Fallback para protocolos simples se houver erro
            self._create_simple_fallback_protocols()
    
    def _create_simple_fallback_protocols(self):
        """Cria protocolos básicos em caso de erro"""
        try:
            # Protocolo básico de relaxamento
            relaxamento_freqs = [7.83, 10, 40, 100, 432, 528]
            self.create_custom_protocol(
                name="Relaxamento Básico",
                description="Protocolo básico para relaxamento e redução de stress",
                frequencies=relaxamento_freqs,
                amplitude=1.5,
                step_duration=4,
                category="Básico"
            )
            
            # Protocolo energético
            energia_freqs = [20, 35, 95, 120, 727, 787]
            self.create_custom_protocol(
                name="Energia e Vitalidade",
                description="Protocolo para aumentar energia e vitalidade",
                frequencies=energia_freqs,
                amplitude=2.0,
                step_duration=3,
                category="Básico"
            )
            
            # Protocolo Rife básico
            rife_freqs = [727, 787, 880, 1500, 1550, 2127]
            self.create_custom_protocol(
                name="Rife Básico",
                description="Protocolo baseado nas frequências clássicas de Rife",
                frequencies=rife_freqs,
                amplitude=2.5,
                step_duration=5,
                category="Rife"
            )
            
            print("✅ Protocolos de fallback criados")
            
        except Exception as e:
            print(f"❌ Erro crítico ao criar protocolos de fallback: {e}")

# Instância global do gestor
therapy_session_manager = TherapySessionManager()
