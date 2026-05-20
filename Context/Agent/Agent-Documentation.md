# Agent Monitor — Documentação Técnica

**Versão 4.0 | Maio 2026**

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
   - 7.3 Disk Coleta
   - 7.4 Network Coleta (I/O)
   - 7.5 Logs Coleta
   - 7.6 Connections Coleta *(Semana 6)*
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
- Métricas de uso de CPU, memória, disco e tráfego de rede
- Novas linhas do `/var/log/auth.log` (leitura incremental)
- Estado das conexões TCP ativas e flag de detecção de port scan

O agente detecta automaticamente se está rodando em hardware físico ou em ambiente virtualizado (KVM, VMware, Xen, Hyper-V) e adapta a coleta conforme o que está disponível. Campos inexistentes em VMs (slots de RAM, S.M.A.R.T., speed de rede) são retornados como `null`, e uma seção `notes` no payload avisa o backend do motivo.

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
| 7      | 02/06 – 05/06 | Estabilidade, instalação e documentação           | 🔄 Pendente |

### Período de Pitch (06 – 12/06)

- **P.1** Garantir que o agente está funcionando na VM que será usada na apresentação
- **P.2** Preparar roteiro de demonstração: `systemctl status linux-agent` → simular ataque SSH → mostrar alerta no dashboard
- **P.3** Estar disponível para suporte técnico durante a apresentação

---

## 3. Estrutura de Diretórios

```
Agent/
├── pyproject.toml
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
        │   └── global_information.py   ← identidade do agente e do host
        ├── discovery/
        │   ├── __init__.py
        │   ├── cpu_discovery/
        │   │   ├── cpu.py          ← roteador físico/virtual
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
        │       ├── tools.py        ← ponto de entrada do módulo
        │       ├── tools_checker.py    ← lógica de verificação e instalação
        │       ├── tools_physical.py
        │       └── tools_virtual.py
        ├── coleta/
        │   ├── collector.py        ← orquestrador de coleta contínua
        │   ├── cpu_coleta/cpu.py
        │   ├── mem_coleta/mem.py
        │   ├── disk_coleta/disk.py
        │   ├── network_coleta/network.py
        │   ├── logs_coleta/logs.py
        │   └── connections_coleta/connections.py   ← SEMANA 6
        └── utils/
            ├── parsers.py          ← todos os parsers centralizados
            ├── sender.py           ← envio HTTP ao backend
            ├── serializer.py       ← serialização JSON
            └── shell.py            ← execução de comandos shell
```

---

## 4. Fluxo de Execução

Ao ser iniciado, o agente segue este fluxo:

| Etapa | Descrição |
|-------|-----------|
| 1 | `build_global_information("discovery")` — resolve identidade (`agent_id`, `host_id`, `hostname`, `primary_ip`), detecta ambiente e persiste IDs em disco |
| 2 | `get_tools_info()` — executado primeiro dentro do discovery; verifica e instala dependências se necessário |
| 3 | `run_discovery()` — executa todos os módulos de discovery via `_safe_collect()` e monta o payload |
| 4 | `send_discovery(discovery)` — envia o payload ao backend via HTTP POST para `POST /api/discovery` |
| 5 | Loop infinito: a cada 5 segundos, coleta métricas (`collect_all()`), logs de autenticação (`collect_auth_logs()`) e conexões TCP (`collect_connections()`), enviando cada um ao endpoint correspondente |

**Flag `--install-deps`:** passada na linha de comando, força a instalação de ferramentas ausentes sem prompt interativo. Detectada em `main()` via `sys.argv` e repassada para `get_tools_info(force_install=True)`.

**Flag `--dry-run`:** imprime os payloads no console via `json.dumps()` em vez de enviá-los ao backend. Útil para desenvolvimento e depuração.

**Resiliência por isolamento:** cada módulo de discovery é chamado via `_safe_collect()`, que captura exceções individualmente. Se um módulo falhar (ex: `dmidecode` sem permissão root), o restante do payload não é afetado — o campo fica com `{"error": "<mensagem>"}` e o agente continua normalmente.

```python
def _safe_collect(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  Erro no discovery de '{name}': {e}")
        return {"error": str(e)}
```

---

## 5. Módulo: global_information

**Arquivo:** `agent/global_information/global_information.py`

