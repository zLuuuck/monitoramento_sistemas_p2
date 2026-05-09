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


def get_tools_info(is_virtualized: bool) -> dict:
    """
    Ponto de entrada do discovery de ferramentas.

    Em físico: verifica todas as ferramentas relevantes para bare-metal.
    Em VM: verifica apenas as ferramentas relevantes em ambiente virtualizado
           (omite dmidecode, smartctl, ethtool, lspci — não fazem sentido em VM).

    Parâmetros:
        is_virtualized (bool): recebido do global_information

    Retorno:
        dict com o resultado da verificação de cada ferramenta.
    """
    if is_virtualized:
        return get_virtual_tools_info()

    return get_physical_tools_info()

# =============================================================================
# FIM discovery/tools_discovery/tools.py
# =============================================================================