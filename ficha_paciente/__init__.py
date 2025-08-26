"""
📋 FICHA PACIENTE - MÓDULO PRINCIPAL
===================================

Este módulo centraliza todas as funcionalidades relacionadas com a ficha de paciente.
Mantém a estrutura original de duas abas principais:

ESTRUTURA ORIGINAL:
📋 DOCUMENTAÇÃO CLÍNICA:
   - 👤 Dados Pessoais
   - 🩺 Declaração de Saúde  
   - 📁 Gestão de Documentos

🩺 ÁREA CLÍNICA:
   - 📝 Histórico Clínico
   - 👁️ Análise de Íris
   - 📋 Modelos de Prescrição (Templates)
   - 📧 Email
   - ⚡ Terapia Quântica (futuro)
"""

# Importar a classe principal do arquivo ficha_paciente.py (ESTRUTURA ORIGINAL)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Resolver conflito de nomes: importar do arquivo .py, não do diretório
import importlib.util
spec = importlib.util.spec_from_file_location("ficha_paciente_module", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "ficha_paciente.py"))
ficha_paciente_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ficha_paciente_module)

# Expor a classe principal ORIGINAL
FichaPaciente = ficha_paciente_module.FichaPaciente

__all__ = ['FichaPaciente']

# Importações dos widgets especializados (mantidas)
from .dados_pessoais import DadosPessoaisWidget
from .historico_clinico import HistoricoClinicoWidget
from .templates_manager import TemplatesManagerWidget
from .comunicacao_manager import ComunicacaoManagerWidget

# Importação principal para compatibilidade (quando implementado)
try:
    from .gestao_documentos import GestaoDocumentosWidget
    __all__.append('GestaoDocumentosWidget')
except ImportError:
    pass

try:
    from .declaracao_saude import DeclaracaoSaudeWidget
    __all__.append('DeclaracaoSaudeWidget')
except ImportError:
    pass

try:
    from .pesquisa_pacientes import PesquisaPacientesManager
    __all__.append('PesquisaPacientesManager')
except ImportError:
    pass

# Atualizar exportações
__all__.extend([
    'DadosPessoaisWidget',
    'HistoricoClinicoWidget', 
    'TemplatesManagerWidget',
    'ComunicacaoManagerWidget'
])

# MANTER ButtonManager disponível para uso futuro (sem interferir na estrutura)
try:
    from .core.button_manager import ButtonManager
    __all__.append('ButtonManager')
except ImportError:
    # ButtonManager é opcional
    pass

__version__ = '2.0.1'  # Estrutura original restaurada