Monta o bloco `global` que encabeça todos os payloads (discovery, métricas, logs e conexões). É chamado uma vez por tipo de coleta na inicialização. Centraliza a detecção de ambiente, evitando que cada módulo execute `lscpu` individualmente.

### Funções internas

**`_load_or_create_id(filename)`** — Lê o ID do arquivo em `~/.agent/<filename>`. Se não existir ou for inválido, gera um número de 5 dígitos (10000–99999) e salva. O ID sobrevive a reinicializações; só muda se o arquivo for deletado manualmente.

**`_get_hostname()`** — Retorna o FQDN via `socket.getfqdn()`. Fallback: `socket.gethostname()`.

**`_get_primary_ip()`** — Determina o IP primário conectando um socket UDP ao `8.8.8.8:80`. Nenhum pacote é enviado — a técnica consulta a tabela de roteamento do kernel para descobrir qual IP seria usado para alcançar a internet.

**`_detect_environment()`** — Executa `lscpu` e verifica o campo `Hypervisor Vendor`. Se presente, o host é virtualizado. Este é o único lugar no agente onde `lscpu` é executado para detecção de ambiente.

**`_build_notes(is_virtualized)`** — Gera lista de notas informativas para o backend sobre campos indisponíveis em VM. Em hardware físico, retorna lista vazia.

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
| `collection_type` | `"discovery"`, `"metrics"`, `"logs"` ou `"connections"` |
| `schema_version` | Versão do schema — incrementar em breaking changes |
| `agent_id` | ID único do agente persistido em `~/.agent/agent_id.txt` |
| `host_id` | ID único do host persistido em `~/.agent/host_id.txt` |
| `hostname` | FQDN ou hostname do sistema |
| `primary_ip` | IP da rota de saída (interface preferida) |
| `environment` | `is_virtualized` + `hypervisor` |
| `notes` | Lista de avisos sobre campos indisponíveis (vazia em físico) |

---

## 6. Módulo: discovery

O módulo de discovery é executado uma única vez após a inicialização e coleta o inventário completo de hardware e SO. Todos os sub-módulos seguem o mesmo padrão de detecção de ambiente: recebem `is_virtualized` como parâmetro (resolvido uma única vez em `global_information`) e delegam para o handler `_physical` ou `_virtual` correspondente.

### 6.1 CPU Discovery

**Arquivos:** `discovery/cpu_discovery/cpu.py`, `cpu_physical.py`, `cpu_virtual.py`

**Fontes de dados:**
- `lscpu` — modelo, fabricante, arquitetura, número de CPUs lógicas, threads por core, hipervisor
- `/proc/cpuinfo` — dados complementares por núcleo lógico
- `sysfs` (`/sys/devices/system/cpu/cpu0/cpufreq/`) — frequências base, máxima e mínima em kHz (convertidas para MHz)

**Hardware físico:** coleta `model_name`, `vendor`, `architecture`, `threads_per_core`, `cores_logical`, frequências (base, max, min). A frequência base é buscada primeiro no sysfs (mais preciso) e depois em `lscpu` como fallback.

**Ambiente virtualizado:** a topologia reflete a alocação de vCPUs do hipervisor, não os núcleos físicos reais. `threads_per_core` retorna `null` quando o valor é genérico (`"1"`), pois não é confiável em VMs. Cada valor de frequência inclui um campo `source` indicando de onde foi obtido (ex: `sysfs.base_frequency`, `proc_cpuinfo.cpu_mhz`).

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
- `dmidecode -t memory` (somente físico, requer root) — slots físicos de RAM, fabricante, tipo DDR, velocidade, serial

**Hardware físico:** retorna totais em bytes e uma lista detalhada de slots físicos. Cada slot inclui: localizador, banco, se está populado, tamanho, tipo DDR, velocidade em MHz, fabricante, part number, serial e fator de forma.

**Ambiente virtualizado:** `slots` retorna `null`. Além dos totais, inclui `buffers`, `cached` e informações de swap.

| Campo | Descrição |
|-------|-----------|
| `total_bytes` | RAM total em bytes |
| `swap_total_bytes` | Swap total em bytes |
| `slots` | `null` em VM; lista de módulos em físico |

### 6.3 Disk Discovery

