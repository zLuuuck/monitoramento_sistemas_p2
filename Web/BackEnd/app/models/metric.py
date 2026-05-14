# Modelo para a tabela 'metrics' - métricas contínuas do sistema

from datetime import datetime


class Metric:
    """Classe wrapper para o modelo Metric (tabela metrics)"""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela metrics"""

        class MetricModel(db.Model):
            __tablename__ = 'metrics'
            __table_args__ = {'extend_existing': True}

            id = db.Column(db.Integer, primary_key=True)
            host_id = db.Column(db.Integer, db.ForeignKey(
                'host.id'), nullable=False)
            timestamp = db.Column(db.DateTime, nullable=False)
            cpu_percent = db.Column(db.Float, nullable=True)
            memory_percent = db.Column(db.Float, nullable=True)
            disk_percent = db.Column(db.Float, nullable=True)
            net_sent = db.Column('net_sent_bytes', db.BigInteger, nullable=True)
            net_recv = db.Column('net_recv_bytes', db.BigInteger, nullable=True)

            # Relacionamento com host
            host = db.relationship('HostModel', back_populates='metrics')

            def to_dict(self):
                """Converte o objeto Metric para dicionário"""
                return {
                    'id': self.id,
                    'host_id': self.host_id,
                    'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                    'cpu_percent': self.cpu_percent,
                    'memory_percent': self.memory_percent,
                    'disk_percent': self.disk_percent,
                    'net_sent': self.net_sent,
                    'net_recv': self.net_recv
                }

        return MetricModel
