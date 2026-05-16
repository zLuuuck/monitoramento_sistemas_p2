# app/utils/parsers.py
# Funções de parsing de logs e contagem de eventos de segurança
# Semana 4 — parse_ssh_log() e count_failed_logins()

import re
import logging
from datetime import datetime, timedelta

# Logger do módulo — usado onde app.logger não está disponível
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# REGEX — linhas do /var/log/auth.log geradas pelo sshd
#
# Exemplos de linhas reconhecidas:
#
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
    r'(?:invalid user\s+)?'                  # prefixo opcional — aparece quando o usuário não existe no sistema
    r'(\S+)'                                 # grupo 2: nome do usuário
    r'\s+from\s+'
    r'((?:\d{1,3}\.){3}\d{1,3})',            # grupo 3: IPv4 de origem
)


def parse_ssh_log(raw_line: str) -> dict | None:
    """
    Extrai campos estruturados de uma linha bruta do auth.log referente ao sshd.

    Retorna um dicionário se a linha for um evento SSH reconhecido, ou None
    caso contrário (ex: linhas de sudo, PAM, cron e outros serviços que
    também escrevem no auth.log).

    Campos do dicionário retornado:
        ip_origem (str) — IP do cliente que tentou se autenticar
        usuario   (str) — nome do usuário alvo da tentativa
        status    (str) — "failed" ou "accepted"

    Os nomes dos campos batem com os índices JSONB criados pela Beatriz:
        idx_logs_auth_ip     — (parsed_data->>'ip_origem') WHERE log_type = 'auth'
        idx_logs_auth_failed — timestamp WHERE log_type = 'auth'
                               AND parsed_data->>'status' = 'failed'
    Isso garante que as queries da Semana 5 usem índice e não façam full scan.
    """
    if not raw_line:
        return None

    correspondencia = _PADRAO_SSH.search(raw_line)

    if not correspondencia:
        # Linha de auth.log que não é evento SSH de login
        return None

    status_raw, usuario, ip_origem = correspondencia.groups()

    # Normaliza o resultado para "failed" ou "accepted"
    status = 'failed' if 'Failed' in status_raw else 'accepted'

    return {
        'ip_origem': ip_origem,
        'usuario':   usuario,
        'status':    status,
    }


def count_failed_logins(LogEntryModel, host_id: int, ip_origem: str, janela_horas: float = 1) -> int:
    """
    Conta tentativas de login SSH com falha de um determinado IP
    dentro de uma janela de tempo.

    Será chamada pela função check_brute_force() na Semana 5.

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

    # Início da janela de tempo calculado a partir de agora
    inicio_janela = datetime.utcnow() - timedelta(hours=janela_horas)

    try:
        contagem = LogEntryModel.query.filter(
            LogEntryModel.host_id   == host_id,
            LogEntryModel.log_type  == 'auth',
            LogEntryModel.timestamp >= inicio_janela,
            # Operadores JSONB do PostgreSQL — batem nos índices parciais do banco
            sa_text("parsed_data->>'status' = 'failed'"),
            sa_text(f"parsed_data->>'ip_origem' = '{ip_origem}'"),
        ).count()

        return contagem

    except Exception as erro:
        # Falha silenciosa: loga o erro mas não interrompe o fluxo principal
        logger.error(
            "Erro ao contar logins falhos (host_id=%s, ip=%s): %s",
            host_id, ip_origem, erro,
        )
        return 0