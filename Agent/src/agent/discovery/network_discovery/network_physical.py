# =============================================================================
# discovery/network_discovery/network_physical.py
#
# Discovery de rede para hardware físico (bare-metal).
#
# Além de ip addr/link, enriquece cada interface com speed/duplex/driver
# via ethtool quando sysfs não retorna os valores.
# =============================================================================

from agent.utils.shell import run
from agent.utils.parsers import (
    parse_ip_addr,
    parse_ip_link,
    parse_default_gateway,
    build_network_interface,
)


def get_physical_network_info(raw_data: dict) -> dict:
    """
    Monta o payload de rede para hardware físico.

    Parâmetros:
        raw_data (dict): saídas brutas de ip addr, ip link e ip route

    Retorno:
        dict com total_interfaces, default_gateway e interfaces com dados de hardware.
    """
    addr_entries = parse_ip_addr(raw_data.get("ip_addr") or "")
    link_map     = parse_ip_link(raw_data.get("ip_link") or "")
    gateway      = parse_default_gateway(raw_data.get("ip_route") or "")

    interfaces = [
        build_network_interface(entry, link_map, is_virtual=False)
        for entry in addr_entries
    ]

    # Tenta enriquecer via ethtool quando sysfs não retornou speed/duplex/driver
    for iface in interfaces:
        _enrich_with_ethtool(iface)

    return {
        "total_interfaces": len(interfaces),
        "default_gateway":  gateway,
        "interfaces":       interfaces,
    }


# =============================================================================
# Enriquecimento via ethtool
# =============================================================================

def _enrich_with_ethtool(iface: dict) -> None:
    """
    Preenche speed/duplex/driver via ethtool quando sysfs não retornou dados.

    Opera in-place no dict da interface. Falha silenciosa.

    Parâmetros:
        iface (dict): dict da interface (modificado in-place)
    """
    name = iface.get("name")
    if not name:
        return

    # ── Driver + bus-info ─────────────────────────────────────────────────────
    if not iface.get("driver"):
        driver_raw = run(f"ethtool -i {name}")
        if driver_raw:
            for line in driver_raw.splitlines():
                line = line.strip()
                if line.startswith("driver:"):
                    iface["driver"] = line.split(":", 1)[1].strip() or None
                elif line.startswith("bus-info:") and not iface.get("bus_info"):
                    iface["bus_info"] = line.split(":", 1)[1].strip() or None

    # ── Speed + duplex ────────────────────────────────────────────────────────
    if iface.get("speed_mbps") is None or iface.get("duplex") is None:
        speed_raw = run(f"ethtool {name}")
        if speed_raw:
            for line in speed_raw.splitlines():
                line = line.strip()
                if iface.get("speed_mbps") is None and line.startswith("Speed:"):
                    val = line.split(":", 1)[1].strip()   # ex: "1000Mb/s"
                    try:
                        iface["speed_mbps"] = int(val.split("M")[0])
                    except (ValueError, IndexError):
                        pass
                elif iface.get("duplex") is None and line.startswith("Duplex:"):
                    iface["duplex"] = line.split(":", 1)[1].strip().lower() or None

# =============================================================================
# FIM discovery/network_discovery/network_physical.py
# =============================================================================