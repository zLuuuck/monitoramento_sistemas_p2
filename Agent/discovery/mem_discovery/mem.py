# discovery/mem_discovery/mem.py
from Agent.utils.shell import run
from Agent.utils.parser import parse_lscpu
from Agent.utils.mem_discovery_parses import parse_meminfo
from Agent.discovery.mem_discovery.mem_physical import get_physical_mem_info
from Agent.discovery.mem_discovery.mem_virtual import get_virtual_mem_info


def get_mem_info():
    """
    Ponto de entrada do discovery de memória RAM.

    Detecta se o host é físico ou virtualizado (usando lscpu, assim como
    o módulo de CPU) e delega para o handler adequado.

    Retorna um dict pronto para serialização JSON.
    """
    # ── Coleta bruta ──────────────────────────────────────────────────────────
    meminfo_raw = run("cat /proc/meminfo")
    lscpu_raw = run("lscpu")

    meminfo = parse_meminfo(meminfo_raw) if meminfo_raw else {}
    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    # ── Detecção de virtualização (mesmo critério do cpu.py) ──────────────────
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor_vendor)

    if is_virtualized:
        return get_virtual_mem_info(meminfo, hypervisor_vendor)

    # ── Hardware físico: tenta dmidecode (requer root) ────────────────────────
    dmidecode_raw = run("dmidecode -t memory")
    return get_physical_mem_info(meminfo, dmidecode_raw)