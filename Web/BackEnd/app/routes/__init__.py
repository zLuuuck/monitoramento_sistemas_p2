# app/routes/__init__.py
# Inicializador do pacote de rotas

from .discovery import register_discovery_routes
from .logs import register_log_routes

__all__ = ['register_discovery_routes', 'register_log_routes']