**Arquivos:** `discovery/disk_discovery/disk.py`, `disk_physical.py`, `disk_virtual.py`

**Fontes de dados:**
- `lsblk -J -b -o NAME,SIZE,TYPE,ROTA,MOUNTPOINT,FSTYPE,LABEL,UUID,MODEL,VENDOR,SERIAL,TRAN,RM` — dispositivos de bloco em JSON nativo
- `smartctl -i -j` (somente físico, requer root) — modelo, serial, firmware, status S.M.A.R.T., horas de uso, temperatura

**Hardware físico:** cruza `lsblk` com `smartctl` para cada dispositivo. Loop devices (`type=loop`) são ignorados. Partições são coletadas recursivamente até `depth 4` para cobrir LVM sobre LUKS sobre partição. O tipo do disco (HDD/SSD) é determinado pelo `rotation_rate` do smartctl ou pelo flag `rota` do lsblk.

**Ambiente virtualizado:** usa apenas `lsblk`. Campos S.M.A.R.T. (`smart_passed`, `power_on_hours`, `temperature_celsius`) retornam `null`.

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
| `form_factor` | `2.5"` \| `M.2`... (`null` em VM) |
| `size_bytes` | Tamanho do disco em bytes |
| `health` | `smart_passed`, `power_on_hours`, `temperature_celsius` (`null` em VM) |
| `partitions` | Lista recursiva de partições com `role` inferido |

### 6.4 Network Discovery

**Arquivos:** `discovery/network_discovery/network.py`, `network_physical.py`, `network_virtual.py`

**Fontes de dados:**
- `ip -j addr show` — endereços IPv4/IPv6, prefixos, escopo
- `ip -j link show` — flags, MAC, MTU
- `ip -j route show default` — gateway padrão
- `sysfs` (`/sys/class/net/<iface>/`) — speed, duplex, driver, bus_info (somente físico)

**Hardware físico:** após construir as interfaces com `ip addr/link`, enriquece com `speed_mbps`, `duplex`, `driver` e `bus_info` via leitura direta do sysfs.

**Ambiente virtualizado:** usa apenas `ip addr` e `ip link`. Campos de hardware ficam ausentes do dict (não retornam `null` — são omitidos via `_normalize_network` no `__main__.py`).

| Campo | Descrição |
|-------|-----------|
| `total_interfaces` | Número de interfaces |
| `default_gateway` | `gateway` e `interface` da rota padrão |
| `interfaces[].name` | Nome da interface |
| `interfaces[].mac` | Endereço MAC |
| `interfaces[].mtu` | MTU |
| `interfaces[].state` | Estado operacional |
| `interfaces[].flags` | Flags da interface |
| `interfaces[].ipv4` / `ipv6` | Endereços com prefixo, escopo e broadcast |
| `interfaces[].speed_mbps` | Velocidade em Mbps (somente físico) |
| `interfaces[].duplex` | `full` \| `half` (somente físico) |
| `interfaces[].driver` | Driver do kernel (somente físico) |
| `interfaces[].bus_info` | Localização PCIe (somente físico) |

### 6.5 Motherboard Discovery

**Arquivos:** `discovery/motherboard_discovery/motherboard.py`, `motherboard_physical.py`

**Fontes de dados:**
- `dmidecode -t 0` — BIOS (fabricante, versão, data)
- `dmidecode -t 2` — baseboard (fabricante, modelo, serial, asset tag)
- `dmidecode -t 4` — sockets de CPU (quantidade e ocupação)
- `dmidecode -t 9` — slots de expansão PCIe
- `dmidecode -t 17` — contagem resumida de slots de RAM
- `lspci` — identificação do chipset via ISA/LPC bridge

**Hardware físico:** monta perfil completo da placa-mãe incluindo chipset, BIOS, sockets de CPU com status de ocupação, resumo de slots de RAM e lista de slots PCIe.

**Ambiente virtualizado:** o campo `motherboard` retorna `null` diretamente — o hipervisor não expõe informações úteis de placa-mãe.

