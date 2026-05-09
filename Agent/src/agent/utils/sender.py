# =============================================================================
# utils/sender.py
# Envio dos payloads (discovery e métricas) ao backend central via HTTP POST.
# =============================================================================

import requests

# Configurações do servidor — preencher antes de ativar o envio
URL   = ""
TOKEN = "seu_token_aqui"


def send_data(data: dict) -> None:
    """
    Envia um payload ao backend central via HTTP POST com autenticação Bearer.

    Parâmetros:
        data (dict): payload a ser enviado (discovery ou métricas)

    Cabeçalhos enviados:
        Content-Type  : application/json
        Authorization : Bearer <TOKEN>

    Tratamento de erros:
        - Imprime o status HTTP em caso de sucesso
        - Captura e imprime erros de conexão sem travar o agente
    """
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }

    try:
        response = requests.post(URL, json=data, headers=headers, timeout=10)
        print(f"📡 Enviado — status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: servidor inacessível")
    except requests.exceptions.Timeout:
        print("❌ Timeout ao tentar enviar para o servidor")
    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")

# =============================================================================
# FIM utils/sender.py
# =============================================================================