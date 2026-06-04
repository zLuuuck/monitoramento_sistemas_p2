--
-- PostgreSQL database dump (schema consolidado)
-- active_connections removida; restrict/unrestrict removidos.
--

-- Dumped from database version 15.18 (Debian 15.18-1.pgdg13+1)
-- Dumped by pg_dump version 15.18 (Debian 15.18-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: cleanup_old_data(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.cleanup_old_data(days_to_keep integer DEFAULT 7) RETURNS void
    LANGUAGE plpgsql
    AS $$ BEGIN
DELETE FROM metrics
WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
DELETE FROM logs
WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agents (
    id integer NOT NULL,
    host_id integer NOT NULL,
    agent_version character varying(20),
    last_checkin timestamp with time zone DEFAULT now(),
    status character varying(20) DEFAULT 'active'::character varying
);


--
-- Name: agents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.agents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: agents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.agents_id_seq OWNED BY public.agents.id;


--
-- Name: alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alerts (
    id bigint NOT NULL,
    host_id integer NOT NULL,
    alert_type character varying(50) NOT NULL,
    source_ip character varying(45),
    "timestamp" timestamp with time zone DEFAULT now(),
    severity character varying(20) DEFAULT 'medium'::character varying,
    metodos character varying(20),
    message text,
    resolved boolean DEFAULT false NOT NULL,
    resolved_at timestamp with time zone
);


--
-- Name: alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alerts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alerts_id_seq OWNED BY public.alerts.id;


--
-- Name: app_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_settings (
    key character varying(100) NOT NULL,
    value text,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: host; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.host (
    id integer NOT NULL,
    hostname character varying(255) NOT NULL,
    ip_address inet,
    created_at timestamp with time zone DEFAULT now(),
    last_seen timestamp with time zone
);


--
-- Name: host_discovery; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.host_discovery (
    host_id integer NOT NULL,
    discovery_date timestamp with time zone DEFAULT now(),
    cpu_model character varying(200),
    cpu_cores smallint,
    cpu_clock_base_mhz integer,
    cpu_ghz numeric(4,1) GENERATED ALWAYS AS (((cpu_clock_base_mhz)::numeric / 1000.0)) STORED,
    memories jsonb,
    disks jsonb,
    networks jsonb,
    total_memory_gb numeric(10,2),
    is_virtualized boolean,
    hypervisor character varying(50),
    cpu_max_mhz integer,
    disk_total_gb numeric(10,2),
    os_name character varying(200),
    os_version character varying(50),
    kernel_release character varying(200),
    uptime_seconds integer,
    motherboard jsonb
);


--
-- Name: host_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.host_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: host_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.host_id_seq OWNED BY public.host.id;


--
-- Name: logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logs (
    id bigint NOT NULL,
    host_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    log_type character varying(50),
    raw_line text,
    parsed_data jsonb
);


--
-- Name: logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.logs_id_seq OWNED BY public.logs.id;


--
-- Name: metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metrics (
    id bigint NOT NULL,
    host_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    cpu_percent numeric(5,2),
    memory_percent numeric(5,2),
    memory_used_mb integer,
    memory_free_mb integer,
    memory_total_mb integer,
    disk_percent numeric(5,2),
    disk_used_mb bigint,
    disk_free_mb bigint,
    disk_total_mb bigint,
    net_sent_bytes bigint,
    net_recv_bytes bigint,
    read_iops double precision,
    write_iops double precision,
    read_bytes_per_sec double precision,
    write_bytes_per_sec double precision,
    net_sent_bytes_per_sec double precision,
    net_recv_bytes_per_sec double precision
);


--
-- Name: metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metrics_id_seq OWNED BY public.metrics.id;


--
-- Name: agents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents ALTER COLUMN id SET DEFAULT nextval('public.agents_id_seq'::regclass);


--
-- Name: alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts ALTER COLUMN id SET DEFAULT nextval('public.alerts_id_seq'::regclass);


--
-- Name: host id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.host ALTER COLUMN id SET DEFAULT nextval('public.host_id_seq'::regclass);


--
-- Name: logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs ALTER COLUMN id SET DEFAULT nextval('public.logs_id_seq'::regclass);


--
-- Name: metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics ALTER COLUMN id SET DEFAULT nextval('public.metrics_id_seq'::regclass);


--
-- Name: agents agents_host_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_host_id_key UNIQUE (host_id);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (id);


--
-- Name: app_settings app_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT app_settings_pkey PRIMARY KEY (key);


--
-- Name: host_discovery host_discovery_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.host_discovery
    ADD CONSTRAINT host_discovery_pkey PRIMARY KEY (host_id);


--
-- Name: host host_hostname_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.host
    ADD CONSTRAINT host_hostname_key UNIQUE (hostname);


--
-- Name: host host_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.host
    ADD CONSTRAINT host_pkey PRIMARY KEY (id);


--
-- Name: logs logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);


--
-- Name: metrics metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics
    ADD CONSTRAINT metrics_pkey PRIMARY KEY (id);


--
-- Name: idx_agents_last_checkin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agents_last_checkin ON public.agents USING btree (last_checkin DESC);


--
-- Name: idx_agents_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agents_status ON public.agents USING btree (status);


--
-- Name: idx_alerts_host_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_host_ts ON public.alerts USING btree (host_id, "timestamp" DESC);


--
-- Name: idx_alerts_source_ip_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_source_ip_ts ON public.alerts USING btree (source_ip, "timestamp" DESC);


--
-- Name: idx_alerts_type_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_type_ts ON public.alerts USING btree (alert_type, "timestamp" DESC);


--
-- Name: idx_discovery_cpu_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_cpu_model ON public.host_discovery USING btree (cpu_model);


--
-- Name: idx_discovery_disks_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_disks_gin ON public.host_discovery USING gin (disks);


--
-- Name: idx_discovery_networks_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_networks_gin ON public.host_discovery USING gin (networks);


--
-- Name: idx_discovery_ram; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_ram ON public.host_discovery USING btree (total_memory_gb);


--
-- Name: idx_discovery_virtualized; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_virtualized ON public.host_discovery USING btree (is_virtualized);


--
-- Name: idx_host_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_host_ip ON public.host USING btree (ip_address);


--
-- Name: idx_logs_auth_failed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_auth_failed ON public.logs USING btree ("timestamp") WHERE (((log_type)::text = 'auth'::text) AND ((parsed_data ->> 'status'::text) = 'failed'::text));


--
-- Name: idx_logs_auth_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_auth_ip ON public.logs USING btree (((parsed_data ->> 'ip_origem'::text))) WHERE ((log_type)::text = 'auth'::text);


--
-- Name: idx_logs_host_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_host_ts ON public.logs USING btree (host_id, "timestamp" DESC);


--
-- Name: idx_logs_parsed_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_parsed_gin ON public.logs USING gin (parsed_data);


--
-- Name: idx_logs_type_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_type_ts ON public.logs USING btree (log_type, "timestamp" DESC);


--
-- Name: idx_metrics_high_cpu; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metrics_high_cpu ON public.metrics USING btree (host_id, "timestamp") WHERE (cpu_percent > (85)::numeric);


--
-- Name: idx_metrics_high_mem; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metrics_high_mem ON public.metrics USING btree (host_id, "timestamp") WHERE (memory_percent > (90)::numeric);


--
-- Name: idx_metrics_host_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metrics_host_ts ON public.metrics USING btree (host_id, "timestamp" DESC);


--
-- Name: idx_metrics_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metrics_ts ON public.metrics USING btree ("timestamp");


--
-- Name: agents agents_host_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_host_id_fkey FOREIGN KEY (host_id) REFERENCES public.host(id) ON DELETE CASCADE;


--
-- Name: alerts alerts_host_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_host_id_fkey FOREIGN KEY (host_id) REFERENCES public.host(id) ON DELETE CASCADE;


--
-- Name: host_discovery host_discovery_host_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.host_discovery
    ADD CONSTRAINT host_discovery_host_id_fkey FOREIGN KEY (host_id) REFERENCES public.host(id) ON DELETE CASCADE;


--
-- Name: logs logs_host_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_host_id_fkey FOREIGN KEY (host_id) REFERENCES public.host(id) ON DELETE CASCADE;


--
-- Name: metrics metrics_host_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics
    ADD CONSTRAINT metrics_host_id_fkey FOREIGN KEY (host_id) REFERENCES public.host(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--