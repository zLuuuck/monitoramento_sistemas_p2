import { Icon } from '../shared/components/Icon';

export function HeaderInfo({ host, type, onVerMais }) {
  return (
    <div className="flex justify-between items-center mb-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Icon name={type === 'physical' ? 'physical' : 'virtual'} size="text-2xl" />
          {host?.name}
          <span className={`text-sm px-2 py-1 rounded-full ${host?.status === 'online' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {host?.status === 'online' ? 'Online' : 'Offline'}
          </span>
        </h2>
        <p className="text-gray-500 text-sm mt-1">
          IP: {host?.ip} • Tipo: {type === 'physical' ? 'Hardware Físico' : 'Virtualizado'}
        </p>
      </div>
      
      <button
        onClick={onVerMais}
        className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
      >
        <Icon name="info" size="text-sm" />
        Ver detalhes
      </button>
    </div>
  );
}