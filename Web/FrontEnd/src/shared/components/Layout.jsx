import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopTabs } from './TopTabs';

export function Layout({ children, hostType = 'physical' }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeSubTab, setActiveSubTab] = useState('overview');

  // Conteúdo diferente baseado na aba ativa
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return children;
      case 'metrics':
        return <div className="p-6">📊 Página de Métricas (em breve)</div>;
      case 'logs':
        return <div className="p-6">📋 Página de Logs (em breve)</div>;
      case 'alerts':
        return <div className="p-6">🚨 Página de Alertas (em breve)</div>;
      case 'endpoints':
        return <div className="p-6">🖥️ Página de Endpoints (em breve)</div>;
      case 'config':
        return <div className="p-6">⚙️ Configurações (em breve)</div>;
      default:
        return children;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar (aba lateral) */}
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