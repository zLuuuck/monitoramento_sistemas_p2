# Aplicação principal Flask para o sistema de monitoramento

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://monitor:monitor@localhost:5432/monitor'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Importa e registra os modelos
from models import registrar_modelos
HostModel, HostDiscoveryModel, MetricModel = registrar_modelos(db)


# ==================== ENDPOINTS ====================

@app.route('/api/status', methods=['GET'])
def status():
    """Verificação de saúde da API"""
    return jsonify({
        'status': 'online',
        'service': 'API Monitoramento',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/hello', methods=['GET'])
def hello():
    """Endpoint de teste"""
    return jsonify({'message': 'Olá do BackEnd Flask!'}), 200


@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificações de saúde do container"""
    return jsonify({"status": "ok"}), 200


# ==================== SEMANA 1 - DISCOVERY ====================

@app.route('/api/discovery', methods=['POST'])
def discovery():
    """Endpoint para receber dados de descoberta de hardware (Semana 1)"""
    try:
        dados = request.get_json()
        
        if dados is None:
            return jsonify({'erro': 'Payload JSON é obrigatório'}), 400
        
        if 'environment' not in dados:
            return jsonify({
                'erro': 'Campo "environment" é obrigatório',
                'mensagem': 'Adicione "environment": "producao" ou "desenvolvimento" ao JSON enviado'
            }), 400
        
        ip_cliente = request.remote_addr
        hostname = dados.get('hostname', f'host-{ip_cliente.replace(".", "-")}')
        
        host = HostModel.query.filter_by(ip_address=ip_cliente).first()
        
        if not host:
            host = HostModel(hostname=hostname, ip_address=ip_cliente)
            db.session.add(host)
            db.session.flush()
        
        discovery = HostDiscoveryModel(
            host_id=host.id,
            is_virtualized=dados.get('is_virtualized', False),
            hypervisor=dados.get('hypervisor'),
            cpu_model=dados.get('cpu_model'),
            cpu_vcpus=dados.get('cpu_vcpus'),
            memory_total_gb=dados.get('memory_total_gb'),
            disk_total_gb=dados.get('disk_total_gb'),
            raw_data=dados
        )
        
        db.session.add(discovery)
        db.session.commit()
        
        return jsonify({
            'message': 'discovery recebido e salvo com sucesso',
            'discovery_id': discovery.id,
            'host_id': host.id,
            'ip_host': ip_cliente,
            'is_virtualized': discovery.is_virtualized
        }), 201
        
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno ao processar discovery: {str(erro)}'}), 500


@app.route('/api/hosts', methods=['GET'])
def get_hosts():
    """Retorna todos os hosts cadastrados"""
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


# ==================== SEMANA 2 - MÉTRICAS ====================

@app.route('/api/metrics', methods=['POST'])
def post_metrics():
    """
    Endpoint para receber métricas contínuas do agente (Semana 2)
    
    Payload esperado:
    {
        "host_id": 1,
        "timestamp": "2026-05-04T10:00:00",
        "cpu_percent": 45.2,
        "memory_percent": 60.5,
        "disk_percent": 30.0,
        "net_sent": 1024000,
        "net_recv": 2048000
    }
    
    Campos obrigatórios: host_id, timestamp
    """
    try:
        dados = request.get_json()
        
        if dados is None:
            return jsonify({'erro': 'Payload JSON é obrigatório'}), 400
        
        # VALIDAÇÃO: campos obrigatórios
        if 'host_id' not in dados:
            return jsonify({'erro': 'Campo "host_id" é obrigatório'}), 400
        
        if 'timestamp' not in dados:
            return jsonify({'erro': 'Campo "timestamp" é obrigatório'}), 400
        
        # Verifica se o host existe
        host = HostModel.query.get(dados['host_id'])
        if not host:
            return jsonify({'erro': f'Host com id {dados["host_id"]} não encontrado'}), 404
        
        # Converte timestamp para datetime
        try:
            timestamp = datetime.fromisoformat(dados['timestamp'])
        except ValueError:
            return jsonify({'erro': 'Formato de timestamp inválido. Use ISO format (ex: 2026-05-04T10:00:00)'}), 400
        
        # Cria a métrica
        metrica = MetricModel(
            host_id=dados['host_id'],
            timestamp=timestamp,
            cpu_percent=dados.get('cpu_percent'),
            memory_percent=dados.get('memory_percent'),
            disk_percent=dados.get('disk_percent'),
            net_sent=dados.get('net_sent'),
            net_recv=dados.get('net_recv')
        )
        
        db.session.add(metrica)
        db.session.commit()
        
        return jsonify({
            'message': 'Métrica salva com sucesso',
            'metric_id': metrica.id,
            'host_id': metrica.host_id,
            'timestamp': metrica.timestamp.isoformat()
        }), 201
        
    except Exception as erro:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno ao processar métrica: {str(erro)}'}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """
    Endpoint para consultar métricas (Semana 2)
    
    Parâmetros (query string):
    - host_id (obrigatório): ID do host
    - limit (opcional, padrão 20): número de registros
    - offset (opcional, padrão 0): deslocamento para paginação
    
    Exemplo: GET /api/metrics?host_id=1&limit=10&offset=0
    """
    try:
        # Parâmetros obrigatórios
        host_id = request.args.get('host_id')
        
        if not host_id:
            return jsonify({'erro': 'Parâmetro "host_id" é obrigatório'}), 400
        
        # Valida se host existe
        host = HostModel.query.get(host_id)
        if not host:
            return jsonify({'erro': f'Host com id {host_id} não encontrado'}), 404
        
        # Parâmetros opcionais com valores padrão
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validações
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0
        
        # Busca as métricas ordenadas por timestamp decrescente
        metricas = MetricModel.query.filter_by(host_id=host_id)\
            .order_by(MetricModel.timestamp.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        # Total de métricas do host
        total = MetricModel.query.filter_by(host_id=host_id).count()
        
        return jsonify({
            'metrics': [m.to_dict() for m in metricas],
            'total': total,
            'limit': limit,
            'offset': offset,
            'host_id': host_id,
            'hostname': host.hostname
        }), 200
        
    except Exception as erro:
        return jsonify({'erro': f'Erro ao buscar métricas: {str(erro)}'}), 500


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
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
    print("   POST /api/metrics    (Semana 2)")
    print("   GET  /api/metrics    (Semana 2 - consulta)")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)