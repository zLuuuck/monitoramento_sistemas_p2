import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout({ children, hostType = 'physical' }) {
  const location = useLocation();
  const activeTab = location.pathname.substring(1) || 'dashboard';
  const [activeSubTab, setActiveSubTab] = useState('overview');

  return (
    <div
      className="flex h-screen"
      style={{
        minWidth: '1024px',
        backgroundColor: 'var(--bg-primary)',
        backgroundImage: 'radial-gradient(circle at 10% 20%, rgba(107, 33, 165, 0.05) 0%, transparent 50%)'
      }}
    >
      <Sidebar activeTab={activeTab} />
      <div className="flex-1 flex flex-col overflow-hidden">
       <main className="flex-1 overflow-y-auto px-6 pb-6 pt-0">
          {children}
        </main>
      </div>
    </div>
  );
}