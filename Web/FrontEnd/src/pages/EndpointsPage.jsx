import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { Icon } from '../shared/components/Icon';
import { api } from '../shared/services/api';

const STATUS_OPTIONS = [
  { value: 'all', label: 'Status: Todos' },
  { value: 'online', label: 'Status: Online' },
  { value: 'alert', label: 'Status: Em alerta' },
  { value: 'offline', label: 'Status: Offline' },
];

function StatCard({ icon, iconColor, label, value }) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl p-4"
      style={{ backgroundColor: '#101C35', border: '1px solid #1A2A4A' }}
    >
      <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: iconColor.bg }}>
        <Icon name={icon} size="text-base" className={iconColor.text} />
      </div>
      <div>
        <p className="text-xs text-[#A8B3CF]">{label}</p>
        <p className="text-xl font-bold text-[#E2E2E8]">{value}</p>
      </div>
    </div>
  );
}

export function EndpointsPage() {
  const { discovery, discoveryLoading, discoveryError } = useOutletContext();
  const [alertCounts, setAlertCounts] = useState({});
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    const loadAlertCounts = async () => {
      try {
        const alerts = await api.getAlerts('active', null, 100);
        const counts = {};
        for (const alert of alerts) {
          counts[alert.host_id] = (counts[alert.host_id] || 0) + 1;
        }
        setAlertCounts(counts);
      } catch (error) {
        console.error('Erro ao carregar contagem de alertas:', error);
      }
    };

    loadAlertCounts();
    const interval = setInterval(loadAlertCounts, 30000);
    return () => clearInterval(interval);
  }, []);

  const hosts = useMemo(() => {
    return (discovery || []).map((host) => {
      const alertCount = alertCounts[host.host_id] || 0;
      const isOnline = host.host?.status === 'online';
      const statusKey = alertCount > 0 ? 'alert' : isOnline ? 'online' : 'offline';
      const osLabel = host.os_name
        ? `${host.os_name}${host.os_version ? ` ${host.os_version}` : ''}`
        : host.is_virtualized ? 'Virtual' : 'Físico';
      return { ...host, alertCount, statusKey, osLabel };
    });
  }, [discovery, alertCounts]);

  const stats = useMemo(() => ({
    total: hosts.length,
    online: hosts.filter((h) => h.statusKey === 'online').length,
    alert: hosts.filter((h) => h.statusKey === 'alert').length,
    offline: hosts.filter((h) => h.statusKey === 'offline').length,
  }), [hosts]);

  const filteredHosts = useMemo(() => {
    const term = search.trim().toLowerCase();
    return hosts.filter((host) => {
      if (statusFilter !== 'all' && host.statusKey !== statusFilter) return false;
      if (!term) return true;
      const haystack = [
        host.host?.hostname,
        host.host?.ip_address,
        host.agent_id != null ? String(host.agent_id) : '',
        String(host.host_id),
      ].join(' ').toLowerCase();
      return haystack.includes(term);
    });
  }, [hosts, search, statusFilter]);

  if (discoveryLoading) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#A855F7] mx-auto mb-2"></div>
        <p>Carregando endpoints...</p>
      </div>
    );
  }

  if (discoveryError) {
    return (
      <div className="p-6 text-red-500 bg-red-50/10 rounded-lg border border-red-500/20">
        Erro ao carregar endpoints: {discoveryError}
      </div>
    );
  }

  if (!discovery || discovery.length === 0) {
    return (
      <div className="p-12 text-center text-gray-500">
        <Icon name="server" size="text-5xl" className="mb-3 opacity-50" />
        <p className="text-lg">Nenhum endpoint cadastrado.</p>
      </div>
    );
  }

  const STATUS_LABELS = { online: 'Online', alert: 'Em alerta', offline: 'Offline' };
  const STATUS_CLASSES = {
    online: { text: 'text-green-400', dot: 'bg-green-400' },
    alert: { text: 'text-yellow-400', dot: 'bg-yellow-400' },
    offline: { text: 'text-red-400', dot: 'bg-red-400' },
  };

  return (
    <section>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-[#E2E2E8]">Endpoints</h2>
        <p className="text-sm text-[#A8B3CF]">
          Todos os hosts monitorados pelo agente Munynn.
        </p>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon="server"
          iconColor={{ bg: 'rgba(168, 85, 247, 0.15)', text: 'text-[#A855F7]' }}
          label="Total de Endpoints"
          value={stats.total}
        />
        <StatCard
          icon="online"
          iconColor={{ bg: 'rgba(74, 222, 128, 0.15)', text: 'text-green-400' }}
          label="Online"
          value={stats.online}
        />
        <StatCard
          icon="warning"
          iconColor={{ bg: 'rgba(250, 204, 21, 0.15)', text: 'text-yellow-400' }}
          label="Com Alerta"
          value={stats.alert}
        />
        <StatCard
          icon="offline"
          iconColor={{ bg: 'rgba(148, 163, 184, 0.15)', text: 'text-[#A8B3CF]' }}
          label="Offline"
          value={stats.offline}
        />
      </div>

      {/* Busca e filtro */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex-1 min-w-[240px] relative">
          <Icon name="search" size="text-sm" className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A8B3CF]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por hostname, IP ou ID do agente..."
            className="w-full pl-9 pr-3 py-2.5 rounded-lg text-sm text-[#E2E2E8] placeholder-[#A8B3CF] focus:outline-none"
            style={{ backgroundColor: '#101C35', border: '1px solid #1A2A4A' }}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 rounded-lg text-sm text-[#E2E2E8] focus:outline-none"
          style={{ backgroundColor: '#101C35', border: '1px solid #1A2A4A' }}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="rounded-xl overflow-hidden" style={{ backgroundColor: '#101C35', border: '1px solid #1A2A4A' }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b" style={{ borderColor: '#1A2A4A' }}>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Host</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">IP Primário</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Agent ID</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Host ID</th>
                <th className="text-center p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredHosts.map((host) => {
                const statusClasses = STATUS_CLASSES[host.statusKey];
                return (
                  <tr key={host.host_id} className="border-b transition-colors hover:bg-[#1A1A2E]" style={{ borderColor: '#1A2A4A' }}>
                    <td className="p-4">
                      <div className="flex items-center gap-2.5">
                        <span className={`w-2 h-2 rounded-full ${statusClasses.dot}`}></span>
                        <div>
                          <p className="text-sm font-semibold text-[#E2E2E8]">
                            {host.host?.hostname || `Host ${host.host_id}`}
                          </p>
                          <p className={`text-xs ${statusClasses.text}`}>
                            {host.osLabel} · {STATUS_LABELS[host.statusKey]}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-sm font-mono text-[#A8B3CF]">
                      {host.host?.ip_address || '-'}
                    </td>
                    <td className="p-4 text-sm font-mono text-[#A8B3CF]">
                      {host.agent_id ?? '-'}
                    </td>
                    <td className="p-4 text-sm font-mono text-[#A8B3CF]">
                      {host.host_id}
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Link
                          to={`/details/${host.host_id}`}
                          className="px-3 py-1.5 rounded-lg transition-all duration-200 text-xs font-medium flex items-center gap-1.5"
                          style={{ backgroundColor: '#4B2D6E', color: '#E2E2E8' }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#4B2D6E'}
                        >
                          <Icon name="eye" size="text-sm" />
                          Detalhes
                        </Link>
                        <Link
                          to={`/metrics/${host.host_id}`}
                          title="Métricas"
                          className="p-2 rounded-lg transition-all duration-200"
                          style={{ backgroundColor: '#1A1A2E', color: '#E2E2E8' }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#1A1A2E'}
                        >
                          <Icon name="chart" size="text-sm" />
                        </Link>
                        <Link
                          to={`/logs/${host.host_id}`}
                          title="Logs"
                          className="p-2 rounded-lg transition-all duration-200"
                          style={{ backgroundColor: '#1A1A2E', color: '#E2E2E8' }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#1A1A2E'}
                        >
                          <Icon name="log" size="text-sm" />
                        </Link>
                        <Link
                          to={`/alerts/${host.host_id}`}
                          title={host.alertCount > 0 ? `${host.alertCount} alerta${host.alertCount === 1 ? '' : 's'} ativo${host.alertCount === 1 ? '' : 's'}` : 'Nenhum alerta ativo'}
                          className="relative p-2 rounded-lg transition-all duration-200"
                          style={{ backgroundColor: '#1A1A2E', color: '#E2E2E8' }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#1A1A2E'}
                        >
                          <Icon name="alert" size="text-sm" />
                          {host.alertCount > 0 && (
                            <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center min-w-[16px] h-[16px] px-1 rounded-full bg-yellow-400 text-[#101C35] text-[9px] font-bold">
                              {host.alertCount}
                            </span>
                          )}
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 text-xs text-[#A8B3CF]">
        Mostrando {filteredHosts.length} de {hosts.length} endpoints
      </div>
    </section>
  );
}
