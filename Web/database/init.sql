CREATE TABLE host (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ
);

CREATE INDEX idx_host_ip ON host (ip_address);

-- 2. TABELA agents (agentes de monitoramento)
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    host_id INT NOT NULL UNIQUE REFERENCES host(id) ON DELETE CASCADE,
    agent_version VARCHAR(20),
    last_checkin TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

CREATE INDEX idx_agents_status ON agents (status);
CREATE INDEX idx_agents_last_checkin ON agents (last_checkin DESC);

-- 3. TABELA host_discovery (hardware estático)
CREATE TABLE host_discovery (
    host_id INT PRIMARY KEY REFERENCES host(id) ON DELETE CASCADE,
    discovery_date TIMESTAMPTZ DEFAULT NOW(),
    cpu_model VARCHAR(200),
    cpu_cores SMALLINT,
    cpu_clock_base_mhz INTEGER,
    cpu_ghz DECIMAL(4,1) GENERATED ALWAYS AS (cpu_clock_base_mhz / 1000.0) STORED,
    memories JSONB,
    disks JSONB,
    networks JSONB,
    total_memory_gb DECIMAL(10,2),
    is_virtualized BOOLEAN,
    hypervisor VARCHAR(50),
    cpu_max_mhz INTEGER,
    disk_total_gb DECIMAL(10,2)
);

CREATE INDEX idx_discovery_virtualized ON host_discovery (is_virtualized);
CREATE INDEX idx_discovery_ram ON host_discovery (total_memory_gb);
CREATE INDEX idx_discovery_cpu_model ON host_discovery (cpu_model);
CREATE INDEX idx_discovery_disks_gin ON host_discovery USING GIN (disks);
CREATE INDEX idx_discovery_networks_gin ON host_discovery USING GIN (networks);

-- 4. TABELA metrics (métricas dinâmicas)
CREATE TABLE metrics (
    id BIGSERIAL PRIMARY KEY,
    host_id INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    cpu_percent DECIMAL(5,2),
    memory_percent DECIMAL(5,2),
    memory_used_mb INTEGER,
    memory_free_mb INTEGER,
    memory_total_mb INTEGER,
    disk_percent DECIMAL(5,2),
    disk_used_mb BIGINT,
    disk_free_mb BIGINT,
    disk_total_mb BIGINT,
    net_sent_bytes BIGINT,
    net_recv_bytes BIGINT
);

CREATE INDEX idx_metrics_host_ts ON metrics (host_id, timestamp DESC);
CREATE INDEX idx_metrics_ts ON metrics (timestamp);
CREATE INDEX idx_metrics_high_cpu ON metrics (host_id, timestamp) WHERE cpu_percent > 85;
CREATE INDEX idx_metrics_high_mem ON metrics (host_id, timestamp) WHERE memory_percent > 90;

-- 5. TABELA logs (eventos de sistema)
CREATE TABLE logs (
    id BIGSERIAL PRIMARY KEY,
    host_id INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    log_type VARCHAR(50),
    raw_line TEXT,
    parsed_data JSONB
);

CREATE INDEX idx_logs_host_ts ON logs (host_id, timestamp DESC);
CREATE INDEX idx_logs_type_ts ON logs (log_type, timestamp DESC);
CREATE INDEX idx_logs_auth_ip ON logs ((parsed_data->>'ip_origem')) WHERE log_type = 'auth';
CREATE INDEX idx_logs_auth_failed ON logs (timestamp) WHERE log_type = 'auth' AND parsed_data->>'status' = 'failed';
CREATE INDEX idx_logs_parsed_gin ON logs USING GIN (parsed_data);

-- 6. TABELA alerts (alertas)
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    host_id INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    source_ip INET NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'medium',
    metodos VARCHAR(20)
);

CREATE INDEX idx_alerts_host_ts ON alerts (host_id, timestamp DESC);
CREATE INDEX idx_alerts_type_ts ON alerts (alert_type, timestamp DESC);
CREATE INDEX idx_alerts_source_ip_ts ON alerts (source_ip, timestamp DESC);

-- 7. TABELA active_connections (conexões de rede ativas)
CREATE TABLE active_connections (
    id BIGSERIAL PRIMARY KEY,
    host_id INT NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    src_ip INET NOT NULL,
    src_port INTEGER NOT NULL,
    dst_ip INET NOT NULL,
    dst_port INTEGER NOT NULL,
    protocol VARCHAR(10) NOT NULL,
    status VARCHAR(20),
    duration_sec INTEGER
);

CREATE INDEX idx_conn_host_ts ON active_connections (host_id, timestamp DESC);
CREATE INDEX idx_conn_status ON active_connections (status);
CREATE INDEX idx_conn_dst_ip_ts ON active_connections (dst_ip, timestamp DESC);
CREATE INDEX idx_conn_duration ON active_connections (duration_sec) WHERE duration_sec > 3600;

-- ============================================================
-- POLÍTICA DE RETENÇÃO (7 dias)
-- ============================================================
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 7)
RETURNS VOID AS $$
BEGIN
    DELETE FROM metrics WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    DELETE FROM logs WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    DELETE FROM active_connections WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;