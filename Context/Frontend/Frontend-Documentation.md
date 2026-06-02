# Frontend — Documentação Técnica

**Versão 1.1 | Junho 2026**

| Campo          | Valor                                                       |
|----------------|-------------------------------------------------------------|
| Projeto        | Monitoramento de Sistemas P2                                |
| Módulo         | Frontend — Dashboard React SPA                              |
| Framework      | React 18 + Vite                                             |
| Gráficos       | Chart.js via react-chartjs-2                                |
| Ambiente       | Docker Container (Node.js + Nginx)                          |
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

---

## 1. Visão Geral

O frontend é uma **Single Page Application (SPA)** construída com React 18 e Vite. Funciona como dashboard de monitoramento em tempo quase real — dados são atualizados automaticamente via polling periódico à API.

**Fluxo principal:**
1. Ao carregar, tenta buscar a lista de hosts com seus dados de discovery
2. Se a API retornar 401 (sem API key), exibe o `LoginModal`
3. Usuário digita a senha do painel → backend valida e retorna a API key
4. API key é salva no `sessionStorage` e usada em todas as requisições seguintes
5. Dashboard exibe hardware, métricas (com gráfico), logs e alertas do host selecionado
6. LogsPanel e AlertsPanel atualizam automaticamente a cada 10s e 15s respectivamente

O frontend **nunca empurra dados** — apenas consome os endpoints GET da API.

---

## 2. Estrutura de Diretórios

```
Web/FrontEnd/
├── Dockerfile
├── nginx.conf
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx                            ← ponto de entrada React
    ├── App.jsx                             ← componente raiz + estado global + LoginModal
    ├── routes.jsx                          ← definição das rotas
    ├── App.css
    ├── index.css
    ├── contexts/
    │   └── ThemeContext.jsx                ← contexto de tema (light/dark)
    ├── shared/
    │   ├── components/
    │   │   ├── Layout.jsx                  ← wrapper com Sidebar + TopTabs + Outlet
    │   │   ├── Sidebar.jsx                 ← menu de navegação lateral
    │   │   ├── TopTabs.jsx                 ← indicador físico/virtual
    │   │   ├── Card.jsx                    ← card reutilizável
    │   │   └── Icon.jsx                    ← biblioteca de ícones SVG
    │   └── services/
    │       └── api.js                      ← cliente HTTP centralizado + auth helpers
    ├── pages/
    │   └── AppPages.jsx                    ← DashboardPage, MetricsPage, LogsPage, AlertsPage
    ├── components/
    │   ├── DiscoveryDashboard.jsx          ← painel de hardware
    │   ├── HostSelector.jsx                ← dropdown de seleção de host
    │   ├── HeaderInfo.jsx                  ← informações do header
    │   └── MetricGrid.jsx                  ← cards de métricas
    ├── features/
    │   ├── metrics/components/
    │   │   └── MetricsChart.jsx            ← gráfico de linha Chart.js
    │   ├── logs_feat/components/
    │   │   ├── LogsPanel.jsx               ← painel de logs com filtros
    │   │   └── LogsPlaceholder.jsx
    │   └── alerts/components/
    │       └── AlertsPanel.jsx             ← painel de alertas com resolução
    └── modals/
        └── EndpointModal.jsx               ← modal (não conectado a nenhuma rota)
```

---

## 3. Roteamento

Definido em `routes.jsx` usando `react-router-dom` v6 com `createBrowserRouter`.

```
/                   → App.jsx (layout wrapper com Outlet)
├── /               → redirect para /dashboard
├── /dashboard      → DashboardPage
├── /metrics        → MetricsPage
├── /logs           → LogsPage
└── /alerts         → AlertsPage
```

> **Rotas na sidebar sem correspondência no router:** `/endpoints` e `/settings` aparecem no menu mas não têm rotas definidas.

---

## 4. Arquitetura de Estado

