# discovery/network_discovery/network_virtual.py
from Agent.utils.network_discovery_parsers import (
    parse_ip_addr,
    parse_ip_link,
    parse_default_gateway,
    build_interface,
)


def get_virtual_network_info(raw_data: dict, hypervisor_vendor: str) -> dict:
    """
    Retorna informações de rede para ambientes virtualizados.

    Usa apenas `ip addr`/`ip link` — ethtool e sysfs não são confiáveis em VMs.
    Campos de hardware (speed_mbps, duplex, driver, bus_info) ficam null.
    Notas contextuais centralizadas em metadata.notes no __main__.

    Parâmetros:
        raw_data (dict): saídas brutas coletadas em network.py
        hypervisor_vendor (str): ex: "KVM", "VMware", "Microsoft"
    """
    addr_entries = parse_ip_addr(raw_data.get("ip_addr") or "")
    link_map     = parse_ip_link(raw_data.get("ip_link") or "")
    gateway      = parse_default_gateway(raw_data.get("ip_route") or "")

    interfaces = [
        build_interface(entry, link_map, is_virtual=True)
        for entry in addr_entries
    ]

    return {
        "total_interfaces": len(interfaces),
        "default_gateway":  gateway,
        "interfaces":       interfaces,
    }
