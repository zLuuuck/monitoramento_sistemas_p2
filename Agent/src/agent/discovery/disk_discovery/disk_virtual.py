# =============================================================================
# discovery/disk_discovery/disk_virtual.py
#
# Discovery de discos para ambientes virtualizados.
#
# Usa apenas lsblk — smartctl não é confiável em VMs.
# Campos de hardware real (firmware, SMART, form_factor) são omitidos.
#
# Tratamento especial para WSL2:
#   O WSL2 expõe múltiplos discos SCSI (volumes do Hyper-V).
#   O disco relevante é identificado pela partição montada em "/".
#   Se detectado WSL2 via kernel_release, aplica filtragem por df.
# =============================================================================

import json
from agent.utils.shell import run
from agent.utils.parsers import (
    parse_lsblk,
    sanitize_string,
    resolve_disk_type,
    resolve_disk_interface,
    resolve_partition_role,
    safe_int,
)

# Tipos de partição que devem aparecer no payload
_PARTITION_TYPES = {"part", "lvm", "md", "raid", "crypt"}


def get_virtual_disk_info(lsblk_raw: str | None, kernel_release: str = "") -> dict:
    """
    Monta o payload de discos para ambiente virtualizado.

    Em WSL2 (kernel contém "microsoft"), aplica filtragem para retornar
    apenas o disco com a partição montada em "/".

    Parâmetros:
        lsblk_raw      (str): saída bruta de lsblk -J -b -o ...
        kernel_release (str): release do kernel (ex: "6.6.87.2-microsoft-standard-WSL2")

    Retorno:
        dict com total_disks e lista de discos relevantes.
    """
    disks_raw = parse_lsblk(lsblk_raw)
    is_wsl2   = "microsoft" in (kernel_release or "").lower()

    # Em WSL2, identifica qual device contém o disco raiz
    root_device = _find_root_device(is_wsl2) if is_wsl2 else None

    disks = []
    for dev in disks_raw:
        # Loop devices não são discos reais
        if dev.get("type") == "loop":
            continue

        name = dev.get("name", "")
        if not name:
            continue

        # WSL2: ignora discos que não são o disco raiz
        if is_wsl2 and root_device and name != root_device:
            continue

        size_bytes = safe_int(dev.get("size"))
        model      = sanitize_string(dev.get("model"))
        vendor     = sanitize_string(dev.get("vendor"))
        serial     = sanitize_string(dev.get("serial"))

        disk_type = resolve_disk_type(
            rotation_rate=None,
            rota_flag=dev.get("rota"),
            is_virtual=True,
        )
        interface = resolve_disk_interface(
            tran=dev.get("tran"),
            smartctl_interface=None,
            model=model,
        )
        partitions = _parse_partitions(dev.get("children") or [])

        disk = {
            "device":     f"/dev/{name}",
            "model":      model,
            "vendor":     vendor,
            "serial":     serial,
            "type":       disk_type,       # "Virtual"
            "interface":  interface,       # "SCSI", "NVMe"…
            "size_bytes": size_bytes,      # conversão para GB/TB fica no frontend
            "partitions": partitions,
        }

        # Inclui serial apenas se disponível (evita campo vazio no payload)
        if not serial:
            disk.pop("serial")

        disks.append(disk)

    return {
        "total_disks": len(disks),
        "disks":       disks,
    }


# =============================================================================
# Detecção do disco raiz no WSL2
# =============================================================================

def _find_root_device(is_wsl2: bool) -> str | None:
    """
    Identifica o nome do device que contém o filesystem raiz ("/").

    Em WSL2, usa `df /` para encontrar o device correto, já que lsblk
    expõe múltiplos discos sem partições montadas visíveis.

    Retorno:
        str com o nome do device (ex: "sdd"), ou None em caso de falha.
    """
    if not is_wsl2:
        return None

    df_raw = run("df --output=source / 2>/dev/null | tail -1")
    if not df_raw:
        return None

    # df retorna algo como "/dev/sdd" ou "drvfs"
    device_path = df_raw.strip()
    if device_path.startswith("/dev/"):
        # Extrai o nome do disco raiz (sem número de partição)
        # Ex: "/dev/sdd1" → "sdd"
        dev_name = device_path.replace("/dev/", "")
        # Remove sufixo numérico de partição, se existir
        import re
        match = re.match(r"([a-z]+)", dev_name)
        return match.group(1) if match else None

    return None


# =============================================================================
# Parse de partições (recursivo)
# =============================================================================

def _parse_partitions(children: list, _depth: int = 0) -> list:
    """
    Coleta partições recursivamente para cobrir LVM, LUKS e RAID aninhados.

    Suporta volumes aninhados como: crypt > lvm > part.
    Depth máximo: 4 (evita loops em configurações anômalas).

    Parâmetros:
        children (list): lista de filhos do device no lsblk
        _depth   (int):  profundidade atual da recursão (uso interno)

    Retorno:
        list[dict] com as partições encontradas.
    """
    if _depth > 4:
        return []

    partitions = []
    for child in children:
        if child.get("type") not in _PARTITION_TYPES:
            continue

        size_bytes = safe_int(child.get("size"))
        mountpoint = child.get("mountpoint") or None
        name       = child.get("name")
        role       = resolve_partition_role(name, mountpoint, size_bytes)

        entry = {
            "name":       name,
            "type":       child.get("type"),
            "mountpoint": mountpoint,
            "fstype":     child.get("fstype") or None,
            "label":      child.get("label")  or None,
            "uuid":       child.get("uuid")   or None,
            "size_bytes": size_bytes,
            "children":   _parse_partitions(child.get("children") or [], _depth + 1),
        }

        # Adiciona role apenas quando inferido (não inclui None)
        if role:
            entry["role"] = role

        partitions.append(entry)

    return partitions

# =============================================================================
# FIM discovery/disk_discovery/disk_virtual.py
# =============================================================================