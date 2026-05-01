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

# Versão do schema — incrementar quando houver quebra de compatibilidade
SCHEMA_VERSION = "1.0"


def get_environment():
    """
    Detecta o ambiente de execução diretamente via lscpu.
    Retorna bloco centralizado com origem explícita dos dados.
    """
    lscpu_raw = run("lscpu")
    lscpu = parse_lscpu(lscpu_raw) if lscpu_raw else {}

    hypervisor = lscpu.get("hypervisor_vendor")
    is_virtualized = bool(hypervisor)

    return {
        "is_virtualized": is_virtualized,
        "hypervisor":     hypervisor or None,
        "source":         "lscpu",
    }


def build_metadata(is_virtualized):
    """
    Centraliza todas as notas contextuais do payload.
    Substitui os campos 'note' espalhados pelos sub-módulos.
    """
    notes = []

    if is_virtualized:
        notes += [
            "cpu.topology reflects vCPU allocation by the hypervisor, not physical CPU topology",
            "cpu.frequency fields may reflect hypervisor-reported values, not actual hardware clocks",
            "memory values represent allocation to this VM, not total physical RAM of the host",
            "memory.slots is unavailable in virtualized environments",
            "disk.type is reported as 'Virtual' — physical media type is unknown from inside a VM",
            "disk.health (SMART) is unavailable in virtualized environments",
        ]

    return {
        "schema_version": SCHEMA_VERSION,
        "notes": notes,
    }


if __name__ == "__main__":
    env = get_environment()

    payload = {
        "metadata":    build_metadata(env["is_virtualized"]),
        "environment": env,
        "cpu":         get_cpu_info(),
        "memory":      get_mem_info(),
        "disk":        get_disk_info(),
    }
    print(to_json(payload))