# discovery/disk_discovery/disk_physical.py
from Agent.utils.shell import run
from Agent.utils.disk_discovery_parsers import (
    parse_lsblk,
    parse_smartctl,
    bytes_to_gb,
    bytes_to_tb,
    resolve_disk_type,
    resolve_interface,
)


def get_physical_disk_info(lsblk_raw):
    """
    Retorna informações de disco para hardware físico.
    Cruza dados do lsblk com smartctl por dispositivo.

    Parâmetro:
        lsblk_raw (str): saída bruta de `lsblk -J -b -o ...`
    """
    disks_raw = parse_lsblk(lsblk_raw)
    disks = []

    for dev in disks_raw:
        name = dev.get("name", "")
        device_path = f"/dev/{name}"

        # smartctl com saída JSON — requer root, falha silenciosa
        smartctl_raw = run(f"smartctl -i -j {device_path}")
        smart = parse_smartctl(smartctl_raw)

        # Tamanho: prioriza smartctl (bytes exatos), fallback lsblk
        size_bytes = smart.get("capacity_bytes") or _safe_int(dev.get("size"))

        # Tipo HDD/SSD
        disk_type = resolve_disk_type(
            rotation_rate=smart.get("rotation_rate"),
            rota_flag=dev.get("rota"),
        )

        # Interface
        interface = resolve_interface(
            tran=dev.get("tran"),
            smartctl_interface=smart.get("interface"),
        )

        # Partições do dispositivo
        partitions = _parse_partitions(dev.get("children") or [])

        disk = {
            "device": device_path,
            "name": name,
            "model": smart.get("model_name") or dev.get("model") or None,
            "model_family": smart.get("model_family"),
            "vendor": smart.get("vendor") or dev.get("vendor") or None,
            "serial": smart.get("serial_number") or dev.get("serial") or None,
            "firmware": smart.get("firmware_version"),
            "type": disk_type,                          # HDD | SSD | Unknown
            "interface": interface,                     # SATA | NVMe | SCSI…
            "form_factor": smart.get("form_factor"),    # 2.5" | 3.5" | M.2…
            "removable": dev.get("rm") in (True, "1", 1),
            "size": {
                "bytes": size_bytes,
                "gb": bytes_to_gb(size_bytes),
                "tb": bytes_to_tb(size_bytes),
            },
            "health": {
                "smart_passed": smart.get("smart_status"),
                "power_on_hours": smart.get("power_on_hours"),
                "temperature_celsius": smart.get("temperature_celsius"),
            },
            "partitions": partitions,
        }
        disks.append(disk)

    return {
        "total_disks": len(disks),
        "disks": disks,
        "virtualization": {
            "is_virtualized": False,
            "hypervisor": None,
        },
    }


# ── helpers privados ──────────────────────────────────────────────────────────

def _parse_partitions(children):
    """Mapeia partições filhas do lsblk para um formato limpo."""
    partitions = []
    for child in children:
        if child.get("type") not in ("part", "lvm", "md"):
            continue
        size_bytes = _safe_int(child.get("size"))
        partitions.append({
            "name": child.get("name"),
            "mountpoint": child.get("mountpoint") or None,
            "size": {
                "bytes": size_bytes,
                "gb": bytes_to_gb(size_bytes),
            },
        })
    return partitions


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None