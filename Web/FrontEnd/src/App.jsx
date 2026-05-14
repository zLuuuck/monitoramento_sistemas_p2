import { useState } from "react";
import "./App.css";
import { useEffect } from "react";
import { Layout } from "./shared/components/Layout";
import { Card } from "./shared/components/Card";
import { LogsPlaceholder } from "./features/logs_feat/components/LogsPlaceholder";
import { MetricsChart } from "./features/metrics/components/MetricsChart";
import { mockApi, mockHosts } from "./shared/services/mockApi";
import { api } from "./shared/services/api";

function App() {
    const [selectedHost, setSelectedHost] = useState("1");
    const [metrics, setMetrics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [discovery, setDiscovery] = useState([]);
    const [discoveryLoading, setDiscoveryLoading] = useState(true);
    const [discoveryError, setDiscoveryError] = useState("");
    const [discoveryPayload, setDiscoveryPayload] = useState("");
    const [postingDiscovery, setPostingDiscovery] = useState(false);
    const [postDiscoveryMessage, setPostDiscoveryMessage] = useState("");

    const carregarDiscovery = async ({ selecionarPrimeiro = false } = {}) => {
        try {
            setDiscoveryLoading(true);
            setDiscoveryError("");
            const dados = await api.getDiscovery();
            setDiscovery(dados);

            if (dados.length > 0 && (selecionarPrimeiro || !selectedHost)) {
                setSelectedHost(String(dados[0].host_id));
            }
        } catch (error) {
            setDiscoveryError(error.message);
        } finally {
            setDiscoveryLoading(false);
        }
    };

    useEffect(() => {
        carregarDiscovery({ selecionarPrimeiro: true });
    }, []);

    // Carregar métricas quando mudar o host
    useEffect(() => {
        const carregarMetricas = async () => {
            setLoading(true);
            const dados = await mockApi.getMetrics(selectedHost);
            setMetrics(dados);
            setLoading(false);
        };
        carregarMetricas();
    }, [selectedHost]);

    // Pega a última métrica (mais recente)
    const ultimaMetrica = metrics[metrics.length - 1];
    const hostsDisponiveis =
        discovery.length > 0
            ? discovery.map((item) => ({
                id: String(item.host_id),
                name: item.host?.hostname || `Host ${item.host_id}`,
                status: "online",
                ip: item.host?.ip_address,
            }))
            : mockHosts;
    const selectedDiscovery = discovery.find(
        (item) => String(item.host_id) === selectedHost,
    );
    const selectedHostInfo = hostsDisponiveis.find(
        (host) => host.id === selectedHost,
    );
    const discos = Array.isArray(selectedDiscovery?.disks)
        ? selectedDiscovery.disks
        : [];
    const redes = Array.isArray(selectedDiscovery?.networks?.interfaces)
        ? selectedDiscovery.networks.interfaces
        : Array.isArray(selectedDiscovery?.networks)
            ? selectedDiscovery.networks
            : [];

    const enviarDiscovery = async (event) => {
        event.preventDefault();
        setPostDiscoveryMessage("");

        let payload;
        try {
            payload = JSON.parse(discoveryPayload);
        } catch {
            setPostDiscoveryMessage("JSON invalido. Verifique o conteudo colado.");
            return;
        }

        try {
            setPostingDiscovery(true);
            const resposta = await api.postDiscovery(payload);
            setPostDiscoveryMessage(resposta.message || "Discovery enviado com sucesso.");
            await carregarDiscovery({ selecionarPrimeiro: true });
            setSelectedHost(String(resposta.host_id));
        } catch (error) {
            setPostDiscoveryMessage(`Erro ao enviar discovery: ${error.message}`);
        } finally {
            setPostingDiscovery(false);
        }
    };

    return (
        <Layout>
            {/* Seletor de Host */}
            <div className="flex justify-end mb-6">
                <div className="flex items-center gap-3">
                    <label className="text-gray-600 text-sm font-medium">Host:</label>
                    <select
                        value={selectedHost}
                        onChange={(e) => setSelectedHost(e.target.value)}
                        className="border border-gray-300 rounded-lg px-4 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {hostsDisponiveis.map((host) => (
                            <option key={host.id} value={host.id}>
                                {host.name} {host.status === "offline" && "(Offline)"}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* GRÁFICO - NOVO! */}
            {!loading && metrics.length > 0 && (
                <div className="mb-8">
                    <MetricsChart
                        metrics={metrics}
                        title={`Métricas - ${selectedHostInfo?.name || "Host selecionado"}`}
                    />
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex justify-center py-20">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
                </div>
            )}

            {/* Cards de Métricas */}
            {!loading && ultimaMetrica && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <Card
                        title="CPU"
                        value={ultimaMetrica.cpu_percent.toFixed(1)}
                        unit="%"
                        icon="⚡"
                        color="blue"
                    />
                    <Card
                        title="Memória"
                        value={ultimaMetrica.memory_percent.toFixed(1)}
                        unit="%"
                        icon="🧠"
                        color="green"
                    />
                    <Card
                        title="Status"
                        value={selectedHostInfo?.status === "online" ? "Online" : "Offline"}
                        unit=""
                        icon={selectedHostInfo?.status === "online" ? "🟢" : "🔴"}
                        color={selectedHostInfo?.status === "online" ? "green" : "red"}
                    />
                </div>
            )}

            {/* Discovery */}
            <section className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="text-xl font-bold text-gray-800">
                            Discovery do Host
                        </h2>
                        <p className="text-sm text-gray-500">
                            Dados coletados pelo agente sobre hardware, virtualização e rede.
                        </p>
                    </div>
                </div>

                <form
                    onSubmit={enviarDiscovery}
                    className="bg-white rounded-lg shadow-md p-6 mb-6"
                >
                    <label
                        htmlFor="discovery-payload"
                        className="block text-sm font-medium text-gray-700 mb-2"
                    >
                        Enviar discovery JSON
                    </label>
                    <textarea
                        id="discovery-payload"
                        value={discoveryPayload}
                        onChange={(event) => setDiscoveryPayload(event.target.value)}
                        placeholder='Cole aqui o conteudo de agent_physical_sample.json, agent_virtual_sample-WSL2.json ou agent_virtual_sample-Ubuntu.json'
                        className="w-full min-h-36 border border-gray-300 rounded-lg px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3 mt-3">
                        <button
                            type="submit"
                            disabled={postingDiscovery || !discoveryPayload.trim()}
                            className="bg-blue-600 text-white rounded-lg px-4 py-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {postingDiscovery ? "Enviando..." : "Enviar discovery"}
                        </button>
                        {postDiscoveryMessage && (
                            <p className="text-sm text-gray-600">{postDiscoveryMessage}</p>
                        )}
                    </div>
                </form>

                {discoveryLoading && (
                    <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">
                        Carregando dados de discovery...
                    </div>
                )}

                {!discoveryLoading && discoveryError && (
                    <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
                        Nao foi possivel carregar o discovery: {discoveryError}
                    </div>
                )}

                {!discoveryLoading && !discoveryError && !selectedDiscovery && (
                    <div className="bg-white rounded-lg shadow-md p-6 text-gray-500">
                        Nenhum discovery cadastrado ainda.
                    </div>
                )}

                {!discoveryLoading && selectedDiscovery && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <Card
                                title="Hostname"
                                value={selectedDiscovery.host?.hostname || "-"}
                                unit=""
                                icon="💻"
                                color="blue"
                            />
                            <Card
                                title="Memória Total"
                                value={formatNumber(selectedDiscovery.total_memory_gb)}
                                unit="GB"
                                icon="🧠"
                                color="green"
                            />
                            <Card
                                title="Disco Total"
                                value={formatNumber(selectedDiscovery.disk_total_gb)}
                                unit="GB"
                                icon="💾"
                                color="yellow"
                            />
                            <Card
                                title="Virtualização"
                                value={selectedDiscovery.is_virtualized ? "Sim" : "Nao"}
                                unit=""
                                icon="🖥️"
                                color={selectedDiscovery.is_virtualized ? "green" : "blue"}
                            />
                        </div>

                        <div className="bg-white rounded-lg shadow-md p-6">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">
                                Detalhes do sistema
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                <Info label="IP" value={selectedDiscovery.host?.ip_address} />
                                <Info
                                    label="Data do discovery"
                                    value={formatDate(selectedDiscovery.discovery_date)}
                                />
                                <Info label="CPU" value={selectedDiscovery.cpu_model} />
                                <Info
                                    label="Nucleos/vCPUs"
                                    value={selectedDiscovery.cpu_cores}
                                />
                                <Info
                                    label="Clock base"
                                    value={formatMhz(selectedDiscovery.cpu_clock_base_mhz)}
                                />
                                <Info
                                    label="Clock maximo"
                                    value={formatMhz(selectedDiscovery.cpu_max_mhz)}
                                />
                                <Info
                                    label="Hypervisor"
                                    value={selectedDiscovery.hypervisor || "Nao informado"}
                                />
                                <Info label="Sistema operacional" value={selectedDiscovery.os_name} />
                                <Info label="Versao do OS" value={selectedDiscovery.os_version} />
                                <Info label="Kernel" value={selectedDiscovery.kernel_release} />
                                <Info
                                    label="Uptime"
                                    value={formatDuration(selectedDiscovery.uptime_seconds)}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <DiscoveryList
                                title="Discos"
                                items={discos}
                                emptyText="Nenhum disco informado"
                            />
                            <DiscoveryList
                                title="Redes"
                                items={redes}
                                emptyText="Nenhuma interface informada"
                            />
                        </div>
                    </div>
                )}
            </section>

            {/* Logs */}
            <LogsPlaceholder />
        </Layout>
    );
}

