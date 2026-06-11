import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './App.jsx';
import {
  DashboardPage,
  MetricsPage,
  LogsPage,
  AlertsPage,
  EndpointsPage,
  SettingsPage
} from './pages';

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