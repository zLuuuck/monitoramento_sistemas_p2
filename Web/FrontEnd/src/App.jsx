import { Component, useState } from 'react';
import './App.css'
import { useEffect } from 'react';
import { Layout } from './shared/components/Layout';
import { LogsPlaceholder } from './features/logs_feat/components/LogsPlaceholder';
import { MetricsChart } from './features/metrics/components/MetricsChart';
import { api } from './shared/services/api';
import { DiscoveryDashboard, MetricCards } from './components/DiscoveryDashboard';

function App() {
  const [selectedHost, setSelectedHost] = useState('');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metricsError, setMetricsError] = useState('');
  const [discovery, setDiscovery] = useState([]);
  const [discoveryLoading, setDiscoveryLoading] = useState(true);
  const [discoveryError, setDiscoveryError] = useState('');

  useEffect(() => {
    const carregarDiscovery = async () => {
      try {
        setDiscoveryLoading(true);
        setDiscoveryError('');
        const dados = await api.getDiscovery();
        setDiscovery(dados);

        if (dados.length > 0) {
          setSelectedHost((currentHost) => currentHost || String(dados[0].host_id));
        }
      } catch (error) {
        setDiscoveryError(error.message);
      } finally {
        setDiscoveryLoading(false);
      }
    };

    carregarDiscovery();
  }, []);

  // Carregar métricas quando mudar o host
  useEffect(() => {
    const carregarMetricas = async () => {
      if (!selectedHost) {
        setMetrics([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      setMetricsError('');

      try {
        const resposta = await api.getMetrics(selectedHost);
        const dados = Array.isArray(resposta?.metrics) ? resposta.metrics : [];
        setMetrics(normalizeMetrics(dados));
      } catch (error) {
        setMetrics([]);
        setMetricsError(error.message);
      } finally {
        setLoading(false);
      }
    };
    carregarMetricas();
  }, [selectedHost]);

  // Pega a última métrica (mais recente)
  const ultimaMetrica = metrics[metrics.length - 1];
  const hostsDisponiveis = discovery.length > 0
    ? discovery.map((item) => ({
        id: String(item.host_id),
        name: item.host?.hostname || `Host ${item.host_id}`,
        status: item.host?.status || 'offline',
        ip: item.host?.ip_address,
      }))
    : [];
  const selectedDiscovery = discovery.find((item) => String(item.host_id) === selectedHost);
  const selectedHostInfo = hostsDisponiveis.find((host) => host.id === selectedHost);

  return (
    <Layout hostType={selectedDiscovery?.is_virtualized ? 'virtual' : 'physical'}>
      {/* Seletor de Host */}
      <div className="flex justify-end mb-6">
        <div className="flex items-center gap-3">
          <label className="text-gray-600 text-sm font-medium">Host:</label>
          <select
            value={selectedHost}
            onChange={(e) => setSelectedHost(e.target.value)}
            className="border border-gray-300 rounded-lg px-4 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={hostsDisponiveis.length === 0}
          >
            {hostsDisponiveis.length === 0 && (
              <option value="">Nenhum host</option>
            )}
            {hostsDisponiveis.map((host) => (
              <option key={host.id} value={host.id}>
                {host.name} {host.status === 'offline' && '(Offline)'}
              </option>
            ))}
          </select>
        </div>
      </div>

      <MetricsErrorBoundary key={selectedHost}>
        {/* GRÁFICO - NOVO! */}
        {!loading && metrics.length > 0 && (
          <div className="mb-8">
            <MetricsChart
              metrics={metrics}
              title={`Métricas - ${selectedHostInfo?.name || 'Host selecionado'}`}
            />
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
          </div>
        )}

        {!loading && metricsError && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            Nao foi possivel carregar as metricas: {metricsError}
          </div>
        )}

        {!loading && selectedHost && !metricsError && metrics.length === 0 && (
          <div className="mb-6 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">
            Nenhuma metrica cadastrada para este host ainda.
          </div>
        )}

        {/* Cards de Métricas */}
        {!loading && ultimaMetrica && (
          <MetricCards latestMetric={ultimaMetrica} />
        )}
      </MetricsErrorBoundary>

      {/* Discovery */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-800">Discovery do Host</h2>
            <p className="text-sm text-gray-500">
              Dados coletados pelo agente sobre hardware, virtualização e rede.
            </p>
          </div>
        </div>

        {discoveryLoading && (
          <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">
            Carregando dados de discovery...
          </div>
        )}

        {!discoveryLoading && discoveryError && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
            Nao foi possivel carregar o discovery: {discoveryError}
          </div>
        )}

        {!discoveryLoading && !discoveryError && !selectedDiscovery && (
          <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">
            Nenhum discovery cadastrado ainda.
          </div>
        )}

        {!discoveryLoading && selectedDiscovery && (
          <DiscoveryDashboard discovery={selectedDiscovery} />
        )}
      </section>

      {/* Logs */}
      <LogsPlaceholder />
    </Layout>
  );
}

function normalizeMetrics(metrics) {
  return metrics
    .filter((metric) => metric && metric.timestamp)
    .map((metric) => ({
      ...metric,
      cpu_percent: toNumber(metric.cpu_percent),
      memory_percent: toNumber(metric.memory_percent),
      disk_percent: toNumber(metric.disk_percent),
      net_sent: toNumber(metric.net_sent),
      net_recv: toNumber(metric.net_recv),
    }));
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

class MetricsErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          O painel de metricas encontrou dados inesperados, mas o restante do dashboard continua disponivel.
        </div>
      );
    }

    return this.props.children;
  }
}

export default App;
