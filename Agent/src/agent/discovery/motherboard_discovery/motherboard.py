# discovery/motherboard_discovery/motherboard.py
from agent.utils.shell import run
from agent.utils.parser import parse_lscpu
from agent.discovery.motherboard_discovery.motherboard_physical import get_physical_motherboard_info
from agent.discovery.motherboard_discovery.motherboard_virtual import get_virtual_motherboard_info


def get_motherboard_info():
    """
    Ponto de entrada do discovery de placa-mãe.

    Em hardware físico usa dmidecode para extrair modelo, fabricante,
    BIOS, socket(s) de CPU, slots de RAM e slots de expansão.
    Em VMs retorna apenas os dados expostos pelo hipervisor via dmidecode.

    Retorna um dict pronto para serialização JSON.
    """
    # ── Coleta common ─────────────────────────────────────────────────────────
    # type 0  → BIOS
    # type 2  → Baseboard (placa-mãe)
    # type 4  → Processor sockets
    # type 9  → System / PCIe slots
    # type 17 → Memory devices (slots de RAM — apenas contagem aqui)
    dmi_bios_raw     = run("dmidecode -t 0")
    dmi_board_raw    = run("dmidecode -t 2")
    dmi_cpu_slot_raw = run("dmidecode -t 4")
    dmi_slots_raw    = run("dmidecode -t 9")
    dmi_mem_raw      = run("dmidecode -t 17")
    lscpu_raw        = run("lscpu")

    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    # ── Detecção de virtualização ─────────────────────────────────────────────
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized    = bool(hypervisor_vendor)

    raw_data = {
        "dmi_bios":     dmi_bios_raw,
        "dmi_board":    dmi_board_raw,
        "dmi_cpu_slot": dmi_cpu_slot_raw,
        "dmi_slots":    dmi_slots_raw,
        "dmi_mem":      dmi_mem_raw,
    }

    if is_virtualized:
        return get_virtual_motherboard_info(raw_data, hypervisor_vendor)

    return get_physical_motherboard_info(raw_data)
