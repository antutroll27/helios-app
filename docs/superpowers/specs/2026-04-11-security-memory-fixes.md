---
# HELIOS Audit — Security & Memory Fixes

**Date:** 2026-04-11
**Scope:** ChatMessage.vue, solar.ts (store), App.vue, NavBar.vue, spaceWeather.ts (store), env.d.ts
**Status:** Approved

---

## Issues Being Fixed

### 1. XSS via v-html in ChatMessage.vue (Critical)

**File:** `src/components/ChatMessage.vue`

The `renderedContent` computed injects AI response content via `v-html` after naive regex-based markdown replacement. HTML entities are not escaped before the regex runs, so `<script>`, `<img onerror=...>` etc. pass through unmodified. Fix: escape HTML entities first, then apply markdown replacements.

**Current implementation (lines 20–25):**

```ts
function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}
```

**Implementation:**

Add a `escapeHtml(str: string): string` helper before the `renderMarkdown` function:

```ts
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}
```

In `renderMarkdown`, call `escapeHtml(text)` as the **first** step before any regex replacement. The markdown regexes (`**bold**`, `*italic*`, `\n`) must run on the escaped string and produce HTML tags — these tags are safe because they were constructed by the renderer, not injected from external content.

The updated function becomes:

```ts
function renderMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}
```

Note: the existing backtick `` `code` `` replacement is not present in the current implementation — do not add it. Only modify the existing three replacements to operate on the escaped string.

---

### 2. onUnmounted in Pinia store — never fires (Critical)

**File:** `src/stores/solar.ts`

`onUnmounted()` is called inside `defineStore()` at line 18. Pinia stores use Vue's effect scope, not component lifecycle — `onUnmounted` never fires in this context, so the `setInterval` for `_nowInterval` is never cleared. Fix: replace `onUnmounted` with `onScopeDispose` from Vue.

**Current implementation (lines 1–2 and 18):**

```ts
import { computed, ref, onUnmounted } from 'vue'
// ...
onUnmounted(() => clearInterval(_nowInterval))
```

**Implementation:**

Replace the import and call site:

```ts
import { computed, ref, onScopeDispose } from 'vue'
// ...
onScopeDispose(() => clearInterval(_nowInterval))
```

`onScopeDispose` is the correct Vue API for cleanup inside Pinia stores. It fires when the store's effect scope is disposed (e.g., when the app unmounts or the store is reset), guaranteeing the interval is always cleared.

---

### 3. Space weather polling never stopped (High)

**File:** `src/App.vue`

`sw.startPolling()` is called in `onMounted` (line 25) but `sw.stopPolling()` is never called. The `stopPolling` method exists in the space weather store (confirmed at lines 158–163 of `spaceWeather.ts`). On HMR remount, duplicate polling intervals accumulate because `startPolling` guards against duplicate intervals within the same store instance, but a fresh store instance on remount does not clear the previous interval.

**Current implementation (lines 1–26):**

```ts
import { onMounted } from 'vue'
// ...
onMounted(async () => {
  await geo.requestLocation()
  await Promise.allSettled([
    sw.fetchAll(),
    donki.fetchAll(),
    env.fetchAll(geo.lat, geo.lng)
  ])
  sw.startPolling()
})
```

**Implementation:**

Add `onUnmounted` to the import and call `sw.stopPolling()` inside it:

```ts
import { onMounted, onUnmounted } from 'vue'
// ...
onUnmounted(() => {
  sw.stopPolling()
})
```

`stopPolling` sets `pollingInterval` to `null` after clearing, so it is safe to call multiple times.

---

### 4. Broken "Restart demo" — wrong localStorage key (High)

**File:** `src/components/NavBar.vue`

`localStorage.removeItem('helios_onboarded')` (line 26) removes a key that does not exist. The actual key used by the user store is constructed using the `PREFIX` constant (`'helios_'`) concatenated with the field name `'hasCompletedOnboarding'`, which gives `'helios_hasCompletedOnboarding'`.

**Confirmed by reading `src/stores/user.ts`:**

```ts
const PREFIX = 'helios_'

function save<T>(key: string, value: T): void {
  localStorage.setItem(PREFIX + key, JSON.stringify(value))
}

// Called as:
watch(hasCompletedOnboarding, (v) => save('hasCompletedOnboarding', v))
```

The stored key is therefore `helios_hasCompletedOnboarding`.

**Current implementation (line 26):**

```ts
localStorage.removeItem('helios_onboarded')
```

