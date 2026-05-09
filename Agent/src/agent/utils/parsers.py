# =============================================================================
# utils/parsers.py
# Parsers centralizados para todos os módulos de discovery e coleta.
#
# Cada função recebe uma string bruta (saída de um comando) e retorna
# uma estrutura Python limpa. Nenhuma chamada shell acontece aqui —
# apenas transformação de dados.
#
# Seções:
#   1. Parsers de CPU   (lscpu, /proc/cpuinfo)
#   2. Parsers de Memória (/proc/meminfo, dmidecode -t memory)
#   3. Parsers de Disco (lsblk JSON, smartctl JSON)
#   4. Parsers de Rede  (ip -j addr, ip -j link, ip -j route)
#   5. Parsers de Sistema (/etc/os-release, uname, uptime, hostname)
#   6. Parsers de Placa-mãe (dmidecode types 0, 2, 4, 9, 17)
#   7. Helpers de conversão de unidades
#   8. Helpers de sanitização de strings
# =============================================================================

import json
import re


# =============================================================================
# 1. PARSERS DE CPU
# =============================================================================

def parse_lscpu(output: str) -> dict:
    """
    Parseia a saída do comando `lscpu` em um dicionário.

    Chaves são normalizadas: minúsculas, espaços → underscores.
    Exemplo: "Hypervisor Vendor: KVM" → {"hypervisor_vendor": "KVM"}

    Parâmetros:
        output (str): saída bruta de `lscpu`

    Retorno:
        dict com todos os campos do lscpu.
    """
    data = {}
    current_key = None

    for line in output.splitlines():
        if not line.strip():
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            data[key] = value
            current_key = key
        elif current_key:
            # Linha de continuação (valores longos que quebram)
            data[current_key] += " " + line.strip()

    return data


def parse_cpuinfo(text: str) -> list[dict]:
    """
    Parseia /proc/cpuinfo em uma lista de dicts, um por núcleo lógico.

    Cada bloco é separado por linha em branco.
    Exemplo: "model name : Intel Core i7" → {"model name": "Intel Core i7"}

    Parâmetros:
        text (str): conteúdo bruto de /proc/cpuinfo

    Retorno:
        list[dict], um dict por núcleo lógico detectado.
    """
    cpus = []
    current = {}

    for line in text.splitlines():
        line = line.strip()

        if not line:
            # Linha em branco = fim de um bloco de CPU
            if current:
                cpus.append(current)
                current = {}
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()

    # Último bloco (sem linha em branco no final)
    if current:
        cpus.append(current)

    return cpus


# =============================================================================
# 2. PARSERS DE MEMÓRIA
# =============================================================================

def parse_meminfo(output: str) -> dict:
    """
    Parseia /proc/meminfo em um dicionário com chaves normalizadas.

    Exemplo: "MemTotal:       16282624 kB" → {"memtotal": "16282624 kB"}

    Parâmetros:
        output (str): conteúdo bruto de /proc/meminfo

    Retorno:
        dict com todos os campos do meminfo.
    """
    data = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        data[key] = value.strip()
    return data


def parse_meminfo_kb(value_str: str | None) -> int | None:
    """
    Converte string do meminfo (ex: "16282624 kB") para inteiro em kB.

    Retorno:
        int com o valor em kB, ou None em caso de falha.
    """
    try:
        return int(value_str.split()[0])
    except (AttributeError, IndexError, ValueError):
        return None


def parse_dmidecode_memory(output: str) -> list[dict]:
    """
    Parseia a saída de `dmidecode -t memory`.

    Retorna uma lista de dicts, um por bloco Handle (cada slot/módulo).
    Chaves normalizadas: minúsculas, espaços → underscores.

    Parâmetros:
        output (str): saída bruta de `dmidecode -t memory`

    Retorno:
        list[dict], um dict por bloco DMI encontrado.
    """
    blocks = []
    current = {}
    inside_block = False

    for line in output.splitlines():
        # Início de novo bloco DMI
        if line.startswith("Handle "):
            if current:
                blocks.append(current)
            current = {}
            inside_block = True
            continue

        if not inside_block:
            continue

        line_stripped = line.strip()
        if not line_stripped:
            continue

        if ":" in line_stripped:
            key, value = line_stripped.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            current[key] = value.strip()

    # Último bloco
    if current:
        blocks.append(current)

    return blocks


