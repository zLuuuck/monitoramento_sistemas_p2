#!/usr/bin/env bash
# uninstall.sh — Remove o Monitor Agent e todos os seus arquivos.
# Uso: sudo ./uninstall.sh

set -euo pipefail

INSTALL_DIR="/opt/monitor-agent"
SERVICE_FILE="/etc/systemd/system/linux-agent.service"
ENV_DIR="/etc/monitor-agent"
LOG_DIR="/var/log/monitor-agent"
CACHE_DIR="/var/cache/monitor-agent"
AGENT_DATA_DIR="$HOME/.agent"

info()    { echo "[INFO]  $*"; }
success() { echo "[OK]    $*"; }
error()   { echo "[ERRO]  $*" >&2; exit 1; }

if [[ "$(id -u)" -ne 0 ]]; then
    error "Execute como root: sudo ./uninstall.sh"
fi

info "Iniciando desinstalação do Monitor Agent..."

# ---------------------------------------------------------------------------
# Parar e desabilitar serviço
# ---------------------------------------------------------------------------
if systemctl is-active --quiet linux-agent 2>/dev/null; then
    systemctl stop linux-agent
    success "Serviço parado."
fi

if systemctl is-enabled --quiet linux-agent 2>/dev/null; then
    systemctl disable linux-agent
    success "Serviço desabilitado."
fi

# ---------------------------------------------------------------------------
# Remover arquivos do serviço e binário
# ---------------------------------------------------------------------------
if [[ -f "$SERVICE_FILE" ]]; then
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    success "Arquivo de serviço removido: $SERVICE_FILE"
fi

if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    success "Binário removido: $INSTALL_DIR"
fi

if [[ -d "$ENV_DIR" ]]; then
    rm -rf "$ENV_DIR"
    success "Configuração removida: $ENV_DIR"
fi

# ---------------------------------------------------------------------------
# Remover logs e cache
# ---------------------------------------------------------------------------
if [[ -d "$LOG_DIR" ]]; then
    read -rp "Remover logs em $LOG_DIR? [s/N] " RESP
    if [[ "${RESP,,}" == "s" || "${RESP,,}" == "sim" ]]; then
        rm -rf "$LOG_DIR"
        success "Logs removidos: $LOG_DIR"
    else
        info "Logs mantidos em $LOG_DIR"
    fi
fi

if [[ -d "$CACHE_DIR" ]]; then
    rm -rf "$CACHE_DIR"
    success "Cache removido: $CACHE_DIR"
fi

# ---------------------------------------------------------------------------
# Remover IDs persistidos do agente
# ---------------------------------------------------------------------------
if [[ -d "$AGENT_DATA_DIR" ]]; then
    read -rp "Remover IDs do agente em $AGENT_DATA_DIR? [s/N] " RESP
    if [[ "${RESP,,}" == "s" || "${RESP,,}" == "sim" ]]; then
        rm -rf "$AGENT_DATA_DIR"
        success "IDs removidos: $AGENT_DATA_DIR"
    else
        info "IDs mantidos em $AGENT_DATA_DIR (útil para reinstalar com o mesmo host_id)"
    fi
fi

echo ""
success "Monitor Agent desinstalado com sucesso."
