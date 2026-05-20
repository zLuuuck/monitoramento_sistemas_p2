# Agent/src/agent/__main__.py
import sys          # <-- ADICIONADO
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
from agent.utils.sender import send_discovery, send_metrics, send_log, send_connections


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


def run_discovery(force_install: bool = False) -> dict:   # <-- ADICIONADO PARÂMETRO
    """
    Executa a coleta inicial (discovery).
    """
    global_info = build_global_information("discovery")
    is_virtualized = global_info["environment"]["is_virtualized"]

    # Tools primeiro, para instalar dependências se necessário
    tools_info = _safe_collect("tools", get_tools_info, is_virtualized, force_install)

    system = _safe_collect("system", get_system_info, is_virtualized)
    kernel_release = (
        (system.get("kernel") or {}).get("release") if isinstance(system, dict) else ""
    )
    motherboard = _safe_collect("motherboard", get_motherboard_info, is_virtualized)

    return {
        "global": global_info,
        "system": system,
        "cpu": _safe_collect("cpu", get_cpu_info, is_virtualized),
        "memory": _safe_collect("memory", get_mem_info, is_virtualized),
        "disk": _safe_collect(
            "disk", get_disk_info, is_virtualized, kernel_release or ""
        ),
        "network": _normalize_network(
            _safe_collect("network", get_network_info, is_virtualized)
        ),
        "motherboard": motherboard,
        "tools": tools_info,
    }


def _safe_collect(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  Erro no discovery de '{name}': {e}")
        return {"error": str(e)}


def main():
    force_install = "--install-deps" in sys.argv
    dry_run = "--dry-run" in sys.argv

    print("Agent iniciado")

    # =========================================================================
    # DISCOVERY
    # =========================================================================
    try:
        print("Executando discovery...")
        discovery = run_discovery(force_install=force_install)   # <-- PASSA O ARGUMENTO

        print("Enviando discovery...")
        if dry_run:
            print(json.dumps(discovery, indent=2, default=str))
        else:
            response = send_discovery(discovery)
            if response and response.get("host_id"):
                discovery["global"]["host_id"] = response["host_id"]

    except Exception as e:
        print(f"Erro no discovery: {e}")

    # =========================================================================
    # COLETA CONTÍNUA
    # =========================================================================
    db_host_id = (discovery.get("global") or {}).get("host_id") if "discovery" in locals() else None

    metrics_global = build_global_information("metrics")
    metrics_global["host_id"] = db_host_id

    logs_global = build_global_information("logs")
    logs_global["host_id"] = db_host_id

    connections_global = build_global_information("connections")
    connections_global["host_id"] = db_host_id

    print("Coleta contínua iniciada...")

    while True:
        # -----------------------------------------------------------------
        # MÉTRICAS (CPU, memória, disco, rede)
        # -----------------------------------------------------------------
        try:
            metrics   = collect_all()
            timestamp = datetime.now(timezone.utc).isoformat()
            payload   = {
                "type":      "metrics",
                "global":    metrics_global,
                "timestamp": timestamp,
                "data": {
                    **metrics,
                    "timestamp": timestamp,
                },
            }
            print("Enviando métricas...")
            if dry_run:
                print(json.dumps(payload, indent=2, default=str))
            else:
                send_metrics(payload)
        except Exception as e:
            print(f"Erro na coleta de métricas: {e}")

        # -----------------------------------------------------------------
        # LOGS DE AUTENTICAÇÃO (auth.log — uma linha por request)
        # -----------------------------------------------------------------
        try:
            log_lines = collect_auth_logs()
            if log_lines:
                print(f"Enviando {len(log_lines)} linha(s) de auth.log...")
            for entry in log_lines:
                log_payload = {
                    "global":    logs_global,
                    "log_type":  "auth",
                    "timestamp": entry["timestamp"],
                    "raw_line":  entry["raw_line"],
                }
                if dry_run:
                    print(json.dumps(log_payload, indent=2, default=str))
                else:
                    send_log(log_payload)
        except Exception as e:
            print(f"Erro na coleta de logs: {e}")

        # -----------------------------------------------------------------
        # CONEXÕES TCP (detecção de port scan)
        # -----------------------------------------------------------------
        try:
            conn_data  = collect_connections()
            timestamp  = datetime.now(timezone.utc).isoformat()
            conn_payload = {
                "global":             connections_global,
                "timestamp":          timestamp,
                "connections":        conn_data.get("connections", []),
                "total":              conn_data.get("total", 0),
                "port_scan_detected": conn_data.get("port_scan_detected", False),
                "syn_sent_count":     conn_data.get("syn_sent_count", 0),
            }
            if conn_data.get("port_scan_detected"):
                print(f"ALERTA: possível port scan detectado — {conn_data['syn_sent_count']} portas SYN_SENT distintas")
            if dry_run:
                print(json.dumps(conn_payload, indent=2, default=str))
            else:
                send_connections(conn_payload)
        except Exception as e:
            print(f"Erro na coleta de conexões: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()