def parse_dmi_size_to_mb(size_str: str | None) -> int | None:
    """
    Converte string de tamanho do dmidecode para MB.

    Exemplos aceitos: "8192 MB", "16 GB", "No Module Installed"
    Retorna None para slots vazios ou strings inválidas.
    """
    if not size_str or size_str in ("No Module Installed", "Unknown", "Not Installed"):
        return None
    try:
        parts = size_str.split()
        value = int(parts[0])
        unit = parts[1].upper() if len(parts) > 1 else "MB"
        return value * 1024 if unit == "GB" else value
    except (IndexError, ValueError):
        return None


# =============================================================================
# 3. PARSERS DE DISCO
# =============================================================================

def parse_lsblk(output: str) -> list[dict]:
    """
    Parseia saída de `lsblk -J -b -o NAME,SIZE,TYPE,...` (JSON nativo).

    Retorna apenas dispositivos do tipo "disk" (exclui partições e loops
    da raiz da lista — partições aparecem como children).

    Parâmetros:
        output (str): saída bruta de lsblk com flag -J

    Retorno:
        list[dict] com os discos encontrados.
    """
    if not output:
        return []
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return []

    return [
        device for device in data.get("blockdevices", [])
        if device.get("type") == "disk"
    ]


def parse_smartctl(output: str) -> dict:
    """
    Parseia saída de `smartctl -i -j /dev/<disk>` (JSON nativo do smartctl).

    Extrai campos relevantes para o discovery: modelo, série, firmware,
    capacidade, tipo de rotação, fator de forma, status SMART e temperatura.

    Parâmetros:
        output (str): saída bruta do smartctl com flag -j

    Retorno:
        dict com campos normalizados, ou {} em caso de falha/ausência.
    """
    if not output:
        return {}
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return {}

    device = data.get("device", {})

    return {
        "model_name":          data.get("model_name"),
        "model_family":        data.get("model_family"),
        "serial_number":       data.get("serial_number"),
        "firmware_version":    data.get("firmware_version"),
        "vendor":              data.get("vendor"),
        "capacity_bytes":      data.get("user_capacity", {}).get("bytes"),
        "rotation_rate":       data.get("rotation_rate"),   # 0=SSD, >0=HDD RPM
        "form_factor": (
            data.get("form_factor", {}).get("name")
            if isinstance(data.get("form_factor"), dict)
            else data.get("form_factor")
        ),
        "interface":           device.get("type"),          # ata, nvme, scsi…
        "smart_status":        data.get("smart_status", {}).get("passed"),
        "power_on_hours":      data.get("power_on_time", {}).get("hours"),
        "temperature_celsius": data.get("temperature", {}).get("current"),
    }


def resolve_disk_type(rotation_rate, rota_flag, is_virtual: bool = False) -> str:
    """
    Determina o tipo do disco baseado nas informações disponíveis.

    Ordem de prioridade:
        1. is_virtual=True  → "Virtual"
        2. rotation_rate=0  → "SSD" (smartctl — mais confiável)
        3. rotation_rate>0  → "HDD" (smartctl)
        4. rota_flag        → HDD se rotacional, SSD se não (lsblk fallback)
        5. sem dados        → "Unknown"

    Atenção: rota_flag pode vir como bool (True/False do JSON do lsblk)
    ou como string ("0"/"1"). Ambos são normalizados aqui.
    rota=True/"1" = rotacional (HDD). rota=False/"0" = não rotacional (SSD).
    """
    if is_virtual:
        return "Virtual"

    if rotation_rate is not None:
        return "SSD" if rotation_rate == 0 else "HDD"

    if rota_flag is not None:
        # Normaliza bool ou string para booleano
        is_rotational = rota_flag is True or str(rota_flag) == "1"
        return "HDD" if is_rotational else "SSD"

    return "Unknown"


# Mapa de interfaces conhecidas e seus nomes normalizados.
# None = interface inválida/ambígua (será ignorada na resolução).
_INTERFACE_MAP = {
    "nvme": "NVMe",
    "sata": "SATA",
    "ata":  "SATA",
    "scsi": "SCSI",
    "sas":  "SAS",
    "usb":  "USB",
    "mmc":  "MMC",
    "ide":  "IDE",
    "spi":  None,   # barramento embarcado — não é interface de disco real
    "":     None,
}


