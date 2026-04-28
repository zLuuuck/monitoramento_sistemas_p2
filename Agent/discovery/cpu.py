# discovery/cpu.py
from utils.shell import run
from utils.parser import parse_lscpu, parse_cpuinfo

def get_cpu_info():
    # Executa comandos
    lscpu_raw = run("lscpu")
    cpuinfo_raw = run("cat /proc/cpuinfo")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    cpuinfo = parse_cpuinfo(cpuinfo_raw) if cpuinfo_raw else []

    # Primeiro processador lógico (para frequência instantânea e flags)
    cpu0 = cpuinfo[0] if cpuinfo else {}

    # ------------------------------------------------------------------
    # Virtualização
    # lscpu pode conter chave "hypervisor_vendor" (ex.: "VMware", "KVM")
    # Nós a convertemos em boolean e string do hypervisor.
    # ------------------------------------------------------------------
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor_vendor)

    # ------------------------------------------------------------------
    # Frequências (todas em MHz)
    # - current_mhz  → instantânea do /proc/cpuinfo
    # - max_mhz      → do lscpu (CPU max MHz) – driver/BIOS
    # - min_mhz      → do lscpu (CPU min MHz)
    # ------------------------------------------------------------------
    current_mhz = safe_float(cpu0.get("cpu MHz"))
    max_mhz = safe_float(lscpu.get("cpu_max_mhz"))
    min_mhz = safe_float(lscpu.get("cpu_min_mhz"))

    # ------------------------------------------------------------------
    # Modelo, vendor, arquitetura
    # ------------------------------------------------------------------
    model_name = lscpu.get("model_name") or cpu0.get("model name")
    vendor = lscpu.get("vendor_id") or cpu0.get("vendor_id")
    architecture = lscpu.get("architecture")
    threads_per_core = safe_int(lscpu.get("thread(s)_per_core"))
    cores_logical = safe_int(lscpu.get("cpu(s)")) or len(cpuinfo)

    # ------------------------------------------------------------------
    # Montagem do resultado
    # ------------------------------------------------------------------
    return {
        "model_name": model_name,
        "vendor": vendor,
        "architecture": architecture,
        "threads_per_core": threads_per_core,
        "cores_logical": cores_logical,
        "frequency": {
            "current_mhz": current_mhz,
            "max_mhz": max_mhz,
            "min_mhz": min_mhz
        },
        "virtualization": {
            "is_virtualized": is_virtualized,
            "hypervisor": hypervisor_vendor if is_virtualized else None
        },
        #"flags": cpu0.get("flags", "").split() if cpu0.get("flags") else []
    }


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None