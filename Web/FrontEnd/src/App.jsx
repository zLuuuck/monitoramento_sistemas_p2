import { useState } from 'react';
import './App.css'
import { useEffect } from 'react';
import { Layout } from './shared/components/Layout';
import { Card } from './shared/components/Card';
import { LogsPlaceholder } from './features/logs_feat/components/LogsPlaceholder';
import { MetricsChart } from './features/metrics/components/MetricsChart';
import { mockApi, mockHosts } from './shared/services/mockApi';

function App() {
  const [selectedHost, setSelectedHost] = useState('1');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

 // Determina tipo de hardware do host selecionado
  const getHostType = (hostId) => {
    const physicalHosts = ['1', '2'];  // Servidor Principal, Web
    return physicalHosts.includes(hostId) ? 'physical' : 'virtual';
  };

  // Carregar métricas quando mudar o host
  useEffect(() => {
    const carregarMetricas = async () => {
      setLoading(true);
      const dados = await mockApi.getMetrics(selectedHost);
      setMetrics(dados);
      setLoading(false);
    };
    carregarMetricas();
  }, [selectedHost]);

  // Pega a última métrica (mais recente)
  const ultimaMetrica = metrics[metrics.length - 1];

  return (
   <Layout hostType={getHostType(selectedHost)}>
      {/* Seletor de Host */}
      <div className="flex justify-end mb-6">
        <div className="flex items-center gap-3">
          <label className="text-gray-600 text-sm font-medium">Host:</label>
          <select
            value={selectedHost}
            onChange={(e) => setSelectedHost(e.target.value)}
            className="border border-gray-300 rounded-lg px-4 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {mockHosts.map((host) => (
              <option key={host.id} value={host.id}>
                {host.name} {host.status === 'offline' && '(Offline)'}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* GRÁFICO */}
      {!loading && metrics.length > 0 && (
        <div className="mb-8">
          <MetricsChart 
            metrics={metrics} 
            title={`Métricas - ${mockHosts.find(h => h.id === selectedHost)?.name}`}
          />
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Cards de Métricas */}
     {!loading && ultimaMetrica && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card 
            title="CPU" 
            value={ultimaMetrica.cpu_percent.toFixed(1)} 
            unit="%" 
            iconName="cpu" 
            color="blue" 
          />
          <Card 
            title="Memória" 
            value={ultimaMetrica.memory_percent.toFixed(1)} 
            unit="%" 
            iconName="memory" 
            color="green" 
          />
          <Card 
            title="Status" 
            value={mockHosts.find(h => h.id === selectedHost)?.status === 'online' ? "Online" : "Offline"} 
            unit="" 
            iconName={mockHosts.find(h => h.id === selectedHost)?.status === 'online' ? "online" : "offline"} 
            color={mockHosts.find(h => h.id === selectedHost)?.status === 'online' ? "green" : "red"} 
          />
        </div>
      )}

      {/* Logs */}
      <LogsPlaceholder />
    </Layout>
  );
}

export default App;