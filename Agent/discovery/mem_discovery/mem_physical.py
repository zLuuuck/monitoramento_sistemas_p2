# discovery/mem_discovery/mem_physical.py
from Agent.utils.mem_discovery_parses import (
    parse_dmidecode_memory,
    parse_dmi_size_to_mb,
    parse_meminfo_kb,
    kb_to_gb,
    kb_to_mb,
)


def get_physical_mem_info(meminfo, dmidecode_raw):
    """
    Retorna informações de memória RAM para hardware físico.

    Parâmetros:
        meminfo (dict): saída já parseada de /proc/meminfo
        dmidecode_raw (str): saída bruta de `dmidecode -t memory`
    """
    # ── Totais via /proc/meminfo ──────────────────────────────────────────────
    total_kb = parse_meminfo_kb(meminfo.get("memtotal"))
    available_kb = parse_meminfo_kb(meminfo.get("memavailable"))
    free_kb = parse_meminfo_kb(meminfo.get("memfree"))

    # ── Slots via dmidecode ───────────────────────────────────────────────────
    dmi_blocks = parse_dmidecode_memory(dmidecode_raw) if dmidecode_raw else []

    # Filtra apenas blocos que são efetivamente slots de memória física
    slot_blocks = [
        b for b in dmi_blocks
        if b.get("type") in ("Memory Device",)
        or "size" in b  # fallback: qualquer bloco com campo "size"
    ]

    total_slots = len(slot_blocks)
    slots = []

    for block in slot_blocks:
        size_mb = parse_dmi_size_to_mb(block.get("size"))
        populated = size_mb is not None

        slot = {
            "locator": block.get("locator"),
            "bank_locator": block.get("bank_locator"),
            "populated": populated,
            "size_mb": size_mb,
            "size_gb": round(size_mb / 1024, 2) if size_mb else None,
            "type": block.get("type", "Unknown"),          # DDR4, DDR5…
            "type_detail": block.get("type_detail"),
            "manufacturer": block.get("manufacturer"),
            "part_number": block.get("part_number", "").strip() or None,
            "serial_number": block.get("serial_number", "").strip() or None,
            "speed_mhz": _parse_speed(block.get("speed")),
            "configured_speed_mhz": _parse_speed(block.get("configured_memory_speed")),
            "form_factor": block.get("form_factor"),
            "data_width_bits": _parse_width(block.get("data_width")),
        }
        slots.append(slot)

    populated_slots = [s for s in slots if s["populated"]]
    used_slots = len(populated_slots)

    return {
        "total_mb": kb_to_mb(total_kb),
        "total_gb": kb_to_gb(total_kb),
        "available_mb": kb_to_mb(available_kb),
        "available_gb": kb_to_gb(available_kb),
        "free_mb": kb_to_mb(free_kb),
        "free_gb": kb_to_gb(free_kb),
        "slots": {
            "total": total_slots,
            "used": used_slots,
            "free": total_slots - used_slots,
            "modules": slots,
        },
        "virtualization": {
            "is_virtualized": False,
            "hypervisor": None,
        },
    }


# ── helpers privados ──────────────────────────────────────────────────────────

def _parse_speed(value_str):
    """
    Extrai inteiro de MHz de strings como '3200 MT/s', '2400 MHz', 'Unknown'.
    """
    if not value_str or value_str.lower() in ("unknown", ""):
        return None
    try:
        return int(value_str.split()[0])
    except (ValueError, IndexError):
        return None


def _parse_width(value_str):
    """Extrai inteiro de bits de strings como '64 bits'."""
    if not value_str:
        return None
    try:
        return int(value_str.split()[0])
    except (ValueError, IndexError):
        return None