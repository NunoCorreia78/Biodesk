"""
Parser do Excel de Frequências - Biodesk Quantum
═══════════════════════════════════════════════════════════════════════

Parser robusto para ler o FrequencyList.xls e extrair frequências terapêuticas.
Inclui cache inteligente e validação rigorosa dos dados.
"""

import os
import pickle
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

try:
    import xlrd
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False

# Não usar pandas devido a incompatibilidades
PANDAS_AVAILABLE = False


@dataclass
class Protocol:
    """Protocolo de frequências para terapia"""
    disease: str
    indikationen: str
    frequencies: List[float]
    dwell_time_s: float = 3.0
    amplitude_vpp: float = 1.0
    waveform: str = "sine"
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validar protocolo após criação"""
        if not self.frequencies:
            raise ValueError("Protocolo deve ter pelo menos uma frequência")
        
        if any(f <= 0 for f in self.frequencies):
            raise ValueError("Todas as frequências devem ser positivas")
        
        if self.dwell_time_s <= 0:
            raise ValueError("Tempo de permanência deve ser positivo")
        
        if self.amplitude_vpp <= 0:
            raise ValueError("Amplitude deve ser positiva")
    
    @property
    def total_duration_s(self) -> float:
        """Duração total do protocolo"""
        return len(self.frequencies) * self.dwell_time_s
    
    @property
    def frequency_range(self) -> Tuple[float, float]:
        """Faixa de frequências (min, max)"""
        return min(self.frequencies), max(self.frequencies)


class ExcelFrequencyParser:
    """
    Parser do Excel de frequências FrequencyList.xls
    
    Funcionalidades:
    - Leitura robusta com cache automático
    - Pesquisa por doença/indicação
    - Geração de protocolos terapêuticos
    - Validação e limpeza de dados
    """
    
    def __init__(self, excel_path: Optional[str] = None):
        """
        Inicializa o parser
        
        Args:
            excel_path: Caminho para o FrequencyList.xls (None usa padrão)
        """
        self.logger = logging.getLogger("ExcelFrequencyParser")
        
        # Configurar caminho do arquivo
        if excel_path is None:
            # Caminho padrão relativo
            base_dir = Path(__file__).parent.parent.parent
            self.excel_path = base_dir / "assets" / "FrequencyList.xls"
        else:
            self.excel_path = Path(excel_path)
        
        # Cache
        self.cache_path = self.excel_path.parent / f".{self.excel_path.stem}_cache.pkl"
        self.data: Optional[List[Dict[str, Any]]] = None
        self.last_modified: Optional[float] = None
        
        # Verificar disponibilidade de bibliotecas
        if not XLRD_AVAILABLE:
            raise ImportError(
                "xlrd não disponível. Instale com: pip install xlrd"
            )
    
    def _get_file_mtime(self) -> float:
        """Obter timestamp de modificação do arquivo"""
        try:
            return os.path.getmtime(self.excel_path)
        except OSError:
            return 0.0
    
    def _load_from_cache(self) -> bool:
        """
        Carregar dados do cache se válido
        
        Returns:
            True se carregou do cache, False caso contrário
        """
        try:
            if not self.cache_path.exists():
                return False
            
            current_mtime = self._get_file_mtime()
            cache_mtime = os.path.getmtime(self.cache_path)
            
            # Cache inválido se arquivo foi modificado
            if current_mtime > cache_mtime:
                self.logger.info("📝 Cache invalidado - arquivo modificado")
                return False
            
            # Carregar cache
            with open(self.cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            self.data = cached_data['data']
            self.last_modified = cached_data['mtime']
            
            self.logger.info(f"⚡ Dados carregados do cache ({len(self.data)} entradas)")
            return True
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar cache: {e}")
            return False
    
    def _save_to_cache(self) -> None:
        """Salvar dados no cache"""
        try:
            cache_data = {
                'data': self.data,
                'mtime': self.last_modified,
                'created_at': datetime.now().isoformat()
            }
            
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.logger.info(f"💾 Cache salvo ({len(self.data)} entradas)")
            
        except Exception as e:
            self.logger.warning(f"Erro ao salvar cache: {e}")
    
    def _clean_frequency_value(self, value: Any) -> Optional[float]:
        """
        Limpar e validar valor de frequência
        
        Args:
            value: Valor bruto da célula
            
        Returns:
            Frequência válida ou None se inválida
        """
        if value is None:
            return None
        
        # Converter para float
        try:
            freq = float(value)
        except (ValueError, TypeError):
            return None
        
        # Filtrar valores inválidos
        if freq <= 0 or freq != freq:  # freq != freq detecta NaN
            return None
        
        # Limite razoável (até 1 MHz)
        if freq > 1_000_000:
            return None
        
        return freq
    
    def _parse_excel_data(self) -> List[Dict[str, Any]]:
        """
        Fazer parsing dos dados do Excel
        
        Returns:
            Lista de dicionários com dados limpos
        """
        self.logger.info(f"📖 Lendo Excel: {self.excel_path}")
        
        try:
            # Abrir workbook
            workbook = xlrd.open_workbook(str(self.excel_path))
            sheet = workbook.sheet_by_index(0)
            
            self.logger.info(f"📊 Planilha: {sheet.nrows} linhas x {sheet.ncols} colunas")
            
            # Ler cabeçalhos (primeira linha)
            if sheet.nrows == 0:
                raise ValueError("Planilha vazia")
            
            headers = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
            
            # Validar estrutura esperada
            if 'Indikationen' not in headers or 'Disease' not in headers:
                raise ValueError("Colunas 'Indikationen' e 'Disease' não encontradas")
            
            # Identificar colunas de frequência (Freq 1, Freq 2, ...)
            freq_columns = []
            for i, header in enumerate(headers):
                if isinstance(header, str) and header.startswith('Freq '):
                    freq_columns.append(i)
            
            if not freq_columns:
                raise ValueError("Nenhuma coluna de frequência encontrada")
            
            self.logger.info(f"🔢 Encontradas {len(freq_columns)} colunas de frequência")
            
            # Processar dados linha por linha
            data = []
            indikationen_col = headers.index('Indikationen')
            disease_col = headers.index('Disease')
            
            for row in range(1, sheet.nrows):  # Pular cabeçalho
                try:
                    # Ler campos principais
                    indikationen = sheet.cell_value(row, indikationen_col)
                    disease = sheet.cell_value(row, disease_col)
                    
                    # Pular linhas com dados principais vazios
                    if not indikationen or not disease:
                        continue
                    
                    # Ler e limpar frequências
                    frequencies = []
                    for freq_col in freq_columns:
                        if freq_col < sheet.ncols:  # Verificar limites
                            raw_value = sheet.cell_value(row, freq_col)
                            clean_freq = self._clean_frequency_value(raw_value)
                            if clean_freq is not None:
                                frequencies.append(clean_freq)
                    
                    # Só incluir se tiver frequências válidas
                    if frequencies:
                        data.append({
                            'indikationen': str(indikationen).strip(),
                            'disease': str(disease).strip(),
                            'frequencies': frequencies,
                            'frequency_count': len(frequencies),
                            'min_freq': min(frequencies),
                            'max_freq': max(frequencies),
                            'row_index': row
                        })
                
                except Exception as e:
                    self.logger.warning(f"Erro na linha {row}: {e}")
                    continue
            
            self.logger.info(f"✅ Processadas {len(data)} entradas válidas")
            return data
            
        except Exception as e:
            raise RuntimeError(f"Erro ao processar Excel: {e}")
    
    def load_data(self, force_reload: bool = False) -> None:
        """
        Carregar dados do Excel (com cache)
        
        Args:
            force_reload: Forçar recarregamento ignorando cache
        """
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.excel_path}")
        
        # Tentar cache primeiro (se não forçar reload)
        if not force_reload and self._load_from_cache():
            return
        
        # Carregar do Excel
        self.data = self._parse_excel_data()
        self.last_modified = self._get_file_mtime()
        
        # Salvar cache
        self._save_to_cache()
    
    def list_diseases(self) -> List[str]:
        """
        Listar todas as doenças disponíveis
        
        Returns:
            Lista ordenada de nomes de doenças
        """
        if self.data is None:
            self.load_data()
        
        diseases = set()
        for entry in self.data:
            diseases.add(entry['disease'])
        
        return sorted(list(diseases))
    
    def get_frequencies_by_disease(self, name: str) -> List[float]:
        """
        Obter frequências para uma doença específica
        
        Args:
            name: Nome da doença (case-insensitive)
            
        Returns:
            Lista de frequências válidas (> 0)
        """
        if self.data is None:
            self.load_data()
        
        name_lower = name.lower().strip()
        all_frequencies = []
        
        for entry in self.data:
            if entry['disease'].lower() == name_lower:
                all_frequencies.extend(entry['frequencies'])
        
        # Remover duplicatas e ordenar
        unique_frequencies = sorted(list(set(all_frequencies)))
        
        # Filtrar apenas positivas (redundante, mas seguro)
        return [f for f in unique_frequencies if f > 0]
    
    def search(self, query: str) -> List[Tuple[str, str]]:
        """
        Pesquisar por doença ou indicação
        
        Args:
            query: Termo de pesquisa (case-insensitive)
            
        Returns:
            Lista de tuplas (disease, indikationen) que fazem match
        """
        if self.data is None:
            self.load_data()
        
        query_lower = query.lower().strip()
        results = []
        
        for entry in self.data:
            disease = entry['disease']
            indikationen = entry['indikationen']
            
            # Pesquisar em ambos os campos
            if (query_lower in disease.lower() or 
                query_lower in indikationen.lower()):
                results.append((disease, indikationen))
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_results = []
        for item in results:
            if item not in seen:
                seen.add(item)
                unique_results.append(item)
        
        return unique_results
    
    def build_protocol_from_disease(self, 
                                  disease: str,
                                  dwell_s: float = 3.0,
                                  amp_vpp: float = 1.0,
                                  waveform: str = "sine") -> Optional[Protocol]:
        """
        Construir protocolo terapêutico para uma doença
        
        Args:
            disease: Nome da doença
            dwell_s: Tempo de permanência por frequência (segundos)
            amp_vpp: Amplitude pico-a-pico (volts)
            waveform: Tipo de forma de onda
            
        Returns:
            Protocolo construído ou None se não encontrado
        """
        if self.data is None:
            self.load_data()
        
        frequencies = self.get_frequencies_by_disease(disease)
        
        if not frequencies:
            self.logger.warning(f"Nenhuma frequência encontrada para: {disease}")
            return None
        
        # Encontrar indicação correspondente
        disease_lower = disease.lower().strip()
        indikationen = ""
        
        for entry in self.data:
            if entry['disease'].lower() == disease_lower:
                indikationen = entry['indikationen']
                break
        
        try:
            protocol = Protocol(
                disease=disease,
                indikationen=indikationen,
                frequencies=frequencies,
                dwell_time_s=dwell_s,
                amplitude_vpp=amp_vpp,
                waveform=waveform
            )
            
            self.logger.info(
                f"📋 Protocolo criado para '{disease}': "
                f"{len(frequencies)} frequências, "
                f"duração total: {protocol.total_duration_s:.1f}s"
            )
            
            return protocol
            
        except ValueError as e:
            self.logger.error(f"Erro ao criar protocolo: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obter estatísticas dos dados carregados
        
        Returns:
            Dicionário com estatísticas
        """
        if self.data is None:
            self.load_data()
        
        total_entries = len(self.data)
        all_frequencies = []
        diseases = set()
        indikationen = set()
        
        for entry in self.data:
            all_frequencies.extend(entry['frequencies'])
            diseases.add(entry['disease'])
            indikationen.add(entry['indikationen'])
        
        return {
            'total_entries': total_entries,
            'unique_diseases': len(diseases),
            'unique_indikationen': len(indikationen),
            'total_frequencies': len(all_frequencies),
            'unique_frequencies': len(set(all_frequencies)),
            'frequency_range': (min(all_frequencies), max(all_frequencies)) if all_frequencies else (0, 0),
            'avg_frequencies_per_entry': len(all_frequencies) / total_entries if total_entries > 0 else 0,
            'file_path': str(self.excel_path),
            'last_modified': datetime.fromtimestamp(self.last_modified) if self.last_modified else None
        }


