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
            f'<tr>'
            f'<td style="padding:10px 16px 10px 0;color:#52525b;font-size:12px;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:top;">IP Atacante</td>'
            f'<td style="padding:10px 0;color:#f87171;font-size:13px;font-family:\'Courier New\',monospace;font-weight:600;">{source_ip}</td>'
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

        # Cores do badge de severidade (fundo levemente colorido sobre dark)
        cor_badge_bg  = {
            'low':      'rgba(251,191,36,.15)',
            'medium':   'rgba(251,146,60,.15)',
            'high':     'rgba(239,68,68,.15)',
            'critical': 'rgba(220,38,38,.20)',
        }.get(severity.lower(), 'rgba(239,68,68,.15)')

        # Barra de progresso / indicador visual de severidade (largura %)
        sev_pct = {'low': '30', 'medium': '55', 'high': '80', 'critical': '100'}.get(severity.lower(), '80')

        corpo_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#09090b;font-family:'Segoe UI',Arial,Helvetica,sans-serif;">
<div style="padding:32px 16px;">
<div style="max-width:580px;margin:auto;">

  <!-- Topo: logo + sistema -->
  <div style="text-align:center;margin-bottom:20px;">
    <span style="display:inline-block;background:#18181b;border:1px solid #27272a;border-radius:8px;padding:6px 16px;font-size:11px;color:#71717a;text-transform:uppercase;letter-spacing:1.4px;">
      PADS3 &middot; Sistema de Monitoramento
    </span>
  </div>

  <!-- Card principal -->
  <div style="background:#18181b;border-radius:16px;border:1px solid #27272a;overflow:hidden;">

    <!-- Linha de acento superior (cor da severidade) -->
    <div style="height:3px;background:linear-gradient(90deg,{cor} 0%,{cor}99 60%,transparent 100%);"></div>

    <!-- Header do alerta -->
    <div style="padding:28px 32px 24px;">
      <!-- Badge de severidade -->
      <div style="display:inline-flex;align-items:center;gap:7px;background:{cor_badge_bg};border:1px solid {cor}55;border-radius:20px;padding:4px 14px;margin-bottom:16px;">
        <span style="font-size:14px;line-height:1;">{emoji}</span>
        <span style="font-size:11px;font-weight:700;color:{cor};text-transform:uppercase;letter-spacing:1px;">{severity.upper()}</span>
      </div>

      <!-- Título -->
      <h1 style="margin:0 0 6px;font-size:22px;font-weight:700;color:#fafafa;line-height:1.3;">{tipo}</h1>
      <p style="margin:0;font-size:14px;color:#71717a;">{host_display}</p>
    </div>

    <!-- Divisor -->
    <div style="height:1px;background:#27272a;margin:0 32px;"></div>

    <!-- Tabela de detalhes -->
    <div style="padding:20px 32px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="padding:10px 16px 10px 0;color:#52525b;font-size:12px;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:top;">Host</td>
          <td style="padding:10px 0;color:#e4e4e7;font-size:14px;font-weight:600;">{host_display}</td>
        </tr>
        <tr>
          <td style="padding:10px 16px 10px 0;color:#52525b;font-size:12px;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:top;">IP do Host</td>
          <td style="padding:10px 0;color:#a1a1aa;font-size:13px;font-family:'Courier New',monospace;">{host_ip_display}</td>
        </tr>
        {ip_atacante_html}
        <tr>
          <td style="padding:10px 16px 10px 0;color:#52525b;font-size:12px;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;width:1%;vertical-align:top;">Data / Hora</td>
          <td style="padding:10px 0;color:#a1a1aa;font-size:13px;">{timestamp}</td>
        </tr>
      </table>
    </div>

    <!-- Divisor -->
    <div style="height:1px;background:#27272a;margin:0 32px;"></div>

    <!-- Descrição -->
    <div style="padding:20px 32px;">
      <p style="margin:0 0 10px;font-size:11px;color:#52525b;text-transform:uppercase;letter-spacing:.8px;">Descrição</p>
      <div style="background:#09090b;border:1px solid #27272a;border-left:3px solid {cor};border-radius:0 8px 8px 0;padding:14px 18px;">
        <p style="margin:0;color:#d4d4d8;font-size:14px;line-height:1.65;">{message}</p>
      </div>
    </div>

    <!-- Indicador de severidade -->
    <div style="padding:0 32px 20px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:11px;color:#52525b;white-space:nowrap;">Criticidade</span>
        <div style="flex:1;height:4px;background:#27272a;border-radius:4px;overflow:hidden;">
          <div style="width:{sev_pct}%;height:100%;background:linear-gradient(90deg,{cor}99,{cor});border-radius:4px;"></div>
        </div>
        <span style="font-size:11px;color:{cor};font-weight:700;white-space:nowrap;">{sev_pct}%</span>
      </div>
    </div>

    <!-- Botão CTA -->
    <div style="padding:4px 32px 32px;text-align:center;">
      <a href="http://painel.monitoramento.lan"
         style="display:inline-block;background:{cor};color:#fff;text-decoration:none;padding:13px 40px;border-radius:10px;font-weight:700;font-size:14px;letter-spacing:.4px;">
        Abrir Painel &rarr;
      </a>
    </div>

  </div><!-- /card -->

  <!-- Rodapé -->
  <div style="text-align:center;margin-top:20px;">
    <p style="margin:0;font-size:11px;color:#3f3f46;">
      Gerado automaticamente &middot; Não responda este email &middot; PADS3
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