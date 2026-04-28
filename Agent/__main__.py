# main.py
import json
from discovery.cpu import get_cpu_info

if __name__ == "__main__":
    cpu = get_cpu_info()
    print(json.dumps(cpu, indent=4))