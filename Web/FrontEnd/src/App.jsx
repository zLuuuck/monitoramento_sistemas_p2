import { useState, useEffect, useCallback } from 'react';
import { Layout } from './shared/components/Layout';
import { api, saveApiKey, loginWithPassword } from './shared/services/api';
import './App.css';
import { Outlet, useParams } from 'react-router-dom';

function LoginModal({ onSuccess }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await loginWithPassword(password);
      saveApiKey(data.api_key);
      onSuccess();
    } catch (err) {
      setError(err.message || 'Senha inválida');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-8 w-full max-w-sm">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">Acesso ao Painel</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Digite a senha do painel para continuar.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            autoFocus
            placeholder="Senha do painel"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={loading || !password}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
          >
            {loading ? 'Verificando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
}

function App() {
  const { hostId: routeHostId } = useParams();
  const [selectedHost, setSelectedHost] = useState('');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metricsError, setMetricsError] = useState('');
  const [discovery, setDiscovery] = useState([]);
  const [discoveryLoading, setDiscoveryLoading] = useState(true);
  const [discoveryError, setDiscoveryError] = useState('');
  const [authRequired, setAuthRequired] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const carregarDiscovery = useCallback(async () => {
    try {
      setDiscoveryLoading(true);
      const dados = await api.getDiscovery();
      setDiscovery(dados);
      setAuthRequired(false);
      if (dados.length > 0) {
        setSelectedHost((currentHost) => currentHost || String(dados[0].host_id));
      }
    } catch (error) {
      if (error.message === 'AUTH_REQUIRED') {
        setAuthRequired(true);
      } else {
        setDiscoveryError(error.message);
      }
    } finally {
      setDiscoveryLoading(false);
    }
  }, []);

  useEffect(() => { carregarDiscovery(); }, [carregarDiscovery, reloadKey]);

  // O host da URL (botões "Details"/"Métricas" do Dashboard) tem prioridade
  // sobre o fallback interno — sem isso, todo card de host abria os mesmos dados.
  const effectiveHost = routeHostId || selectedHost;

  useEffect(() => {
    const carregarMetricas = async () => {
      if (!effectiveHost) {
        setMetrics([]);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const resposta = await api.getMetrics(effectiveHost);
        const dados = Array.isArray(resposta?.metrics) ? resposta.metrics : [];
        setMetrics(normalizeMetrics(dados));
        setAuthRequired(false);
      } catch (error) {
        setMetrics([]);
        if (error.message === 'AUTH_REQUIRED') {
          setAuthRequired(true);
        } else {
          setMetricsError(error.message);
        }
      } finally {
        setLoading(false);
      }
    };

    // Carrega imediatamente
    carregarMetricas();

    // POLLING: atualiza a cada 10 segundos
    const intervalId = setInterval(carregarMetricas, 10000);

    // Limpa o intervalo quando o componente desmontar ou dependências mudarem
    return () => clearInterval(intervalId);
  }, [effectiveHost, reloadKey]);

  const hostsDisponiveis = discovery.map((item) => ({
    id: String(item.host_id),
    name: item.host?.hostname || `Host ${item.host_id}`,
    status: item.host?.status || 'offline',
  }));

  const selectedDiscovery = discovery.find((item) => String(item.host_id) === effectiveHost);
  const selectedHostInfo = hostsDisponiveis.find((host) => host.id === effectiveHost);

  return (
    <>
      {authRequired && (
        <LoginModal onSuccess={() => {
          setAuthRequired(false);
          setReloadKey((k) => k + 1);
        }} />
      )}
      <Layout hostType={selectedDiscovery?.is_virtualized ? 'virtual' : 'physical'}>
        <Outlet context={{ selectedHost: effectiveHost, metrics, loading, metricsError, selectedDiscovery, selectedHostInfo, discovery, discoveryLoading, discoveryError }} />
      </Layout>
    </>
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