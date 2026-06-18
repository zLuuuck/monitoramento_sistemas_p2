import { useOutletContext } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { Icon } from '../shared/components/Icon';

export function DashboardPage() {
  const { discovery, discoveryLoading, discoveryError } = useOutletContext();

  if (discoveryLoading) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#A855F7] mx-auto mb-2"></div>
        <p>Carregando hosts...</p>
      </div>
    );
  }

  if (discoveryError) {
    return (
      <div className="p-6 text-red-500 bg-red-50/10 rounded-lg border border-red-500/20">
        Erro ao carregar hosts: {discoveryError}
      </div>
    );
  }

  if (!discovery || discovery.length === 0) {
    return (
      <div className="p-12 text-center text-gray-500">
        <Icon name="server" size="text-5xl" className="mb-3 opacity-50" />
        <p className="text-lg">Nenhum host cadastrado.</p>
      </div>
    );
  }

  return (
    <section>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-[#E2E2E8]">Dashboard</h2>
        <p className="text-sm text-[#A8B3CF]">
          Visão geral de todos os hosts monitorados
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {discovery.map((host) => (
          <div
            key={host.host_id}
            className="rounded-xl p-5 transition-all duration-300 hover:shadow-xl"
            style={{
              backgroundColor: '#101C35',
              border: '1px solid #1A2A4A',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
            }}
          >
            {/* Nome + Status */}
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-lg font-bold text-[#E2E2E8]">
                  {host.host?.hostname || `Host ${host.host_id}`}
                </h3>
                <p className="text-sm text-[#A8B3CF]">
                  {host.host?.ip_address || 'IP não informado'}
                </p>
              </div>
              <span className={`flex items-center gap-1.5 text-xs font-semibold ${host.host?.status === 'online' ? 'text-green-400' : 'text-red-400'
                }`}>
                <span className={`w-2 h-2 rounded-full ${host.host?.status === 'online' ? 'bg-green-400' : 'bg-red-400'
                  }`}></span>
                {host.host?.status === 'online' ? 'Online' : 'Offline'}
              </span>
            </div>

            {/* Cards internos — IDs em cima, métricas embaixo */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* Host ID */}
              <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#2D2D44' }}>
                <p className="text-[#A8B3CF] text-xs uppercase tracking-wide">Host ID</p>
                <p className="text-[#E2E2E8] text-xl font-bold">{host.host_id}</p>
                <p className="text-[#A8B3CF] text-xs">Identificador</p>
              </div>

              {/* Agente */}
              <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#2D2D44' }}>
                <p className="text-[#A8B3CF] text-xs uppercase tracking-wide">Agente</p>
                <p className="text-[#E2E2E8] text-xl font-bold">{host.agent_id ?? '-'}</p>
                <p className="text-[#A8B3CF] text-xs">ID do agente</p>
              </div>

              {/* CPU */}
              <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#2D2D44' }}>
                <p className="text-[#A8B3CF] text-xs uppercase tracking-wide">CPU</p>
                <p className="text-[#E2E2E8] text-xl font-bold">{host.cpu_cores || 0}</p>
                <p className="text-[#A8B3CF] text-xs">vCPUs</p>
              </div>

              {/* RAM */}
              <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#2D2D44' }}>
                <p className="text-[#A8B3CF] text-xs uppercase tracking-wide">RAM</p>
                <p className="text-[#E2E2E8] text-xl font-bold">{host.total_memory_gb || 0}</p>
                <p className="text-[#A8B3CF] text-xs">GB</p>
              </div>
            </div>

            {/* Botões */}
            <div className="flex gap-2">
              <Link
                to={`/details/${host.host_id}`}
                className="flex-1 text-center px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium flex items-center justify-center gap-2"
                style={{
                  backgroundColor: '#4B2D6E',
                  color: '#E2E2E8'  // ← Branco suave
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#4B2D6E'}
              >
                <Icon name="info" size="text-sm" />
                Details
              </Link>
              <Link
                to={`/metrics/${host.host_id}`}
                className="flex-1 text-center px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium flex items-center justify-center gap-2"
                style={{
                  backgroundColor: '#4B2D6E',
                  color: '#E2E2E8'  // ← Branco suave
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#4B2D6E'}
              >
                <Icon name="chart" size="text-sm" />
                Métricas
              </Link>
            </div>

          </div>
        ))}
      </div>
    </section>
  );
}