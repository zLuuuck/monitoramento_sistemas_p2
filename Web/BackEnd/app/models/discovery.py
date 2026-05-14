from datetime import datetime


class HostDiscovery:
    """Wrapper para o modelo HostDiscovery."""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela host_discovery"""

        class HostDiscoveryModel(db.Model):
            __tablename__ = 'host_discovery'
            __table_args__ = {'extend_existing': True}

            host_id = db.Column(db.Integer, db.ForeignKey(
                'host.id'), primary_key=True)
            discovery_date = db.Column(db.DateTime, default=datetime.utcnow)
            cpu_model = db.Column(db.String(200), nullable=True)
            cpu_cores = db.Column(db.Integer, nullable=True)
            cpu_clock_base_mhz = db.Column(db.Integer, nullable=True)
            memories = db.Column(db.JSON, nullable=True)
            disks = db.Column(db.JSON, nullable=True)
            networks = db.Column(db.JSON, nullable=True)
            total_memory_gb = db.Column(db.Float, nullable=True)
            is_virtualized = db.Column(db.Boolean, nullable=True)
            hypervisor = db.Column(db.String(50), nullable=True)
            cpu_max_mhz = db.Column(db.Integer, nullable=True)
            disk_total_gb = db.Column(db.Float, nullable=True)

            host = db.relationship('HostModel', back_populates='discovery')

            def to_dict(self):
                """Converte o objeto HostDiscovery para dicionario."""
                return {
                    'host_id': self.host_id,
                    'discovery_date': self.discovery_date.isoformat() if self.discovery_date else None,
                    'is_virtualized': self.is_virtualized,
                    'hypervisor': self.hypervisor,
                    'cpu_model': self.cpu_model,
                    'cpu_cores': self.cpu_cores,
                    'cpu_clock_base_mhz': self.cpu_clock_base_mhz,
                    'cpu_max_mhz': self.cpu_max_mhz,
                    'memories': self.memories,
                    'disks': self.disks,
                    'networks': self.networks,
                    'total_memory_gb': self.total_memory_gb,
                    'disk_total_gb': self.disk_total_gb,
                }

            def para_dict(self):
                return self.to_dict()

        return HostDiscoveryModel
