import psutil  # Biblioteca que permite acessar informações do sistema operacional

def get_cpu_usage():
    """
    Coleta o uso atual da CPU.

    psutil.cpu_percent(interval=1):
    - Mede o uso da CPU durante 1 segundo
    - Retorna um valor percentual (0 a 100)

    Retorno:
        dict com percentual de uso da CPU
    """
    return {
        "percent": psutil.cpu_percent(interval=1)
    }