| Campo | Descrição |
|-------|-----------|
| `manufacturer` / `product_name` | Fabricante e modelo da placa-mãe |
| `serial_number` / `asset_tag` | Identificação física |
| `chipset` | Chipset via lspci (`null` em VM) |
| `bios` | `vendor`, `version`, `release_date`, `revision` |
| `cpu_sockets` | Total de sockets e quantos populados (`null` em VM) |
| `ram_slots` | Total, usados e livres (`null` em VM) |
| `expansion_slots` | Lista de slots PCIe (ausente em VM) |

### 6.6 System Discovery

**Arquivos:** `discovery/system_discovery/system.py`, `system_physical.py`, `system_virtual.py`

**Fontes de dados:**
- `/etc/os-release` — distribuição, versão, codinome
- `uname -a` — versão e release do kernel, arquitetura
- `hostname -f` — hostname completo
- `/proc/uptime` — tempo de atividade em segundos
- `timedatectl show --property=Timezone --value` — fuso horário

As informações de OS são idênticas para físico e virtualizado. O que difere é apenas o campo `is_virtualized` e `hypervisor` no bloco `global`.

| Campo | Descrição |
|-------|-----------|
| `hostname` | Nome completo do host |
| `os.name` / `pretty_name` | Nome e versão amigável do SO |
| `os.id` / `id_like` | Identificador interno e família |
| `os.version` / `version_id` | Versão e número da versão |
| `os.codename` | Codinome da distribuição (ex: `noble`) |
| `kernel.release` / `version` / `machine` | Dados do kernel |
| `timezone` | Fuso horário configurado |
| `uptime_seconds` | Tempo de atividade em segundos |

### 6.7 Tools Discovery

**Arquivos:** `discovery/tools_discovery/tools.py`, `tools_checker.py`, `tools_physical.py`, `tools_virtual.py`

**O que faz:** verifica quais ferramentas externas estão disponíveis no host e, opcionalmente, instala as ausentes. É executado primeiro dentro do `run_discovery()`, antes dos demais módulos, para garantir que as dependências estejam presentes.

**Ferramentas verificadas em físico:** `lscpu`, `lsblk`, `ip`, `dmidecode`, `smartctl`, `ethtool`, `lspci`, `journalctl`, `timedatectl`

**Ferramentas verificadas em VM:** `lscpu`, `lsblk`, `ip`, `journalctl`, `timedatectl` (ferramentas que requerem hardware físico são ignoradas)

**Lógica de instalação (`tools_checker.py`):**
1. Verifica quais ferramentas estão instaladas via `shutil.which`
2. Se houver ausentes: detecta o gerenciador de pacotes (`apt`, `dnf`, `pacman`, `zypper`)
3. Se for terminal interativo: pergunta ao usuário se deseja instalar
4. Se não for terminal interativo (serviço, pipe, cron): registra e segue sem instalar
5. Flag `--install-deps` força a instalação sem prompt em qualquer contexto
6. Re-verifica e atualiza o status após instalação

**Campos que requerem root:** `dmidecode`, `smartctl`. O campo `has_root` indica se o agente está rodando como root (`os.geteuid() == 0`).

**Pacotes por gerenciador:**

| Ferramenta | apt | dnf | pacman | zypper |
|------------|-----|-----|--------|--------|
| dmidecode | dmidecode | dmidecode | dmidecode | dmidecode |
| smartctl | smartmontools | smartmontools | smartmontools | smartmontools |
| ethtool | ethtool | ethtool | ethtool | ethtool |
| lspci | pciutils | pciutils | pciutils | pciutils |
| lsblk / lscpu | util-linux | util-linux | util-linux | util-linux |
| ip | iproute2 | iproute | iproute2 | iproute2 |
| journalctl / timedatectl | systemd | systemd | systemd | systemd |

**Payload gerado por ferramenta:**

```json
"lsblk": {
  "installed":   true,
  "path":        "/usr/bin/lsblk",
  "version":     "lsblk from util-linux 2.39.3",
  "has_root":    false,
  "needs_root":  false
}
```

---

## 7. Módulo: coleta

O módulo de coleta executa em loop infinito a cada 5 segundos. Todos os sub-módulos usam `psutil` para acessar informações do sistema de forma portável.

**Arquivo principal:** `coleta/collector.py`

```python
def collect_all():
    return {
        "cpu":     get_cpu_usage(),
        "memory":  get_memory_usage(),
        "disk":    get_disk_usage(),
        "network": get_network_usage(),
    }

def collect_auth_logs() -> list[dict]:
    return get_new_auth_log_lines()

def collect_connections() -> dict:
    return get_active_connections()
```

