import AlertsPanel from '../features/alerts/components/AlertsPanel';

export function AlertsPage() {
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Alertas de Segurança</h2>
        <p className="text-sm text-page opacity-80">
          Eventos e notificações de segurança detectados no host.
        </p>
      </div>
      <AlertsPanel />
    </section>
  );
}