# ═══════════════════════════════════════════════════════════════════════
# TESTES (executar com: python -m pytest biodesk/quantum/excel_parser.py)
# ═══════════════════════════════════════════════════════════════════════

def test_protocol_creation():
    """Teste básico de criação de protocolo"""
    frequencies = [10.0, 20.0, 30.0]
    
    protocol = Protocol(
        disease="Test Disease",
        indikationen="Test Indication",
        frequencies=frequencies,
        dwell_time_s=2.0,
        amplitude_vpp=0.5,
        waveform="square"
    )
    
    assert protocol.disease == "Test Disease"
    assert protocol.frequencies == frequencies
    assert protocol.total_duration_s == 6.0  # 3 freq * 2s
    assert protocol.frequency_range == (10.0, 30.0)


def test_protocol_validation():
    """Teste de validação de protocolo"""
    try:
        # Frequência zero deve falhar
        Protocol(
            disease="Test",
            indikationen="Test",
            frequencies=[10.0, 0.0, 30.0],
            dwell_time_s=1.0,
            amplitude_vpp=1.0
        )
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass  # Esperado
    
    try:
        # Lista vazia deve falhar
        Protocol(
            disease="Test",
            indikationen="Test",
            frequencies=[],
            dwell_time_s=1.0,
            amplitude_vpp=1.0
        )
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass  # Esperado


