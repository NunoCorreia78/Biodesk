"""
Módulo de Declarações de Saúde - Biodesk
═══════════════════════════════════════════════════════════════════════

Sistema completo para gestão de declarações de estado de saúde de pacientes,
incluindo formulários dinâmicos, validação e exportação para PDF.

Componentes principais:
- FormRenderer: Interface gráfica para preenchimento
- PDFExporter: Geração de documentos PDF profissionais  
- FormValidator: Validação de dados e contraindicações
- SignatureWidget: Captura de assinaturas digitais
"""

from .renderer import (
    HealthDeclarationRenderer,
    FieldRenderer,
    FormValidator,
    SignatureWidget,
    RatingWidget
)

from .export_pdf import (
    HealthDeclarationPDFExporter,
    PDFGenerator,
    QtPrintGenerator,
    SignatureImage
)

__version__ = "1.0.0"
__author__ = "Biodesk Development Team"

__all__ = [
    # Renderização de formulários
    'HealthDeclarationRenderer',
    'FieldRenderer', 
    'FormValidator',
    'SignatureWidget',
    'RatingWidget',
    
    # Exportação PDF
    'HealthDeclarationPDFExporter',
    'PDFGenerator',
    'QtPrintGenerator', 
    'SignatureImage'
]


def create_health_declaration_system(form_spec_path):
    """
    Factory function para criar sistema completo de declarações
    
    Args:
        form_spec_path: Caminho para arquivo de especificação do formulário
        
    Returns:
        Tuple (renderer, exporter) com componentes configurados
    """
    renderer = HealthDeclarationRenderer(form_spec_path)
    exporter = HealthDeclarationPDFExporter()
    
    return renderer, exporter


# Configurações padrão
DEFAULT_FORM_SPEC = "form_spec.json"
DEFAULT_OUTPUT_DIR = "generated_documents"
DEFAULT_SIGNATURE_SIZE = (400, 150)

# Metadados do módulo
MODULE_INFO = {
    "name": "health_declarations",
    "version": __version__,
    "description": "Sistema de declarações de saúde com formulários dinâmicos e PDF",
    "dependencies": [
        "PyQt6>=6.0.0",
        "reportlab>=3.6.0"  # Opcional
    ],
    "author": __author__
}
