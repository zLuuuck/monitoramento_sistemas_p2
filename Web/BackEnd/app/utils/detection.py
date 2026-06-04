# app/utils/detection.py
# Funções de detecção de ameaças de segurança e recursos.
# check_brute_force()      — detecta ataques de força bruta SSH.
# check_port_scan()        — registra alerta quando o agente detecta varredura de portas.
# check_resource_alert()   — alerta quando CPU, memória ou disco ultrapassam 80%.

import json
import logging
import os
from datetime import datetime

from .parsers import count_failed_logins
from .teams import enviar_alerta_teams
from .notifier import enviar_alerta_email

logger = logging.getLogger(__name__)


def _get_email_recipients(db) -> list:
    """Lê destinatários de email da tabela app_settings; fallback para ALERT_RECIPIENT do .env."""
    try:
        row = db.session.execute(
            db.text("SELECT value FROM app_settings WHERE key = 'email_recipients'")
        ).fetchone()
        if row and row[0]:
            parsed = json.loads(row[0])
            if parsed:
                return parsed
    except Exception:
        pass
    fallback = os.getenv('ALERT_RECIPIENT', '')
    return [fallback] if fallback else []

def _notificacao_habilitada(db, canal: str) -> bool:
    """Lê o toggle notify_teams / notify_email de app_settings.
    Fallback: teams=True, email=False (espelha os defaults de garantir_schema_notifications).
    """
    defaults = {'teams': True, 'email': False}
    try:
        row = db.session.execute(
            db.text("SELECT value FROM app_settings WHERE key = :key"),
            {'key': f'notify_{canal}'},
        ).fetchone()
        if row and row[0] is not None:
            return row[0].lower() == 'true'
    except Exception:
        pass
    return defaults.get(canal, False)


LIMIAR_BRUTE_FORCE = 5
JANELA_HORAS = 1 / 60

_THRESHOLD_KEYS = {
    'cpu_high':  'threshold_cpu',
    'mem_high':  'threshold_mem',
    'disk_high': 'threshold_disk',
}


def _get_threshold(db, alert_type: str) -> float:
    """Lê o limiar de recurso da tabela app_settings; fallback para 80.0."""
    key = _THRESHOLD_KEYS.get(alert_type)
    if not key:
        return 80.0
    try:
        row = db.session.execute(
            db.text("SELECT value FROM app_settings WHERE key = :key"),
            {'key': key},
        ).fetchone()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        pass
    return 80.0


def check_brute_force(db, LogEntryModel, AlertModel, host_id: int, ip_origem: str,
                      hostname: str = '', host_ip: str = '') -> bool:
    """
    Verifica se um IP está realizando ataque de força bruta SSH contra um host.

    Fluxo:
        1. Conta falhas SSH do ip_origem nos últimos 60 segundos via count_failed_logins()
        2. Se >= LIMIAR_BRUTE_FORCE falhas: verifica se já existe alerta ativo
           (resolved=False) para a combinação host_id + ip_origem + "brute_force"
        3. Se não existir alerta ativo: cria um novo e salva no banco
        4. Retorna True se um alerta novo foi criado, False caso contrário

    Parâmetros:
        db            — instância do SQLAlchemy (para db.session)
        LogEntryModel — modelo de logs (injetado para evitar import circular)
        AlertModel    — modelo de alertas (injetado para evitar import circular)
        host_id       — ID do host monitorado
        ip_origem     — IP suspeito extraído do parsed_data do log SSH

    Retorna:
        bool — True se um novo alerta foi criado, False caso contrário.
        Em caso de erro interno, retorna False silenciosamente para não
        interromper o fluxo de recebimento de logs.
    """
    try:
        total_falhas = count_failed_logins(
            LogEntryModel,
            host_id,
            ip_origem,
            janela_horas=JANELA_HORAS,
        )

        if total_falhas < LIMIAR_BRUTE_FORCE:
            return False

        logger.warning(
            'Possível brute force detectado | host_id=%s | ip=%s | falhas=%s',
            host_id, ip_origem, total_falhas,
        )

        alerta_existente = AlertModel.query.filter_by(
            host_id    = host_id,
            source_ip  = ip_origem,
            alert_type = 'brute_force',
            resolved   = False,
        ).first()

        if alerta_existente:
            logger.info(
                'Alerta de brute force já ativo (id=%s) | host_id=%s | ip=%s',
                alerta_existente.id, host_id, ip_origem,
            )
            return False

        novo_alerta = AlertModel(
            host_id     = host_id,
            alert_type  = 'brute_force',
            source_ip   = ip_origem,
            timestamp   = datetime.utcnow(),
            severity    = 'high',
            metodos     = 'password',
            message     = f'Força bruta SSH: {total_falhas} tentativas em 60s de {ip_origem}',
            resolved    = False,
            resolved_at = None,
        )

        db.session.add(novo_alerta)
        db.session.commit()

        logger.warning(
            'ALERTA CRIADO | brute_force | host_id=%s | ip=%s | falhas=%s | alerta_id=%s',
            host_id, ip_origem, total_falhas, novo_alerta.id,
        )

        if _notificacao_habilitada(db, 'teams'):
            enviar_alerta_teams(
                titulo    = f'Brute Force SSH — {hostname or f"Host {host_id}"}',
                mensagem  = novo_alerta.message,
                severidade= 'critical',
                origem    = f'{hostname} ({host_ip})' if hostname else f'host-{host_id}',
            )
        else:
            logger.info('brute_force host=%s: Teams skip — notify_teams=false', host_id)

        if _notificacao_habilitada(db, 'email'):
            enviar_alerta_email(
                alert_type = 'brute_force',
                host_id    = host_id,
                source_ip  = ip_origem,
                message    = novo_alerta.message,
                severity   = 'high',
                hostname   = hostname,
                host_ip    = host_ip,
                recipients = _get_email_recipients(db),
            )
        else:
            logger.info('brute_force host=%s: email skip — notify_email=false', host_id)

        return True

    except Exception as erro:
        db.session.rollback()
        logger.error(
            'Erro em check_brute_force (host_id=%s, ip=%s): %s',
            host_id, ip_origem, erro,
        )
        return False


