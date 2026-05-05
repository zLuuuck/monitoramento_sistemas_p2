# Agent/__main__.py
import sys
import time
import json
from pathlib import Path

# Ajusta o path para permitir imports absolutos (Agent.*)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agent.utils.shell import run
from Agent.utils.parser import parse_lscpu
from Agent.discovery.cpu_discovery.cpu import get_cpu_info
from Agent.discovery.mem_discovery.mem import get_mem_info
from Agent.discovery.disk_discovery.disk import get_disk_info
from Agent.discovery.system_discovery.system import get_system_info
from Agent.discovery.network_discovery.network import get_network_info
from Agent.discovery.motherboard_discovery.motherboard import get_motherboard_info
from Agent.coleta.collector import collect_all
from Agent.sender import send_data

# Versão do schema (controle de compatibilidade do payload)
SCHEMA_VERSION = "1.0"


def get_environment():
    """
    Detecta se o sistema está virtualizado usando o comando 'lscpu'.

    Retorna dict com is_virtualized, hypervisor e source.
    """
    lscpu_raw      = run("lscpu")
    lscpu          = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    hypervisor     = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor)

    return {
        "is_virtualized": is_virtualized,
        "hypervisor":     hypervisor or None,
        "source":         "lscpu",
    }


def build_metadata(is_virtualized: bool) -> dict:
    """
    Cria metadados do payload.

    Inclui observações importantes quando o sistema está virtualizado.
    """
    notes = []

    if is_virtualized:
        notes += [
            "cpu topology may reflect VM allocation, not physical cores",
            "memory slots unavailable in virtualized environments",
            "disk is virtual — smartctl data unavailable",
            "network hardware fields (speed, driver, bus_info) unavailable in VM",
            "motherboard chipset and expansion slots unavailable in VM",
        ]

    return {
        "schema_version": SCHEMA_VERSION,
        "notes":          notes,
    }


def run_discovery() -> dict:
    """
    Executa a coleta inicial (discovery).

    Essa coleta ocorre apenas uma vez e define a 'linha de base' do sistema:
    sistema operacional, hardware (CPU, memória, disco, placa-mãe) e rede.
    """
    env = get_environment()

    return {
        "type":        "discovery",
        "metadata":    build_metadata(env["is_virtualized"]),
        "environment": env,
        "system":      _safe_collect("system",      get_system_info),
        "cpu":         _safe_collect("cpu",          get_cpu_info),
        "memory":      _safe_collect("memory",       get_mem_info),
        "disk":        _safe_collect("disk",         get_disk_info),
        "network":     _safe_collect("network",      get_network_info),
        "motherboard": _safe_collect("motherboard",  get_motherboard_info),
    }


def _safe_collect(name: str, fn) -> dict:
    """
    Executa fn() com tratamento de erro isolado.

    Se um módulo de discovery falhar (ex: dmidecode sem root), o restante
    do payload não é afetado — o campo fica com {"error": "<mensagem>"}.
    """
    try:
        return fn()
    except Exception as e:
        print(f"  ⚠️  Erro no discovery de '{name}': {e}")
        return {"error": str(e)}


def main():
    print("🚀 Agent iniciado")

    # =========================================================================
    # 🔎 DISCOVERY (executa uma vez)
    # =========================================================================
    try:
        print("🔍 Executando discovery...")
        discovery = run_discovery()

        print("📤 Enviando discovery...")
        print(json.dumps(discovery, indent=2, default=str))
        # send_data(discovery)

    except Exception as e:
        print(f"❌ Erro no discovery: {e}")

    # =========================================================================
    # 🔄 COLETA CONTÍNUA
    # =========================================================================
    print("📊 Coleta contínua iniciada...")

    while True:
        try:
            metrics = collect_all()

            payload = {
                "type":      "metrics",
                "timestamp": time.time(),
                "data":      metrics,
            }

            print("📤 Enviando métricas...")
            print(json.dumps(payload, indent=2, default=str))
            # send_data(payload)

        except Exception as e:
            print(f"❌ Erro na coleta: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()