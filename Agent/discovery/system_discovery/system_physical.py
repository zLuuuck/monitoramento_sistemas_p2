# discovery/system_discovery/system_physical.py
from Agent.utils.system_discovery_parsers import (
    parse_os_release,
    parse_uname,
    parse_uptime_seconds,
    clean_hostname,
    clean_timezone,
)


def get_physical_system_info(raw_data: dict) -> dict:
    """
    Retorna informações do sistema operacional para hardware físico.

    Parâmetro:
        raw_data (dict): saídas brutas coletadas em system.py
    """
    os_info  = parse_os_release(raw_data.get("os_release") or "")
    uname    = parse_uname(raw_data.get("uname") or "")
    hostname = clean_hostname(raw_data.get("hostname") or "")
    uptime_s = parse_uptime_seconds(raw_data.get("uptime") or "")
    timezone = clean_timezone(raw_data.get("timezone") or "")

    return {
        "hostname": hostname,
        "os": {
            "name":        os_info.get("name"),
            "pretty_name": os_info.get("pretty_name"),
            "id":          os_info.get("id"),           # ubuntu | debian | fedora…
            "id_like":     os_info.get("id_like"),      # ex: "debian" para Ubuntu
            "version":     os_info.get("version"),
            "version_id":  os_info.get("version_id"),
            "codename":    os_info.get("version_codename") or os_info.get("ubuntu_codename"),
            "build_id":    os_info.get("build_id"),
        },
        "kernel": {
            "release": uname.get("kernel_release"),
            "version": uname.get("kernel_version"),
            "machine": uname.get("machine"),
        },
        "timezone":       timezone or None,
        "uptime_seconds": uptime_s,
        "virtualization": {
            "is_virtualized": False,
            "hypervisor":     None,
        },
    }
