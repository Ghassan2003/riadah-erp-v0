import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Code splitting for optimal caching - separate vendor chunks
    rollupOptions: {
      output: {
        manualChunks: {
          'react-core': ['react', 'react-dom'],
          'react-router': ['react-router-dom'],
          'ui-vendor': ['lucide-react', 'react-hot-toast'],
          'charts': ['recharts'],
        },
        // Hash-based filenames for long-term caching
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    // Target modern browsers for smaller bundle
    target: 'es2020',
    // Minify with esbuild (fastest)
    minify: 'esbuild',
    // Disable sourcemaps in production
    sourcemap: false,
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Increase chunk size warning threshold (Recharts is large)
    chunkSizeWarningLimit: 600,
    // Optimize CSS
    cssMinify: true,
  },
  // Optimize deps for faster dev server
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'lucide-react', 'recharts'],
  },
})
