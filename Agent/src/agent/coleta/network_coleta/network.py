import time
import psutil

_prev_net = None
_prev_time: float | None = None


def get_network_usage() -> dict:
    global _prev_net, _prev_time

    net = psutil.net_io_counters()
    now = time.monotonic()

    result = {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
    }

    if _prev_net is not None:
        elapsed = now - _prev_time
        if elapsed > 0:
            result["bytes_sent_per_sec"] = round((net.bytes_sent - _prev_net.bytes_sent) / elapsed, 2)
            result["bytes_recv_per_sec"] = round((net.bytes_recv - _prev_net.bytes_recv) / elapsed, 2)

    _prev_net  = net
    _prev_time = now
    return result
