# =============================================================================
# discovery/tools_discovery/tools.py
#
# Discovery de ferramentas do sistema — ponto de entrada do módulo.
#
# Verifica quais ferramentas externas estão disponíveis no host,
# permitindo ao backend entender por que certos campos do discovery
# vieram null: pode ser VM, falta de root, ou ferramenta não instalada.
#
# Não detecta virtualização aqui — recebe o ambiente já resolvido
# via parâmetro (detectado uma única vez no global_information).
# =============================================================================

from agent.discovery.tools_discovery.tools_physical import get_physical_tools_info
from agent.discovery.tools_discovery.tools_virtual  import get_virtual_tools_info


def get_tools_info(is_virtualized: bool, force_install: bool = False) -> dict:
    """
    Ponto de entrada do discovery de ferramentas.

    Parâmetros:
        is_virtualized (bool): True se VM.
        force_install (bool): instala sem prompt (ex: flag --install-deps).

    Retorno:
        dict com resultado da verificação/instalação.
    """
    if is_virtualized:
        return get_virtual_tools_info(force_install=force_install)

    return get_physical_tools_info(force_install=force_install)

# =============================================================================
# FIM discovery/tools_discovery/tools.py
# =============================================================================