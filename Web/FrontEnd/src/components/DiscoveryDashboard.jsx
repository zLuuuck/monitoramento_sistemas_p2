import { Card } from '../shared/components/Card';
import { Icon } from '../shared/components/Icon';

export function DiscoveryDashboard({ discovery }) {
  const redes = normalizeNetworks(discovery?.networks);
  const discos = Array.isArray(discovery?.disks) ? discovery.disks : [];
  const memoryModules = normalizeMemoryModules(discovery?.memories);
  const isPhysicalHost = discovery && !discovery.is_virtualized;

  return (
    <div className="space-y-6">
      {/* Card principal do host */}
      <div className="bg-[#1A1A2E] rounded-xl border border-[#2D2D44] shadow-lg p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-xl font-bold text-[#E2E2E8]">
                {discovery.host?.hostname || `Host ${discovery.host_id}`}
              </h3>
              <span className={`rounded-md px-2 py-1 text-xs font-semibold ${discovery.host?.status === 'online' ? 'bg-[#10B981] text-white' : 'bg-[#4B5563] text-[#E2E2E8]'}`}>
                {discovery.host?.status || 'offline'}
              </span>
              <span className="rounded-md bg-[#4B2D6E] px-2 py-1 text-xs font-semibold text-[#A855F7]">
                {discovery.is_virtualized ? 'Virtual' : 'Fisico'}
              </span>
            </div>
            <p className="mt-1 text-sm text-[#8B8B9D]">
              {discovery.host?.ip_address || 'IP nao informado'} | Discovery em {formatDate(discovery.discovery_date)}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4 xl:min-w-[520px]">
            <MiniStat label="CPU" value={discovery.cpu_cores || '-'} detail={discovery.is_virtualized ? 'vCPUs' : 'nucleos'} />
            <MiniStat label="RAM" value={formatNumber(discovery.total_memory_gb)} detail="GB" />
            <MiniStat label="Disco" value={formatStorage(discovery.disk_total_gb)} detail={`${discos.length} unidade${discos.length === 1 ? '' : 's'}`} />
            <MiniStat label="Rede" value={redes.length} detail={redes.length === 1 ? 'interface' : 'interfaces'} />
          </div>
        </div>
      </div>

      {/* Cards de métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        <Card
          title="CPU"
          value={discovery.cpu_cores || '-'}
          unit={discovery.is_virtualized ? 'vCPUs' : 'nucleos'}
          iconName="cpu"
          color="blue"
          subtitle={discovery.cpu_model || 'Modelo nao informado'}
        >
          <Details>
            <Info label="Clock base" value={formatMhz(discovery.cpu_clock_base_mhz)} compact />
            <Info label="Clock maximo" value={formatMhz(discovery.cpu_max_mhz)} compact />
          </Details>
        </Card>

        <Card
          title="Memoria"
          value={formatNumber(discovery.total_memory_gb)}
          unit="GB"
          iconName="memory"
          color="green"
          subtitle={memorySummary(discovery.memories)}
        >
          <Details>
            <Info label="Swap" value={formatBytes(discovery.memories?.swap_total_bytes)} compact />
            <Info label="Slots usados" value={formatSlots(discovery.memories?.slots)} compact />
          </Details>
        </Card>

        <Card
          title="Disco"
          value={formatStorage(discovery.disk_total_gb)}
          unit=""
          iconName="disk"
          color="yellow"
          subtitle={`${discos.length} disco${discos.length === 1 ? '' : 's'} identificado${discos.length === 1 ? '' : 's'}`}
        >
          <Details>
            <Info label="Maior disco" value={formatStorage(maxDiskSize(discos))} compact />
            <Info label="Tipos" value={uniqueValues(discos.map((disk) => disk.type)).join(', ') || '-'} compact />
          </Details>
        </Card>

        <Card
          title="Rede"
          value={redes.length}
          unit={redes.length === 1 ? 'interface' : 'interfaces'}
          iconName="network"
          color="purple"
          subtitle={defaultGatewayLabel(discovery.networks)}
        >
          <Details>
            <Info label="Interfaces ativas" value={redes.filter((item) => item.state === 'UP').length} compact />
            <Info label="IPs encontrados" value={redes.flatMap(getInterfaceIps).length} compact />
          </Details>
        </Card>
      </div>

      {/* Detalhes do sistema */}
      <Panel title="Detalhes do sistema">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          <Info label="Hostname" value={discovery.host?.hostname} />
          <Info label="IP principal" value={discovery.host?.ip_address} />
          <Info label="Data do discovery" value={formatDate(discovery.discovery_date)} />
          <Info label="Sistema operacional" value={discovery.os_name} />
          <Info label="Versao do SO" value={discovery.os_version} />
          <Info label="Kernel" value={discovery.kernel_release} />
          <Info label="Uptime" value={formatDuration(discovery.uptime_seconds)} />
          <Info label="Virtualizacao" value={discovery.is_virtualized ? 'Sim' : 'Nao'} />
          <Info label="Hypervisor" value={discovery.hypervisor || 'Nao informado'} />
        </div>
      </Panel>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <DiskList disks={discos} />
        <NetworkList networks={redes} />
      </div>

      {isPhysicalHost && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <MemoryDetails memories={discovery.memories} modules={memoryModules} />
          <MotherboardDetails motherboard={discovery.motherboard} />
        </div>
      )}
    </div>
  );
}

