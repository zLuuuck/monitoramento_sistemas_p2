import { Icon } from './Icon';

export function Sidebar({ activeTab, onTabChange }) {
  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: 'dashboard' },
    { id: 'metrics', name: 'Métricas', icon: 'chart' },
    { id: 'logs', name: 'Logs', icon: 'log' },
    { id: 'alerts', name: 'Alertas', icon: 'alert' },
    { id: 'endpoints', name: 'Endpoints', icon: 'server' },
    { id: 'config', name: 'Configurações', icon: 'settings' },
  ];

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Logo / Título */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Icon name="dashboard" size="text-2xl" />
          <span className="font-bold text-xl">Monitor</span>
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 py-6">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-6 py-3 transition-colors ${
                  activeTab === item.id
                    ? 'bg-blue-600 text-white border-l-4 border-blue-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon name={item.icon} size="text-lg" />
                <span>{item.name}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer do menu */}
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500 text-center">
        Monitoramento P2
      </div>
    </aside>
  );
}