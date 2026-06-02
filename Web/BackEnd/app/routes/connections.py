# app/routes/connections.py
# Blueprint responsável por receber e persistir conexões TCP ativas enviadas pelo agente.
# Semana 6: implementação inicial com detecção de port scan via flag do agente.
# Correção: ip_origem do alerta usa o IP remoto mais frequente, não o primary_ip do host.

from collections import Counter
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from ..utils.auth import require_api_key

# Blueprint criado aqui — registro feito em app.py via register_connections_routes()
connections_bp = Blueprint('connections', __name__)


def register_connections_routes(app, db, HostModel, ActiveConnectionModel, AlertModel, check_port_scan_fn):
    """
    Registra as rotas de conexões TCP na aplicação Flask.

    Recebe todas as dependências por parâmetro para manter o padrão de
    injeção do projeto — sem imports diretos de modelos dentro deste arquivo.

    Parâmetros:
        app                  — instância Flask
        db                   — instância SQLAlchemy
        HostModel            — modelo da tabela host
        ActiveConnectionModel — modelo da tabela active_connections
        AlertModel           — modelo da tabela alerts
        check_port_scan_fn   — função check_port_scan de detection.py (injetada)
    """

    @connections_bp.route('/api/connections', methods=['POST'])
    @require_api_key
    def receber_conexoes():
        """
        Recebe o payload do agente com as conexões TCP ativas do host.

        Fluxo:
            1. Valida e extrai campos do payload
            2. Persiste cada conexão na tabela active_connections
            3. Se port_scan_detected=true no payload, aciona check_port_scan()
            4. Retorna 201 Created com resumo do processamento
        """
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({'erro': 'Payload JSON ausente ou inválido'}), 400

        # --- Extração dos campos globais (mesmo padrão dos outros endpoints) ---
        global_info = dados.get('global', {})
        host_id_raw = global_info.get('host_id')
        primary_ip  = global_info.get('primary_ip', '')

        if not host_id_raw:
            return jsonify({'erro': 'Campo global.host_id obrigatório'}), 400

        # host_id chega como string no payload — converter para inteiro
        try:
            host_id = int(host_id_raw)
        except (ValueError, TypeError):
            return jsonify({'erro': 'global.host_id deve ser numérico'}), 400

        # --- Timestamp do payload (fallback para agora em UTC se ausente ou inválido) ---
        timestamp_raw = dados.get('timestamp')
        try:
            timestamp = datetime.fromisoformat(timestamp_raw)
        except (TypeError, ValueError):
            timestamp = datetime.now(timezone.utc)

        # --- Listas do payload ---
        conexoes          = dados.get('connections', [])
        scan_sources      = dados.get('scan_sources', {})   # {attacker_ip: distinct_port_count}
        port_scan_flag    = dados.get('port_scan_detected', bool(scan_sources))

        # --- Persistência das conexões ---
        registros_salvos = 0

        try:
            for conn in conexoes:
                # Mapeamento dos campos do agente para o modelo do banco:
                #   local_port  → dst_port  (porta do serviço no host monitorado)
                #   remote_ip   → src_ip    (IP remoto que iniciou a conexão)
                #   remote_port → src_port  (porta efêmera do lado remoto)
                #   state       → status    (estado TCP: ESTABLISHED, etc.)
                #   protocol    → "tcp"     (fixo — agente só coleta TCP)
                #   dst_ip      → primary_ip do host (extraído do campo global)
                nova_conexao = ActiveConnectionModel(
                    host_id      = host_id,
                    timestamp    = timestamp,
                    src_ip       = conn.get('remote_ip', ''),
                    src_port     = conn.get('remote_port', 0),
                    dst_ip       = primary_ip,
                    dst_port     = conn.get('local_port', 0),
                    protocol     = 'tcp',
                    status       = conn.get('state', ''),
                    duration_sec = conn.get('duration_sec', None),
                )
                db.session.add(nova_conexao)
                registros_salvos += 1

            db.session.commit()

        except Exception as erro:
            db.session.rollback()
            return jsonify({'erro': f'Falha ao salvar conexões: {str(erro)}'}), 500

        # --- Detecção de port scan ---
        # O agente usa tcpdump para detectar SYN entrantes e envia scan_sources:
        # {ip_atacante: qtd_portas_distintas}. O backend cria um alerta por IP.
        # Fallback para payloads antigos (sem scan_sources): usa heurística de frequência.
        alertas_criados = 0

        if port_scan_flag:
            host      = HostModel.query.get(host_id)
            _hn       = host.hostname    if host else ''
            _hip      = host.ip_address  if host else primary_ip

            if scan_sources:
                # Novo modelo: agente fornece IPs atacantes diretamente com contagem
                for ip_atacante, port_count in scan_sources.items():
                    criado = check_port_scan_fn(
                        db, AlertModel, host_id,
                        ip_atacante, int(port_count),
                        _hn, _hip,
                    )
                    if criado:
                        alertas_criados += 1
            else:
                # Fallback: payload antigo sem scan_sources
                if conexoes:
                    contagem = Counter(
                        c.get('remote_ip', '') for c in conexoes if c.get('remote_ip')
                    )
                    ip_atacante = contagem.most_common(1)[0][0] if contagem else primary_ip
                else:
                    ip_atacante = primary_ip
                criado = check_port_scan_fn(db, AlertModel, host_id, ip_atacante, 0, _hn, _hip)
                if criado:
                    alertas_criados += 1

        return jsonify({
            'mensagem':       'Conexões recebidas com sucesso',
            'host_id':        host_id,
            'total_salvo':    registros_salvos,
            'port_scan_flag': port_scan_flag,
            'scan_sources':   scan_sources,
            'alertas_criados': alertas_criados,
        }), 201

    # Registra o blueprint na aplicação
    app.register_blueprint(connections_bp)