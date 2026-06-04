import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { DiscoveryDashboard, MetricCards } from '../components/DiscoveryDashboard';
import { MetricsChart } from '../features/metrics/components/MetricsChart';
import { LogsPanel } from '../features/logs_feat/components/LogsPanel';
import AlertsPanel from '../features/alerts/components/AlertsPanel';
import { Icon } from '../shared/components/Icon';
import { useTheme } from '../contexts/ThemeContext';
import { api, saveApiKey, hasBrowserApiKey } from '../shared/services/api';

// ==================== COMPONENTE INTERNO ====================

function ApiKeyCard() {
  const [keyInfo, setKeyInfo] = useState(null);
  const [generatedKey, setGeneratedKey] = useState('');
  const [copied, setCopied] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [browserKeyStored, setBrowserKeyStored] = useState(() => hasBrowserApiKey());
  const [inputKey, setInputKey] = useState('');
  const [browserKeySaved, setBrowserKeySaved] = useState(false);

  const fetchKeyInfo = useCallback(async () => {
    try {
      const data = await api.getApiKey();
      setKeyInfo(data);
    } catch {
      setKeyInfo({ configured: false, key_prefix: null });
    }
  }, []);

  useEffect(() => { fetchKeyInfo(); }, [fetchKeyInfo]);

  const handleGenerate = async () => {
    if (!window.confirm('Gerar uma nova chave vai invalidar a chave atual. Continuar?')) return;

    // Sem chave no navegador não temos X-API-Key para enviar → autenticar por senha
    let password;
    if (!browserKeyStored) {
      password = window.prompt('Nenhuma chave armazenada neste navegador.\nDigite a senha do painel (PANEL_PASSWORD) para continuar:');
      if (password === null) return; // usuário cancelou o prompt
    }

    setGenerating(true);
    setError('');
    setGeneratedKey('');
    setCopied(false);
    try {
      const data = await api.generateApiKey(password);
      setGeneratedKey(data.api_key);
      saveApiKey(data.api_key);
      setBrowserKeyStored(true);
      await fetchKeyInfo();
    } catch (e) {
      setError(e.message || 'Erro ao gerar chave');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedKey).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    });
  };

  const handleSaveBrowserKey = (key) => {
    const target = key || inputKey.trim();
    if (!target) return;
    saveApiKey(target);
    setBrowserKeyStored(true);
    setBrowserKeySaved(true);
    setInputKey('');
    setTimeout(() => setBrowserKeySaved(false), 3000);
  };

  return (
    <div className="bg-card rounded-lg shadow-md p-6 space-y-5">
      <div>
        <h3 className="text-lg font-semibold text-page mb-1 flex items-center gap-2">
          <Icon name="alert" size="text-lg" />
          API Key
        </h3>
        <p className="text-sm text-page opacity-70">
          Chave de autenticação usada pelo agente e por este navegador para acessar o backend.
        </p>
      </div>

      {/* Status da chave no servidor */}
      {keyInfo && (
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${keyInfo.configured ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-page">
            {keyInfo.configured
              ? <>Servidor: <code className="font-mono bg-gray-100 dark:bg-gray-800 px-1 rounded">{keyInfo.key_prefix}</code></>
              : 'Servidor: nenhuma chave configurada'}
          </span>
        </div>
      )}

      {/* Status da chave no navegador */}
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${browserKeyStored ? 'bg-green-500' : 'bg-amber-500'}`} />
        <span className="text-sm text-page">
          {browserKeyStored ? 'Navegador: chave configurada' : 'Navegador: sem chave — requisições vão falhar com 401'}
        </span>
      </div>

      {/* Gerar nova chave */}
      <div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {generating ? 'Gerando...' : 'Gerar nova chave no servidor'}
        </button>
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </div>

      {/* Chave gerada — exibida uma única vez */}
      {generatedKey && (
        <div className="rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 p-4 space-y-3">
          <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
            Copie agora — esta chave não será exibida novamente
          </p>
          <div className="flex items-center gap-2">
            <input
              readOnly
              value={generatedKey}
              className="flex-1 font-mono text-xs px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-page"
            />
            <button
              onClick={handleCopy}
              className={`flex-shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                copied ? 'bg-green-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-page'
              }`}
            >
              {copied ? 'Copiado!' : 'Copiar'}
            </button>
          </div>
          <p className="text-xs text-page opacity-60">
            Para o agente: <code className="font-mono">API_KEY=&lt;chave&gt;</code> no arquivo de configuração.
          </p>
          <button
            onClick={() => handleSaveBrowserKey(generatedKey)}
            className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
              browserKeySaved
                ? 'bg-green-500 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-page hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {browserKeySaved ? 'Salvo no navegador!' : 'Salvar também neste navegador'}
          </button>
        </div>
      )}

      {/* Configurar chave manualmente no navegador */}
      <div className="border-t pt-4" style={{ borderColor: 'var(--card-border)' }}>
        <p className="text-sm font-medium text-page mb-2">Configurar chave neste navegador</p>
        <p className="text-xs text-page opacity-60 mb-3">
          A chave fica no <code className="font-mono">localStorage</code> — nunca é enviada para outros domínios
          nem compilada no código-fonte do app.
        </p>
        <div className="flex items-center gap-2">
          <input
            type="password"
            placeholder="Cole a API key aqui"
            value={inputKey}
            onChange={(e) => setInputKey(e.target.value)}
            className="flex-1 font-mono text-xs px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-page"
          />
          <button
            onClick={() => handleSaveBrowserKey()}
            disabled={!inputKey.trim()}
            className="flex-shrink-0 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {browserKeySaved ? 'Salvo!' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}

// 1. ABA DASHBOARD (Visão Geral)
export function DashboardPage() {
  const { selectedDiscovery, loading } = useOutletContext();

  if (loading) return <div className="p-6 text-gray-500">Carregando dados do host...</div>;

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Discovery do Host</h2>
        <p className="text-sm text-page opacity-80">Dados coletados sobre hardware, virtualização e rede.</p>
      </div>
      {selectedDiscovery ? (
        <DiscoveryDashboard discovery={selectedDiscovery} />
      ) : (
        <div className="bg-card rounded-lg shadow-md p-6 text-page opacity-70">Nenhum discovery cadastrado.</div>
      )}
    </section>
  );
}

// 2. ABA MÉTRICAS
export function MetricsPage() {
  const { metrics, loading, metricsError, selectedHostInfo } = useOutletContext();

  if (loading) return <div className="p-6 text-gray-500">Carregando gráficos...</div>;
  if (metricsError) return <div className="text-red-500 p-4">{metricsError}</div>;

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Métricas do Host</h2>
        <p className="text-sm text-page opacity-80">
          Gráficos e indicadores de desempenho do host selecionado.
        </p>
      </div>
      <div className="space-y-6">
        {metrics.length > 0 ? (
          <>
            <MetricsChart metrics={metrics} title={`Métricas - ${selectedHostInfo?.name}`} />
            <MetricCards latestMetric={metrics[metrics.length - 1]} />
          </>
        ) : (
          <div className="bg-card rounded-lg shadow-md p-6 text-page opacity-70">Nenhuma métrica encontrada para este host.</div>
        )}
      </div>
    </section>
  );
}

// 3. ABA LOGS
export function LogsPage() {
  const { selectedHost } = useOutletContext();
  return <LogsPanel hostId={selectedHost} />;
}

// 4. ABA ALERTAS
export function AlertsPage() {
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Alertas de Segurança</h2>
        <p className="text-sm text-page opacity-80">
          Eventos e notificações de segurança detectados no host.
        </p>
      </div>
      <AlertsPanel />
    </section>
  );
}

// 5. ABA ENDPOINTS
export function EndpointsPage() {
  const { discovery, discoveryLoading, discoveryError } = useOutletContext();

  if (discoveryLoading) {
    return <div className="bg-card rounded-lg shadow-md p-6 text-page opacity-70">Carregando endpoints...</div>;
  }

  if (discoveryError) {
    return <div className="bg-card rounded-lg shadow-md p-6 text-red-500">Erro ao carregar endpoints: {discoveryError}</div>;
  }

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Endpoints Monitorados</h2>
        <p className="text-sm text-page opacity-80">
          Lista de todos os hosts e dispositivos monitorados pelo sistema.
        </p>
      </div>

      <div className="bg-card rounded-lg shadow-md overflow-hidden">
        {discovery && discovery.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">ID</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Hostname</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Status</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Tipo</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">IP</th>
                  <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-gray-300">Sistema</th>
                </tr>
              </thead>
              <tbody>
                {discovery.map((item) => (
                  <tr key={item.host_id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="p-4 text-sm text-page opacity-80">{item.host_id}</td>
                    <td className="p-4 text-sm font-medium text-page">{item.host?.hostname || `Host ${item.host_id}`}</td>
                    <td className="p-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.host?.status === 'online' 
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' 
                          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {item.host?.status || 'offline'}
                      </span>
                    </td>
                    <td className="p-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.is_virtualized
                          ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                      }`}>
                        {item.is_virtualized ? 'Virtual' : 'Físico'}
                      </span>
                    </td>
                    <td className="p-4 text-sm font-mono text-page opacity-80">{item.host?.ip_address || '-'}</td>
                    <td className="p-4 text-sm text-page opacity-80">{item.operating_system || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-page opacity-70">
            <Icon name="server" size="text-3xl" className="mb-2" />
            <p>Nenhum endpoint cadastrado</p>
            <p className="text-sm">Os dados do discovery aparecerão aqui automaticamente.</p>
          </div>
        )}
      </div>
    </section>
  );
}

