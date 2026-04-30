from Agent.utils.shell import run_command
from Agent.utils.mem_discovery_parses import parse_lshw_json, parse_dmidecode
from Agent.discovery.mem_discovery.mem_physical import build_physical
from Agent.discovery.mem_discovery.mem_virtual import build_virtual

def is_virtual():
    """Detecta virtualização de forma simples (pode ser importada do cpu.py)."""
    res = run_command("lscpu")
    if res and "hypervisor_vendor" in res:
        return True
    return False

def get_memory_info():
    # Tenta lshw primeiro (precisa de sudo)
    raw_json = run_command("sudo lshw -class memory -json")
    lshw_data = parse_lshw_json(raw_json) if raw_json else None

    # Fallback para dmidecode
    raw_dmi = run_command("sudo dmidecode -t memory")
    dmi_data = parse_dmidecode(raw_dmi) if raw_dmi else None

    # Fallback mínimo: /proc/meminfo
    meminfo = run_command("cat /proc/meminfo")

    virtual = is_virtual()

    if virtual:
        return build_virtual(lshw_data, dmi_data, meminfo)
    else:
        return build_physical(lshw_data, dmi_data, meminfo)