# app/app.py
# Aplicação principal Flask para o sistema de monitoramento.
# Semana 5: registro do AlertModel e das rotas de alertas.
# Semana 6: registro do ActiveConnectionModel, rotas de conexões e check_port_scan.

import json
import secrets

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados PostgreSQL via variável de ambiente
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://monitor:monitor@localhost:5432/monitor'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Registra todos os modelos
# Semana 6: registrar_modelos agora retorna ActiveConnectionModel também
from .models import registrar_modelos
(
    HostModel,
    AgentModel,
    HostDiscoveryModel,
    MetricModel,
    LogEntryModel,
    AlertModel,               # Semana 5
    ActiveConnectionModel,    # Semana 6
) = registrar_modelos(db)


def garantir_schema_discovery():
    """Adiciona colunas de discovery em bancos criados antes do schema atual."""
    comandos = [
        'ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS os_name VARCHAR(200)',
        'ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS os_version VARCHAR(50)',
        'ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS kernel_release VARCHAR(200)',
        'ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS uptime_seconds INTEGER',
        'ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS motherboard JSONB',
    ]
    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de discovery: %s', erro)


def garantir_schema_metrics():
    """Adiciona colunas de métricas em bancos sem init.sql atualizado."""
    comandos = [
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS memory_used_mb INTEGER',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS memory_free_mb INTEGER',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS memory_total_mb INTEGER',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS disk_used_mb BIGINT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS disk_free_mb BIGINT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS disk_total_mb BIGINT',
    ]
    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de metricas: %s', erro)


def garantir_schema_alerts():
    """
    Adiciona as colunas resolved e resolved_at na tabela alerts.

    O init.sql original criou a tabela sem esses campos.
    Esta função garante que bancos existentes sejam atualizados
    sem depender de recriação do container.
    """
    comandos = [
        'ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT FALSE',
        'ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ',
    ]
    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de alerts: %s', erro)


def garantir_schema_alerts_message():
    """Adiciona coluna message à tabela alerts para descrição legível do alerta."""
    comandos = [
        'ALTER TABLE alerts ADD COLUMN IF NOT EXISTS message TEXT',
    ]
    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de message em alerts: %s', erro)


def garantir_schema_iops():
    """Adiciona colunas de IOPS de disco e taxas de rede em bancos sem schema atualizado."""
    comandos = [
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS read_iops FLOAT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS write_iops FLOAT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS read_bytes_per_sec FLOAT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS write_bytes_per_sec FLOAT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS net_sent_bytes_per_sec FLOAT',
        'ALTER TABLE metrics ADD COLUMN IF NOT EXISTS net_recv_bytes_per_sec FLOAT',
    ]
    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de IOPS: %s', erro)


def garantir_schema_connections_ip():
    """Converte src_ip/dst_ip de inet para varchar(45) se o banco foi criado com o tipo errado."""
    try:
        with app.app_context():
            db.session.execute(db.text(
                "ALTER TABLE active_connections "
                "ALTER COLUMN src_ip TYPE VARCHAR(45) USING src_ip::text, "
                "ALTER COLUMN dst_ip TYPE VARCHAR(45) USING dst_ip::text"
            ))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('garantir_schema_connections_ip: %s', erro)


def garantir_schema_alerts_source_ip():
    """Converte alerts.source_ip de inet para varchar(45) e permite NULL."""
    try:
        with app.app_context():
            db.session.execute(db.text(
                "ALTER TABLE alerts "
                "ALTER COLUMN source_ip TYPE VARCHAR(45) USING source_ip::text"
            ))
            db.session.execute(db.text(
                "ALTER TABLE alerts ALTER COLUMN source_ip DROP NOT NULL"
            ))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('garantir_schema_alerts_source_ip: %s', erro)


def garantir_schema_settings():
    """Cria tabela de configurações do sistema se ainda não existir."""
    try:
        with app.app_context():
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key     VARCHAR(100) PRIMARY KEY,
                    value   TEXT,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de settings: %s', erro)


def _load_api_key_from_db() -> str:
    """Lê a API key do banco; usa API_KEY do .env como fallback."""
    try:
        with app.app_context():
            row = db.session.execute(
                db.text("SELECT value FROM app_settings WHERE key = 'api_key'")
            ).fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    return os.environ.get('API_KEY', '')


garantir_schema_discovery()
garantir_schema_metrics()
garantir_schema_alerts()
garantir_schema_alerts_message()
garantir_schema_iops()
garantir_schema_settings()
garantir_schema_connections_ip()
garantir_schema_alerts_source_ip()


