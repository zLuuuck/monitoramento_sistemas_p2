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
from Agent.coleta.collector import collect_all
from Agent.sender import send_data

# Versão do schema (controle de compatibilidade do payload)
SCHEMA_VERSION = "1.0"


def get_environment():
    """
    Detecta se o sistema está virtualizado usando o comando 'lscpu'.

    Retorna:
        - se está virtualizado
        - nome do hypervisor (se existir)
    """

    lscpu_raw = run("lscpu")
    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    hypervisor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor)

    return {
        "is_virtualized": is_virtualized,
        "hypervisor": hypervisor or None,
        "source": "lscpu",
    }


def build_metadata(is_virtualized):
    """
    Cria metadados do payload.

    Inclui observações importantes quando o sistema está virtualizado.
    """

    notes = []

    if is_virtualized:
        notes += [
            "cpu topology may reflect VM",
            "memory is VM allocated",
            "disk is virtual",
        ]

    return {
        "schema_version": SCHEMA_VERSION,
        "notes": notes,
    }


def run_discovery():
    """
    Executa a coleta inicial (discovery).

    Essa coleta ocorre apenas uma vez e define
    a "linha de base" do sistema.
    """

    env = get_environment()

    return {
        "type": "discovery",
        "metadata": build_metadata(env["is_virtualized"]),
        "environment": env,
        "cpu": get_cpu_info(),
        "memory": get_mem_info(),
        "disk": get_disk_info(),
    }


def main():
    print("🚀 Agent iniciado")

    # =========================
    # 🔎 DISCOVERY (uma vez)
    # =========================
    try:
        print("🔍 Executando discovery...")
        discovery = run_discovery()

        print("📤 Enviando discovery...")
        print(json.dumps(discovery, indent=2, default=str))
#        send_data(discovery)

    except Exception as e:
        print("Erro no discovery:", e)

    # =========================
    # 🔄 COLETA CONTÍNUA
    # =========================
    print("📊 Coleta contínua iniciada...")

    while True:
        try:
            # Coleta todas as métricas e logs
            metrics = collect_all()

            # Estrutura do payload enviada ao backend
            payload = {
                "type": "metrics",
                "timestamp": time.time(),  # timestamp atual
                "data": metrics,
            }

            print("📤 Enviando métricas...")
            print(json.dumps(payload, indent=2, default=str))
            #send_data(payload)

        except Exception as e:
            print("Erro na coleta:", e)

        # Intervalo de coleta (5 segundos conforme projeto)
        time.sleep(5)


if __name__ == "__main__":
    main()