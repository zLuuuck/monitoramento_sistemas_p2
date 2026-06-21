# Backend Monitor — Documentação Técnica Completa
**Versão do código:** 6.0.0 | **Última atualização:** Junho 2026  
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
      │  X-API-Key: {API_KEY}
      ▼
[Nginx :80]
      │  roteia por server_name (virtual host), não por path
      ├─ api.monitoramento.lan     → backend Flask :5000
      └─ painel.monitoramento.lan  → frontend Vite :5173

[Frontend React]
      │
      │  HTTP GET  (com API key em localStorage)
      └─ api.monitoramento.lan → backend Flask :5000
```

O backend **nunca** inicia conexão com os agentes. Toda comunicação é iniciada pelo agente (modelo push).

### Cinco funções principais

| Função | O que faz |
|--------|-----------|
| **Ingestão de Discovery** | Recebe inventário de hardware/SO na inicialização do agente |
| **Ingestão de Métricas** | Recebe snapshots de CPU/RAM/disco/rede a cada ~6 segundos |
| **Ingestão de Logs** | Recebe linhas brutas do `auth.log`, aplica parsing estruturado |
| **Detecção de Segurança** | Detecta brute force SSH (≥5 falhas/60s) e port scan (via flag do agente) |
| **Autenticação** | API key para agentes; PANEL_PASSWORD + API key para o painel web |

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
| requests | (para Teams webhook) |

### Infraestrutura

| Componente | Versão / Papel |
|------------|----------------|
| PostgreSQL | 15 — banco relacional principal |
| Docker Compose | Orquestra 4 containers |
| Nginx (alpine) | Proxy reverso — roteia por **virtual host** (`server_name`): `api.monitoramento.lan` → backend, `painel.monitoramento.lan` → frontend (não por prefixo de path) |

### Variáveis de ambiente (`.env`)

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `DATABASE_URL` | String de conexão PostgreSQL | Sim (fallback: `postgresql://monitor:monitor@localhost:5432/monitor`) |
| `FLASK_ENV` | Modo de execução | Não |
| `FLASK_DEBUG` | Ativa hot reload | Não |
| `PORT` | Porta do Flask | Não (padrão 5000) |
| `API_KEY` | Token de autenticação — **fallback** se não houver chave no banco | Não |
| `PANEL_PASSWORD` | Senha do painel web — validada em `POST /api/auth/login` | Sim (sem ele o login retorna 503) |
| `TEAMS_WEBHOOK_URL` | Webhook do Microsoft Teams para notificações | Não |
| `SMTP_EMAIL` | Email remetente para alertas (Gmail) | Não |
| `SMTP_PASSWORD` | App Password do Gmail (`STARTTLS`, porta 587) | Não |
| `RETENTION_DAYS` | Dias de retenção para cleanup automático (padrão: 7) | Não |
| `ALERT_RECIPIENT` | Email destinatário padrão — fallback se `email_recipients` vazio no banco | Não |

> **API_KEY:** gerada via `POST /api/settings/apikey/generate` e persistida na tabela `app_settings`. O valor no `.env` só é usado como fallback se o banco não tiver uma chave.  
> **PANEL_PASSWORD:** não precisa ir para o banco — é lida diretamente do ambiente via `os.environ.get('PANEL_PASSWORD')`.  
> **`.env` não é versionado** — usar `scp` para copiar para a VM antes de `docker compose up`.

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
│   │   └── alert.py             # AlertModel → tabela alerts
│   ├── routes/
│   │   ├── __init__.py          # Exporta register_*_routes()
│   │   ├── discovery.py         # POST/GET /api/discovery
│   │   ├── metrics.py           # POST/GET /api/metrics
│   │   ├── logs.py              # POST/GET /api/logs
│   │   ├── alerts.py            # GET /api/alerts + PATCH /api/alerts/<id>/resolve
│   │   └── connections.py       # POST /api/security/portscan (sinalização de port scan)
│   └── utils/
│       ├── __init__.py          # Exporta parse_ssh_log, count_failed_logins, check_brute_force
│       ├── auth.py              # require_api_key — decorator de autenticação (X-API-Key)
│       ├── parsers.py           # Parsing de auth.log + count_failed_logins()
│       ├── detection.py         # check_brute_force() + check_port_scan() + check_resource_alert()
│       ├── teams.py             # enviar_alerta_teams() — webhook Microsoft Teams
│       └── notifier.py          # enviar_alerta_email() — notificações por email (Gmail/SMTP)
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

| Serviço | Imagem / Build | Porta no host |
|---------|----------------|---------------|
| `postgres` | `postgres:15` | — (interna `5432`) |
| `backend` | `./BackEnd` (build) | — (interna `5000`) |
| `frontend` | `./FrontEnd` (build) | — (interna `5173`) |
| `nginx` | `nginx:alpine` | `80:80` |

> Apenas o Nginx expõe porta no host. Para acessar o PostgreSQL durante desenvolvimento: `docker compose exec postgres psql -U monitor -d monitor`

### Detalhes relevantes

- **Hot reload do backend:** Volume `./BackEnd/app:/app/app` monta o código diretamente no container. Alterações em `.py` têm efeito imediato com `FLASK_DEBUG=1`.
- **Carregamento do `.env`:** `env_file` aponta para `./BackEnd/.env` com `required: false` — o container sobe mesmo sem o arquivo; variáveis ausentes causam degradação controlada (ex.: PANEL_PASSWORD retorna 503 no login).
- **Healthcheck do postgres:** O `entrypoint.sh` usa `nc -z postgres 5432` em loop de 1 segundo para aguardar o banco antes de iniciar o Flask.
- **init.sql:** Executado pelo PostgreSQL na **primeira inicialização** do volume. O backend **não usa** `db.create_all()`.
- **Nginx:** Lê `nginx.conf` como volume somente-leitura.

### docker-compose.yml — trecho relevante do backend

```yaml
backend:
  build: ./BackEnd
  volumes:
    - ./BackEnd/app:/app/app   # Hot Reload
  env_file:
    - path: ./BackEnd/.env
      required: false          # não quebra se .env não existir na VM
  environment:
    - DATABASE_URL=postgresql://monitor:monitor@postgres:5432/monitor
    - FLASK_ENV=development
    - FLASK_DEBUG=1
  dns:
    - 8.8.8.8
    - 8.8.4.4
```

> **DNS explícito:** O container backend usa DNS do Google em vez do resolver interno do Docker. Necessário para que `requests` consiga resolver domínios externos como `*.powerplatform.com` (usado pelo Power Automate). Sem isso, envios ao Teams falham com `NameResolutionError [Errno -3]`.

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
5. Chama `registrar_modelos(db)` — instancia todos os 6 modelos
6. Executa as 8 funções de migração de schema
7. Chama `_notificar_alertas_ativos()` — notifica Teams sobre alertas ativos no startup
8. Carrega API key do banco via `_load_api_key_from_db()`
9. Registra os 5 blueprints de rotas

