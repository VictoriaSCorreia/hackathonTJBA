import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        // Aumenta timeouts do proxy para requests longos (fase de análise final)
        timeout: 180000,
        proxyTimeout: 180000,
      },
    },
  },
})
