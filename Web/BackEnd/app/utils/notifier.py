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
from zoneinfo import ZoneInfo

_TZ_BRT = ZoneInfo('America/Sao_Paulo')

logger = logging.getLogger(__name__)

# Credenciais lidas do ambiente — nunca hardcoded
_SMTP_EMAIL      = os.getenv('SMTP_EMAIL', '')
_SMTP_PASSWORD   = os.getenv('SMTP_PASSWORD', '')
_ALERT_RECIPIENT = os.getenv('ALERT_RECIPIENT', '')

_SMTP_HOST = 'smtp.gmail.com'
_SMTP_PORT = 587

_SEVERITY_EMOJI = {
    'low':      '🔵',
    'medium':   '🟡',
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

# Cores de severidade (dark mode — paleta Tailwind)
_COR_SEVERIDADE = {
    'low':      '#60a5fa',   # blue-400
    'medium':   '#fbbf24',   # amber-400
    'high':     '#f87171',   # red-400
    'critical': '#fca5a5',   # red-300
}

_COR_BADGE_BG = {
    'low':      'rgba(96,165,250,0.15)',
    'medium':   'rgba(251,191,36,0.15)',
    'high':     'rgba(248,113,113,0.15)',
    'critical': 'rgba(252,165,165,0.20)',
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
        sev_key      = severity.lower()
        emoji        = _SEVERITY_EMOJI.get(sev_key, '⚠️')
        tipo         = _TIPO_LEGIVEL.get(alert_type, alert_type.upper())
        cor          = _COR_SEVERIDADE.get(sev_key, '#f87171')
        cor_badge_bg = _COR_BADGE_BG.get(sev_key, 'rgba(248,113,113,0.15)')
        timestamp    = datetime.now(_TZ_BRT).strftime('%d/%m/%Y %H:%M:%S (BRT)')

        host_display    = hostname if hostname else f'Host {host_id}'
        host_ip_display = host_ip if host_ip else '—'
        assunto = f'{emoji} [ALERTA][{severity.upper()}] {tipo} — {host_display}'

        # Plain-text (fallback)
        ip_atacante_txt = f'IP do Atacante: {source_ip}\n' if source_ip else ''
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

        # Linha de IP do atacante (tabela HTML) — só quando presente
        ip_atacante_html = (
            f'<tr style="border-top:1px solid #374151;">'
            f'<td style="padding:9px 20px 9px 0;color:#6b7280;font-size:11px;'
            f'text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;'
            f'width:1%;vertical-align:middle;font-weight:600;">&#x26A0; IP Atacante</td>'
            f'<td style="padding:9px 0;color:#f87171;font-size:13px;'
            f'font-family:\'Courier New\',Courier,monospace;font-weight:700;">{source_ip}</td>'
            f'</tr>'
        ) if source_ip else ''

        corpo_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#111827;font-family:'Segoe UI',Arial,Helvetica,sans-serif;">
<div style="padding:32px 16px;">
<div style="max-width:600px;margin:auto;">

  <!-- Header: logo + brand (espelha a sidebar do frontend) -->
  <div style="margin-bottom:24px;">
    <table style="border-collapse:collapse;">
      <tr>
        <td style="padding:0 12px 0 0;vertical-align:middle;">
          <div style="width:38px;height:38px;background:#2563eb;border-radius:8px;text-align:center;line-height:38px;font-size:20px;">&#x1F6E1;&#xFE0F;</div>
        </td>
        <td style="vertical-align:middle;">
          <div style="font-size:17px;font-weight:700;color:#f3f4f6;line-height:1.2;">Monitor</div>
          <div style="font-size:11px;color:#6b7280;margin-top:2px;">Sistema de Monitoramento &middot; PADS3</div>
        </td>
      </tr>
    </table>
  </div>

  <!-- Card principal (espelha --card-bg dark: #1f2937, --card-border: #374151) -->
  <div style="background:#1f2937;border-radius:12px;border:1px solid #374151;overflow:hidden;">

    <!-- Barra de acento superior (cor de severidade) -->
    <div style="height:3px;background:{cor};"></div>

    <!-- Cabeçalho do alerta -->
    <div style="padding:28px 32px 24px;">
      <!-- Badge de severidade (estilo AlertsPanel do frontend) -->
      <div style="margin-bottom:14px;">
        <span style="display:inline-block;background:{cor_badge_bg};color:{cor};
          font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.9px;
          padding:4px 14px;border-radius:6px;">{emoji}&nbsp;{severity.upper()}</span>
      </div>
      <!-- Tipo do alerta -->
      <h1 style="margin:0 0 6px;font-size:22px;font-weight:700;color:#f3f4f6;line-height:1.3;">{tipo}</h1>
      <!-- Host -->
      <p style="margin:0;font-size:13px;color:#9ca3af;">{host_display}</p>
    </div>

    <!-- Divisor -->
    <div style="height:1px;background:#374151;margin:0 32px;"></div>

    <!-- Tabela de detalhes -->
    <div style="padding:20px 32px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="padding:9px 18px 9px 0;color:#6b7280;font-size:11px;text-transform:uppercase;
            letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:middle;font-weight:600;">&#x1F4BB; Host</td>
          <td style="padding:9px 0;color:#f3f4f6;font-size:14px;font-weight:600;">{host_display}</td>
        </tr>
        <tr style="border-top:1px solid #374151;">
          <td style="padding:9px 18px 9px 0;color:#6b7280;font-size:11px;text-transform:uppercase;
            letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:middle;font-weight:600;">&#x1F310; IP do Host</td>
          <td style="padding:9px 0;color:#9ca3af;font-size:13px;font-family:'Courier New',Courier,monospace;">{host_ip_display}</td>
        </tr>
        {ip_atacante_html}
        <tr style="border-top:1px solid #374151;">
          <td style="padding:9px 18px 9px 0;color:#6b7280;font-size:11px;text-transform:uppercase;
            letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:middle;font-weight:600;">&#x1F552; Hor&aacute;rio</td>
          <td style="padding:9px 0;color:#9ca3af;font-size:13px;">{timestamp}</td>
        </tr>
      </table>
    </div>

    <!-- Divisor -->
    <div style="height:1px;background:#374151;margin:0 32px;"></div>

    <!-- Descrição do evento -->
    <div style="padding:20px 32px 28px;">
      <p style="margin:0 0 10px;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.9px;font-weight:600;">Descri&ccedil;&atilde;o do Evento</p>
      <div style="background:#111827;border:1px solid #374151;border-left:3px solid {cor};border-radius:0 8px 8px 0;padding:14px 18px;">
        <p style="margin:0;color:#d1d5db;font-size:14px;line-height:1.7;">{message}</p>
      </div>
    </div>

    <!-- Footer do card: botão CTA (azul fixo — cor da marca, igual à sidebar) -->
    <div style="background:#111827;border-top:1px solid #374151;padding:20px 32px;text-align:center;border-radius:0 0 12px 12px;">
      <a href="http://painel.monitoramento.lan"
         style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;
           padding:11px 36px;border-radius:8px;font-weight:600;font-size:14px;letter-spacing:.3px;">
        Abrir Painel de Alertas &rarr;
      </a>
    </div>

  </div><!-- /card -->

  <!-- Rodapé -->
  <div style="text-align:center;margin-top:20px;">
    <p style="margin:0;font-size:11px;color:#4b5563;line-height:1.8;">
      Gerado automaticamente &middot; PADS3 &middot; N&atilde;o responda este email
    </p>
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
