# app/routes/logs.py
# Rotas para recebimento e consulta de logs do sistema operacional
# Semana 4: integração com parse_ssh_log()
# Semana 5: chama check_brute_force() quando log SSH é "failed"
# Semana 6: parse_ssh_log() substituído por parse_auth_log() — cobre todos
#           os eventos do auth.log (CRON, PAM, sudo, logind, disconnect)

from flask import Blueprint, jsonify, request
from datetime import datetime

# Semana 6: parse_auth_log substitui parse_ssh_log como ponto de entrada
from ..utils.parsers import parse_auth_log

# Detecção de brute force — Semana 5 (sem alteração)
from ..utils.detection import check_brute_force
from ..utils.auth import require_api_key


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
    @require_api_key
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
        Semana 6: parse_ssh_log() substituído por parse_auth_log(), que cobre
                  todos os tipos de evento do auth.log (CRON, PAM, sudo,
                  logind, disconnect). Nenhuma alteração no banco ou no agente.
        """
        try:
            dados = request.get_json(silent=True)

            # Valida payload JSON
            if dados is None:
                return jsonify({'erro': 'Payload JSON é obrigatório'}), 400

            # host_id aceito na raiz OU dentro do bloco "global" (padrão do agente)
            global_block = dados.get('global') or {}
            host_id_raw  = dados.get('host_id') if 'host_id' in dados else global_block.get('host_id')

            if host_id_raw is None:
                return jsonify({'erro': 'Campo "host_id" é obrigatório (raiz ou global.host_id)'}), 400

            try:
                host_id = int(host_id_raw)
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
            # SEMANA 6 — Parsing automático de todos os eventos do auth.log
            #
            # parse_auth_log() substitui parse_ssh_log(). Ela tenta em sequência
            # todos os parsers registrados e retorna o primeiro que casar:
            #   ssh_login       → Failed/Accepted password (comportamento anterior)
            #   sudo            → execução de comando privilegiado
            #   pam_auth_failure → falha de autenticação PAM
            #   ssh_disconnect  → encerramento de sessão SSH
            #   pam_session     → abertura/fechamento de sessão PAM (inclui CRON)
            #   logind_session  → eventos systemd-logind
            #
            # O campo event_type no parsed_data identifica o subtipo para o front.
            # Os campos status, usuario e ip_origem são mantidos nos mesmos
            # nomes para preservar compatibilidade com os índices JSONB do banco
            # e com a lógica de brute force existente.
            # ------------------------------------------------------------------
            parsed_data = None

            if log_type == 'auth':
                parsed_data = parse_auth_log(raw_line)

                if parsed_data is not None:
                    app.logger.info(
                        "Log auth parseado | host_id=%s | event_type=%s | status=%s | usuario=%s | ip=%s",
                        host_id,
                        parsed_data.get('event_type'),
                        parsed_data.get('status'),
                        parsed_data.get('usuario'),
                        parsed_data.get('ip_origem'),
                    )
                else:
                    # Linha de auth.log que nenhum parser reconheceu
                    app.logger.info(
                        "Log auth sem padrão reconhecido | host_id=%s | linha: %.100s",
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
            # SEMANA 5 — Detecção de brute force SSH (sem alteração)
            #
            # Continua funcionando porque parse_auth_log() preserva os campos
            # status = "failed" e ip_origem para eventos ssh_login,
            # exatamente como parse_ssh_log() fazia antes.
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
                        hostname = host.hostname,
                        host_ip  = host.ip_address or '',
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
                'event_type':    parsed_data.get('event_type') if parsed_data else None,
                'alerta_criado': alerta_criado,
            }), 201

        except Exception as erro:
            db.session.rollback()
            return jsonify({
                'erro': f'Erro interno ao processar log: {str(erro)}'
            }), 500

    @logs_bp.route('/logs', methods=['GET'])
    @require_api_key
    def get_logs():
        """
        Consulta logs com paginação e filtro por tipo.

        Parâmetros (query string):
            host_id  (opcional — quando ausente, retorna logs de todos os hosts)
            limit    (padrão: 20, máximo: 100)
            offset   (padrão: 0)
            log_type (opcional — ex: "auth", "system")

        Exemplo: GET /api/logs?host_id=1&log_type=auth&limit=10
        Exemplo (todos os hosts): GET /api/logs?log_type=auth&limit=50
        """
        try:
            host_id_raw = request.args.get('host_id')
            host_id = None
            host = None

            if host_id_raw:
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

            # Monta a query com filtros — sem host_id, abrange todos os hosts
            query = LogEntryModel.query
            if host_id is not None:
                query = query.filter_by(host_id=host_id)
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

            total = query.count()

            # Mapa host_id -> hostname para exibição na visão geral (todos os hosts)
            hostnames = {}
            if host_id is None and logs:
                ids = {log.host_id for log in logs}
                hostnames = {
                    h.id: h.hostname
                    for h in HostModel.query.filter(HostModel.id.in_(ids)).all()
                }

            logs_dict = []
            for log in logs:
                item = log.to_dict()
                if host_id is None:
                    item['hostname'] = hostnames.get(log.host_id)
                logs_dict.append(item)

            return jsonify({
                'logs':     logs_dict,
                'total':    total,
                'limit':    limit,
                'offset':   offset,
                'host_id':  host_id,
                'hostname': host.hostname if host else None,
                'log_type': log_type,
            }), 200

        except Exception as erro:
            return jsonify({
                'erro': f'Erro ao buscar logs: {str(erro)}'
            }), 500

    return logs_bp