_STARTUP_FLAG = '/tmp/.monitor_startup_notified'


def _notificar_alertas_ativos():
    """
    Na inicialização do container, envia notificações Teams para alertas não resolvidos.
    Usa um flag em /tmp para não reenviar a cada hot-reload (arquivo some no restart).
    """
    import os as _os
    if _os.path.exists(_STARTUP_FLAG):
        return
    try:
        open(_STARTUP_FLAG, 'w').close()
    except Exception:
        pass

    try:
        with app.app_context():
            from .utils.teams import enviar_alerta_teams
            alertas = db.session.execute(
                db.text(
                    "SELECT id, alert_type, host_id, message "
                    "FROM alerts WHERE resolved = false ORDER BY id"
                )
            ).fetchall()
            if not alertas:
                return
            app.logger.info('Startup: %d alerta(s) ativo(s) — notificando Teams', len(alertas))
            for a in alertas:
                enviar_alerta_teams(
                    titulo=f'[ALERTA ATIVO] {a.alert_type} — Host {a.host_id}',
                    mensagem=a.message or f'{a.alert_type} detectado no host {a.host_id}',
                    severidade='warning',
                    origem=f'startup/host-{a.host_id}',
                )
    except Exception as e:
        app.logger.warning('_notificar_alertas_ativos: %s', e)


_notificar_alertas_ativos()

app.config['API_KEY'] = _load_api_key_from_db()


# Registra os Blueprints de rotas
from .routes import (
    register_discovery_routes,
    register_log_routes,
    register_metric_routes,
    register_alerts_routes,
)

# Semana 6: importação do blueprint de conexões e da função de detecção
from .routes.connections import register_connections_routes
from .utils.detection import check_port_scan, check_resource_alert
from .utils.auth import require_api_key

register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel, MetricModel)
register_metric_routes(app, db, HostModel, AgentModel, MetricModel, AlertModel, check_resource_alert)
register_log_routes(app, db, HostModel, LogEntryModel, AlertModel)
register_alerts_routes(app, db, HostModel, AlertModel)

# Semana 6: rotas de conexões TCP com injeção de check_port_scan
register_connections_routes(
    app,
    db,
    HostModel,
    ActiveConnectionModel,
    AlertModel,
    check_port_scan,          # função injetada — sem import direto no blueprint
)


# ==================== ENDPOINTS GERAIS ====================

