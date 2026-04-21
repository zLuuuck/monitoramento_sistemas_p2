import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',        // Permite conexões externas (Docker)
    port: 5173,             // Porta fixa
    watch: {
      usePolling: true      // Hot Reload no Windows
    },
    // 🔥 Proxy para o BackEnd (Evita erro de CORS durante desenvolvimento)
    //proxy: {
    // '/api': {
    //    target: 'http://backend:5000', // Use o nome do serviço no docker-compose
    //    changeOrigin: true,
    //    secure: false,
        // rewrite: (path) => path.replace(/^\/api/, '') // Se precisar remover o /api
    //  }
    //}
  }
})