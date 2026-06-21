# Changelog da Documentação (Context/)

Registro da revisão de 21/06/2026: comparação de cada `.md` em `Context/` contra o estado **atual** do código (HEAD em `c5c551c`), por área. Nenhum código foi alterado — apenas os `.md`. Nenhum commit foi feito.

---

## Agent

**Código mudou desde o último commit do doc (`a078475`, 05/06)?** Não — `git diff a078475..HEAD -- Agent/` está vazio.

**Verificação feita:** leitura completa de `sender.py` e `connections.py` (as partes mais detalhadas e arriscadas da doc — URLs, headers, lógica de tcpdump/port scan) confirmou que o código bate exatamente com o que a doc descreve (v6.0).

**Alterado na doc:** nada.

**[VERIFICAR] pendente:** nenhum.

---

## Backend

**O que mudou no código** (`git diff a078475..HEAD -- Web/BackEnd/`):
- `discovery.py`: `GET /api/discovery` agora inclui `agent_id` em cada item retornado (resolvido via `AgentModel.query.filter_by(host_id=...)` em `_discovery_to_response()`).
- `logs.py`: `GET /api/logs` teve `host_id` tornado **opcional** — sem ele, agrega logs de todos os hosts e cada item ganha um campo `hostname` extra (resolvido em lote).

**O que mais foi corrigido na doc** (achados ao verificar o código atual, não vindos do diff — a doc já estava desatualizada nesses pontos antes mesmo dessas duas mudanças):
- Diagrama de arquitetura (seção 1) e linhas da seção 7/12 ainda diziam `Authorization: Bearer {API_KEY}` — o agente só envia `X-API-Key` desde a Fase A (confirmado em `Agent-Documentation.md` e no código do agente). Corrigido em todos os pontos, incluindo a tabela de validações (seção 12).
- O Nginx foi descrito roteando por **prefixo de path** (`/api/*` → backend, `/*` → frontend) — o `nginx.conf` real roteia por **`server_name`** (virtual host: `api.monitoramento.lan` / `painel.monitoramento.lan`). Essa mudança de path-based para vhost-based aconteceu entre os commits `80469df` e `a078475` (antes da doc atual já existir) — ou seja, a doc nunca refletiu o nginx.conf real. Corrigido + cross-referenciado com o novo `Context/Infra/04 - Configuração do Proxy Reverso.md`.
- "API key em sessionStorage" → corrigido para `localStorage` (alinhado com `Frontend-Documentation.md` e o código real de `api.js`).
- Lista de "rotas protegidas" ainda citava `POST /api/connections`, endpoint que foi renomeado para `/api/security/portscan` na v7.0 (já documentado em outra seção da própria doc, mas essa lista específica não tinha sido atualizada).
- `/api/status` na tabela de endpoints dizia `version: "5.0.0"` — o código (`app.py`) retorna `"4.0.0"`. Corrigido.
- "instancia todos os 7 modelos" → o projeto tem 6 modelos (`Host, Agent, HostDiscovery, Metric, LogEntry, Alert`); confirmado em `app/models/__init__.py`. Corrigido.

**Alterado na doc:** `Context/Backend/Backend-Documentation.md` — seções 1, 5, 7.1, 7.3, 8.1, 9, 12, 17, e o rodapé de versão (v8.0.0 → v8.1.0), todos os pontos acima.

**[VERIFICAR] pendente:**
- Cabeçalho do documento diz "Versão do código: 6.0.0", mas o rodapé diz v8.1.0 — são contadores diferentes (versão de doc vs. versão de código) que já estavam dessincronizados antes desta revisão. Não há `VERSION`/`__version__` no código-fonte do backend para confirmar um número de versão real; não alterei o cabeçalho por falta de fonte de verdade.

---

## Database

**O que mudou no código:** nada — `git diff a078475..HEAD -- Web/database/ Web/BackEnd/app/models/` está vazio.

