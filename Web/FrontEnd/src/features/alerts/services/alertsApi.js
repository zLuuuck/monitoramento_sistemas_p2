// src/features/alerts/services/alertsApi.js
import api from '../../../shared/services/api';

export const fetchAlerts = async (status = null) => {
    try {
    const params = status ? { status } : {};
    const response = await api.get('/api/alerts', { params });
    return response.data;
} catch (error) {
    console.error('Erro ao buscar alertas:', error);
    throw error;
    }
};

export const resolveAlert = async (alertId) => {
    try {
    const response = await api.patch(`/api/alerts/${alertId}/resolve`);
    return response.data;
    } catch (error) {
    console.error('Erro ao resolver alerta:', error);
    throw error;
    }
};