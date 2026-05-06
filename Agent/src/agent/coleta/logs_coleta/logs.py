def get_logs():
    """
    Coleta logs do sistema (arquivo auth.log no Linux).

    Esse arquivo contém eventos importantes como:
    - tentativas de login
    - falhas de autenticação (ex: brute force)

    Estratégia:
    - lê o arquivo
    - retorna apenas as últimas 10 linhas (para evitar payload muito grande)

    OBS:
    - Pode precisar rodar como sudo
    """

    try:
        with open("/var/log/auth.log", "r") as file:
            lines = file.readlines()[-10:]  # pega as últimas 10 linhas
            return lines

    except Exception as e:
        # Caso não consiga acessar o arquivo (permissão ou inexistente)
        return [f"Erro ao ler logs: {str(e)}"]