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