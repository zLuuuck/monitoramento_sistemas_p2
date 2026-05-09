# discovery/motherboard_discovery/motherboard_physical.py
from agent.utils.shell import run
from agent.utils.parsers import (
    parse_baseboard,
    parse_bios,
    parse_cpu_sockets,
    parse_memory_slots_summary,
    parse_system_slots,
    _clean,
)


def get_physical_motherboard_info(raw_data: dict) -> dict:
    """
    Retorna informações completas da placa-mãe para hardware físico.

    Combina dmidecode types 0, 2, 4, 9 e 17 para montar o perfil completo.
    O chipset é resolvido via lspci (ISA/LPC bridge), pois dmidecode não o
    expõe diretamente em type 2.

    Parâmetro:
        raw_data (dict): saídas brutas coletadas em motherboard.py
    """
    board        = parse_baseboard(raw_data.get("dmi_board") or "")
    bios         = parse_bios(raw_data.get("dmi_bios") or "")
    cpu_sockets  = parse_cpu_sockets(raw_data.get("dmi_cpu_slot") or "")
    mem_summary  = parse_memory_slots_summary(raw_data.get("dmi_mem") or "")
    system_slots = parse_system_slots(raw_data.get("dmi_slots") or "")
    chipset      = _resolve_chipset()

    return {
        "manufacturer":  _clean(board.get("manufacturer")),
        "product_name":  _clean(board.get("product_name")),
        "version":       _clean(board.get("version")),
        "serial_number": _clean(board.get("serial_number")),
        "asset_tag":     _clean(board.get("asset_tag")),
        "chipset":       chipset,
        "bios": {
            "vendor":       _clean(bios.get("vendor")),
            "version":      _clean(bios.get("version")),
            "release_date": _clean(bios.get("release_date")),
            "revision":     _clean(bios.get("bios_revision")),
        },
        "cpu_sockets": {
            "total":     len(cpu_sockets),
            "populated": sum(1 for s in cpu_sockets if s["populated"]),
            "sockets":   cpu_sockets,
        },
        "ram_slots":      mem_summary,
        "expansion_slots": system_slots,
        "virtualization": {
            "is_virtualized": False,
            "hypervisor":     None,
        },
    }


# ── helpers privados ──────────────────────────────────────────────────────────

def _resolve_chipset() -> str | None:
    """
    Identifica o chipset via lspci buscando ISA bridge / LPC bridge /
    Platform Controller Hub — onde o chipset aparece tipicamente.
    Falha silenciosa — retorna None se lspci não estiver disponível.
    """
    lspci_raw = run("lspci")
    if not lspci_raw:
        return None

    keywords = (
        "isa bridge",
        "lpc bridge",
        "fusion controller hub",
        "platform controller hub",
    )
    for line in lspci_raw.splitlines():
        lower = line.lower()
        if any(kw in lower for kw in keywords):
            parts = line.split(":", 2)
            return parts[2].strip() if len(parts) >= 3 else line.strip()
    return None
