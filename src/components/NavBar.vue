<script setup lang="ts">
import { useGeoStore } from '@/stores/geo'
import { useUserStore } from '@/stores/user'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useEnvironmentStore } from '@/stores/environment'
import { useDonkiStore } from '@/stores/donki'
import { useTheme } from '@/composables/useTheme'
import { Sun, Moon, Settings, RotateCcw, MapPin, Activity } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const geo = useGeoStore()
const user = useUserStore()
const sw = useSpaceWeatherStore()
const env = useEnvironmentStore()
const donki = useDonkiStore()
const { isDark, toggle } = useTheme()
const router = useRouter()

const isReloading = ref(false)

async function fullReload() {
  isReloading.value = true
  // Reset onboarding so judges can see it
  user.hasCompletedOnboarding = false
  localStorage.removeItem('helios_hasCompletedOnboarding')
  // Re-fetch all data
  await geo.requestLocation()
  await Promise.allSettled([
    sw.fetchAll(),
    donki.fetchAll(),
    env.fetchAll(geo.lat, geo.lng)
  ])
  isReloading.value = false
}
</script>

<template>
  <nav class="navbar">
    <!-- Left: Location -->
    <div class="nav-left">
      <MapPin :size="13" style="color: var(--text-muted); flex-shrink: 0;" />
      <div class="nav-location">
        <span class="nav-loc-name font-mono">{{ geo.locationName }}</span>
        <span class="nav-loc-coords font-mono">{{ geo.lat.toFixed(2) }}°, {{ geo.lng.toFixed(2) }}°</span>
      </div>
      <span class="nav-live-dot pulse-live">●</span>
    </div>

    <!-- Center: Logo SVG -->
    <div class="nav-center">
      <svg class="nav-logo-svg" viewBox="0 0 501 427" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M388.793 0.819253C388.375 7.54175 388.432 14.3335 387.463 20.9755C381.374 62.7093 361.568 96.6013 328.108 122.224C302.744 141.647 273.848 152.046 241.889 153.044C223.3 153.625 204.68 153.206 186.075 153.239C185.192 153.241 184.309 153.262 183.114 153.391C182.68 154.284 182.449 155.06 182.449 155.835C182.43 184.184 182.432 212.533 182.431 240.882C181.868 240.922 181.304 240.996 180.74 240.996C160.17 241.002 139.6 241.001 119.03 240.997C118.594 240.997 118.157 240.955 117.657 240.929C117.657 238.575 117.553 236.265 117.672 233.966C119.64 196.038 133.501 163.072 159.61 135.521C184.843 108.895 215.917 93.3996 252.325 88.8483C258.871 88.03 265.528 87.891 272.138 87.8357C288.605 87.6977 305.075 87.793 321.544 87.7744C322.314 87.7735 323.472 88.2295 323.567 86.4725C323.845 85.5293 324.03 84.8033 324.03 84.0771C324.045 57.0751 324.061 30.073 324.003 3.07105C323.999 1.22588 324.54 0.773443 326.335 0.778701C347.154 0.839676 367.974 0.818589 388.793 0.819253Z" fill="currentColor"/>
        <path d="M158.201 7.5107e-05C170.241 1.37922e-07 182.091 0 193.938 0C196.08 80.3132 127.106 154.174 41 153.171C41 131.45 41 109.727 41 87.8017C70.1701 87.8017 99.2787 87.8017 128.571 87.8017C128.571 58.4865 128.571 29.3729 128.571 0.000144437C138.507 0.000144437 148.259 0.000144397 158.201 7.5107e-05Z" fill="currentColor"/>
        <path d="M464.883 153.108C464.195 153.154 463.507 153.239 462.82 153.239C435.124 153.242 407.428 153.236 379.732 153.232C379.176 153.232 378.619 153.232 377.814 153.232C377.814 167.94 377.814 182.486 377.814 197.031C377.814 211.594 377.814 226.156 377.814 240.859C355.951 240.859 334.223 240.859 312.367 240.859C312.367 238.542 312.276 236.167 312.381 233.801C315.338 166.969 362.143 109.284 426.928 92.5833C439.267 89.4025 451.802 87.7814 464.714 87.9534C464.885 109.828 464.884 131.468 464.883 153.108Z" fill="currentColor"/>
        <path d="M5.97777 404.785V352.48H12.2544V375.718H36.7633V352.48H43.04V404.785H36.7633V381.397H12.2544V404.785H5.97777ZM105.825 404.785V352.48H138.031V358.158H112.102V375.643H135.938V381.322H112.102V399.106H138.404V404.785H105.825ZM198.741 404.785V352.48H205.017V399.106H231.469V404.785H198.741ZM290.342 404.785V352.48H296.619V404.785H290.342ZM378.376 405.831C372.149 405.831 367.167 404.038 363.431 400.451C359.745 396.815 357.902 391.534 357.902 384.61V372.655C357.902 365.73 359.745 360.475 363.431 356.888C367.167 353.252 372.149 351.433 378.376 351.433C384.652 351.433 389.634 353.252 393.32 356.888C397.056 360.475 398.924 365.73 398.924 372.655V384.61C398.924 391.534 397.056 396.815 393.32 400.451C389.634 404.038 384.652 405.831 378.376 405.831ZM378.376 400.227C382.909 400.227 386.421 398.882 388.911 396.192C391.402 393.452 392.647 389.666 392.647 384.834V372.43C392.647 367.598 391.402 363.837 388.911 361.147C386.421 358.407 382.909 357.038 378.376 357.038C373.892 357.038 370.405 358.407 367.914 361.147C365.424 363.837 364.178 367.598 364.178 372.43V384.834C364.178 389.666 365.424 393.452 367.914 396.192C370.405 398.882 373.892 400.227 378.376 400.227ZM477.602 405.831C473.817 405.831 470.429 405.159 467.44 403.814C464.451 402.469 462.085 400.451 460.342 397.761C458.648 395.021 457.801 391.609 457.801 387.524V385.955H464.003V387.524C464.003 391.858 465.273 395.096 467.814 397.238C470.354 399.33 473.617 400.376 477.602 400.376C481.687 400.376 484.801 399.455 486.943 397.612C489.085 395.769 490.156 393.452 490.156 390.663C490.156 388.72 489.658 387.176 488.661 386.03C487.715 384.884 486.37 383.962 484.626 383.265C482.883 382.518 480.84 381.87 478.499 381.322L474.614 380.351C471.575 379.554 468.885 378.582 466.544 377.437C464.202 376.291 462.359 374.797 461.014 372.953C459.719 371.06 459.071 368.644 459.071 365.705C459.071 362.766 459.794 360.226 461.238 358.084C462.733 355.942 464.8 354.298 467.44 353.152C470.13 352.006 473.219 351.433 476.706 351.433C480.243 351.433 483.406 352.056 486.196 353.301C489.035 354.497 491.252 356.29 492.846 358.681C494.49 361.023 495.312 363.987 495.312 367.573V370.712H489.11V367.573C489.11 365.033 488.562 362.99 487.466 361.446C486.42 359.902 484.95 358.756 483.057 358.009C481.214 357.262 479.097 356.888 476.706 356.888C473.269 356.888 470.504 357.66 468.412 359.205C466.319 360.699 465.273 362.841 465.273 365.631C465.273 367.474 465.722 368.968 466.618 370.114C467.515 371.26 468.785 372.206 470.429 372.953C472.073 373.651 474.041 374.273 476.332 374.821L480.218 375.793C483.256 376.44 485.971 377.337 488.362 378.483C490.803 379.579 492.746 381.098 494.191 383.041C495.635 384.934 496.358 387.425 496.358 390.513C496.358 393.602 495.586 396.292 494.041 398.583C492.497 400.875 490.305 402.668 487.466 403.963C484.676 405.208 481.388 405.831 477.602 405.831Z" fill="currentColor"/>
      </svg>
      <span class="nav-tagline font-mono">CIRCADIAN INTELLIGENCE</span>
    </div>

    <!-- Right: Controls -->
    <div class="nav-right">
      <button class="nav-btn" @click="fullReload" title="Restart demo" :disabled="isReloading">
        <RotateCcw :size="15" :class="{ 'spin-anim': isReloading }" style="color: var(--text-secondary)" />
      </button>
      <button class="nav-btn" @click="toggle" :title="isDark ? 'Light mode' : 'Dark mode'">
        <Sun v-if="isDark" :size="15" style="color: var(--text-secondary)" />
        <Moon v-else :size="15" style="color: var(--text-secondary)" />
      </button>
      <button class="nav-btn" @click="router.push('/biometrics')" title="Biometrics">
        <Activity :size="15" style="color: var(--text-secondary)" />
      </button>
      <button class="nav-btn" @click="router.push('/settings')" title="Settings">
        <Settings :size="15" style="color: var(--text-secondary)" />
      </button>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.42rem 1.1rem;
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--glass-border);
}

/* Left */
.nav-left {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
}

.nav-location {
  display: flex;
  flex-direction: column;
}

.nav-loc-name {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.03em;
}

.nav-loc-coords {
  font-size: 0.45rem;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.nav-live-dot {
  font-size: 0.4rem;
  color: #00D4AA;
  margin-left: 0.15rem;
}

/* Center */
.nav-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: visible;
  padding: 0.12rem 0;
}

.nav-logo-svg {
  height: 30px;
  width: auto;
  color: var(--text-primary);
  display: block;
}

.nav-tagline {
  font-size: 0.31rem;
  letter-spacing: 0.22em;
  color: var(--text-muted);
  margin-top: 0.05rem;
}

/* Right */
.nav-right {
  display: flex;
  align-items: center;
  gap: 0.15rem;
}

.nav-btn {
  padding: 0.4rem;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: wait;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(-360deg); }
}

.spin-anim {
  animation: spin 0.8s linear infinite;
}
</style>
