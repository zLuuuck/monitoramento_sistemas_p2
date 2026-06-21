# 04 - Configuração do Proxy Reverso

> **Nota:** este arquivo ficou em branco desde a criação do repositório — o passo a passo de terminal (como em `02` e `03`) nunca foi registrado. O conteúdo abaixo documenta o **resultado final** atualmente em produção, lido diretamente de `Web/BackEnd/nginx/nginx.conf` e `Web/docker-compose.yml`, e não a sequência de comandos usada para chegar lá.

## Visão geral

Diferente do que a arquitetura planejada (`00 - Arquitetura principal.md`) descrevia inicialmente (Caddy, roteamento por path `/api/*` vs `/*`), o proxy reverso implementado é **Nginx**, sem TLS, roteando por **virtual host (`server_name`)** — não por prefixo de caminho. Isso é consistente com os dois subdomínios já preparados no DNS (`03 - Implementação do DNS.md`): `api.monitoramento.lan` e `painel.monitoramento.lan`, ambos resolvendo para `10.10.10.1`.

## Container

No `docker-compose.yml`, o serviço `nginx` é a única porta exposta ao host:

```yaml
nginx:
  image: nginx:alpine
  container_name: web_nginx
  ports:
    - "80:80"
  volumes:
    - ./BackEnd/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - backend
    - frontend
```

O arquivo de configuração vive em `Web/BackEnd/nginx/nginx.conf` (faz parte do diretório do backend, não tem pasta própria) e é montado somente leitura.

## nginx.conf — roteamento por virtual host

```nginx
events {}

http {
    # DNS interno do Docker — resolve nomes de serviço por requisição (não no boot)
    resolver 127.0.0.11 valid=30s;

    # api.monitoramento.lan → backend Flask
    server {
        listen 80;
        server_name api.monitoramento.lan;

        location / {
            set $backend http://backend:5000;
            proxy_pass $backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # painel.monitoramento.lan → frontend Vite
    server {
        listen 80;
        server_name painel.monitoramento.lan;

        location / {
            set $frontend http://frontend:5173;
            proxy_pass $frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            # WebSocket necessário para Hot Reload do Vite
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

**Pontos a destacar:**

- `resolver 127.0.0.11 valid=30s;` — usa o DNS interno do Docker para resolver os nomes de serviço (`backend`, `frontend`) **a cada requisição**, em vez de resolver uma vez no boot do Nginx. Isso evita que o Nginx fique com um IP de container "morto" em cache caso o `backend`/`frontend` seja recriado (ex.: depois de um `docker compose up` parcial).
- O `set $backend ...` / `set $frontend ...` antes do `proxy_pass` é o que força essa resolução por requisição — `proxy_pass http://backend:5000;` direto, sem a variável, resolveria só uma vez no startup.
- O vhost `painel.monitoramento.lan` inclui os headers `Upgrade`/`Connection: upgrade` porque o frontend roda o **servidor de desenvolvimento do Vite** (não um build estático) — o HMR (Hot Module Reload) do Vite depende de WebSocket.
- Não há bloco de `server` para o domínio "nu" `monitoramento.lan` — só os dois subdomínios são tratados; uma requisição para `monitoramento.lan` direto cairia no `server` padrão do Nginx (sem `server_name` correspondente), que normalmente é o primeiro bloco definido — ou seja, cairia no backend. `> [VERIFICAR]` se esse comportamento é intencional (não há teste documentado para esse caso, diferente do que foi feito para `api.` e `painel.` em `03`).

## Por que server_name e não path-based routing

A documentação de arquitetura (`00`) e, por um tempo, a documentação do Backend (`Context/Backend/Backend-Documentation.md`) descreviam o Nginx roteando por prefixo de path (`/api/*` → backend, `/*` → frontend). Isso **nunca correspondeu ao `nginx.conf` real** — o arquivo sempre roteou por `server_name`, alinhado com a configuração de DNS de `03`, que já preparava dois subdomínios distintos antes mesmo do Nginx existir. Esse texto foi corrigido em ambos os documentos nesta revisão.

---

*Seção reconstruída em 21/06/2026 a partir do `nginx.conf` e `docker-compose.yml` atuais — não documenta o processo histórico de configuração (que não foi registrado), apenas o estado final.*
