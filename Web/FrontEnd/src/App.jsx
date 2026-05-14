import { useState } from 'react';
import './App.css'
import { useEffect } from 'react';
import { Layout } from './shared/components/Layout';
import { Card } from './shared/components/Card';
import { LogsPlaceholder } from './features/logs_feat/components/LogsPlaceholder';
import { MetricsChart } from './features/metrics/components/MetricsChart';
import { mockApi, mockHosts } from './shared/services/mockApi';
import { api } from './shared/services/api';
import { Icon } from './shared/components/Icon';
import { HostSelector } from './components/HostSelector';
import { MetricsGrid } from './components/MetricsGrid';
import { HeaderInfo } from './components/HeaderInfo';
import { EndpointModal } from './modals/EndpointModal';

function App() {
  const [selectedHost, setSelectedHost] = useState('1');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const currentHost = mockHosts.find(h => h.id === selectedHost);
  const getHostType = (id) => ['1', '2'].includes(id) ? 'physical' : 'virtual';

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const dados = await mockApi.getMetrics(selectedHost);
      setMetrics(dados);
      setLoading(false);
    };
    load();
  }, [selectedHost]);

  const handleVerMais = () => {
    const ultimaMetrica = metrics[metrics.length - 1];
    setEndpointDetails({
      id: currentHost.id,
      name: currentHost.name,
      status: currentHost.status,
      ip: currentHost.ip,
      type: getHostType(selectedHost),
      metrics: ultimaMetrica,
      lastUpdate: new Date().toLocaleString('pt-BR'),
    });
    setShowModal(true);
  };

  const [endpointDetails, setEndpointDetails] = useState(null);

  return (
    <Layout hostType={getHostType(selectedHost)}>
      
      <HeaderInfo host={currentHost} type={getHostType(selectedHost)} onVerMais={handleVerMais} />
      
      <div className="flex justify-end mb-6">
        <HostSelector hosts={mockHosts} selectedHost={selectedHost} onSelect={setSelectedHost} />
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div></div>
      ) : (
        <>
          {metrics.length > 0 && <MetricsChart metrics={metrics} title={`Evolução - ${currentHost?.name}`} />}
          <MetricsGrid metrics={metrics} />
          <LogsPlaceholder />
        </>
      )}

      <EndpointModal data={endpointDetails} onClose={() => setShowModal(false)} />
      
    </Layout>
  );
}

export default App;
