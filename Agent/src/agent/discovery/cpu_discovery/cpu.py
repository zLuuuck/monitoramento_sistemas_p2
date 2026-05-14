# =============================================================================
# discovery/cpu_discovery/cpu.py
#
# Discovery de CPU — ponto de entrada do módulo.
#
# Coleta os dados brutos (lscpu + /proc/cpuinfo) e delega para o
# handler correto com base no ambiente já detectado pelo global_information.
# =============================================================================

from agent.utils.shell import run
from agent.utils.parsers import parse_lscpu, parse_cpuinfo
from agent.discovery.cpu_discovery.cpu_physical import get_physical_cpu_info
from agent.discovery.cpu_discovery.cpu_virtual import get_virtual_cpu_info


def get_cpu_info(is_virtualized: bool) -> dict:
    """
    Ponto de entrada do discovery de CPU.

    Recebe o ambiente já resolvido (is_virtualized) e delega para
    o handler físico ou virtual conforme necessário.

    Parâmetros:
        is_virtualized (bool): recebido do global_information, não redetectado aqui

    Retorno:
        dict com informações da CPU.
    """
    # ── Coleta bruta ──────────────────────────────────────────────────────────
    lscpu_raw   = run("lscpu")
    cpuinfo_raw = run("cat /proc/cpuinfo")

    # ── Parse ─────────────────────────────────────────────────────────────────
    lscpu   = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    cpuinfo = parse_cpuinfo(cpuinfo_raw) if cpuinfo_raw else []
    cpu0    = cpuinfo[0] if cpuinfo else {}   # primeiro núcleo como referência

    # ── Despacho ─────────────────────────────────────────────────────────────
    if is_virtualized:
        return get_virtual_cpu_info(lscpu, cpuinfo, cpu0)
    else:
        return get_physical_cpu_info(lscpu, cpuinfo, cpu0)

# =============================================================================
# FIM discovery/cpu_discovery/cpu.py
# =============================================================================