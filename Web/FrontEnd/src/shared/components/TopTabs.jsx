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
                ? 'border-purple-500 text-purple-500'
                : 'border-transparent text-gray-500 hover:text-purple-400'
            }`}
            style={{ color: activeSubTab === tab.id ? undefined : 'var(--text-page)' }}
          >
            <Icon name={tab.icon} size="text-sm" />
            <span>{tab.name}</span>
          </button>
        ))}
      </div>
      
      {/* Badge sem linha (border-t removido) */}
      <div className="px-6 py-2" style={{ backgroundColor: 'var(--bg-page)' }}>
        {hostType === 'physical' ? (
          <span className="flex items-center gap-1 text-purple-500">  {/* ← ROXO */}
            <Icon name="physical" size="text-xs" />
            Hardware Físico
          </span>
        ) : (
          <span className="flex items-center gap-1 text-purple-500">  {/* ← ROXO também */}
            <Icon name="virtual" size="text-xs" />
            Ambiente Virtualizado
          </span>
        )}
      </div>
    </div>
  );
}