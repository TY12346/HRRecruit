import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const publicBasePath = process.env.VITE_PUBLIC_BASE_PATH || './';

export default defineConfig({
  base: publicBasePath,
  plugins: [react()],
});
