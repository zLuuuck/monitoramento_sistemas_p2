import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Layout } from './shared/components/Layout';
import { api } from './shared/services/api';
import './App.css';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

//tem que mudar algo aqui pra aquela barra funcionar

// Componente para alternar o tema (pode ficar aqui ou mover para outro arquivo)
function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className="px-3 py-2 rounded-lg border border-gray-300 bg-white dark:bg-gray-800 dark:border-gray-600"
      title={theme === 'light' ? 'Modo escuro' : 'Modo claro'}
    >
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  );
}

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

  useEffect(() => {
    const carregarMetricas = async () => {
      if (!selectedHost) {
        setMetrics([]);
        setLoading(false);
        return;
      }
      setLoading(true);
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

  const hostsDisponiveis = discovery.map((item) => ({
    id: String(item.host_id),
    name: item.host?.hostname || `Host ${item.host_id}`,
    status: item.host?.status || 'offline',
  }));

  const selectedDiscovery = discovery.find((item) => String(item.host_id) === selectedHost);
  const selectedHostInfo = hostsDisponiveis.find((host) => host.id === selectedHost);

  return (
    <ThemeProvider>
      <Layout hostType={selectedDiscovery?.is_virtualized ? 'virtual' : 'physical'}>
        {/* Seletor Global de Host no Topo das Páginas */}
        <div className="flex justify-end mb-6">
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <label className="text-gray-600 dark:text-gray-300 text-sm font-medium">Host:</label>
            <select
              value={selectedHost}
              onChange={(e) => setSelectedHost(e.target.value)}
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 bg-white dark:bg-gray-800 dark:text-white focus:outline-none"
              disabled={hostsDisponiveis.length === 0}
            >
              {hostsDisponiveis.length === 0 && <option value="">Nenhum host</option>}
              {hostsDisponiveis.map((host) => (
                <option key={host.id} value={host.id}>
                  {host.name} {host.status === 'offline' && '(Offline)'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* O Outlet injeta a subpágina da rota atual e distribui os dados compartilhados via context */}
        <Outlet context={{ selectedHost, metrics, loading, metricsError, selectedDiscovery, selectedHostInfo }} />
      </Layout>
    </ThemeProvider>
  );
}

function normalizeMetrics(metrics) {
  return metrics
    .filter((metric) => metric && metric.timestamp)
    .map((metric) => ({
      ...metric,
      cpu_percent: Number(metric.cpu_percent) || null,
      memory_percent: Number(metric.memory_percent) || null,
      disk_percent: Number(metric.disk_percent) || null,
    }));
}

export default App;