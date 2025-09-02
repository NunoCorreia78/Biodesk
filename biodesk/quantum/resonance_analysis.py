"""
FASE 2: Sistema de Análise de Ressonância Informacional
======================================================

Módulo que implementa análise de ressonância estilo CoRe para medicina informacional.
Baseado em princípios de ressonância e testemunho digital.
"""

import numpy as np
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
import random

@dataclass
class ResonanceItem:
    """Item para avaliação de ressonância"""
    name: str
    category: str
    subcategory: str = ""
    description: str = ""
    frequency: Optional[float] = None
    resonance_value: int = 0  # -100 a +100
    stability: float = 0.0   # 0.0 a 1.0
    confidence: float = 0.0  # 0.0 a 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class ResonanceField:
    """Campo de avaliação de ressonância"""
    name: str
    description: str
    color: str
    weight: float = 1.0

# Campos de avaliação disponíveis (baseado no CoRe)
RESONANCE_FIELDS = [
    ResonanceField("Campo informacional", "Padrões de informação e coerência quântica", "#4A90E2", 1.0),
    ResonanceField("Campo energético", "Fluxos de energia vital e meridanos", "#F5A623", 0.9),
    ResonanceField("Campo espiritual", "Conexão espiritual e propósito de vida", "#BD10E0", 0.8),
    ResonanceField("Campo físico", "Estrutura física e manifestação material", "#7ED321", 1.1),
    ResonanceField("Campo emocional", "Estados emocionais e padrões psíquicos", "#D0021B", 0.95),
]

class ResonanceAnalyzer(QThread):
    """
    Analisador de ressonância informacional
    Implementa algoritmo similar ao CoRe para avaliação não-invasiva
    """
    
    # Sinais PyQt6
    progress = pyqtSignal(int)  # 0-100%
    item_analyzed = pyqtSignal(dict)  # resultado de cada item
    analysis_complete = pyqtSignal(list)  # lista final ordenada
    status_update = pyqtSignal(str)
    field_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.items_to_analyze = []
        self.field = "Campo informacional"
        self.patient_witness = {}
        self.threshold_min = -20
        self.threshold_max = 20
        self.analysis_id = ""
        self.is_running = False
        
    def set_analysis_parameters(self, 
                               items: List[ResonanceItem],
                               field: str,
                               patient_witness: Dict,
                               threshold: Tuple[int, int] = (-20, 20)):
        """Configura parâmetros da análise"""
        self.items_to_analyze = items
        self.field = field
        self.patient_witness = patient_witness
        self.threshold_min, self.threshold_max = threshold
        
        # Gerar ID único para esta análise
        analysis_data = f"{field}_{json.dumps(patient_witness, sort_keys=True)}_{len(items)}"
        self.analysis_id = hashlib.md5(analysis_data.encode()).hexdigest()[:8]
        
    def calculate_resonance(self, item: ResonanceItem) -> Tuple[int, float, float]:
        """
        Calcula valor de ressonância (-100 a +100), estabilidade e confiança
        
        Algoritmo baseado em:
        1. Testemunho do paciente (nome, data nascimento) 
        2. Campo selecionado
        3. Propriedades do item
        4. Componente "quântica" (pseudo-aleatória mas determinística)
        5. Estabilidade temporal
        """
        
        # 1. Hash do testemunho para consistência
        witness_string = json.dumps(self.patient_witness, sort_keys=True)
        witness_hash = int(hashlib.md5(witness_string.encode()).hexdigest()[:8], 16)
        
        # 2. Hash do item
        item_string = f"{item.name}_{item.category}_{item.subcategory}"
        item_hash = int(hashlib.md5(item_string.encode()).hexdigest()[:8], 16)
        
        # 3. Hash do campo
        field_hash = int(hashlib.md5(self.field.encode()).hexdigest()[:8], 16)
        
        # 4. Combinar todos os hashes para seed determinística
        combined_seed = witness_hash ^ item_hash ^ field_hash
        np.random.seed(combined_seed % (2**32))
        
        # 5. Componente base determinística (-100 a +100)
        base_resonance = ((combined_seed % 200) - 100)
        
        # 6. Modulação pelo campo selecionado
        field_weights = {
            "Campo informacional": 1.0,
            "Campo energético": 0.9,
            "Campo espiritual": 0.8,
            "Campo físico": 1.1,
            "Campo emocional": 0.95
        }
        field_factor = field_weights.get(self.field, 1.0)
        
        # 7. Componente "quântica" (flutuação natural)
        quantum_noise = np.random.normal(0, 12)  # Desvio padrão 12
        
        # 8. Cálculo da ressonância final
        resonance = base_resonance * field_factor + quantum_noise
        resonance = int(max(-100, min(100, resonance)))
        
        # 9. Calcular estabilidade (baseada na consistência)
        stability_seed = (combined_seed >> 8) % 1000
        np.random.seed(stability_seed)
        stability = max(0.3, min(1.0, abs(np.random.normal(0.75, 0.15))))
        
        # 10. Calcular confiança (baseada no valor absoluto e estabilidade)
        confidence = min(1.0, (abs(resonance) / 100.0) * stability)
        
        return resonance, stability, confidence
    
    def run(self):
        """Executa análise de ressonância completa"""
        if not self.items_to_analyze:
            self.status_update.emit("❌ Nenhum item para analisar")
            return
            
        self.is_running = True
        results = []
        total = len(self.items_to_analyze)
        
        self.status_update.emit(f"🔮 Iniciando análise de {total} itens no {self.field}...")
        self.field_changed.emit(self.field)
        
        # Simular tempo de "conexão" com testemunho
        self.status_update.emit("🧬 Estabelecendo conexão com testemunho digital...")
        self.msleep(500)
        
        for i, item in enumerate(self.items_to_analyze):
            if not self.is_running:
                break
                
            # Calcular ressonância
            resonance, stability, confidence = self.calculate_resonance(item)
            
            # Atualizar item
            item.resonance_value = resonance
            item.stability = stability
            item.confidence = confidence
            
            # Verificar se está dentro do threshold
            in_range = self.threshold_min <= resonance <= self.threshold_max
            
            # Emitir resultado individual
            result = {
                'name': item.name,
                'category': item.category,
                'subcategory': item.subcategory,
                'value': resonance,
                'stability': stability,
                'confidence': confidence,
                'in_range': in_range,
                'field': self.field,
                'analysis_id': self.analysis_id
            }
            
            self.item_analyzed.emit(result)
            
            # Adicionar aos resultados se dentro do threshold
            if in_range:
                results.append(item)
            
            # Atualizar progresso
            progress = int((i + 1) / total * 100)
            self.progress.emit(progress)
            
            # Simular tempo de processamento (realista)
            self.msleep(50 + np.random.randint(0, 30))  # 50-80ms por item
        
        if self.is_running:
            # Ordenar por valor absoluto de ressonância (mais fortes primeiro)
            results.sort(key=lambda x: abs(x.resonance_value), reverse=True)
            
            self.status_update.emit(f"✅ Análise completa: {len(results)} itens ressonantes encontrados")
            self.analysis_complete.emit(results)
        else:
            self.status_update.emit("⏹️ Análise cancelada pelo usuário")
            
        self.is_running = False
    
    def stop_analysis(self):
        """Para a análise em andamento"""
        self.is_running = False
        self.status_update.emit("⏹️ Parando análise...")

