# =============================================================================
# discovery/system_discovery/system.py
#
# Discovery do sistema operacional e kernel.
# Coleta informações do OS, kernel, hostname, timezone e uptime.
#
# Não detecta virtualização aqui — recebe o ambiente já resolvido
# via parâmetro (detectado uma única vez no __main__).
# =============================================================================

from agent.utils.shell import run
from agent.utils.parsers import (
    parse_os_release,
    parse_uname,
    parse_uptime_seconds,
    clean_hostname,
    clean_timezone,
)


def get_system_info(is_virtualized: bool) -> dict:
    """
    Coleta informações do sistema operacional e kernel.

    As informações de OS são idênticas para físico e VM —
    o bloco de virtualização foi movido para global_information.

    Parâmetros:
        is_virtualized (bool): recebido do global_information, não redetectado aqui

    Retorno:
        dict com hostname, os, kernel, timezone e uptime_seconds.
    """
    # ── Coleta bruta ──────────────────────────────────────────────────────────
    os_release_raw = run("cat /etc/os-release")
    uname_raw      = run("uname -a")
    hostname_raw   = run("hostname -f")
    uptime_raw     = run("cat /proc/uptime")
    timezone_raw   = run("timedatectl show --property=Timezone --value")

    # ── Parse ─────────────────────────────────────────────────────────────────
    os_info  = parse_os_release(os_release_raw or "")
    uname    = parse_uname(uname_raw or "")
    hostname = clean_hostname(hostname_raw or "")
    uptime_s = parse_uptime_seconds(uptime_raw or "")
    timezone = clean_timezone(timezone_raw or "")

    # ── Montagem do payload ───────────────────────────────────────────────────
    return {
        "hostname": hostname,
        "os": {
            # Nome amigável e versão completa (ex: "Ubuntu 24.04.4 LTS (Noble Numbat)")
            "name":        os_info.get("name"),
            "pretty_name": os_info.get("pretty_name"),
            "version":     os_info.get("version"),
            "codename":    os_info.get("version_codename") or os_info.get("ubuntu_codename"),
            # id e id_like omitidos (ubuntu, debian) — não são úteis para monitoramento
        },
        "kernel": {
            "release": uname.get("kernel_release"),   # ex: "6.8.0-110-generic"
            "version": uname.get("kernel_version"),   # ex: "#110-Ubuntu SMP..."
            "machine": uname.get("machine"),          # ex: "x86_64"
        },
        "timezone":       timezone or None,
        "uptime_seconds": uptime_s,
    }

# =============================================================================
# FIM discovery/system_discovery/system.py
# =============================================================================