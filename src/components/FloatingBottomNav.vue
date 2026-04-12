<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { Home, Activity, Settings } from 'lucide-vue-next'

const route  = useRoute()
const router = useRouter()
const { isDark } = useTheme()

const activeColor = computed(() => isDark.value ? '#00D4AA' : '#FFBD76')
const activeBg    = computed(() => isDark.value
  ? 'rgba(0, 212, 170, 0.13)'
  : 'rgba(255, 189, 118, 0.18)'
)

const items = [
  { to: '/',            icon: Home,     label: 'Home'       },
  { to: '/biometrics',  icon: Activity, label: 'Biometrics' },
  { to: '/settings',    icon: Settings, label: 'Settings'   },
]

function isActive(to: string) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}
</script>

<template>
  <nav class="fnav" aria-label="Main navigation">
    <button
      v-for="item in items"
      :key="item.to"
      class="fnav-btn"
      :class="{ 'fnav-btn--active': isActive(item.to) }"
      :style="isActive(item.to)
        ? { background: activeBg, color: activeColor }
        : {}"
      :aria-current="isActive(item.to) ? 'page' : undefined"
      @click="router.push(item.to)"
    >
      <component :is="item.icon" :size="16" class="fnav-icon" />
      <span class="fnav-label">{{ item.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.fnav {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.3rem;
  background: var(--glass-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--glass-border);
  border-radius: 999px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45), 0 2px 8px rgba(0, 0, 0, 0.25);
}

.fnav-btn {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0.52rem 0.65rem;
  border: none;
  background: transparent;
  border-radius: 999px;
  cursor: pointer;
  color: var(--text-muted);
  font-family: inherit;
  white-space: nowrap;
  transition:
    color       0.25s ease,
    background  0.25s ease,
    padding     0.3s  cubic-bezier(0.4, 0, 0.2, 1),
    gap         0.3s  cubic-bezier(0.4, 0, 0.2, 1);
}

.fnav-btn:hover:not(.fnav-btn--active) {
  color: var(--text-secondary);
  background: rgba(255, 246, 233, 0.05);
}

.fnav-btn--active {
  padding: 0.52rem 1rem;
  gap: 0.42rem;
}

.fnav-icon {
  flex-shrink: 0;
  display: block;
}

.fnav-label {
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  max-width: 0;
  overflow: hidden;
  opacity: 0;
  transition:
    max-width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    opacity   0.2s ease 0.05s;
}

.fnav-btn--active .fnav-label {
  max-width: 90px;
  opacity: 1;
}
</style>
