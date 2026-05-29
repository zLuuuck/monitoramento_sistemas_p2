# Banco de Dados — Documentação Técnica

**Versão 1.0 | Maio 2026**

| Campo          | Valor                                                       |
|----------------|-------------------------------------------------------------|
| Projeto        | Monitoramento de Sistemas P2                                |
| Módulo         | Database — PostgreSQL Schema + Retenção                     |
| SGBD           | PostgreSQL 15                                               |
| Ambiente       | Docker Container                                            |
| Equipe         | Lucas Toterol Rodrigues & Caio Federico Esquivel Lovera Arze |

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Diagrama de Relacionamentos](#2-diagrama-de-relacionamentos)
3. [Tabelas](#3-tabelas)
   - 3.1 host
   - 3.2 agents
   - 3.3 host_discovery
   - 3.4 metrics
   - 3.5 logs
   - 3.6 alerts
   - 3.7 active_connections
4. [Índices](#4-índices)
5. [Funções Armazenadas](#5-funções-armazenadas)
6. [Política de Retenção](#6-política-de-retenção)
7. [Padrões de Consulta Frequentes](#7-padrões-de-consulta-frequentes)
8. [Inicialização](#8-inicialização)
9. [Migrações Incrementais](#9-migrações-incrementais)

---

## 1. Visão Geral

O banco de dados é o repositório central de todos os dados coletados pelos agentes. Utiliza **PostgreSQL 15** com os seguintes recursos:

- **JSONB** para armazenamento de dados semi-estruturados (módulos de memória, discos, interfaces de rede, logs parseados)
- **Coluna gerada** (`cpu_ghz`) calculada automaticamente pelo banco
- **Tipo INET** para endereços IP (suporta IPv4 e IPv6 nativamente)
- **Índices parciais** para acelerar queries de alertas de alta utilização (CPU > 85%, memória > 90%)
- **ON DELETE CASCADE** em todas as chaves estrangeiras — remover um host apaga todos os seus dados
- **Função de retenção** para limpeza periódica de dados antigos

O schema completo está em `Web/database/init.sql` e é executado automaticamente pelo Docker na criação do container PostgreSQL.

---

## 2. Diagrama de Relacionamentos

```
host (1)
├─── agents (1:1)           — um agente por host
├─── host_discovery (1:1)   — um inventário de hardware por host
├─── metrics (1:N)          — N snapshots de métricas por host
├─── logs (1:N)             — N linhas de log por host
├─── alerts (1:N)           — N alertas de segurança por host
└─── active_connections (1:N) — N snapshots de conexões TCP por host
```

Todas as tabelas filhas têm `ON DELETE CASCADE` — deletar um registro em `host` propaga para todas as tabelas relacionadas.

---

## 3. Tabelas

### 3.1 host

Tabela central do sistema. Cada host monitorado tem exatamente uma linha aqui.

```sql
CREATE TABLE host (
    id         SERIAL PRIMARY KEY,
    hostname   VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen  TIMESTAMPTZ
);
```

| Coluna     | Tipo           | Descrição                                             |
|------------|----------------|-------------------------------------------------------|
| id         | SERIAL PK      | Identificador numérico auto-incremental               |
| hostname   | VARCHAR(255)   | Nome do host — chave natural, deve ser único          |
| ip_address | INET           | IP principal (atualizado a cada POST de métricas)     |
| created_at | TIMESTAMPTZ    | Quando o host foi registrado pela primeira vez        |
| last_seen  | TIMESTAMPTZ    | Timestamp do último dado recebido (métricas ou logs)  |

**Status online:** calculado dinamicamente no backend — host está "online" se `last_seen > NOW() - 30s`.

---

### 3.2 agents

Registro do agente associado a cada host. Relação 1:1 com `host`.

```sql
CREATE TABLE agents (
    id            SERIAL PRIMARY KEY,
    host_id       INT NOT NULL UNIQUE REFERENCES host(id) ON DELETE CASCADE,
    agent_version VARCHAR(20),
    last_checkin  TIMESTAMPTZ DEFAULT NOW(),
    status        VARCHAR(20) DEFAULT 'active'
);
```

| Coluna        | Tipo         | Descrição                                      |
|---------------|--------------|------------------------------------------------|
| id            | SERIAL PK    | ID do registro de agente                       |
| host_id       | INT FK UNIQUE | Referência ao host (UNIQUE = 1:1)             |
| agent_version | VARCHAR(20)  | Versão do binário (ex: `1.7.0`)               |
| last_checkin  | TIMESTAMPTZ  | Atualizado a cada POST de métricas             |
| status        | VARCHAR(20)  | Estado: `active` (único valor atual)           |

---

### 3.3 host_discovery

Inventário de hardware e sistema operacional. Atualizado sempre que o agente reinicia.

```sql
CREATE TABLE host_discovery (
    host_id             INT PRIMARY KEY REFERENCES host(id) ON DELETE CASCADE,
    discovery_date      TIMESTAMPTZ DEFAULT NOW(),
    cpu_model           VARCHAR(200),
    cpu_cores           SMALLINT,
    cpu_clock_base_mhz  INTEGER,
    cpu_ghz             DECIMAL(4,1) GENERATED ALWAYS AS (cpu_clock_base_mhz / 1000.0) STORED,
    cpu_max_mhz         INTEGER,
    total_memory_gb     DECIMAL(10,2),
    disk_total_gb       DECIMAL(10,2),
    is_virtualized      BOOLEAN,
    hypervisor          VARCHAR(50),
    memories            JSONB,
    disks               JSONB,
    networks            JSONB,
    os_name             VARCHAR(200),
    os_version          VARCHAR(50),
    kernel_release      VARCHAR(200),
    uptime_seconds      INTEGER
);
```

**Coluna gerada:** `cpu_ghz = cpu_clock_base_mhz / 1000.0` — calculada e armazenada automaticamente pelo PostgreSQL, sem custo de query.

**Colunas JSONB:**

| Coluna   | Estrutura típica |
|----------|-----------------|
| memories | `[{"slot": "DIMM A1", "size_gb": 8, "speed_mhz": 3200, "type": "DDR4", "manufacturer": "Samsung"}]` |
| disks    | `[{"device": "/dev/sda", "mountpoint": "/", "fstype": "ext4", "total_gb": 512, "used_gb": 180}]` |
| networks | `[{"interface": "eth0", "ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:ff", "driver": "e1000e", "speed_mbps": 1000}]` |

---

### 3.4 metrics

Série temporal de métricas de desempenho. Tabela de maior crescimento — uma linha por ciclo de 5s por host.

```sql
CREATE TABLE metrics (
    id                     BIGSERIAL PRIMARY KEY,
    host_id                INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    timestamp              TIMESTAMPTZ NOT NULL,
    cpu_percent            DECIMAL(5,2),
    memory_percent         DECIMAL(5,2),
    memory_used_mb         INTEGER,
    memory_free_mb         INTEGER,
    memory_total_mb        INTEGER,
    disk_percent           DECIMAL(5,2),
    disk_used_mb           BIGINT,
    disk_free_mb           BIGINT,
    disk_total_mb          BIGINT,
    net_sent_bytes         BIGINT,
    net_recv_bytes         BIGINT,
    read_iops              FLOAT,
    write_iops             FLOAT,
    read_bytes_per_sec     FLOAT,
    write_bytes_per_sec    FLOAT,
    net_sent_bytes_per_sec FLOAT,
    net_recv_bytes_per_sec FLOAT
);
```

**Crescimento estimado:** com 1 host e ciclo de 5s → ~17.280 linhas/dia → ~120.960 linhas/semana. Com retenção de 7 dias o tamanho se estabiliza.

---

### 3.5 logs

Linhas de log recebidas do agente. Inclui linha bruta e dados estruturados do parsing.

```sql
CREATE TABLE logs (
    id          BIGSERIAL PRIMARY KEY,
    host_id     INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    timestamp   TIMESTAMPTZ NOT NULL,
    log_type    VARCHAR(50),
    raw_line    TEXT,
    parsed_data JSONB
);
```

| Coluna      | Descrição                                                         |
|-------------|-------------------------------------------------------------------|
| log_type    | `auth` (auth.log) ou `system` (syslog/outros)                    |
| raw_line    | Linha original exatamente como estava no arquivo de log           |
| parsed_data | Resultado do `parse_auth_log()` — null se não reconheceu o padrão |

**Estrutura de parsed_data (auth log):**
```json
{
  "event_type": "ssh_login",
  "status": "failed",
  "usuario": "root",
  "ip_origem": "10.0.0.5"
}
```

**Eventos parseados:** `ssh_login`, `sudo`, `pam_auth_failure`, `ssh_disconnect`, `pam_session`, `cron_session`, `sudo_session`, `logind_session`

---

### 3.6 alerts

Alertas de segurança gerados automaticamente pela detecção no backend.

```sql
CREATE TABLE alerts (
    id          BIGSERIAL PRIMARY KEY,
    host_id     INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    alert_type  VARCHAR(50) NOT NULL,
    source_ip   INET NOT NULL,
    timestamp   TIMESTAMPTZ DEFAULT NOW(),
    severity    VARCHAR(20) DEFAULT 'medium',
    metodos     VARCHAR(20),
    message     TEXT,
    resolved    BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ
);
```

**Valores de alert_type:**

| Valor       | Gerado por              | Threshold                               |
|-------------|-------------------------|-----------------------------------------|
| brute_force | `check_brute_force()`   | ≥ 5 falhas SSH em 60s do mesmo IP      |
| port_scan   | `check_port_scan()`     | ≥ 10 portas distintas em 60s via tcpdump |

**Deduplicação:** o backend verifica se já existe um alerta com `resolved=False` para o mesmo `host_id + source_ip + alert_type` antes de criar um novo. Isso evita spam de alertas para ataques contínuos.

**Fluxo de resolução:** `resolved` muda de `FALSE` para `TRUE` via `PATCH /api/alerts/{id}/resolve`. `resolved_at` é preenchido com o timestamp da resolução.

---

### 3.7 active_connections

Snapshot das conexões TCP ativas no momento da coleta. Uma linha por conexão por ciclo.

```sql
CREATE TABLE active_connections (
    id           BIGSERIAL PRIMARY KEY,
    host_id      INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    timestamp    TIMESTAMPTZ NOT NULL,
    src_ip       INET NOT NULL,
    src_port     INTEGER NOT NULL,
    dst_ip       INET NOT NULL,
    dst_port     INTEGER NOT NULL,
    protocol     VARCHAR(10) NOT NULL,
    status       VARCHAR(20),
    duration_sec INTEGER
);
```

**Convenção de nomenclatura:** `src_ip/src_port` é sempre o lado remoto (quem iniciou), `dst_ip/dst_port` é o host monitorado.

**Valores típicos de status:** `ESTABLISHED`, `TIME_WAIT`, `CLOSE_WAIT`, `LISTEN`, `SYN_SENT`

---

## 4. Índices

### Índices em host

| Nome          | Colunas    | Uso                                         |
|---------------|------------|---------------------------------------------|
| idx_host_ip   | ip_address | Lookup de host por IP                       |

### Índices em agents

| Nome                   | Colunas       | Uso                                    |
|------------------------|---------------|----------------------------------------|
| idx_agents_status      | status        | Filtrar agentes ativos                 |
| idx_agents_last_checkin| last_checkin DESC | Encontrar agentes com checkin recente |

### Índices em host_discovery

| Nome                       | Colunas           | Uso                                      |
|----------------------------|-------------------|------------------------------------------|
| idx_discovery_virtualized  | is_virtualized    | Filtrar VMs vs físicos                   |
| idx_discovery_ram          | total_memory_gb   | Ordenar por RAM                          |
| idx_discovery_cpu_model    | cpu_model         | Busca por modelo de CPU                  |
| idx_discovery_disks_gin    | disks (GIN)       | Queries JSONB em estrutura de discos     |
| idx_discovery_networks_gin | networks (GIN)    | Queries JSONB em estrutura de redes      |

### Índices em metrics

| Nome                  | Colunas                         | Uso                                        |
|-----------------------|---------------------------------|--------------------------------------------|
| idx_metrics_host_ts   | (host_id, timestamp DESC)       | Query principal: últimas N métricas de host X |
| idx_metrics_ts        | timestamp                       | Limpeza por retenção                       |
| idx_metrics_high_cpu  | (host_id, timestamp) WHERE cpu_percent > 85 | Alertas de CPU alta (futuro) |
| idx_metrics_high_mem  | (host_id, timestamp) WHERE memory_percent > 90 | Alertas de memória alta (futuro) |

Os dois índices parciais (`high_cpu`, `high_mem`) são índices especializados que só indexam linhas que superam o threshold — zero custo quando CPU/memória estão normais.

### Índices em logs

| Nome                  | Colunas                                                 | Uso                                   |
|-----------------------|---------------------------------------------------------|---------------------------------------|
| idx_logs_host_ts      | (host_id, timestamp DESC)                               | Últimas N linhas de log de host X     |
| idx_logs_type_ts      | (log_type, timestamp DESC)                              | Filtrar por tipo de log               |
| idx_logs_auth_ip      | (parsed_data->>'ip_origem') WHERE log_type = 'auth'    | Busca rápida por IP atacante          |
| idx_logs_auth_failed  | timestamp WHERE log_type = 'auth' AND status = 'failed' | Contagem de falhas para brute force   |
| idx_logs_parsed_gin   | parsed_data (GIN)                                       | Queries JSONB genéricas               |

### Índices em alerts

| Nome                    | Colunas                    | Uso                                      |
|-------------------------|----------------------------|------------------------------------------|
| idx_alerts_host_ts      | (host_id, timestamp DESC)  | Alertas de um host em ordem cronológica  |
| idx_alerts_type_ts      | (alert_type, timestamp DESC)| Filtrar por tipo de alerta              |
| idx_alerts_source_ip_ts | (source_ip, timestamp DESC) | Histórico de ataques de um IP           |

### Índices em active_connections

| Nome               | Colunas                     | Uso                                         |
|--------------------|-----------------------------|---------------------------------------------|
| idx_conn_host_ts   | (host_id, timestamp DESC)   | Últimas conexões de um host                 |
| idx_conn_status    | status                      | Filtrar por estado TCP                      |
| idx_conn_dst_ip_ts | (dst_ip, timestamp DESC)    | Conexões para um IP de destino específico   |
| idx_conn_duration  | duration_sec WHERE > 3600   | Conexões de longa duração (> 1 hora)        |

---

## 5. Funções Armazenadas

### cleanup_old_data

```sql
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 7)
RETURNS VOID AS $$
BEGIN
    DELETE FROM metrics         WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    DELETE FROM logs            WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    DELETE FROM active_connections WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;
```

**Tabelas limpas:** `metrics`, `logs`, `active_connections`  
**Não afeta:** `host`, `agents`, `host_discovery`, `alerts` (dados permanentes ou gerenciados manualmente)

**Chamada manual:**
```sql
SELECT cleanup_old_data(7);   -- apaga dados com mais de 7 dias
SELECT cleanup_old_data(30);  -- apaga dados com mais de 30 dias
```

Não há trigger automático — a função deve ser chamada manualmente ou via cron externo ao container.

---

## 6. Política de Retenção

| Tabela              | Retida pela função | Critério de limpeza            |
|---------------------|--------------------|--------------------------------|
| metrics             | Sim                | timestamp > N dias             |
| logs                | Sim                | timestamp > N dias             |
| active_connections  | Sim                | timestamp > N dias             |
| host                | Não                | Permanente (gerenciado manualmente) |
| agents              | Não                | Permanente                     |
| host_discovery      | Não                | Permanente (sobrescrito no restart do agente) |
| alerts              | Não                | Permanente (resolvidos manualmente) |

**Padrão configurado:** 7 dias. Alterar passando `days_to_keep` diferente na chamada da função.

---

## 7. Padrões de Consulta Frequentes

### Últimas métricas de um host (dashboard)
```sql
SELECT * FROM metrics
WHERE host_id = :host_id
ORDER BY timestamp DESC
LIMIT 30;
```
Usa `idx_metrics_host_ts`.

### Verificar se host está online
```sql
SELECT last_seen > NOW() - INTERVAL '30 seconds' AS is_online
FROM host WHERE id = :host_id;
```

### Contar falhas SSH de um IP na última hora (brute force)
```sql
SELECT COUNT(*) FROM logs
WHERE host_id = :host_id
  AND log_type = 'auth'
  AND timestamp > NOW() - INTERVAL '1 hour'
  AND parsed_data->>'status' = 'failed'
  AND parsed_data->>'ip_origem' = :ip_origem;
```
Usa `idx_logs_auth_failed` + `idx_logs_auth_ip`.

### Verificar alerta ativo existente (deduplicação)
```sql
SELECT id FROM alerts
WHERE host_id = :host_id
  AND source_ip = :ip_origem
  AND alert_type = :tipo
  AND resolved = FALSE
LIMIT 1;
```
Usa `idx_alerts_host_ts`.

### Alertas ativos ordenados (frontend)
```sql
SELECT * FROM alerts
WHERE resolved = FALSE
ORDER BY timestamp DESC
LIMIT 20;
```
Usa `idx_alerts_type_ts`.

---

## 8. Inicialização

O arquivo `Web/database/init.sql` é executado automaticamente pelo Docker na **primeira** criação do volume PostgreSQL. Nas execuções subsequentes, se o volume já existir, o init.sql é ignorado.

Para recriar o schema do zero:
```bash
# No docker-compose, derruba containers e apaga volumes
docker compose down -v
docker compose up -d
```

> Apaga todos os dados. Só use em ambiente de desenvolvimento.

---

## 9. Migrações Incrementais

Campos adicionados após a criação inicial do banco são aplicados pelo backend no startup via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Não requer recriar o container ou o volume.

Histórico de migrações incrementais:

| Função no backend                  | Campos adicionados                                                                 | Quando |
|------------------------------------|------------------------------------------------------------------------------------|--------|
| `garantir_schema_discovery()`      | `os_name`, `os_version`, `kernel_release`, `uptime_seconds`, `motherboard`        | Semana 3 |
| `garantir_schema_metrics()`        | `memory_used_mb`, `memory_free_mb`, `memory_total_mb`, `disk_used_mb`, `disk_free_mb`, `disk_total_mb` | Semana 2 |
| `garantir_schema_alerts()`         | `resolved`, `resolved_at`                                                          | Semana 5 |
| `garantir_schema_alerts_message()` | `message`                                                                          | Semana 6 |
| `garantir_schema_iops()`           | `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `net_sent_bytes_per_sec`, `net_recv_bytes_per_sec` | Semana 7 |

---

*Para documentação técnica do backend, consulte [Context/Backend/Backend-Documentation.md](../Backend/Backend-Documentation.md).*
*Para documentação do agente, consulte [Context/Agent/Agent-Documentation.md](../Agent/Agent-Documentation.md).*
