# HELIOS Security & Memory Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix six critical/high-severity bugs covering XSS injection, a memory leak in the solar store, a duplicate polling interval in App.vue, a broken "Restart demo" button, an always-`'None'` flare class, and stale ambient module declarations.

**Architecture:** All fixes are isolated one- or two-file changes with no new dependencies. Each task is independently verifiable with `npm run build`. The XSS fix is the highest priority and must ship first; the remaining five can be applied in any order.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Pinia, Vite 8.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `helios-app/src/components/ChatMessage.vue` | Modify | Add `escapeHtml` helper; pipe escaped string through `renderMarkdown` |
| `helios-app/src/stores/solar.ts` | Modify | Replace `onUnmounted` import + call with `onScopeDispose` |
| `helios-app/src/App.vue` | Modify | Add `onUnmounted` import; add `sw.stopPolling()` in `onUnmounted` callback |
| `helios-app/src/components/NavBar.vue` | Modify | Fix localStorage key from `'helios_onboarded'` → `'helios_hasCompletedOnboarding'` |
| `helios-app/src/stores/spaceWeather.ts` | Modify | Populate `flareClass.value` at end of `fetchAll` by parsing `activeAlerts` |
| `helios-app/src/env.d.ts` | Modify | Remove `declare module 'globe.gl'` and `declare module 'three'` blocks |

---

## Task 1: XSS fix — escape HTML entities in ChatMessage.vue

**Spec:** `docs/superpowers/specs/2026-04-11-security-memory-fixes.md` § Issue 1

**Files:**
- Modify: `helios-app/src/components/ChatMessage.vue` lines 20–25

**Context:**

Current `renderMarkdown` at lines 20–25:
```ts
function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}
```

The function passes raw AI content directly to `v-html` without escaping `<`, `>`, `&`, `"`, `'`. A response containing `<script>alert(1)</script>` executes in the browser.

The fix is to add an `escapeHtml` function **before** `renderMarkdown` and call it as the **first** step inside `renderMarkdown`. The markdown regexes then run on the already-escaped string and produce safe HTML tags.

- [ ] **Step 1: Read the file to confirm current line numbers**

Read `helios-app/src/components/ChatMessage.vue` and confirm `renderMarkdown` is at lines 20–25 with no existing `escapeHtml` function.

- [ ] **Step 2: Add `escapeHtml` helper and update `renderMarkdown`**

In `helios-app/src/components/ChatMessage.vue`, add the following block immediately **before** the `renderMarkdown` function (i.e., insert before line 20):

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

Then update `renderMarkdown` to call `escapeHtml(text)` as the first step:

```ts
function renderMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}
```

Do NOT add a backtick `` `code` `` replacement — the existing implementation has only three replacements; keep it that way.

- [ ] **Step 3: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 4: Commit**

```bash
cd helios-app && git add src/components/ChatMessage.vue && git commit -m "security: escape HTML entities before markdown rendering to prevent XSS"
```

---

## Task 2: Memory fix — replace `onUnmounted` with `onScopeDispose` in solar.ts

**Spec:** `docs/superpowers/specs/2026-04-11-security-memory-fixes.md` § Issue 2

**Files:**
- Modify: `helios-app/src/stores/solar.ts` lines 1–2 and 18

**Context:**

Current file at line 2:
```ts
import { computed, ref, onUnmounted } from 'vue'
```
At line 18:
```ts
onUnmounted(() => clearInterval(_nowInterval))
```

`onUnmounted` never fires inside a Pinia store because Pinia stores use Vue's effect scope, not a component lifecycle. The `setInterval` for `_nowInterval` therefore leaks on HMR remount and app teardown. `onScopeDispose` fires when the store's effect scope is disposed.

- [ ] **Step 1: Update the Vue import**

In `helios-app/src/stores/solar.ts`, replace:
```ts
import { computed, ref, onUnmounted } from 'vue'
```
With:
```ts
import { computed, ref, onScopeDispose } from 'vue'
```

- [ ] **Step 2: Update the cleanup call**

In `helios-app/src/stores/solar.ts`, replace:
```ts
onUnmounted(() => clearInterval(_nowInterval))
```
With:
```ts
onScopeDispose(() => clearInterval(_nowInterval))
```

- [ ] **Step 3: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 4: Commit**

```bash
cd helios-app && git add src/stores/solar.ts && git commit -m "fix: replace onUnmounted with onScopeDispose in solar store to prevent interval leak"
```

---

## Task 3: Polling cleanup — add `stopPolling` in App.vue `onUnmounted`

**Spec:** `docs/superpowers/specs/2026-04-11-security-memory-fixes.md` § Issue 3

**Files:**
- Modify: `helios-app/src/App.vue` lines 1–26

**Context:**

Current `App.vue` script:
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

`sw.stopPolling()` is never called. On HMR remount, a new store instance is created and `startPolling()` registers a fresh `setInterval` without clearing the previous one, resulting in duplicate polling intervals.

`stopPolling()` already exists in `spaceWeather.ts` (lines 158–163) and clears + nulls the interval, making it safe to call multiple times.

- [ ] **Step 1: Update the Vue import**

In `helios-app/src/App.vue`, replace:
```ts
import { onMounted } from 'vue'
```
With:
```ts
import { onMounted, onUnmounted } from 'vue'
```

