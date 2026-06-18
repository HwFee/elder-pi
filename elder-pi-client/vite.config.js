import { defineConfig } from 'vite';

export default defineConfig({
  test: {
    environment: 'jsdom',
    exclude: ['node_modules/**'],
  },
  build: {
    outDir: 'dist',
  },
  server: {
    host: '127.0.0.1',
    port: 3000,
  },
});
