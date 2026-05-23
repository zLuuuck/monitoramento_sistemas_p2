# app/models/connection.py
# Modelo que representa uma conexão TCP ativa capturada pelo agente coletor.
# Semana 6: primeira implementação — tabela já existe no banco (não usar db.create_all()).


class ActiveConnection:
    """Wrapper para o modelo ActiveConnection, seguindo o padrão get_model(db) do projeto."""

    @staticmethod
    def get_model(db):
        """Retorna o modelo SQLAlchemy para a tabela active_connections."""

        class ActiveConnectionModel(db.Model):
            __tablename__ = 'active_connections'
            __table_args__ = {'extend_existing': True}

            # Chave primária — BIGSERIAL gerado pelo banco
            id = db.Column(db.BigInteger, primary_key=True)

            # Host de onde a conexão foi coletada
            host_id = db.Column(
                db.Integer,
                db.ForeignKey('host.id'),
                nullable=False,
            )

            # Momento da coleta (com fuso horário, igual ao banco TIMESTAMPTZ)
            timestamp = db.Column(db.DateTime(timezone=True), nullable=False)

            # IP de origem da conexão (quem iniciou — lado remoto)
            src_ip = db.Column(db.String(45), nullable=False)

            # Porta de origem (lado remoto)
            src_port = db.Column(db.Integer, nullable=False)

            # IP de destino (o próprio host monitorado)
            dst_ip = db.Column(db.String(45), nullable=False)

            # Porta de destino (serviço no host monitorado, ex: 22 para SSH)
            dst_port = db.Column(db.Integer, nullable=False)

            # Protocolo — sempre "tcp" nesta versão do agente
            protocol = db.Column(db.String(10), nullable=False, default='tcp')

            # Estado da conexão (ex: ESTABLISHED, TIME_WAIT, LISTEN)
            status = db.Column(db.String(20), nullable=False)

            # Duração em segundos — opcional, agente pode não informar
            duration_sec = db.Column(db.Integer, nullable=True)

            def to_dict(self):
                """Converte o objeto para dicionário serializável em JSON."""
                return {
                    'id':           self.id,
                    'host_id':      self.host_id,
                    'timestamp':    self.timestamp.isoformat() if self.timestamp else None,
                    'src_ip':       self.src_ip,
                    'src_port':     self.src_port,
                    'dst_ip':       self.dst_ip,
                    'dst_port':     self.dst_port,
                    'protocol':     self.protocol,
                    'status':       self.status,
                    'duration_sec': self.duration_sec,
                }

        return ActiveConnectionModel