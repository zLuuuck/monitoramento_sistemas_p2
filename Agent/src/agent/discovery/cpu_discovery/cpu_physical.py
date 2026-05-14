# =============================================================================
# discovery/cpu_discovery/cpu_physical.py
#
# Discovery de CPU para hardware físico (bare-metal).
#
# Em hardware físico temos acesso ao sysfs para frequências precisas.
# Não há campo "virtualization" no payload — esse contexto está em global.
# =============================================================================

from agent.utils.parsers import safe_float, safe_int, read_sysfs_khz_to_mhz


def get_physical_cpu_info(lscpu: dict, cpuinfo: list, cpu0: dict) -> dict:
    """
    Monta o payload de CPU para hardware físico.

    Parâmetros:
        lscpu   (dict): saída parseada de `lscpu`
        cpuinfo (list): saída parseada de /proc/cpuinfo (lista por núcleo)
        cpu0    (dict): primeiro núcleo de cpuinfo (usado como fallback)

    Retorno:
        dict com model_name, vendor, architecture, topology e frequency.
    """
    # ── Frequências — sysfs (kHz→MHz) tem prioridade sobre lscpu ─────────────
    base_mhz = (
        read_sysfs_khz_to_mhz("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency")
        or safe_float(lscpu.get("base_frequency"))
    )
    max_mhz = (
        read_sysfs_khz_to_mhz("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
        or safe_float(lscpu.get("cpu_max_mhz"))
    )
    min_mhz = (
        read_sysfs_khz_to_mhz("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq")
        or safe_float(lscpu.get("cpu_min_mhz"))
    )

    return {
        "model_name":   lscpu.get("model_name") or cpu0.get("model name"),
        "vendor":       lscpu.get("vendor_id")  or cpu0.get("vendor_id"),
        "architecture": lscpu.get("architecture"),
        "topology": {
            # Em físico usamos cores_logical (total de threads visíveis pelo OS)
            "cores_logical":   safe_int(lscpu.get("cpu(s)")) or len(cpuinfo),
            "threads_per_core": safe_int(lscpu.get("thread(s)_per_core")),
            "source":          "lscpu",
        },
        "frequency": {
            "base_mhz": base_mhz,
            "max_mhz":  max_mhz,
            "min_mhz":  min_mhz,
        },
    }

# =============================================================================
# FIM discovery/cpu_discovery/cpu_physical.py
# =============================================================================