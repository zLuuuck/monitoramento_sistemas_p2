# =============================================================================
# global_information/global_information.py
#
# Responsável por montar o bloco "global" que encabeça todos os payloads.
#
# Contém:
#   - Identidade do agente e do host (IDs persistidos em disco)
#   - IP primário do host
#   - Ambiente detectado (físico ou virtualizado)
#   - Notas de contexto geradas com base no ambiente
#   - Versão do schema e tipo de coleta
#
# Os IDs são gerados uma única vez e salvos em ~/.agent/.
# O ambiente (is_virtualized + hypervisor) é detectado via lscpu e
# repassado a todos os módulos de discovery — eliminando a necessidade
# de cada módulo rodar lscpu independentemente.
# =============================================================================

import random
import socket
import json
import subprocess
from pathlib import Path

from agent.utils.shell import run
from agent.utils.parsers import parse_lscpu

# Diretório de persistência dos IDs do agente
_DATA_DIR = Path.home() / ".agent"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Versão do schema do payload — incrementar quando houver breaking changes
SCHEMA_VERSION = "1.0"


# =============================================================================
# IDs PERSISTIDOS
# =============================================================================

def _load_or_create_id(filename: str) -> str:
    """
    Lê o ID do arquivo em ~/.agent/<filename>.
    Se não existir ou for inválido, gera um número de 5 dígitos e salva.

    O ID sobrevive a reinicializações do agente.
    Só muda se o arquivo for deletado manualmente.
    """
    id_path = _DATA_DIR / filename
    if id_path.exists():
        value = id_path.read_text().strip()
        if value.isdigit() and len(value) == 5:
            return value

    # Gera ID de 5 dígitos sem zeros à esquerda
    new_id = str(random.randint(10_000, 99_999))
    id_path.write_text(new_id)
    return new_id


# =============================================================================
# HOSTNAME E IP
# =============================================================================

def _get_hostname() -> str:
    """
    Retorna o FQDN do host (nome completo qualificado).
    Fallback: socket.gethostname() se FQDN não estiver disponível.
    """
    try:
        return socket.getfqdn() or socket.gethostname()
    except Exception:
        return "unknown"


def _get_primary_ip() -> str | None:
    """
    Determina o IP primário do host sem enviar pacotes de verdade.

    Técnica: conecta um socket UDP ao 8.8.8.8:80 — o kernel preenche
    o endereço de origem com o IP da interface que seria usada para
    alcançar esse destino, sem enviar nada.

    Retorna None se não for possível determinar.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


# =============================================================================
# DETECÇÃO DE AMBIENTE
# =============================================================================

def _detect_environment() -> dict:
    """
    Detecta se o sistema está rodando em hardware físico ou virtualizado.

    Método: executa `lscpu` e verifica o campo "Hypervisor Vendor".
    Se presente, o sistema é uma VM. Caso contrário, é físico.

    Esta função é o único lugar no agente onde lscpu é executado.
    O resultado é repassado como parâmetro para todos os módulos de
    discovery, evitando chamadas redundantes.

    Retorno:
        dict com:
            is_virtualized (bool): True se for VM
            hypervisor (str|None): nome do hipervisor (KVM, VMware, Microsoft...)
    """
    lscpu_raw  = run("lscpu")
    lscpu      = parse_lscpu(lscpu_raw) if lscpu_raw else {}
    hypervisor = lscpu.get("hypervisor_vendor") or None

    return {
        "is_virtualized": bool(hypervisor),
        "hypervisor":     hypervisor,
    }


# =============================================================================
# NOTAS DE CONTEXTO
# =============================================================================

def _build_notes(is_virtualized: bool) -> list[str]:
    """
    Gera lista de notas informativas sobre o ambiente detectado.

    Em VMs, avisa o backend sobre campos que não estarão disponíveis
    (slots de RAM, S.M.A.R.T., hardware de rede, placa-mãe física).
    Em hardware físico, a lista fica vazia.
    """
    if not is_virtualized:
        return []

    return [
        "cpu topology reflects VM vCPU allocation, not physical cores",
        "memory slots unavailable in virtualized environments",
        "disk is virtual — smartctl data unavailable",
        "network hardware fields (speed, driver, bus_info) unavailable in VM",
        "motherboard section absent in virtualized environments",
    ]


# =============================================================================
# PONTO DE ENTRADA PÚBLICO
# =============================================================================

def build_global_information(collection_type: str) -> dict:
    """
    Monta o bloco "global" que encabeça todos os payloads do agente.

    Este bloco contém a identidade completa do agente + host, o ambiente
    detectado e as notas de contexto. É chamado uma vez na inicialização
    e o resultado é reutilizado em todos os payloads.

    Parâmetros:
        collection_type (str): "discovery" ou "metrics"

    Retorno:
        dict com o bloco global completo.

    Estrutura gerada:
    {
        "collection_type": "discovery",
        "schema_version":  "1.0",
        "agent_id":        "38472",
        "host_id":         "71203",
        "hostname":        "servidor-01.exemplo.com",
        "primary_ip":      "192.168.1.42",
        "environment": {
            "is_virtualized": true,
            "hypervisor":     "VMware"
        },
        "notes": ["..."]
    }
    """
    agent_id    = _load_or_create_id("agent_id.txt")
    host_id     = _load_or_create_id("host_id.txt")
    hostname    = _get_hostname()
    primary_ip  = _get_primary_ip()
    environment = _detect_environment()
    notes       = _build_notes(environment["is_virtualized"])

    return {
        "collection_type": collection_type,
        "schema_version":  SCHEMA_VERSION,
        "agent_id":        agent_id,
        "host_id":         host_id,
        "hostname":        hostname,
        "primary_ip":      primary_ip,
        "environment":     environment,
        "notes":           notes,
    }

# =============================================================================
# FIM global_information/global_information.py
# =============================================================================