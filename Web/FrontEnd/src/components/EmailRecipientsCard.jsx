import { useState, useEffect, useCallback } from 'react';
import { Icon } from '../shared/components/Icon';
import { api } from '../shared/services/api';

export function EmailRecipientsCard() {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [inputEmail, setInputEmail] = useState('');
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState('');
  const [error, setError] = useState('');

  const fetchRecipients = useCallback(async () => {
    try {
      const data = await api.getEmailRecipients();
      setRecipients(data.recipients || []);
    } catch {
      setRecipients([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchRecipients(); }, [fetchRecipients]);

  const handleAdd = async () => {
    const email = inputEmail.trim();
    if (!email) return;
    setSaving(true);
    setError('');
    try {
      const data = await api.addEmailRecipient(email);
      setRecipients(data.recipients || []);
      setInputEmail('');
      setAdding(false);
    } catch (e) {
      setError(e.message || 'Erro ao adicionar email');
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async (email) => {
    setRemoving(email);
    setError('');
    try {
      const data = await api.removeEmailRecipient(email);
      setRecipients(data.recipients || []);
    } catch (e) {
      setError(e.message || 'Erro ao remover email');
    } finally {
      setRemoving('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleAdd();
    if (e.key === 'Escape') { setAdding(false); setInputEmail(''); setError(''); }
  };

  return (
    <div className="bg-card rounded-lg shadow-md p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-page mb-1 flex items-center gap-2">
          <Icon name="alert" size="text-lg" />
          Destinatários de Email
        </h3>
        <p className="text-sm text-page opacity-70">
          Alertas de segurança serão enviados para estes endereços.
        </p>
      </div>

      {loading ? (
        <p className="text-sm text-page opacity-50">Carregando...</p>
      ) : (
        <div className="space-y-2">
          {recipients.length === 0 && !adding && (
            <p className="text-sm text-page opacity-50 py-1">Nenhum destinatário configurado.</p>
          )}
          {recipients.map((email) => (
            <div
              key={email}
              className="flex items-center justify-between px-3 py-2 rounded-lg border"
              style={{ borderColor: 'var(--card-border)' }}
            >
              <span className="text-sm font-mono text-page truncate flex-1 mr-2">{email}</span>
              <button
                onClick={() => handleRemove(email)}
                disabled={removing === email}
                className="flex-shrink-0 text-xs px-2 py-1 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40 transition-colors"
              >
                {removing === email ? '...' : 'Remover'}
              </button>
            </div>
          ))}
        </div>
      )}

      {adding ? (
        <div className="space-y-2">
          <input
            type="email"
            placeholder="email@exemplo.com"
            value={inputEmail}
            onChange={(e) => setInputEmail(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            className="w-full font-mono text-sm px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-page focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={saving || !inputEmail.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button
              onClick={() => { setAdding(false); setInputEmail(''); setError(''); }}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-page rounded-lg text-sm font-medium transition-colors hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Cancelar
            </button>
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      ) : (
        <button
          onClick={() => { setAdding(true); setError(''); }}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-sm text-page opacity-60 hover:opacity-100 hover:border-blue-400 dark:hover:border-blue-500 transition-all"
        >
          + Adicionar email
        </button>
      )}

      {error && !adding && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}