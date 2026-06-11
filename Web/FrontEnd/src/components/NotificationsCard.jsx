import { useState, useEffect, useCallback } from 'react';
import { Icon } from '../shared/components/Icon';
import { api } from '../shared/services/api';

export function NotificationsCard() {
  const [values, setValues] = useState({ teams: true, email: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState('');
  const [error, setError] = useState('');

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.getNotifications();
      setValues({ teams: data.teams, email: data.email });
    } catch {
      // mantém defaults
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchNotifications(); }, [fetchNotifications]);

  const handleToggle = async (field) => {
    const next = !values[field];
    setValues((prev) => ({ ...prev, [field]: next }));
    setError('');
    setSaving(field);
    try {
      const data = await api.patchNotifications({ [field]: next });
      setValues({ teams: data.teams, email: data.email });
    } catch (e) {
      setValues((prev) => ({ ...prev, [field]: !next }));
      setError(e.message || 'Erro ao salvar');
    } finally {
      setSaving('');
    }
  };

  const toggles = [
    { label: 'Alertas no Teams', field: 'teams' },
    { label: 'Alertas por E-mail', field: 'email' },
  ];

  return (
    <div className="bg-card rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
        <Icon name="alert" size="text-lg" />
        Notificações
      </h3>
      {loading ? (
        <p className="text-sm text-page opacity-50">Carregando...</p>
      ) : (
        <div className="space-y-4">
          {toggles.map(({ label, field }) => (
            <div key={field} className="flex items-center justify-between">
              <p className="font-medium text-page">{label}</p>
              <button
                role="switch"
                aria-checked={values[field]}
                onClick={() => handleToggle(field)}
                disabled={saving === field}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  values[field] ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
                } ${saving === field ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    values[field] ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )}
    </div>
  );
}