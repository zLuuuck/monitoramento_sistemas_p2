# utils/system_discovery_parsers.py
"""
Parsers para o módulo system_discovery.
Fontes: /etc/os-release, uname -a, /proc/uptime, hostname -f, timedatectl.
Sem chamadas a shell aqui — apenas transformação de strings brutas.
"""
import re


# ── /etc/os-release ───────────────────────────────────────────────────────────

def parse_os_release(raw: str) -> dict:
    """
    Parseia /etc/os-release em dict com chaves lowercase.

    Exemplo de entrada:
        NAME="Ubuntu"
        VERSION_ID="22.04"
        ID=ubuntu
        ID_LIKE=debian
    """
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip().lower()] = value.strip().strip('"')
    return result


# ── uname -a ──────────────────────────────────────────────────────────────────

def parse_uname(raw: str) -> dict:
    """
    Parseia a saída de `uname -a`.

    Formato típico:
        Linux hostname 5.15.0-91-generic #101-Ubuntu SMP ... x86_64 GNU/Linux
    Retorna kernel_release, kernel_version e machine.
    """
    parts = raw.strip().split()
    if len(parts) < 3:
        return {}

    kernel_release = parts[2]
    machine        = parts[-2] if len(parts) > 5 else None
    version_parts  = parts[3:-2] if len(parts) > 5 else []
    kernel_version = " ".join(version_parts) or None

    return {
        "kernel_release": kernel_release,
        "kernel_version": kernel_version,
        "machine":        machine,
    }


# ── /proc/uptime ──────────────────────────────────────────────────────────────

def parse_uptime_seconds(raw: str) -> int | None:
    """
    Extrai uptime total em segundos de /proc/uptime.
    Formato: '123456.78 98765.43'
    """
    try:
        return int(float(raw.strip().split()[0]))
    except (ValueError, IndexError):
        return None


# ── helpers de limpeza ────────────────────────────────────────────────────────

def clean_hostname(raw: str) -> str | None:
    value = raw.strip()
    return value if value else None


def clean_timezone(raw: str) -> str | None:
    value = raw.strip()
    return value if value else None
