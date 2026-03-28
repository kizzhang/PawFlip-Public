import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3002,
        host: '0.0.0.0',
        // 代理后端 API 请求（开发环境）
        proxy: {
          '/api': {
            target: env.VITE_API_URL || 'http://localhost:8003',
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, '/api'),
          },
        },
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
          '@services': path.resolve(__dirname, './services'),
        }
      }
    };
});