def test_frequency_cleaning():
    """Teste de limpeza de valores de frequência"""
    parser = ExcelFrequencyParser("/fake/path")  # Não vai carregar dados
    
    # Valores válidos
    assert parser._clean_frequency_value(10.5) == 10.5
    assert parser._clean_frequency_value("20.0") == 20.0
    assert parser._clean_frequency_value(100) == 100.0
    
    # Valores inválidos
    assert parser._clean_frequency_value(0) is None
    assert parser._clean_frequency_value(-10) is None
    assert parser._clean_frequency_value("invalid") is None
    assert parser._clean_frequency_value(None) is None
    assert parser._clean_frequency_value(float('nan')) is None


# TODO: Teste com arquivo real do FrequencyList.xls
def test_with_real_file():
    """
    TODO: Teste com o arquivo FrequencyList.xls real
    
    Este teste deve ser executado apenas quando o arquivo estiver disponível.
    """
    # Caminho para o arquivo real
    real_file_path = Path(__file__).parent.parent.parent / "assets" / "FrequencyList.xls"
    
    if not real_file_path.exists():
        print(f"⚠️  Arquivo real não encontrado: {real_file_path}")
        print("   Teste será pulado")
        return
    
    try:
        parser = ExcelFrequencyParser(str(real_file_path))
        parser.load_data()
        
        # Verificações básicas
        stats = parser.get_statistics()
        print(f"📊 Estatísticas do arquivo real:")
        print(f"   Entradas: {stats['total_entries']}")
        print(f"   Doenças únicas: {stats['unique_diseases']}")
        print(f"   Frequências únicas: {stats['unique_frequencies']}")
        print(f"   Faixa: {stats['frequency_range'][0]:.1f} - {stats['frequency_range'][1]:.1f} Hz")
        
        # Testar algumas funcionalidades
        diseases = parser.list_diseases()
        assert len(diseases) > 0, "Deveria ter pelo menos uma doença"
        
        # Testar pesquisa
        search_results = parser.search("AAA")
        print(f"🔍 Resultados para 'AAA': {len(search_results)}")
        
        # Testar criação de protocolo
        if diseases:
            first_disease = diseases[0]
            protocol = parser.build_protocol_from_disease(first_disease)
            if protocol:
                print(f"📋 Protocolo para '{first_disease}': {len(protocol.frequencies)} frequências")
        
        print("✅ Teste com arquivo real passou")
        
    except Exception as e:
        print(f"❌ Erro no teste com arquivo real: {e}")
        raise


if __name__ == "__main__":
    # Executar testes básicos
    print("🧪 Executando testes do ExcelFrequencyParser...")
    
    test_protocol_creation()
    print("✅ test_protocol_creation")
    
    test_protocol_validation()
    print("✅ test_protocol_validation")
    
    test_frequency_cleaning()
    print("✅ test_frequency_cleaning")
    
    test_with_real_file()
    
    print("🎉 Todos os testes concluídos!")
