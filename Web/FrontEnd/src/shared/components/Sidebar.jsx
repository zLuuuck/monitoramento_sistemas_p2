import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Icon } from './Icon';
import { api } from '../services/api';

const MENU_GROUPS = [
  {
    label: 'Principal',
    items: [
      { id: 'dashboard', name: 'Dashboard', icon: 'dashboard', path: '/dashboard' },
      { id: 'logs', name: 'Logs Gerais', icon: 'log', path: '/logs' },
    ],
  },
  {
    label: 'Monitoramento',
    items: [
      { id: 'alerts', name: 'Alertas Gerais', icon: 'alert', path: '/alerts' },
      { id: 'endpoints', name: 'Endpoints', icon: 'server', path: '/endpoints' },
    ],
  },
  {
    label: 'Sistema',
    items: [
      { id: 'settings', name: 'Configurações', icon: 'settings', path: '/settings' },
    ],
  },
];

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

  return (
    <aside
      className={`flex flex-col transition-all duration-300 ease-in-out ${isMinimized ? 'w-20' : 'w-64'
        }`}
      style={{ backgroundColor: 'var(--bg-secondary)', borderRight: '1px solid var(--border-subtle)' }}
    >
      {/* Logo Munynn */}
      <div className="relative border-b p-4" style={{ borderColor: 'var(--border-subtle)' }}>
        <button
          onClick={toggleSidebar}
          className="absolute top-2 right-2 transition-colors p-1 rounded z-10"
          style={{ color: 'var(--text-secondary)' }}
          title={isMinimized ? 'Expandir menu' : 'Minimizar menu'}
        >
          <Icon name={isMinimized ? 'expand' : 'minimize'} size="text-base" />
        </button>

        <div className="flex flex-col items-center gap-3">
          <img
            src="/logo-Munynn.jpeg"
            alt="Munynn"
            className={`rounded-xl object-cover transition-all duration-300 ${isMinimized ? 'w-10 h-10' : 'w-20 h-20'}`}
          />
          {!isMinimized && (
            <div className="text-center leading-tight">
              <p className="font-bold text-xl tracking-wide" style={{ color: 'var(--text-primary)' }}>MUNYNN</p>
              <p className="font-semibold text-sm tracking-widest" style={{ color: 'var(--text-secondary)' }}>SYSTEM</p>
            </div>
          )}
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 py-6 overflow-y-auto">
        {MENU_GROUPS.map((group) => (
          <div key={group.label} className="mb-4">
            {!isMinimized && (
              <p
                className="px-4 mb-2 text-xs font-semibold uppercase tracking-wider"
                style={{ color: 'var(--text-muted)' }}
              >
                {group.label}
              </p>
            )}
            <ul className="space-y-1">
              {group.items.map((item) => (
                <li key={item.id}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-3 transition-all duration-200 ${activeTab === item.id ? 'border-r-4' : ''
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
          </div>
        ))}
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
              Munynn Security
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
