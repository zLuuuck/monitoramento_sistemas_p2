# =============================================================================
# discovery/tools_discovery/tools_checker.py
#
# Lógica central de verificação e instalação de ferramentas.
# Compartilhada entre tools_physical.py e tools_virtual.py.
#
# Fluxo:
#   1. Verifica quais ferramentas estão instaladas (shutil.which)
#   2. Se alguma obrigatória estiver faltando:
#      - Se rodando em terminal interativo: pergunta se deseja instalar
#      - Se rodando como serviço/pipe (sem terminal): registra e segue
#   3. Instala usando o gerenciador detectado (apt, dnf, pacman, zypper)
#   4. Retorna o status final de cada ferramenta
#
# Limitações conhecidas (evoluções futuras):
#   - Instalação requer root — sem root, falha silenciosamente
#   - Não verifica atualizações — apenas presença do binário
#   - Flag --install-deps no CLI instala sem perguntar (não-interativo)
# =============================================================================

import os
import sys
import shutil
import subprocess

# =============================================================================
# Definição das ferramentas
# =============================================================================

# Nome do pacote por gerenciador para cada ferramenta.
# Quando o pacote tem nome diferente do binário, cada gerenciador é explícito.
_TOOL_PACKAGES = {
    "dmidecode": {
        "apt": "dmidecode",
        "dnf": "dmidecode",
        "pacman": "dmidecode",
        "zypper": "dmidecode",
    },
    "smartctl": {
        "apt": "smartmontools",
        "dnf": "smartmontools",
        "pacman": "smartmontools",
        "zypper": "smartmontools",
    },
    "ethtool": {
        "apt": "ethtool",
        "dnf": "ethtool",
        "pacman": "ethtool",
        "zypper": "ethtool",
    },
    "lspci": {
        "apt": "pciutils",
        "dnf": "pciutils",
        "pacman": "pciutils",
        "zypper": "pciutils",
    },
    "lsblk": {
        "apt": "util-linux",
        "dnf": "util-linux",
        "pacman": "util-linux",
        "zypper": "util-linux",
    },
    "ip": {
        "apt": "iproute2",
        "dnf": "iproute",
        "pacman": "iproute2",
        "zypper": "iproute2",
    },
    "lscpu": {
        "apt": "util-linux",
        "dnf": "util-linux",
        "pacman": "util-linux",
        "zypper": "util-linux",
    },
    "journalctl": {
        "apt": "systemd",
        "dnf": "systemd",
        "pacman": "systemd",
        "zypper": "systemd",
    },
    "timedatectl": {
        "apt": "systemd",
        "dnf": "systemd",
        "pacman": "systemd",
        "zypper": "systemd",
    },
}

# Ferramentas que requerem root para funcionar corretamente
_NEEDS_ROOT = {"dmidecode", "smartctl"}

# Comandos de instalação por gerenciador
_INSTALL_COMMANDS = {
    "apt": "apt-get install -y {package}",
    "dnf": "dnf install -y {package}",
    "pacman": "pacman -S --noconfirm {package}",
    "zypper": "zypper install -y {package}",
}


# =============================================================================
# Ponto de entrada público
# =============================================================================


def check_tools(names: list, force_install: bool = False) -> dict:
    """
    Verifica uma lista de ferramentas e oferece instalação das ausentes.

    Parâmetros:
        names         (list): ferramentas a verificar
        force_install (bool): se True, instala sem perguntar
                              (equivalente à flag --install-deps)

    Retorno:
        dict[str, dict] com o status final de cada ferramenta.
    """
    # ── Primeira verificação ──────────────────────────────────────────────────
    results = {name: _check_single(name) for name in names}
    missing = [name for name, info in results.items() if not info["installed"]]

    print("  Verificando dependências...")
    _print_status(results)

    if not missing:
        return results

    # ── Gerenciador de pacotes ────────────────────────────────────────────────
    pkg_manager = _detect_package_manager()
    if not pkg_manager:
        print("  ⚠ Gerenciador de pacotes não identificado.")
        print(f"  Instale manualmente: {', '.join(missing)}")
        return results

    # ── Decide se instala ─────────────────────────────────────────────────────
    should_install = force_install or _ask_install(missing, pkg_manager)

    if should_install:
        _install_tools(missing, pkg_manager)
        # Re-verifica após instalação para atualizar status no payload
        for name in missing:
            results[name] = _check_single(name)
        print("  Status após instalação:")
        _print_status({name: results[name] for name in missing})
    else:
        print("  Continuando sem as ferramentas ausentes.")
        print("  Alguns campos do discovery ficarão incompletos.")

    return results


# =============================================================================
# Verificação individual
# =============================================================================


def _check_single(name: str) -> dict:
    """
    Verifica o status de uma única ferramenta.

    Retorno:
        dict com:
            installed  (bool)     : True se o binário existe no PATH
            path       (str|None) : caminho completo do binário
            version    (str|None) : primeira linha da saída de --version
            has_root   (bool)     : True se o agente roda como root (uid=0)
            needs_root (bool)     : True se a ferramenta requer root
    """
    binary_path = shutil.which(name)
    installed = binary_path is not None

    return {
        "installed": installed,
        "path": binary_path,
        "version": _extract_version(name, binary_path) if installed else None,
        "has_root": (os.geteuid() == 0),
        "needs_root": name in _NEEDS_ROOT,
    }


