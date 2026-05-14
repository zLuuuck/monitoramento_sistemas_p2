# discovery/system_discovery/system.py
from agent.utils.shell import run
from agent.utils.parser import parse_lscpu
from agent.discovery.system_discovery.system_physical import get_physical_system_info
from agent.discovery.system_discovery.system_virtual import get_virtual_system_info


def get_system_info():
    """
    Ponto de entrada do discovery de sistema operacional.

    Detecta se o host é físico ou virtualizado (mesmo critério de cpu.py/mem.py)
    e delega para o handler adequado.

    Retorna um dict pronto para serialização JSON.
    """
    # ── Coleta comum ──────────────────────────────────────────────────────────
    os_release_raw = run("cat /etc/os-release")
    lscpu_raw      = run("lscpu")
    uname_raw      = run("uname -a")
    hostname_raw   = run("hostname -f")
    uptime_raw     = run("cat /proc/uptime")
    timezone_raw   = run("timedatectl show --property=Timezone --value")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    # ── Detecção de virtualização (mesmo critério do cpu.py) ──────────────────
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized    = bool(hypervisor_vendor)

    raw_data = {
        "os_release": os_release_raw,
        "uname":      uname_raw,
        "hostname":   hostname_raw,
        "uptime":     uptime_raw,
        "timezone":   timezone_raw,
    }

    if is_virtualized:
        return get_virtual_system_info(raw_data, hypervisor_vendor)

    return get_physical_system_info(raw_data)