@app.route('/api/status', methods=['GET'])
def status():
    """Verificação de saúde da API."""
    return jsonify({
        'status':    'online',
        'service':   'API Monitoramento',
        'version':   '4.0.0',  # Semana 6
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/hello', methods=['GET'])
def hello():
    """Endpoint de teste."""
    return jsonify({'message': 'Olá do BackEnd Flask!'}), 200


@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificações de saúde do container."""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/heartbeat', methods=['POST'])
@require_api_key
def heartbeat():
    """Atualiza last_seen do host — keep-alive enviado pelo agente."""
    dados = request.get_json(silent=True) or {}
    global_info = dados.get('global') or {}

    host_id_raw = global_info.get('host_id')
    hostname    = global_info.get('hostname')

    host = None
    if host_id_raw:
        try:
            host = HostModel.query.get(int(host_id_raw))
        except (TypeError, ValueError):
            pass
    if not host and hostname:
        host = HostModel.query.filter_by(hostname=hostname).first()

    if host:
        host.last_seen = datetime.utcnow()
        agent = AgentModel.query.filter_by(host_id=host.id).first()
        if agent:
            agent.last_checkin = datetime.utcnow()
            agent.status = 'active'
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify({'status': 'ok'}), 200


@app.route('/api/hosts', methods=['GET'])
@require_api_key
def get_hosts():
    """Retorna todos os hosts cadastrados."""
    try:
        incluir_discovery = request.args.get('include_discovery', 'false').lower() == 'true'
        hosts = HostModel.query.order_by(HostModel.id.desc()).all()

        hosts_lista = []
        for host in hosts:
            host_dict = host.to_dict()
            if incluir_discovery and hasattr(host, 'discovery') and host.discovery:
                host_dict['dados_hardware'] = host.discovery.to_dict()
            hosts_lista.append(host_dict)

        return jsonify({'hosts': hosts_lista, 'total': len(hosts_lista)}), 200

    except Exception as erro:
        return jsonify({'erro': f'Erro ao buscar hosts: {str(erro)}'}), 500


# ==================== SETTINGS ====================

@app.route('/api/auth/login', methods=['POST'])
def panel_login():
    """Autentica com a senha do painel e retorna a API key para o navegador."""
    senha = (request.get_json(silent=True) or {}).get('password', '')
    panel_password = os.environ.get('PANEL_PASSWORD', '')
    if not panel_password:
        return jsonify({'erro': 'PANEL_PASSWORD não configurado no servidor'}), 503
    if not senha or senha != panel_password:
        return jsonify({'erro': 'Senha inválida'}), 401
    api_key = app.config.get('API_KEY', '')
    if not api_key:
        return jsonify({'erro': 'API Key não configurada — gere uma em Configurações'}), 404
    return jsonify({'api_key': api_key}), 200


@app.route('/api/settings/apikey', methods=['GET'])
def get_apikey_settings():
    """Retorna status e prefixo da API key atual (nunca o valor completo)."""
    key = app.config.get('API_KEY', '')
    if key:
        return jsonify({
            'configured': True,
            'key_prefix': key[:8] + '...' + key[-4:],
        }), 200
    return jsonify({'configured': False, 'key_prefix': None}), 200


@app.route('/api/settings/apikey/generate', methods=['POST'])
def generate_apikey():
    """Gera uma nova API key, persiste no banco e retorna o valor uma única vez."""
    new_key = secrets.token_hex(32)
    try:
        db.session.execute(
            db.text("""
                INSERT INTO app_settings (key, value, updated_at)
                VALUES ('api_key', :value, NOW())
                ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
            """),
            {'value': new_key},
        )
        db.session.commit()
        app.config['API_KEY'] = new_key
        return jsonify({
            'api_key': new_key,
            'message': 'Copie agora — não será exibida novamente',
        }), 201
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao gerar API key: {str(erro)}'}), 500


def _load_email_recipients() -> list:
    try:
        row = db.session.execute(
            db.text("SELECT value FROM app_settings WHERE key = 'email_recipients'")
        ).fetchone()
        return json.loads(row[0]) if row and row[0] else []
    except Exception:
        return []


def _save_email_recipients(recipients: list) -> None:
    db.session.execute(
        db.text("""
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('email_recipients', :value, NOW())
            ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
        """),
        {'value': json.dumps(recipients)},
    )
    db.session.commit()


@app.route('/api/settings/email-recipients', methods=['GET'])
@require_api_key
def get_email_recipients():
    """Retorna a lista de destinatários de email para alertas."""
    try:
        return jsonify({'recipients': _load_email_recipients()}), 200
    except Exception as erro:
        return jsonify({'erro': str(erro)}), 500


@app.route('/api/settings/email-recipients', methods=['POST'])
@require_api_key
def add_email_recipient():
    """Adiciona um destinatário à lista de emails de alertas."""
    email = (request.get_json(silent=True) or {}).get('email', '').strip().lower()
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'erro': 'Email inválido'}), 400
    try:
        recipients = _load_email_recipients()
        if email not in recipients:
            recipients.append(email)
            _save_email_recipients(recipients)
        return jsonify({'recipients': recipients}), 201
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': str(erro)}), 500


@app.route('/api/settings/email-recipients/<path:email>', methods=['DELETE'])
@require_api_key
def remove_email_recipient(email):
    """Remove um destinatário da lista de emails de alertas."""
    try:
        recipients = _load_email_recipients()
        recipients = [r for r in recipients if r != email]
        _save_email_recipients(recipients)
        return jsonify({'recipients': recipients}), 200
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': str(erro)}), 500


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    port       = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print('=' * 60)
    print('Sistema de Monitoramento - Backend')
    print('=' * 60)
    print(f'Servidor: http://localhost:{port}')
    print(f'Banco: PostgreSQL (monitor/monitor@localhost:5432/monitor)')
    print(f'Modo Debug: {debug_mode}')
    print('=' * 60)
    print('\nEndpoints disponíveis:')
    print('   GET   /api/status')
    print('   GET   /api/hello')
    print('   GET   /api/hosts')
    print('   POST  /api/discovery       (Semana 1)')
    print('   GET   /api/discovery       (Semana 1)')
    print('   POST  /api/metrics         (Semana 2)')
    print('   GET   /api/metrics         (Semana 2)')
    print('   POST  /api/logs            (Semanas 3/4 — com parsing SSH)')
    print('   GET   /api/logs            (Semanas 3/4)')
    print('   GET   /api/alerts          (Semana 5 — brute force)')
    print('   PATCH /api/alerts/<id>/resolve  (Semana 5)')
    print('   POST  /api/connections     (Semana 6 — TCP + port scan)')
    print('=' * 60)

    app.run(host='0.0.0.0', port=port, debug=debug_mode)