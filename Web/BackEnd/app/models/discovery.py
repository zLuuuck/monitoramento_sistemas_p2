from datetime import datetime


class HostDiscovery:
    """Wrapper para o modelo HostDiscovery."""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela host_discovery."""

        class HostDiscoveryModel(db.Model):
            __tablename__ = 'host_discovery'
            __table_args__ = {'extend_existing': True}

            # Chave primária e data
            host_id             = db.Column(db.Integer, db.ForeignKey('host.id'), primary_key=True)
            discovery_date      = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

            # CPU
            cpu_model           = db.Column(db.String(200),    nullable=True)
            cpu_cores           = db.Column(db.SmallInteger,   nullable=True)
            cpu_clock_base_mhz  = db.Column(db.Integer,        nullable=True)
            # cpu_ghz é coluna gerada pelo banco (GENERATED ALWAYS AS) — somente leitura
            cpu_ghz             = db.Column(db.Numeric(4, 1),  nullable=True)
            cpu_max_mhz         = db.Column(db.Integer,        nullable=True)

            # Memória e disco
            total_memory_gb     = db.Column(db.Numeric(10, 2), nullable=True)
            disk_total_gb       = db.Column(db.Numeric(10, 2), nullable=True)

            # Virtualização
            is_virtualized      = db.Column(db.Boolean,        nullable=True)
            hypervisor          = db.Column(db.String(50),     nullable=True)

            # JSON bruto (JSONB no PostgreSQL)
            memories            = db.Column(db.JSON,           nullable=True)
            disks               = db.Column(db.JSON,           nullable=True)
            networks            = db.Column(db.JSON,           nullable=True)

            # Sistema operacional e kernel
            # Presentes no payload de VM — ausentes em máquina física (nullable)
            # Requer as colunas abaixo no init.sql da Beatriz:
            #   ALTER TABLE host_discovery ADD COLUMN os_name VARCHAR(200);
            #   ALTER TABLE host_discovery ADD COLUMN os_version VARCHAR(50);
            #   ALTER TABLE host_discovery ADD COLUMN kernel_release VARCHAR(200);
            #   ALTER TABLE host_discovery ADD COLUMN uptime_seconds INTEGER;
            os_name             = db.Column(db.String(200),    nullable=True)
            os_version          = db.Column(db.String(50),     nullable=True)
            kernel_release      = db.Column(db.String(200),    nullable=True)
            uptime_seconds      = db.Column(db.Integer,        nullable=True)

            host = db.relationship('HostModel', back_populates='discovery')

            def to_dict(self):
                """Converte o objeto HostDiscovery para dicionário."""
                return {
                    'host_id':            self.host_id,
                    'discovery_date':     self.discovery_date.isoformat() if self.discovery_date else None,

                    # CPU
                    'cpu_model':          self.cpu_model,
                    'cpu_cores':          self.cpu_cores,
                    'cpu_clock_base_mhz': self.cpu_clock_base_mhz,
                    'cpu_ghz':            float(self.cpu_ghz) if self.cpu_ghz is not None else None,
                    'cpu_max_mhz':        self.cpu_max_mhz,

                    # Memória e disco
                    'total_memory_gb':    float(self.total_memory_gb) if self.total_memory_gb is not None else None,
                    'disk_total_gb':      float(self.disk_total_gb) if self.disk_total_gb is not None else None,

                    # Virtualização
                    'is_virtualized':     self.is_virtualized,
                    'hypervisor':         self.hypervisor,

                    # JSON bruto
                    'memories':           self.memories,
                    'disks':              self.disks,
                    'networks':           self.networks,

                    # Sistema operacional e kernel (VM)
                    'os_name':            self.os_name,
                    'os_version':         self.os_version,
                    'kernel_release':     self.kernel_release,
                    'uptime_seconds':     self.uptime_seconds,
                }

            def para_dict(self):
                return self.to_dict()

        return HostDiscoveryModel