<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { useAI, PROVIDERS } from '@/composables/useAI'
import { useAuthStore } from '@/stores/auth'
import ChatMessage from '@/components/ChatMessage.vue'
import { ChevronUp, ChevronDown, Send } from 'lucide-vue-next'

const chat = useChatStore()
const user = useUserStore()
const ai = useAI()

const isExpanded = ref(false)
const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

const auth = useAuthStore()
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

const sessionId = ref<string | null>(null)
let inactivityTimer: ReturnType<typeof setTimeout> | null = null

const WELCOME_MESSAGE =
  "I'm HELIOS. I have access to live NASA satellite data and your local solar conditions right now. Ask me anything about your sleep, circadian rhythm, or travel plans."

const hasApiKey = computed(() => !!user.apiKey)

const currentProviderName = computed(() => {
  const p = PROVIDERS.find((pr) => pr.id === user.provider)
  return p ? p.name : user.provider
})

// Seed welcome message on mount
onMounted(() => {
  if (chat.messages.length === 0) {
    chat.addAssistantMessage(WELCOME_MESSAGE)
  }
})

onUnmounted(() => {
  if (inactivityTimer) clearTimeout(inactivityTimer)
  endSession()
})

// Auto-scroll to bottom when messages change
watch(
  () => chat.messages.length,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    nextTick(() => scrollToBottom())
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

async function endSession() {
  // Guard: clear immediately to prevent double-call (inactivity timer + unmount racing)
  if (!sessionId.value || !BACKEND_URL) return
  const id = sessionId.value
  sessionId.value = null
  if (!auth.session) return
  fetch(`${BACKEND_URL}/api/chat/end-session?session_id=${id}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${auth.session.access_token}` },
  }).catch(() => {})  // fire-and-forget, never block unmount
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chat.isStreaming) return
  if (!hasApiKey.value) return

  // Expand on first send
  if (!isExpanded.value) isExpanded.value = true

  inputText.value = ''

  // 1. Add user message
  chat.addUserMessage(text)

  // 2. Add loading placeholder
  const loadingId = chat.addLoadingMessage()

  await nextTick()
  scrollToBottom()

  try {
    // Build conversation history (exclude loading message)
    const history = chat.messages
      .filter((m) => !m.loading && m.id !== loadingId)
      .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))

    // Remove the last user message from history since sendMessage adds it
    history.pop()

    // 3. Call AI
    const response = await ai.sendMessage(
      text,
      user.provider,
      user.apiKey,
      history,
      sessionId.value ?? undefined,
    )

    // Capture session_id from backend response and reset inactivity timer
    if (response.sessionId) {
      sessionId.value = response.sessionId
    }
    if (BACKEND_URL && auth.session) {
      if (inactivityTimer) clearTimeout(inactivityTimer)
      inactivityTimer = setTimeout(endSession, 10 * 60 * 1000)
    }

    // 4. Finalise
    chat.finaliseMessage(loadingId, response.message, response.visualCards)
  } catch (err: unknown) {
    const errorMsg =
      err instanceof Error ? err.message : 'Something went wrong. Please try again.'
    chat.finaliseMessage(
      loadingId,
      `**Error:** ${errorMsg}`
    )
  }

  await nextTick()
  scrollToBottom()
}
</script>

<template>
  <div class="chat-interface" :class="{ 'chat-interface--expanded': isExpanded }">
    <!-- Header -->
    <button class="chat-header" @click="toggleExpand">
      <div class="chat-header-left">
        <span class="chat-header-title font-display tracking-label">ASK HELIOS</span>
        <span v-if="hasApiKey" class="chat-provider-chip font-mono">
          {{ currentProviderName }}
        </span>
      </div>
      <component
        :is="isExpanded ? ChevronDown : ChevronUp"
        :size="18"
        style="color: var(--text-muted); flex-shrink: 0;"
      />
    </button>

    <!-- Messages area (visible when expanded) -->
    <div v-if="isExpanded" ref="messagesContainer" class="chat-messages">
      <ChatMessage
        v-for="msg in chat.messages"
        :key="msg.id"
        :message="msg"
      />
    </div>

    <!-- Input area -->
    <div class="chat-input-area">
      <div v-if="!hasApiKey" class="chat-no-key">
        <span>Configure your AI provider in settings to start chatting</span>
      </div>
      <div v-else class="chat-input-wrap">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="chat-input"
          placeholder="Ask about your sleep, travel, or circadian health..."
          rows="1"
          :disabled="chat.isStreaming"
          @keydown="handleKeydown"
        />
        <button
          class="chat-send-btn"
          :disabled="!inputText.trim() || chat.isStreaming"
          @click="sendMessage"
        >
          <Send :size="16" color="#0A171D" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 1rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-interface--expanded {
  max-height: 60vh;
}

/* ── Header ─────────────────────────────────────────── */

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  width: 100%;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.2s;
}
.chat-header:hover {
  background: var(--bg-card-hover);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.chat-header-title {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
}

.chat-provider-chip {
  font-size: 0.55rem;
  font-weight: 500;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: rgba(0, 63, 71, 0.35);
  color: #00D4AA;
  border: 1px solid rgba(0, 212, 170, 0.2);
}

/* ── Messages ───────────────────────────────────────── */

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 120px;
  max-height: calc(60vh - 120px);
  scroll-behavior: smooth;
}

/* Hide scrollbar for clean look */
.chat-messages::-webkit-scrollbar {
  width: 3px;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 2px;
}

/* ── Input area ─────────────────────────────────────── */

.chat-input-area {
  padding: 0.75rem;
  border-top: 1px solid var(--border-subtle);
}

.chat-input-wrap {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  padding: 0.375rem 0.375rem 0.375rem 0.875rem;
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.82rem;
  line-height: 1.5;
  resize: none;
  max-height: 80px;
  padding: 0.375rem 0;
}
.chat-input::placeholder {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.chat-send-btn {
  width: 34px;
  height: 34px;
  border-radius: 0.5rem;
  border: none;
  background: #FFBD76;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.chat-send-btn:hover:not(:disabled) {
  background: #FFD4A0;
  transform: scale(1.05);
}
.chat-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── No API key notice ──────────────────────────────── */

.chat-no-key {
  text-align: center;
  padding: 0.5rem 0;
}
.chat-no-key span {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
}
</style>
