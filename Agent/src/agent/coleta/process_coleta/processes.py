import psutil


def get_top_processes(n: int = 15) -> dict:
    """
    Retorna os top N processos por CPU, memória RAM, disco (I/O acumulado)
    e rede (número de conexões abertas — proxy para atividade de rede,
    já que psutil não expõe bytes de rede por processo sem leitura de /proc).
    """
    procs = []
    for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_info", "io_counters"]):
        try:
            info = p.info
            mem  = info.get("memory_info")
            io   = info.get("io_counters")

            try:
                conns = len(p.connections())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                conns = 0

            procs.append({
                "pid":              info["pid"],
                "name":             info.get("name") or "",
                "username":         info.get("username") or "",
                "cpu_percent":      info.get("cpu_percent") or 0.0,
                "memory_rss":       mem.rss if mem else 0,
                "disk_bytes":       (io.read_bytes + io.write_bytes) if io else 0,
                "open_connections": conns,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    def _top(key: str) -> list:
        return sorted(procs, key=lambda x: x[key], reverse=True)[:n]

    return {
        "top_cpu":     _top("cpu_percent"),
        "top_memory":  _top("memory_rss"),
        "top_disk":    _top("disk_bytes"),
        "top_network": _top("open_connections"),
    }