**O que foi corrigido na doc** (a doc já estava desatualizada mesmo sem diff de código — comparando contra o `init.sql` atual, não contra um diff):
- Quatro notas afirmavam que certas colunas/tabelas "não estão no init.sql" e são "adicionadas por `garantir_schema_*()`" no startup. Isso é **falso para o `init.sql` consolidado atual** — ele já declara diretamente:
  - `os_name`, `os_version`, `kernel_release`, `uptime_seconds`, `motherboard` em `host_discovery`
  - as colunas `memory_*_mb`, `disk_*_mb`, `*_iops`, `*_bytes_per_sec` em `metrics`
  - `source_ip VARCHAR(45)` nullable em `alerts` (não `INET NOT NULL`)
  - a tabela `app_settings` inteira
  
  As funções `garantir_schema_*()` ainda existem no backend (confirmado em `app.py`), mas hoje servem só para compatibilidade com volumes antigos pré-consolidação — não para o fluxo normal de um ambiente novo. Corrigido nas 4 notas.

**Alterado na doc:** `Context/Database/Database-Documentation.md` — seções 3.3, 3.4, 3.6, 3.8, e cabeçalho/rodapé de versão (1.1/1.3 → 1.4, sincronizados).

**[VERIFICAR] pendente:** nenhum.

---

## Frontend

**O que mudou no código** (`git diff 403b7a6..HEAD -- Web/FrontEnd/`, mais o que já havia mudado desde `a078475`): reescrita ampla. Resumo do que foi confirmado lendo o código atual (não só o diff, que por si só já passava de 2400 linhas):
- `pages/AppPages.jsx` (arquivo único de ~720 linhas) foi removido e dividido em `DashboardPage`, `DetailsPage` (novo), `MetricsPage`, `LogsPage`, `AlertsPage`, `EndpointsPage`, `SettingsPage`, todos em arquivos próprios sob `src/pages/`.
- `contexts/ThemeContext.jsx` e `shared/components/TopTabs.jsx` foram **removidos do projeto** — não há mais alternância de tema claro/escuro nem indicador físico/virtual no topo do layout.
- Rotas agora usam `:hostId` (obrigatório em `/details/:hostId` e `/metrics/:hostId`; opcional em `/logs[/:hostId]` e `/alerts[/:hostId]`) — `react-router-dom` atualizado de v6 para v7.
- `App.jsx`: métricas agora têm auto-refresh via `setInterval` de 10s (antes só atualizavam ao trocar de host) — isso fecha o gap F-4 da revisão anterior da doc.
- `Sidebar.jsx`: badge de alertas passou a consumir `GET /api/alerts?status=active` de verdade (antes era hardcoded `"3"` — gap F-2, agora corrigido); menu reagrupado, branding "Munynn", minimizável.
- `Icon.jsx`: trocou de biblioteca de SVG inline própria para Font Awesome (`@fortawesome/react-fontawesome`).
- `Card.jsx`: API mudou para `title/value/unit/iconName/color/subtitle/children`.
- Novo componente `GaugeCard.jsx` (dependência nova `react-gauge-component`) usado em `MetricsPage` — porém o gauge de "Rede" usa valor mockado fixo (`25`), não dado real.
- `EndpointsPage.jsx` e `SettingsPage.jsx` foram reescritos por completo (stats, busca, filtro, links por host / thresholds e notificações implementados inline).
- React 18 → 19; React Router v6 → v7 (confirmado em `package.json`).
- Confirmado código morto (arquivos existem mas não são importados em lugar nenhum): `NotificationsCard.jsx`, `ThresholdsCard.jsx`, `EmailRecipientsCard.jsx`, `HostSelector.jsx`, `HeaderInfo.jsx`, `MetricGrid.jsx`, `LogsPlaceholder.jsx`, `EndpointModal.jsx`, `features/alerts/services/alertsApi.js`, `api.postDiscovery()`, `shared/types/index.ts`. A doc anterior descrevia `NotificationsCard`/`ThresholdsCard`/`EmailRecipientsCard` como a implementação real de `SettingsPage` — isso não é mais verdade; `SettingsPage.jsx` reimplementou a mesma lógica inline.
- `index.html` referencia `/src/style.css`, arquivo que não existe (`src/index.css` é o real, importado via `main.jsx`).

**Alterado na doc:** `Context/Frontend/Frontend-Documentation.md` — reescrita quase completa (mantendo a estrutura de seções/TOC original), de v1.4 para v2.0. Seção 11 (Gaps) e 12 (Evolução) expandidas com os achados acima.

