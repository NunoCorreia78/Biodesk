
def detectar_templates_word():
    """Detecta templates Word disponíveis"""
    
    from pathlib import Path
    import json
    from datetime import datetime
    
    templates_word = {}
    base_path = Path(r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\templates")
    
    # Pastas de templates Word
    pastas_word = [
        "orientacoes_word", "exercicios_word", "suplementos_word",
        "dietas_word", "seguimento_word", "exames_word"
    ]
    
    for pasta in pastas_word:
        pasta_path = base_path / pasta
        if pasta_path.exists():
            categoria = pasta.replace("_word", "")
            templates_word[categoria] = []
            
            # Buscar arquivos .docx
            for arquivo in pasta_path.glob("*.docx"):
                if not arquivo.name.startswith("~"):  # Ignorar arquivos temporários
                    templates_word[categoria].append({
                        "nome": arquivo.stem.replace("_", " ").title(),
                        "arquivo": str(arquivo),
                        "tipo": "word_direto"
                    })
    
    return templates_word

def processar_template_word(arquivo_word, dados_paciente):
    """Processa template Word e retorna caminho do PDF gerado"""
    
    try:
        import win32com.client
        from pathlib import Path
        
        # Criar pasta temporária para processamento
        temp_dir = Path(r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\temp_word")
        temp_dir.mkdir(exist_ok=True)
        
        # Copiar template para pasta temporária
        arquivo_original = Path(arquivo_word)
        arquivo_temp = temp_dir / f"temp_{dados_paciente.get('nome', 'paciente')}_{arquivo_original.name}"
        shutil.copy2(arquivo_original, arquivo_temp)
        
        # Converter para PDF
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        try:
            doc = word.Documents.Open(str(arquivo_temp))
            
            # Substituir placeholders básicos se existirem
            content = doc.Content.Text
            if "{{nome_paciente}}" in content:
                doc.Content.Find.Execute(
                    FindText="{{nome_paciente}}", 
                    ReplaceWith=dados_paciente.get("nome", ""),
                    Replace=2  # wdReplaceAll
                )
            
            if "{{data_hoje}}" in content:
                doc.Content.Find.Execute(
                    FindText="{{data_hoje}}", 
                    ReplaceWith=datetime.now().strftime("%d/%m/%Y"),
                    Replace=2
                )
            
            # Salvar como PDF
            pdf_path = arquivo_temp.with_suffix('.pdf')
            doc.SaveAs2(str(pdf_path), FileFormat=17)  # wdFormatPDF
            doc.Close()
            
            return str(pdf_path)
            
        finally:
            word.Quit()
            
    except Exception as e:
        print(f"Erro ao processar template Word: {e}")
        return None

def obter_email_personalizado(arquivo_word):
    """Obtém configuração de email personalizada para o template"""
    
    from pathlib import Path
    import json
    
    config_path = Path(r"c:\Users\Nuno Correia\OneDrive\Documentos\Biodesk\templates\config_templates_word.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Identificar template pelo nome do arquivo
        nome_arquivo = Path(arquivo_word).stem
        
        emails_config = config.get("emails_personalizados", {})
        
        # Buscar configuração específica
        for key, email_config in emails_config.items():
            if key in nome_arquivo.lower():
                return email_config
        
        # Configuração padrão se não encontrar específica
        return {
            "assunto": "Documento Personalizado - {{nome_paciente}}",
            "corpo": """Caro(a) {{nome_paciente}},

{{saudacao}}!

Envio em anexo o documento personalizado conforme nossa consulta de {{data_hoje}}.

Por favor, siga as orientações cuidadosamente e contacte-me para qualquer esclarecimento.

Com os melhores cumprimentos,
{{nome_profissional}}
{{nome_clinica}} - {{telefone_clinica}}

"Saúde Integral através da Medicina Natural"
""",
            "observacoes": "Email automático para template Word"
        }
        
    except Exception as e:
        print(f"Erro ao carregar configuração de email: {e}")
        return None
