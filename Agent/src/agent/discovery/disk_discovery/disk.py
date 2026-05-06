# discovery/disk_discovery/disk.py
from agent.utils.shell import run
from agent.utils.parser import parse_lscpu
from agent.discovery.disk_discovery.disk_physical import get_physical_disk_info
from agent.discovery.disk_discovery.disk_virtual import get_virtual_disk_info

# Campos solicitados ao lsblk via JSON
# NAME      → nome do device (sda, sda1, nvme0n1…)
# SIZE      → tamanho em bytes (-b)
# TYPE      → disk | part | lvm | md | loop | crypt
# ROTA      → 1=rotacional (HDD), 0=SSD
# MOUNTPOINT→ ponto de montagem atual
# FSTYPE    → filesystem (ext4, xfs, swap, vfat…)
# LABEL     → label da partição
# UUID      → UUID do filesystem
# MODEL     → modelo (discos raiz)
# VENDOR    → fabricante (discos raiz)
# SERIAL    → número de série (discos raiz)
# TRAN      → interface (sata, nvme, usb…)
# RM        → 1=removível
_LSBLK_CMD = (
    "lsblk -J -b "
    "-o NAME,SIZE,TYPE,ROTA,MOUNTPOINT,FSTYPE,LABEL,UUID,MODEL,VENDOR,SERIAL,TRAN,RM"
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
    lscpu     = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    # ── Detecção de virtualização (mesmo critério do cpu.py) ──────────────────
    hypervisor_vendor = lscpu.get("hypervisor_vendor")
    is_virtualized    = bool(hypervisor_vendor)

    if is_virtualized:
        return get_virtual_disk_info(lsblk_raw, hypervisor_vendor)

    return get_physical_disk_info(lsblk_raw)
