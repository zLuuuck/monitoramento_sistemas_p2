# =============================================================================
# coleta/connections_coleta/connections.py
#
# Coleta conexões TCP ativas e detecta port scans ENTRANTES via tcpdump.
#
# Comportamento:
#   - Thread tcpdump: captura pacotes TCP SYN de origem externa em tempo real.
#   - Thread eval (2s): mantém janela deslizante de 60s e atualiza _active_scans.
#   - get_active_connections(): retorna conexões ativas + estado atual de detecção.
#   - Detecção: >= _PORTSCAN_THRESHOLD portas distintas do mesmo IP em 60s → scan.
#   - Graceful degradation: se tcpdump não estiver instalado ou sem permissão,
#     a detecção é desabilitada silenciosamente (port_scan_detected sempre False).
# =============================================================================

import psutil
import subprocess
import threading
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta

_PORTSCAN_WINDOW    = 60   # janela deslizante em segundos
_PORTSCAN_THRESHOLD = 10   # portas distintas de um mesmo IP → scan detectado
_EVAL_INTERVAL      = 2    # segundos entre avaliações da janela

_lock = threading.Lock()
_syn_window: dict  = defaultdict(list)  # {src_ip: [(datetime, dst_port), ...]}
_active_scans: dict = {}                # {src_ip: distinct_port_count} — atualizado a cada 2s

# Regex para extrair src_ip, src_port, dst_ip, dst_port da saída do tcpdump
_TCPDUMP_RE = re.compile(
    r'(\d{1,3}(?:\.\d{1,3}){3})\.(\d+)\s*>\s*(\d{1,3}(?:\.\d{1,3}){3})\.(\d+):'
)


def _local_ips() -> set:
    """Retorna todos os IPs configurados neste host para filtrar pacotes de saída."""
    ips = {"127.0.0.1", "::1"}
    try:
        for addrs in psutil.net_if_addrs().values():
            for addr in addrs:
                ips.add(addr.address)
    except Exception:
        pass
    return ips


_LOCAL_IPS = _local_ips()


def _thread_tcpdump() -> None:
    """
    Thread daemon: captura pacotes TCP SYN entrantes via tcpdump.

    Filtra apenas pacotes de origem externa (não LOCAL_IPS) para evitar
    contar conexões de saída legítimas do próprio host como port scan.
    """
    import logging as _logging
    _log = _logging.getLogger(__name__)

    # Tenta encontrar tcpdump no PATH e em locais comuns
    tcpdump_bin = "tcpdump"
    for candidate in ("/usr/bin/tcpdump", "/usr/sbin/tcpdump", "/sbin/tcpdump"):
        import os as _os
        if _os.path.isfile(candidate):
            tcpdump_bin = candidate
            break

    try:
        proc = subprocess.Popen(
            [
                tcpdump_bin, "-n", "-l", "-i", "any",
                "tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        _log.info("tcpdump iniciado (pid=%s, bin=%s)", proc.pid, tcpdump_bin)
        _log.info("IPs locais filtrados: %s", _LOCAL_IPS)
        pacotes_capturados = 0
        for line in proc.stdout:
            m = _TCPDUMP_RE.search(line)
            if not m:
                _log.debug("tcpdump linha sem match: %r", line[:120])
                continue
            src_ip   = m.group(1)
            dst_port = int(m.group(4))
            if src_ip in _LOCAL_IPS:
                continue  # pacote de saída deste host — ignora
            pacotes_capturados += 1
            if pacotes_capturados <= 5 or pacotes_capturados % 50 == 0:
                _log.info("SYN capturado #%d: src=%s dst_port=%d", pacotes_capturados, src_ip, dst_port)
            with _lock:
                _syn_window[src_ip].append((datetime.utcnow(), dst_port))
        # tcpdump encerrou — loga stderr para diagnóstico
        stderr_out = proc.stderr.read() if proc.stderr else ''
        _log.warning("tcpdump encerrou (rc=%s): %s", proc.returncode, stderr_out[:200])
    except FileNotFoundError:
        _log.warning("tcpdump não encontrado — detecção de port scan desabilitada")
    except Exception as exc:
        _log.warning("tcpdump thread erro: %s", exc)


def _thread_eval() -> None:
    """
    Thread daemon: a cada 2 segundos, poda a janela deslizante e atualiza _active_scans.

    Um IP entra em _active_scans quando acumulou >= _PORTSCAN_THRESHOLD portas
    distintas na janela de 60s. Sai automaticamente quando a janela expira.
    """
    while True:
        time.sleep(_EVAL_INTERVAL)
        now    = datetime.utcnow()
        cutoff = now - timedelta(seconds=_PORTSCAN_WINDOW)
        with _lock:
            # Poda entradas fora da janela
            for ip in list(_syn_window.keys()):
                _syn_window[ip] = [
                    (ts, p) for ts, p in _syn_window[ip] if ts > cutoff
                ]
                if not _syn_window[ip]:
                    del _syn_window[ip]

            # Atualiza dicionário de scans ativos
            _active_scans.clear()
            for ip, entries in _syn_window.items():
                distinct = len({p for _, p in entries})
                import logging as _l
                _l.getLogger(__name__).debug(
                    "eval: ip=%s entries=%d distinct=%d threshold=%d",
                    ip, len(entries), distinct, _PORTSCAN_THRESHOLD,
                )
                if distinct >= _PORTSCAN_THRESHOLD:
                    _active_scans[ip] = distinct


# Inicia as threads como daemon — encerram junto com o processo principal
threading.Thread(target=_thread_tcpdump, daemon=True, name="tcpdump-capture").start()
threading.Thread(target=_thread_eval,    daemon=True, name="portscan-eval").start()

_TRACKED_STATES = {"ESTABLISHED", "SYN_SENT", "TIME_WAIT", "CLOSE_WAIT"}


def get_active_connections() -> dict:
    """
    Retorna conexões TCP ativas e o estado atual de detecção de port scan.

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
            "total":              int,
            "port_scan_detected": bool,
            "scan_sources":       {src_ip: distinct_port_count, ...}
        }
    """
    try:
        raw = psutil.net_connections(kind="tcp")
    except Exception as e:
        with _lock:
            scans = dict(_active_scans)
        return {
            "connections":        [],
            "total":              0,
            "port_scan_detected": bool(scans),
            "scan_sources":       scans,
            "error":              str(e),
        }

    connections = []
    for conn in raw:
        if conn.status not in _TRACKED_STATES:
            continue
        connections.append({
            "local_port":  conn.laddr.port if conn.laddr else None,
            "remote_ip":   conn.raddr.ip   if conn.raddr else None,
            "remote_port": conn.raddr.port if conn.raddr else None,
            "state":       conn.status,
        })

    with _lock:
        scans = dict(_active_scans)

    return {
        "connections":        connections,
        "total":              len(connections),
        "port_scan_detected": bool(scans),
        "scan_sources":       scans,   # {ip_atacante: qtd_portas_distintas}
    }
