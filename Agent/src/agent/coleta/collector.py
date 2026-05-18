# Importa todas as funções de coleta de cada módulo
from agent.coleta.cpu_coleta.cpu import get_cpu_usage
from agent.coleta.mem_coleta.mem import get_memory_usage
from agent.coleta.disk_coleta.disk import get_disk_usage
from agent.coleta.network_coleta.network import get_network_usage
from agent.coleta.logs_coleta.logs import get_new_auth_log_lines


def collect_all():
    """
    Agrega métricas de CPU, memória, disco e rede.
    Logs são coletados separadamente via collect_auth_logs().
    """
    return {
        "cpu":     get_cpu_usage(),
        "memory":  get_memory_usage(),
        "disk":    get_disk_usage(),
        "network": get_network_usage(),
    }


def collect_auth_logs() -> list[dict]:
    """
    Retorna as novas linhas de /var/log/auth.log desde o último envio.
    Cada entrada: {"timestamp": "...", "raw_line": "..."}
    """
    return get_new_auth_log_lines()