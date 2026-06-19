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
  className={`flex flex-col transition-all duration-300 ease-in-out ${
    isMinimized ? 'w-20' : 'w-72'
  }`}
  style={{
    background:
      'linear-gradient(180deg, #0B0B12 0%, #080810 100%)',
      borderRight: '1px solid var(--raven-purple-light)',
      boxShadow: '1px 0 14px 0 var(--raven-purple-glow), inset -1px 0 0 rgba(255,255,255,0.03)',
  }}
>
      {/* Logo Munynn */}
      <div className="relative border-b p-5" style={{ borderColor: 'var(--border-subtle)' }}>
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
            className={`rounded-2xl object-cover shadow-lg transition-all duration-300 ${isMinimized ? 'w-12 h-12' : 'w-28 h-28'}`}
            style={{ boxShadow: '0 0 24px var(--raven-purple-glow)' }}
          />
          {!isMinimized && (
            <div className="text-center leading-tight">
              <p className="font-extrabold text-2xl tracking-wide" style={{ color: 'var(--text-primary)' }}>MUNYNN</p>
              <p className="font-semibold text-base tracking-[0.3em]" style={{ color: 'var(--text-secondary)' }}>SYSTEM</p>
            </div>
          )}
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 py-6 overflow-hidden">
        {MENU_GROUPS.map((group) => (
          <div key={group.label} className="mb-5">
            {!isMinimized && (
              <div className="flex items-center gap-2 px-5 mb-2">
                <span className="w-3 h-[3px] rounded-full" style={{ backgroundColor: 'var(--raven-purple-light)' }}></span>
                <p
                  className="text-[11px] font-bold uppercase tracking-[0.2em]"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {group.label}
                </p>
              </div>
            )}
            <ul className="space-y-1.5 px-3">
              {group.items.map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <li key={item.id} className="relative">
                    <Link
                      to={item.path}
                      className={`relative overflow-hidden group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${isMinimized ? 'justify-center' : ''}`}
                      title={isMinimized ? item.name : ''}
                      style={{
                        background: isActive
                          ? 'linear-gradient(135deg, #3D245A, #56317E)'
                          : 'transparent',
                        color: isActive ? 'white' : 'var(--text-secondary)',
                        boxShadow: isActive   ? `
                        0 0 0 1px rgba(139,92,246,.15),
                        0 8px 24px rgba(91,33,182,.20)
                        ` : 'none',
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.background =
                          'linear-gradient(90deg, rgba(139,92,246,.10), rgba(139,92,246,.03))';

                          e.currentTarget.style.boxShadow =
                          '0 0 20px rgba(139,92,246,.08)';

                          e.currentTarget.style.color = 'white';

                          e.currentTarget.style.transform = 'translateX(6px)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.boxShadow = 'none';
                        e.currentTarget.style.color = 'var(--text-secondary)';
                        e.currentTarget.style.transform = 'translateX(0)';
                        }
                      }}
                    >
                      <span
                        className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0"
                        style={{
                        backgroundColor: isActive
                        ? 'rgba(255,255,255,0.15)'
                        : 'rgba(139,92,246,0.05)',
                        border: isActive
                        ? 'none'
                        : '1px solid rgba(139,92,246,.08)'
                        }}
                      >
                    {isActive && (
                      <span
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full"
                        style={{
                        background: 'var(--raven-purple-light)',
                        boxShadow: '0 0 12px var(--raven-purple-light)',
      }}
    />
  )}
                        <Icon name={item.icon} size="text-base" />
                      </span>
                      {!isMinimized && <span className="text-sm font-medium">{item.name}</span>}

                      {item.id === 'alerts' && !isMinimized && alertCount > 0 && (
                        <span
                          className="ml-auto text-xs font-bold rounded-full px-2 py-0.5"
                          style={{ backgroundColor: isActive ? 'rgba(255,255,255,0.25)' : 'var(--raven-purple)', color: 'white' }}
                        >
                          {alertCount}
                        </span>
                      )}
                      {item.id === 'alerts' && isMinimized && alertCount > 0 && (
                        <span className="absolute top-1 right-1 w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--raven-purple-light)' }}></span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div
      className="border-t p-4 text-center"
      style={{ borderColor: 'var(--border-subtle)' }}
    >
      {!isMinimized && (
      <p
      className="text-[11px]"
      style={{ color: 'var(--text-muted)' }}
    >
      © 2026 Munynn System
    </p>
  )}
</div>
    </aside>
  );
}
