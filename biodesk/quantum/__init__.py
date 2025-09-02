"""
Módulo de Terapia Quântica e Análise de Ressonância
═══════════════════════════════════════════════════════════════════════

Módulo completo para:
- Terapia quântica informacional
- Análise de ressonância estilo CoRe
- Geração de protocolos terapêuticos inteligentes
- Interface de balanceamento e execução
- Sistema de relatórios e documentação
"""

# FASE 2: Sistema de Ressonância 
from .resonance_analysis import (
    ResonanceAnalyzer,
    ResonanceDatabase, 
    ResonanceItem,
    ResonanceField,
    RESONANCE_FIELDS,
    resonance_database
)

from .resonance_interface import (
    ResonanceAnalysisWidget,
    ResonanceControlPanel,
    CategoryTreeWidget,
    ResonanceResultsTable
)

# FASE 3: Sistema de Protocolos
from .protocol_generator import (
    ProtocolGenerator,
    TherapyProtocol,
    ProtocolStep,
    ProtocolType,
    FrequencyMapper,
    protocol_generator
)

# FASE 4: Interface de Balanceamento
from .balancing_interface import (
    BalancingInterface,
    ProtocolCreationWidget,
    ProtocolExecutionWidget
)

# FASE 5: Sistema de Relatórios
from .reports_system import (
    ReportsInterface,
    DocumentationWidget,
    ReportGenerator,
    SessionData
)

__all__ = [
    # Fase 2: Análise de Ressonância
    'ResonanceAnalyzer',
    'ResonanceDatabase',
    'ResonanceItem', 
    'ResonanceField',
    'RESONANCE_FIELDS',
    'resonance_database',
    'ResonanceAnalysisWidget',
    'ResonanceControlPanel', 
    'CategoryTreeWidget',
    'ResonanceResultsTable',
    
    # Fase 3: Protocolos Inteligentes
    'ProtocolGenerator',
    'TherapyProtocol',
    'ProtocolStep',
    'ProtocolType',
    'FrequencyMapper',
    'protocol_generator',
    
    # Fase 4: Interface de Balanceamento
    'BalancingInterface',
    'ProtocolCreationWidget',
    'ProtocolExecutionWidget',
    
    # Fase 5: Sistema de Relatórios
    'ReportsInterface',
    'DocumentationWidget',
    'ReportGenerator',
    'SessionData'
]

__version__ = "2.0.0 - Sistema Completo (Fases 2-5)"
__author__ = "Biodesk Quantum Analysis System"
