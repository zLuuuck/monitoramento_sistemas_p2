import { useState, useEffect, useCallback } from 'react';
import { api } from '../../../shared/services/api';

// ─── helpers ────────────────────────────────────────────────────────────────

function formatTs(ts) {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return ts;
  }
}

function StatusBadge({ status }) {
  if (!status) return <span className="text-[#8B8B9D] text-xs">—</span>;

  const cfg = {
    failed: 'bg-red-600 text-white font-bold',
    accepted: 'bg-green-600 text-white font-bold',
  };

  const label = { failed: 'FALHA', accepted: 'ACEITO' };

  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${cfg[status] ?? 'bg-[#1A1A2E] text-[#8B8B9D] border border-[#2D2D44]'}`}>
      {label[status] ?? status.toUpperCase()}
    </span>
  );
}

// ─── parsed table ────────────────────────────────────────────────────────────

function ParsedTable({ logs }) {
  const [expanded, setExpanded] = useState(null);

  return (
    <div className="overflow-x-auto rounded-lg border border-[#1A2A4A]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#101C35] text-[#A8B3CF] text-left">
            <th className="px-4 py-2 font-medium">Timestamp</th>
            <th className="px-4 py-2 font-medium">Status</th>
            <th className="px-4 py-2 font-medium">Usuário</th>
            <th className="px-4 py-2 font-medium">IP Origem</th>
            <th className="px-4 py-2 font-medium w-8"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#2D2D44]">
          {logs.map((log) => {
            const p = log.parsed_data;
            const isOpen = expanded === log.id;
            const isParsed = !!p;

            return (
              <>
                <tr
                  key={log.id}
                  onClick={() => setExpanded(isOpen ? null : log.id)}
                  className={`cursor-pointer transition-colors ${isParsed
                      ? p.status === 'failed'
                        ? 'hover:bg-[#EF4444]/10'
                        : 'hover:bg-[#10B981]/10'
                      : 'hover:bg-[#1A1A2E]'
                    } ${isOpen ? 'bg-[#1A1A2E]' : ''}`}
                >
                  {isParsed ? (
                    <>
                      <td className="px-4 py-2 text-[#E2E2E8] whitespace-nowrap">{formatTs(log.timestamp)}</td>
                      <td className="px-4 py-2"><StatusBadge status={p.status} /></td>
                      <td className="px-4 py-2 font-mono text-[#E2E2E8]">{p.usuario ?? '—'}</td>
                      <td className="px-4 py-2 font-mono text-[#E2E2E8]">{p.ip_origem ?? '—'}</td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-2 text-[#8B8B9D] whitespace-nowrap">{formatTs(log.timestamp)}</td>
                      <td colSpan={3} className="px-4 py-2 text-[#8B8B9D] italic truncate max-w-xs">
                        {log.raw_line}
                      </td>
                    </>
                  )}
                  <td className="px-4 py-2 text-[#8B8B9D] text-center">
                    {isOpen ? '▲' : '▼'}
                  </td>
                </tr>

                {isOpen && (
                  <tr key={`${log.id}-raw`} className="bg-[#1A1A2E]">
                    <td colSpan={5} className="px-4 py-2">
                      <p className="text-xs text-[#8B8B9D] mb-1">Raw line</p>
                      <pre className="text-xs font-mono text-[#E2E2E8] whitespace-pre-wrap break-all bg-[#050816] rounded px-3 py-2">
                        {log.raw_line}
                      </pre>
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── raw view ────────────────────────────────────────────────────────────────

function RawView({ logs }) {
  return (
    <div className="rounded-lg bg-[#101C35] border border-[#1A2A4A] p-4 font-mono text-xs overflow-x-auto max-h-[480px] overflow-y-auto">
      {logs.map((log) => {
        const status = log.parsed_data?.status;
        const color =
          status === 'failed' ? 'text-[#EF4444]' :
            status === 'accepted' ? 'text-[#10B981]' :
              'text-[#A8B3CF]';
        return (
          <div key={log.id} className={`py-0.5 leading-5 ${color} hover:bg-[#1A1A2E] px-2 rounded`}>
            <span className="text-[#6B6B7D] mr-2 select-none">{formatTs(log.timestamp)}</span>
            {log.raw_line}
          </div>
        );
      })}
    </div>
  );
}

