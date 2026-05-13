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

# Registra os Blueprints de rotas
from .routes import register_discovery_routes, register_log_routes
register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel)
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


# ==================== SEMANA 2 — MÉTRICAS ====================

@app.route('/api/metrics', methods=['POST'])
def post_metrics():
    """
    Recebe métricas contínuas do agente e persiste no banco.

    Payload esperado (formato real do agente — contrato alinhado na Semana 2):
    {
        "type": "metrics",
        "timestamp": 1777902570.47,
        "data": {
            "cpu":     { "percent": 16.1 },
            "memory":  { "total": 12473155584, "used": 1713872896, "percent": 18.3 },
            "disk":    { "total": 982820896768, "used": 131115290624, "percent": 14.1 },
            "network": { "bytes_sent": 13883199, "bytes_recv": 252322769 },
            "logs":    [ "..." ]
        }
    }

    Campos obrigatórios: host_id, timestamp
    """
    # Aviso: o campo "data.logs" chega embutido no payload de métricas.
    # O contrato de separação entre métricas e logs ainda está sendo alinhado
    # com a equipe do agente — logs embutidos são ignorados por enquanto.
    app.logger.warning(
        '[/api/metrics] Campo "data.logs" recebido mas não processado. '
        'Contrato de separação entre métricas e logs pendente com equipe do agente.'
    )

    try:
        dados = request.get_json()

        if dados is None:
            return jsonify({'erro': 'Payload JSON é obrigatório'}), 400

        # Suporta envelope { "type": "metrics", "data": {...} } ou campos diretos
        if dados.get('type') == 'metrics' and 'data' in dados:
            data    = dados['data']
            cpu     = data.get('cpu') or {}
            memory  = data.get('memory') or {}
            disk    = data.get('disk') or {}
            network = data.get('network') or {}
            ts_raw  = dados.get('timestamp')
        else:
            # Formato legado com campos diretos no corpo
            data    = dados
            cpu     = {}
            memory  = {}
            disk    = {}
            network = {}
            ts_raw  = dados.get('timestamp')

        # host_id obrigatório — aceita no corpo ou como query param
        host_id_raw = dados.get('host_id') or request.args.get('host_id')
        if not host_id_raw:
            return jsonify({'erro': 'Campo "host_id" é obrigatório'}), 400

        # Validação de tipo numérico
        try:
            host_id = int(host_id_raw)
        except (TypeError, ValueError):
            return jsonify({'erro': 'Campo "host_id" deve ser numérico'}), 400

        # timestamp obrigatório
        if ts_raw is None:
            return jsonify({'erro': 'Campo "timestamp" é obrigatório'}), 400

        # Converte timestamp Unix float ou ISO string para datetime
        try:
            if isinstance(ts_raw, (int, float)):
                timestamp = datetime.utcfromtimestamp(ts_raw)
            else:
                timestamp = datetime.fromisoformat(str(ts_raw))
        except (ValueError, OSError):
            return jsonify({'erro': 'Formato de timestamp inválido'}), 400

        # Verifica se o host existe no banco
        host = HostModel.query.get(host_id)
        if not host:
            return jsonify({'erro': f'Host com id {host_id} não encontrado'}), 404

        # Converte memória de bytes para MB
        mem_total_bytes = memory.get('total') or 0
        mem_used_bytes  = memory.get('used') or 0
        mem_total_mb    = int(mem_total_bytes / (1024 * 1024)) if mem_total_bytes else None
        mem_used_mb     = int(mem_used_bytes  / (1024 * 1024)) if mem_used_bytes  else None
        mem_free_mb     = int((mem_total_bytes - mem_used_bytes) / (1024 * 1024)) if mem_total_bytes and mem_used_bytes else None

        # Converte disco de bytes para MB
        disk_total_bytes = disk.get('total') or 0
        disk_used_bytes  = disk.get('used') or 0
        disk_free_bytes  = (disk_total_bytes - disk_used_bytes) if disk_total_bytes and disk_used_bytes else None
        disk_total_mb    = int(disk_total_bytes / (1024 * 1024)) if disk_total_bytes else None
        disk_used_mb     = int(disk_used_bytes  / (1024 * 1024)) if disk_used_bytes  else None
        disk_free_mb     = int(disk_free_bytes  / (1024 * 1024)) if disk_free_bytes  else None

        # Cria o registro de métrica com todos os campos do banco
        metrica = MetricModel(
            host_id         = host_id,
            timestamp       = timestamp,
            cpu_percent     = cpu.get('percent') or data.get('cpu_percent'),
            memory_percent  = memory.get('percent') or data.get('memory_percent'),
            memory_used_mb  = mem_used_mb,
            memory_free_mb  = mem_free_mb,
            memory_total_mb = mem_total_mb,
            disk_percent    = disk.get('percent') or data.get('disk_percent'),
            disk_used_mb    = disk_used_mb,
            disk_free_mb    = disk_free_mb,
            disk_total_mb   = disk_total_mb,
            net_sent_bytes  = network.get('bytes_sent') or data.get('net_sent'),
            net_recv_bytes  = network.get('bytes_recv') or data.get('net_recv'),
        )

        db.session.add(metrica)
        db.session.commit()

        return jsonify({
            'message':   'Métrica salva com sucesso',
            'metric_id': metrica.id,
            'host_id':   metrica.host_id,
            'timestamp': metrica.timestamp.isoformat(),
        }), 201

    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno ao processar métrica: {str(erro)}'}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """
    Consulta métricas de um host com paginação.

    Parâmetros (query string):
    - host_id (obrigatório)
    - limit   (padrão 20, máximo 100)
    - offset  (padrão 0)

    Exemplo: GET /api/metrics?host_id=1&limit=10&offset=0
    """
    try:
        host_id_raw = request.args.get('host_id')
        if not host_id_raw:
            return jsonify({'erro': 'Parâmetro "host_id" é obrigatório'}), 400

        try:
            host_id = int(host_id_raw)
        except (TypeError, ValueError):
            return jsonify({'erro': 'Parâmetro "host_id" deve ser numérico'}), 400

        host = HostModel.query.get(host_id)
        if not host:
            return jsonify({'erro': f'Host com id {host_id} não encontrado'}), 404

        limit  = min(max(request.args.get('limit',  20, type=int), 1), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)

        metricas = MetricModel.query.filter_by(host_id=host_id)\
            .order_by(MetricModel.timestamp.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        total = MetricModel.query.filter_by(host_id=host_id).count()

        return jsonify({
            'metrics':  [m.to_dict() for m in metricas],
            'total':    total,
            'limit':    limit,
            'offset':   offset,
            'host_id':  host_id,
            'hostname': host.hostname,
        }), 200

    except Exception as erro:
        return jsonify({'erro': f'Erro ao buscar métricas: {str(erro)}'}), 500


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
    print("   POST /api/logs       (Semana 3)")
    print("   GET  /api/logs       (Semana 3)")
    print("=" * 60)

    app.run(host='0.0.0.0', port=port, debug=debug_mode)