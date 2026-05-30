import { Icon } from './Icon';

export function TopTabs({ activeSubTab, onSubTabChange, hostType }) {
  const subTabs = [
    { id: 'overview', name: 'Visão Geral', icon: 'info' },
    { id: 'performance', name: 'Desempenho', icon: 'chart' },
    { id: 'hardware', name: 'Hardware', icon: 'physical' },
    { id: 'network', name: 'Rede', icon: 'network' },
  ];

  return (
    <div style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--card-border)' }} className="border-b">
      <div className="flex space-x-8 px-6">
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onSubTabChange(tab.id)}
            className={`flex items-center gap-2 py-4 px-1 border-b-2 transition-colors ${
              activeSubTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            style={{ color: activeSubTab === tab.id ? undefined : 'var(--text-page)' }}
          >
            <Icon name={tab.icon} size="text-sm" />
            <span>{tab.name}</span>
          </button>
        ))}
      </div>
      
      <div className="px-6 py-2 border-t" style={{ backgroundColor: 'var(--bg-page)', borderColor: 'var(--card-border)' }}>
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