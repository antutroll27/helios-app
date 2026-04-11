# Home Bundle Staged Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the initial home-route bundle by moving the globe and chat experiences behind intentional staged async boundaries without making the page feel empty or broken.

**Architecture:** Keep [`HomePage.vue`](../../../../src/pages/HomePage.vue) as a thin composition surface that renders lightweight cards and protocol content synchronously. Move the heavy globe and chat paths behind async components, use a small composable to control staged reveal timing and viewport/interaction loading, and update Vite chunking so `globe.gl` and `three` are isolated from the initial home shell.

**Tech Stack:** Vue 3 + Composition API + TypeScript, Vite, Vitest, `defineAsyncComponent`, `IntersectionObserver`, manual Vite chunking.

---

## File Map

### Home route shell

- Modify: `src/pages/HomePage.vue`
- Create: `src/components/home/HomeGlobePlaceholder.vue`
- Create: `src/components/home/HomeChatPlaceholder.vue`
- Create: `src/composables/useStagedReveal.ts`
- Create: `src/composables/useStagedReveal.test.ts`

Responsibility split:

- `HomePage.vue` owns route composition, staged mount orchestration, and async boundaries only.
- `HomeGlobePlaceholder.vue` owns the immediate above-the-fold fallback shell for the globe section.
- `HomeChatPlaceholder.vue` owns the lightweight chat shell visible before the full chat bundle loads.
- `useStagedReveal.ts` owns timer/viewport/interaction state so staged-loading logic is testable without the route component.
- `useStagedReveal.test.ts` guards the composable behavior with timer-driven tests.

### Bundle output configuration

- Modify: `vite.config.ts`

Responsibility split:

- `vite.config.ts` isolates `three`, `globe.gl`, and other heavy vendor paths into explicit chunks so the lazy boundaries produce network-level wins.

---

### Task 1: Build and Test the Staged Reveal Composable

**Files:**
- Create: `src/composables/useStagedReveal.ts`
- Create: `src/composables/useStagedReveal.test.ts`

- [ ] **Step 1: Write the failing Vitest tests**

Create `src/composables/useStagedReveal.test.ts`:

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useStagedReveal } from './useStagedReveal'

