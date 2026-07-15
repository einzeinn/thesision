import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({
  base: '/static/dist/',
  build: {
    outDir: resolve(__dirname, 'src/frontend/app/dist'),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, 'src/frontend/app/app.ts'),
      formats: ['es'],
      fileName: () => 'app.js',
    },
  },
});
