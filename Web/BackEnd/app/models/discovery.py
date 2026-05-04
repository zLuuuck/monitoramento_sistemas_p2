# Modelo para a tabela 'host_discovery' - dados de hardware coletados

from datetime import datetime


class HostDiscovery:
    """Classe wrapper para o modelo HostDiscovery (tabela host_discovery)"""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela host_discovery"""

        class HostDiscoveryModel(db.Model):
            __tablename__ = 'host_discovery'
            __table_args__ = {'extend_existing': True}

            id = db.Column(db.Integer, primary_key=True)
            host_id = db.Column(db.Integer, db.ForeignKey(
                'hosts.id'), nullable=False)
            is_virtualized = db.Column(db.Boolean, nullable=False)
            hypervisor = db.Column(db.String(100), nullable=True)
            cpu_model = db.Column(db.String(255), nullable=True)
            cpu_vcpus = db.Column(db.Integer, nullable=True)
            memory_total_gb = db.Column(db.Float, nullable=True)
            disk_total_gb = db.Column(db.Float, nullable=True)
            raw_data = db.Column(db.JSON, nullable=False)  # Payload completo
            created_at = db.Column(db.DateTime, default=datetime.utcnow)

            # Relacionamento com host
            host = db.relationship('HostModel', back_populates='discovery')

            def para_dict(self):
                """Converte o objeto HostDiscovery para dicionário"""
                return {
                    'id': self.id,
                    'host_id': self.host_id,
                    'is_virtualized': self.is_virtualized,
                    'hypervisor': self.hypervisor,
                    'cpu_model': self.cpu_model,
                    'cpu_vcpus': self.cpu_vcpus,
                    'memory_total_gb': self.memory_total_gb,
                    'disk_total_gb': self.disk_total_gb,
                    'raw_data': self.raw_data,
                    'created_at': self.created_at.isoformat() if self.created_at else None
                }

        return HostDiscoveryModel
