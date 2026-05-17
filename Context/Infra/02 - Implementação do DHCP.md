# 02 - Implementação do DHCP
Vamos configurar o servidor DHCP no servidor principal
Vamos mudar a rede para 10.10.10.0/26, afim de aguentar mais host

## Mudando IP Fixo no Linux

Neste caso, usando uma máquina virtual, ele fica em `/etc/netplan/50-cloud-init.yaml`, mas se não fosse, ficaria na mesma pasta, mas com outro nome.

Podemos editar esse arquivo usando comando `sudo vim /etc/netplan/50-cloud-init.yaml` e aplicar a seguinte configuração:

``` yaml
teste@teste-ubuntu ~ sudo cat /etc/netplan/50-cloud-init.yaml
[sudo] password for teste:
network:
  version: 2
  ethernets:
    ens33: #interface para internet, manter em dhcp para obter IP
      dhcp4: true
    ens34: #interface usada para a rede ethernet, lab
      dhcp4: false
      addresses:
        - "10.10.10.1/26"
```

Após a aplicação da configuração, reinicamos a rede com o comando `sudo netplan apply`. Conferirmos com o comando `ip -c a`, e localizamos a interface `ens34`:

``` bash
teste@teste-ubuntu ~ ip -c a
3: ens34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:2e:bd:1c brd ff:ff:ff:ff:ff:ff
    altname enp2s2
    inet 10.10.10.1/26 brd 10.10.10.63 scope global ens34
       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe2e:bd1c/64 scope link
       valid_lft forever preferred_lft forever
```

## DHCP 

Instalação do `isc-dhcp-server`:
```
sudo apt install isc-dhcp-server
```

Ele vem com uma boa explicação em `/etc/dhcp/dhcpd.conf`, que nós excluiremos esse conteúdo e aplicaremos nossa configuração:

```
# Opções globais
option domain-name "monitoramento.lan";

default-lease-time 600;
max-lease-time 7200;

ddns-update-style none;
authoritative;

# Sub-rede
subnet 10.10.10.0 netmask 255.255.255.192 {
  range 10.10.10.10 10.10.10.50;
  option routers 10.10.10.1;
  option domain-name-servers 10.10.10.1;
  option subnet-mask 255.255.255.192;
  option broadcast-address 10.10.10.63;
}
```

Atribuímos a nossa interface (ens34)
```
sudo vim /etc/default/isc-dhcp-server

INTERFACESv4="ens34"
```

reiniciamos o serviço:

```
sudo systemctl restart isc-dhcp-server
sudo systemctl status isc-dhcp-server
```

e pronto!
Esta funcionando. Para testar, mudei os dois computadores conectados nessa interface física para usar DHCP:

```
Adaptador Ethernet Ethernet:

   Sufixo DNS específico de conexão. . . . . . : monitoramento.lan
   Endereço IPv6 de link local . . . . . . . . : fe80::586b:e1bf:3ce6:62b6%17
   Endereço IPv4. . . . . . . .  . . . . . . . : 10.10.10.11
   Máscara de Sub-rede . . . . . . . . . . . . : 255.255.255.192
   Gateway Padrão. . . . . . . . . . . . . . . : 10.10.10.1
```

Também podemos dar uma olhada nos logs:

```
$ sudo journalctl -u isc-dhcp-server | grep DHCP

May 17 00:21:32 teste-ubuntu systemd[1]: Started isc-dhcp-server.service - ISC DHCP IPv4 server.
May 17 00:21:32 teste-ubuntu dhcpd[63492]: Internet Systems Consortium DHCP Server 4.4.3-P1
May 17 00:21:32 teste-ubuntu sh[63492]: Internet Systems Consortium DHCP Server 4.4.3-P1
May 17 00:52:35 teste-ubuntu systemd[1]: Started isc-dhcp-server.service - ISC DHCP IPv4 server.
May 17 00:52:36 teste-ubuntu dhcpd[71631]: Internet Systems Consortium DHCP Server 4.4.3-P1
May 17 00:52:36 teste-ubuntu sh[71631]: Internet Systems Consortium DHCP Server 4.4.3-P1
May 17 00:53:11 teste-ubuntu dhcpd[71631]: DHCPDISCOVER from 28:c5:c8:fc:51:8a via ens34
May 17 00:53:12 teste-ubuntu dhcpd[71631]: DHCPOFFER on 10.10.10.10 to 28:c5:c8:fc:51:8a (MNOT12) via ens34
May 17 00:53:12 teste-ubuntu dhcpd[71631]: DHCPREQUEST for 10.10.10.10 (10.10.10.1) from 28:c5:c8:fc:51:8a (MNOT12) via ens34
May 17 00:53:12 teste-ubuntu dhcpd[71631]: DHCPACK on 10.10.10.10 to 28:c5:c8:fc:51:8a (MNOT12) via ens34
May 17 00:54:08 teste-ubuntu dhcpd[71631]: DHCPDISCOVER from 00:e0:4c:4c:12:90 via ens34
May 17 00:54:09 teste-ubuntu dhcpd[71631]: DHCPOFFER on 10.10.10.11 to 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:54:09 teste-ubuntu dhcpd[71631]: DHCPREQUEST for 10.10.10.11 (10.10.10.1) from 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:54:09 teste-ubuntu dhcpd[71631]: DHCPACK on 10.10.10.11 to 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:54:09 teste-ubuntu dhcpd[71631]: DHCPREQUEST for 10.10.10.11 (10.10.10.1) from 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:54:09 teste-ubuntu dhcpd[71631]: DHCPACK on 10.10.10.11 to 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:58:23 teste-ubuntu dhcpd[71631]: DHCPREQUEST for 10.10.10.10 from 28:c5:c8:fc:51:8a (MNOT12) via ens34
May 17 00:58:23 teste-ubuntu dhcpd[71631]: DHCPACK on 10.10.10.10 to 28:c5:c8:fc:51:8a (MNOT12) via ens34
May 17 00:59:19 teste-ubuntu dhcpd[71631]: DHCPREQUEST for 10.10.10.11 from 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:59:19 teste-ubuntu dhcpd[71631]: DHCPACK on 10.10.10.11 to 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:59:19 teste-ubuntu dhcpd[71631]: DHCPREQUEST for 10.10.10.11 from 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
May 17 00:59:19 teste-ubuntu dhcpd[71631]: DHCPACK on 10.10.10.11 to 00:e0:4c:4c:12:90 (ZLUUUCK-WINDOWS) via ens34
```

O que correspondem com nossas expectativas de ter o DHCP funcionando.