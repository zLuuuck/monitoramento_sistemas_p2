# app/models/__init__.py
# Inicializador do pacote de modelos
# Semana 5: adicionado Alert
# Semana 6: adicionado ActiveConnection

from .host import Host
from .agent import Agent
from .discovery import HostDiscovery
from .metric import Metric
from .log import LogEntry
from .alert import Alert
from .connection import ActiveConnection  # Semana 6

# Dicionário para armazenar as classes modelo instanciadas
modelos = {}


def registrar_modelos(db):
    """Registra os modelos no SQLAlchemy após a criação do db."""

    from .host import Host as HostClass
    from .agent import Agent as AgentClass
    from .discovery import HostDiscovery as DiscoveryClass
    from .metric import Metric as MetricClass
    from .log import LogEntry as LogEntryClass
    from .alert import Alert as AlertClass
    from .connection import ActiveConnection as ConnectionClass  # Semana 6

    # Instancia cada modelo via get_model(db) — padrão do projeto
    HostModel             = HostClass.get_model(db)
    AgentModel            = AgentClass.get_model(db)
    DiscoveryModel        = DiscoveryClass.get_model(db)
    MetricModel           = MetricClass.get_model(db)
    LogEntryModel         = LogEntryClass.get_model(db)
    AlertModel            = AlertClass.get_model(db)
    ActiveConnectionModel = ConnectionClass.get_model(db)  # Semana 6

    modelos['Host']             = HostModel
    modelos['Agent']            = AgentModel
    modelos['HostDiscovery']    = DiscoveryModel
    modelos['Metric']           = MetricModel
    modelos['LogEntry']         = LogEntryModel
    modelos['Alert']            = AlertModel
    modelos['ActiveConnection'] = ActiveConnectionModel  # Semana 6

    return HostModel, AgentModel, DiscoveryModel, MetricModel, LogEntryModel, AlertModel, ActiveConnectionModel


__all__ = [
    'Host', 'Agent', 'HostDiscovery', 'Metric', 'LogEntry', 'Alert',
    'ActiveConnection',       # Semana 6
    'registrar_modelos', 'modelos',
]