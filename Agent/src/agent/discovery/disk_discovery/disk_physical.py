# =============================================================================
# discovery/disk_discovery/disk_physical.py
#
# Discovery de discos para hardware físico (bare-metal).
#
# Cruza dados do lsblk com smartctl por dispositivo para obter:
# - Dados de identificação (modelo, fabricante, série, firmware)
# - Saúde do disco (SMART passed, horas ligado, temperatura)
# - Tipo exato (HDD/SSD via rotation_rate)
# - Partições recursivas (suporta LVM, LUKS, RAID até depth 4)
# =============================================================================

from agent.utils.shell import run
from agent.utils.parsers import (
    parse_lsblk,
    parse_smartctl,
    resolve_disk_type,
    resolve_disk_interface,
    safe_int,
)

_PARTITION_TYPES = {"part", "lvm", "md", "raid", "crypt"}


def get_physical_disk_info(lsblk_raw: str | None) -> dict:
    """
    Monta o payload de discos para hardware físico.

    Parâmetros:
        lsblk_raw (str): saída bruta de `lsblk -J -b -o ...`

    Retorno:
        dict com total_disks e lista de discos com detalhes físicos.
    """
    disks_raw = parse_lsblk(lsblk_raw)
    disks = []

    for dev in disks_raw:
        if dev.get("type") == "loop":
            continue
        name = dev.get("name", "")
        if not name:
            continue

        device_path = f"/dev/{name}"

        # ── smartctl — requer root, falha silenciosa ───────────────────────
        smartctl_raw = run(f"smartctl -i -j {device_path}")
        smart        = parse_smartctl(smartctl_raw)

        # Tamanho: prioriza smartctl (bytes exatos), fallback lsblk
        size_bytes = smart.get("capacity_bytes") or safe_int(dev.get("size"))

        disk_type = resolve_disk_type(
            rotation_rate=smart.get("rotation_rate"),
            rota_flag=dev.get("rota"),
        )
        interface = resolve_disk_interface(
            tran=dev.get("tran"),
            smartctl_interface=smart.get("interface"),
        )
        partitions = _parse_partitions(dev.get("children") or [])

        disks.append({
            "device":       device_path,
            "model":        smart.get("model_name")  or dev.get("model")  or None,
            "model_family": smart.get("model_family"),
            "vendor":       smart.get("vendor")      or dev.get("vendor") or None,
            "serial":       smart.get("serial_number") or dev.get("serial") or None,
            "firmware":     smart.get("firmware_version"),
            "type":         disk_type,          # HDD | SSD | Unknown
            "interface":    interface,           # SATA | NVMe | SCSI…
            "form_factor":  smart.get("form_factor"),   # 2.5" | 3.5" | M.2…
            "removable":    dev.get("rm") in (True, "1", 1),
            "size_bytes":   size_bytes,
            "health": {
                "smart_passed":        smart.get("smart_status"),
                "power_on_hours":      smart.get("power_on_hours"),
                "temperature_celsius": smart.get("temperature_celsius"),
            },
            "partitions": partitions,
        })

    return {
        "total_disks": len(disks),
        "disks":       disks,
    }


def _parse_partitions(children: list, _depth: int = 0) -> list:
    """
    Coleta partições recursivamente para cobrir LVM, LUKS e RAID aninhados.
    Depth máximo: 4.
    """
    if _depth > 4:
        return []

    partitions = []
    for child in children:
        if child.get("type") not in _PARTITION_TYPES:
            continue

        size_bytes = safe_int(child.get("size"))
        partitions.append({
            "name":       child.get("name"),
            "type":       child.get("type"),
            "mountpoint": child.get("mountpoint") or None,
            "fstype":     child.get("fstype")     or None,
            "label":      child.get("label")      or None,
            "uuid":       child.get("uuid")       or None,
            "size_bytes": size_bytes,
            "children":   _parse_partitions(child.get("children") or [], _depth + 1),
        })

    return partitions

# =============================================================================
# FIM discovery/disk_discovery/disk_physical.py
# =============================================================================