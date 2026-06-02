# GET routes permanecem abertas nesta etapa para não quebrar o frontend,
# que ainda não envia o header X-API-Key. Decisão consciente — fechar GET
# numa etapa futura após o frontend ser adaptado para incluir o header.

import functools
import os

from flask import jsonify, request

_API_KEY = os.environ.get("API_KEY")
if not _API_KEY:
    raise RuntimeError(
        "A variável de ambiente API_KEY deve estar definida antes de subir o servidor"
    )


def require_api_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != _API_KEY:
            return jsonify({"error": "invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return wrapper
