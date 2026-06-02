import os
import json
import requests
from datetime import datetime

WEBHOOK_URL = "https://default55c2d0ef74a4438aa61361607a13ee.e0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/bd11bf05f56e42dc8f2cf25a9c36df15/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=cRbsmLFYWZfE89e28RVzDfZ7TnOlRtyYokH0thHJweA"
def enviar_alerta(titulo: str, mensagem: str, severidade: str = "info",
                  origem: str = "app", link: str | None = None) -> None:
    payload = {
        "titulo": titulo,
        "mensagem": mensagem,
        "severidade": severidade,
        "origem": origem,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "link": link or "",
    }
    r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    r.raise_for_status()
    print(f"OK {r.status_code}")

if __name__ == "__main__":
    enviar_alerta(
        titulo="Teste de alerta",
        mensagem="Disparo manual via script Python",
        severidade="warning",
        origem="teste-local",
        link="https://exemplo.local/detalhes",
    )