import { Card } from '../shared/components/Card';

export function MetricsGrid({ metrics }) {
  const ultimaMetrica = metrics[metrics.length - 1];

  if (!ultimaMetrica) return null;

  return (
    <div className="grid grid-cols-4 gap-6 mb-8">
      <Card title="CPU" value={ultimaMetrica.cpu_percent} unit="%" iconName="cpu" color="blue" />
      <Card title="Memória" value={ultimaMetrica.memory_percent} unit="%" iconName="memory" color="green" />
      <Card title="Disco" value={ultimaMetrica.disk_percent ?? '-'} unit="%" iconName="disk" color="yellow" />
      <Card title="Rede" value={ultimaMetrica.net_recv ?? '-'} unit="bytes" iconName="network" color="purple" />
    </div>
  );
}
