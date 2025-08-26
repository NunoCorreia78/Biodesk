# 🚀 CONTEXTO PARA CONTINUAÇÃO DO CHAT - BIODESK

## 📅 **Estado Atual:** 26 Agosto 2025

### 🎯 **ÚLTIMA IMPLEMENTAÇÃO COMPLETA:**
✅ BiodeskStyles v2.0 sistema centralizado 100% funcional
✅ Backup seguro realizado no GitHub (commit: 9a2e062)
✅ 90+ botões convertidos em 16+ arquivos
✅ Templates hierárquicos organizados
✅ Hover colors harmonizados
✅ Main window com esquema verde personalizado

---

## 🏗️ **ARQUITETURA ATUAL:**

### **biodesk_styles.py** (CORE)
- Sistema centralizado com 8 tipos de botões
- Detecção automática por texto/emoji
- QSS global com seletores de alta prioridade
- Hover colors: verde #77dd77, vermelho #ff6961, amarelo #fdf9c4, cinza #cdced0

### **main_window.py** 
- Botões principais com styling individual:
  - btn_pacientes: hover #a0cf9c
  - btn_iris: hover #d6ffd2  
  - btn_terapia: hover #e4ffe1
- Sombras removidas, cantos arredondados 15px

### **templates_manager.py**
- Estrutura hierárquica implementada:
  - 🏃 Alongamentos: Cervical, Dorsal, Lombar, Membros Superiores/Inferiores
  - 💪 Exercícios: Posturais, Core, Mobilização, Respiratórios
  - 🥗 Nutrição: Anti-inflamatória, Detox, Alcalina, Mediterrânica
  - 💊 Suplementos: Complexo B, Ómega 3, Magnésio, Probióticos
  - 📋 Autocuidado: Sono, Stress, Hidratação, Rotinas
  - 📚 Educativos: Alimentação, Exercícios Casa, Prevenção
  - 🎯 Por Condição: Ansiedade, Insónia, Dores, Fadiga

### **iris_canvas.py**
- Botões otimizados: "Calibrar", "Ajustar" (antes eram "Calib: OFF/ON")
- Estados com checkmark: "✓ Calibrar", "✓ Ajustar"

---

## 🎯 **PRÓXIMAS IMPLEMENTAÇÕES PENDENTES:**

### **1. 🔒 DESATIVAR REDIMENSIONAMENTO (PRIORIDADE)**
**Problema:** Layout perde proporcionalidade ao redimensionar
**Solução:** Remover botão maximize/restore da window
```python
# Em todas as janelas principais:
self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
```
**Arquivos a modificar:**
- main_window.py
- ficha_paciente.py  
- iris_canvas.py
- terapia_quantica_window.py
- Todas as janelas que abrem

### **2. 💊 CANVAS DE PRESCRIÇÃO SUPLEMENTOS**
**Objetivo:** Substituir sub-categorias por formulário dinâmico
**Implementação:**
- Remover botões: Complexo B, Ómega 3, etc.
- Criar canvas com campos:
  - Nome do suplemento (texto livre)
  - Dosagem (dropdown + campo)
  - Frequência (1x/dia, 2x/dia, etc.)
  - Duração (semanas/meses)
  - Observações especiais
- Gerar PDF de prescrição profissional

---

## 🛠️ **COMANDOS ÚTEIS:**

### **Testar aplicação:**
```bash
cd "C:\Users\Nuno Correia\OneDrive\Documentos\Biodesk"
.\.venv\Scripts\python.exe main_window.py
```

### **Git status:**
```bash
git status
git log --oneline -5
```

---

## 📂 **ESTRUTURA DE ARQUIVOS CRÍTICOS:**

```
Biodesk/
├── biodesk_styles.py ⭐ (CORE STYLING)
├── main_window.py ⭐ (ENTRADA PRINCIPAL)
├── ficha_paciente.py ⭐ (MÓDULO PACIENTES)
├── iris_canvas.py ⭐ (ANÁLISE ÍRIS)
├── ficha_paciente/
│   ├── templates_manager.py ⭐ (TEMPLATES HIERÁRQUICOS)
│   ├── dados_pessoais.py
│   ├── declaracao_saude.py
│   ├── comunicacao_manager.py
│   └── iris_integration.py
└── biodesk_ui_kit.py (LEGACY - minimal)
```

---

## 🎨 **PALETA DE CORES ATUAL:**

### **Hover Colors:**
- 🟢 Verde (Save/Update): #77dd77
- 🔴 Vermelho (Delete): #ff6961  
- 🟡 Amarelo (Draft): #fdf9c4
- ⚪ Cinza (Tool/Default): #cdced0

### **Main Window (Especiais):**
- 🏥 Pacientes: #a0cf9c
- 👁️ Íris: #d6ffd2
- ⚛️ Terapia: #e4ffe1

---

## 🔧 **ESTADO TÉCNICO:**

### **✅ FUNCIONANDO:**
- Sistema de estilos centralizado
- Detecção automática de tipos de botão
- QSS global aplicado
- Templates hierárquicos
- Hover effects consistentes

### **⚠️ PROBLEMAS CONHECIDOS:**
- Layout não responsivo (redimensionamento)
- Algumas janelas podem ter styling inconsistente
- Suplementos precisam de canvas dedicado

---

## 🚨 **INSTRUÇÕES PARA NOVO CHAT:**

1. **Começar sempre verificando** se BiodeskStyles está a funcionar
2. **Não alterar** biodesk_styles.py sem backup
3. **Testar** cada modificação antes de continuar
4. **Fazer commit** antes de mudanças grandes
5. **Usar sempre** BiodeskStyles.create_button() para novos botões

---

## 💬 **ÚLTIMO PEDIDO DO UTILIZADOR:**
**"Desativa todos os botões de redimensionamento (aquele que fica entre o minimizar e o fechar)"**

**Implementação necessária:**
```python
self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
```

---

**🎯 PRONTO PARA CONTINUAR! Sistema estável e funcional.**
