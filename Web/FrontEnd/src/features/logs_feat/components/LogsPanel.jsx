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
  if (!status) return <span className="text-gray-400 text-xs">—</span>;

  const cfg = {
    failed:   'bg-red-100 text-red-700 border border-red-200',
    accepted: 'bg-green-100 text-green-700 border border-green-200',
  };

  const label = { failed: 'FALHA', accepted: 'ACEITO' };

  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${cfg[status] ?? 'bg-gray-100 text-gray-600 border border-gray-200'}`}>
      {label[status] ?? status.toUpperCase()}
    </span>
  );
}

// ─── parsed table ────────────────────────────────────────────────────────────

function ParsedTable({ logs }) {
  const [expanded, setExpanded] = useState(null);

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-gray-500 text-left">
            <th className="px-4 py-2 font-medium">Timestamp</th>
            <th className="px-4 py-2 font-medium">Status</th>
            <th className="px-4 py-2 font-medium">Usuário</th>
            <th className="px-4 py-2 font-medium">IP Origem</th>
            <th className="px-4 py-2 font-medium w-8"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {logs.map((log) => {
            const p = log.parsed_data;
            const isOpen = expanded === log.id;
            const isParsed = !!p;

            return (
              <>
                <tr
                  key={log.id}
                  onClick={() => setExpanded(isOpen ? null : log.id)}
                  className={`cursor-pointer transition-colors ${
                    isParsed
                      ? p.status === 'failed'
                        ? 'hover:bg-red-50'
                        : 'hover:bg-green-50'
                      : 'hover:bg-gray-50'
                  } ${isOpen ? 'bg-slate-50' : ''}`}
                >
                  {isParsed ? (
                    <>
                      <td className="px-4 py-2 text-gray-600 whitespace-nowrap">{formatTs(log.timestamp)}</td>
                      <td className="px-4 py-2"><StatusBadge status={p.status} /></td>
                      <td className="px-4 py-2 font-mono text-gray-800">{p.usuario ?? '—'}</td>
                      <td className="px-4 py-2 font-mono text-gray-800">{p.ip_origem ?? '—'}</td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-2 text-gray-500 whitespace-nowrap">{formatTs(log.timestamp)}</td>
                      <td colSpan={3} className="px-4 py-2 text-gray-400 italic truncate max-w-xs">
                        {log.raw_line}
                      </td>
                    </>
                  )}
                  <td className="px-4 py-2 text-gray-400 text-center">
                    {isOpen ? '▲' : '▼'}
                  </td>
                </tr>

                {isOpen && (
                  <tr key={`${log.id}-raw`} className="bg-slate-50">
                    <td colSpan={5} className="px-4 py-2">
                      <p className="text-xs text-gray-400 mb-1">Raw line</p>
                      <pre className="text-xs font-mono text-slate-700 whitespace-pre-wrap break-all bg-slate-100 rounded px-3 py-2">
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
    <div className="rounded-lg bg-gray-900 p-4 font-mono text-xs overflow-x-auto max-h-[480px] overflow-y-auto">
      {logs.map((log) => {
        const status = log.parsed_data?.status;
        const color =
          status === 'failed'   ? 'text-red-400' :
          status === 'accepted' ? 'text-green-400' :
                                  'text-gray-400';
        return (
          <div key={log.id} className={`py-0.5 leading-5 ${color} hover:bg-white/5 px-2 rounded`}>
            <span className="text-gray-600 mr-2 select-none">{formatTs(log.timestamp)}</span>
            {log.raw_line}
          </div>
        );
      })}
    </div>
  );
}

// ─── main component ──────────────────────────────────────────────────────────

const FILTER_TABS = [
  { key: 'all',      label: 'Todos'    },
  { key: 'failed',   label: 'Falha'    },
  { key: 'accepted', label: 'Aceito'   },
  { key: 'unparsed', label: 'Outros'   },
];

export function LogsPanel({ hostId }) {
  const [logs, setLogs]               = useState([]);
  const [total, setTotal]             = useState(0);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [view, setView]               = useState('parsed');   // 'parsed' | 'raw'
  const [statusFilter, setFilter]     = useState('all');
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

  // Contagens para os badges dos filtros
  const counts = {
    all:      logs.length,
    failed:   logs.filter((l) => l.parsed_data?.status === 'failed').length,
    accepted: logs.filter((l) => l.parsed_data?.status === 'accepted').length,
    unparsed: logs.filter((l) => !l.parsed_data).length,
  };

  const filtered = logs.filter((log) => {
    if (statusFilter === 'all')      return true;
    if (statusFilter === 'unparsed') return !log.parsed_data;
    return log.parsed_data?.status === statusFilter;
  });

  return (
    <div className="bg-white rounded-lg shadow-md p-6">

      {/* ── Cabeçalho ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">📋</span>
          <h2 className="text-xl font-semibold text-gray-800">Logs de Autenticação</h2>
          {total > 0 && (
            <span className="text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5">
              {total} no banco
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-gray-400">
              Atualizado {lastUpdated.toLocaleTimeString('pt-BR')}
            </span>
          )}
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-40 flex items-center gap-1 transition-opacity"
          >
            <span className={loading ? 'animate-spin inline-block' : ''}>⟳</span>
            Atualizar
          </button>
        </div>
      </div>

      {/* ── Controles ── */}
      <div className="flex flex-wrap items-center gap-3 mb-4">

        {/* Toggle Parsed / Raw */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
          {[['parsed', 'Estruturado'], ['raw', 'Raw']].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={`px-3 py-1.5 transition-colors ${
                view === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Filtro de status */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
          {FILTER_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1.5 transition-colors ${
                statusFilter === key
                  ? 'bg-slate-700 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
              <span className={`ml-1 text-xs rounded-full px-1.5 ${
                statusFilter === key ? 'bg-white/20' : 'bg-gray-100'
              }`}>
                {counts[key]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Erro ── */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Erro ao carregar logs: {error}
        </div>
      )}

      {/* ── Sem host ── */}
      {!hostId && (
        <div className="text-center py-12 text-gray-400">
          Selecione um host para ver os logs.
        </div>
      )}

      {/* ── Carregando (primeira carga) ── */}
      {hostId && loading && logs.length === 0 && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      )}

      {/* ── Sem resultados ── */}
      {hostId && !loading && filtered.length === 0 && !error && (
        <div className="text-center py-12 text-gray-400">
          Nenhum log encontrado para o filtro selecionado.
        </div>
      )}

      {/* ── Conteúdo ── */}
      {filtered.length > 0 && view === 'parsed' && <ParsedTable logs={filtered} />}
      {filtered.length > 0 && view === 'raw'    && <RawView    logs={filtered} />}
    </div>
  );
}