def resolve_disk_interface(tran: str | None, smartctl_interface: str | None, model: str | None = None) -> str:
    """
    Normaliza o tipo de interface do disco.

    Ordem de prioridade:
        1. Campo TRAN do lsblk (mais confiável para hardware físico)
        2. Campo device.type do smartctl
        3. Inferência pelo nome do modelo (último recurso)

    Parâmetros:
        tran               : campo TRAN do lsblk (sata, nvme, usb, spi…)
        smartctl_interface : campo device.type do smartctl (ata, nvme, scsi…)
        model              : string do modelo (usado como desambiguador em VMs)

    Retorno:
        string normalizada (ex: "NVMe", "SATA") ou "Unknown".
    """
    for raw in [tran, smartctl_interface]:
        clean = (raw or "").strip().lower()
        if clean in _INTERFACE_MAP:
            resolved = _INTERFACE_MAP[clean]
            if resolved:
                return resolved
        elif clean:
            return clean.upper()

    # Último recurso: inferência pelo modelo
    if model:
        m = model.lower()
        if "nvme" in m:
            return "NVMe"
        if "sata" in m:
            return "SATA"
        if any(k in m for k in ("virtual", "vmware", "qemu", "vbox")):
            return "SCSI"

    return "Unknown"


def resolve_partition_role(name: str | None, mountpoint: str | None, size_bytes: int | None) -> str | None:
    """
    Infere o papel de uma partição quando mountpoint é None.

    Usado no discovery de disco virtual para dar contexto a partições
    sem ponto de montagem aparente.

    Retorno:
        string descritiva ("bios_boot", "lvm_pv", "unknown") ou None.
    """
    if mountpoint:
        return None   # já tem mountpoint, não precisa inferência

    if not name:
        return None

    # Partição muito pequena (< 10 MB) → BIOS boot ou EFI guard
    if size_bytes and size_bytes < 10 * 1024 * 1024:
        return "bios_boot"

    # Nome contém referência a LVM
    if any(k in (name or "").lower() for k in ("lvm", "vg", "pv")):
        return "lvm_pv"

    return "unknown"


# =============================================================================
# 4. PARSERS DE REDE
# =============================================================================

def parse_ip_addr(raw: str) -> list[dict]:
    """
    Parseia `ip -j addr show`. Retorna lista de interfaces, excluindo loopback.

    Parâmetros:
        raw (str): saída bruta de `ip -j addr show`

    Retorno:
        list[dict] com as interfaces (exceto "lo").
    """
    if not raw:
        return []
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [e for e in entries if e.get("ifname") != "lo"]


def parse_ip_link(raw: str) -> dict[str, dict]:
    """
    Parseia `ip -j link show`. Retorna dict indexado por ifname, sem loopback.

    Parâmetros:
        raw (str): saída bruta de `ip -j link show`

    Retorno:
        dict[str, dict] mapeando nome da interface → dados do link.
    """
    if not raw:
        return {}
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return {e["ifname"]: e for e in entries if e.get("ifname") != "lo"}


def parse_default_gateway(raw: str) -> dict | None:
    """
    Parseia `ip -j route show default`.

    Retorna apenas gateway e interface (os campos mais relevantes).
    Omite metric e protocol — não são úteis para o discovery.

    Parâmetros:
        raw (str): saída bruta de `ip -j route show default`

    Retorno:
        dict com "gateway" e "interface", ou None se não encontrado.
    """
    if not raw:
        return None
    try:
        routes = json.loads(raw)
    except json.JSONDecodeError:
        return None

    for route in routes:
        if route.get("dst") in ("default", "0.0.0.0/0"):
            return {
                "gateway":   route.get("gateway"),
                "interface": route.get("dev"),
            }
    return None


