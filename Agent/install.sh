#!/usr/bin/env bash
# install.sh — Instala o Monitor Agent como serviço systemd.
# Uso: sudo ./install.sh

set -euo pipefail

INSTALL_DIR="/opt/monitor-agent"
SERVICE_FILE="/etc/systemd/system/linux-agent.service"
ENV_DIR="/etc/monitor-agent"
ENV_FILE="$ENV_DIR/env"
BINARY_NAME="agent"
BINARY_SRC="$(dirname "$0")/Agent_Exec/dist/$BINARY_NAME"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()    { echo "[INFO]  $*"; }
success() { echo "[OK]    $*"; }
error()   { echo "[ERRO]  $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Verificar root
# ---------------------------------------------------------------------------
if [[ "$(id -u)" -ne 0 ]]; then
    error "Execute como root: sudo ./install.sh"
fi

info "Iniciando instalação do Monitor Agent..."

# ---------------------------------------------------------------------------
# Verificar binário
# ---------------------------------------------------------------------------
if [[ ! -f "$BINARY_SRC" ]]; then
    info "Binário não encontrado em $BINARY_SRC. Tentando compilar..."

    AGENT_DIR="$(dirname "$0")"

    if ! command -v pyinstaller &>/dev/null; then
        error "pyinstaller não encontrado. Instale com: pip install pyinstaller"
    fi

    if [[ ! -f "$AGENT_DIR/.ambiente_venv/bin/activate" ]]; then
        info "Criando ambiente virtual..."
        python3 -m venv "$AGENT_DIR/.ambiente_venv"
    fi

    source "$AGENT_DIR/.ambiente_venv/bin/activate"
    pip install -e "$AGENT_DIR" --quiet
    pip install pyinstaller --quiet

    pyinstaller --onefile -n "$BINARY_NAME" \
        --paths "$AGENT_DIR/src" \
        --distpath "$AGENT_DIR/Agent_Exec/dist" \
        --workpath "$AGENT_DIR/Agent_Exec/build" \
        "$AGENT_DIR/Agent_Exec/main.py" \
        --noconfirm --clean

    deactivate
    success "Binário compilado em $BINARY_SRC"
fi

# ---------------------------------------------------------------------------
# Copiar binário
# ---------------------------------------------------------------------------
mkdir -p "$INSTALL_DIR"
cp "$BINARY_SRC" "$INSTALL_DIR/$BINARY_NAME"
chmod +x "$INSTALL_DIR/$BINARY_NAME"
success "Binário instalado em $INSTALL_DIR/$BINARY_NAME"

# ---------------------------------------------------------------------------
# Configurar variáveis de ambiente
# ---------------------------------------------------------------------------
mkdir -p "$ENV_DIR"
chmod 700 "$ENV_DIR"

if [[ -f "$ENV_FILE" ]]; then
    info "Arquivo de configuração já existe: $ENV_FILE"
    read -rp "Reconfigurar variáveis de ambiente? [s/N] " RESP
    RESP="${RESP,,}"
else
    RESP="s"
fi

if [[ "$RESP" == "s" || "$RESP" == "sim" ]]; then
    read -rp "Token de autenticação [Enter para pular — sem auth]: " API_TOKEN

    read -rp "Nível de log (DEBUG/INFO/WARNING) [padrão: INFO]: " LOG_LEVEL
    LOG_LEVEL="${LOG_LEVEL:-INFO}"

    cat > "$ENV_FILE" <<EOF
MONITOR_API_BASE_URL=http://api.monitoramento.lan
MONITOR_TOKEN=$API_TOKEN
MONITOR_LOG_LEVEL=$LOG_LEVEL
EOF
    chmod 600 "$ENV_FILE"
    success "Configuração salva em $ENV_FILE"
fi

# ---------------------------------------------------------------------------
# Criar diretórios de logs e cache (fila de retry)
# ---------------------------------------------------------------------------
mkdir -p /var/log/monitor-agent
mkdir -p /var/cache/monitor-agent
success "Diretórios criados: /var/log/monitor-agent/ e /var/cache/monitor-agent/"

# ---------------------------------------------------------------------------
# Instalar serviço systemd
# ---------------------------------------------------------------------------
SERVICE_SRC="$(dirname "$0")/linux-agent.service"

if [[ ! -f "$SERVICE_SRC" ]]; then
    error "Arquivo de serviço não encontrado: $SERVICE_SRC"
fi

cp "$SERVICE_SRC" "$SERVICE_FILE"
success "Serviço instalado em $SERVICE_FILE"

# ---------------------------------------------------------------------------
# Habilitar e iniciar serviço
# ---------------------------------------------------------------------------
systemctl daemon-reload
systemctl enable linux-agent
systemctl restart linux-agent

success "Serviço habilitado e iniciado."
echo ""
info "Verifique o status com:"
echo "    systemctl status linux-agent"
echo ""
info "Acompanhe os logs em tempo real com:"
echo "    journalctl -u linux-agent -f"
