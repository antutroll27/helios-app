<script setup lang="ts">
import { computed } from 'vue'
import ChatResponseRenderer from '@/components/ChatResponseRenderer.vue'
import { parseChatMessageContent } from '@/lib/chatFormatting'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{
  message: ChatMessage
}>()

const isUser = computed(() => props.message.role === 'user')

const formattedTime = computed(() => {
  const d = new Date(props.message.timestamp)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
})

const renderedSegments = computed(() => parseChatMessageContent(props.message.content))

const hasVisualCards = computed(
  () => props.message.visualCards && props.message.visualCards.length > 0
)
</script>

<template>
  <div
    class="chat-message-row"
    :class="{ 'chat-message-row--user': isUser, 'chat-message-row--assistant': !isUser }"
  >
    <div
      class="chat-bubble"
      :class="{
        'chat-bubble--user': isUser,
        'chat-bubble--assistant': !isUser,
        'chat-bubble--loading': message.loading
      }"
    >
      <!-- Loading dots -->
      <div v-if="message.loading" class="loading-dots">
        <span class="dot" />
        <span class="dot" />
        <span class="dot" />
      </div>

      <!-- Content -->
      <div
        v-else-if="message.content"
        class="chat-bubble-content"
      >
        <template v-for="(segment, index) in renderedSegments" :key="index">
          <br v-if="segment.kind === 'break'" />
          <strong v-else-if="segment.kind === 'bold'">{{ segment.text }}</strong>
          <em v-else-if="segment.kind === 'italic'">{{ segment.text }}</em>
          <span v-else>{{ segment.text }}</span>
        </template>
      </div>

      <!-- Visual cards -->
      <div v-if="hasVisualCards && !message.loading" class="chat-visual-cards">
        <ChatResponseRenderer :cards="message.visualCards!" />
      </div>
    </div>

    <!-- Timestamp -->
    <span
      class="chat-timestamp"
      :class="{ 'chat-timestamp--right': isUser }"
    >
      {{ formattedTime }}
    </span>
  </div>
</template>

<style scoped>
.chat-message-row {
  display: flex;
  flex-direction: column;
  max-width: 85%;
  animation: msgFadeIn 0.35s ease-out forwards;
}
.chat-message-row--user {
  align-self: flex-end;
  align-items: flex-end;
}
.chat-message-row--assistant {
  align-self: flex-start;
  align-items: flex-start;
}

@keyframes msgFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Bubble ─────────────────────────────────────────── */

.chat-bubble {
  padding: 0.75rem 1rem;
  line-height: 1.55;
  font-size: 0.85rem;
  font-family: var(--font-body);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.chat-bubble--user {
  background: rgba(255, 189, 118, 0.18);
  border: 1px solid rgba(255, 189, 118, 0.25);
  color: var(--text-primary);
  border-radius: 1rem 1rem 0.25rem 1rem;
}

.chat-bubble--assistant {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  color: var(--text-primary);
  border-radius: 1rem 1rem 1rem 0.25rem;
}

.chat-bubble--loading {
  padding: 1rem 1.25rem;
}

.chat-bubble-content :deep(strong) {
  font-weight: 600;
  color: var(--text-primary);
}

.chat-bubble-content :deep(em) {
  font-style: italic;
  color: var(--text-secondary);
}

/* ── Visual cards below message ─────────────────────── */

.chat-visual-cards {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
}

/* ── Loading dots ───────────────────────────────────── */

.loading-dots {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: dotBounce 1.4s ease-in-out infinite;
}
.dot:nth-child(2) {
  animation-delay: 0.16s;
}
.dot:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes dotBounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

/* ── Timestamp ──────────────────────────────────────── */

.chat-timestamp {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--text-muted);
  margin-top: 0.3rem;
  padding: 0 0.25rem;
  opacity: 0.7;
}
.chat-timestamp--right {
  text-align: right;
}
</style>
