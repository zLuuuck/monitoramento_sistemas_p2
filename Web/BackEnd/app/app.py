# app/app.py
# Aplicação principal Flask para o sistema de monitoramento.
# Semana 5: registro do AlertModel e das rotas de alertas.
# Semana 6: registro do ActiveConnectionModel, rotas de conexões e check_port_scan.

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


garantir_schema_discovery()
garantir_schema_metrics()
garantir_schema_alerts()
garantir_schema_iops()


# Registra os Blueprints de rotas
from .routes import (
    register_discovery_routes,
    register_log_routes,
    register_metric_routes,
    register_alerts_routes,
)

# Semana 6: importação do blueprint de conexões e da função de detecção
from .routes.connections import register_connections_routes
from .utils.detection import check_port_scan

register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel, MetricModel)
register_metric_routes(app, db, HostModel, AgentModel, MetricModel)
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


@app.route('/api/hosts', methods=['GET'])
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