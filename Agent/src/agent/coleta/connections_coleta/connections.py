# =============================================================================
# coleta/connections_coleta/connections.py
#
# Coleta conexões TCP ativas e detecta possível port scan.
#
# Comportamento:
#   - Usa psutil.net_connections() para listar conexões TCP ativas.
#   - Filtra estados relevantes: ESTABLISHED, SYN_SENT, TIME_WAIT, CLOSE_WAIT.
#   - Detecta port scan quando >= _PORTSCAN_THRESHOLD conexões SYN_SENT
#     apontam para portas distintas.
# =============================================================================

import psutil

_PORTSCAN_THRESHOLD = 10  # SYN_SENT para portas distintas → possível port scan

_TRACKED_STATES = {"ESTABLISHED", "SYN_SENT", "TIME_WAIT", "CLOSE_WAIT"}


def get_active_connections() -> dict:
    """
    Retorna conexões TCP ativas e indicador de port scan.

    Retorno:
        {
            "connections": [
                {
                    "local_port":  int | None,
                    "remote_ip":   str | None,
                    "remote_port": int | None,
                    "state":       str
                },
                ...
            ],
            "total":             int,
            "port_scan_detected": bool,
            "syn_sent_count":    int   # portas distintas em SYN_SENT
        }
    """
    try:
        raw = psutil.net_connections(kind="tcp")
    except Exception as e:
        return {
            "connections": [],
            "total": 0,
            "port_scan_detected": False,
            "syn_sent_count": 0,
            "error": str(e),
        }

    connections = []
    syn_sent_remote_ports = set()

    for conn in raw:
        if conn.status not in _TRACKED_STATES:
            continue

        remote_ip   = conn.raddr.ip   if conn.raddr else None
        remote_port = conn.raddr.port if conn.raddr else None
        local_port  = conn.laddr.port if conn.laddr else None

        connections.append({
            "local_port":  local_port,
            "remote_ip":   remote_ip,
            "remote_port": remote_port,
            "state":       conn.status,
        })

        if conn.status == "SYN_SENT" and remote_port is not None:
            syn_sent_remote_ports.add(remote_port)

    syn_sent_count    = len(syn_sent_remote_ports)
    port_scan_detected = syn_sent_count >= _PORTSCAN_THRESHOLD

    return {
        "connections":        connections,
        "total":              len(connections),
        "port_scan_detected": port_scan_detected,
        "syn_sent_count":     syn_sent_count,
    }
