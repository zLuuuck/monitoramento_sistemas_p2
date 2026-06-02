# app/routes/alerts.py
# Rotas para consulta e resolução de alertas de segurança
# Semana 5: GET /api/alerts e PATCH /api/alerts/<id>/resolve

from flask import Blueprint, jsonify, request
from datetime import datetime

from ..utils.auth import require_api_key


def register_alerts_routes(app, db, HostModel, AlertModel):
    """Registra as rotas de alertas no app Flask."""
    app.register_blueprint(
        create_alerts_blueprint(db, HostModel, AlertModel)
    )


def create_alerts_blueprint(db, HostModel, AlertModel):
    alerts_bp = Blueprint('alerts', __name__, url_prefix='/api')

    @alerts_bp.route('/alerts', methods=['GET'])
    def get_alerts():
        """
        Retorna alertas de segurança com filtros opcionais.

        Parâmetros (query string):
            status  — "active" (padrão), "resolved" ou "all"
            host_id — filtra por host específico (opcional)
            limit   — máximo de registros (padrão: 20, máximo: 100)
            offset  — deslocamento para paginação (padrão: 0)

        Exemplos:
            GET /api/alerts
            GET /api/alerts?status=active&host_id=1
            GET /api/alerts?status=all&limit=50
            GET /api/alerts?status=resolved
        """
        try:
            # Parâmetro de status — "active" é o padrão (mais útil para o frontend)
            status   = request.args.get('status', 'active').lower()
            host_id  = request.args.get('host_id', type=int)
            limit    = min(max(request.args.get('limit',  20, type=int), 1), 100)
            offset   = max(request.args.get('offset',  0, type=int), 0)

            # Valida o valor do parâmetro status
            if status not in ('active', 'resolved', 'all'):
                return jsonify({
                    'erro': 'Parâmetro "status" deve ser "active", "resolved" ou "all"'
                }), 400

            # Monta a query base
            query = AlertModel.query

            # Aplica filtro de status
            if status == 'active':
                query = query.filter_by(resolved=False)
            elif status == 'resolved':
                query = query.filter_by(resolved=True)
            # "all" não filtra por resolved

            # Aplica filtro de host (opcional)
            if host_id is not None:
                # Verifica se o host existe
                host = HostModel.query.get(host_id)
                if not host:
                    return jsonify({
                        'erro': f'Host com id {host_id} não encontrado'
                    }), 404
                query = query.filter_by(host_id=host_id)

            # Conta total antes da paginação (para o frontend calcular páginas)
            total = query.count()

            # Aplica ordenação e paginação
            alertas = (
                query
                .order_by(AlertModel.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return jsonify({
                'alerts': [a.to_dict() for a in alertas],
                'total':  total,
                'status': status,
                'limit':  limit,
                'offset': offset,
            }), 200

        except Exception as erro:
            return jsonify({
                'erro': f'Erro ao buscar alertas: {str(erro)}'
            }), 500

    @alerts_bp.route('/alerts/<int:alerta_id>/resolve', methods=['PATCH'])
    @require_api_key
    def resolve_alert(alerta_id):
        """
        Marca um alerta como resolvido.

        Parâmetros de rota:
            alerta_id — ID do alerta a ser resolvido

        Retorna:
            200 OK com o alerta atualizado
            404 Not Found se o alerta não existir
            400 Bad Request se o alerta já estiver resolvido

        Exemplo:
            PATCH /api/alerts/3/resolve
        """
        try:
            # Busca o alerta pelo ID
            alerta = AlertModel.query.get(alerta_id)

            if not alerta:
                return jsonify({
                    'erro': f'Alerta com id {alerta_id} não encontrado'
                }), 404

            # Evita resolver um alerta que já foi resolvido
            if alerta.resolved:
                return jsonify({
                    'erro':      f'Alerta {alerta_id} já está resolvido',
                    'resolved_at': alerta.resolved_at.isoformat() if alerta.resolved_at else None,
                }), 400

            # Marca como resolvido e registra o momento da resolução
            alerta.resolved    = True
            alerta.resolved_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'message': f'Alerta {alerta_id} resolvido com sucesso',
                'alert':   alerta.to_dict(),
            }), 200

        except Exception as erro:
            db.session.rollback()
            return jsonify({
                'erro': f'Erro ao resolver alerta: {str(erro)}'
            }), 500

    return alerts_bp