### 7.1 CPU Coleta

**Arquivo:** `coleta/cpu_coleta/cpu.py`

Usa `psutil.cpu_percent(interval=1)`, que mede o uso durante 1 segundo. O intervalo garante medição precisa em vez de snapshot instantâneo.

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

Usa `psutil.disk_usage('/')` para o ponto de montagem raiz.

| Campo | Descrição |
|-------|-----------|
| `total` | Espaço total em bytes |
| `used` | Espaço utilizado em bytes |
| `percent` | Percentual de uso (0–100) |

### 7.4 Network Coleta (I/O)

**Arquivo:** `coleta/network_coleta/network.py`

Usa `psutil.net_io_counters()`. Retorna contadores acumulados desde a inicialização do sistema — não são deltas. O backend é responsável por calcular a taxa entre amostras.

| Campo | Descrição |
|-------|-----------|
| `bytes_sent` | Total de bytes enviados (acumulado) |
| `bytes_recv` | Total de bytes recebidos (acumulado) |

### 7.5 Logs Coleta

**Arquivo:** `coleta/logs_coleta/logs.py`

Lê o arquivo `/var/log/auth.log` de forma incremental, registrando eventos de autenticação: tentativas de login, falhas (possível brute force), escalonamento via `sudo`.

**Comportamento:**
- Rastreia posição (byte offset + inode) em `~/.agent/auth_log_state.json`
- **Primeira execução:** envia as últimas 100 linhas (histórico inicial) e salva a posição no final do arquivo
- **Execuções seguintes:** envia apenas as linhas novas desde o último envio
- **Detecção de rotação:** detecta mudança de inode e reinicia a leitura do início do novo arquivo
- **Nunca reenvia** a mesma linha ao servidor

**Permissão necessária:** `/var/log/auth.log` pertence ao grupo `adm`. Adicionar o usuário ao grupo ou rodar como root:

```bash
sudo usermod -a -G adm <seu_usuario>
```

**Retorno por entrada:**

```json
{
  "timestamp": "2026-05-18T14:35:00+00:00",
  "raw_line":  "May 18 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100"
}
```

### 7.6 Connections Coleta *(Semana 6)*

**Arquivo:** `coleta/connections_coleta/connections.py`

Coleta conexões TCP ativas e detecta possível port scan. Usa `psutil.net_connections(kind="tcp")`.

**Estados rastreados:** `ESTABLISHED`, `SYN_SENT`, `TIME_WAIT`, `CLOSE_WAIT`

**Detecção de port scan:** quando 10 ou mais conexões `SYN_SENT` apontam para portas remotas distintas, `port_scan_detected` é `true`. O limiar é configurável pela constante `_PORTSCAN_THRESHOLD = 10`.

```python
_PORTSCAN_THRESHOLD = 10
_TRACKED_STATES = {"ESTABLISHED", "SYN_SENT", "TIME_WAIT", "CLOSE_WAIT"}
```

**Retorno:**

```json
{
  "connections": [
    {
      "local_port":  22,
      "remote_ip":   "192.168.1.100",
      "remote_port": 54321,
      "state":       "ESTABLISHED"
    }
  ],
  "total":              1,
  "port_scan_detected": false,
  "syn_sent_count":     0
}
```

| Campo | Descrição |
|-------|-----------|
| `connections` | Lista de conexões TCP nos estados rastreados |
| `connections[].local_port` | Porta local |
| `connections[].remote_ip` | IP remoto |
| `connections[].remote_port` | Porta remota |
| `connections[].state` | Estado da conexão |
| `total` | Total de conexões rastreadas |
| `port_scan_detected` | `true` se `syn_sent_count >= 10` |
| `syn_sent_count` | Número de portas remotas distintas em SYN_SENT |

---

## 8. Estrutura dos Payloads

### 8.1 Payload de Discovery

Enviado uma vez na inicialização. Endpoint: `POST /api/discovery`

