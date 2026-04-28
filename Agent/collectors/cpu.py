# discovery/cpu.py
from utils.shell import run
from utils.parser import parse_key_value

def get_cpu_info():
    output = run("lscpu")

    if not output:
        return {}

    parsed = parse_key_value(output)

    return {
        "model_name": parsed.get("Model name"),
        "architecture": parsed.get("Architecture"),
        "cpu_mhz": parsed.get("CPU MHz"),
        "cpu_max_mhz": parsed.get("CPU max MHz"),
        "cpu_min_mhz": parsed.get("CPU min MHz"),
        "cores": parsed.get("CPU(s)"),
        "vendor": parsed.get("Vendor ID")
    }