### Estado Global (App.jsx via Context)

`App.jsx` mantém o estado compartilhado e o distribui via React Context para todos os filhos:

| Estado             | Tipo    | Descrição                                                       |
|--------------------|---------|-----------------------------------------------------------------|
| `selectedHost`     | string  | ID do host selecionado no dropdown                              |
| `discoveries`      | array   | Lista de todos os hosts com dados de discovery                  |
| `selectedDiscovery`| object  | Discovery do host atualmente selecionado                        |
| `selectedHostInfo` | object  | Info resumida do host (hostname, ip, is_online)                 |
| `metrics`          | array   | Últimas N métricas do host selecionado                          |
| `loading`          | boolean | Loading da busca inicial de discoveries                         |
| `metricsLoading`   | boolean | Loading da busca de métricas                                    |
| `error`            | string  | Erro da busca inicial                                           |
| `metricsError`     | string  | Erro da busca de métricas                                       |
| `authRequired`     | boolean | `true` quando a API retorna 401 — exibe o `LoginModal`          |
| `reloadKey`        | number  | Incrementado após login bem-sucedido para forçar re-fetch       |

**Effects em App.jsx:**
- `useEffect([carregarDiscovery, reloadKey])` — busca `getDiscovery()` no mount e após login
- `useEffect([selectedHost, reloadKey])` — busca `getMetrics(selectedHost)` ao mudar de host ou após login

**`carregarDiscovery`** é memoizado com `useCallback` para não recriar a função a cada render.

### Estado Local (componentes que gerenciam seus próprios dados)

| Componente   | Estado local                                              | Auto-refresh |
|--------------|-----------------------------------------------------------|--------------|
| LogsPanel    | logs, total, loading, error, view, statusFilter, lastUpdated | 10 segundos |
| AlertsPanel  | alerts, loading, error                                    | 15 segundos  |
| Sidebar      | minimized (persistido em localStorage)                    | —            |

---

## 5. Componentes

### 5.1 App (raiz)

**Arquivo:** `src/App.jsx`

Componente raiz que gerencia estado global, faz chamadas de API e renderiza o `Layout`.

#### LoginModal

Componente interno de `App.jsx` que aparece quando `authRequired === true`. Bloqueia toda a interface com um overlay escuro e exige a senha do painel para continuar.

**Fluxo:**
1. Usuário digita a senha e envia o formulário
2. `loginWithPassword(password)` → `POST /api/auth/login { password }`
3. Backend valida `PANEL_PASSWORD`, retorna `{ api_key }`
4. `saveApiKey(api_key)` → salva no `sessionStorage` (ou `localStorage`)
5. `onSuccess()` → `setAuthRequired(false)` + `setReloadKey(k => k + 1)`
6. `reloadKey` incrementado dispara re-fetch de discovery e métricas

**Estados internos do modal:** `password`, `error`, `loading`

**Quando aparece:**
- Na carga inicial se a API retornar 401 em `getDiscovery()`
- Ao buscar métricas se retornar 401
- Em qualquer requisição que retorne `AUTH_REQUIRED`

```jsx
{authRequired && (
  <LoginModal onSuccess={() => {
    setAuthRequired(false);
    setReloadKey((k) => k + 1);
  }} />
)}
```

---

### 5.2 Layout

**Arquivo:** `src/shared/components/Layout.jsx`

Wrapper visual que compõe a estrutura da página:

