import { ref, watch } from 'vue'

const isDark = ref(true)

// Initialize immediately from persisted preference
const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('helios_theme') : null
isDark.value = saved ? saved === 'dark' : true
if (typeof document !== 'undefined') {
  document.documentElement.classList.toggle('light', !isDark.value)
}

// Single module-level watcher — avoids duplicate watchers when useTheme()
// is called from multiple components (e.g. App.vue + NavBar.vue).
watch(isDark, (val) => {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('helios_theme', val ? 'dark' : 'light')
  }
  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('light', !val)
  }
})

export function useTheme() {
  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
}
