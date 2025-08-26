"""
🎛️ BUTTON MANAGER CENTRALIZADO - BIODESK v2.0
=======================================

Sistema ATUALIZADO para usar BiodeskStyles.
Centraliza TODOS os botões da aplicação em um só lugar.
Elimina duplicação de código e garante estilos uniformes.

Autor: Biodesk Team
Data: 26/08/2025 - ATUALIZADO para BiodeskStyles v2.0
"""

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from typing import Optional, Callable, Any
import sys
import os

# Importar BiodeskStyles
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from biodesk_styles import BiodeskStyles, ButtonType
    BIODESK_STYLES_AVAILABLE = True
    print("✅ ButtonManager usando BiodeskStyles v2.0")
except ImportError:
    print("⚠️ BiodeskStyles não disponível, usando sistema legado")
    from biodesk_ui_kit import BiodeskUIKit
    BIODESK_STYLES_AVAILABLE = False

class ButtonManager:
    """
    Manager centralizado para todos os botões da aplicação.
    ATUALIZADO para usar BiodeskStyles v2.0
    """
    
    @staticmethod
    def create_button(text: str, button_type: Optional[str] = None, icon: Optional[str] = None, 
                     callback: Optional[Callable] = None, tooltip: Optional[str] = None) -> QPushButton:
        """
        Cria botão usando BiodeskStyles ou sistema legado
        
        Args:
            text: Texto do botão
            button_type: Tipo do botão ('save', 'delete', 'draft', etc.)
            icon: Caminho para ícone opcional
            callback: Função callback opcional
            tooltip: Tooltip opcional
        
        Returns:
            QPushButton configurado
        """
        
        if BIODESK_STYLES_AVAILABLE:
            # Usar novo sistema BiodeskStyles
            button_type_enum = None
            if button_type:
                type_mapping = {
                    'save': ButtonType.SAVE,
                    'delete': ButtonType.DELETE,
                    'draft': ButtonType.DRAFT,
                    'navigation': ButtonType.NAVIGATION,
                    'update': ButtonType.UPDATE,
                    'tool': ButtonType.TOOL,
                    'dialog': ButtonType.DIALOG,
                    'primary': ButtonType.SAVE,  # Compatibilidade
                    'secondary': ButtonType.DEFAULT,  # Compatibilidade
                    'action': ButtonType.SAVE,  # Compatibilidade
                    'small': ButtonType.DEFAULT  # Compatibilidade
                }
                button_type_enum = type_mapping.get(button_type, ButtonType.DEFAULT)
            
            # Converter ícone se necessário
            icon_obj = None
            if icon:
                if isinstance(icon, str):
                    icon_obj = QIcon(icon)
                else:
                    icon_obj = icon
            
            button = BiodeskStyles.create_button(text, button_type_enum, icon_obj)
            
        else:
            # Sistema legado como fallback
            button = QPushButton(text)
            ButtonManager._apply_legacy_style(button, button_type or 'default')
            
            if icon:
                if isinstance(icon, str):
                    button.setIcon(QIcon(icon))
                else:
                    button.setIcon(icon)
        
        # Aplicar callback e tooltip
        if callback:
            button.clicked.connect(callback)
        
        if tooltip:
            button.setToolTip(tooltip)
        
        return button

    @staticmethod
    def create_button(
        text: str,
        button_type: str = 'primary',
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        enabled: bool = True,
        parent: Optional[QWidget] = None
    ) -> QPushButton:
        """
        Cria um botão com configurações padronizadas.
        
        Args:
            text: Texto do botão
            button_type: Tipo do botão ('primary', 'secondary', 'action', 'small')
            icon: Ícone do botão (emoji ou caminho)
            tooltip: Tooltip do botão
            enabled: Se o botão está habilitado
            parent: Widget pai
            
        Returns:
            QPushButton configurado
        """
        button = QPushButton(text, parent)
        
        # Aplica configuração do tipo
        config = ButtonManager.BUTTON_CONFIGS.get(button_type, ButtonManager.BUTTON_CONFIGS['primary'])
        
        # Configura propriedades básicas
        button.setMinimumHeight(config['min_height'])
        button.setEnabled(enabled)
        
        # Configura fonte
        font = button.font()
        font.setPointSize(config['font_size'])
        if config['font_weight'] == 'bold':
            font.setBold(True)
        button.setFont(font)
        
        # Configura tooltip
        if tooltip:
            button.setToolTip(tooltip)
        
        # Aplica estilo através do BiodeskUIKit
        BiodeskUIKit.apply_universal_button_style(button)
        
        return button
    
    @staticmethod
    def create_action_button(
        text: str,
        action: Callable,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        button_type: str = 'action',
        parent: Optional[QWidget] = None
    ) -> QPushButton:
        """
        Cria um botão já conectado a uma ação.
        
        Args:
            text: Texto do botão
            action: Função a ser executada no clique
            icon: Ícone do botão
            tooltip: Tooltip do botão
            button_type: Tipo do botão
            parent: Widget pai
            
        Returns:
            QPushButton configurado e conectado
        """
        button = ButtonManager.create_button(
            text=text,
            button_type=button_type,
            icon=icon,
            tooltip=tooltip,
            parent=parent
        )
        
        # Conecta a ação
        button.clicked.connect(action)
        
        return button
    
    @staticmethod
    def create_ficha_toolbar_buttons(parent: QWidget) -> dict:
        """
        Cria todos os botões da toolbar da ficha de paciente.
        
        Args:
            parent: Widget pai dos botões
            
        Returns:
            Dict com todos os botões criados
        """
        buttons = {}
        
        # Botões principais da ficha
        buttons['followup'] = ButtonManager.create_button(
            text="📅 Follow-up",
            button_type='primary',
            tooltip="Configurar follow-ups automáticos",
            parent=parent
        )
        
        buttons['template'] = ButtonManager.create_button(
            text="📄 Templates",
            button_type='primary',
            tooltip="Gerenciar templates de documentos",
            parent=parent
        )
        
        buttons['lista_followups'] = ButtonManager.create_button(
            text="📋 Lista",
            button_type='secondary',
            tooltip="Ver lista de follow-ups agendados",
            parent=parent
        )
        
        buttons['enviar_email'] = ButtonManager.create_button(
            text="📧 Enviar",
            button_type='action',
            tooltip="Enviar email para o paciente",
            parent=parent
        )
        
        buttons['config'] = ButtonManager.create_button(
            text="⚙️ Config",
            button_type='secondary',
            tooltip="Configurações da aplicação",
            parent=parent
        )
        
        buttons['terapia_quantica'] = ButtonManager.create_button(
            text="⚡ Terapia Quântica",
            button_type='action',
            tooltip="Abrir módulo de terapia quântica",
            parent=parent
        )
        
        return buttons
    
    @staticmethod
    def create_dialog_buttons(parent: QWidget) -> dict:
        """
        Cria botões padrão para dialogs.
        
        Args:
            parent: Widget pai dos botões
            
        Returns:
            Dict com botões padrão de dialog
        """
        buttons = {}
        
        buttons['ok'] = ButtonManager.create_button(
            text="✅ OK",
            button_type='primary',
            tooltip="Confirmar ação",
            parent=parent
        )
        
        buttons['cancelar'] = ButtonManager.create_button(
            text="❌ Cancelar",
            button_type='secondary',
            tooltip="Cancelar ação",
            parent=parent
        )
        
        buttons['aplicar'] = ButtonManager.create_button(
            text="🔄 Aplicar",
            button_type='action',
            tooltip="Aplicar mudanças",
            parent=parent
        )
        
        buttons['fechar'] = ButtonManager.create_button(
            text="🔙 Fechar",
            button_type='secondary',
            tooltip="Fechar janela",
            parent=parent
        )
        
        return buttons
    
    @staticmethod
    def create_email_buttons(parent: QWidget) -> dict:
        """
        Cria botões específicos para funcionalidades de email.
        
        Args:
            parent: Widget pai dos botões
            
        Returns:
            Dict com botões de email
        """
        buttons = {}
        
        buttons['enviar_email'] = ButtonManager.create_button(
            text="📧 Enviar Email",
            button_type='action',
            tooltip="Enviar email com templates",
            parent=parent
        )
        
        buttons['config_email'] = ButtonManager.create_button(
            text="⚙️ Config Email",
            button_type='secondary',
            tooltip="Configurar conta de email",
            parent=parent
        )
        
        buttons['preview_email'] = ButtonManager.create_button(
            text="👁️ Preview",
            button_type='secondary',
            tooltip="Visualizar email antes de enviar",
            parent=parent
        )
        
        return buttons
    
    @staticmethod
    def create_template_buttons(parent: QWidget) -> dict:
        """
        Cria botões específicos para templates.
        
        Args:
            parent: Widget pai dos botões
            
        Returns:
            Dict com botões de template
        """
        buttons = {}
        
        buttons['usar_template'] = ButtonManager.create_button(
            text="✨ Usar Template",
            button_type='primary',
            tooltip="Usar template selecionado",
            parent=parent
        )
        
        buttons['editar_template'] = ButtonManager.create_button(
            text="✏️ Editar",
            button_type='secondary',
            tooltip="Editar template",
            parent=parent
        )
        
        buttons['novo_template'] = ButtonManager.create_button(
            text="➕ Novo",
            button_type='action',
            tooltip="Criar novo template",
            parent=parent
        )
        
        return buttons
    
    @staticmethod
    def apply_style_to_existing_button(button: QPushButton, button_type: str = 'primary'):
        """
        Aplica estilo a um botão já existente.
        
        Args:
            button: Botão existente
            button_type: Tipo de estilo a aplicar
        """
        config = ButtonManager.BUTTON_CONFIGS.get(button_type, ButtonManager.BUTTON_CONFIGS['primary'])
        
        # Configura propriedades
        button.setMinimumHeight(config['min_height'])
        
        # Configura fonte
        font = button.font()
        font.setPointSize(config['font_size'])
        if config['font_weight'] == 'bold':
            font.setBold(True)
        button.setFont(font)
        
        # Aplica estilo
        BiodeskUIKit.apply_universal_button_style(button)

