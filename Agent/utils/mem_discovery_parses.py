# utils/mem_discovery_parses.py

def parse_meminfo(output):
    """
    Parseia /proc/meminfo e retorna um dict com chaves normalizadas.
    Exemplo de linha: "MemTotal:       16282624 kB"
    """
    data = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        data[key] = value
    return data


def parse_dmidecode_memory(output):
    """
    Parseia a saída de `dmidecode -t memory`.
    Retorna uma lista de dicts, um por bloco de Handle (cada slot/módulo).
    Ignora blocos sem informação útil (ex: "No Module Installed").
    """
    blocks = []
    current = {}
    inside_block = False

    for line in output.splitlines():
        # Início de um novo bloco DMI
        if line.startswith("Handle "):
            if current:
                blocks.append(current)
            current = {}
            inside_block = True
            continue

        if not inside_block:
            continue

        line_stripped = line.strip()
        if not line_stripped:
            continue

        if ":" in line_stripped:
            key, value = line_stripped.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            current[key] = value

    if current:
        blocks.append(current)

    return blocks


def parse_meminfo_kb(value_str):
    """
    Converte string tipo "16282624 kB" para inteiro em kB.
    Retorna None em caso de falha.
    """
    try:
        return int(value_str.split()[0])
    except (AttributeError, IndexError, ValueError):
        return None


def kb_to_gb(kb):
    """Converte kB para GB (float arredondado em 2 casas)."""
    if kb is None:
        return None
    return round(kb / (1024 ** 2), 2)


def kb_to_mb(kb):
    """Converte kB para MB (int)."""
    if kb is None:
        return None
    return round(kb / 1024, 2)


def parse_dmi_size_to_mb(size_str):
    """
    Converte string de tamanho do dmidecode para MB inteiro.
    Exemplos: "8192 MB", "16 GB", "No Module Installed"
    Retorna None se não for possível converter.
    """
    if not size_str or size_str in ("No Module Installed", "Unknown", "Not Installed"):
        return None
    try:
        parts = size_str.split()
        value = int(parts[0])
        unit = parts[1].upper() if len(parts) > 1 else "MB"
        if unit == "GB":
            return value * 1024
        return value  # assume MB
    except (IndexError, ValueError):
        return None