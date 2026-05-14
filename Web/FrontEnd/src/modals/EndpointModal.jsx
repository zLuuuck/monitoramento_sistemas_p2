import { Icon } from '../shared/components/Icon';

export function EndpointModal({ data, onClose }) {
  if (!data) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${data.type === 'physical' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'}`}>
              <Icon name={data.type === 'physical' ? 'physical' : 'virtual'} size="text-sm" />
            </div>
            <span className="font-semibold text-gray-800">{data.name}</span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          {/* Status e IP */}
          <div className="flex justify-between items-center bg-gray-50 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${data.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm">{data.status === 'online' ? 'Online' : 'Offline'}</span>
            </div>
            <div><span className="text-xs text-gray-400">IP:</span> <span className="text-sm font-mono">{data.ip}</span></div>
          </div>

          {/* Métricas */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Métricas</h4>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-sm"><span>CPU</span><span>{data.metrics?.cpu_percent.toFixed(1)}%</span></div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-0.5"><div className="bg-blue-500 rounded-full h-1.5" style={{ width: `${data.metrics?.cpu_percent || 0}%` }}></div></div>
              </div>
              <div>
                <div className="flex justify-between text-sm"><span>Memória</span><span>{data.metrics?.memory_percent.toFixed(1)}%</span></div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-0.5"><div className="bg-green-500 rounded-full h-1.5" style={{ width: `${data.metrics?.memory_percent || 0}%` }}></div></div>
              </div>
            </div>
          </div>

          {/* Última atualização */}
          <div className="text-center pt-2"><p className="text-xs text-gray-400">Última atualização: {data.lastUpdate}</p></div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-100">
          <button onClick={onClose} className="w-full py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors text-sm">Fechar</button>
        </div>
      </div>
    </div>
  );
}