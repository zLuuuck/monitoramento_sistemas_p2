from agent.coleta.cpu_coleta.cpu import get_cpu_usage
from agent.coleta.mem_coleta.mem import get_memory_usage
from agent.coleta.disk_coleta.disk import get_disk_usage
from agent.coleta.network_coleta.network import get_network_usage
from agent.coleta.logs_coleta.logs import get_new_auth_log_lines
from agent.coleta.connections_coleta.connections import get_active_connections
from agent.coleta.process_coleta.processes import get_top_processes


def collect_all():
    """
    Agrega métricas de CPU, memória, disco, rede e top processos.
    Logs e conexões são coletados separadamente.
    """
    return {
        "cpu":       get_cpu_usage(),
        "memory":    get_memory_usage(),
        "disk":      get_disk_usage(),
        "network":   get_network_usage(),
        "processes": get_top_processes(),
    }


def collect_auth_logs() -> list[dict]:
    return get_new_auth_log_lines()


def collect_connections() -> dict:
    return get_active_connections()
