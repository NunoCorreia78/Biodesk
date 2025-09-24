# Integração Quarkus Super Heroes com Biodesk

Este diretório contém os arquivos necessários para integrar a aplicação de demonstração Quarkus Super Heroes com o sistema Biodesk.

## 🎯 Objetivo

O Quarkus Super Heroes é uma aplicação de demonstração que mostra as capacidades do framework Quarkus em microserviços. Esta integração permite que o Biodesk utilize esses serviços como backend adicional para funcionalidades específicas.

## 📋 Pré-requisitos

### Java e Quarkus
- Java 11+ (recomendado Java 17 ou 21)
- Maven 3.8+
- Docker (para execução containerizada)
- Git

### Python (para integração com Biodesk)
- Python 3.8+
- requests
- asyncio

## 🚀 Instalação e Configuração

### 1. Instalação do Quarkus Super Heroes

```bash
# Navegar para o diretório de integração
cd quarkus_integration

# Clonar o repositório Quarkus Super Heroes
git clone https://github.com/quarkusio/quarkus-super-heroes.git

# Navegar para o diretório
cd quarkus-super-heroes

# Construir todos os microserviços
./mvnw clean package

# Ou usar Docker Compose para execução completa
docker-compose -f deploy/docker-compose/java11.yml up -d
```

### 2. Integração com Biodesk

Os seguintes serviços estarão disponíveis após a instalação:

- **Hero Service**: `http://localhost:8083` - Gestão de heróis
- **Villain Service**: `http://localhost:8084` - Gestão de vilões  
- **Fight Service**: `http://localhost:8082` - Sistema de combates
- **Statistics Service**: `http://localhost:8085` - Estatísticas em tempo real
- **Event Statistics**: `http://localhost:8086` - Eventos e métricas

## 🔧 Configuração

### Variáveis de Ambiente

Criar arquivo `.env` no diretório `quarkus_integration`:

```bash
# Quarkus Services URLs
QUARKUS_HERO_SERVICE_URL=http://localhost:8083
QUARKUS_VILLAIN_SERVICE_URL=http://localhost:8084
QUARKUS_FIGHT_SERVICE_URL=http://localhost:8082
QUARKUS_STATS_SERVICE_URL=http://localhost:8085

# Biodesk Integration
BIODESK_INTEGRATION_ENABLED=true
BIODESK_LOG_LEVEL=INFO
```

## 📡 API de Integração

A integração é feita através da classe `BiodeskQuarkusIntegration` que fornece:

- Conectividade com os microserviços Quarkus
- Mapeamento de dados entre sistemas
- Sistema de logging integrado
- Tratamento de erros e fallbacks

### Exemplo de Uso

```python
from quarkus_integration.biodesk_quarkus_client import BiodeskQuarkusIntegration

# Inicializar integração
quarkus_client = BiodeskQuarkusIntegration()

# Verificar conectividade
if quarkus_client.check_services_health():
    print("✅ Serviços Quarkus conectados")
    
    # Obter estatísticas para dashboard
    stats = quarkus_client.get_fight_statistics()
    
    # Integrar com sistema de terapia
    quarkus_client.sync_therapy_data()
```

## 🔍 Monitoramento

### Health Checks
- Verificação automática de saúde dos serviços
- Alertas em caso de falha
- Reconexão automática

### Dashboards Disponíveis
- **Hero Management**: Interface para gestão de heróis
- **Statistics**: Painel de estatísticas em tempo real
- **Fight History**: Histórico de combates

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
quarkus_integration/
├── README.md                          # Este arquivo
├── install_quarkus_heroes.py          # Script de instalação automatizada
├── biodesk_quarkus_client.py          # Cliente de integração
├── config.py                          # Configurações
├── health_monitor.py                  # Monitor de saúde dos serviços
├── quarkus-super-heroes/              # Clone do repositório (será criado)
└── examples/                          # Exemplos de uso
    ├── hero_management_example.py
    ├── statistics_integration.py
    └── therapy_sync_example.py
```

## 🚨 Solução de Problemas

### Serviços não iniciam
```bash
# Verificar se as portas estão livres
netstat -tlnp | grep -E "(8082|8083|8084|8085|8086)"

# Limpar e reconstruir
cd quarkus-super-heroes
./mvnw clean package -DskipTests
```

### Erros de conexão
- Verificar se todos os serviços estão rodando
- Checar configuração de firewall
- Validar URLs nos arquivos de configuração

### Performance lenta
- Aumentar memória JVM: `export MAVEN_OPTS="-Xmx2g"`
- Usar profile nativo: `./mvnw package -Pnative`

## 📚 Documentação Adicional

- [Quarkus Super Heroes GitHub](https://github.com/quarkusio/quarkus-super-heroes)
- [Documentação Quarkus](https://quarkus.io/guides/)
- [Biodesk Integration API](/docs/quarkus_integration_api.md)

## ⚡ Início Rápido

Para uma instalação rápida e automática:

```bash
cd /caminho/para/Biodesk/quarkus_integration
python install_quarkus_heroes.py --auto-setup
```

Este script irá:
1. Verificar pré-requisitos
2. Clonar o repositório
3. Construir os serviços
4. Configurar a integração
5. Executar testes de conectividade

---

**Desenvolvido para integração com Biodesk** 🚀