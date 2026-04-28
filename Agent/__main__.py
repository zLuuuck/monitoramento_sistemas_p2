from discovery.cpu import get_cpu_info
from discovery.memory import get_memory_info
from discovery.system import get_system_info
import json

def run_discovery():
    return {
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "system": get_system_info()
    }

if __name__ == "__main__":
    data = run_discovery()
    print(json.dumps(data, indent=4))