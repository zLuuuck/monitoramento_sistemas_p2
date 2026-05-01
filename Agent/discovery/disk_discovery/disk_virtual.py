# discovery/disk_discovery/disk_virtual.py
from Agent.utils.disk_discovery_parsers import (
    parse_lsblk,
    sanitize_string,
    bytes_to_gb,
    bytes_to_tb,
    resolve_disk_type,
    resolve_interface,
    resolve_partition_role,
)


def get_virtual_disk_info(lsblk_raw, hypervisor_vendor):
    """
    Retorna informações de disco para ambientes virtualizados.

    Em VMs, smartctl não é confiável (discos são virtuais: virtio, vmdk, vhd…).
    Usamos apenas lsblk. Campos de hardware real (firmware, SMART, form_factor)
    são explicitamente nulos — não inventamos dados.
    """
    disks_raw = parse_lsblk(lsblk_raw)
    disks = []

    for dev in disks_raw:
        name      = dev.get("name", "")
        size_bytes = _safe_int(dev.get("size"))

        # Sanitiza strings vindas do lsblk (ex: "VMware, " → "VMware")
        model  = sanitize_string(dev.get("model"))
        vendor = sanitize_string(dev.get("vendor"))
        serial = sanitize_string(dev.get("serial"))

        # Disco virtual — tipo sempre "Virtual", independente do campo ROTA
        disk_type = resolve_disk_type(
            rotation_rate=None,
            rota_flag=dev.get("rota"),
            is_virtual=True,
        )

        # Interface: tenta lsblk, usa modelo como desambiguador se TRAN for inválido
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
            "firmware":    None,        # indisponível em VMs
            "type":        disk_type,   # sempre "Virtual"
            "interface":   interface,
            "form_factor": None,        # não se aplica a discos virtuais
            "removable":   dev.get("rm") in (True, "1", 1),
            "size": {
                "bytes": size_bytes,
                "gb":    bytes_to_gb(size_bytes),
                "tb":    bytes_to_tb(size_bytes),
            },
            "health": {
                "smart_passed":        None,
                "power_on_hours":      None,
                "temperature_celsius": None,
                "note": "SMART data unavailable in virtualized environments",
            },
            "partitions": partitions,
        }
        disks.append(disk)

    return {
        "total_disks": len(disks),
        "disks": disks,
        # bloco virtualization removido — centralizado em environment no __main__
    }


# ── helpers privados ──────────────────────────────────────────────────────────

def _parse_partitions(children):
    partitions = []
    for child in children:
        if child.get("type") not in ("part", "lvm", "md"):
            continue

        size_bytes = _safe_int(child.get("size"))
        mountpoint = child.get("mountpoint") or None
        name       = child.get("name")

        # Infere papel da partição quando mountpoint é None
        role = resolve_partition_role(name, mountpoint, size_bytes)

        entry = {
            "name":       name,
            "mountpoint": mountpoint,
            "size": {
                "bytes": size_bytes,
                "gb":    bytes_to_gb(size_bytes),
            },
        }
        if role:
            entry["role"] = role   # só adiciona quando tem algo útil a dizer

        partitions.append(entry)
    return partitions


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None