```
┌──────────┬──────────────────────────────────┐
│          │ TopTabs (físico/virtual badge)   │
│ Sidebar  ├──────────────────────────────────┤
│          │                                  │
│          │  <Outlet /> (página atual)       │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

> **Gap conhecido:** `Layout.jsx` não passa `activeSubTab` e `onSubTabChange` para `TopTabs.jsx`. Qualquer clique em sub-tab causa `TypeError: onSubTabChange is not a function`.

---

### 5.3 Sidebar

**Arquivo:** `src/shared/components/Sidebar.jsx`

Menu de navegação lateral com links para as 4 rotas funcionais + 2 links inativos.

> **Gap conhecido:** badge de contador de alertas hardcoded como `"3"` — não consome `GET /api/alerts?status=active`.

---

### 5.4 TopTabs

**Arquivo:** `src/shared/components/TopTabs.jsx`

Indicador visual do tipo de hardware do host selecionado (físico/virtual).

---

### 5.5 DiscoveryDashboard

**Arquivo:** `src/components/DiscoveryDashboard.jsx`

Painel principal da página Dashboard. Exibe hardware, SO, CPU, memória, disco, rede e placa-mãe do host selecionado.

---

### 5.6 MetricsChart

**Arquivo:** `src/features/metrics/components/MetricsChart.jsx`

Gráfico de linha com Chart.js. Datasets: CPU % (azul), Memória % (verde), Disco % (laranja). Eixo Y: 0–100. Sem animações para performance.

---

### 5.7 LogsPanel

**Arquivo:** `src/features/logs_feat/components/LogsPanel.jsx`

Painel de logs com dois modos de visualização:
- **Parsed (tabela):** timestamp, status (badge), usuário, IP origem, tipo de evento
- **Raw (terminal):** fundo escuro, fonte monospace, colorização sintática

Filtros por status com contagens: Todos / Failed / Accepted / Unparsed.

Auto-refresh: **10 segundos**.

---

### 5.8 AlertsPanel

**Arquivo:** `src/features/alerts/components/AlertsPanel.jsx`

Painel de alertas com resolução manual.

Por alerta exibe: badge de severidade (high=vermelho), tipo, IP de origem, timestamp, mensagem descritiva. Botão "Resolver" chama `api.resolveAlert(id)` e remove da lista local imediatamente.

Auto-refresh: **15 segundos**.

---

### 5.9 Componentes Compartilhados

**Card** (`src/shared/components/Card.jsx`) — wrapper visual reutilizável com título, ícone opcional e slot de conteúdo.

**Icon** (`src/shared/components/Icon.jsx`) — biblioteca de ícones SVG inline. Referenciados por nome: `<Icon name="cpu" />`.

---

## 6. Serviço de API

**Arquivo:** `src/shared/services/api.js`

Cliente HTTP centralizado. Todas as chamadas de API passam por aqui.

**Base URL:** `${import.meta.env.VITE_API_BASE_URL}` — se não definida, usa string vazia (requisições relativas via Nginx).

**Cabeçalho de autenticação:** incluído automaticamente em todas as requisições se `getApiKey()` retornar um valor:

```js
headers: {
  'Content-Type': 'application/json',
  ...(key ? { Authorization: `Bearer ${key}` } : {}),
}
```

### Funções de dados

| Função                       | Método | Endpoint                                              | Descrição                                     |
|------------------------------|--------|-------------------------------------------------------|-----------------------------------------------|
| `getDiscovery()`             | GET    | `/api/discovery`                                      | Lista todos os hosts com dados de hardware    |
| `getMetrics(hostId, limit)`  | GET    | `/api/metrics?host_id=N&limit=30`                     | Últimas N métricas do host                    |
| `getLogs(hostId, options)`   | GET    | `/api/logs?host_id=N&limit=50&offset=0&log_type=auth` | Logs paginados do host                        |
| `getAlerts(status)`          | GET    | `/api/alerts?status=active`                           | Alertas por status                            |
| `resolveAlert(alertId)`      | PATCH  | `/api/alerts/{id}/resolve`                            | Resolve um alerta                             |

### Funções de autenticação

| Função                     | Descrição |
|----------------------------|-----------|
| `loginWithPassword(password)` | `POST /api/auth/login { password }` — retorna `{ api_key }` ou lança erro |
| `saveApiKey(apiKey)` | Salva a API key no `sessionStorage` (persiste durante a sessão do navegador) |
| `getApiKey()` | Lê a API key do `sessionStorage` — usada internamente pelo cliente HTTP |
| `hasBrowserApiKey()` | Retorna `true` se houver uma API key salva |

### Tratamento de erros

Todas as funções fazem `throw` com a mensagem do campo `erro` da resposta JSON, ou com o status HTTP. Quando a resposta é 401, a mensagem é `'AUTH_REQUIRED'` — os componentes que recebem esse erro setam `authRequired=true` para exibir o modal.

```js
if (response.status === 401) {
  throw new Error('AUTH_REQUIRED');
}
```

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
      │                  sessionStorage.setItem(...)
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

Toda requisição feita através de `api.js` inclui automaticamente `Authorization: Bearer {api_key}` no header, se a chave existir no `sessionStorage`.

### Comportamento quando a sessão expira

Se a API key for revogada ou o `sessionStorage` limpo (aba fechada), a próxima requisição retornará 401 e o `LoginModal` aparecerá novamente.

---

## 8. Páginas

Definidas em `src/pages/AppPages.jsx`.

| Página         | Rota        | Componente principal     | Dados consumidos                         |
|----------------|-------------|--------------------------|------------------------------------------|
| DashboardPage  | /dashboard  | DiscoveryDashboard       | `selectedDiscovery` (do context)         |
| MetricsPage    | /metrics    | MetricsChart + MetricGrid| `metrics`, `selectedHostInfo` (context)  |
| LogsPage       | /logs       | LogsPanel                | `selectedHost` — estado próprio          |
| AlertsPage     | /alerts     | AlertsPanel              | — estado próprio                         |

---

## 9. Auto-refresh e Intervalos

| Dados          | Intervalo        | Componente   | Chamada de API                      |
|----------------|------------------|--------------|-------------------------------------|
| Discovery      | No mount + após login | App.jsx | `api.getDiscovery()`               |
| Métricas       | Ao mudar de host + após login | App.jsx | `api.getMetrics(selectedHost)` |
| Logs           | 10 segundos      | LogsPanel    | `api.getLogs(hostId)`               |
| Alertas        | 15 segundos      | AlertsPanel  | `api.getAlerts('active')`           |

Não há WebSocket. Toda atualização é por polling HTTP.

---

## 10. Variáveis de Ambiente

| Variável            | Default      | Descrição                                           |
|---------------------|--------------|-----------------------------------------------------|
| `VITE_API_BASE_URL` | `""` (vazio) | URL base da API backend. Em Docker, normalmente vazio (Nginx faz o proxy) |

---

## 11. Gaps Conhecidos

Issues identificados no código que ainda não foram corrigidos:

| ID  | Componente    | Descrição                                                                                              | Impacto            |
|-----|---------------|--------------------------------------------------------------------------------------------------------|--------------------|
| F-1 | Layout.jsx    | Não passa `activeSubTab` / `onSubTabChange` para `TopTabs.jsx` — qualquer clique em sub-tab causa `TypeError: onSubTabChange is not a function` | Crash de runtime ao clicar em sub-tab |
| F-2 | Sidebar.jsx   | Badge de alertas hardcoded como `"3"` — não consome `GET /api/alerts?status=active` | Dado incorreto no badge |
| F-3 | routes.jsx    | Rotas `/endpoints` e `/settings` não existem — links na sidebar não navegam | Links mortos no menu |
| F-4 | App.jsx       | Métricas não atualizam automaticamente — só atualizam ao trocar de host ou após login | Dashboard não reflete dados em tempo real sem interação |

---

*Documentação atualizada em 02/06/2026 — v1.1*  
*Adições: sistema de autenticação (LoginModal, authRequired, reloadKey, saveApiKey, loginWithPassword, getApiKey, hasBrowserApiKey), ThemeContext, fluxo completo de auth documentado.*
