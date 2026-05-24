import React, { useEffect, useState } from 'react';
import { api } from '../../../shared/services/api';

const severityColors = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-blue-100 text-blue-800',
};

const AlertsPanel = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

const loadAlerts = async () => {
    try {
        setLoading(true);
        setError(null);
        const data = await api.getAlerts('active');
        setAlerts(data);
    } catch (err) {
        console.error('Erro ao carregar alertas:', err);
        setError('Não foi possível carregar os alertas.');
    } finally {
        setLoading(false);
    }
};

const handleResolve = async (alertId) => {
    try {
        await api.resolveAlert(alertId);
        setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
    } catch (err) {
        console.error('Erro ao resolver alerta:', err);
        alert('Falha ao resolver alerta. Tente novamente.');
    }
};

    useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 15000);
    return () => clearInterval(interval);
}, []);

    if (loading && alerts.length === 0) {
    return (
        <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-xl font-bold mb-3">Alertas de Segurança</h2>
        <div className="text-gray-500">Carregando alertas...</div>
        </div>
    );
}

if (error) {
    return (
        <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-xl font-bold mb-3">Alertas de Segurança</h2>
        <div className="text-red-500">{error}</div>
        </div>
    );
}

return (
    <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-xl font-bold mb-3">Alertas de Segurança</h2>
    {alerts.length === 0 ? (
        <p className="text-gray-500">Nenhum alerta ativo.</p>
        ) : (
        <ul className="space-y-3">
            {alerts.map((alert) => (
            <li key={alert.id} className="border rounded-lg p-3 flex justify-between items-start">
                <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                    <span
                    className={`text-xs font-semibold px-2 py-1 rounded ${
                        severityColors[alert.severity] || severityColors.low
                    }`}
                    >
                    {alert.severity?.toUpperCase() || 'MÉDIO'}
                    </span>
                    <span className="font-mono text-sm">{alert.type || 'Desconhecido'}</span>
                </div>
                <p className="text-sm text-gray-600">
                    IP: {alert.source_ip || 'N/A'} |{' '}
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Data inválida'}
                </p>
                <p className="text-sm text-gray-700 mt-1">{alert.message || 'Sem mensagem'}</p>
                </div>
                <button
                onClick={() => handleResolve(alert.id)}
                className="ml-4 text-sm bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded"
                >
                Resolver
                </button>
            </li>
            ))}
        </ul>
        )}
    </div>
    );
};

export default AlertsPanel;