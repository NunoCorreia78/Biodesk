"""
Protocolos Terapêuticos Predefinidos
═══════════════════════════════════════════════════════════════════════

Biblioteca de protocolos terapêuticos baseados em literatura científica
e práticas estabelecidas de medicina frequencial.
"""

from typing import Dict, List
from frequency_generator import FrequencyStep
from therapy_session import TherapyProtocol
import uuid
from datetime import datetime

class TherapyProtocols:
    """
    Biblioteca de protocolos terapêuticos predefinidos
    """
    
    @staticmethod
    def get_basic_protocols() -> List[TherapyProtocol]:
        """Retorna protocolos básicos essenciais"""
        
        protocols = []
        
        # 1. Protocolo Schumann Básico
        schumann_steps = [
            FrequencyStep(7.83, 1.5, 0.0, 600, "Frequência Schumann - Ressonância Natural da Terra"),
            FrequencyStep(14.3, 1.5, 0.0, 300, "Primeiro harmónico Schumann"),
            FrequencyStep(20.8, 1.5, 0.0, 300, "Segundo harmónico Schumann")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Ressonância Schumann",
            description="Protocolo baseado na ressonância natural da Terra. Promove equilibrio e relaxamento profundo.",
            category="Básico",
            steps=schumann_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 2. Protocolo de Relaxamento
        relaxamento_steps = [
            FrequencyStep(0.5, 1.0, 0.0, 180, "Delta - Sono profundo"),
            FrequencyStep(2.0, 1.2, 0.0, 240, "Delta - Regeneração"),
            FrequencyStep(6.0, 1.5, 0.0, 300, "Theta - Relaxamento"),
            FrequencyStep(10.0, 1.8, 0.0, 300, "Alpha - Meditação"),
            FrequencyStep(7.83, 2.0, 0.0, 480, "Schumann - Estabilização")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Relaxamento Profundo",
            description="Sequência de frequências para relaxamento profundo e redução de stress.",
            category="Relaxamento",
            steps=relaxamento_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 3. Protocolo Energético
        energia_steps = [
            FrequencyStep(15.0, 2.0, 0.0, 240, "Beta baixo - Ativação mental"),
            FrequencyStep(20.0, 2.2, 0.0, 240, "Beta - Concentração"),
            FrequencyStep(35.0, 2.5, 0.0, 180, "Gamma baixo - Energia"),
            FrequencyStep(95.0, 2.8, 0.0, 240, "Frequência de vitalidade"),
            FrequencyStep(120.0, 3.0, 0.0, 180, "Frequência de energia"),
            FrequencyStep(40.0, 2.0, 0.0, 300, "Gamma - Integração")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Energia e Vitalidade",
            description="Protocolo para aumentar energia, vitalidade e clareza mental.",
            category="Energético",
            steps=energia_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 4. Protocolo Rife Clássico
        rife_steps = [
            FrequencyStep(20.0, 2.0, 0.0, 180, "Rife Base - Preparação"),
            FrequencyStep(727.0, 2.5, 0.0, 300, "Rife 727 - Purificação"),
            FrequencyStep(787.0, 2.5, 0.0, 300, "Rife 787 - Limpeza"),
            FrequencyStep(880.0, 2.8, 0.0, 300, "Rife 880 - Harmonização"),
            FrequencyStep(1500.0, 3.0, 0.0, 240, "Rife 1500 - Regeneração"),
            FrequencyStep(1550.0, 3.0, 0.0, 240, "Rife 1550 - Estabilização"),
            FrequencyStep(2127.0, 2.5, 0.0, 180, "Rife 2127 - Finalização")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Rife Clássico",
            description="Protocolo baseado nas frequências clássicas de Royal Raymond Rife.",
            category="Rife",
            steps=rife_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 5. Protocolo Solfeggio
        solfeggio_steps = [
            FrequencyStep(174.0, 1.8, 0.0, 240, "174Hz - Fundação, redução da dor"),
            FrequencyStep(285.0, 1.8, 0.0, 240, "285Hz - Regeneração de tecidos"),
            FrequencyStep(396.0, 2.0, 0.0, 300, "396Hz - Libertação do medo"),
            FrequencyStep(417.0, 2.0, 0.0, 300, "417Hz - Facilitação da mudança"),
            FrequencyStep(528.0, 2.2, 0.0, 360, "528Hz - Transformação e cura do DNA"),
            FrequencyStep(639.0, 2.0, 0.0, 300, "639Hz - Conexão e relacionamentos"),
            FrequencyStep(741.0, 2.0, 0.0, 240, "741Hz - Despertar da intuição"),
            FrequencyStep(852.0, 1.8, 0.0, 240, "852Hz - Ordem espiritual")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Frequências Solfeggio",
            description="Protocolo completo das frequências sagradas Solfeggio para cura holística.",
            category="Solfeggio",
            steps=solfeggio_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        return protocols
    
    @staticmethod
    def get_specialized_protocols() -> List[TherapyProtocol]:
        """Retorna protocolos especializados"""
        
        protocols = []
        
        # 1. Protocolo Anti-Stress
        stress_steps = [
            FrequencyStep(3.5, 1.5, 0.0, 300, "Delta profundo - Calma"),
            FrequencyStep(7.83, 2.0, 0.0, 420, "Schumann - Equilíbrio natural"),
            FrequencyStep(10.0, 2.2, 0.0, 360, "Alpha - Relaxamento mental"),
            FrequencyStep(432.0, 2.5, 0.0, 480, "432Hz - Frequência da natureza"),
            FrequencyStep(528.0, 2.8, 0.0, 360, "528Hz - Reparação celular"),
            FrequencyStep(40.0, 1.8, 0.0, 240, "Gamma - Integração final")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Anti-Stress Intensivo",
            description="Protocolo especializado para redução profunda do stress e ansiedade.",
            category="Especializado",
            steps=stress_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 2. Protocolo para Insónia
        insonia_steps = [
            FrequencyStep(0.5, 1.0, 0.0, 360, "Delta 0.5Hz - Indução do sono"),
            FrequencyStep(1.0, 1.2, 0.0, 420, "Delta 1Hz - Sono profundo"),
            FrequencyStep(2.0, 1.5, 0.0, 300, "Delta 2Hz - Regeneração"),
            FrequencyStep(3.5, 1.8, 0.0, 240, "Theta - Transição"),
            FrequencyStep(7.83, 2.0, 0.0, 480, "Schumann - Sincronização"),
            FrequencyStep(10.0, 1.5, 0.0, 300, "Alpha - Relaxamento final")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Indução do Sono",
            description="Protocolo específico para tratamento da insónia e melhoria da qualidade do sono.",
            category="Especializado",
            steps=insonia_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 3. Protocolo Digestivo
        digestivo_steps = [
            FrequencyStep(10.0, 1.8, 0.0, 240, "Alpha - Relaxamento visceral"),
            FrequencyStep(727.0, 2.5, 0.0, 300, "Rife 727 - Sistema digestivo"),
            FrequencyStep(787.0, 2.5, 0.0, 300, "Rife 787 - Purificação"),
            FrequencyStep(880.0, 2.8, 0.0, 360, "Rife 880 - Harmonização"),
            FrequencyStep(1550.0, 3.0, 0.0, 240, "Frequência intestinal"),
            FrequencyStep(528.0, 2.5, 0.0, 300, "528Hz - Regeneração celular")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Harmonização Digestiva",
            description="Protocolo para melhoramento da função digestiva e saúde intestinal.",
            category="Especializado",
            steps=digestivo_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 4. Protocolo Circulatório
        circulatorio_steps = [
            FrequencyStep(15.0, 2.0, 0.0, 240, "Beta - Ativação circulatória"),
            FrequencyStep(727.0, 2.5, 0.0, 300, "Rife - Sistema vascular"),
            FrequencyStep(787.0, 2.5, 0.0, 300, "Rife - Limpeza sanguínea"),
            FrequencyStep(880.0, 2.8, 0.0, 360, "Rife - Oxigenação"),
            FrequencyStep(1500.0, 3.0, 0.0, 240, "Frequência cardíaca"),
            FrequencyStep(2720.0, 2.5, 0.0, 180, "Circulação periférica")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Melhoria Circulatória",
            description="Protocolo para otimização da circulação sanguínea e saúde cardiovascular.",
            category="Especializado",
            steps=circulatorio_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        return protocols
    
    @staticmethod
    def get_quick_protocols() -> List[TherapyProtocol]:
        """Retorna protocolos rápidos (15-20 minutos)"""
        
        protocols = []
        
        # 1. Relaxamento Rápido
        quick_relax_steps = [
            FrequencyStep(7.83, 2.0, 0.0, 300, "Schumann - Equilíbrio"),
            FrequencyStep(10.0, 2.2, 0.0, 240, "Alpha - Relaxamento"),
            FrequencyStep(528.0, 2.5, 0.0, 360, "528Hz - Cura"),
            FrequencyStep(40.0, 2.0, 0.0, 180, "Gamma - Integração")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Relaxamento Expresso",
            description="Protocolo rápido para relaxamento e redução de stress em 18 minutos.",
            category="Rápido",
            steps=quick_relax_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 2. Energia Rápida
        quick_energy_steps = [
            FrequencyStep(20.0, 2.5, 0.0, 240, "Beta - Ativação"),
            FrequencyStep(95.0, 3.0, 0.0, 300, "Energia"),
            FrequencyStep(120.0, 3.2, 0.0, 240, "Vitalidade"),
            FrequencyStep(40.0, 2.5, 0.0, 180, "Gamma - Foco")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Energia Expresso",
            description="Protocolo rápido para aumento de energia e vitalidade em 16 minutos.",
            category="Rápido",
            steps=quick_energy_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        # 3. Foco Mental
        focus_steps = [
            FrequencyStep(13.0, 2.0, 0.0, 180, "SMR - Estabilização"),
            FrequencyStep(15.0, 2.2, 0.0, 240, "Beta baixo - Concentração"),
            FrequencyStep(20.0, 2.5, 0.0, 300, "Beta - Foco"),
            FrequencyStep(40.0, 2.8, 0.0, 240, "Gamma - Clareza mental"),
            FrequencyStep(10.0, 2.0, 0.0, 180, "Alpha - Integração")
        ]
        
        protocols.append(TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name="Foco Mental",
            description="Protocolo para melhoria da concentração e clareza mental em 19 minutos.",
            category="Rápido",
            steps=focus_steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=False
        ))
        
        return protocols
    
    @staticmethod
    def get_iris_based_frequencies() -> Dict[str, List[float]]:
        """
        Retorna mapeamento de condições iridológicas para frequências terapêuticas
        Baseado em literatura de medicina frequencial e iridologia
        """
        
        return {
            # Sistema nervoso
            "sistema_nervoso": [3.5, 7.83, 10.0, 40.0, 100.0],
            "stress_nervoso": [0.5, 2.0, 7.83, 10.0, 432.0],
            "ansiedade": [0.5, 1.2, 2.5, 6.3, 10.0, 528.0],
            "depressao": [0.5, 1.8, 10.0, 35.0, 7.83],
            
            # Sistema digestivo
            "digestao": [10.0, 727.0, 787.0, 880.0, 1550.0],
            "intestinos": [727.0, 787.0, 880.0, 1550.0, 2720.0],
            "figado": [727.0, 787.0, 880.0, 1550.0, 3176.0],
            "pancreas": [727.0, 787.0, 880.0, 1500.0, 1550.0],
            
            # Sistema circulatório
            "circulacao": [15.0, 727.0, 787.0, 880.0, 1500.0, 2720.0],
            "coracao": [727.0, 787.0, 880.0, 1500.0, 1862.0],
            "pressao_arterial": [10.0, 727.0, 787.0, 880.0, 1500.0],
            
            # Sistema respiratório
            "pulmoes": [727.0, 787.0, 880.0, 1234.0, 1550.0],
            "respiracao": [7.83, 10.0, 727.0, 787.0, 880.0],
            
            # Sistema reprodutor
            "reprodutor": [727.0, 787.0, 880.0, 1500.0, 1550.0],
            "hormonios": [727.0, 787.0, 880.0, 1500.0, 2127.0],
            
            # Sistema músculo-esquelético
            "musculos": [120.0, 240.0, 300.0, 727.0, 787.0, 880.0],
            "articulacoes": [727.0, 776.0, 787.0, 802.0, 880.0, 1500.0],
            "ossos": [120.0, 727.0, 787.0, 880.0, 1500.0],
            
            # Sistema imunitário
            "imunidade": [1500.0, 1550.0, 1862.0, 2170.0, 2720.0, 3176.0],
            "linfatico": [727.0, 787.0, 880.0, 1500.0, 2170.0],
            
            # Detoxificação
            "detox": [727.0, 787.0, 880.0, 1500.0, 1550.0, 10000.0],
            "purificacao": [727.0, 787.0, 880.0, 1550.0, 2127.0],
            
            # Energia e vitalidade
            "energia": [20.0, 35.0, 95.0, 120.0, 727.0, 787.0],
            "fadiga": [727.0, 776.0, 787.0, 802.0, 880.0, 1500.0],
            "vitalidade": [20.0, 95.0, 120.0, 528.0, 727.0, 787.0],
            
            # Equilíbrio geral
            "equilibrio": [7.83, 10.0, 40.0, 432.0, 528.0],
            "harmonizacao": [7.83, 432.0, 528.0, 639.0, 741.0],
            
            # Frequências específicas por órgão
            "tiróide": [727.0, 787.0, 880.0, 1500.0, 1550.0],
            "supra_renais": [727.0, 787.0, 880.0, 1500.0, 2127.0],
            "rins": [727.0, 787.0, 880.0, 1500.0, 1550.0],
            "bexiga": [727.0, 787.0, 880.0, 1550.0],
            
            # Condições específicas
            "inflamacao": [727.0, 787.0, 880.0, 1500.0, 1550.0],
            "dor": [95.0, 666.0, 727.0, 787.0, 880.0, 3000.0],
            "insonia": [0.5, 1.0, 2.0, 3.5, 7.83, 10.0],
            "concentracao": [13.0, 15.0, 20.0, 40.0, 100.0]
        }
    
    @staticmethod
    def create_iris_protocol(iris_conditions: List[str], patient_name: str) -> TherapyProtocol:
        """
        Cria protocolo personalizado baseado em condições identificadas na íris
        """
        frequency_map = TherapyProtocols.get_iris_based_frequencies()
        selected_frequencies = set()
        
        # Sempre incluir frequências base
        base_frequencies = [7.83, 528.0]  # Schumann + DNA repair
        selected_frequencies.update(base_frequencies)
        
        # Adicionar frequências específicas para cada condição
        for condition in iris_conditions:
            condition_lower = condition.lower().replace(" ", "_")
            
            # Procurar correspondências
            for key, freqs in frequency_map.items():
                if key in condition_lower or any(word in condition_lower for word in key.split("_")):
                    selected_frequencies.update(freqs[:3])  # Máximo 3 por condição
        
        # Converter para lista ordenada
        frequencies = sorted(list(selected_frequencies))
        
        # Limitar a 12 frequências para sessão razoável
        if len(frequencies) > 12:
            frequencies = frequencies[:12]
        
        # Criar passos do protocolo
        steps = []
        
        # Passo inicial de preparação
        steps.append(FrequencyStep(7.83, 1.5, 0.0, 300, "Preparação - Frequência Schumann"))
        
        # Passos principais
        for i, freq in enumerate(frequencies[1:], 1):  # Pular Schumann que já foi adicionada
            # Determinar amplitude baseada na frequência
            if freq < 50:
                amplitude = 1.8  # Frequências baixas
            elif freq < 500:
                amplitude = 2.2  # Frequências médias
            else:
                amplitude = 2.8  # Frequências altas
            
            # Duração variada
            duration = 240 if i % 2 == 0 else 300
            
            steps.append(FrequencyStep(
                freq, amplitude, 0.0, duration,
                f"Terapêutica {freq}Hz - Passo {i}"
            ))
        
        # Passo final de integração
        steps.append(FrequencyStep(40.0, 2.0, 0.0, 240, "Integração final - Gamma"))
        
        return TherapyProtocol(
            protocol_id=str(uuid.uuid4()),
            name=f"Protocolo Íris - {patient_name}",
            description=f"Protocolo personalizado baseado na análise iridológica de {patient_name}. "
                       f"Inclui {len(frequencies)} frequências específicas para as condições identificadas.",
            category="Íris Personalizado",
            steps=steps,
            created_by="Sistema Biodesk",
            created_at=datetime.now(),
            iris_based=True,
            iris_data={"conditions": iris_conditions, "frequencies_used": frequencies}
        )
    
    @staticmethod
    def get_frequencies_for_condition(condition: str) -> List[float]:
        """
        Mapeia uma condição específica para frequências terapêuticas
        
        Args:
            condition: Nome da condição médica ou sintoma
            
        Returns:
            Lista de frequências em Hz apropriadas para a condição
        """
        
        # Dicionário de mapeamento condições -> frequências
        condition_frequency_map = {
            # Sistema Nervoso
            "Ansiedade": [7.83, 10.0, 12.0, 432.0],
            "Depressão": [7.83, 10.0, 40.0, 528.0],
            "Stress": [7.83, 8.0, 10.0, 396.0],
            "Insónia": [0.5, 2.0, 6.0, 7.83],
            "Distúrbios do sono": [0.5, 2.0, 6.0, 7.83],
            "Cefaleia": [9.4, 10.0, 40.0, 110.0],
            "Enxaqueca": [9.4, 10.0, 40.0, 110.0],
            "Fadiga mental": [12.0, 15.0, 40.0, 70.0],
            "Déficit de atenção": [12.0, 15.0, 20.0, 40.0],
            
            # Sistema Digestivo
            "Dispepsia": [20.0, 465.0, 727.0, 787.0],
            "Má digestão": [20.0, 465.0, 727.0, 787.0],
            "Refluxo gastroesofágico": [20.0, 465.0, 727.0],
            "Azia": [20.0, 465.0, 727.0],
            "Obstipação": [20.0, 440.0, 880.0],
            "Prisão de ventre": [20.0, 440.0, 880.0],
            "Diarreia": [20.0, 727.0, 787.0, 880.0],
            "Síndrome do intestino irritável": [20.0, 440.0, 727.0, 880.0],
            "Náuseas": [20.0, 465.0, 727.0],
            "Flatulência": [20.0, 440.0, 727.0],
            "Gases": [20.0, 440.0, 727.0],
            
            # Sistema Respiratório
            "Asma": [7.7, 787.0, 880.0, 2720.0],
            "Bronquite": [20.0, 727.0, 880.0, 987.0],
            "Tosse": [727.0, 880.0, 974.0, 1550.0],
            "Sinusite": [20.0, 440.0, 727.0, 880.0],
            "Rinite alérgica": [20.0, 440.0, 727.0],
            "Congestão nasal": [20.0, 440.0, 727.0],
            
            # Sistema Circulatório
            "Hipertensão arterial": [7.83, 10.0, 20.0, 727.0],
            "Hipertensão": [7.83, 10.0, 20.0, 727.0],
            "Má circulação": [20.0, 727.0, 787.0, 880.0],
            "Arritmias": [7.83, 10.0, 80.0, 160.0],
            "Palpitações": [7.83, 10.0, 80.0, 160.0],
            "Varizes": [20.0, 727.0, 787.0],
            "Hipercolesterolemia": [20.0, 727.0, 880.0],
            "Colesterol alto": [20.0, 727.0, 880.0],
            
            # Sistema Musculoesquelético
            "Artrite": [9.4, 20.0, 727.0, 787.0],
            "Artrose": [9.4, 20.0, 727.0, 787.0],
            "Artralgia": [9.4, 20.0, 727.0, 787.0],
            "Dores articulares": [9.4, 20.0, 727.0, 787.0],
            "Fibromialgia": [7.83, 9.4, 20.0, 528.0],
            "Mialgia": [20.0, 727.0, 787.0, 880.0],
            "Dores musculares": [20.0, 727.0, 787.0, 880.0],
            "Tendinite": [9.4, 20.0, 727.0, 787.0],
            "Bursite": [9.4, 20.0, 727.0, 787.0],
            "Dores nas costas": [9.4, 20.0, 727.0, 787.0],
            
            # Sistema Reprodutor
            "Distúrbios menstruais": [7.83, 20.0, 465.0],
            "Irregularidades menstruais": [7.83, 20.0, 465.0],
            "Dismenorreia": [7.83, 20.0, 465.0],
            "Dores menstruais": [7.83, 20.0, 465.0],
            "Síndrome pré-menstrual": [7.83, 20.0, 465.0],
            "TPM": [7.83, 20.0, 465.0],
            "Sintomas da menopausa": [7.83, 20.0, 465.0, 528.0],
            "Menopausa": [7.83, 20.0, 465.0, 528.0],
            "Problemas de próstata": [20.0, 727.0, 787.0],
            
            # Sistema Endócrino
            "Diabetes": [20.0, 727.0, 787.0, 880.0],
            "Distúrbios da tireoide": [20.0, 727.0, 787.0],
            "Desequilíbrios hormonais": [7.83, 20.0, 465.0, 528.0],
            
            # Sistema Imunitário
            "Alergias": [20.0, 727.0, 787.0, 880.0],
            "Doenças auto-imunes": [20.0, 528.0, 727.0, 787.0],
            "Imunodeficiência": [20.0, 528.0, 727.0, 880.0],
            
            # Frequências especiais
            "Bem-estar geral": [7.83, 528.0, 396.0, 417.0],
            "Harmonização energética": [528.0, 639.0, 741.0, 852.0],
            "Regeneração celular": [10.0, 20.0, 528.0, 2720.0],
            "Protocolo pré-definido selecionado": [7.83, 528.0, 396.0, 417.0, 639.0, 741.0, 852.0]
        }
        
        # Normalizar o nome da condição (lowercase, sem acentos)
        condition_lower = condition.lower()
        
        # Buscar correspondência exata primeiro
        for mapped_condition, frequencies in condition_frequency_map.items():
            if mapped_condition.lower() == condition_lower:
                return frequencies
        
        # Buscar correspondência parcial
        for mapped_condition, frequencies in condition_frequency_map.items():
            if condition_lower in mapped_condition.lower() or mapped_condition.lower() in condition_lower:
                return frequencies
        
        # Se não encontrou correspondência, retornar frequências de bem-estar geral
        return [7.83, 528.0, 396.0, 417.0]
