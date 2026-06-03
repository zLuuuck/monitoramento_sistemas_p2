# app/utils/notifier.py
# Módulo de notificação por email para alertas de segurança.
# Usa smtplib (stdlib Python) com Gmail via App Password (STARTTLS, porta 587).
# Semana 7: implementação inicial — brute force SSH e port scan.

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# Credenciais lidas do ambiente — nunca hardcoded
_SMTP_EMAIL      = os.getenv('SMTP_EMAIL', '')
_SMTP_PASSWORD   = os.getenv('SMTP_PASSWORD', '')
_ALERT_RECIPIENT = os.getenv('ALERT_RECIPIENT', '')

_SMTP_HOST = 'smtp.gmail.com'
_SMTP_PORT = 587

# Mapeamento de severidade para emoji no assunto
_SEVERITY_EMOJI = {
    'low':      '🟡',
    'medium':   '🟠',
    'high':     '🔴',
    'critical': '🚨',
}

# Mapeamento de tipo de alerta para nome legível
_TIPO_LEGIVEL = {
    'brute_force': 'Força Bruta SSH',
    'port_scan':   'Port Scan',
}


def enviar_alerta_email(
    alert_type: str,
    host_id: int,
    source_ip: str,
    message: str,
    severity: str,
) -> bool:
    """
    Envia um email de alerta de segurança via smtplib (Gmail + App Password).

    Parâmetros:
        alert_type — tipo do alerta ("brute_force" ou "port_scan")
        host_id    — ID do host afetado
        source_ip  — IP de origem do ataque
        message    — mensagem descritiva do alerta
        severity   — severidade ("low", "medium", "high", "critical")

    Retorna:
        bool — True se enviado com sucesso, False em caso de falha.
        Falha NUNCA interrompe o fluxo principal (try/except completo).
    """
    # Verifica configuração mínima
    if not all([_SMTP_EMAIL, _SMTP_PASSWORD, _ALERT_RECIPIENT]):
        logger.warning(
            'notifier: variáveis SMTP não configuradas — email não enviado.'
        )
        return False

    try:
        emoji     = _SEVERITY_EMOJI.get(severity.lower(), '⚠️')
        tipo      = _TIPO_LEGIVEL.get(alert_type, alert_type.upper())
        timestamp = datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC')

        assunto = f'{emoji} [ALERTA][{severity.upper()}] {tipo} detectado — Host {host_id}'

        # Corpo em texto simples (legível em qualquer cliente)
        corpo_txt = f"""
ALERTA DE SEGURANÇA — Sistema de Monitoramento PADS3
=====================================================

Tipo:        {tipo}
Severidade:  {severity.upper()}
Host ID:     {host_id}
IP de Origem: {source_ip}
Data/Hora:   {timestamp}

Descrição:
{message}

-----------------------------------------------------
Este email foi gerado automaticamente pelo backend
de monitoramento. Acesse o painel para mais detalhes.
        """.strip()

        # Corpo HTML (visual melhorado)
        cor_severidade = {
            'low': '#f0ad4e', 'medium': '#e67e22',
            'high': '#e74c3c', 'critical': '#8e1a0e',
        }.get(severity.lower(), '#e74c3c')

        corpo_html = f"""
<html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
  <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;
              border-top:5px solid {cor_severidade};padding:30px;">
    <h2 style="color:{cor_severidade};margin-top:0;">{emoji} Alerta de Segurança</h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tr style="background:#f9f9f9;">
        <td style="padding:8px 12px;font-weight:bold;width:140px;">Tipo</td>
        <td style="padding:8px 12px;">{tipo}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;font-weight:bold;">Severidade</td>
        <td style="padding:8px 12px;">
          <span style="background:{cor_severidade};color:#fff;padding:2px 10px;
                       border-radius:4px;">{severity.upper()}</span>
        </td>
      </tr>
      <tr style="background:#f9f9f9;">
        <td style="padding:8px 12px;font-weight:bold;">Host ID</td>
        <td style="padding:8px 12px;">{host_id}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;font-weight:bold;">IP de Origem</td>
        <td style="padding:8px 12px;font-family:monospace;">{source_ip}</td>
      </tr>
      <tr style="background:#f9f9f9;">
        <td style="padding:8px 12px;font-weight:bold;">Data/Hora</td>
        <td style="padding:8px 12px;">{timestamp}</td>
      </tr>
    </table>
    <div style="background:#f9f9f9;padding:12px;border-radius:4px;
                border-left:4px solid {cor_severidade};">
      <strong>Descrição:</strong><br>{message}
    </div>
    <p style="color:#999;font-size:12px;margin-top:24px;margin-bottom:0;">
      Email gerado automaticamente pelo backend PADS3.
      Acesse o painel para resolver o alerta.
    </p>
  </div>
</body></html>
        """.strip()

        # Monta mensagem MIME multipart (texto + HTML)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From']    = _SMTP_EMAIL
        msg['To']      = _ALERT_RECIPIENT
        msg.attach(MIMEText(corpo_txt, 'plain', 'utf-8'))
        msg.attach(MIMEText(corpo_html, 'html',  'utf-8'))

        # Envia via Gmail STARTTLS
        contexto = ssl.create_default_context()
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as servidor:
            servidor.ehlo()
            servidor.starttls(context=contexto)
            servidor.ehlo()
            servidor.login(_SMTP_EMAIL, _SMTP_PASSWORD)
            servidor.sendmail(_SMTP_EMAIL, _ALERT_RECIPIENT, msg.as_string())

        logger.info(
            'Email de alerta enviado | tipo=%s | host_id=%s | ip=%s',
            alert_type, host_id, source_ip,
        )
        return True

    except Exception as erro:
        # Falha silenciosa — nunca interrompe o fluxo principal
        logger.error(
            'Erro ao enviar email de alerta (tipo=%s, host_id=%s, ip=%s): %s',
            alert_type, host_id, source_ip, erro,
        )
        return False