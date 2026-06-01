from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import or_


def register_metric_routes(app, db, HostModel, AgentModel, MetricModel, AlertModel=None, check_resource_alert_fn=None):
    """Registra as rotas de metricas no app Flask."""
    app.register_blueprint(
        create_metric_blueprint(db, HostModel, AgentModel, MetricModel, AlertModel, check_resource_alert_fn)
    )


def create_metric_blueprint(db, HostModel, AgentModel, MetricModel, AlertModel=None, check_resource_alert_fn=None):
    metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')

    @metrics_bp.route('/metrics', methods=['POST'])
    def post_metrics():
        """Recebe metricas continuas do agente, normaliza e persiste."""
        try:
            dados = request.get_json(silent=True)
            if dados is None:
                return jsonify({'erro': 'Payload JSON e obrigatorio'}), 400

            normalized = _normalize_metrics_payload(dados, request.remote_addr)
            if normalized['timestamp'] is None:
                return jsonify({'erro': 'Campo "timestamp" e obrigatorio'}), 400

            host = _resolve_host(db, HostModel, AgentModel, normalized)
            if not host:
                return jsonify({'erro': 'Nao foi possivel identificar o host'}), 400

            metric = MetricModel(
                host_id=host.id,
                timestamp=normalized['timestamp'],
                cpu_percent=normalized['cpu_percent'],
                memory_percent=normalized['memory_percent'],
                memory_used_mb=normalized['memory_used_mb'],
                memory_free_mb=normalized['memory_free_mb'],
                memory_total_mb=normalized['memory_total_mb'],
                disk_percent=normalized['disk_percent'],
                disk_used_mb=normalized['disk_used_mb'],
                disk_free_mb=normalized['disk_free_mb'],
                disk_total_mb=normalized['disk_total_mb'],
                net_sent=normalized['net_sent_bytes'],
                net_recv=normalized['net_recv_bytes'],
                disk_read_iops=normalized['disk_read_iops'],
                disk_write_iops=normalized['disk_write_iops'],
                disk_read_bytes_per_sec=normalized['disk_read_bytes_per_sec'],
                disk_write_bytes_per_sec=normalized['disk_write_bytes_per_sec'],
                net_sent_per_sec=normalized['net_sent_bytes_per_sec'],
                net_recv_per_sec=normalized['net_recv_bytes_per_sec'],
            )

            host.last_seen = datetime.utcnow()
            agent = AgentModel.query.filter_by(host_id=host.id).first()
            if agent:
                agent.last_checkin = datetime.utcnow()
                agent.status = 'active'

            db.session.add(metric)
            db.session.commit()

            # Verifica limiares de recursos e cria alertas se necessário
            if AlertModel is not None and check_resource_alert_fn is not None:
                check_resource_alert_fn(db, AlertModel, host.id, 'cpu_high',  normalized['cpu_percent']    or 0.0, 80.0)
                check_resource_alert_fn(db, AlertModel, host.id, 'mem_high',  normalized['memory_percent'] or 0.0, 80.0)
                check_resource_alert_fn(db, AlertModel, host.id, 'disk_high', normalized['disk_percent']   or 0.0, 80.0)

            return jsonify({
                'message': 'Metrica salva com sucesso',
                'metric_id': metric.id,
                'host_id': metric.host_id,
                'timestamp': metric.timestamp.isoformat(),
            }), 201

        except Exception as erro:
            db.session.rollback()
            return jsonify({'erro': f'Erro interno ao processar metrica: {str(erro)}'}), 500

    @metrics_bp.route('/metrics', methods=['GET'])
    def get_metrics():
        """Consulta metricas de um host com paginacao."""
        try:
            host_id_raw = request.args.get('host_id')
            if not host_id_raw:
                return jsonify({'erro': 'Parametro "host_id" e obrigatorio'}), 400

            try:
                host_id = int(host_id_raw)
            except (TypeError, ValueError):
                return jsonify({'erro': 'Parametro "host_id" deve ser numerico'}), 400

            host = HostModel.query.get(host_id)
            if not host:
                return jsonify({'erro': f'Host com id {host_id} nao encontrado'}), 404

            limit = min(max(request.args.get('limit', 20, type=int), 1), 100)
            offset = max(request.args.get('offset', 0, type=int), 0)

            query = MetricModel.query.filter_by(host_id=host_id)
            latest_metric = query.order_by(MetricModel.timestamp.desc()).first()
            metricas = query.order_by(MetricModel.timestamp.desc()) \
                .limit(limit) \
                .offset(offset) \
                .all()

            ordered_metrics = list(reversed(metricas))

            return jsonify({
                'metrics': [m.to_dict() for m in ordered_metrics],
                'total': query.count(),
                'limit': limit,
                'offset': offset,
                'host_id': host_id,
                'hostname': host.hostname,
                'last_metric_at': latest_metric.timestamp.isoformat() if latest_metric else None,
                'is_online': _is_online_from_metric(latest_metric.timestamp if latest_metric else None),
                'status': 'online' if _is_online_from_metric(latest_metric.timestamp if latest_metric else None) else 'offline',
            }), 200

        except Exception as erro:
            return jsonify({'erro': f'Erro ao buscar metricas: {str(erro)}'}), 500

    return metrics_bp


