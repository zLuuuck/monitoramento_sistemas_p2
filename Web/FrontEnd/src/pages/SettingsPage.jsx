import { useState, useEffect } from 'react';
import { Card } from '../shared/components/Card';
import { api } from '../shared/services/api';
import ApiKeyCard from '../components/ApiKeyCard';

export function SettingsPage() {
  // Estados para os limites
  const [thresholds, setThresholds] = useState({ cpu: 80, mem: 80, disk: 80 });
  const [thresholdsLoading, setThresholdsLoading] = useState(true);

  // Estados para notificações
  const [notifications, setNotifications] = useState({ teams: true, email: false });
  const [notifLoading, setNotifLoading] = useState(true);

  // Estados para emails
  const [recipients, setRecipients] = useState([]);
  const [recipientsLoading, setRecipientsLoading] = useState(true);
  const [newEmail, setNewEmail] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // Carregar limites
  useEffect(() => {
    const loadThresholds = async () => {
      try {
        const data = await api.getThresholds();
        setThresholds({ cpu: data.cpu, mem: data.mem, disk: data.disk });
      } catch (error) {
        console.error('Erro ao carregar limites:', error);
      } finally {
        setThresholdsLoading(false);
      }
    };
    loadThresholds();
  }, []);

  // Carregar notificações
  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const data = await api.getNotifications();
        setNotifications({ teams: data.teams, email: data.email });
      } catch (error) {
        console.error('Erro ao carregar notificações:', error);
      } finally {
        setNotifLoading(false);
      }
    };
    loadNotifications();
  }, []);

  // Carregar destinatários
  useEffect(() => {
    const loadRecipients = async () => {
      try {
        const data = await api.getEmailRecipients();
        setRecipients(data.recipients || []);
      } catch (error) {
        console.error('Erro ao carregar destinatários:', error);
      } finally {
        setRecipientsLoading(false);
      }
    };
    loadRecipients();
  }, []);

  // Salvar limites
  const saveThresholds = async () => {
    setSaving(true);
    try {
      await api.patchThresholds({
        cpu: thresholds.cpu,
        mem: thresholds.mem,
        disk: thresholds.disk,
      });
      setMessage({ text: 'Limites salvos com sucesso!', type: 'success' });
      setTimeout(() => setMessage({ text: '', type: '' }), 3000);
    } catch (error) {
      setMessage({ text: 'Erro ao salvar limites', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // Alternar notificação
  const toggleNotification = async (field) => {
    const newValue = !notifications[field];
    setNotifications(prev => ({ ...prev, [field]: newValue }));
    try {
      await api.patchNotifications({ [field]: newValue });
    } catch (error) {
      setNotifications(prev => ({ ...prev, [field]: !newValue }));
      setMessage({ text: 'Erro ao salvar notificação', type: 'error' });
    }
  };

  // Adicionar email
  const addEmail = async () => {
    if (!newEmail.trim()) {
      setMessage({ text: 'Digite um email válido', type: 'error' });
      return;
    }
    setSaving(true);
    try {
      const data = await api.addEmailRecipient(newEmail);
      setRecipients(data.recipients || []);
      setNewEmail('');
      setMessage({ text: 'Email adicionado!', type: 'success' });
      setTimeout(() => setMessage({ text: '', type: '' }), 3000);
    } catch (error) {
      setMessage({ text: 'Erro ao adicionar email', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // Remover email
  const removeEmail = async (email) => {
    try {
      const data = await api.removeEmailRecipient(email);
      setRecipients(data.recipients || []);
      setMessage({ text: 'Email removido!', type: 'success' });
      setTimeout(() => setMessage({ text: '', type: '' }), 3000);
    } catch (error) {
      setMessage({ text: 'Erro ao remover email', type: 'error' });
    }
  };

  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-xl font-bold crow-text-primary">Configurações</h2>
        <p className="text-sm crow-text-secondary">
          Configure as preferências do sistema de monitoramento.
        </p>
      </div>

      {/* Mensagem de feedback */}
      {message.text && (
        <div className={`mb-4 p-3 rounded-lg ${message.type === 'success' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'}`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Card Monitoramento */}
        <Card
          title="Monitoramento"
          value="Limites de Alerta"
          unit=""
          iconName="chart"
          color="purple"
          subtitle="Configure os limites para disparar alertas"
        >
          <div className="space-y-3 mt-2">
            <div className="flex justify-between items-center">
              <span className="crow-text-primary">CPU</span>
              <input
                type="number"
                value={thresholds.cpu}
                onChange={(e) => setThresholds({ ...thresholds, cpu: parseInt(e.target.value) || 0 })}
                min="1"
                max="99"
                className="w-20 px-2 py-1 rounded bg-[#1A1A2E] border border-[#1A2A4A] text-center crow-text-primary focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
              />
              <span className="crow-text-secondary">%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="crow-text-primary">RAM</span>
              <input
                type="number"
                value={thresholds.mem}
                onChange={(e) => setThresholds({ ...thresholds, mem: parseInt(e.target.value) || 0 })}
                min="1"
                max="99"
                className="w-20 px-2 py-1 rounded bg-[#1A1A2E] border border-[#1A2A4A] text-center crow-text-primary focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
              />
              <span className="crow-text-secondary">%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="crow-text-primary">Disco</span>
              <input
                type="number"
                value={thresholds.disk}
                onChange={(e) => setThresholds({ ...thresholds, disk: parseInt(e.target.value) || 0 })}
                min="1"
                max="99"
                className="w-20 px-2 py-1 rounded bg-[#1A1A2E] border border-[#1A2A4A] text-center crow-text-primary focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
              />
              <span className="crow-text-secondary">%</span>
            </div>
            <button
              onClick={saveThresholds}
              disabled={saving}
              className="w-full mt-3 px-4 py-2 bg-[#4B2D6E] text-[#E2E2E8] rounded-lg hover:bg-[#2D2D44] transition-colors disabled:opacity-50"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </Card>

        {/* Card Notificações */}
        <Card
          title="Notificações"
          value="Canais de Alerta"
          unit=""
          iconName="alert"
          color="purple"
          subtitle="Configure onde receber os alertas"
        >
          <div className="space-y-3 mt-2">
            <div className="flex justify-between items-center">
              <span className="crow-text-primary">Alertas no Teams</span>
              <button
                onClick={() => toggleNotification('teams')}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${notifications.teams ? 'bg-[#A855F7] text-white' : 'bg-[#2D2D44] text-[#A8B3CF]'}`}
              >
                {notifications.teams ? 'Ativado' : 'Desativado'}
              </button>
            </div>
            <div className="flex justify-between items-center">
              <span className="crow-text-primary">Alertas por E-mail</span>
              <button
                onClick={() => toggleNotification('email')}
                className={`px-3 py-1 rounded-full text-[#E2E2E8] transition-colors ${notifications.email ? 'bg-[#A855F7] text-white' : 'bg-[#2D2D44] text-[#A8B3CF]'}`}
              >
                {notifications.email ? 'Ativado' : 'Desativado'}
              </button>
            </div>
          </div>
        </Card>

        {/* Card Destinatários */}
        <Card
          title="Destinatários"
          value="Email para Alertas"
          unit=""
          iconName="email"
          color="purple"
          subtitle="Alertas serão enviados para estes endereços"
        >
          <div className="mt-2">
            <div className="space-y-2">
              {recipients.length === 0 ? (
                <p className="text-sm crow-text-secondary py-2 text-center">Nenhum destinatário configurado.</p>
              ) : (
                recipients.map((email) => (
                  <div key={email} className="flex justify-between items-center px-3 py-2 rounded-lg border border-[#1A2A4A]">
                    <span className="text-sm crow-text-primary">{email}</span>
                    <button
                      onClick={() => removeEmail(email)}
                      className="text-red-500 hover:text-red-400 text-sm"
                    >
                      Remover
                    </button>
                  </div>
                ))
              )}
            </div>
            <div className="flex gap-2 mt-3">
              <input
                type="email"
                placeholder="email@exemplo.com"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                className="flex-1 px-3 py-2 rounded bg-[#1A1A2E] border border-[#1A2A4A] text-[#E2E2E8] focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
              />
              <button
                onClick={addEmail}
                disabled={saving}
                className="px-4 py-2 bg-[#4B2D6E] text-[#E2E2E8] rounded-lg hover:bg-[#2D2D44] transition-colors disabled:opacity-50"
              >
                Adicionar
              </button>
            </div>
          </div>
        </Card>

        {/* Card Sobre */}
        <Card
          title="Sobre"
          value="Monitoramento P2"
          unit=""
          iconName="info"
          color="purple"
          subtitle="Sistema de monitoramento de endpoints"
        >
          <div className="mt-2 space-y-1 text-sm crow-text-secondary">
            <p>Versão: 2.0.0</p>
            <p>Frontend: React + Vite + Tailwind</p>
            <p className="text-xs pt-2">© 2026 - Projeto de Monitoramento</p>
          </div>
        </Card>

        <Card
          title="API"
          value="Autenticação"
          unit=""
          iconName="key"
          color="purple"
          subtitle="Gerenciamento da API Key"
        >
          <ApiKeyCard />
        </Card>

      </div>
    </section>
  );
}