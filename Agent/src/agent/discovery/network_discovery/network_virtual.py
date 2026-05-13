# =============================================================================
# discovery/network_discovery/network_virtual.py
#
# Discovery de rede para ambientes virtualizados.
#
# Usa apenas `ip addr` e `ip link` — ethtool e sysfs não são confiáveis em VMs.
# Campos de hardware (speed_mbps, duplex, driver, bus_info) são OMITIDOS
# do payload (não incluídos como null) pois não existem em VMs.
# =============================================================================

from agent.utils.parsers import (
    parse_ip_addr,
    parse_ip_link,
    parse_default_gateway,
    build_network_interface,
)


def get_virtual_network_info(raw_data: dict) -> dict:
    """
    Monta o payload de rede para ambiente virtualizado.

    Parâmetros:
        raw_data (dict): saídas brutas de ip addr, ip link e ip route

    Retorno:
        dict com total_interfaces, default_gateway e interfaces sem campos de hardware.
    """
    addr_entries = parse_ip_addr(raw_data.get("ip_addr") or "")
    link_map     = parse_ip_link(raw_data.get("ip_link") or "")
    gateway      = parse_default_gateway(raw_data.get("ip_route") or "")

    # is_virtual=True → build_network_interface omite speed/duplex/driver/bus_info
    interfaces = [
        build_network_interface(entry, link_map, is_virtual=True)
        for entry in addr_entries
    ]

    return {
        "total_interfaces": len(interfaces),
        "default_gateway":  gateway,
        "interfaces":       interfaces,
    }

# =============================================================================
# FIM discovery/network_discovery/network_virtual.py
# =============================================================================