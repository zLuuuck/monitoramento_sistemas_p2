# app/routes/logs.py
# Rotas para recebimento e consulta de logs do sistema operacional

from flask import Blueprint, jsonify, request
from datetime import datetime


def register_log_routes(app, db, HostModel, LogEntryModel):
    """Registra as rotas de logs no app Flask."""
    app.register_blueprint(
        create_log_blueprint(db, HostModel, LogEntryModel)
    )


def create_log_blueprint(db, HostModel, LogEntryModel):
    logs_bp = Blueprint('logs', __name__, url_prefix='/api')

    @logs_bp.route('/logs', methods=['POST'])
    def post_logs():
        """
        Recebe logs do sistema operacional enviados pelo agente e persiste no banco.

        Payload esperado (definido com a equipe do agente — tarefa 3.1):
        {
            "host_id":   1,
            "timestamp": "2026-04-21T14:35:00Z",
            "log_type":  "auth",
            "raw_line":  "Apr 21 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100"
        }

        Campos obrigatórios: host_id, timestamp, raw_line
        Campos opcionais:    log_type (padrão: "system"), parsed_data

        Retorna 201 Created com ID do log salvo.
        """
        try:
            dados = request.get_json(silent=True)

            if dados is None:
                return jsonify({'erro': 'Payload JSON é obrigatório'}), 400

            # Validação: host_id obrigatório e numérico
            if 'host_id' not in dados:
                return jsonify({'erro': 'Campo "host_id" é obrigatório'}), 400

            try:
                host_id = int(dados['host_id'])
            except (TypeError, ValueError):
                return jsonify({'erro': 'Campo "host_id" deve ser numérico'}), 400

            # Validação: timestamp obrigatório
            if 'timestamp' not in dados:
                return jsonify({'erro': 'Campo "timestamp" é obrigatório'}), 400

            # Validação: raw_line obrigatório
            if 'raw_line' not in dados or not str(dados['raw_line']).strip():
                return jsonify({'erro': 'Campo "raw_line" é obrigatório'}), 400

            # Verifica se o host existe no banco
            host = HostModel.query.get(host_id)
            if not host:
                return jsonify({'erro': f'Host com id {host_id} não encontrado'}), 404

            # Converte timestamp ISO 8601 ou Unix float para datetime
            ts_raw = dados['timestamp']
            try:
                if isinstance(ts_raw, (int, float)):
                    timestamp = datetime.utcfromtimestamp(ts_raw)
                else:
                    timestamp = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
            except (ValueError, OSError):
                return jsonify({'erro': 'Formato de timestamp inválido. Use ISO 8601 (ex: 2026-04-21T14:35:00Z)'}), 400

            # log_type: usa "system" como padrão se não informado
            log_type = dados.get('log_type') or 'system'

            # Cria o registro de log — parsed_data fica nulo até a Semana 4
            log = LogEntryModel(
                host_id     = host_id,
                timestamp   = timestamp,
                log_type    = log_type,
                raw_line    = str(dados['raw_line']),
                parsed_data = dados.get('parsed_data'),
            )

            db.session.add(log)
            db.session.commit()

            return jsonify({
                'message':  'Log salvo com sucesso',
                'log_id':   log.id,
                'host_id':  log.host_id,
                'log_type': log.log_type,
            }), 201

        except Exception as erro:
            db.session.rollback()
            return jsonify({
                'erro': f'Erro interno ao processar log: {str(erro)}'
            }), 500

    @logs_bp.route('/logs', methods=['GET'])
    def get_logs():
        """
        Consulta logs de um host com paginação e filtro por tipo.

        Parâmetros (query string):
        - host_id  (obrigatório)
        - limit    (padrão 20, máximo 100)
        - offset   (padrão 0)
        - log_type (opcional — filtra por tipo, ex: "auth")

        Exemplo: GET /api/logs?host_id=1&log_type=auth&limit=10
        """
        try:
            # host_id obrigatório e numérico
            host_id_raw = request.args.get('host_id')
            if not host_id_raw:
                return jsonify({'erro': 'Parâmetro "host_id" é obrigatório'}), 400

            try:
                host_id = int(host_id_raw)
            except (TypeError, ValueError):
                return jsonify({'erro': 'Parâmetro "host_id" deve ser numérico'}), 400

            # Verifica se o host existe
            host = HostModel.query.get(host_id)
            if not host:
                return jsonify({'erro': f'Host com id {host_id} não encontrado'}), 404

            # Parâmetros de paginação
            limit    = min(max(request.args.get('limit',  20, type=int), 1), 100)
            offset   = max(request.args.get('offset', 0, type=int), 0)
            log_type = request.args.get('log_type')

            # Monta query base filtrando por host
            query = LogEntryModel.query.filter_by(host_id=host_id)

            # Aplica filtro por tipo se informado
            if log_type:
                query = query.filter_by(log_type=log_type)

            # Ordena do mais recente para o mais antigo
            logs = query.order_by(LogEntryModel.timestamp.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()

            # Conta total sem paginação
            total_query = LogEntryModel.query.filter_by(host_id=host_id)
            if log_type:
                total_query = total_query.filter_by(log_type=log_type)
            total = total_query.count()

            return jsonify({
                'logs':     [log.to_dict() for log in logs],
                'total':    total,
                'limit':    limit,
                'offset':   offset,
                'host_id':  host_id,
                'hostname': host.hostname,
                'log_type': log_type,
            }), 200

        except Exception as erro:
            return jsonify({
                'erro': f'Erro ao buscar logs: {str(erro)}'
            }), 500

    return logs_bp