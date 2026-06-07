import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopTabs } from './TopTabs';

export function Layout({ children, hostType = 'physical' }) {
  const location = useLocation();
  const activeTab = location.pathname.substring(1) || 'dashboard';

  const [activeSubTab, setActiveSubTab] = useState('overview');

  return (
    <div 
      className="flex h-screen" 
      style={{ minWidth: '1024px', backgroundColor: 'var(--bg-page)' }}
    >
      <Sidebar activeTab={activeTab} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopTabs hostType={hostType} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}