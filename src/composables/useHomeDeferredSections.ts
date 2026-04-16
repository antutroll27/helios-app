import { onBeforeUnmount, onMounted, ref } from 'vue'

import { useStagedReveal } from './useStagedReveal'

const CHAT_ROOT_MARGIN = '240px 0px'

export function useHomeDeferredSections() {
  const chatSectionRef = ref<HTMLElement | null>(null)
  const stagedReveal = useStagedReveal({
    globeDelayMs: 450,
    chatDelayMs: 1400,
  })

  let chatObserver: IntersectionObserver | null = null

  function disconnectObserver() {
    chatObserver?.disconnect()
    chatObserver = null
  }

  function createChatObserver() {
    const section = chatSectionRef.value

    if (!section) {
      return
    }

    if (typeof IntersectionObserver === 'undefined') {
      stagedReveal.triggerChat()
      return
    }

    chatObserver = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) {
          return
        }

        stagedReveal.triggerChat()
        disconnectObserver()
      },
      {
        rootMargin: CHAT_ROOT_MARGIN,
        threshold: 0.01,
      },
    )

    chatObserver.observe(section)
  }

  onMounted(() => {
    stagedReveal.start()
    createChatObserver()
  })

  onBeforeUnmount(() => {
    disconnectObserver()
    stagedReveal.stop()
  })

  return {
    chatSectionRef,
    showGlobe: stagedReveal.showGlobe,
    showChat: stagedReveal.showChat,
  }
}
