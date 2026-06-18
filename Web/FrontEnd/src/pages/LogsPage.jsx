import { useParams } from 'react-router-dom';
import { LogsPanel } from '../features/logs_feat/components/LogsPanel';

export function LogsPage() {
  const { hostId } = useParams();
  return <LogsPanel hostId={hostId} />;
}