import { useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopTabs } from './TopTabs';

export function Layout({ children, hostType = 'physical' }) {
  const location = useLocation();

  // Mapeia a aba ativa na Sidebar baseando-se no endereço atual da URL
  const activeTab = location.pathname.substring(1) || 'dashboard';

  return (
    <div className="flex h-screen bg-gray-100" style={{ minWidth: '1024px' }}>
      {/* Sidebar recebe qual aba está ativa de acordo com a URL */}
      <Sidebar activeTab={activeTab} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopTabs hostType={hostType} />

        {/* O container principal renderiza o Seletor de Host + a subpágina correta */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}