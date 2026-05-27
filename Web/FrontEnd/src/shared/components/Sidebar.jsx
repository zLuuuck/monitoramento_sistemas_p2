import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Importamos o Link do React Router
import { Icon } from './Icon';

export function Sidebar({ activeTab }) {
  // Estado da sidebar (minimizada ou expandida)
  const [isMinimized, setIsMinimized] = useState(false);

  // Carregar preferência salva no localStorage ao iniciar
  useEffect(() => {
    const savedState = localStorage.getItem('sidebarMinimized');
    if (savedState !== null) {
      setIsMinimized(savedState === 'true');
    }
  }, []);

  // Salvar preferência quando mudar
  const toggleSidebar = () => {
    const newState = !isMinimized;
    setIsMinimized(newState);
    localStorage.setItem('sidebarMinimized', newState);
  };

  // Itens do menu com o caminho (path) de cada rota mapeado
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
      className={`bg-gray-900 text-white flex flex-col transition-all duration-300 ease-in-out ${
        isMinimized ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo / Header da Sidebar */}
      <div className={`p-4 border-b border-gray-800 flex items-center ${
        isMinimized ? 'justify-center' : 'justify-between'
      }`}>
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
        
        {/* Botão minimizar/expandir */}
        <button
          onClick={toggleSidebar}
          className="text-gray-400 hover:text-white transition-colors p-1 rounded hover:bg-gray-800"
          title={isMinimized ? "Expandir menu" : "Minimizar menu"}
        >
          <Icon name={isMinimized ? "expand" : "minimize"} size="text-base" />
        </button>
      </div>

      {/* Menu de Navegação */}
      <nav className="flex-1 py-6">
        <ul className="space-y-1">
          {menuItems.map((item) => (
            <li key={item.id}>
              {/* Trocamos o button pelo Link para atualizar a URL real do navegador */}
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 transition-all duration-200 ${
                  activeTab === item.id
                    ? 'bg-blue-600 text-white border-r-4 border-blue-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                } ${isMinimized ? 'justify-center' : ''}`}
                title={isMinimized ? item.name : ''}
              >
                <Icon name={item.icon} size="text-lg" />
                {!isMinimized && <span className="text-sm">{item.name}</span>}
                
                {/* Indicador de notificação */}
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

      {/* Footer da Sidebar */}
      <div className="border-t border-gray-800">
        {!isMinimized ? (
          <div className="p-4">
            <div className="text-xs text-gray-500 text-center mb-3">
              Monitoramento P2
            </div>
            <div className="flex items-center justify-center gap-2 text-xs text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Sistema Online</span>
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