def build_network_interface(addr_entry: dict, link_map: dict, is_virtual: bool = False) -> dict:
    """
    Monta o dict final de uma interface de rede.

    Em hardware físico, tenta enriquecer com speed/duplex/driver via sysfs.
    Em VM, esses campos são omitidos completamente (sem nulls desnecessários).

    Parâmetros:
        addr_entry (dict): entrada de `ip -j addr show` para esta interface
        link_map   (dict): mapa ifname→dados de `ip -j link show`
        is_virtual (bool): True para omitir campos de hardware indisponíveis em VM

    Retorno:
        dict com os dados da interface.
    """
    ifname = addr_entry.get("ifname", "")
    link   = link_map.get(ifname, {})

    # ── Endereços IP ─────────────────────────────────────────────────────────
    ipv4_list, ipv6_list = [], []
    for addr_info in addr_entry.get("addr_info", []):
        family = addr_info.get("family")
        ip     = addr_info.get("local")
        if not ip:
            continue
        entry = {
            "address":   ip,
            "prefix":    addr_info.get("prefixlen"),
            "scope":     addr_info.get("scope"),
            "broadcast": addr_info.get("broadcast"),
        }
        if family == "inet":
            ipv4_list.append(entry)
        elif family == "inet6":
            ipv6_list.append(entry)

    # ── Base da interface ─────────────────────────────────────────────────────
    iface = {
        "name":      ifname,
        "mac":       addr_entry.get("address") or link.get("address"),
        "link_type": addr_entry.get("link_type") or link.get("link_type"),
        "mtu":       addr_entry.get("mtu") or link.get("mtu"),
        "state":     addr_entry.get("operstate") or link.get("operstate"),
        "flags":     addr_entry.get("flags") or link.get("flags") or [],
        "ipv4":      ipv4_list,
        "ipv6":      ipv6_list,
    }

    # ── Hardware (sysfs) — somente em físico ─────────────────────────────────
    # Em VM esses campos não existem e não são incluídos no dict
    if not is_virtual:
        driver     = _sysfs_str(f"/sys/class/net/{ifname}/device/driver/module/name")
        speed_raw  = _sysfs_int(f"/sys/class/net/{ifname}/speed")
        speed_mbps = speed_raw if speed_raw and speed_raw > 0 else None
        duplex     = _sysfs_str(f"/sys/class/net/{ifname}/duplex")

        # Bus info via uevent
        bus_info = None
        uevent = _sysfs_str(f"/sys/class/net/{ifname}/device/uevent")
        if uevent:
            for line in uevent.splitlines():
                if line.startswith("PCI_SLOT_NAME="):
                    bus_info = line.split("=", 1)[1]
                    break

        iface["speed_mbps"] = speed_mbps
        iface["duplex"]     = duplex
        iface["driver"]     = driver
        iface["bus_info"]   = bus_info

    return iface


def _sysfs_str(path: str) -> str | None:
    """Lê um arquivo sysfs e retorna o conteúdo como string. None em caso de erro."""
    try:
        with open(path) as f:
            v = f.read().strip()
            return v if v else None
    except OSError:
        return None


def _sysfs_int(path: str) -> int | None:
    """Lê um arquivo sysfs e retorna o conteúdo como int. None em caso de erro."""
    v = _sysfs_str(path)
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None


# =============================================================================
# 5. PARSERS DE SISTEMA OPERACIONAL
# =============================================================================

def parse_os_release(output: str) -> dict:
    """
    Parseia /etc/os-release em um dicionário.

    Remove aspas dos valores (o arquivo usa KEY="value" ou KEY=value).
    Chaves normalizadas para minúsculas.

    Parâmetros:
        output (str): conteúdo bruto de /etc/os-release

    Retorno:
        dict com os campos do arquivo.
    """
    data = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        # Remove aspas envolventes (simples ou duplas)
        value = value.strip().strip('"').strip("'")
        data[key.strip().lower()] = value
    return data


def parse_uname(output: str) -> dict:
    """
    Parseia a saída de `uname -a` nos campos relevantes.

    Formato típico:
        Linux hostname 6.8.0-110-generic #110-Ubuntu SMP x86_64 x86_64 GNU/Linux

    Parâmetros:
        output (str): saída bruta de `uname -a`

    Retorno:
        dict com kernel_release, kernel_version e machine.
    """
    parts = output.strip().split(None, 4)
    # parts: [sysname, nodename, kernel_release, kernel_version..., machine]
    if len(parts) < 3:
        return {}

    # Última palavra é a arquitetura (ex: x86_64)
    last_parts = output.strip().rsplit(None, 2)
    machine = last_parts[-2] if len(last_parts) >= 2 else None

    # Tudo entre kernel_release e machine é a kernel_version
    kernel_version = parts[3] if len(parts) > 3 else None

    return {
        "kernel_release": parts[2],
        "kernel_version": kernel_version,
        "machine":        machine,
    }


