import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['lucide-react'], // Явно включити для оптимізації
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
});