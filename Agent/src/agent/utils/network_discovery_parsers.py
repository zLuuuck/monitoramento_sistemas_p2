# utils/network_discovery_parsers.py
"""
Parsers para o módulo network_discovery.
Fontes: `ip -j addr show`, `ip -j link show`, `ip -j route show default`, sysfs.
Sem chamadas a shell aqui — apenas transformação de dados.
"""
import json


# ── ip addr ───────────────────────────────────────────────────────────────────

def parse_ip_addr(raw: str) -> list[dict]:
    """
    Parseia `ip -j addr show`. Retorna lista de interfaces, excluindo loopback.
    """
    if not raw:
        return []
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [e for e in entries if e.get("ifname") != "lo"]


# ── ip link ───────────────────────────────────────────────────────────────────

def parse_ip_link(raw: str) -> dict[str, dict]:
    """
    Parseia `ip -j link show`. Retorna dict indexado por ifname (sem loopback).
    """
    if not raw:
        return {}
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return {e["ifname"]: e for e in entries if e.get("ifname") != "lo"}


# ── default gateway ───────────────────────────────────────────────────────────

def parse_default_gateway(raw: str) -> dict | None:
    """
    Parseia `ip -j route show default`.
    Retorna dict com gateway/interface/metric/protocol, ou None.
    """
    if not raw:
        return None
    try:
        routes = json.loads(raw)
    except json.JSONDecodeError:
        return None
    for route in routes:
        if route.get("dst") in ("default", "0.0.0.0/0"):
            return {
                "gateway":   route.get("gateway"),
                "interface": route.get("dev"),
                "metric":    route.get("metric"),
                "protocol":  route.get("protocol"),
            }
    return None


# ── construtor de interface ───────────────────────────────────────────────────

def build_interface(addr_entry: dict, link_map: dict, is_virtual: bool = False) -> dict:
    """
    Monta o dict final de uma interface a partir de `ip addr` + `ip link`.
    Em bare-metal, enriquece com sysfs (speed, duplex, driver, bus_info PCI).
    Em VM, esses campos ficam None.
    """
    ifname = addr_entry.get("ifname", "")
    link   = link_map.get(ifname, {})

    # ── Endereços IP ─────────────────────────────────────────────────────────
    ipv4_list, ipv6_list = [], []
    for addr_info in addr_entry.get("addr_info", []):
        family = addr_info.get("family")
        ip     = addr_info.get("local")
        if not ip:
            continue
        entry = {
            "address":   ip,
            "prefix":    addr_info.get("prefixlen"),
            "scope":     addr_info.get("scope"),
            "broadcast": addr_info.get("broadcast"),
        }
        if family == "inet":
            ipv4_list.append(entry)
        elif family == "inet6":
            ipv6_list.append(entry)

    # ── Hardware (sysfs) ─────────────────────────────────────────────────────
    driver     = None
    speed_mbps = None
    duplex     = None
    bus_info   = None

    if not is_virtual:
        driver     = _sysfs_str(f"/sys/class/net/{ifname}/device/driver/module/name")
        speed_raw  = _sysfs_int(f"/sys/class/net/{ifname}/speed")
        speed_mbps = speed_raw if speed_raw and speed_raw > 0 else None
        duplex     = _sysfs_str(f"/sys/class/net/{ifname}/duplex")
        uevent     = _sysfs_str(f"/sys/class/net/{ifname}/device/uevent")
        if uevent:
            for line in uevent.splitlines():
                if line.startswith("PCI_SLOT_NAME="):
                    bus_info = line.split("=", 1)[1]
                    break

    return {
        "name":       ifname,
        "mac":        addr_entry.get("address") or link.get("address"),
        "link_type":  addr_entry.get("link_type") or link.get("link_type"),
        "mtu":        addr_entry.get("mtu") or link.get("mtu"),
        "state":      addr_entry.get("operstate") or link.get("operstate"),
        "flags":      addr_entry.get("flags") or link.get("flags") or [],
        "ipv4":       ipv4_list,
        "ipv6":       ipv6_list,
        "speed_mbps": speed_mbps,
        "duplex":     duplex,
        "driver":     driver,
        "bus_info":   bus_info,
    }


# ── sysfs helpers (privados) ──────────────────────────────────────────────────

def _sysfs_str(path: str) -> str | None:
    try:
        with open(path) as f:
            v = f.read().strip()
            return v if v else None
    except OSError:
        return None


def _sysfs_int(path: str) -> int | None:
    v = _sysfs_str(path)
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None
