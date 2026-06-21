# Frontend — Documentação Técnica

**Versão 2.0 | Junho 2026**

| Campo          | Valor                                                       |
|----------------|-------------------------------------------------------------|
| Projeto        | Monitoramento de Sistemas P2                                |
| Módulo         | Frontend — Dashboard React SPA ("Munynn System")             |
| Framework      | React 19 + Vite (Tailwind CSS v4 via `@tailwindcss/vite`)   |
| Gráficos       | Chart.js via `react-chartjs-2` + `react-gauge-component`   |
| Ícones         | Font Awesome (`@fortawesome/react-fontawesome`)             |
| Ambiente       | Docker Container (Node.js, servidor de desenvolvimento Vite)|
| Equipe         | Lucas Toterol Rodrigues & Caio Federico Esquivel Lovera Arze |

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Roteamento](#3-roteamento)
4. [Arquitetura de Estado](#4-arquitetura-de-estado)
5. [Componentes](#5-componentes)
6. [Serviço de API](#6-serviço-de-api)
7. [Autenticação no Frontend](#7-autenticação-no-frontend)
8. [Páginas](#8-páginas)
9. [Auto-refresh e Intervalos](#9-auto-refresh-e-intervalos)
10. [Variáveis de Ambiente](#10-variáveis-de-ambiente)
11. [Gaps Conhecidos](#11-gaps-conhecidos)
12. [Evolução do Projeto](#12-evolução-do-projeto)

---

## 1. Visão Geral

O frontend é uma **Single Page Application (SPA)** construída com React 19 e Vite, com tema visual fixo escuro ("Tema Corvo" / marca "Munynn"). Funciona como dashboard de monitoramento em tempo quase real — dados são atualizados automaticamente via polling periódico à API.

**Fluxo principal:**
1. Ao carregar, `App.jsx` busca a lista de hosts com seus dados de discovery (`api.getDiscovery()`)
2. Se a API retornar 401 (sem API key), exibe o `LoginModal`
3. Usuário digita a senha do painel → backend valida e retorna a API key
4. `saveApiKey()` grava a chave no `localStorage` e `reloadKey` é incrementado, disparando novo fetch
5. **Dashboard** (`/dashboard`) mostra um card por host com atalhos para Detalhes e Métricas
6. **Detalhes** (`/details/:hostId`) mostra o inventário de hardware/SO (`DiscoveryDashboard`)
7. **Métricas** (`/metrics/:hostId`) mostra gauges em tempo real + gráfico histórico (`MetricsChart`)
8. **Logs** (`/logs` ou `/logs/:hostId`) e **Alertas** (`/alerts` ou `/alerts/:hostId`) funcionam tanto numa visão agregada (todos os hosts) quanto filtrados por host, dependendo de haver `:hostId` na rota
9. Métricas, logs e contagem de alertas atualizam automaticamente via `setInterval` — não há mais necessidade de trocar de host para ver dados novos (ver seção 11, gap F-4 do histórico — **corrigido**)

O frontend **nunca empurra dados** — apenas consome os endpoints GET (e PATCH/POST de configuração) da API.

---

## 2. Estrutura de Diretórios

```
Web/FrontEnd/
├── Dockerfile                               ← node:24, `npm install` + `npm run dev` (servidor Vite)
├── package.json
├── vite.config.js                           ← proxy /api → backend:5000, HMR via Nginx (clientPort 80)
├── index.html                               ← título "Munynn Systetm Dashboard" [sic]
├── public/
│   ├── logo-Munynn.jpeg / logo-Munynn.svg   ← logo usado na Sidebar e no favicon
│   ├── favicon.svg
│   └── icons.svg                            ← presente mas não referenciado no código (não usado)
└── src/
    ├── main.jsx                             ← ponto de entrada React (RouterProvider, sem ThemeProvider)
    ├── App.jsx                              ← componente raiz + estado global + LoginModal
    ├── routes.jsx                           ← definição das rotas (react-router-dom v7)
    ├── App.css
    ├── index.css                            ← tema fixo ("Tema Corvo"): variáveis CSS, sem alternância claro/escuro
    ├── shared/
    │   ├── components/
    │   │   ├── Layout.jsx                   ← wrapper com Sidebar + <main> (TopTabs foi removido)
    │   │   ├── Sidebar.jsx                  ← menu lateral com grupos, badge de alertas real, minimizável
    │   │   ├── Card.jsx                     ← card de métrica reutilizável (title/value/unit/icon/color/subtitle)
    │   │   └── Icon.jsx                     ← wrapper de ícones Font Awesome (antes era SVG inline)
    │   ├── services/
    │   │   └── api.js                       ← cliente HTTP centralizado + auth helpers
    │   └── types/
    │       └── index.ts                     ← interfaces TypeScript (Host/Metric/LogEntry/Alert) — não usadas
    │                                            em lugar nenhum do código; projeto é JS puro, sem tsconfig
    ├── pages/
    │   ├── index.js                         ← reexporta todas as páginas
    │   ├── DashboardPage.jsx                ← grid de cards, um por host
    │   ├── DetailsPage.jsx                  ← inventário de hardware do host (`/details/:hostId`)
    │   ├── MetricsPage.jsx                  ← gauges + gráfico histórico (`/metrics/:hostId`)
    │   ├── LogsPage.jsx                     ← wrapper fino sobre LogsPanel
    │   ├── AlertsPage.jsx                   ← wrapper sobre AlertsPanel, resolve nome do host pela rota
    │   ├── EndpointsPage.jsx                ← tabela de hosts com filtros, busca e contagem de alertas
    │   └── SettingsPage.jsx                 ← thresholds, notificações e destinatários de email **inline**
    │                                            (ver gap F-6 — não usa mais os cards dedicados abaixo)
    ├── components/
    │   ├── DiscoveryDashboard.jsx           ← painel de hardware (export `DiscoveryDashboard` + `MetricCards`)
    │   ├── GaugeCard.jsx                    ← gauge semicircular (react-gauge-component) — usado em MetricsPage
    │   ├── ApiKeyCard.jsx                   ← único card "novo" de Settings que está de fato em uso
    │   ├── NotificationsCard.jsx            ← ⚠️ não importado em lugar nenhum (código morto)
    │   ├── ThresholdsCard.jsx               ← ⚠️ não importado em lugar nenhum (código morto)
    │   ├── EmailRecipientsCard.jsx          ← ⚠️ não importado em lugar nenhum (código morto)
    │   ├── HostSelector.jsx                 ← ⚠️ não importado em lugar nenhum (código morto)
    │   ├── HeaderInfo.jsx                   ← ⚠️ não importado em lugar nenhum (código morto)
    │   └── MetricGrid.jsx                   ← ⚠️ exporta `MetricsGrid`, não importado em lugar nenhum (código morto)
    ├── features/
    │   ├── metrics/components/
    │   │   └── MetricsChart.jsx             ← gráfico de linha Chart.js
    │   ├── logs_feat/components/
    │   │   ├── LogsPanel.jsx                ← painel de logs; aceita `hostId` opcional (agregado ou por host)
    │   │   └── LogsPlaceholder.jsx          ← ⚠️ não importado em lugar nenhum (código morto)
    │   └── alerts/
    │       ├── components/
    │       │   └── AlertsPanel.jsx          ← painel de alertas; aceita `hostId`/`hostNames` opcionais
    │       └── services/
    │           └── alertsApi.js             ← ⚠️ não importado em lugar nenhum — `AlertsPanel` usa `api.js` direto
    └── modals/
        └── EndpointModal.jsx                ← ⚠️ não importado em lugar nenhum (código morto)
```

> **Removidos desde a revisão anterior desta doc:** `contexts/ThemeContext.jsx` (tema claro/escuro alternável), `shared/components/TopTabs.jsx` (badge físico/virtual no topo) e `pages/AppPages.jsx` (arquivo monolítico de ~720 linhas — substituído pelos arquivos individuais em `pages/`).

---

## 3. Roteamento

Definido em `routes.jsx` usando `react-router-dom` **v7** (`createBrowserRouter`). Várias rotas agora aceitam `:hostId` opcional — quando ausente, a página exibe dados agregados de todos os hosts (alinhado com o backend, que tornou `host_id` opcional em `GET /api/logs` e já aceitava `host_id` opcional em `GET /api/alerts`).

```
/                       → App.jsx (layout wrapper com Outlet)
├── /                   → redirect para /dashboard
├── /dashboard          → DashboardPage              (grid de hosts)
├── /details/:hostId    → DetailsPage                (hardware do host — sem hostId não existe rota)
├── /metrics/:hostId    → MetricsPage                (gauges + histórico — sem hostId não existe rota)
├── /logs               → LogsPage                   (logs de todos os hosts)
├── /logs/:hostId       → LogsPage                   (logs de um host)
├── /alerts             → AlertsPage                 (alertas de todos os hosts)
├── /alerts/:hostId     → AlertsPage                 (alertas de um host)
├── /endpoints          → EndpointsPage
└── /settings           → SettingsPage
```

> **Nota:** não existem mais rotas estáticas `/metrics` ou `/details` sem `:hostId` — o acesso é sempre feito a partir de um link com o ID do host (cards do Dashboard, tabela de Endpoints, etc.). `App.jsx` lê `:hostId` via `useParams()` e combina com o estado interno `selectedHost` (ver seção 4).

---

## 4. Arquitetura de Estado

### Estado Global (App.jsx)

`App.jsx` não usa mais Context — ele mantém o estado e o repassa para as páginas via `<Outlet context={{ ... }} />`, consumido com `useOutletContext()` em cada página.

| Estado            | Tipo    | Descrição                                                              |
|-------------------|---------|--------------------------------------------------------------------------|
| `selectedHost`    | string  | Fallback interno de host selecionado (primeiro host retornado por discovery) |
| `discovery`       | array   | Lista de todos os hosts com dados de discovery (renomeado de `discoveries`) |
| `discoveryLoading`| boolean | Loading da busca de discovery (renomeado de `loading`)                  |
| `discoveryError`  | string  | Erro da busca de discovery (renomeado de `error`)                       |
| `metrics`         | array   | Últimas métricas do host efetivo, normalizadas (`normalizeMetrics()`)   |
| `loading`         | boolean | Loading da busca de métricas (antes era `metricsLoading`)               |
| `metricsError`    | string  | Erro da busca de métricas                                               |
| `authRequired`    | boolean | `true` quando a API retorna 401 — exibe o `LoginModal`                  |
| `reloadKey`       | number  | Incrementado após login bem-sucedido para forçar re-fetch               |

**`effectiveHost`** — `routeHostId || selectedHost`, onde `routeHostId` vem de `useParams()`. O host da URL (`/metrics/:hostId`, `/details/:hostId`) tem prioridade sobre o fallback interno; sem essa regra, todo card de host abriria os dados do mesmo host selecionado globalmente.

**Effects em App.jsx:**
- `useEffect([carregarDiscovery, reloadKey])` — busca `getDiscovery()` no mount e após login
- `useEffect([effectiveHost, reloadKey])` — busca `getMetrics(effectiveHost)` imediatamente **e a cada 10 segundos via `setInterval`** (gap F-4 da revisão anterior — **corrigido**: métricas agora atualizam sozinhas, não só ao trocar de host)

**`normalizeMetrics(metrics)`** — filtra métricas sem `timestamp` e força `cpu_percent`/`memory_percent`/`disk_percent` para `Number(...) || null`.

### Estado Local (componentes que gerenciam seus próprios dados)

| Componente   | Estado local                                                        | Auto-refresh |
|--------------|-----------------------------------------------------------------------|--------------|
| LogsPanel    | `logs, total, loading, error, view, statusFilter, lastUpdated`        | 10 segundos  |
| AlertsPanel  | `alerts, loading, error`                                               | 15 segundos  |
| Sidebar      | `isMinimized` (persistido em `localStorage.sidebarMinimized`), `alertCount` (polling 30s) | 30 segundos (alertCount) |
| EndpointsPage| `alertCounts, search, statusFilter`                                    | 30 segundos (alertCounts) |
| SettingsPage | `thresholds, notifications, recipients, newEmail, saving, message`     | — (sem polling, carrega uma vez no mount) |

---

## 5. Componentes

### 5.1 App (raiz)

**Arquivo:** `src/App.jsx`

Componente raiz que gerencia estado global, faz chamadas de API e renderiza o `Layout`. Não usa mais React Context — distribui dados via `<Outlet context={{...}} />`.

#### LoginModal

Componente interno de `App.jsx`, inalterado em relação à revisão anterior: aparece quando `authRequired === true`, bloqueia a interface e exige a senha do painel.

**Fluxo:** `loginWithPassword(password)` → `saveApiKey(api_key)` → `onSuccess()` → `setAuthRequired(false)` + `setReloadKey(k => k + 1)`.

---

### 5.2 Layout

**Arquivo:** `src/shared/components/Layout.jsx`

Wrapper visual simplificado — **não inclui mais `TopTabs`** (componente removido do projeto):

```
┌──────────┬──────────────────────────────────┐
│          │                                  │
│ Sidebar  │  {children} (página atual)        │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

Calcula `activeTab` a partir de `useLocation().pathname` e passa para a `Sidebar`. Recebe uma prop `hostType` (vinda de `App.jsx`, `'virtual'` ou `'physical'`), mas **não a utiliza em nenhum lugar do JSX** — prop morta, resquício do antigo badge `TopTabs`.

> **Gap F-1 da revisão anterior:** estava relacionado à falta de `activeSubTab`/`onSubTabChange` no `TopTabs.jsx`. Como `TopTabs.jsx` foi removido do projeto, o gap deixou de existir (não por correção, e sim por remoção do componente problemático).

---

### 5.3 Sidebar

**Arquivo:** `src/shared/components/Sidebar.jsx`

Reescrita completa: menu agrupado em três seções (`Principal`, `Monitoramento`, `Sistema`), com identidade visual "Munynn" (logo, glow roxo, animação de radar em SVG) e botão de minimizar/expandir (estado persistido em `localStorage.sidebarMinimized`).

```js
MENU_GROUPS = [
  { label: 'Principal',      items: [Dashboard (/dashboard), Logs Gerais (/logs)] },
  { label: 'Monitoramento',  items: [Alertas Gerais (/alerts), Endpoints (/endpoints)] },
  { label: 'Sistema',        items: [Configurações (/settings)] },
]
```

**Badge de alertas:** busca `api.getAlerts('active')` no mount e a cada **30 segundos**, exibindo a contagem real ao lado do item "Alertas Gerais".

> **Gap F-2 da revisão anterior (badge hardcoded como `"3"`) — corrigido.** O badge agora reflete `GET /api/alerts?status=active` em tempo real.

---

### 5.4 ~~TopTabs~~ — REMOVIDO

O arquivo `src/shared/components/TopTabs.jsx` não existe mais no projeto. O indicador físico/virtual no topo da página foi removido; essa informação ainda existe nos dados (`discovery.is_virtualized`) e é exibida como badge dentro de `DiscoveryDashboard` (seção 5.5), mas não há mais um indicador fixo no topo do layout.

---

### 5.5 DiscoveryDashboard

**Arquivo:** `src/components/DiscoveryDashboard.jsx`

Exporta dois componentes:
- **`DiscoveryDashboard({ discovery })`** — painel completo de hardware/SO/CPU/memória/disco/rede/placa-mãe de um host. Usado em `DetailsPage`.
- **`MetricCards({ latestMetric })`** — quatro `Card` com CPU/Memória/Disco/Rede (valores percentuais + bytes de rede). Usado em `MetricsPage` e `DetailsPage`.

Detalhes de hardware específicos de máquina física (`MemoryDetails`, `MotherboardDetails`) só são renderizados quando `!discovery.is_virtualized`.

---

### 5.6 MetricsChart

**Arquivo:** `src/features/metrics/components/MetricsChart.jsx`

Gráfico de linha com Chart.js (`updateMode="none"`, sem animação). Sem mudanças funcionais desde a revisão anterior — apenas o fundo do card passou para o tema escuro (`bg-[#1A1A2E]`).

---

### 5.7 GaugeCard — NOVO

**Arquivo:** `src/components/GaugeCard.jsx`

Gauge semicircular via `react-gauge-component` (dependência nova). Recebe `title, value, unit, icon` e calcula a própria cor (verde ≤60%, laranja 61–80%, vermelho >80%) e rótulo textual (`Normal`/`Atenção`/`Instável`) a partir do `value`. A prop `color` passada por `MetricsPage` **não é usada** pelo componente (ele ignora esse parâmetro e decide a cor sozinho).

Usado em `MetricsPage` para CPU, Memória, Disco e Rede.

> **Gap novo (F-7):** o gauge de "Rede" em `MetricsPage` recebe um valor **fixo (`25`)**, não calculado a partir de métricas reais — não há campo de "% de utilização de rede" no payload de métricas (o agente envia bytes/sec, não percentual). O gauge de "Disco" também tem fallback mockado (`35`) quando `disk_percent` e `disk_io` estão ambos ausentes.

---

### 5.8 LogsPanel

**Arquivo:** `src/features/logs_feat/components/LogsPanel.jsx`

Recebe `hostId` opcional (`undefined` na rota `/logs`, definido na rota `/logs/:hostId`):
- **Com `hostId`:** título "Logs de Autenticação", chama `api.getLogs(hostId, ...)`
- **Sem `hostId`:** título "Logs Gerais — Todos os Hosts", chama `api.getLogs(undefined, ...)` → backend retorna logs de todos os hosts com campo `hostname` por linha; a tabela/raw view ganha uma coluna/prefixo extra de host (`showHost={!hostId}`)

Dois modos de visualização — **Estruturado** (tabela com timestamp, host quando agregado, status, usuário, IP) e **Raw** (terminal monospace colorizado). Filtros: Todos / Falha / Aceito / Outros (corresponde a `unparsed` no código).

Auto-refresh: **10 segundos**.

---

### 5.9 AlertsPanel

**Arquivo:** `src/features/alerts/components/AlertsPanel.jsx` (export default, não nomeado)

Recebe `hostId` e `hostNames` opcionais. Chama `api.getAlerts('active', hostId)` — **não usa mais `alertsApi.js`**, que ficou como código morto (ver seção 2). Quando `hostNames` é fornecido (visão agregada, sem `hostId`), cada alerta exibe um badge com o nome do host de origem.

Botão "Resolver" chama `api.resolveAlert(id)` e remove o alerta da lista local imediatamente.

Auto-refresh: **15 segundos**.

---

### 5.10 EndpointsPage

**Arquivo:** `src/pages/EndpointsPage.jsx` (arquivo próprio — não mais parte de `AppPages.jsx`)

Reescrita completa em relação à revisão anterior. Agora inclui:
- 4 cards de resumo (Total, Online, Com Alerta, Offline) calculados a partir de `discovery` + contagem de alertas ativos por host
- Campo de busca (hostname, IP, agent ID ou host ID) e filtro por status (`all/online/alert/offline`)
- Tabela com colunas Host (+ SO/status), IP Primário, Agent ID, Host ID e Ações
- Ações por linha: links para `/details/:hostId`, `/metrics/:hostId`, `/logs/:hostId` e `/alerts/:hostId` (este último com badge de contagem de alertas do host)

Contagem de alertas por host vem de `api.getAlerts('active', null, 100)`, repetida a cada **30 segundos**.

---

### 5.11 SettingsPage

**Arquivo:** `src/pages/SettingsPage.jsx` (arquivo próprio — não mais parte de `AppPages.jsx`)

> **Mudança importante:** ao contrário do que a revisão anterior desta doc descrevia, `SettingsPage` **não usa mais** os componentes `NotificationsCard`, `ThresholdsCard` nem `EmailRecipientsCard` — a lógica de thresholds, toggles de notificação e destinatários de email foi **reimplementada inline** dentro do próprio `SettingsPage.jsx`. Os três arquivos de componente continuam no repositório, mas são código morto (nenhum import os referencia — ver seção 2).
>
> O card de **"Aparência" (toggle claro/escuro) também não existe mais** — o `ThemeContext` foi removido do projeto e a aplicação usa um único tema escuro fixo.

Cards atuais, em grid de 2 colunas (`lg:grid-cols-2`):

| Card | Implementação | Descrição |
|------|----------------|-----------|
| Monitoramento (Limites de Alerta) | inline em `SettingsPage` | Inputs numéricos de CPU/RAM/Disco (1–99) + botão "Salvar" → `PATCH /api/settings/thresholds` |
| Notificações | inline em `SettingsPage` | Toggles Teams/Email → `PATCH /api/settings/notifications` |
| Destinatários | inline em `SettingsPage` | Lista + adicionar/remover email → `POST`/`DELETE /api/settings/email-recipients` |
| Sobre | inline em `SettingsPage` | Texto institucional, lista da equipe, versão "2.0.0" |
| API | `ApiKeyCard` (`src/components/ApiKeyCard.jsx`) | Único card de configuração que continua sendo um componente separado e de fato importado |

`ApiKeyCard` está descrito em detalhe na seção 5.12 abaixo e seu comportamento não mudou desde a revisão anterior.

---

### 5.12 ApiKeyCard

**Arquivo:** `src/components/ApiKeyCard.jsx`

Sem alterações de comportamento desde a revisão anterior:
- **Status do servidor:** `GET /api/settings/apikey`
- **Status do navegador:** `hasBrowserApiKey()` (localStorage)
- **Gerar nova chave:** `POST /api/settings/apikey/generate` — se não houver chave no navegador, pede `PANEL_PASSWORD` via `window.prompt()`; exibe a chave gerada uma única vez com botão de copiar
- **Salvar no navegador:** automático ao gerar, ou manualmente colando uma chave existente

---

### 5.13 Componentes Compartilhados

**Card** (`src/shared/components/Card.jsx`) — reescrito: agora é um card de métrica genérico com `title, value, unit, iconName (ou icon), color, subtitle` e `children` opcional (slot para detalhes extras). Cores predefinidas: `purple/blue/green/red/yellow/gray`.

**Icon** (`src/shared/components/Icon.jsx`) — **trocou de biblioteca**: antes era uma biblioteca de ícones SVG inline própria; agora é um wrapper sobre `@fortawesome/react-fontawesome` com um mapa `name → ícone Font Awesome` (`cpu, memory, disk, network, bezier, dashboard, chart, log, alert, server, settings, online, offline, info, external, minimize, expand, chevron-down, menu, email, physical, virtual, time, key, eye, search, warning`). Nomes fora desse mapa geram apenas um `console.warn` e retornam `null` (sem crash).

---

### 5.14 Componentes órfãos (código morto confirmado)

Os arquivos abaixo existem no repositório mas **não são importados em nenhum outro arquivo** do frontend — não fazem parte de nenhuma página renderizada:

| Arquivo | Exporta | Observação |
|---------|---------|------------|
| `components/NotificationsCard.jsx` | `NotificationsCard` | Substituído pela lógica inline em `SettingsPage.jsx` |
| `components/ThresholdsCard.jsx` | `ThresholdsCard` | Idem |
| `components/EmailRecipientsCard.jsx` | `EmailRecipientsCard` | Idem |
| `components/HostSelector.jsx` | `HostSelector` | Resquício de uma versão anterior com dropdown de host |
| `components/HeaderInfo.jsx` | `HeaderInfo` | Resquício de header antigo |
| `components/MetricGrid.jsx` | `MetricsGrid` | Resquício, substituído por `MetricCards` em `DiscoveryDashboard.jsx` |
| `features/logs_feat/components/LogsPlaceholder.jsx` | `LogsPlaceholder` | Resquício de antes do `LogsPanel` real existir |
| `features/alerts/services/alertsApi.js` | `fetchAlerts`, `resolveAlert` | `AlertsPanel` usa `api.js` diretamente, não este arquivo |
| `modals/EndpointModal.jsx` | `EndpointModal` | Já estava órfão na revisão anterior da doc |
| `shared/types/index.ts` | interfaces TS (`Host`, `Metric`, `LogEntry`, `Alert`) | Projeto é JS puro (sem `tsconfig.json`); nenhum arquivo `.ts`/`.tsx` os importa |
| `api.postDiscovery(payload)` (em `api.js`) | função | Não é chamada por nenhuma página — o frontend nunca envia discovery, só o agente |

> Estes arquivos não quebram nada (não são importados, então não entram no bundle de produção do Vite após tree-shaking), mas representam dívida técnica de limpeza.

---

## 6. Serviço de API

**Arquivo:** `src/shared/services/api.js`

Cliente HTTP centralizado baseado em `fetch` (não Axios). Todas as chamadas de API passam pela função interna `request(path, options)`.

**Base URL:** `${import.meta.env.VITE_API_BASE_URL}` — se não definida, usa string vazia (requisições relativas, atendidas pelo proxy do Nginx em produção ou pelo proxy do Vite em dev — ver `vite.config.js`).

**Cabeçalho de autenticação:**

```js
headers: {
  'Content-Type': 'application/json',
  ...(apiKey ? { 'X-API-Key': apiKey } : {}),
}
```

A chave é lida exclusivamente do `localStorage` (`monitor_api_key`) em runtime — **nunca** de uma variável `VITE_*`, porque variáveis `VITE_` são embutidas em texto plano no bundle entregue ao navegador (comentário explícito no código-fonte sobre essa decisão de segurança).

### Funções de dados

| Função                         | Método | Endpoint                                                       | Descrição                                          |
|--------------------------------|--------|------------------------------------------------------------------|-----------------------------------------------------|
| `getDiscovery()`               | GET    | `/api/discovery`                                                 | Lista todos os hosts com dados de hardware (retorna `data.discoveries`) |
| `postDiscovery(payload)`       | POST   | `/api/discovery`                                                 | ⚠️ Definida, mas não chamada por nenhuma página (código morto) |
| `getMetrics(hostId, limit=30)` | GET    | `/api/metrics?host_id=N&limit=30`                                | Métricas do host; sem `hostId` retorna objeto vazio sem chamar a API |
| `getLogs(hostId, options)`     | GET    | `/api/logs?[host_id=N&]limit=50&offset=0&log_type=auth`          | `host_id` **opcional** — omitido, retorna logs agregados de todos os hosts |
| `getAlerts(status='active', hostId=null, limit=null)` | GET | `/api/alerts?status=...[&host_id=N][&limit=N]`     | Parâmetros `hostId` e `limit` são novos nesta revisão (antes só aceitava `status`) |
| `resolveAlert(alertId)`        | PATCH  | `/api/alerts/{id}/resolve`                                        | Resolve um alerta                                   |
| `getApiKey()`                  | GET    | `/api/settings/apikey`                                            | Status e prefixo da API key no servidor             |
| `generateApiKey(password?)`    | POST   | `/api/settings/apikey/generate`                                   | Gera nova API key (aceita senha opcional)           |
| `getNotifications()`           | GET    | `/api/settings/notifications`                                     | Retorna toggles `teams` e `email`                   |
| `patchNotifications(body)`     | PATCH  | `/api/settings/notifications`                                     | Atualiza toggles de notificação                      |
| `getThresholds()`              | GET    | `/api/settings/thresholds`                                        | Retorna limiares de CPU, memória e disco             |
| `patchThresholds(body)`        | PATCH  | `/api/settings/thresholds`                                        | Atualiza limiares de recurso                          |
| `getEmailRecipients()`         | GET    | `/api/settings/email-recipients`                                  | Lista destinatários de email para alertas             |
| `addEmailRecipient(email)`     | POST   | `/api/settings/email-recipients`                                  | Adiciona email à lista                                |
| `removeEmailRecipient(email)`  | DELETE | `/api/settings/email-recipients/{email}`                          | Remove email da lista                                 |

### Funções de autenticação

| Função                     | Descrição |
|----------------------------|-----------|
| `loginWithPassword(password)` | `POST /api/auth/login { password }` — usa `fetch` direto (não passa por `request()`/`API_BASE_URL`); retorna `{ api_key }` ou lança erro |
| `saveApiKey(apiKey)` | Salva (ou remove, se `apiKey` for vazio) a API key no `localStorage` |
| `hasBrowserApiKey()` | Retorna `true` se houver uma API key salva no `localStorage` |

> **`alertsApi.js`** (`src/features/alerts/services/alertsApi.js`) ainda existe no repositório com `fetchAlerts()`/`resolveAlert()` via Axios, mas **não é mais usado** — `AlertsPanel` foi migrado para usar `api.js` diretamente (ver seção 5.14).

### Tratamento de erros

Inalterado desde a revisão anterior: toda função de `request()` lança `Error('AUTH_REQUIRED')` em 401, ou `Error(body.erro || 'Erro HTTP {status}')` para outras falhas.

---

## 7. Autenticação no Frontend

### Fluxo completo

```
Carrega App.jsx
      │
      ├─ getDiscovery()  → 401 Unauthorized
      │       │
      │       └─ setAuthRequired(true)
      │                │
      │                └─ <LoginModal> aparece na tela
      │                        │
      │                  Usuário digita senha
      │                        │
      │                  loginWithPassword(senha)
      │                  POST /api/auth/login
      │                        │
      │                  saveApiKey(api_key)
      │                  localStorage.setItem('monitor_api_key', ...)
      │                        │
      │                  onSuccess()
      │                  setAuthRequired(false)
      │                  setReloadKey(k => k + 1)
      │                        │
      └─ getDiscovery()  → 200 OK  (reloadKey mudou)
             │
             └─ Dashboard carregado normalmente
```

### Onde a API key é usada

Toda requisição feita através de `api.js` inclui automaticamente `X-API-Key: {api_key}` no header, se a chave existir no `localStorage`.

### Comportamento quando a sessão expira

Se a API key for revogada ou o `localStorage` limpo, a próxima requisição retornará 401 e o `LoginModal` aparecerá novamente. Por estar no `localStorage` (não `sessionStorage`), a chave **persiste entre abas e após fechar o navegador**.

---

## 8. Páginas

Definidas em arquivos individuais sob `src/pages/`, reexportados por `src/pages/index.js`.

| Página         | Rota                  | Componente principal                | Dados consumidos                                   |
|----------------|-----------------------|--------------------------------------|------------------------------------------------------|
| DashboardPage  | `/dashboard`          | grid de cards inline                 | `discovery`, `discoveryLoading`, `discoveryError`     |
| DetailsPage    | `/details/:hostId`    | `DiscoveryDashboard`                 | `selectedDiscovery`, `loading` (context)              |
| MetricsPage    | `/metrics/:hostId`    | `GaugeCard` × 4 + `MetricsChart` + `MetricCards` | `metrics`, `loading`, `metricsError`, `selectedHostInfo` |
| LogsPage       | `/logs`, `/logs/:hostId` | `LogsPanel`                       | `hostId` via `useParams()`                            |
| AlertsPage     | `/alerts`, `/alerts/:hostId` | `AlertsPanel`                  | `hostId` via `useParams()` + `discovery` (para nomes de host) |
| EndpointsPage  | `/endpoints`          | tabela inline                        | `discovery`, `discoveryLoading`, `discoveryError`      |
| SettingsPage   | `/settings`           | cards inline + `ApiKeyCard`          | endpoints de `/api/settings/*`                         |

---

## 9. Auto-refresh e Intervalos

| Dados                  | Intervalo  | Componente     | Chamada de API                          |
|-------------------------|------------|------------------|--------------------------------------------|
| Discovery               | No mount + após login | App.jsx | `api.getDiscovery()`                       |
| Métricas                | **10 segundos** (`setInterval`) | App.jsx | `api.getMetrics(effectiveHost)`            |
| Logs                    | 10 segundos | LogsPanel        | `api.getLogs(hostId)`                      |
| Alertas (painel)        | 15 segundos | AlertsPanel      | `api.getAlerts('active', hostId)`          |
| Alertas (badge Sidebar) | 30 segundos | Sidebar          | `api.getAlerts('active')`                  |
| Alertas (contagem por host) | 30 segundos | EndpointsPage | `api.getAlerts('active', null, 100)`       |

Não há WebSocket. Toda atualização é por polling HTTP.

> **Mudança em relação à revisão anterior:** métricas agora têm polling próprio (10s) — antes só atualizavam ao trocar de host ou logar (gap F-4, agora corrigido).

---

## 10. Variáveis de Ambiente

| Variável            | Default      | Descrição                                           |
|---------------------|--------------|-----------------------------------------------------|
| `VITE_API_BASE_URL` | `""` (vazio) | URL base da API backend. Em Docker, normalmente vazio — em desenvolvimento o proxy do Vite (`vite.config.js`) redireciona `/api` para `http://backend:5000`; em produção o Nginx faz esse proxy. |

> O container `frontend` no `docker-compose.yml` **não monta um volume** com o código-fonte (diferente do `backend`, que monta `./BackEnd/app`) — as variáveis `CHOKIDAR_USEPOLLING`/`WATCHPACK_POLLING` definidas no compose só teriam efeito se houvesse um bind mount; sem ele, o conteúdo de `src/` vem da imagem construída em `COPY . .` no `Dockerfile`. `> [VERIFICAR]` com quem mantém o Infra/Docker se isso é intencional (rebuild manual a cada mudança) ou um volume ausente por engano.

---

## 11. Gaps Conhecidos

Issues identificados no código que ainda não foram corrigidos, mais os identificados nesta revisão:

| ID  | Componente    | Descrição                                                                                              | Impacto            |
|-----|---------------|----------------------------------------------------------------------------------------------------------|---------------------|
| ~~F-1~~ | ~~Layout.jsx~~ | ~~Não passava `activeSubTab`/`onSubTabChange` para `TopTabs.jsx`~~ | ✅ **Não se aplica mais** — `TopTabs.jsx` foi removido do projeto |
| ~~F-2~~ | ~~Sidebar.jsx~~ | ~~Badge de alertas hardcoded como `"3"`~~ | ✅ **Corrigido** — badge consome `GET /api/alerts?status=active` a cada 30s |
| ~~F-3~~ | ~~routes.jsx~~ | ~~Rotas `/endpoints` e `/settings` não existiam~~ | ✅ Corrigido (já documentado na revisão anterior) |
| ~~F-4~~ | ~~App.jsx~~ | ~~Métricas só atualizavam ao trocar de host ou após login~~ | ✅ **Corrigido** — `setInterval(carregarMetricas, 10000)` |
| ~~F-5~~ | ~~SettingsPage~~ | ~~Selects de preferências sem efeito real~~ | ✅ Corrigido (já documentado na revisão anterior) |
| F-6 | NotificationsCard / ThresholdsCard / EmailRecipientsCard | Componentes existem mas não são importados — `SettingsPage` reimplementou a mesma lógica inline | Duplicação/dívida técnica; risco de divergência se um dos dois lados for editado sem o outro |
| F-7 | GaugeCard / MetricsPage | Gauge de "Rede" usa valor mockado fixo (`25`); gauge de "Disco" cai para mock (`35`) quando não há `disk_percent`/`disk_io` | Métricas de rede no painel de gauges não refletem dados reais |
| F-8 | index.html | `<link href="/src/style.css">` referencia um arquivo que não existe em `src/` (o CSS real é `index.css`, importado via JS em `main.jsx`) | Requisição 404 inofensiva no carregamento da página |
| F-9 | Layout.jsx | Prop `hostType` recebida mas nunca usada no JSX (resquício do antigo `TopTabs`) | Nenhum — apenas código morto |
| F-10 | SettingsPage | Card "Aparência" (toggle claro/escuro) não existe mais — `ThemeContext` foi removido; app é dark-only | Usuários não têm mais opção de tema claro (mudança de produto, não bug, mas reverte o que a doc anterior descrevia) |

---

## 12. Evolução do Projeto — Decisões Iniciais vs. Decisões Finais

| Decisão | Anterior (doc v1.4) | Atual (esta revisão) | Motivo |
|---------|----------------------|------------------------|--------|
| **Estrutura de páginas** | Um único arquivo `pages/AppPages.jsx` (~720 linhas) com todas as páginas e cards inline | Um arquivo por página em `pages/`, reexportados via `pages/index.js`; cards de Settings movidos para `components/` (parcialmente — ver F-6) | Manutenibilidade; arquivo único havia ficado grande demais |
| **Auto-refresh de métricas** | Inexistente — só atualizava ao trocar de host (gap F-4) | `setInterval` de 10s em `App.jsx` | Dashboard em "tempo quase real" de fato, sem exigir interação |
| **Badge de alertas na Sidebar** | Hardcoded como `"3"` (gap F-2) | `api.getAlerts('active')` real, a cada 30s | Dado correto sem trabalho do operador |
| **Navegação por host** | Dropdown global de host (`HostSelector`, hoje órfão) selecionava o host para todas as páginas | Rotas com `:hostId` (`/details/:hostId`, `/metrics/:hostId`, `/logs/:hostId`, `/alerts/:hostId`) — cada host tem links diretos a partir do Dashboard/Endpoints | Permite abrir detalhes de hosts diferentes em abas diferentes; URLs compartilháveis |
| **Visão agregada de Logs/Alertas** | Sempre por host (`host_id` obrigatório) | `/logs` e `/alerts` sem `:hostId` mostram dados de todos os hosts, com coluna/badge de host | Acompanha a mudança equivalente no backend (`host_id` opcional em `GET /api/logs`/`GET /api/alerts`) |
| **Ícones** | Biblioteca SVG inline própria (`Icon.jsx`) | Font Awesome via `@fortawesome/react-fontawesome` | Catálogo de ícones maior e mais consistente, sem manter SVGs manualmente |
| **Tema claro/escuro** | `ThemeContext` com toggle salvo, card "Aparência" em Settings | Removido — tema único e fixo ("Tema Corvo" / Munynn) | Identidade visual única do produto final; simplificação |
| **Gauges de métricas em tempo real** | Não existiam | `GaugeCard` (`react-gauge-component`) para CPU/Memória/Disco/Rede em `MetricsPage` | Leitura mais rápida do estado atual do host, complementando o gráfico histórico |
| **Cards de Settings (Notificações/Thresholds/Destinatários)** | `NotificationsCard`/`ThresholdsCard`/`EmailRecipientsCard` como componentes dedicados | Lógica reimplementada inline em `SettingsPage.jsx`; os três componentes ficaram órfãos | Não confirmado no código o motivo exato — `(inferido)`: provavelmente para customizar o layout/grid de Settings sem alterar a API dos componentes antigos |
| **React Router** | v6 (`createBrowserRouter`) | v7 (mesma API `createBrowserRouter`, pacote `react-router-dom@^7`) | Atualização de dependência |
| **React** | 18 | 19 (`react@^19.2.5`) | Atualização de dependência |

---

*Documentação atualizada em 21/06/2026 — v2.0*
*Adições v1.1: sistema de autenticação (LoginModal, authRequired, reloadKey, saveApiKey, loginWithPassword, getApiKey, hasBrowserApiKey), ThemeContext, fluxo completo de auth documentado.*
*Adições v1.2: EndpointsPage e SettingsPage (Gap F-3 corrigido); EmailRecipientsCard e ApiKeyCard; rotas /endpoints e /settings funcionais; api.js — header mudou de `Authorization: Bearer` para `X-API-Key`, storage migrou de sessionStorage para localStorage; novos métodos de email recipients na API; Gap F-5 identificado (selects de preferências sem efeito).*
*Adições v1.3 (Fase A — hardening): `api.generateApiKey(password?)` aceita senha opcional; `handleGenerate` pede PANEL_PASSWORD via prompt quando não há chave no localStorage; `vite.config.js` — `server.hmr.clientPort: 80` para HMR via Nginx (porta 5173 não exposta no host).*
*Adições v1.4 (05/06/2026): `alertsApi.js` documentado (seção 6); `NotificationsCard` e `ThresholdsCard` adicionados à seção 5.10 (Gap F-5 corrigido); `getNotifications`, `patchNotifications`, `getThresholds`, `patchThresholds` adicionados à referência da api.js; seção 12 (Evolução do Projeto) adicionada.*
*Adições v2.0 (21/06/2026 — esta revisão, reescrita ampla após verificação linha a linha do código atual): `pages/AppPages.jsx` removido e dividido em arquivos por página; `ThemeContext.jsx` e `TopTabs.jsx` removidos do projeto (gaps F-1/F-10); rotas `:hostId` opcionais em Logs/Alertas e obrigatórias em Details/Metrics; auto-refresh de métricas implementado (gap F-4 corrigido); badge de alertas na Sidebar passou a usar dados reais (gap F-2 corrigido); `Icon.jsx` migrado de SVG inline para Font Awesome; `GaugeCard` novo (com mock de Rede — gap F-7); `Card.jsx` reescrito com API mais rica; identificados como código morto: `NotificationsCard`, `ThresholdsCard`, `EmailRecipientsCard`, `HostSelector`, `HeaderInfo`, `MetricGrid`, `LogsPlaceholder`, `EndpointModal`, `alertsApi.js`, `api.postDiscovery`, `shared/types/index.ts` (gap F-6); identificado link morto para `/src/style.css` em `index.html` (gap F-8); React Router v6→v7 e React 18→19; volume do container `frontend` no docker-compose marcado como `[VERIFICAR]`.*
