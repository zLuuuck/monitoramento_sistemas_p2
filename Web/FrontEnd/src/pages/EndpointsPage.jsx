import { useOutletContext } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { Icon } from '../shared/components/Icon';

export function EndpointsPage() {
  const { discovery, discoveryLoading, discoveryError } = useOutletContext();

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

  return (
    <section>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-[#E2E2E8]">Endpoints Monitorados</h2>
        <p className="text-sm text-[#A8B3CF]">
          Lista de todos os hosts e dispositivos monitorados pelo sistema.
        </p>
      </div>

      <div className="rounded-xl overflow-hidden" style={{ backgroundColor: '#101C35', border: '1px solid #1A2A4A' }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b" style={{ borderColor: '#1A2A4A' }}>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">ID</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Hostname</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Status</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Tipo</th>
                <th className="text-left p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">IP</th>
                <th className="text-center p-4 text-xs font-medium uppercase tracking-wide text-[#A8B3CF]">Ações</th>
              </tr>
            </thead>
            <tbody>
              {discovery.map((host) => (
                <tr key={host.host_id} className="border-b transition-colors hover:bg-[#1A1A2E]" style={{ borderColor: '#1A2A4A' }}>
                  <td className="p-4 text-sm text-[#E2E2E8]">{host.host_id}</td>
                  <td className="p-4 text-sm font-medium text-[#E2E2E8]">
                    {host.host?.hostname || `Host ${host.host_id}`}
                  </td>
                  <td className="p-4 text-sm">
                    <span className={`flex items-center gap-1.5 text-xs font-semibold ${
                      host.host?.status === 'online' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      <span className={`w-2 h-2 rounded-full ${
                        host.host?.status === 'online' ? 'bg-green-400' : 'bg-red-400'
                      }`}></span>
                      {host.host?.status === 'online' ? 'Online' : 'Offline'}
                    </span>
                  </td>
                  <td className="p-4 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      host.is_virtualized
                        ? 'bg-purple-500/20 text-white border border-purple-500/30'
                        : 'bg-blue-500/20 text-white border border-blue-500/30'
                    }`}>
                      {host.is_virtualized ? 'Virtual' : 'Físico'}
                    </span>
                  </td>
                  <td className="p-4 text-sm font-mono text-[#A8B3CF]">
                    {host.host?.ip_address || '-'}
                  </td>
                  <td className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link
                        to={`/logs/${host.host_id}`}
                        className="px-3 py-1.5 rounded-lg transition-all duration-200 text-xs font-medium flex items-center gap-1.5"
                        style={{
                          backgroundColor: '#4B2D6E',
                          color: '#E2E2E8'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#4B2D6E'}
                      >
                        <Icon name="log" size="text-sm" />
                        Logs
                      </Link>
                      <Link
                        to={`/alerts/${host.host_id}`}
                        className="px-3 py-1.5 rounded-lg transition-all duration-200 text-xs font-medium flex items-center gap-1.5"
                        style={{
                          backgroundColor: '#4B2D6E',
                          color: '#E2E2E8'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2D2D44'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#4B2D6E'}
                      >
                        <Icon name="alert" size="text-sm" />
                        Alertas
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 text-xs text-[#A8B3CF]">
        Mostrando {discovery.length} de {discovery.length} endpoints
      </div>
    </section>
  );
}