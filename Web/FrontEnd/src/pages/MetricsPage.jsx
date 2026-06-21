// src/pages/MetricsPage.jsx
import { useOutletContext } from 'react-router-dom';
import { MetricCards } from '../components/DiscoveryDashboard';
import { MetricsChart } from '../features/metrics/components/MetricsChart';
import { GaugeCard } from '../components/GaugeCard';
import { Icon } from '../shared/components/Icon';

export function MetricsPage() {
  const { metrics, loading, metricsError, selectedHostInfo } = useOutletContext();

  if (loading) return <div className="p-6 text-gray-500">Carregando gráficos...</div>;
  if (metricsError) return <div className="text-red-500 p-4">{metricsError}</div>;

  // Pega a última métrica (valor atual)
  const ultimaMetrica = metrics[metrics.length - 1];

  const discoPercent = ultimaMetrica?.disk_percent || ultimaMetrica?.disk_io || 0;

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Métricas do Host</h2>
        <p className="text-sm text-page opacity-80">
          Indicadores de desempenho em tempo real e histórico do host selecionado.
        </p>
      </div>

      {/* GAUGES - Valor Atual (em tempo real) */}
      {!loading && ultimaMetrica && (
        <div className="mb-6">
          <h3 className="text-md font-semibold text-page mb-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            Status em Tempo Real
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <GaugeCard
              title="CPU"
              value={ultimaMetrica.cpu_percent || 0}
              unit="%"
              icon="cpu"
              color="blue"
            />
            <GaugeCard
              title="Memória"
              value={ultimaMetrica.memory_percent || 0}
              unit="%"
              icon="memory"
              color="green"
            />
            <GaugeCard
              title="Disco"
              value={discoPercent}
              unit="%"
              icon="disk"
              color="orange"
            />
          </div>
        </div>
      )}

      {/* GRÁFICO DE LINHA - Histórico */}
      <div className="space-y-6">
        {metrics.length > 0 ? (
          <>
            <div>
              <h3 className="... flex items-center gap-2">
                <Icon name="bezier" size="text-lg" />
                Histórico de Métricas
              </h3>
              <MetricsChart metrics={metrics} title={`Evolução - ${selectedHostInfo?.name}`} />
            </div>

            {/* Cards com valores detalhados (opcional - pode remover se quiser) */}
            <MetricCards latestMetric={ultimaMetrica} />
          </>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">
            Nenhuma métrica encontrada para este host.
          </div>
        )}
      </div>
    </section>
  );
}