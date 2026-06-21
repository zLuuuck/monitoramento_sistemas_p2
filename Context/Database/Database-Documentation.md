# Banco de Dados — Documentação Técnica

**Versão 1.4 | Junho 2026**

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
- **VARCHAR(45)** para endereços IP — suporta IPv4 e IPv6 sem as restrições de tipo INET para campos de origem externa
- **Índices parciais** para acelerar queries de alertas de alta utilização
- **ON DELETE CASCADE** em todas as chaves estrangeiras
- **Função de retenção** para limpeza periódica de dados antigos

O schema base está em `Web/database/init.sql`. O backend aplica migrações incrementais via `ALTER TABLE` no startup — ver seção 9.

> **Nota:** o `init.sql` foi consolidado (commit `3b7189a`) e reflete o schema atual de produção — inclui todas as colunas e exclui `active_connections`. Novos ambientes criados com o `init.sql` atual partem do schema correto; as funções `garantir_schema_*` são idempotentes e não causam erro em bancos já atualizados.

---

## 2. Diagrama de Relacionamentos

```
host (1)
├─── agents (1:1)              — um agente por host
├─── host_discovery (1:1)      — um inventário de hardware por host
├─── metrics (1:N)             — N snapshots de métricas por host
├─── logs (1:N)                — N linhas de log por host
└─── alerts (1:N)              — N alertas de segurança por host

app_settings (independente)    — configurações do sistema (API key, email, thresholds, toggles)
```

Todas as tabelas filhas têm `ON DELETE CASCADE` — deletar um host propaga para todas as tabelas relacionadas. `app_settings` não tem FK com `host`.

> **Nota:** a tabela `active_connections` existiu durante o desenvolvimento (Semanas 6–7) e foi removida. Ver seção 10 — Evolução do Projeto.

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
| last_seen  | TIMESTAMPTZ    | Timestamp do último dado recebido                     |

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
    motherboard         JSONB,
    os_name             VARCHAR(200),
    os_version          VARCHAR(50),
    kernel_release      VARCHAR(200),
    uptime_seconds      INTEGER
);
```

**Coluna gerada:** `cpu_ghz = cpu_clock_base_mhz / 1000.0` — calculada e armazenada automaticamente pelo PostgreSQL.

> As colunas `os_name`, `os_version`, `kernel_release`, `uptime_seconds` e `motherboard` já fazem parte do `init.sql` consolidado (criadas diretamente na `CREATE TABLE`). A função `garantir_schema_discovery()` continua existindo no backend (`ADD COLUMN IF NOT EXISTS`) apenas para atualizar volumes antigos criados antes da consolidação — em um ambiente novo ela não tem efeito (colunas já existem).

---

### 3.4 metrics

Série temporal de métricas de desempenho. Tabela de maior crescimento — uma linha por ciclo de ~5s por host.

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

**Crescimento estimado:** ~17.280 linhas/dia por host com ciclo de 5s. Sem retenção ativa, a tabela cresce indefinidamente.

> As colunas de `memory_*_mb`, `disk_*_mb` e `*_iops`, `*_bytes_per_sec` já fazem parte do `init.sql` consolidado. `garantir_schema_metrics()` e `garantir_schema_iops()` continuam no backend apenas para atualizar volumes antigos pré-consolidação.

---

### 3.5 logs

Linhas de log recebidas do agente com dados estruturados do parsing.

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
  "ip_origem": "10.10.10.26"
}
```

**Eventos parseados:** `ssh_login`, `sudo`, `pam_auth_failure`, `ssh_disconnect`, `pam_session`, `cron_session`, `sudo_session`, `logind_session`

---

### 3.6 alerts

Alertas de segurança gerados automaticamente pela detecção no backend.

```sql
-- Estado efetivo em runtime (após migrações):
CREATE TABLE alerts (
    id          BIGSERIAL PRIMARY KEY,
    host_id     INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    alert_type  VARCHAR(50) NOT NULL,
    source_ip   VARCHAR(45),              -- nullable: NULL para alertas de recurso
    timestamp   TIMESTAMPTZ DEFAULT NOW(),
    severity    VARCHAR(20) DEFAULT 'medium',
    metodos     VARCHAR(20),
    message     TEXT,
    resolved    BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ
);
```

