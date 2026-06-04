# app/routes/connections.py
# Endpoint de sinalização de port scan enviado pelo agente.
# Não persiste dados — apenas aciona check_port_scan() quando o agente
# reporta detecção de varredura via tcpdump.

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from ..utils.auth import require_api_key

portscan_bp = Blueprint('portscan', __name__)


def register_portscan_routes(app, db, HostModel, AlertModel, check_port_scan_fn):
    """
    Registra a rota POST /api/security/portscan.

    Parâmetros injetados para manter o padrão do projeto (sem imports diretos
    de modelos dentro deste arquivo).
    """

    @portscan_bp.route('/api/security/portscan', methods=['POST'])
    @require_api_key
    def receber_portscan():
        """
        Recebe sinal de port scan detectado pelo agente via tcpdump.

        Payload esperado:
            {
                "global":             {"host_id": str|int, "primary_ip": str, ...},
                "timestamp":          str ISO-8601,
                "port_scan_detected": true,
                "scan_sources":       {"ip_atacante": qtd_portas, ...}
            }

        O agente só envia este request quando port_scan_detected=True.
        Se scan_sources chegar vazio (inconsistência do agente), o alerta NÃO é
        criado — atribuir o scan ao IP do próprio host poluiria os dados.
        """
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({'erro': 'Payload JSON ausente ou inválido'}), 400

        global_info = dados.get('global', {})
        host_id_raw = global_info.get('host_id')
        primary_ip  = global_info.get('primary_ip', '')

        if not host_id_raw:
            return jsonify({'erro': 'Campo global.host_id obrigatório'}), 400

        try:
            host_id = int(host_id_raw)
        except (ValueError, TypeError):
            return jsonify({'erro': 'global.host_id deve ser numérico'}), 400

        scan_sources = dados.get('scan_sources', {})

        if not scan_sources:
            app.logger.warning(
                'portscan host=%s: port_scan_detected=true mas scan_sources vazio — alerta suprimido',
                host_id,
            )
            return jsonify({
                'mensagem':       'Sinal recebido sem scan_sources — alerta suprimido',
                'host_id':        host_id,
                'alertas_criados': 0,
            }), 200

        host  = HostModel.query.get(host_id)
        _hn   = host.hostname   if host else ''
        _hip  = host.ip_address if host else primary_ip

        alertas_criados = 0
        for ip_atacante, port_count in scan_sources.items():
            criado = check_port_scan_fn(
                db, AlertModel, host_id,
                ip_atacante, int(port_count),
                _hn, _hip,
            )
            if criado:
                alertas_criados += 1

        return jsonify({
            'mensagem':        'Sinal de port scan processado',
            'host_id':         host_id,
            'scan_sources':    scan_sources,
            'alertas_criados': alertas_criados,
        }), 201

    app.register_blueprint(portscan_bp)
