import { useOutletContext } from 'react-router-dom';
import { LogsPanel } from '../features/logs_feat/components/LogsPanel';

export function LogsPage() {
  const { selectedHost } = useOutletContext();
  return <LogsPanel hostId={selectedHost} />;
}