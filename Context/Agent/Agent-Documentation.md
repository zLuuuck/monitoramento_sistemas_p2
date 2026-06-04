# Agent Monitor — Documentação Técnica

**Versão 5.1 | Junho 2026**

| Campo             | Valor                                              |
|-------------------|----------------------------------------------------|
| Projeto           | Monitoramento de Sistemas P2                       |
| Módulo            | Agent — Discovery + Coleta + Identidade + Executável |
| Linguagem         | Python 3.12                                        |
| Ambiente Testado  | Ubuntu Linux 24 (físico e virtualizado)            |
| Equipe            | Lucas Toterol Rodrigues & Caio Federico Esquivel Lovera Arze |

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Cronograma](#2-cronograma)
3. [Estrutura de Diretórios](#3-estrutura-de-diretórios)
4. [Fluxo de Execução](#4-fluxo-de-execução)
5. [Módulo: global_information](#5-módulo-global_information)
6. [Módulo: discovery](#6-módulo-discovery)
7. [Módulo: coleta](#7-módulo-coleta)
8. [Estrutura dos Payloads](#8-estrutura-dos-payloads)
9. [Módulo: utils](#9-módulo-utils)
10. [Módulo: sender](#10-módulo-sender)
11. [Organização como Módulo Python](#11-organização-como-módulo-python)
12. [Geração do Executável com PyInstaller](#12-geração-do-executável-com-pyinstaller)
13. [Variáveis de Ambiente](#13-variáveis-de-ambiente)
14. [Dependências](#14-dependências)
15. [Resumo dos Módulos](#15-resumo-dos-módulos)
16. [Observações Importantes](#16-observações-importantes)

---

## 1. Visão Geral

O Agent Monitor é um agente de monitoramento Linux escrito em Python 3.12. Ele executa duas funções principais:

**Discovery** — coleta uma vez, na inicialização, um inventário completo de hardware e sistema operacional do host.

**Coleta Contínua** — a cada ~5 segundos, envia via HTTP POST:
- Heartbeat mínimo (sinal de vida independente das métricas)
- Métricas de CPU, memória, disco (com IOPS) e rede (com bytes/sec)
- Top 15 processos por CPU, RAM, disco e conexões de rede
- Novas linhas do `/var/log/auth.log` (leitura incremental)
- Estado das conexões TCP ativas e flag de detecção de port scan

O agente detecta automaticamente se está rodando em hardware físico ou em ambiente virtualizado (KVM, VMware, Xen, Hyper-V) e adapta a coleta conforme o que está disponível. Campos inexistentes em VMs (slots de RAM, S.M.A.R.T., speed de rede) são retornados como `null`, e uma seção `notes` no payload avisa o backend do motivo.

**Resiliência:** em caso de falha de conexão, os payloads são enfileirados localmente em `/var/cache/monitor-agent/retry_queue.json` e reenviados automaticamente quando a conexão retornar.

O agente é distribuído como um executável único gerado com PyInstaller (`--onefile`), sem dependência de Python instalado na máquina alvo.

---

## 2. Cronograma

| Semana | Período       | Foco Principal                                    | Status |
|--------|---------------|---------------------------------------------------|--------|
| 1      | 21/04 – 27/04 | Coleta local e definição do contrato              | ✅ Concluída |
| 2      | 28/04 – 04/05 | Primeira integração (envio HTTP)                  | ✅ Concluída |
| 3      | 05/05 – 11/05 | Empacotamento e coleta avançada                   | ✅ Concluída |
| 4      | 12/05 – 18/05 | Leitura de logs (`auth.log`)                      | ✅ Concluída |
| 5      | 19/05 – 25/05 | Simulação de ataques e suporte à detecção         | ✅ Concluída |
| 6      | 26/05 – 01/06 | Coleta de rede (port scan) e preparação parcial   | ✅ Concluída |
| 7      | 02/06 – 05/06 | Estabilidade, instalação, logging e expansão      | ✅ Concluída |

**Entregáveis da Semana 7:**
- Serviço systemd (`linux-agent.service`) + script de instalação (`install.sh`)
- Sistema de logging rotativo (`utils/logger.py`) com journald e arquivo em `/var/log/monitor-agent/`
- IOPS de disco (`read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`)
- Taxa de rede em bytes/sec (`bytes_sent_per_sec`, `bytes_recv_per_sec`)
- Top 15 processos por CPU, RAM, disco e conexões (`coleta/process_coleta/`)
- Fila de retry persistente (`utils/retry_queue.py`) com enfileiramento em JSON local
- Heartbeat dedicado (`POST /api/heartbeat`) independente das métricas
- Flag `--debug-exec` para exibir payloads no terminal sem enviar ao backend
- **Fix de compatibilidade PyInstaller:** limpeza de `LD_LIBRARY_PATH` antes de spawnar tcpdump (ver seção 7.6)

### Período de Pitch (06 – 12/06)

- **P.1** Garantir que o agente está funcionando na VM que será usada na apresentação
- **P.2** Preparar roteiro de demonstração: `systemctl status linux-agent` → simular ataque SSH → mostrar alerta no dashboard → simular port scan com nmap → mostrar alerta
- **P.3** Estar disponível para suporte técnico durante a apresentação

---

## 3. Estrutura de Diretórios

```
Agent/
├── pyproject.toml
├── install.sh                      ← instala como serviço systemd
├── linux-agent.service             ← definição do serviço
├── Agent_Exec/
│   ├── main.py                     ← entry point do PyInstaller
│   ├── dist/                       ← binário final gerado (não versionado)
│   └── build/                      ← artefatos intermediários (não versionados)
└── src/
    └── agent/
        ├── __init__.py
        ├── __main__.py             ← ponto de entrada principal
        ├── global_information/
        │   └── global_information.py
        ├── discovery/
        │   ├── __init__.py
        │   ├── cpu_discovery/
        │   ├── mem_discovery/
        │   ├── disk_discovery/
        │   ├── network_discovery/
        │   ├── motherboard_discovery/
        │   ├── system_discovery/
        │   └── tools_discovery/
        ├── coleta/
        │   ├── collector.py                        ← orquestrador
        │   ├── cpu_coleta/cpu.py
        │   ├── mem_coleta/mem.py
        │   ├── disk_coleta/disk.py                 ← inclui IOPS
        │   ├── network_coleta/network.py            ← inclui bytes/sec
        │   ├── logs_coleta/logs.py
        │   ├── connections_coleta/connections.py   ← detecção de port scan via tcpdump (sem psutil)
        │   └── process_coleta/processes.py         ← top processos
        └── utils/
            ├── parsers.py
            ├── sender.py                           ← envio HTTP + retry + heartbeat
            ├── retry_queue.py                      ← fila de retry persistente
            ├── serializer.py
            ├── shell.py
            └── logger.py                           ← logging rotativo
```

**Arquivos ignorados pelo git (`.gitignore`):**

| Caminho | Motivo |
|---------|--------|
| `Agent/Agent_Exec/dist/` | Binário compilado — gerado localmente, não versionado |
| `Agent/Agent_Exec/build/` | Artefatos intermediários do PyInstaller |
| `Agent/.spec/` e `*.spec` | Spec files do PyInstaller |

**Diretórios em runtime (criados pelo `install.sh`):**

| Caminho | Finalidade |
|---------|------------|
| `/opt/monitor-agent/` | Binário instalado |
| `/etc/monitor-agent/env` | Variáveis de ambiente (chmod 600) |
| `/var/log/monitor-agent/` | Arquivo de log rotativo |
| `/var/cache/monitor-agent/` | Fila de retry (`retry_queue.json`) |

---

## 4. Fluxo de Execução

| Etapa | Descrição |
|-------|-----------|
| 1 | `build_global_information("discovery")` — resolve identidade, detecta ambiente, persiste IDs em disco |
| 2 | `get_tools_info()` — verifica e instala dependências se necessário |
| 3 | `run_discovery()` — executa todos os módulos de discovery via `_safe_collect()` |
| 4 | `send_discovery(discovery)` — envia payload ao backend (`POST /api/discovery`) |
| 5 | Loop infinito (~5s): **flush retry → heartbeat → métricas → logs → port scan (só envia quando detectado)** |

**Detalhe do loop contínuo:**

```
┌─ início do ciclo ─────────────────────────────────────────┐
│  1. flush_retry_queue()  — reenviar payloads pendentes     │
│  2. send_heartbeat()     — sinal de vida mínimo            │
│  3. collect_all()        — CPU, RAM, disco, rede, processos│
│     send_metrics()                                         │
│  4. collect_auth_logs()  — novas linhas de auth.log        │
│     send_log() (uma chamada por linha)                     │
│  5. collect_scan_status() — port scan (só envia se True)   │
│     send_portscan()  → POST /api/security/portscan         │
│  time.sleep(5)                                             │
└───────────────────────────────────────────────────────────┘
```

**Flag `--debug-exec`:** exibe cada payload no terminal via `json.dumps()` em vez de enviá-los ao backend.

```bash
/opt/monitor-agent/agent --debug-exec          # com logs no stderr
/opt/monitor-agent/agent --debug-exec 2>/dev/null  # só JSONs
```

---

## 5. Módulo: global_information

**Arquivo:** `agent/global_information/global_information.py`

Monta o bloco `global` que encabeça todos os payloads. Centraliza a detecção de ambiente.

**`_load_or_create_id(filename)`** — Lê o ID do arquivo em `~/.agent/<filename>`. Se não existir, gera um número de 5 dígitos (10000–99999) e salva.

**`_get_primary_ip()`** — Determina o IP primário conectando um socket UDP ao `8.8.8.8:80`. Nenhum pacote é enviado — consulta a tabela de roteamento do kernel.

**`_detect_environment()`** — Executa `lscpu` e verifica o campo `Hypervisor Vendor`.

### Payload gerado

```json
{
  "collection_type": "discovery",
  "schema_version":  "1.0",
  "agent_id":        "38472",
  "host_id":         "71203",
  "hostname":        "teste-ubuntu",
  "primary_ip":      "10.10.10.1",
  "environment": {
    "is_virtualized": true,
    "hypervisor":     "VMware"
  },
  "notes": [...]
}
```

---

## 6. Módulo: discovery

Executado uma única vez após a inicialização. Todos os sub-módulos recebem `is_virtualized` e delegam para o handler `_physical` ou `_virtual` correspondente.

### 6.1 CPU Discovery

**Fontes:** `lscpu`, `/proc/cpuinfo`, sysfs (`/sys/devices/system/cpu/`)

### 6.2 Memory Discovery

**Fontes:** `/proc/meminfo`, `dmidecode -t memory` (somente físico, root)

### 6.3 Disk Discovery

**Fontes:** `lsblk -J`, `smartctl -i -j` (somente físico, root)

### 6.4 Network Discovery

**Fontes:** `ip -j addr show`, `ip -j link show`, `ip -j route show default`, sysfs (somente físico)

### 6.5 Motherboard Discovery

**Fontes:** `dmidecode -t 0/2/4/9/17`, `lspci`  
Retorna `null` em ambientes virtualizados.

### 6.6 System Discovery

**Fontes:** `/etc/os-release`, `uname -a`, `hostname -f`, `/proc/uptime`, `timedatectl`

### 6.7 Tools Discovery

Verifica ferramentas externas e instala ausentes se autorizado. Executado antes dos demais módulos.

---

## 7. Módulo: coleta

Loop contínuo a cada 5 segundos. Todos os sub-módulos usam `psutil`.

```python
def collect_all():
    return {
        "cpu":       get_cpu_usage(),
        "memory":    get_memory_usage(),
        "disk":      get_disk_usage(),       # inclui IOPS
        "network":   get_network_usage(),    # inclui bytes/sec
        "processes": get_top_processes(),    # top 15 por categoria
    }
```

### 7.1 CPU Coleta

Usa `psutil.cpu_percent(interval=1)`.

### 7.2 Memory Coleta

Usa `psutil.virtual_memory()`.

### 7.3 Disk Coleta

Usa `psutil.disk_usage('/')` para espaço e `psutil.disk_io_counters()` para I/O. IOPS e bytes/sec calculados como delta entre ciclos — **ausentes no primeiro ciclo**.

### 7.4 Network Coleta

Usa `psutil.net_io_counters()`. Taxas por segundo calculadas como delta — **ausentes no primeiro ciclo**.

### 7.5 Logs Coleta

Lê `/var/log/auth.log` incrementalmente, rastreando byte offset e inode em `~/.agent/auth_log_state.json`.

- **Primeira execução:** envia as últimas 100 linhas
- **Execuções seguintes:** envia apenas linhas novas
- **Rotação detectada:** inode diferente → reinicia leitura

### 7.6 Connections Coleta

**Arquivo:** `coleta/connections_coleta/connections.py`

Realiza **detecção de port scan via tcpdump**. A coleta de conexões TCP via `psutil` foi removida — não havia tela consumidora no frontend e causava erro 500 no backend por FK violada. As threads de tcpdump e toda a lógica de detecção foram preservadas.

#### Detecção de port scan (tcpdump)

Duas threads daemon são iniciadas no momento do **import do módulo** (ao ser importado pelo agente, não a cada ciclo):

**Thread `tcpdump-capture`:**

Executa tcpdump com filtro para capturar apenas pacotes TCP SYN sem ACK (novos pedidos de conexão entrantes):

```
tcpdump -n -l -i any "tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0"
```

Pacotes cujo IP de origem pertence ao próprio host (resolvidos via `psutil.net_if_addrs()`) são descartados — assim apenas tráfego **externo entrante** é contabilizado.

**Regex de extração da saída do tcpdump:**
```python
r'(\d{1,3}(?:\.\d{1,3}){3})\.(\d+)\s*>\s*(\d{1,3}(?:\.\d{1,3}){3})\.(\d+):'
```
Extrai: `src_ip`, `src_port`, `dst_ip`, `dst_port`.

**Thread `portscan-eval` (ciclo de 2s):**

Mantém janela deslizante de 60 segundos por IP de origem. A cada 2 segundos, poda entradas expiradas e atualiza `_active_scans` com IPs que atingiram o limiar.

**Limiar:** `_PORTSCAN_THRESHOLD = 10` portas distintas de um mesmo IP em 60 segundos.

#### Fix crítico: LD_LIBRARY_PATH e PyInstaller

Quando o agente é empacotado com PyInstaller (`--onefile`), o binário extrai suas bibliotecas para um diretório temporário (`/tmp/_MEIxxxxxx/`) e define `LD_LIBRARY_PATH` apontando para ele. Qualquer subprocesso filho herda essa variável.

O problema: o `tcpdump` herdava o `LD_LIBRARY_PATH` do PyInstaller e carregava a `libpcap.so` do diretório temporário (incompatível com o tcpdump do sistema), resultando em **zero pacotes capturados** — o loop `for line in proc.stdout:` nunca avançava.

**Solução implementada:** antes de spawnar o tcpdump, copia e limpa o ambiente do processo:

```python
import os as _os
clean_env = _os.environ.copy()
clean_env.pop('LD_LIBRARY_PATH', None)
clean_env.pop('LD_PRELOAD', None)

proc = subprocess.Popen(
    [tcpdump_bin, "-n", "-l", "-i", "any",
     "tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    env=clean_env,   # ← usa ambiente limpo, sem LD_LIBRARY_PATH do PyInstaller
)
```

Isso garante que o tcpdump carregue a libpcap do sistema operacional, não a versão bundlada.

#### Resolução do binário tcpdump

Para evitar depender do PATH (que pode estar incompleto em ambientes systemd), o módulo busca o binário em locais comuns antes de recorrer ao PATH:

```python
tcpdump_bin = "tcpdump"
for candidate in ("/usr/bin/tcpdump", "/usr/sbin/tcpdump", "/sbin/tcpdump"):
    if os.path.isfile(candidate):
        tcpdump_bin = candidate
        break
```

#### Logging de diagnóstico

O módulo emite logs em nível INFO/DEBUG para facilitar diagnóstico:

```
INFO  tcpdump iniciado (pid=12345, bin=/usr/bin/tcpdump)
INFO  IPs locais filtrados: {'127.0.0.1', '10.10.10.1', '::1', ...}
INFO  SYN capturado #1: src=10.10.10.26 dst_port=22
INFO  SYN capturado #2: src=10.10.10.26 dst_port=80
...
INFO  SYN capturado #50: src=10.10.10.26 dst_port=443   ← a cada 50 pacotes
WARNING  tcpdump encerrou (rc=1): <stderr>               ← se o processo morrer
```

Para ver esses logs na VM:
```bash
journalctl -u linux-agent -f | grep -E "tcpdump|SYN|port_scan|IPs locais"
```

#### Graceful degradation

Se `tcpdump` não estiver instalado ou o processo não tiver `cap_net_raw`, a thread encerra silenciosamente. `port_scan_detected` permanece sempre `false` e nenhum request é enviado ao backend.

#### Campos retornados por `get_scan_status()`

| Campo | Descrição |
|-------|-----------|
| `port_scan_detected` | `true` se algum IP atingiu o limiar de portas distintas |
| `scan_sources` | `{ip_atacante: qtd_portas_distintas, ...}` — IPs ativos no scan |

### 7.7 Process Coleta

Usa `psutil.process_iter()` para retornar quatro listas de top 15 processos.

```python
return {
    "top_cpu":     sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:15],
    "top_memory":  sorted(procs, key=lambda x: x["memory_rss"],  reverse=True)[:15],
    "top_disk":    sorted(procs, key=lambda x: x["disk_bytes"],  reverse=True)[:15],
    "top_network": sorted(procs, key=lambda x: x["open_connections"], reverse=True)[:15],
}
```

**`cpu_percent`:** retorna `0.0` no primeiro ciclo (psutil precisa de dois snapshots para calcular delta).

**`disk_bytes`:** total acumulado desde o início do processo, não taxa por segundo.

---

## 8. Estrutura dos Payloads

### 8.1 Payload de Discovery

```json
{
  "global": { "collection_type": "discovery", "host_id": "71203", "primary_ip": "10.10.10.1", "..." },
  "system":      { "hostname": "teste-ubuntu", "os": {...}, "kernel": {...}, "uptime_seconds": 808 },
  "cpu":         { "model_name": "AMD Ryzen 5", "topology": {"vcpus": 2}, "frequency": {...} },
  "memory":      { "total": {"bytes": 2013175808, "gb": 1.87} },
  "disk":        { "disks": [{"device": "/dev/sda", "size": {"bytes": 32212254720}}] },
  "network":     { "interfaces": [...] },
  "motherboard": null,
  "tools":       { "..." }
}
```

### 8.2 Payload de Métricas

```json
{
  "type":      "metrics",
  "global":    { "collection_type": "metrics", "host_id": "71203", "..." },
  "timestamp": "2026-06-02T19:24:45.000000+00:00",
  "data": {
    "cpu":    { "percent": 23.5 },
    "memory": { "total": 2013175808, "used": 1006587904, "percent": 50.0 },
    "disk": {
      "total": 32212254720, "used": 16106127360, "percent": 50.0,
      "read_iops": 45.2, "write_iops": 12.8,
      "read_bytes_per_sec": 184320.0, "write_bytes_per_sec": 52428.8
    },
    "network": {
      "bytes_sent": 1048576, "bytes_recv": 5242880,
      "bytes_sent_per_sec": 2048.5, "bytes_recv_per_sec": 10240.0
    },
    "processes": {
      "top_cpu":     [{ "pid": 122298, "name": "agent", "username": "root", "cpu_percent": 2.1, "..." }],
      "top_memory":  [...],
      "top_disk":    [...],
      "top_network": [{ "pid": 122298, "name": "agent", "open_connections": 3, "..." }]
    }
  }
}
```

> `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `bytes_sent_per_sec` e `bytes_recv_per_sec` estão **ausentes no primeiro ciclo**.

### 8.3 Payload de Log

```json
{
  "global":    { "collection_type": "logs", "host_id": "71203", "..." },
  "log_type":  "auth",
  "timestamp": "2026-06-02T19:24:58+00:00",
  "raw_line":  "Jun  2 19:24:58 teste-ubuntu sshd[999]: Failed password for root from 10.10.10.26 port 54321 ssh2"
}
```

### 8.4 Payload de Port Scan

Enviado apenas quando `port_scan_detected=True` → `POST /api/security/portscan`.

```json
{
  "global":             { "collection_type": "metrics", "host_id": "71203", "primary_ip": "10.10.10.1" },
  "timestamp":          "2026-06-02T19:24:58.000000+00:00",
  "port_scan_detected": true,
  "scan_sources": {
    "10.10.10.26": 1000
  }
}
```

Quando não há scan ativo, nenhum request é enviado ao backend (sem polling).

### 8.5 Payload de Heartbeat

```json
{
  "type":      "heartbeat",
  "global":    { "collection_type": "metrics", "host_id": "71203", "..." },
  "timestamp": "2026-06-02T19:24:45.000000+00:00"
}
```

Heartbeats **nunca são enfileirados** — um heartbeat stale não tem valor.

---

## 9. Módulo: utils

### `agent/utils/parsers.py`

Parsers centralizados de saída de comandos shell. Nenhuma chamada shell acontece aqui.

| Seção | Funções |
|-------|---------|
| CPU | `parse_lscpu()`, `parse_cpuinfo()` |
| Memória | `parse_meminfo()`, `parse_dmidecode_memory()`, `parse_dmi_size_to_mb()` |
| Disco | `parse_lsblk()`, `parse_smartctl()`, `resolve_disk_type()`, `resolve_disk_interface()` |
| Rede | `parse_ip_addr()`, `parse_ip_link()`, `parse_default_gateway()` |
| SO | `parse_os_release()`, `parse_uname()`, `parse_uptime_seconds()` |
| Placa-mãe | `parse_baseboard()`, `parse_bios()`, `parse_cpu_sockets()`, `parse_memory_slots_summary()` |

### `agent/utils/shell.py`

| Função | Descrição |
|--------|-----------|
| `run(cmd)` | Executa comando com `LC_ALL=C`. Retorna `stdout` ou `None`. Timeout: 10s. |
| `run_permissive(cmd)` | Retorna `stdout` mesmo com exit code não-zero. Usado para `smartctl`. Timeout: 15s. |

> **`LC_ALL=C` é obrigatório** — garante saída em inglês independente do locale. Sem isso, `lscpu` em português quebra os parsers silenciosamente.

### `agent/utils/logger.py`

| Handler | Destino | Configuração |
|---------|---------|--------------|
| `StreamHandler` | stdout → journald | `[YYYY-MM-DD HH:MM:SS] [LEVEL] mensagem` |
| `RotatingFileHandler` | `/var/log/monitor-agent/agent.log` | 10 MB por arquivo, 5 backups |

### `agent/utils/retry_queue.py`

Fila de retry persistente em disco.

| Função | Descrição |
|--------|-----------|
| `enqueue(payload, url)` | Adiciona item à fila (descarta mais antigo se MAX_ITEMS atingido) |
| `load_queue()` | Lê e retorna a fila atual |
| `save_queue(queue)` | Persiste a fila |

**Arquivo:** `/var/cache/monitor-agent/retry_queue.json`  
**Limite:** 50 itens  
**Corrupção:** descartada silenciosamente com WARNING

---

## 10. Módulo: sender

**Arquivo:** `agent/utils/sender.py`

### URLs configuradas

```python
API_BASE_URL    = os.getenv("MONITOR_API_BASE_URL", "http://api.monitoramento.lan")
DISCOVERY_URL   = os.getenv("MONITOR_DISCOVERY_URL")   or f"{API_BASE_URL}/api/discovery"
METRICS_URL     = os.getenv("MONITOR_METRICS_URL")     or f"{API_BASE_URL}/api/metrics"
LOGS_URL        = os.getenv("MONITOR_LOGS_URL")        or f"{API_BASE_URL}/api/logs"
PORTSCAN_URL    = os.getenv("MONITOR_PORTSCAN_URL")    or f"{API_BASE_URL}/api/security/portscan"
HEARTBEAT_URL   = os.getenv("MONITOR_HEARTBEAT_URL")   or f"{API_BASE_URL}/api/heartbeat"
API_KEY = os.getenv("API_KEY", "")
```

### Cabeçalhos enviados

| Cabeçalho | Valor | Condição |
|-----------|-------|----------|
| `Content-Type` | `application/json` | Sempre |
| `X-API-Key` | `{API_KEY}` | Somente se `API_KEY` não for vazio |

> `MONITOR_TOKEN` / `Authorization: Bearer` foram removidos na Fase A (hardening). Apenas `X-API-Key` é enviado.

### Tratamento de erros

| Exceção | Ação |
|---------|------|
| `ConnectionError` | `logger.error()` + enfileira para retry |
| `Timeout` | `logger.error()` + enfileira para retry |
| `HTTPError` (4xx/5xx) | `logger.error()` com body da resposta — não enfileira |
| Exceção genérica | `logger.exception()` com traceback — não enfileira |

---

## 11. Organização como Módulo Python

### Instalação em modo editável (desenvolvimento)

```bash
cd Agent/
python -m venv .ambiente_venv
source .ambiente_venv/bin/activate
pip install -e .
```

### Argumentos de linha de comando

```bash
agent                   # execução normal — envia ao backend
agent --install-deps    # força instalação de ferramentas ausentes
agent --debug-exec      # exibe payloads no terminal sem enviar ao backend
```

---

## 12. Geração do Executável com PyInstaller

### Comando de geração

```bash
pyinstaller --onefile -n agent \
  --paths src \
  --distpath Agent_Exec/dist \
  --workpath Agent_Exec/build \
  Agent_Exec/main.py
```

O binário final fica em `Agent_Exec/dist/agent`.

### Problema com LD_LIBRARY_PATH (PyInstaller)

Binários `--onefile` do PyInstaller extraem suas bibliotecas para `/tmp/_MEIxxxxxx/` e sobrescrevem `LD_LIBRARY_PATH` para apontar para esse diretório. **Todo processo filho herda esse `LD_LIBRARY_PATH`**, o que fazia o tcpdump carregar uma `libpcap.so` incompatível e capturar zero pacotes.

A solução (já implementada em `connections.py`) é remover essas variáveis do ambiente antes de spawnar qualquer subprocesso que dependa de bibliotecas do sistema:

```python
clean_env = os.environ.copy()
clean_env.pop('LD_LIBRARY_PATH', None)
clean_env.pop('LD_PRELOAD', None)
proc = subprocess.Popen([tcpdump_bin, ...], env=clean_env)
```

### Atualizar o binário instalado

```bash
# Opção 1 — substituição direta (mais rápida)
sudo systemctl stop linux-agent
sudo cp Agent_Exec/dist/agent /opt/monitor-agent/agent
sudo systemctl start linux-agent

# Opção 2 — reinstalação completa
sudo ./install.sh
```

> **Atenção:** após `git pull` na VM, sempre verificar se o binário instalado em `/opt/monitor-agent/agent` está atualizado. Um binário antigo não reflete mudanças no código fonte.

---

## 13. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MONITOR_API_BASE_URL` | `http://api.monitoramento.lan` | URL base do backend |
| `MONITOR_DISCOVERY_URL` | `{BASE}/api/discovery` | Override do endpoint de discovery |
| `MONITOR_METRICS_URL` | `{BASE}/api/metrics` | Override do endpoint de métricas |
| `MONITOR_LOGS_URL` | `{BASE}/api/logs` | Override do endpoint de logs |
| `MONITOR_PORTSCAN_URL` | `{BASE}/api/security/portscan` | Override do endpoint de sinalização de port scan |
| `MONITOR_HEARTBEAT_URL` | `{BASE}/api/heartbeat` | Override do endpoint de heartbeat |
| `API_KEY` | `""` | API key para o header `X-API-Key` — obrigatório para autenticar no backend |
| `MONITOR_LOG_LEVEL` | `INFO` | Nível de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MONITOR_RETRY_FILE` | `/var/cache/monitor-agent/retry_queue.json` | Caminho da fila de retry |
| `MONITOR_RETRY_MAX` | `50` | Máximo de itens na fila de retry |

**`MONITOR_LOG_LEVEL=DEBUG`:** loga os JSONs completos de cada payload e mensagens de debug do tcpdump antes de enviá-los.

**Exemplo de arquivo `/etc/monitor-agent/env`:**

```ini
MONITOR_API_BASE_URL=http://api.monitoramento.lan
API_KEY=sua_api_key_aqui
MONITOR_LOG_LEVEL=INFO
```

> Configurar `API_KEY` no arquivo de env do agente (`/etc/monitor-agent/env` ou `.env` local). É a única forma de autenticação aceita pelo backend.

---

## 14. Dependências

### Python (runtime)

| Pacote | Uso |
|--------|-----|
| `psutil` | CPU, memória, disco, rede I/O, processos, IPs locais (net_if_addrs para filtro tcpdump) |
| `requests` | HTTP POST para o backend |

### Ferramentas do sistema (Linux)

| Ferramenta | Pacote | Uso | Requer root |
|------------|--------|-----|-------------|
| `lscpu` | util-linux | Detecção de ambiente, CPU discovery | Não |
| `lsblk` | util-linux | Disk discovery | Não |
| `ip` | iproute2 | Network discovery | Não |
| `dmidecode` | dmidecode | Memory/Motherboard discovery | Sim |
| `smartctl` | smartmontools | Disk health (S.M.A.R.T.) | Sim |
| `ethtool` | ethtool | Network hardware | Não |
| `lspci` | pciutils | Chipset discovery | Não |
| `journalctl` | systemd | Logs | Não |
| `timedatectl` | systemd | Timezone | Não |
| `tcpdump` | tcpdump | Captura de SYN para detecção de port scan | Sim (root ou cap_net_raw) |
| `binutils` | binutils | Necessário para compilar com PyInstaller | Sim (build only) |

---

## 15. Resumo dos Módulos

| Módulo | Arquivo | Função |
|--------|---------|--------|
| `__main__` | `agent/__main__.py` | Ponto de entrada — orquestra discovery e loop de coleta |
| `global_information` | `global_information/global_information.py` | Bloco de identidade dos payloads |
| `discovery.*` | `discovery/*/` | Inventário de hardware/SO (executado uma vez) |
| `coleta.collector` | `coleta/collector.py` | Orquestrador da coleta contínua |
| `coleta.connections_coleta` | `coleta/connections_coleta/connections.py` | Detecção de port scan via tcpdump (sem coleta TCP psutil) |
| `coleta.logs_coleta` | `coleta/logs_coleta/logs.py` | Leitura incremental de auth.log |
| `coleta.process_coleta` | `coleta/process_coleta/processes.py` | Top 15 processos por CPU, RAM, disco e conexões |
| `utils.sender` | `utils/sender.py` | HTTP POST + retry + heartbeat |
| `utils.retry_queue` | `utils/retry_queue.py` | Fila de retry persistente em JSON |
| `utils.logger` | `utils/logger.py` | Logging rotativo em `/var/log/monitor-agent/agent.log` |

---

## 16. Observações Importantes

### Gerenciamento do Serviço

```bash
sudo systemctl start linux-agent      # iniciar
sudo systemctl stop linux-agent       # parar
sudo systemctl restart linux-agent    # reiniciar
sudo systemctl status linux-agent     # verificar status
sudo journalctl -u linux-agent -f     # logs em tempo real
```

### Diagnóstico do tcpdump (port scan)

```bash
# Ver se tcpdump está capturando pacotes:
journalctl -u linux-agent -f | grep -E "tcpdump|SYN|IPs locais|port_scan"

# Testar captura manualmente (fora do agente):
sudo tcpdump -n -l -i any "tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0"

# Verificar se LD_LIBRARY_PATH está presente no ambiente do serviço:
sudo cat /proc/$(pgrep -f linux-agent)/environ | tr '\0' '\n' | grep LD_LIBRARY
```

### Atualizar o Agente na VM

```bash
# 1. Na máquina de desenvolvimento: commit + push das alterações
# 2. Na VM:
git pull
source .ambiente_venv/bin/activate
pyinstaller --onefile -n agent --paths src \
  --distpath Agent_Exec/dist --workpath Agent_Exec/build \
  Agent_Exec/main.py
sudo systemctl stop linux-agent
sudo cp Agent_Exec/dist/agent /opt/monitor-agent/agent
sudo systemctl start linux-agent
journalctl -u linux-agent -f
```

### Permissões necessárias

| Recurso | Permissão | Motivo |
|---------|-----------|--------|
| `/var/log/auth.log` | Grupo `adm` ou root | Leitura de logs de autenticação |
| `dmidecode` | root | Detalhes de RAM e placa-mãe |
| `smartctl` | root | Saúde do disco (S.M.A.R.T.) |
| `psutil.net_if_addrs()` | — | Listar IPs do host para filtrar pacotes de saída no tcpdump |
| `tcpdump` | root ou `cap_net_raw` | Captura de pacotes SYN |

O `install.sh` garante que o serviço rode como root, atendendo todas as permissões acima automaticamente.

### Desinstalar

```bash
sudo systemctl stop linux-agent
sudo systemctl disable linux-agent
sudo rm /etc/systemd/system/linux-agent.service
sudo rm -rf /opt/monitor-agent /etc/monitor-agent /var/cache/monitor-agent
sudo systemctl daemon-reload
```

---

*Documentação atualizada em 04/06/2026 — v6.0*  
*Adições v6.0: remoção da coleta TCP via psutil (`net_connections`) — sem tela consumidora no frontend e causava erro 500. Threads tcpdump preservadas. Função renomeada de `get_active_connections()` para `get_scan_status()`. Agente passa a enviar `POST /api/security/portscan` somente quando `port_scan_detected=True` (sem polling a cada 5s). Variável de ambiente renomeada de `MONITOR_CONNECTIONS_URL` para `MONITOR_PORTSCAN_URL`.*  
*Adições v5.1: fix LD_LIBRARY_PATH para PyInstaller, resolução explícita do binário tcpdump, logging de diagnóstico do tcpdump, nota sobre binutils para compilação, validação completa de brute force e port scan.*  
*Adições v5.2: sender.py — variável `API_KEY` e header `X-API-Key` adicionados (alinhamento com backend); `MONITOR_TOKEN`/`Authorization: Bearer` mantidos como legado; exemplo de env atualizado.*  
*Adições v5.3 (Fase A — hardening): `MONITOR_TOKEN` e `Authorization: Bearer` removidos de `sender.py`; agente envia exclusivamente `X-API-Key`.*
