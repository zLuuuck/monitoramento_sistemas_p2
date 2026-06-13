// src/components/GaugeCard.jsx
import GaugeComponent from 'react-gauge-component';
import { Icon } from '../shared/components/Icon';

export function GaugeCard({ title, value, unit, icon, color = 'blue' }) {
  // Converte o valor para percentual (garante entre 0 e 100)
  const percent = Math.min(100, Math.max(0, value));
  
  // Cores baseadas na cor escolhida
  const colors = {
    blue: { arc: '#3b82f6', text: '#2563eb' },
    green: { arc: '#22c55e', text: '#16a34a' },
    red: { arc: '#ef4444', text: '#dc2626' },
    yellow: { arc: '#f59e0b', text: '#d97706' },
    purple: { arc: '#a855f7', text: '#9333ea' },
    orange: { arc: '#f97316', text: '#ea580c' },
    pink: { arc: '#ec4899', text: '#db2777' },
  };

  // Cor baseada no valor (se não for especificada)
  const getValueColor = () => {
    if (percent > 80) return { arc: '#ef4444', text: '#dc2626' };
    if (percent > 60) return { arc: '#f59e0b', text: '#d97706' };
    return colors[color] || colors.blue;
  };

  const themeColor = colors[color] || getValueColor();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 text-center transition-all hover:shadow-lg">
      {/* Ícone e Título */}
      <div className="flex items-center justify-center gap-2 mb-3">
        {icon && <Icon name={icon} size="text-lg" />}
        <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">{title}</h3>
      </div>

      {/* Gráfico Gauge (velocímetro) */}
      <div className="flex justify-center">
        <GaugeComponent
          value={percent}
          type="semicircle"
          labels={{
            valueLabel: {
              formatTextValue: (val) => `${Math.round(val)}${unit}`,
              style: { fill: themeColor.text, fontSize: 20, fontWeight: 'bold' },
            },
            tickLabels: {
              type: 'outer',
              defaultTickValueConfig: {
                formatTextValue: (val) => `${val}${unit}`,
                style: { fontSize: 8, fill: '#9ca3af' },
              },
            },
          }}
          arc={{
            colorArray: ['#e5e7eb', themeColor.arc],
            padding: 0.02,
            width: 0.25,
          }}
          pointer={{ type: 'arrow', elastic: true }}
          style={{ width: '100%', height: '140px' }}
        />
      </div>

      {/* Valor numérico */}
      <p className="text-xl font-bold mt-2" style={{ color: themeColor.text }}>
        {Math.round(percent)}{unit}
      </p>
    </div>
  );
}