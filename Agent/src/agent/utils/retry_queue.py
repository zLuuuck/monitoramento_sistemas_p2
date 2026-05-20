import json
import os
from pathlib import Path

from agent.utils.logger import get_logger

QUEUE_FILE = Path(os.getenv("MONITOR_RETRY_FILE", "/var/cache/monitor-agent/retry_queue.json"))
MAX_ITEMS  = int(os.getenv("MONITOR_RETRY_MAX", "50"))

logger = get_logger()


def enqueue(payload: dict, url: str) -> None:
    queue = _load()
    if len(queue) >= MAX_ITEMS:
        queue.pop(0)
        logger.warning("Fila de retry cheia (%d). Item mais antigo descartado.", MAX_ITEMS)
    queue.append({"url": url, "payload": payload})
    _save(queue)


def load_queue() -> list[dict]:
    return _load()


def save_queue(queue: list[dict]) -> None:
    _save(queue)


def _load() -> list:
    if not QUEUE_FILE.exists():
        return []
    try:
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Fila de retry corrompida em %s — resetando.", QUEUE_FILE)
        return []


def _save(queue: list) -> None:
    try:
        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_FILE.write_text(json.dumps(queue), encoding="utf-8")
    except Exception:
        logger.exception("Erro ao salvar fila de retry em %s", QUEUE_FILE)
