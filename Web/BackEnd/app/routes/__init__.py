# app/routes/__init__.py
# Inicializador do pacote de rotas
# Semana 5: adicionado register_alerts_routes

from .discovery import register_discovery_routes
from .logs import register_log_routes
from .metrics import register_metric_routes
from .alerts import register_alerts_routes  # Semana 5

__all__ = [
    'register_discovery_routes',
    'register_log_routes',
    'register_metric_routes',
    'register_alerts_routes',  # Semana 5
]