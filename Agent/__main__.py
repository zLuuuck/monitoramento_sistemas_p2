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
    payload = {
        "cpu": get_cpu_info(),
        "memory": get_mem_info(),
        "disk": get_disk_info(),
    }
    print(to_json(payload))