// ==================== EMAIL RECIPIENTS CARD ====================

function EmailRecipientsCard() {
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

// ==================== NOTIFICATIONS CARD ====================

function NotificationsCard() {
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

// ==================== THRESHOLDS CARD ====================

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

// 6. ABA CONFIGURAÇÕES
export function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-page">Configurações</h2>
        <p className="text-sm text-page opacity-80">
          Configure as preferências do sistema de monitoramento.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card - Aparência */}
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
            <Icon name="settings" size="text-lg" />
            Aparência
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-page">Tema</p>
              <p className="text-sm text-page opacity-70">Alternar entre tema claro e escuro</p>
            </div>
            <button
              onClick={toggleTheme}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-page"
            >
              {theme === 'light' ? '☀️ Modo claro' : '🌙 Modo escuro'}
            </button>
          </div>
        </div>

        {/* Card - Notificações */}
        <NotificationsCard />

        {/* Card - Monitoramento (thresholds configuráveis) */}
        <ThresholdsCard />

        {/* Card - Destinatários de Email */}
        <EmailRecipientsCard />

        {/* Card - API Key */}
        <ApiKeyCard />

        {/* Card - Sobre */}
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-page mb-4 flex items-center gap-2">
            <Icon name="info" size="text-lg" />
            Sobre o Sistema
          </h3>
          <div className="space-y-2 text-sm text-page opacity-80">
            <p><strong>Monitoramento P2</strong> - Sistema de monitoramento de endpoints</p>
            <p>Versão: 2.0.0</p>
            <p>Frontend: React + Vite + Tailwind</p>
            <p className="pt-2 text-xs">© 2026 - Projeto de Monitoramento</p>
          </div>
        </div>
      </div>
    </section>
  );
}