# HELIOS Code Quality Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract duplicated timezone and time-formatting helpers into a shared utility file, tighten one loose type annotation, fix time inputs hardcoded to dark mode, and replace an implicit Date comparison with an explicit one.

**Architecture:** Task 1 creates `src/lib/timezoneUtils.ts` and Tasks 2–4 replace local copies with imports from it. Tasks 5–7 are independent one-file fixes. All tasks are low-risk and independently verifiable with `npm run build`.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Pinia, Vite 8. No new npm dependencies.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `helios-app/src/lib/timezoneUtils.ts` | **Create** | Export `getTimezoneOffsetHours` and `fmtTime` |
| `helios-app/src/stores/jetlag.ts` | Modify | Remove local `getTzOffsetHours`; import `getTimezoneOffsetHours` |
| `helios-app/src/composables/useCobeGlobeData.ts` | Modify | Remove local `getTimeZoneOffsetHours`; import `getTimezoneOffsetHours` |
| `helios-app/src/stores/protocol.ts` | Modify | Remove module-level `fmt`; import `fmtTime as fmt` |
| `helios-app/src/composables/useAI.ts` | Modify | Remove local `fmt`; import `fmtTime as fmt` |
| `helios-app/src/components/ChatResponseRenderer.vue` | Modify | Add `import { type Component } from 'vue'`; retype `healthIconMap` |
| `helios-app/src/pages/SettingsPage.vue` | Modify | Add `:global(:root.light) .time-input` override in scoped CSS |
| `helios-app/src/components/OnboardingModal.vue` | Modify | Add `:global(:root.light) .time-input` override in scoped CSS |
| `helios-app/src/stores/protocol.ts` | Modify | Replace implicit `>` Date comparison with `.getTime()` |

---

## Task 1: Create `src/lib/timezoneUtils.ts`

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issues 1 & 2

**Files:**
- Create: `helios-app/src/lib/timezoneUtils.ts`

**Context:**

Two separate implementations of the same timezone offset logic exist:

In `jetlag.ts` as `getTzOffsetHours(tz, date)`:
```ts
function getTzOffsetHours(tz: string, date: Date): number {
  const fmtOptions: Intl.DateTimeFormatOptions = { timeZone: tz, ... }
  const parts = new Intl.DateTimeFormat('en-US', fmtOptions).formatToParts(date)
  const get = (type: string): number => { ... }
  const localMs = Date.UTC(get('year'), get('month') - 1, ...)
  const offsetMs = localMs - date.getTime()
  return Math.round((offsetMs / 3_600_000) * 4) / 4
}
```

In `useCobeGlobeData.ts` as `getTimeZoneOffsetHours(timeZone, date)`:
```ts
function getTimeZoneOffsetHours(timeZone: string, date: Date) {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone, ... }).formatToParts(date)
  const pick = (type: string) => Number(parts.find(...)?.value ?? 0)
  const localMs = Date.UTC(pick('year'), pick('month') - 1, ...)
  return Math.round(((localMs - date.getTime()) / 3_600_000) * 4) / 4
}
```

Both produce identical values. The shared file will use the `getTimeZoneOffsetHours` implementation from `useCobeGlobeData.ts` (cleaner `pick` helper, no intermediate `get` function).

Additionally, both `protocol.ts` (line 218) and `useAI.ts` (line 50) define a local `fmt(date: Date): string` helper. They differ only by locale (`[]` vs `'en-US'`). The shared `fmtTime` will use `[]` (system locale) — a deliberate trade-off that aligns with system locale consistency. The AI system prompt time strings are not locale-sensitive for correctness.

- [ ] **Step 1: Create `timezoneUtils.ts`**

Create `helios-app/src/lib/timezoneUtils.ts` with exactly this content:

```ts
/**
 * Returns the UTC offset in hours for a given IANA timezone at a given instant.
 * Uses Intl.DateTimeFormat.formatToParts to read local time parts and computes
 * the offset vs UTC, handling DST automatically.
 * Result is rounded to the nearest quarter-hour to avoid floating-point noise.
 */
export function getTimezoneOffsetHours(timeZone: string, date: Date): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)

  const pick = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? 0)

  const localMs = Date.UTC(
    pick('year'),
    pick('month') - 1,
    pick('day'),
    pick('hour'),
    pick('minute'),
    pick('second'),
  )

  return Math.round(((localMs - date.getTime()) / 3_600_000) * 4) / 4
}

/**
 * Formats a Date as a locale time string (HH:MM, 2-digit hour and minute).
 * Uses the system locale (no explicit locale string) for consistency across the codebase.
 */
export function fmtTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
```

- [ ] **Step 2: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built`. The new file is not yet imported by anything, so no behaviour change.

- [ ] **Step 3: Commit**

```bash
cd helios-app && git add src/lib/timezoneUtils.ts && git commit -m "refactor: create timezoneUtils.ts with shared getTimezoneOffsetHours and fmtTime"
```

---

## Task 2: Replace local timezone helper in `jetlag.ts`

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issue 1

**Files:**
- Modify: `helios-app/src/stores/jetlag.ts`

**Context:**

`getTzOffsetHours` is declared as a module-scope function starting at line 65 and is called in two places:
- `generateJetLagSchedule` at line 145–146 (`getTzOffsetHours(input.originTz, ...)`, `getTzOffsetHours(input.destinationTz, ...)`)
- `totalShiftHours` computed at lines 288–291 (`getTzOffsetHours(tripInput.value.originTz, ...)`, `getTzOffsetHours(tripInput.value.destinationTz, ...)`)

The replacement `getTimezoneOffsetHours` from `timezoneUtils.ts` has identical behaviour.

- [ ] **Step 1: Add the import**

At the top of `helios-app/src/stores/jetlag.ts`, add after the existing imports:

```ts
import { getTimezoneOffsetHours } from '@/lib/timezoneUtils'
```

- [ ] **Step 2: Remove the local `getTzOffsetHours` function**

Delete the entire `getTzOffsetHours` function (lines 65–89 approximately — the JSDoc comment through the closing `}`).

- [ ] **Step 3: Replace all call sites**

Replace all calls to `getTzOffsetHours(` with `getTimezoneOffsetHours(` throughout the file. There are exactly 4 call sites in `generateJetLagSchedule` and `totalShiftHours`. The function signature is identical — same argument order (`tz, date`).

- [ ] **Step 4: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 5: Commit**

```bash
cd helios-app && git add src/stores/jetlag.ts && git commit -m "refactor: replace local getTzOffsetHours with shared getTimezoneOffsetHours"
```

---

## Task 3: Replace local timezone helper in `useCobeGlobeData.ts`

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issue 1

**Files:**
- Modify: `helios-app/src/composables/useCobeGlobeData.ts`

**Context:**

`getTimeZoneOffsetHours` is declared at lines 68–92 and called in `buildDestinationComparisons` at lines 147 and 150. The shared `getTimezoneOffsetHours` in `timezoneUtils.ts` was extracted from this exact implementation — they are identical.

- [ ] **Step 1: Add the import**

At the top of `helios-app/src/composables/useCobeGlobeData.ts`, add after the existing imports:

```ts
import { getTimezoneOffsetHours } from '@/lib/timezoneUtils'
```

- [ ] **Step 2: Remove the local `getTimeZoneOffsetHours` function**

Delete the entire `getTimeZoneOffsetHours` function (lines 68–92 approximately).

- [ ] **Step 3: Replace all call sites**

Replace all calls to `getTimeZoneOffsetHours(` with `getTimezoneOffsetHours(` in the file. There are exactly 2 call sites inside `buildDestinationComparisons`.

- [ ] **Step 4: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 5: Commit**

```bash
cd helios-app && git add src/composables/useCobeGlobeData.ts && git commit -m "refactor: replace local getTimeZoneOffsetHours with shared getTimezoneOffsetHours"
```

---

## Task 4: Replace local `fmt` helpers with `fmtTime` in protocol.ts and useAI.ts

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issue 2

**Files:**
- Modify: `helios-app/src/stores/protocol.ts`
- Modify: `helios-app/src/composables/useAI.ts`

**Context:**

`protocol.ts` defines at line 218 (outside the store, module-scoped):
```ts
function fmt(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
```

`useAI.ts` defines at lines 50–52 (module-scoped):
```ts
function fmt(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}
```

Both are replaced by `fmtTime` from `timezoneUtils.ts` which uses `[]` (system locale). The change from `'en-US'` to `[]` in `useAI.ts` is intentional — AI system prompt time strings do not require a specific locale for correctness. Import as `fmtTime as fmt` to avoid renaming all 10+ call sites.

**Step-by-step for `protocol.ts`:**

- [ ] **Step 1: Add `fmtTime` import to protocol.ts**

At the top of `helios-app/src/stores/protocol.ts`, add after the existing imports:

```ts
import { fmtTime as fmt } from '@/lib/timezoneUtils'
```

- [ ] **Step 2: Remove the local `fmt` function from protocol.ts**

Delete the module-level `fmt` function at the bottom of the file (line 218+):
```ts
function fmt(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
```

- [ ] **Step 3: Build check (protocol.ts)**

```bash
cd helios-app && npm run build
```

Expected: `✓ built`. All `fmt(...)` calls in `dailyProtocol` now resolve to the imported `fmtTime`.

**Step-by-step for `useAI.ts`:**

- [ ] **Step 4: Add `fmtTime` import to useAI.ts**

At the top of `helios-app/src/composables/useAI.ts`, add after the existing imports:

```ts
import { fmtTime as fmt } from '@/lib/timezoneUtils'
```

- [ ] **Step 5: Remove the local `fmt` function from useAI.ts**

Delete the module-level `fmt` function at lines 50–52:
```ts
function fmt(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}
```

- [ ] **Step 6: Build check (useAI.ts)**

```bash
cd helios-app && npm run build
```

Expected: `✓ built`.

- [ ] **Step 7: Commit**

```bash
cd helios-app && git add src/stores/protocol.ts src/composables/useAI.ts && git commit -m "refactor: replace local fmt() helpers with shared fmtTime from timezoneUtils"
```

---

## Task 5: Fix `healthIconMap` typed as `object` in ChatResponseRenderer.vue

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issue 3

**Files:**
- Modify: `helios-app/src/components/ChatResponseRenderer.vue` lines 1–23

**Context:**

Current script at lines 1–4 and 17:
```ts
<script setup lang="ts">
import SpaceWeatherGauge from './SpaceWeatherGauge.vue'
import ProtocolCard from './ProtocolCard.vue'
import { Heart, Zap, Shield, Activity } from 'lucide-vue-next'
// ...
const healthIconMap: Record<string, object> = {
```

There is **no existing Vue import** in this file. `object` is too broad — it does not convey that values are Vue component constructors. The fix adds a fresh Vue import for `Component` and uses it as the value type.

- [ ] **Step 1: Add the Vue Component type import**

In `helios-app/src/components/ChatResponseRenderer.vue`, add a new import line after the existing imports:

```ts
import { type Component } from 'vue'
```

The complete import block should look like:
```ts
import SpaceWeatherGauge from './SpaceWeatherGauge.vue'
import ProtocolCard from './ProtocolCard.vue'
import { Heart, Zap, Shield, Activity } from 'lucide-vue-next'
import { type Component } from 'vue'
```

- [ ] **Step 2: Update the `healthIconMap` type annotation**

Find:
```ts
const healthIconMap: Record<string, object> = {
```
Replace with:
```ts
const healthIconMap: Record<string, Component> = {
```

- [ ] **Step 3: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 4: Commit**

```bash
cd helios-app && git add src/components/ChatResponseRenderer.vue && git commit -m "fix: type healthIconMap as Record<string, Component> instead of object"
```

---

## Task 6: Fix hardcoded `color-scheme: dark` on time inputs in light mode

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issue 4

**Files:**
- Modify: `helios-app/src/pages/SettingsPage.vue` (scoped CSS)
- Modify: `helios-app/src/components/OnboardingModal.vue` (scoped CSS)

**Context:**

Both files have `.time-input { color-scheme: dark }` hardcoded in their scoped CSS. In light mode (when `:root.light` is the class applied by `useTheme.ts`), the native time picker chrome appears dark while the surrounding UI is light.

Scoped CSS uses attribute selectors (e.g., `[data-v-abc123]`) so `:root.light .time-input` would not match without `:global`. The fix uses `:global(:root.light) .time-input` to reach the root selector from scoped CSS.

**For SettingsPage.vue:**

- [ ] **Step 1: Find the `.time-input` rule in SettingsPage.vue**

In `helios-app/src/pages/SettingsPage.vue`, find the scoped CSS block containing:
```css
.time-input {
  ...
  color-scheme: dark;
}
```

The `color-scheme: dark` property is at line 405 inside the `.time-input` rule.

- [ ] **Step 2: Add light mode override for SettingsPage.vue**

Keep `color-scheme: dark` in the existing `.time-input` rule (it serves as the default). After the `.time-input:focus` rule block, add:

```css
:global(:root.light) .time-input {
  color-scheme: light;
}
```

- [ ] **Step 3: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built`.

**For OnboardingModal.vue:**

- [ ] **Step 4: Find the `.time-input` rule in OnboardingModal.vue**

In `helios-app/src/components/OnboardingModal.vue`, find the scoped CSS block containing:
```css
.time-input {
  ...
  color-scheme: dark;
}
```

The `color-scheme: dark` property is at line 427 inside the `.time-input` rule.

- [ ] **Step 5: Add light mode override for OnboardingModal.vue**

Keep `color-scheme: dark` in the existing `.time-input` rule. After the `.time-input:focus` rule block, add:

```css
:global(:root.light) .time-input {
  color-scheme: light;
}
```

- [ ] **Step 6: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built`.

- [ ] **Step 7: Commit**

```bash
cd helios-app && git add src/pages/SettingsPage.vue src/components/OnboardingModal.vue && git commit -m "fix: add light mode color-scheme override for time inputs"
```

---

## Task 7: Fix implicit Date comparison in protocol.ts

**Spec:** `docs/superpowers/specs/2026-04-11-code-quality.md` § Issue 5

**Files:**
- Modify: `helios-app/src/stores/protocol.ts` line ~57

**Context:**

The `wakeWindowTime` computed at line 55–58 currently reads:
```ts
const wakeWindowTime = computed<Date>(() => {
  const idealWake = addHours(sleepTime.value, 8)
  return idealWake > solar.wakeWindowStart ? idealWake : solar.wakeWindowStart
})
```

`idealWake > solar.wakeWindowStart` compares two `Date` objects using `>`. This works via implicit `valueOf()`, but it is not obvious and TypeScript does not consider it best practice. The fix uses explicit `.getTime()` comparison.

- [ ] **Step 1: Replace the implicit Date comparison**

In `helios-app/src/stores/protocol.ts`, find:
```ts
  return idealWake > solar.wakeWindowStart ? idealWake : solar.wakeWindowStart
```
Replace with:
```ts
  return idealWake.getTime() > solar.wakeWindowStart.getTime() ? idealWake : solar.wakeWindowStart
```

- [ ] **Step 2: Build check**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors.

- [ ] **Step 3: Commit**

```bash
cd helios-app && git add src/stores/protocol.ts && git commit -m "fix: use explicit .getTime() for Date comparison in wakeWindowTime computed"
```

---

## Success Criteria

| # | Criterion |
|---|---|
| 1 | `npm run build` passes with zero TypeScript errors after all tasks |
| 2 | `src/lib/timezoneUtils.ts` exists and exports `getTimezoneOffsetHours` and `fmtTime` |
| 3 | Neither `jetlag.ts` nor `useCobeGlobeData.ts` contain a local timezone offset function |
| 4 | Neither `protocol.ts` nor `useAI.ts` contain a local `fmt` function |
| 5 | `healthIconMap` typed as `Record<string, Component>` — no `object` |
| 6 | Time inputs in SettingsPage and OnboardingModal have `:global(:root.light) .time-input { color-scheme: light }` |
| 7 | `wakeWindowTime` computed uses `.getTime()` for Date comparison |