def _normalize_metrics_payload(dados, remote_addr):
    global_info = dados.get('global') or {}
    data = dados.get('data') if isinstance(dados.get('data'), dict) else dados
    cpu = data.get('cpu') or {}
    memory = data.get('memory') or {}
    disk = data.get('disk') or {}
    network = data.get('network') or {}

    timestamp = _parse_timestamp(dados.get('timestamp') or data.get('timestamp'))

    mem_total_bytes = _number(memory.get('total') or data.get('memory_total_bytes'))
    mem_used_bytes = _number(memory.get('used') or data.get('memory_used_bytes'))
    mem_free_bytes = (
        mem_total_bytes - mem_used_bytes
        if mem_total_bytes is not None and mem_used_bytes is not None
        else None
    )

    disk_total_bytes = _number(disk.get('total') or data.get('disk_total_bytes'))
    disk_used_bytes = _number(disk.get('used') or data.get('disk_used_bytes'))
    disk_free_bytes = (
        disk_total_bytes - disk_used_bytes
        if disk_total_bytes is not None and disk_used_bytes is not None
        else None
    )

    return {
        'host_id': _safe_int(
            dados.get('host_id')
            or data.get('host_id')
            or global_info.get('host_id')
            or request.args.get('host_id')
        ),
        'agent_id': _safe_int(global_info.get('agent_id') or dados.get('agent_id')),
        'hostname': (
            global_info.get('hostname')
            or dados.get('hostname')
            or data.get('hostname')
        ),
        'ip_address': (
            global_info.get('primary_ip')
            or dados.get('primary_ip')
            or data.get('primary_ip')
            or remote_addr
        ),
        'schema_version': global_info.get('schema_version') or dados.get('schema_version'),
        'timestamp': timestamp,
        'cpu_percent': _number(cpu.get('percent') or data.get('cpu_percent')),
        'memory_percent': _number(memory.get('percent') or data.get('memory_percent')),
        'memory_used_mb': _bytes_to_mb(mem_used_bytes),
        'memory_free_mb': _bytes_to_mb(mem_free_bytes),
        'memory_total_mb': _bytes_to_mb(mem_total_bytes),
        'disk_percent': _number(disk.get('percent') or data.get('disk_percent')),
        'disk_used_mb': _bytes_to_mb(disk_used_bytes),
        'disk_free_mb': _bytes_to_mb(disk_free_bytes),
        'disk_total_mb': _bytes_to_mb(disk_total_bytes),
        'net_sent_bytes': _safe_int(network.get('bytes_sent') or data.get('net_sent') or data.get('net_sent_bytes')),
        'net_recv_bytes': _safe_int(network.get('bytes_recv') or data.get('net_recv') or data.get('net_recv_bytes')),
        'disk_read_iops': _number(disk.get('read_iops')),
        'disk_write_iops': _number(disk.get('write_iops')),
        'disk_read_bytes_per_sec': _number(disk.get('read_bytes_per_sec')),
        'disk_write_bytes_per_sec': _number(disk.get('write_bytes_per_sec')),
        'net_sent_bytes_per_sec': _number(network.get('bytes_sent_per_sec')),
        'net_recv_bytes_per_sec': _number(network.get('bytes_recv_per_sec')),
    }


def _resolve_host(db, HostModel, AgentModel, normalized):
    filters = []
    if normalized['host_id'] is not None:
        filters.append(HostModel.id == normalized['host_id'])
    if normalized['hostname']:
        filters.append(HostModel.hostname == normalized['hostname'])
    if normalized['ip_address']:
        filters.append(HostModel.ip_address == normalized['ip_address'])

    host = HostModel.query.filter(or_(*filters)).first() if filters else None
    if host:
        return host

    if not normalized['hostname']:
        return None

    host = HostModel(
        id=normalized['host_id'],
        hostname=normalized['hostname'],
        ip_address=normalized['ip_address'],
        last_seen=datetime.utcnow(),
    )
    db.session.add(host)
    db.session.flush()

    agent = AgentModel(host_id=host.id)
    if normalized['agent_id'] is not None:
        agent.id = normalized['agent_id']
    agent.agent_version = normalized['schema_version']
    agent.last_checkin = datetime.utcnow()
    agent.status = 'active'
    db.session.add(agent)

    return host


def _parse_timestamp(value):
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value)
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, OSError, TypeError):
        return None


def _is_online_from_metric(last_metric_at, timeout_seconds=30):
    if last_metric_at is None:
        return False
    if last_metric_at.tzinfo is not None:
        last_metric_at = last_metric_at.astimezone(timezone.utc).replace(tzinfo=None)
    return (datetime.utcnow() - last_metric_at).total_seconds() < timeout_seconds


def _number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bytes_to_mb(value):
    if value is None:
        return None
    return int(value / (1024 * 1024))
