# utils/disk_discovery_parsers.py
import json
import re


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
        "model_name":         data.get("model_name"),
        "model_family":       data.get("model_family"),
        "serial_number":      data.get("serial_number"),
        "firmware_version":   data.get("firmware_version"),
        "vendor":             data.get("vendor"),
        "product":            data.get("product"),
        "revision":           data.get("revision"),
        "capacity_bytes": (
            data.get("user_capacity", {}).get("bytes")
        ),
        "logical_block_size":  data.get("logical_block_size"),
        "physical_block_size": data.get("physical_block_size"),
        "rotation_rate":       data.get("rotation_rate"),  # 0 = SSD, >0 = HDD RPM
        "form_factor": (
            data.get("form_factor", {}).get("name")
            if isinstance(data.get("form_factor"), dict)
            else data.get("form_factor")
        ),
        "interface":           device.get("type"),          # ata, nvme, scsi…
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


def sanitize_string(value):
    """
    Limpa strings vindas de lsblk/dmidecode:
    - Remove espaços extras nas bordas
    - Remove vírgulas e caracteres de controle no final
    - Retorna None se a string ficar vazia
    """
    if not value:
        return None
    # Remove espaços, vírgulas e caracteres de controle nas bordas
    cleaned = re.sub(r"[\s,;]+$", "", value.strip())
    cleaned = re.sub(r"^[\s,;]+", "", cleaned)
    return cleaned if cleaned else None


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


def resolve_disk_type(rotation_rate, rota_flag, is_virtual=False):
    """
    Determina o tipo do disco.

    - is_virtual=True  → "Virtual" (disco apresentado por hipervisor)
    - rotation_rate=0  → "SSD"
    - rotation_rate>0  → "HDD"
    - rota_flag="1"    → "HDD" (fallback lsblk)
    - rota_flag="0"    → "SSD" (fallback lsblk)
    """
    if is_virtual:
        return "Virtual"

    if rotation_rate is not None:
        if rotation_rate == 0:
            return "SSD"
        if rotation_rate > 0:
            return "HDD"

    if rota_flag is not None:
        return "HDD" if str(rota_flag) == "1" else "SSD"

    return "Unknown"


# Interfaces conhecidas e seus aliases normalizados
_INTERFACE_MAP = {
    "nvme": "NVMe",
    "sata": "SATA",
    "ata":  "SATA",
    "scsi": "SCSI",
    "sas":  "SAS",
    "usb":  "USB",
    "mmc":  "MMC",
    "ide":  "IDE",
    # Valores espúrios que aparecem em VMs VMware/QEMU no campo TRAN do lsblk
    "spi":  None,   # barramento embarcado — não é interface de disco real
    "":     None,
}


def resolve_interface(tran, smartctl_interface, model=None):
    """
    Normaliza o tipo de interface do disco.

    tran              : campo TRAN do lsblk (sata, nvme, usb, spi…)
    smartctl_interface: campo device.type do smartctl (ata, nvme, scsi…)
    model             : string do modelo do disco (usado como desambiguador)

    Retorna string normalizada ou "Unknown".
    """
    tran_clean = (tran or "").strip().lower()
    smart_clean = (smartctl_interface or "").strip().lower()

    # Tenta resolver pelo TRAN primeiro
    if tran_clean in _INTERFACE_MAP:
        resolved = _INTERFACE_MAP[tran_clean]
        if resolved:
            return resolved
        # tran é inválido (ex: "spi") — cai pro smartctl ou inferência por modelo
    elif tran_clean:
        return tran_clean.upper()

    # Tenta pelo smartctl
    if smart_clean in _INTERFACE_MAP:
        resolved = _INTERFACE_MAP[smart_clean]
        if resolved:
            return resolved
    elif smart_clean:
        return smart_clean.upper()

    # Último recurso: inferência pelo nome do modelo
    if model:
        model_lower = model.lower()
        if "nvme" in model_lower:
            return "NVMe"
        if "sata" in model_lower:
            return "SATA"
        if any(k in model_lower for k in ("virtual", "vmware", "qemu", "vbox")):
            return "SCSI"   # padrão para discos virtuais sem interface declarada

    return "Unknown"


def resolve_partition_role(name, mountpoint, size_bytes):
    """
    Infere o papel provável de uma partição quando mountpoint é None.

    Retorna string descritiva ou None se não for possível inferir.
    """
    if mountpoint:
        return None  # já tem mountpoint, não precisa de inferência

    if not name:
        return None

    name_lower = name.lower()

    # Partição muito pequena (< 10 MB) sem mountpoint → BIOS boot / EFI guard
    if size_bytes and size_bytes < 10 * 1024 * 1024:
        return "bios_boot"

    # Nomes comuns de LVM physical volume
    if any(k in name_lower for k in ("lvm", "vg", "pv")):
        return "lvm_pv"

    return "unmounted"