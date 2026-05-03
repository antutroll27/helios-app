import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

const NODE_MODULES_SEGMENT = '/node_modules/'
const DEFERRED_ENTRY_PATTERNS = [
  'home-globe-',
  'home-chat-',
  'ChatInterface-',
  'HeliosGlobePanel-',
] as const
const VENDOR_CHUNK_GROUPS = {
  'home-globe-vendor': ['cobe', 'phenomenon'],
  'home-ui-vendor': [
    '@vueuse/core',
    'lucide-vue-next',
    'pinia',
    'suncalc'
  ],
  'biometrics-vendor': ['echarts', 'vue-echarts', 'zrender']
} as const

function matchesPackage(id: string, packageName: string) {
  return id.includes(`${NODE_MODULES_SEGMENT}${packageName}/`)
}

function isDeferredEntryAsset(dep: string) {
  return DEFERRED_ENTRY_PATTERNS.some((pattern) => dep.includes(pattern))
}

function resolveManualChunk(id: string) {
  if (matchesPackage(id, 'cobe') || matchesPackage(id, 'phenomenon')) {
    return 'home-globe-vendor'
  }

  for (const [chunkName, packages] of Object.entries(VENDOR_CHUNK_GROUPS)) {
    if (packages.some((packageName) => matchesPackage(id, packageName))) {
      return chunkName
    }
  }

  if (id.includes(NODE_MODULES_SEGMENT)) {
    return 'vendor'
  }

  return undefined
}

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'HELIOS — Circadian Intelligence',
        short_name: 'HELIOS',
        description: 'Your body runs on the Sun.',
        start_url: '/',
        scope: '/',
        theme_color: '#0A171D',
        background_color: '#0A171D',
        display: 'standalone',
        orientation: 'portrait',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        globIgnores: ['sw-reset.html'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/services\.swpc\.noaa\.gov\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'noaa-cache', expiration: { maxAgeSeconds: 300 } }
          },
          {
            urlPattern: /^https:\/\/api\.open-meteo\.com\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'meteo-cache', expiration: { maxAgeSeconds: 600 } }
          }
        ]
      }
    })
  ],
  build: {
    modulePreload: {
      resolveDependencies(_filename, deps) {
        return deps.filter((dep) => !isDeferredEntryAsset(dep))
      },
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          return resolveManualChunk(id)
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
