# discovery/cpu.py
from Agent.utils.shell import run
from Agent.utils.parser import parse_lscpu, parse_cpuinfo
from Agent.discovery.cpu_discovery.cpu_physical import get_physical_cpu_info
from Agent.discovery.cpu_discovery.cpu_virtual import get_virtual_cpu_info

def get_cpu_info():
    # Coleta comum
    lscpu_raw = run("lscpu")
    cpuinfo_raw = run("cat /proc/cpuinfo")
    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    cpuinfo = parse_cpuinfo(cpuinfo_raw) if cpuinfo_raw else []
    cpu0 = cpuinfo[0] if cpuinfo else {}

    # Detecção de virtualização
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor_vendor)

    if is_virtualized:
        return get_virtual_cpu_info(lscpu, cpuinfo, cpu0, hypervisor_vendor)
    else:
        return get_physical_cpu_info(lscpu, cpuinfo, cpu0)