> **Atenção:** o `init.sql` consolidado já declara `source_ip VARCHAR(45)` nullable diretamente — o tipo `INET NOT NULL` só existia em versões anteriores (pré-consolidação) do arquivo. A migração `garantir_schema_alerts_source_ip()` permanece no backend apenas para corrigir volumes antigos que ainda tenham a coluna no formato original.

**Valores de alert_type:**

| Valor       | Gerado por              | Threshold / Condição                          |
|-------------|-------------------------|-----------------------------------------------|
| brute_force | `check_brute_force()`   | ≥ 5 falhas SSH em 60s do mesmo IP            |
| port_scan   | `check_port_scan()`     | ≥ 10 portas distintas em 60s via tcpdump     |
| cpu_high    | `check_resource_alert()`| CPU > 80%                                    |
| mem_high    | `check_resource_alert()`| Memória > 80%                                |
| disk_high   | `check_resource_alert()`| Disco > 80%                                  |

**`source_ip` por tipo de alerta:**
- `brute_force`, `port_scan`: IP do atacante (string IPv4 ou IPv6)
- `cpu_high`, `mem_high`, `disk_high`: `NULL` — alertas de recurso não têm origem de rede

**Deduplicação:**
- `brute_force`: um alerta ativo por `host_id + source_ip + alert_type` enquanto `resolved=False`
- `port_scan`: um alerta por `host_id + source_ip` nos últimos **2 minutos** — permite novos alertas para novos scans sem precisar resolver o anterior
- `cpu_high` / `mem_high` / `disk_high`: um alerta ativo por `host_id + alert_type` enquanto `resolved=False`

**Fluxo de resolução:** `PATCH /api/alerts/{id}/resolve` define `resolved=TRUE`, `resolved_at=NOW()`.

---

### ~~3.7 active_connections~~ — REMOVIDA

> **Esta tabela foi removida** (commit `3b7189a`, Semana 7). Havia sido criada para registrar snapshots de conexões TCP via `psutil.net_connections()`, mas nunca teve tela consumidora no frontend e causava erro 500 por FK violada quando o `host_id` chegava antes do host existir no banco.
>
> A detecção de port scan migrou para threads de `tcpdump` no agente (captura de pacotes SYN), que não depende dessa tabela. O alerta de port scan é gerado diretamente na tabela `alerts`. O `init.sql` atual não cria `active_connections`.
>
> Ver seção 10 — Evolução do Projeto para contexto completo.

---

### 3.8 app_settings

Configurações do sistema persistidas no banco. Não tem FK com nenhuma outra tabela.

