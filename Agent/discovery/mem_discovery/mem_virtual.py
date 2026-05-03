# discovery/mem_discovery/mem_virtual.py
from Agent.utils.mem_discovery_parses import (
    parse_meminfo_kb,
    kb_to_gb,
    kb_to_mb,
)


def get_virtual_mem_info(meminfo, hypervisor_vendor):
    """
    Retorna informações de memória RAM para ambientes virtualizados.

    Unidade base: bytes. Campos 'gb' são display helpers.
    Notas contextuais centralizadas em metadata.notes no __main__.
    """
    total_kb      = parse_meminfo_kb(meminfo.get("memtotal"))
    available_kb  = parse_meminfo_kb(meminfo.get("memavailable"))
    free_kb       = parse_meminfo_kb(meminfo.get("memfree"))
    buffers_kb    = parse_meminfo_kb(meminfo.get("buffers"))
    cached_kb     = parse_meminfo_kb(meminfo.get("cached"))
    swap_total_kb = parse_meminfo_kb(meminfo.get("swaptotal"))
    swap_free_kb  = parse_meminfo_kb(meminfo.get("swapfree"))

    return {
        "total":     _size(total_kb),
        "available": _size(available_kb),
        "free":      _size(free_kb),
        "buffers":   _size(buffers_kb),
        "cached":    _size(cached_kb),
        "swap": {
            "total": _size(swap_total_kb),
            "free":  _size(swap_free_kb),
        },
        # slots indisponíveis em VM — sem nota inline (vai em metadata.notes)
        "slots": {
            "total":   None,
            "used":    None,
            "free":    None,
            "modules": [],
        },
    }


def _size(kb):
    """
    Retorna objeto de tamanho com bytes como unidade base e gb como display.
    Derivado de kB (fonte: /proc/meminfo).
    """
    if kb is None:
        return {"bytes": None, "gb": None}
    bytes_val = kb * 1024
    return {
        "bytes": bytes_val,
        "gb":    kb_to_gb(kb),
    }