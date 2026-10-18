import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Solo proxiar REST. WS conecta directo al backend (puerto 8000)
      // para evitar ECONNABORTED en el proxy WS de Vite con uvicorn.
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