```sql
-- Já criada diretamente no init.sql consolidado (CREATE TABLE public.app_settings).
-- garantir_schema_settings() permanece no backend como CREATE TABLE IF NOT EXISTS,
-- só tem efeito em volumes antigos pré-consolidação:
CREATE TABLE IF NOT EXISTS app_settings (
    key        VARCHAR(100) PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

| Chave (`key`) | Valor padrão | Gerenciada por | Descrição |
|---------------|-------------|----------------|-----------|
| `api_key` | — | `POST /api/settings/apikey/generate` | Token de autenticação de agentes e painel web |
| `email_recipients` | `[]` (JSON array) | `GET/POST/DELETE /api/settings/email-recipients` | Lista de emails para alertas |
| `notify_teams` | `true` | `PATCH /api/settings/notifications` | Toggle de notificação via Teams |
| `notify_email` | `false` | `PATCH /api/settings/notifications` | Toggle de notificação via Email |
| `threshold_cpu` | `80` | `PATCH /api/settings/thresholds` | Limiar de CPU (%) para alerta `cpu_high` |
| `threshold_mem` | `80` | `PATCH /api/settings/thresholds` | Limiar de memória (%) para alerta `mem_high` |
| `threshold_disk` | `80` | `PATCH /api/settings/thresholds` | Limiar de disco (%) para alerta `disk_high` |

**Uso:**
- `api_key` é gerada via `POST /api/settings/apikey/generate` e carregada para `app.config['API_KEY']` no startup.
- `email_recipients` lida por `_get_email_recipients(db)` em `detection.py` antes de cada alerta; fallback para `ALERT_RECIPIENT` do `.env` se vazia.
- `notify_teams` / `notify_email` inseridos com `ON CONFLICT DO NOTHING` no startup — não sobrescrevem valores existentes.
- `threshold_*` inseridos com `ON CONFLICT DO NOTHING` no startup — não sobrescrevem valores configurados pelo operador.

Todos os valores sobrevivem a restarts do container enquanto o volume PostgreSQL existir.

---

## 4. Índices

### Índices em host

| Nome          | Colunas    | Uso                               |
|---------------|------------|-----------------------------------|
| idx_host_ip   | ip_address | Lookup de host por IP             |

### Índices em agents

| Nome                    | Colunas              | Uso                                    |
|-------------------------|----------------------|----------------------------------------|
| idx_agents_status       | status               | Filtrar agentes ativos                 |
| idx_agents_last_checkin | last_checkin DESC    | Encontrar agentes com checkin recente  |

### Índices em host_discovery

| Nome                       | Colunas           | Uso                                      |
|----------------------------|-------------------|------------------------------------------|
| idx_discovery_virtualized  | is_virtualized    | Filtrar VMs vs físicos                   |
| idx_discovery_ram          | total_memory_gb   | Ordenar por RAM                          |
| idx_discovery_cpu_model    | cpu_model         | Busca por modelo de CPU                  |
| idx_discovery_disks_gin    | disks (GIN)       | Queries JSONB em estrutura de discos     |
| idx_discovery_networks_gin | networks (GIN)    | Queries JSONB em estrutura de redes      |

### Índices em metrics

| Nome                  | Colunas                                         | Uso                                         |
|-----------------------|-------------------------------------------------|---------------------------------------------|
| idx_metrics_host_ts   | (host_id, timestamp DESC)                       | Últimas N métricas de host X — query principal |
| idx_metrics_ts        | timestamp                                       | Limpeza por retenção                        |
| idx_metrics_high_cpu  | (host_id, timestamp) WHERE cpu_percent > 85     | Alertas de CPU alta (parcial — baixo custo) |
| idx_metrics_high_mem  | (host_id, timestamp) WHERE memory_percent > 90  | Alertas de memória alta (parcial)           |

### Índices em logs

| Nome                  | Colunas                                                  | Uso                                   |
|-----------------------|----------------------------------------------------------|---------------------------------------|
| idx_logs_host_ts      | (host_id, timestamp DESC)                                | Últimas N linhas de log de host X     |
| idx_logs_type_ts      | (log_type, timestamp DESC)                               | Filtrar por tipo de log               |
| idx_logs_auth_ip      | (parsed_data->>'ip_origem') WHERE log_type = 'auth'      | Busca rápida por IP atacante          |
| idx_logs_auth_failed  | timestamp WHERE log_type = 'auth' AND status = 'failed'  | Contagem de falhas para brute force   |
| idx_logs_parsed_gin   | parsed_data (GIN)                                        | Queries JSONB genéricas               |

### Índices em alerts

| Nome                    | Colunas                     | Uso                                      |
|-------------------------|-----------------------------|------------------------------------------|
| idx_alerts_host_ts      | (host_id, timestamp DESC)   | Alertas de um host em ordem cronológica  |
| idx_alerts_type_ts      | (alert_type, timestamp DESC)| Filtrar por tipo de alerta              |
| idx_alerts_source_ip_ts | (source_ip, timestamp DESC) | Histórico de ataques de um IP           |

---

## 5. Funções Armazenadas

### cleanup_old_data

```sql
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 7)
RETURNS VOID AS $$
BEGIN
    DELETE FROM metrics  WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    DELETE FROM logs     WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;
