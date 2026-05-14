# utils/shell.py
import subprocess

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None
    except:
        return None