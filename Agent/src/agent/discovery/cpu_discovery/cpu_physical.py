# discovery/cpu_physical.py
from agent.utils.sysfs import read_sysfs_khz_to_mhz

def get_physical_cpu_info(lscpu, cpuinfo, cpu0):
    """
    Retorna dicionário com informações da CPU para hardware físico.
    Espera receber os dicionários já parseados:
    - lscpu: dict
    - cpuinfo: list
    - cpu0: dict (primeiro processador lógico)
    """
    # Frequência base – sysfs (kHz -> MHz) depois lscpu
    base_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
        ) or
        safe_float(lscpu.get("base_frequency"))
    )

    # Máxima
    max_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq"
        ) or
        safe_float(lscpu.get("cpu_max_mhz"))
    )

    # Mínima
    min_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq"
        ) or
        safe_float(lscpu.get("cpu_min_mhz"))
    )

    return {
        "model_name": lscpu.get("model_name") or cpu0.get("model name"),
        "vendor": lscpu.get("vendor_id") or cpu0.get("vendor_id"),
        "architecture": lscpu.get("architecture"),
        "threads_per_core": safe_int(lscpu.get("thread(s)_per_core")),
        "cores_logical": safe_int(lscpu.get("cpu(s)")) or len(cpuinfo),
        "frequency": {
            "base_mhz": base_mhz,
            "max_mhz": max_mhz,
            "min_mhz": min_mhz
        },
        "virtualization": {
            "is_virtualized": False,
            "hypervisor": None
        }
        # flags opcionais:
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