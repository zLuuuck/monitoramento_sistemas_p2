# discovery/mem_discovery/mem_virtual.py
from Agent.utils.mem_discovery_parses import (
    parse_meminfo_kb,
    kb_to_gb,
    kb_to_mb,
)


def get_virtual_mem_info(meminfo, hypervisor_vendor):
    """
    Retorna informações de memória RAM para ambientes virtualizados.

    Os valores de total/disponível refletem a memória alocada à VM
    pelo hipervisor — não a RAM física do host. dmidecode não é usado
    pois retorna dados fictícios ou está bloqueado em VMs.
    """
    total_kb      = parse_meminfo_kb(meminfo.get("memtotal"))
    available_kb  = parse_meminfo_kb(meminfo.get("memavailable"))
    free_kb       = parse_meminfo_kb(meminfo.get("memfree"))
    buffers_kb    = parse_meminfo_kb(meminfo.get("buffers"))
    cached_kb     = parse_meminfo_kb(meminfo.get("cached"))
    swap_total_kb = parse_meminfo_kb(meminfo.get("swaptotal"))
    swap_free_kb  = parse_meminfo_kb(meminfo.get("swapfree"))

    return {
        # Contexto explícito: esses valores são da VM, não do host físico
        "allocated_note": (
            "Values represent memory allocated to this VM by the hypervisor, "
            "not the total physical RAM of the host"
        ),
        "total_mb":     kb_to_mb(total_kb),
        "total_gb":     kb_to_gb(total_kb),
        "available_mb": kb_to_mb(available_kb),
        "available_gb": kb_to_gb(available_kb),
        "free_mb":      kb_to_mb(free_kb),
        "free_gb":      kb_to_gb(free_kb),
        "buffers_mb":   kb_to_mb(buffers_kb),
        "cached_mb":    kb_to_mb(cached_kb),
        "swap": {
            "total_mb": kb_to_mb(swap_total_kb),
            "free_mb":  kb_to_mb(swap_free_kb),
        },
        "slots": {
            "total":   None,
            "used":    None,
            "free":    None,
            "modules": [],
            "note":    "Slot information unavailable in virtualized environments",
        },
        # bloco virtualization removido — centralizado em environment no __main__
    }