curl -X POST http://localhost/api/discovery \
    -H "Content-Type: application/json" \
    -d '{
    "type": "discovery",
    "agent": {
        "agent_id": "67579",
        "host_id": "17005",
        "hostname": "teste-ubuntu",
        "primary_ip": "192.168.48.129",
        "all_ipv4": [
        "192.168.48.129",
        "10.10.10.1"
        ]
    },
    "metadata": {
        "schema_version": "1.0",
        "notes": [
        "cpu topology may reflect VM allocation, not physical cores",
        "memory slots unavailable in virtualized environments",
        "disk is virtual \u2014 smartctl data unavailable",
        "network hardware fields (speed, driver, bus_info) unavailable in VM",
        "motherboard chipset and expansion slots unavailable in VM"
        ]
    },
    "environment": {
        "is_virtualized": true,
        "hypervisor": "VMware",
        "source": "lscpu"
    },
    "system": {
        "hostname": "teste-ubuntu",
        "os": {
        "name": "Ubuntu",
        "pretty_name": "Ubuntu 24.04.4 LTS",
        "id": "ubuntu",
        "id_like": "debian",
        "version": "24.04.4 LTS (Noble Numbat)",
        "version_id": "24.04",
        "codename": "noble",
        "build_id": null
        },
        "kernel": {
        "release": "6.8.0-110-generic",
        "version": "#110-Ubuntu SMP PREEMPT_DYNAMIC Thu Mar 19 15:09:20 UTC 2026 x86_64 x86_64",
        "machine": "x86_64"
        },
        "timezone": "Etc/UTC",
        "uptime_seconds": 200,
        "virtualization": {
        "is_virtualized": true,
        "hypervisor": "VMware"
        }
    },
    "cpu": {
        "model_name": "AMD Ryzen 5 7520U with Radeon Graphics",
        "vendor": "AuthenticAMD",
        "architecture": "x86_64",
        "topology": {
        "vcpus": 2,
        "threads_per_core": null,
        "source": "lscpu"
        },
        "frequency": {
        "base_mhz": {
            "value": null,
            "source": null
        },
        "max_mhz": {
            "value": 2794.545,
            "source": "proc_cpuinfo.cpu_mhz"
        },
        "min_mhz": {
            "value": null,
            "source": null
        }
        }
    },
    "memory": {
        "total": {
        "bytes": 2013163520,
        "gb": 1.87
        },
        "available": {
        "bytes": 1607245824,
        "gb": 1.5
        },
        "free": {
        "bytes": 1378406400,
        "gb": 1.28
        },
        "buffers": {
        "bytes": 19587072,
        "gb": 0.02
        },
        "cached": {
        "bytes": 338702336,
        "gb": 0.32
        },
        "swap": {
        "total": {
            "bytes": 2147479552,
            "gb": 2.0
        },
        "free": {
            "bytes": 2147479552,
            "gb": 2.0
        }
        },
        "slots": {
        "total": null,
        "used": null,
        "free": null,
        "modules": []
        }
    },
    "disk": {
        "total_disks": 1,
        "disks": [
        {
            "device": "/dev/sda",
            "name": "sda",
            "model": "VMware Virtual S",
            "vendor": "VMware",
            "serial": null,
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 32212254720,
            "gb": 30.0,
            "tb": 0.03
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": [
            {
                "name": "sda1",
                "type": "part",
                "mountpoint": null,
                "fstype": null,
                "label": null,
                "uuid": null,
                "size": {
                "bytes": 1048576,
                "gb": 0.0
                },
                "children": [],
                "role": "bios_boot"
            },
            {
                "name": "sda2",
                "type": "part",
                "mountpoint": "/boot",
                "fstype": "ext4",
                "label": null,
                "uuid": "e20783f7-5c1a-4511-9d27-1d35c2d8de8b",
                "size": {
                "bytes": 2147483648,
                "gb": 2.0
                },
                "children": []
            },
            {
                "name": "sda3",
                "type": "part",
                "mountpoint": null,
                "fstype": "LVM2_member",
                "label": null,
                "uuid": "gmjf2B-U6Fd-hVZQ-TBlf-bqZY-U0FE-vf21RT",
                "size": {
                "bytes": 30061625344,
                "gb": 28.0
                },
                "children": [
                {
                    "name": "ubuntu--vg-ubuntu--lv",
                    "type": "lvm",
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "label": null,
                    "uuid": "c4695e5a-c0b7-4651-9fe9-3d67f3e28f43",
                    "size": {
                    "bytes": 15028191232,
                    "gb": 14.0
                    },
                    "children": []
                }
                ],
                "role": "unknown"
            }
            ]
        }
        ]
    },
    "network": {
        "total_interfaces": 2,
        "default_gateway": {
        "gateway": "192.168.48.2",
        "interface": "ens33",
        "metric": 100,
        "protocol": "dhcp"
        },
        "interfaces": [
        {
            "name": "ens33",
            "mac": "00:0c:29:2e:bd:12",
            "link_type": "ether",
            "mtu": 1500,
            "state": "UP",
            "flags": [
            "BROADCAST",
            "MULTICAST",
            "UP",
            "LOWER_UP"
            ],
            "ipv4": [
            {
                "address": "192.168.48.129",
                "prefix": 24,
                "scope": "global",
                "broadcast": "192.168.48.255"
            }
            ],
            "ipv6": [
            {
                "address": "fe80::20c:29ff:fe2e:bd12",
                "prefix": 64,
                "scope": "link",
                "broadcast": null
            }
            ],
            "speed_mbps": null,
            "duplex": null,
            "driver": null,
            "bus_info": null
        },
        {
            "name": "ens34",
            "mac": "00:0c:29:2e:bd:1c",
            "link_type": "ether",
            "mtu": 1500,
            "state": "UP",
            "flags": [
            "BROADCAST",
            "MULTICAST",
            "UP",
            "LOWER_UP"
            ],
            "ipv4": [
            {
                "address": "10.10.10.1",
                "prefix": 27,
                "scope": "global",
                "broadcast": "10.10.10.31"
            }
            ],
            "ipv6": [
            {
                "address": "fe80::20c:29ff:fe2e:bd1c",
                "prefix": 64,
                "scope": "link",
                "broadcast": null
            }
            ],
            "speed_mbps": null,
            "duplex": null,
            "driver": null,
            "bus_info": null
        }
        ]
    },
    "motherboard": {
        "manufacturer": null,
        "product_name": null,
        "version": null,
        "serial_number": null,
        "asset_tag": null,
        "chipset": null,
        "bios": {
        "vendor": null,
        "version": null,
        "release_date": null,
        "revision": null
        },
        "cpu_sockets": {
        "total": null,
        "populated": null,
        "sockets": []
        },
        "ram_slots": {
        "total": null,
        "used": null,
        "free": null
        },
        "expansion_slots": []
    }
    }'
