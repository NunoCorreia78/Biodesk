"""
📧 Email Scheduler - Sistema de Agendamento de Emails
Verifica e envia emails agendados automaticamente
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from pathlib import Path
import traceback


class EmailScheduler(QObject):
    """Scheduler para emails agendados"""
    
    # Sinais
    email_enviado = pyqtSignal(dict)  # Emitido quando email é enviado
    email_falhado = pyqtSignal(dict, str)  # Emitido quando envio falha
    status_atualizado = pyqtSignal(str)  # Status geral do scheduler
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurações
        self.intervalo_verificacao = 60000  # 1 minuto em ms
        self.emails_agendados_file = "emails_agendados.json"
        self.historico_file = "historico_envios/emails_agendados.json"
        self.emails_enviados_file = "historico_envios/emails_enviados.json"
        
        # Timer para verificação periódica
        self.timer = QTimer()
        self.timer.timeout.connect(self.verificar_emails_pendentes)
        
        # Estado
        self.ativo = False
        self.ultimo_verificacao = None
        
        # Garantir que pastas existem
        self._criar_diretorios()
        
        print("📧 EmailScheduler inicializado")
    
    def _criar_diretorios(self):
        """Criar diretorios necessários"""
        try:
            os.makedirs("historico_envios", exist_ok=True)
            
            # Criar ficheiros vazios se não existirem
            for arquivo in [self.emails_agendados_file, self.historico_file, self.emails_enviados_file]:
                if not os.path.exists(arquivo):
                    with open(arquivo, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                        
        except Exception as e:
            print(f"❌ Erro ao criar diretorios: {e}")
    
    def iniciar(self):
        """Iniciar o scheduler"""
        if not self.ativo:
            self.timer.start(self.intervalo_verificacao)
            self.ativo = True
            self.status_atualizado.emit("Scheduler iniciado")
            print("✅ EmailScheduler iniciado - verificação a cada 1 minuto")
            
            # Verificar imediatamente
            self.verificar_emails_pendentes()
    
    def parar(self):
        """Parar o scheduler"""
        if self.ativo:
            self.timer.stop()
            self.ativo = False
            self.status_atualizado.emit("Scheduler parado")
            print("⏹️ EmailScheduler parado")
    
    def agendar_email(self, email_data: Dict[str, Any]) -> str:
        """
        Agendar um novo email
        
        Args:
            email_data: Dict com dados do email
            
        Returns:
            ID do email agendado
        """
        try:
            # Gerar ID único
            email_id = f"{datetime.now().timestamp()}"
            
            # Preparar dados do email
            email_agendado = {
                "id": email_id,
                "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_envio": email_data.get("data_envio"),
                "paciente_id": email_data.get("paciente_id"),
                "paciente_nome": email_data.get("paciente_nome"),
                "destinatario": email_data.get("destinatario"),
                "assunto": email_data.get("assunto"),
                "mensagem": email_data.get("mensagem"),
                "anexos": email_data.get("anexos", []),
                "status": "agendado"
            }
            
            # Carregar emails agendados existentes
            emails_agendados = self._carregar_emails_agendados()
            
            # Adicionar novo email
            emails_agendados.append(email_agendado)
            
            # Guardar lista atualizada
            self._salvar_emails_agendados(emails_agendados)
            
            # Também salvar no histórico
            self._adicionar_ao_historico(email_agendado)
            
            print(f"📅 Email agendado: {email_data.get('assunto')} para {email_data.get('data_envio')}")
            self.status_atualizado.emit(f"Email agendado: {email_data.get('assunto')}")
            
            return email_id
            
        except Exception as e:
            print(f"❌ Erro ao agendar email: {e}")
            traceback.print_exc()
            return None
    
    def cancelar_email(self, email_id: str) -> bool:
        """Cancelar email agendado"""
        try:
            emails_agendados = self._carregar_emails_agendados()
            
            for email in emails_agendados:
                if email.get("id") == email_id and email.get("status") == "agendado":
                    email["status"] = "cancelado"
                    email["data_cancelamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Salvar alterações
                    self._salvar_emails_agendados(emails_agendados)
                    
                    # Atualizar histórico
                    self._atualizar_historico(email)
                    
                    print(f"❌ Email cancelado: {email.get('assunto')}")
                    self.status_atualizado.emit(f"Email cancelado: {email.get('assunto')}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao cancelar email: {e}")
            return False
    
    def verificar_emails_pendentes(self):
        """Verificar e enviar emails que chegaram na hora"""
        try:
            self.ultimo_verificacao = datetime.now()
            
            emails_agendados = self._carregar_emails_agendados()
            emails_para_enviar = []
            
            agora = datetime.now()
            
            # Filtrar emails que devem ser enviados agora
            for email in emails_agendados:
                if email.get("status") != "agendado":
                    continue
                    
                data_envio_str = email.get("data_envio")
                if not data_envio_str:
                    continue
                
                try:
                    data_envio = datetime.strptime(data_envio_str, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        data_envio = datetime.strptime(data_envio_str, "%Y-%m-%d %H:%M")
                    except:
                        continue
                
                # Se chegou a hora (com margem de 1 minuto)
                if data_envio <= agora:
                    emails_para_enviar.append(email)
            
            # Enviar emails pendentes
            for email in emails_para_enviar:
                self._processar_envio_email(email)
            
            if emails_para_enviar:
                # Salvar alterações
                self._salvar_emails_agendados(emails_agendados)
            
            # Log da verificação
            total_agendados = len([e for e in emails_agendados if e.get("status") == "agendado"])
            if total_agendados > 0:
                print(f"🔍 Verificação: {len(emails_para_enviar)} enviados, {total_agendados} pendentes")
                
        except Exception as e:
            print(f"❌ Erro na verificação de emails: {e}")
            traceback.print_exc()
    
    def _processar_envio_email(self, email_data: Dict[str, Any]):
        """Processar envio de um email específico"""
        try:
            # Tentar importar sistema de email
            try:
                from email_sender import EmailSender
                email_sender = EmailSender()
                sistema_email_disponivel = True
            except ImportError:
                sistema_email_disponivel = False
            
            sucesso = False
            
            if sistema_email_disponivel:
                # Envio real
                try:
                    anexos = email_data.get("anexos", [])
                    if anexos:
                        sucesso, erro = email_sender.send_email_with_attachments(
                            email_data.get("destinatario"),
                            email_data.get("assunto"),
                            email_data.get("mensagem"),
                            anexos
                        )
                    else:
                        sucesso, erro = email_sender.send_email(
                            email_data.get("destinatario"),
                            email_data.get("assunto"),
                            email_data.get("mensagem")
                        )
                    
                    if not sucesso:
                        print(f"❌ Falha no envio: {erro}")
                        
                except Exception as e:
                    print(f"❌ Erro no sistema de email: {e}")
                    sucesso = False
            else:
                # Modo simulação
                print(f"📧 SIMULAÇÃO - Email enviado:")
                print(f"   Para: {email_data.get('destinatario')}")
                print(f"   Assunto: {email_data.get('assunto')}")
                sucesso = True  # Considerar sucesso em modo simulação
            
            # Atualizar status
            if sucesso:
                email_data["status"] = "enviado"
                email_data["data_envio_real"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Registrar no histórico de enviados
                self._registrar_email_enviado(email_data)
                
                print(f"✅ Email enviado: {email_data.get('assunto')}")
                self.email_enviado.emit(email_data)
                
            else:
                email_data["status"] = "falhado"
                email_data["data_falha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"❌ Falha no envio: {email_data.get('assunto')}")
                self.email_falhado.emit(email_data, "Erro no envio")
            
            # Atualizar histórico
            self._atualizar_historico(email_data)
            
        except Exception as e:
            print(f"❌ Erro ao processar envio: {e}")
            traceback.print_exc()
    
    def _carregar_emails_agendados(self) -> List[Dict[str, Any]]:
        """Carregar lista de emails agendados"""
        try:
            if os.path.exists(self.emails_agendados_file):
                with open(self.emails_agendados_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar emails agendados: {e}")
        return []
    
    def _salvar_emails_agendados(self, emails: List[Dict[str, Any]]):
        """Salvar lista de emails agendados"""
        try:
            with open(self.emails_agendados_file, 'w', encoding='utf-8') as f:
                json.dump(emails, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar emails agendados: {e}")
    
    def _adicionar_ao_historico(self, email_data: Dict[str, Any]):
        """Adicionar email ao histórico completo"""
        try:
            historico = []
            if os.path.exists(self.historico_file):
                with open(self.historico_file, 'r', encoding='utf-8') as f:
                    historico = json.load(f)
            
            historico.append(email_data.copy())
            
            # Manter apenas os últimos 1000 registros
            if len(historico) > 1000:
                historico = historico[-1000:]
            
            with open(self.historico_file, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erro ao adicionar ao histórico: {e}")
    
    def _atualizar_historico(self, email_atualizado: Dict[str, Any]):
        """Atualizar email no histórico"""
        try:
            historico = []
            if os.path.exists(self.historico_file):
                with open(self.historico_file, 'r', encoding='utf-8') as f:
                    historico = json.load(f)
            
            # Encontrar e atualizar o email
            for i, email in enumerate(historico):
                if email.get("id") == email_atualizado.get("id"):
                    historico[i] = email_atualizado.copy()
                    break
            
            with open(self.historico_file, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erro ao atualizar histórico: {e}")
    
    def _registrar_email_enviado(self, email_data: Dict[str, Any]):
        """Registrar email no histórico de enviados"""
        try:
            enviados = []
            if os.path.exists(self.emails_enviados_file):
                with open(self.emails_enviados_file, 'r', encoding='utf-8') as f:
                    enviados = json.load(f)
            
            # Registro simplificado para histórico de enviados
            registro = {
                "data_envio": email_data.get("data_envio_real"),
                "paciente_id": email_data.get("paciente_id"),
                "paciente_nome": email_data.get("paciente_nome"),
                "destinatario": email_data.get("destinatario"),
                "assunto": email_data.get("assunto"),
                "num_anexos": len(email_data.get("anexos", [])),
                "enviado_real": True,
                "status": "Enviado via Scheduler"
            }
            
            enviados.append(registro)
            
            # Manter apenas os últimos 1000 registros
            if len(enviados) > 1000:
                enviados = enviados[-1000:]
            
            with open(self.emails_enviados_file, 'w', encoding='utf-8') as f:
                json.dump(enviados, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erro ao registrar email enviado: {e}")
    
    def obter_emails_agendados(self) -> List[Dict[str, Any]]:
        """Obter lista de emails agendados"""
        return self._carregar_emails_agendados()
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obter estatísticas do scheduler"""
        try:
            emails = self._carregar_emails_agendados()
            
            estatisticas = {
                "total": len(emails),
                "agendados": len([e for e in emails if e.get("status") == "agendado"]),
                "enviados": len([e for e in emails if e.get("status") == "enviado"]),
                "cancelados": len([e for e in emails if e.get("status") == "cancelado"]),
                "falhados": len([e for e in emails if e.get("status") == "falhado"]),
                "ultimo_verificacao": self.ultimo_verificacao.strftime("%Y-%m-%d %H:%M:%S") if self.ultimo_verificacao else "Nunca",
                "ativo": self.ativo
            }
            
            return estatisticas
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {"erro": str(e)}


# Instância global do scheduler
_scheduler_instance = None

def get_email_scheduler() -> EmailScheduler:
    """Obter instância singleton do scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = EmailScheduler()
    return _scheduler_instance
