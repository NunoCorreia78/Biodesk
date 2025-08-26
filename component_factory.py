"""
Biodesk - Factory Pattern para Lazy Loading
===========================================

Sistema de factory para carregamento sob demanda de componentes pesados,
melhorando significativamente o tempo de startup da aplicação.
"""

import threading
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal


class ComponentFactory(QObject):
    """Factory para carregamento lazy de componentes pesados"""
    
    component_loaded = pyqtSignal(str, object)  # nome_componente, instancia
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._components: Dict[str, Any] = {}
            self._loading: Dict[str, bool] = {}
            self._initialized = True
    
    def get_iris_canvas(self):
        """Obtém instância do IrisCanvas (lazy loading)"""
        if 'iris_canvas' not in self._components:
            if not self._loading.get('iris_canvas', False):
                self._loading['iris_canvas'] = True
                try:
                    from iris_canvas import IrisCanvas
                    self._components['iris_canvas'] = IrisCanvas()
                    self.component_loaded.emit('iris_canvas', self._components['iris_canvas'])
                    # print("✅ IrisCanvas carregado sob demanda")
                except ImportError as e:
                    print(f"⚠️ Erro ao carregar IrisCanvas: {e}")
                    self._components['iris_canvas'] = None
                finally:
                    self._loading['iris_canvas'] = False
        
        return self._components.get('iris_canvas')
    
    def get_pdf_viewer(self):
        """Obtém instância do PDFViewer (lazy loading)"""
        if 'pdf_viewer' not in self._components:
            if not self._loading.get('pdf_viewer', False):
                self._loading['pdf_viewer'] = True
                try:
                    from pdf_viewer import PDFViewer
                    self._components['pdf_viewer'] = PDFViewer()
                    self.component_loaded.emit('pdf_viewer', self._components['pdf_viewer'])
                    print("✅ PDFViewer carregado sob demanda")
                except ImportError as e:
                    print(f"⚠️ Erro ao carregar PDFViewer: {e}")
                    self._components['pdf_viewer'] = None
                finally:
                    self._loading['pdf_viewer'] = False
        
        return self._components.get('pdf_viewer')
    
    def get_webengine_editor(self):
        """Obtém instância do EditorDocumentos (lazy loading)"""
        if 'webengine_editor' not in self._components:
            if not self._loading.get('webengine_editor', False):
                self._loading['webengine_editor'] = True
                try:
                    from editor_documentos import EditorDocumentos
                    self._components['webengine_editor'] = EditorDocumentos()
                    self.component_loaded.emit('webengine_editor', self._components['webengine_editor'])
                    print("✅ EditorDocumentos carregado sob demanda")
                except ImportError as e:
                    print(f"⚠️ Erro ao carregar EditorDocumentos: {e}")
                    self._components['webengine_editor'] = None
                finally:
                    self._loading['webengine_editor'] = False
        
        return self._components.get('webengine_editor')
    
    def get_email_sender(self):
        """Obtém instância do EmailSender (lazy loading)"""
        if 'email_sender' not in self._components:
            if not self._loading.get('email_sender', False):
                self._loading['email_sender'] = True
                try:
                    from email_sender import EmailSender
                    self._components['email_sender'] = EmailSender()
                    self.component_loaded.emit('email_sender', self._components['email_sender'])
                    print("✅ EmailSender carregado sob demanda")
                except ImportError as e:
                    print(f"⚠️ Erro ao carregar EmailSender: {e}")
                    self._components['email_sender'] = None
                finally:
                    self._loading['email_sender'] = False
        
        return self._components.get('email_sender')
    
    def get_cv2_module(self):
        """Obtém módulo cv2 (lazy loading para evitar janela que pisca)"""
        if 'cv2' not in self._components:
            if not self._loading.get('cv2', False):
                self._loading['cv2'] = True
                try:
                    import cv2
                    self._components['cv2'] = cv2
                    self.component_loaded.emit('cv2', cv2)
                    print("✅ OpenCV (cv2) carregado sob demanda")
                except ImportError as e:
                    print(f"⚠️ Erro ao carregar OpenCV: {e}")
                    self._components['cv2'] = None
                finally:
                    self._loading['cv2'] = False
        
        return self._components.get('cv2')
    
    def preload_component(self, component_name: str):
        """Pré-carrega um componente específico em background"""
        def _preload():
            method_map = {
                'iris_canvas': self.get_iris_canvas,
                'pdf_viewer': self.get_pdf_viewer,
                'webengine_editor': self.get_webengine_editor,
                'email_sender': self.get_email_sender,
                'cv2': self.get_cv2_module
            }
            
            if component_name in method_map:
                method_map[component_name]()
            else:
                print(f"⚠️ Componente '{component_name}' não reconhecido")
        
        # Executar em thread separada para não bloquear UI
        thread = threading.Thread(target=_preload, daemon=True)
        thread.start()
    
    def preload_essential_components(self):
        """Pré-carrega componentes essenciais em background"""
        essential = ['email_sender', 'cv2']  # Componentes mais usados
        
        for component in essential:
            self.preload_component(component)
    
    def is_component_loaded(self, component_name: str) -> bool:
        """Verifica se um componente já está carregado"""
        return component_name in self._components and self._components[component_name] is not None
    
    def is_component_loading(self, component_name: str) -> bool:
        """Verifica se um componente está sendo carregado"""
        return self._loading.get(component_name, False)
    
    def clear_component(self, component_name: str):
        """Remove um componente da cache (liberando memória)"""
        if component_name in self._components:
            del self._components[component_name]
            print(f"🗑️ Componente '{component_name}' removido da cache")
    
    def clear_all_components(self):
        """Remove todos os componentes da cache"""
        self._components.clear()
        self._loading.clear()
        print("🗑️ Todos os componentes removidos da cache")
    
    def get_loaded_components(self) -> list:
        """Retorna lista de componentes carregados"""
        return [name for name, component in self._components.items() if component is not None]
    
    def get_memory_usage_estimate(self) -> dict:
        """Estimativa de uso de memória por componente"""
        estimates = {
            'iris_canvas': '~15MB',
            'pdf_viewer': '~8MB', 
            'webengine_editor': '~25MB',
            'email_sender': '~2MB',
            'cv2': '~12MB'
        }
        
        loaded = self.get_loaded_components()
        return {comp: estimates.get(comp, '~Unknown') for comp in loaded}


# Singleton global para uso em toda aplicação
factory = ComponentFactory()


def get_factory() -> ComponentFactory:
    """Obtém instância global do factory"""
    return factory
