import time
import psutil

_prev_io = None
_prev_time: float | None = None


def get_disk_usage() -> dict:
    global _prev_io, _prev_time

    disk = psutil.disk_usage("/")
    io = psutil.disk_io_counters()
    now = time.monotonic()

    result = {
        "total":   disk.total,
        "used":    disk.used,
        "percent": disk.percent,
    }

    if _prev_io is not None and io is not None:
        elapsed = now - _prev_time
        if elapsed > 0:
            result["read_iops"]          = round((io.read_count  - _prev_io.read_count)  / elapsed, 2)
            result["write_iops"]         = round((io.write_count - _prev_io.write_count) / elapsed, 2)
            result["read_bytes_per_sec"] = round((io.read_bytes  - _prev_io.read_bytes)  / elapsed, 2)
            result["write_bytes_per_sec"]= round((io.write_bytes - _prev_io.write_bytes) / elapsed, 2)

    _prev_io   = io
    _prev_time = now
    return result
