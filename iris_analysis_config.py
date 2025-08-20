"""
Configuração para análise de íris - Constituições e Sinais Iridológicos
═══════════════════════════════════════════════════════════════════════

Este arquivo define as listas predefinidas de constituições e sinais
utilizados na análise iridológica, garantindo consistência nos dados.
"""

# ═══════════════ CONSTITUIÇÕES DA ÍRIS ═══════════════
CONSTITUICOES_IRIS = [
    "Não definida",  # Valor padrão
    "Linfática",
    "Hematogénea", 
    "Mista",
    "Fibras Diretas",
    "Fibras em Rede",
    "Fibras Onduladas"
]

# ═══════════════ SINAIS IRIDOLÓGICOS ═══════════════
SINAIS_IRIS = [
    # Estruturas anatómicas
    "Lacuna",
    "Cripta",
    "Defecto",
    
    # Padrões radiais  
    "Raio Solar",
    "Raio Parasimpático",
    "Furo de Agulha",
    
    # Anéis e círculos
    "Anel Nervoso",
    "Anel de Tensão",
    "Arco Senil",
    "Anel de Colesterol",
    
    # Pigmentações
    "Pigmento Tóxico", 
    "Pigmento Psora",
    "Pigmento Droga",
    "Mancha Hepática",
    
    # Alterações de densidade
    "Densidade Aumentada",
    "Densidade Diminuída",
    "Fibras Abertas",
    "Fibras Fechadas",
    
    # Colorações específicas
    "Halo Escuro",
    "Halo Claro", 
    "Coloração Amarelada",
    "Coloração Acastanhada",
    
    # Sinais topográficos específicos
    "Sinal no Coração",
    "Sinal no Fígado", 
    "Sinal nos Rins",
    "Sinal no Pulmão",
    "Sinal no Sistema Nervoso",
    "Sinal no Sistema Digestivo"
]

# ═══════════════ FUNÇÕES AUXILIARES ═══════════════

def get_constituicoes() -> list:
    """Retorna a lista de constituições disponíveis"""
    return CONSTITUICOES_IRIS.copy()

def get_sinais() -> list:
    """Retorna a lista de sinais disponíveis"""
    return SINAIS_IRIS.copy()

def validar_constituicao(constituicao: str) -> bool:
    """Valida se uma constituição está na lista predefinida"""
    return constituicao in CONSTITUICOES_IRIS

def validar_sinal(sinal: str) -> bool:
    """Valida se um sinal está na lista predefinida"""
    return sinal in SINAIS_IRIS

def formatar_sinais_para_bd(sinais: list) -> str:
    """Converte lista de sinais para string formatada para BD"""
    if not sinais:
        return ""
    # Filtrar apenas sinais válidos
    sinais_validos = [s for s in sinais if validar_sinal(s)]
    return ", ".join(sinais_validos)

def formatar_sinais_da_bd(sinais_str: str) -> list:
    """Converte string da BD de volta para lista de sinais"""
    if not sinais_str or sinais_str.strip() == "":
        return []
    return [s.strip() for s in sinais_str.split(",") if s.strip()]

def obter_descricao_constituicao(constituicao: str) -> str:
    """Retorna uma breve descrição da constituição"""
    descricoes = {
        "Linfática": "Íris clara, fibras finas e bem definidas. Tendência linfática.",
        "Hematogénea": "Íris escura, fibras densas. Tendência circulatória/hematogénea.", 
        "Mista": "Combinação de características linfáticas e hematogéneas.",
        "Fibras Diretas": "Fibras retilíneas bem organizadas.",
        "Fibras em Rede": "Fibras entrelaçadas formando padrão de rede.",
        "Fibras Onduladas": "Fibras com padrão ondulado ou serpenteante."
    }
    return descricoes.get(constituicao, "Constituição não classificada.")

def obter_descricao_sinal(sinal: str) -> str:
    """Retorna uma breve descrição do sinal iridológico"""
    descricoes = {
        "Lacuna": "Abertura ou cavidade nas fibras da íris",
        "Cripta": "Depressão profunda em formato de losango",
        "Defecto": "Área de fibras enfraquecidas ou ausentes",
        "Raio Solar": "Linha radiada do colar para a periferia",
        "Anel Nervoso": "Círculo concêntrico indicando tensão nervosa",
        "Pigmento Tóxico": "Acumulação de toxinas representada por pigmentação"
    }
    return descricoes.get(sinal, "Sinal iridológico identificado.")

# ═══════════════ CLASSE PRINCIPAL ═══════════════

class IrisAnalysisConfig:
    """Classe centralizada para configuração da análise de íris"""
    
    @staticmethod
    def get_constituicoes():
        return get_constituicoes()
    
    @staticmethod  
    def get_sinais():
        return get_sinais()
    
    @staticmethod
    def validar_dados(constituicao: str = None, sinais: list = None) -> tuple:
        """
        Valida dados de análise de íris
        
        Returns:
            tuple: (bool_valido, lista_erros)
        """
        erros = []
        
        if constituicao and not validar_constituicao(constituicao):
            erros.append(f"Constituição inválida: {constituicao}")
            
        if sinais:
            sinais_invalidos = [s for s in sinais if not validar_sinal(s)]
            if sinais_invalidos:
                erros.append(f"Sinais inválidos: {', '.join(sinais_invalidos)}")
        
        return len(erros) == 0, erros
    
    @staticmethod
    def criar_resumo_analise(constituicao: str = None, sinais: list = None) -> str:
        """Cria um resumo textual da análise para histórico"""
        if not constituicao and not sinais:
            return "Análise de íris realizada (sem dados específicos)"
            
        partes = []
        
        if constituicao and constituicao != "Não definida":
            partes.append(f"Constituição: {constituicao}")
            
        if sinais:
            sinais_texto = ", ".join(sinais)
            partes.append(f"Sinais identificados: {sinais_texto}")
            
        if not partes:
            return "Análise de íris realizada"
            
        return f"Análise de Íris - {' | '.join(partes)}"