```

**Tabelas limpas:** `metrics`, `logs`  
**Não afeta:** `host`, `agents`, `host_discovery`, `alerts`, `app_settings`

> A tabela `active_connections` foi removida — a função não a limpa mais.

**Chamada manual:**
```sql
SELECT cleanup_old_data(7);   -- apaga dados com mais de 7 dias
SELECT cleanup_old_data(30);  -- apaga dados com mais de 30 dias
```

**Chamada automática:** o backend (`app.py`) usa `APScheduler` para disparar `cleanup_old_data(:dias)` todos os dias às **03:00 UTC**. O número de dias é controlado pela variável `RETENTION_DAYS` (padrão 7). O endpoint `POST /api/maintenance/cleanup` permite disparar manualmente.

---

## 6. Política de Retenção

| Tabela         | Retida pela função | Critério de limpeza                         |
|----------------|--------------------|---------------------------------------------|
| metrics        | Sim                | timestamp > N dias                          |
| logs           | Sim                | timestamp > N dias                          |
| host           | Não                | Permanente (gerenciado manualmente)         |
| agents         | Não                | Permanente                                  |
| host_discovery | Não                | Permanente (sobrescrito no restart do agente) |
| alerts         | Não                | Permanente (resolvidos manualmente pelo operador) |
| app_settings   | Não                | Permanente (configurações do sistema)       |

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

### Verificar alerta de brute force ativo (deduplicação)
```sql
SELECT id FROM alerts
WHERE host_id   = :host_id
  AND source_ip = :ip_origem
  AND alert_type = 'brute_force'
  AND resolved = FALSE
LIMIT 1;
```

### Verificar alerta de port scan recente (cooldown 2 minutos)
```sql
SELECT id FROM alerts
WHERE host_id    = :host_id
  AND source_ip  = :ip_atacante
  AND alert_type = 'port_scan'
  AND resolved   = FALSE
  AND timestamp >= NOW() - INTERVAL '2 minutes'
LIMIT 1;
```

### Alertas ativos ordenados (frontend)
```sql
SELECT * FROM alerts
WHERE resolved = FALSE
ORDER BY timestamp DESC
LIMIT 20;
```

### Ler API key persistida
```sql
SELECT value FROM app_settings WHERE key = 'api_key';
```

### Ler destinatários de email
```sql
SELECT value FROM app_settings WHERE key = 'email_recipients';
-- Retorna JSON array: ["user@exemplo.com", "admin@empresa.com"]
```

---

## 8. Inicialização

O arquivo `Web/database/init.sql` é executado automaticamente pelo Docker na **primeira** criação do volume PostgreSQL. Nas execuções subsequentes, se o volume já existir, o init.sql é ignorado — as migrações incrementais do backend cuidam das atualizações.

Para recriar o schema do zero (apaga todos os dados):
```bash
docker compose down -v
docker compose up -d
```

> Usar apenas em ambiente de desenvolvimento.

---

## 9. Migrações Incrementais

Campos adicionados após a criação inicial do banco são aplicados pelo backend no startup. Não requer recriar container ou volume.

| Função no backend                    | Operação                                                                                   | Quando adicionada |
|--------------------------------------|--------------------------------------------------------------------------------------------|-------------------|
| `garantir_schema_discovery()`        | ADD COLUMN: `os_name`, `os_version`, `kernel_release`, `uptime_seconds`, `motherboard`    | Semana 3 |
| `garantir_schema_metrics()`          | ADD COLUMN: `memory_used_mb`, `memory_free_mb`, `memory_total_mb`, `disk_used_mb`, `disk_free_mb`, `disk_total_mb` | Semana 2 |
| `garantir_schema_alerts()`           | ADD COLUMN: `resolved` (BOOLEAN), `resolved_at` (TIMESTAMPTZ)                             | Semana 5 |
| `garantir_schema_alerts_message()`   | ADD COLUMN: `message` (TEXT)                                                               | Semana 6 |
| `garantir_schema_iops()`             | ADD COLUMN: `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `net_sent_bytes_per_sec`, `net_recv_bytes_per_sec` | Semana 7 |
| `garantir_schema_settings()`         | CREATE TABLE IF NOT EXISTS `app_settings`                                                  | Semana 7 |
| `garantir_schema_alerts_source_ip()` | ALTER COLUMN `source_ip` TYPE VARCHAR(45) + DROP NOT NULL em `alerts`                      | Semana 7 |
| `garantir_schema_notifications()`    | INSERT ON CONFLICT DO NOTHING: `notify_teams=true`, `notify_email=false` em `app_settings` | Fase D |
| `garantir_schema_thresholds()`       | INSERT ON CONFLICT DO NOTHING: `threshold_cpu/mem/disk=80` em `app_settings`               | Fase C |

