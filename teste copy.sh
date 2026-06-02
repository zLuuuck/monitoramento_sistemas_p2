curl -s -X POST "https://default55c2d0ef74a4438aa61361607a13ee.e0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/bd11bf05f56e42dc8f2cf25a9c36df15/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=cRbsmLFYWZfE89e28RVzDfZ7TnOlRtyYokH0thHJweA" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Port Scan detectado — Host 1",
    "mensagem": "Varredura de portas: 1000 portas distintas em 60s de 10.10.10.26",
    "severidade": "CRITICAL",
    "icone": "🔴",
    "origem": "host-1",
    "timestamp": "02/06/2026 16:30:00",
    "link": ""
  }'