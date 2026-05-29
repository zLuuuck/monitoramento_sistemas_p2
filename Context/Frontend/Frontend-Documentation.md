# Frontend — Documentação Técnica

**Versão 1.0 | Maio 2026**

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
   - 5.1 App (raiz)
   - 5.2 Layout
   - 5.3 Sidebar
   - 5.4 TopTabs
   - 5.5 DiscoveryDashboard
   - 5.6 MetricsChart
   - 5.7 LogsPanel
   - 5.8 AlertsPanel
   - 5.9 Componentes Compartilhados (Card, Icon)
6. [Serviço de API](#6-serviço-de-api)
7. [Páginas](#7-páginas)
8. [Auto-refresh e Intervalos](#8-auto-refresh-e-intervalos)
9. [Variáveis de Ambiente](#9-variáveis-de-ambiente)
10. [Gaps Conhecidos](#10-gaps-conhecidos)

---

## 1. Visão Geral

O frontend é uma **Single Page Application (SPA)** construída com React 18 e Vite. Funciona como dashboard de monitoramento em tempo quase real — dados são atualizados automaticamente via polling periódico à API.

**Fluxo principal:**
1. Ao carregar, busca a lista de hosts com seus dados de discovery
2. Usuário seleciona o host no dropdown da sidebar
3. Dashboard exibe hardware, métricas (com gráfico), logs e alertas daquele host
4. LogsPanel e AlertsPanel atualizam automaticamente a cada 10s e 15s respectivamente

O frontend **nunca empurra dados** — apenas consome os endpoints GET da API. Os dados chegam do agente via backend, e o frontend os lê.

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
    ├── App.jsx                             ← componente raiz + estado global
    ├── routes.jsx                          ← definição das rotas
    ├── App.css
    ├── index.css
    ├── shared/
    │   ├── components/
    │   │   ├── Layout.jsx                  ← wrapper com Sidebar + TopTabs + Outlet
    │   │   ├── Sidebar.jsx                 ← menu de navegação lateral
    │   │   ├── TopTabs.jsx                 ← indicador físico/virtual
    │   │   ├── Card.jsx                    ← card reutilizável
    │   │   └── Icon.jsx                    ← biblioteca de ícones SVG
    │   └── services/
    │       └── api.js                      ← cliente HTTP centralizado
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

**Rotas na sidebar sem correspondência no router:** `/endpoints` e `/settings` aparecem no menu mas não têm rotas definidas — clicar neles não navega a lugar nenhum.

---

## 4. Arquitetura de Estado

O estado é dividido em dois níveis:

### Estado Global (App.jsx via Context)

`App.jsx` mantém o estado compartilhado e o distribui via React Context para todos os filhos:

| Estado             | Tipo    | Descrição                                               |
|--------------------|---------|----------------------------------------------------------|
| `selectedHost`     | string  | ID do host selecionado no dropdown                       |
| `discoveries`      | array   | Lista de todos os hosts com dados de discovery           |
| `selectedDiscovery`| object  | Discovery do host atualmente selecionado                 |
| `selectedHostInfo` | object  | Info resumida do host (hostname, ip, is_online)          |
| `metrics`          | array   | Últimas N métricas do host selecionado                   |
| `loading`          | boolean | Loading da busca inicial de discoveries                  |
| `metricsLoading`   | boolean | Loading da busca de métricas                             |
| `error`            | string  | Erro da busca inicial                                    |
| `metricsError`     | string  | Erro da busca de métricas                                |

**Effects em App.jsx:**
- `useEffect([], [])` — busca `getDiscovery()` no mount
- `useEffect([selectedHost])` — busca `getMetrics(selectedHost)` sempre que o host muda

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

Componente raiz que:
- Gerencia todo o estado global
- Faz as chamadas de API para discovery e métricas
- Renderiza o `Layout` com `Outlet` (onde as páginas são inseridas)
- Provê o contexto para filhos via React Context

```jsx
// Contexto disponível para todos os filhos via useContext()
{
  selectedHost,
  setSelectedHost,
  metrics,
  loading,
  metricsError,
  selectedDiscovery,
  selectedHostInfo
}
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

Recebe props de navegação e as passa para `Sidebar` e `TopTabs`.

**Gap conhecido:** `Layout.jsx` não passa `activeSubTab` e `onSubTabChange` para `TopTabs.jsx`. Qualquer clique em sub-tab causa `TypeError: onSubTabChange is not a function`.

---

### 5.3 Sidebar

**Arquivo:** `src/shared/components/Sidebar.jsx`

Menu de navegação lateral com:
- Links de navegação para as 4 rotas funcionais (Dashboard, Metrics, Logs, Alerts)
- 2 links inativos (Endpoints, Settings) sem rotas correspondentes
- Destaque visual na rota ativa
- Toggle de minimizar/expandir (estado em `localStorage`)
- Badge de contador de alertas — **atualmente hardcoded como "3"**, não consome a API

---

### 5.4 TopTabs

**Arquivo:** `src/shared/components/TopTabs.jsx`

Indicador visual do tipo de hardware do host selecionado (físico/virtual). Recebe `activeSubTab` e `onSubTabChange` via props.

**Gap conhecido:** essas props não são passadas pelo `Layout.jsx`, causando erro de runtime ao clicar.

---

### 5.5 DiscoveryDashboard

**Arquivo:** `src/components/DiscoveryDashboard.jsx`

Painel principal da página Dashboard. Recebe o objeto `discovery` como prop e exibe:

**Cards de resumo (4 mini-stats):**
| Card          | Exibe                         |
|---------------|-------------------------------|
| CPU           | Modelo e número de cores      |
| RAM           | Total em GB                   |
| Disco         | Capacidade total em GB        |
| Rede          | Número de interfaces          |

**Painéis detalhados:**
- Status do host (hostname, IP, badge online/offline, badge físico/virtual)
- Sistema (OS, kernel, uptime, hypervisor)
- CPU (modelo, cores, clock base, clock máximo, GHz)
- Memória (total GB + lista de módulos com slot, tipo, speed)
- Disco (lista de partições com device, mountpoint, filesystem, tamanho)
- Rede (lista de interfaces com IP, MAC, driver, velocidade)
- Módulos de RAM detalhados (apenas hosts físicos)
- Placa-mãe (apenas hosts físicos, se `motherboard` presente)

**Funções auxiliares internas:**
- `normalizeNetworks()` — normaliza o formato das interfaces (compatibilidade entre payload antigo e novo)
- `normalizeMemoryModules()` — normaliza formato dos módulos de memória

---

### 5.6 MetricsChart

**Arquivo:** `src/features/metrics/components/MetricsChart.jsx`

Gráfico de linha com Chart.js mostrando as últimas N métricas no tempo.

**Datasets:**
| Dataset     | Cor    | Campo         |
|-------------|--------|---------------|
| CPU %       | Azul   | cpu_percent   |
| Memória %   | Verde  | memory_percent|
| Disco %     | Laranja| disk_percent  |

**Configuração do gráfico:**
- Eixo X: timestamps formatados como `HH:MM`
- Eixo Y: 0–100 (percentual)
- Sem animações (desabilitadas para performance no polling)
- Responsivo, mantém aspect ratio

---

### 5.7 LogsPanel

**Arquivo:** `src/features/logs_feat/components/LogsPanel.jsx`

Painel completo de visualização de logs de autenticação.

**Estado interno:**
- `logs` — array de linhas de log
- `view` — `parsed` ou `raw`
- `statusFilter` — `all`, `failed`, `accepted`, `unparsed`
- `lastUpdated` — timestamp da última atualização
- `loading` / `error`

**Modos de visualização:**

*Parsed (tabela):*

| Coluna    | Fonte              |
|-----------|--------------------|
| Timestamp | log.timestamp      |
| Status    | parsed_data.status (badge colorido) |
| Usuário   | parsed_data.usuario |
| IP Origem | parsed_data.ip_origem |
| Tipo      | parsed_data.event_type |

Linha expansível exibe o `raw_line` completo.

*Raw (terminal):*
- Fundo escuro, fonte monospace
- Colorização sintática: vermelho para `failed`, verde para `accepted/session_open`

**Filtros de status (com contagens):**
- Todos / Failed / Accepted / Unparsed (log sem parsed_data)

**Auto-refresh:** a cada **10 segundos** chama `api.getLogs(hostId, {limit: 50})`.

---

### 5.8 AlertsPanel

**Arquivo:** `src/features/alerts/components/AlertsPanel.jsx`

Painel de alertas de segurança com resolução manual.

**Estado interno:** `alerts`, `loading`, `error`

**Exibição por alerta:**
- Badge de severidade colorido (high=vermelho, medium=amarelo, low=cinza)
- Tipo de alerta (`brute_force` → "Força Bruta", `port_scan` → "Port Scan")
- IP de origem
- Timestamp
- Mensagem descritiva (`alert.message`)
- Botão "Resolver" — chama `api.resolveAlert(id)` e remove o alerta da lista local imediatamente

**Auto-refresh:** a cada **15 segundos** chama `api.getAlerts('active')`.

---

### 5.9 Componentes Compartilhados

**Card** (`src/shared/components/Card.jsx`)
- Wrapper visual reutilizável com título, ícone opcional e slot de conteúdo
- Usado em DiscoveryDashboard e MetricGrid

**Icon** (`src/shared/components/Icon.jsx`)
- Biblioteca de ícones SVG inline
- Referenciados por nome (ex: `<Icon name="cpu" />`)
- Evita dependência de pacote de ícones externo

---

## 6. Serviço de API

**Arquivo:** `src/shared/services/api.js`

Cliente HTTP centralizado. Todas as chamadas de API passam por aqui — nenhum componente faz `fetch` diretamente.

**Base URL:** `${import.meta.env.VITE_API_BASE_URL}` — se não definida, usa string vazia (requisições relativas, assumindo mesmo servidor).

| Função                       | Método | Endpoint                                              | Descrição                                     |
|------------------------------|--------|-------------------------------------------------------|-----------------------------------------------|
| `getDiscovery()`             | GET    | `/api/discovery`                                      | Lista todos os hosts com dados de hardware    |
| `postDiscovery(payload)`     | POST   | `/api/discovery`                                      | (não usado pelo frontend atualmente)          |
| `getMetrics(hostId, limit)`  | GET    | `/api/metrics?host_id=N&limit=30`                     | Últimas N métricas do host                    |
| `getLogs(hostId, options)`   | GET    | `/api/logs?host_id=N&limit=50&offset=0&log_type=auth` | Logs paginados do host                        |
| `getAlerts(status)`          | GET    | `/api/alerts?status=active`                           | Alertas por status                            |
| `resolveAlert(alertId)`      | PATCH  | `/api/alerts/{id}/resolve`                            | Resolve um alerta                             |

**Tratamento de erros:** todas as funções fazem `throw` com a mensagem do campo `erro` da resposta JSON, ou com o status HTTP se não houver JSON de erro.

---

## 7. Páginas

Definidas em `src/pages/AppPages.jsx`.

| Página         | Rota        | Componente principal     | Dados consumidos do contexto         |
|----------------|-------------|--------------------------|--------------------------------------|
| DashboardPage  | /dashboard  | DiscoveryDashboard       | `selectedDiscovery`                  |
| MetricsPage    | /metrics    | MetricsChart + MetricGrid| `metrics`, `selectedHostInfo`        |
| LogsPage       | /logs       | LogsPanel                | `selectedHost` (gerencia próprio estado) |
| AlertsPage     | /alerts     | AlertsPanel              | — (gerencia próprio estado)          |

---

## 8. Auto-refresh e Intervalos

| Dados          | Intervalo | Componente   | Chamada de API                      |
|----------------|-----------|--------------|-------------------------------------|
| Discovery      | Apenas no mount | App.jsx | `api.getDiscovery()`               |
| Métricas       | Ao mudar de host | App.jsx | `api.getMetrics(selectedHost)`    |
| Logs           | 10 segundos | LogsPanel  | `api.getLogs(hostId)`               |
| Alertas        | 15 segundos | AlertsPanel | `api.getAlerts('active')`          |

Não há WebSocket. Toda atualização é por polling HTTP.

---

## 9. Variáveis de Ambiente

| Variável            | Default          | Descrição                                           |
|---------------------|------------------|-----------------------------------------------------|
| `VITE_API_BASE_URL` | `""` (vazio)     | URL base da API backend. Em Docker, normalmente `http://backend:5000` ou proxy Nginx |

Em Docker, a URL é configurada via `docker-compose.yml` ou `.env` no diretório do FrontEnd.

---

## 10. Gaps Conhecidos

Issues identificados que ainda não foram corrigidos:

| ID  | Componente   | Descrição                                                                                              | Impacto            |
|-----|--------------|--------------------------------------------------------------------------------------------------------|--------------------|
| F-1 | Layout.jsx   | Não passa `activeSubTab` / `onSubTabChange` para `TopTabs.jsx` — qualquer clique em sub-tab causa `TypeError: onSubTabChange is not a function` | Crash de runtime ao clicar em sub-tab |
| F-2 | Sidebar.jsx  | Badge de alertas hardcoded como `"3"` — não consome `GET /api/alerts?status=active` | Dado incorreto no badge |
| F-3 | routes.jsx   | Rotas `/endpoints` e `/settings` não existem — links na sidebar não navegam | Links mortos no menu |
| F-4 | App.jsx      | Métricas não atualizam automaticamente — só atualizam ao trocar de host | Dashboard não reflete dados em tempo real |

---

*Para documentação técnica do backend, consulte [Context/Backend/Backend-Documentation.md](../Backend/Backend-Documentation.md).*
*Para documentação do banco de dados, consulte [Context/Database/Database-Documentation.md](../Database/Database-Documentation.md).*
*Para documentação do agente, consulte [Context/Agent/Agent-Documentation.md](../Agent/Agent-Documentation.md).*
