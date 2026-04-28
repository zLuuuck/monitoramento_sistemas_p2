# discovery/system.py
from utils.shell import run

def get_system_info():
    return {
        "hostname": run("hostname"),
        "os": run("uname -o"),
        "kernel": run("uname -r")
    }