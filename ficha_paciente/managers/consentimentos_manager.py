# -*- coding: utf-8 -*-
"""
ConsentimentosManager - Sistema Avançado de Gestão de Consentimentos
==================================================================

Responsável por toda a lógica de:
- Geração de PDFs de consentimento
- Templates de consentimento  
- Histórico de consentimentos
- Validação de consentimentos
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
import json
from datetime import datetime

from ..services.pdf_service_simple import get_pdf_service
from ..services.template_service import TemplateService

class ConsentimentosManager(QObject):
    """Gerenciador centralizado de consentimentos"""
    
    # Sinais
    consentimento_gerado = pyqtSignal(str, str)  # tipo, caminho_arquivo
    consentimento_erro = pyqtSignal(str)  # mensagem_erro
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.template_service = TemplateService()
        self.pdf_service = get_pdf_service()
        
        # Cache de templates
        self._templates_cache = {}
        
    def gerar_consentimento_simples(self, paciente_id, tipo_consentimento="geral"):
        """Gera consentimento simples usando serviços modulares"""
        try:
            # Obter dados do paciente
            paciente = self.db_manager.obter_paciente(paciente_id)
            if not paciente:
                self.consentimento_erro.emit("Paciente não encontrado")
                return None
            
            # Gerar usando PDF service
            template_data = {
                'nome': paciente.get('nome', ''),
                'data_nascimento': paciente.get('data_nascimento', ''),
                'tipo': tipo_consentimento,
                'data_atual': datetime.now().strftime('%d/%m/%Y')
            }
            
            pdf_path = self.pdf_service.gerar_consentimento_simples(
                paciente_id, template_data
            )
            
            if pdf_path:
                self.consentimento_gerado.emit(tipo_consentimento, pdf_path)
                return pdf_path
            else:
                self.consentimento_erro.emit("Erro na geração do PDF")
                return None
                
        except Exception as e:
            self.consentimento_erro.emit(f"Erro: {str(e)}")
            return None
    
    def gerar_consentimento_historico(self, paciente_id, historico_data):
        """Gera consentimento com histórico usando serviços modulares"""
        try:
            # Usar template service para processar dados
            template_data = self.template_service.processar_dados_historico(
                paciente_id, historico_data
            )
            
            # Gerar PDF
            pdf_path = self.pdf_service.gerar_consentimento_historico(
                paciente_id, template_data
            )
            
            if pdf_path:
                self.consentimento_gerado.emit("historico", pdf_path)
                return pdf_path
            else:
                self.consentimento_erro.emit("Erro na geração do PDF com histórico")
                return None
                
        except Exception as e:
            self.consentimento_erro.emit(f"Erro no histórico: {str(e)}")
            return None
    
    def obter_templates_disponiveis(self):
        """Retorna lista de templates de consentimento disponíveis"""
        return self.template_service.listar_templates_consentimento()
    
    def validar_consentimento(self, dados_consentimento):
        """Valida dados do consentimento antes da geração"""
        erros = []
        
        required_fields = ['nome', 'data_nascimento']
        for field in required_fields:
            if not dados_consentimento.get(field):
                erros.append(f"Campo obrigatório: {field}")
        
        return len(erros) == 0, erros
    
    def obter_historico_consentimentos(self, paciente_id):
        """Obtém histórico de consentimentos do paciente"""
        try:
            # Implementar busca no banco de dados
            historico = self.db_manager.obter_historico_consentimentos(paciente_id)
            return historico or []
        except Exception as e:
            print(f"Erro ao obter histórico: {e}")
            return []

# Factory function para fácil integração
def criar_consentimentos_manager(db_manager, parent=None):
    """Factory function para criar ConsentimentosManager"""
    return ConsentimentosManager(db_manager, parent)
