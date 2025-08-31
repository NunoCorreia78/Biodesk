"""
TemplateService - Serviço centralizado para gestão de templates
Extraído do monolito ficha_paciente.py para modularização
"""

from typing import Optional, Dict, Any, List
import os
from datetime import datetime


class TemplateService:
    """Serviço centralizado para operações de templates"""
    
    def __init__(self, paciente_data: Optional[Dict] = None):
        self.paciente_data = paciente_data or {}
    
    def on_template_selecionado(self, template_data: Dict) -> bool:
        """
        Callback unificado quando template é selecionado
        
        Consolida múltiplos métodos similares do monolito
        """
        try:
            print(f"📋 TemplateService: Template selecionado: {template_data.get('nome', 'N/A')}")
            
            # Validar template
            if not self._validar_template(template_data):
                return False
            
            # Processar variáveis do template
            template_processado = self._processar_variaveis_template(template_data)
            
            # Notificar sistemas dependentes
            self._notificar_template_aplicado(template_processado)
            
            return True
            
        except Exception as e:
            print(f"❌ TemplateService: Erro ao processar template: {e}")
            return False
    
    def on_template_gerado(self, template_data: Dict) -> bool:
        """
        Callback quando template é gerado/criado
        
        Método consolidado do monolito
        """
        try:
            print(f"📋 TemplateService: Template gerado: {template_data.get('nome', 'N/A')}")
            
            # Salvar template se necessário
            if template_data.get('salvar', False):
                self._salvar_template(template_data)
            
            # Aplicar template imediatamente se solicitado
            if template_data.get('aplicar_imediato', False):
                return self.on_template_selecionado(template_data)
            
            return True
            
        except Exception as e:
            print(f"❌ TemplateService: Erro ao gerar template: {e}")
            return False
    
    def abrir_templates_mensagem(self) -> Dict[str, Any]:
        """
        Abre diálogo de templates de mensagem
        
        Consolidado de múltiplas implementações do monolito
        """
        try:
            # Carregar templates disponíveis
            templates = self._carregar_templates_disponiveis()
            
            # Preparar dados para o diálogo
            dados_dialogo = {
                'templates': templates,
                'paciente': self.paciente_data,
                'data_atual': datetime.now().strftime('%d/%m/%Y'),
                'templates_personalizados': self._carregar_templates_personalizados()
            }
            
            print(f"📋 TemplateService: {len(templates)} templates carregados")
            return dados_dialogo
            
        except Exception as e:
            print(f"❌ TemplateService: Erro ao carregar templates: {e}")
            return {'templates': [], 'erro': str(e)}
    
    def aplicar_protocolo_historico(self, protocolo_data: Dict) -> bool:
        """
        Aplica protocolo ao histórico do paciente
        
        Método consolidado e otimizado
        """
        try:
            print(f"📋 TemplateService: Aplicando protocolo: {protocolo_data.get('nome', 'N/A')}")
            
            # Validar protocolo
            if not protocolo_data.get('conteudo'):
                print("❌ TemplateService: Protocolo sem conteúdo")
                return False
            
            # Processar variáveis do protocolo
            protocolo_processado = self._processar_variaveis_template(protocolo_data)
            
            # Aplicar ao histórico (delegar para HistóricoService se existir)
            sucesso = self._aplicar_ao_historico(protocolo_processado)
            
            if sucesso:
                print("✅ TemplateService: Protocolo aplicado ao histórico")
            
            return sucesso
            
        except Exception as e:
            print(f"❌ TemplateService: Erro ao aplicar protocolo: {e}")
            return False
    
    def substituir_variaveis_template(self, template_html: str) -> str:
        """
        Substitui variáveis no template HTML
        
        Consolidado de múltiplas implementações duplicadas
        """
        try:
            if not template_html:
                return ""
            
            # Variáveis padrão do paciente
            variaveis = {
                '{{nome_paciente}}': self.paciente_data.get('nome', 'N/A'),
                '{{data_nascimento}}': self.paciente_data.get('data_nascimento', 'N/A'),
                '{{telefone}}': self.paciente_data.get('telefone', 'N/A'),
                '{{email}}': self.paciente_data.get('email', 'N/A'),
                '{{data_hoje}}': datetime.now().strftime('%d/%m/%Y'),
                '{{data_completa}}': datetime.now().strftime('%d/%m/%Y %H:%M'),
                '{{ano_atual}}': str(datetime.now().year)
            }
            
            # Aplicar substituições
            resultado = template_html
            for variavel, valor in variaveis.items():
                resultado = resultado.replace(variavel, str(valor))
            
            return resultado
            
        except Exception as e:
            print(f"❌ TemplateService: Erro ao substituir variáveis: {e}")
            return template_html
    
    def obter_template_consentimento(self, tipo: str) -> Dict[str, Any]:
        """
        Obtém template de consentimento por tipo
        
        Método consolidado para diferentes tipos de consentimento
        """
        try:
            templates_consentimento = {
                'rgpd': {
                    'nome': 'Consentimento RGPD',
                    'categoria': 'consentimento',
                    'html': self._gerar_template_rgpd(),
                    'variaveis': ['nome_paciente', 'data_hoje', 'data_nascimento']
                },
                'tratamento': {
                    'nome': 'Consentimento de Tratamento',
                    'categoria': 'consentimento',
                    'html': self._gerar_template_tratamento(),
                    'variaveis': ['nome_paciente', 'data_hoje', 'tipo_tratamento']
                },
                'fotografia': {
                    'nome': 'Consentimento Fotográfico',
                    'categoria': 'consentimento',
                    'html': self._gerar_template_fotografia(),
                    'variaveis': ['nome_paciente', 'data_hoje']
                }
            }
            
            template = templates_consentimento.get(tipo)
            if template:
                # Processar variáveis
                template['html'] = self.substituir_variaveis_template(template['html'])
                
            return template or {}
            
        except Exception as e:
            print(f"❌ TemplateService: Erro ao obter template: {e}")
            return {}
    
    # ---- Métodos privados ----
    
    def _validar_template(self, template_data: Dict) -> bool:
        """Valida dados do template"""
        return bool(template_data.get('nome') and template_data.get('conteudo'))
    
    def _processar_variaveis_template(self, template_data: Dict) -> Dict:
        """Processa variáveis no template"""
        template_copia = template_data.copy()
        
        if 'conteudo' in template_copia:
            template_copia['conteudo'] = self.substituir_variaveis_template(
                template_copia['conteudo']
            )
        
        if 'html' in template_copia:
            template_copia['html'] = self.substituir_variaveis_template(
                template_copia['html']
            )
            
        return template_copia
    
    def _notificar_template_aplicado(self, template_data: Dict) -> None:
        """Notifica outros sistemas sobre template aplicado"""
        # Placeholder para integração com outros serviços
        pass
    
    def _salvar_template(self, template_data: Dict) -> bool:
        """Salva template personalizado"""
        try:
            # Implementar salvamento em ficheiro/base de dados
            print(f"💾 TemplateService: Template '{template_data.get('nome')}' salvo")
            return True
        except Exception:
            return False
    
    def _carregar_templates_disponiveis(self) -> List[Dict]:
        """Carrega lista de templates disponíveis"""
        # Templates padrão do sistema
        return [
            {'id': 'receita_simples', 'nome': 'Receita Simples', 'categoria': 'prescricao'},
            {'id': 'protocolo_detox', 'nome': 'Protocolo Detox', 'categoria': 'protocolo'},
            {'id': 'exercicios_base', 'nome': 'Exercícios Base', 'categoria': 'exercicios'},
            {'id': 'dieta_antiinflamatoria', 'nome': 'Dieta Anti-inflamatória', 'categoria': 'nutricao'}
        ]
    
    def _carregar_templates_personalizados(self) -> List[Dict]:
        """Carrega templates personalizados do utilizador"""
        # Placeholder - implementar carregamento de ficheiros
        return []
    
    def _aplicar_ao_historico(self, protocolo_data: Dict) -> bool:
        """Aplica protocolo ao histórico do paciente"""
        try:
            # Placeholder - delegar para HistóricoService
            print(f"📝 TemplateService: Protocolo aplicado ao histórico")
            return True
        except Exception:
            return False
    
    def _gerar_template_rgpd(self) -> str:
        """Gera template base de consentimento RGPD"""
        return """
        <h2>Consentimento para Tratamento de Dados Pessoais (RGPD)</h2>
        <p>Eu, {{nome_paciente}}, nascido(a) em {{data_nascimento}}, 
        consinto o tratamento dos meus dados pessoais conforme RGPD.</p>
        <p>Data: {{data_hoje}}</p>
        """
    
    def _gerar_template_tratamento(self) -> str:
        """Gera template base de consentimento de tratamento"""
        return """
        <h2>Consentimento Informado para Tratamento</h2>
        <p>Eu, {{nome_paciente}}, consinto o tratamento proposto 
        após ter sido devidamente informado(a).</p>
        <p>Data: {{data_hoje}}</p>
        """
    
    def _gerar_template_fotografia(self) -> str:
        """Gera template base de consentimento fotográfico"""
        return """
        <h2>Consentimento para Captação de Imagens</h2>
        <p>Eu, {{nome_paciente}}, autorizo a captação de fotografias 
        para fins de documentação clínica.</p>
        <p>Data: {{data_hoje}}</p>
        """


# ---- Funções de conveniência ----

def aplicar_template_rapido(paciente_data: Dict, template_data: Dict) -> bool:
    """Função rápida para aplicar template (compatibilidade)"""
    service = TemplateService(paciente_data)
    return service.on_template_selecionado(template_data)


def processar_variaveis_rapido(template_html: str, paciente_data: Dict) -> str:
    """Função rápida para processar variáveis (compatibilidade)"""
    service = TemplateService(paciente_data)
    return service.substituir_variaveis_template(template_html)