def parse_uptime_seconds(output: str) -> float | None:
    """
    Parseia /proc/uptime e retorna os segundos de uptime como float.

    Formato: "980.45 1234.56" (uptime total e tempo idle)

    Parâmetros:
        output (str): conteúdo bruto de /proc/uptime

    Retorno:
        float com segundos de uptime, ou None em caso de falha.
    """
    try:
        return float(output.strip().split()[0])
    except (AttributeError, IndexError, ValueError):
        return None


def clean_hostname(raw: str) -> str | None:
    """Limpa e retorna o hostname, ou None se vazio."""
    value = (raw or "").strip()
    return value if value else None


def clean_timezone(raw: str) -> str | None:
    """Limpa e retorna o timezone, ou None se vazio."""
    value = (raw or "").strip()
    return value if value else None


# =============================================================================
# 6. PARSERS DE PLACA-MÃE (dmidecode)
# =============================================================================

def parse_baseboard(output: str) -> dict:
    """
    Parseia a saída de `dmidecode -t 2` (Baseboard/Placa-mãe).

    Retorna dict com campos do baseboard: manufacturer, product_name,
    version, serial_number, asset_tag.

    Parâmetros:
        output (str): saída bruta de `dmidecode -t 2`
    """
    return _parse_dmi_section(output)


def parse_bios(output: str) -> dict:
    """
    Parseia a saída de `dmidecode -t 0` (BIOS).

    Retorna dict com campos da BIOS: vendor, version, release_date,
    bios_revision.

    Parâmetros:
        output (str): saída bruta de `dmidecode -t 0`
    """
    return _parse_dmi_section(output)


def parse_cpu_sockets(output: str) -> list[dict]:
    """
    Parseia `dmidecode -t 4` (Processor) para extrair sockets de CPU.

    Retorna lista com um dict por socket, indicando se está populado.

    Parâmetros:
        output (str): saída bruta de `dmidecode -t 4`
    """
    blocks = _parse_dmi_blocks(output)
    sockets = []

    for block in blocks:
        socket_designation = _clean(block.get("socket_designation"))
        status = block.get("status", "").lower()
        # Status "populated" indica que há uma CPU instalada no socket
        populated = "populated" in status

        if socket_designation:
            sockets.append({
                "designation": socket_designation,
                "populated":   populated,
                "type":        _clean(block.get("type")),
                "speed_mhz":   _parse_dmi_speed(block.get("current_speed")),
            })

    return sockets


def parse_memory_slots_summary(output: str) -> dict:
    """
    Parseia `dmidecode -t 17` para obter um resumo dos slots de RAM.

    Retorna apenas contagens (total, usados, livres) — os detalhes
    completos de cada módulo ficam em mem_physical.py.

    Parâmetros:
        output (str): saída bruta de `dmidecode -t 17`
    """
    blocks = _parse_dmi_blocks(output)

    # Filtra apenas blocos que são Memory Device (slots reais)
    slot_blocks = [
        b for b in blocks
        if b.get("type") == "memory device" or "size" in b
    ]

    total = len(slot_blocks)
    used  = sum(
        1 for b in slot_blocks
        if parse_dmi_size_to_mb(b.get("size")) is not None
    )

    return {
        "total": total,
        "used":  used,
        "free":  total - used,
    }


def parse_system_slots(output: str) -> list[dict]:
    """
    Parseia `dmidecode -t 9` (System Slots / PCIe slots).

    Retorna lista de slots de expansão com tipo e status de uso.

    Parâmetros:
        output (str): saída bruta de `dmidecode -t 9`
    """
    blocks = _parse_dmi_blocks(output)
    slots = []

    for block in blocks:
        slot_id = _clean(block.get("id"))
        slot_type = _clean(block.get("type"))
        if not slot_type:
            continue
        slots.append({
            "id":           slot_id,
            "type":         slot_type,
            "current_usage": _clean(block.get("current_usage")),
            "bus_address":   _clean(block.get("bus_address")),
        })

    return slots