export function MetricCards({ latestMetric }) {
  const cards = [
    {
      title: 'CPU',
      value: formatPercent(latestMetric?.cpu_percent),
      unit: '%',
      iconName: 'cpu',
      color: 'blue',
      subtitle: 'Uso atual',
    },
    {
      title: 'Memoria',
      value: formatPercent(latestMetric?.memory_percent),
      unit: '%',
      iconName: 'memory',
      color: 'green',
      subtitle: 'Uso atual',
    },
    {
      title: 'Disco',
      value: formatPercent(latestMetric?.disk_percent),
      unit: '%',
      iconName: 'disk',
      color: 'yellow',
      subtitle: 'Uso atual',
    },
    {
      title: 'Rede',
      value: formatBytes(latestMetric?.net_recv) || '-',
      unit: '',
      iconName: 'network',
      color: 'purple',
      subtitle: `Recebido${latestMetric?.net_sent ? ` | enviado ${formatBytes(latestMetric.net_sent)}` : ''}`,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
      {cards.map((card) => (
        <Card key={card.title} {...card} />
      ))}
    </div>
  );
}

function MiniStat({ label, value, detail }) {
  return (
    <div className="rounded-lg border border-[#2D2D44] bg-[#1A1A2E] p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-[#8B8B9D]">{label}</p>
      <p className="mt-1 text-lg font-bold text-[#E2E2E8]">{value}</p>
      <p className="text-xs text-[#8B8B9D]">{detail}</p>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="bg-[#1A1A2E] rounded-xl border border-[#2D2D44] shadow-lg p-6">
      <h3 className="text-lg font-semibold text-[#E2E2E8] mb-4 flex items-center gap-2">
        <Icon name="info" size="text-lg" />
        {title}
      </h3>
      {children}
    </div>
  );
}

function Details({ children }) {
  return <div className="grid grid-cols-1 gap-2 text-sm">{children}</div>;
}

function Info({ label, value, compact = false }) {
  return (
    <div className={`${compact ? '' : 'border border-[#2D2D44] rounded-lg p-3 bg-[#1A1A2E]'}`}>
      <p className="text-xs font-medium uppercase tracking-wide text-[#8B8B9D]">{label}</p>
      <p className="font-semibold text-[#E2E2E8] break-words">{isEmpty(value) ? '-' : value}</p>
    </div>
  );
}

function DiskList({ disks }) {
  return (
    <Panel title="Discos">
      {disks.length === 0 ? (
        <p className="text-sm text-[#8B8B9D]">Nenhum disco informado.</p>
      ) : (
        <div className="space-y-3">
          {disks.map((disk, index) => (
            <div key={disk.device || disk.serial || index} className="border border-[#2D2D44] rounded-lg p-4 bg-[#1A1A2E]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-[#E2E2E8]">{disk.device || `Disco ${index + 1}`}</p>
                  <p className="text-sm text-[#8B8B9D]">{disk.model || disk.vendor || 'Modelo nao informado'}</p>
                </div>
                <span className="rounded-md bg-[#4B2D6E] px-3 py-1 text-sm font-semibold text-[#A855F7]">
                  {formatStorage(getDiskSizeGb(disk))}
                </span>
              </div>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                <Info label="Tipo" value={disk.type} compact />
                <Info label="Interface" value={disk.interface} compact />
                <Info label="Saude" value={formatDiskHealth(disk.health)} compact />
                <Info label="Serial" value={disk.serial} compact />
                <Info label="Firmware" value={disk.firmware} compact />
              </div>
              <PartitionList partitions={disk.partitions} />
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}

function PartitionList({ partitions, level = 0 }) {
  if (!Array.isArray(partitions) || partitions.length === 0) {
    return null;
  }

  return (
    <div className={`${level === 0 ? 'mt-4 border-t border-[#2D2D44] pt-3' : 'mt-2 ml-4 border-l border-[#2D2D44] pl-3'}`}>
      {level === 0 && (
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[#8B8B9D]">Particoes</p>
      )}
      <div className="space-y-2">
        {partitions.map((partition, index) => (
          <div key={`${partition.name || 'partition'}-${index}`} className="rounded-md bg-[#1A1A2E] p-3 border border-[#2D2D44]">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-semibold text-[#E2E2E8]">{partition.name || `Particao ${index + 1}`}</p>
                <p className="text-xs text-[#8B8B9D]">
                  {[partition.type, partition.fstype, partition.mountpoint].filter(Boolean).join(' | ') || 'Sem montagem informada'}
                </p>
              </div>
              <span className="rounded-md bg-[#4B2D6E] px-2 py-1 text-sm font-semibold text-[#A855F7]">
                {formatStorage(getPartitionSizeGb(partition))}
              </span>
            </div>
            <PartitionList partitions={partition.children} level={level + 1} />
          </div>
        ))}
      </div>
    </div>
  );
}

function NetworkList({ networks }) {
  return (
    <Panel title="Redes">
      {networks.length === 0 ? (
        <p className="text-sm text-[#8B8B9D]">Nenhuma interface informada.</p>
      ) : (
        <div className="space-y-3">
          {networks.map((network, index) => {
            const ips = getInterfaceIps(network);
            return (
              <div key={network.name || network.mac || index} className="border border-[#2D2D44] rounded-lg p-4 bg-[#1A1A2E]">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-[#E2E2E8]">{network.name || `Interface ${index + 1}`}</p>
                    <p className="text-sm text-[#8B8B9D]">{network.mac || 'MAC nao informado'}</p>
                  </div>
                  <span className={`rounded-md px-3 py-1 text-sm font-semibold ${network.state === 'UP' ? 'bg-[#10B981] text-white' : 'bg-[#4B5563] text-[#E2E2E8]'}`}>
                    {network.state || 'N/A'}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Info label="IP" value={ips.join(', ') || 'Sem IP'} compact />
                  <Info label="Driver" value={network.driver} compact />
                  <Info label="MTU" value={network.mtu} compact />
                  <Info label="Barramento" value={network.bus_info} compact />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Panel>
  );
}

function MemoryDetails({ memories, modules }) {
  const slots = memories?.slots || {};

  return (
    <Panel title="Memoria RAM fisica">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <Info label="Total" value={formatBytes(memories?.total_bytes) || `${formatNumber(memories?.total_gb)} GB`} />
        <Info label="Slots totais" value={slots.total} />
        <Info label="Slots livres" value={slots.free} />
      </div>
      {modules.length === 0 ? (
        <p className="text-sm text-[#8B8B9D]">Nenhum modulo de memoria informado.</p>
      ) : (
        <div className="space-y-3">
          {modules.map((module, index) => (
            <div key={module.locator || index} className="border border-[#2D2D44] rounded-lg p-4 bg-[#1A1A2E]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-[#E2E2E8]">{module.locator || `Slot ${index + 1}`}</p>
                  <p className="text-sm text-[#8B8B9D]">{module.bank_locator || 'Banco nao informado'}</p>
                </div>
                <span className="rounded-md bg-[#4B2D6E] px-3 py-1 text-sm font-semibold text-[#A855F7]">
                  {module.populated ? formatMemoryModuleSize(module) : 'Vazio'}
                </span>
              </div>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                <Info label="Tipo" value={module.type} compact />
                <Info label="Velocidade" value={module.speed_mhz ? `${module.speed_mhz} MHz` : null} compact />
                <Info label="Fabricante" value={module.manufacturer} compact />
                <Info label="Part number" value={module.part_number} compact />
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}

function MotherboardDetails({ motherboard }) {
  if (!motherboard) {
    return (
      <Panel title="Placa mae">
        <p className="text-sm text-[#8B8B9D]">Nenhuma informacao de placa mae foi informada.</p>
      </Panel>
    );
  }

  return (
    <Panel title="Placa mae">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Info label="Fabricante" value={motherboard.manufacturer} />
        <Info label="Modelo" value={motherboard.product_name} />
        <Info label="Versao" value={motherboard.version} />
        <Info label="Chipset" value={motherboard.chipset} />
        <Info label="BIOS" value={formatBios(motherboard.bios)} />
        <Info label="Sockets CPU" value={formatSlots(motherboard.cpu_sockets)} />
        <Info label="Slots RAM" value={formatSlots(motherboard.ram_slots)} />
        <Info label="Slots expansao" value={formatExpansionSlots(motherboard.expansion_slots)} />
      </div>
    </Panel>
  );
}

// ==================== FUNÇÕES AUXILIARES (mantidas iguais) ====================

function normalizeNetworks(networks) {
  if (Array.isArray(networks?.interfaces)) {
    return networks.interfaces;
  }
  if (Array.isArray(networks)) {
    return networks;
  }
  return [];
}

function normalizeMemoryModules(memories) {
  const modules = memories?.slots?.modules;
  return Array.isArray(modules) ? modules : [];
}

function getInterfaceIps(network) {
  const ipv4 = Array.isArray(network?.ipv4) ? network.ipv4 : [];
  return ipv4.map((ip) => ip.prefix ? `${ip.address}/${ip.prefix}` : ip.address).filter(Boolean);
}

function getDiskSizeGb(disk) {
  return disk?.size?.gb || disk?.size_gb || bytesToGb(disk?.size_bytes || disk?.size?.bytes);
}

function getPartitionSizeGb(partition) {
  return partition?.size?.gb || partition?.size_gb || bytesToGb(partition?.size_bytes || partition?.size?.bytes);
}

function maxDiskSize(disks) {
  return disks.reduce((max, disk) => Math.max(max, Number(getDiskSizeGb(disk) || 0)), 0);
}

function uniqueValues(values) {
  return [...new Set(values.filter(Boolean))];
}

function memorySummary(memories) {
  const slots = memories?.slots;
  if (!slots) {
    return 'Detalhes de slots indisponiveis';
  }
  return `${slots.used ?? '-'} de ${slots.total ?? '-'} slots usados`;
}

function defaultGatewayLabel(networks) {
  const gateway = networks?.default_gateway;
  if (!gateway?.gateway) {
    return 'Gateway padrao nao informado';
  }
  return `${gateway.gateway}${gateway.interface ? ` via ${gateway.interface}` : ''}`;
}

function formatDiskHealth(health) {
  if (!health) {
    return null;
  }
  if (typeof health.smart_passed === 'boolean') {
    return health.smart_passed ? 'SMART OK' : 'SMART com alerta';
  }
  return null;
}

function formatMemoryModuleSize(module) {
  if (module.size_gb) {
    return `${formatNumber(module.size_gb)} GB`;
  }
  if (module.size_mb) {
    return formatStorage(Number(module.size_mb) / 1024);
  }
  return '-';
}

function formatSlots(slots) {
  if (!slots) {
    return null;
  }
  const total = slots.total ?? '-';
  const used = slots.used ?? slots.populated ?? '-';
  const free = slots.free;
  return free === undefined ? `${used}/${total}` : `${used}/${total} usados, ${free} livres`;
}

function formatBios(bios) {
  if (!bios) {
    return null;
  }
  return [bios.vendor, bios.version, bios.release_date].filter(Boolean).join(' | ');
}

function formatExpansionSlots(slots) {
  if (!Array.isArray(slots) || slots.length === 0) {
    return null;
  }
  const used = slots.filter((slot) => slot.current_usage === 'In Use').length;
  return `${used}/${slots.length} em uso`;
}

function formatPercent(value) {
  if (isEmpty(value)) {
    return '-';
  }
  return Number(value).toFixed(1);
}

function formatNumber(value) {
  if (isEmpty(value)) {
    return '-';
  }
  return Number(value).toLocaleString('pt-BR', {
    maximumFractionDigits: 2,
  });
}

function formatStorage(valueGb) {
  if (isEmpty(valueGb)) {
    return '-';
  }
  const gb = Number(valueGb);
  if (gb >= 1024) {
    return `${formatNumber(gb / 1024)} TB`;
  }
  return `${formatNumber(gb)} GB`;
}

function formatBytes(value) {
  if (isEmpty(value)) {
    return null;
  }
  const bytes = Number(value);
  const gb = bytes / (1024 ** 3);
  if (gb >= 1) {
    return `${formatNumber(gb)} GB`;
  }
  const mb = bytes / (1024 ** 2);
  return `${formatNumber(mb)} MB`;
}

function formatMhz(value) {
  if (isEmpty(value)) {
    return '-';
  }
  return `${formatNumber(value)} MHz`;
}

function formatDate(value) {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleString('pt-BR');
}

function formatDuration(value) {
  if (isEmpty(value)) {
    return '-';
  }
  const totalSeconds = Number(value);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  return [
    days ? `${days}d` : null,
    hours ? `${hours}h` : null,
    `${minutes}min`,
  ].filter(Boolean).join(' ');
}

function bytesToGb(value) {
  if (isEmpty(value)) {
    return null;
  }
  return Number(value) / (1024 ** 3);
}

function isEmpty(value) {
  return value === null || value === undefined || value === '';
}