// ─── main component ──────────────────────────────────────────────────────────

const FILTER_TABS = [
  { key: 'all', label: 'Todos' },
  { key: 'failed', label: 'Falha' },
  { key: 'accepted', label: 'Aceito' },
  { key: 'unparsed', label: 'Outros' },
];

export function LogsPanel({ hostId }) {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState('parsed');
  const [statusFilter, setFilter] = useState('all');
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchLogs = useCallback(async () => {
    if (!hostId) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.getLogs(hostId, { limit: 50 });
      setLogs(data.logs || []);
      setTotal(data.total || 0);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [hostId]);

  useEffect(() => {
    fetchLogs();
    const id = setInterval(fetchLogs, 10_000);
    return () => clearInterval(id);
  }, [fetchLogs]);

  const counts = {
    all: logs.length,
    failed: logs.filter((l) => l.parsed_data?.status === 'failed').length,
    accepted: logs.filter((l) => l.parsed_data?.status === 'accepted').length,
    unparsed: logs.filter((l) => !l.parsed_data).length,
  };

  const filtered = logs.filter((log) => {
    if (statusFilter === 'all') return true;
    if (statusFilter === 'unparsed') return !log.parsed_data;
    return log.parsed_data?.status === statusFilter;
  });

  return (
    <div className="crow-card p-6">

      {/* ── Cabeçalho ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold crow-text-primary">Logs de Autenticação</h2>
          {total > 0 && (
            <span className="text-xs text-[#A8B3CF] bg-[#1A1A2E] rounded-full px-2 py-0.5">
              {total} no banco
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-[#8B8B9D]">
              Atualizado {lastUpdated.toLocaleTimeString('pt-BR')}
            </span>
          )}
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="text-sm text-[#A855F7] hover:text-[#C084FC] disabled:opacity-40 flex items-center gap-1 transition-opacity"
          >
            <span className={loading ? 'animate-spin inline-block' : ''}>⟳</span>
            Atualizar
          </button>
        </div>
      </div>

      {/* ── Controles ── */}
      <div className="flex flex-wrap items-center gap-3 mb-4">

        <div className="flex rounded-lg border border-[#1A2A4A] overflow-hidden text-sm">
          {[['parsed', 'Estruturado'], ['raw', 'Raw']].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={`px-3 py-1.5 transition-colors ${view === key
                  ? 'bg-[#4B2D6E] text-[#A855F7]'
                  : 'bg-[#1A1A2E] text-[#A8B3CF] hover:bg-[#2D2D44]'
                }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex rounded-lg border border-[#1A2A4A] overflow-hidden text-sm">
          {FILTER_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1.5 transition-colors ${statusFilter === key
                  ? 'bg-[#4B2D6E] text-[#A855F7]'
                  : 'bg-[#1A1A2E] text-[#A8B3CF] hover:bg-[#2D2D44]'
                }`}
            >
              {label}
              <span className={`ml-1 text-xs rounded-full px-1.5 ${statusFilter === key ? 'bg-white/20' : 'bg-[#2D2D44]'
                }`}>
                {counts[key]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Erro ── */}
      {error && (
        <div className="mb-4 rounded-lg border border-[#EF4444] bg-[#EF4444]/10 px-4 py-3 text-sm text-[#EF4444]">
          Erro ao carregar logs: {error}
        </div>
      )}

      {/* ── Sem host ── */}
      {!hostId && (
        <div className="text-center py-12 text-[#8B8B9D]">
          Selecione um host para ver os logs.
        </div>
      )}

      {/* ── Carregando (primeira carga) ── */}
      {hostId && loading && logs.length === 0 && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#A855F7]" />
        </div>
      )}

      {/* ── Sem resultados ── */}
      {hostId && !loading && filtered.length === 0 && !error && (
        <div className="text-center py-12 text-[#8B8B9D]">
          Nenhum log encontrado para o filtro selecionado.
        </div>
      )}

      {/* ── Conteúdo ── */}
      {filtered.length > 0 && view === 'parsed' && <ParsedTable logs={filtered} />}
      {filtered.length > 0 && view === 'raw' && <RawView logs={filtered} />}
    </div>
  );
}