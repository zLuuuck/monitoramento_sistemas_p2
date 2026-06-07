import { useOutletContext } from 'react-router-dom';
import { Icon } from '../shared/components/Icon';

export function EndpointsPage() {
  const { discovery, discoveryLoading, discoveryError } = useOutletContext();

  if (discoveryLoading) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
        <p>Carregando endpoints...</p>
      </div>
    );
  }

  if (discoveryError) {
    return (
      <div className="p-6 text-red-500 bg-red-50 rounded-lg">
        Erro ao carregar endpoints: {discoveryError}
      </div>
    );
  }

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Endpoints Monitorados</h2>
        <p className="text-sm text-page opacity-80">
          Lista de todos os hosts e dispositivos monitorados pelo sistema.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        {discovery && discovery.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">ID</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Hostname</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Status</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Tipo</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">IP</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Sistema</th>
                </tr>
              </thead>
              <tbody>
                {discovery.map((item) => (
                  <tr key={item.host_id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="p-4 text-sm text-page">{item.host_id}</td>
                    <td className="p-4 text-sm font-medium text-page">{item.host?.hostname || `Host ${item.host_id}`}</td>
                    <td className="p-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.host?.status === 'online' 
                          ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
                          : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                      }`}>
                        {item.host?.status || 'offline'}
                      </span>
                    </td>
                    <td className="p-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.is_virtualized
                          ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                      }`}>
                        {item.is_virtualized ? 'Virtual' : 'Físico'}
                      </span>
                    </td>
                    <td className="p-4 text-sm font-mono text-page">{item.host?.ip_address || '-'}</td>
                    <td className="p-4 text-sm text-page">{item.operating_system || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-gray-500">
            <Icon name="server" size="text-4xl" className="mb-2 mx-auto" />
            <p>Nenhum endpoint cadastrado</p>
            <p className="text-sm">Os dados do discovery aparecerão aqui automaticamente.</p>
          </div>
        )}
      </div>
    </section>
  );
}