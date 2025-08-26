# Dialogs module for ficha_paciente
from .followup_dialog import FollowUpDialog
from .template_dialog import TemplateDialog
from .signature_dialog import SignatureDialog
from .import_pdf_dialog import ImportPdfDialog

__all__ = ['FollowUpDialog', 'TemplateDialog', 'SignatureDialog', 'ImportPdfDialog']
