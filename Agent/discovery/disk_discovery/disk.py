# discovery/disk_discovery/disk.py
from Agent.utils.shell import run
from Agent.utils.parser import parse_lscpu
from Agent.discovery.disk_discovery.disk_physical import get_physical_disk_info
from Agent.discovery.disk_discovery.disk_virtual import get_virtual_disk_info

# Campos solicitados ao lsblk via JSON
# NAME, SIZE (bytes), TYPE, ROTA (rotacional?), MOUNTPOINT,
# MODEL, VENDOR, SERIAL, TRAN (interface), RM (removível)
_LSBLK_CMD = (
    "lsblk -J -b -o NAME,SIZE,TYPE,ROTA,MOUNTPOINT,MODEL,VENDOR,SERIAL,TRAN,RM"
)


def get_disk_info():
    """
    Ponto de entrada do discovery de discos.

    Detecta se o host é físico ou virtualizado (mesmo critério de cpu.py/mem.py)
    e delega para o handler adequado.

    Retorna um dict pronto para serialização JSON.
    """
    # ── Coleta comum ──────────────────────────────────────────────────────────
    lsblk_raw = run(_LSBLK_CMD)
    lscpu_raw = run("lscpu")
    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    # ── Detecção de virtualização (mesmo critério do cpu.py) ──────────────────
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor_vendor)

    if is_virtualized:
        return get_virtual_disk_info(lsblk_raw, hypervisor_vendor)

    return get_physical_disk_info(lsblk_raw)