**Implementation:**

Replace with the correct key:

```ts
localStorage.removeItem('helios_hasCompletedOnboarding')
```

The `user.hasCompletedOnboarding = false` assignment on line 25 resets the in-memory ref correctly. The `localStorage.removeItem` fix ensures the persisted value is also cleared, so the onboarding modal appears on next page reload.

---

### 5. flareClass ref never populated (High)

**File:** `src/stores/spaceWeather.ts`

`const flareClass = ref<string>('None')` is declared at line 25 and exported at line 169, but is never assigned anywhere in the store. The `fetchAll` function calls five fetchers (`fetchKpIndex`, `fetchSolarWindMag`, `fetchSolarWindPlasma`, `fetchAlerts`, `fetchGScale`) — none of which populate `flareClass`. There is no `fetchFlares` function in the current implementation; flare data is not currently fetched from NOAA.

**Current state:** `flareClass` is always `'None'` regardless of actual solar flare activity.

**Implementation:**

Since there is no `activeFlares` array in the current store (confirmed by reading the full file), the fix should wire `flareClass` to the existing `activeAlerts` array, which is populated by `fetchAlerts`. NOAA alert messages contain flare class references in their `product_id` field (e.g., `AL_FLARE_CLASS_M1.5`).

Add the following after `lastUpdated.value = new Date()` at the end of `fetchAll`:

```ts
// Extract flare class from active NOAA alerts.
// NOAA flare alerts contain flare class strings (e.g. "M1.5", "X2.3") in the
// message body text, not in product_id (which uses WMO routing codes like "ALTK07").
const flareAlert = activeAlerts.value.find(
  (a) => a.message?.toUpperCase().includes('FLARE')
)
// If a flare alert is found, attempt to extract the class from the message.
// Fall back to 'Active' if a flare message exists but class cannot be parsed.
flareClass.value = flareAlert
  ? (flareAlert.message?.match(/\b([MXC]\d+\.?\d*)\b/)?.[1] ?? 'Active')
  : 'None'
```

This searches `message` (not `product_id`) because NOAA WMO product codes (`ALTK07`, `WATA20`) do not contain the word "FLARE". The flare class string (e.g. `M1.5`, `X2.3`) appears in the alert message body and is extracted with the regex `\b([MXC]\d+\.?\d*)\b`.

**Alternative (if a dedicated flare endpoint is added later):** When `activeFlares` is introduced, replace the above with:

```ts
flareClass.value = activeFlares.value.length > 0
  ? (activeFlares.value[0].classType ?? 'None')
  : 'None'
```

The exact field name (`classType`) must be verified against the NOAA DONKI API response shape when that endpoint is integrated.

---

### 6. Stale ambient module declarations (High)

**File:** `src/env.d.ts`

The file contains ambient `declare module 'globe.gl'` (lines 9–12) and `declare module 'three'` (lines 14–22) declarations for libraries no longer used. The project migrated from `globe.gl` + `Three.js` to COBE (confirmed in `CLAUDE.md`: "Replaced globe.gl/Three.js with COBE"). These stale type stubs suppress real TypeScript type errors if those packages are accidentally re-imported.

**Current content of `src/env.d.ts`:**

```ts
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'globe.gl' {
  const Globe: any
  export default Globe
}

declare module 'three' {
  export class DirectionalLight {
    constructor(color: number, intensity: number)
    position: { set(x: number, y: number, z: number): void }
  }
  export class AmbientLight {
    constructor(color: number, intensity: number)
  }
}
```

**Implementation:**

Remove the `declare module 'globe.gl'` and `declare module 'three'` blocks entirely. The file after the fix should contain only:

```ts
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

---

## Success Criteria

1. `npm run build` passes with zero TypeScript errors after all changes
2. XSS: `<script>alert(1)</script>` in AI response content is rendered as escaped text (`&lt;script&gt;alert(1)&lt;/script&gt;`), not executed
3. Solar store: interval is cleaned up when the store scope is disposed (no memory leak on HMR or app teardown)
4. App.vue: `stopPolling` called in `onUnmounted` — no duplicate intervals on HMR remount
5. NavBar: clicking "Restart demo" clears `helios_hasCompletedOnboarding` from localStorage and the onboarding modal reappears on next reload
6. spaceWeather: `flareClass` reflects actual flare activity derived from live NOAA alert data, not always `'None'`
7. env.d.ts: no stale `globe.gl` or `three` module declarations remain
