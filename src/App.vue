<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGeoStore } from '@/stores/geo'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useDonkiStore } from '@/stores/donki'
import { useEnvironmentStore } from '@/stores/environment'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import NavBar from '@/components/NavBar.vue'
import FloatingBottomNav from '@/components/FloatingBottomNav.vue'
import AuthBanner from '@/components/AuthBanner.vue'

const geo   = useGeoStore()
const sw    = useSpaceWeatherStore()
const donki = useDonkiStore()
const env   = useEnvironmentStore()
const auth  = useAuthStore()
const route = useRoute()
const { isDark } = useTheme()

const isAuthRoute = computed(() => route.name === 'auth')

onMounted(async () => {
  auth.init()  // non-blocking — resolves auth state in background
  await geo.requestLocation()
  // Fetch all live data in parallel once we have GPS
  await Promise.allSettled([
    sw.fetchAll(),
    donki.fetchAll(),
    env.fetchAll(geo.lat, geo.lng)
  ])
  // Start polling
  sw.startPolling()
})

onUnmounted(() => {
  sw.stopPolling()
  auth.dispose()
})
</script>

<template>
  <div
    class="min-h-screen transition-colors duration-300"
    :style="{
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)'
    }"
  >
    <NavBar            v-if="!isAuthRoute" />
    <AuthBanner v-if="!isAuthRoute && !auth.loading" />
    <main class="main-content">
      <RouterView />
    </main>
    <FloatingBottomNav v-if="!isAuthRoute" />
  </div>
</template>

<style>
/* Give every page breathing room above the floating nav */
.main-content {
  padding-bottom: calc(5rem + env(safe-area-inset-bottom, 0px));
}
</style>