class ResonanceDatabase:
    """
    Base de dados de itens para análise de ressonância
    Baseada nas categorias do CoRe
    """
    
    def __init__(self):
        self.categories = {}
        self._load_default_database()
    
    def _load_default_database(self):
        """Carrega base de dados padrão com categorias do CoRe"""
        
        # Acupuntura e Medicina Chinesa
        self.categories["Acupuntura"] = {
            "Acupuntura do couro cabeludo": [
                "Área motora", "Área da fala", "Área equilibrio", "Área visão"
            ],
            "Acupuntura auricular": [
                "Ponto Shen Men", "Ponto Rim", "Ponto Fígado", "Ponto Coração", "Ponto Pulmão"
            ],
            "Meridianos principais": [
                "Meridiano Pulmão", "Meridiano Intestino Grosso", "Meridiano Estômago",
                "Meridiano Baço", "Meridiano Coração", "Meridiano Intestino Delgado",
                "Meridiano Bexiga", "Meridiano Rim", "Meridiano Pericárdio",
                "Meridiano Triplo Aquecedor", "Meridiano Vesícula Biliar", "Meridiano Fígado"
            ],
            "Pontos especiais": [
                "Yintang", "Baihui", "Shenmen", "Hegu", "Zusanli", "Sanyinjiao"
            ]
        }
        
        # Homeopatia
        self.categories["Homeopatia"] = {
            "Policrestos": [
                "Sulphur", "Calcarea carbonica", "Lycopodium", "Pulsatilla",
                "Arsenicum album", "Nux vomica", "Phosphorus", "Sepia"
            ],
            "Nosódios": [
                "Tuberculinum", "Medorrhinum", "Syphilinum", "Psorinum",
                "Carcinosinum", "Influenzinum"
            ],
            "Sais de Schüssler": [
                "Calcarea fluorica", "Calcarea phosphorica", "Ferrum phosphoricum",
                "Kalium muriaticum", "Kalium phosphoricum", "Kalium sulphuricum",
                "Magnesia phosphorica", "Natrum muriaticum", "Natrum phosphoricum",
                "Natrum sulphuricum", "Silicea", "Calcarea sulphurica"
            ],
            "Florais de Bach": [
                "Rescue Remedy", "Rock Rose", "Mimulus", "Cherry Plum", "Aspen",
                "Red Chestnut", "Impatiens", "Cerato", "Scleranthus", "Water Violet"
            ]
        }
        
        # Fitoterapia e Medicina Natural
        self.categories["Medicina Natural"] = {
            "Fitoterapia Ocidental": [
                "Echinacea", "Ginkgo biloba", "Ginseng", "Hypericum",
                "Valeriana", "Passiflora", "Melissa", "Chamomilla"
            ],
            "Medicina Ayurvédica": [
                "Ashwagandha", "Brahmi", "Triphala", "Turmeric",
                "Guduchi", "Amalaki", "Haritaki", "Bibhitaki"
            ],
            "Medicina Chinesa": [
                "Ginseng", "Astragalus", "Schisandra", "Reishi",
                "Cordyceps", "He Shou Wu", "Dang Gui", "Gan Cao"
            ],
            "Aromaterapia": [
                "Lavanda", "Tea Tree", "Eucalipto", "Rosmarinho",
                "Limão", "Laranja", "Ylang-ylang", "Bergamota"
            ]
        }
        
        # Nutrição e Suplementos
        self.categories["Nutrição"] = {
            "Vitaminas": [
                "Vitamina A", "Vitamina B1", "Vitamina B2", "Vitamina B6",
                "Vitamina B12", "Vitamina C", "Vitamina D", "Vitamina E",
                "Vitamina K", "Ácido Fólico", "Biotina", "Niacina"
            ],
            "Minerais": [
                "Cálcio", "Magnésio", "Zinco", "Ferro", "Selénio",
                "Crómio", "Manganês", "Cobre", "Iodo", "Potássio"
            ],
            "Aminoácidos": [
                "Triptofano", "Tirosina", "Glicina", "Taurina",
                "Arginina", "Lisina", "Metionina", "Cistina"
            ],
            "Ácidos Gordos": [
                "Omega 3", "Omega 6", "Omega 9", "EPA", "DHA",
                "Ácido Linoleico", "Ácido Alfa-Linoleico"
            ]
        }
        
        # Sistemas Orgânicos
        self.categories["Órgãos e Sistemas"] = {
            "Sistema Digestivo": [
                "Estômago", "Intestino Delgado", "Intestino Grosso", "Fígado",
                "Vesícula Biliar", "Pâncreas", "Esófago"
            ],
            "Sistema Respiratório": [
                "Pulmões", "Brônquios", "Traqueia", "Laringe", "Diafragma"
            ],
            "Sistema Cardiovascular": [
                "Coração", "Artérias", "Veias", "Sistema Linfático"
            ],
            "Sistema Nervoso": [
                "Cérebro", "Medula Espinhal", "Sistema Nervoso Simpático",
                "Sistema Nervoso Parassimpático", "Plexos Nervosos"
            ],
            "Sistema Endócrino": [
                "Hipófise", "Tiroide", "Suprarrenais", "Pâncreas Endócrino",
                "Gónadas", "Paratiroide", "Timo", "Pineal"
            ]
        }
    
    def get_all_items(self) -> List[ResonanceItem]:
        """Retorna todos os itens da base de dados como objetos ResonanceItem"""
        items = []
        
        for category, subcategories in self.categories.items():
            for subcategory, item_names in subcategories.items():
                for item_name in item_names:
                    item = ResonanceItem(
                        name=item_name,
                        category=category,
                        subcategory=subcategory,
                        description=f"{item_name} do grupo {subcategory}"
                    )
                    items.append(item)
        
        return items
    
    def get_categories(self) -> Dict[str, Dict[str, List[str]]]:
        """Retorna estrutura completa de categorias"""
        return self.categories
    
    def search_items(self, query: str) -> List[ResonanceItem]:
        """Procura itens por nome ou categoria"""
        query = query.lower()
        items = []
        
        for category, subcategories in self.categories.items():
            if query in category.lower():
                # Adicionar todos os itens da categoria
                for subcategory, item_names in subcategories.items():
                    for item_name in item_names:
                        items.append(ResonanceItem(
                            name=item_name,
                            category=category,
                            subcategory=subcategory
                        ))
            else:
                # Procurar em subcategorias e itens
                for subcategory, item_names in subcategories.items():
                    if query in subcategory.lower():
                        for item_name in item_names:
                            items.append(ResonanceItem(
                                name=item_name,
                                category=category,
                                subcategory=subcategory
                            ))
                    else:
                        for item_name in item_names:
                            if query in item_name.lower():
                                items.append(ResonanceItem(
                                    name=item_name,
                                    category=category,
                                    subcategory=subcategory
                                ))
        
        return items

# Instância global da base de dados
resonance_database = ResonanceDatabase()
