import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, process.cwd(), 'CAMPUSTWIN_')
  return {
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: { '/api': { target: process.env.CAMPUSTWIN_API_TARGET || environment.CAMPUSTWIN_API_TARGET || 'http://127.0.0.1:8000', changeOrigin: true } },
  },
  }
})
