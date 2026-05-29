# Agent Monitor — Documentação Técnica

**Versão 5.0 | Maio 2026**

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
   - 6.1 CPU Discovery
   - 6.2 Memory Discovery
   - 6.3 Disk Discovery
   - 6.4 Network Discovery
   - 6.5 Motherboard Discovery
   - 6.6 System Discovery
   - 6.7 Tools Discovery
7. [Módulo: coleta](#7-módulo-coleta)
   - 7.1 CPU Coleta
   - 7.2 Memory Coleta
   - 7.3 Disk Coleta *(IOPS)*
   - 7.4 Network Coleta *(bytes/sec)*
   - 7.5 Logs Coleta
   - 7.6 Connections Coleta
   - 7.7 Process Coleta *(Top Processos)*
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

**Coleta Contínua** — a cada 5 segundos, envia via HTTP POST:
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

**Objetivo:** Desenvolver um agente nativo (Linux) que coleta métricas do sistema e logs de segurança, enviando-os via HTTP para o servidor central.

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

### Período de Pitch (06 – 12/06)

- **P.1** Garantir que o agente está funcionando na VM que será usada na apresentação
- **P.2** Preparar roteiro de demonstração: `systemctl status linux-agent` → simular ataque SSH → mostrar alerta no dashboard
- **P.3** Estar disponível para suporte técnico durante a apresentação

---

## 3. Estrutura de Diretórios

```
Agent/
├── pyproject.toml
├── install.sh                      ← instala como serviço systemd
├── linux-agent.service             ← definição do serviço
├── agent.spec                      ← spec gerado pelo PyInstaller
├── Agent_Exec/
│   ├── main.py                     ← entry point do PyInstaller
│   ├── dist/                       ← binário final gerado
│   └── build/                      ← artefatos intermediários
└── src/
    └── agent/
        ├── __init__.py
        ├── __main__.py             ← ponto de entrada principal
        ├── global_information/
        │   └── global_information.py
        ├── discovery/
        │   ├── __init__.py
        │   ├── cpu_discovery/
        │   │   ├── cpu.py
        │   │   ├── cpu_physical.py
        │   │   └── cpu_virtual.py
        │   ├── mem_discovery/
        │   │   ├── mem.py
        │   │   ├── mem_physical.py
        │   │   └── mem_virtual.py
        │   ├── disk_discovery/
        │   │   ├── disk.py
        │   │   ├── disk_physical.py
        │   │   └── disk_virtual.py
        │   ├── network_discovery/
        │   │   ├── network.py
        │   │   ├── network_physical.py
        │   │   └── network_virtual.py
        │   ├── motherboard_discovery/
        │   │   ├── motherboard.py
        │   │   └── motherboard_physical.py
        │   ├── system_discovery/
        │   │   ├── system.py
        │   │   ├── system_physical.py
        │   │   └── system_virtual.py
        │   └── tools_discovery/
        │       ├── tools.py
        │       ├── tools_checker.py
        │       ├── tools_physical.py
        │       └── tools_virtual.py
        ├── coleta/
        │   ├── collector.py                        ← orquestrador
        │   ├── cpu_coleta/cpu.py
        │   ├── mem_coleta/mem.py
        │   ├── disk_coleta/disk.py                 ← inclui IOPS
        │   ├── network_coleta/network.py            ← inclui bytes/sec
        │   ├── logs_coleta/logs.py
        │   ├── connections_coleta/connections.py
        │   └── process_coleta/processes.py         ← top processos
        └── utils/
            ├── parsers.py
            ├── sender.py                           ← envio HTTP + retry + heartbeat
            ├── retry_queue.py                      ← fila de retry persistente
            ├── serializer.py
            ├── shell.py
            └── logger.py                           ← logging rotativo
```

**Diretórios em runtime (criados pelo `install.sh`):**

| Caminho | Finalidade |
|---------|------------|
| `/opt/monitor-agent/` | Binário instalado |
| `/etc/monitor-agent/env` | Variáveis de ambiente (chmod 600) |
| `/var/log/monitor-agent/` | Arquivo de log rotativo |
| `/var/cache/monitor-agent/` | Fila de retry (`retry_queue.json`) |

---

## 4. Fluxo de Execução

Ao ser iniciado, o agente segue este fluxo:

| Etapa | Descrição |
|-------|-----------|
| 1 | `build_global_information("discovery")` — resolve identidade, detecta ambiente, persiste IDs em disco |
| 2 | `get_tools_info()` — verifica e instala dependências se necessário |
| 3 | `run_discovery()` — executa todos os módulos de discovery via `_safe_collect()` |
| 4 | `send_discovery(discovery)` — envia payload ao backend (`POST /api/discovery`) |
| 5 | Loop infinito (5s): **flush retry → heartbeat → métricas → logs → conexões** |

**Detalhe do loop contínuo:**

```
┌─ início do ciclo ─────────────────────────────────────────┐
│  1. flush_retry_queue()  — reenviar payloads pendentes     │
│  2. send_heartbeat()     — sinal de vida mínimo            │
│  3. collect_all()        — CPU, RAM, disco, rede, processos│
│     send_metrics()                                         │
│  4. collect_auth_logs()  — novas linhas de auth.log        │
│     send_log() (uma chamada por linha)                     │
│  5. collect_connections() — TCP ativas + port scan         │
│     send_connections()                                     │
│  time.sleep(5)                                             │
└───────────────────────────────────────────────────────────┘
```

**Flag `--install-deps`:** força instalação de ferramentas ausentes sem prompt interativo.

**Flag `--debug-exec`:** exibe cada payload no terminal via `json.dumps()` em vez de enviá-los ao backend. Útil para validar o formato dos dados em desenvolvimento ou na VM antes de apontar para o servidor real.

```bash
# Com o venv (desenvolvimento)
python -m agent --debug-exec

# Com o binário instalado
/opt/monitor-agent/agent --debug-exec

# Filtrar só os JSONs, sem logs no terminal
/opt/monitor-agent/agent --debug-exec 2>/dev/null
```

**Resiliência por isolamento:** cada módulo de discovery é chamado via `_safe_collect()`, que captura exceções individualmente. Se um módulo falhar, o campo fica com `{"error": "<mensagem>"}` e o agente continua.

---

## 5. Módulo: global_information

**Arquivo:** `agent/global_information/global_information.py`

Monta o bloco `global` que encabeça todos os payloads (discovery, métricas, logs, conexões e heartbeat). É chamado uma vez por tipo de coleta na inicialização. Centraliza a detecção de ambiente.

### Funções internas

**`_load_or_create_id(filename)`** — Lê o ID do arquivo em `~/.agent/<filename>`. Se não existir ou for inválido, gera um número de 5 dígitos (10000–99999) e salva.

**`_get_hostname()`** — Retorna o FQDN via `socket.getfqdn()`. Fallback: `socket.gethostname()`.

**`_get_primary_ip()`** — Determina o IP primário conectando um socket UDP ao `8.8.8.8:80`. Nenhum pacote é enviado — consulta a tabela de roteamento do kernel.

**`_detect_environment()`** — Executa `lscpu` e verifica o campo `Hypervisor Vendor`. Se presente, o host é virtualizado.

**`_build_notes(is_virtualized)`** — Gera lista de notas informativas para o backend sobre campos indisponíveis em VM.

### Payload gerado

```json
{
  "collection_type": "discovery",
  "schema_version":  "1.0",
  "agent_id":        "38472",
  "host_id":         "71203",
  "hostname":        "servidor-01.exemplo.com",
  "primary_ip":      "192.168.1.42",
  "environment": {
    "is_virtualized": true,
    "hypervisor":     "VMware"
  },
  "notes": [
    "cpu topology reflects VM vCPU allocation, not physical cores",
    "memory slots unavailable in virtualized environments",
    "disk is virtual — smartctl data unavailable",
    "network hardware fields (speed, driver, bus_info) unavailable in VM",
    "motherboard section absent in virtualized environments"
  ]
}
```

| Campo | Descrição |
|-------|-----------|
| `collection_type` | `"discovery"`, `"metrics"`, `"logs"`, `"connections"` ou `"heartbeat"` |
| `schema_version` | Versão do schema — incrementar em breaking changes |
| `agent_id` | ID único do agente persistido em `~/.agent/agent_id.txt` |
| `host_id` | ID único do host persistido em `~/.agent/host_id.txt` |
| `hostname` | FQDN ou hostname do sistema |
| `primary_ip` | IP da rota de saída (interface preferida) |
| `environment` | `is_virtualized` + `hypervisor` |
| `notes` | Lista de avisos sobre campos indisponíveis (vazia em físico) |

---

## 6. Módulo: discovery

O módulo de discovery é executado uma única vez após a inicialização e coleta o inventário completo de hardware e SO. Todos os sub-módulos recebem `is_virtualized` como parâmetro e delegam para o handler `_physical` ou `_virtual` correspondente.

### 6.1 CPU Discovery

**Arquivos:** `discovery/cpu_discovery/cpu.py`, `cpu_physical.py`, `cpu_virtual.py`

**Fontes de dados:**
- `lscpu` — modelo, fabricante, arquitetura, número de CPUs lógicas, threads por core, hipervisor
- `/proc/cpuinfo` — dados complementares por núcleo lógico
- `sysfs` (`/sys/devices/system/cpu/cpu0/cpufreq/`) — frequências base, máxima e mínima em kHz

**Hardware físico:** coleta `model_name`, `vendor`, `architecture`, `threads_per_core`, `cores_logical`, frequências. A frequência base é buscada primeiro no sysfs e depois em `lscpu` como fallback.

**Ambiente virtualizado:** a topologia reflete a alocação de vCPUs. `threads_per_core` retorna `null` quando genérico (`"1"`).

| Campo | Descrição |
|-------|-----------|
| `model_name` | Modelo do processador |
| `vendor` | Fabricante (Intel, AMD...) |
| `architecture` | Arquitetura (x86_64, arm64...) |
| `topology.vcpus` | vCPUs alocados (somente VMs) |
| `topology.cores_logical` | CPUs lógicas (somente físico) |
| `frequency.base_mhz` | Frequência base com campo `source` |
| `frequency.max_mhz` | Frequência máxima com campo `source` |
| `frequency.min_mhz` | Frequência mínima com campo `source` |

### 6.2 Memory Discovery

**Arquivos:** `discovery/mem_discovery/mem.py`, `mem_physical.py`, `mem_virtual.py`

**Fontes de dados:**
- `/proc/meminfo` — total, disponível, livre, buffers, cached, swap
- `dmidecode -t memory` (somente físico, requer root) — slots físicos, fabricante, tipo DDR, velocidade

| Campo | Descrição |
|-------|-----------|
| `total_bytes` | RAM total em bytes |
| `swap_total_bytes` | Swap total em bytes |
| `slots` | `null` em VM; lista de módulos em físico |

### 6.3 Disk Discovery

**Arquivos:** `discovery/disk_discovery/disk.py`, `disk_physical.py`, `disk_virtual.py`

**Fontes de dados:**
- `lsblk -J -b -o NAME,SIZE,TYPE,ROTA,MOUNTPOINT,FSTYPE,LABEL,UUID,MODEL,VENDOR,SERIAL,TRAN,RM`
- `smartctl -i -j` (somente físico, requer root)

**Resolução de tipo de disco (`resolve_disk_type`):**

| Prioridade | Condição | Resultado |
|------------|----------|-----------|
| 1 | `is_virtual=True` | `"Virtual"` |
| 2 | `rotation_rate=0` | `"SSD"` |
| 3 | `rotation_rate>0` | `"HDD"` |
| 4 | `rota_flag` do lsblk | `"HDD"` ou `"SSD"` |
| 5 | sem dados | `"Unknown"` |

| Campo | Descrição |
|-------|-----------|
| `device` | Caminho do dispositivo (ex: `/dev/sda`) |
| `model` / `vendor` / `serial` | Identificação do disco |
| `type` | `HDD` \| `SSD` \| `Virtual` \| `Unknown` |
| `interface` | `SATA` \| `NVMe` \| `SCSI` \| `USB`... |
| `size_bytes` | Tamanho do disco em bytes |
| `health` | `smart_passed`, `power_on_hours`, `temperature_celsius` (`null` em VM) |
| `partitions` | Lista recursiva de partições com `role` inferido |

### 6.4 Network Discovery

**Arquivos:** `discovery/network_discovery/network.py`, `network_physical.py`, `network_virtual.py`

**Fontes de dados:**
- `ip -j addr show`, `ip -j link show`, `ip -j route show default`
- `sysfs` (`/sys/class/net/<iface>/`) — speed, duplex, driver, bus_info (somente físico)

| Campo | Descrição |
|-------|-----------|
| `total_interfaces` | Número de interfaces |
| `default_gateway` | `gateway` e `interface` da rota padrão |
| `interfaces[].name` | Nome da interface |
| `interfaces[].mac` | Endereço MAC |
| `interfaces[].mtu` | MTU |
| `interfaces[].state` | Estado operacional |
| `interfaces[].ipv4` / `ipv6` | Endereços com prefixo, escopo e broadcast |
| `interfaces[].speed_mbps` | Velocidade em Mbps (somente físico) |
| `interfaces[].driver` | Driver do kernel (somente físico) |

### 6.5 Motherboard Discovery

**Arquivos:** `discovery/motherboard_discovery/motherboard.py`, `motherboard_physical.py`

**Fontes de dados:** `dmidecode -t 0/2/4/9/17`, `lspci`

**Ambiente virtualizado:** o campo `motherboard` retorna `null` — o hipervisor não expõe informações úteis.

| Campo | Descrição |
|-------|-----------|
| `manufacturer` / `product_name` | Fabricante e modelo |
| `chipset` | Chipset via lspci (`null` em VM) |
| `bios` | `vendor`, `version`, `release_date`, `revision` |
| `cpu_sockets` | Total de sockets e quantos populados |
| `ram_slots` | Total, usados e livres |
| `expansion_slots` | Lista de slots PCIe |

### 6.6 System Discovery

**Arquivos:** `discovery/system_discovery/system.py`, `system_physical.py`, `system_virtual.py`

**Fontes de dados:** `/etc/os-release`, `uname -a`, `hostname -f`, `/proc/uptime`, `timedatectl`

| Campo | Descrição |
|-------|-----------|
| `hostname` | Nome completo do host |
| `os.name` / `pretty_name` | Nome e versão amigável do SO |
| `kernel.release` / `version` / `machine` | Dados do kernel |
| `timezone` | Fuso horário configurado |
| `uptime_seconds` | Tempo de atividade em segundos |

### 6.7 Tools Discovery

**Arquivos:** `discovery/tools_discovery/tools.py`, `tools_checker.py`, `tools_physical.py`, `tools_virtual.py`

Verifica quais ferramentas externas estão disponíveis e, opcionalmente, instala as ausentes. Executado primeiro dentro do `run_discovery()`.

**Ferramentas verificadas em físico:** `lscpu`, `lsblk`, `ip`, `dmidecode`, `smartctl`, `ethtool`, `lspci`, `journalctl`, `timedatectl`

**Ferramentas verificadas em VM:** `lscpu`, `lsblk`, `ip`, `journalctl`, `timedatectl`

**Lógica de instalação:** verifica via `shutil.which` → detecta gerenciador de pacotes (`apt`, `dnf`, `pacman`, `zypper`) → instala se `--install-deps` ou terminal interativo com confirmação do usuário.

---

## 7. Módulo: coleta

O módulo de coleta executa em loop infinito a cada 5 segundos. Todos os sub-módulos usam `psutil` para acessar informações do sistema.

**Arquivo principal:** `coleta/collector.py`

```python
def collect_all():
    return {
        "cpu":       get_cpu_usage(),
        "memory":    get_memory_usage(),
        "disk":      get_disk_usage(),       # inclui IOPS
        "network":   get_network_usage(),    # inclui bytes/sec
        "processes": get_top_processes(),    # top 15 por categoria
    }

def collect_auth_logs() -> list[dict]:
    return get_new_auth_log_lines()

def collect_connections() -> dict:
    return get_active_connections()
```

### 7.1 CPU Coleta

**Arquivo:** `coleta/cpu_coleta/cpu.py`

Usa `psutil.cpu_percent(interval=1)`, que mede o uso durante 1 segundo.

| Campo | Descrição |
|-------|-----------|
| `percent` | Percentual de uso da CPU (0–100) |

### 7.2 Memory Coleta

**Arquivo:** `coleta/mem_coleta/mem.py`

Usa `psutil.virtual_memory()`.

| Campo | Descrição |
|-------|-----------|
| `total` | RAM total em bytes |
| `used` | Memória utilizada em bytes |
| `percent` | Percentual de uso (0–100) |

### 7.3 Disk Coleta

**Arquivo:** `coleta/disk_coleta/disk.py`

Usa `psutil.disk_usage('/')` para espaço e `psutil.disk_io_counters()` para I/O. Os campos de IOPS e bytes/sec são calculados como **delta** entre o ciclo atual e o anterior (variáveis de módulo `_prev_io` e `_prev_time`). No **primeiro ciclo**, esses campos não são incluídos no payload — o backend deve tratá-los como ausentes/`null`.

| Campo | Descrição |
|-------|-----------|
| `total` | Espaço total em bytes |
| `used` | Espaço utilizado em bytes |
| `percent` | Percentual de uso (0–100) |
| `read_iops` | Operações de leitura por segundo *(ausente no 1º ciclo)* |
| `write_iops` | Operações de escrita por segundo *(ausente no 1º ciclo)* |
| `read_bytes_per_sec` | Bytes lidos por segundo *(ausente no 1º ciclo)* |
| `write_bytes_per_sec` | Bytes escritos por segundo *(ausente no 1º ciclo)* |

### 7.4 Network Coleta

**Arquivo:** `coleta/network_coleta/network.py`

Usa `psutil.net_io_counters()`. Os contadores acumulados (`bytes_sent`, `bytes_recv`) refletem o total desde o boot. As taxas por segundo são calculadas como **delta** entre ciclos, da mesma forma que o IOPS do disco.

| Campo | Descrição |
|-------|-----------|
| `bytes_sent` | Total de bytes enviados desde o boot (acumulado) |
| `bytes_recv` | Total de bytes recebidos desde o boot (acumulado) |
| `bytes_sent_per_sec` | Bytes enviados por segundo *(ausente no 1º ciclo)* |
| `bytes_recv_per_sec` | Bytes recebidos por segundo *(ausente no 1º ciclo)* |

### 7.5 Logs Coleta

**Arquivo:** `coleta/logs_coleta/logs.py`

Lê `/var/log/auth.log` de forma incremental, rastreando byte offset e inode em `~/.agent/auth_log_state.json`.

- **Primeira execução:** envia as últimas 100 linhas e salva posição no final
- **Execuções seguintes:** envia apenas linhas novas
- **Rotação detectada:** inode diferente → reinicia leitura do novo arquivo

**Permissão necessária:** grupo `adm` ou root.

```json
{
  "timestamp": "2026-05-18T14:35:00+00:00",
  "raw_line":  "May 18 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100"
}
```

### 7.6 Connections Coleta

**Arquivo:** `coleta/connections_coleta/connections.py`

Combina `psutil.net_connections(kind="tcp")` para listar conexões ativas com **detecção de port scan entrante via tcpdump**.

#### Detecção de port scan (tcpdump)

Duas threads daemon são iniciadas no momento do import do módulo:

**Thread `tcpdump-capture`:** executa `tcpdump -n -l -i any` com filtro `tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0`, capturando cada pacote SYN que chega à máquina. Pacotes cujo IP de origem pertence ao próprio host (IPs locais resolvidos via `psutil.net_if_addrs()`) são descartados — assim apenas tráfego externo entrante é contabilizado.

**Thread `portscan-eval` (ciclo de 2s):** mantém uma janela deslizante de 60 segundos por IP de origem. A cada 2 segundos, poda entradas expiradas e atualiza `_active_scans` com os IPs que atingiram o limiar de portas distintas.

**Limiar:** `_PORTSCAN_THRESHOLD = 10` portas distintas de um mesmo IP em 60 segundos.

**Graceful degradation:** se `tcpdump` não estiver instalado ou o processo não tiver permissão, a thread encerra silenciosamente. `port_scan_detected` permanece sempre `false` — o restante da coleta não é afetado.

**Permissão necessária:** root ou `cap_net_raw` (atendido automaticamente quando instalado via `install.sh`).

#### Campos retornados por `get_active_connections()`

| Campo | Descrição |
|-------|-----------|
| `connections[].local_port` | Porta local |
| `connections[].remote_ip` | IP remoto |
| `connections[].remote_port` | Porta remota |
| `connections[].state` | Estado da conexão (`ESTABLISHED`, `SYN_SENT`, etc.) |
| `total` | Total de conexões rastreadas |
| `port_scan_detected` | `true` se algum IP atingiu o limiar de portas distintas |
| `scan_sources` | `{ip_atacante: qtd_portas_distintas, ...}` — IPs ativos no scan |

### 7.7 Process Coleta

**Arquivo:** `coleta/process_coleta/processes.py`

Usa `psutil.process_iter()` para iterar sobre todos os processos e retornar quatro listas de top 15, cada uma ordenada por um critério diferente.

**Comportamento da CPU:** `cpu_percent` usa cache interno do psutil. No primeiro ciclo (início do agente) todos os processos retornam `0.0` — a partir do segundo ciclo os valores são precisos.

**Comportamento do disco:** `disk_bytes` é o valor acumulado de bytes lidos + escritos desde que o processo foi iniciado (não é taxa por segundo). O backend pode calcular delta entre amostras se necessário.

**Comportamento de rede:** psutil não expõe bytes de rede por processo sem leitura complexa de `/proc`. O campo `open_connections` (número de conexões TCP/UDP abertas) é usado como proxy de atividade de rede.

```python
def _top(key: str) -> list:
    return sorted(procs, key=lambda x: x[key], reverse=True)[:n]

return {
    "top_cpu":     _top("cpu_percent"),
    "top_memory":  _top("memory_rss"),
    "top_disk":    _top("disk_bytes"),
    "top_network": _top("open_connections"),
}
```

**Campos por processo:**

| Campo | Descrição |
|-------|-----------|
| `pid` | ID do processo |
| `name` | Nome do executável |
| `username` | Usuário que o executa |
| `cpu_percent` | % de CPU utilizada |
| `memory_rss` | Memória RAM física (RSS) em bytes |
| `disk_bytes` | Total de bytes lidos + escritos (acumulado desde o início do processo) |
| `open_connections` | Número de conexões TCP/UDP abertas |

**Tratamento de permissão:** processos de outros usuários podem lançar `AccessDenied` no `p.connections()`. Nesses casos, `open_connections` é definido como `0` e o processo continua nas demais listas.

---

## 8. Estrutura dos Payloads

### 8.1 Payload de Discovery

Enviado uma vez na inicialização. Endpoint: `POST /api/discovery`

```json
{
  "global": { "collection_type": "discovery", "..." },
  "system":      { "..." },
  "cpu":         { "..." },
  "memory":      { "..." },
  "disk":        { "..." },
  "network":     { "..." },
  "motherboard": { "..." },
  "tools":       { "..." }
}
```

### 8.2 Payload de Métricas

Enviado a cada 5 segundos. Endpoint: `POST /api/metrics`

```json
{
  "type":      "metrics",
  "global":    { "collection_type": "metrics", "agent_id": "38472", "host_id": "71203", "..." },
  "timestamp": "2026-05-20T14:35:00.123456+00:00",
  "data": {
    "timestamp": "2026-05-20T14:35:00.123456+00:00",
    "cpu":    { "percent": 23.5 },
    "memory": { "total": 8589934592, "used": 4294967296, "percent": 50.0 },
    "disk": {
      "total":              107374182400,
      "used":               53687091200,
      "percent":            50.0,
      "read_iops":          45.2,
      "write_iops":         12.8,
      "read_bytes_per_sec": 184320.0,
      "write_bytes_per_sec":52428.8
    },
    "network": {
      "bytes_sent":         1048576,
      "bytes_recv":         5242880,
      "bytes_sent_per_sec": 2048.5,
      "bytes_recv_per_sec": 10240.0
    },
    "processes": {
      "top_cpu": [
        { "pid": 1234, "name": "python3", "username": "root", "cpu_percent": 45.2, "memory_rss": 52428800, "disk_bytes": 1048576, "open_connections": 3 }
      ],
      "top_memory": [ { "..." } ],
      "top_disk":   [ { "..." } ],
      "top_network":[ { "..." } ]
    }
  }
}
```

> **Nota:** `read_iops`, `write_iops`, `read_bytes_per_sec`, `write_bytes_per_sec`, `bytes_sent_per_sec` e `bytes_recv_per_sec` estão **ausentes** no payload do primeiro ciclo (sem dados anteriores para calcular delta). O backend deve tratar ausência desses campos como `null`.

### 8.3 Payload de Log

Enviado uma linha por request. Endpoint: `POST /api/logs`

```json
{
  "global":    { "collection_type": "logs", "..." },
  "log_type":  "auth",
  "timestamp": "2026-05-18T14:35:00+00:00",
  "raw_line":  "May 18 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100"
}
```

### 8.4 Payload de Conexões

Enviado a cada 5 segundos. Endpoint: `POST /api/connections`

```json
{
  "global":    { "collection_type": "connections", "..." },
  "timestamp": "2026-05-20T14:35:00.123456+00:00",
  "connections": [
    { "local_port": 22, "remote_ip": "192.168.1.100", "remote_port": 54321, "state": "ESTABLISHED" }
  ],
  "total":              1,
  "port_scan_detected": true,
  "scan_sources": {
    "10.0.0.5": 45
  }
}
```

`scan_sources` é um dicionário `{ip_atacante: qtd_portas_distintas_em_60s}`. Contém apenas IPs que ultrapassaram o limiar de 10 portas. Quando não há scan, o campo é `{}` e `port_scan_detected` é `false`.
```

### 8.5 Payload de Heartbeat

Enviado no início de cada ciclo (antes das métricas). Endpoint: `POST /api/heartbeat`

```json
{
  "type":      "heartbeat",
  "global":    { "collection_type": "metrics", "agent_id": "38472", "host_id": "71203", "..." },
  "timestamp": "2026-05-20T14:35:00.123456+00:00"
}
```

**Finalidade:** permite ao backend distinguir "agente vivo mas com falha na coleta de métricas" de "agente morto". Falhas no heartbeat são logadas em `DEBUG` e **nunca enfileiradas** para retry — um heartbeat stale não tem valor.

---

## 9. Módulo: utils

### `agent/utils/parsers.py`

Todos os parsers centralizados. Nenhuma chamada shell acontece aqui — apenas transformação de dados.

| Seção | Funções | Usada por |
|-------|---------|-----------|
| Parsers de CPU | `parse_lscpu()`, `parse_cpuinfo()` | `cpu_*`, `global_information` |
| Parsers de Memória | `parse_meminfo()`, `parse_dmidecode_memory()`, `parse_dmi_size_to_mb()` | `mem_*` |
| Parsers de Disco | `parse_lsblk()`, `parse_smartctl()`, `resolve_disk_type()`, `resolve_disk_interface()`, `resolve_partition_role()` | `disk_*` |
| Parsers de Rede | `parse_ip_addr()`, `parse_ip_link()`, `parse_default_gateway()`, `build_network_interface()` | `network_*` |
| Parsers de SO | `parse_os_release()`, `parse_uname()`, `parse_uptime_seconds()`, `clean_hostname()`, `clean_timezone()` | `system_*` |
| Parsers de Placa-mãe | `parse_baseboard()`, `parse_bios()`, `parse_cpu_sockets()`, `parse_memory_slots_summary()`, `parse_system_slots()` | `motherboard_*` |
| Conversão de unidades | `kb_to_bytes()`, `bytes_to_gb()`, `safe_float()`, `safe_int()` | Geral |
| Sanitização | `_clean()`, `sanitize_string()`, `read_sysfs_khz_to_mhz()` | Geral |

### `agent/utils/shell.py`

| Função | Descrição |
|--------|-----------|
| `run(cmd)` | Executa comando com `LC_ALL=C`. Retorna `stdout` ou `None` em qualquer falha. Timeout: 10s. |
| `run_permissive(cmd)` | Retorna `stdout` mesmo com exit code não-zero. Usado para `smartctl`. Timeout: 15s. |

> **`LC_ALL=C` é obrigatório** — garante saída em inglês independente do locale. Sem isso, `lscpu` em português retorna `"Arquitetura"` em vez de `"Architecture"`, quebrando os parsers silenciosamente.

### `agent/utils/logger.py`

Configura o sistema de logging. Singleton via `get_logger()` — todos os módulos importam o mesmo logger instance.

**Saídas:**

| Handler | Destino | Configuração |
|---------|---------|--------------|
| `StreamHandler` | stdout → journald | `[YYYY-MM-DD HH:MM:SS] [LEVEL] mensagem` |
| `RotatingFileHandler` | `/var/log/monitor-agent/agent.log` | 10 MB por arquivo, 5 backups |

**`log_payload(logger, label, payload)`:** loga o JSON completo apenas em nível `DEBUG`. Chamada em `__main__.py` (discovery) e `sender.py` (antes de cada POST).

**`logger.exception()`:** usado em todos os blocos `except` — registra mensagem + traceback completo automaticamente.

### `agent/utils/retry_queue.py`

Fila de retry persistente em disco. Armazena payloads que falharam por `ConnectionError` ou `Timeout` para reenvio automático no próximo ciclo.

**Funções públicas:**

| Função | Descrição |
|--------|-----------|
| `enqueue(payload, url)` | Adiciona item à fila. Se `MAX_ITEMS` atingido, o item mais antigo é descartado. |
| `load_queue()` | Lê e retorna a fila atual como lista. |
| `save_queue(queue)` | Persiste a fila no arquivo. |

**Arquivo:** `QUEUE_FILE` = `/var/cache/monitor-agent/retry_queue.json` (configurável via `MONITOR_RETRY_FILE`)

**Limite:** `MAX_ITEMS` = 50 (configurável via `MONITOR_RETRY_MAX`)

**Corrupção:** se o arquivo JSON estiver corrompido, é descartado silenciosamente com `WARNING` no log e a fila recomeça vazia.

---

## 10. Módulo: sender

**Arquivo:** `agent/utils/sender.py`

Responsável por enviar os payloads ao backend via HTTP POST, gerenciar a fila de retry e enviar o heartbeat.

### URLs configuradas

```python
API_BASE_URL    = os.getenv("MONITOR_API_BASE_URL", "http://api.monitoramento.lan")
DISCOVERY_URL   = os.getenv("MONITOR_DISCOVERY_URL")   or f"{API_BASE_URL}/api/discovery"
METRICS_URL     = os.getenv("MONITOR_METRICS_URL")     or f"{API_BASE_URL}/api/metrics"
LOGS_URL        = os.getenv("MONITOR_LOGS_URL")        or f"{API_BASE_URL}/api/logs"
CONNECTIONS_URL = os.getenv("MONITOR_CONNECTIONS_URL") or f"{API_BASE_URL}/api/connections"
HEARTBEAT_URL   = os.getenv("MONITOR_HEARTBEAT_URL")   or f"{API_BASE_URL}/api/heartbeat"
TOKEN           = os.getenv("MONITOR_TOKEN", "")
```

### Cabeçalhos enviados

| Cabeçalho | Valor |
|-----------|-------|
| `Content-Type` | `application/json` |
| `Authorization` | `Bearer {TOKEN}` (somente se `MONITOR_TOKEN` não for vazio) |

### Funções públicas

| Função | Endpoint | Comportamento em falha |
|--------|----------|------------------------|
| `send_discovery(data)` | `POST /api/discovery` | Enfileira em `ConnectionError`/`Timeout` |
| `send_metrics(data)` | `POST /api/metrics` | Enfileira em `ConnectionError`/`Timeout` |
| `send_log(data)` | `POST /api/logs` | Enfileira em `ConnectionError`/`Timeout` |
| `send_connections(data)` | `POST /api/connections` | Enfileira em `ConnectionError`/`Timeout` |
| `send_heartbeat(data)` | `POST /api/heartbeat` | Falha logada em `DEBUG`, **nunca enfileirada** |
| `flush_retry_queue()` | Itera sobre a fila | Para no 1º item que falhar (conexão ainda caída) |

### Lógica de retry

```
flush_retry_queue():
  para cada item na fila:
    tenta POST
    se ConnectionError/Timeout:
      mantém este item + todos os seguintes
      interrompe (conexão ainda caída)
    se HTTPError (4xx/5xx):
      descarta item (servidor rejeitou — não adianta retentar)
    se sucesso:
      remove item da fila
  salva fila restante
```

`flush_retry_queue()` é chamado uma vez no início de cada ciclo em `__main__.py`, antes de qualquer envio novo.

### Tratamento de erros em `send_data()`

| Exceção | Ação |
|---------|------|
| `ConnectionError` | `logger.error()` + enfileira para retry |
| `Timeout` | `logger.error()` + enfileira para retry |
| `HTTPError` (4xx/5xx) | `logger.error()` com body da resposta — não enfileira |
| Exceção genérica | `logger.exception()` com traceback — não enfileira |

---

## 11. Organização como Módulo Python

### `pyproject.toml`

```toml
[project]
name    = "agent-monitor"
version = "1.0.0"
dependencies = ["psutil", "requests"]

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
agent = "agent.__main__:main"
```

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

`--debug-exec` substitui o `--dry-run` anterior. Imprime cada payload JSON no stdout em vez de enviá-lo. Útil para:
- Validar o formato dos dados durante desenvolvimento
- Verificar os JSONs antes de apontar para o servidor real
- Debug sem depender da disponibilidade do backend

```bash
# Filtrar apenas os JSONs (sem linhas de log no stderr)
/opt/monitor-agent/agent --debug-exec 2>/dev/null
```

---

## 12. Geração do Executável com PyInstaller

O agente é distribuído como um binário Linux único, sem dependência de Python na máquina alvo.

### Entry point

`Agent_Exec/main.py` é minimal — apenas importa e chama `main()`:

```python
from agent.__main__ import main

if __name__ == "__main__":
    main()
```

### Comando de geração

```bash
pyinstaller --onefile -n agent \
  --paths src \
  --distpath Agent_Exec/dist \
  --workpath Agent_Exec/build \
  Agent_Exec/main.py
```

| Flag | Descrição |
|------|-----------|
| `--onefile` | Empacota tudo em um único binário autocontido |
| `-n agent` | Nome do executável gerado |
| `--paths src` | Adiciona `src/` ao PYTHONPATH interno do PyInstaller |
| `--distpath` | Saída do binário final (`Agent_Exec/dist/`) |

O binário final fica em `Agent_Exec/dist/agent`.

### Atualizar o binário instalado

```bash
# Opção 1 — substituição direta
sudo systemctl stop linux-agent
sudo cp Agent_Exec/dist/agent /opt/monitor-agent/agent
sudo systemctl start linux-agent

# Opção 2 — reinstalação completa (reconfigura se necessário)
sudo ./install.sh
```

---

## 13. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MONITOR_API_BASE_URL` | `http://api.monitoramento.lan` | URL base do backend |
| `MONITOR_DISCOVERY_URL` | `{BASE}/api/discovery` | Override do endpoint de discovery |
| `MONITOR_METRICS_URL` | `{BASE}/api/metrics` | Override do endpoint de métricas |
| `MONITOR_LOGS_URL` | `{BASE}/api/logs` | Override do endpoint de logs |
| `MONITOR_CONNECTIONS_URL` | `{BASE}/api/connections` | Override do endpoint de conexões |
| `MONITOR_HEARTBEAT_URL` | `{BASE}/api/heartbeat` | Override do endpoint de heartbeat |
| `MONITOR_TOKEN` | `""` | Bearer token (opcional — sem header Auth se vazio) |
| `MONITOR_LOG_LEVEL` | `INFO` | Nível de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MONITOR_RETRY_FILE` | `/var/cache/monitor-agent/retry_queue.json` | Caminho da fila de retry |
| `MONITOR_RETRY_MAX` | `50` | Máximo de itens na fila de retry |

**`MONITOR_TOKEN`:** opcional. Se vazio, o header `Authorization` não é incluído nas requisições.

**`MONITOR_LOG_LEVEL=DEBUG`:** loga os JSONs completos de cada payload antes de enviá-los — útil para depurar a integração com o backend.

**Exemplo de arquivo `/etc/monitor-agent/env`:**

```ini
MONITOR_API_BASE_URL=http://192.168.1.50:5000
MONITOR_TOKEN=
MONITOR_LOG_LEVEL=INFO
```

---

## 14. Dependências

### Python (runtime)

| Pacote | Uso |
|--------|-----|
| `psutil` | CPU, memória, disco, rede I/O, conexões TCP, processos |
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
| `tcpdump` | tcpdump | Captura de pacotes SYN para detecção de port scan | Sim (root ou cap_net_raw) |

---

## 15. Resumo dos Módulos

| Módulo | Arquivo | Função |
|--------|---------|--------|
| `__main__` | `agent/__main__.py` | Ponto de entrada — orquestra discovery e loop de coleta |
| `global_information` | `global_information/global_information.py` | Bloco de identidade dos payloads |
| `discovery.*` | `discovery/*/` | Inventário de hardware/SO (executado uma vez) |
| `coleta.collector` | `coleta/collector.py` | Orquestrador da coleta contínua |
| `coleta.cpu_coleta` | `coleta/cpu_coleta/cpu.py` | % CPU via psutil |
| `coleta.mem_coleta` | `coleta/mem_coleta/mem.py` | Uso de RAM via psutil |
| `coleta.disk_coleta` | `coleta/disk_coleta/disk.py` | Uso de disco + IOPS via psutil |
| `coleta.network_coleta` | `coleta/network_coleta/network.py` | Bytes I/O + bytes/sec via psutil |
| `coleta.logs_coleta` | `coleta/logs_coleta/logs.py` | Leitura incremental de auth.log |
| `coleta.connections_coleta` | `coleta/connections_coleta/connections.py` | Conexões TCP + detecção de port scan |
| `coleta.process_coleta` | `coleta/process_coleta/processes.py` | Top 15 processos por CPU, RAM, disco e conexões |
| `utils.parsers` | `utils/parsers.py` | Parsers de saída de comandos shell |
| `utils.sender` | `utils/sender.py` | HTTP POST + retry + heartbeat |
| `utils.retry_queue` | `utils/retry_queue.py` | Fila de retry persistente em JSON |
| `utils.shell` | `utils/shell.py` | Wrapper de subprocess com `LC_ALL=C` |
| `utils.serializer` | `utils/serializer.py` | Serialização JSON |
| `utils.logger` | `utils/logger.py` | Logging rotativo em `/var/log/monitor-agent/agent.log` |

---

## 16. Observações Importantes

### Sistema de Logging

| Handler | Consulta |
|---------|---------|
| journald | `journalctl -u linux-agent -f` |
| Arquivo rotativo | `tail -f /var/log/monitor-agent/agent.log` |

**`MONITOR_LOG_LEVEL=DEBUG`** loga os JSONs completos de cada payload antes de enviá-los. Ativar temporariamente:

```bash
sudo nano /etc/monitor-agent/env   # alterar para: MONITOR_LOG_LEVEL=DEBUG
sudo systemctl restart linux-agent
tail -f /var/log/monitor-agent/agent.log
```

### Fila de Retry

Payloads que falham por `ConnectionError` ou `Timeout` são persistidos em `/var/cache/monitor-agent/retry_queue.json`. O agente tenta reenviá-los automaticamente no início do próximo ciclo.

- **Limite:** 50 itens. Ao estourar, o item mais antigo é descartado com `WARNING` no log.
- **Erros HTTP (4xx/5xx)** não são enfileirados — o servidor rejeitou o payload, retentar não resolve.
- **Heartbeats** nunca são enfileirados — sinal de vida stale não tem valor.

Para inspecionar a fila manualmente:

```bash
cat /var/cache/monitor-agent/retry_queue.json | python3 -m json.tool
```

### Gerenciamento do Serviço

```bash
sudo systemctl start linux-agent      # iniciar
sudo systemctl stop linux-agent       # parar
sudo systemctl restart linux-agent    # reiniciar
sudo systemctl status linux-agent     # verificar status
sudo systemctl enable linux-agent     # habilitar no boot
sudo systemctl disable linux-agent    # desabilitar no boot
```

### Atualizar o Agente

```bash
# Compilar novo binário primeiro:
source .ambiente_venv/bin/activate
pyinstaller --onefile -n agent --paths src --distpath Agent_Exec/dist --workpath Agent_Exec/build Agent_Exec/main.py

# Substituir e reiniciar:
sudo systemctl stop linux-agent
sudo cp Agent_Exec/dist/agent /opt/monitor-agent/agent
sudo systemctl start linux-agent
```

Ou, para reinstalação completa com reconfiguração:

```bash
sudo ./install.sh
```

### Permissões

| Recurso | Permissão | Motivo |
|---------|-----------|--------|
| `/var/log/auth.log` | Grupo `adm` ou root | Leitura de logs de autenticação |
| `dmidecode` | root | Detalhes de RAM e placa-mãe |
| `smartctl` | root | Saúde do disco (S.M.A.R.T.) |
| `psutil.net_connections()` | root para outros usuários | Conexões TCP de processos de outros usuários |
| `tcpdump` | root ou `cap_net_raw` | Captura de pacotes SYN para detecção de port scan entrante |

Para adicionar usuário ao grupo `adm` (auth.log sem root):

```bash
sudo usermod -a -G adm $USER
# Fazer logout e login para aplicar
```

### Sincronização com Backend

Antes de modificar o formato de qualquer payload, validar com a equipe de Backend (Douglas e Fernando) o formato exato esperado. Em particular:

- **IOPS e bytes/sec** podem estar ausentes no primeiro ciclo — o backend deve aceitar payload sem esses campos.
- **`data.processes`** é uma estrutura nova — verificar se o endpoint `/api/metrics` já trata esse campo.
- **`POST /api/heartbeat`** é um endpoint novo que precisa ser implementado no backend.

### Firewall

A porta do servidor backend (ex: `5000`) deve estar acessível a partir da máquina do agente.

### Desinstalar

```bash
sudo systemctl stop linux-agent
sudo systemctl disable linux-agent
sudo rm /etc/systemd/system/linux-agent.service
sudo rm -rf /opt/monitor-agent
sudo rm -rf /etc/monitor-agent
sudo rm -rf /var/cache/monitor-agent
sudo systemctl daemon-reload
```

---

*Documentação gerada em 20/05/2026 — v5.0 | Semana 7: IOPS, bytes/sec, top processos, retry queue, heartbeat, --debug-exec*
*Atualizado em 29/05/2026 — v5.1 | Detecção de port scan migrada de SYN_SENT (saída) para tcpdump entrante com janela deslizante de 60s e avaliação a cada 2s. Campo `syn_sent_count` substituído por `scan_sources`.*
