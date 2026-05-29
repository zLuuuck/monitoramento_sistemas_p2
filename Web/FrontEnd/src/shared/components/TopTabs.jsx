import { Icon } from './Icon';

export function TopTabs({ activeSubTab, onSubTabChange, hostType }) {
  const subTabs = [
    { id: 'overview', name: 'Visão Geral', icon: 'info' },
    { id: 'performance', name: 'Desempenho', icon: 'chart' },
    { id: 'hardware', name: 'Hardware', icon: 'physical' },
    { id: 'network', name: 'Rede', icon: 'network' },
  ];

  return ( //da uma olhada aqui tbm, pode ter algo aqui quebrando;
    <div className="border-b border-gray-200 bg-white">
      <div className="flex space-x-8 px-6">
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onSubTabChange(tab.id)}
            className={`flex items-center gap-2 py-4 px-1 border-b-2 transition-colors ${
              activeSubTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Icon name={tab.icon} size="text-sm" />
            <span>{tab.name}</span>
          </button>
        ))}
      </div>
      
      {/* Badge indicador de tipo de hardware */}
      <div className="px-6 py-2 bg-gray-50 border-t border-gray-100 text-xs">
        {hostType === 'physical' ? (
          <span className="flex items-center gap-1 text-blue-600">
            <Icon name="physical" size="text-xs" />
            Hardware Físico
          </span>
        ) : (
          <span className="flex items-center gap-1 text-green-600">
            <Icon name="virtual" size="text-xs" />
            Ambiente Virtualizado
          </span>
        )}
      </div>
    </div>
  );
}