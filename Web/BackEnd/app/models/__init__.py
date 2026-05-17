# app/models/__init__.py
# Inicializador do pacote de modelos
# Semana 5: adicionado Alert

from .host import Host
from .agent import Agent
from .discovery import HostDiscovery
from .metric import Metric
from .log import LogEntry
from .alert import Alert  # Semana 5

# Dicionário para armazenar as classes modelo instanciadas
modelos = {}


def registrar_modelos(db):
    """Registra os modelos no SQLAlchemy após a criação do db."""

    from .host import Host as HostClass
    from .agent import Agent as AgentClass
    from .discovery import HostDiscovery as DiscoveryClass
    from .metric import Metric as MetricClass
    from .log import LogEntry as LogEntryClass
    from .alert import Alert as AlertClass  # Semana 5

    # Instancia cada modelo via get_model(db) — padrão do projeto
    HostModel        = HostClass.get_model(db)
    AgentModel       = AgentClass.get_model(db)
    DiscoveryModel   = DiscoveryClass.get_model(db)
    MetricModel      = MetricClass.get_model(db)
    LogEntryModel    = LogEntryClass.get_model(db)
    AlertModel       = AlertClass.get_model(db)  # Semana 5

    modelos['Host']          = HostModel
    modelos['Agent']         = AgentModel
    modelos['HostDiscovery'] = DiscoveryModel
    modelos['Metric']        = MetricModel
    modelos['LogEntry']      = LogEntryModel
    modelos['Alert']         = AlertModel  # Semana 5

    return HostModel, AgentModel, DiscoveryModel, MetricModel, LogEntryModel, AlertModel


__all__ = [
    'Host', 'Agent', 'HostDiscovery', 'Metric', 'LogEntry', 'Alert',
    'registrar_modelos', 'modelos',
]