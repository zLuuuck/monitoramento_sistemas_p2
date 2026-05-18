import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopTabs } from './TopTabs';
import { Icon } from './Icon';

export function Layout({ children, hostType = 'physical', logsPanel }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeSubTab, setActiveSubTab] = useState('overview');

  // Renderizar conteúdo baseado na aba ativa
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return children;
      case 'metrics':
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-400">
              <Icon name="chart" size="text-4xl" className="mb-2" />
              <p>Página de Métricas Detalhadas</p>
              <p className="text-sm">Em desenvolvimento</p>
            </div>
          </div>
        );
      case 'logs':
        return logsPanel ?? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-400">
              <Icon name="log" size="text-4xl" className="mb-2" />
              <p>Central de Logs</p>
              <p className="text-sm">Nenhum host selecionado</p>
            </div>
          </div>
        );
      case 'alerts':
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-400">
              <Icon name="alert" size="text-4xl" className="mb-2" />
              <p>Painel de Alertas</p>
              <p className="text-sm">Em desenvolvimento</p>
            </div>
          </div>
        );
      case 'endpoints':
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-400">
              <Icon name="server" size="text-4xl" className="mb-2" />
              <p>Gerenciamento de Endpoints</p>
              <p className="text-sm">Em desenvolvimento</p>
            </div>
          </div>
        );
      case 'settings':
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-400">
              <Icon name="settings" size="text-4xl" className="mb-2" />
              <p>Configurações do Sistema</p>
              <p className="text-sm">Em desenvolvimento</p>
            </div>
          </div>
        );
      default:
        return children;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100" style={{ minWidth: '1024px' }}>
      {/* Sidebar (aba lateral minimizável) */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Conteúdo principal */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Tabs (aba superior) */}
        <TopTabs 
          activeSubTab={activeSubTab}
          onSubTabChange={setActiveSubTab}
          hostType={hostType}
        />

        {/* Conteúdo rolável */}
        <main className="flex-1 overflow-y-auto p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}