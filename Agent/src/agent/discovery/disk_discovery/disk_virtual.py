# discovery/disk_discovery/disk_virtual.py
from agent.utils.disk_discovery_parsers import (
    parse_lsblk,
    sanitize_string,
    bytes_to_gb,
    bytes_to_tb,
    resolve_disk_type,
    resolve_interface,
    resolve_partition_role,
)

_PARTITION_TYPES = {"part", "lvm", "md", "raid", "crypt"}


def get_virtual_disk_info(lsblk_raw: str, hypervisor_vendor: str) -> dict:
    """
    Retorna informações de disco para ambientes virtualizados.

    Usa apenas lsblk — smartctl não é confiável em VMs.
    Campos de hardware real (firmware, SMART, form_factor) são null.

    Cobertura:
    - Loop devices (type=loop) são ignorados.
    - Partições coletadas recursivamente: part, lvm, md, raid, crypt.
    - Notas contextuais centralizadas em metadata.notes no __main__.
    """
    disks_raw = parse_lsblk(lsblk_raw)
    disks = []

    for dev in disks_raw:
        if dev.get("type") == "loop":
            continue
        name = dev.get("name", "")
        if not name:
            continue

        size_bytes = _safe_int(dev.get("size"))
        model      = sanitize_string(dev.get("model"))
        vendor     = sanitize_string(dev.get("vendor"))
        serial     = sanitize_string(dev.get("serial"))

        disk_type = resolve_disk_type(
            rotation_rate=None,
            rota_flag=dev.get("rota"),
            is_virtual=True,
        )

        interface = resolve_interface(
            tran=dev.get("tran"),
            smartctl_interface=None,
            model=model,
        )

        partitions = _parse_partitions(dev.get("children") or [])

        disk = {
            "device":      f"/dev/{name}",
            "name":        name,
            "model":       model,
            "vendor":      vendor,
            "serial":      serial,
            "firmware":    None,
            "type":        disk_type,
            "interface":   interface,
            "form_factor": None,
            "removable":   dev.get("rm") in (True, "1", 1),
            "size": {
                "bytes": size_bytes,
                "gb":    bytes_to_gb(size_bytes),
                "tb":    bytes_to_tb(size_bytes),
            },
            # SMART null em VM — nota vai em metadata.notes
            "health": {
                "smart_passed":        None,
                "power_on_hours":      None,
                "temperature_celsius": None,
            },
            "partitions": partitions,
        }
        disks.append(disk)

    return {
        "total_disks": len(disks),
        "disks":       disks,
    }


# ── helpers privados ──────────────────────────────────────────────────────────

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

        size_bytes = _safe_int(child.get("size"))
        mountpoint = child.get("mountpoint") or None
        name       = child.get("name")

        role = resolve_partition_role(name, mountpoint, size_bytes)

        entry = {
            "name":       name,
            "type":       child.get("type"),
            "mountpoint": mountpoint,
            "fstype":     child.get("fstype") or None,
            "label":      child.get("label") or None,
            "uuid":       child.get("uuid") or None,
            "size": {
                "bytes": size_bytes,
                "gb":    bytes_to_gb(size_bytes),
            },
            "children": _parse_partitions(child.get("children") or [], _depth + 1),
        }
        if role:
            entry["role"] = role

        partitions.append(entry)
    return partitions


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