```json
{
  "global": {
    "collection_type": "discovery",
    "schema_version":  "1.0",
    "agent_id":        "38472",
    "host_id":         "71203",
    "hostname":        "servidor-01.exemplo.com",
    "primary_ip":      "192.168.1.42",
    "environment": {
      "is_virtualized": false,
      "hypervisor":     null
    },
    "notes": []
  },
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
  "type":   "metrics",
  "global": {
    "collection_type": "metrics",
    "schema_version":  "1.0",
    "agent_id":        "38472",
    "host_id":         "71203",
    "hostname":        "servidor-01.exemplo.com",
    "primary_ip":      "192.168.1.42",
    "environment":     { "..." },
    "notes":           []
  },
  "timestamp": "2026-05-20T14:35:00.123456+00:00",
  "data": {
    "timestamp": "2026-05-20T14:35:00.123456+00:00",
    "cpu":       { "percent": 23.5 },
    "memory":    { "total": 8589934592, "used": 4294967296, "percent": 50.0 },
    "disk":      { "total": 107374182400, "used": 53687091200, "percent": 50.0 },
    "network":   { "bytes_sent": 1048576, "bytes_recv": 5242880 }
  }
}
```

### 8.3 Payload de Log

Enviado uma linha por request, para cada nova linha de auth.log. Endpoint: `POST /api/logs`

```json
{
  "global": {
    "collection_type": "logs",
    "schema_version":  "1.0",
    "agent_id":        "38472",
    "host_id":         "71203",
    "hostname":        "servidor-01.exemplo.com",
    "primary_ip":      "192.168.1.42",
    "environment":     { "..." },
    "notes":           []
  },
  "log_type":  "auth",
  "timestamp": "2026-05-18T14:35:00+00:00",
  "raw_line":  "May 18 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100"
}
```

### 8.4 Payload de Conexões *(Semana 6)*

Enviado a cada 5 segundos. Endpoint: `POST /api/connections`

```json
{
  "global": {
    "collection_type": "connections",
    "schema_version":  "1.0",
    "agent_id":        "38472",
    "host_id":         "71203",
    "hostname":        "servidor-01.exemplo.com",
    "primary_ip":      "192.168.1.42",
    "environment":     { "..." },
    "notes":           []
  },
  "timestamp": "2026-05-20T14:35:00.123456+00:00",
  "connections": [
    {
      "local_port":  22,
      "remote_ip":   "192.168.1.100",
      "remote_port": 54321,
      "state":       "ESTABLISHED"
    }
  ],
  "total":              1,
  "port_scan_detected": false,
  "syn_sent_count":     0
}
```

---

## 9. Módulo: utils

### `agent/utils/parsers.py`

Todos os parsers e helpers estão centralizados em um único arquivo. Nenhuma chamada shell acontece aqui — apenas transformação de dados.

| Seção | Funções | Usada por |
|-------|---------|-----------|
| Parsers de CPU | `parse_lscpu()`, `parse_cpuinfo()` | `cpu_*`, `global_information` |
| Parsers de Memória | `parse_meminfo()`, `parse_meminfo_kb()`, `parse_dmidecode_memory()`, `parse_dmi_size_to_mb()` | `mem_*` |
| Parsers de Disco | `parse_lsblk()`, `parse_smartctl()`, `resolve_disk_type()`, `resolve_disk_interface()`, `resolve_partition_role()` | `disk_*` |
| Parsers de Rede | `parse_ip_addr()`, `parse_ip_link()`, `parse_default_gateway()`, `build_network_interface()` | `network_*` |
| Parsers de SO | `parse_os_release()`, `parse_uname()`, `parse_uptime_seconds()`, `clean_hostname()`, `clean_timezone()` | `system_*` |
| Parsers de Placa-mãe | `parse_baseboard()`, `parse_bios()`, `parse_cpu_sockets()`, `parse_memory_slots_summary()`, `parse_system_slots()` | `motherboard_*` |
| Conversão de unidades | `kb_to_bytes()`, `kb_to_gb()`, `kb_to_mb()`, `bytes_to_gb()`, `bytes_to_tb()`, `safe_float()`, `safe_int()` | Geral |
| Sanitização | `_clean()`, `sanitize_string()`, `read_sysfs_khz_to_mhz()` | Geral |

### `agent/utils/shell.py`

