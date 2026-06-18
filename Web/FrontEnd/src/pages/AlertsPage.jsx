import { useParams, useOutletContext } from 'react-router-dom';
import AlertsPanel from '../features/alerts/components/AlertsPanel';

export function AlertsPage() {
  const { hostId } = useParams();
  const { discovery } = useOutletContext();

  const hostInfo = hostId
    ? discovery?.find((item) => String(item.host_id) === hostId)
    : null;
  const hostName = hostInfo?.host?.hostname || (hostId ? `Host ${hostId}` : null);

  const hostNames = (discovery || []).reduce((acc, item) => {
    acc[item.host_id] = item.host?.hostname || `Host ${item.host_id}`;
    return acc;
  }, {});

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">
          {hostId ? `Alertas — ${hostName}` : 'Alertas Gerais'}
        </h2>
        <p className="text-sm text-page opacity-80">
          {hostId
            ? `Eventos e notificações de segurança detectados em ${hostName}.`
            : 'Eventos e notificações de segurança detectados em todos os hosts.'}
        </p>
      </div>
      <AlertsPanel hostId={hostId} hostNames={hostId ? null : hostNames} />
    </section>
  );
}