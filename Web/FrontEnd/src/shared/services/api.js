const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.erro || `Erro HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  getDiscovery: async () => {
    const data = await request('/api/discovery');
    return data.discoveries || [];
  },
  postDiscovery: async (payload) => {
    return request('/api/discovery', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getMetrics: async (hostId, limit = 30) => {
    if (!hostId) {
      return { metrics: [], status: 'offline', is_online: false, last_metric_at: null };
    }
    return request(`/api/metrics?host_id=${hostId}&limit=${limit}`);
  },
  getLogs: async (hostId, options = {}) => {
    if (!hostId) return { logs: [], total: 0 };
    const { limit = 50, offset = 0, log_type = 'auth' } = options;
    let url = `/api/logs?host_id=${hostId}&limit=${limit}&offset=${offset}`;
    if (log_type) url += `&log_type=${log_type}`;
    return request(url);
  },
  // ALERTAS (agora dentro do objeto api)
  getAlerts: async (status = 'active') => {
    const params = status ? `?status=${status}` : '';
    const data = await request(`/api/alerts${params}`);
    return data.alerts || [];
  },
  resolveAlert: async (alertId) => {
    return request(`/api/alerts/${alertId}/resolve`, {
      method: 'PATCH',
    });
  },
};