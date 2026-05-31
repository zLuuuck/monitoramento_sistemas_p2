import { useOutletContext } from 'react-router-dom';
import { DiscoveryDashboard, MetricCards } from '../components/DiscoveryDashboard';
import { MetricsChart } from '../features/metrics/components/MetricsChart';
import { LogsPanel } from '../features/logs_feat/components/LogsPanel';
import AlertsPanel from '../features/alerts/components/AlertsPanel';
import { Icon } from '../shared/components/Icon';
import { useTheme } from '../contexts/ThemeContext';

// 1. ABA DASHBOARD (Visão Geral)
export function DashboardPage() {
  const { selectedDiscovery, loading } = useOutletContext();

  if (loading) return <div className="p-6 text-gray-500">Carregando dados do host...</div>;

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Discovery do Host</h2>
        <p className="text-sm text-gray-500">Dados coletados sobre hardware, virtualização e rede.</p>
      </div>
      {selectedDiscovery ? (
        <DiscoveryDashboard discovery={selectedDiscovery} />
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">Nenhum discovery cadastrado.</div>
      )}
    </section>
  );
}

// 2. ABA MÉTRICAS
export function MetricsPage() {
  const { metrics, loading, metricsError, selectedHostInfo } = useOutletContext();

  if (loading) return <div className="p-6 text-gray-500">Carregando gráficos...</div>;
  if (metricsError) return <div className="text-red-500 p-4">{metricsError}</div>;

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Métricas do Host</h2>
        <p className="text-sm text-page opacity-80">
          Gráficos e indicadores de desempenho do host selecionado.
        </p>
      </div>
      <div className="space-y-6">
        {metrics.length > 0 ? (
          <>
            <MetricsChart metrics={metrics} title={`Métricas - ${selectedHostInfo?.name}`} />
            <MetricCards latestMetric={metrics[metrics.length - 1]} />
          </>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">Nenhuma métrica encontrada para este host.</div>
        )}
      </div>
    </section>
  );
}

// 3. ABA LOGS
export function LogsPage() {
  const { selectedHost } = useOutletContext();
  return <LogsPanel hostId={selectedHost} />;
}

// 4. ABA ALERTAS
export function AlertsPage() {
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Alertas de Segurança</h2>
        <p className="text-sm text-page opacity-80">
          Eventos e notificações de segurança detectados no host.
        </p>
      </div>
      <AlertsPanel />
    </section>
  );
}

// 5. ABA ENDPOINTS
export function EndpointsPage() {
  const { discovery, discoveryLoading, discoveryError } = useOutletContext();

  if (discoveryLoading) {
    return <div className="p-6 text-gray-500">Carregando endpoints...</div>;
  }

  if (discoveryError) {
    return <div className="p-6 text-red-500">Erro ao carregar endpoints: {discoveryError}</div>;
  }

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Endpoints Monitorados</h2>
        <p className="text-sm text-page opacity-80">
          Lista de todos os hosts e dispositivos monitorados pelo sistema.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {discovery && discovery.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600">ID</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600">Hostname</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600">Status</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600">Tipo</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600">IP</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600">Sistema</th>
                </tr>
              </thead>
              <tbody>
                {discovery.map((item) => (
                  <tr key={item.host_id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="p-4 text-sm">{item.host_id}</td>
                    <td className="p-4 text-sm font-medium">{item.host?.hostname || `Host ${item.host_id}`}</td>
                    <td className="p-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.host?.status === 'online' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {item.host?.status || 'offline'}
                      </span>
                    </td>
                    <td className="p-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.is_virtualized
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {item.is_virtualized ? 'Virtual' : 'Físico'}
                      </span>
                    </td>
                    <td className="p-4 text-sm font-mono">{item.host?.ip_address || '-'}</td>
                    <td className="p-4 text-sm">{item.operating_system || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-gray-500">
            <Icon name="server" size="text-3xl" className="mb-2" />
            <p>Nenhum endpoint cadastrado</p>
            <p className="text-sm">Os dados do discovery aparecerão aqui automaticamente.</p>
          </div>
        )}
      </div>
    </section>
  );
}

// 6. ABA CONFIGURAÇÕES
export function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Configurações</h2>
        <p className="text-sm text-page opacity-80">
          Configure as preferências do sistema de monitoramento.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card - Aparência */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
            <Icon name="settings" size="text-lg" />
            Aparência
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-page">Tema</p>
              <p className="text-sm text-page opacity-70">Alternar entre tema claro e escuro</p>
            </div>
            <button
              onClick={toggleTheme}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
            >
              {theme === 'light' ? '🌙 Modo escuro' : '☀️ Modo claro'}
            </button>
          </div>
        </div>

        {/* Card - Preferências de Monitoramento */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
            <Icon name="chart" size="text-lg" />
            Monitoramento
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-page">Intervalo de Atualização</p>
                <p className="text-sm text-page opacity-70">Tempo entre cada coleta de métricas</p>
              </div>
              <select className="px-3 py-1 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                <option>10 segundos</option>
                <option>30 segundos</option>
                <option>1 minuto</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-page">Limite de Alertas</p>
                <p className="text-sm text-page opacity-70">Alertar quando CPU ultrapassar</p>
              </div>
              <select className="px-3 py-1 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                <option>80%</option>
                <option>85%</option>
                <option>90%</option>
              </select>
            </div>
          </div>
        </div>

        {/* Card - Notificações */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
            <Icon name="alert" size="text-lg" />
            Notificações
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-page">Alertas por Email</p>
                <p className="text-sm text-page opacity-70">Receber notificações por email</p>
              </div>
              <button className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded-lg text-sm">Desativado</button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-page">Notificações no Desktop</p>
                <p className="text-sm text-page opacity-70">Alertas pop-up no navegador</p>
              </div>
              <button className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm">Ativado</button>
            </div>
          </div>
        </div>

        {/* Card - Sobre */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
            <Icon name="info" size="text-lg" />
            Sobre o Sistema
          </h3>
          <div className="space-y-2 text-sm text-page opacity-80">
            <p><strong>Monitoramento P2</strong> - Sistema de monitoramento de endpoints</p>
            <p>Versão: 2.0.0</p>
            <p>Frontend: React + Vite + Tailwind</p>
            <p className="pt-2 text-xs">© 2026 - Projeto de Monitoramento</p>
          </div>
        </div>
      </div>
    </section>
  );
}