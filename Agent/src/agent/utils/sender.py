# =============================================================================
# utils/sender.py
# Envio dos payloads (discovery e métricas) ao backend central via HTTP POST.
# =============================================================================

import os
from urllib.parse import urljoin

import requests

API_BASE_URL = os.getenv("MONITOR_API_BASE_URL", "http://192.168.0.2:5000")
DISCOVERY_URL = os.getenv("MONITOR_DISCOVERY_URL") or urljoin(
    API_BASE_URL.rstrip("/") + "/", "api/discovery"
)
METRICS_URL = os.getenv("MONITOR_METRICS_URL") or urljoin(
    API_BASE_URL.rstrip("/") + "/", "api/metrics"
)
TOKEN = os.getenv("MONITOR_TOKEN", "")


def send_data(data: dict, url: str | None = None) -> dict | None:
    """
    Envia um payload ao backend central via HTTP POST com autenticação Bearer.

    Parâmetros:
        data (dict): payload a ser enviado (discovery ou métricas)

    Cabeçalhos enviados:
        Content-Type  : application/json
        Authorization : Bearer <TOKEN>

    Tratamento de erros:
        - Imprime o status HTTP em caso de sucesso
        - Captura e imprime erros de conexão sem travar o agente
    """
    target_url = url or _url_for_payload(data)
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    try:
        response = requests.post(target_url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Enviado para {target_url} - status: {response.status_code}")
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        print(f"Erro de conexao: servidor inacessivel em {target_url}")
    except requests.exceptions.Timeout:
        print(f"Timeout ao tentar enviar para {target_url}")
    except requests.exceptions.HTTPError as e:
        body = getattr(e.response, "text", "")
        print(f"Erro HTTP ao enviar para {target_url}: {e.response.status_code} {body}")
    except Exception as e:
        print(f"Erro ao enviar para {target_url}: {e}")
    return None


def send_discovery(data: dict) -> dict | None:
    return send_data(data, DISCOVERY_URL)


def send_metrics(data: dict) -> dict | None:
    return send_data(data, METRICS_URL)


def _url_for_payload(data: dict) -> str:
    collection_type = (
        data.get("type")
        or data.get("collection_type")
        or (data.get("global") or {}).get("collection_type")
    )
    if collection_type == "discovery":
        return DISCOVERY_URL
    if collection_type == "metrics":
        return METRICS_URL
    return METRICS_URL

# =============================================================================
# FIM utils/sender.py
# =============================================================================
