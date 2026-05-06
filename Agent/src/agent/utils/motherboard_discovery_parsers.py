# utils/motherboard_discovery_parsers.py
"""
Parsers para o módulo motherboard_discovery.
Fonte principal: saídas brutas de dmidecode (types 0, 2, 4, 9, 17).
Sem chamadas a shell aqui — apenas transformação de strings.
"""
import re


# ── parser genérico de blocos dmidecode ───────────────────────────────────────

def parse_dmi_blocks(raw: str) -> list[dict]:
    """
    Divide a saída de dmidecode em blocos e parseia cada um em dict.
    Cada bloco começa em 'Handle 0x...' e contém pares 'Campo: valor' indentados.
    """
    if not raw:
        return []

    blocks, current, in_block = [], {}, False

    for line in raw.splitlines():
        if line.startswith("Handle "):
            if current:
                blocks.append(current)
            current, in_block = {}, True
            continue
        if not in_block:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("\t") or (line.startswith("  ") and ":" in line):
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                current[_norm(key)] = value.strip()
        elif ":" not in line and stripped:
            current.setdefault("_type_label", stripped)

    if current:
        blocks.append(current)
    return blocks


def _norm(key: str) -> str:
    """'Socket Designation' → 'socket_designation'"""
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


# ── baseboard — type 2 ────────────────────────────────────────────────────────

def parse_baseboard(raw: str) -> dict:
    """Extrai dados da placa-mãe (dmidecode type 2)."""
    blocks = parse_dmi_blocks(raw)
    for block in blocks:
        if block.get("manufacturer") or block.get("product_name"):
            return block
    return blocks[0] if blocks else {}


# ── BIOS — type 0 ─────────────────────────────────────────────────────────────

def parse_bios(raw: str) -> dict:
    """Extrai dados de BIOS (dmidecode type 0)."""
    blocks = parse_dmi_blocks(raw)
    for block in blocks:
        if block.get("vendor") or block.get("version"):
            return block
    return blocks[0] if blocks else {}


# ── processor sockets — type 4 ────────────────────────────────────────────────

def parse_cpu_sockets(raw: str) -> list[dict]:
    """
    Retorna lista de sockets de CPU (dmidecode type 4).
    Indica se populated (status contém 'Populated') e informações do socket.
    """
    blocks  = parse_dmi_blocks(raw)
    sockets = []
    for block in blocks:
        designation = block.get("socket_designation")
        if not designation:
            continue
        status = block.get("status", "")
        sockets.append({
            "designation":        designation,
            "populated":          "populated" in status.lower(),
            "type":               block.get("type"),
            "upgrade":            block.get("upgrade"),
            "max_speed_mhz":      _safe_mhz(block.get("max_speed")),
            "current_speed_mhz":  _safe_mhz(block.get("current_speed")),
            "manufacturer":       block.get("manufacturer"),
            "version":            block.get("version"),
            "serial":             _clean(block.get("serial_number")),
            "part_number":        _clean(block.get("part_number")),
        })
    return sockets


# ── memory slots summary — type 17 ────────────────────────────────────────────

def parse_memory_slots_summary(raw: str) -> dict:
    """
    Conta total de slots e slots populados (dmidecode type 17).
    Detalhes completos ficam no mem_discovery.
    """
    blocks    = parse_dmi_blocks(raw)
    total     = 0
    populated = 0
    for block in blocks:
        size = block.get("size", "").lower()
        if not size:
            continue
        total += 1
        if re.search(r"\d", size):   # qualquer valor numérico = slot ocupado
            populated += 1
    return {"total": total, "used": populated, "free": total - populated}


# ── expansion slots — type 9 ──────────────────────────────────────────────────

def parse_system_slots(raw: str) -> list[dict]:
    """Retorna lista de slots PCIe/PCI/AGP (dmidecode type 9)."""
    blocks = parse_dmi_blocks(raw)
    slots  = []
    for block in blocks:
        designation = block.get("designation") or block.get("slot_designation")
        slot_type   = block.get("type") or block.get("slot_type")
        if not designation and not slot_type:
            continue
        slots.append({
            "designation":    designation,
            "type":           slot_type,
            "width":          block.get("data_bus_width") or block.get("slot_data_bus_width"),
            "current_usage":  block.get("current_usage"),
        })
    return slots


# ── helpers privados ──────────────────────────────────────────────────────────

def _safe_mhz(value_str: str | None) -> int | None:
    if not value_str:
        return None
    m = re.search(r"(\d+)", value_str)
    return int(m.group(1)) if m else None


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    return None if cleaned.lower() in ("", "not specified", "not provided", "unknown") else cleaned
