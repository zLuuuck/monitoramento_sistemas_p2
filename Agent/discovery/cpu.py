# discovery/cpu.py
from utils.shell import run
from utils.parser import parse_lscpu, parse_cpuinfo

def get_cpu_info():
    lscpu_raw = run("lscpu")
    cpuinfo_raw = run("cat /proc/cpuinfo")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    cpuinfo = parse_cpuinfo(cpuinfo_raw) if cpuinfo_raw else []

    cpu0 = cpuinfo[0] if cpuinfo else {}

    return {
        "model_name": lscpu.get("model_name") or cpu0.get("model name"),
        "vendor": lscpu.get("vendor_id") or cpu0.get("vendor_id"),
        "architecture": lscpu.get("architecture"),
        "cores_logical": len(cpuinfo) if cpuinfo else lscpu.get("cpu(s)"),
        "threads_per_core": lscpu.get("thread(s)_per_core"),
        "frequency_mhz": safe_float(cpu0.get("cpu MHz")),
        "hypervisor": lscpu.get("hypervisor_vendor"),
        "flags": cpu0.get("flags")
    }


def safe_float(value):
    try:
        return float(value)
    except:
        return None