### Gerenciamento de destinatários de email (app.py)

Três endpoints novos gerenciam a lista de emails para notificações de alertas, persistida na tabela `app_settings` com a chave `'email_recipients'` (JSON array de strings).

| Endpoint | Método | Auth | Descrição |
|----------|--------|------|-----------|
| `/api/settings/email-recipients` | GET | Sim | Retorna lista de destinatários atual |
| `/api/settings/email-recipients` | POST | Sim | Adiciona email (valida formato `@domain.tld`) |
| `/api/settings/email-recipients/<email>` | DELETE | Sim | Remove email pelo endereço |

**Funções de suporte:**

**`_load_email_recipients()`** — Lê e retorna a lista do banco como `list[str]`. Retorna `[]` em caso de erro.

**`_save_email_recipients(recipients)`** — Persiste a lista via `INSERT ... ON CONFLICT DO UPDATE` na tabela `app_settings`.

### Migrações de schema automáticas

O banco é criado pelo `init.sql` e pode ser mais antigo que o código. As funções abaixo adicionam/alteram colunas via SQL na inicialização, sem exigir recriação do container.

| Função | Operação | Tabela |
|--------|----------|--------|
| `garantir_schema_discovery()` | ADD COLUMN IF NOT EXISTS `os_name`, `os_version`, `kernel_release`, `uptime_seconds`, `motherboard` | `host_discovery` |
| `garantir_schema_metrics()` | ADD COLUMN IF NOT EXISTS `memory_used_mb`, `memory_free_mb`, `memory_total_mb`, `disk_used_mb`, `disk_free_mb`, `disk_total_mb` | `metrics` |
| `garantir_schema_alerts()` | ADD COLUMN IF NOT EXISTS `resolved` (BOOLEAN), `resolved_at` (TIMESTAMPTZ) | `alerts` |
| `garantir_schema_alerts_message()` | ADD COLUMN IF NOT EXISTS `message` (TEXT) | `alerts` |
| `garantir_schema_iops()` | ADD COLUMN IF NOT EXISTS `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `net_sent_bytes_per_sec`, `net_recv_bytes_per_sec` | `metrics` |
| `garantir_schema_settings()` | CREATE TABLE IF NOT EXISTS `app_settings` | — |
| `garantir_schema_alerts_source_ip()` | ALTER COLUMN `source_ip` TYPE VARCHAR(45) + DROP NOT NULL | `alerts` |
| `garantir_schema_notifications()` | INSERT ON CONFLICT DO NOTHING: `notify_teams=true`, `notify_email=false` | `app_settings` |
| `garantir_schema_thresholds()` | INSERT ON CONFLICT DO NOTHING: `threshold_cpu=80`, `threshold_mem=80`, `threshold_disk=80` | `app_settings` |

> **Nota:** `init.sql` declara `alerts.source_ip` como `INET NOT NULL`. A migração `garantir_schema_alerts_source_ip()` converte a coluna para `VARCHAR(45) nullable` em bancos existentes.

### Funções de suporte ao startup

**`_load_api_key_from_db()`**  
Lê a API key da tabela `app_settings` (chave `'api_key'`). Se não encontrar, usa a variável de ambiente `API_KEY` como fallback. O valor carregado fica em `app.config['API_KEY']` e é consultado pelo `require_api_key` em toda requisição autenticada.

**`_load_threshold(key, default=80)`**  
Lê um limiar numérico de `app_settings` pela chave informada (ex: `'threshold_cpu'`). Retorna o inteiro lido ou `default=80` em caso de ausência/erro.

**`_load_notify_flag(canal)`**  
Lê o toggle `notify_teams` ou `notify_email` de `app_settings`. Defaults: `teams=True`, `email=False`.

**`_notificar_alertas_ativos()`**  
Na inicialização do container, consulta todos os alertas com `resolved=False` e envia uma notificação Teams para cada um, para que a equipe saiba que há ameaças ativas após um restart. Usa o arquivo `/tmp/.monitor_startup_notified` como flag para não reenviar durante hot-reloads do Flask (o arquivo some apenas quando o container é reiniciado de verdade).

### Registro de blueprints (injeção de dependência)

```python
register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel, MetricModel)
register_metric_routes(app, db, HostModel, AgentModel, MetricModel, AlertModel, check_resource_alert)
register_log_routes(app, db, HostModel, LogEntryModel, AlertModel)
register_alerts_routes(app, db, HostModel, AlertModel)
register_portscan_routes(app, db, HostModel, AlertModel, check_port_scan)
```

Os blueprints recebem funções de detecção por parâmetro para evitar import circular com `detection.py`.

### Endpoints gerais (definidos diretamente em app.py)

| Endpoint | Método | Auth | Resposta |
|----------|--------|------|----------|
| `/health` | GET | Não | `{"status": "ok"}` — 200 |
| `/api/status` | GET | Não | `{"status": "online", "service": "API Monitoramento", "version": "4.0.0", "timestamp": "..."}` — 200 |
| `/api/hello` | GET | Não | `{"message": "Olá do BackEnd Flask!"}` — 200 |
| `/api/hosts` | GET | Sim | Lista de hosts com status online/offline |
| `/api/heartbeat` | POST | Sim | `{"status": "ok"}` — atualiza `last_seen` do host |
| `/api/auth/login` | POST | Não | Autentica com PANEL_PASSWORD, retorna API key |
| `/api/settings/apikey` | GET | Não | Status e prefixo da API key atual (sem auth — baixo risco, necessário para tela de login) |
| `/api/settings/apikey/generate` | POST | Parcial | Gera nova API key — requer `X-API-Key` válido **ou** `password` (PANEL_PASSWORD) no body; estado inicial aceita só senha |

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

**Métodos:**

| Método | O que faz |
|--------|-----------|
| `to_dict()` | Serializa para JSON, inclui `status` e `is_online` calculados |
| `_is_online(last_metric_at, timeout_seconds=30)` | `True` se última métrica < 30s atrás |
| `_last_metric_at()` | Retorna `timestamp` da métrica mais recente |

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

`parsed_data` quando preenchido contém pelo menos: `event_type`, `status`, `usuario`, `ip_origem`.

### 6.6 Alert — tabela `alerts`

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | `BigInteger` PK | BIGSERIAL — gerado pelo banco |
| `host_id` | `Integer` FK | NOT NULL |
| `alert_type` | `String(50)` | `"brute_force"`, `"port_scan"`, `"cpu_high"`, `"mem_high"`, `"disk_high"` |
| `source_ip` | `String(45)` | IP de origem do ataque — **nullable** (NULL para alertas de recurso) |
| `timestamp` | `DateTime` | Default: `utcnow` |
| `severity` | `String(20)` | `"low"`, `"medium"`, `"high"`, `"critical"`. Default: `"medium"` |
| `metodos` | `String(20)` | `"password"` para brute force; `null` para demais |
| `message` | `Text` | Descrição legível |
| `resolved` | `Boolean` | `False` = ativo; `True` = resolvido. Default: `False` |
| `resolved_at` | `DateTime` | Momento da resolução, nullable |

> `source_ip` foi convertido de `INET NOT NULL` para `VARCHAR(45) nullable` pela migração `garantir_schema_alerts_source_ip()`. Alertas de recurso (cpu_high, mem_high, disk_high) não têm IP de origem — o campo fica NULL.

---

## 7. Rotas (Routes)

Cada arquivo cria um Blueprint Flask e expõe uma função `register_*_routes()` chamada por `app.py`. Os modelos são **injetados por parâmetro**.

### 7.1 discovery.py

#### POST /api/discovery

Recebe e persiste o inventário de hardware do agente.

**Fluxo de execução:**

1. `_extract_discovery_fields(dados, remote_addr)` — normaliza os dois formatos em um dict padronizado
2. Busca host existente por `ip_address`, `hostname` ou `host_id` (OR). Se não encontrar, cria novo
3. `_upsert_agent()` — cria ou atualiza registro na tabela `agents`
4. Cria ou sobrescreve registro em `host_discovery` (1:1 por `host_id`)
5. Retorna 201 com `host_id`, `agent_id`, `hostname`, `ip_host`, `is_virtualized`

#### GET /api/discovery

Retorna dados de discovery para o frontend. Parâmetro opcional: `?host_id=N`.

Cada item retornado inclui `agent_id` no nível raiz do dict — resolvido via `AgentModel.query.filter_by(host_id=...)` em `_discovery_to_response()` (não vem apenas do registro original de discovery, é buscado a cada chamada).

---

### 7.2 metrics.py

#### POST /api/metrics

Persiste um snapshot de métricas a cada envio do agente. Aciona `check_resource_alert()` para CPU, memória e disco.

**Validações:**
- Payload JSON obrigatório (400 se ausente)
- Campo `timestamp` obrigatório
- Host deve ser identificável (400 se impossível)

**Fluxo:**

1. `_normalize_metrics_payload()` — extrai e normaliza todos os campos
2. `_resolve_host()` — busca ou cria host
3. Cria `MetricModel`, atualiza `host.last_seen` e `agent.last_checkin`
4. Chama `check_resource_alert()` para CPU, memória e disco (cria alertas se > 80%)
5. Retorna 201 com `metric_id`, `host_id`, `timestamp`

#### GET /api/metrics

Parâmetros: `host_id` (obrigatório), `limit` (padrão 20, máximo 100), `offset` (padrão 0).

Retorna métricas em **ordem cronológica crescente**.

---

### 7.3 logs.py

#### POST /api/logs

Recebe uma linha de log por requisição, persiste e detecta brute force.

**Fluxo:**

1. Valida `host_id`, `timestamp`, `raw_line`
2. Se `log_type == "auth"`: chama `parse_auth_log(raw_line)`
3. Persiste `LogEntryModel` com `parsed_data` ou `null`
4. **Após o commit:** se `status == "failed"` e `ip_origem` presente → chama `check_brute_force()`
5. Retorna 201 com `log_id`, `parsed`, `event_type`, `alerta_criado`

> `check_brute_force()` é chamado **após** o `db.session.commit()` para garantir que a falha recém-salva já seja contabilizada na query de contagem da janela de 60 segundos.

> O objeto `host` já está disponível na rota (consultado para validar existência do host), então `host.hostname` e `host.ip_address` são passados diretamente sem consulta extra.

#### GET /api/logs

Parâmetros: `host_id` (**opcional** — quando ausente, retorna logs agregados de **todos os hosts**), `limit`, `offset`, `log_type` (opcional).

Quando `host_id` é omitido, cada entrada do array `logs` ganha um campo extra `hostname` (resolvido em lote via `HostModel.query.filter(HostModel.id.in_(ids))` a partir dos `host_id` presentes na página retornada), para a visão geral do frontend conseguir identificar a origem de cada log sem uma consulta por linha. Os campos `host_id` e `hostname` de nível raiz da resposta ficam `null` nesse modo.

---

### 7.4 alerts.py

#### GET /api/alerts

Parâmetros:
- `status` (padrão `"active"`) — `"active"` | `"resolved"` | `"all"`. Retorna 400 para valores inválidos
- `host_id` (opcional)
- `limit` (padrão 20, máximo 100), `offset` (padrão 0)

**Exemplo de resposta:**
```json
{
  "alerts": [
    {
      "id": 42,
      "host_id": 2,
      "alert_type": "port_scan",
      "source_ip": "10.10.10.26",
      "timestamp": "2026-06-02T19:26:01",
      "severity": "high",
      "metodos": null,
      "message": "Varredura de portas: 1000 portas distintas em 60s de 10.10.10.26",
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
- **400 Bad Request** — alerta já estava resolvido

---

### 7.5 connections.py

#### POST /api/security/portscan

Recebe sinal de port scan detectado pelo agente via tcpdump. **Não persiste dados** — apenas aciona `check_port_scan()`.

**Campos obrigatórios:** `global.host_id`

**Campos opcionais:** `global.primary_ip`, `timestamp`, `scan_sources`

**Fluxo:**

1. Valida e extrai `global.host_id`
2. Se `scan_sources` vier vazio: loga `WARNING` e retorna 200 sem criar alerta (evita atribuir scan ao IP da própria vítima)
3. Itera `scan_sources` → `check_port_scan()` por IP atacante
4. Retorna 201 com `scan_sources` e `alertas_criados`

> O agente só envia este endpoint quando `port_scan_detected=True`, ou seja, em eventos reais de detecção — sem polling a cada 5s.

> **Motivo da remoção da persistência em `active_connections`:** a tabela não tinha tela consumidora no frontend e gerava erro 500 por FK violada (`host_id` inexistente em certas janelas de inicialização). A detecção de port scan não dependia da lista de conexões TCP — dependia apenas de `scan_sources` produzido pelas threads de tcpdump. A funcionalidade de alerta foi preservada integralmente; apenas o peso morto foi removido.

---

## 8. Utilitários (Utils)

### 8.1 auth.py

Contém o decorator `require_api_key` aplicado a todas as rotas que recebem dados dos agentes ou expõem dados sensíveis ao frontend.

```python
@require_api_key
def endpoint():
    ...
```

**Lógica:**
1. Extrai o header `X-API-Key: {token}`
2. Compara com `app.config['API_KEY']` (carregado do banco no startup)
3. Se inválido ou ausente: retorna 401

> **Mudança de protocolo:** o header foi alterado de `Authorization: Bearer {token}` para `X-API-Key: {token}`. Desde a Fase A de hardening, o agente envia **exclusivamente** `X-API-Key` — `MONITOR_TOKEN` e o header `Authorization: Bearer` foram removidos do agente (ver `Agent-Documentation.md`, seção 10). O backend só reconhece `X-API-Key`.

**Rotas protegidas (decoradas com `@require_api_key`):**
- `POST /api/heartbeat`
- `GET /api/hosts`
- `POST /api/security/portscan`
- `GET /api/settings/email-recipients`
- `POST /api/settings/email-recipients`
- `DELETE /api/settings/email-recipients/<email>`
- Demais rotas de ingestão e consulta (discovery, metrics, logs, alerts)

---

### 8.2 teams.py

Envia notificações para o Microsoft Teams via webhook Power Automate configurado em `TEAMS_WEBHOOK_URL`.

**Função pública:**

```python
enviar_alerta_teams(titulo, mensagem, severidade='info', origem='backend', link='') -> bool
```

**Comportamento:** lê `TEAMS_WEBHOOK_URL` dentro da função (não em module-level) para evitar problema de lazy loading. Se não configurado, loga `WARNING` e retorna `False` silenciosamente. Usado em `check_brute_force()`, `check_port_scan()`, `check_resource_alert()` e `_notificar_alertas_ativos()`.

**Payload enviado ao Power Automate:**

```json
{
  "titulo":     "Port Scan detectado — servidor-web",
  "mensagem":   "Varredura de portas: 45 portas distintas em 60s de 192.168.1.10",
  "severidade": "CRITICAL",
  "icone":      "🔴",
  "origem":     "servidor-web (10.10.10.5)",
  "timestamp":  "02/06/2026 14:35:00",
  "link":       ""
}
```

**Mapeamento severidade → ícone:**

| Severidade | Ícone | Uso |
|------------|-------|-----|
| `critical` | 🔴 | Brute force SSH, port scan |
| `high` | 🟠 | — |
| `warning` | 🟡 | Alertas de recurso (CPU/RAM/disco) |
| `info` | 🔵 | Notificações informativas |

**Logging:** sucesso e erros são logados em nível `WARNING` (visível no Flask por padrão para loggers customizados). Inclui status HTTP e primeiros 300 chars do body em caso de falha.

**Integração Power Automate:**
- O endpoint HTTP do Power Automate retorna **202 Accepted imediatamente** — o flow roda assíncrono
- JSON schema do trigger: `Context/Teams/http-trigger-schema.json`
- Adaptive Card JSON: `Context/Teams/adaptive-card.json`
- Expressões dinâmicas no card: `@{triggerBody()?['campo']}`

---

### 8.3 notifier.py

**Arquivo:** `app/utils/notifier.py`

Módulo de notificação por email para alertas de segurança. Usa `smtplib` (stdlib Python) com Gmail via **App Password** (`STARTTLS`, porta 587). Não requer bibliotecas externas.

**Função pública:**

```python
enviar_alerta_email(
    alert_type, host_id, source_ip, message, severity,
    hostname='', host_ip='',
    recipients=None,   # lista de emails; None → fallback para ALERT_RECIPIENT
) -> bool
```

**Credenciais lidas do `.env`:**

| Variável | Uso |
|----------|-----|
| `SMTP_EMAIL` | Remetente (conta Gmail autenticada) |
| `SMTP_PASSWORD` | App Password do Gmail (não a senha normal da conta) |
| `ALERT_RECIPIENT` | Destinatário padrão quando `recipients` está vazio/None |

**Destinatários em runtime:** lidos do banco via `_get_email_recipients(db)` em `detection.py`. O campo `app_settings.email_recipients` armazena um JSON array de strings. Se o banco retornar lista vazia, cai no `ALERT_RECIPIENT` do `.env`.

**Corpo do email:** enviado em dois formatos simultâneos (MIME multipart):
- **Texto plano** — fallback para clientes sem HTML
- **HTML** — card dark-mode com badge de severidade colorido, tabela de detalhes (host, IP do host, IP atacante quando aplicável, data/hora), barra de progresso de criticidade e botão CTA para o painel

**Mapeamento severidade → aparência:**

| Severidade | Cor | Emoji | Barra % |
|------------|-----|-------|---------|
| `low` | `#d97706` | 🟡 | 30% |
| `medium` | `#ea580c` | 🟠 | 55% |
| `high` | `#dc2626` | 🔴 | 80% |
| `critical` | `#7f1d1d` | 🚨 | 100% |

**Assunto gerado:** `{emoji} [ALERTA][{SEVERITY}] {tipo_legivel} — {hostname}`

**Comportamento de falha:** `try/except` completo — qualquer erro de SMTP/rede é logado em `ERROR` e `False` é retornado silenciosamente. Nunca interrompe o fluxo de detecção.

**Exemplo de log de sucesso:**
```
INFO  Email de alerta enviado | tipo=brute_force | host_id=2 | ip=10.10.10.26 | destinatários=2
```

---

### 8.4 parsers.py

Parsers de `/var/log/auth.log` e função de contagem de falhas.

#### parse_auth_log(raw_line) — Orquestrador principal

Tenta cada parser na ordem de especificidade e retorna o primeiro resultado não-`None`.

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

#### count_failed_logins(LogEntryModel, host_id, ip_origem, janela_horas=1) → int

Conta tentativas de login SSH com falha de um IP dentro de uma janela de tempo. Usa operadores JSONB nativos do PostgreSQL.

**SQL equivalente:**
```sql
SELECT COUNT(*) FROM logs
WHERE host_id       = :host_id
  AND log_type      = 'auth'
  AND timestamp    >= :inicio_janela
  AND parsed_data->>'status'    = 'failed'
  AND parsed_data->>'ip_origem' = :ip_origem
```

> **Vulnerabilidade identificada:** `ip_origem` é interpolado diretamente na string SQL em vez de usar parâmetros vinculados. Na prática o risco é baixo (valor extraído por regex IPv4), mas a forma correta seria `sa_text("... = :ip").bindparams(ip=ip_origem)`.

---

### 8.5 detection.py

#### Função auxiliar: `_get_email_recipients(db)` → list

Lê a lista de destinatários de email da tabela `app_settings` (chave `'email_recipients'`). Se não encontrar ou der erro, usa `ALERT_RECIPIENT` do `.env` como fallback. Retorna `[]` se nenhum destinatário configurado.

Chamada internamente pelas três funções de detecção antes de invocar `enviar_alerta_email()`.

#### Função auxiliar: `_notificacao_habilitada(db, canal)` → bool

Lê o toggle `notify_teams` / `notify_email` de `app_settings`. Defaults: `teams=True`, `email=False`. Chamada antes de cada envio de notificação nas três funções de detecção — se desabilitado, o log é emitido em INFO e o envio é ignorado silenciosamente.

#### Função auxiliar: `_get_threshold(db, alert_type)` → float

Lê o limiar de recurso (`threshold_cpu`, `threshold_mem`, `threshold_disk`) de `app_settings`. Fallback para `80.0`. Chamada por `check_resource_alert()` para comparar com o valor atual da métrica.

---

#### check_brute_force(db, LogEntryModel, AlertModel, host_id, ip_origem, hostname='', host_ip='') → bool

**Constantes:**
- `LIMIAR_BRUTE_FORCE = 5` — mínimo de falhas para disparar alerta
- `JANELA_HORAS = 1/60` — janela de 60 segundos

**Parâmetros opcionais:**
- `hostname` — nome do host (ex: `"servidor-web"`) — usado no título do alerta Teams
- `host_ip` — IP do host monitorado — exibido no campo `origem` do alerta Teams

**Fluxo:**

1. Chama `count_failed_logins()` com `janela_horas=1/60`
2. Se `total_falhas < 5`: retorna `False`
3. Consulta se já existe alerta ativo (`resolved=False`) para `host_id + source_ip + "brute_force"` — evita duplicatas
4. Se já existe: retorna `False`
5. Cria `AlertModel` com `severity="high"`, `metodos="password"`
6. Chama `enviar_alerta_teams()` com título `"Brute Force SSH — {hostname}"` (ou `"Host {id}"` se sem hostname)
7. Chama `enviar_alerta_email()` com os destinatários de `_get_email_recipients(db)`
8. Retorna `True`

---

#### check_port_scan(db, AlertModel, host_id, ip_origem, port_count=0, hostname='', host_ip='') → bool

**Deduplicação por janela de tempo (2 minutos):**

Ao contrário do brute force (que suprime enquanto `resolved=False`), o port scan usa uma janela temporal de cooldown:

- Verifica se existe alerta com `resolved=False` criado nos últimos **2 minutos** para `host_id + ip_origem + "port_scan"`
- Se existir alerta recente: retorna `False` — evita flood durante um scan em andamento (agente reporta a cada ~6s por ~60s)
- Se não existir alerta recente: cria novo alerta — mesmo que haja um alerta antigo não-resolvido, um novo scan ~2min depois gera novo alerta

**Motivação:** o agente reporta `port_scan_detected=true` repetidamente enquanto a janela deslizante de 60s não expirar. Sem cooldown, cada POST (a cada ~6s) criaria um novo alerta. Com cooldown de 2 minutos: 1 alerta por scan, mas novo scan após 2+ minutos gera novo alerta sem precisar resolver o anterior.

**Fluxo:**
```python
cutoff = datetime.utcnow() - timedelta(minutes=2)
alerta_recente = AlertModel.query.filter(
    host_id == host_id,
    source_ip == ip_origem,
    alert_type == 'port_scan',
    resolved == False,
    timestamp >= cutoff,
).first()
```

Falha silenciosa — nunca interrompe o salvamento das conexões.

---

#### check_resource_alert(db, AlertModel, host_id, alert_type, valor, limiar, hostname='', host_ip='') → bool

Cria alerta se `valor > limiar` e não houver alerta ativo do mesmo tipo para o host.

**Tipos suportados:** `cpu_high`, `mem_high`, `disk_high`  
**Limiar padrão:** 80%  
**`source_ip`:** sempre `None` (alertas de recurso não têm IP de origem)

**Parâmetros opcionais:**
- `hostname` — nome do host — usado no título do alerta Teams: `"CPU alta — servidor-web"`
- `host_ip` — IP do host — exibido no campo `origem` do alerta Teams

---

## 9. Referência de Endpoints

| Endpoint | Método | Auth | Quem chama | Descrição |
|----------|--------|------|------------|-----------|
| `/health` | GET | Não | Docker healthcheck | `{"status": "ok"}` — 200 |
| `/api/status` | GET | Não | Monitoramento | Versão e timestamp da API |
| `/api/hello` | GET | Não | Teste | Endpoint de verificação básica |
| `/api/auth/login` | POST | Não | Frontend | Valida PANEL_PASSWORD, retorna API key ao navegador |
| `/api/settings/apikey` | GET | Não | Frontend | Status e prefixo da API key atual (sem auth intencional) |
| `/api/settings/apikey/generate` | POST | Parcial | Frontend (admin) | Gera nova API key — requer `X-API-Key` válido ou `{"password":"..."}` no body |
| `/api/hosts` | GET | Sim | Frontend | Lista hosts com status online/offline |
| `/api/heartbeat` | POST | Sim | Agente | Atualiza `last_seen` do host |
| `/api/discovery` | POST | Sim | Agente | Recebe inventário de hardware |
| `/api/discovery` | GET | Sim | Frontend | Retorna dados de hardware (cada item inclui `agent_id`) |
| `/api/metrics` | POST | Sim | Agente | Recebe snapshot de métricas (~5s) |
| `/api/metrics` | GET | Sim | Frontend | Consulta métricas com paginação |
| `/api/logs` | POST | Sim | Agente | Recebe linha do auth.log + parsing + detecção |
| `/api/logs` | GET | Sim | Frontend | Consulta logs com filtro e paginação — `host_id` opcional (agrega todos os hosts) |
| `/api/alerts` | GET | Sim | Frontend | Lista alertas de segurança |
| `/api/alerts/<id>/resolve` | PATCH | Sim | Frontend | Marca alerta como resolvido |
| `/api/security/portscan` | POST | Sim | Agente | Recebe sinal de port scan (tcpdump) → cria alerta |
| `/api/settings/email-recipients` | GET | Sim | Frontend | Lista destinatários de email para alertas |
| `/api/settings/email-recipients` | POST | Sim | Frontend | Adiciona email à lista de destinatários |
| `/api/settings/email-recipients/<email>` | DELETE | Sim | Frontend | Remove email da lista de destinatários |
| `/api/settings/thresholds` | GET | Sim | Frontend | Retorna limiares configurados de CPU, memória e disco (%) |
| `/api/settings/thresholds` | PATCH | Sim | Frontend | Atualiza um ou mais limiares (cpu, mem, disk) — valor inteiro 1–99 |
| `/api/settings/notifications` | GET | Sim | Frontend | Retorna toggles de notificação (`teams`, `email`) |
| `/api/settings/notifications` | PATCH | Sim | Frontend | Atualiza toggles de notificação — aceita subset `{"teams": bool, "email": bool}` |
| `/api/maintenance/cleanup` | POST | Sim | Admin/Teste | Dispara limpeza de dados antigos imediatamente; retorna linhas removidas por tabela |

### POST /api/auth/login

**Body:**
```json
{ "password": "senha-do-painel" }
```

**Respostas:**
- **200 OK:** `{ "api_key": "abc123..." }` — frontend salva no sessionStorage
- **401 Unauthorized:** senha inválida
- **503 Service Unavailable:** `PANEL_PASSWORD` não configurado no servidor
- **404 Not Found:** API key não gerada ainda (ir em Configurações → Gerar)

---

## 10. Fluxos de Dados

### 10.1 Autenticação do Painel Web

```
Navegador → POST /api/auth/login { password }
                │
                ├─ Verifica PANEL_PASSWORD (variável de ambiente)
                ├─ [senha inválida] → 401
                ├─ [PANEL_PASSWORD ausente] → 503
                └─ Retorna { api_key }
                        │
                        └─ Frontend salva api_key no sessionStorage
                           Inclui em todas as próximas requisições:
                           X-API-Key: {api_key}
```

### 10.2 Discovery (inicialização do agente)

```
Agente → POST /api/discovery { X-API-Key }
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

### 10.3 Métricas + Alertas de Recurso

```
Agente → POST /api/metrics { X-API-Key }
                │
                ├─ _normalize_metrics_payload()
                ├─ _resolve_host()  → retorna objeto host (com .hostname e .ip_address)
                ├─ INSERT MetricModel
                │
                ├─ check_resource_alert(cpu_percent,  80.0, host.hostname, host.ip_address)
                ├─ check_resource_alert(memory_percent, 80.0, host.hostname, host.ip_address)
                └─ check_resource_alert(disk_percent,  80.0, host.hostname, host.ip_address)
                    ├─ [valor <= limiar] → False
                    ├─ [alerta ativo existente] → False
                    └─ INSERT AlertModel { cpu_high/mem_high/disk_high, source_ip=None }
                       + Teams: "CPU alta — servidor-web"
                       + Email: destinatários de app_settings → True
```

### 10.4 Logs + Detecção de Brute Force

```
Agente → POST /api/logs { X-API-Key }
                │
                ├─ Valida host_id → HostModel.query.get(host_id) → objeto host
                ├─ parse_auth_log(raw_line)
                │
                ├─ INSERT LogEntryModel { parsed_data }
                ├─ db.session.commit()
                │
                └─ [status == "failed" e ip_origem presente]
                    └─ check_brute_force(host_id, ip_origem, host.hostname, host.ip_address)
                        ├─ count_failed_logins(60s) → N falhas
                        ├─ [N < 5] → False
                        ├─ [alerta resolved=False existente] → False
                        └─ INSERT AlertModel { brute_force, high }
                           + Teams: "Brute Force SSH — servidor-web"
                           + Email: destinatários de app_settings → True
```

### 10.5 Detecção de Port Scan

```
Agente (threads tcpdump) → detecta ≥10 portas distintas de um IP em 60s
                │
                └─ [port_scan_detected=True] → POST /api/security/portscan
                        │
                        ├─ [scan_sources vazio] → loga WARNING, retorna 200 sem alerta
                        │
                        └─ [com scan_sources] → itera IPs atacantes
                            └─ check_port_scan(host_id, ip_atacante, port_count, host.hostname, host.ip_address)
                                ├─ [alerta resolved=False criado há < 2min] → False
                                └─ INSERT AlertModel { port_scan, high }
                                   + Teams: "Port Scan detectado — servidor-web" (se notify_teams=true)
                                   + Email: destinatários de app_settings (se notify_email=true) → True
```

---

## 11. Regras de Negócio e Detecção

### 11.1 Status Online/Offline

- **Online:** última métrica recebida há **menos de 30 segundos**
- Calculado em tempo real a cada `to_dict()` — não persistido no banco

### 11.2 Detecção de Brute Force SSH

- **Limiar:** ≥ 5 falhas do mesmo IP em 60 segundos
- **Deduplicação:** um alerta ativo por `host_id + source_ip + "brute_force"` (resolved=False)
- **Severidade:** `"high"`, método: `"password"`

### 11.3 Detecção de Port Scan

- **Responsável pela análise:** o agente (via tcpdump, SYN tracking com janela deslizante de 60s)
- **Papel do backend:** persiste o alerta quando `port_scan_detected=true`
- **Deduplicação:** cooldown de 2 minutos — evita flood durante scan ativo, mas permite novos alertas para novos scans (sem precisar resolver o anterior se já passou 2+ minutos)
- **Severidade:** `"high"`, método: `null`

### 11.4 Alertas de Recurso (CPU / Memória / Disco)

- **Limiar:** configurável via `PATCH /api/settings/thresholds`. Default: 80% para CPU, memória e disco. Lido dinamicamente de `app_settings` por `_get_threshold()` a cada verificação.
- **Deduplicação:** um alerta ativo por `host_id + alert_type` (resolved=False)
- **`source_ip`:** `None` — alertas de recurso não têm origem de rede
- **Severidade:** `"high"`

### 11.5 Resolução de Alertas

- `PATCH /api/alerts/<id>/resolve` — define `resolved=True`, `resolved_at=datetime.utcnow()`
- Após resolução, nova detecção do mesmo IP/tipo **pode** gerar novo alerta

### 11.6 Notificações (Teams + Email)

Cada alerta criado **verifica os toggles** antes de disparar notificações. `_notificacao_habilitada(db, 'teams')` e `_notificacao_habilitada(db, 'email')` são consultados a cada evento. Se habilitados, dispara Teams e Email independentemente. Ambos falham silenciosamente — nunca interrompem o fluxo de detecção.

**Título e origem dos alertas:** o hostname real e IP do host monitorado são exibidos no lugar do ID numérico:
- Título: `"Port Scan detectado — servidor-web"` (ou `"Port Scan detectado — Host 24233"` se hostname indisponível)
- Origem: `"servidor-web (10.10.10.5)"` (ou `"host-24233"` se sem hostname)

**Como hostname/IP chegam a cada função de detecção:**

| Função | Fonte do hostname/IP |
|--------|---------------------|
| `check_brute_force` | `host` já consultado em `logs.py` para validação do host_id |
| `check_resource_alert` | `host` retornado por `_resolve_host()` em `metrics.py` |
| `check_port_scan` | `HostModel.query.get(host_id)` consultado em `connections.py` (rota `/api/security/portscan`) |

**Destinatários de email:** lidos de `app_settings.email_recipients` (JSON array) via `_get_email_recipients(db)`. Fallback para `ALERT_RECIPIENT` do `.env` se a lista no banco estiver vazia.

**Gerenciar destinatários pelo painel:**  `GET/POST/DELETE /api/settings/email-recipients` → aba Configurações do frontend.

### 11.7 Notificações Teams no Startup

- Na inicialização do container, `_notificar_alertas_ativos()` envia Teams para todos os alertas com `resolved=False`
- Flag `/tmp/.monitor_startup_notified` evita reenvio durante hot-reloads do Flask
- O arquivo some apenas quando o container é reiniciado de verdade (não no hot-reload)

---

## 12. Validações e Códigos de Erro

### Códigos retornados

| Código | Situação |
|--------|----------|
| `200 OK` | Consulta bem-sucedida (GET, PATCH /resolve) |
| `201 Created` | Dado persistido com sucesso (POST) |
| `400 Bad Request` | Campo obrigatório ausente, tipo inválido, alerta já resolvido |
| `401 Unauthorized` | API key ausente ou inválida; senha do painel inválida |
| `404 Not Found` | Host ou alerta não encontrado; API key não gerada |
| `500 Internal Server Error` | Exceção não tratada (com `db.session.rollback()`) |
| `503 Service Unavailable` | PANEL_PASSWORD não configurado |

### Validações por endpoint

| Endpoint | Campo | Validação |
|----------|-------|-----------|
| `POST /api/auth/login` | `password` | Obrigatório; comparado com `PANEL_PASSWORD` |
| `POST /api/logs` | `host_id` | Obrigatório, deve ser numérico, host deve existir (404) |
| `POST /api/logs` | `raw_line` | Obrigatório, não pode ser vazio ou whitespace |
| `GET /api/metrics` | `host_id` | Obrigatório, deve ser numérico, host deve existir |
| `GET /api/logs` | `host_id` | **Opcional** — se informado, deve ser numérico e o host deve existir (404); se ausente, retorna logs de todos os hosts |
| `GET /api/alerts` | `status` | Deve ser `"active"`, `"resolved"` ou `"all"` |
| `POST /api/security/portscan` | `global.host_id` | Obrigatório, deve ser numérico |
| `PATCH /api/alerts/<id>/resolve` | alerta | Deve existir (404); se já resolvido retorna 400 |
| Todas (exceto auth/login, settings, health) | `X-API-Key` | Obrigatório → 401 se ausente/inválido |

---

## 13. Chaves de app_settings

Todas as configurações do sistema que precisam sobreviver a restarts são persistidas na tabela `app_settings`. Abaixo a lista completa de chaves usadas em produção:

| Chave | Valor padrão | Gerenciada por | Descrição |
|-------|-------------|----------------|-----------|
| `api_key` | — | `POST /api/settings/apikey/generate` | Token de autenticação dos agentes e do painel web |
| `email_recipients` | `[]` (JSON array) | `POST/DELETE /api/settings/email-recipients` | Lista de emails para alertas |
| `notify_teams` | `true` | `PATCH /api/settings/notifications` | Habilita/desabilita alertas via Teams |
| `notify_email` | `false` | `PATCH /api/settings/notifications` | Habilita/desabilita alertas via Email |
| `threshold_cpu` | `80` | `PATCH /api/settings/thresholds` | Limiar de CPU (%) para gerar alerta `cpu_high` |
| `threshold_mem` | `80` | `PATCH /api/settings/thresholds` | Limiar de memória (%) para gerar alerta `mem_high` |
| `threshold_disk` | `80` | `PATCH /api/settings/thresholds` | Limiar de disco (%) para gerar alerta `disk_high` |

Os valores de `notify_*` e `threshold_*` são inseridos com `ON CONFLICT DO NOTHING` no startup (via `garantir_schema_notifications()` e `garantir_schema_thresholds()`), portanto não sobrescrevem configurações já existentes.

---

## 15. Coerência com o Trabalho Acadêmico

| Funcionalidade proposta | Status no código |
|------------------------|------------------|
| Arquitetura cliente-servidor com agentes push | ✅ Implementado |
| Coleta de métricas de CPU, memória, disco, rede | ✅ Implementado |
| Coleta de inventário de hardware (discovery) | ✅ Implementado |
| Análise de logs (auth.log) | ✅ Implementado |
| Detecção de brute force SSH (≥5 falhas/60s) | ✅ Implementado e validado |
| Detecção de port scan | ✅ Implementado e validado (via tcpdump no agente) |
| Alertas de recurso (CPU/RAM/disco configurável) | ✅ Implementado — limiar configurável via painel |
| PostgreSQL com JSONB | ✅ Implementado |
| Docker Compose com 4 serviços | ✅ Implementado |
| Nginx como proxy reverso | ✅ Implementado |
| Dashboard web para visualização | ✅ Implementado no frontend |
| Autenticação por token (API_KEY + X-API-Key) | ✅ Implementado — header `X-API-Key` em todos os endpoints protegidos |
| Senha do painel web (PANEL_PASSWORD) | ✅ Implementado — login modal no frontend |
| Notificações Teams | ✅ Implementado — brute force, port scan, recursos e startup (toggle configurável) |
| Notificações por email | ✅ Implementado — Gmail/SMTP (toggle configurável) |
| Gerenciamento de destinatários de email | ✅ Implementado — `GET/POST/DELETE /api/settings/email-recipients` + UI |
| Política de retenção de dados de 7 dias | ✅ Automatizada via APScheduler (03:00 UTC) + `POST /api/maintenance/cleanup` manual |

---

## 16. Divergências e Observações Técnicas

### 16.1 Versão Python

O PDF de capa (v4.0) menciona Python 3.13. O `Dockerfile` real usa `python:3.12-alpine`.

### 16.2 Atributos Python vs colunas do banco (Metric)

O `MetricModel` usa aliases para vários campos. Exemplo:

```python
net_sent = db.Column('net_sent_bytes', db.BigInteger, ...)  # Python: .net_sent | banco: net_sent_bytes
disk_read_iops = db.Column('read_iops', db.Float, ...)      # Python: .disk_read_iops | banco: read_iops
```

O `to_dict()` usa os nomes Python, não os nomes das colunas. O frontend precisa conhecer esses nomes.

### 16.4 SQL Injection em count_failed_logins — ✅ CORRIGIDO (Fase A)

Em `parsers.py`, `ip_origem` era interpolado diretamente na string SQL. Corrigido para usar parâmetros vinculados:

```python
# Antes (vulnerável):
sa_text(f"parsed_data->>'ip_origem' = '{ip_origem}'")

# Após correção:
sa_text("parsed_data->>'ip_origem' = :ip_origem").bindparams(ip_origem=ip_origem)
```

### 16.5 init.sql — schema consolidado

O `init.sql` foi atualizado (commit `3b7189a`) para refletir o schema atual — inclui todas as colunas adicionadas pelas migrações e exclui a tabela `active_connections` que foi removida. Novos ambientes criados com o `init.sql` atual já partem do schema correto; as funções `garantir_schema_*` são idempotentes e não causam erro em bancos atualizados.

### 16.6 Política de retenção — ✅ AUTOMATIZADA (Fase B)

`APScheduler` (`BackgroundScheduler`) dispara `cleanup_old_data(:dias)` todos os dias às 03:00 UTC. O número de dias é configurável via `RETENTION_DAYS` (padrão 7). O endpoint `POST /api/maintenance/cleanup` permite disparar a limpeza manualmente. Em modo debug com reloader, o scheduler só sobe no processo filho (`WERKZEUG_RUN_MAIN=true`) para evitar duplicação.

### 16.7 request em função helper de metrics.py

Em `_normalize_metrics_payload()`, há uma referência a `request.args.get('host_id')` sem que `request` seja passado como parâmetro explícito. Funciona corretamente dentro do contexto Flask, mas dificulta testes unitários.

---

## 17. Evolução do Projeto — Decisões Iniciais vs. Decisões Finais

Esta seção documenta as principais mudanças de decisão técnica ao longo do desenvolvimento, com a motivação de cada alteração.

| Decisão | Inicial | Final/Atual | Motivo |
|---------|---------|-------------|--------|
| **Proxy reverso** | Caddy (TLS automático + Step-CA) | Nginx (HTTP simples) | Caddy introduzia complexidade de TLS e Step-CA desnecessária para o laboratório; Nginx suficiente |
| **TLS / HTTPS** | Obrigatório — agentes usariam `verify="/etc/agente/root_ca.crt"` | HTTP sem TLS | Step-CA não foi implementado; escopo simplificado para o ambiente de lab |
| **Tabela de conexões TCP** | `active_connections` — snapshot de todas as conexões psutil | Removida | Sem tela consumidora no frontend; causava erro 500 por FK violada na janela de startup |
| **Detecção de port scan** | Via `psutil.net_connections()` no agente | Via `tcpdump` (captura SYN) no agente | `psutil` listava conexões estabelecidas, não diferenciava escaneamento de tráfego legítimo |
| **Header de autenticação** | `Authorization: Bearer {token}` | `X-API-Key: {token}` | Padrão mais comum para APIs machine-to-machine; menos conflito com proxies e frameworks |
| **Envio de port scan** | Polling a cada ~5s (sempre que agente coletava conexões) | Somente quando `port_scan_detected=True` | Elimina requisições desnecessárias e alertas falsos de "nenhum scan ativo" |
| **Notificações** | Apenas Teams (webhook Power Automate) | Teams + Email (Gmail/SMTP) configuráveis por toggle | Necessidade de notificação sem dependência do canal Teams; toggles para evitar spam em testes |
| **Thresholds de alerta** | Fixos em 80% no código-fonte | Configuráveis via `app_settings` + UI | Operadores precisam ajustar conforme o hardware e a carga esperada de cada host |
| **Retenção de dados** | Manual — operador chama `cleanup_old_data()` no banco | Automática — APScheduler dispara às 03:00 UTC diariamente | Evita crescimento indefinido das tabelas sem intervenção manual |
| **Startup do container** | `entrypoint.sh` aguardava PostgreSQL com loop `nc -z` | `postgres` healthcheck + `depends_on: service_healthy` | Elimina race condition: backend só sobe após o banco estar de fato pronto |
| **Armazenamento da API key** | Variável de ambiente `API_KEY` no `.env` | Banco de dados (`app_settings`) com fallback para env | Permite rotação de chave sem redeployar o container |
| **Modelo de notificação no startup** | Não havia | `_notificar_alertas_ativos()` envia Teams ao inicializar | Garante visibilidade de ameaças ativas após restart inesperado do container |
| **Consulta de logs (`GET /api/logs`)** | `host_id` obrigatório — só era possível consultar logs de um host por vez | `host_id` opcional — sem ele, retorna logs agregados de todos os hosts, com campo `hostname` por entrada | Dashboard precisava de uma visão geral de logs sem exigir que o operador escolhesse um host primeiro |
| **`GET /api/discovery`** | Resposta não trazia o agente associado ao host | Cada item inclui `agent_id` (resolvido via `AgentModel.query.filter_by(host_id=...)`) | Frontend precisa relacionar o agente ativo a cada host na tela de discovery |

---

*Documentação atualizada em 21/06/2026 — v8.1.0*  
*Adições v5.0: autenticação (API key + PANEL_PASSWORD), Teams, alertas de recurso, migrations adicionais, check_port_scan com cooldown temporal, notificação de startup.*  
*Adições v5.1: DNS explícito no docker-compose (8.8.8.8/8.8.4.4); teams.py com payload completo (icone, timestamp, link), lazy URL loading corrigido, log levels WARNING; hostname e host_ip nos alertas Teams.*  
*Adições v6.0: notifier.py (email via Gmail/SMTP com HTML dark-mode); endpoints de gerenciamento de destinatários de email (`GET/POST/DELETE /api/settings/email-recipients`); `_get_email_recipients(db)` em detection.py; mudança de header de autenticação de `Authorization: Bearer` para `X-API-Key`; app_settings passa a armazenar `email_recipients`.*  
*Adições v6.1 (Fase A — hardening): `POST /api/settings/apikey/generate` protegido com X-API-Key ou PANEL_PASSWORD; SQL injection em `count_failed_logins` corrigido (bind params); portas 5432/5000/5173 removidas do host no docker-compose (apenas Nginx 80 exposto).*  
*Adições v6.2 (Fase B — retenção): APScheduler adicionado; `_executar_cleanup` + `_job_cleanup` + `_iniciar_scheduler` em `app.py`; cron 03:00 UTC; `RETENTION_DAYS` env; endpoint `POST /api/maintenance/cleanup`.*  
*Adições v6.3 (Fases C/D): thresholds configuráveis (CPU/RAM/disco) via `app_settings`; toggles `notify_teams`/`notify_email`; `NotificationsCard` e `ThresholdsCard` no frontend; Sidebar limpa (badge e dot fixos removidos).*  
*Adições v7.0 (remoção active_connections): tabela `active_connections` e model `connection.py` removidos — sem tela consumidora no frontend e causava erro 500 por FK. Rota renomeada de `POST /api/connections` para `POST /api/security/portscan`; endpoint não persiste dados, apenas aciona `check_port_scan()`. Agente passa a enviar o sinal somente quando `port_scan_detected=True`, eliminando polling a cada 5s. Fallback legado (IP mais frequente em connections[]) removido; `scan_sources` vazio com flag `True` suprime o alerta (em vez de poluir com o IP da vítima).*  
*Adições v8.0 (05/06/2026): seção 13 (Chaves de app_settings) adicionada com lista completa de chaves; migrações `garantir_schema_notifications()` e `garantir_schema_thresholds()` documentadas; endpoints `GET/PATCH /api/settings/thresholds` e `GET/PATCH /api/settings/notifications` adicionados à referência; funções `_load_threshold`, `_load_notify_flag`, `_notificacao_habilitada`, `_get_threshold` documentadas; seção 17 (Evolução do Projeto) adicionada; init.sql corrigido para refletir schema consolidado; política de retenção atualizada como automatizada.*  
*Adições v8.1 (21/06/2026 — esta revisão): `GET /api/discovery` passa a incluir `agent_id` em cada item (resolvido via `AgentModel`); `GET /api/logs` com `host_id` agora opcional — sem ele, agrega logs de todos os hosts e inclui `hostname` por entrada; diagramas e tabelas que ainda citavam `Authorization: Bearer` corrigidos para `X-API-Key` (header já era só X-API-Key desde a Fase A, doc estava desatualizada nesses trechos); referência a `POST /api/connections` (renomeado para `/api/security/portscan` na v7.0) corrigida na lista de rotas protegidas; contagem de modelos corrigida de 7 para 6; diagrama de arquitetura (seção 1) corrigido — o Nginx roteia por `server_name` (`api.monitoramento.lan`/`painel.monitoramento.lan`), não por prefixo de path `/api/*` vs `/*`, conforme `Web/BackEnd/nginx/nginx.conf` (confirmado também ao revisar `Context/Infra`); referência a "API key em sessionStorage" corrigida para `localStorage`, alinhado com `Frontend-Documentation.md`.*
