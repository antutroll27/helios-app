import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'
import './components/telemetry-module.css'

const PRELOAD_RECOVERY_KEY = 'helios-preload-recovery'

window.addEventListener('vite:preloadError', (event) => {
  event.preventDefault()

  if (sessionStorage.getItem(PRELOAD_RECOVERY_KEY) === '1') {
    return
  }

  sessionStorage.setItem(PRELOAD_RECOVERY_KEY, '1')
  window.location.reload()
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
