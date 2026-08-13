import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Only used in local dev; in production VITE_API_URL is set as a build arg
      '/api': 'http://localhost:8000'
    }
  }
})
