import { ref, watch } from 'vue'

const isDark = ref(true)

// Initialize immediately
const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('helios_theme') : null
isDark.value = saved ? saved === 'dark' : true
if (typeof document !== 'undefined') {
  document.documentElement.classList.toggle('light', !isDark.value)
}

export function useTheme() {
  watch(isDark, (val) => {
    localStorage.setItem('helios_theme', val ? 'dark' : 'light')
    document.documentElement.classList.toggle('light', !val)
  })

  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
}
