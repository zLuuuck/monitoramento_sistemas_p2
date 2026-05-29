# Backend — Documentação Técnica

**Versão 1.0 | Maio 2026**

| Campo             | Valor                                                       |
|-------------------|-------------------------------------------------------------|
| Projeto           | Monitoramento de Sistemas P2                                |
| Módulo            | Backend — API Flask + Modelos + Detecção de Segurança       |
| Linguagem         | Python 3.12 + Flask + SQLAlchemy                            |
| Banco de Dados    | PostgreSQL 15                                               |
| Ambiente          | Docker Container                                            |
| Equipe            | Lucas Toterol Rodrigues & Caio Federico Esquivel Lovera Arze |

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Inicialização da Aplicação](#3-inicialização-da-aplicação)
4. [Modelos de Dados](#4-modelos-de-dados)
   - 4.1 HostModel
   - 4.2 AgentModel
   - 4.3 HostDiscoveryModel
   - 4.4 MetricModel
   - 4.5 LogEntryModel
   - 4.6 AlertModel
   - 4.7 ActiveConnectionModel
5. [Rotas — Endpoints](#5-rotas--endpoints)
   - 5.1 Discovery (`/api/discovery`)
   - 5.2 Metrics (`/api/metrics`)
   - 5.3 Logs (`/api/logs`)
   - 5.4 Alerts (`/api/alerts`)
   - 5.5 Connections (`/api/connections`)
   - 5.6 Endpoints Gerais
6. [Utilitários — Detecção de Segurança](#6-utilitários--detecção-de-segurança)
   - 6.1 check_brute_force
   - 6.2 check_port_scan
7. [Utilitários — Parsing de Logs](#7-utilitários--parsing-de-logs)
8. [Variáveis de Ambiente](#8-variáveis-de-ambiente)
9. [Migrações de Schema](#9-migrações-de-schema)
10. [Dependências](#10-dependências)
11. [Resumo dos Endpoints](#11-resumo-dos-endpoints)

---

## 1. Visão Geral

O backend é uma API REST construída com **Flask** e **SQLAlchemy**, responsável por:

- **Receber dados do agente** — cada host monitorado envia payloads a cada 5 segundos: discovery (hardware), métricas (CPU/RAM/disco/rede), logs de autenticação e conexões TCP ativas.
- **Persistir no PostgreSQL** — todos os dados são armazenados nas tabelas correspondentes para consulta histórica.
- **Detectar ameaças** — analisa logs e sinais do agente para gerar alertas de brute force e port scan.
- **Servir o frontend** — expõe endpoints de consulta paginados que alimentam o dashboard React.

A aplicação é **stateless**: não mantém sessão nem estado em memória entre requisições. Toda a lógica de deduplicação de alertas é feita consultando o banco.

---

## 2. Estrutura de Diretórios

```
Web/BackEnd/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── app/
    ├── app.py                  ← aplicação principal, startup e rotas gerais
    ├── models/
    │   ├── __init__.py         ← registrar_modelos() — exporta todos os modelos
    │   ├── host.py
    │   ├── agent.py
    │   ├── discovery.py
    │   ├── metric.py
    │   ├── log.py
    │   ├── alert.py
    │   └── connection.py
    ├── routes/
    │   ├── __init__.py         ← exporta as funções register_*_routes
    │   ├── discovery.py
    │   ├── metrics.py
    │   ├── logs.py
    │   ├── alerts.py
    │   └── connections.py
    └── utils/
        ├── __init__.py
        ├── detection.py        ← check_brute_force, check_port_scan
        └── parsers.py          ← parse_auth_log, count_failed_logins
```

**Padrão de injeção de dependências:** cada blueprint recebe modelos e funções como parâmetro na função `register_*_routes()`. Nenhum arquivo de rota importa modelos diretamente — isso evita importações circulares.

---

## 3. Inicialização da Aplicação

O arquivo `app.py` segue esta sequência na inicialização:

| Etapa | Descrição |
|-------|-----------|
| 1 | Flask instanciado com CORS habilitado globalmente |
| 2 | Configuração de `DATABASE_URL` (env var ou fallback local) |
| 3 | `registrar_modelos(db)` — cria todas as classes de modelo |
| 4 | `garantir_schema_*()` — aplica ALTER TABLE migrations seguras |
| 5 | `register_*_routes()` — registra os blueprints de rota |
| 6 | Endpoints gerais definidos inline (`/api/status`, `/api/hello`, `/health`, `/api/hosts`) |

---

## 4. Modelos de Dados

Todos os modelos são registrados em `models/__init__.py` via `registrar_modelos(db)`, que retorna uma tupla com 7 classes na ordem:
`(HostModel, AgentModel, HostDiscoveryModel, MetricModel, LogEntryModel, AlertModel, ActiveConnectionModel)`

### 4.1 HostModel

**Tabela:** `host`

| Coluna       | Tipo           | Descrição                                 |
|--------------|----------------|-------------------------------------------|
| id           | SERIAL PK      | Identificador único                       |
| hostname     | VARCHAR(255)   | Nome do host (UNIQUE NOT NULL)            |
| ip_address   | INET           | IP principal do host                      |
| created_at   | TIMESTAMPTZ    | Data de primeiro cadastro                 |
| last_seen    | TIMESTAMPTZ    | Timestamp da última métrica recebida      |

`to_dict()` inclui campo calculado `is_online`: True se `last_seen` for dentro dos últimos 30 segundos.

### 4.2 AgentModel

**Tabela:** `agents`

| Coluna          | Tipo         | Descrição                                  |
|-----------------|--------------|--------------------------------------------|
| id              | SERIAL PK    | Identificador único                        |
| host_id         | INT FK       | Referência a `host.id` (ON DELETE CASCADE) |
| agent_version   | VARCHAR(20)  | Versão do binário do agente                |
| last_checkin    | TIMESTAMPTZ  | Último heartbeat ou coleta recebida        |
| status          | VARCHAR(20)  | Estado do agente (`active`, etc.)          |

### 4.3 HostDiscoveryModel

**Tabela:** `host_discovery`

| Coluna              | Tipo             | Descrição                                      |
|---------------------|------------------|------------------------------------------------|
| host_id             | INT PK FK        | Chave primária = chave estrangeira de `host`   |
| discovery_date      | TIMESTAMPTZ      | Quando o discovery foi executado               |
| cpu_model           | VARCHAR(200)     | Modelo do processador                          |
| cpu_cores           | SMALLINT         | Número de núcleos físicos                      |
| cpu_clock_base_mhz  | INTEGER          | Clock base em MHz                              |
| cpu_ghz             | DECIMAL(4,1)     | **Coluna gerada** = cpu_clock_base_mhz / 1000  |
| cpu_max_mhz         | INTEGER          | Clock máximo em MHz                            |
| total_memory_gb     | DECIMAL(10,2)    | RAM total em GB                                |
| disk_total_gb       | DECIMAL(10,2)    | Capacidade total de disco em GB                |
| is_virtualized      | BOOLEAN          | True se VM                                     |
| hypervisor          | VARCHAR(50)      | KVM, VMware, Xen, Hyper-V, etc.               |
| memories            | JSONB            | Módulos de RAM com slots, speed, tipo          |
| disks               | JSONB            | Partições com tamanho, filesystem, mountpoint  |
| networks            | JSONB            | Interfaces com IP, MAC, driver                 |
| os_name             | VARCHAR(200)     | Nome do sistema operacional                    |
| os_version          | VARCHAR(50)      | Versão do OS                                   |
| kernel_release      | VARCHAR(200)     | Kernel (ex: 6.8.0-45-generic)                 |
| uptime_seconds      | INTEGER          | Uptime em segundos no momento do discovery     |

### 4.4 MetricModel

**Tabela:** `metrics`

| Coluna                 | Tipo          | Descrição                              |
|------------------------|---------------|----------------------------------------|
| id                     | BIGSERIAL PK  | ID da métrica                          |
| host_id                | INT FK        | Host ao qual a métrica pertence        |
| timestamp              | TIMESTAMPTZ   | Quando a coleta foi feita              |
| cpu_percent            | DECIMAL(5,2)  | % de uso de CPU                        |
| memory_percent         | DECIMAL(5,2)  | % de uso de memória                    |
| memory_used_mb         | INTEGER       | RAM usada em MB                        |
| memory_free_mb         | INTEGER       | RAM livre em MB                        |
| memory_total_mb        | INTEGER       | RAM total em MB                        |
| disk_percent           | DECIMAL(5,2)  | % de uso de disco                      |
| disk_used_mb           | BIGINT        | Disco usado em MB                      |
| disk_free_mb           | BIGINT        | Disco livre em MB                      |
| disk_total_mb          | BIGINT        | Disco total em MB                      |
| net_sent_bytes         | BIGINT        | Total de bytes enviados (acumulado)    |
| net_recv_bytes         | BIGINT        | Total de bytes recebidos (acumulado)   |
| read_iops              | FLOAT         | Operações de leitura por segundo       |
| write_iops             | FLOAT         | Operações de escrita por segundo       |
| read_bytes_per_sec     | FLOAT         | Bytes lidos por segundo                |
| write_bytes_per_sec    | FLOAT         | Bytes escritos por segundo             |
| net_sent_bytes_per_sec | FLOAT         | Bytes de rede enviados por segundo     |
| net_recv_bytes_per_sec | FLOAT         | Bytes de rede recebidos por segundo    |

### 4.5 LogEntryModel

**Tabela:** `logs`

| Coluna      | Tipo          | Descrição                                             |
|-------------|---------------|-------------------------------------------------------|
| id          | BIGSERIAL PK  | ID do evento                                          |
| host_id     | INT FK        | Host de origem                                        |
| timestamp   | TIMESTAMPTZ   | Timestamp do evento no log                            |
| log_type    | VARCHAR(50)   | Tipo: `auth`, `system`                                |
| raw_line    | TEXT          | Linha original do arquivo de log                      |
| parsed_data | JSONB         | Campos parseados (event_type, status, usuario, ip_origem, etc.) |

### 4.6 AlertModel

**Tabela:** `alerts`

| Coluna      | Tipo          | Descrição                                             |
|-------------|---------------|-------------------------------------------------------|
| id          | BIGSERIAL PK  | ID do alerta                                          |
| host_id     | INT FK        | Host onde o ataque foi detectado                      |
| alert_type  | VARCHAR(50)   | `brute_force` ou `port_scan`                          |
| source_ip   | INET          | IP de origem do ataque                                |
| timestamp   | TIMESTAMPTZ   | Quando o alerta foi criado                            |
| severity    | VARCHAR(20)   | `low`, `medium`, `high`, `critical`                   |
| metodos     | VARCHAR(20)   | `password` (brute force) ou null (port scan)          |
| message     | TEXT          | Descrição legível (ex: "Força bruta SSH: 8 tentativas em 60s de 10.0.0.5") |
| resolved    | BOOLEAN       | False = alerta ativo                                  |
| resolved_at | TIMESTAMPTZ   | Quando foi resolvido manualmente                      |

### 4.7 ActiveConnectionModel

**Tabela:** `active_connections`

| Coluna      | Tipo          | Descrição                                          |
|-------------|---------------|----------------------------------------------------|
| id          | BIGSERIAL PK  | ID do registro                                     |
| host_id     | INT FK        | Host monitorado                                    |
| timestamp   | TIMESTAMPTZ   | Quando a snapshot foi coletada                     |
| src_ip      | INET          | IP remoto (quem iniciou a conexão)                 |
| src_port    | INTEGER       | Porta efêmera do lado remoto                       |
| dst_ip      | INET          | IP do host monitorado                              |
| dst_port    | INTEGER       | Porta do serviço no host monitorado                |
| protocol    | VARCHAR(10)   | Sempre `tcp`                                       |
| status      | VARCHAR(20)   | Estado TCP: `ESTABLISHED`, `TIME_WAIT`, etc.       |
| duration_sec| INTEGER       | Duração da conexão em segundos (pode ser null)     |

---

## 5. Rotas — Endpoints

### 5.1 Discovery (`/api/discovery`)

**`POST /api/discovery`** — Recebe inventário de hardware e SO do agente.

Payload esperado:
```json
{
  "global": { "host_id": "abc123", "hostname": "servidor-01", "primary_ip": "192.168.1.10" },
  "cpu": { "model": "Intel Core i7", "cores": 8, "clock_base_mhz": 3600, "max_mhz": 4800 },
  "memory": { "total_gb": 16.0, "modules": [...] },
  "disk": { "total_gb": 512.0, "partitions": [...] },
  "network": { "interfaces": [...] },
  "system": { "os_name": "Ubuntu", "os_version": "22.04", "kernel_release": "6.8.0", "uptime_seconds": 3600 },
  "is_virtualized": false,
  "hypervisor": null,
  "notes": []
}
```

Fluxo interno:
1. Upsert em `host` (hostname → id)
2. Upsert em `agents` (host_id, agent_version)
3. Upsert em `host_discovery` com todos os campos
4. Atualiza `host.last_seen`

Resposta `201`:
```json
{
  "message": "Discovery recebido com sucesso",
  "discovery_id": 1,
  "host_id": 1,
  "hostname": "servidor-01",
  "ip_host": "192.168.1.10",
  "is_virtualized": false
}
```

---

**`GET /api/discovery?host_id=N`** — Lista todos os discoveries ou de um host específico.

Resposta `200`:
```json
{
  "discoveries": [
    {
      "host_id": 1,
      "hostname": "servidor-01",
      "ip_address": "192.168.1.10",
      "is_online": true,
      "cpu_model": "Intel Core i7",
      "cpu_cores": 8,
      ...
    }
  ],
  "total": 1
}
```

---

### 5.2 Metrics (`/api/metrics`)

**`POST /api/metrics`** — Recebe snapshot de métricas de desempenho do agente.

Payload esperado:
```json
{
  "global": { "host_id": "abc123", "hostname": "servidor-01", "primary_ip": "192.168.1.10" },
  "timestamp": "2026-05-29T12:00:00",
  "cpu": { "percent": 45.2 },
  "memory": { "percent": 68.1, "used_mb": 10900, "free_mb": 5100, "total_mb": 16000 },
  "disk": { "percent": 72.4, "used_mb": 180000, "free_mb": 70000, "total_mb": 250000 },
  "network": { "bytes_sent": 1024000, "bytes_recv": 2048000 },
  "iops": { "read_iops": 120.5, "write_iops": 45.2, "read_bytes_per_sec": 5120000, "write_bytes_per_sec": 1024000 },
  "net_rate": { "bytes_sent_per_sec": 8192.0, "bytes_recv_per_sec": 16384.0 }
}
```

Normalização aplicada: bytes → MB para `net_sent_bytes` e `net_recv_bytes`.

Atualiza `host.last_seen` e `agents.last_checkin` a cada POST.

Resposta `201`:
```json
{
  "message": "Métricas recebidas com sucesso",
  "metric_id": 123,
  "host_id": 1,
  "timestamp": "2026-05-29T12:00:00"
}
```

---

**`GET /api/metrics?host_id=N&limit=20&offset=0`** — Consulta métricas paginadas.

| Parâmetro | Tipo    | Default | Máximo |
|-----------|---------|---------|--------|
| host_id   | integer | —       | —      |
| limit     | integer | 20      | 100    |
| offset    | integer | 0       | —      |

Resposta `200`:
```json
{
  "metrics": [...],
  "total": 1440,
  "hostname": "servidor-01",
  "is_online": true,
  "status": "online"
}
```

---

### 5.3 Logs (`/api/logs`)

**`POST /api/logs`** — Recebe linhas de log do agente (uma por requisição).

Payload esperado:
```json
{
  "global": { "host_id": "abc123", "primary_ip": "192.168.1.10" },
  "timestamp": "2026-05-29T12:00:00",
  "log_type": "auth",
  "raw_line": "May 29 12:00:01 servidor-01 sshd[1234]: Failed password for root from 10.0.0.5 port 54321 ssh2"
}
```

Fluxo interno:
1. Tenta parsear a linha com `parse_auth_log()` → salva em `parsed_data`
2. Se `parsed_data.status == "failed"`, chama `check_brute_force()`
3. Persiste em `logs`

Resposta `201`:
```json
{
  "message": "Log recebido com sucesso",
  "log_id": 456,
  "host_id": 1,
  "log_type": "auth",
  "parsed": true,
  "event_type": "ssh_login",
  "alerta_criado": false
}
```

---

**`GET /api/logs?host_id=N&limit=50&offset=0&log_type=auth`** — Consulta logs paginados.

Resposta `200`:
```json
{
  "logs": [...],
  "total": 320,
  "hostname": "servidor-01",
  "log_type": "auth"
}
```

---

### 5.4 Alerts (`/api/alerts`)

**`GET /api/alerts?status=active&host_id=N&limit=20&offset=0`** — Lista alertas.

| Parâmetro | Valores             | Default  |
|-----------|---------------------|----------|
| status    | active, resolved, all | active |
| host_id   | integer             | (todos)  |
| limit     | integer             | 20       |
| offset    | integer             | 0        |

Resposta `200`:
```json
{
  "alerts": [
    {
      "id": 1,
      "host_id": 1,
      "alert_type": "brute_force",
      "source_ip": "10.0.0.5",
      "timestamp": "2026-05-29T12:00:00",
      "severity": "high",
      "metodos": "password",
      "message": "Força bruta SSH: 8 tentativas em 60s de 10.0.0.5",
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

---

**`PATCH /api/alerts/{alerta_id}/resolve`** — Resolve um alerta manualmente.

Resposta `200`:
```json
{
  "message": "Alerta resolvido com sucesso",
  "alert": { ...alerta completo com resolved=true... }
}
```

Erros:
- `404` — alerta não encontrado
- `400` — alerta já estava resolvido

---

### 5.5 Connections (`/api/connections`)

**`POST /api/connections`** — Recebe conexões TCP ativas e flag de port scan do agente.

Payload esperado:
```json
{
  "global": { "host_id": "abc123", "primary_ip": "192.168.1.10" },
  "timestamp": "2026-05-29T12:00:00",
  "connections": [
    {
      "remote_ip": "10.0.0.5",
      "remote_port": 54321,
      "local_port": 22,
      "state": "ESTABLISHED",
      "duration_sec": 120
    }
  ],
  "port_scan_detected": true,
  "scan_sources": {
    "10.0.0.5": 45
  }
}
```

Mapeamento agente → banco:

| Campo do agente | Coluna no banco   | Descrição                    |
|-----------------|-------------------|------------------------------|
| remote_ip       | src_ip            | IP externo que conectou      |
| remote_port     | src_port          | Porta efêmera do externo     |
| local_port      | dst_port          | Porta do serviço no host     |
| state           | status            | Estado TCP                   |
| (global)primary_ip | dst_ip         | IP do host monitorado        |

Fluxo de detecção:
- Se `scan_sources` presente: cria um alerta por IP atacante com contagem de portas
- Fallback (payload antigo sem `scan_sources`): usa IP mais frequente nas conexões

Resposta `201`:
```json
{
  "mensagem": "Conexões recebidas com sucesso",
  "host_id": 1,
  "total_salvo": 12,
  "port_scan_flag": true,
  "scan_sources": { "10.0.0.5": 45 },
  "alertas_criados": 1
}
```

---

### 5.6 Endpoints Gerais

| Método | Rota           | Descrição                                          |
|--------|----------------|----------------------------------------------------|
| GET    | `/api/status`  | Health check com versão da API                     |
| GET    | `/api/hello`   | Endpoint de teste                                  |
| GET    | `/health`      | Health probe para Docker/container orchestration   |
| GET    | `/api/hosts`   | Lista todos os hosts (parâmetro `include_discovery=true` para incluir hardware) |

---

## 6. Utilitários — Detecção de Segurança

Arquivo: `utils/detection.py`

As duas funções são **injetadas** nas rotas que precisam delas — não são importadas diretamente pelos blueprints.

### 6.1 check_brute_force

```python
check_brute_force(db, LogEntryModel, AlertModel, host_id, ip_origem) → bool
```

| Etapa | Ação |
|-------|------|
| 1 | Conta falhas SSH de `ip_origem` no `host_id` nos últimos 60s via `count_failed_logins()` |
| 2 | Se contagem < 5: retorna False |
| 3 | Verifica se já existe alerta ativo (`resolved=False`) para o mesmo host_id + ip_origem + brute_force |
| 4 | Se alerta ativo: retorna False (não duplica) |
| 5 | Cria `AlertModel` com severity=high, metodos=password, message descritivo |
| 6 | Retorna True |

Threshold: **5 falhas em 60 segundos**

### 6.2 check_port_scan

```python
check_port_scan(db, AlertModel, host_id, ip_origem, port_count=0) → bool
```

| Etapa | Ação |
|-------|------|
| 1 | Verifica se já existe alerta ativo para host_id + ip_origem + port_scan |
| 2 | Se ativo: retorna False |
| 3 | Cria `AlertModel` com severity=high, message incluindo o número de portas distintas varridas |
| 4 | Retorna True |

A detecção em si (contagem de SYNs) é feita **no agente** via tcpdump. O backend apenas persiste o alerta quando recebe o sinal.

---

## 7. Utilitários — Parsing de Logs

Arquivo: `utils/parsers.py`

### Orquestrador

```python
parse_auth_log(raw_line) → dict | None
```

Tenta os parsers na seguinte ordem de prioridade. Retorna o primeiro resultado não-nulo.

| Prioridade | Parser                    | Detecta                                      |
|-----------|---------------------------|----------------------------------------------|
| 1         | `parse_ssh_log()`         | `Failed/Accepted password` para SSH          |
| 2         | `parse_sudo()`            | Execução de comandos via `sudo`              |
| 3         | `parse_pam_auth_failure()`| Falhas de autenticação PAM genéricas         |
| 4         | `parse_ssh_disconnect()`  | Desconexões SSH                              |
| 5         | `parse_pam_session()`     | Abertura/fechamento de sessões PAM/CRON/sudo |
| 6         | `parse_logind_session()`  | Eventos de sessão do systemd-logind          |

### Campos do parsed_data

| Campo       | Tipo   | Descrição                                   |
|-------------|--------|---------------------------------------------|
| event_type  | string | ssh_login, sudo, pam_auth_failure, pam_session, etc. |
| status      | string | failed, accepted, session_open, session_close, sudo_exec |
| usuario     | string | Nome do usuário envolvido                   |
| ip_origem   | string | IP de origem (quando disponível)            |
| servico     | string | Serviço PAM (quando disponível)             |
| comando     | string | Comando executado (sudo apenas)             |

### Contagem de falhas

```python
count_failed_logins(LogEntryModel, host_id, ip_origem, janela_horas=1) → int
```

Faz query diretamente no PostgreSQL usando operadores JSONB:
```sql
WHERE host_id = :host_id
  AND log_type = 'auth'
  AND timestamp > (NOW() - interval '1 hour')
  AND parsed_data->>'status' = 'failed'
  AND parsed_data->>'ip_origem' = :ip_origem
```

Retorna 0 em caso de erro (silent failure — não deve interromper o fluxo).

---

## 8. Variáveis de Ambiente

| Variável       | Default                                        | Descrição                       |
|----------------|------------------------------------------------|---------------------------------|
| `DATABASE_URL` | `postgresql://monitor:monitor@localhost:5432/monitor` | String de conexão PostgreSQL |
| `PORT`         | `5000`                                         | Porta do servidor Flask         |
| `FLASK_DEBUG`  | `True`                                         | Modo debug (False em produção)  |

Em Docker, as variáveis são injetadas pelo `docker-compose.yml`.

---

## 9. Migrações de Schema

O backend não usa Alembic. Em vez disso, cada novo campo adicionado ao banco após a criação inicial tem uma função `garantir_schema_*()` que roda no startup via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Isso garante que bancos criados antes do `init.sql` atual sejam atualizados sem recriar o container.

| Função                         | Adiciona                                            |
|--------------------------------|-----------------------------------------------------|
| `garantir_schema_discovery()`  | `os_name`, `os_version`, `kernel_release`, `uptime_seconds`, `motherboard` em `host_discovery` |
| `garantir_schema_metrics()`    | `memory_used_mb`, `memory_free_mb`, `memory_total_mb`, `disk_used_mb`, `disk_free_mb`, `disk_total_mb` em `metrics` |
| `garantir_schema_alerts()`     | `resolved`, `resolved_at` em `alerts`               |
| `garantir_schema_alerts_message()` | `message` em `alerts`                          |
| `garantir_schema_iops()`       | `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `net_sent_bytes_per_sec`, `net_recv_bytes_per_sec` em `metrics` |

---

## 10. Dependências

| Pacote           | Finalidade                              |
|------------------|-----------------------------------------|
| Flask            | Framework web                           |
| Flask-CORS       | Headers CORS para o frontend React      |
| Flask-SQLAlchemy | ORM sobre PostgreSQL                    |
| psycopg2-binary  | Driver PostgreSQL                       |
| python-dotenv    | Carrega variáveis de ambiente do `.env` |

---

## 11. Resumo dos Endpoints

| Método | Rota                           | Descrição                                   |
|--------|--------------------------------|---------------------------------------------|
| POST   | `/api/discovery`               | Recebe inventário de hardware do agente     |
| GET    | `/api/discovery`               | Lista discoveries (com status online)       |
| POST   | `/api/metrics`                 | Recebe snapshot de métricas                 |
| GET    | `/api/metrics`                 | Consulta métricas paginadas                 |
| POST   | `/api/logs`                    | Recebe linha de log (com parsing automático)|
| GET    | `/api/logs`                    | Consulta logs paginados                     |
| GET    | `/api/alerts`                  | Lista alertas (active/resolved/all)         |
| PATCH  | `/api/alerts/{id}/resolve`     | Resolve alerta manualmente                  |
| POST   | `/api/connections`             | Recebe conexões TCP + flag port scan        |
| GET    | `/api/status`                  | Health check da API                         |
| GET    | `/api/hello`                   | Endpoint de teste                           |
| GET    | `/health`                      | Probe de container                          |
| GET    | `/api/hosts`                   | Lista todos os hosts                        |

---

*Para documentação técnica do agente, consulte [Context/Agent/Agent-Documentation.md](../Agent/Agent-Documentation.md).*
*Para documentação do banco de dados, consulte [Context/Database/Database-Documentation.md](../Database/Database-Documentation.md).*