function Info({ label, value }) {
    const displayValue =
        value === null || value === undefined || value === "" ? "-" : value;

    return (
        <div className="border border-gray-200 rounded-lg p-3">
            <p className="text-gray-500">{label}</p>
            <p className="font-medium text-gray-800 break-words">{displayValue}</p>
        </div>
    );
}

function DiscoveryList({ title, items, emptyText }) {
    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
            {items.length === 0 ? (
                <p className="text-sm text-gray-500">{emptyText}</p>
            ) : (
                <div className="space-y-3">
                    {items.map((item, index) => (
                        <div
                            key={item.name || item.device || item.interface || index}
                            className="border border-gray-200 rounded-lg p-3"
                        >
                            <p className="font-medium text-gray-800">
                                {item.name ||
                                    item.device ||
                                    item.interface ||
                                    item.mountpoint ||
                                    `Item ${index + 1}`}
                            </p>
                            <p className="text-sm text-gray-500 break-words">
                                {summarizeObject(item)}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function summarizeObject(item) {
    return (
        Object.entries(item)
            .filter(
                ([, value]) =>
                    value !== null && value !== undefined && typeof value !== "object",
            )
            .map(([key, value]) => `${key}: ${value}`)
            .join(" | ") || "Sem detalhes adicionais"
    );
}

function formatNumber(value) {
    if (value === null || value === undefined || value === "") {
        return "-";
    }

    return Number(value).toLocaleString("pt-BR", {
        maximumFractionDigits: 2,
    });
}

function formatMhz(value) {
    if (!value) {
        return "-";
    }

    return `${formatNumber(value)} MHz`;
}

function formatDate(value) {
    if (!value) {
        return "-";
    }

    return new Date(value).toLocaleString("pt-BR");
}

function formatDuration(value) {
    if (value === null || value === undefined || value === "") {
        return "-";
    }

    const seconds = Number(value);
    if (Number.isNaN(seconds)) {
        return "-";
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
        return `${hours}h ${minutes}min`;
    }

    return `${minutes}min`;
}

export default App;
