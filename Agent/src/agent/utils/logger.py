import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("/var/log/monitor-agent")
LOG_FILE = LOG_DIR / "agent.log"
LOG_LEVEL = os.getenv("MONITOR_LOG_LEVEL", "INFO").upper()

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("monitor-agent")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stdout → journald quando rodando como serviço systemd
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    # arquivo em /var/log/monitor-agent/agent.log
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB por arquivo
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning(
            "Sem permissão para criar %s. Logs apenas no stdout.", LOG_DIR
        )

    _logger = logger
    return logger


def log_payload(logger: logging.Logger, label: str, payload: dict) -> None:
    """Loga o payload completo em nível DEBUG."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s:\n%s", label, json.dumps(payload, indent=2, default=str))
