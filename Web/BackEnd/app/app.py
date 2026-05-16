# app/app.py
# Aplicação principal Flask para o sistema de monitoramento

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

# Registra todos os modelos (Host, Agent, HostDiscovery, Metric, LogEntry)
from .models import registrar_modelos
HostModel, AgentModel, HostDiscoveryModel, MetricModel, LogEntryModel = registrar_modelos(db)


def garantir_schema_discovery():
    """Adiciona colunas de discovery em bancos criados antes do schema atual."""
    comandos = [
        "ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS os_name VARCHAR(200)",
        "ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS os_version VARCHAR(50)",
        "ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS kernel_release VARCHAR(200)",
        "ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS uptime_seconds INTEGER",
        "ALTER TABLE host_discovery ADD COLUMN IF NOT EXISTS motherboard JSONB",
    ]

    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning("Nao foi possivel garantir schema de discovery: %s", erro)


garantir_schema_discovery()


def garantir_schema_metrics():
    """Adiciona colunas de metricas em bancos atuais sem depender do init.sql."""
    comandos = [
        "ALTER TABLE metrics ADD COLUMN IF NOT EXISTS memory_used_mb INTEGER",
        "ALTER TABLE metrics ADD COLUMN IF NOT EXISTS memory_free_mb INTEGER",
        "ALTER TABLE metrics ADD COLUMN IF NOT EXISTS memory_total_mb INTEGER",
        "ALTER TABLE metrics ADD COLUMN IF NOT EXISTS disk_used_mb BIGINT",
        "ALTER TABLE metrics ADD COLUMN IF NOT EXISTS disk_free_mb BIGINT",
        "ALTER TABLE metrics ADD COLUMN IF NOT EXISTS disk_total_mb BIGINT",
    ]

    try:
        with app.app_context():
            for comando in comandos:
                db.session.execute(db.text(comando))
            db.session.commit()
    except Exception as erro:
        db.session.rollback()
        app.logger.warning("Nao foi possivel garantir schema de metricas: %s", erro)


garantir_schema_metrics()

# Registra os Blueprints de rotas
from .routes import register_discovery_routes, register_log_routes, register_metric_routes
register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel, MetricModel)
register_metric_routes(app, db, HostModel, AgentModel, MetricModel)
register_log_routes(app, db, HostModel, LogEntryModel)


# ==================== ENDPOINTS GERAIS ====================

@app.route('/api/status', methods=['GET'])
def status():
    """Verificação de saúde da API."""
    return jsonify({
        'status':    'online',
        'service':   'API Monitoramento',
        'version':   '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/hello', methods=['GET'])
def hello():
    """Endpoint de teste."""
    return jsonify({'message': 'Olá do BackEnd Flask!'}), 200


@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificações de saúde do container."""
    return jsonify({"status": "ok"}), 200


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

    print("=" * 60)
    print("🚀 Sistema de Monitoramento - Backend")
    print("=" * 60)
    print(f"📍 Servidor: http://localhost:{port}")
    print(f"🐘 Banco: PostgreSQL (monitor/monitor@localhost:5432/monitor)")
    print(f"🐛 Modo Debug: {debug_mode}")
    print("=" * 60)
    print("\n📌 Endpoints disponíveis:")
    print("   GET  /api/status")
    print("   GET  /api/hello")
    print("   GET  /api/hosts")
    print("   POST /api/discovery  (Semana 1)")
    print("   GET  /api/discovery  (Semana 1)")
    print("   POST /api/metrics    (Semana 2)")
    print("   GET  /api/metrics    (Semana 2)")
    print("   POST /api/logs       (Semana 3/4 — com parsing SSH)")
    print("   GET  /api/logs       (Semana 3/4)")
    print("=" * 60)

    app.run(host='0.0.0.0', port=port, debug=debug_mode)
