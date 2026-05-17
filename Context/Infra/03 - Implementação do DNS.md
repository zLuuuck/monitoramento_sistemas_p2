# 03 - Implementação do DNS

## Verificando porta 53

Especificamente no ubuntu, o processo `systemd-resolve` ocupa a porta 53, esperando algum DNS aparecer (em listening):

``` zsh
sudo lsof -i :53

COMMAND   PID            USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
systemd-r 637 systemd-resolve   14u  IPv4  13459      0t0  UDP _localdnsstub:domain
systemd-r 637 systemd-resolve   15u  IPv4  13460      0t0  TCP _localdnsstub:domain (LISTEN)
systemd-r 637 systemd-resolve   16u  IPv4  13461      0t0  UDP _localdnsproxy:domain
systemd-r 637 systemd-resolve   17u  IPv4  13462      0t0  TCP _localdnsproxy:domain (LISTEN)
```

Para desativar, descometamos uma linha em `/etc/systemd/resolved.conf` chamada `#DNSStubListener=yes`.
Por padrão, essa opção fica ativa, então descometamos essa linhas e trocamos o "yes" por "no".
Por fim, reiniciamos o serviço:
``` zsh
$ sudo systemctl restart systemd-resolved
$ sudo lsof -i :53
```
## Download

Vamos baixar o pacote `dnsmasq` para podermos aplicar nossa configuração DNS:

``` bash
sudo apt install dnsmasq
```

## Configurando

Para editar seu arquivo de configuração:

``` zsh
sudo vim /etc/dnsmasq.conf
```

Apagaremos todo seu conteúdo comentado (há muitas instruções, pois este serviço pode ser utilizado tanto DNS quanto DNS+DHCP, portanto, limitado), e colocamos nossa configuração:

``` zsh
# Interface correta
interface=ens34

# Não escutar loopback apenas
bind-interfaces

domain=monitoramento.lan

no-resolv

# SEM forwarders (sem internet)

address=/api.monitoramento.lan/10.10.10.1
address=/painel.monitoramento.lan/10.10.10.1
```

Reiniciamos o serviço e testamos:

``` zsh
sudo systemctl restart dnsmasq
sudo systemctl status dnsmasq
```

No arquivo `/etc/hosts` do servidor, também adicionamos a linha `10.10.10.1 monitoramento.lan`
## Testes

Testes no servidor:
```
 ✘ teste@teste-ubuntu  ~  ping monitoramento.lan
PING monitoramento.lan (10.10.10.1) 56(84) bytes of data.
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=1 ttl=64 time=0.485 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=2 ttl=64 time=0.095 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=3 ttl=64 time=0.108 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=4 ttl=64 time=0.270 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=5 ttl=64 time=0.118 ms
^C
--- monitoramento.lan ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4112ms
rtt min/avg/max/mdev = 0.095/0.215/0.485/0.149 ms
 teste@teste-ubuntu  ~  dig teste.monitoramento.lan

; <<>> DiG 9.18.39-0ubuntu0.24.04.3-Ubuntu <<>> teste.monitoramento.lan
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: REFUSED, id: 792
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; EDE: 14 (Not Ready)
;; QUESTION SECTION:
;teste.monitoramento.lan.       IN      A

;; Query time: 0 msec
;; SERVER: 10.10.10.1#53(10.10.10.1) (UDP)
;; WHEN: Sun May 17 02:46:51 UTC 2026
;; MSG SIZE  rcvd: 58

 teste@teste-ubuntu  ~  dig monitoramento.lan

; <<>> DiG 9.18.39-0ubuntu0.24.04.3-Ubuntu <<>> monitoramento.lan
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 36117
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
;; QUESTION SECTION:
;monitoramento.lan.             IN      A

;; ANSWER SECTION:
monitoramento.lan.      0       IN      A       10.10.10.1

;; Query time: 0 msec
;; SERVER: 10.10.10.1#53(10.10.10.1) (UDP)
;; WHEN: Sun May 17 02:46:58 UTC 2026
;; MSG SIZE  rcvd: 62

 teste@teste-ubuntu  ~  dig api.monitoramento.lan

; <<>> DiG 9.18.39-0ubuntu0.24.04.3-Ubuntu <<>> api.monitoramento.lan
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 11258
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
;; QUESTION SECTION:
;api.monitoramento.lan.         IN      A

;; ANSWER SECTION:
api.monitoramento.lan.  0       IN      A       10.10.10.1

;; Query time: 0 msec
;; SERVER: 10.10.10.1#53(10.10.10.1) (UDP)
;; WHEN: Sun May 17 02:47:05 UTC 2026
;; MSG SIZE  rcvd: 66

 teste@teste-ubuntu  ~  ping api.monitoramento.lan
PING api.monitoramento.lan (10.10.10.1) 56(84) bytes of data.
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=1 ttl=64 time=0.077 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=2 ttl=64 time=0.077 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=3 ttl=64 time=0.074 ms
64 bytes from monitoramento.lan (10.10.10.1): icmp_seq=4 ttl=64 time=0.107 ms
^C
--- api.monitoramento.lan ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3070ms
rtt min/avg/max/mdev = 0.074/0.083/0.107/0.013 ms
```

