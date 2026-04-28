# discovery/memory.py
from utils.shell import run

def get_memory_info():
    free = run("free -h")
    dmi = run("sudo dmidecode -t memory")

    return {
        "free_output": free,
        "dmi_raw": dmi
    }