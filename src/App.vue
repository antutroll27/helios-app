<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useGeoStore } from '@/stores/geo'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useDonkiStore } from '@/stores/donki'
import { useEnvironmentStore } from '@/stores/environment'
import { useTheme } from '@/composables/useTheme'
import NavBar from '@/components/NavBar.vue'

const geo = useGeoStore()
const sw = useSpaceWeatherStore()
const donki = useDonkiStore()
const env = useEnvironmentStore()
const { isDark } = useTheme()

onMounted(async () => {
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
    <NavBar />
    <main>
      <RouterView />
    </main>
  </div>
</template>
