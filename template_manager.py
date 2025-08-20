"""
Sistema de Templates Externos para Biodesk
Permite importar e gerenciar templates de documentos
"""

import os
import json
from typing import Dict, List
from datetime import datetime

class BiodeskTemplateManager:
    """Gerenciador de templates externos para o Biodesk"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Garante que os diretórios de templates existem"""
        categories = ["exercicios", "dietas", "alongamentos", "suplementos", "orientacoes"]
        
        for category in categories:
            category_path = os.path.join(self.templates_dir, category)
            os.makedirs(category_path, exist_ok=True)
    
    def import_template_from_file(self, file_path: str, category: str, template_name: str = None) -> bool:
        """Importa um template de um arquivo externo"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ Arquivo não encontrado: {file_path}")
                return False
            
            # Ler conteúdo do arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Nome do template
            if not template_name:
                template_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Criar estrutura do template
            template_data = {
                "nome": template_name,
                "texto": content,
                "categoria": category,
                "data_criacao": datetime.now().isoformat(),
                "origem": "arquivo_externo",
                "arquivo_origem": file_path,
                "editavel": True
            }
            
            # Salvar template
            return self.save_template(template_data, category)
            
        except Exception as e:
            print(f"❌ Erro ao importar template: {e}")
            return False
    
    def save_template(self, template_data: Dict, category: str) -> bool:
        """Salva um template na categoria especificada"""
        try:
            category_path = os.path.join(self.templates_dir, category)
            os.makedirs(category_path, exist_ok=True)
            
            # Nome do arquivo (sanitizado)
            safe_name = self.sanitize_filename(template_data["nome"])
            file_path = os.path.join(category_path, f"{safe_name}.json")
            
            # Salvar arquivo JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Template salvo: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar template: {e}")
            return False
    
    def load_templates(self, category: str) -> List[Dict]:
        """Carrega todos os templates de uma categoria"""
        templates = []
        category_path = os.path.join(self.templates_dir, category)
        
        if not os.path.exists(category_path):
            return templates
        
        try:
            for filename in os.listdir(category_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(category_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        templates.append(template_data)
            
            # Ordenar por nome
            templates.sort(key=lambda x: x.get('nome', ''))
            
        except Exception as e:
            print(f"❌ Erro ao carregar templates da categoria {category}: {e}")
        
        return templates
    
    def create_template_preview(self, template_data: Dict, paciente_data: Dict = None) -> str:
        """Cria preview personalizado para um template"""
        template_name = template_data.get('nome', 'Template')
        template_content = template_data.get('texto', '')
        category = template_data.get('categoria', 'geral')
        
        # Dados do paciente
        nome_paciente = paciente_data.get('nome', 'N/A') if paciente_data else 'N/A'
        data_atual = datetime.now().strftime('%d/%m/%Y')
        
        # Ícones por categoria
        category_icons = {
            'exercicios': '🏃',
            'dietas': '🥗',
            'alongamentos': '🧘',
            'suplementos': '💊',
            'orientacoes': '📝'
        }
        
        icon = category_icons.get(category, '📄')
        
        # Preview limpo e elegante
        preview = f"""
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
                    🩺 PRESCRIÇÃO MÉDICA                    
                                                          
     [LOGO]            Dr. Nuno Correia                   
    Biodesk         Medicina Integrativa                  
                  & Análise Iridológica                   
                                                          
📧 geral@nunocorreia.pt     📞 (+351) 123 456 789         
🌐 www.nunocorreia.pt                   Data: {data_atual}    
▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌

📋 DADOS DO PACIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nome:       {nome_paciente}
Data Nasc:  {paciente_data.get('data_nascimento', 'N/A') if paciente_data else 'N/A'}
Email:      {paciente_data.get('email', 'N/A') if paciente_data else 'N/A'}
Contacto:   {paciente_data.get('contacto', 'N/A') if paciente_data else 'N/A'}

