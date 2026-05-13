# app/models/__init__.py
# Inicializador do pacote de modelos

from .host import Host
from .agent import Agent
from .discovery import HostDiscovery
from .metric import Metric
from .log import LogEntry

# Dicionário para armazenar as classes modelo
modelos = {}

def registrar_modelos(db):
    """Registra os modelos no SQLAlchemy após a criação do db"""

    from .host import Host as HostClass
    from .agent import Agent as AgentClass
    from .discovery import HostDiscovery as DiscoveryClass
    from .metric import Metric as MetricClass
    from .log import LogEntry as LogEntryClass

    # Usando get_model (padrão em todos os modelos)
    HostModel = HostClass.get_model(db)
    AgentModel = AgentClass.get_model(db)
    DiscoveryModel = DiscoveryClass.get_model(db)
    MetricModel = MetricClass.get_model(db)
    LogEntryModel = LogEntryClass.get_model(db)

    modelos['Host'] = HostModel
    modelos['Agent'] = AgentModel
    modelos['HostDiscovery'] = DiscoveryModel
    modelos['Metric'] = MetricModel
    modelos['LogEntry'] = LogEntryModel

    return HostModel, AgentModel, DiscoveryModel, MetricModel, LogEntryModel

__all__ = ['Host', 'Agent', 'HostDiscovery', 'Metric', 'LogEntry', 'registrar_modelos', 'modelos']