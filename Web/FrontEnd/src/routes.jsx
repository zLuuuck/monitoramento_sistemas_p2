import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './App.jsx';
import { DashboardPage, MetricsPage, LogsPage, AlertsPage } from './pages/AppPages.jsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />, // O App.jsx vira o "Provedor" do estado dos hosts
    children: [
      {
        path: '/',
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: '/dashboard',
        element: <DashboardPage />,
      },
      {
        path: '/metrics',
        element: <MetricsPage />,
      },
      {
        path: '/logs',
        element: <LogsPage />,
      },
      {
        path: '/alerts',
        element: <AlertsPage />,
      },
    ],
  },
]);

export default router;