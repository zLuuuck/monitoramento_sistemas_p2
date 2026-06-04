import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['painel.monitoramento.lan'],
    watch: {
      usePolling: true      // Hot Reload no Windows
    },
    // HMR via Nginx (porta 80) — necessário quando a 5173 não está exposta no host
    hmr: {
      clientPort: 80,
    },
    // Proxy para o BackEnd — acesso via nome de serviço interno do Docker
    proxy: {
      '/api': {
        target: 'http://backend:5000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