# =============================================================================
# Detecção de gerenciador de pacotes
# =============================================================================


def _detect_package_manager() -> str | None:
    """
    Detecta o gerenciador de pacotes disponível no sistema.

    Suporte atual:
        apt     → Debian, Ubuntu, Mint, Pop!_OS
        dnf     → Fedora, RHEL, CentOS Stream
        pacman  → Arch, Manjaro, EndeavourOS
        zypper  → openSUSE, SLES

    Retorna o nome do primeiro encontrado, ou None.
    """
    for manager in ("apt", "dnf", "pacman", "zypper"):
        if shutil.which(manager):
            return manager
    return None


# =============================================================================
# Interação com o usuário
# =============================================================================


def _ask_install(missing: list, pkg_manager: str) -> bool:
    """
    Pergunta ao usuário se deseja instalar as ferramentas faltantes.

    Só pergunta se houver terminal interativo (sys.stdin.isatty()).
    Em pipes, serviços ou cron, retorna False silenciosamente —
    o agente não pode ficar travado esperando input que nunca virá.

    Para forçar instalação sem terminal, use a flag --install-deps.
    """
    if not sys.stdin.isatty():
        print("  ℹ Sem terminal interativo — instalação ignorada.")
        print("  Use --install-deps para instalar automaticamente.")
        return False

    print("")
    print("  As ferramentas abaixo são necessárias para o discovery completo:")
    for name in missing:
        pkg = _get_package_name(name, pkg_manager)
        print(f"    ✗ {name}  (pacote: {pkg})")
    print("")

    try:
        answer = input("  Deseja instalá-las agora? [s/N]: ").strip().lower()
        return answer in ("s", "sim", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        print("")
        return False


# =============================================================================
# Instalação
# =============================================================================


def _install_tools(names: list, pkg_manager: str) -> None:
    """
    Instala ferramentas usando o gerenciador de pacotes detectado.

    Instala uma por uma para que a falha de uma não impeça as outras.
    Requer root — sem root, o gerenciador vai recusar e reportar o erro.
    """
    print("")
    for name in names:
        package = _get_package_name(name, pkg_manager)
        cmd = _INSTALL_COMMANDS[pkg_manager].format(package=package)

        print(f"  Instalando {name} ({package})...")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # instalações podem demorar em conexões lentas
                env={**os.environ, "LC_ALL": "C", "DEBIAN_FRONTEND": "noninteractive"},
            )
            if result.returncode == 0:
                print(f"  ✓ {name} instalado com sucesso")
            else:
                # Mostra a última linha do erro do gerenciador de pacotes
                err_lines = (result.stderr or result.stdout or "").strip().splitlines()
                err_msg = err_lines[-1] if err_lines else "erro desconhecido"
                print(f"  ✗ Falha ao instalar {name}: {err_msg}")
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout ao instalar {name} — verifique a conexão")
        except Exception as e:
            print(f"  ✗ Erro inesperado ao instalar {name}: {e}")
    print("")


def _get_package_name(tool_name: str, pkg_manager: str) -> str:
    """Retorna o nome do pacote correto para o gerenciador informado."""
    return _TOOL_PACKAGES.get(tool_name, {}).get(pkg_manager, tool_name)


# =============================================================================
# Extração de versão
# =============================================================================


def _extract_version(name: str, path: str) -> str | None:
    """
    Extrai a versão de uma ferramenta.

    Usa --version para a maioria. Exceção: `ip` usa -Version (maiúsculo).
    Captura stdout + stderr juntos pois ferramentas variam em onde imprimem.
    Retorna a primeira linha não-vazia da saída, independente do exit code.
    """
    flag = "-Version" if name == "ip" else "--version"
    raw = _run_capture(f"{path} {flag}")
    if not raw:
        return None

    for line in raw.splitlines():
        line = line.strip()
        if line:
            return line
    return None


def _run_capture(cmd: str) -> str | None:
    """
    Executa um comando e retorna stdout + stderr combinados.

    Independente do exit code — usado para capturar versões de ferramentas
    que retornam exit code != 0 mesmo em execução normal.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
        return result.stdout.strip() or None
    except Exception:
        return None


# =============================================================================
# Display
# =============================================================================


def _print_status(results: dict) -> None:
    """
    Imprime o status das ferramentas verificadas.

    Agrupa as instaladas em uma linha e lista individualmente as ausentes.
    """
    ok = [n for n, i in results.items() if i["installed"]]
    missing = [n for n, i in results.items() if not i["installed"]]

    if ok:
        print(f"  ✓ {', '.join(ok)}")
    for name in missing:
        print(f"  ✗ {name} — não encontrado")


# =============================================================================
# FIM discovery/tools_discovery/tools_checker.py
# =============================================================================
