# utils/sysfs.py
def read_sysfs_khz_to_mhz(path):
    """
    Lê um arquivo do sysfs que contém um valor em kHz e retorna o valor em MHz (float).
    Se o arquivo não existir ou ocorrer erro, retorna None.
    """
    try:
        with open(path, 'r') as f:
            khz = float(f.read().strip())
            return khz / 1000.0
    except (FileNotFoundError, ValueError, PermissionError, OSError):
        return None