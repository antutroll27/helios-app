import { getCurrentScope, onScopeDispose, readonly, shallowRef } from 'vue'

interface UseStagedRevealOptions {
  globeDelayMs?: number
  chatDelayMs?: number
  autoRevealChat?: boolean
}

interface TimerHandle {
  value: ReturnType<typeof setTimeout> | null
}

function clearTimer(timer: TimerHandle) {
  if (timer.value !== null) {
    clearTimeout(timer.value)
    timer.value = null
  }
}

export function useStagedReveal(options: UseStagedRevealOptions = {}) {
  const {
    globeDelayMs = 0,
    chatDelayMs = 0,
    autoRevealChat = false,
  } = options
  const effectiveChatDelayMs = Math.max(chatDelayMs, globeDelayMs)

  const showGlobe = shallowRef(false)
  const showChat = shallowRef(false)
  const globeTimer: TimerHandle = { value: null }
  const chatTimer: TimerHandle = { value: null }

  function clearTimers() {
    clearTimer(globeTimer)
    clearTimer(chatTimer)
  }

  function stop() {
    clearTimers()
    showGlobe.value = false
    showChat.value = false
  }

  function triggerChat() {
    clearTimer(chatTimer)
    showChat.value = true
  }

  function start() {
    stop()

    globeTimer.value = setTimeout(() => {
      showGlobe.value = true
      globeTimer.value = null
    }, globeDelayMs)

    if (autoRevealChat) {
      chatTimer.value = setTimeout(() => {
        showChat.value = true
        chatTimer.value = null
      }, effectiveChatDelayMs)
    }
  }

  if (getCurrentScope()) {
    onScopeDispose(stop)
  }

  return {
    showGlobe: readonly(showGlobe),
    showChat: readonly(showChat),
    start,
    stop,
    triggerChat,
  }
}
