<div align="center">

# Munynn System

### Monitoramento de Sistemas Linux — Projeto Interdisciplinar (PI)

Análise e Desenvolvimento de Sistemas — Universidade Tuiuti do Paraná

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.12-3776AB)
![React](https://img.shields.io/badge/react-19-61DAFB)
![Flask](https://img.shields.io/badge/flask-3.0-000000)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-336791)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)

</div>

---

## Sobre o projeto

O **Munynn System** é uma plataforma de monitoramento de servidores Linux desenvolvida como Projeto Interdisciplinar (PI) do curso de Análise e Desenvolvimento de Sistemas. Um **agente** é instalado em cada máquina monitorada e envia, periodicamente, inventário de hardware, métricas de desempenho e eventos de segurança para um **backend** central, que persiste tudo em PostgreSQL e detecta automaticamente padrões de ataque. Um **painel web** (dashboard) consome essa API para exibir tudo em tempo quase real.

O objetivo acadêmico do projeto é entender, na prática, como funciona um sistema de monitoramento e detecção de intrusão de ponta a ponta:

- **Como métricas e inventário são coletados** — o agente lê `/proc`, `psutil`, `lscpu`, `lsblk`, `dmidecode`, `smartctl`, etc., normaliza tudo em payloads JSON e envia via HTTP para o backend (arquitetura *push*: o agente sempre inicia a conexão, o backend nunca conecta nos agentes).
- **Como ataques de força bruta (brute force SSH) são detectados** — o agente lê `/var/log/auth.log` incrementalmente; o backend faz o parsing de cada linha e, ao encontrar **5 ou mais falhas de login do mesmo IP em 60 segundos**, gera um alerta.
- **Como varreduras de porta (port scan) são detectadas** — o agente captura pacotes TCP `SYN` sem `ACK` via `tcpdump` e mantém uma janela deslizante de 60 segundos por IP de origem; ao atingir **10 portas distintas do mesmo IP**, sinaliza o backend, que cria o alerta.
- **Como alertas de recurso são gerados** — o backend compara CPU, memória e disco contra limiares configuráveis (80% por padrão) a cada métrica recebida.
- **Como tudo isso chega até quem opera o sistema** — alertas podem disparar notificações no Microsoft Teams e por email, além de aparecerem em tempo real no painel web.

A documentação técnica completa de cada módulo (Agente, Backend, Banco de Dados, Frontend e Infraestrutura) está em [`Context/`](Context/) — este README cobre a visão geral e o passo a passo para rodar o projeto.

---

## Arquitetura

```
┌────────────────────┐       HTTP POST (push)        ┌──────────────────────────────────┐
│   Agente (Linux)   │ ─────────────────────────────>│           Nginx :80              │
│binário PyInstaller │       X-API-Key header        │ (roteia por server_name / vhost) │
└────────────────────┘                               └──────────────┬──────────┬────────┘
                                                                    │          │
                                                      api.monitoramento.lan   painel.monitoramento.lan
                                                                    │           │
                                                                    ▼           ▼
                                                          ┌────────────────┐ ┌──────────────────┐
                                                          │ Backend Flask  │ │ Frontend React/  │
                                                          │     :5000      │ │  Vite :5173      │
                                                          └───────┬────────┘ └──────────────────┘
                                                                  │   ▲ HTTP GET (painel web)
                                                                  ▼   │
                                                          ┌────────────────┐
                                                          │  PostgreSQL 15  │
                                                          └────────────────┘
```

| Componente | Tecnologia | Função |
|------------|------------|--------|
| **Agente** | Python 3.12 (binário PyInstaller) | Coleta hardware/SO uma vez (discovery) e métricas/logs/eventos de segurança continuamente (~5s) |
| **Backend** | Python 3.12 + Flask 3 + SQLAlchemy | API REST, persistência, detecção de brute force/port scan/recurso, notificações |
| **Banco de dados** | PostgreSQL 15 | Armazena hosts, agentes, discovery, métricas, logs e alertas (JSONB para dados semi-estruturados) |
| **Frontend** | React 19 + Vite + Tailwind CSS | Painel web (dashboard, métricas, logs, alertas, endpoints, configurações) |
| **Proxy reverso** | Nginx | Roteia por domínio: `api.monitoramento.lan` → backend, `painel.monitoramento.lan` → frontend |

Documentação detalhada de cada peça: [Agent](Context/Agent/Agent-Documentation.md) · [Backend](Context/Backend/Backend-Documentation.md) · [Database](Context/Database/Database-Documentation.md) · [Frontend](Context/Frontend/Frontend-Documentation.md) · [Infra](Context/Infra/)

---

## Como rodar o servidor (backend + banco + painel)

### Pré-requisitos

- Docker e Docker Compose
- Uma máquina (física ou virtual) para hospedar os containers — neste projeto, um Ubuntu Server

### 1. Configurar variáveis de ambiente

Crie o arquivo `Web/BackEnd/.env` (não versionado) com pelo menos:

```ini
# Senha para acessar o painel web e gerar a API key inicial — obrigatória
PANEL_PASSWORD=uma-senha-forte

# Conexão com o Postgres (já vem com este valor por padrão no docker-compose)
DATABASE_URL=postgresql://monitor:monitor@postgres:5432/monitor

# Opcionais — notificações
TEAMS_WEBHOOK_URL=
SMTP_EMAIL=
SMTP_PASSWORD=
ALERT_RECIPIENT=

# Opcional — dias de retenção de métricas/logs (padrão 7)
RETENTION_DAYS=7
```

> O container sobe mesmo sem o `.env` (ele é opcional para o Docker), mas sem `PANEL_PASSWORD` o login do painel retorna 503.

### 2. Subir os containers

```bash
cd Web
docker compose up -d --build
```

Isso inicia 4 containers: `postgres`, `backend`, `frontend` e `nginx` (única porta exposta ao host: **80**). O `postgres` aplica `database/init.sql` na primeira inicialização; o backend espera o banco ficar saudável antes de subir.

### 3. Apontar os domínios para o servidor

O Nginx roteia por **nome de domínio**, não por porta ou path — então `api.monitoramento.lan` e `painel.monitoramento.lan` precisam resolver para o IP do servidor onde os containers estão rodando.

- **Setup completo de laboratório** (DHCP + DNS dedicados, o que este projeto usa de fato): ver [`Context/Infra/`](Context/Infra/) — `isc-dhcp-server` distribuindo IPs e `dnsmasq` resolvendo `api.monitoramento.lan`/`painel.monitoramento.lan` para o servidor.
- **Teste rápido sem infraestrutura de rede própria:** adicione ao `/etc/hosts` (Linux/macOS) ou `C:\Windows\System32\drivers\etc\hosts` (Windows) da sua máquina e de cada VM de agente:

  ```
  <IP-DO-SERVIDOR>  api.monitoramento.lan
  <IP-DO-SERVIDOR>  painel.monitoramento.lan
  ```

### 4. Primeiro acesso ao painel

1. Acesse `http://painel.monitoramento.lan` no navegador.
2. Digite o `PANEL_PASSWORD` configurado no passo 1 — o painel troca a senha por uma API key e a guarda no `localStorage`.
3. Vá em **Configurações → API** e clique em **Gerar nova chave no servidor**. Copie a chave exibida (ela só aparece uma vez).

Essa chave é o que cada agente vai usar para se autenticar (header `X-API-Key`).

---

## Como instalar e usar os agentes

Cada máquina Linux que você quer monitorar precisa rodar o agente. Requisitos da máquina-alvo:

- Linux com `systemd` (testado em Ubuntu 24.04), arquitetura x86_64
- Acesso de rede a `api.monitoramento.lan` (DNS configurado — ver passo 3 acima) e `root` para instalar como serviço
- Para detecção de port scan: `tcpdump` instalado (opcional — sem ele, só essa detecção é desabilitada, o resto funciona normalmente)

### Instalação

```bash
cd Agent/
sudo ./install.sh
```

O script pede a **API key** gerada no painel (passo 4 acima) e o **nível de log** desejado, depois:
- copia o binário (compilando com PyInstaller se necessário) para `/opt/monitor-agent/`
- grava a configuração em `/etc/monitor-agent/env`
- registra e inicia o serviço systemd `linux-agent`

```bash
systemctl status linux-agent       # verificar status
journalctl -u linux-agent -f       # acompanhar logs em tempo real
```

Em poucos segundos o host aparece no Dashboard do painel, com Discovery (hardware) preenchido e métricas chegando a cada ~5 segundos.

Guia completo (atualizar, desinstalar, debug, fila de retry, permissões): [`Agent/Readme.md`](Agent/Readme.md) e [`Context/Agent/Agent-Documentation.md`](Context/Agent/Agent-Documentation.md).

---

## Usando o painel

| Página | O que mostra |
|--------|--------------|
| **Dashboard** | Um card por host monitorado, com atalhos para Detalhes e Métricas |
| **Detalhes** | Inventário completo de hardware/SO coletado pelo agente (CPU, memória, discos, rede, placa-mãe) |
| **Métricas** | Gauges em tempo real (CPU/Memória/Disco/Rede) + histórico em gráfico de linha |
| **Logs** | Eventos de `auth.log` parseados (login SSH, sudo, sessões), agregados ou por host |
| **Alertas** | Brute force, port scan e uso excessivo de recurso, com botão de resolver |
| **Endpoints** | Tabela com todos os hosts, status, busca e contagem de alertas por host |
| **Configurações** | Limiares de alerta, canais de notificação (Teams/Email), destinatários de email e gerenciamento da API key |

Todas as telas (exceto o histórico de métricas) atualizam sozinhas via polling — não é necessário recarregar a página.

---

## Estrutura do repositório

```
.
├── Agent/        # Agente Python (coleta + envio), distribuído como binário PyInstaller
├── Web/
│   ├── BackEnd/  # API Flask + detecção de segurança + notificações
│   ├── FrontEnd/ # Painel React + Vite
│   ├── database/ # Schema PostgreSQL (init.sql)
│   └── docker-compose.yml
├── Context/      # Documentação técnica detalhada de cada módulo
└── abntex/       # Documento acadêmico do PI (ABNT)
```

---

## Equipe

- Beatriz Pimentel de Mello
- Caio Federico Esquivel Lovera Arze
- Denyse Panza Clemente Ferreira
- Douglas Clayton da Silva
- Fernando Bach
- Larissa Quirino dos Santos
- Lucas Toterol Rodrigues

---

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE) para o texto completo.
