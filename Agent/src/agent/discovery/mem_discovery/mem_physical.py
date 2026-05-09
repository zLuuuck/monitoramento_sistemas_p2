# =============================================================================
# discovery/mem_discovery/mem_physical.py
#
# Discovery de memória RAM para hardware físico (bare-metal).
#
# Em hardware físico, usamos dmidecode -t memory para obter os detalhes
# dos módulos instalados: fabricante, tipo DDR, velocidade, serial, etc.
# =============================================================================

from agent.utils.parsers import (
    parse_dmidecode_memory,
    parse_dmi_size_to_mb,
    parse_meminfo_kb,
    kb_to_bytes,
    _parse_dmi_speed,
)


def get_physical_mem_info(meminfo: dict, dmidecode_raw: str | None) -> dict:
    """
    Monta o payload de memória para hardware físico.

    Parâmetros:
        meminfo       (dict): saída parseada de /proc/meminfo
        dmidecode_raw (str):  saída bruta de `dmidecode -t memory` (pode ser None)

    Retorno:
        dict com total_bytes, swap_total_bytes e slots detalhados.
    """
    # ── Totais via /proc/meminfo ──────────────────────────────────────────────
    total_kb      = parse_meminfo_kb(meminfo.get("memtotal"))
    swap_total_kb = parse_meminfo_kb(meminfo.get("swaptotal"))

    # ── Slots via dmidecode ───────────────────────────────────────────────────
    dmi_blocks = parse_dmidecode_memory(dmidecode_raw) if dmidecode_raw else []

    # Filtra apenas blocos que representam slots de memória física
    slot_blocks = [
        b for b in dmi_blocks
        if b.get("type") in ("memory device",) or "size" in b
    ]

    slots = []
    for block in slot_blocks:
        size_mb   = parse_dmi_size_to_mb(block.get("size"))
        populated = size_mb is not None   # slot vazio tem size="No Module Installed"

        slots.append({
            "locator":              block.get("locator"),
            "bank_locator":         block.get("bank_locator"),
            "populated":            populated,
            "size_mb":              size_mb,
            "type":                 block.get("type", "Unknown"),  # DDR4, DDR5…
            "manufacturer":         block.get("manufacturer"),
            "part_number":          (block.get("part_number") or "").strip() or None,
            "speed_mhz":            _parse_dmi_speed(block.get("speed")),
            "configured_speed_mhz": _parse_dmi_speed(block.get("configured_memory_speed")),
            "form_factor":          block.get("form_factor"),
            "data_width_bits":      _parse_width(block.get("data_width")),
        })

    populated_count = sum(1 for s in slots if s["populated"])
    total_slots     = len(slots)

    return {
        "total_bytes":      kb_to_bytes(total_kb),
        "swap_total_bytes": kb_to_bytes(swap_total_kb),
        "slots": {
            "total":   total_slots,
            "used":    populated_count,
            "free":    total_slots - populated_count,
            "modules": slots,
        },
    }


def _parse_width(value_str: str | None) -> int | None:
    """Extrai inteiro de bits de strings como '64 bits'."""
    if not value_str:
        return None
    try:
        return int(value_str.split()[0])
    except (ValueError, IndexError):
        return None

# =============================================================================
# FIM discovery/mem_discovery/mem_physical.py
# =============================================================================