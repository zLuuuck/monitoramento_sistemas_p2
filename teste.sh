curl -X POST http://10.81.243.50/api/discovery \
    -H "Content-Type: application/json" \
    -d '{
  "global": {
    "collection_type": "discovery",
    "schema_version": "1.0",
    "agent_id": "55595",
    "host_id": "93391",
    "hostname": "zluuuck-desktop-mint",
    "primary_ip": "192.168.0.100",
    "environment": {
      "is_virtualized": false,
      "hypervisor": null
    },
    "notes": []
  },
  "system": {
    "hostname": "zluuuck-desktop-mint",
    "os": {
      "name": "Linux Mint",
      "pretty_name": "Linux Mint 22.3",
      "version": "22.3 (Zena)",
      "codename": "zena"
    },
    "kernel": {
      "release": "6.17.0-23-generic",
      "version": "#23~24.04.1-Ubuntu",
      "machine": "x86_64"
    },
    "timezone": "America/Sao_Paulo",
    "uptime_seconds": 13314.02
  },
  "cpu": {
    "model_name": "Intel(R) Core(TM) i5-4690 CPU @ 3.50GHz",
    "vendor": "GenuineIntel",
    "architecture": "x86_64",
    "topology": {
      "cores_logical": 4,
      "threads_per_core": 1,
      "source": "lscpu"
    },
    "frequency": {
      "base_mhz": null,
      "max_mhz": 3900.0,
      "min_mhz": 800.0
    }
  },
  "memory": {
    "total_bytes": 4036304896,
    "swap_total_bytes": 2147479552,
    "slots": {
      "total": 2,
      "used": 1,
      "free": 1,
      "modules": [
        {
          "locator": "ChannelA-DIMM0",
          "bank_locator": "BANK 0",
          "populated": false,
          "size_mb": null,
          "type": "Unknown",
          "manufacturer": null,
          "part_number": null,
          "speed_mhz": null,
          "configured_speed_mhz": null,
          "form_factor": "DIMM",
          "data_width_bits": null
        },
        {
          "locator": "ChannelB-DIMM0",
          "bank_locator": "BANK 2",
          "populated": true,
          "size_mb": 4096,
          "type": "DDR3",
          "manufacturer": "1312",
          "part_number": "9905458-009.A00LF",
          "speed_mhz": 1333,
          "configured_speed_mhz": 1333,
          "form_factor": "DIMM",
          "data_width_bits": 64
        }
      ]
    }
  },
  "disk": {
    "total_disks": 1,
    "disks": [
      {
        "device": "/dev/sda",
        "model": "TOSHIBA DT01ACA100",
        "model_family": "Toshiba 3.5\" DT01ACA... Desktop HDD",
        "vendor": "ATA",
        "serial": "47O9NPHFS",
        "firmware": "MS2OA750",
        "type": "HDD",
        "interface": "SATA",
        "form_factor": "3.5 inches",
        "removable": false,
        "size_bytes": 1000204886016,
        "health": {
          "smart_passed": true,
          "power_on_hours": 41251,
          "temperature_celsius": 30
        },
        "partitions": [
          {
            "name": "sda1",
            "type": "part",
            "mountpoint": "/boot/efi",
            "fstype": "vfat",
            "label": null,
            "uuid": "112B-CC87",
            "size_bytes": 536870912,
            "children": []
          },
          {
            "name": "sda2",
            "type": "part",
            "mountpoint": "/",
            "fstype": "ext4",
            "label": null,
            "uuid": "3f45f7a3-f478-4292-8de5-38615876c7ef",
            "size_bytes": 999666221056,
            "children": []
          }
        ]
      }
    ]
  },
  "network": {
    "total_interfaces": 2,
    "default_gateway": {
      "gateway": "192.168.0.1",
      "interface": "wlxb4b0240c2ae8"
    },
    "interfaces": [
      {
        "name": "enp3s0",
        "mac": "70:4d:7b:cd:f5:f3",
        "link_type": "ether",
        "mtu": 1500,
        "state": "DOWN",
        "flags": [
          "NO-CARRIER",
          "BROADCAST",
          "MULTICAST",
          "UP"
        ],
        "ipv4": [],
        "ipv6": [],
        "duplex": "unknown",
        "driver": "r8169",
        "bus_info": "0000:03:00.0"
      },
      {
        "name": "wlxb4b0240c2ae8",
        "mac": "b4:b0:24:0c:2a:e8",
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
            "address": "192.168.0.100",
            "prefix": 24,
            "scope": "global",
            "broadcast": "192.168.0.255"
          }
        ],
        "ipv6": [
          {
            "address": "fe80::26bd:cccb:a43d:2c",
            "prefix": 64,
            "scope": "link"
          }
        ],
        "driver": "rtw88_8822bu",
        "bus_info": "3-2:1.0"
      }
    ]
  },
  "motherboard": {
    "manufacturer": "ASUSTeK COMPUTER INC.",
    "product_name": "H81M-A/BR",
    "version": "Rev X.0x",
    "serial_number": "161275095209049",
    "asset_tag": null,
    "chipset": "Intel Corporation H81 Express LPC Controller (rev 05)",
    "bios": {
      "vendor": "American Megatrends Inc.",
      "version": "2203",
      "release_date": "06/17/2015",
      "revision": "4.6"
    },
    "cpu_sockets": {
      "total": 1,
      "populated": 1,
      "sockets": [
        {
          "designation": "SOCKET 1150",
          "populated": true,
          "type": "Central Processor",
          "speed_mhz": 3500
        }
      ]
    },
    "ram_slots": {
      "total": 2,
      "used": 1,
      "free": 1
    },
    "expansion_slots": [
      {
        "id": "1",
        "type": "x16 PCI Express",
        "current_usage": "In Use",
        "bus_address": "0000:01:00.0"
      },
      {
        "id": "2",
        "type": "x1 PCI Express",
        "current_usage": "Available",
        "bus_address": "0000:02:00.0"
      },
      {
        "id": "3",
        "type": "x1 PCI Express",
        "current_usage": "In Use",
        "bus_address": "0000:03:00.0"
      }
    ]
  },
  "tools": {
    "dmidecode": {
      "installed": true,
      "path": "/usr/sbin/dmidecode",
      "version": "3.5",
      "has_root": true,
      "needs_root": true
    },
    "smartctl": {
      "installed": true,
      "path": "/usr/sbin/smartctl",
      "version": "smartctl 7.4 2023-08-01 r5530 [x86_64-linux-6.17.0-23-generic] (local build)",
      "has_root": true,
      "needs_root": true
    },
    "ethtool": {
      "installed": true,
      "path": "/usr/sbin/ethtool",
      "version": "ethtool version 6.7",
      "has_root": true,
      "needs_root": false
    },
    "lspci": {
      "installed": true,
      "path": "/usr/bin/lspci",
      "version": "lspci version 3.10.0",
      "has_root": true,
      "needs_root": false
    },
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
