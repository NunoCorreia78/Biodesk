"""
Biodesk - Módulo Ficha Paciente Refatorizado
============================================

Este módulo contém a versão refatorizada da ficha do paciente,
dividida em componentes especializados para melhor performance e manutenção.

Estrutura:
- main_window.py: Janela principal e coordenação
- dados_pessoais.py: Gestão de dados pessoais ✅ IMPLEMENTADO
- historico_clinico.py: Histórico clínico e anotações
- templates_manager.py: Sistema de templates e prescrições  
- comunicacao_manager.py: Centro de comunicação e emails
- iris_integration.py: Integração com análise de íris
- signature_widget.py: Assinaturas digitais

Performance Esperada:
- Startup: 75% mais rápido (~2-3s vs 8-12s)
- Memory: 47% menos uso (~80MB vs 150MB)
- Load Patient: 85% mais rápido (~0.5s vs 3-5s)
"""

# Importar a classe principal do arquivo ficha_paciente.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Resolver conflito de nomes: importar do arquivo .py, não do diretório
import importlib.util
spec = importlib.util.spec_from_file_location("ficha_paciente_module", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "ficha_paciente.py"))
ficha_paciente_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ficha_paciente_module)

# Expor a classe principal
FichaPaciente = ficha_paciente_module.FichaPaciente

__all__ = ['FichaPaciente']

# Importações principais
from .dados_pessoais import DadosPessoaisWidget
from .historico_clinico import HistoricoClinicoWidget
from .templates_manager import TemplatesManagerWidget
from .comunicacao_manager import ComunicacaoManagerWidget

# Importação principal para compatibilidade (quando implementado)
# from .main_window import FichaPacienteRefatorizada as FichaPaciente

__all__ = ['DadosPessoaisWidget', 'HistoricoClinicoWidget', 'TemplatesManagerWidget', 'ComunicacaoManagerWidget']  # 'FichaPaciente' quando implementado
__version__ = '2.0.0'
