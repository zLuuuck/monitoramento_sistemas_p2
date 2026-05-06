# discovery/motherboard_discovery/motherboard_virtual.py
from agent.utils.motherboard_discovery_parsers import (
    parse_baseboard,
    parse_bios,
    _clean,
)


def get_virtual_motherboard_info(raw_data: dict, hypervisor_vendor: str) -> dict:
    """
    Retorna informações de placa-mãe para ambientes virtualizados.

    Em VMs, dmidecode type 2 expõe dados do host virtual (ex: 'QEMU Board',
    'VMware SVGA II'). Campos reais de hardware (chipset, sockets físicos,
    slots PCIe) ficam null — não são expostos pelo hipervisor.
    Notas contextuais centralizadas em metadata.notes no __main__.

    Parâmetros:
        raw_data (dict): saídas brutas coletadas em motherboard.py
        hypervisor_vendor (str): ex: "KVM", "VMware", "Microsoft"
    """
    board = parse_baseboard(raw_data.get("dmi_board") or "")
    bios  = parse_bios(raw_data.get("dmi_bios") or "")

    return {
        "manufacturer":  _clean(board.get("manufacturer")),
        "product_name":  _clean(board.get("product_name")),
        "version":       _clean(board.get("version")),
        "serial_number": _clean(board.get("serial_number")),
        "asset_tag":     _clean(board.get("asset_tag")),
        "chipset":       None,   # não exposto pelo hipervisor
        "bios": {
            "vendor":       _clean(bios.get("vendor")),
            "version":      _clean(bios.get("version")),
            "release_date": _clean(bios.get("release_date")),
            "revision":     _clean(bios.get("bios_revision")),
        },
        # Slots não são expostos pelo hipervisor
        "cpu_sockets": {
            "total":     None,
            "populated": None,
            "sockets":   [],
        },
        "ram_slots": {
            "total": None,
            "used":  None,
            "free":  None,
        },
        "expansion_slots": [],
    }
