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
            memory_used_mb = db.Column(db.Integer, nullable=True)
            memory_free_mb = db.Column(db.Integer, nullable=True)
            memory_total_mb = db.Column(db.Integer, nullable=True)
            disk_percent = db.Column(db.Float, nullable=True)
            disk_used_mb = db.Column(db.BigInteger, nullable=True)
            disk_free_mb = db.Column(db.BigInteger, nullable=True)
            disk_total_mb = db.Column(db.BigInteger, nullable=True)
            net_sent = db.Column('net_sent_bytes', db.BigInteger, nullable=True)
            net_recv = db.Column('net_recv_bytes', db.BigInteger, nullable=True)
            disk_read_iops = db.Column('read_iops', db.Float, nullable=True)
            disk_write_iops = db.Column('write_iops', db.Float, nullable=True)
            disk_read_bytes_per_sec = db.Column('read_bytes_per_sec', db.Float, nullable=True)
            disk_write_bytes_per_sec = db.Column('write_bytes_per_sec', db.Float, nullable=True)
            net_sent_per_sec = db.Column('net_sent_bytes_per_sec', db.Float, nullable=True)
            net_recv_per_sec = db.Column('net_recv_bytes_per_sec', db.Float, nullable=True)

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
                    'memory_used_mb': self.memory_used_mb,
                    'memory_free_mb': self.memory_free_mb,
                    'memory_total_mb': self.memory_total_mb,
                    'disk_percent': self.disk_percent,
                    'disk_used_mb': self.disk_used_mb,
                    'disk_free_mb': self.disk_free_mb,
                    'disk_total_mb': self.disk_total_mb,
                    'net_sent': self.net_sent,
                    'net_recv': self.net_recv,
                    'disk_read_iops': self.disk_read_iops,
                    'disk_write_iops': self.disk_write_iops,
                    'disk_read_bytes_per_sec': self.disk_read_bytes_per_sec,
                    'disk_write_bytes_per_sec': self.disk_write_bytes_per_sec,
                    'net_sent_per_sec': self.net_sent_per_sec,
                    'net_recv_per_sec': self.net_recv_per_sec,
                }

        return MetricModel
