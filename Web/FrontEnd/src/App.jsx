import { useState } from "react";
import "./App.css";
import { useEffect } from "react";
import { Layout } from "./shared/components/Layout";
import { Card } from "./shared/components/Card";
import { LogsPlaceholder } from "./features/logs_feat/components/LogsPlaceholder";
import { MetricsChart } from "./features/metrics/components/MetricsChart";
import { api } from "./shared/services/api";

function App() {
    const [selectedHost, setSelectedHost] = useState("");
    const [metrics, setMetrics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [metricsError, setMetricsError] = useState("");
    const [discovery, setDiscovery] = useState([]);
    const [discoveryLoading, setDiscoveryLoading] = useState(true);
    const [discoveryError, setDiscoveryError] = useState("");
    const [hostStatusById, setHostStatusById] = useState({});
    const [discoveryPayload, setDiscoveryPayload] = useState("");
    const [postingDiscovery, setPostingDiscovery] = useState(false);
    const [postDiscoveryMessage, setPostDiscoveryMessage] = useState("");

    const carregarDiscovery = async ({ selecionarPrimeiro = false, silent = false } = {}) => {
        try {
            if (!silent) {
                setDiscoveryLoading(true);
            }
            setDiscoveryError("");
            const dados = await api.getDiscovery();
            setDiscovery((atuais) => sameDiscovery(atuais, dados) ? atuais : dados);

            if (dados.length > 0 && selecionarPrimeiro) {
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

        return undefined;
    }, []);

    // Carregar métricas quando mudar o host
    useEffect(() => {
        const carregarMetricas = async ({ silent = false } = {}) => {
            if (!selectedHost) {
                setMetrics([]);
                setLoading(false);
                return;
            }

            try {
                if (!silent) {
                    setLoading(true);
                }
                setMetricsError("");
                const resposta = await api.getMetrics(selectedHost);
                const dados = resposta.metrics || [];
                setMetrics((atuais) => sameMetrics(atuais, dados) ? atuais : dados);
                setHostStatusById((atuais) => {
                    const proximo = {
                        status: resposta.status || "offline",
                        isOnline: Boolean(resposta.is_online),
                        lastMetricAt: resposta.last_metric_at,
                    };

                    return sameJson(atuais[selectedHost], proximo)
                        ? atuais
                        : { ...atuais, [selectedHost]: proximo };
                });
            } catch (error) {
                if (!silent) {
                    setMetrics([]);
                }
                setMetricsError(error.message);
            } finally {
                if (!silent) {
                    setLoading(false);
                }
            }
        };

        carregarMetricas();
        const intervalId = window.setInterval(
            () => carregarMetricas({ silent: true }),
            5000,
        );

        return () => window.clearInterval(intervalId);
    }, [selectedHost]);

    // Pega a última métrica (mais recente)
    const ultimaMetrica = metrics[metrics.length - 1];
    const hostsDisponiveis =
        discovery.length > 0
            ? discovery.map((item) => ({
                id: String(item.host_id),
                name: item.host?.hostname || `Host ${item.host_id}`,
                status: hostStatusById[String(item.host_id)]?.status || item.host?.status || "offline",
                isOnline: hostStatusById[String(item.host_id)]?.isOnline ?? Boolean(item.host?.is_online),
                ip: item.host?.ip_address,
            }))
            : [];
    const selectedDiscovery = discovery.find(
        (item) => String(item.host_id) === selectedHost,
    );
    const selectedHostInfo = hostsDisponiveis.find(
        (host) => host.id === selectedHost,
    );
    const hostIsVirtualized = isTruthy(selectedDiscovery?.is_virtualized);
    const selectedDisks = parseJsonValue(selectedDiscovery?.disks);
    const selectedNetworks = parseJsonValue(selectedDiscovery?.networks);
    const selectedMemories = parseJsonValue(selectedDiscovery?.memories);
    const selectedMotherboard = parseJsonValue(selectedDiscovery?.motherboard);
    const discos = Array.isArray(selectedDisks)
        ? selectedDisks
        : [];
    const redes = Array.isArray(selectedNetworks?.interfaces)
        ? selectedNetworks.interfaces
        : Array.isArray(selectedNetworks)
            ? selectedNetworks
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
                        {hostsDisponiveis.length === 0 && (
                            <option value="">Nenhum host cadastrado</option>
                        )}
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

            {!loading && metricsError && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-8">
                    Nao foi possivel carregar metricas: {metricsError}
                </div>
            )}

            {!loading && !metricsError && metrics.length === 0 && selectedDiscovery && (
                <div className="bg-white rounded-lg shadow-md p-6 text-gray-500 mb-8">
                    Nenhuma metrica recebida para este host ainda.
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
                        value={formatPercent(ultimaMetrica.cpu_percent)}
                        unit="%"
                        icon="⚡"
                        color="blue"
                    />
                    <Card
                        title="Memória"
                        value={formatPercent(ultimaMetrica.memory_percent)}
                        unit="%"
                        icon="🧠"
                        color="green"
                    />
                    <Card
                        title="Status"
                        value={selectedHostInfo?.isOnline ? "Online" : "Offline"}
                        unit=""
                        icon={selectedHostInfo?.isOnline ? "🟢" : "🔴"}
                        color={selectedHostInfo?.isOnline ? "green" : "red"}
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
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
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
                                value={hostIsVirtualized ? "Sim" : "Nao"}
                                unit=""
                                icon="🖥️"
                                color={hostIsVirtualized ? "green" : "blue"}
                            />
                            <Card
                                title="Status"
                                value={selectedHostInfo?.isOnline ? "Online" : "Offline"}
                                unit=""
                                icon={selectedHostInfo?.isOnline ? "🟢" : "🔴"}
                                color={selectedHostInfo?.isOnline ? "green" : "red"}
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
                                {hostIsVirtualized && (
                                    <Info
                                        label="Hypervisor"
                                        value={selectedDiscovery.hypervisor || "Nao informado"}
                                    />
                                )}
                                <Info label="Sistema operacional" value={selectedDiscovery.os_name} />
                                <Info label="Versao do OS" value={selectedDiscovery.os_version} />
                                <Info label="Kernel" value={selectedDiscovery.kernel_release} />
                                <Info
                                    label="Uptime"
                                    value={formatDuration(selectedDiscovery.uptime_seconds)}
                                />
                            </div>
                        </div>

                        {!hostIsVirtualized && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <MemoryDetails memory={selectedMemories} />
                                <MotherboardDetails motherboard={selectedMotherboard} />
                            </div>
                        )}

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <DiskList items={discos} />
                            <NetworkList items={redes} />
                        </div>
                    </div>
                )}
            </section>

            {/* Logs */}
            <LogsPlaceholder />
        </Layout>
    );
}

