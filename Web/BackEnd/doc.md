# Doc.md — Sistema de Monitoramento de Servidores Linux
# Documentação dos endpoints do backend com exemplos de uso via curl.
# Atualizado na Semana 6: adição do endpoint POST /api/connections.

BASE_URL = http://localhost:5000


---

## Endpoints Gerais

### GET /health
Verifica se o container está de pé.

```bash
curl -X GET http://localhost:5000/health
```

Resposta esperada (200):
```json
{ "status": "ok" }
```

---

### GET /api/status
Retorna status da API com versão e timestamp.

```bash
curl -X GET http://localhost:5000/api/status
```

Resposta esperada (200):
```json
{
  "status": "online",
  "service": "API Monitoramento",
  "version": "4.0.0",
  "timestamp": "2026-05-26T10:00:00.000000"
}
```

---

### GET /api/hosts
Lista todos os hosts cadastrados.

```bash
curl -X GET http://localhost:5000/api/hosts
```

Com dados de hardware:
```bash
curl -X GET "http://localhost:5000/api/hosts?include_discovery=true"
```

---

## Semana 1 — Discovery

### POST /api/discovery
Recebe dados de identificação e hardware do host.

```bash
curl -X POST http://localhost:5000/api/discovery \
  -H "Content-Type: application/json" \
  -d '{
    "global": {
      "collection_type": "discovery",
      "host_id": "71203",
      "hostname": "teste-ubuntu",
      "primary_ip": "192.168.48.129"
    },
    "timestamp": "2026-05-26T10:00:00+00:00",
    "os": {
      "name": "Ubuntu",
      "version": "22.04",
      "kernel_release": "5.15.0-91-generic"
    },
    "cpu": {
      "model": "Intel Core i5",
      "cores": 4,
      "threads": 8,
      "frequency_mhz": 2400
    },
    "memory": {
      "total_mb": 8192
    },
    "disk": {
      "total_mb": 102400
    },
    "uptime_seconds": 3600
  }'
```

### GET /api/discovery
Lista todos os registros de discovery.

```bash
curl -X GET http://localhost:5000/api/discovery
```

---

## Semana 2 — Métricas

### POST /api/metrics
Recebe métricas de CPU, memória e disco coletadas pelo agente.

```bash
curl -X POST http://localhost:5000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "global": {
      "collection_type": "metrics",
      "host_id": "71203",
      "hostname": "teste-ubuntu",
      "primary_ip": "192.168.48.129"
    },
    "timestamp": "2026-05-26T10:00:00+00:00",
    "cpu_percent": 45.2,
    "memory_used_mb": 4096,
    "memory_free_mb": 4096,
    "memory_total_mb": 8192,
    "disk_used_mb": 51200,
    "disk_free_mb": 51200,
    "disk_total_mb": 102400
  }'
```

### GET /api/metrics
Lista métricas armazenadas. Suporta filtro por host.

```bash
curl -X GET http://localhost:5000/api/metrics

curl -X GET "http://localhost:5000/api/metrics?host_id=71203"
```

---

## Semanas 3/4 — Logs

### POST /api/logs
Recebe entradas de log do sistema (suporte a parsing SSH).

```bash
curl -X POST http://localhost:5000/api/logs \
  -H "Content-Type: application/json" \
  -d '{
    "global": {
      "collection_type": "logs",
      "host_id": "71203",
      "hostname": "teste-ubuntu",
      "primary_ip": "192.168.48.129"
    },
    "timestamp": "2026-05-26T10:00:00+00:00",
    "logs": [
      {
        "timestamp": "2026-05-26T10:00:00+00:00",
        "level": "WARNING",
        "service": "sshd",
        "message": "Failed password for root from 192.168.1.50 port 54321 ssh2"
      }
    ]
  }'
```

### GET /api/logs
Lista logs armazenados.

```bash
curl -X GET http://localhost:5000/api/logs

curl -X GET "http://localhost:5000/api/logs?host_id=71203&level=WARNING"
```

---

## Semana 5 — Alertas

### GET /api/alerts
Lista todos os alertas. Suporta filtro por host e por tipo.

```bash
curl -X GET http://localhost:5000/api/alerts

curl -X GET "http://localhost:5000/api/alerts?host_id=71203"

curl -X GET "http://localhost:5000/api/alerts?resolved=false"
```

### PATCH /api/alerts/<id>/resolve
Marca um alerta como resolvido.

```bash
curl -X PATCH http://localhost:5000/api/alerts/1/resolve
```

Resposta esperada (200):
```json
{
  "mensagem": "Alerta 1 marcado como resolvido",
  "alerta_id": 1
}
```

---

## Semana 6 — Conexões TCP

### POST /api/connections
Recebe conexões TCP ativas coletadas pelo agente.
Se `port_scan_detected=true`, o backend cria automaticamente um alerta de severidade alta.

```bash
curl -X POST http://localhost:5000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "global": {
      "collection_type": "connections",
      "host_id": "71203",
      "hostname": "teste-ubuntu",
      "primary_ip": "192.168.48.129"
    },
    "timestamp": "2026-05-26T10:00:00+00:00",
    "connections": [
      {
        "local_port": 22,
        "remote_ip": "192.168.1.100",
        "remote_port": 54321,
        "state": "ESTABLISHED"
      },
      {
        "local_port": 80,
        "remote_ip": "10.0.0.5",
        "remote_port": 61234,
        "state": "TIME_WAIT"
      }
    ],
    "total": 2,
    "port_scan_detected": false,
    "syn_sent_count": 0
  }'
```

Resposta esperada (201):
```json
{
  "mensagem": "Conexões recebidas com sucesso",
  "host_id": 71203,
  "total_salvo": 2,
  "syn_sent_count": 0,
  "port_scan_flag": false,
  "alerta_criado": false
}
```

**Simulando detecção de port scan** (agente envia flag=true):

```bash
curl -X POST http://localhost:5000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "global": {
      "collection_type": "connections",
      "host_id": "71203",
      "hostname": "teste-ubuntu",
      "primary_ip": "192.168.48.129"
    },
    "timestamp": "2026-05-26T10:05:00+00:00",
    "connections": [
      {
        "local_port": 22,
        "remote_ip": "192.168.1.200",
        "remote_port": 44444,
        "state": "SYN_SENT"
      }
    ],
    "total": 1,
    "port_scan_detected": true,
    "syn_sent_count": 15
  }'
```

Resposta esperada (201):
```json
{
  "mensagem": "Conexões recebidas com sucesso",
  "host_id": 71203,
  "total_salvo": 1,
  "syn_sent_count": 15,
  "port_scan_flag": true,
  "alerta_criado": true
}
```

---

## Mapeamento de campos — POST /api/connections

| Campo no payload do agente | Campo na tabela `active_connections` | Observação                        |
|---------------------------|--------------------------------------|-----------------------------------|
| `connections[].local_port`  | `dst_port`                           | Porta do serviço no host          |
| `connections[].remote_ip`   | `src_ip`                             | IP remoto que iniciou a conexão   |
| `connections[].remote_port` | `src_port`                           | Porta efêmera do lado remoto      |
| `connections[].state`       | `status`                             | Estado TCP (ESTABLISHED, etc.)    |
| *(fixo)*                    | `protocol`                           | Sempre `"tcp"` nesta versão       |
| `global.primary_ip`         | `dst_ip`                             | IP do próprio host monitorado     |
| `global.host_id`            | `host_id`                            | FK para a tabela `host`           |
| `timestamp`                 | `timestamp`                          | Timestamp da coleta               |