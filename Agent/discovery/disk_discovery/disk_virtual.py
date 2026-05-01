# discovery/disk_discovery/disk_virtual.py
from Agent.utils.disk_discovery_parsers import (
    parse_lsblk,
    bytes_to_gb,
    bytes_to_tb,
    resolve_disk_type,
    resolve_interface,
)


def get_virtual_disk_info(lsblk_raw, hypervisor_vendor):
    """
    Retorna informações de disco para ambientes virtualizados.

    Em VMs, smartctl não é confiável (discos são virtuais: virtio, vmdk, vhd…).
    Usamos apenas lsblk, que é sempre acessível e retorna dados corretos
    sobre os volumes apresentados à VM pelo hipervisor.

    Parâmetros:
        lsblk_raw (str): saída bruta de `lsblk -J -b -o ...`
        hypervisor_vendor (str): nome do hipervisor detectado
    """
    disks_raw = parse_lsblk(lsblk_raw)
    disks = []

    for dev in disks_raw:
        name = dev.get("name", "")
        size_bytes = _safe_int(dev.get("size"))

        # Em VMs o campo ROTA do lsblk ainda é útil:
        # virtio-blk e NVMe virtual reportam rota=0 (não-rotacional)
        disk_type = resolve_disk_type(
            rotation_rate=None,      # smartctl indisponível
            rota_flag=dev.get("rota"),
        )

        interface = resolve_interface(
            tran=dev.get("tran"),
            smartctl_interface=None,
        )

        partitions = _parse_partitions(dev.get("children") or [])

        disk = {
            "device": f"/dev/{name}",
            "name": name,
            # model/vendor podem vir do lsblk em alguns hipervisores
            "model": dev.get("model") or None,
            "vendor": dev.get("vendor") or None,
            "serial": dev.get("serial") or None,
            "firmware": None,         # indisponível em VMs
            "type": disk_type,
            "interface": interface,
            "form_factor": None,      # não se aplica a discos virtuais
            "removable": dev.get("rm") in (True, "1", 1),
            "size": {
                "bytes": size_bytes,
                "gb": bytes_to_gb(size_bytes),
                "tb": bytes_to_tb(size_bytes),
            },
            # SMART indisponível em VMs — campos explicitamente nulos
            "health": {
                "smart_passed": None,
                "power_on_hours": None,
                "temperature_celsius": None,
                "note": "SMART data unavailable in virtualized environments",
            },
            "partitions": partitions,
        }
        disks.append(disk)

    return {
        "total_disks": len(disks),
        "disks": disks,
        "virtualization": {
            "is_virtualized": True,
            "hypervisor": hypervisor_vendor,
        },
    }


# ── helpers privados ──────────────────────────────────────────────────────────

def _parse_partitions(children):
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