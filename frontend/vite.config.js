import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: { '/api': { target: process.env.CAMPUSTWIN_API_TARGET || 'http://127.0.0.1:8000', changeOrigin: true } },
  },
})
