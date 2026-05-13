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
        """
        Recebe e persiste o discovery gerado pelo Agent.

        O endpoint aceita dois formatos de payload, dependendo do ambiente
        onde o agente está sendo executado:

        --- MÁQUINA FÍSICA (ex: Linux Mint) ---
        {
            "type": "discovery",
            "metadata": { "schema_version": "1.0", "notes": [] },
            "environment": { "is_virtualized": false, "hypervisor": null },
            "cpu": {
                "model_name": "Intel(R) Core(TM) i5-4690 CPU @ 3.50GHz",
                "vendor": "GenuineIntel",
                "cores_logical": 4,
                "frequency": {
                    "base_mhz": null,
                    "max_mhz": 3900.0,
                    "min_mhz": 800.0
                }
            },
            "memory": {
                "total_mb": 11895.33,
                "total_gb": 11.62,
                "slots": {
                    "modules": [
                        { "size_gb": 4.0, "type": "DDR3", "speed_mhz": 1333 }
                    ]
                }
            },
            "disk": {
                "total_disks": 1,
                "disks": [
                    {
                        "device": "/dev/sda",
                        "model": "TOSHIBA DT01ACA100",
                        "size": { "bytes": 1000204886016, "gb": 931.51 }
                    }
                ]
            }
        }

        --- MÁQUINA VIRTUAL (ex: Ubuntu 24.04 em VMware) ---
        {
            "type": "discovery",
            "metadata": { "schema_version": "1.0", "notes": ["..."] },
            "environment": { "is_virtualized": true, "hypervisor": "VMware" },
            "system": {
                "hostname": "teste-ubuntu",
                "os": {
                    "name": "Ubuntu",
                    "pretty_name": "Ubuntu 24.04.4 LTS",
                    "version_id": "24.04"
                },
                "kernel": { "release": "6.8.0-110-generic" },
                "uptime_seconds": 808
            },
            "cpu": {
                "model_name": "AMD Ryzen 5 7520U with Radeon Graphics",
                "topology": { "vcpus": 2 },
                "frequency": {
                    "base_mhz": { "value": null },
                    "max_mhz": { "value": 2794.546 }
                }
            },
            "memory": {
                "total": { "bytes": 2013175808, "gb": 1.87 },
                "slots": { "modules": [] }
            },
            "disk": {
                "total_disks": 1,
                "disks": [
                    {
                        "device": "/dev/sda",
                        "model": "VMware Virtual S",
                        "size": { "bytes": 32212254720, "gb": 30.0 }
                    }
                ]
            },
            "network": {
                "total_interfaces": 2,
                "default_gateway": { "gateway": "192.168.48.2", "interface": "ens33" },
                "interfaces": [
                    {
                        "name": "ens33",
                        "mac": "00:0c:29:2e:bd:12",
                        "ipv4": [{ "address": "192.168.48.129", "prefix": 24 }]
                    }
                ]
            },
            "motherboard": {
                "manufacturer": null,
                "product_name": null,
                "bios": { "vendor": null, "version": null }
            }
        }

        Campos obrigatórios: nenhum (o endpoint é tolerante a ausências).
        O hostname e IP são extraídos do payload ou inferidos do request.

        Retorna 201 Created com os dados persistidos.
        """
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
                host.last_seen = datetime.utcnow()

            agent = _upsert_agent(db, AgentModel, host.id, campos)

            discovery = HostDiscoveryModel.query.filter_by(
                host_id=host.id
            ).first()

            if not discovery:
                discovery = HostDiscoveryModel(host_id=host.id)
                db.session.add(discovery)

            # Campos comuns (físico e VM)
            discovery.is_virtualized    = campos['is_virtualized']
            discovery.hypervisor        = campos['hypervisor']
            discovery.cpu_model         = campos['cpu_model']
            discovery.cpu_cores         = campos['cpu_vcpus']
            discovery.cpu_clock_base_mhz = campos['cpu_clock_base_mhz']
            discovery.cpu_max_mhz       = campos['cpu_max_mhz']
            discovery.total_memory_gb   = campos['memory_total_gb']
            discovery.disk_total_gb     = campos['disk_total_gb']
            discovery.memories          = campos['memories']
            discovery.disks             = campos['disks']
            discovery.networks          = campos['networks']

            # Campos exclusivos da VM (system)
            discovery.os_name           = campos['os_name']
            discovery.os_version        = campos['os_version']
            discovery.kernel_release    = campos['kernel_release']
            discovery.uptime_seconds    = campos['uptime_seconds']

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


