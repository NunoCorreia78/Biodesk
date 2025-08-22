#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 SISTEMA DE DETECÇÃO DE ALTERAÇÕES
==================================

Sistema para detectar alterações em declarações de saúde
"""

import hashlib
import json
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class DetectorAlteracoes(QObject):
    """Detecta alterações em declarações de saúde"""
    
    estado_alterado = pyqtSignal(str)  # Emite: "não preenchida", "preenchida", "alterada"
    
    def __init__(self):
        super().__init__()
        self.hash_original = None
        self.data_original = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.verificar_alteracoes)
        self.timer.start(5000)  # Verifica a cada 5 segundos
        
    def calcular_hash(self, dados):
        """Calcula hash dos dados para detectar alterações"""
        dados_str = json.dumps(dados, sort_keys=True)
        return hashlib.sha256(dados_str.encode()).hexdigest()
        
    def definir_estado_inicial(self, dados):
        """Define o estado inicial da declaração"""
        if not dados:
            self.estado_alterado.emit("não preenchida")
            return
            
        self.hash_original = self.calcular_hash(dados)
        self.data_original = datetime.now()
        self.estado_alterado.emit("preenchida")
        
    def verificar_alteracoes(self):
        """Verifica se houve alterações nos dados"""
        if not hasattr(self, 'widget_declaracao'):
            return
            
        dados_atuais = self.widget_declaracao.coletar_dados()
        
        if not dados_atuais:
            self.estado_alterado.emit("não preenchida")
            return
            
        hash_atual = self.calcular_hash(dados_atuais)
        
        if self.hash_original is None:
            self.hash_original = hash_atual
            self.data_original = datetime.now()
            self.estado_alterado.emit("preenchida")
        elif hash_atual != self.hash_original:
            data_alteracao = datetime.now().strftime('%d/%m/%Y %H:%M')
            self.estado_alterado.emit(f"alterada em {data_alteracao}")
            
    def conectar_widget(self, widget_declaracao):
        """Conecta ao widget de declaração para monitorar"""
        self.widget_declaracao = widget_declaracao
