# app/models/log.py
# Modelo para a tabela 'logs' - eventos de sistema operacional

from datetime import datetime


class LogEntry:
    """Classe wrapper para o modelo LogEntry (tabela logs)"""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela logs"""

        class LogEntryModel(db.Model):
            __tablename__ = 'logs'
            __table_args__ = {'extend_existing': True}

            id = db.Column(db.BigInteger, primary_key=True)

            host_id = db.Column(
                db.Integer,
                db.ForeignKey('host.id'),
                nullable=False
            )

            timestamp = db.Column(
                db.DateTime,
                nullable=False,
                default=datetime.utcnow
            )

            log_type = db.Column(
                db.String(50),
                nullable=True
            )

            raw_line = db.Column(
                db.Text,
                nullable=False
            )

            parsed_data = db.Column(
                db.JSON,
                nullable=True
            )

            # Relacionamento com host
            host = db.relationship(
                'HostModel',
                back_populates='logs'
            )

            def to_dict(self):
                """Converte o objeto LogEntry para dicionário"""
                return {
                    'id': self.id,
                    'host_id': self.host_id,
                    'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                    'log_type': self.log_type,
                    'raw_line': self.raw_line,
                    'parsed_data': self.parsed_data
                }

        return LogEntryModel