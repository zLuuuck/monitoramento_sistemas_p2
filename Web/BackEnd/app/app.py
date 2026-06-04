# app/app.py
# Aplicação principal Flask para o sistema de monitoramento.

import json
import secrets

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

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

from .models import registrar_modelos
(
    HostModel,
    AgentModel,
    HostDiscoveryModel,
    MetricModel,
    LogEntryModel,
    AlertModel,
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


def garantir_schema_notifications():
    """Insere toggles padrão de notificação em app_settings se ainda não existirem."""
    defaults = [
        ('notify_teams', 'true'),
        ('notify_email', 'false'),
    ]
    try:
        with app.app_context():
            for key, value in defaults:
                db.session.execute(
                    db.text("""
                        INSERT INTO app_settings (key, value, updated_at)
                        VALUES (:key, :value, NOW())
                        ON CONFLICT (key) DO NOTHING
                    """),
                    {'key': key, 'value': value},
                )
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de notifications: %s', erro)


def garantir_schema_thresholds():
    """Insere valores padrão de threshold em app_settings se ainda não existirem."""
    defaults = [
        ('threshold_cpu',  '80'),
        ('threshold_mem',  '80'),
        ('threshold_disk', '80'),
    ]
    try:
        with app.app_context():
            for key, value in defaults:
                db.session.execute(
                    db.text("""
                        INSERT INTO app_settings (key, value, updated_at)
                        VALUES (:key, :value, NOW())
                        ON CONFLICT (key) DO NOTHING
                    """),
                    {'key': key, 'value': value},
                )
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning('Nao foi possivel garantir schema de thresholds: %s', erro)


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
garantir_schema_alerts_source_ip()
garantir_schema_notifications()
garantir_schema_thresholds()


# ==================== RETENÇÃO DE DADOS ====================

def _executar_cleanup(dias: int) -> dict:
    """Apaga dados com mais de `dias` dias das tabelas de série temporal.

    Chama a função SQL cleanup_old_data() do banco e retorna o número de
    linhas removidas por tabela (contagem feita antes do DELETE).
    Deve ser chamada dentro de um app_context ativo.
    """
    corte = datetime.utcnow() - timedelta(days=dias)
    contagens = {}
    for tabela in ('metrics', 'logs'):
        n = db.session.execute(
            db.text(f'SELECT COUNT(*) FROM {tabela} WHERE timestamp < :corte'),
            {'corte': corte},
        ).scalar() or 0
        contagens[tabela] = n

    db.session.execute(
        db.text('SELECT cleanup_old_data(:dias)'),
        {'dias': dias},
    )
    db.session.commit()
    return contagens


def _job_cleanup():
    """Tarefa diária do APScheduler — executa dentro do contexto da aplicação."""
    dias = int(os.environ.get('RETENTION_DAYS', 7))
    app.logger.info('Scheduler: iniciando cleanup (retenção: %d dias)', dias)
    try:
        with app.app_context():
            resultado = _executar_cleanup(dias)
        app.logger.info(
            'Scheduler: cleanup concluído — metrics=%d, logs=%d',
            resultado.get('metrics', 0),
            resultado.get('logs', 0),
        )
    except Exception as e:
        app.logger.error('Scheduler: erro no cleanup: %s', e)


def _iniciar_scheduler():
    """Inicia o BackgroundScheduler que dispara cleanup_old_data 1×/dia às 03:00 UTC.

    Em modo debug com reloader, o Werkzeug sobe dois processos. Verificar
    WERKZEUG_RUN_MAIN garante que o scheduler seja criado apenas no processo
    filho (worker real), evitando dois schedulers rodando em paralelo.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _job_cleanup,
        trigger=CronTrigger(hour=3, minute=0, timezone='UTC'),
        id='cleanup_old_data',
        replace_existing=True,
    )
    scheduler.start()
    app.logger.info('Scheduler iniciado — cleanup diário às 03:00 UTC')


# Inicia o scheduler apenas uma vez:
#   - em produção (não debug): sempre
#   - em debug com reloader: só no processo filho (WERKZEUG_RUN_MAIN=true)
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    _iniciar_scheduler()


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
            teams_on = _load_notify_flag('teams')
            alertas = db.session.execute(
                db.text(
                    "SELECT id, alert_type, host_id, message "
                    "FROM alerts WHERE resolved = false ORDER BY id"
                )
            ).fetchall()
            if not alertas:
                return
            app.logger.info('Startup: %d alerta(s) ativo(s)', len(alertas))
            if not teams_on:
                app.logger.info('Startup: Teams skip — notify_teams=false')
                return
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

from .routes.connections import register_portscan_routes
from .utils.detection import check_port_scan, check_resource_alert
from .utils.auth import require_api_key

register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel, MetricModel)
register_metric_routes(app, db, HostModel, AgentModel, MetricModel, AlertModel, check_resource_alert)
register_log_routes(app, db, HostModel, LogEntryModel, AlertModel)
register_alerts_routes(app, db, HostModel, AlertModel)
register_portscan_routes(app, db, HostModel, AlertModel, check_port_scan)


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
    """Retorna status e prefixo da API key (nunca o valor completo). Sem autenticação
    intencional: expõe apenas os primeiros/últimos caracteres — baixo risco, necessário
    para a tela de login verificar se uma chave já existe antes de redirecionar."""
    key = app.config.get('API_KEY', '')
    if key:
        return jsonify({
            'configured': True,
            'key_prefix': key[:8] + '...' + key[-4:],
        }), 200
    return jsonify({'configured': False, 'key_prefix': None}), 200


@app.route('/api/settings/apikey/generate', methods=['POST'])
def generate_apikey():
    """Gera uma nova API key, persiste no banco e retorna o valor uma única vez.

    Autenticação por um de dois mecanismos:
      1. Header X-API-Key com a chave atual válida.
      2. Body JSON { "password": "<PANEL_PASSWORD>" }.

    Estado inicial (nenhuma chave gerada ainda): aceita APENAS senha, porque não
    há chave existente para validar via header. Neste caso o header é ignorado.
    """
    current_key    = app.config.get('API_KEY', '')
    panel_password = os.environ.get('PANEL_PASSWORD', '')
    body           = request.get_json(silent=True) or {}

    provided_key      = request.headers.get('X-API-Key', '')
    provided_password = body.get('password', '')

    if not current_key:
        # Estado inicial — nenhuma chave configurada: só aceita senha
        if not panel_password or provided_password != panel_password:
            return jsonify({
                'erro': 'Nenhuma chave configurada ainda. Forneça a senha do painel para gerar a primeira chave.'
            }), 401
    else:
        # Chave existente: aceita header válido OU senha correta
        key_ok      = bool(provided_key and provided_key == current_key)
        password_ok = bool(panel_password and provided_password == panel_password)
        if not key_ok and not password_ok:
            return jsonify({
                'erro': 'Credencial inválida — forneça o header X-API-Key com a chave atual ou a senha do painel no body.'
            }), 401

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


def _load_threshold(key: str, default: int = 80) -> int:
    try:
        row = db.session.execute(
            db.text("SELECT value FROM app_settings WHERE key = :key"),
            {'key': key},
        ).fetchone()
        if row and row[0] is not None:
            return int(row[0])
    except Exception:
        pass
    return default


@app.route('/api/settings/thresholds', methods=['GET'])
@require_api_key
def get_thresholds():
    """Retorna os limiares configurados para alertas de recurso."""
    try:
        return jsonify({
            'cpu':  _load_threshold('threshold_cpu'),
            'mem':  _load_threshold('threshold_mem'),
            'disk': _load_threshold('threshold_disk'),
        }), 200
    except Exception as erro:
        return jsonify({'erro': str(erro)}), 500


@app.route('/api/settings/thresholds', methods=['PATCH'])
@require_api_key
def patch_thresholds():
    """Atualiza um ou mais limiares de recurso. Aceita subset de {cpu, mem, disk}.
    Cada valor deve ser inteiro entre 1 e 99. Retorna estado atualizado."""
    body  = request.get_json(silent=True) or {}
    mapa  = {'cpu': 'threshold_cpu', 'mem': 'threshold_mem', 'disk': 'threshold_disk'}
    erros = []

    for campo in mapa:
        if campo not in body:
            continue
        try:
            v = int(body[campo])
        except (TypeError, ValueError):
            erros.append(f'"{campo}" deve ser um número inteiro')
            continue
        if not 1 <= v <= 99:
            erros.append(f'"{campo}" deve estar entre 1 e 99 (recebido: {body[campo]})')

    if erros:
        return jsonify({'erro': '; '.join(erros)}), 400

    if not any(c in body for c in mapa):
        return jsonify({'erro': 'Nenhum campo reconhecido (cpu, mem, disk)'}), 400

    try:
        for campo, chave in mapa.items():
            if campo not in body:
                continue
            db.session.execute(
                db.text("""
                    INSERT INTO app_settings (key, value, updated_at)
                    VALUES (:key, :value, NOW())
                    ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
                """),
                {'key': chave, 'value': str(int(body[campo]))},
            )
        db.session.commit()
        return jsonify({
            'cpu':  _load_threshold('threshold_cpu'),
            'mem':  _load_threshold('threshold_mem'),
            'disk': _load_threshold('threshold_disk'),
        }), 200
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': str(erro)}), 500


def _load_notify_flag(canal: str) -> bool:
    """Lê toggle de notificação; default teams=True, email=False."""
    key = f'notify_{canal}'
    defaults = {'teams': True, 'email': False}
    try:
        row = db.session.execute(
            db.text("SELECT value FROM app_settings WHERE key = :key"),
            {'key': key},
        ).fetchone()
        if row and row[0] is not None:
            return row[0].lower() == 'true'
    except Exception:
        pass
    return defaults.get(canal, False)


@app.route('/api/settings/notifications', methods=['GET'])
@require_api_key
def get_notifications():
    """Retorna o estado dos toggles de notificação (teams, email)."""
    try:
        return jsonify({
            'teams': _load_notify_flag('teams'),
            'email': _load_notify_flag('email'),
        }), 200
    except Exception as erro:
        return jsonify({'erro': str(erro)}), 500


@app.route('/api/settings/notifications', methods=['PATCH'])
@require_api_key
def patch_notifications():
    """Atualiza um ou mais toggles de notificação. Aceita subset de {teams, email} com valores booleanos."""
    body  = request.get_json(silent=True) or {}
    canais = ('teams', 'email')
    erros  = []

    for canal in canais:
        if canal not in body:
            continue
        if not isinstance(body[canal], bool):
            erros.append(f'"{canal}" deve ser boolean (true/false)')

    if erros:
        return jsonify({'erro': '; '.join(erros)}), 400

    if not any(c in body for c in canais):
        return jsonify({'erro': 'Nenhum campo reconhecido (teams, email)'}), 400

    try:
        for canal in canais:
            if canal not in body:
                continue
            db.session.execute(
                db.text("""
                    INSERT INTO app_settings (key, value, updated_at)
                    VALUES (:key, :value, NOW())
                    ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
                """),
                {'key': f'notify_{canal}', 'value': 'true' if body[canal] else 'false'},
            )
        db.session.commit()
        return jsonify({
            'teams': _load_notify_flag('teams'),
            'email': _load_notify_flag('email'),
        }), 200
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': str(erro)}), 500


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


# ==================== MANUTENÇÃO ====================

@app.route('/api/maintenance/cleanup', methods=['POST'])
@require_api_key
def maintenance_cleanup():
    """Dispara o cleanup de dados antigos imediatamente.

    Útil para testes e para forçar limpeza manual sem aguardar o scheduler.
    Retorna contagem de linhas removidas por tabela.
    """
    dias = int(os.environ.get('RETENTION_DAYS', 7))
    try:
        resultado = _executar_cleanup(dias)
        app.logger.info(
            'Cleanup manual via API: metrics=%d, logs=%d',
            resultado.get('metrics', 0),
            resultado.get('logs', 0),
        )
        return jsonify({'removidos': resultado, 'dias_retencao': dias}), 200
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': f'Erro no cleanup: {str(erro)}'}), 500


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