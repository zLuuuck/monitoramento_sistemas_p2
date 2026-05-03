import requests  # Biblioteca para fazer requisições HTTP

URL = ""

# Token simples de autenticação (conforme seu projeto)
TOKEN = "seu_token_aqui"


def send_data(data):
    """
    Envia dados para o servidor central via HTTP POST.

    Parâmetros:
        data (dict): payload a ser enviado (discovery ou métricas)

    Cabeçalhos:
        - Content-Type: JSON
        - Authorization: token simples

    Tratamento:
        - Exibe status da resposta
        - Captura erros de conexão
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }

    try:
        response = requests.post(URL, json=data, headers=headers)
        print("Status:", response.status_code)

    except Exception as e:
        print("Erro ao enviar:", e)