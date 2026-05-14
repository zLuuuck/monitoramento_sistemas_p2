import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faMicrochip,        // CPU
  faMemory,           // Memória RAM
  faServer,           // Servidor
  faChartLine,        // Gráficos
  faBell,             // Alertas
  faFileAlt,          // Logs
  faTachometerAlt,    // Dashboard
  faCheckCircle,      // Status Online
  faExclamationCircle, // Status Offline
  faInfoCircle,       // Info
  faExternalLinkAlt,  // Ver mais
  faDesktop,          // Computador físico
  faCloud,            // Virtualizado
  faChevronLeft,      // Minimizar (<)
  faChevronRight,     // Expandir (>)
  faBars,             // Menu hambúrguer
  faCog,              // Configurações
  faNetworkWired,     // Rede
  faHdd,              // Disco
  faClock,            // Relógio
} from '@fortawesome/free-solid-svg-icons';

// Mapeamento dos ícones
const icons = {
  // Métricas
  cpu: faMicrochip,
  memory: faMemory,
  disk: faHdd,
  network: faNetworkWired,
  
  // Navegação
  dashboard: faTachometerAlt,
  chart: faChartLine,
  log: faFileAlt,
  alert: faBell,
  server: faServer,
  settings: faCog,
  
  // Status
  online: faCheckCircle,
  offline: faExclamationCircle,
  
  // Ações
  info: faInfoCircle,
  external: faExternalLinkAlt,
  minimize: faChevronLeft,
  expand: faChevronRight,
  menu: faBars,
  
  // Hardware
  physical: faDesktop,
  virtual: faCloud,
  
  // Utilitários
  time: faClock,
};

export function Icon({ name, className, size = 'text-base' }) {
  const icon = icons[name];
  
  if (!icon) {
    console.warn(`Ícone não encontrado: ${name}`);
    return null;
  }
  
  return (
    <FontAwesomeIcon 
      icon={icon} 
      className={`${size} ${className || ''}`}
    />
  );
}