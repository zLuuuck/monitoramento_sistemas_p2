# app/utils/__init__.py
# Inicializador do pacote de utilitários — criado na Semana 4

from .parsers import parse_ssh_log, count_failed_logins

__all__ = ['parse_ssh_log', 'count_failed_logins']