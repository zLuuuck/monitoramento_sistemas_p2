export interface Host {
  id: string;
  name: string;
  status: 'online' | 'offline';
  ip?: string;
}

export interface Metric {
  id: string;
  hostId: string;
  cpu_percent: number;
  memory_percent: number;
  timestamp: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  type: 'auth' | 'system' | 'attack';
  message: string;
  source_ip: string | null;
}

export interface Alert {
  id: string;
  severity: 'high' | 'medium' | 'low';
  type: string;
  source_ip: string;
  timestamp: string;
  resolved: boolean;
}