# =============================================================================
# discovery/cpu_discovery/cpu_virtual.py
#
# Discovery de CPU para ambientes virtualizados.
#
# Em VMs a topologia reflete alocação de vCPUs do hipervisor, não os
# núcleos físicos reais. As frequências têm rastreio de origem (source)
# para indicar de onde o valor foi obtido, pois a confiabilidade varia.
# =============================================================================

from agent.utils.parsers import safe_float, safe_int, read_sysfs_khz_to_mhz


def get_virtual_cpu_info(lscpu: dict, cpuinfo: list, cpu0: dict) -> dict:
    """
    Monta o payload de CPU para ambiente virtualizado.

    Parâmetros:
        lscpu   (dict): saída parseada de `lscpu`
        cpuinfo (list): saída parseada de /proc/cpuinfo
        cpu0    (dict): primeiro núcleo de cpuinfo

    Retorno:
        dict com model_name, vendor, architecture, topology e frequency.
    """
    # ── Topologia ─────────────────────────────────────────────────────────────
    vcpu_count = safe_int(lscpu.get("cpu(s)")) or len(cpuinfo)

    # threads_per_core "1" em VM é genérico e não confiável → retorna None
    raw_threads      = safe_int(lscpu.get("thread(s)_per_core"))
    threads_per_core = raw_threads if raw_threads and raw_threads > 1 else None

    # ── Frequências com rastreio de origem ────────────────────────────────────
    max_mhz,  max_source  = _resolve_max_mhz(lscpu, cpu0)
    min_mhz,  min_source  = _resolve_min_mhz(lscpu)
    base_mhz, base_source = _resolve_base_mhz(lscpu)

    return {
        "model_name":   lscpu.get("model_name") or cpu0.get("model name"),
        "vendor":       lscpu.get("vendor_id")  or cpu0.get("vendor_id"),
        "architecture": lscpu.get("architecture"),
        "topology": {
            # Em VM usamos vcpus (não cores_logical) para deixar claro que
            # são vCPUs alocados, não núcleos físicos
            "vcpus":            vcpu_count,
            "threads_per_core": threads_per_core,
            "source":           "lscpu",
        },
        "frequency": {
            # Inclui "source" para indicar de onde veio cada valor,
            # pois em VMs a confiabilidade das frequências varia
            "base_mhz": {"value": base_mhz, "source": base_source},
            "max_mhz":  {"value": max_mhz,  "source": max_source},
            "min_mhz":  {"value": min_mhz,  "source": min_source},
        },
    }


# =============================================================================
# Resolvers de frequência com rastreio de origem
# =============================================================================

def _resolve_max_mhz(lscpu: dict, cpu0: dict) -> tuple:
    """Resolve a frequência máxima com a melhor fonte disponível."""
    # Prioridade: lscpu.cpu_max_mhz > lscpu.cpu_mhz > /proc/cpuinfo
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


def _resolve_min_mhz(lscpu: dict) -> tuple:
    """Resolve a frequência mínima com a melhor fonte disponível."""
    # Prioridade: sysfs > lscpu
    v = read_sysfs_khz_to_mhz("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq")
    if v:
        return v, "sysfs.cpuinfo_min_freq"
    v = safe_float(lscpu.get("cpu_min_mhz"))
    if v:
        return v, "lscpu.cpu_min_mhz"
    return None, None


def _resolve_base_mhz(lscpu: dict) -> tuple:
    """Resolve a frequência base com a melhor fonte disponível."""
    # Prioridade: sysfs > lscpu
    v = read_sysfs_khz_to_mhz("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency")
    if v:
        return v, "sysfs.base_frequency"
    v = safe_float(lscpu.get("base_frequency"))
    if v:
        return v, "lscpu.base_frequency"
    return None, None

# =============================================================================
# FIM discovery/cpu_discovery/cpu_virtual.py
# =============================================================================