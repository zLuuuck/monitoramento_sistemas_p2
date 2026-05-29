# Backend Monitor — Documentação Técnica Completa
**Versão do código:** 4.0.0 | **Última atualização:** Maio 2026  
**Projeto:** Monitoramento de Sistemas P2 — UTP / PADS3

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Stack e Dependências](#2-stack-e-dependências)
3. [Estrutura de Diretórios](#3-estrutura-de-diretórios)
4. [Infraestrutura — Docker](#4-infraestrutura--docker)
5. [Inicialização — app/app.py](#5-inicialização--appapppy)
6. [Modelos (Models)](#6-modelos-models)
7. [Rotas (Routes)](#7-rotas-routes)
8. [Utilitários (Utils)](#8-utilitários-utils)
9. [Referência de Endpoints](#9-referência-de-endpoints)
10. [Fluxos de Dados](#10-fluxos-de-dados)
11. [Regras de Negócio e Detecção](#11-regras-de-negócio-e-detecção)
12. [Validações e Códigos de Erro](#12-validações-e-códigos-de-erro)
13. [Coerência com o Trabalho Acadêmico](#13-coerência-com-o-trabalho-acadêmico)
14. [Divergências e Observações Técnicas](#14-divergências-e-observações-técnicas)

---

## 1. Visão Geral

O Backend Monitor é uma **API REST** desenvolvida em Python/Flask que atua como núcleo do sistema de monitoramento. Ele recebe dados empurrados pelos agentes instalados nos servidores Linux monitorados, persiste tudo no PostgreSQL e expõe endpoints GET para o frontend React.

### Arquitetura de comunicação

```
[Agentes Linux]
      │
      │  HTTP POST (push — agente inicia)
      ▼
[Nginx :80]
      │
      ├─ /api/*  → backend Flask :5000
      └─ /*      → frontend React/Vite :5173

[Frontend React]
      │
      │  HTTP GET
      └─ /api/*  → backend Flask :5000
```

O backend **nunca** inicia conexão com os agentes. Toda comunicação é iniciada pelo agente (modelo push).

### Quatro funções principais

| Função | O que faz |
|--------|-----------|
| **Ingestão de Discovery** | Recebe inventário de hardware/SO na inicialização do agente |
| **Ingestão de Métricas** | Recebe snapshots de CPU/RAM/disco/rede a cada 5 segundos |
| **Ingestão de Logs** | Recebe linhas brutas do `auth.log`, aplica parsing estruturado |
| **Detecção de Segurança** | Detecta brute force SSH (≥5 falhas em 60s) e port scan (via flag do agente) |

---

## 2. Stack e Dependências

### Linguagem e framework

| Componente | Versão real (Dockerfile) |
|------------|--------------------------|
| Python | **3.12** (alpine) |
| Flask | 3.0.3 |
| Flask-CORS | 4.0.1 |
| Flask-SQLAlchemy | 3.1.1 |
| psycopg2-binary | 2.9.9 |
| python-dotenv | 1.0.1 |

> **Nota:** O PDF de capa (v4.0) menciona Python 3.13. O `Dockerfile` real usa `python:3.12-alpine`.

### Infraestrutura

| Componente | Versão / Papel |
|------------|----------------|
| PostgreSQL | 15 — banco relacional principal |
| Docker Compose | Orquestra 4 containers |
| Nginx (alpine) | Proxy reverso — roteia `/api/*` → backend, `/*` → frontend |

### Variáveis de ambiente (`.env`)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | String de conexão PostgreSQL | `postgresql://monitor:monitor@localhost:5432/monitor` |
| `FLASK_ENV` | Modo de execução | `development` |
| `FLASK_DEBUG` | Ativa hot reload | `1` |
| `PORT` | Porta do Flask | `5000` |
| `API_KEY` | Token de autenticação (presente no `.env.example`) | — |

> **Atenção:** `API_KEY` está no `.env.example` mas **não está implementado** em nenhum middleware ou rota. Os endpoints não realizam autenticação por token no código atual.

---

## 3. Estrutura de Diretórios

```
BackEnd/
├── app/
│   ├── __init__.py              # Vazio — marca app/ como pacote Python
│   ├── app.py                   # Ponto de entrada: Flask, SQLAlchemy, migrações, blueprints
│   ├── models/
│   │   ├── __init__.py          # registrar_modelos(db) — instancia e exporta todos os modelos
│   │   ├── host.py              # HostModel → tabela host
│   │   ├── agent.py             # AgentModel → tabela agents
│   │   ├── discovery.py         # HostDiscoveryModel → tabela host_discovery
│   │   ├── metric.py            # MetricModel → tabela metrics
│   │   ├── log.py               # LogEntryModel → tabela logs
│   │   ├── alert.py             # AlertModel → tabela alerts
│   │   └── connection.py        # ActiveConnectionModel → tabela active_connections
│   ├── routes/
│   │   ├── __init__.py          # Exporta register_*_routes()
│   │   ├── discovery.py         # POST/GET /api/discovery
│   │   ├── metrics.py           # POST/GET /api/metrics
│   │   ├── logs.py              # POST/GET /api/logs
│   │   ├── alerts.py            # GET /api/alerts + PATCH /api/alerts/<id>/resolve
│   │   └── connections.py       # POST /api/connections
│   └── utils/
│       ├── __init__.py          # Exporta parse_ssh_log, count_failed_logins, check_brute_force
│       ├── parsers.py           # Parsing de auth.log + count_failed_logins()
│       └── detection.py         # check_brute_force() + check_port_scan()
├── nginx/
│   └── nginx.conf               # Proxy reverso
├── requirements.txt
├── Dockerfile
├── entrypoint.sh
└── .env.example
```

### Padrão arquitetural dos modelos

Todos os modelos seguem o padrão **Wrapper + `get_model(db)`**: uma classe Python define o modelo SQLAlchemy dentro do método estático `get_model(db)`, recebendo a instância `db` por parâmetro. Isso evita importações circulares — `app.py` chama `registrar_modelos(db)` e distribui os modelos já instanciados para os blueprints via injeção de dependência.

---

## 4. Infraestrutura — Docker

### Containers (docker-compose.yml)

| Serviço | Imagem / Build | Porta exposta |
|---------|----------------|---------------|
| `postgres` | `postgres:15` | `5432:5432` |
| `backend` | `./BackEnd` (build) | `5000:5000` |
| `frontend` | `./FrontEnd` (build) | `5173:5173` |
| `nginx` | `nginx:alpine` | `80:80` |

### Detalhes relevantes

- **Hot reload do backend:** Volume `./BackEnd/app:/app/app` monta o código diretamente no container. Alterações em `.py` têm efeito imediato com `FLASK_DEBUG=1`.
- **Healthcheck do postgres:** O `entrypoint.sh` usa `nc -z postgres 5432` (netcat) em loop de 1 segundo para aguardar o banco antes de iniciar o Flask.
- **init.sql:** Montado em `/docker-entrypoint-initdb.d/` — executado automaticamente pelo PostgreSQL na **primeira inicialização** do volume. O backend **não usa** `db.create_all()`.
- **Nginx:** Lê `nginx.conf` como volume somente-leitura. Não precisa ser reconstruído para alterações de configuração.

### entrypoint.sh

```sh
#!/bin/sh
echo "Aguardando PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL está pronto!"
exec flask run --host=0.0.0.0 --port=5000
```

### Dockerfile

```dockerfile
FROM python:3.12-alpine
WORKDIR /app
RUN apk add --no-cache gcc musl-dev postgresql-dev netcat-openbsd
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
EXPOSE 5000
ENTRYPOINT ["./entrypoint.sh"]
```

---

## 5. Inicialização — app/app.py

Único arquivo que conhece e conecta todos os componentes. Executa na sequência:

1. `load_dotenv()` — carrega variáveis do `.env`
2. Cria instância `Flask` com `CORS` habilitado globalmente
3. Configura `SQLALCHEMY_DATABASE_URI` via `DATABASE_URL`
4. Inicializa `SQLAlchemy(app)`
5. Chama `registrar_modelos(db)` — instancia todos os 7 modelos
6. Executa as 5 funções de migração de schema
7. Registra os 5 blueprints de rotas

### Migrações de schema automáticas

O banco é criado pelo `init.sql` e pode ser mais antigo que o código. As funções abaixo adicionam colunas via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` na inicialização, sem exigir recriação do container.

| Função | Colunas adicionadas | Tabela |
|--------|---------------------|--------|
| `garantir_schema_discovery()` | `os_name`, `os_version`, `kernel_release`, `uptime_seconds`, `motherboard` | `host_discovery` |
| `garantir_schema_metrics()` | `memory_used_mb`, `memory_free_mb`, `memory_total_mb`, `disk_used_mb`, `disk_free_mb`, `disk_total_mb` | `metrics` |
| `garantir_schema_alerts()` | `resolved` (BOOLEAN), `resolved_at` (TIMESTAMPTZ) | `alerts` |
| `garantir_schema_alerts_message()` | `message` (TEXT) | `alerts` |
| `garantir_schema_iops()` | `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `net_sent_bytes_per_sec`, `net_recv_bytes_per_sec` | `metrics` |

### Registro de blueprints (injeção de dependência)

```python
register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel, MetricModel)
register_metric_routes(app, db, HostModel, AgentModel, MetricModel)
register_log_routes(app, db, HostModel, LogEntryModel, AlertModel)
register_alerts_routes(app, db, HostModel, AlertModel)
register_connections_routes(app, db, HostModel, ActiveConnectionModel, AlertModel, check_port_scan)
```

O blueprint de `connections` recebe `check_port_scan` por parâmetro para evitar import circular com `detection.py`.

### Endpoints gerais (definidos diretamente em app.py)

| Endpoint | Método | Resposta |
|----------|--------|----------|
| `/health` | GET | `{"status": "ok"}` — 200 |
| `/api/status` | GET | `{"status": "online", "version": "4.0.0", "timestamp": "..."}` — 200 |
| `/api/hello` | GET | `{"message": "Olá do BackEnd Flask!"}` — 200 |
| `/api/hosts` | GET | Lista de hosts com status online/offline |

#### GET /api/hosts

Parâmetro opcional: `?include_discovery=true` — inclui dados de hardware de cada host.

Retorna:
```json
{
  "hosts": [
    {
      "id": 1,
      "hostname": "servidor-linux",
      "ip_address": "192.168.1.10",
      "created_at": "2026-05-01T10:00:00",
      "last_seen": "2026-05-29T14:35:00",
      "last_metric_at": "2026-05-29T14:34:58",
      "status": "online",
      "is_online": true
    }
  ],
  "total": 1
}
```

**Regra de status online/offline:** calculado em tempo real por `_is_online()` no modelo `Host`. Um host é `"online"` se sua última métrica foi recebida há **menos de 30 segundos**.

---

## 6. Modelos (Models)

### 6.1 Host — tabela `host`

Entidade central. Todas as outras tabelas têm FK para `host.id`.

| Coluna | Tipo Python | Tipo PostgreSQL | Observação |
|--------|-------------|-----------------|------------|
| `id` | `Integer` | `INTEGER` | PK — corresponde ao `host_id` enviado pelo agente |
| `hostname` | `String(255)` | `VARCHAR(255)` | UNIQUE, NOT NULL |
| `ip_address` | `String(45)` | `VARCHAR(45)` | Atualizado a cada discovery/métrica |
| `created_at` | `DateTime` | `TIMESTAMP` | Default: `utcnow` |
| `last_seen` | `DateTime` | `TIMESTAMP` | Atualizado a cada métrica recebida |

**Relacionamentos:**
- `discovery` → `HostDiscoveryModel` (1:1, cascade delete)
- `metrics` → `MetricModel` (1:N, lazy='dynamic')
- `logs` → `LogEntryModel` (1:N, lazy='dynamic')

**Métodos:**

| Método | O que faz |
|--------|-----------|
| `to_dict()` | Serializa para JSON, inclui `status` e `is_online` calculados |
| `_is_online(last_metric_at, timeout_seconds=30)` | `True` se última métrica < 30s atrás |
| `_last_metric_at()` | Retorna `timestamp` da métrica mais recente |
| `para_dict()` | Alias de `to_dict()` |

### 6.2 Agent — tabela `agents`

Representa o processo do agente instalado. Relação 1:1 com host.

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | `Integer` PK | Corresponde ao `agent_id` gerado pelo agente |
| `host_id` | `Integer` FK | UNIQUE — um agente por host |
| `agent_version` | `String(20)` | Campo `schema_version` do payload |
| `last_checkin` | `DateTime` | Atualizado a cada discovery ou métrica |
| `status` | `String(20)` | `"active"` enquanto enviando dados |

### 6.3 HostDiscovery — tabela `host_discovery`

Inventário de hardware coletado na inicialização do agente. Relação 1:1 com host (`host_id` é a PK). Sobrescrito a cada novo discovery do mesmo host.

| Coluna | Tipo | Observação |
|--------|------|------------|
| `host_id` | `Integer` PK/FK | Chave primária também é FK para host |
| `discovery_date` | `DateTime(timezone=True)` | Data da coleta |
| `cpu_model` | `String(200)` | — |
| `cpu_cores` | `SmallInteger` | Núcleos lógicos / vCPUs |
| `cpu_clock_base_mhz` | `Integer` | — |
| `cpu_ghz` | `Numeric(4,1)` | **GENERATED ALWAYS AS** `cpu_clock_base_mhz / 1000.0` — SQLAlchemy não insere |
| `cpu_max_mhz` | `Integer` | — |
| `total_memory_gb` | `Numeric(10,2)` | — |
| `disk_total_gb` | `Numeric(10,2)` | Soma de todos os discos |
| `is_virtualized` | `Boolean` | — |
| `hypervisor` | `String(50)` | KVM, VMware, Xen, etc. |
| `memories` | `JSON` | Payload bruto de memória (JSONB no PostgreSQL) |
| `disks` | `JSON` | Payload bruto de discos |
| `networks` | `JSON` | Payload bruto de redes |
| `motherboard` | `JSON` | Payload bruto de placa-mãe |
| `os_name` | `String(200)` | Exclusivo de VM |
| `os_version` | `String(50)` | Exclusivo de VM |
| `kernel_release` | `String(200)` | Exclusivo de VM |
| `uptime_seconds` | `Integer` | Exclusivo de VM |

### 6.4 Metric — tabela `metrics`

Um novo registro é inserido a cada envio do agente (~5 segundos). O histórico completo é mantido.

| Coluna Python | Coluna no banco | Tipo | Observação |
|---------------|-----------------|------|------------|
| `id` | `id` | `Integer` PK | — |
| `host_id` | `host_id` | `Integer` FK | NOT NULL |
| `timestamp` | `timestamp` | `DateTime` | NOT NULL |
| `cpu_percent` | `cpu_percent` | `Float` | 0–100 |
| `memory_percent` | `memory_percent` | `Float` | — |
| `memory_used_mb` | `memory_used_mb` | `Integer` | — |
| `memory_free_mb` | `memory_free_mb` | `Integer` | — |
| `memory_total_mb` | `memory_total_mb` | `Integer` | — |
| `disk_percent` | `disk_percent` | `Float` | — |
| `disk_used_mb` | `disk_used_mb` | `BigInteger` | — |
| `disk_free_mb` | `disk_free_mb` | `BigInteger` | — |
| `disk_total_mb` | `disk_total_mb` | `BigInteger` | — |
| `net_sent` | `net_sent_bytes` | `BigInteger` | Contador acumulado desde o boot |
| `net_recv` | `net_recv_bytes` | `BigInteger` | Contador acumulado desde o boot |
| `disk_read_iops` | `read_iops` | `Float` | Delta calculado pelo agente |
| `disk_write_iops` | `write_iops` | `Float` | Delta calculado pelo agente |
| `disk_read_bytes_per_sec` | `read_bytes_per_sec` | `Float` | Taxa de leitura |
| `disk_write_bytes_per_sec` | `write_bytes_per_sec` | `Float` | Taxa de escrita |
| `net_sent_per_sec` | `net_sent_bytes_per_sec` | `Float` | Taxa de envio de rede |
| `net_recv_per_sec` | `net_recv_bytes_per_sec` | `Float` | Taxa de recepção de rede |

> **Atenção:** Os nomes dos atributos Python diferem dos nomes das colunas no banco para vários campos. O SQLAlchemy mapeia via `db.Column('nome_no_banco', ...)`.

### 6.5 LogEntry — tabela `logs`

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | `BigInteger` PK | — |
| `host_id` | `Integer` FK | NOT NULL |
| `timestamp` | `DateTime` | Default: `utcnow` |
| `log_type` | `String(50)` | `"auth"` ou `"system"` (padrão) |
| `raw_line` | `Text` | Linha bruta exatamente como chegou do agente, NOT NULL |
| `parsed_data` | `JSON` | Resultado do parsing (JSONB no banco). NULL se não reconhecido |

`parsed_data` quando preenchido contém pelo menos: `event_type`, `status`, `usuario`, `ip_origem`. Campos adicionais variam por tipo de evento.

### 6.6 Alert — tabela `alerts`

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | `BigInteger` PK | BIGSERIAL — gerado pelo banco |
| `host_id` | `Integer` FK | NOT NULL |
| `alert_type` | `String(50)` | `"brute_force"` ou `"port_scan"` |
| `source_ip` | `String(45)` | IP de origem do ataque |
| `timestamp` | `DateTime` | Default: `utcnow` |
| `severity` | `String(20)` | `"low"`, `"medium"`, `"high"`, `"critical"`. Default: `"medium"` |
| `metodos` | `String(20)` | `"password"` para brute force; `null` para port scan |
| `message` | `Text` | Descrição legível. Ex: `"Força bruta SSH: 8 tentativas em 60s de 10.0.0.5"` |
| `resolved` | `Boolean` | `False` = ativo; `True` = resolvido. Default: `False` |
| `resolved_at` | `DateTime` | Momento da resolução, nullable |

> `resolved` e `resolved_at` não estavam no `init.sql` original — são adicionados por `garantir_schema_alerts()`.

### 6.7 ActiveConnection — tabela `active_connections`

| Coluna no banco | Atributo Python | Tipo | Origem no payload do agente |
|-----------------|-----------------|------|------------------------------|
| `id` | `id` | `BigInteger` PK | — |
| `host_id` | `host_id` | `Integer` FK | `global.host_id` |
| `timestamp` | `timestamp` | `DateTime(timezone=True)` | `timestamp` do payload |
| `src_ip` | `src_ip` | `String(45)` | `connections[].remote_ip` |
| `src_port` | `src_port` | `Integer` | `connections[].remote_port` |
| `dst_ip` | `dst_ip` | `String(45)` | `global.primary_ip` |
| `dst_port` | `dst_port` | `Integer` | `connections[].local_port` |
| `protocol` | `protocol` | `String(10)` | Fixo: `"tcp"` |
| `status` | `status` | `String(20)` | `connections[].state` |
| `duration_sec` | `duration_sec` | `Integer` | `connections[].duration_sec` (opcional) |

---

## 7. Rotas (Routes)

Cada arquivo cria um Blueprint Flask e expõe uma função `register_*_routes()` chamada por `app.py`. Os modelos são **injetados por parâmetro** — nenhum blueprint importa modelos diretamente.

> **Exceção:** `connections.py` cria o Blueprint como variável de módulo (`connections_bp = Blueprint(...)`) em vez de dentro da função factory, diferente dos demais blueprints.

### 7.1 discovery.py

#### POST /api/discovery

Recebe e persiste o inventário de hardware do agente. Compatível com dois formatos de payload.

**Validações:**
- `Content-Type: application/json` obrigatório (retorna 400 se payload ausente)
- Campo `type` ou `collection_type` aceito na raiz ou em `global.collection_type`. Se presente, deve ser `"discovery"` (retorna 400 caso contrário)

**Fluxo de execução:**

1. `_extract_discovery_fields(dados, remote_addr)` — normaliza os dois formatos em um dict padronizado
2. Busca host existente por `ip_address`, `hostname` ou `host_id` (OR). Se não encontrar, cria novo
3. `_upsert_agent()` — cria ou atualiza registro na tabela `agents`
4. Cria ou sobrescreve registro em `host_discovery` (1:1 por `host_id`)
5. Retorna 201 com `host_id`, `agent_id`, `hostname`, `ip_host`, `is_virtualized`

**Formatos de payload suportados:**

*Máquina física (Linux Mint):*
```json
{
  "type": "discovery",
  "environment": { "is_virtualized": false, "hypervisor": null },
  "cpu": {
    "model_name": "Intel Core i5-4690",
    "cores_logical": 4,
    "frequency": { "base_mhz": null, "max_mhz": 3900.0 }
  },
  "memory": { "total_mb": 11895.33 },
  "disk": {
    "disks": [{ "size": { "bytes": 1000204886016, "gb": 931.51 } }]
  }
}
```

*VM (Ubuntu 24.04 em VMware):*
```json
{
  "type": "discovery",
  "global": { "host_id": "71203", "primary_ip": "192.168.48.129" },
  "environment": { "is_virtualized": true, "hypervisor": "VMware" },
  "system": {
    "hostname": "teste-ubuntu",
    "os": { "name": "Ubuntu", "pretty_name": "Ubuntu 24.04.4 LTS", "version_id": "24.04" },
    "kernel": { "release": "6.8.0-110-generic" },
    "uptime_seconds": 808
  },
  "cpu": {
    "model_name": "AMD Ryzen 5 7520U",
    "topology": { "vcpus": 2 },
    "frequency": { "base_mhz": { "value": null }, "max_mhz": { "value": 2794.546 } }
  },
  "memory": { "total": { "bytes": 2013175808, "gb": 1.87 } },
  "disk": { "disks": [{ "device": "/dev/sda", "size": { "bytes": 32212254720, "gb": 30.0 } }] },
  "network": {
    "default_gateway": { "interface": "ens33" },
    "interfaces": [{ "name": "ens33", "ipv4": [{ "address": "192.168.48.129" }] }]
  }
}
```

**Helpers de extração (funções privadas):**

| Função | Responsabilidade |
|--------|-----------------|
| `_extract_discovery_fields(dados, remote_addr)` | Orquestrador — retorna dict padronizado compatível com ambos os formatos |
| `_get_cpu_freq(cpu, field, fallback)` | Extrai frequência como valor direto (físico) ou `{value: N}` (VM) |
| `_get_primary_ip_from_network(network)` | Extrai IP da interface padrão (payload VM) |
| `_get_disk_total_gb(dados)` | Soma o tamanho de todos os discos listados |
| `_upsert_agent(db, AgentModel, host_id, campos)` | Cria ou atualiza agente; prioridade: `agent_id` → por `host_id` → novo |
| `_get_nested(source, *keys, fallback)` | Acessa chaves aninhadas sem `KeyError` |
| `_safe_int(value)` | Converte para int com fallback `None` |
| `_bytes_to_gb(value)` | Converte bytes para GB |
| `_get_value(source, key, fallback)` | `dict.get()` com fallback seguro |
| `_is_host_online(last_seen, timeout_seconds=30)` | Calcula online/offline |
| `_latest_metric_at(MetricModel, host_id)` | Retorna timestamp da métrica mais recente |
| `_discovery_to_response(discovery, MetricModel)` | Monta resposta enriquecida com status do host |

**Resolução de hostname e IP:**

```
ip_address = agent.primary_ip
          ?? global.primary_ip
          ?? dados.primary_ip
          ?? _get_primary_ip_from_network(network)
          ?? request.remote_addr
          ?? '0.0.0.0'

hostname   = agent.hostname
          ?? global.hostname
          ?? system.hostname
          ?? dados.hostname
          ?? f'host-{ip_address.replace(".", "-")}'
```

#### GET /api/discovery

Retorna dados de discovery para o frontend.

Parâmetro opcional: `?host_id=N` — filtra por host específico.

Resposta: lista de discoveries, cada um enriquecido com `host` (id, hostname, ip, status online/offline calculado).

---

### 7.2 metrics.py

#### POST /api/metrics

Persiste um snapshot de métricas a cada envio do agente.

**Validações:**
- Payload JSON obrigatório (400 se ausente)
- Campo `timestamp` obrigatório (400 se ausente)
- Host deve ser identificável por `host_id`, `hostname` ou `ip_address` (400 se impossível)

**Fluxo:**

1. `_normalize_metrics_payload(dados, remote_addr)` — extrai e normaliza todos os campos
2. `_resolve_host(db, HostModel, AgentModel, normalized)` — busca ou cria host
3. Cria `MetricModel`, atualiza `host.last_seen` e `agent.last_checkin`
4. Retorna 201 com `metric_id`, `host_id`, `timestamp`

**Normalização do payload (`_normalize_metrics_payload`):**

Compatível com dois formatos:
- Estrutura `global/data` (payload padrão do agente): `dados.data.cpu.percent`, `dados.data.memory.total`, etc.
- Flat (legacy): `dados.cpu_percent`, `dados.memory_used_bytes`, etc.

Conversões aplicadas:
- `memory.total` (bytes) → `memory_total_mb` (`/ 1024²`)
- `memory.used` (bytes) → `memory_used_mb`
- `memory_free_mb` = `memory_total_mb - memory_used_mb` (calculado pelo backend)
- `disk.total` (bytes) → `disk_total_mb`
- `disk.used` (bytes) → `disk_used_mb`
- `disk_free_mb` = `disk_total_mb - disk_used_mb`
- Timestamp: aceita ISO 8601 (string) ou Unix timestamp (int/float)

**Resolução de host (`_resolve_host`):**

Tenta localizar por `host_id` OR `hostname` OR `ip_address`. Se não encontrar e `hostname` existir, cria novo host e agente. Se impossível identificar, retorna `None` (400).

#### GET /api/metrics

Parâmetros:
- `host_id` (obrigatório) — retorna 400 se ausente, 404 se host não existe
- `limit` (padrão 20, máximo 100)
- `offset` (padrão 0)

Retorna métricas em **ordem cronológica crescente** (query DESC invertida para consistência de gráficos). Inclui `is_online`, `status`, `last_metric_at`, `total` (sem paginação).

---

### 7.3 logs.py

#### POST /api/logs

Recebe uma linha de log por requisição, persiste e detecta brute force.

**Validações:**
- `host_id` obrigatório na raiz ou em `global.host_id` (400 se ausente)
- `host_id` deve ser numérico (400 se string inválida)
- `timestamp` obrigatório (400 se ausente)
- `raw_line` obrigatório e não pode ser vazio/whitespace (400)
- Host deve existir no banco (404)

**Timestamp aceito:**
- ISO 8601 string: `"2026-05-19T14:35:00Z"` ou `"2026-05-19T14:35:00+00:00"`
- Unix timestamp (int ou float): `1716126900`

**Fluxo:**

1. Valida todos os campos obrigatórios
2. Se `log_type == "auth"`: chama `parse_auth_log(raw_line)` — retorna `parsed_data` ou `None`
3. Persiste `LogEntryModel` com `parsed_data` preenchido ou `null`
4. **Após o commit:** se `log_type == "auth"` e `parsed_data.status == "failed"` e `ip_origem` presente → chama `check_brute_force()`
5. Retorna 201 com `log_id`, `host_id`, `log_type`, `parsed` (bool), `event_type`, `alerta_criado` (bool)

> `check_brute_force()` é chamado **após** o `db.session.commit()` para garantir que a falha recém-salva já seja contabilizada na query de contagem da janela de 60 segundos.

**Payload esperado:**
```json
{
  "host_id": 1,
  "timestamp": "2026-05-19T14:35:00Z",
  "log_type": "auth",
  "raw_line": "May 19 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100 port 22 ssh2"
}
```

`log_type` padrão: `"system"` quando não informado.

#### GET /api/logs

Parâmetros:
- `host_id` (obrigatório)
- `limit` (padrão 20, máximo 100)
- `offset` (padrão 0)
- `log_type` (opcional — ex: `"auth"`)

Ordena do mais recente para o mais antigo (aproveita índice `idx_logs_host_ts`). Retorna `total` sem paginação para o frontend calcular páginas.

---

### 7.4 alerts.py

#### GET /api/alerts

Parâmetros:
- `status` (padrão `"active"`) — `"active"` | `"resolved"` | `"all"`. Retorna 400 para valores inválidos
- `host_id` (opcional) — verifica existência do host (404 se não encontrado)
- `limit` (padrão 20, máximo 100)
- `offset` (padrão 0)

Retorna `total` antes da paginação, `status`, `limit`, `offset`.

**Exemplo de resposta:**
```json
{
  "alerts": [
    {
      "id": 1,
      "host_id": 2,
      "alert_type": "brute_force",
      "source_ip": "192.168.1.100",
      "timestamp": "2026-05-21T03:14:00",
      "severity": "high",
      "metodos": "password",
      "message": "Força bruta SSH: 7 tentativas em 60s de 192.168.1.100",
      "resolved": false,
      "resolved_at": null
    }
  ],
  "total": 1,
  "status": "active",
  "limit": 20,
  "offset": 0
}
```

#### PATCH /api/alerts/\<id\>/resolve

Marca um alerta como resolvido.

- **200 OK** — retorna alerta atualizado com `resolved=true` e `resolved_at` preenchido
- **404 Not Found** — alerta não existe
- **400 Bad Request** — alerta já estava resolvido (retorna `resolved_at` do momento anterior)

Sem body na requisição — apenas o `id` na URL.

---

### 7.5 connections.py

#### POST /api/connections

Recebe conexões TCP ativas coletadas pelo agente via `ss`/`netstat`.

**Campos obrigatórios:**
- `global.host_id` (400 se ausente ou não numérico)

**Campos opcionais:**
- `global.primary_ip` — IP do host monitorado (usado como `dst_ip`)
- `timestamp` — aceita ISO 8601; fallback: `datetime.now(timezone.utc)`
- `connections[]` — lista de conexões TCP
- `scan_sources` — dict `{ip_atacante: qtd_portas}` enviado pelo agente
- `port_scan_detected` — bool; default: `bool(scan_sources)`

**Mapeamento connections[] → active_connections:**

| Campo no payload | Campo no banco | Observação |
|-----------------|----------------|------------|
| `remote_ip` | `src_ip` | IP remoto que iniciou a conexão |
| `remote_port` | `src_port` | Porta efêmera do lado remoto |
| `local_port` | `dst_port` | Porta do serviço no host (ex: 22 = SSH) |
| `state` | `status` | Estado TCP: ESTABLISHED, TIME_WAIT, etc. |
| `duration_sec` | `duration_sec` | Opcional |
| `global.primary_ip` | `dst_ip` | IP do próprio host monitorado |
| fixo: `"tcp"` | `protocol` | Sempre TCP nesta versão |

**Fluxo:**

1. Valida e extrai campos globais
2. Persiste cada conexão em `active_connections` em lote (commit único)
3. Se `port_scan_detected == True`:
   - **Com `scan_sources`:** itera sobre IPs atacantes e chama `check_port_scan()` por IP
   - **Sem `scan_sources` (fallback):** usa frequência de `remote_ip` nas conexões para identificar o IP mais frequente como atacante
4. Retorna 201 com `total_salvo`, `port_scan_flag`, `scan_sources`, `alertas_criados`

**Resposta:**
```json
{
  "mensagem": "Conexões recebidas com sucesso",
  "host_id": 1,
  "total_salvo": 5,
  "port_scan_flag": true,
  "scan_sources": { "10.0.0.5": 47 },
  "alertas_criados": 1
}
```

---

## 8. Utilitários (Utils)

### 8.1 parsers.py

Contém os parsers de linhas do `/var/log/auth.log` e a função de contagem de falhas.

#### parse_auth_log(raw_line) — Orquestrador principal

Ponto de entrada usado por `logs.py`. Tenta cada parser na ordem de especificidade e retorna o primeiro resultado não-`None`. Falhas em parsers individuais são isoladas (não propagam para os próximos).

**Ordem dos parsers (`_PARSERS`):**

| # | Função | Eventos reconhecidos |
|---|--------|---------------------|
| 1 | `parse_ssh_log()` | `Failed password` / `Accepted password` — login SSH |
| 2 | `parse_sudo()` | Execução de comando via `sudo` |
| 3 | `parse_pam_auth_failure()` | `pam_unix(...): authentication failure` |
| 4 | `parse_ssh_disconnect()` | `Disconnected from user` / `Received disconnect` |
| 5 | `parse_pam_session()` | `session opened/closed` (sshd, sudo, CRON) |
| 6 | `parse_logind_session()` | `New session` / `Removed session` (systemd-logind) |

#### parse_ssh_log(raw_line) → dict | None

**Regex:** `(Failed password|Accepted password)\s+for\s+(?:invalid user\s+)?(\S+)\s+from\s+((?:\d{1,3}\.){3}\d{1,3})`

**Retorna:**
```json
{
  "event_type": "ssh_login",
  "status": "failed",
  "usuario": "root",
  "ip_origem": "192.168.1.100"
}
```

Campos `status` (`"failed"` / `"accepted"`) e `ip_origem` são usados pelos índices JSONB do banco e pela detecção de brute force.

#### parse_sudo(raw_line) → dict | None

**Regex:** `sudo:\s+(\S+)\s+:\s+TTY=\S+\s+;\s+PWD=(\S+)\s+;\s+USER=(\S+)\s+;\s+COMMAND=(.+)$`

**Retorna:**
```json
{
  "event_type": "sudo",
  "status": "sudo_exec",
  "usuario": "teste",
  "ip_origem": null,
  "usuario_alvo": "root",
  "comando": "/usr/bin/systemctl status linux-agent",
  "diretorio": "/home/teste"
}
```

#### parse_pam_auth_failure(raw_line) → dict | None

**Retorna:**
```json
{
  "event_type": "pam_auth_failure",
  "status": "failed",
  "usuario": "root",
  "ip_origem": "10.81.243.81",
  "servico": "sshd:auth"
}
```

#### parse_ssh_disconnect(raw_line) → dict | None

Reconhece dois padrões:
- `Disconnected from user <usuario> <ip>` → inclui `usuario` e `ip_origem`
- `Received disconnect from <ip>` → inclui apenas `ip_origem`

**Retorna:**
```json
{
  "event_type": "ssh_disconnect",
  "status": "session_close",
  "usuario": "teste",
  "ip_origem": "10.81.243.81"
}
```

#### parse_pam_session(raw_line) → dict | None

Reconhece `pam_unix(...): session opened/closed`. Diferencia `cron_session`, `sudo_session` e `pam_session` pelo nome do serviço PAM.

**Retorna:**
```json
{
  "event_type": "pam_session",
  "status": "session_open",
  "usuario": "teste",
  "ip_origem": null,
  "servico": "sshd:session"
}
```

#### parse_logind_session(raw_line) → dict | None

Reconhece `systemd-logind[...]: New session N of user X` e `Removed session N`.

**Retorna:**
```json
{
  "event_type": "logind_session",
  "status": "session_open",
  "usuario": "teste",
  "ip_origem": null,
  "session_id": "20"
}
```

#### count_failed_logins(LogEntryModel, host_id, ip_origem, janela_horas=1) → int

Conta tentativas de login SSH com falha de um IP dentro de uma janela de tempo.

Usa operadores JSONB nativos do PostgreSQL (`->>`), aproveitando os índices parciais criados pelo `init.sql`.

**SQL equivalente:**
```sql
SELECT COUNT(*) FROM logs
WHERE host_id       = :host_id
  AND log_type      = 'auth'
  AND timestamp    >= :inicio_janela
  AND parsed_data->>'status'    = 'failed'
  AND parsed_data->>'ip_origem' = :ip_origem
```

> **Vulnerabilidade identificada:** A query usa interpolação de string direta: `sa_text(f"parsed_data->>'ip_origem' = '{ip_origem}'")`. Isso é uma **vulnerabilidade de SQL injection** se `ip_origem` vier de input não sanitizado. O campo vem do parsing de logs, então na prática é extraído por regex e tem formato IPv4 — mas o risco existe.

Retorna `0` em caso de qualquer exceção (falha silenciosa) para não interromper o fluxo de logs.

---

### 8.2 detection.py

#### check_brute_force(db, LogEntryModel, AlertModel, host_id, ip_origem) → bool

**Constantes:**
- `LIMIAR_BRUTE_FORCE = 5` — mínimo de falhas para disparar alerta
- `JANELA_HORAS = 1/60` — janela de 60 segundos

**Fluxo:**

1. Chama `count_failed_logins()` com `janela_horas=1/60`
2. Se `total_falhas < 5`: retorna `False`
3. Consulta se já existe alerta ativo (`resolved=False`) para `host_id + source_ip + "brute_force"` — evita duplicatas
4. Se já existe: retorna `False`
5. Cria `AlertModel` com `severity="high"`, `metodos="password"`, `message="Força bruta SSH: N tentativas em 60s de IP"`
6. `db.session.add()` + `db.session.commit()`
7. Retorna `True`

Em caso de exceção interna: `rollback` silencioso, retorna `False`. Nunca interrompe o salvamento do log.

#### check_port_scan(db, AlertModel, host_id, ip_origem, port_count=0) → bool

O agente usa `tcpdump` para detectar SYN entrantes e envia `port_scan_detected=true` com `scan_sources`. O backend apenas persiste o alerta.

**Fluxo:**

1. Consulta se já existe alerta ativo de `port_scan` para `host_id + ip_origem` — evita duplicatas
2. Gera mensagem:
   - Com `port_count`: `"Varredura de portas: N portas distintas em 60s de IP"`
   - Sem: `"Varredura de portas detectada de IP"`
3. Cria `AlertModel` com `severity="high"`, `metodos=None`
4. Retorna `True` se criado, `False` caso contrário

Falha silenciosa — nunca interrompe o salvamento das conexões.

---

## 9. Referência de Endpoints

| Endpoint | Método | Quem chama | Descrição |
|----------|--------|------------|-----------|
| `/health` | GET | Docker healthcheck | Retorna `{"status": "ok"}` — 200 |
| `/api/status` | GET | Monitoramento | Versão e timestamp da API |
| `/api/hello` | GET | Teste | Endpoint de verificação básica |
| `/api/hosts` | GET | Frontend | Lista hosts com status online/offline |
| `/api/discovery` | POST | Agente | Recebe inventário de hardware |
| `/api/discovery` | GET | Frontend | Retorna dados de hardware |
| `/api/metrics` | POST | Agente | Recebe snapshot de métricas (a cada 5s) |
| `/api/metrics` | GET | Frontend | Consulta métricas com paginação |
| `/api/logs` | POST | Agente | Recebe linha do auth.log + parsing + detecção |
| `/api/logs` | GET | Frontend | Consulta logs com filtro e paginação |
| `/api/alerts` | GET | Frontend | Lista alertas de segurança |
| `/api/alerts/<id>/resolve` | PATCH | Frontend | Marca alerta como resolvido |
| `/api/connections` | POST | Agente | Recebe conexões TCP + detecta port scan |

### Campos de identificação do host nos payloads do agente

Os campos chegam em `global.host_id` e `global.primary_ip`. O backend localiza o host por:
1. `host_id` (prioridade)
2. `hostname`
3. `ip_address`

Se nenhum localizar, cria novo host (exceto em `/api/logs`, que retorna 404).

---

## 10. Fluxos de Dados

### 10.1 Discovery (inicialização do agente)

```
Agente → POST /api/discovery
                │
                ├─ _extract_discovery_fields()  ← normaliza payload físico/VM
                │
                ├─ Busca host (ip OR hostname OR id)
                │   └─ Não existe → cria HostModel
                │
                ├─ _upsert_agent()  ← cria ou atualiza AgentModel
                │
                ├─ Cria ou sobrescreve HostDiscoveryModel
                │
                └─ 201 Created { host_id, agent_id, hostname, is_virtualized }
```

### 10.2 Métricas (a cada ~5 segundos)

```
Agente → POST /api/metrics
                │
                ├─ _normalize_metrics_payload()  ← bytes→MB, calcula free
                │
                ├─ _resolve_host()  ← busca ou cria host + agente
                │
                ├─ INSERT MetricModel
                ├─ UPDATE host.last_seen = now()
                ├─ UPDATE agent.last_checkin = now()
                │
                └─ 201 Created { metric_id, host_id, timestamp }
```

### 10.3 Logs + Detecção de Brute Force

```
Agente → POST /api/logs
                │
                ├─ Valida host_id, timestamp, raw_line
                │
                ├─ [se log_type == "auth"]
                │   └─ parse_auth_log(raw_line)
                │       ├─ parse_ssh_log()        ← tenta primeiro
                │       ├─ parse_sudo()
                │       ├─ parse_pam_auth_failure()
                │       ├─ parse_ssh_disconnect()
                │       ├─ parse_pam_session()
                │       └─ parse_logind_session()
                │
                ├─ INSERT LogEntryModel { parsed_data }
                ├─ db.session.commit()
                │
                ├─ [se status == "failed" e ip_origem presente]
                │   └─ check_brute_force(host_id, ip_origem)
                │       ├─ count_failed_logins(60s) → N falhas
                │       ├─ [N < 5] → retorna False
                │       ├─ [alerta ativo existente] → retorna False
                │       └─ INSERT AlertModel { brute_force, high } → True
                │
                └─ 201 Created { log_id, parsed, event_type, alerta_criado }
```

### 10.4 Conexões TCP + Detecção de Port Scan

```
Agente → POST /api/connections
                │
                ├─ Valida global.host_id
                │
                ├─ INSERT ActiveConnectionModel (em lote, por conexão)
                ├─ db.session.commit()
                │
                ├─ [se port_scan_detected == true]
                │   ├─ [com scan_sources] → itera IPs atacantes
                │   │   └─ check_port_scan(host_id, ip_atacante, port_count)
                │   │       ├─ [alerta ativo existente] → False
                │   │       └─ INSERT AlertModel { port_scan, high } → True
                │   │
                │   └─ [sem scan_sources — fallback]
                │       └─ Counter(remote_ip) → IP mais frequente
                │           └─ check_port_scan(host_id, ip_mais_frequente, 0)
                │
                └─ 201 Created { total_salvo, port_scan_flag, alertas_criados }
```

---

## 11. Regras de Negócio e Detecção

### 11.1 Status Online/Offline

- **Online:** última métrica recebida há **menos de 30 segundos**
- **Offline:** sem métricas nos últimos 30 segundos ou nenhuma métrica registrada
- Calculado em tempo real a cada chamada a `to_dict()` ou `_is_online()` — não é persistido no banco

### 11.2 Detecção de Brute Force SSH

- **Limiar:** ≥ 5 falhas de login SSH do mesmo IP em 60 segundos
- **Janela:** `JANELA_HORAS = 1/60` (60 segundos)
- **Deduplicação:** apenas um alerta ativo por combinação `host_id + source_ip + "brute_force"`. Enquanto o alerta existir como `resolved=False`, novos eventos não geram duplicatas
- **Severidade:** sempre `"high"`, método: `"password"`
- **Falha silenciosa:** exceções internas não interrompem o salvamento do log

### 11.3 Detecção de Port Scan

- **Responsável pela análise:** o agente (via `tcpdump`, SYN tracking)
- **Papel do backend:** apenas persiste o alerta quando `port_scan_detected=true`
- **Fonte dos IPs:** `scan_sources` (dict `{ip: qtd_portas}`) enviado pelo agente. Fallback: IP mais frequente em `connections[].remote_ip`
- **Deduplicação:** um alerta ativo por `host_id + source_ip + "port_scan"`
- **Severidade:** sempre `"high"`, método: `null`

### 11.4 Resolução de Alertas

- Operador aciona `PATCH /api/alerts/<id>/resolve` manualmente pelo frontend
- Define `resolved=True` e `resolved_at=datetime.utcnow()`
- Após resolução, nova detecção do mesmo IP **pode** gerar novo alerta (deduplicação só bloqueia enquanto `resolved=False`)

### 11.5 Deduplicação de Host

- Busca por OR: `ip_address = X OR hostname = Y OR id = Z`
- Se encontrar qualquer um: atualiza campos (não cria duplicata)
- Se não encontrar: cria novo host

### 11.6 Upsert de Discovery

- `host_discovery` tem relação 1:1 com `host` (`host_id` é PK)
- A cada novo discovery do mesmo host: sobrescreve todos os campos (não histórico)

---

## 12. Validações e Códigos de Erro

### Códigos retornados

| Código | Situação |
|--------|----------|
| `200 OK` | Consulta bem-sucedida (GET, PATCH /resolve) |
| `201 Created` | Dado persistido com sucesso (POST) |
| `400 Bad Request` | Campo obrigatório ausente, tipo inválido, alerta já resolvido, status inválido |
| `404 Not Found` | Host ou alerta não encontrado |
| `500 Internal Server Error` | Exceção não tratada (com `db.session.rollback()`) |

### Validações por endpoint

| Endpoint | Campo | Validação |
|----------|-------|-----------|
| `POST /api/logs` | `host_id` | Obrigatório (raiz ou `global.host_id`), deve ser numérico |
| `POST /api/logs` | `timestamp` | Obrigatório, aceita ISO 8601 ou Unix timestamp |
| `POST /api/logs` | `raw_line` | Obrigatório, não pode ser vazio ou só whitespace |
| `POST /api/logs` | host | Deve existir no banco (404) |
| `GET /api/metrics` | `host_id` | Obrigatório, deve ser numérico, host deve existir |
| `GET /api/logs` | `host_id` | Obrigatório, deve ser numérico, host deve existir |
| `GET /api/alerts` | `status` | Deve ser `"active"`, `"resolved"` ou `"all"` |
| `POST /api/connections` | `global.host_id` | Obrigatório, deve ser numérico |
| `PATCH /api/alerts/<id>/resolve` | alerta | Deve existir (404); se já resolvido retorna 400 |

### Tratamento de erros

Todos os blueprints usam `try/except` global que faz `db.session.rollback()` e retorna 500 com a mensagem de erro. A detecção de brute force e port scan são **sempre silenciosas** — nunca propagam erros para o endpoint chamador.

---

## 13. Coerência com o Trabalho Acadêmico

O trabalho acadêmico (Trabalho.pdf) propõe as seguintes funcionalidades. Status de implementação:

| Funcionalidade proposta | Status no código |
|------------------------|------------------|
| Arquitetura cliente-servidor com agentes push | ✅ Implementado |
| Coleta de métricas de CPU, memória, disco, rede | ✅ Implementado |
| Coleta de inventário de hardware (discovery) | ✅ Implementado |
| Análise de logs (auth.log) | ✅ Implementado |
| Detecção de brute force SSH (≥5 falhas/60s) | ✅ Implementado |
| Detecção de port scan | ✅ Implementado (via flag do agente) |
| PostgreSQL com JSONB | ✅ Implementado |
| Docker Compose com 4 serviços | ✅ Implementado |
| Nginx como proxy reverso | ✅ Implementado |
| Dashboard web para visualização | ✅ Implementado no frontend (fora deste doc) |
| Autenticação por token estático (API_KEY) | ❌ **Não implementado** — presente no `.env.example` mas sem middleware |
| Política de retenção de dados de 7 dias | ❌ **Não implementado** — mencionado no trabalho, sem implementação no backend |

---

## 14. Divergências e Observações Técnicas

### 14.1 Diferenças em relação ao PDF de documentação (v4.0)

| Item | PDF v4.0 | Código real |
|------|----------|-------------|
| Versão Python | 3.13 | **3.12** (Dockerfile: `python:3.12-alpine`) |
| Entrypoint | Não documentado | `entrypoint.sh` com netcat para aguardar postgres |
| Blueprint `connections` | Factory pattern (como os outros) | Blueprint criado como variável de módulo no topo do arquivo |
| `to_dict()` de `Metric` | Documenta `net_sent`/`net_recv` | Campo Python é `net_sent` mas coluna no banco é `net_sent_bytes` |

### 14.2 Vulnerabilidade de SQL Injection

Em `app/utils/parsers.py`, função `count_failed_logins()`, linha 446:

```python
sa_text(f"parsed_data->>'ip_origem' = '{ip_origem}'"),
```

`ip_origem` é interpolado diretamente na string SQL. Na prática o risco é baixo porque `ip_origem` é extraído por regex que aceita apenas IPv4 (`(?:\d{1,3}\.){3}\d{1,3}`), mas a forma correta é usar parâmetros vinculados:

```python
sa_text("parsed_data->>'ip_origem' = :ip").bindparams(ip=ip_origem)
```

### 14.3 Autenticação ausente

O `.env.example` documenta `API_KEY` e o Trabalho menciona "validação por token estático". No código atual **nenhum** endpoint exige autenticação. Qualquer cliente na rede pode enviar dados ou ler todos os alertas/logs/métricas.

### 14.4 Nomes de atributos Python vs colunas do banco (Metric)

O `MetricModel` usa aliases para vários campos. Exemplo:

```python
net_sent = db.Column('net_sent_bytes', db.BigInteger, ...)  # Python: .net_sent | banco: net_sent_bytes
disk_read_iops = db.Column('read_iops', db.Float, ...)      # Python: .disk_read_iops | banco: read_iops
```

O `to_dict()` usa os nomes Python (`net_sent`, `disk_read_iops`, etc.), não os nomes das colunas. O frontend precisa conhecer esses nomes.

### 14.5 Política de retenção de dados

O Trabalho acadêmico menciona política de retenção de 7 dias para mitigar o crescimento do banco. Essa funcionalidade **não está implementada** no backend. A tabela `metrics` cresce indefinidamente (~17280 registros por host por dia com intervalo de 5 segundos).

### 14.6 request em função helper de metrics.py

Em `_normalize_metrics_payload()`, há uma referência a `request.args.get('host_id')` (linha 153). Essa função é chamada dentro de uma rota Flask, então o contexto de request está disponível via proxy do Flask — funciona corretamente, mas `request` não é passado como parâmetro explicitamente, o que pode dificultar testes unitários.

---

*Documentação gerada com base na leitura direta do código-fonte em 29/05/2026.*
