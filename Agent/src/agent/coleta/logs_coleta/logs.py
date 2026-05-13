def get_logs():


    """
    Coleta logs do sistema (arquivo auth.log no Linux).

    Caio, coletar logs também do syslog e dmesg e journalctl, para ter uma visão mais ampla do sistema. Mas cuidado para não coletar logs muito grandes (ex: syslog pode ser gigante). Talvez limitar a última semana ou os últimos 1000 eventos.
    
    Faça ele verificar se o arquivo de log existe e tem permissão de leitura. Se não tiver, retorne uma mensagem de erro clara (ex: "Permissão negada para ler auth.log" ou "Arquivo auth.log não encontrado"). Assim o backend sabe que a coleta de logs falhou por causa de permissão ou ausência do arquivo, e pode agir de acordo (ex: alertar o usuário para rodar o agent com sudo ou verificar a configuração do sistema).
    
    Faça ele identificar se aquele log já foi lido antes, para evitar enviar logs duplicados. Uma forma simples é salvar a posição do último byte lido em um arquivo (ex: logs_position.txt) e, na próxima execução, começar a ler a partir dessa posição. Se o arquivo de log for rotacionado (ex: auth.log.1), ele pode detectar isso comparando o inode do arquivo atual com o inode salvo da última leitura. Se o inode mudou, significa que o arquivo foi rotacionado e ele deve começar a ler do início do novo arquivo.

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