def _parse_dmi_section(output: str) -> dict:
    """Parseia a primeira seção relevante de uma saída dmidecode."""
    blocks = _parse_dmi_blocks(output)
    return blocks[0] if blocks else {}


def _parse_dmi_blocks(output: str) -> list[dict]:
    """
    Parseia blocos Handle de uma saída dmidecode genérica.

    Cada bloco começa com "Handle " e contém pares chave: valor.
    """
    blocks = []
    current = {}
    inside = False

    for line in output.splitlines():
        if line.startswith("Handle "):
            if current:
                blocks.append(current)
            current = {}
            inside = True
            continue

        if not inside:
            continue

        stripped = line.strip()
        if not stripped:
            continue

        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            current[key] = value.strip()

    if current:
        blocks.append(current)

    return blocks


def _parse_dmi_speed(value_str: str | None) -> int | None:
    """Extrai inteiro de MHz de strings como '3200 MT/s', '2400 MHz'."""
    if not value_str or value_str.lower() in ("unknown", ""):
        return None
    try:
        return int(value_str.split()[0])
    except (ValueError, IndexError):
        return None


# =============================================================================
# 7. HELPERS DE CONVERSÃO DE UNIDADES
# =============================================================================

def kb_to_bytes(kb: int | None) -> int | None:
    """Converte kB para bytes."""
    return kb * 1024 if kb is not None else None


def kb_to_gb(kb: int | None) -> float | None:
    """Converte kB para GB com 2 casas decimais."""
    if kb is None:
        return None
    return round(kb / (1024 ** 2), 2)


def kb_to_mb(kb: int | None) -> float | None:
    """Converte kB para MB com 2 casas decimais."""
    if kb is None:
        return None
    return round(kb / 1024, 2)


def bytes_to_gb(value: int | None) -> float | None:
    """Converte bytes para GB com 2 casas decimais."""
    if value is None:
        return None
    try:
        return round(int(value) / (1024 ** 3), 2)
    except (ValueError, TypeError):
        return None


def bytes_to_tb(value: int | None) -> float | None:
    """Converte bytes para TB com 2 casas decimais."""
    if value is None:
        return None
    try:
        return round(int(value) / (1024 ** 4), 2)
    except (ValueError, TypeError):
        return None


def safe_float(value) -> float | None:
    """Converte value para float. Retorna None em caso de falha."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value) -> int | None:
    """Converte value para int. Retorna None em caso de falha."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# =============================================================================
# 8. HELPERS DE SANITIZAÇÃO DE STRINGS
# =============================================================================

def _clean(value: str | None) -> str | None:
    """
    Remove espaços, aspas e valores genéricos sem informação.

    Valores considerados vazios: "Not Specified", "Unknown", "N/A", "".
    Retorna None nesses casos.
    """
    if not value:
        return None
    cleaned = value.strip().strip('"').strip("'")
    if cleaned.lower() in ("not specified", "unknown", "n/a", "to be filled by o.e.m.", ""):
        return None
    return cleaned


def sanitize_string(value: str | None) -> str | None:
    """
    Limpa strings vindas de lsblk/dmidecode.

    Remove espaços extras, vírgulas e caracteres de controle nas bordas.
    Retorna None se a string ficar vazia após limpeza.
    """
    if not value:
        return None
    cleaned = re.sub(r"[\s,;]+$", "", value.strip())
    cleaned = re.sub(r"^[\s,;]+", "", cleaned)
    return cleaned if cleaned else None


def read_sysfs_khz_to_mhz(path: str) -> float | None:
    """
    Lê um arquivo sysfs com valor em kHz e converte para MHz.

    Usado para leitura de frequências de CPU em hardware físico.
    Retorna None se o arquivo não existir ou ocorrer qualquer erro.
    """
    try:
        with open(path, "r") as f:
            khz = float(f.read().strip())
            return khz / 1000.0
    except (FileNotFoundError, ValueError, PermissionError, OSError):
        return None

# =============================================================================
# FIM utils/parsers.py
# =============================================================================