{icon} PRESCRIÇÃO: {template_name.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 CONTEÚDO:
{self.format_content_for_preview(template_content)}

✅ ORIENTAÇÕES GERAIS:
   • Seguir rigorosamente as indicações acima
   • Manter acompanhamento conforme orientação
   • Em caso de dúvidas, contactar a clínica
   • Retorno conforme agendamento

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍⚕️ Dr. Nuno Correia
   Medicina Integrativa

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documento gerado pelo Sistema Biodesk - {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Confidencial - Destinado exclusivamente ao paciente                    Página 1
        """
        
        return preview.strip()
    
    def format_content_for_preview(self, content: str) -> str:
        """Formata o conteúdo do template para o preview"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                if not line.startswith('•') and not line.startswith('-'):
                    formatted_lines.append(f"   • {line}")
                else:
                    formatted_lines.append(f"   {line}")
        
        return '\n'.join(formatted_lines[:8])  # Limitar a 8 linhas
    
    def sanitize_filename(self, name: str) -> str:
        """Sanitiza nome para usar como nome de arquivo"""
        import re
        # Remover caracteres especiais
        safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Substituir espaços por underscore
        safe_name = safe_name.replace(' ', '_')
        # Limitar tamanho
        return safe_name[:50]
    
    def update_template(self, template_data: Dict, category: str) -> bool:
        """Atualiza um template existente"""
        template_data["data_modificacao"] = datetime.now().isoformat()
        return self.save_template(template_data, category)
    
    def delete_template(self, template_name: str, category: str) -> bool:
        """Remove um template"""
        try:
            safe_name = self.sanitize_filename(template_name)
            file_path = os.path.join(self.templates_dir, category, f"{safe_name}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Template removido: {file_path}")
                return True
            else:
                print(f"❌ Template não encontrado: {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao remover template: {e}")
            return False
    
    def export_template_to_file(self, template_data, file_path):
        """
        Exporta um template para arquivo JSON
        
        Args:
            template_data: Dados do template para exportar
            file_path: Caminho do arquivo para salvar
            
        Returns:
            bool: True se exportado com sucesso, False caso contrário
        """
        try:
            # Preparar dados para exportação
            export_data = {
                "biodesk_template": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "template": template_data
                }
            }
            
            # Salvar no arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"[TEMPLATE_MANAGER] ✅ Template exportado para: {file_path}")
            return True
            
        except Exception as e:
            print(f"[TEMPLATE_MANAGER] ❌ Erro ao exportar template: {e}")
            return False


def criar_templates_exemplo():
    """Cria alguns templates de exemplo para demonstração"""
    manager = BiodeskTemplateManager()
    
    # Template de exercícios
    exercicio_template = {
        "nome": "Exercícios para Postura",
        "texto": """Realizar alongamentos matinais durante 10 minutos
Caminhadas leves de 30 minutos, 3x por semana
Exercícios de fortalecimento do core, 2x por semana
Yoga ou pilates, 1x por semana
Evitar permanecer na mesma posição por mais de 1 hora""",
        "categoria": "exercicios",
        "data_criacao": datetime.now().isoformat(),
        "origem": "sistema",
        "editavel": True
    }
    
    # Template de dieta
    dieta_template = {
        "nome": "Dieta Anti-inflamatória",
        "texto": """Consumir vegetais de folha verde diariamente
Incluir peixes ricos em ômega-3, 2x por semana
Evitar alimentos processados e açúcares refinados
Beber 2 litros de água por dia
Consumir frutas antioxidantes (mirtilos, romã)
Reduzir o consumo de carne vermelha""",
        "categoria": "dietas",
        "data_criacao": datetime.now().isoformat(),
        "origem": "sistema",
        "editavel": True
    }
    
    # Salvar templates
    manager.save_template(exercicio_template, "exercicios")
    manager.save_template(dieta_template, "dietas")
    
    print("✅ Templates de exemplo criados com sucesso!")


if __name__ == "__main__":
    # Teste do sistema
    criar_templates_exemplo()
    
    manager = BiodeskTemplateManager()
    
    # Testar carregamento
    exercicios = manager.load_templates("exercicios")
    print(f"\n📋 Templates de exercícios carregados: {len(exercicios)}")
    
    if exercicios:
        # Testar preview
        paciente_teste = {
            'nome': 'Maria Silva',
            'data_nascimento': '15/03/1985',
            'email': 'maria@exemplo.com',
            'contacto': '964 778 426'
        }
        
        preview = manager.create_template_preview(exercicios[0], paciente_teste)
        print("\n🖼️ Preview do template:")
        print(preview)
