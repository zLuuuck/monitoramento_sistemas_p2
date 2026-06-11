import { useOutletContext } from 'react-router-dom';
import { DiscoveryDashboard, MetricCards } from '../components/DiscoveryDashboard';
import { MetricsChart } from '../features/metrics/components/MetricsChart';

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
          <div className="bg-card rounded-lg shadow-md p-6 text-page opacity-70">Nenhuma métrica encontrada para este host.</div>
        )}
      </div>
    </section>
  );
}