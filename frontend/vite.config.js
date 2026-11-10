import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// During development the React app runs on :5173 and forwards API calls to the hub on :8000.
// `npm run build` writes frontend/dist, which the FastAPI hub serves directly.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // reachable from phones on the same Wi-Fi during development
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
