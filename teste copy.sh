curl -X POST http://10.81.243.50/api/discovery \
    -H "Content-Type: application/json" \
    -d '{
    "global": {
        "collection_type": "discovery",
        "schema_version": "1.0",
        "agent_id": "70227",
        "host_id": "81725",
        "hostname": "teste-ubuntu",
        "primary_ip": "192.168.48.129",
        "environment": {
            "is_virtualized": true,
            "hypervisor": "VMware"
        },
        "notes": [
            "cpu topology reflects VM vCPU allocation, not physical cores",
            "memory slots unavailable in virtualized environments",
            "disk is virtual \u2014 smartctl data unavailable",
            "network hardware fields (speed, driver, bus_info) unavailable in VM",
            "motherboard section absent in virtualized environments"
        ]
    },
    "system": {
        "hostname": "teste-ubuntu",
        "os": {
            "name": "Ubuntu",
            "pretty_name": "Ubuntu 24.04.4 LTS",
            "version": "24.04.4 LTS (Noble Numbat)",
            "codename": "noble"
        },
        "kernel": {
            "release": "6.8.0-110-generic",
            "version": "#110-Ubuntu",
            "machine": "x86_64"
        },
        "timezone": "Etc/UTC",
        "uptime_seconds": 190.13
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
        "total_bytes": 2013184000,
        "swap_total_bytes": 2147479552,
        "slots": null
    },
    "disk": {
        "total_disks": 1,
        "disks": [
            {
                "device": "/dev/sda",
                "model": "VMware Virtual S",
                "vendor": "VMware",
                "type": "Virtual",
                "interface": "SCSI",
                "size_bytes": 32212254720,
                "partitions": [
                    {
                        "name": "sda1",
                        "type": "part",
                        "mountpoint": null,
                        "fstype": null,
                        "label": null,
                        "uuid": null,
                        "size_bytes": 1048576,
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
                        "size_bytes": 2147483648,
                        "children": []
                    },
                    {
                        "name": "sda3",
                        "type": "part",
                        "mountpoint": null,
                        "fstype": "LVM2_member",
                        "label": null,
                        "uuid": "gmjf2B-U6Fd-hVZQ-TBlf-bqZY-U0FE-vf21RT",
                        "size_bytes": 30061625344,
                        "children": [
                            {
                                "name": "ubuntu--vg-ubuntu--lv",
                                "type": "lvm",
                                "mountpoint": "/",
                                "fstype": "ext4",
                                "label": null,
                                "uuid": "c4695e5a-c0b7-4651-9fe9-3d67f3e28f43",
                                "size_bytes": 15028191232,
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
            "interface": "ens33"
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
                        "scope": "link"
                    }
                ]
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
                        "scope": "link"
                    }
                ]
            }
        ]
    },
    "motherboard": null,
    "tools": {
        "lsblk": {
            "installed": true,
            "path": "/usr/bin/lsblk",
            "version": "lsblk from util-linux 2.39.3",
            "has_root": true,
            "needs_root": false
        },
        "ip": {
            "installed": true,
            "path": "/usr/sbin/ip",
            "version": "ip utility, iproute2-6.1.0, libbpf 1.3.0",
            "has_root": true,
            "needs_root": false
        },
        "lscpu": {
            "installed": true,
            "path": "/usr/bin/lscpu",
            "version": "lscpu from util-linux 2.39.3",
            "has_root": true,
            "needs_root": false
        },
        "journalctl": {
            "installed": true,
            "path": "/usr/bin/journalctl",
            "version": "systemd 255 (255.4-1ubuntu8.15)",
            "has_root": true,
            "needs_root": false
        },
        "timedatectl": {
            "installed": true,
            "path": "/usr/bin/timedatectl",
            "version": "systemd 255 (255.4-1ubuntu8.15)",
            "has_root": true,
            "needs_root": false
        }
    }
}'
