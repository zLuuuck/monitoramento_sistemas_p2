# discovery/cpu.py
from utils.shell import run
from utils.parser import parse_lscpu, parse_cpuinfo
from utils.sysfs import read_sysfs_khz_to_mhz


def get_cpu_info():
    lscpu_raw = run("lscpu")
    cpuinfo_raw = run("cat /proc/cpuinfo")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    cpuinfo = parse_cpuinfo(cpuinfo_raw) if cpuinfo_raw else []
    cpu0 = cpuinfo[0] if cpuinfo else {}

    # Virtualização
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor_vendor)

    # ------------------------------------------------------------------
    # Frequências com múltiplos fallbacks
    # ------------------------------------------------------------------
    # 1. Máxima (max_mhz)
    max_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq"
        ) or                                          # sysfs (kHz -> MHz)
        safe_float(lscpu.get("cpu_max_mhz")) or        # lscpu "CPU max MHz"
        safe_float(lscpu.get("cpu_mhz"))               # último fallback: "CPU MHz" (comum em VMs)
    )

    # 2. Mínima (min_mhz)
    min_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq"
        ) or
        safe_float(lscpu.get("cpu_min_mhz"))
        # sem fallback genérico: se não houver, fica null (aceitável)
    )

    # 3. Base (base_mhz)
    base_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
        ) or                                          # sysfs base (kHz)
        safe_float(lscpu.get("base_frequency")) or     # raro no lscpu
        # se ainda for None, usar max_mhz como base? (opcional, descomente)
        # max_mhz
        None
    )

    # Se você quiser que base_mhz sempre tenha algum valor útil, descomente a linha acima.
    # Em VMs, a base real é desconhecida, mas max_mhz pode servir como referência.

    # ------------------------------------------------------------------
    # Identificação
    # ------------------------------------------------------------------
    model_name = lscpu.get("model_name") or cpu0.get("model name")
    vendor = lscpu.get("vendor_id") or cpu0.get("vendor_id")
    architecture = lscpu.get("architecture")
    threads_per_core = safe_int(lscpu.get("thread(s)_per_core"))
    cores_logical = safe_int(lscpu.get("cpu(s)")) or len(cpuinfo)

    return {
        "model_name": model_name,
        "vendor": vendor,
        "architecture": architecture,
        "threads_per_core": threads_per_core,
        "cores_logical": cores_logical,
        "frequency": {
            "base_mhz": base_mhz,
            "max_mhz": max_mhz,
            "min_mhz": min_mhz
        },
        "virtualization": {
            "is_virtualized": is_virtualized,
            "hypervisor": hypervisor_vendor if is_virtualized else None
        }
        # "flags": cpu0.get("flags", "").split() if cpu0.get("flags") else []
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