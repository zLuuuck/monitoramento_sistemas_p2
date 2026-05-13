export function Card({ title, value, unit, icon, color }) {
  const cores = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
  };

  const corEscolhida = cores[color] || cores.blue;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-500 text-sm">{title}</p>
          <p className="text-2xl md:text-3xl font-bold text-gray-800 break-words">
            {value} <span className="text-lg font-normal">{unit}</span>
          </p>
        </div>
        <div className={`${corEscolhida} p-3 rounded-full text-2xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
