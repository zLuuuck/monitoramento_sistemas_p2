# app/utils/parsers.py
# Funções de parsing de logs e contagem de eventos de segurança
# Semana 4 — parse_ssh_log() e count_failed_logins()
# Semana 6 — parse_auth_log(): orquestrador que cobre todos os eventos do auth.log

import re
import logging
from datetime import datetime, timedelta

# Logger do módulo — usado onde app.logger não está disponível
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# REGEX — linhas do /var/log/auth.log geradas pelo sshd (login SSH)
#
# Exemplos de linhas reconhecidas:
#   Apr 21 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100 port 22 ssh2
#   Apr 21 14:36:00 server sshd[124]: Accepted password for admin from 10.10.10.5 port 54321 ssh2
#   Apr 21 14:37:00 server sshd[125]: Failed password for invalid user ghost from 10.0.0.1 port 60000 ssh2
#
# Grupos capturados:
#   1 → "Failed password"  ou  "Accepted password"
#   2 → nome do usuário (o prefixo "invalid user " é ignorado pelo (?:...) antes)
#   3 → endereço IPv4 de origem
# ---------------------------------------------------------------------------
_PADRAO_SSH = re.compile(
    r'(Failed password|Accepted password)'   # grupo 1: resultado da tentativa
    r'\s+for\s+'
    r'(?:invalid user\s+)?'                  # prefixo opcional — aparece quando o usuário não existe
    r'(\S+)'                                 # grupo 2: nome do usuário
    r'\s+from\s+'
    r'((?:\d{1,3}\.){3}\d{1,3})',            # grupo 3: IPv4 de origem
)

# ---------------------------------------------------------------------------
# REGEX — PAM authentication failure
#
# Exemplos:
#   sshd[10719]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=10.81.243.81
#   sshd[10719]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=10.81.243.81 user=root
#
# Grupos capturados:
#   1 → serviço PAM, ex: "sshd:auth"
#   2 → rhost (IPv4), pode ser ausente
#   3 → user (nome do usuário), pode ser ausente
# ---------------------------------------------------------------------------
_PADRAO_PAM_AUTH_FAILURE = re.compile(
    r'pam_unix\(([^)]+)\):\s+authentication failure'  # grupo 1: serviço
    r'.*?rhost=((?:\d{1,3}\.){3}\d{1,3})?'           # grupo 2: rhost IPv4 (opcional)
    r'(?:\s+user=(\S+))?',                            # grupo 3: user (opcional)
)

# ---------------------------------------------------------------------------
# REGEX — PAM session opened/closed
#
# Exemplos:
#   sshd[30500]: pam_unix(sshd:session): session opened for user teste(uid=1000) by teste(uid=0)
#   sshd[30500]: pam_unix(sshd:session): session closed for user teste
#   sudo[1234]:  pam_unix(sudo:session): session opened for user root(uid=0) by teste(uid=1000)
#
# Grupos capturados:
#   1 → serviço PAM, ex: "sshd:session"
#   2 → "opened" ou "closed"
#   3 → nome do usuário
# ---------------------------------------------------------------------------
_PADRAO_PAM_SESSION = re.compile(
    r'pam_unix\(([^)]+)\):\s+session\s+(opened|closed)'  # grupos 1 e 2
    r'\s+for\s+user\s+(\S+?)(?:\(uid=\d+\))?'            # grupo 3: usuário (sem o uid)
    r'(?:\s+by\s+|$)',
)

# ---------------------------------------------------------------------------
# REGEX — systemd-logind: sessões de usuário
#
# Exemplos:
#   systemd-logind[828]: New session 20 of user teste.
#   systemd-logind[828]: Removed session 20.
#   systemd-logind[828]: Session 20 logged out. Waiting for processes to exit.
#
# Grupos capturados:
#   1 → "New session" | "Removed session" | "Session ... logged out"
#   2 → número da sessão
#   3 → nome do usuário (apenas no evento "New session")
# ---------------------------------------------------------------------------
_PADRAO_LOGIND_NEW = re.compile(
    r'systemd-logind\[\d+\]:\s+New session\s+(\d+)\s+of\s+user\s+(\S+?)\.?$'
)
_PADRAO_LOGIND_REMOVED = re.compile(
    r'systemd-logind\[\d+\]:\s+(Removed session|Session\s+\d+\s+logged out)\s*(\d*)',
)

