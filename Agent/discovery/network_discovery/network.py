# discovery/network_discovery/network.py
from Agent.utils.shell import run
from Agent.utils.parser import parse_lscpu
from Agent.discovery.network_discovery.network_physical import get_physical_network_info
from Agent.discovery.network_discovery.network_virtual import get_virtual_network_info


def get_network_info():
    """
    Ponto de entrada do discovery de interfaces de rede.

    Detecta se o host é físico ou virtualizado (mesmo critério de cpu.py/mem.py)
    e delega para o handler adequado.

    Retorna um dict pronto para serialização JSON.
    """
    # ── Coleta comum ──────────────────────────────────────────────────────────
    # ip -j: saída JSON nativa — mais confiável que ifconfig/ip text
    ip_addr_raw  = run("ip -j addr show")
    ip_link_raw  = run("ip -j link show")
    ip_route_raw = run("ip -j route show default")
    lscpu_raw    = run("lscpu")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    # ── Detecção de virtualização ─────────────────────────────────────────────
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized    = bool(hypervisor_vendor)

    raw_data = {
        "ip_addr":  ip_addr_raw,
        "ip_link":  ip_link_raw,
        "ip_route": ip_route_raw,
    }

    if is_virtualized:
        return get_virtual_network_info(raw_data, hypervisor_vendor)

    return get_physical_network_info(raw_data)
