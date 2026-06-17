import { useOutletContext } from 'react-router-dom';
import { DiscoveryDashboard, MetricCards } from '../components/DiscoveryDashboard';

export function DetailsPage() {
  const { selectedDiscovery, loading } = useOutletContext();

  if (loading) return <div className="p-6 text-gray-500">Carregando dados do host...</div>;

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Discovery do Host</h2>
        <p className="text-sm text-page opacity-80">Dados coletados sobre hardware, virtualização e rede.</p>
      </div>
      {selectedDiscovery ? (
        <DiscoveryDashboard discovery={selectedDiscovery} />
      ) : (
        <div className="bg-card rounded-lg shadow-md p-6 text-page opacity-70">Nenhum discovery cadastrado.</div>
      )}
    </section>
  );
}
