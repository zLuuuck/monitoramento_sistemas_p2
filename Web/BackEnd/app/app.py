from flask import Flask, jsonify, request  # request movido para o topo (boa prática)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração do banco (ainda não será usado nesta etapa)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://user:pass@database:5432/monitoramento'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do SQLAlchemy (sem models por enquanto)
db = SQLAlchemy(app)


@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'service': 'API Monitoramento',
        'version': '1.0.0'
    })


@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Olá do BackEnd Flask!'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

# ❌ ROTA DE TESTE REMOVIDA (mantida comentada para histórico)
# @app.route('/api/data', methods=['POST'])
# def receive_data():
#     data = request.get_json()
#     return jsonify({'received': data}), 201


# ✅ ENDPOINT: DISCOVERY
@app.route('/api/discovery', methods=['POST'])
def discovery():
    # Recebe JSON enviado pelo agente
    data = request.get_json()

    # Extração segura da informação de virtualização
    environment = data.get('environment', {}) if data else {}
    is_virtualized = environment.get('is_virtualized')

    # Log dos dados recebidos (sem persistência no banco)
    app.logger.info(f"[DISCOVERY] Dados recebidos: {data}")
    app.logger.info(f"[DISCOVERY] Máquina virtualizada: {is_virtualized}")

    # Retorno conforme especificação
    return jsonify({
        "message": "discovery recebido",
        "is_virtualized": is_virtualized
    }), 201


# ✅ ENDPOINT: METRICS (mock)
@app.route('/api/metrics', methods=['POST'])
def metrics():
    # Recebe JSON (contrato ainda não definido)
    data = request.get_json()

    # Log dos dados recebidos
    app.logger.info(f"[METRICS] Dados recebidos: {data}")

    # ⚠️ IMPORTANTE:
    # Este endpoint será atualizado quando o contrato JSON
    # com a equipe do agente for definido.
    return jsonify({
        "message": "metrics recebido (mock)"
    }), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)