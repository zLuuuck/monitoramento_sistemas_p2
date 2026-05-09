# Agent/src/agent/__main__.py
import time
import json

from agent.discovery.cpu_discovery.cpu import get_cpu_info
from agent.discovery.mem_discovery.mem import get_mem_info
from agent.discovery.disk_discovery.disk import get_disk_info
from agent.discovery.system_discovery.system import get_system_info
from agent.discovery.network_discovery.network import get_network_info
from agent.discovery.motherboard_discovery.motherboard import get_motherboard_info
from agent.discovery.tools_discovery.tools import get_tools_info
from agent.global_information.global_information import build_global_information
from agent.coleta.collector import collect_all
from agent.utils.sender import send_data


def _without_none(value):
    """
    Remove campos com valor None de estruturas aninhadas.

    Usado apenas onde o contrato pede ausência do campo em vez de null
    (por exemplo, interfaces de rede em VM).
    """
    if isinstance(value, dict):
        return {
            key: _without_none(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [_without_none(item) for item in value]

    return value


def _normalize_network(network: dict) -> dict:
    """Remove campos null apenas da lista de interfaces de rede."""
    if not isinstance(network, dict):
        return network

    normalized = dict(network)
    normalized["interfaces"] = [
        _without_none(interface)
        for interface in normalized.get("interfaces", [])
    ]
    return normalized


def run_discovery() -> dict:
    """
    Executa a coleta inicial (discovery).

    Essa coleta ocorre apenas uma vez e define a 'linha de base' do sistema:
    sistema operacional, hardware (CPU, memória, disco, placa-mãe) e rede.
    """
    global_info = build_global_information("discovery")
    is_virtualized = global_info["environment"]["is_virtualized"]

    system = _safe_collect("system", get_system_info, is_virtualized)
    kernel_release = (system.get("kernel") or {}).get("release") if isinstance(system, dict) else ""
    motherboard = _safe_collect("motherboard", get_motherboard_info, is_virtualized)

    return {
        "global":      global_info,
        "system":      system,
        "cpu":         _safe_collect("cpu", get_cpu_info, is_virtualized),
        "memory":      _safe_collect("memory", get_mem_info, is_virtualized),
        "disk":        _safe_collect("disk", get_disk_info, is_virtualized, kernel_release or ""),
        "network":     _normalize_network(_safe_collect("network", get_network_info, is_virtualized)),
        "motherboard": motherboard,
        "tools":       _safe_collect("tools", get_tools_info, is_virtualized),
    }


def _safe_collect(name: str, fn, *args, **kwargs):
    """
    Executa fn() com tratamento de erro isolado.

    Se um módulo de discovery falhar (ex: dmidecode sem root), o restante
    do payload não é afetado — o campo fica com {"error": "<mensagem>"}.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  Erro no discovery de '{name}': {e}")
        return {"error": str(e)}


def main():
    print("Agent iniciado")

    # =========================================================================
    # DISCOVERY (executa uma vez)
    # =========================================================================
    try:
        print("Executando discovery...")
        discovery = run_discovery()

        print("Enviando discovery...")
        print(json.dumps(discovery, indent=2, default=str))
        # send_data(discovery)

    except Exception as e:
        print(f"Erro no discovery: {e}")

    # =========================================================================
    # COLETA CONTÍNUA
    # =========================================================================
    metrics_global = build_global_information("metrics")

    print("Coleta contínua iniciada...")

    while True:
        try:
            metrics = collect_all()

            payload = {
                "global":    metrics_global,
                "timestamp": time.time(),
                "data":      metrics,
            }

            print("Enviando métricas...")
            print(json.dumps(payload, indent=2, default=str))
            # send_data(payload)

        except Exception as e:
            print(f"Erro na coleta: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()