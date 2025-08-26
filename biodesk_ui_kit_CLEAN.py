"""
🚨 ARQUIVO OBSOLETO - NÃO USAR!
===============================

⚠️ DEPRECATED: Este arquivo está OBSOLETO desde BiodeskStyles v2.0
✅ MIGRAR PARA: biodesk_styles.py

Este arquivo só existe para compatibilidade de emergência.
TODOS os novos desenvolvimentos devem usar BiodeskStyles v2.0
"""

# 🔄 REDIRECIONAMENTO AUTOMÁTICO PARA O NOVO SISTEMA
from biodesk_styles import BiodeskStyles, ButtonType

class BiodeskUIKit:
    """OBSOLETO: Usar BiodeskStyles v2.0"""
    
    @classmethod
    def apply_universal_button_style(cls, button):
        """OBSOLETO: Redireciona para BiodeskStyles"""
        BiodeskStyles.apply_to_existing_button(button, ButtonType.DEFAULT)
    
    @classmethod  
    def create_primary_button(cls, text: str, icon=None):
        """OBSOLETO: Redireciona para BiodeskStyles"""
        return BiodeskStyles.create_button(text, ButtonType.DEFAULT)
    
    @classmethod
    def create_secondary_button(cls, text: str, icon=None):
        """OBSOLETO: Redireciona para BiodeskStyles"""
        return BiodeskStyles.create_button(text, ButtonType.NAVIGATION)
    
    @classmethod
    def create_success_button(cls, text: str, icon=None):
        """OBSOLETO: Redireciona para BiodeskStyles"""
        return BiodeskStyles.create_button(text, ButtonType.SAVE)
    
    @classmethod
    def create_danger_button(cls, text: str, icon=None):
        """OBSOLETO: Redireciona para BiodeskStyles"""
        return BiodeskStyles.create_button(text, ButtonType.DELETE)
    
    @classmethod
    def create_neutral_button(cls, text: str, icon=None, hover_color=None):
        """OBSOLETO: Redireciona para BiodeskStyles"""
        return BiodeskStyles.create_button(text, ButtonType.DEFAULT)
    
    # 🎨 CORES OBSOLETAS - MANTIDAS SÓ PARA COMPATIBILIDADE
    COLORS = {
        'primary': '#007bff', 'success': '#28a745', 'warning': '#ffc107',
        'danger': '#dc3545', 'light': '#f8f9fa', 'dark': '#343a40',
        'white': '#ffffff', 'border': '#dee2e6', 'border_light': '#e9ecef',
        'text': '#212529', 'text_muted': '#6c757d', 'background': '#ffffff',
        'background_light': '#f8f9fa'
    }
    
    # 📝 FONTES OBSOLETAS  
    FONTS = {
        'family': "'Segoe UI', system-ui, sans-serif",
        'size_normal': '14px'
    }