describe('useStagedReveal', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('reveals the globe after the configured delay', () => {
    const reveal = useStagedReveal({ globeDelayMs: 400, chatDelayMs: 1200 })

    reveal.start()
    expect(reveal.showGlobe.value).toBe(false)

    vi.advanceTimersByTime(399)
    expect(reveal.showGlobe.value).toBe(false)

    vi.advanceTimersByTime(1)
    expect(reveal.showGlobe.value).toBe(true)
  })

  it('does not reveal chat until the chat trigger is requested', () => {
    const reveal = useStagedReveal({ globeDelayMs: 400, chatDelayMs: 1200 })

    reveal.start()
    vi.advanceTimersByTime(2000)

    expect(reveal.showChat.value).toBe(false)

    reveal.triggerChat()
    expect(reveal.showChat.value).toBe(true)
  })

  it('allows timed chat reveal when configured for automatic staging', () => {
    const reveal = useStagedReveal({
      globeDelayMs: 400,
      chatDelayMs: 1200,
      autoRevealChat: true,
    })

    reveal.start()
    vi.advanceTimersByTime(1199)
    expect(reveal.showChat.value).toBe(false)

    vi.advanceTimersByTime(1)
    expect(reveal.showChat.value).toBe(true)
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
npm run test -- src/composables/useStagedReveal.test.ts
```

Expected:

- Vitest fails with module-not-found for `./useStagedReveal`.

- [ ] **Step 3: Write the minimal composable implementation**

Create `src/composables/useStagedReveal.ts`:

```ts
import { onBeforeUnmount, ref } from 'vue'

interface StagedRevealOptions {
  globeDelayMs: number
  chatDelayMs: number
  autoRevealChat?: boolean
}

export function useStagedReveal(options: StagedRevealOptions) {
  const showGlobe = ref(false)
  const showChat = ref(false)

  let globeTimer: ReturnType<typeof setTimeout> | null = null
  let chatTimer: ReturnType<typeof setTimeout> | null = null

  function clearTimers() {
    if (globeTimer) clearTimeout(globeTimer)
    if (chatTimer) clearTimeout(chatTimer)
    globeTimer = null
    chatTimer = null
  }

  function start() {
    clearTimers()

    globeTimer = setTimeout(() => {
      showGlobe.value = true
    }, options.globeDelayMs)

    if (options.autoRevealChat) {
      chatTimer = setTimeout(() => {
        showChat.value = true
      }, options.chatDelayMs)
    }
  }

  function triggerChat() {
    showChat.value = true
    if (chatTimer) {
      clearTimeout(chatTimer)
      chatTimer = null
    }
  }

  onBeforeUnmount(clearTimers)

  return {
    showGlobe,
    showChat,
    start,
    triggerChat,
    clearTimers,
  }
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
npm run test -- src/composables/useStagedReveal.test.ts
```

Expected:

- Vitest reports `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/composables/useStagedReveal.ts src/composables/useStagedReveal.test.ts
git commit -m "Add staged reveal composable for home route loading"
```

---

### Task 2: Convert HomePage to Async Globe and Chat Boundaries

**Files:**
- Modify: `src/pages/HomePage.vue`
- Create: `src/components/home/HomeGlobePlaceholder.vue`
- Create: `src/components/home/HomeChatPlaceholder.vue`

- [ ] **Step 1: Add the lightweight fallback components**

Create `src/components/home/HomeGlobePlaceholder.vue`:

```vue
<script setup lang="ts">
defineProps<{
  ready?: boolean
}>()
</script>

<template>
  <div class="home-globe-placeholder" :class="{ 'is-ready': ready }">
    <div class="placeholder-orbit" />
    <div class="placeholder-grid" />
    <div class="placeholder-hud placeholder-hud--right">
      <span>SOLAR ELEVATION</span>
      <span>PHASE</span>
      <span>SUNRISE</span>
    </div>
    <div class="placeholder-hud placeholder-hud--left">
      <span>LATITUDE</span>
      <span>LONGITUDE</span>
      <span>TIMEZONE</span>
    </div>
    <div class="placeholder-badge">Loading live orbital view...</div>
  </div>
</template>

<style scoped>
.home-globe-placeholder {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 0;
  background:
    radial-gradient(circle at 50% 38%, rgba(255, 189, 118, 0.16), transparent 28%),
    radial-gradient(circle at 50% 45%, rgba(0, 212, 170, 0.18), transparent 42%),
    linear-gradient(180deg, #08131a 0%, #0a171d 62%, #081117 100%);
}

.placeholder-orbit {
  position: absolute;
  inset: 12% 18%;
  border-radius: 50%;
  border: 1px solid rgba(255, 246, 233, 0.12);
  box-shadow: 0 0 80px rgba(0, 212, 170, 0.08);
}

.placeholder-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.8), transparent);
}

.placeholder-hud {
  position: absolute;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.55rem;
  letter-spacing: 0.14em;
  color: rgba(255, 246, 233, 0.42);
  font-family: var(--font-mono);
}

.placeholder-hud--right {
  top: 1.5rem;
  right: 1rem;
}

.placeholder-hud--left {
  bottom: 5rem;
  left: 1rem;
}

.placeholder-badge {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: rgba(255, 246, 233, 0.72);
  letter-spacing: 0.08em;
}

@media (max-width: 768px) {
  .placeholder-hud {
    display: none;
  }
}
</style>
```

Create `src/components/home/HomeChatPlaceholder.vue`:

```vue
<template>
  <div class="home-chat-placeholder">
    <div class="chat-header">
      <span class="chat-title font-display">ASK HELIOS</span>
      <span class="chat-chip font-mono">STAGED LOAD</span>
    </div>
    <div class="chat-body">
      <div class="line line--lg" />
      <div class="line line--md" />
      <div class="line line--sm" />
    </div>
  </div>
</template>

<style scoped>
.home-chat-placeholder {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 1rem;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.chat-title {
  font-size: 0.65rem;
  letter-spacing: 0.08em;
}

.chat-chip {
  font-size: 0.55rem;
  color: var(--text-muted);
}

.chat-body {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.line {
  height: 0.75rem;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--border-subtle), rgba(255,255,255,0.04));
}

.line--lg { width: 92%; }
.line--md { width: 72%; }
.line--sm { width: 56%; }
</style>
```

- [ ] **Step 2: Run the build before wiring them in**

Run:

```bash
npm run build
```

Expected:

- Build still passes before the route-shell refactor.

- [ ] **Step 3: Convert `HomePage.vue` to async staged boundaries**

Modify `src/pages/HomePage.vue`:

```vue
<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { Watch, Activity, Smartphone } from 'lucide-vue-next'
import HomeChatPlaceholder from '@/components/home/HomeChatPlaceholder.vue'
import HomeGlobePlaceholder from '@/components/home/HomeGlobePlaceholder.vue'
import EnvironmentBadge from '@/components/EnvironmentBadge.vue'
import OnboardingModal from '@/components/OnboardingModal.vue'
import ProtocolTimeline from '@/components/ProtocolTimeline.vue'
import SocialJetLagScore from '@/components/SocialJetLagScore.vue'
import SpaceWeatherGauge from '@/components/SpaceWeatherGauge.vue'
import { useStagedReveal } from '@/composables/useStagedReveal'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const chatSection = ref<HTMLElement | null>(null)

const AsyncHeliosGlobe = defineAsyncComponent(() => import('@/components/HeliosGlobe.vue'))
const AsyncChatInterface = defineAsyncComponent(() => import('@/components/ChatInterface.vue'))

const staged = useStagedReveal({
  globeDelayMs: 450,
  chatDelayMs: 1400,
})

onMounted(() => {
  staged.start()

  const target = chatSection.value
  if (!target) return

  const observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry?.isIntersecting) {
        staged.triggerChat()
        observer.disconnect()
      }
    },
    { rootMargin: '240px 0px' }
  )

  observer.observe(target)
})
```

Update the template sections:

```vue
<section class="globe-section">
  <HomeGlobePlaceholder v-if="!staged.showGlobe" />
  <AsyncHeliosGlobe v-else />
  <div class="globe-fade" />
