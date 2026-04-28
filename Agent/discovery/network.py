import psutil

def get_network_info():
    interfaces = []

    addrs = psutil.net_if_addrs()

    for interface, addr_list in addrs.items():
        ips = []

        for addr in addr_list:
            if addr.family.name == 'AF_INET':
                ips.append(addr.address)

        interfaces.append({
            "name": interface,
            "ips": ips
        })

    return interfaces