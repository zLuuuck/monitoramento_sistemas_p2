import { useState } from 'react'
import './App.css'
import { useEffect } from 'react';
import { Layout } from './shared/components/Layout';
import { Card } from './shared/components/Card';
import { LogsPlaceholder } from './features/logs_feat/components/LogsPlaceholder';
import { mockApi, mockHosts } from './shared/services/mockApi';

function App() {
  const [selectedHost, setSelectedHost] = useState('1');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

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
    <Layout>
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
            icon="⚡" 
            color="blue" 
          />
          <Card 
            title="Memória" 
            value={ultimaMetrica.memory_percent.toFixed(1)} 
            unit="%" 
            icon="🧠" 
            color="green" 
          />
          <Card 
            title="Status" 
            value={mockHosts.find(h => h.id === selectedHost)?.status === 'online' ? "Online" : "Offline"} 
            unit="" 
            icon={mockHosts.find(h => h.id === selectedHost)?.status === 'online' ? "🟢" : "🔴"} 
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