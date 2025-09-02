"""
Sistema de Logging e Armazenamento - Terapia Quântica
═══════════════════════════════════════════════════════════════════════

Sistema completo de registo de sessões terapêuticas com:
- Armazenamento em JSONL + CSV
- Integridade e hash de dados
- Integração com gestor de documentos
- Metadados completos
"""

import json
import csv
import hashlib
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

# Para compressão de dados grandes
import gzip
import pickle


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SessionMetadata:
    """Metadados da sessão terapêutica"""
    session_id: str
    patient_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Informações do protocolo
    protocol_name: str = ""
    protocol_source: str = ""  # "excel", "manual", "assessment"
    protocol_version: str = "1.0"
    total_steps: int = 0
    
    # Configurações técnicas
    device_info: Dict[str, Any] = field(default_factory=dict)
    software_version: str = "1.0.0"
    calibration_info: Dict[str, Any] = field(default_factory=dict)
    
    # Estatísticas da sessão
    steps_completed: int = 0
    total_duration_s: float = 0.0
    average_impedance: float = 0.0
    data_points_count: int = 0
    
    # Integridade
    data_hash: str = ""
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário serializável"""
        data = asdict(self)
        
        # Converter datetime para ISO string
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        """Criar a partir de dicionário"""
        # Converter strings ISO para datetime
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        
        return cls(**data)


@dataclass
class StepLogEntry:
    """Entrada de log para um passo do protocolo"""
    timestamp: datetime
    step_index: int
    frequency_hz: float
    amplitude_vpp: float
    duration_s: float
    waveform: str
    
    # Medições
    measured_data: Dict[str, float] = field(default_factory=dict)
    
    # Status
    status: str = "completed"  # completed, skipped, error
    error_message: str = ""
    
    # Métricas calculadas
    impedance_ohm: float = 0.0
    current_ma: float = 0.0
    power_mw: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepLogEntry':
        """Criar a partir de dicionário"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class EventLogEntry:
    """Entrada de log para eventos gerais"""
    timestamp: datetime
    level: LogLevel
    message: str
    category: str = "general"  # general, protocol, hardware, safety, user
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventLogEntry':
        """Criar a partir de dicionário"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'level' in data and isinstance(data['level'], str):
            data['level'] = LogLevel(data['level'])
        return cls(**data)


class SessionLogger:
    """Logger de sessão terapêutica"""
    
    def __init__(self, base_path: Path):
        """
        Inicializar logger
        
        Args:
            base_path: Caminho base para armazenamento (pasta do paciente)
        """
        self.base_path = Path(base_path)
        self.logger = logging.getLogger("SessionLogger")
        
        # Estado da sessão atual
        self.current_session: Optional[SessionMetadata] = None
        self.step_logs: List[StepLogEntry] = []
        self.event_logs: List[EventLogEntry] = []
        
        # Caminhos de arquivo
        self.session_file: Optional[Path] = None
        self.jsonl_file: Optional[Path] = None
        self.csv_file: Optional[Path] = None
        
        # Garantir que pasta existe
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"SessionLogger inicializado: {self.base_path}")
    
    def log_session_start(self, patient_id: str, protocol_meta: Dict[str, Any]) -> str:
        """
        Iniciar nova sessão de log
        
        Args:
            patient_id: ID do paciente
            protocol_meta: Metadados do protocolo
            
        Returns:
            session_id: ID único da sessão
        """
        # Gerar ID único da sessão
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Criar metadados da sessão
        self.current_session = SessionMetadata(
            session_id=session_id,
            patient_id=patient_id,
            start_time=datetime.now(timezone.utc),
            protocol_name=protocol_meta.get('name', 'Protocolo'),
            protocol_source=protocol_meta.get('source', 'manual'),
            protocol_version=protocol_meta.get('version', '1.0'),
            total_steps=protocol_meta.get('total_steps', 0),
            device_info=protocol_meta.get('device_info', {}),
            software_version=protocol_meta.get('software_version', '1.0.0'),
            calibration_info=protocol_meta.get('calibration_info', {})
        )
        
        # Definir caminhos de arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_file = self.base_path / f"session_{timestamp}.json"
        self.jsonl_file = self.base_path / f"session_{timestamp}.jsonl"
        self.csv_file = self.base_path / f"session_{timestamp}.csv"
        
        # Limpar logs anteriores
        self.step_logs.clear()
        self.event_logs.clear()
        
        # Log evento de início
        self.log_event("Sessão terapêutica iniciada", LogLevel.INFO, "protocol", {
            'session_id': session_id,
            'patient_id': patient_id,
            'protocol': protocol_meta
        })
        
        self.logger.info(f"Nova sessão iniciada: {session_id}")
        return session_id
    
    def log_step(self, step_idx: int, freq_hz: float, amp_vpp: float, 
                duration_s: float, waveform: str, measured: Dict[str, float],
                status: str = "completed", error_msg: str = "") -> None:
        """
        Registar passo do protocolo
        
        Args:
            step_idx: Índice do passo
            freq_hz: Frequência em Hz
            amp_vpp: Amplitude pico-a-pico em V
            duration_s: Duração em segundos
            waveform: Tipo de forma de onda
            measured: Dados medidos
            status: Status do passo
            error_msg: Mensagem de erro (se houver)
        """
        if not self.current_session:
            raise RuntimeError("Nenhuma sessão ativa")
        
        # Calcular métricas derivadas
        impedance_ohm = measured.get('impedance', 0.0)
        current_ma = measured.get('current', 0.0) * 1000  # Converter para mA
        power_mw = (amp_vpp / 2) * current_ma  # Aproximação P = V_rms * I
        
        # Criar entrada de log
        step_entry = StepLogEntry(
            timestamp=datetime.now(timezone.utc),
            step_index=step_idx,
            frequency_hz=freq_hz,
            amplitude_vpp=amp_vpp,
            duration_s=duration_s,
            waveform=waveform,
            measured_data=measured.copy(),
            status=status,
            error_message=error_msg,
            impedance_ohm=impedance_ohm,
            current_ma=current_ma,
            power_mw=power_mw
        )
        
        self.step_logs.append(step_entry)
        
        # Escrever em JSONL imediatamente
        self._write_jsonl_entry(step_entry.to_dict(), "step")
        
        # Atualizar estatísticas da sessão
        if status == "completed":
            self.current_session.steps_completed += 1
            self.current_session.total_duration_s += duration_s
            
            # Atualizar impedância média
            if impedance_ohm > 0:
                n = self.current_session.steps_completed
                current_avg = self.current_session.average_impedance
                self.current_session.average_impedance = (
                    (current_avg * (n-1) + impedance_ohm) / n
                )
        
        self.current_session.data_points_count += 1
        
        self.logger.debug(f"Passo {step_idx} registado: {freq_hz}Hz, {status}")
    
    def log_event(self, message: str, level: LogLevel = LogLevel.INFO, 
                 category: str = "general", details: Optional[Dict] = None) -> None:
        """
        Registar evento geral
        
        Args:
            message: Mensagem do evento
            level: Nível de log
            category: Categoria do evento
            details: Detalhes adicionais
        """
        event_entry = EventLogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            category=category,
            details=details or {}
        )
        
        self.event_logs.append(event_entry)
        
        # Escrever em JSONL
        self._write_jsonl_entry(event_entry.to_dict(), "event")
        
        # Log também no sistema de logging padrão
        log_method = getattr(self.logger, level.value.lower())
        log_method(f"[{category}] {message}")
    
    def finalize_session(self, summary: Optional[Dict] = None) -> Path:
        """
        Finalizar sessão e salvar arquivos
        
        Args:
            summary: Resumo adicional da sessão
            
        Returns:
            path_csv: Caminho do arquivo CSV gerado
        """
        if not self.current_session:
            raise RuntimeError("Nenhuma sessão ativa")
        
        # Finalizar metadados
        self.current_session.end_time = datetime.now(timezone.utc)
        
        if summary:
            self.current_session.device_info.update(summary.get('device_info', {}))
        
        # Calcular hash dos dados
        self.current_session.data_hash = self._calculate_data_hash()
        self.current_session.checksum = self._calculate_checksum()
        
        # Log evento de finalização
        self.log_event("Sessão terapêutica finalizada", LogLevel.INFO, "protocol", {
            'steps_completed': self.current_session.steps_completed,
            'total_duration': self.current_session.total_duration_s,
            'data_points': self.current_session.data_points_count
        })
        
        # Salvar arquivos
        self._save_session_metadata()
        csv_path = self._save_csv()
        self._compress_jsonl()
        
        self.logger.info(f"Sessão finalizada: {self.current_session.session_id}")
        self.logger.info(f"Arquivos salvos: {csv_path}")
        
        return csv_path
    
    def _write_jsonl_entry(self, data: Dict[str, Any], entry_type: str) -> None:
        """Escrever entrada em arquivo JSONL"""
        if not self.jsonl_file:
            return
        
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': entry_type,
            'data': data
        }
        
        try:
            with open(self.jsonl_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Erro ao escrever JSONL: {e}")
    
    def _save_session_metadata(self) -> None:
        """Salvar metadados da sessão"""
        if not self.session_file or not self.current_session:
            return
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar metadados: {e}")
    
    def _save_csv(self) -> Path:
        """Salvar dados em formato CSV"""
        if not self.csv_file:
            raise RuntimeError("Arquivo CSV não definido")
        
        try:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Cabeçalho
                headers = [
                    'Timestamp', 'Passo', 'Frequência (Hz)', 'Amplitude (V)',
                    'Duração (s)', 'Forma', 'Status', 'Impedância (Ω)',
                    'Corrente (mA)', 'Potência (mW)', 'RMS (V)', 'Vpp (V)',
                    'DC (V)', 'Erro'
                ]
                writer.writerow(headers)
                
                # Dados dos passos
                for step in self.step_logs:
                    measured = step.measured_data
                    row = [
                        step.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        step.step_index,
                        f"{step.frequency_hz:.3f}",
                        f"{step.amplitude_vpp:.3f}",
                        f"{step.duration_s:.1f}",
                        step.waveform,
                        step.status,
                        f"{step.impedance_ohm:.0f}",
                        f"{step.current_ma:.3f}",
                        f"{step.power_mw:.3f}",
                        f"{measured.get('rms', 0):.6f}",
                        f"{measured.get('vpp', 0):.6f}",
                        f"{measured.get('dc', 0):.6f}",
                        step.error_message
                    ]
                    writer.writerow(row)
                
                # Linha de resumo
                if self.current_session:
                    writer.writerow([])  # Linha vazia
                    writer.writerow(['RESUMO DA SESSÃO'])
                    writer.writerow(['Session ID', self.current_session.session_id])
                    writer.writerow(['Patient ID', self.current_session.patient_id])
                    writer.writerow(['Protocolo', self.current_session.protocol_name])
                    writer.writerow(['Início', self.current_session.start_time.strftime('%Y-%m-%d %H:%M:%S')])
                    if self.current_session.end_time:
                        writer.writerow(['Fim', self.current_session.end_time.strftime('%Y-%m-%d %H:%M:%S')])
                    writer.writerow(['Passos Completados', self.current_session.steps_completed])
                    writer.writerow(['Duração Total (s)', f"{self.current_session.total_duration_s:.1f}"])
                    writer.writerow(['Impedância Média (Ω)', f"{self.current_session.average_impedance:.0f}"])
                    writer.writerow(['Pontos de Dados', self.current_session.data_points_count])
                    writer.writerow(['Hash dos Dados', self.current_session.data_hash])
            
            return self.csv_file
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")
            raise
    
    def _compress_jsonl(self) -> None:
        """Comprimir arquivo JSONL para economizar espaço"""
        if not self.jsonl_file or not self.jsonl_file.exists():
            return
        
        try:
            compressed_file = self.jsonl_file.with_suffix('.jsonl.gz')
            
            with open(self.jsonl_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remover arquivo original
            self.jsonl_file.unlink()
            
            self.logger.info(f"JSONL comprimido: {compressed_file}")
            
        except Exception as e:
            self.logger.error(f"Erro ao comprimir JSONL: {e}")
    
    def _calculate_data_hash(self) -> str:
        """Calcular hash MD5 dos dados da sessão"""
        data_str = ""
        
        # Hash dos passos
        for step in self.step_logs:
            data_str += f"{step.step_index}{step.frequency_hz}{step.amplitude_vpp}"
            data_str += f"{step.duration_s}{step.status}"
        
        # Hash dos eventos críticos
        for event in self.event_logs:
            if event.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                data_str += f"{event.message}{event.level.value}"
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _calculate_checksum(self) -> str:
        """Calcular checksum SHA256 para integridade"""
        if not self.current_session:
            return ""
        
        checksum_data = {
            'session_id': self.current_session.session_id,
            'patient_id': self.current_session.patient_id,
            'steps_count': len(self.step_logs),
            'events_count': len(self.event_logs),
            'start_time': self.current_session.start_time.isoformat()
        }
        
        data_str = json.dumps(checksum_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]  # Primeiros 16 chars
    
    def load_session(self, session_file: Path) -> SessionMetadata:
        """Carregar sessão a partir de arquivo"""
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return SessionMetadata.from_dict(data)
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar sessão: {e}")
            raise
    
    def export_session_summary(self, session_id: str, output_path: Path) -> Dict[str, Any]:
        """Exportar resumo da sessão para análise"""
        if not self.current_session or self.current_session.session_id != session_id:
            raise ValueError("Sessão não encontrada ou não ativa")
        
        # Calcular estatísticas
        frequencies = [step.frequency_hz for step in self.step_logs if step.status == "completed"]
        impedances = [step.impedance_ohm for step in self.step_logs if step.impedance_ohm > 0]
        currents = [step.current_ma for step in self.step_logs if step.current_ma > 0]
        
        summary = {
            'session_info': self.current_session.to_dict(),
            'statistics': {
                'total_steps': len(self.step_logs),
                'completed_steps': len([s for s in self.step_logs if s.status == "completed"]),
                'error_steps': len([s for s in self.step_logs if s.status == "error"]),
                'frequency_range': {
                    'min': min(frequencies) if frequencies else 0,
                    'max': max(frequencies) if frequencies else 0,
                    'average': sum(frequencies) / len(frequencies) if frequencies else 0
                },
                'impedance_stats': {
                    'min': min(impedances) if impedances else 0,
                    'max': max(impedances) if impedances else 0,
                    'average': sum(impedances) / len(impedances) if impedances else 0
                },
                'current_stats': {
                    'min': min(currents) if currents else 0,
                    'max': max(currents) if currents else 0,
                    'average': sum(currents) / len(currents) if currents else 0
                }
            },
            'events_summary': {
                'info_count': len([e for e in self.event_logs if e.level == LogLevel.INFO]),
                'warning_count': len([e for e in self.event_logs if e.level == LogLevel.WARNING]),
                'error_count': len([e for e in self.event_logs if e.level == LogLevel.ERROR]),
                'critical_count': len([e for e in self.event_logs if e.level == LogLevel.CRITICAL])
            }
        }
        
        # Salvar resumo
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Resumo exportado: {output_path}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar resumo: {e}")
            raise


# ═══════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO COM GESTOR DE DOCUMENTOS
# ═══════════════════════════════════════════════════════════════════════

class DocumentIntegration:
    """Integração com o sistema de gestão de documentos do Biodesk"""
    
    def __init__(self, base_documents_path: Path):
        self.base_path = Path(base_documents_path)
        self.logger = logging.getLogger("DocumentIntegration")
    
    def register_session_files(self, patient_id: str, session_files: List[Path]) -> Dict[str, str]:
        """
        Registar ficheiros de sessão no gestor de documentos
        
        Args:
            patient_id: ID do paciente
            session_files: Lista de ficheiros gerados
            
        Returns:
            Dict com caminhos finais e metadados
        """
        patient_folder = self.base_path / "Documentos_Pacientes" / patient_id / "terapia_quantica"
        patient_folder.mkdir(parents=True, exist_ok=True)
        
        registered_files = {}
        
        for file_path in session_files:
            if file_path.exists():
                # Copiar para pasta do paciente
                dest_path = patient_folder / file_path.name
                
                try:
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    
                    registered_files[file_path.stem] = str(dest_path)
                    self.logger.info(f"Ficheiro registado: {dest_path}")
                    
                except Exception as e:
                    self.logger.error(f"Erro ao copiar {file_path}: {e}")
        
        return registered_files
    
    def create_session_report(self, session_metadata: SessionMetadata, 
                            summary_data: Dict[str, Any]) -> Path:
        """Criar relatório PDF da sessão (placeholder)"""
        # TODO: Implementar geração de PDF com reportlab
        patient_folder = self.base_path / "Documentos_Pacientes" / session_metadata.patient_id
        report_path = patient_folder / f"relatorio_{session_metadata.session_id}.pdf"
        
        # Por agora, criar arquivo de texto simples
        try:
            with open(report_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(f"RELATÓRIO DE SESSÃO TERAPÊUTICA\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Sessão: {session_metadata.session_id}\n")
                f.write(f"Paciente: {session_metadata.patient_id}\n")
                f.write(f"Data: {session_metadata.start_time.strftime('%d/%m/%Y %H:%M')}\n")
                f.write(f"Protocolo: {session_metadata.protocol_name}\n")
                f.write(f"Passos completados: {session_metadata.steps_completed}\n")
                f.write(f"Duração total: {session_metadata.total_duration_s:.1f}s\n")
                f.write(f"Impedância média: {session_metadata.average_impedance:.0f}Ω\n")
                
                # TODO: Adicionar gráficos e análises detalhadas
            
            self.logger.info(f"Relatório criado: {report_path}")
            return report_path.with_suffix('.txt')
            
        except Exception as e:
            self.logger.error(f"Erro ao criar relatório: {e}")
            raise


# ═══════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════

def demo_session_logging():
    """Demonstração do sistema de logging"""
    import tempfile
    import time
    
    print("🧪 DEMO: Sistema de Logging de Sessões")
    print("="*50)
    
    # Criar pasta temporária
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir) / "patient_123" / "therapy_sessions"
        
        # Criar logger
        logger = SessionLogger(base_path)
        
        # Iniciar sessão
        protocol_meta = {
            'name': 'Protocolo de Relaxamento',
            'source': 'excel',
            'version': '1.0',
            'total_steps': 3,
            'device_info': {'device': 'HS3 Demo', 'serial': 'DEMO123'},
            'software_version': '1.0.0'
        }
        
        session_id = logger.log_session_start("patient_123", protocol_meta)
        print(f"✅ Sessão iniciada: {session_id}")
        
        # Simular execução de protocolo
        frequencies = [100.0, 300.0, 500.0]
        
        for i, freq in enumerate(frequencies):
            print(f"   🎵 Executando passo {i+1}: {freq}Hz")
            
            # Simular medições
            measured = {
                'rms': 0.001 + i * 0.0005,
                'vpp': 0.002 + i * 0.001,
                'dc': 0.0001,
                'impedance': 1000 + i * 100,
                'current': 0.001 + i * 0.0001
            }
            
            # Registar passo
            logger.log_step(
                step_idx=i,
                freq_hz=freq,
                amp_vpp=1.0,
                duration_s=3.0,
                waveform="sine",
                measured=measured,
                status="completed"
            )
            
            time.sleep(0.1)  # Simular tempo de execução
        
        # Registar alguns eventos
        logger.log_event("Impedância estável", LogLevel.INFO, "hardware")
        logger.log_event("Protocolo completado com sucesso", LogLevel.INFO, "protocol")
        
        # Finalizar sessão
        summary = {
            'device_info': {'final_temperature': 25.5}
        }
        
        csv_path = logger.finalize_session(summary)
        print(f"✅ Sessão finalizada: {csv_path}")
        
        # Mostrar conteúdo do CSV
        print(f"\n📄 Conteúdo do CSV:")
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):  # Primeiras 10 linhas
                    print(f"   {i+1:2d}: {line.strip()}")
                if len(lines) > 10:
                    print(f"   ... (+{len(lines)-10} linhas)")
        
        print(f"\n📁 Ficheiros gerados:")
        for file_path in base_path.glob("*"):
            size_kb = file_path.stat().st_size / 1024
            print(f"   📄 {file_path.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    demo_session_logging()
