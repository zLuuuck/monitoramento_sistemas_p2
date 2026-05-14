from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from datetime import datetime


def register_discovery_routes(app, db, HostModel, AgentModel, HostDiscoveryModel):
    """Registra as rotas de discovery no app Flask."""
    app.register_blueprint(
        create_discovery_blueprint(db, HostModel, AgentModel, HostDiscoveryModel)
    )


def create_discovery_blueprint(db, HostModel, AgentModel, HostDiscoveryModel):
    discovery_bp = Blueprint('discovery', __name__, url_prefix='/api')

    @discovery_bp.route('/discovery', methods=['POST'])
    def post_discovery():
        """Recebe e persiste o discovery gerado pelo Agent."""
        try:
            dados = request.get_json(silent=True)

            if dados is None:
                return jsonify({'erro': 'Payload JSON e obrigatorio'}), 400

            if dados.get('type') not in (None, 'discovery'):
                return jsonify({'erro': 'Payload enviado nao e do tipo discovery'}), 400

            campos = _extract_discovery_fields(dados, request.remote_addr)

            host = HostModel.query.filter(
                or_(
                    HostModel.ip_address == campos['ip_address'],
                    HostModel.hostname == campos['hostname'],
                )
            ).first()

            if not host:
                host = HostModel(
                    hostname=campos['hostname'],
                    ip_address=campos['ip_address'],
                )
                db.session.add(host)
                db.session.flush()
            else:
                host.hostname = campos['hostname']

            agent = _upsert_agent(db, AgentModel, host.id, campos)

            discovery = HostDiscoveryModel.query.filter_by(
                host_id=host.id
            ).first()

            if not discovery:
                discovery = HostDiscoveryModel(host_id=host.id)
                db.session.add(discovery)

            discovery.is_virtualized = campos['is_virtualized']
            discovery.hypervisor = campos['hypervisor']
            discovery.cpu_model = campos['cpu_model']
            discovery.cpu_cores = campos['cpu_vcpus']
            discovery.cpu_clock_base_mhz = campos['cpu_clock_base_mhz']
            discovery.cpu_max_mhz = campos['cpu_max_mhz']
            discovery.total_memory_gb = campos['memory_total_gb']
            discovery.disk_total_gb = campos['disk_total_gb']
            discovery.memories = campos['memories']
            discovery.disks = campos['disks']
            discovery.networks = campos['networks']

            db.session.commit()

            return jsonify({
                'message': 'discovery recebido e salvo com sucesso',
                'discovery_id': discovery.host_id,
                'host_id': host.id,
                'agent_id': agent.id,
                'hostname': host.hostname,
                'ip_host': host.ip_address,
                'is_virtualized': discovery.is_virtualized,
            }), 201

        except Exception as erro:
            db.session.rollback()
            return jsonify({
                'erro': f'Erro interno ao processar discovery: {str(erro)}'
            }), 500

    @discovery_bp.route('/discovery', methods=['GET'])
    def get_discovery():
        """Retorna os dados de discovery cadastrados para exibicao no frontend."""
        try:
            host_id = request.args.get('host_id', type=int)

            query = HostDiscoveryModel.query.join(HostModel)
            if host_id is not None:
                query = query.filter(HostDiscoveryModel.host_id == host_id)

            discoveries = query.order_by(HostDiscoveryModel.discovery_date.desc()).all()

            return jsonify({
                'discoveries': [
                    _discovery_to_response(discovery)
                    for discovery in discoveries
                ],
                'total': len(discoveries),
            }), 200

        except Exception as erro:
            return jsonify({
                'erro': f'Erro ao buscar discovery: {str(erro)}'
            }), 500

    return discovery_bp


def _discovery_to_response(discovery):
    dados = discovery.to_dict()
    host = discovery.host

    dados['host'] = {
        'id': host.id,
        'hostname': host.hostname,
        'ip_address': host.ip_address,
        'created_at': host.created_at.isoformat() if host.created_at else None,
        'last_seen': host.last_seen.isoformat() if host.last_seen else None,
    } if host else None

    return dados


