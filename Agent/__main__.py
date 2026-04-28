# main.py
import json
from Agent.discovery.cpu.cpu import get_cpu_info

if __name__ == "__main__":
    cpu = get_cpu_info()
    print(json.dumps(cpu, indent=4))