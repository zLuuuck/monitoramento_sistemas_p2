# app/utils/teams.py
# Envia alertas para o canal do Microsoft Teams via Power Automate webhook.
# Falha silenciosa — nunca deve interromper o fluxo principal de detecção.

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

_TZ_BRT = ZoneInfo('America/Sao_Paulo')

logger = logging.getLogger(__name__)


def enviar_alerta_teams(titulo: str, mensagem: str, severidade: str = 'info',
                        origem: str = 'backend', link: str = '') -> bool:
    """
    Dispara uma notificação no Teams via Power Automate webhook.

    Retorna True se enviado com sucesso, False silenciosamente em caso de falha.
    """
    url = os.getenv('TEAMS_WEBHOOK_URL', '')
    if not url:
        logger.warning('TEAMS_WEBHOOK_URL não configurado — alerta não enviado')
        return False

    sev_lower = severidade.lower()

    # Emojis idênticos ao notifier.py
    icone = {
        'critical': '🚨',
        'high':     '🔴',
        'warning':  '🟡',
        'medium':   '🟡',
        'info':     '🔵',
        'low':      '🔵',
    }.get(sev_lower, '⚪')

    # cor_card é o "style" do container do Adaptive Card no Power Automate
    cor_card = {
        'critical': 'attention',
        'high':     'attention',
        'warning':  'warning',
        'medium':   'warning',
        'info':     'accent',
        'low':      'accent',
    }.get(sev_lower, 'attention')

    payload = {
        'titulo':     titulo,
        'mensagem':   mensagem,
        'severidade': severidade.upper(),
        'icone':      icone,
        'origem':     origem,
        'timestamp':  datetime.now(_TZ_BRT).strftime('%d/%m/%Y %H:%M:%S (BRT)'),
        'link':       link,
        'cor_card':   cor_card,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)

        if not r.ok:
            logger.warning(
                'Falha ao enviar alerta Teams "%s" | status=%s | body=%s',
                titulo, r.status_code, r.text[:300],
            )
            return False

        logger.warning('Alerta Teams ENVIADO: %s | status=%s', titulo, r.status_code)
        return True

    except requests.exceptions.Timeout:
        logger.warning('Timeout ao enviar alerta Teams "%s"', titulo)
        return False
    except Exception as erro:
        logger.warning('Erro ao enviar alerta Teams "%s": %s', titulo, erro)
        return False
