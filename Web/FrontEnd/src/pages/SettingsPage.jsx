import { useTheme } from '../contexts/ThemeContext';
import { Icon } from '../shared/components/Icon';
import ApiKeyCard from '../components/ApiKeyCard';
import { EmailRecipientsCard } from '../components/EmailRecipientsCard';
import { NotificationsCard } from '../components/NotificationsCard';
import ThresholdsCard from '../components/ThresholdsCard';

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
        {/* Aparência */}
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

        {/* Notificações */}
        <NotificationsCard />

        {/* Monitoramento (thresholds configuráveis) */}
        <ThresholdsCard />

        {/* Destinatários de Email */}
        <EmailRecipientsCard />

        {/* API Key */}
        <ApiKeyCard />

        {/* Sobre */}
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