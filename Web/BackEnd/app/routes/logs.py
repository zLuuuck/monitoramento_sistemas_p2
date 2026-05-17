# app/routes/logs.py
# Rotas para recebimento e consulta de logs do sistema operacional
# Semana 4: integração com parse_ssh_log()
# Semana 5: chama check_brute_force() quando log SSH é "failed"

from flask import Blueprint, jsonify, request
from datetime import datetime

# Parser SSH — Semana 4
from ..utils.parsers import parse_ssh_log

# Detecção de brute force — Semana 5
from ..utils.detection import check_brute_force


def register_log_routes(app, db, HostModel, LogEntryModel, AlertModel):
    """
    Registra as rotas de logs no app Flask.

    Semana 5: AlertModel adicionado como parâmetro para ser injetado
    em check_brute_force() sem criar import circular.
    """
    app.register_blueprint(
        create_log_blueprint(app, db, HostModel, LogEntryModel, AlertModel)
    )


def create_log_blueprint(app, db, HostModel, LogEntryModel, AlertModel):
    logs_bp = Blueprint('logs', __name__, url_prefix='/api')

    @logs_bp.route('/logs', methods=['POST'])
    def post_logs():
        """
        Recebe logs do sistema operacional enviados pelo agente e persiste no banco.

        Payload esperado:
        {
            "host_id":   1,
            "timestamp": "2026-05-19T14:35:00Z",
            "log_type":  "auth",
            "raw_line":  "May 19 14:35:00 server sshd[123]: Failed password for root from 192.168.1.100 port 22 ssh2"
        }

        Campos obrigatórios: host_id, timestamp, raw_line
        Campos opcionais:    log_type (padrão: "system")

        Semana 4: quando log_type == "auth", chama parse_ssh_log() automaticamente.
        Semana 5: quando parsed_data contém status == "failed", chama
                  check_brute_force() para detectar possível ataque SSH.
        """
        try:
            dados = request.get_json(silent=True)

            # Valida payload JSON
            if dados is None:
                return jsonify({'erro': 'Payload JSON é obrigatório'}), 400

            # Valida campo obrigatório: host_id
            if 'host_id' not in dados:
                return jsonify({'erro': 'Campo "host_id" é obrigatório'}), 400

            try:
                host_id = int(dados['host_id'])
            except (TypeError, ValueError):
                return jsonify({'erro': 'Campo "host_id" deve ser numérico'}), 400

            # Valida campo obrigatório: timestamp
            if 'timestamp' not in dados:
                return jsonify({'erro': 'Campo "timestamp" é obrigatório'}), 400

            # Valida campo obrigatório: raw_line (não pode ser vazio)
            if 'raw_line' not in dados or not str(dados['raw_line']).strip():
                return jsonify({'erro': 'Campo "raw_line" é obrigatório'}), 400

            # Verifica se o host existe no banco
            host = HostModel.query.get(host_id)
            if not host:
                return jsonify({'erro': f'Host com id {host_id} não encontrado'}), 404

            # Converte timestamp — aceita ISO 8601 (string) ou Unix timestamp (número)
            ts_raw = dados['timestamp']
            try:
                if isinstance(ts_raw, (int, float)):
                    timestamp = datetime.utcfromtimestamp(ts_raw)
                else:
                    timestamp = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
            except (ValueError, OSError):
                return jsonify({
                    'erro': 'Formato de timestamp inválido. Use ISO 8601 (ex: 2026-05-19T14:35:00Z)'
                }), 400

            # log_type padrão: "system"
            log_type = dados.get('log_type') or 'system'
            raw_line = str(dados['raw_line'])

            # ------------------------------------------------------------------
            # SEMANA 4 — Parsing automático de logs de autenticação SSH
            # ------------------------------------------------------------------
            parsed_data = None

            if log_type == 'auth':
                parsed_data = parse_ssh_log(raw_line)

                if parsed_data is not None:
                    app.logger.info(
                        "Log SSH parseado | host_id=%s | status=%s | usuario=%s | ip=%s",
                        host_id,
                        parsed_data.get('status'),
                        parsed_data.get('usuario'),
                        parsed_data.get('ip_origem'),
                    )
                else:
                    # Linha de auth.log que não é evento SSH (sudo, PAM, cron...)
                    app.logger.info(
                        "Log auth sem padrão SSH | host_id=%s | linha: %.100s",
                        host_id,
                        raw_line,
                    )

            # Persiste o log com parsed_data preenchido ou null
            log = LogEntryModel(
                host_id     = host_id,
                timestamp   = timestamp,
                log_type    = log_type,
                raw_line    = raw_line,
                parsed_data = parsed_data,
            )

            db.session.add(log)
            db.session.commit()

            # ------------------------------------------------------------------
            # SEMANA 5 — Detecção de brute force SSH
            #
            # Após salvar o log com sucesso, verifica se o IP está realizando
            # um ataque de força bruta. A detecção ocorre somente quando:
            #   - log_type é "auth"
            #   - parsed_data foi preenchido (linha SSH reconhecida)
            #   - status do evento é "failed" (tentativa com falha)
            #
            # check_brute_force() é chamado APÓS o commit para garantir que
            # a falha recém-salva já seja contabilizada na janela de tempo.
            #
            # A função retorna True se um novo alerta foi criado.
            # Falhas internas da detecção são silenciosas — não afetam o 201.
            # ------------------------------------------------------------------
            alerta_criado = False

            if (
                log_type    == 'auth'
                and parsed_data is not None
                and parsed_data.get('status') == 'failed'
            ):
                ip_origem = parsed_data.get('ip_origem')
                if ip_origem:
                    alerta_criado = check_brute_force(
                        db,
                        LogEntryModel,
                        AlertModel,
                        host_id,
                        ip_origem,
                    )

                    if alerta_criado:
                        app.logger.warning(
                            "ALERTA DE BRUTE FORCE criado | host_id=%s | ip=%s",
                            host_id, ip_origem,
                        )

            return jsonify({
                'message':       'Log salvo com sucesso',
                'log_id':        log.id,
                'host_id':       log.host_id,
                'log_type':      log.log_type,
                'parsed':        parsed_data is not None,
                'alerta_criado': alerta_criado,  # Semana 5: informa ao chamador
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
            host_id  (obrigatório)
            limit    (padrão: 20, máximo: 100)
            offset   (padrão: 0)
            log_type (opcional — ex: "auth", "system")

        Exemplo: GET /api/logs?host_id=1&log_type=auth&limit=10
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

            # Parâmetros de paginação com limites de segurança
            limit    = min(max(request.args.get('limit',  20, type=int), 1), 100)
            offset   = max(request.args.get('offset',  0, type=int), 0)
            log_type = request.args.get('log_type')

            # Monta a query com filtros
            query = LogEntryModel.query.filter_by(host_id=host_id)
            if log_type:
                query = query.filter_by(log_type=log_type)

            # Ordena do mais recente para o mais antigo — aproveita idx_logs_host_ts
            logs = (
                query
                .order_by(LogEntryModel.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            # Conta o total sem paginação para o frontend calcular páginas
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