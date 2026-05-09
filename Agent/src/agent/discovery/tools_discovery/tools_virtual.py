# =============================================================================
# discovery/tools_discovery/tools_virtual.py
#
# Discovery de ferramentas para ambientes virtualizados.
#
# Em VMs, ferramentas de hardware físico (dmidecode, smartctl, ethtool,
# lspci) não fazem sentido — o hipervisor não expõe esses recursos de
# forma confiável. São omitidas para não poluir o payload com dados
# irrelevantes para o ambiente.
#
# Ferramentas verificadas em VM:
#   lsblk      → discos virtuais e partições
#   ip         → interfaces de rede virtuais e rotas
#   lscpu      → CPU (vCPUs alocados pelo hipervisor)
#   journalctl → logs do sistema (systemd)
#   timedatectl→ fuso horário
# =============================================================================

from agent.discovery.tools_discovery.tools_checker import check_tools

# Ferramentas relevantes para ambientes virtualizados.
# Ferramentas de hardware físico (dmidecode, smartctl, ethtool, lspci)
# são omitidas — não fazem sentido em VM.
_VIRTUAL_TOOLS = [
    "lsblk",
    "ip",
    "lscpu",
    "journalctl",
    "timedatectl",
]


def get_virtual_tools_info(force_install: bool = False) -> dict:
    """
    Verifica e, se necessário, instala ferramentas para ambiente virtualizado.

    Parâmetros:
        force_install (bool): se True, instala sem perguntar.

    Retorno:
        dict com status de cada ferramenta.
    """
    return check_tools(_VIRTUAL_TOOLS, force_install=force_install)

# =============================================================================
# FIM discovery/tools_discovery/tools_virtual.py
# =============================================================================