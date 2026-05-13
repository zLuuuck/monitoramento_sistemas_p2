from datetime import datetime


class Agent:
    """Wrapper para o modelo Agent."""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela agents."""

        class AgentModel(db.Model):
            __tablename__ = 'agents'
            __table_args__ = {'extend_existing': True}

            id = db.Column(db.Integer, primary_key=True)
            host_id = db.Column(
                db.Integer,
                db.ForeignKey('host.id'),
                nullable=False,
                unique=True,
            )
            agent_version = db.Column(db.String(20), nullable=True)
            last_checkin = db.Column(db.DateTime, default=datetime.utcnow)
            status = db.Column(db.String(20), default='active')

            def to_dict(self):
                return {
                    'id': self.id,
                    'host_id': self.host_id,
                    'agent_version': self.agent_version,
                    'last_checkin': self.last_checkin.isoformat() if self.last_checkin else None,
                    'status': self.status,
                }

            def para_dict(self):
                return self.to_dict()

        return AgentModel
