# =============================================================================
# discovery/mem_discovery/mem_virtual.py
#
# Discovery de memória RAM para ambientes virtualizados.
#
# Em VMs, informações de slots físicos (fabricante, DDR type, velocidade)
# não estão disponíveis — o hipervisor não as expõe.
#
# O discovery coleta apenas o total de RAM e swap.
# Métricas de uso (livre, usado, disponível) pertencem à coleta contínua.
# =============================================================================

from agent.utils.parsers import parse_meminfo_kb, kb_to_bytes


def get_virtual_mem_info(meminfo: dict) -> dict:
    """
    Monta o payload de memória para ambiente virtualizado.

    Retorna apenas os totais — uso de memória é responsabilidade
    da coleta contínua (coleta/mem_coleta), não do discovery.

    Parâmetros:
        meminfo (dict): saída parseada de /proc/meminfo

    Retorno:
        dict com total_bytes, swap_total_bytes e slots (ausente em VM).
    """
    # ── Totais de RAM e swap ──────────────────────────────────────────────────
    total_kb      = parse_meminfo_kb(meminfo.get("memtotal"))
    swap_total_kb = parse_meminfo_kb(meminfo.get("swaptotal"))

    return {
        # Unidade base: bytes — conversão para GB/MB fica no frontend
        "total_bytes":      kb_to_bytes(total_kb),
        "swap_total_bytes": kb_to_bytes(swap_total_kb),

        # Slots não disponíveis em VM — campo ausente (não null) indica isso
        # O backend deve verificar a ausência do campo, não o valor null
        "slots": None,
    }

# =============================================================================
# FIM discovery/mem_discovery/mem_virtual.py
# =============================================================================