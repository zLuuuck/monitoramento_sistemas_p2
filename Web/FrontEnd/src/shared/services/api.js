const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);

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
};