# ==================== HELPERS ====================

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
    """
    Extrai campos do payload de discovery.

    Compatível com dois formatos:
    - Máquina física: cpu.cores_logical, memory.total_mb, frequency como valores diretos
    - VM: cpu.topology.vcpus, memory.total.gb, frequency como objetos com .value
    """
    agent       = dados.get('agent') or {}
    system      = dados.get('system') or {}
    environment = dados.get('environment') or {}
    metadata    = dados.get('metadata') or {}
    cpu         = dados.get('cpu') or {}
    memory      = dados.get('memory') or {}
    os_info     = system.get('os') or {}
    kernel      = system.get('kernel') or {}

    ip_address = (
        agent.get('primary_ip')
        or dados.get('primary_ip')
        or _get_primary_ip_from_network(dados.get('network'))
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
        environment, 'is_virtualized',
        fallback=dados.get('is_virtualized', False),
    )

    # cpu_vcpus: VM usa topology.vcpus, física usa cores_logical direto
    cpu_vcpus = (
        _get_nested(cpu, 'topology', 'vcpus')
        or cpu.get('cores_logical')
        or dados.get('cpu_vcpus')
    )

    # memory_total_gb: VM usa memory.total.gb, física usa memory.total_gb ou total_mb
    memory_total_gb = (
        _get_nested(memory, 'total', 'gb')
        or memory.get('total_gb')
        or (memory['total_mb'] / 1024 if memory.get('total_mb') else None)
        or dados.get('memory_total_gb')
    )

    return {
        'hostname':          hostname,
        'ip_address':        ip_address,
        'agent_id':          _safe_int(agent.get('agent_id') or dados.get('agent_id')),
        'agent_version':     metadata.get('schema_version') or dados.get('agent_version'),
        'is_virtualized':    bool(is_virtualized),
        'hypervisor':        _get_value(environment, 'hypervisor', fallback=dados.get('hypervisor')),

        # CPU
        'cpu_model':         cpu.get('model_name') or dados.get('cpu_model'),
        'cpu_vcpus':         cpu_vcpus,
        'cpu_clock_base_mhz': _get_cpu_freq(cpu, 'base_mhz', fallback=dados.get('cpu_clock_base_mhz')),
        'cpu_max_mhz':       _get_cpu_freq(cpu, 'max_mhz',  fallback=dados.get('cpu_max_mhz')),

        # Memória
        'memory_total_gb':   memory_total_gb,
        'memories':          memory or dados.get('memories'),

        # Disco
        'disk_total_gb':     _get_disk_total_gb(dados),
        'disks':             _get_nested(dados, 'disk', 'disks', fallback=dados.get('disks')),

        # Rede
        'networks':          dados.get('network') or dados.get('networks'),

        # Sistema (exclusivo VM)
        'os_name':           os_info.get('pretty_name') or os_info.get('name'),
        'os_version':        os_info.get('version_id'),
        'kernel_release':    kernel.get('release'),
        'uptime_seconds':    system.get('uptime_seconds'),
    }


def _get_cpu_freq(cpu, field, fallback=None):
    """
    Extrai frequência de CPU nos dois formatos:
    - Físico: cpu.frequency.max_mhz = 3900.0  (valor direto)
    - VM:     cpu.frequency.max_mhz = { "value": 2794.546 }  (objeto com .value)
    """
    freq = _get_nested(cpu, 'frequency', field)
    if freq is None:
        return fallback
    if isinstance(freq, dict):
        value = freq.get('value')
        return int(float(value)) if value is not None else fallback
    return int(float(freq))


def _get_primary_ip_from_network(network):
    """Tenta extrair o IP primário da interface padrão (payload da VM)."""
    if not isinstance(network, dict):
        return None
    gateway_iface = (network.get('default_gateway') or {}).get('interface')
    for iface in (network.get('interfaces') or []):
        if iface.get('name') == gateway_iface:
            ipv4_list = iface.get('ipv4') or []
            if ipv4_list:
                return ipv4_list[0].get('address')
    return None


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

    agent.host_id      = host_id
    agent.agent_version = campos['agent_version']
    agent.last_checkin = datetime.utcnow()
    agent.status       = 'active'

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