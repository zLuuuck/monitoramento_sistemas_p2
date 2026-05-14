# =============================================================================
# discovery/disk_discovery/disk.py
#
# Discovery de discos — ponto de entrada do módulo.
#
# Coleta os dados brutos via lsblk e delega para o handler correto
# com base no ambiente recebido do global_information.
#
# Campos solicitados ao lsblk via JSON (-J -b):
#   NAME       → nome do device (sda, nvme0n1…)
#   SIZE       → tamanho em bytes
#   TYPE       → disk | part | lvm | md | loop | crypt
#   ROTA       → 1=rotacional (HDD), 0=SSD
#   MOUNTPOINT → ponto de montagem atual
#   FSTYPE     → filesystem (ext4, xfs, swap, vfat…)
#   LABEL      → label da partição
#   UUID       → UUID do filesystem
#   MODEL      → modelo do disco
#   VENDOR     → fabricante
#   SERIAL     → número de série
#   TRAN       → interface (sata, nvme, usb…)
#   RM         → 1=removível
# =============================================================================

from agent.utils.shell import run
from agent.discovery.disk_discovery.disk_physical import get_physical_disk_info
from agent.discovery.disk_discovery.disk_virtual import get_virtual_disk_info

_LSBLK_CMD = (
    "lsblk -J -b "
    "-o NAME,SIZE,TYPE,ROTA,MOUNTPOINT,FSTYPE,LABEL,UUID,MODEL,VENDOR,SERIAL,TRAN,RM"
)


def get_disk_info(is_virtualized: bool, kernel_release: str = "") -> dict:
    """
    Ponto de entrada do discovery de discos.

    Parâmetros:
        is_virtualized (bool): recebido do global_information
        kernel_release (str):  usado para detectar WSL2 e ajustar coleta

    Retorno:
        dict com total_disks e lista de discos.
    """
    # ── Coleta bruta ──────────────────────────────────────────────────────────
    lsblk_raw = run(_LSBLK_CMD)

    # ── Despacho ─────────────────────────────────────────────────────────────
    if is_virtualized:
        return get_virtual_disk_info(lsblk_raw, kernel_release)

    return get_physical_disk_info(lsblk_raw)

# =============================================================================
# FIM discovery/disk_discovery/disk.py
# =============================================================================