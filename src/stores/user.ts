import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

type Chronotype = 'early' | 'intermediate' | 'late'
type Provider = 'openai' | 'claude' | 'gemini' | 'grok' | 'perplexity' | 'kimi' | 'glm'

const PREFIX = 'helios_'

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    if (raw === null) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function save<T>(key: string, value: T): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value))
  } catch (err) {
    console.warn(`[user] Failed to save "${key}" to localStorage:`, err)
  }
}

export const useUserStore = defineStore('user', () => {
  // ─── Preferences ─────────────────────────────────────────────────────────────
  const usualSleepTime = ref<string>(load('usualSleepTime', '23:00'))
  const chronotype = ref<Chronotype>(load<Chronotype>('chronotype', 'intermediate'))
  const hasCompletedOnboarding = ref<boolean>(load('hasCompletedOnboarding', false))

  // ─── API Provider ─────────────────────────────────────────────────────────────
  const provider = ref<Provider>(load<Provider>('provider', 'openai'))
  const apiKey = ref<string>(load('apiKey', ''))

  // ─── Watchers — persist to localStorage ──────────────────────────────────────
  watch(usualSleepTime, (v) => save('usualSleepTime', v))
  watch(chronotype, (v) => save('chronotype', v))
  watch(hasCompletedOnboarding, (v) => save('hasCompletedOnboarding', v))
  watch(provider, (v) => save('provider', v))
  watch(apiKey, (v) => save('apiKey', v))

  // ─── Actions ──────────────────────────────────────────────────────────────────

  function completeOnboarding(sleepTime: string, chrono: Chronotype): void {
    usualSleepTime.value = sleepTime
    chronotype.value = chrono
    hasCompletedOnboarding.value = true
  }

  function setProvider(newProvider: Provider, key: string): void {
    provider.value = newProvider
    apiKey.value = key
  }

  /**
   * Returns a Date object for today set to the user's usual sleep time.
   * If the time has already passed today, returns tomorrow's date at that time.
   */
  function getSleepTimeToday(): Date {
    const parts = usualSleepTime.value.split(':').map(Number)
    const hours = Number.isFinite(parts[0]) ? parts[0] : 23
    const minutes = Number.isFinite(parts[1]) ? parts[1] : 0
    const now = new Date()
    const target = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes, 0, 0)
    if (target.getTime() <= now.getTime()) {
      // Sleep time already passed today → next occurrence is tomorrow
      target.setDate(target.getDate() + 1)
    }
    return target
  }

  return {
    usualSleepTime,
    chronotype,
    hasCompletedOnboarding,
    provider,
    apiKey,
    completeOnboarding,
    setProvider,
    getSleepTimeToday
  }
})
