import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3001,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://192.168.1.48:8009',
        changeOrigin: true,
      },
    },
  },
})