# ---------------------------------------------------------------------------
# REGEX — sshd: Disconnected / Received disconnect
#
# Exemplos:
#   sshd[30628]: Disconnected from user teste 10.81.243.81 port 64077
#   sshd[30628]: Received disconnect from 10.81.243.81 port 64077:11: disconnected by user
#
# Grupos capturados para Disconnected from user:
#   1 → nome do usuário
#   2 → IPv4 de origem
#
# Grupos capturados para Received disconnect:
#   1 → IPv4 de origem
# ---------------------------------------------------------------------------
_PADRAO_SSH_DISCONNECTED = re.compile(
    r'sshd\[\d+\]:\s+Disconnected from user\s+(\S+)\s+((?:\d{1,3}\.){3}\d{1,3})'
)
_PADRAO_SSH_RECV_DISCONNECT = re.compile(
    r'sshd\[\d+\]:\s+Received disconnect from\s+((?:\d{1,3}\.){3}\d{1,3})'
)

# ---------------------------------------------------------------------------
# REGEX — sudo: execução de comando com privilégio elevado
#
# Exemplo:
#   sudo: teste : TTY=pts/2 ; PWD=/home/teste/monitoramento_sistemas ; USER=root ; COMMAND=/usr/bin/systemctl status linux-agent
#
# Grupos capturados:
#   1 → usuário que executou o sudo
#   2 → diretório de trabalho (PWD)
#   3 → usuário alvo (USER=)
#   4 → comando executado (COMMAND=)
# ---------------------------------------------------------------------------
_PADRAO_SUDO = re.compile(
    r'sudo:\s+(\S+)\s+:\s+TTY=\S+\s+;\s+PWD=(\S+)\s+;\s+USER=(\S+)\s+;\s+COMMAND=(.+)$'
)

# ---------------------------------------------------------------------------
# REGEX — CRON: sessões abertas/fechadas pelo cron
#
# Exemplos:
#   CRON[31236]: pam_unix(cron:session): session opened for user root(uid=0) by (uid=0)
#   CRON[31236]: pam_unix(cron:session): session closed for user root
#
# Coberto pelo _PADRAO_PAM_SESSION acima (serviço "cron:session").
# Este regex extra captura linhas CRON que não passam pelo padrão PAM.
#
# Grupos capturados:
#   1 → "opened" ou "closed"
#   2 → nome do usuário
# ---------------------------------------------------------------------------
_PADRAO_CRON = re.compile(
    r'CRON\[\d+\]:\s+.*session\s+(opened|closed)\s+for\s+user\s+(\S+?)(?:\(uid=\d+\))?'
)


# ===========================================================================
# FUNÇÕES DE PARSING INDIVIDUAIS
# ===========================================================================

def parse_ssh_log(raw_line: str) -> dict | None:
    """
    Extrai campos estruturados de uma linha de login/falha SSH (sshd).

    Retorna dict com event_type, status, usuario, ip_origem
    ou None se a linha não for reconhecida.

    Os campos ip_origem e status batem com os índices JSONB do banco:
        idx_logs_auth_ip     — (parsed_data->>'ip_origem') WHERE log_type = 'auth'
        idx_logs_auth_failed — timestamp WHERE log_type = 'auth'
                               AND parsed_data->>'status' = 'failed'
    """
    if not raw_line:
        return None

    m = _PADRAO_SSH.search(raw_line)
    if not m:
        return None

    status_raw, usuario, ip_origem = m.groups()
    status = 'failed' if 'Failed' in status_raw else 'accepted'

    return {
        'event_type': 'ssh_login',
        'status':     status,
        'usuario':    usuario,
        'ip_origem':  ip_origem,
    }


