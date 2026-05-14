import { Icon } from '../shared/components/Icon';

export function HostSelector({ hosts, selectedHost, onSelect }) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-gray-600 text-sm font-medium">Host:</label>
      <select
        value={selectedHost}
        onChange={(e) => onSelect(e.target.value)}
        className="border border-gray-300 rounded-lg px-4 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {hosts.map((host) => (
          <option key={host.id} value={host.id}>
            {host.name} {host.status === 'offline' && '(Offline)'}
          </option>
        ))}
      </select>
    </div>
  );
}