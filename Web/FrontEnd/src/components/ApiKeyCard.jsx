import { useState, useEffect, useCallback } from 'react';
import { Icon } from '../shared/components/Icon';
import { api, saveApiKey, hasBrowserApiKey } from '../shared/services/api';

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

export default ApiKeyCard;