# Classe de conveniência para criação rápida de botões específicos
class FichaButtons:
    """
    Classe de conveniência para criar botões específicos da ficha de paciente.
    """
    
    @staticmethod
    def followup_button(parent: QWidget, action: Callable) -> QPushButton:
        """Cria botão de follow-up já conectado"""
        return ButtonManager.create_action_button(
            text="📅 Follow-up",
            action=action,
            tooltip="Configurar follow-ups automáticos",
            parent=parent
        )
    
    @staticmethod
    def template_button(parent: QWidget, action: Callable) -> QPushButton:
        """Cria botão de templates já conectado"""
        return ButtonManager.create_action_button(
            text="📄 Templates",
            action=action,
            tooltip="Gerenciar templates de documentos",
            parent=parent
        )
    
    @staticmethod
    def email_button(parent: QWidget, action: Callable) -> QPushButton:
        """Cria botão de email já conectado"""
        return ButtonManager.create_action_button(
            text="📧 Enviar Email",
            action=action,
            tooltip="Enviar email para o paciente",
            parent=parent
        )
    
    @staticmethod
    def terapia_button(parent: QWidget, action: Callable) -> QPushButton:
        """Cria botão de terapia quântica já conectado"""
        return ButtonManager.create_action_button(
            text="⚡ Terapia Quântica",
            action=action,
            tooltip="Abrir módulo de terapia quântica",
            button_type='action',
            parent=parent
        )
    
    # ========== MÉTODOS ESPECÍFICOS PARA FICHA PACIENTE ==========
    
    @staticmethod
    def followup_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para agendamento de follow-up"""
        return ButtonManager.create_action_button(
            text="📅 Follow-up",
            action=action,
            tooltip="Agendar follow-up automático para o paciente",
            parent=parent
        )
    
    @staticmethod
    def lista_followups_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para listar follow-ups"""
        return ButtonManager.create_button(
            text="📋 Lista",
            action=action,
            tooltip="Ver lista de follow-ups agendados",
            button_type='small',
            parent=parent
        )
    
    @staticmethod
    def config_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão de configuração"""
        return ButtonManager.create_button(
            text="⚙️ Config",
            action=action,
            tooltip="Configurações de email",
            button_type='secondary',
            parent=parent
        )
    
    @staticmethod
    def cancelar_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão de cancelar"""
        btn = ButtonManager.create_button(
            text="❌ Cancelar",
            action=action,
            tooltip="Cancelar operação",
            button_type='secondary',
            parent=parent
        )
        # Estilo específico para botão de cancelar (vermelho)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
            }}
            QPushButton:pressed {{
                background-color: #991b1b;
            }}
        """)
        return btn
    
    @staticmethod
    def usar_template_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para usar template"""
        btn = ButtonManager.create_button(
            text="✅ Usar Template",
            action=action,
            tooltip="Aplicar template selecionado",
            button_type='primary',
            parent=parent
        )
        # Estilo específico para botão de sucesso (verde)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #16a34a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: #15803d;
            }}
            QPushButton:pressed {{
                background-color: #166534;
            }}
        """)
        return btn
    
    @staticmethod
    def template_personalizado_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para template personalizado"""
        return ButtonManager.create_action_button(
            text="✨ Usar Template Personalizado",
            action=action,
            tooltip="Usar template personalizado",
            parent=parent
        )
    
    @staticmethod
    def abrir_terapia_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para módulo de terapia"""
        btn = ButtonManager.create_action_button(
            text="⚡ Abrir Módulo de Terapia",
            action=action,
            tooltip="Abrir módulo de terapia quântica",
            parent=parent
        )
        btn.setMinimumWidth(200)
        return btn
    
    @staticmethod
    def entendido_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão de confirmação"""
        return ButtonManager.create_button(
            text="🔙 Entendido",
            action=action,
            tooltip="Fechar e confirmar",
            button_type='secondary',
            parent=parent
        )
    
    @staticmethod
    def fechar_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão de fechar"""
        return ButtonManager.create_button(
            text="🔙 Fechar",
            action=action,
            tooltip="Fechar janela",
            button_type='secondary',
            parent=parent
        )
    
    @staticmethod
    def assinatura_paciente_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para assinatura do paciente com estilo especial"""
        btn = ButtonManager.create_button(
            text="📝 Paciente",
            action=action,
            tooltip="Capturar assinatura do paciente",
            button_type='primary',
            parent=parent
        )
        
        # Estilo especial para assinatura (gradiente)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }}
            QPushButton:hover {{
                background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }}
            QPushButton:pressed {{
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
            }}
        """)
        return btn
    
    @staticmethod
    def cancelar_selecionado_button(parent: QWidget, action: Callable) -> QPushButton:
        """Botão para cancelar item selecionado"""
        return ButtonManager.cancelar_button(parent, action)

# Exportar classes principais
__all__ = ['ButtonManager', 'FichaButtons']
