# utils/parser.py
def parse_lscpu(output):
    data = {}
    current_key = None

    for line in output.splitlines():
        if not line.strip():
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()

            data[key] = value
            current_key = key
        else:
            if current_key:
                data[current_key] += " " + line.strip()

    return data

def parse_cpuinfo(text):
    cpus = []
    current = {}

    for line in text.splitlines():
        line = line.strip()

        if not line:
            if current:
                cpus.append(current)
                current = {}
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()

    if current:
        cpus.append(current)

    return cpus