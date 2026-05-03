import psutil

def get_network_usage():
    """
    Coleta estatísticas de rede do sistema.

    psutil.net_io_counters():
    - bytes_sent: total de bytes enviados
    - bytes_recv: total de bytes recebidos

    Retorno:
        dict com dados de tráfego de rede
    """
    net = psutil.net_io_counters()

    return {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv
    }