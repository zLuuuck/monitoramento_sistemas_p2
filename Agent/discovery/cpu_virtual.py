# discovery/cpu_virtual.py
from utils.sysfs import read_sysfs_khz_to_mhz

def get_virtual_cpu_info(lscpu, cpuinfo, cpu0, hypervisor_vendor):
    """
    Retorna dicionário com informações da CPU para ambiente virtualizado.
    hypervisor_vendor: string com o nome do hypervisor (ex: "VMware").
    """
    # Máxima – comum vir de "CPU MHz" fixo em VMs
    max_mhz = (
        safe_float(lscpu.get("cpu_max_mhz")) or
        safe_float(lscpu.get("cpu_mhz"))  # fallback: campo "CPU MHz" do lscpu
    )

    # Mínima – rara em VMs, mas tenta
    min_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq"
        ) or
        safe_float(lscpu.get("cpu_min_mhz"))
    )

    # Base – improvável, mas tenta
    base_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
        ) or
        safe_float(lscpu.get("base_frequency"))
        # se desejar, pode usar max_mhz como base se for None
        # or max_mhz
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
            "is_virtualized": True,
            "hypervisor": hypervisor_vendor
        }
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