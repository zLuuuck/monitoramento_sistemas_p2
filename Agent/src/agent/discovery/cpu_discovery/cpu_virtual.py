# discovery/cpu_discovery/cpu_virtual.py
from agent.utils.sysfs import read_sysfs_khz_to_mhz


def get_virtual_cpu_info(lscpu, cpuinfo, cpu0, hypervisor_vendor):
    """
    Retorna informações da CPU para ambiente virtualizado.

    Em VMs, a topologia reflete alocação de vCPUs do hipervisor.
    Campos de frequência incluem 'source' indicando de onde o valor veio.
    Notas contextuais foram centralizadas em metadata.notes no __main__.
    """
    # Frequência máxima com rastreio de origem
    max_mhz, max_source = _resolve_max_mhz(lscpu, cpu0)

    # Mínima
    min_mhz, min_source = _resolve_min_mhz(lscpu)

    # Base
    base_mhz, base_source = _resolve_base_mhz(lscpu)

    # threads_per_core: "1" genérico de VM não é confiável → null
    raw_threads = safe_int(lscpu.get("thread(s)_per_core"))
    threads_per_core = raw_threads if raw_threads and raw_threads > 1 else None

    vcpu_count = safe_int(lscpu.get("cpu(s)")) or len(cpuinfo)

    return {
        "model_name":   lscpu.get("model_name") or cpu0.get("model name"),
        "vendor":       lscpu.get("vendor_id")  or cpu0.get("vendor_id"),
        "architecture": lscpu.get("architecture"),
        "topology": {
            "vcpus":            vcpu_count,
            "threads_per_core": threads_per_core,
            "source":           "lscpu",
        },
        "frequency": {
            "base_mhz":  {"value": base_mhz,  "source": base_source},
            "max_mhz":   {"value": max_mhz,   "source": max_source},
            "min_mhz":   {"value": min_mhz,   "source": min_source},
        },
    }


# ── resolvers de frequência com rastreio de origem ────────────────────────────

def _resolve_max_mhz(lscpu, cpu0):
    v = safe_float(lscpu.get("cpu_max_mhz"))
    if v:
        return v, "lscpu.cpu_max_mhz"
    v = safe_float(lscpu.get("cpu_mhz"))
    if v:
        return v, "lscpu.cpu_mhz"
    v = safe_float(cpu0.get("cpu MHz"))
    if v:
        return v, "proc_cpuinfo.cpu_mhz"
    return None, None


def _resolve_min_mhz(lscpu):
    from agent.utils.sysfs import read_sysfs_khz_to_mhz
    v = read_sysfs_khz_to_mhz(
        "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq"
    )
    if v:
        return v, "sysfs.cpuinfo_min_freq"
    v = safe_float(lscpu.get("cpu_min_mhz"))
    if v:
        return v, "lscpu.cpu_min_mhz"
    return None, None


def _resolve_base_mhz(lscpu):
    from agent.utils.sysfs import read_sysfs_khz_to_mhz
    v = read_sysfs_khz_to_mhz(
        "/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
    )
    if v:
        return v, "sysfs.base_frequency"
    v = safe_float(lscpu.get("base_frequency"))
    if v:
        return v, "lscpu.base_frequency"
    return None, None


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