def parse_pam_auth_failure(raw_line: str) -> dict | None:
    """
    Extrai campos de uma linha pam_unix(...): authentication failure.

    Retorna dict com event_type, status, usuario, ip_origem
    ou None se não reconhecida.
    """
    if not raw_line:
        return None

    m = _PADRAO_PAM_AUTH_FAILURE.search(raw_line)
    if not m:
        return None

    servico, rhost, usuario = m.groups()

    return {
        'event_type': 'pam_auth_failure',
        'status':     'failed',
        'usuario':    usuario or None,
        'ip_origem':  rhost or None,
        'servico':    servico,
    }


def parse_pam_session(raw_line: str) -> dict | None:
    """
    Extrai campos de linhas pam_unix(...): session opened/closed.

    Retorna dict com event_type, status, usuario, ip_origem
    ou None se não reconhecida.
    """
    if not raw_line:
        return None

    # Tenta pelo padrão genérico PAM session
    m = _PADRAO_PAM_SESSION.search(raw_line)
    if not m:
        # Tenta pelo padrão específico do CRON
        m2 = _PADRAO_CRON.search(raw_line)
        if not m2:
            return None
        acao, usuario = m2.groups()
        return {
            'event_type': 'cron_session',
            'status':     'session_open' if acao == 'opened' else 'session_close',
            'usuario':    usuario,
            'ip_origem':  None,
        }

    servico, acao, usuario = m.groups()

    # Diferencia CRON de sessão SSH/sudo pelo nome do serviço PAM
    if 'cron' in servico.lower():
        event_type = 'cron_session'
    elif 'sudo' in servico.lower():
        event_type = 'sudo_session'
    else:
        event_type = 'pam_session'

    return {
        'event_type': event_type,
        'status':     'session_open' if acao == 'opened' else 'session_close',
        'usuario':    usuario,
        'ip_origem':  None,
        'servico':    servico,
    }


def parse_logind_session(raw_line: str) -> dict | None:
    """
    Extrai campos de eventos systemd-logind (New session / Removed session).

    Retorna dict com event_type, status, usuario, ip_origem
    ou None se não reconhecida.
    """
    if not raw_line or 'systemd-logind' not in raw_line:
        return None

    # Evento: nova sessão (tem usuário)
    m = _PADRAO_LOGIND_NEW.search(raw_line)
    if m:
        session_id, usuario = m.groups()
        return {
            'event_type': 'logind_session',
            'status':     'session_open',
            'usuario':    usuario,
            'ip_origem':  None,
            'session_id': session_id,
        }

    # Evento: sessão removida / logged out (sem usuário)
    m2 = _PADRAO_LOGIND_REMOVED.search(raw_line)
    if m2:
        return {
            'event_type': 'logind_session',
            'status':     'session_close',
            'usuario':    None,
            'ip_origem':  None,
        }

    return None


def parse_ssh_disconnect(raw_line: str) -> dict | None:
    """
    Extrai campos de linhas sshd: Disconnected from user / Received disconnect.

    Retorna dict com event_type, status, usuario, ip_origem
    ou None se não reconhecida.
    """
    if not raw_line:
        return None

    # Disconnected from user <usuario> <ip>
    m = _PADRAO_SSH_DISCONNECTED.search(raw_line)
    if m:
        usuario, ip_origem = m.groups()
        return {
            'event_type': 'ssh_disconnect',
            'status':     'session_close',
            'usuario':    usuario,
            'ip_origem':  ip_origem,
        }

    # Received disconnect from <ip>
    m2 = _PADRAO_SSH_RECV_DISCONNECT.search(raw_line)
    if m2:
        return {
            'event_type': 'ssh_disconnect',
            'status':     'session_close',
            'usuario':    None,
            'ip_origem':  m2.group(1),
        }

    return None


def parse_sudo(raw_line: str) -> dict | None:
    """
    Extrai campos de linhas de execução via sudo.

    Retorna dict com event_type, status, usuario, ip_origem, comando
    ou None se não reconhecida.
    """
    if not raw_line or 'sudo' not in raw_line:
        return None

    m = _PADRAO_SUDO.search(raw_line)
    if not m:
        return None

    usuario, pwd, usuario_alvo, comando = m.groups()

    return {
        'event_type':   'sudo',
        'status':       'sudo_exec',
        'usuario':      usuario,
        'ip_origem':    None,
        'usuario_alvo': usuario_alvo,
        'comando':      comando.strip(),
        'diretorio':    pwd,
    }


