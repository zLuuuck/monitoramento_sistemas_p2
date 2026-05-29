# app/models/alert.py
# Modelo para a tabela 'alerts' — alertas de segurança gerados automaticamente
# Semana 5: brute force SSH é o primeiro tipo de alerta implementado

from datetime import datetime


class Alert:
    """Wrapper para o modelo Alert, seguindo o padrão get_model(db) do projeto."""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela alerts."""

        class AlertModel(db.Model):
            __tablename__ = 'alerts'
            __table_args__ = {'extend_existing': True}

            # Chave primária — BIGSERIAL no banco (gerado pelo init.sql da Beatriz)
            id = db.Column(db.BigInteger, primary_key=True)

            # Host que sofreu o ataque
            host_id = db.Column(
                db.Integer,
                db.ForeignKey('host.id'),
                nullable=False,
            )

            # Tipo do alerta — "brute_force" ou "port_scan"
            alert_type = db.Column(db.String(50), nullable=False)

            # IP de origem do ataque
            source_ip = db.Column(db.String(45), nullable=False)

            # Momento em que o alerta foi gerado
            timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

            # Severidade — "low", "medium", "high", "critical"
            severity = db.Column(db.String(20), default='medium', nullable=False)

            # Campo herdado do schema da Beatriz (método de ataque, ex: "password")
            metodos = db.Column(db.String(20), nullable=True)

            # Descrição legível do alerta (ex: "45 portas varridas em 60s de 10.0.0.5")
            message = db.Column(db.Text, nullable=True)

            # Campos adicionados na Semana 5 para controle de resolução
            # ATENÇÃO: estas colunas precisam existir no banco.
            # Se o banco foi criado com o init.sql original (sem elas), rodar:
            #   ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT FALSE;
            #   ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;
            resolved = db.Column(db.Boolean, default=False, nullable=False)
            resolved_at = db.Column(db.DateTime, nullable=True)

            # Relacionamento com host (sem back_populates para não exigir
            # alteração no host.py nesta semana)
            host = db.relationship('HostModel', foreign_keys=[host_id])

            def to_dict(self):
                """Converte o objeto Alert para dicionário."""
                return {
                    'id':          self.id,
                    'host_id':     self.host_id,
                    'alert_type':  self.alert_type,
                    'source_ip':   self.source_ip,
                    'timestamp':   self.timestamp.isoformat() if self.timestamp else None,
                    'severity':    self.severity,
                    'metodos':     self.metodos,
                    'message':     self.message,
                    'resolved':    self.resolved,
                    'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
                }

            def para_dict(self):
                return self.to_dict()

        return AlertModel