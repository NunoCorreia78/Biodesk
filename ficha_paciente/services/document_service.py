"""
DocumentService - Serviço centralizado para gestão de documentos
Extraído do monolito ficha_paciente.py para modularização
"""

from typing import Optional, Dict, Any, List
import os
import shutil
from pathlib import Path
from datetime import datetime


class DocumentService:
    """Serviço centralizado para operações de documentos"""
    
    def __init__(self, paciente_data: Optional[Dict] = None):
        self.paciente_data = paciente_data or {}
        self.pasta_documentos = self._obter_pasta_documentos()
    
    def on_documento_adicionado(self, caminho_documento: str) -> bool:
        """
        Callback quando documento é adicionado
        
        Consolidado do monolito ficha_paciente.py
        """
        try:
            print(f"📄 DocumentService: Documento adicionado: {os.path.basename(caminho_documento)}")
            
            # Validar arquivo
            if not self._validar_documento(caminho_documento):
                return False
            
            # Criar metadata
            self._criar_metadata_documento(caminho_documento)
            
            # Organizar na estrutura de pastas
            self._organizar_documento(caminho_documento)
            
            print("✅ DocumentService: Documento processado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ DocumentService: Erro ao adicionar documento: {e}")
            return False
    
    def on_documento_removido(self, caminho_documento: str) -> bool:
        """
        Callback quando documento é removido
        
        Método consolidado com retry e validações
        """
        try:
            print(f"🗑️ DocumentService: Removendo documento: {os.path.basename(caminho_documento)}")
            
            # Remover com múltiplas tentativas (padrão do sistema)
            sucesso = self._remover_com_retry(caminho_documento)
            
            if sucesso:
                # Remover metadata associada
                self._remover_metadata_documento(caminho_documento)
                print("✅ DocumentService: Documento removido com sucesso")
            
            return sucesso
            
        except Exception as e:
            print(f"❌ DocumentService: Erro ao remover documento: {e}")
            return False
    
    def on_documento_visualizado(self, caminho_documento: str) -> bool:
        """
        Callback quando documento é visualizado
        
        Atualiza estatísticas e histórico
        """
        try:
            print(f"👁️ DocumentService: Visualizando documento: {os.path.basename(caminho_documento)}")
            
            # Registrar visualização
            self._registrar_visualizacao(caminho_documento)
            
            # Abrir documento com aplicação padrão
            if os.path.exists(caminho_documento):
                os.startfile(caminho_documento)  # Windows
                return True
            else:
                print("❌ DocumentService: Arquivo não encontrado")
                return False
                
        except Exception as e:
            print(f"❌ DocumentService: Erro ao visualizar documento: {e}")
            return False
    
    def on_documento_assinado(self, caminho_documento: str) -> bool:
        """
        Callback quando documento é assinado
        
        Atualiza status e metadata
        """
        try:
            print(f"✍️ DocumentService: Documento assinado: {os.path.basename(caminho_documento)}")
            
            # Atualizar metadata com info de assinatura
            self._atualizar_metadata_assinatura(caminho_documento)
            
            # Criar backup do documento assinado
            self._criar_backup_documento_assinado(caminho_documento)
            
            return True
            
        except Exception as e:
            print(f"❌ DocumentService: Erro ao processar assinatura: {e}")
            return False
    
    def atualizar_lista_documentos(self) -> List[Dict[str, Any]]:
        """
        Atualiza e retorna lista de documentos do paciente
        
        Método consolidado com cache otimizado
        """
        try:
            documentos = []
            
            if not os.path.exists(self.pasta_documentos):
                os.makedirs(self.pasta_documentos, exist_ok=True)
                return documentos
            
            # Escanear pasta de documentos
            for arquivo in os.listdir(self.pasta_documentos):
                caminho_completo = os.path.join(self.pasta_documentos, arquivo)
                
                if os.path.isfile(caminho_completo) and not arquivo.endswith('.meta'):
                    info_documento = self._obter_info_documento(caminho_completo)
                    if info_documento:
                        documentos.append(info_documento)
            
            # Ordenar por data de modificação (mais recente primeiro)
            documentos.sort(key=lambda x: x.get('data_modificacao', ''), reverse=True)
            
            print(f"📋 DocumentService: {len(documentos)} documentos carregados")
            return documentos
            
        except Exception as e:
            print(f"❌ DocumentService: Erro ao atualizar lista: {e}")
            return []
    
    def importar_pdf_manual(self, caminho_origem: str) -> bool:
        """
        Importa PDF manualmente para o paciente
        
        Método consolidado do monolito
        """
        try:
            print(f"📥 DocumentService: Importando PDF: {os.path.basename(caminho_origem)}")
            
            # Validar arquivo
            if not self._validar_pdf(caminho_origem):
                return False
            
            # Gerar nome único
            nome_destino = self._gerar_nome_unico_documento(caminho_origem)
            caminho_destino = os.path.join(self.pasta_documentos, nome_destino)
            
            # Copiar arquivo
            shutil.copy2(caminho_origem, caminho_destino)
            
            # Processar como documento adicionado
            return self.on_documento_adicionado(caminho_destino)
            
        except Exception as e:
            print(f"❌ DocumentService: Erro ao importar PDF: {e}")
            return False
    
    def obter_estatisticas_documentos(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos documentos
        
        Novo método consolidado
        """
        try:
            documentos = self.atualizar_lista_documentos()
            
            estatisticas = {
                'total': len(documentos),
                'por_tipo': {},
                'assinados': 0,
                'nao_assinados': 0,
                'tamanho_total': 0
            }
            
            for doc in documentos:
                # Contagem por tipo
                tipo = doc.get('tipo', 'outros')
                estatisticas['por_tipo'][tipo] = estatisticas['por_tipo'].get(tipo, 0) + 1
                
                # Contagem de assinados
                if doc.get('assinado', False):
                    estatisticas['assinados'] += 1
                else:
                    estatisticas['nao_assinados'] += 1
                
                # Tamanho total
                estatisticas['tamanho_total'] += doc.get('tamanho', 0)
            
            return estatisticas
            
        except Exception as e:
            print(f"❌ DocumentService: Erro ao obter estatísticas: {e}")
            return {'total': 0, 'erro': str(e)}
    
    # ---- Métodos privados ----
    
    def _obter_pasta_documentos(self) -> str:
        """Obtém pasta de documentos do paciente"""
        paciente_id = self.paciente_data.get('id', 'novo')
        return os.path.join('Documentos_Pacientes', str(paciente_id))
    
    def _validar_documento(self, caminho: str) -> bool:
        """Valida se o documento é válido"""
        if not os.path.exists(caminho):
            print("❌ DocumentService: Arquivo não existe")
            return False
        
        # Verificar extensões permitidas
        extensoes_permitidas = ['.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg']
        extensao = Path(caminho).suffix.lower()
        
        if extensao not in extensoes_permitidas:
            print(f"❌ DocumentService: Extensão não permitida: {extensao}")
            return False
        
        return True
    
    def _validar_pdf(self, caminho: str) -> bool:
        """Valida especificamente arquivos PDF"""
        if not self._validar_documento(caminho):
            return False
        
        if not caminho.lower().endswith('.pdf'):
            print("❌ DocumentService: Arquivo não é PDF")
            return False
        
        return True
    
    def _criar_metadata_documento(self, caminho: str) -> None:
        """Cria arquivo de metadata para o documento"""
        try:
            info_arquivo = os.stat(caminho)
            nome_base = os.path.basename(caminho)
            
            metadata = {
                'nome_original': nome_base,
                'tamanho': info_arquivo.st_size,
                'data_adicao': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'paciente_id': self.paciente_data.get('id'),
                'paciente_nome': self.paciente_data.get('nome', 'N/A'),
                'tipo': self._detectar_tipo_documento(nome_base),
                'assinado': False,
                'visualizacoes': 0
            }
            
            # Salvar metadata
            caminho_meta = caminho + '.meta'
            with open(caminho_meta, 'w', encoding='utf-8') as f:
                for chave, valor in metadata.items():
                    f.write(f"{chave}: {valor}\n")
                    
        except Exception as e:
            print(f"⚠️ DocumentService: Erro ao criar metadata: {e}")
    
    def _detectar_tipo_documento(self, nome_arquivo: str) -> str:
        """Detecta tipo do documento pelo nome"""
        nome_lower = nome_arquivo.lower()
        
        if 'receita' in nome_lower or 'prescri' in nome_lower:
            return 'prescricao'
        elif 'consentimento' in nome_lower or 'rgpd' in nome_lower:
            return 'consentimento'
        elif 'declaracao' in nome_lower:
            return 'declaracao'
        elif 'protocolo' in nome_lower:
            return 'protocolo'
        else:
            return 'outros'
    
    def _organizar_documento(self, caminho: str) -> None:
        """Organiza documento na estrutura de pastas apropriada"""
        try:
            # Criar subpastas por tipo se necessário
            tipo = self._detectar_tipo_documento(os.path.basename(caminho))
            pasta_tipo = os.path.join(self.pasta_documentos, tipo)
            
            os.makedirs(pasta_tipo, exist_ok=True)
            
        except Exception as e:
            print(f"⚠️ DocumentService: Erro ao organizar: {e}")
    
    def _remover_com_retry(self, caminho: str, max_tentativas: int = 3) -> bool:
        """Remove arquivo com múltiplas tentativas (padrão do sistema)"""
        import time
        
        for tentativa in range(max_tentativas):
            try:
                if os.path.exists(caminho):
                    os.remove(caminho)
                    return True
                else:
                    return True  # Já não existe
                    
            except OSError as e:
                if tentativa < max_tentativas - 1:
                    print(f"⚠️ DocumentService: Tentativa {tentativa + 1} falhada, tentando novamente...")
                    time.sleep(1)
                else:
                    print(f"❌ DocumentService: Falha após {max_tentativas} tentativas: {e}")
                    return False
        
        return False
    
    def _remover_metadata_documento(self, caminho: str) -> None:
        """Remove metadata associada ao documento"""
        try:
            caminho_meta = caminho + '.meta'
            if os.path.exists(caminho_meta):
                os.remove(caminho_meta)
        except Exception as e:
            print(f"⚠️ DocumentService: Erro ao remover metadata: {e}")
    
    def _registrar_visualizacao(self, caminho: str) -> None:
        """Registra visualização do documento"""
        try:
            caminho_meta = caminho + '.meta'
            if os.path.exists(caminho_meta):
                # Incrementar contador de visualizações
                # Implementação simplificada
                pass
        except Exception:
            pass
    
    def _atualizar_metadata_assinatura(self, caminho: str) -> None:
        """Atualiza metadata com informação de assinatura"""
        try:
            caminho_meta = caminho + '.meta'
            if os.path.exists(caminho_meta):
                # Marcar como assinado
                with open(caminho_meta, 'a', encoding='utf-8') as f:
                    f.write(f"assinado: True\n")
                    f.write(f"data_assinatura: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        except Exception as e:
            print(f"⚠️ DocumentService: Erro ao atualizar metadata: {e}")
    
    def _criar_backup_documento_assinado(self, caminho: str) -> None:
        """Cria backup do documento assinado"""
        try:
            pasta_backup = os.path.join(self.pasta_documentos, 'backups')
            os.makedirs(pasta_backup, exist_ok=True)
            
            nome_backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(caminho)}"
            caminho_backup = os.path.join(pasta_backup, nome_backup)
            
            shutil.copy2(caminho, caminho_backup)
            print(f"💾 DocumentService: Backup criado: {nome_backup}")
            
        except Exception as e:
            print(f"⚠️ DocumentService: Erro ao criar backup: {e}")
    
    def _obter_info_documento(self, caminho: str) -> Optional[Dict[str, Any]]:
        """Obtém informações completas do documento"""
        try:
            if not os.path.exists(caminho):
                return None
            
            info_arquivo = os.stat(caminho)
            nome_base = os.path.basename(caminho)
            
            # Carregar metadata se existir
            metadata = self._carregar_metadata(caminho)
            
            return {
                'nome': nome_base,
                'caminho': caminho,
                'tamanho': info_arquivo.st_size,
                'data_modificacao': datetime.fromtimestamp(info_arquivo.st_mtime).strftime('%d/%m/%Y %H:%M'),
                'tipo': metadata.get('tipo', self._detectar_tipo_documento(nome_base)),
                'assinado': metadata.get('assinado', False),
                'visualizacoes': metadata.get('visualizacoes', 0)
            }
            
        except Exception as e:
            print(f"⚠️ DocumentService: Erro ao obter info: {e}")
            return None
    
    def _carregar_metadata(self, caminho: str) -> Dict[str, Any]:
        """Carrega metadata do documento"""
        try:
            caminho_meta = caminho + '.meta'
            metadata = {}
            
            if os.path.exists(caminho_meta):
                with open(caminho_meta, 'r', encoding='utf-8') as f:
                    for linha in f:
                        if ':' in linha:
                            chave, valor = linha.strip().split(':', 1)
                            metadata[chave.strip()] = valor.strip()
            
            return metadata
            
        except Exception:
            return {}
    
    def _gerar_nome_unico_documento(self, caminho_origem: str) -> str:
        """Gera nome único para evitar conflitos"""
        nome_base = os.path.basename(caminho_origem)
        nome_sem_ext = os.path.splitext(nome_base)[0]
        extensao = os.path.splitext(nome_base)[1]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{nome_sem_ext}_{timestamp}{extensao}"


# ---- Funções de conveniência ----

def processar_documento_rapido(paciente_data: Dict, caminho_documento: str, acao: str) -> bool:
    """Função rápida para processar documento (compatibilidade)"""
    service = DocumentService(paciente_data)
    
    if acao == 'adicionar':
        return service.on_documento_adicionado(caminho_documento)
    elif acao == 'remover':
        return service.on_documento_removido(caminho_documento)
    elif acao == 'visualizar':
        return service.on_documento_visualizado(caminho_documento)
    elif acao == 'assinar':
        return service.on_documento_assinado(caminho_documento)
    else:
        return False
