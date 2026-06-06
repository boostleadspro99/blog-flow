import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/v1': {
        target: 'http://localhost:3897',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:3897',
        changeOrigin: true,
      },
      '/user': {
        target: 'http://localhost:3897',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:3897',
        changeOrigin: true,
      },
    },
  },
});
