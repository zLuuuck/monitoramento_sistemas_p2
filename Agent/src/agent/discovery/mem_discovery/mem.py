# =============================================================================
# discovery/mem_discovery/mem.py
#
# Discovery de memória RAM — ponto de entrada do módulo.
#
# Coleta os dados brutos e delega para o handler correto
# com base no ambiente recebido do global_information.
# =============================================================================

from agent.utils.shell import run
from agent.utils.parsers import parse_meminfo
from agent.discovery.mem_discovery.mem_physical import get_physical_mem_info
from agent.discovery.mem_discovery.mem_virtual import get_virtual_mem_info


def get_mem_info(is_virtualized: bool) -> dict:
    """
    Ponto de entrada do discovery de memória RAM.

    Parâmetros:
        is_virtualized (bool): recebido do global_information, não redetectado aqui

    Retorno:
        dict com informações de memória RAM.
    """
    # ── Coleta bruta ──────────────────────────────────────────────────────────
    meminfo_raw = run("cat /proc/meminfo")
    meminfo     = parse_meminfo(meminfo_raw) if meminfo_raw else {}

    # ── Despacho ─────────────────────────────────────────────────────────────
    if is_virtualized:
        return get_virtual_mem_info(meminfo)

    # Hardware físico: tenta dmidecode para dados dos slots (requer root)
    dmidecode_raw = run("dmidecode -t memory")
    return get_physical_mem_info(meminfo, dmidecode_raw)

# =============================================================================
# FIM discovery/mem_discovery/mem.py
# =============================================================================