from datetime import datetime, timezone


class Host:
    """Wrapper para o modelo Host."""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela host."""

        class HostModel(db.Model):
            __tablename__ = 'host'
            __table_args__ = {'extend_existing': True}

            id = db.Column(db.Integer, primary_key=True)
            hostname = db.Column(db.String(255), nullable=False, unique=True)
            ip_address = db.Column(db.String(45), nullable=True)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            last_seen = db.Column(db.DateTime, nullable=True)

            discovery = db.relationship(
                'HostDiscoveryModel',
                back_populates='host',
                cascade='all, delete-orphan',
                uselist=False,
            )

            metrics = db.relationship(
                'MetricModel', back_populates='host', lazy='dynamic')

            logs = db.relationship(
                'LogEntryModel', back_populates='host', lazy='dynamic')

            def to_dict(self):
                """Converte o objeto Host para dicionario."""
                last_metric_at = self._last_metric_at()
                is_online = self._is_online(last_metric_at)
                return {
                    'id': self.id,
                    'hostname': self.hostname,
                    'ip_address': self.ip_address,
                    'created_at': self.created_at.isoformat() if self.created_at else None,
                    'last_seen': self.last_seen.isoformat() if self.last_seen else None,
                    'last_metric_at': last_metric_at.isoformat() if last_metric_at else None,
                    'status': 'online' if is_online else 'offline',
                    'is_online': is_online
                }

            def _last_metric_at(self):
                latest = self.metrics.order_by(db.text('timestamp DESC')).first()
                return latest.timestamp if latest else None

            def _is_online(self, last_metric_at, timeout_seconds=30):
                if last_metric_at is None:
                    return False
                if last_metric_at.tzinfo is not None:
                    last_metric_at = last_metric_at.astimezone(timezone.utc).replace(tzinfo=None)
                return (datetime.utcnow() - last_metric_at).total_seconds() < timeout_seconds

            def para_dict(self):
                return self.to_dict()

        return HostModel
