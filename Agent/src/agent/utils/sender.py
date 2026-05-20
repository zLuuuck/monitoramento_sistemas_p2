# =============================================================================
# utils/sender.py
# Envio dos payloads ao backend central via HTTP POST.
# Inclui fila de retry para falhas de conexão e endpoint de heartbeat.
# =============================================================================

import os
from urllib.parse import urljoin

import requests

from agent.utils import retry_queue
from agent.utils.logger import get_logger, log_payload

logger = get_logger()

API_BASE_URL    = os.getenv("MONITOR_API_BASE_URL", "http://api.monitoramento.lan")
DISCOVERY_URL   = os.getenv("MONITOR_DISCOVERY_URL")   or urljoin(API_BASE_URL.rstrip("/") + "/", "api/discovery")
METRICS_URL     = os.getenv("MONITOR_METRICS_URL")     or urljoin(API_BASE_URL.rstrip("/") + "/", "api/metrics")
LOGS_URL        = os.getenv("MONITOR_LOGS_URL")        or urljoin(API_BASE_URL.rstrip("/") + "/", "api/logs")
CONNECTIONS_URL = os.getenv("MONITOR_CONNECTIONS_URL") or urljoin(API_BASE_URL.rstrip("/") + "/", "api/connections")
HEARTBEAT_URL   = os.getenv("MONITOR_HEARTBEAT_URL")   or urljoin(API_BASE_URL.rstrip("/") + "/", "api/heartbeat")
TOKEN           = os.getenv("MONITOR_TOKEN", "")


def _make_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return headers


def flush_retry_queue() -> None:
    """Reenvia payloads enfileirados durante falhas de conexão anteriores."""
    queue = retry_queue.load_queue()
    if not queue:
        return

    logger.info("Fila de retry: tentando reenviar %d payload(s)...", len(queue))
    remaining = []
    for i, item in enumerate(queue):
        try:
            resp = requests.post(item["url"], json=item["payload"], headers=_make_headers(), timeout=10)
            resp.raise_for_status()
            logger.info("Retry bem-sucedido para %s", item["url"])
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # conexão ainda indisponível — mantém este e todos os seguintes
            remaining.extend(queue[i:])
            break
        except requests.exceptions.HTTPError as e:
            # servidor rejeitou (4xx/5xx) — descarta, não tem sentido retentar
            logger.error(
                "Retry rejeitado com HTTP %s em %s — payload descartado",
                e.response.status_code,
                item["url"],
            )
        except Exception:
            logger.exception("Retry falhou inesperadamente para %s — payload descartado", item["url"])

    retry_queue.save_queue(remaining)
    if remaining:
        logger.info("Fila de retry: %d payload(s) ainda pendentes.", len(remaining))
    else:
        logger.info("Fila de retry esvaziada com sucesso.")


def send_data(data: dict, url: str | None = None) -> dict | None:
    """
    Envia payload ao backend via HTTP POST.
    Em caso de falha de conexão ou timeout, enfileira para retry.
    Erros HTTP (4xx/5xx) são logados mas não enfileirados.
    """
    target_url = url or _url_for_payload(data)
    headers    = _make_headers()

    log_payload(logger, f"Payload → {target_url}", data)

    try:
        response = requests.post(target_url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Enviado para %s - status: %s", target_url, response.status_code)
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Servidor inacessivel em %s — payload enfileirado para retry", target_url)
        retry_queue.enqueue(data, target_url)
    except requests.exceptions.Timeout:
        logger.error("Timeout ao enviar para %s — payload enfileirado para retry", target_url)
        retry_queue.enqueue(data, target_url)
    except requests.exceptions.HTTPError as e:
        body = getattr(e.response, "text", "")
        logger.error(
            "Erro HTTP %s ao enviar para %s: %s",
            e.response.status_code,
            target_url,
            body,
        )
    except Exception:
        logger.exception("Erro inesperado ao enviar para %s", target_url)
    return None


def send_discovery(data: dict) -> dict | None:
    return send_data(data, DISCOVERY_URL)


def send_metrics(data: dict) -> dict | None:
    return send_data(data, METRICS_URL)


def send_log(data: dict) -> dict | None:
    return send_data(data, LOGS_URL)


def send_connections(data: dict) -> dict | None:
    return send_data(data, CONNECTIONS_URL)


def send_heartbeat(data: dict) -> dict | None:
    """
    Envia heartbeat mínimo ao backend.
    Falhas são logadas em DEBUG e nunca enfileiradas — heartbeat stale não tem valor.
    """
    try:
        resp = requests.post(HEARTBEAT_URL, json=data, headers=_make_headers(), timeout=5)
        resp.raise_for_status()
        return resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
    except Exception:
        logger.debug("Heartbeat falhou para %s (ignorado)", HEARTBEAT_URL)
        return None


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
