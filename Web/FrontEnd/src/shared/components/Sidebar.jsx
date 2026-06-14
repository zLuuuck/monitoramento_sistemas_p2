import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Icon } from './Icon';
import { api } from '../services/api';  

export function Sidebar({ activeTab }) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [alertCount, setAlertCount] = useState(0);  

  // Buscar número real de alertas
  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const alerts = await api.getAlerts('active');
        setAlertCount(alerts.length);
      } catch (error) {
        console.error('Erro ao carregar alertas:', error);
      }
    };
    
    loadAlerts();
    const interval = setInterval(loadAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

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
      style={{ backgroundColor: 'var(--bg-secondary)', borderRight: '1px solid var(--border-subtle)' }}
    >
      {/* Logo Corvo */}
      <div
        className={`p-4 border-b flex items-center ${
          isMinimized ? 'justify-center' : 'justify-between'
        }`}
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        {!isMinimized && (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center raven-glow" style={{ backgroundColor: 'var(--raven-purple)' }}>
              <span className="text-white text-xl">🐦‍⬛</span>
            </div>
            <div>
              <span className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>Corvo</span>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Monitoring</p>
            </div>
          </div>
        )}
        {isMinimized && (
          <div className="w-10 h-10 rounded-full flex items-center justify-center raven-glow" style={{ backgroundColor: 'var(--raven-purple)' }}>
            <span className="text-white text-xl">🐦‍⬛</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="transition-colors p-1 rounded"
          style={{ color: 'var(--text-secondary)' }}
          title={isMinimized ? 'Expandir menu' : 'Minimizar menu'}
        >
          <Icon name={isMinimized ? 'expand' : 'minimize'} size="text-base" />
        </button>
      </div>

      {/* Menu */}
      <nav className="flex-1 py-6">
        <ul className="space-y-1">
          {menuItems.map((item) => (
            <li key={item.id}>
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 transition-all duration-200 ${
                  activeTab === item.id ? 'border-r-4' : ''
                } ${isMinimized ? 'justify-center' : ''}`}
                title={isMinimized ? item.name : ''}
                style={{
                  backgroundColor: activeTab === item.id ? 'var(--raven-purple)' : 'transparent',
                  color: activeTab === item.id ? 'white' : 'var(--text-secondary)',
                  borderRightColor: activeTab === item.id ? 'var(--raven-purple-light)' : 'transparent',
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== item.id) {
                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== item.id) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                <Icon name={item.icon} size="text-lg" />
                {!isMinimized && <span className="text-sm">{item.name}</span>}
                
                {/* usa alertCount real */}
                {item.id === 'alerts' && !isMinimized && alertCount > 0 && (
                  <span className="ml-auto text-white text-xs rounded-full px-2 py-0.5" style={{ backgroundColor: 'var(--raven-purple)' }}>
                    {alertCount}
                  </span>
                )}
                {item.id === 'alerts' && isMinimized && alertCount > 0 && (
                  <span className="ml-auto w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--raven-purple)' }}></span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t p-4" style={{ borderColor: 'var(--border-subtle)' }}>
        {!isMinimized ? (
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span>Sistema Online</span>
            </div>
            <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
              🐦‍⬛ Corvo Security
            </p>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
          </div>
        )}
      </div>
    </aside>
  );
}