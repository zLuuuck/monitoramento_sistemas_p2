# =============================================================================
# discovery/network_discovery/network.py
#
# Discovery de interfaces de rede — ponto de entrada do módulo.
#
# Coleta os dados brutos via ip e delega para o handler correto
# com base no ambiente recebido do global_information.
# =============================================================================

from agent.utils.shell import run
from agent.discovery.network_discovery.network_physical import get_physical_network_info
from agent.discovery.network_discovery.network_virtual import get_virtual_network_info


def get_network_info(is_virtualized: bool) -> dict:
    """
    Ponto de entrada do discovery de rede.

    Parâmetros:
        is_virtualized (bool): recebido do global_information, não redetectado aqui

    Retorno:
        dict com total_interfaces, default_gateway e lista de interfaces.
    """
    # ── Coleta bruta ──────────────────────────────────────────────────────────
    # ip -j: saída JSON nativa — mais confiável que ifconfig/ip text
    ip_addr_raw  = run("ip -j addr show")
    ip_link_raw  = run("ip -j link show")
    ip_route_raw = run("ip -j route show default")

    raw_data = {
        "ip_addr":  ip_addr_raw,
        "ip_link":  ip_link_raw,
        "ip_route": ip_route_raw,
    }

    # ── Despacho ─────────────────────────────────────────────────────────────
    if is_virtualized:
        return get_virtual_network_info(raw_data)

    return get_physical_network_info(raw_data)

# =============================================================================
# FIM discovery/network_discovery/network.py
# =============================================================================