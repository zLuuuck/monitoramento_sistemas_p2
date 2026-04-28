# discovery/cpu.py
from utils.shell import run
from utils.parser import parse_lscpu, parse_cpuinfo
from utils.sysfs import read_sysfs_khz_to_mhz


def get_cpu_info():
    # Executa comandos
    lscpu_raw = run("lscpu")
    cpuinfo_raw = run("cat /proc/cpuinfo")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    cpuinfo = parse_cpuinfo(cpuinfo_raw) if cpuinfo_raw else []

    # Primeiro processador lógico (para flags opcionais)
    cpu0 = cpuinfo[0] if cpuinfo else {}

    # ------------------------------------------------------------------
    # Virtualização
    # ------------------------------------------------------------------
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor_vendor)

    # ------------------------------------------------------------------
    # Frequências
    # - base_mhz: frequência nominal do hardware (sysfs ou lscpu)
    # - max_mhz : máximo suportado (lscpu)
    # - min_mhz : mínimo suportado (lscpu)
    # ------------------------------------------------------------------
    base_mhz = read_sysfs_khz_to_mhz(
        "/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
    )
    if base_mhz is None:
        # Fallback 1: raro campo 'base_frequency' no lscpu
        base_mhz = safe_float(lscpu.get("base_frequency"))
    # Fallback 2 (opcional): usar max_mhz como base quando não há outra fonte
    # if base_mhz is None:
    #     base_mhz = safe_float(lscpu.get("cpu_max_mhz"))

    max_mhz = safe_float(lscpu.get("cpu_max_mhz"))
    min_mhz = safe_float(lscpu.get("cpu_min_mhz"))

    # ------------------------------------------------------------------
    # Identificação da CPU
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
            "base_mhz": base_mhz,
            "max_mhz": max_mhz,
            "min_mhz": min_mhz
        },
        "virtualization": {
            "is_virtualized": is_virtualized,
            "hypervisor": hypervisor_vendor if is_virtualized else None
        },
        # Inclua flags se desejar:
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