def check_port_scan(db, AlertModel, host_id: int, ip_origem: str, port_count: int = 0,
                    hostname: str = '', host_ip: str = '') -> bool:
    """
    Registra um alerta de port scan quando o agente sinaliza detecção.

    O agente realiza a análise de SYN_SENT no lado dele e envia
    port_scan_detected=true no payload. O backend apenas persiste o alerta,
    suprimindo duplicatas dentro de uma janela de 2 minutos — tempo suficiente
    para cobrir um scan em andamento (agente reporta a cada ~6s por ~60s),
    mas que permite novos alertas quando um scan diferente ocorrer depois.

    Fluxo:
        1. Verifica se já existe alerta não-resolvido criado nos últimos 2 min
           para host_id + ip_origem + "port_scan"
        2. Se não existir: cria novo alerta com severity="high"
        3. Retorna True se alerta foi criado, False caso contrário

    Parâmetros:
        db         — instância do SQLAlchemy (para db.session)
        AlertModel — modelo de alertas (injetado para evitar import circular)
        host_id    — ID do host onde o port scan foi detectado
        ip_origem  — IP do atacante (fornecido pelo agente via scan_sources)
        port_count — número de portas distintas varridas (0 = desconhecido)

    Retorna:
        bool — True se um novo alerta foi criado, False caso contrário.
        Falha silenciosa (try/except) — nunca interrompe o salvamento das conexões.
    """
    from datetime import timedelta
    _COOLDOWN = timedelta(minutes=2)

    try:
        cutoff = datetime.utcnow() - _COOLDOWN
        alerta_recente = AlertModel.query.filter(
            AlertModel.host_id    == host_id,
            AlertModel.source_ip  == ip_origem,
            AlertModel.alert_type == 'port_scan',
            AlertModel.resolved   == False,
            AlertModel.timestamp  >= cutoff,
        ).first()

        if alerta_recente:
            logger.info(
                'Alerta de port scan recente (id=%s, criado=%s) | host_id=%s | ip=%s',
                alerta_recente.id, alerta_recente.timestamp, host_id, ip_origem,
            )
            return False

        msg = (
            f'Varredura de portas: {port_count} portas distintas em 60s de {ip_origem}'
            if port_count
            else f'Varredura de portas detectada de {ip_origem}'
        )
        novo_alerta = AlertModel(
            host_id     = host_id,
            alert_type  = 'port_scan',
            source_ip   = ip_origem,
            timestamp   = datetime.utcnow(),
            severity    = 'high',
            metodos     = None,
            message     = msg,
            resolved    = False,
            resolved_at = None,
        )

        db.session.add(novo_alerta)
        db.session.commit()

        logger.warning(
            'ALERTA CRIADO | port_scan | host_id=%s | ip=%s | alerta_id=%s',
            host_id, ip_origem, novo_alerta.id,
        )

        if _notificacao_habilitada(db, 'teams'):
            enviar_alerta_teams(
                titulo    = f'Port Scan detectado — {hostname or f"Host {host_id}"}',
                mensagem  = msg,
                severidade= 'critical',
                origem    = f'{hostname} ({host_ip})' if hostname else f'host-{host_id}',
            )
        else:
            logger.info('port_scan host=%s: Teams skip — notify_teams=false', host_id)

        if _notificacao_habilitada(db, 'email'):
            enviar_alerta_email(
                alert_type = 'port_scan',
                host_id    = host_id,
                source_ip  = ip_origem,
                message    = msg,
                severity   = 'high',
                hostname   = hostname,
                host_ip    = host_ip,
                recipients = _get_email_recipients(db),
            )
        else:
            logger.info('port_scan host=%s: email skip — notify_email=false', host_id)

        return True

    except Exception as erro:
        db.session.rollback()
        logger.error(
            'Erro em check_port_scan (host_id=%s, ip=%s): %s',
            host_id, ip_origem, erro,
        )
        return False


