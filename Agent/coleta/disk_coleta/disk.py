import psutil

def get_disk_usage():
    """
    Coleta informações de uso do disco principal ('/').

    psutil.disk_usage('/'):
    - total: espaço total
    - used: espaço utilizado
    - percent: percentual de uso

    Retorno:
        dict com dados do disco
    """
    disk = psutil.disk_usage('/')

    return {
        "total": disk.total,
        "used": disk.used,
        "percent": disk.percent
    }