Testamos no windows:

```
PS C:\Users\zLuuuck> ping teste.monitoramento.lan

Disparando teste.monitoramento.lan [10.10.10.1] com 32 bytes de dados:
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64

Estatísticas do Ping para 10.10.10.1:
    Pacotes: Enviados = 4, Recebidos = 4, Perdidos = 0 (0% de
             perda),
Aproximar um número redondo de vezes em milissegundos:
    Mínimo = 0ms, Máximo = 0ms, Média = 0ms
PS C:\Users\zLuuuck> nslookup monitoramento.lan
Servidor:  monitoramento.lan
Address:  10.10.10.1

Nome:    monitoramento.lan
Address:  10.10.10.1

PS C:\Users\zLuuuck> nslookup api.monitoramento.lan
Servidor:  monitoramento.lan
Address:  10.10.10.1

Nome:    api.monitoramento.lan
Address:  10.10.10.1

PS C:\Users\zLuuuck> ping teste.monitoramento.lan
A solicitação ping não pôde encontrar o host teste.monitoramento.lan. Verifique o nome e tente
novamente.
PS C:\Users\zLuuuck> ping api.monitoramento.lan

Disparando api.monitoramento.lan [10.10.10.1] com 32 bytes de dados:
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64

Estatísticas do Ping para 10.10.10.1:
    Pacotes: Enviados = 4, Recebidos = 4, Perdidos = 0 (0% de
             perda),
Aproximar um número redondo de vezes em milissegundos:
    Mínimo = 0ms, Máximo = 0ms, Média = 0ms
PS C:\Users\zLuuuck> ping painel.monitoramento.lan

Disparando painel.monitoramento.lan [10.10.10.1] com 32 bytes de dados:
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64
Resposta de 10.10.10.1: bytes=32 tempo<1ms TTL=64

Estatísticas do Ping para 10.10.10.1:
    Pacotes: Enviados = 4, Recebidos = 4, Perdidos = 0 (0% de
             perda),
Aproximar um número redondo de vezes em milissegundos:
    Mínimo = 0ms, Máximo = 0ms, Média = 0ms
```


## Proxy Reverso

Nas duas últimas linhas do `/etc/dnsmasq.conf`, colocamos:

```
address=/api.monitoramento.lan/10.10.10.1
address=/painel.monitoramento.lan/10.10.10.1
```

Estes endereços servirão para que o agente possa enviar as métricas via api.monitoramento.lan, onde vamos reconfigurar o nginx posteriormente para aceitar essa solicitação

Ambos subdomínios são apontados para `10.10.10.1` pois quem vai resolver o encaminhamento, vai ser o Nginx (proxy reverso.)