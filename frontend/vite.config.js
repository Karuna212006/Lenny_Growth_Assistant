import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/sessions': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/artifacts': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})

