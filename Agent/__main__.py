# Agent/__main__.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agent.utils.shell import run
from Agent.utils.parser import parse_lscpu
from Agent.discovery.cpu_discovery.cpu import get_cpu_info
from Agent.discovery.mem_discovery.mem import get_mem_info
from Agent.discovery.disk_discovery.disk import get_disk_info
from Agent.utils.serializer import to_json


def get_environment():
    """
    Detecta o ambiente de execução diretamente via lscpu.
    Centraliza a informação de virtualização no topo do payload,
    evitando redundância nos sub-módulos.
    """
    lscpu_raw = run("lscpu")
    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    hypervisor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor)

    return {
        "is_virtualized": is_virtualized,
        "hypervisor": hypervisor or None,
    }


if __name__ == "__main__":
    payload = {
        "environment": get_environment(),
        "cpu":    get_cpu_info(),
        "memory": get_mem_info(),
        "disk":   get_disk_info(),
    }
    print(to_json(payload))