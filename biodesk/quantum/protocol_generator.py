"""
FASE 3: Sistema de Protocolos Inteligentes
==========================================

Geração automática de protocolos terapêuticos baseados em análise de ressonância
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from .resonance_analysis import ResonanceItem, ResonanceField

class ProtocolType(Enum):
    """Tipos de protocolo disponíveis"""
    HARMONIZACAO = "harmonizacao"
    NEUTRALIZACAO = "neutralizacao"
    FORTALECIMENTO = "fortalecimento"
    EQUILIBRIO = "equilibrio"
    DETOX = "detox"
    REGENERACAO = "regeneracao"

@dataclass
class ProtocolStep:
    """Passo individual do protocolo"""
    name: str
    frequency: float
    amplitude: float
    duration: int  # segundos
    resonance_item: Optional[ResonanceItem] = None
    description: str = ""
    step_type: str = "therapy"  # therapy, preparation, integration
    pause_after: int = 0  # pausa em segundos após este passo

@dataclass 
class TherapyProtocol:
    """Protocolo completo de terapia"""
    name: str
    description: str
    protocol_type: ProtocolType
    steps: List[ProtocolStep] = field(default_factory=list)
    total_duration: int = 0  # segundos
    created_date: datetime = field(default_factory=datetime.now)
    patient_witness: Dict = field(default_factory=dict)
    analysis_results: List[ResonanceItem] = field(default_factory=list)
    field_used: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_total_duration(self):
        """Calcula duração total incluindo pausas"""
        total = sum(step.duration + step.pause_after for step in self.steps)
        self.total_duration = total
        return total

class FrequencyMapper:
    """
    Mapeamento de itens de ressonância para frequências terapêuticas
    Baseado em literatura de medicina frequencial e radiônica
    """
    
    def __init__(self):
        self.frequency_mappings = self._load_frequency_mappings()
        
    def _load_frequency_mappings(self) -> Dict[str, Dict[str, float]]:
        """Carrega mapeamentos de frequências por categoria"""
        return {
            "Homeopatia": {
                # Frequências baseadas em potências homeopáticas
                "Sulphur": 432.0,
                "Calcarea carbonica": 528.0,
                "Lycopodium": 741.0,
                "Pulsatilla": 852.0,
                "Arsenicum album": 396.0,
                "Nux vomica": 285.0,
                "Phosphorus": 963.0,
                "Sepia": 417.0,
                "Tuberculinum": 174.0,
                "Medorrhinum": 639.0,
                "Syphilinum": 111.0,
                "Psorinum": 222.0,
                "Carcinosinum": 333.0,
                "Influenzinum": 444.0,
                # Sais de Schüssler
                "Calcarea fluorica": 1864.0,
                "Calcarea phosphorica": 2720.0,
                "Ferrum phosphoricum": 1840.0,
                "Kalium muriaticum": 1552.0,
                "Kalium phosphoricum": 3024.0,
                "Kalium sulphuricum": 2032.0,
                "Magnesia phosphorica": 2816.0,
                "Natrum muriaticum": 1744.0,
                "Natrum phosphoricum": 2840.0,
                "Natrum sulphuricum": 1648.0,
                "Silicea": 2128.0,
                "Calcarea sulphurica": 2360.0
            },
            
            "Acupuntura": {
                # Frequências dos meridianos (baseado em medicina chinesa)
                "Meridiano Pulmão": 72.0,
                "Meridiano Intestino Grosso": 81.0,
                "Meridiano Estômago": 90.0,
                "Meridiano Baço": 99.0,
                "Meridiano Coração": 108.0,
                "Meridiano Intestino Delgado": 117.0,
                "Meridiano Bexiga": 126.0,
                "Meridiano Rim": 135.0,
                "Meridiano Pericárdio": 144.0,
                "Meridiano Triplo Aquecedor": 153.0,
                "Meridiano Vesícula Biliar": 162.0,
                "Meridiano Fígado": 171.0,
                # Pontos especiais
                "Yintang": 256.0,
                "Baihui": 512.0,
                "Shenmen": 1024.0,
                "Hegu": 64.0,
                "Zusanli": 128.0,
                "Sanyinjiao": 192.0
            },
            
            "Medicina Natural": {
                # Frequências de plantas medicinais
                "Echinacea": 304.0,
                "Ginkgo biloba": 608.0,
                "Ginseng": 912.0,
                "Hypericum": 216.0,
                "Valeriana": 324.0,
                "Passiflora": 432.0,
                "Melissa": 540.0,
                "Chamomilla": 648.0,
                "Ashwagandha": 756.0,
                "Brahmi": 864.0,
                "Triphala": 972.0,
                "Turmeric": 1080.0,
                # Aromaterapia
                "Lavanda": 40.0,
                "Tea Tree": 88.0,
                "Eucalipto": 136.0,
                "Rosmarinho": 184.0,
                "Limão": 232.0,
                "Laranja": 280.0,
                "Ylang-ylang": 328.0,
                "Bergamota": 376.0
            },
            
            "Nutrição": {
                # Frequências de nutrientes
                "Vitamina A": 1000.0,
                "Vitamina B1": 1100.0,
                "Vitamina B2": 1200.0,
                "Vitamina B6": 1300.0,
                "Vitamina B12": 1400.0,
                "Vitamina C": 1500.0,
                "Vitamina D": 1600.0,
                "Vitamina E": 1700.0,
                "Vitamina K": 1800.0,
                "Ácido Fólico": 1900.0,
                "Biotina": 2000.0,
                "Niacina": 2100.0,
                # Minerais
                "Cálcio": 2200.0,
                "Magnésio": 2300.0,
                "Zinco": 2400.0,
                "Ferro": 2500.0,
                "Selénio": 2600.0,
                "Crómio": 2700.0,
                "Manganês": 2800.0,
                "Cobre": 2900.0,
                "Iodo": 3000.0,
                "Potássio": 3100.0
            },
            
            "Órgãos e Sistemas": {
                # Frequências dos órgãos (baseado em medicina vibracional)
                "Coração": 341.3,
                "Pulmões": 220.0,
                "Fígado": 317.83,
                "Rim": 319.88,
                "Estômago": 110.0,
                "Intestino Delgado": 164.3,
                "Intestino Grosso": 176.0,
                "Vesícula Biliar": 164.3,
                "Pâncreas": 117.3,
                "Baço": 319.88,
                "Cérebro": 256.0,
                "Medula Espinhal": 386.0,
                "Timo": 319.88,
                "Pineal": 963.0,
                "Hipófise": 144.0,
                "Tiroide": 384.0,
                "Suprarrenais": 492.8
            }
        }
    
    def get_frequency(self, item: ResonanceItem) -> float:
        """Obtém frequência terapêutica para um item"""
        category_map = self.frequency_mappings.get(item.category, {})
        
        # Tentar match exato primeiro
        if item.name in category_map:
            return category_map[item.name]
        
        # Tentar match parcial
        for name, freq in category_map.items():
            if name.lower() in item.name.lower() or item.name.lower() in name.lower():
                return freq
        
        # Frequência baseada em hash se não encontrar
        item_hash = hash(f"{item.category}_{item.name}")
        base_frequencies = [111, 222, 333, 444, 528, 639, 741, 852, 963]
        return base_frequencies[abs(item_hash) % len(base_frequencies)]

class ProtocolGenerator:
    """
    Gerador de protocolos terapêuticos baseados em análise de ressonância
    """
    
    def __init__(self):
        self.frequency_mapper = FrequencyMapper()
        self.amplitude_settings = {
            "preparation": 1.5,    # Preparação suave
            "harmonization": 2.0,  # Harmonização standard
            "neutralization": 2.5, # Neutralização ativa
            "integration": 1.0     # Integração suave
        }
        
    def generate_protocol(self, 
                         analysis_results: List[ResonanceItem],
                         protocol_type: ProtocolType,
                         patient_witness: Dict,
                         field_used: str,
                         options: Dict = None) -> TherapyProtocol:
        """
        Gera protocolo terapêutico baseado nos resultados da análise
        """
        options = options or {}
        
        # Filtrar e ordenar resultados
        positive_items = [item for item in analysis_results if item.resonance_value > 0]
        negative_items = [item for item in analysis_results if item.resonance_value < 0]
        
        # Ordenar por força de ressonância
        positive_items.sort(key=lambda x: x.resonance_value, reverse=True)
        negative_items.sort(key=lambda x: abs(x.resonance_value), reverse=True)
        
        # Criar protocolo baseado no tipo
        if protocol_type == ProtocolType.HARMONIZACAO:
            protocol = self._create_harmonization_protocol(positive_items, patient_witness, field_used)
        elif protocol_type == ProtocolType.NEUTRALIZACAO:
            protocol = self._create_neutralization_protocol(negative_items, patient_witness, field_used)
        elif protocol_type == ProtocolType.FORTALECIMENTO:
            protocol = self._create_strengthening_protocol(positive_items, patient_witness, field_used)
        elif protocol_type == ProtocolType.EQUILIBRIO:
            protocol = self._create_balance_protocol(positive_items, negative_items, patient_witness, field_used)
        elif protocol_type == ProtocolType.DETOX:
            protocol = self._create_detox_protocol(negative_items, patient_witness, field_used)
        elif protocol_type == ProtocolType.REGENERACAO:
            protocol = self._create_regeneration_protocol(positive_items, patient_witness, field_used)
        else:
            raise ValueError(f"Tipo de protocolo não suportado: {protocol_type}")
        
        protocol.analysis_results = analysis_results
        protocol.calculate_total_duration()
        
        return protocol
    
    def _create_harmonization_protocol(self, positive_items: List[ResonanceItem], 
                                     patient_witness: Dict, field_used: str) -> TherapyProtocol:
        """Protocolo de harmonização com itens positivos"""
        protocol = TherapyProtocol(
            name="Harmonização Informacional",
            description="Protocolo para reforçar padrões ressonantes positivos",
            protocol_type=ProtocolType.HARMONIZACAO,
            patient_witness=patient_witness,
            field_used=field_used
        )
        
        steps = []
        
        # 1. Preparação (frequência base de harmonização)
        steps.append(ProtocolStep(
            name="Preparação - Abertura",
            frequency=528.0,  # Frequência do Amor
            amplitude=self.amplitude_settings["preparation"],
            duration=60,  # 1 minuto
            description="Preparação energética para harmonização",
            step_type="preparation",
            pause_after=10
        ))
        
        # 2. Harmonização com os 5 itens mais ressonantes
        top_items = positive_items[:5]
        for i, item in enumerate(top_items):
            freq = self.frequency_mapper.get_frequency(item)
            duration = min(120, max(60, int(item.resonance_value * 1.2)))  # 60-120s baseado na ressonância
            
            steps.append(ProtocolStep(
                name=f"Harmonização - {item.name}",
                frequency=freq,
                amplitude=self.amplitude_settings["harmonization"],
                duration=duration,
                resonance_item=item,
                description=f"Reforço da ressonância positiva ({item.resonance_value:+d})",
                step_type="therapy",
                pause_after=15 if i < len(top_items)-1 else 30
            ))
        
        # 3. Integração (frequência de fechamento)
        steps.append(ProtocolStep(
            name="Integração - Fechamento",
            frequency=396.0,  # Frequência de libertação
            amplitude=self.amplitude_settings["integration"],
            duration=90,
            description="Integração e estabilização dos padrões harmonizados",
            step_type="integration"
        ))
        
        protocol.steps = steps
        return protocol
    
    def _create_neutralization_protocol(self, negative_items: List[ResonanceItem],
                                      patient_witness: Dict, field_used: str) -> TherapyProtocol:
        """Protocolo de neutralização de stressors"""
        protocol = TherapyProtocol(
            name="Neutralização de Stressors",
            description="Protocolo para neutralizar padrões de stress informacional",
            protocol_type=ProtocolType.NEUTRALIZACAO,
            patient_witness=patient_witness,
            field_used=field_used
        )
        
        steps = []
        
        # 1. Preparação
        steps.append(ProtocolStep(
            name="Preparação - Proteção",
            frequency=741.0,  # Frequência de limpeza
            amplitude=self.amplitude_settings["preparation"],
            duration=90,
            description="Preparação para neutralização de stressors",
            step_type="preparation",
            pause_after=15
        ))
        
        # 2. Neutralização dos 3 stressors mais fortes
        top_stressors = negative_items[:3]
        for i, item in enumerate(top_stressors):
            freq = self.frequency_mapper.get_frequency(item)
            # Usar frequência inversa para neutralização
            inverse_freq = freq * 0.618  # Proporção áurea para inversão
            duration = min(180, max(90, int(abs(item.resonance_value) * 1.5)))
            
            steps.append(ProtocolStep(
                name=f"Neutralização - {item.name}",
                frequency=inverse_freq,
                amplitude=self.amplitude_settings["neutralization"],
                duration=duration,
                resonance_item=item,
                description=f"Neutralização de stressor ({item.resonance_value:+d})",
                step_type="therapy",
                pause_after=20 if i < len(top_stressors)-1 else 30
            ))
        
        # 3. Limpeza energética
        steps.append(ProtocolStep(
            name="Limpeza - Purificação",
            frequency=852.0,  # Frequência de purificação
            amplitude=self.amplitude_settings["harmonization"],
            duration=120,
            description="Limpeza energética pós-neutralização",
            step_type="therapy",
            pause_after=20
        ))
        
        # 4. Integração
        steps.append(ProtocolStep(
            name="Integração - Estabilização",
            frequency=432.0,  # Frequência natural
            amplitude=self.amplitude_settings["integration"],
            duration=90,
            description="Estabilização após neutralização",
            step_type="integration"
        ))
        
        protocol.steps = steps
        return protocol
    
    def _create_balance_protocol(self, positive_items: List[ResonanceItem],
                               negative_items: List[ResonanceItem],
                               patient_witness: Dict, field_used: str) -> TherapyProtocol:
        """Protocolo de equilíbrio completo"""
        protocol = TherapyProtocol(
            name="Equilíbrio Informacional Completo",
            description="Protocolo combinado de neutralização e harmonização",
            protocol_type=ProtocolType.EQUILIBRIO,
            patient_witness=patient_witness,
            field_used=field_used
        )
        
        steps = []
        
        # 1. Preparação
        steps.append(ProtocolStep(
            name="Preparação - Centragem",
            frequency=256.0,  # Frequência de centragem
            amplitude=self.amplitude_settings["preparation"],
            duration=90,
            description="Centragem energética para equilíbrio",
            step_type="preparation",
            pause_after=15
        ))
        
        # 2. Neutralização (2 stressors principais)
        top_stressors = negative_items[:2]
        for item in top_stressors:
            freq = self.frequency_mapper.get_frequency(item) * 0.618
            duration = min(150, max(90, int(abs(item.resonance_value) * 1.2)))
            
            steps.append(ProtocolStep(
                name=f"Neutralização - {item.name}",
                frequency=freq,
                amplitude=self.amplitude_settings["neutralization"],
                duration=duration,
                resonance_item=item,
                description=f"Neutralização equilibrada ({item.resonance_value:+d})",
                step_type="therapy",
                pause_after=15
            ))
        
        # 3. Harmonização (3 itens positivos principais)
        top_positive = positive_items[:3]
        for item in top_positive:
            freq = self.frequency_mapper.get_frequency(item)
            duration = min(120, max(60, int(item.resonance_value * 1.0)))
            
            steps.append(ProtocolStep(
                name=f"Harmonização - {item.name}",
                frequency=freq,
                amplitude=self.amplitude_settings["harmonization"],
                duration=duration,
                resonance_item=item,
                description=f"Harmonização equilibrada ({item.resonance_value:+d})",
                step_type="therapy",
                pause_after=15
            ))
        
        # 4. Integração final
        steps.append(ProtocolStep(
            name="Integração - Equilíbrio Final",
            frequency=528.0,  # Frequência do amor/equilíbrio
            amplitude=self.amplitude_settings["integration"],
            duration=120,
            description="Integração e estabilização do equilíbrio",
            step_type="integration"
        ))
        
        protocol.steps = steps
        return protocol
    
    def _create_strengthening_protocol(self, positive_items: List[ResonanceItem],
                                     patient_witness: Dict, field_used: str) -> TherapyProtocol:
        """Protocolo de fortalecimento intensivo"""
        protocol = TherapyProtocol(
            name="Fortalecimento Intensivo",
            description="Protocolo para amplificar padrões positivos dominantes",
            protocol_type=ProtocolType.FORTALECIMENTO,
            patient_witness=patient_witness,
            field_used=field_used
        )
        
        steps = []
        
        # Protocolo mais intensivo com os 7 melhores itens
        top_items = positive_items[:7]
        
        # Preparação específica
        steps.append(ProtocolStep(
            name="Preparação - Ativação",
            frequency=963.0,  # Frequência de ativação
            amplitude=self.amplitude_settings["preparation"],
            duration=60,
            description="Ativação para fortalecimento",
            step_type="preparation",
            pause_after=10
        ))
        
        # Fortalecimento por ondas
        for wave in range(2):  # 2 ondas de fortalecimento
            for i, item in enumerate(top_items):
                freq = self.frequency_mapper.get_frequency(item)
                if wave == 1:  # Segunda onda com frequência harmonizada
                    freq = freq * 1.618  # Proporção áurea
                
                duration = min(90, max(45, int(item.resonance_value * 0.8)))
                amplitude = self.amplitude_settings["harmonization"] * (1.1 if wave == 1 else 1.0)
                
                steps.append(ProtocolStep(
                    name=f"Fortalecimento {wave+1} - {item.name}",
                    frequency=freq,
                    amplitude=amplitude,
                    duration=duration,
                    resonance_item=item,
                    description=f"Fortalecimento onda {wave+1} ({item.resonance_value:+d})",
                    step_type="therapy",
                    pause_after=10 if i < len(top_items)-1 else 20
                ))
        
        # Integração potenciada
        steps.append(ProtocolStep(
            name="Integração - Potenciação",
            frequency=639.0,  # Frequência de conexão
            amplitude=self.amplitude_settings["integration"],
            duration=120,
            description="Integração e potenciação dos padrões fortalecidos",
            step_type="integration"
        ))
        
        protocol.steps = steps
        return protocol
    
    def _create_detox_protocol(self, negative_items: List[ResonanceItem],
                             patient_witness: Dict, field_used: str) -> TherapyProtocol:
        """Protocolo de desintoxicação informacional"""
        protocol = TherapyProtocol(
            name="Desintoxicação Informacional",
            description="Protocolo especializado em limpeza de padrões tóxicos",
            protocol_type=ProtocolType.DETOX,
            patient_witness=patient_witness,
            field_used=field_used
        )
        
        steps = []
        
        # Preparação para detox
        steps.append(ProtocolStep(
            name="Preparação - Ativação Detox",
            frequency=174.0,  # Frequência de libertação
            amplitude=self.amplitude_settings["preparation"],
            duration=120,
            description="Ativação dos sistemas de limpeza",
            step_type="preparation",
            pause_after=20
        ))
        
        # Processo de limpeza em camadas
        detox_frequencies = [285.0, 396.0, 741.0]  # Frequências de limpeza
        
        for i, freq in enumerate(detox_frequencies):
            steps.append(ProtocolStep(
                name=f"Limpeza Camada {i+1}",
                frequency=freq,
                amplitude=self.amplitude_settings["neutralization"],
                duration=180,  # 3 minutos por camada
                description=f"Limpeza profunda camada {i+1}",
                step_type="therapy",
                pause_after=30
            ))
        
        # Neutralização específica dos stressors mais fortes
        strong_stressors = [item for item in negative_items if item.resonance_value <= -50][:3]
        for item in strong_stressors:
            freq = self.frequency_mapper.get_frequency(item) * 0.5  # Frequência de dissolução
            
            steps.append(ProtocolStep(
                name=f"Dissolução - {item.name}",
                frequency=freq,
                amplitude=self.amplitude_settings["neutralization"],
                duration=120,
                resonance_item=item,
                description=f"Dissolução de padrão tóxico ({item.resonance_value:+d})",
                step_type="therapy",
                pause_after=20
            ))
        
        # Regeneração pós-detox
        steps.append(ProtocolStep(
            name="Regeneração - Renovação",
            frequency=528.0,  # Frequência regenerativa
            amplitude=self.amplitude_settings["harmonization"],
            duration=180,
            description="Regeneração após desintoxicação",
            step_type="therapy",
            pause_after=30
        ))
        
        # Integração final
        steps.append(ProtocolStep(
            name="Integração - Estabilização",
            frequency=432.0,  # Frequência natural
            amplitude=self.amplitude_settings["integration"],
            duration=120,
            description="Estabilização pós-detox",
            step_type="integration"
        ))
        
        protocol.steps = steps
        return protocol
    
    def _create_regeneration_protocol(self, positive_items: List[ResonanceItem],
                                    patient_witness: Dict, field_used: str) -> TherapyProtocol:
        """Protocolo de regeneração e revitalização"""
        protocol = TherapyProtocol(
            name="Regeneração e Revitalização",
            description="Protocolo para estimular processos regenerativos",
            protocol_type=ProtocolType.REGENERACAO,
            patient_witness=patient_witness,
            field_used=field_used
        )
        
        steps = []
        
        # Ativação regenerativa
        steps.append(ProtocolStep(
            name="Ativação - Regeneração",
            frequency=111.0,  # Frequência de ativação celular
            amplitude=self.amplitude_settings["preparation"],
            duration=90,
            description="Ativação dos processos regenerativos",
            step_type="preparation",
            pause_after=15
        ))
        
        # Sequência de frequências regenerativas
        regen_frequencies = [528.0, 639.0, 741.0, 852.0, 963.0]  # Sequência solfeggio
        
        for i, freq in enumerate(regen_frequencies):
            steps.append(ProtocolStep(
                name=f"Regeneração {i+1} - {freq}Hz",
                frequency=freq,
                amplitude=self.amplitude_settings["harmonization"],
                duration=120,
                description=f"Estímulo regenerativo nível {i+1}",
                step_type="therapy",
                pause_after=20
            ))
        
        # Reforço com itens positivos mais regenerativos
        regen_items = [item for item in positive_items 
                      if any(keyword in item.name.lower() or keyword in item.category.lower()
                           for keyword in ['vita', 'regen', 'repair', 'heal', 'restor'])][:3]
        
        if not regen_items:  # Se não há itens específicos, usar os 3 mais fortes
            regen_items = positive_items[:3]
        
        for item in regen_items:
            freq = self.frequency_mapper.get_frequency(item) * 1.414  # Multiplicar por raiz de 2
            
            steps.append(ProtocolStep(
                name=f"Revitalização - {item.name}",
                frequency=freq,
                amplitude=self.amplitude_settings["harmonization"],
                duration=150,
                resonance_item=item,
                description=f"Revitalização específica ({item.resonance_value:+d})",
                step_type="therapy",
                pause_after=25
            ))
        
        # Integração regenerativa
        steps.append(ProtocolStep(
            name="Integração - Consolidação",
            frequency=432.0,  # Frequência natural
            amplitude=self.amplitude_settings["integration"],
            duration=180,  # 3 minutos para consolidação
            description="Consolidação dos processos regenerativos",
            step_type="integration"
        ))
        
        protocol.steps = steps
        return protocol
    
    def estimate_protocol_effectiveness(self, protocol: TherapyProtocol) -> Dict[str, float]:
        """Estima eficácia do protocolo baseado nos parâmetros"""
        scores = {
            "strength": 0.0,        # Força do protocolo
            "balance": 0.0,         # Equilíbrio
            "coherence": 0.0,       # Coerência
            "duration_score": 0.0,  # Adequação da duração
            "overall": 0.0          # Pontuação geral
        }
        
        if not protocol.steps:
            return scores
        
        # Calcular força baseada na ressonância dos itens
        resonance_values = [step.resonance_item.resonance_value 
                          for step in protocol.steps 
                          if step.resonance_item]
        
        if resonance_values:
            avg_resonance = sum(abs(v) for v in resonance_values) / len(resonance_values)
            scores["strength"] = min(1.0, avg_resonance / 80.0)  # Normalizar para 0-1
        
        # Calcular equilíbrio (variedade de tipos de passo)
        step_types = set(step.step_type for step in protocol.steps)
        scores["balance"] = len(step_types) / 3.0  # Máximo 3 tipos
        
        # Calcular coerência (frequências harmônicas)
        frequencies = [step.frequency for step in protocol.steps]
        if len(frequencies) > 1:
            # Verificar relações harmônicas
            harmonic_score = 0
            for i in range(len(frequencies)-1):
                ratio = frequencies[i+1] / frequencies[i]
                if 0.5 <= ratio <= 2.0:  # Oitava
                    harmonic_score += 1
                elif abs(ratio - 1.5) < 0.1:  # Quinta
                    harmonic_score += 0.8
                elif abs(ratio - 1.25) < 0.1:  # Quarta
                    harmonic_score += 0.6
            scores["coherence"] = min(1.0, harmonic_score / (len(frequencies)-1))
        
        # Avaliar duração (15-45 minutos é ideal)
        duration_minutes = protocol.total_duration / 60
        if 15 <= duration_minutes <= 45:
            scores["duration_score"] = 1.0
        elif duration_minutes < 15:
            scores["duration_score"] = duration_minutes / 15
        else:
            scores["duration_score"] = max(0.3, 1.0 - (duration_minutes - 45) / 60)
        
        # Pontuação geral
        scores["overall"] = (
            scores["strength"] * 0.4 +
            scores["balance"] * 0.2 +
            scores["coherence"] * 0.2 +
            scores["duration_score"] * 0.2
        )
        
        return scores

# Instância global do gerador
protocol_generator = ProtocolGenerator()