function sameMetrics(current, next) {
    if (current.length !== next.length) {
        return false;
    }

    const currentLast = current[current.length - 1];
    const nextLast = next[next.length - 1];

    return currentLast?.id === nextLast?.id
        && currentLast?.timestamp === nextLast?.timestamp;
}

function sameJson(current, next) {
    return JSON.stringify(current) === JSON.stringify(next);
}

function sameDiscovery(current, next) {
    return sameJson(
        current.map(discoveryComparable),
        next.map(discoveryComparable),
    );
}

function discoveryComparable(item) {
    return {
        ...item,
        host: item.host
            ? {
                ...item.host,
                last_seen: undefined,
            }
            : item.host,
    };
}

function parseJsonValue(value) {
    if (typeof value !== "string") {
        return value;
    }

    try {
        const parsed = JSON.parse(value);
        return typeof parsed === "string" ? parseJsonValue(parsed) : parsed;
    } catch {
        return value;
    }
}

function isTruthy(value) {
    if (typeof value === "string") {
        return value.toLowerCase() === "true";
    }

    return Boolean(value);
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

function DiskList({ items }) {
    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Discos</h3>
            {items.length === 0 ? (
                <p className="text-sm text-gray-500">Nenhum disco informado</p>
            ) : (
                <div className="space-y-3">
                    {items.map((item, index) => (
                        <div
                            key={item.device || index}
                            className="border border-gray-200 rounded-lg p-3"
                        >
                            <p className="font-medium text-gray-800">
                                {item.device || `Disco ${index + 1}`}
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 text-sm">
                                <Info label="Modelo" value={item.model} />
                                <Info label="Tipo" value={item.type} />
                                <Info label="Interface" value={item.interface} />
                                <Info label="Tamanho" value={formatBytesAsGb(item.size_bytes || item.size?.bytes)} />
                                <Info label="Serial" value={item.serial} />
                                <Info label="Firmware" value={item.firmware} />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function NetworkList({ items }) {
    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Redes</h3>
            {items.length === 0 ? (
                <p className="text-sm text-gray-500">Nenhuma interface informada</p>
            ) : (
                <div className="space-y-3">
                    {items.map((item, index) => (
                        <div
                            key={item.name || item.interface || index}
                            className="border border-gray-200 rounded-lg p-3"
                        >
                            <p className="font-medium text-gray-800">
                                {item.name || item.interface || `Interface ${index + 1}`}
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 text-sm">
                                <Info label="Estado" value={item.state} />
                                <Info label="MAC" value={item.mac} />
                                <Info label="IPv4" value={formatInterfaceAddresses(item, "ipv4")} />
                                <Info label="IPv6" value={formatInterfaceAddresses(item, "ipv6")} />
                                <Info label="Driver" value={item.driver} />
                                <Info label="MTU" value={item.mtu} />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function MemoryDetails({ memory }) {
    const slots = memory?.slots || {};
    const modules = Array.isArray(slots.modules) ? slots.modules : [];

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Memória RAM</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm mb-4">
                <Info label="Total" value={formatBytesAsGb(memory?.total_bytes)} />
                <Info label="Slots usados" value={slots.used} />
                <Info label="Slots livres" value={slots.free} />
            </div>
            {modules.length === 0 ? (
                <p className="text-sm text-gray-500">Nenhum módulo informado</p>
            ) : (
                <div className="space-y-3">
                    {modules.map((module, index) => (
                        <div key={module.locator || index} className="border border-gray-200 rounded-lg p-3">
                            <p className="font-medium text-gray-800">
                                {module.locator || `Slot ${index + 1}`}
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 text-sm">
                                <Info label="Populado" value={module.populated ? "Sim" : "Nao"} />
                                <Info label="Tamanho" value={module.size_mb ? `${formatNumber(module.size_mb / 1024)} GB` : "-"} />
                                <Info label="Tipo" value={module.type} />
                                <Info label="Fabricante" value={module.manufacturer} />
                                <Info label="Part number" value={module.part_number} />
                                <Info label="Velocidade" value={formatMhz(module.speed_mhz)} />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function MotherboardDetails({ motherboard }) {
    const bios = motherboard?.bios || {};
    const ramSlots = motherboard?.ram_slots || {};

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Placa-mãe</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <Info label="Fabricante" value={motherboard?.manufacturer} />
                <Info label="Modelo" value={motherboard?.product_name} />
                <Info label="Versão" value={motherboard?.version} />
                <Info label="Serial" value={motherboard?.serial_number} />
                <Info label="Chipset" value={motherboard?.chipset} />
                <Info label="BIOS" value={[bios.vendor, bios.version].filter(Boolean).join(" ") || "-"} />
                <Info label="Data da BIOS" value={bios.release_date} />
                <Info label="Slots RAM" value={ramSlots.total ? `${ramSlots.used || 0}/${ramSlots.total} usados` : "-"} />
            </div>
        </div>
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

function formatBytesAsGb(value) {
    if (value === null || value === undefined || value === "") {
        return "-";
    }

    const number = Number(value);
    if (Number.isNaN(number)) {
        return "-";
    }

    return `${formatNumber(number / (1024 ** 3))} GB`;
}

function formatAddresses(addresses) {
    const normalized = normalizeAddresses(addresses);

    if (normalized.length === 0) {
        return "-";
    }

    return normalized
        .map((item) => {
            if (!item.address) {
                return null;
            }
            return item.prefix !== undefined
                ? `${item.address}/${item.prefix}`
                : item.address;
        })
        .filter(Boolean)
        .join(", ") || "-";
}

function formatInterfaceAddresses(item, version) {
    const candidates = version === "ipv4"
        ? [
            item.ipv4,
            item.ipv4_addresses,
            item.addresses?.ipv4,
            item.addresses_v4,
            item.ip,
            item.address,
        ]
        : [
            item.ipv6,
            item.ipv6_addresses,
            item.addresses?.ipv6,
            item.addresses_v6,
        ];

    for (const candidate of candidates) {
        const formatted = formatAddresses(candidate);
        if (formatted !== "-") {
            return formatted;
        }
    }

    return "-";
}

function normalizeAddresses(addresses) {
    addresses = parseJsonValue(addresses);

    if (!addresses) {
        return [];
    }

    if (typeof addresses === "string") {
        return addresses.trim() ? [{ address: addresses }] : [];
    }

    if (!Array.isArray(addresses)) {
        if (addresses.address || addresses.ip) {
            return [{ ...addresses, address: addresses.address || addresses.ip }];
        }

        return Object.values(addresses).flatMap(normalizeAddresses);
    }

    return addresses
        .map((item) => {
            if (typeof item === "string") {
                return { address: item };
            }
            return item;
        })
        .filter(Boolean);
}

function formatPercent(value) {
    if (value === null || value === undefined || value === "") {
        return "-";
    }

    const number = Number(value);
    if (Number.isNaN(number)) {
        return "-";
    }

    return number.toFixed(1);
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
