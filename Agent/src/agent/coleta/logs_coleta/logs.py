# =============================================================================
# coleta/logs_coleta/logs.py
#
# Coleta incremental de /var/log/auth.log.
#
# Comportamento:
#   - Rastreia posição (byte offset + inode) em ~/.agent/auth_log_state.json.
#   - Na primeira execução: envia as últimas 100 linhas (histórico inicial)
#     e salva a posição no final do arquivo.
#   - Nas execuções seguintes: envia apenas as linhas novas desde o último envio.
#   - Detecta rotação de log (mudança de inode) e reinicia a leitura do início
#     do novo arquivo.
#   - Nunca reenvia a mesma linha ao servidor.
# =============================================================================

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

_STATE_FILE  = Path.home() / ".agent" / "auth_log_state.json"
_AUTH_LOG    = "/var/log/auth.log"
_FIRST_RUN_LINES = 100   # linhas enviadas na primeira execução (histórico inicial)

# Regex para extrair o timestamp da linha de auth.log
# Exemplo: "May 18 14:35:00 server sshd[123]: ..."
_LOG_TS_RE = re.compile(r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})')


# =============================================================================
# ESTADO PERSISTIDO
# =============================================================================

def _load_state() -> dict:
    try:
        if _STATE_FILE.exists():
            return json.loads(_STATE_FILE.read_text())
    except Exception:
        pass
    return {"inode": None, "offset": 0}


def _save_state(inode: int, offset: int) -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps({"inode": inode, "offset": offset}))
    except Exception as e:
        print(f"Aviso: nao foi possivel salvar estado de logs: {e}")


# =============================================================================
# PARSING DE TIMESTAMP
# =============================================================================

def _parse_log_timestamp(line: str) -> str:
    """
    Extrai o timestamp da linha de auth.log e retorna ISO 8601 UTC.
    Assume o ano corrente. Fallback: momento atual.
    """
    m = _LOG_TS_RE.match(line)
    if m:
        try:
            ts = datetime.strptime(
                f"{datetime.utcnow().year} {m.group(1)}", "%Y %b %d %H:%M:%S"
            )
            return ts.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# COLETA PRINCIPAL
# =============================================================================

def get_new_auth_log_lines() -> list[dict]:
    """
    Retorna as novas linhas de /var/log/auth.log desde a última leitura.

    Cada entrada é um dict:
        {
            "timestamp": "2026-05-18T14:35:00+00:00",
            "raw_line":  "May 18 14:35:00 server sshd[123]: Failed password ..."
        }

    Retorna lista vazia se não houver linhas novas, arquivo não existir
    ou em caso de erro de permissão.
    """
    # Verifica existência e permissão antes de abrir
    try:
        stat = os.stat(_AUTH_LOG)
        current_inode = stat.st_ino
    except FileNotFoundError:
        print(f"Aviso: {_AUTH_LOG} nao encontrado")
        return []
    except PermissionError:
        print(f"Erro: sem permissao para acessar {_AUTH_LOG} — execute o agent com sudo")
        return []

    state        = _load_state()
    first_run    = state.get("inode") is None
    inode_changed = not first_run and state.get("inode") != current_inode

    try:
        with open(_AUTH_LOG, "r", errors="replace") as f:
            if first_run:
                # Primeira execução: pega as últimas _FIRST_RUN_LINES linhas
                all_lines   = f.readlines()
                eof_offset  = f.tell()
                raw_lines   = all_lines[-_FIRST_RUN_LINES:]
                _save_state(current_inode, eof_offset)

            elif inode_changed:
                # Log foi rotacionado: começa do início do novo arquivo
                raw_lines  = f.readlines()
                _save_state(current_inode, f.tell())

            else:
                # Execução normal: lê apenas as linhas novas
                f.seek(state.get("offset", 0))
                raw_lines  = f.readlines()
                _save_state(current_inode, f.tell())

    except PermissionError:
        print(f"Erro: sem permissao para ler {_AUTH_LOG}")
        return []
    except Exception as e:
        print(f"Erro ao ler {_AUTH_LOG}: {e}")
        return []

    # Monta lista de entradas ignorando linhas vazias
    entries = []
    for line in raw_lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        entries.append({
            "timestamp": _parse_log_timestamp(line),
            "raw_line":  line,
        })

    return entries


# Alias mantido para compatibilidade com collector.py antigo
def get_logs():
    return get_new_auth_log_lines()
