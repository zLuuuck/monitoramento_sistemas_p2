# agent_information/agent_information.py
"""
Identidade fixa do agente e do host.

- agent_id   : gerado uma vez e persistido em disco (agent_id.txt).
               Sobrevive a reinicializações; muda só se o arquivo for deletado.
- host_id    : gerado da mesma forma, persistido em host_id.txt.
- hostname   : obtido via socket.getfqdn() com fallback para socket.gethostname().
- primary_ip : IP que o sistema usaria para alcançar a internet, resolvido via
               connect() UDP (sem enviar nenhum pacote). Fallback: lista de
               todos os IPv4 do host excluindo loopback.
"""

import os
import random
import socket
import json
import subprocess
from pathlib import Path

# Diretório onde os IDs persistidos ficam guardados
_BASE_DIR = Path(__file__).resolve().parent


# ── ID persistido ────────────────────────────────────────────────────────────

def _load_or_create_id(filename: str) -> str:
    """
    Lê o ID do arquivo filename dentro de _BASE_DIR.
    Se não existir, gera um número aleatório de 10 dígitos e salva.
    """
    id_path = _BASE_DIR / filename
    if id_path.exists():
        value = id_path.read_text().strip()
        if value.isdigit() and len(value) == 10:
            return value

    # Gera garantindo 10 dígitos (sem zeros à esquerda)
    new_id = str(random.randint(10_000, 99_999))
    id_path.write_text(new_id)
    return new_id


# ── Hostname ──────────────────────────────────────────────────────────────────

def _get_hostname() -> str:
    try:
        return socket.getfqdn() or socket.gethostname()
    except Exception:
        return "unknown"


# ── IP principal (rota de saída) ──────────────────────────────────────────────

def _get_primary_ip() -> str | None:
    """
    Descobre o IP que o sistema usaria para alcançar a internet conectando
    um socket UDP ao 8.8.8.8:80 — nenhum pacote é enviado de verdade.

    Retorna None se não for possível determinar.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


def _get_all_ipv4() -> list[str]:
    """
    Retorna todos os IPv4 do host, excluindo loopback (127.x.x.x).
    Método principal: ip -j -4 addr show.
    Fallback: gethostbyname_ex + getaddrinfo.
    """
    # ── Método principal: ip addr (confiável) ─────────────────────────────
    try:
        result = subprocess.run(
            ["ip", "-j", "-4", "addr", "show"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            ips = []
            for iface in data:
                # Ignora loopback
                if iface.get("ifname") == "lo":
                    continue
                for addr_info in iface.get("addr_info", []):
                    local = addr_info.get("local")
                    if local and not local.startswith("127."):
                        ips.append(local)
            # Remove duplicatas mantendo ordem
            seen = set()
            unique = [ip for ip in ips if ip not in seen and not seen.add(ip)]
            if unique:
                return unique
    except Exception:
        pass

    # ── Fallback: resolução de hostname ───────────────────────────────────
    ips = []
    try:
        _, _, ip_list = socket.gethostbyname_ex(socket.gethostname())
        for ip in ip_list:
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass

    if not ips:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = info[4][0]
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        except Exception:
            pass

    return ips


# ── Ponto de entrada público ──────────────────────────────────────────────────

def get_agent_information() -> dict:
    """
    Retorna o dict de identidade do agente e do host.

    Estrutura:
    {
        "agent_id":   "3847291056",
        "host_id":    "7120394856",
        "hostname":   "servidor-01.exemplo.com",
        "primary_ip": "192.168.1.42",   # IP da rota de saída
        "all_ipv4":   ["192.168.1.42"]  # todos os IPs (fallback / auditoria)
    }
    """
    agent_id = _load_or_create_id("agent_id.txt")
    host_id  = _load_or_create_id("host_id.txt")
    hostname = _get_hostname()

    primary_ip = _get_primary_ip()
    all_ipv4   = _get_all_ipv4()
    
    if not all_ipv4 and primary_ip:
        all_ipv4 = [primary_ip]

    # Se primary_ip não foi resolvido, usa o primeiro da lista de fallback
    if not primary_ip and all_ipv4:
        primary_ip = all_ipv4[0]

    return {
        "agent_id":   agent_id,
        "host_id":    host_id,
        "hostname":   hostname,
        "primary_ip": primary_ip,
        "all_ipv4":   all_ipv4,
    }