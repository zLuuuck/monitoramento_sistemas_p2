# discovery/cpu_discovery/cpu_virtual.py
from Agent.utils.sysfs import read_sysfs_khz_to_mhz


def get_virtual_cpu_info(lscpu, cpuinfo, cpu0, hypervisor_vendor):
    """
    Retorna informações da CPU para ambiente virtualizado.

    Em VMs, a topologia (threads, cores) reflete a alocação de vCPUs feita
    pelo hipervisor — não o hardware físico subjacente. Campos não confiáveis
    são retornados como null com fonte e nota explícitas.
    """
    # Frequência máxima: lscpu (max oficial) → lscpu (MHz atual) → /proc/cpuinfo
    max_mhz = (
        safe_float(lscpu.get("cpu_max_mhz")) or
        safe_float(lscpu.get("cpu_mhz")) or
        safe_float(cpu0.get("cpu MHz"))
    )

    # Mínima — rara em VMs, tenta sysfs depois lscpu
    min_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq"
        ) or
        safe_float(lscpu.get("cpu_min_mhz"))
    )

    # Base — improvável em VM, tenta mesmo assim
    base_mhz = (
        read_sysfs_khz_to_mhz(
            "/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
        ) or
        safe_float(lscpu.get("base_frequency"))
    )

    # threads_per_core: em VMs esse valor reflete a config do hipervisor,
    # não SMT real. Se vier como "1" de forma genérica, não é confiável —
    # retornamos null para não enganar o consumidor da API.
    raw_threads = safe_int(lscpu.get("thread(s)_per_core"))
    threads_per_core = raw_threads if raw_threads and raw_threads > 1 else None

    # cores_logical: número de vCPUs alocadas à VM
    vcpu_count = safe_int(lscpu.get("cpu(s)")) or len(cpuinfo)

    return {
        "model_name": lscpu.get("model_name") or cpu0.get("model name"),
        "vendor": lscpu.get("vendor_id") or cpu0.get("vendor_id"),
        "architecture": lscpu.get("architecture"),
        "topology": {
            "vcpus": vcpu_count,
            "threads_per_core": threads_per_core,
            "source": "virtualized",
            "note": (
                "Values reflect vCPU allocation by the hypervisor, "
                "not the physical CPU topology of the host"
            ),
        },
        "frequency": {
            "base_mhz": base_mhz,
            "max_mhz": max_mhz,
            "min_mhz": min_mhz,
        },
        # bloco virtualization removido — centralizado em environment no __main__
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