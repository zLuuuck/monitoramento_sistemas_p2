# Agent/src/agent/__main__.py
import sys
import time
import json
from datetime import datetime, timezone

from agent.discovery.cpu_discovery.cpu import get_cpu_info
from agent.discovery.mem_discovery.mem import get_mem_info
from agent.discovery.disk_discovery.disk import get_disk_info
from agent.discovery.system_discovery.system import get_system_info
from agent.discovery.network_discovery.network import get_network_info
from agent.discovery.motherboard_discovery.motherboard import get_motherboard_info
from agent.discovery.tools_discovery.tools import get_tools_info
from agent.global_information.global_information import build_global_information
from agent.coleta.collector import collect_all, collect_auth_logs, collect_connections
from agent.utils.sender import (
    send_discovery,
    send_metrics,
    send_log,
    send_connections,
    send_heartbeat,
    flush_retry_queue,
)
from agent.utils.logger import get_logger, log_payload

logger = get_logger()


def _without_none(value):
    if isinstance(value, dict):
        return {
            key: _without_none(item) for key, item in value.items() if item is not None
        }
    if isinstance(value, list):
        return [_without_none(item) for item in value]
    return value


def _normalize_network(network: dict) -> dict:
    if not isinstance(network, dict):
        return network
    normalized = dict(network)
    normalized["interfaces"] = [
        _without_none(interface) for interface in normalized.get("interfaces", [])
    ]
    return normalized


def run_discovery(force_install: bool = False) -> dict:
    global_info    = build_global_information("discovery")
    is_virtualized = global_info["environment"]["is_virtualized"]

    tools_info = _safe_collect("tools", get_tools_info, is_virtualized, force_install)

    system         = _safe_collect("system", get_system_info, is_virtualized)
    kernel_release = (
        (system.get("kernel") or {}).get("release") if isinstance(system, dict) else ""
    )
    motherboard = _safe_collect("motherboard", get_motherboard_info, is_virtualized)

    return {
        "global":      global_info,
        "system":      system,
        "cpu":         _safe_collect("cpu", get_cpu_info, is_virtualized),
        "memory":      _safe_collect("memory", get_mem_info, is_virtualized),
        "disk":        _safe_collect("disk", get_disk_info, is_virtualized, kernel_release or ""),
        "network":     _normalize_network(_safe_collect("network", get_network_info, is_virtualized)),
        "motherboard": motherboard,
        "tools":       tools_info,
    }


def _safe_collect(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        logger.exception("Erro no discovery de '%s'", name)
        return {"error": f"discovery '{name}' falhou — veja os logs"}


def main():
    force_install = "--install-deps" in sys.argv
    debug_exec    = "--debug-exec" in sys.argv

    logger.info("Monitor Agent iniciado (debug_exec=%s)", debug_exec)

    # =========================================================================
    # DISCOVERY
    # =========================================================================
    try:
        logger.info("Executando discovery...")
        discovery = run_discovery(force_install=force_install)

        logger.info("Enviando discovery...")
        if debug_exec:
            print(json.dumps(discovery, indent=2, default=str))
        else:
            log_payload(logger, "Discovery payload", discovery)
            response = send_discovery(discovery)
            if response and response.get("host_id"):
                discovery["global"]["host_id"] = response["host_id"]

    except Exception:
        logger.exception("Erro no discovery")

    # =========================================================================
    # COLETA CONTÍNUA
    # =========================================================================
    db_host_id = (discovery.get("global") or {}).get("host_id") if "discovery" in locals() else None

    metrics_global              = build_global_information("metrics")
    metrics_global["host_id"]   = db_host_id

    logs_global                 = build_global_information("logs")
    logs_global["host_id"]      = db_host_id

    connections_global              = build_global_information("connections")
    connections_global["host_id"]   = db_host_id

    logger.info("Coleta contínua iniciada...")

    while True:
        # -----------------------------------------------------------------
        # RETRY — reenviar payloads pendentes de ciclos anteriores
        # -----------------------------------------------------------------
        try:
            flush_retry_queue()
        except Exception:
            logger.exception("Erro ao processar fila de retry")

        # -----------------------------------------------------------------
        # HEARTBEAT
        # -----------------------------------------------------------------
        try:
            hb_payload = {
                "type":      "heartbeat",
                "global":    metrics_global,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if debug_exec:
                print(json.dumps(hb_payload, indent=2, default=str))
            else:
                send_heartbeat(hb_payload)
        except Exception:
            logger.exception("Erro ao enviar heartbeat")

        # -----------------------------------------------------------------
        # MÉTRICAS (CPU, memória, disco, rede, top processos)
        # -----------------------------------------------------------------
        try:
            metrics   = collect_all()
            timestamp = datetime.now(timezone.utc).isoformat()
            metrics_payload = {
                "type":      "metrics",
                "global":    metrics_global,
                "timestamp": timestamp,
                "data": {
                    **metrics,
                    "timestamp": timestamp,
                },
            }
            logger.info("Enviando métricas...")
            if debug_exec:
                print(json.dumps(metrics_payload, indent=2, default=str))
            else:
                send_metrics(metrics_payload)
        except Exception:
            logger.exception("Erro na coleta de métricas")

        # -----------------------------------------------------------------
        # LOGS DE AUTENTICAÇÃO (auth.log — uma linha por request)
        # -----------------------------------------------------------------
        try:
            log_lines = collect_auth_logs()
            if log_lines:
                logger.info("Enviando %d linha(s) de auth.log...", len(log_lines))
            for entry in log_lines:
                auth_payload = {
                    "global":    logs_global,
                    "log_type":  "auth",
                    "timestamp": entry["timestamp"],
                    "raw_line":  entry["raw_line"],
                }
                if debug_exec:
                    print(json.dumps(auth_payload, indent=2, default=str))
                else:
                    send_log(auth_payload)
        except Exception:
            logger.exception("Erro na coleta de logs")

        # -----------------------------------------------------------------
        # CONEXÕES TCP (detecção de port scan entrante via tcpdump)
        # -----------------------------------------------------------------
        try:
            conn_data    = collect_connections()
            timestamp    = datetime.now(timezone.utc).isoformat()
            scan_sources = conn_data.get("scan_sources", {})
            conn_payload = {
                "global":             connections_global,
                "timestamp":          timestamp,
                "connections":        conn_data.get("connections", []),
                "total":              conn_data.get("total", 0),
                "port_scan_detected": conn_data.get("port_scan_detected", False),
                "scan_sources":       scan_sources,
            }
            if conn_data.get("port_scan_detected"):
                for ip, port_count in scan_sources.items():
                    logger.warning(
                        "ALERTA: port scan ENTRANTE de %s — %d portas distintas em 60s",
                        ip, port_count,
                    )
            if debug_exec:
                print(json.dumps(conn_payload, indent=2, default=str))
            else:
                send_connections(conn_payload)
        except Exception:
            logger.exception("Erro na coleta de conexoes")

        time.sleep(5)


if __name__ == "__main__":
    main()