</section>
```

```vue
<section ref="chatSection" class="chat-section">
  <HomeChatPlaceholder v-if="!staged.showChat" />
  <AsyncChatInterface v-else />
</section>
```

Keep the existing data cards, protocol section, wearable section, and attribution synchronous.

- [ ] **Step 4: Run the focused tests and build**

Run:

```bash
npm run test -- src/composables/useStagedReveal.test.ts
npm run build
```

Expected:

- Vitest passes.
- Build passes.

- [ ] **Step 5: Commit**

```bash
git add src/pages/HomePage.vue src/components/home/HomeGlobePlaceholder.vue src/components/home/HomeChatPlaceholder.vue
git commit -m "Stage home route globe and chat loading"
```

---

### Task 3: Isolate Heavy Chunks in Vite Output

**Files:**
- Modify: `vite.config.ts`

- [ ] **Step 1: Add explicit manual chunking**

Modify `vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

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
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/services\.swpc\.noaa\.gov\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'noaa-cache', expiration: { maxAgeSeconds: 300 } },
          },
          {
            urlPattern: /^https:\/\/api\.open-meteo\.com\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'meteo-cache', expiration: { maxAgeSeconds: 600 } },
          },
        ],
      },
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three')) return 'three-core'
          if (id.includes('node_modules/globe.gl')) return 'globe-vendor'
          if (id.includes('src/components/HeliosGlobe.vue')) return 'home-globe'
          if (id.includes('src/components/ChatInterface.vue')) return 'home-chat'
          if (id.includes('node_modules')) return 'vendor'
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

- [ ] **Step 2: Run the build and capture the chunk output**

Run:

```bash
npm run build
```

Expected:

- Build passes.
- `three` and globe-related code are emitted in separate chunks instead of inflating the initial home route the same way.

- [ ] **Step 3: Verify the outcome against the baseline**

Run:

```bash
npm run build | Select-String "HomePage|three|globe|ChatInterface"
```

Expected:

- `HomePage` chunk is materially smaller than the original `~1.25 MB` baseline.
- `three` remains large, but it is isolated in its own lazy chunk.

- [ ] **Step 4: Commit**

```bash
git add vite.config.ts
git commit -m "Split home route globe and chat chunks"
```

---

### Task 4: Final Verification and Cleanup

**Files:**
- Review only: `src/pages/HomePage.vue`
- Review only: `vite.config.ts`
- Review only: `src/composables/useStagedReveal.ts`

- [ ] **Step 1: Run the complete verification set**

Run:

```bash
npm run test -- src/composables/useStagedReveal.test.ts
npm run build
```

Expected:

- Vitest passes.
- Production build passes.

- [ ] **Step 2: Re-check the home route output**

Run:

```bash
npm run build | Select-String "HomePage|three|globe|home-chat|home-globe"
```

Expected:

- The initial home route chunk is meaningfully lower than the original baseline.
- `three` and globe code are isolated into non-critical chunks.

- [ ] **Step 3: Commit**

```bash
git add src/pages/HomePage.vue src/components/home/HomeGlobePlaceholder.vue src/components/home/HomeChatPlaceholder.vue src/composables/useStagedReveal.ts src/composables/useStagedReveal.test.ts vite.config.ts
git commit -m "Reduce home route bundle with staged loading"
```

---

## Self-Review

### Spec coverage

- Async staged globe loading is covered in Task 2.
- Lazy chat loading is covered in Task 2.
- Preserving the route shell and synchronous protocol/data widgets is covered in Task 2.
- Chunk isolation for `three` / `globe.gl` is covered in Task 3.
- Verification against bundle output is covered in Tasks 3 and 4.

### Placeholder scan

- No `TODO`, `TBD`, or “similar to above” placeholders remain.
- Each code-changing step includes concrete code.
- Each verification step includes a real command and expected result.

### Type consistency

- The staged composable returns `showGlobe`, `showChat`, `start`, and `triggerChat` consistently.
- The route uses `defineAsyncComponent` boundaries with named placeholders.
- Chunk names remain consistent across Task 3 and Task 4.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-09-home-bundle-staged-loading.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
