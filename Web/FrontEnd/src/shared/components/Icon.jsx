import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faMicrochip,      // CPU
  faMemory,         // Memória RAM
  faServer,         // Servidor
  faChartLine,      // Gráficos
  faBell,           // Alertas
  faFileAlt,        // Logs
  faTachometerAlt,  // Dashboard
  faCheckCircle,    // Status Online
  faExclamationCircle, // Status Offline
  faInfoCircle,     // Info
  faExternalLinkAlt, // Ver mais
  faDesktop,        // Computador físico
  faCloud,          // Virtualizado
} from '@fortawesome/free-solid-svg-icons';

// Mapeamento dos ícones
const icons = {
  cpu: faMicrochip,
  memory: faMemory,
  server: faServer,
  chart: faChartLine,
  alert: faBell,
  log: faFileAlt,
  dashboard: faTachometerAlt,
  online: faCheckCircle,
  offline: faExclamationCircle,
  info: faInfoCircle,
  external: faExternalLinkAlt,
  physical: faDesktop,
  virtual: faCloud,
};

export function Icon({ name, className, size = 'text-xl' }) {
  const icon = icons[name];
  
  if (!icon) return null;
  
  return (
    <FontAwesomeIcon 
      icon={icon} 
      className={`${size} ${className}`}
    />
  );
}