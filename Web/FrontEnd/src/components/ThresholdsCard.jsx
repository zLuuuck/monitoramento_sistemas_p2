import { useState, useEffect, useCallback } from 'react';
import { Icon } from '../shared/components/Icon';
import { api } from '../shared/services/api';

function ThresholdsCard() {
  const [values, setValues] = useState({ cpu: '', mem: '', disk: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const fetchThresholds = useCallback(async () => {
    try {
      const data = await api.getThresholds();
      setValues({ cpu: String(data.cpu), mem: String(data.mem), disk: String(data.disk) });
    } catch {
      setValues({ cpu: '80', mem: '80', disk: '80' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchThresholds(); }, [fetchThresholds]);

  const handleChange = (field) => (e) => {
    setValues((prev) => ({ ...prev, [field]: e.target.value }));
    setError('');
    setSuccess(false);
  };

  const validate = () => {
    const erros = [];
    for (const [label, field] of [['CPU', 'cpu'], ['RAM', 'mem'], ['Disco', 'disk']]) {
      const n = parseInt(values[field], 10);
      if (isNaN(n) || n < 1 || n > 99) erros.push(`${label}: valor deve ser entre 1 e 99`);
    }
    return erros;
  };

  const handleSave = async () => {
    const erros = validate();
    if (erros.length) { setError(erros.join('; ')); return; }
    setSaving(true);
    setError('');
    setSuccess(false);
    try {
      const data = await api.patchThresholds({
        cpu: parseInt(values.cpu, 10),
        mem: parseInt(values.mem, 10),
        disk: parseInt(values.disk, 10),
      });
      setValues({ cpu: String(data.cpu), mem: String(data.mem), disk: String(data.disk) });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e) {
      setError(e.message || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const campos = [
    { label: 'CPU', field: 'cpu' },
    { label: 'RAM', field: 'mem' },
    { label: 'Disco', field: 'disk' },
  ];

  return (
    <div className="bg-card rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
        <Icon name="chart" size="text-lg" />
        Monitoramento
      </h3>
      {loading ? (
        <p className="text-sm text-page opacity-50">Carregando...</p>
      ) : (
        <div className="space-y-4">
          {campos.map(({ label, field }) => (
            <div key={field} className="flex items-center justify-between gap-4">
              <div>
                <p className="font-medium text-page">{label}</p>
                <p className="text-sm text-page opacity-70">Limite para alerta (%)</p>
              </div>
              <input
                type="number"
                min="1"
                max="99"
                value={values[field]}
                onChange={handleChange(field)}
                className="w-20 text-center px-2 py-1 border rounded-lg bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-page"
              />
            </div>
          ))}
          <div className="pt-2 flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            {success && <span className="text-sm text-green-600 dark:text-green-400">Salvo!</span>}
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )}
    </div>
  );
}

export default ThresholdsCard;