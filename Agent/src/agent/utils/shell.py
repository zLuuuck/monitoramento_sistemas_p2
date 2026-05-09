# =============================================================================
# utils/shell.py
# Utilitário para execução de comandos shell de forma segura.
# Usado por todos os módulos de discovery para coletar dados do sistema.
# =============================================================================

import subprocess


def run(cmd: str) -> str | None:
    """
    Executa um comando shell e retorna a saída (stdout) como string.

    - Falha silenciosa: retorna None se o comando não existir,
      retornar código de erro, ou lançar qualquer exceção.
    - Não lança exceções — os módulos que chamam run() não precisam
      de try/except para comandos individuais.

    Parâmetros:
        cmd (str): comando completo a ser executado (ex: "lscpu", "ip -j addr show")

    Retorno:
        str com stdout do comando, ou None em caso de falha.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,          # evita travar o agente em comandos lentos
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None

# =============================================================================
# FIM utils/shell.py
# =============================================================================