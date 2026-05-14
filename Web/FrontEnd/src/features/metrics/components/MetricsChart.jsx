import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Registrar os componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export function MetricsChart({ metrics, title }) {
  // Se não tem dados, mostra mensagem
  if (!metrics || metrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-400">
        Nenhum dado disponível para exibir no gráfico
      </div>
    );
  }

  // Preparar os dados para o gráfico
  const data = {
    labels: metrics.map(m => {
      const date = new Date(m.timestamp);
      return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }),
    datasets: [
      {
        label: 'CPU (%)',
        data: metrics.map(m => Number(m.cpu_percent || 0)),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Memória (%)',
        data: metrics.map(m => Number(m.memory_percent || 0)),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.3,
        fill: true,
      },
    ],
  };

  // Configurações do gráfico
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    animations: false,
    transitions: {
      active: {
        animation: {
          duration: 0,
        },
      },
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: title || 'Métricas em Tempo Real',
        font: {
          size: 16,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${Number(context.raw || 0).toFixed(1)}%`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Uso (%)',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Horário',
        },
      },
    },
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="h-96">
        <Line data={data} options={options} updateMode="none" />
      </div>
    </div>
  );
}
