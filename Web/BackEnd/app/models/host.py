# app/models/host.py
# Modelo para a tabela 'hosts' - informações dos hosts monitorados

from datetime import datetime


class Host:
    """Classe wrapper para o modelo Host (tabela hosts)"""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela hosts"""

        class HostModel(db.Model):
            __tablename__ = 'hosts'
            __table_args__ = {'extend_existing': True}

            id = db.Column(db.Integer, primary_key=True)
            hostname = db.Column(db.String(255), nullable=False)
            ip_address = db.Column(db.String(45), nullable=False)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)

            # Relacionamento com host_discovery (1 host pode ter 0 ou 1 discovery) - SEMANA 1
            discovery = db.relationship(
                'HostDiscoveryModel', back_populates='host', uselist=False)

            # Relacionamento com metrics (1 host pode ter N métricas) - SEMANA 2 (NOVO)
            metrics = db.relationship(
                'MetricModel', back_populates='host', lazy='dynamic')

            def para_dict(self):
                """Converte o objeto Host para dicionário"""
                return {
                    'id': self.id,
                    'hostname': self.hostname,
                    'ip_address': self.ip_address,
                    'created_at': self.created_at.isoformat() if self.created_at else None
                }

        return HostModel