def check_resource_alert(db, AlertModel, host_id: int, alert_type: str,
                         valor: float,
                         hostname: str = '', host_ip: str = '') -> bool:
    """
    Cria um alerta de recurso (cpu_high / mem_high / disk_high) se valor > limiar
    e não houver alerta ativo do mesmo tipo para o host.

    O limiar é lido de app_settings (threshold_cpu / threshold_mem / threshold_disk);
    fallback para 80.0 se a chave não existir.

    Parâmetros:
        db         — instância do SQLAlchemy
        AlertModel — modelo de alertas (injetado para evitar import circular)
        host_id    — ID do host monitorado
        alert_type — 'cpu_high', 'mem_high' ou 'disk_high'
        valor      — valor atual da métrica (%)

    Retorna:
        bool — True se um novo alerta foi criado, False caso contrário.
        Falha silenciosa — nunca interrompe o fluxo de salvamento de métricas.
    """
    limiar = _get_threshold(db, alert_type)
    if valor is None or valor <= limiar:
        return False

    try:
        alerta_existente = AlertModel.query.filter_by(
            host_id    = host_id,
            alert_type = alert_type,
            resolved   = False,
        ).first()

        if alerta_existente:
            return False

        nomes = {
            'cpu_high':  'CPU',
            'mem_high':  'Memória',
            'disk_high': 'Disco',
        }
        recurso = nomes.get(alert_type, alert_type)
        msg = f'{recurso} em {valor:.1f}% — acima do limiar de {limiar:.0f}% no host {host_id}'

        novo_alerta = AlertModel(
            host_id     = host_id,
            alert_type  = alert_type,
            source_ip   = None,
            timestamp   = datetime.utcnow(),
            severity    = 'high',
            metodos     = None,
            message     = msg,
            resolved    = False,
            resolved_at = None,
        )

        db.session.add(novo_alerta)
        db.session.commit()

        logger.warning(
            'ALERTA CRIADO | %s | host_id=%s | valor=%.1f%% | alerta_id=%s',
            alert_type, host_id, valor, novo_alerta.id,
        )

        if _notificacao_habilitada(db, 'teams'):
            enviar_alerta_teams(
                titulo    = f'{recurso} alta — {hostname or f"Host {host_id}"}',
                mensagem  = msg,
                severidade= 'warning',
                origem    = f'{hostname} ({host_ip})' if hostname else f'host-{host_id}',
            )
        else:
            logger.info('%s host=%s: Teams skip — notify_teams=false', alert_type, host_id)

        if _notificacao_habilitada(db, 'email'):
            enviar_alerta_email(
                alert_type = alert_type,
                host_id    = host_id,
                source_ip  = '',
                message    = msg,
                severity   = 'high',
                hostname   = hostname,
                host_ip    = host_ip,
                recipients = _get_email_recipients(db),
            )
        else:
            logger.info('%s host=%s: email skip — notify_email=false', alert_type, host_id)

        return True

    except Exception as erro:
        db.session.rollback()
        logger.error(
            'Erro em check_resource_alert (%s, host_id=%s): %s',
            alert_type, host_id, erro,
        )
        return False