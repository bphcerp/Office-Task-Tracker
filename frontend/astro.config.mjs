import { defineConfig } from 'astro/config';
import node from '@astrojs/node';

// https://astro.build/config
export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  vite: {
    server: {
      proxy: {
        // Optional: forward browser /api calls during dev (e.g. a future ingest button).
        // SSR data fetching uses BACKEND_UPSTREAM directly in src/lib/api.ts.
        '/api': {
          target: process.env.BACKEND_UPSTREAM ?? 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  },
});