def _extract_discovery_fields(dados, remote_addr):
    agent = dados.get('agent') or {}
    system = dados.get('system') or {}
    environment = dados.get('environment') or {}
    metadata = dados.get('metadata') or {}
    cpu = dados.get('cpu') or {}
    memory = dados.get('memory') or {}

    ip_address = (
        agent.get('primary_ip')
        or dados.get('primary_ip')
        or remote_addr
        or '0.0.0.0'
    )

    hostname = (
        agent.get('hostname')
        or system.get('hostname')
        or dados.get('hostname')
        or f'host-{ip_address.replace(".", "-")}'
    )

    is_virtualized = _get_value(
        environment,
        'is_virtualized',
        fallback=dados.get('is_virtualized', False),
    )

    return {
        'hostname': hostname,
        'ip_address': ip_address,
        'agent_id': _safe_int(agent.get('agent_id') or dados.get('agent_id')),
        'agent_version': metadata.get('schema_version') or dados.get('agent_version'),
        'is_virtualized': bool(is_virtualized),
        'hypervisor': _get_value(
            environment,
            'hypervisor',
            fallback=dados.get('hypervisor'),
        ),
        'cpu_model': cpu.get('model_name') or dados.get('cpu_model'),
        'cpu_vcpus': _get_nested(
            cpu,
            'topology',
            'vcpus',
            fallback=dados.get('cpu_vcpus'),
        ),
        'cpu_clock_base_mhz': _get_int_from_nested(
            cpu,
            'frequency',
            'base_mhz',
            'value',
            fallback=dados.get('cpu_clock_base_mhz'),
        ),
        'cpu_max_mhz': _get_int_from_nested(
            cpu,
            'frequency',
            'max_mhz',
            'value',
            fallback=dados.get('cpu_max_mhz'),
        ),
        'memory_total_gb': _get_nested(
            memory,
            'total',
            'gb',
            fallback=dados.get('memory_total_gb'),
        ),
        'disk_total_gb': _get_disk_total_gb(dados),
        'memories': memory or dados.get('memories'),
        'disks': _get_nested(dados, 'disk', 'disks', fallback=dados.get('disks')),
        'networks': dados.get('network') or dados.get('networks'),
    }


def _upsert_agent(db, AgentModel, host_id, campos):
    agent = None

    if campos['agent_id'] is not None:
        agent = AgentModel.query.get(campos['agent_id'])

    if not agent:
        agent = AgentModel.query.filter_by(host_id=host_id).first()

    if not agent:
        agent = AgentModel(host_id=host_id)
        if campos['agent_id'] is not None:
            agent.id = campos['agent_id']
        db.session.add(agent)

    agent.host_id = host_id
    agent.agent_version = campos['agent_version']
    agent.last_checkin = datetime.utcnow()
    agent.status = 'active'

    return agent


def _get_value(source, key, fallback=None):
    if isinstance(source, dict):
        return source.get(key, fallback)
    return fallback


def _get_nested(source, *keys, fallback=None):
    current = source
    for key in keys:
        if not isinstance(current, dict):
            return fallback
        current = current.get(key)
    return fallback if current is None else current


def _get_int_from_nested(source, *keys, fallback=None):
    value = _get_nested(source, *keys, fallback=fallback)
    if value is None:
        return None
    return int(float(value))


def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_disk_total_gb(dados):
    if dados.get('disk_total_gb') is not None:
        return dados.get('disk_total_gb')

    disk = dados.get('disk') or {}
    disks = disk.get('disks') or []
    total = 0.0

    for item in disks:
        size = item.get('size') or {}
        gb = size.get('gb')
        if gb is None and size.get('bytes') is not None:
            gb = size['bytes'] / (1024 ** 3)
        if gb is not None:
            total += float(gb)

    return round(total, 2) if disks else None
