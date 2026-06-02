# GET routes permanecem abertas nesta etapa para não quebrar o frontend,
# que ainda não envia o header X-API-Key. Decisão consciente — fechar GET
# numa etapa futura após o frontend ser adaptado para incluir o header.

import functools

from flask import current_app, jsonify, request


def require_api_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        api_key = current_app.config.get('API_KEY', '')
        if not api_key:
            return jsonify({"error": "API key not configured — generate one in Settings"}), 401
        if request.headers.get("X-API-Key") != api_key:
            return jsonify({"error": "invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return wrapper
