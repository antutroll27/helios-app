# HELIOS Audit — Code Quality

**Date:** 2026-04-11
**Scope:** jetlag.ts, useCobeGlobeData.ts, ChatResponseRenderer.vue, SettingsPage.vue, OnboardingModal.vue, protocol.ts
**Status:** Approved

---

## Issues Being Fixed

### 1. Duplicated timezone offset helper (Low)

**Files:** `src/stores/jetlag.ts`, `src/composables/useCobeGlobeData.ts`

Both files implement functionally identical functions for computing timezone offset hours using `Intl.DateTimeFormat.formatToParts`. This logic is duplicated and should be extracted to a shared location.

**Implementation:**

Read both files to understand the exact implementations. Then:

1. Create `src/lib/timezoneUtils.ts` exporting a single `getTimezoneOffsetHours(timezone: string): number` function (use the better-named version from the two implementations)
2. In `jetlag.ts`, remove the local function and import from `@/lib/timezoneUtils`
3. In `useCobeGlobeData.ts`, remove the local function and import from `@/lib/timezoneUtils`

Do not change the logic — only consolidate it.

---

### 2. Duplicated fmt() time-formatting helper (Low)

**Files:** `src/stores/protocol.ts`, `src/composables/useAI.ts`

Both define a `fmt(date: Date): string` function calling `toLocaleTimeString`. They are near-identical (minor locale difference). Since these are in different modules with different purposes (store vs composable), and the functions are private/module-scoped, this is lower priority than #1.

**Implementation:**

Add `fmtTime(date: Date): string` to `src/lib/timezoneUtils.ts` (the file created in fix #1):
```ts
export function fmtTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
```

Then:
- In `protocol.ts`, remove the local `fmt` function and import `fmtTime as fmt` from `@/lib/timezoneUtils`
- In `useAI.ts`, check if a local `fmt` exists and if so, remove it and import `fmtTime as fmt`

Read both files first to confirm the exact function signatures and usage.

---

### 3. healthIconMap typed as `object` (Low)

**File:** `src/components/ChatResponseRenderer.vue`

`const healthIconMap: Record<string, object>` types values as `object` — too loose for Vue component constructors. Fix: type as `Record<string, Component>`.

**Implementation:**

Read `src/components/ChatResponseRenderer.vue` to find the map declaration. The file has **no existing Vue import** — add a fresh one:

```ts
import { type Component } from 'vue'
const healthIconMap: Record<string, Component> = { ... }
```

Also note: `fmtTime` in `timezoneUtils.ts` uses `[]` (system locale) while `useAI.ts`'s existing `fmt` uses `'en-US'`. Replacing the `useAI.ts` version with `fmtTime` is an intentional trade-off — system locale is preferred for consistency across the codebase, and the AI system prompt time strings are not locale-sensitive for correctness.

---

### 4. Hardcoded `color-scheme: dark` on time inputs (Low)

**Files:** `src/pages/SettingsPage.vue`, `src/components/OnboardingModal.vue`

Both have `.time-input { color-scheme: dark }` hardcoded in scoped CSS. In light mode, native time picker chrome appears dark while surrounding UI is light.

**Implementation:**

In both files, replace the hardcoded `color-scheme: dark` with a CSS variable approach:

```css
.time-input {
  color-scheme: dark; /* default — matches :root dark theme */
}

:root.light .time-input {
  color-scheme: light;
}
```

Note: scoped styles don't pierce the `:root` class directly. Use `:global(:root.light) .time-input` or move the override to the global `src/style.css` targeting `.time-input` inside `.light`. Read both files to understand the current structure before deciding which approach fits.

---

### 5. Implicit Date `>` comparison in protocol.ts (Low)

**File:** `src/stores/protocol.ts` line ~57

`idealWake > solar.wakeWindowStart` compares Date objects using `>`. While this works via implicit `valueOf()`, it is not obvious. Fix: use explicit `.getTime()` comparison.

**Implementation:**

Read `src/stores/protocol.ts` to find the exact line. Replace:
```ts
idealWake > solar.wakeWindowStart
```
With:
```ts
idealWake.getTime() > solar.wakeWindowStart.getTime()
```

---

## Success Criteria

1. `npm run build` passes with zero TypeScript errors
2. `src/lib/timezoneUtils.ts` exists and exports `getTimezoneOffsetHours` and `fmtTime`
3. Neither `jetlag.ts` nor `useCobeGlobeData.ts` contain a local timezone offset function
4. `healthIconMap` typed as `Record<string, Component>` — no `object`
5. Time inputs in SettingsPage and OnboardingModal respect light/dark theme
6. Date comparison in protocol.ts uses explicit `.getTime()`
