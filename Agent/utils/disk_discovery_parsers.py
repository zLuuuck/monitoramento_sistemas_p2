# utils/disk_discovery_parsers.py
import json


def parse_lsblk(output):
    """
    Parseia saída de `lsblk -J -b -o NAME,SIZE,TYPE,ROTA,MOUNTPOINT,MODEL,VENDOR,SERIAL,TRAN,RM`
    Retorna lista de dicts (apenas devices do tipo 'disk').
    """
    if not output:
        return []
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return []

    disks = []
    for device in data.get("blockdevices", []):
        if device.get("type") == "disk":
            disks.append(device)
    return disks


def parse_smartctl(output):
    """
    Parseia saída de `smartctl -i -j /dev/<disk>` (JSON nativo do smartctl).
    Retorna dict com os campos relevantes, ou {} se falhar.
    """
    if not output:
        return {}
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return {}

    device = data.get("device", {})
    info = {
        "model_name": data.get("model_name"),
        "model_family": data.get("model_family"),
        "serial_number": data.get("serial_number"),
        "firmware_version": data.get("firmware_version"),
        "vendor": data.get("vendor"),
        "product": data.get("product"),
        "revision": data.get("revision"),
        "capacity_bytes": (
            data.get("user_capacity", {}).get("bytes")
        ),
        "logical_block_size": data.get("logical_block_size"),
        "physical_block_size": data.get("physical_block_size"),
        "rotation_rate": data.get("rotation_rate"),   # 0 = SSD, >0 = HDD (RPM)
        "form_factor": (
            data.get("form_factor", {}).get("name")
            if isinstance(data.get("form_factor"), dict)
            else data.get("form_factor")
        ),
        "interface": device.get("type"),               # ata, nvme, scsi…
        "smart_status": (
            data.get("smart_status", {}).get("passed")
        ),
        "power_on_hours": (
            data.get("power_on_time", {}).get("hours")
        ),
        "temperature_celsius": (
            data.get("temperature", {}).get("current")
        ),
    }
    return info


def bytes_to_gb(value):
    """Converte bytes para GB com 2 casas decimais."""
    if value is None:
        return None
    try:
        return round(int(value) / (1024 ** 3), 2)
    except (ValueError, TypeError):
        return None


def bytes_to_tb(value):
    """Converte bytes para TB com 2 casas decimais."""
    if value is None:
        return None
    try:
        return round(int(value) / (1024 ** 4), 2)
    except (ValueError, TypeError):
        return None


def resolve_disk_type(rotation_rate, rota_flag):
    """
    Determina se o disco é HDD, SSD ou NVMe.

    - rotation_rate: int vindo do smartctl (0 = SSD, >0 = HDD em RPM)
    - rota_flag: string "0" ou "1" vinda do lsblk (campo ROTA)
    """
    # smartctl é mais confiável quando disponível
    if rotation_rate is not None:
        if rotation_rate == 0:
            return "SSD"
        if rotation_rate > 0:
            return "HDD"

    # fallback: campo ROTA do lsblk ("0" = não-rotacional = SSD/NVMe)
    if rota_flag is not None:
        return "HDD" if str(rota_flag) == "1" else "SSD"

    return "Unknown"


def resolve_interface(tran, smartctl_interface):
    """
    Normaliza o tipo de interface do disco.
    tran: campo TRAN do lsblk (sata, nvme, usb…)
    smartctl_interface: campo device.type do smartctl (ata, nvme, scsi…)
    """
    value = (tran or smartctl_interface or "").lower()
    mapping = {
        "nvme": "NVMe",
        "sata": "SATA",
        "ata": "SATA",
        "scsi": "SCSI",
        "sas": "SAS",
        "usb": "USB",
        "mmc": "MMC",
    }
    return mapping.get(value, value.upper() if value else "Unknown")