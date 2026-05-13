# =============================================================================
# utils/shell.py
# Utilitário para execução de comandos shell de forma segura.
# Usado por todos os módulos de discovery para coletar dados do sistema.
# =============================================================================

import subprocess
import os

# Ambiente base para comandos de sistema.
# LC_ALL=C força saída em inglês, garantindo que parsers funcionem
# independente do idioma configurado no sistema (PT, DE, ES...).
# Sem isso, lscpu em português retorna "Arquitetura" em vez de "Architecture",
# quebrando o parse silenciosamente.
_ENV_C = {**os.environ, "LC_ALL": "C", "LANG": "C"}


def run(cmd: str) -> str | None:
    """
    Executa um comando shell com locale forçado para inglês (LC_ALL=C).

    - Saída sempre em inglês: garante compatibilidade dos parsers
      independente do idioma do sistema operacional.
    - Falha silenciosa: retorna None se o comando não existir,
      retornar código de erro, ou lançar qualquer exceção.
    - Não lança exceções — os módulos que chamam run() não precisam
      de try/except para comandos individuais.

    Parâmetros:
        cmd (str): comando completo a ser executado

    Retorno:
        str com stdout do comando, ou None em caso de falha.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,      # evita travar o agente em comandos lentos
            env=_ENV_C,      # saída em inglês independente do locale do sistema
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def run_permissive(cmd: str) -> str | None:
    """
    Executa um comando e retorna stdout mesmo com código de saída não-zero.

    Usado para comandos que retornam exit code != 0 mesmo com dados válidos.
    Caso de uso principal: smartctl, que retorna códigos não-zero quando
    detecta warnings no disco (ex: poucos setores realocados), mas ainda
    assim retorna JSON útil no stdout.

    Parâmetros:
        cmd (str): comando completo a ser executado

    Retorno:
        str com stdout do comando (mesmo em erro), ou None se stdout vazio.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,      # smartctl pode demorar mais em discos lentos
            env=_ENV_C,
        )
        # Retorna stdout se tiver conteúdo, independente do exit code
        return result.stdout.strip() or None
    except Exception:
        return None

# =============================================================================
# FIM utils/shell.py
# =============================================================================