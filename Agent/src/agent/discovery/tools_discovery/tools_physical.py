# =============================================================================
# discovery/tools_discovery/tools_physical.py
#
# Discovery de ferramentas para hardware físico (bare-metal).
#
# Verifica todas as ferramentas relevantes para coleta em bare-metal,
# incluindo as que requerem root (dmidecode, smartctl).
#
# Ferramentas verificadas:
#   dmidecode  → placa-mãe, RAM, BIOS, sockets de CPU
#   smartctl   → saúde e metadados de disco
#   ethtool    → speed/duplex/driver de interface de rede
#   lspci      → chipset e dispositivos PCIe
#   lsblk      → discos e partições
#   ip         → interfaces de rede e rotas
#   lscpu      → CPU e detecção de virtualização
#   journalctl → logs do sistema (systemd)
#   timedatectl→ fuso horário
# =============================================================================

from agent.discovery.tools_discovery.tools_checker import check_tools

# Ferramentas relevantes para hardware físico
_PHYSICAL_TOOLS = [
    "dmidecode",
    "smartctl",
    "ethtool",
    "lspci",
    "lsblk",
    "ip",
    "lscpu",
    "journalctl",
    "timedatectl",
]


def get_physical_tools_info(force_install: bool = False) -> dict:
    """
    Verifica e, se necessário, instala ferramentas para hardware físico.

    Parâmetros:
        force_install (bool): se True, instala sem perguntar.

    Retorno:
        dict com status de cada ferramenta.
    """
    return check_tools(_PHYSICAL_TOOLS, force_install=force_install)

# =============================================================================
# FIM discovery/tools_discovery/tools_physical.py
# =============================================================================