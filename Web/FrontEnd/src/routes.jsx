import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './App.jsx';
import { 
  DashboardPage, 
  MetricsPage, 
  LogsPage, 
  AlertsPage,
  EndpointsPage,   
  SettingsPage      
} from './pages/AppPages.jsx';

// Componente de erro 404
function NotFound() {
  return (
    <div className="p-8 text-center">
      <h1 className="text-2xl font-bold text-red-600">404 - Página não encontrada</h1>
      <p className="mt-2">A rota que você tentou acessar não existe.</p>
      <a href="/dashboard" className="mt-4 inline-block px-4 py-2 bg-blue-500 text-white rounded-lg">
        Voltar ao Dashboard
      </a>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { path: '/', element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/metrics', element: <MetricsPage /> },
      { path: '/logs', element: <LogsPage /> },
      { path: '/alerts', element: <AlertsPage /> },
      { path: '/endpoints', element: <EndpointsPage /> },   
      { path: '/settings', element: <SettingsPage /> },     
    ],
  },
]);

export default router;