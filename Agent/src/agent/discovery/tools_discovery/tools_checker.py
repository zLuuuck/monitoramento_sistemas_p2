# =============================================================================
# discovery/tools_discovery/tools_checker.py
#
# Lógica central de verificação de ferramentas.
# Compartilhada entre tools_physical.py e tools_virtual.py.
#
# Para cada ferramenta, verifica:
#   - installed   : se o binário existe no sistema (via `which`)
#   - path        : caminho completo do binário
#   - version     : versão extraída da saída do comando de versão
#   - has_root    : se o processo atual tem permissão efetiva de root (uid=0)
#
# Nota sobre has_root:
#   Verifica se o agente está rodando como root (os.geteuid() == 0).
#   Não testa sudo — isso exigiria um comando real que pode pedir senha.
#   Um agente rodando com sudo já tem uid=0 nesse contexto.
# =============================================================================

import os
import shutil
from agent.utils.shell import run


# =============================================================================
# Definição das ferramentas
# =============================================================================

# Cada entrada: (nome, comando_de_versão, regex_ou_índice_para_extrair_versão)
# version_flag: flag que o comando aceita para imprimir a versão
# version_parser: função que recebe a saída e retorna a string de versão

_TOOL_DEFINITIONS = {
    # ── Ferramentas de hardware físico ────────────────────────────────────────
    "dmidecode": {
        "version_flag":   "--version",
        "requires_root":  True,   # dmidecode só funciona com root
    },
    "smartctl": {
        "version_flag":   "--version",
        "requires_root":  True,   # smartctl precisa de root para acessar o disco
    },
    "ethtool": {
        "version_flag":   "--version",
        "requires_root":  False,  # ethtool lê, não precisa de root para info básica
    },
    "lspci": {
        "version_flag":   "--version",
        "requires_root":  False,
    },

    # ── Ferramentas comuns (físico e VM) ──────────────────────────────────────
    "lsblk": {
        "version_flag":   "--version",
        "requires_root":  False,
    },
    "ip": {
        "version_flag":   "-Version",   # ip usa -Version com V maiúsculo
        "requires_root":  False,
    },
    "lscpu": {
        "version_flag":   "--version",
        "requires_root":  False,
    },
    "journalctl": {
        "version_flag":   "--version",
        "requires_root":  False,
    },
    "timedatectl": {
        "version_flag":   "--version",
        "requires_root":  False,
    },
}


# =============================================================================
# Função principal de verificação
# =============================================================================

def check_tool(name: str) -> dict:
    """
    Verifica o status de uma ferramenta no sistema.

    Parâmetros:
        name (str): nome do binário (ex: "smartctl", "lsblk")

    Retorno:
        dict com:
            installed  (bool)      : True se o binário existe no PATH
            path       (str|None)  : caminho completo do binário
            version    (str|None)  : versão extraída da saída do comando
            has_root   (bool)      : True se o agente está rodando como root
            needs_root (bool)      : True se a ferramenta requer root para funcionar
    """
    definition  = _TOOL_DEFINITIONS.get(name, {})
    needs_root  = definition.get("requires_root", False)
    version_flag = definition.get("version_flag", "--version")

    # ── Verifica se está instalado e localiza o binário ──────────────────────
    binary_path = shutil.which(name)
    installed   = binary_path is not None

    # ── Extrai versão ─────────────────────────────────────────────────────────
    version = None
    if installed:
        version = _extract_version(name, binary_path, version_flag)

    # ── Verifica permissão efetiva ────────────────────────────────────────────
    # os.geteuid() == 0 significa que o processo está rodando como root,
    # seja diretamente ou via sudo. Não testa sudo interativo.
    has_root = (os.geteuid() == 0)

    return {
        "installed":   installed,
        "path":        binary_path,
        "version":     version,
        "has_root":    has_root,
        "needs_root":  needs_root,
    }


def check_tools(names: list[str]) -> dict:
    """
    Verifica uma lista de ferramentas e retorna um dict indexado por nome.

    Parâmetros:
        names (list[str]): lista de nomes de ferramentas a verificar

    Retorno:
        dict[str, dict] com o resultado de check_tool() para cada ferramenta.
    """
    return {name: check_tool(name) for name in names}


# =============================================================================
# Extração de versão
# =============================================================================

def _extract_version(name: str, path: str, version_flag: str) -> str | None:
    """
    Extrai a string de versão de uma ferramenta.

    Tenta o comando com a flag de versão e pega a primeira linha não vazia.
    Algumas ferramentas imprimem a versão no stderr (ex: smartctl),
    então tenta stdout primeiro, depois stderr.

    Parâmetros:
        name         (str): nome da ferramenta
        path         (str): caminho completo do binário
        version_flag (str): flag para obter a versão (ex: "--version")

    Retorno:
        str com a versão, ou None se não conseguir extrair.
    """
    # Ferramentas que precisam de root podem falhar sem ele —
    # nesse caso retorna None sem travar
    raw = _run_version_cmd(f"{path} {version_flag}")
    if not raw:
        # Algumas ferramentas usam stderr para versão (ex: ip)
        raw = _run_version_cmd_stderr(f"{path} {version_flag}")
    if not raw:
        return None

    # Pega a primeira linha não vazia — geralmente contém a versão
    for line in raw.splitlines():
        line = line.strip()
        if line:
            return line

    return None


def _run_version_cmd(cmd: str) -> str | None:
    """Roda um comando e retorna stdout, mesmo com exit code != 0."""
    import subprocess
    import os
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _run_version_cmd_stderr(cmd: str) -> str | None:
    """Roda um comando e retorna stderr (para ferramentas que imprimem versão lá)."""
    import subprocess
    import os
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
        return result.stderr.strip() or None
    except Exception:
        return None

# =============================================================================
# FIM discovery/tools_discovery/tools_checker.py
# =============================================================================