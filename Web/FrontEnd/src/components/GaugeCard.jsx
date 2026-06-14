// src/components/GaugeCard.jsx
import GaugeComponent from 'react-gauge-component';
import { Icon } from '../shared/components/Icon';

export function GaugeCard({ title, value, unit, icon }) {
    const percent = Math.min(100, Math.max(0, value));

    //  CORES POR ESTADO DE SAÚDE
    const getColorByValue = (val) => {
        if (val > 80) return { arc: '#ef4444', text: '#dc2626' };  // Vermelho - Instável
        if (val > 60) return { arc: '#f97316', text: '#ea580c' };  // Laranja - Atenção
        return { arc: '#22c55e', text: '#16a34a' };                // Verde - Normal
    };

    const themeColor = getColorByValue(percent);

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 text-center transition-all hover:shadow-lg">
            <div className="flex items-center justify-center gap-2 mb-3">
                {icon && <Icon name={icon} size="text-lg" />}
                <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">{title}</h3>
            </div>

            <div className="flex justify-center">
                <GaugeComponent
                    value={percent}
                    type="semicircle"
                    labels={{
                        valueLabel: {
                            formatTextValue: (val) => {
                                if (val > 80) return 'Instável';
                                if (val > 60) return 'Atenção';
                                return 'Normal';
                            },
                            style: { fill: themeColor.text, fontSize: 14, fontWeight: 'bold' },
                        },
                        tickLabels: {
                            type: 'outer',
                            defaultTickValueConfig: {
                                formatTextValue: (val) => `${val}${unit}`,
                                style: { fontSize: 8, fill: '#9ca3af' },
                            },
                        },
                    }
                    }
                    arc={{
                        colorArray: ['#e5e7eb', themeColor.arc],
                        padding: 0.02,
                        width: 0.25,
                    }}
                    pointer={{ type: 'arrow', elastic: true }}
                    style={{ width: '100%', height: '140px' }}
                />
            </div>

            <p className="text-xl font-bold mt-2" style={{ color: themeColor.text }}>
                {Math.round(percent)}{unit}
            </p>
        </div>
    );
}