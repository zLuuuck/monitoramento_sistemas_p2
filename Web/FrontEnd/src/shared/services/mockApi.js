// Dados falsos para testar o dashboard

// Lista de hosts (computadores monitorados)
export const mockHosts = [
  { id: '1', name: 'Servidor Principal', status: 'online', ip: '192.168.1.10' },
  { id: '2', name: 'Servidor Web', status: 'online', ip: '192.168.1.20' },
  { id: '3', name: 'Banco de Dados', status: 'offline', ip: '192.168.1.30' },
];

// Função para gerar métricas falsas
export function gerarMetricasMock(hostId) {
  const metrics = [];
  const agora = Date.now();
  
  for (let i = 0; i < 10; i++) {
    metrics.push({
      id: `m${i}`,
      hostId: hostId,
      cpu_percent: Math.random() * 80 + 10,  // entre 10% e 90%
      memory_percent: Math.random() * 70 + 20, // entre 20% e 90%
      timestamp: new Date(agora - (10 - i) * 60000).toISOString(),
    });
  }
  
  return metrics;
}

// Logs falsos
export const mockLogs = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    type: 'auth',
    message: 'Falha de login para usuário root',
    source_ip: '192.168.1.100',
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    type: 'system',
    message: 'Sistema iniciado com sucesso',
    source_ip: null,
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    type: 'attack',
    message: 'Múltiplas tentativas de login detectadas',
    source_ip: '45.33.22.11',
  },
];

// Funções que simulam uma API
export const mockApi = {
  getHosts: async () => {
    await delay(500);
    return [...mockHosts];
  },
  getMetrics: async (hostId) => {
    await delay(300);
    return gerarMetricasMock(hostId);
  },
  getLogs: async () => {
    await delay(400);
    return [...mockLogs];
  },
};

// Função auxiliar para simular delay de rede
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));