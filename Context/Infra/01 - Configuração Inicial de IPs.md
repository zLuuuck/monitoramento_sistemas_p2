# 01 - Configuração Inicial de IPs
Para fins de testes, configurei 2 interfaces na VM Ubuntu server:

``` bash
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:2e:bd:12 brd ff:ff:ff:ff:ff:ff
    altname enp2s1
    inet 192.168.0.10/24 metric 100 brd 192.168.0.255 scope global dynamic ens33
       valid_lft 2141sec preferred_lft 2141sec
    inet6 fe80::20c:29ff:fe2e:bd12/64 scope link
       valid_lft forever preferred_lft forever
3: ens34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:2e:bd:1c brd ff:ff:ff:ff:ff:ff
    altname enp2s2
    inet 10.10.10.1/27 brd 10.10.10.31 scope global ens34
       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe2e:bd1c/64 scope link
       valid_lft forever preferred_lft forever
```

sendo a interface ens33, configurada em modo Bridge na minha placa wifi, a que faz conexão com minha internet real, para fins de atualização de pacotes, instalação de ferramentas e pulling de imagens.

Essa interface deverá ser desativada depois de finalizar toda a configuração e fixar o Docker compose e os dockers files.

A segunda interface, está configurada diretamente na minha placa de rede ethernet (adaptador), que vai diretamente no Switch. Essa placa de rede existe enquanto houver o adaptador conectado e funcionando no Switch não gerenciável. 

Então ficou da seguinte maneira
- VM Ubuntu-Server
	- Interface `ens33`
		- Bridge com placa wifi
		- DHCP com rotedor da internet
		- Conexão com a internet acontece via essa placa
		- Será desativada após todas as configurações finais.
	- Interface `ens34`
		- Bridge com placa de rede ethernet (adaptador)
		- IP estático (10.10.10.1/27)
		- Só funciona quando eu tenho o adaptador conectado e funcionando.
- Computador Host
	- Interface WiFi
		- DHCP
		- Comunicação direta com o roteador
		- Acesso à internet
	- Interface ethernet (adaptador)
		- IP Fixado (10.10.10.2) para fins de testes e ssh inicial
		- pings funcionando com 10.10.10.1 e 10.10.10.3
			- Tive que liberar a regra de entrada no firewall do windows (ICMPv4)
- Notebook do trabalho (para testar conectividade)
	- Também, tem interface WiFi e Ethernet (sem adaptador)
	- Wifi, mesmas configurações do computador host
	- Ethernet
		- IP fixo 10.10.10.3
		- Pings funcionando 10.10.10.1 e 10.10.10.2
		- Também foi feito mudanças nas regras de firewall (entrada e saída)