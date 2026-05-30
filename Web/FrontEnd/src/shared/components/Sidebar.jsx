import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Icon } from './Icon';

export function Sidebar({ activeTab }) {
  const [isMinimized, setIsMinimized] = useState(false);

  useEffect(() => {
    const savedState = localStorage.getItem('sidebarMinimized');
    if (savedState !== null) {
      setIsMinimized(savedState === 'true');
    }
  }, []);

  const toggleSidebar = () => {
    const newState = !isMinimized;
    setIsMinimized(newState);
    localStorage.setItem('sidebarMinimized', newState);
  };

  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: 'dashboard', path: '/dashboard' },
    { id: 'metrics', name: 'Métricas', icon: 'chart', path: '/metrics' },
    { id: 'logs', name: 'Logs', icon: 'log', path: '/logs' },
    { id: 'alerts', name: 'Alertas', icon: 'alert', path: '/alerts' },
    { id: 'endpoints', name: 'Endpoints', icon: 'server', path: '/endpoints' },
    { id: 'settings', name: 'Configurações', icon: 'settings', path: '/settings' },
  ];

  return (
    <aside
      className={`flex flex-col transition-all duration-300 ease-in-out ${
        isMinimized ? 'w-20' : 'w-64'
      }`}
      style={{ backgroundColor: 'var(--sidebar-bg)', color: 'var(--text-page)' }}
    >
      <div
        className={`p-4 border-b flex items-center ${
          isMinimized ? 'justify-center' : 'justify-between'
        }`}
        style={{ borderColor: 'var(--card-border)' }}
      >
        {!isMinimized && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <Icon name="dashboard" size="text-sm" />
            </div>
            <span className="font-bold text-lg">Monitor</span>
          </div>
        )}
        {isMinimized && (
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <Icon name="dashboard" size="text-sm" />
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="text-gray-400 hover:text-white transition-colors p-1 rounded"
          style={{ color: 'var(--text-page)' }}
          title={isMinimized ? 'Expandir menu' : 'Minimizar menu'}
        >
          <Icon name={isMinimized ? 'expand' : 'minimize'} size="text-base" />
        </button>
      </div>

      <nav className="flex-1 py-6">
        <ul className="space-y-1">
          {menuItems.map((item) => (
            <li key={item.id}>
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 transition-all duration-200 ${
                  activeTab === item.id
                    ? 'bg-blue-600 text-white border-r-4 border-blue-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                } ${isMinimized ? 'justify-center' : ''}`}
                title={isMinimized ? item.name : ''}
                style={{
                  backgroundColor: activeTab === item.id ? '#2563eb' : undefined,
                  color: activeTab === item.id ? 'white' : 'var(--text-page)',
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== item.id) {
                    e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== item.id) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <Icon name={item.icon} size="text-lg" />
                {!isMinimized && <span className="text-sm">{item.name}</span>}
                {item.id === 'alerts' && !isMinimized && (
                  <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
                    3
                  </span>
                )}
                {item.id === 'alerts' && isMinimized && (
                  <span className="ml-auto w-2 h-2 bg-red-500 rounded-full"></span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t" style={{ borderColor: 'var(--card-border)' }}>
        {!isMinimized ? (
          <div className="p-4">
            <div className="text-xs text-center mb-3" style={{ color: 'var(--text-page)', opacity: 0.7 }}>
              Monitoramento P2
            </div>
            <div className="flex items-center justify-center gap-2 text-xs">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span style={{ color: 'var(--text-page)' }}>Sistema Online</span>
            </div>
          </div>
        ) : (
          <div className="p-4 flex justify-center">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
        )}
      </div>
    </aside>
  );
}