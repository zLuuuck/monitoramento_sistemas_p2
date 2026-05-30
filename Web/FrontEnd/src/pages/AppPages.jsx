import { useOutletContext } from 'react-router-dom';
import { DiscoveryDashboard, MetricCards } from '../components/DiscoveryDashboard';
import { MetricsChart } from '../features/metrics/components/MetricsChart';
import { LogsPanel } from '../features/logs_feat/components/LogsPanel';
import AlertsPanel from '../features/alerts/components/AlertsPanel';
import { Icon } from '../shared/components/Icon';

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
