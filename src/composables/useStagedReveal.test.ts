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

  it('does not auto-reveal chat before the globe stage', () => {
    const reveal = useStagedReveal({
      globeDelayMs: 1200,
      chatDelayMs: 400,
      autoRevealChat: true,
    })

    reveal.start()

    vi.advanceTimersByTime(400)

    expect(reveal.showGlobe.value).toBe(false)
    expect(reveal.showChat.value).toBe(false)

    vi.advanceTimersByTime(799)

    expect(reveal.showGlobe.value).toBe(false)
    expect(reveal.showChat.value).toBe(false)

    vi.advanceTimersByTime(1)

    expect(reveal.showGlobe.value).toBe(true)
    expect(reveal.showChat.value).toBe(true)
  })

  it('stops pending timers when stopped explicitly', () => {
    const reveal = useStagedReveal({
      globeDelayMs: 400,
      chatDelayMs: 1200,
      autoRevealChat: true,
    })

    reveal.start()
    reveal.stop()

    vi.advanceTimersByTime(2000)

    expect(reveal.showGlobe.value).toBe(false)
    expect(reveal.showChat.value).toBe(false)
  })
})
