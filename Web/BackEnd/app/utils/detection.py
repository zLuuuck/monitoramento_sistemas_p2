# app/utils/detection.py
# Funções de detecção de ameaças de segurança.
# Semana 5: check_brute_force() — detecta ataques de força bruta SSH.
# Semana 6: check_port_scan()   — registra alerta quando o agente detecta varredura de portas.

import logging
from datetime import datetime

from .parsers import count_failed_logins

# Logger do módulo
logger = logging.getLogger(__name__)

# Limiar de tentativas falhas para disparar alerta de brute force
LIMIAR_BRUTE_FORCE = 5

# Janela de tempo monitorada em horas (1/60 = 60 segundos)
JANELA_HORAS = 1 / 60


def check_brute_force(db, LogEntryModel, AlertModel, host_id: int, ip_origem: str) -> bool:
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
        # Passo 1: conta falhas SSH deste IP na janela de 60 segundos
        total_falhas = count_failed_logins(
            LogEntryModel,
            host_id,
            ip_origem,
            janela_horas=JANELA_HORAS,
        )

        # Abaixo do limiar — não é brute force (ainda)
        if total_falhas < LIMIAR_BRUTE_FORCE:
            return False

        logger.warning(
            'Possível brute force detectado | host_id=%s | ip=%s | falhas=%s',
            host_id, ip_origem, total_falhas,
        )

        # Passo 2: verifica se já existe um alerta ativo para este host + IP
        alerta_existente = AlertModel.query.filter_by(
            host_id    = host_id,
            source_ip  = ip_origem,
            alert_type = 'brute_force',
            resolved   = False,
        ).first()

        if alerta_existente:
            # Alerta já existe e ainda está ativo — não cria duplicata
            logger.info(
                'Alerta de brute force já ativo (id=%s) | host_id=%s | ip=%s',
                alerta_existente.id, host_id, ip_origem,
            )
            return False

        # Passo 3: cria novo alerta de brute force
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

        return True

    except Exception as erro:
        # Falha silenciosa — nunca deve interromper o salvamento do log
        db.session.rollback()
        logger.error(
            'Erro em check_brute_force (host_id=%s, ip=%s): %s',
            host_id, ip_origem, erro,
        )
        return False


def check_port_scan(db, AlertModel, host_id: int, ip_origem: str, port_count: int = 0) -> bool:
    """
    Registra um alerta de port scan quando o agente sinaliza detecção.

    O agente realiza a análise de SYN_SENT no lado dele e envia
    port_scan_detected=true no payload. O backend apenas persiste o alerta,
    evitando duplicatas para o mesmo host enquanto o alerta estiver ativo.

    Fluxo:
        1. Verifica se já existe alerta ativo (resolved=False) para
           host_id + ip_origem + "port_scan"
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
    try:
        # Passo 1: verifica se já existe alerta ativo de port scan para este host
        alerta_existente = AlertModel.query.filter_by(
            host_id    = host_id,
            source_ip  = ip_origem,
            alert_type = 'port_scan',
            resolved   = False,
        ).first()

        if alerta_existente:
            # Alerta já ativo — não cria duplicata
            logger.info(
                'Alerta de port scan já ativo (id=%s) | host_id=%s | ip=%s',
                alerta_existente.id, host_id, ip_origem,
            )
            return False

        # Passo 2: cria novo alerta de port scan
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

        return True

    except Exception as erro:
        # Falha silenciosa — nunca deve interromper o salvamento das conexões
        db.session.rollback()
        logger.error(
            'Erro em check_port_scan (host_id=%s, ip=%s): %s',
            host_id, ip_origem, erro,
        )
        return False