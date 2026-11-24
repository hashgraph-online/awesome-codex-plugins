import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The kit's CSS and icons live one folder up (../_kit); allow the dev server to read them.
export default defineConfig({
  plugins: [react()],
  base: './',
  server: { fs: { allow: ['..'] } },
});
