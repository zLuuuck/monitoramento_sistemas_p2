# app/utils/teams.py
# Envia alertas para o canal do Microsoft Teams via Power Automate webhook.
# Falha silenciosa — nunca deve interromper o fluxo principal de detecção.

import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL', '')


def enviar_alerta_teams(titulo: str, mensagem: str, severidade: str = 'info',
                        origem: str = 'backend', link: str = '') -> bool:
    """
    Dispara uma notificação no Teams via Power Automate webhook.

    Retorna True se enviado com sucesso, False silenciosamente em caso de falha.
    """
    if not WEBHOOK_URL:
        logger.debug('TEAMS_WEBHOOK_URL não configurado — alerta não enviado')
        return False

    payload = {
        'titulo':     titulo,
        'mensagem':   mensagem,
        'severidade': severidade,
        'origem':     origem,
        'timestamp':  datetime.now().astimezone().isoformat(timespec='seconds'),
        'link':       link,
    }

    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        logger.info('Alerta Teams enviado: %s | status=%s', titulo, r.status_code)
        return True
    except Exception as erro:
        logger.warning('Falha ao enviar alerta Teams ("%s"): %s', titulo, erro)
        return False
