const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// A chave NÃO é lida de variáveis VITE_ — essas são embutidas no bundle pelo
// Vite e ficam visíveis em texto plano no fonte entregue ao navegador.
// A chave vive apenas no localStorage, definida em runtime pelo administrador.
function getStoredApiKey() {
  return localStorage.getItem('monitor_api_key') || '';
}

export function saveApiKey(key) {
  if (key) {
    localStorage.setItem('monitor_api_key', key);
  } else {
    localStorage.removeItem('monitor_api_key');
  }
}

export function hasBrowserApiKey() {
  return Boolean(localStorage.getItem('monitor_api_key'));
}

async function request(path, options = {}) {
  const apiKey = getStoredApiKey();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-API-Key': apiKey } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 401) {
    throw new Error('AUTH_REQUIRED');
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.erro || `Erro HTTP ${response.status}`);
  }

  return response.json();
}

export async function loginWithPassword(password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.erro || `Erro ${response.status}`);
  return body;
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
  getApiKey: () => request('/api/settings/apikey'),
  generateApiKey: (password) => request('/api/settings/apikey/generate', {
    method: 'POST',
    body: JSON.stringify(password ? { password } : {}),
  }),
  getNotifications: () => request('/api/settings/notifications'),
  patchNotifications: (body) => request('/api/settings/notifications', {
    method: 'PATCH',
    body: JSON.stringify(body),
  }),
  getThresholds: () => request('/api/settings/thresholds'),
  patchThresholds: (body) => request('/api/settings/thresholds', {
    method: 'PATCH',
    body: JSON.stringify(body),
  }),
  getEmailRecipients: () => request('/api/settings/email-recipients'),
  addEmailRecipient: (email) => request('/api/settings/email-recipients', {
    method: 'POST',
    body: JSON.stringify({ email }),
  }),
  removeEmailRecipient: (email) => request(`/api/settings/email-recipients/${encodeURIComponent(email)}`, {
    method: 'DELETE',
  }),
};