**[VERIFICAR] pendente:**
- O container `frontend` no `docker-compose.yml` não tem bind mount do código-fonte (diferente do `backend`), mas o compose define `CHOKIDAR_USEPOLLING`/`WATCHPACK_POLLING` — variáveis que só fazem sentido com um volume montado. Não confirmei se isso é um volume faltante por engano ou uma decisão consciente (talvez o fluxo real seja rebuildar a imagem a cada mudança). Marcado como `[VERIFICAR]` na seção 10 da doc.
- O motivo exato de `SettingsPage.jsx` ter reimplementado a lógica de `NotificationsCard`/`ThresholdsCard`/`EmailRecipientsCard` inline em vez de usá-los está marcado como `(inferido)` na seção 12 — não há comentário no código explicando a decisão.

---

## Infra

**O que mudou no código relevante** (`docker-compose.yml`, `nginx.conf`) desde a base dos docs de Infra (`80469df`, 17/05, mais antiga que a base dos outros docs):
- `nginx.conf`: roteamento mudou de **path-based** (`location /api` → backend, `location /` → frontend, sem `server_name`) para **vhost-based** (`server_name api.monitoramento.lan` → backend, `server_name painel.monitoramento.lan` → frontend, com `resolver 127.0.0.11` para não cachear IP de container morto).
- `docker-compose.yml`: portas `5432`/`5000`/`5173` deixaram de ser expostas no host (hardening); `backend` ganhou `env_file` opcional e `dns: [8.8.8.8, 8.8.4.4]` (para resolver domínios externos do Teams).

**O que foi corrigido/adicionado na doc:**
- `00 - Arquitetura principal.md`: já estava majoritariamente correta (tem até uma seção própria "Planejado vs. Implementado"). Adicionei uma nota explícita sobre o roteamento por `server_name` (que não estava detalhado ali) e referência cruzada para o novo `04`.
- `04 - Configuração do Proxy Reverso.md`: estava **vazio** desde a criação do repositório (nunca foi escrito, diferente de `01`/`02`/`03`, que documentam passo a passo real). Escrevi o conteúdo a partir do `nginx.conf` e `docker-compose.yml` atuais — documenta o **estado final**, não um passo a passo de terminal (porque esse passo a passo nunca existiu/foi registrado).
- `01 - Configuração Inicial de IPs.md`, `02 - Implementação do DHCP.md`, `03 - Implementação do DNS.md`: nenhuma mudança — são registros sequenciais de configuração (estilo "diário de bordo"), e o estado final que eles descrevem (sub-rede `10.10.10.0/26`, DHCP via `isc-dhcp-server`, DNS via `dnsmasq` com os subdomínios `api.`/`painel.monitoramento.lan`) é consistente com o `nginx.conf` atual. Não há nada nesses três arquivos para confirmar ou refutar a partir do código deste repositório (são configuração de host/rede física, fora do versionamento).

**Alterado na doc:** `Context/Infra/00 - Arquitetura principal.md` (nota adicionada) e `Context/Infra/04 - Configuração do Proxy Reverso.md` (conteúdo criado do zero).

**[VERIFICAR] pendente:**
- Não há `server { }` para o domínio "nu" `monitoramento.lan` no `nginx.conf` — uma requisição para esse domínio cairia no primeiro `server` block sem `server_name` correspondente (comportamento padrão do Nginx), que seria o vhost de `api.monitoramento.lan`. Não testei isso na prática; marcado como `[VERIFICAR]` em `04`.

---

## Resumo de arquivos tocados

- `Context/Backend/Backend-Documentation.md`
- `Context/Database/Database-Documentation.md`
- `Context/Frontend/Frontend-Documentation.md`
- `Context/Infra/00 - Arquitetura principal.md`
- `Context/Infra/04 - Configuração do Proxy Reverso.md` (criado)
- `Context/Agent/Agent-Documentation.md` — **não alterado** (verificado, já estava correto)
- `Context/Infra/01 - Configuração Inicial de IPs.md` — não alterado
- `Context/Infra/02 - Implementação do DHCP.md` — não alterado
- `Context/Infra/03 - Implementação do DNS.md` — não alterado

Nenhum arquivo fora de `Context/` foi tocado. Nenhum commit foi feito.
