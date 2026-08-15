import { defineConfig } from 'astro/config';
import node from '@astrojs/node';

// https://astro.build/config
export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  vite: {
    server: {
      proxy: {
        // In dev, forward /api calls to the backend container/host.
        '/api': {
          target: process.env.BACKEND_UPSTREAM ?? 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  },
});
