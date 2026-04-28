import psutil

def get_disk_info():
    disks = []

    for part in psutil.disk_partitions():
        usage = psutil.disk_usage(part.mountpoint)

        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "filesystem": part.fstype,
            "total_gb": round(usage.total / (1024**3), 2)
        })

    return disks