| Função | Descrição |
|--------|-----------|
| `run(cmd)` | Executa comando com `LC_ALL=C`. Retorna `stdout` ou `None` em qualquer falha. Timeout: 10s. |
| `run_permissive(cmd)` | Retorna `stdout` mesmo com exit code não-zero. Usado para `smartctl`, que retorna códigos não-zero com dados válidos. Timeout: 15s. |

> **`LC_ALL=C` é obrigatório** — garante saída em inglês independente do locale do sistema. Sem isso, `lscpu` em português retorna `"Arquitetura"` em vez de `"Architecture"`, quebrando os parsers silenciosamente.

### `agent/utils/serializer.py`

```python
def to_json(data):
    return json.dumps(data, indent=4)
```

---

## 10. Módulo: sender

**Arquivo:** `agent/utils/sender.py`

Responsável por enviar os payloads ao backend central via HTTP POST com autenticação Bearer Token.

### URLs configuradas

As URLs são resolvidas na inicialização a partir de variáveis de ambiente, com fallback para `MONITOR_API_BASE_URL`:

```python
API_BASE_URL    = os.getenv("MONITOR_API_BASE_URL", "http://api.monitoramento.lan")
DISCOVERY_URL   = os.getenv("MONITOR_DISCOVERY_URL")   or f"{API_BASE_URL}/api/discovery"
METRICS_URL     = os.getenv("MONITOR_METRICS_URL")     or f"{API_BASE_URL}/api/metrics"
LOGS_URL        = os.getenv("MONITOR_LOGS_URL")        or f"{API_BASE_URL}/api/logs"
CONNECTIONS_URL = os.getenv("MONITOR_CONNECTIONS_URL") or f"{API_BASE_URL}/api/connections"
TOKEN           = os.getenv("MONITOR_TOKEN", "")
```

### Cabeçalhos enviados

| Cabeçalho | Valor |
|-----------|-------|
| `Content-Type` | `application/json` |
| `Authorization` | `Bearer {TOKEN}` (somente se `MONITOR_TOKEN` estiver definido) |

### Funções públicas

```python
send_discovery(data)    → POST /api/discovery
send_metrics(data)      → POST /api/metrics
send_log(data)          → POST /api/logs
send_connections(data)  → POST /api/connections   # Semana 6
```

### Tratamento de erros

`ConnectionError`, `Timeout` e `HTTPError` são capturados e impressos sem travar o agente. O loop continua normalmente na próxima iteração.

---

## 11. Organização como Módulo Python

O agente é organizado como um pacote Python instalável, permitindo execução direta via `python -m agent` ou geração de executável com PyInstaller.

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

`where = ["src"]` instrui o setuptools a buscar pacotes dentro de `src/`. A entrada `[project.scripts]` cria o comando `agent` no PATH após instalação, apontando para `main()` em `src/agent/__main__.py`.

### Instalação em modo editável (desenvolvimento)

```bash
cd Agent/
python -m venv .ambiente_venv
source .ambiente_venv/bin/activate
pip install -e .
```

Com `pip install -e .`, o Python aponta diretamente para o código em `src/`. Alterações em `.py` têm efeito imediato sem reinstalação. O comando `agent` fica disponível no PATH do venv.

### Execução direta (sem instalar)

```bash
cd Agent/
python -m agent
```

Requer que `src/` esteja no `PYTHONPATH` ou que o pacote esteja instalado.

### Argumentos de linha de comando

```bash
agent                  # execução normal
agent --install-deps   # força instalação de dependências ausentes
agent --dry-run        # imprime payloads no console sem enviar ao backend
```

---

## 12. Geração do Executável com PyInstaller

O agente é distribuído como um binário Linux único, sem dependência de Python instalado na máquina alvo.

### Entry point do PyInstaller

O arquivo `Agent_Exec/main.py` é minimal — apenas importa e chama `main()`:

```python
# Agent_Exec/main.py
from agent.__main__ import main

if __name__ == "__main__":
    main()
```

Essa separação existe porque o PyInstaller precisa de um arquivo `.py` como entrada, mas o código real fica em `src/agent/__main__.py`, organizado como módulo Python.

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
| `--distpath` | Diretório de saída do binário final (`Agent_Exec/dist/`) |
| `--workpath` | Diretório de artefatos intermediários |

O binário final fica em `Agent_Exec/dist/agent`.

---

