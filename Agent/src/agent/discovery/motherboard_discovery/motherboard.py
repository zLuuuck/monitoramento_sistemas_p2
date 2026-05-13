# discovery/motherboard_discovery/motherboard.py
from agent.utils.shell import run
from agent.discovery.motherboard_discovery.motherboard_physical import get_physical_motherboard_info


def get_motherboard_info(is_virtualized: bool) -> dict | None:
    """
    Ponto de entrada do discovery de placa-mãe.

    Em hardware físico usa dmidecode para extrair modelo, fabricante,
    BIOS, socket(s) de CPU, slots de RAM e slots de expansão.
    Em VMs retorna None, pois a placa-mãe física não é exposta de forma
    confiável pelo hipervisor.

    Retorna um dict pronto para serialização JSON.
    """
    if is_virtualized:
        return None

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

    raw_data = {
        "dmi_bios":     dmi_bios_raw,
        "dmi_board":    dmi_board_raw,
        "dmi_cpu_slot": dmi_cpu_slot_raw,
        "dmi_slots":    dmi_slots_raw,
        "dmi_mem":      dmi_mem_raw,
    }

    return get_physical_motherboard_info(raw_data)