# ===========================================================================
# ORQUESTRADOR — parse_auth_log()
#
# Substitui a chamada direta a parse_ssh_log() em logs.py.
# Tenta cada parser na ordem de especificidade (mais específico primeiro).
# Retorna o primeiro resultado não-nulo, ou None se nenhum casar.
#
# Ordem dos parsers:
#   1. SSH login (Failed/Accepted password) — mais crítico para brute force
#   2. sudo — comando privilegiado
#   3. PAM authentication failure — falha de autenticação PAM
#   4. SSH disconnect — encerramento de sessão SSH
#   5. PAM session (inclui CRON) — abertura/fechamento de sessão PAM
#   6. systemd-logind — eventos de sessão do sistema
# ===========================================================================

_PARSERS = [
    parse_ssh_log,
    parse_sudo,
    parse_pam_auth_failure,
    parse_ssh_disconnect,
    parse_pam_session,
    parse_logind_session,
]


def parse_auth_log(raw_line: str) -> dict | None:
    """
    Orquestrador de parsing para linhas do /var/log/auth.log.

    Tenta cada parser registrado em _PARSERS e retorna o primeiro resultado
    não-nulo. Retorna None se nenhum parser reconhecer a linha.

    Este é o único ponto de entrada que logs.py deve chamar — substitui
    a chamada direta a parse_ssh_log().
    """
    if not raw_line:
        return None

    for parser in _PARSERS:
        try:
            resultado = parser(raw_line)
            if resultado is not None:
                return resultado
        except Exception as e:
            # Falha isolada em um parser não deve quebrar os outros
            logger.warning("Erro no parser %s: %s | linha: %.80s", parser.__name__, e, raw_line)

    return None


# ===========================================================================
# CONTAGEM DE FALHAS — count_failed_logins()
#
# Mantida sem alteração. Continua sendo usada pelo check_brute_force()
# da detecção de brute force (Semana 5).
# ===========================================================================

def count_failed_logins(LogEntryModel, host_id: int, ip_origem: str, janela_horas: float = 1) -> int:
    """
    Conta tentativas de login SSH com falha de um determinado IP
    dentro de uma janela de tempo.

    Parâmetros:
        LogEntryModel  — modelo SQLAlchemy injetado (evita import circular com app.py)
        host_id        — ID do host monitorado
        ip_origem      — IP suspeito a ser verificado
        janela_horas   — tamanho da janela em horas (padrão: 1 hora)
                         Para 60 segundos: janela_horas=1/60

    Retorna:
        int — número de falhas encontradas na janela. Retorna 0 em caso de
        qualquer erro para não interromper o fluxo de recebimento de logs.

    Sobre a query:
        Usa os operadores JSONB nativos do PostgreSQL (->>), que aproveitam
        os índices parciais do banco criados pela Beatriz.
        É muito mais eficiente do que carregar os objetos e filtrar em Python.

        SQL equivalente gerado:
            SELECT COUNT(*) FROM logs
            WHERE host_id      = :host_id
              AND log_type     = 'auth'
              AND timestamp   >= :inicio_janela
              AND parsed_data->>'status'    = 'failed'
              AND parsed_data->>'ip_origem' = :ip_origem
    """
    from sqlalchemy import text as sa_text

    inicio_janela = datetime.utcnow() - timedelta(hours=janela_horas)

    try:
        contagem = LogEntryModel.query.filter(
            LogEntryModel.host_id   == host_id,
            LogEntryModel.log_type  == 'auth',
            LogEntryModel.timestamp >= inicio_janela,
            sa_text("parsed_data->>'status' = 'failed'"),
            sa_text(f"parsed_data->>'ip_origem' = '{ip_origem}'"),
        ).count()

        return contagem

    except Exception as erro:
        logger.error(
            "Erro ao contar logins falhos (host_id=%s, ip=%s): %s",
            host_id, ip_origem, erro,
        )
        return 0