## 13. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MONITOR_API_BASE_URL` | `http://api.monitoramento.lan` | URL base do backend |
| `MONITOR_DISCOVERY_URL` | `{BASE}/api/discovery` | Override para endpoint de discovery |
| `MONITOR_METRICS_URL` | `{BASE}/api/metrics` | Override para endpoint de métricas |
| `MONITOR_LOGS_URL` | `{BASE}/api/logs` | Override para endpoint de logs |
| `MONITOR_CONNECTIONS_URL` | `{BASE}/api/connections` | Override para endpoint de conexões |
| `MONITOR_TOKEN` | `""` | Bearer token de autenticação |

**Exemplo de uso:**

```bash
export MONITOR_API_BASE_URL="http://192.168.1.50:5000"
export MONITOR_TOKEN="meu-token-secreto"
./agent
```

---

## 14. Dependências

### Python (runtime)

| Pacote | Uso |
|--------|-----|
| `psutil` | Métricas de CPU, memória, disco, rede I/O e conexões TCP |
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
| `journalctl` | systemd | Logs (futuro) | Não |
| `timedatectl` | systemd | Timezone | Não |

---

## 15. Resumo dos Módulos

| Módulo | Arquivo | Função |
|--------|---------|--------|
| `__main__` | `agent/__main__.py` | Ponto de entrada, orquestra discovery e loop de coleta |
| `global_information` | `global_information/global_information.py` | Bloco de identidade dos payloads |
| `discovery.*` | `discovery/*/` | Inventário de hardware/SO (executado uma vez) |
| `coleta.collector` | `coleta/collector.py` | Orquestrador da coleta contínua |
| `coleta.cpu_coleta` | `coleta/cpu_coleta/cpu.py` | % CPU via psutil |
| `coleta.mem_coleta` | `coleta/mem_coleta/mem.py` | Uso de RAM via psutil |
| `coleta.disk_coleta` | `coleta/disk_coleta/disk.py` | Uso de disco via psutil |
| `coleta.network_coleta` | `coleta/network_coleta/network.py` | Bytes I/O via psutil |
| `coleta.logs_coleta` | `coleta/logs_coleta/logs.py` | Leitura incremental de auth.log |
| `coleta.connections_coleta` | `coleta/connections_coleta/connections.py` | Conexões TCP + detecção de port scan |
| `utils.parsers` | `utils/parsers.py` | Parsers de saída de comandos shell |
| `utils.sender` | `utils/sender.py` | HTTP POST com Bearer token |
| `utils.shell` | `utils/shell.py` | Wrapper de subprocess com `LC_ALL=C` |
| `utils.serializer` | `utils/serializer.py` | Serialização JSON |

---

## 16. Observações Importantes

### Permissões de Leitura de Logs

No Linux, o arquivo `/var/log/auth.log` pertence ao grupo `adm`. Para evitar rodar o agente como `root`, adicione o usuário ao grupo `adm`:

```bash
sudo usermod -a -G adm <seu_usuario>
```

### Permissões para Hardware Discovery

Os módulos `dmidecode` (memória, placa-mãe) e `smartctl` (saúde do disco) requerem root. Sem root, esses campos retornam `{"error": "..."}` no payload de discovery, mas o agente continua normalmente.

### Firewall

Certifique-se de que a porta do servidor backend (ex: `5000`) está acessível a partir da máquina onde o agente roda.

### Sincronização com Backend

Antes de modificar o formato de qualquer payload, validar com a equipe de Backend (Douglas e Fernando) o formato exato esperado. Mudanças de última hora quebram a integração.

### Semana 7 — Pendente

- **7.1** Criar arquivo de serviço systemd `/etc/systemd/system/linux-agent.service`
- **7.2** Testar inicialização automática após reboot
- **7.4** Criar script de instalação `install.sh`
- **7.5** Escrever `README.md` com: como instalar, como configurar a URL, como verificar logs
- **7.6** Teste de estabilidade: deixar o agente rodando por 24h e verificar vazamento de memória ou crashes

**Template do serviço systemd:**

```ini
[Unit]
Description=Monitor Agent
After=network.target

[Service]
ExecStart=/opt/monitor-agent/linux-agent
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable linux-agent && systemctl start linux-agent
```

---

*Documentação gerada em 20/05/2026 — v4.0*
