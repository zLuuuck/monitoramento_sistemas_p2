# Importa todas as funções de coleta de cada módulo
from agent.coleta.cpu_coleta.cpu import get_cpu_usage
from agent.coleta.mem_coleta.mem import get_memory_usage
from agent.coleta.disk_coleta.disk import get_disk_usage
from agent.coleta.network_coleta.network import get_network_usage
from agent.coleta.logs_coleta.logs import get_logs


def collect_all():
    """
    Função central que agrega TODAS as coletas.

    Ela chama cada módulo específico e organiza tudo
    em um único dicionário estruturado.

    Retorno:
        dict com todas as métricas e logs
    """

    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "network": get_network_usage(),
        "logs": get_logs()
    }