import psutil

def get_memory_usage():
    """
    Coleta informações de uso de memória RAM.

    psutil.virtual_memory() retorna um objeto com:
    - total: memória total disponível
    - used: memória utilizada
    - percent: percentual de uso

    Retorno:
        dict com dados de memória
    """
    mem = psutil.virtual_memory()

    return {
        "total": mem.total,
        "used": mem.used,
        "percent": mem.percent
    }