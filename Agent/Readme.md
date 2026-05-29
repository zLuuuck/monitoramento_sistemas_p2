# Monitor Agent

Agente de monitoramento Linux para o projeto PADS3. Coleta métricas de CPU, memória, disco (com IOPS), rede, top processos, logs de autenticação e conexões TCP, enviando tudo via HTTP para o servidor central.

---

## Requisitos

- Linux Ubuntu 22.04+ (ou qualquer distro com systemd)
- Arquitetura x86_64
- `root` para instalar e rodar como serviço

---

## Instalação rápida

1. Copie o binário `Agent_Exec/dist/agent` para a máquina alvo (ou compile — veja abaixo).
2. Execute o script de instalação:

```bash
sudo ./install.sh
```

O script:
- Copia o binário para `/opt/monitor-agent/agent`
- Cria `/etc/monitor-agent/env` com a URL do servidor e o token
- Cria `/var/log/monitor-agent/` (logs) e `/var/cache/monitor-agent/` (fila de retry)
- Instala e inicia o serviço systemd `linux-agent`

---

## Configurar a URL do servidor

A URL e o token ficam em `/etc/monitor-agent/env`. Edite o arquivo e reinicie:

```bash
sudo nano /etc/monitor-agent/env
```

```ini
MONITOR_API_BASE_URL=http://192.168.1.50:5000
MONITOR_TOKEN=                # deixe vazio se o backend não exige autenticação
MONITOR_LOG_LEVEL=INFO        # DEBUG para logar os JSONs completos de cada payload
```

```bash
sudo systemctl restart linux-agent
```

Para sobrescrever endpoints individuais, adicione as variáveis opcionais:

```ini
MONITOR_DISCOVERY_URL=http://outro-servidor/api/discovery
MONITOR_METRICS_URL=http://outro-servidor/api/metrics
MONITOR_LOGS_URL=http://outro-servidor/api/logs
MONITOR_CONNECTIONS_URL=http://outro-servidor/api/connections
MONITOR_HEARTBEAT_URL=http://outro-servidor/api/heartbeat
```

---

## Verificar status e logs

```bash
# Status do serviço
systemctl status linux-agent

# Logs em tempo real (via journald)
journalctl -u linux-agent -f

# Logs das últimas 100 linhas
journalctl -u linux-agent -n 100

# Arquivo de log rotativo (inclui JSONs completos em nível DEBUG)
tail -f /var/log/monitor-agent/agent.log
```

Para ver os payloads JSON completos que são enviados ao backend, mude o nível de log para DEBUG:

```bash
sudo nano /etc/monitor-agent/env
# Altere: MONITOR_LOG_LEVEL=DEBUG
sudo systemctl restart linux-agent
tail -f /var/log/monitor-agent/agent.log
```

---

## Gerenciar o serviço

```bash
sudo systemctl start linux-agent      # iniciar
sudo systemctl stop linux-agent       # parar
sudo systemctl restart linux-agent    # reiniciar
sudo systemctl enable linux-agent     # habilitar no boot
sudo systemctl disable linux-agent    # desabilitar no boot
```

---

## Atualizar o agente

```bash
# Substituição direta do binário
sudo systemctl stop linux-agent
sudo cp Agent_Exec/dist/agent /opt/monitor-agent/agent
sudo systemctl start linux-agent

# Reinstalação completa (recompila e reconfigura se necessário)
sudo ./install.sh
```

---

## Compilar o binário (opcional)

Se não houver binário pré-compilado, compile na máquina que rodará o agente:

```bash
cd Agent/
python3 -m venv .ambiente_venv
source .ambiente_venv/bin/activate
pip install -e .
pip install pyinstaller

pyinstaller --onefile -n agent \
  --paths src \
  --distpath Agent_Exec/dist \
  --workpath Agent_Exec/build \
  Agent_Exec/main.py
```

O binário final fica em `Agent_Exec/dist/agent`.

---

## Executar sem instalar (desenvolvimento)

```bash
cd Agent/
source .ambiente_venv/bin/activate

# Execução normal
python -m agent

# Ver payloads sem enviar ao backend
python -m agent --debug-exec

# Ver payloads sem enviar (só JSONs, sem logs no terminal)
python -m agent --debug-exec 2>/dev/null

# Forçar instalação de ferramentas ausentes (dmidecode, smartctl...)
sudo python -m agent --install-deps
```

---

## Fila de retry

Quando o backend está inacessível, os payloads são salvos em `/var/cache/monitor-agent/retry_queue.json` e reenviados automaticamente quando a conexão retornar.

Para inspecionar a fila manualmente:

```bash
cat /var/cache/monitor-agent/retry_queue.json | python3 -m json.tool
```

---

## Permissões necessárias

| Recurso | Permissão | Motivo |
|---------|-----------|--------|
| `/var/log/auth.log` | Grupo `adm` ou root | Leitura de logs de autenticação |
| `dmidecode` | root | Detalhes de RAM e placa-mãe |
| `smartctl` | root | Saúde do disco (S.M.A.R.T.) |
| `tcpdump` | root ou `cap_net_raw` | Captura de pacotes SYN para detecção de port scan entrante |

Para leitura de auth.log sem root:
```bash
sudo usermod -a -G adm $USER
# Fazer logout e login para aplicar
```

O serviço systemd roda como root por padrão, então todas as permissões são atendidas automaticamente quando instalado via `install.sh`.

> **Nota sobre tcpdump:** se não estiver instalado na máquina alvo, a detecção de port scan é desabilitada silenciosamente — o restante da coleta funciona normalmente. Para instalar: `sudo apt install tcpdump`.

---

## Desinstalar

```bash
sudo systemctl stop linux-agent
sudo systemctl disable linux-agent
sudo rm /etc/systemd/system/linux-agent.service
sudo rm -rf /opt/monitor-agent
sudo rm -rf /etc/monitor-agent
sudo rm -rf /var/cache/monitor-agent
sudo systemctl daemon-reload
```

---

Para documentação técnica completa (estrutura de payloads, módulos, variáveis de ambiente), consulte [Context/Agent/Agent-Documentation.md](../Context/Agent/Agent-Documentation.md).