> **Nota:** `garantir_schema_connections_ip()` existiu durante a Semana 7 para migrar `active_connections.src_ip`/`dst_ip` de INET para VARCHAR(45). Foi removida junto com a tabela `active_connections`.

**Todas as migrações são idempotentes** — re-executar não causa erro. Erros em migrações individuais são capturados com rollback e log de WARNING, nunca impedir o startup do backend.

---

## 10. Evolução do Projeto — Decisões Iniciais vs. Decisões Finais

| Decisão | Inicial | Final/Atual | Motivo |
|---------|---------|-------------|--------|
| **Tabela `active_connections`** | Criada para persistir snapshots de conexões TCP via `psutil` | Removida | Sem tela consumidora no frontend; causava erro 500 por FK violada durante startup |
| **Detecção de port scan** | Analisava conexões TCP armazenadas na tabela | Via threads `tcpdump` no agente; alerta vai direto para `alerts` | Abordagem via psutil não diferenciava conexões legítimas de escaneamento |
| **`alerts.source_ip`** | Tipo `INET NOT NULL` no init.sql | `VARCHAR(45) nullable` | Alertas de recurso (cpu/mem/disk) não têm IP de origem; NULL necessário |
| **Retenção de dados** | `cleanup_old_data()` chamada manualmente no banco | Invocada automaticamente pelo APScheduler às 03:00 UTC | Evita crescimento indefinido sem intervenção manual |
| **`app_settings` — chaves** | Apenas `api_key` | `api_key`, `email_recipients`, `notify_teams`, `notify_email`, `threshold_cpu/mem/disk` | Expansão das funcionalidades configuráveis pelo operador |
| **`cleanup_old_data()` — tabelas** | Limpava `metrics`, `logs`, `active_connections` | Limpa apenas `metrics` e `logs` | Tabela `active_connections` removida |
| **`init.sql` — status** | Defasado (declarava `source_ip INET NOT NULL`, sem migrações) | Consolidado — reflete schema atual de produção | Facilita criação de novos ambientes sem depender de migrações do backend |

---

*Documentação atualizada em 21/06/2026 — v1.4*  
*Adições v1.1: app_settings, migrações de tipo IP (INET → VARCHAR(45)), nullable source_ip, deduplicação por cooldown de port scan, alertas de recurso (cpu_high/mem_high/disk_high).*  
*Adições v1.2: app_settings agora armazena `email_recipients` (JSON array de destinatários para notificações por email); query de exemplo adicionada.*  
*Adições v1.3 (05/06/2026): tabela `active_connections` removida do diagrama e da documentação; `cleanup_old_data()` atualizada (remove active_connections); app_settings com chaves completas (notify_*, threshold_*); `garantir_schema_connections_ip()` removida; `garantir_schema_notifications/thresholds()` adicionadas; retenção automática via APScheduler documentada; init.sql marcado como consolidado; seção 10 (Evolução) adicionada.*  
*Adições v1.4 (21/06/2026 — esta revisão, sem mudança de schema): corrigidas quatro notas que ainda diziam que certas colunas/tabelas "não estão no init.sql" — confirmado lendo o `init.sql` atual que `os_name/os_version/kernel_release/uptime_seconds/motherboard` (host_discovery), as colunas `memory_*_mb`/`disk_*_mb`/`*_iops`/`*_bytes_per_sec` (metrics), `source_ip VARCHAR(45)` nullable (alerts) e a tabela `app_settings` já vêm criadas diretamente no dump consolidado; as funções `garantir_schema_*` correspondentes seguem no backend só para compatibilidade com volumes antigos pré-consolidação.*