- [ ] **Step 2: Add `onUnmounted` callback**

After the closing `})` of the `onMounted` block, add:

```ts
onUnmounted(() => {
  sw.stopPolling()
})
```

- [ ] **Step 3: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 4: Commit**

```bash
cd helios-app && git add src/App.vue && git commit -m "fix: stop space weather polling on unmount to prevent duplicate intervals"
```

---

## Task 4: LocalStorage key fix — correct "Restart demo" key in NavBar.vue

**Spec:** `docs/superpowers/specs/2026-04-11-security-memory-fixes.md` § Issue 4

**Files:**
- Modify: `helios-app/src/components/NavBar.vue` line 26

**Context:**

Current `fullReload` function in NavBar.vue at line 26:
```ts
localStorage.removeItem('helios_onboarded')
```

The actual key written by `user.ts` is constructed as `PREFIX + key` = `'helios_'` + `'hasCompletedOnboarding'` = `'helios_hasCompletedOnboarding'`. The current code removes a key that doesn't exist, so `hasCompletedOnboarding` persists in localStorage and the onboarding modal never reappears on page reload.

The in-memory reset on line 25 (`user.hasCompletedOnboarding = false`) is correct — only the localStorage removal is wrong.

- [ ] **Step 1: Fix the localStorage key**

In `helios-app/src/components/NavBar.vue`, find and replace:
```ts
localStorage.removeItem('helios_onboarded')
```
With:
```ts
localStorage.removeItem('helios_hasCompletedOnboarding')
```

- [ ] **Step 2: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built`.

- [ ] **Step 3: Commit**

```bash
cd helios-app && git add src/components/NavBar.vue && git commit -m "fix: correct localStorage key in NavBar restart demo button"
```

---

## Task 5: flareClass — populate from NOAA alert messages in spaceWeather.ts

**Spec:** `docs/superpowers/specs/2026-04-11-security-memory-fixes.md` § Issue 5

**Files:**
- Modify: `helios-app/src/stores/spaceWeather.ts` — end of `fetchAll` function (after line 147)

**Context:**

`const flareClass = ref<string>('None')` is declared at line 25 and exported at line 169 but never assigned. `fetchAll` sets `lastUpdated.value = new Date()` at line 147 and then returns. The value is always `'None'`.

**Important:** NOAA `product_id` fields contain WMO routing codes like `'ALTK07'` — they do NOT contain the word "FLARE". Flare class strings (e.g. `'M1.5'`, `'X2.3'`) appear in the `message` body text of alerts. The fix must:
1. Search `a.message` (not `a.product_id`) for the word "FLARE"
2. Extract the class string using regex `\b([MXC]\d+\.?\d*)\b`
3. Fall back to `'Active'` if a flare message is found but the class can't be parsed
4. Fall back to `'None'` if no flare message exists

- [ ] **Step 1: Add flareClass population at the end of `fetchAll`**

In `helios-app/src/stores/spaceWeather.ts`, find:
```ts
    lastUpdated.value = new Date()
  }
```

And replace with:
```ts
    lastUpdated.value = new Date()

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
  }
```

- [ ] **Step 2: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 3: Commit**

```bash
cd helios-app && git add src/stores/spaceWeather.ts && git commit -m "fix: populate flareClass from NOAA alert message body instead of always returning None"
```

---

## Task 6: Remove stale ambient module declarations from env.d.ts

**Spec:** `docs/superpowers/specs/2026-04-11-security-memory-fixes.md` § Issue 6

**Files:**
- Modify: `helios-app/src/env.d.ts`

**Context:**

The file currently contains:
```ts
declare module 'globe.gl' {
  const Globe: any
  export default Globe
}

declare module 'three' {
  export class DirectionalLight { ... }
  export class AmbientLight { ... }
}
```

These were for the old globe.gl + Three.js implementation. The project migrated to COBE (`cobe` library). These stubs suppress TypeScript errors if either package is accidentally re-imported. They must be removed. Only the `/// <reference>` directive and `declare module '*.vue'` block should remain.

- [ ] **Step 1: Remove the stale declarations**

Overwrite `helios-app/src/env.d.ts` with:

```ts
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 2: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors. If `globe.gl` or `three` are accidentally imported anywhere, TypeScript will now report errors — investigate and remove those imports.

- [ ] **Step 3: Commit**

```bash
cd helios-app && git add src/env.d.ts && git commit -m "chore: remove stale globe.gl and three.js ambient module declarations"
```

---

## Success Criteria

| # | Criterion |
|---|---|
| 1 | `npm run build` passes with zero TypeScript errors after all 6 tasks |
| 2 | `renderMarkdown('<script>alert(1)</script>')` returns `'&lt;script&gt;alert(1)&lt;/script&gt;'` — not executed via `v-html` |
| 3 | `solar.ts`: `onScopeDispose` imported and called — `onUnmounted` not present |
| 4 | `App.vue`: `onUnmounted` imported and `sw.stopPolling()` called inside it |
| 5 | `NavBar.vue`: `localStorage.removeItem('helios_hasCompletedOnboarding')` — not `'helios_onboarded'` |
| 6 | `spaceWeather.ts`: `flareClass.value` set at end of `fetchAll` using `activeAlerts` message search |
| 7 | `env.d.ts`: no `globe.gl` or `three` declarations remain |
