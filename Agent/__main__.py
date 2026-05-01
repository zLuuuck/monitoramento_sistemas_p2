# Agent/__main__.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from Agent.discovery.cpu_discovery.cpu import get_cpu_info
from Agent.discovery.mem_discovery.mem import get_mem_info
from Agent.discovery.disk_discovery.disk import get_disk_info
from Agent.utils.serializer import to_json

if __name__ == "__main__":
    cpu  = get_cpu_info()
    mem  = get_mem_info()
    disk = get_disk_info()

    # Bloco de ambiente centralizado — extraído de qualquer um dos módulos
    # (todos detectam via lscpu, resultado é idêntico)
    environment = (
        cpu.pop("virtualization", None)
        or mem.pop("virtualization", None)
        or disk.pop("virtualization", None)
    )

    # Remove bloco redundante dos demais caso ainda exista
    for block in (cpu, mem, disk):
        block.pop("virtualization", None)

    payload = {
        "environment": environment,
        "cpu": cpu,
        "memory": mem,
        "disk": disk,
    }
    print(to_json(payload))