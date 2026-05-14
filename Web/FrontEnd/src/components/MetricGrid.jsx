import { Card } from '../shared/components/Card';

export function MetricsGrid({ metrics }) {
  const ultimaMetrica = metrics[metrics.length - 1];
  
  // Valores mock para Disco e Rede
  const disco = 45.5;
  const rede = 32.3;

  if (!ultimaMetrica) return null;

  return (
    <div className="grid grid-cols-4 gap-6 mb-8">
      <Card title="CPU" value={ultimaMetrica.cpu_percent} unit="%" iconName="cpu" color="blue" />
      <Card title="Memória" value={ultimaMetrica.memory_percent} unit="%" iconName="memory" color="green" />
      <Card title="Disco" value={disco} unit="%" iconName="disk" color="yellow" />
      <Card title="Rede" value={rede} unit="%" iconName="network" color="purple" />
    </div>
  );
}