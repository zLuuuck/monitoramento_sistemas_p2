import sys
from pathlib import Path

# Adiciona o diretório pai de Agent/ (a raiz do projeto) ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from Agent.discovery.cpu_discovery.cpu import get_cpu_info

if __name__ == "__main__":
    cpu = get_cpu_info()
    print(json.dumps(cpu, indent=4))