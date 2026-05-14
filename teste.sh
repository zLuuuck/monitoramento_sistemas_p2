curl -X POST http://localhost/api/discovery \
  -H "Content-Type: application/json" \
  -d '{
    "type": "discovery",
    "agent": {
        "agent_id": "66445",
        "host_id": "32926",
        "hostname": "ZLUUUCK-WINDOWS.localdomain",
        "primary_ip": "172.25.69.91",
        "all_ipv4": [
        "172.25.69.91"
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
        "hypervisor": "Microsoft",
        "source": "lscpu"
    },
    "system": {
        "hostname": "ZLUUUCK-WINDOWS.localdomain",
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
        "release": "6.6.87.2-microsoft-standard-WSL2",
        "version": "#1 SMP PREEMPT_DYNAMIC Thu Jun 5 18:30:46 UTC 2025 x86_64 x86_64",
        "machine": "x86_64"
        },
        "timezone": "America/Sao_Paulo",
        "uptime_seconds": 729,
        "virtualization": {
        "is_virtualized": true,
        "hypervisor": "Microsoft"
        }
    },
    "cpu": {
        "model_name": "AMD Ryzen 5 7520U with Radeon Graphics",
        "vendor": "AuthenticAMD",
        "architecture": "x86_64",
        "topology": {
        "vcpus": 8,
        "threads_per_core": 2,
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
        "bytes": 3722682368,
        "gb": 3.47
        },
        "available": {
        "bytes": 2995908608,
        "gb": 2.79
        },
        "free": {
        "bytes": 2286907392,
        "gb": 2.13
        },
        "buffers": {
        "bytes": 71454720,
        "gb": 0.07
        },
        "cached": {
        "bytes": 670072832,
        "gb": 0.62
        },
        "swap": {
        "total": {
            "bytes": 1073741824,
            "gb": 1.0
        },
        "free": {
            "bytes": 911773696,
            "gb": 0.85
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
        "total_disks": 6,
        "disks": [
        {
            "device": "/dev/sda",
            "name": "sda",
            "model": "Virtual Disk",
            "vendor": "Msft",
            "serial": "60022480728b63b9f0b8d5e28f1d4859",
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 407490560,
            "gb": 0.38,
            "tb": 0.0
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": []
        },
        {
            "device": "/dev/sdb",
            "name": "sdb",
            "model": "Virtual Disk",
            "vendor": "Msft",
            "serial": "600224805b5ac507b80a045bc3303ae1",
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 195080192,
            "gb": 0.18,
            "tb": 0.0
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": []
        },
        {
            "device": "/dev/sdc",
            "name": "sdc",
            "model": "Virtual Disk",
            "vendor": "Msft",
            "serial": "60022480c4b5b981886c8a660f68c121",
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 1073745920,
            "gb": 1.0,
            "tb": 0.0
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": []
        },
        {
            "device": "/dev/sdd",
            "name": "sdd",
            "model": "Virtual Disk",
            "vendor": "Msft",
            "serial": "60022480ad075f1a3aeb93f017e5267e",
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 1099511627776,
            "gb": 1024.0,
            "tb": 1.0
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": []
        },
        {
            "device": "/dev/sde",
            "name": "sde",
            "model": "Virtual Disk",
            "vendor": "Msft",
            "serial": "60022480467babea0c2ff48825beb8aa",
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 158334976,
            "gb": 0.15,
            "tb": 0.0
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": []
        },
        {
            "device": "/dev/sdf",
            "name": "sdf",
            "model": "Virtual Disk",
            "vendor": "Msft",
            "serial": "600224808290474e9653ed663a8d8b3e",
            "firmware": null,
            "type": "Virtual",
            "interface": "SCSI",
            "form_factor": null,
            "removable": false,
            "size": {
            "bytes": 1099511627776,
            "gb": 1024.0,
            "tb": 1.0
            },
            "health": {
            "smart_passed": null,
            "power_on_hours": null,
            "temperature_celsius": null
            },
            "partitions": []
        }
        ]
    },
    "network": {
        "total_interfaces": 1,
        "default_gateway": {
        "gateway": "172.25.64.1",
        "interface": "eth0",
        "metric": null,
        "protocol": "kernel"
        },
        "interfaces": [
        {
            "name": "eth0",
            "mac": "00:15:5d:2d:23:3e",
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
                "address": "172.25.69.91",
                "prefix": 20,
                "scope": "global",
                "broadcast": "172.25.79.255"
            }
            ],
            "ipv6": [
            {
                "address": "fe80::215:5dff:fe2d:233e",
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
