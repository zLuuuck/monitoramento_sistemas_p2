Segue a arquitetura revisada, incorporando todas as correções discutidas:

---

# Composição

A rede será composta por:

- **1 servidor centralizado Ubuntu Server**
  - Responsável por:
    - DHCP (isc-dhcp-server)
    - DNS (dnsmasq, executado diretamente no host)
    - Distribuição de certificados HTTPS (Step-CA)
    - Aplicação via contêineres Docker (proxy reverso, backend, frontend e banco de dados)
  - Observação: manteremos todos os serviços no mesmo host para simplificar o laboratório, embora não seja a prática ideal em produção.
  - **Docker [(Infraestrutura como Código – IaC)](https://www.redhat.com/pt-br/topics/automation/what-is-infrastructure-as-code-iac)**
    - Serviços conteinerizados:
      - **Caddy**: proxy reverso com terminação TLS automática, servindo o frontend estático e encaminhando requisições à API.
      - **Node.js 24 (Alpine)**: utilizado apenas para *build* do frontend com Vite, React e TailwindCSS. O artefato final (arquivos estáticos) será servido pelo Caddy.
      - **Python 3.12 (Alpine)**: backend Flask, com módulos listados em `requirements.txt` (ex.: Flask-SQLAlchemy para integração com o banco).
      - **PostgreSQL 15**: banco de dados para métricas, informações de endpoints e demais dados da aplicação. **A porta 5432 NÃO será exposta ao host**; o acesso é feito exclusivamente pela rede interna do Docker.
      - **Step-CA**: autoridade certificadora interna para emissão dos certificados HTTPS utilizados pelo Caddy e confiáveis pelos agentes.

- **Agentes & Endpoints**
  - Cerca de 7 ou mais endpoints executando agentes de monitoramento.
  - Agentes implementados em Python, distribuídos como binários (gerados com PyInstaller) para Linux.
  - Comunicação: somente **HTTPS** com o servidor, utilizando `POST` nos endpoints:
    - `/api/discovery`
    - `/api/metrics`
  - Cada agente deve receber o certificado raiz da CA (`root_ca.crt`) e configurar a verificação SSL, por exemplo:
    ```python
    requests.post(url, verify="/etc/agente/root_ca.crt")
    ```
    (Caminho a ser padronizado na instalação do agente.)

---

# Rede

- Sub‑rede: `10.10.10.0/26` (máscara 255.255.255.192), provendo até 62 hosts.
- **DHCP** (via `isc-dhcp-server` no host) configurado com:
  ```bash
  subnet 10.10.10.0 netmask 255.255.255.192 {
    range 10.10.10.10 10.10.10.50;
    option routers 10.10.10.1;
    option domain-name-servers 10.10.10.1;
    option domain-name "monitoramento.lan";
    default-lease-time 600;
    max-lease-time 7200;
  }
  ```
  Isso garante que todos os endpoints recebam IP, gateway e o servidor DNS corretos automaticamente.
- **DNS** – executado diretamente no host via `dnsmasq`, resolvendo o domínio principal:
  ```
  address=/monitoramento.lan/10.10.10.1
  ```
  *Nota:* evita‑se o uso de `.local` (reservado para mDNS – RFC 6762) para prevenir conflitos com Avahi/Bonjour.
- Assim, os agentes e qualquer administrador acessam o servidor por `https://monitoramento.lan`, sem depender do IP.

---

# Observações importantes (segurança e robustez mínima)

- **Isolamento do banco**: o PostgreSQL não expõe porta no host, sendo acessado apenas pelos contêineres do backend e do Step‑CA via rede Docker interna.
- **Persistência de dados críticos**: os volumes Docker mapeiam não só o banco, mas também os certificados emitidos pelo Step‑CA e diretórios de log.
- **Firewall local**: configuração básica com `ufw` para permitir apenas tráfego necessário (DHCP, DNS, HTTPS).
- **Logging centralizado**: planeja‑se a coleta de logs dos contêineres e do host para facilitar diagnóstico de falhas (ex.: erros de TLS, indisponibilidade da API).
- **Healthchecks**: serão adicionados ao backend e ao Caddy para detectar paradas silenciosas.

---

# Fluxo básico de operação (corrigido)

```
Agente (endpoint) → DNS (10.10.10.1) → resolve monitoramento.lan
                  → HTTPS (confia na CA Step‑CA)
                  → Caddy (proxy reverso) → Backend Flask → PostgreSQL
                  → Frontend estático servido pelo Caddy (interface administrativa)
```

As principais fragilidades foram tratadas: domínio válido, confiança TLS explícita nos agentes, serviços de rede executados fora de contêineres para evitar dependências circulares, e exposição mínima da superfície de ataque.

---

# Arquitetura Implementada vs. Arquitetura Planejada

> **Atenção:** a arquitetura acima descreve o **planejamento inicial**. O que foi efetivamente implementado difere em pontos importantes:

| Componente | Planejado | Implementado | Motivo da mudança |
|-----------|-----------|--------------|-------------------|
| **Proxy reverso** | Caddy (terminação TLS automática, HTTP/2) | **Nginx** (HTTP simples, sem TLS) | Caddy introduzia complexidade desnecessária para o laboratório; Nginx já era familiar e suficiente |
| **Step-CA** | Autoridade certificadora interna para agentes e Caddy | **Não implementado** | Escopo simplificado; comunicação HTTP entre agentes e backend foi aceita para o ambiente de lab |
| **TLS / HTTPS** | Obrigatório — agentes com `verify="/etc/agente/root_ca.crt"` | **HTTP simples** — sem TLS, sem verificação de certificado | Consequência da não implementação do Step-CA |
| **Serviço de frontend** | Node.js 24 Alpine (só build Vite) — estático servido pelo Caddy | Node.js + Vite **dev server** — servido pelo Nginx como proxy | Dev server facilita hot reload durante o desenvolvimento |
| **Endpoints da API** | Somente `/api/discovery` e `/api/metrics` | `/api/discovery`, `/api/metrics`, `/api/logs`, `/api/alerts`, `/api/heartbeat`, `/api/security/portscan` e endpoints de configuração | Escopo expandiu ao longo das semanas |
| **Firewall (ufw)** | Planejado — permitir DHCP, DNS, HTTPS | Implementado apenas para uso básico | Ambiente de laboratório controlado |
| **Healthchecks Docker** | Planejados para backend e Caddy | Implementado apenas no `postgres` (pg_isready); backend usa `depends_on: service_healthy` | Suficiente para evitar race condition no startup |

### O que ficou como planejado

- Sub-rede `10.10.10.0/26` com DHCP (`isc-dhcp-server`) no host Ubuntu Server
- DNS com `dnsmasq` resolvendo `*.monitoramento.lan` → `10.10.10.1`
- PostgreSQL sem porta exposta no host (acesso apenas pela rede interna Docker)
- 4 containers Docker Compose (postgres, backend, frontend, nginx)
- Agentes Python distribuídos como binários PyInstaller
- Comunicação push — agentes iniciam, backend nunca conecta nos agentes

> **Roteamento do Nginx:** o `nginx.conf` real roteia por **virtual host** (`server_name: api.monitoramento.lan` → backend, `server_name: painel.monitoramento.lan` → frontend), não por prefixo de path (`/api/*` vs `/*`). Essa distinção não estava explícita neste documento e chegou a ser descrita de forma incorreta em `Context/Backend/Backend-Documentation.md` (corrigido nesta revisão). Detalhes completos em `04 - Configuração do Proxy Reverso.md`.