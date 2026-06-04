# app/utils/notifier.py
# Módulo de notificação por email para alertas de segurança.
# Usa smtplib (stdlib Python) com Gmail via App Password (STARTTLS, porta 587).

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

_SEVERITY_EMOJI = {
    'low':      '🟡',
    'medium':   '🟠',
    'high':     '🔴',
    'critical': '🚨',
}

_TIPO_LEGIVEL = {
    'brute_force': 'Força Bruta SSH',
    'port_scan':   'Port Scan',
    'cpu_high':    'CPU Alta',
    'mem_high':    'Memória Alta',
    'disk_high':   'Disco Alto',
}

_COR_SEVERIDADE = {
    'low':      '#d97706',
    'medium':   '#ea580c',
    'high':     '#dc2626',
    'critical': '#7f1d1d',
}


def enviar_alerta_email(
    alert_type: str,
    host_id: int,
    source_ip: str,
    message: str,
    severity: str,
    hostname: str = '',
    host_ip: str = '',
    recipients: list | None = None,
) -> bool:
    """
    Envia email de alerta para todos os destinatários em `recipients`.
    Se `recipients` for None ou vazio, usa ALERT_RECIPIENT do .env como fallback.
    Falha NUNCA interrompe o fluxo principal (try/except completo).
    """
    destinatarios = [r for r in (recipients or []) if r]
    if not destinatarios:
        if _ALERT_RECIPIENT:
            destinatarios = [_ALERT_RECIPIENT]

    if not all([_SMTP_EMAIL, _SMTP_PASSWORD]) or not destinatarios:
        logger.warning('notifier: SMTP ou destinatários não configurados — email não enviado.')
        return False

    try:
        emoji     = _SEVERITY_EMOJI.get(severity.lower(), '⚠️')
        tipo      = _TIPO_LEGIVEL.get(alert_type, alert_type.upper())
        cor       = _COR_SEVERIDADE.get(severity.lower(), '#dc2626')
        timestamp = datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC')

        host_display = hostname if hostname else f'Host {host_id}'
        assunto = f'{emoji} [ALERTA][{severity.upper()}] {tipo} — {host_display}'

        # Linha de IP do atacante — só aparece quando há source_ip
        ip_atacante_txt = f'IP do Atacante: {source_ip}\n' if source_ip else ''
        ip_atacante_html = (
            f'<tr style="background:color-mix(in srgb,{cor} 8%,#fff);">'
            f'<td class="lbl" style="padding:10px 8px 10px 0;color:#6b7280;width:140px;vertical-align:top;font-size:14px;">IP do Atacante</td>'
            f'<td class="val" style="padding:10px 0;color:#111827;font-family:monospace;font-size:14px;">{source_ip}</td>'
            f'</tr>'
        ) if source_ip else ''

        host_ip_display = host_ip if host_ip else '—'

        corpo_txt = f"""ALERTA DE SEGURANÇA — Sistema de Monitoramento PADS3
=====================================================

Tipo:         {tipo}
Severidade:   {severity.upper()}
Host:         {host_display}
IP do Host:   {host_ip_display}
{ip_atacante_txt}Data/Hora:    {timestamp}

Descrição:
{message}

-----------------------------------------------------
Acesse o painel: http://painel.monitoramento.lan
""".strip()

        corpo_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body{{margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;}}
  @media(prefers-color-scheme:dark){{
    body{{background:#0d0d0d!important;}}
    .wrap{{background:#1c1c1e!important;border-color:#2c2c2e!important;}}
    .lbl{{color:#9ca3af!important;}}
    .val{{color:#f3f4f6!important;}}
    .row-alt{{background:#252528!important;}}
    .desc{{background:#252528!important;color:#f3f4f6!important;}}
    .foot{{color:#6b7280!important;border-top-color:#2c2c2e!important;}}
  }}
</style>
</head>
<body>
<div style="padding:24px 16px;">
<div class="wrap" style="max-width:600px;margin:auto;background:#fff;border-radius:10px;border:1px solid #e5e7eb;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.08);">

  <!-- Header -->
  <div style="background:{cor};padding:24px 28px;">
    <p style="margin:0 0 4px;font-size:11px;color:rgba(255,255,255,.75);text-transform:uppercase;letter-spacing:1.2px;">Sistema de Monitoramento PADS3</p>
    <h1 style="margin:0 0 10px;color:#fff;font-size:20px;font-weight:700;">{emoji}&nbsp;{tipo}</h1>
    <span style="display:inline-block;background:rgba(255,255,255,.22);color:#fff;font-size:11px;font-weight:700;padding:3px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:.8px;">{severity.upper()}</span>
  </div>

  <!-- Detalhes -->
  <div style="padding:24px 28px 8px;">
    <table style="width:100%;border-collapse:collapse;">
      <tr>
        <td class="lbl" style="padding:10px 8px 10px 0;color:#6b7280;width:140px;vertical-align:top;font-size:14px;">Host</td>
        <td class="val" style="padding:10px 0;color:#111827;font-size:14px;font-weight:600;">{host_display}</td>
      </tr>
      <tr class="row-alt" style="background:#f9fafb;">
        <td class="lbl" style="padding:10px 8px;color:#6b7280;width:140px;vertical-align:top;font-size:14px;">IP do Host</td>
        <td class="val" style="padding:10px 8px 10px 0;color:#111827;font-family:monospace;font-size:14px;">{host_ip_display}</td>
      </tr>
      {ip_atacante_html}
      <tr>
        <td class="lbl" style="padding:10px 8px 10px 0;color:#6b7280;width:140px;vertical-align:top;font-size:14px;">Data/Hora</td>
        <td class="val" style="padding:10px 0;color:#111827;font-size:14px;">{timestamp}</td>
      </tr>
    </table>
  </div>

  <!-- Descrição -->
  <div style="padding:4px 28px 24px;">
    <div class="desc" style="background:#f9fafb;border-left:4px solid {cor};padding:14px 16px;border-radius:0 6px 6px 0;">
      <p style="margin:0 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#9ca3af;">Descrição</p>
      <p style="margin:0;color:#111827;font-size:14px;line-height:1.6;">{message}</p>
    </div>
  </div>

  <!-- Botão -->
  <div style="padding:0 28px 28px;text-align:center;">
    <a href="http://painel.monitoramento.lan"
       style="display:inline-block;background:{cor};color:#fff;text-decoration:none;padding:13px 36px;border-radius:6px;font-weight:700;font-size:15px;letter-spacing:.3px;">
      Abrir Painel
    </a>
  </div>

  <!-- Rodapé -->
  <div class="foot" style="padding:14px 28px;border-top:1px solid #f3f4f6;text-align:center;">
    <p style="margin:0;font-size:11px;color:#9ca3af;">Gerado automaticamente pelo backend PADS3</p>
  </div>

</div>
</div>
</body>
</html>""".strip()

        # Envia para cada destinatário individualmente
        contexto = ssl.create_default_context()
        enviados = 0
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as servidor:
            servidor.ehlo()
            servidor.starttls(context=contexto)
            servidor.ehlo()
            servidor.login(_SMTP_EMAIL, _SMTP_PASSWORD)
            for dest in destinatarios:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = assunto
                msg['From']    = _SMTP_EMAIL
                msg['To']      = dest
                msg.attach(MIMEText(corpo_txt, 'plain', 'utf-8'))
                msg.attach(MIMEText(corpo_html, 'html',  'utf-8'))
                servidor.sendmail(_SMTP_EMAIL, dest, msg.as_string())
                enviados += 1

        logger.info(
            'Email de alerta enviado | tipo=%s | host_id=%s | ip=%s | destinatários=%d',
            alert_type, host_id, source_ip, enviados,
        )
        return True

    except Exception as erro:
        logger.error(
            'Erro ao enviar email de alerta (tipo=%s, host_id=%s, ip=%s): %s',
            alert_type, host_id, source_ip, erro,
        )
        return False