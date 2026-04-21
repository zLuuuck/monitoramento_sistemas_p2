from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas (ideal para desenvolvimento)

# Configuração do banco de dados (exemplo com PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://user:pass@database:5432/monitoramento'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do SQLAlchemy (comentada por enquanto, será usada depois)
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy(app)

# ---------- Rotas da API REST ----------

@app.route('/api/status', methods=['GET'])
def status():
    """Endpoint de verificação de saúde da API."""
    return jsonify({
        'status': 'online',
        'service': 'API Monitoramento',
        'version': '1.0.0'
    })

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Olá do BackEnd Flask!'})

# Exemplo de rota POST (para testes)
@app.route('/api/data', methods=['POST'])
def receive_data():
    from flask import request
    data = request.get_json()
    return jsonify({'received': data}), 201

# ---------- Execução ----------
if __name__ == '__main__':
    # Isso só é usado se rodarmos com "python app.py", mas usaremos "flask run"
    app.run(host='0.0.0.0', port=5000, debug=True)