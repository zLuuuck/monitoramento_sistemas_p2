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
      return [];
    }

    const data = await request(`/api/metrics?host_id=${hostId}&limit=${limit}`);
    return data.metrics || [];
  },
};
