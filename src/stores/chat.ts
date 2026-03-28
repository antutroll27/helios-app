import { defineStore } from 'pinia'
import { ref } from 'vue'

// ─── Types ────────────────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant'

export type VisualCardType =
  | 'protocol'
  | 'jetlag_timeline'
  | 'health_impact'
  | 'recommendation'
  | 'space_weather'
  | 'environment'

export interface VisualCard {
  type: VisualCardType
  title: string
  data: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  visualCards?: VisualCard[]
  timestamp: Date
  loading: boolean
}

// ─── ID generator ─────────────────────────────────────────────────────────────

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref<boolean>(false)

  function addUserMessage(content: string): ChatMessage {
    const message: ChatMessage = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
      loading: false
    }
    messages.value.push(message)
    return message
  }

  function addAssistantMessage(content: string, visualCards?: VisualCard[]): ChatMessage {
    const message: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content,
      visualCards: visualCards ?? undefined,
      timestamp: new Date(),
      loading: false
    }
    messages.value.push(message)
    return message
  }

  /**
   * Adds a loading placeholder for a streaming assistant response.
   * Returns the message id so the caller can update it once streaming completes.
   */
  function addLoadingMessage(): string {
    const id = generateId()
    const message: ChatMessage = {
      id,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true
    }
    messages.value.push(message)
    isStreaming.value = true
    return id
  }

  /**
   * Finalise a previously added loading message with its streamed content.
   */
  function finaliseMessage(id: string, content: string, visualCards?: VisualCard[]): void {
    const message = messages.value.find((m) => m.id === id)
    if (message) {
      message.content = content
      message.loading = false
      if (visualCards) message.visualCards = visualCards
    }
    isStreaming.value = false
  }

  /**
   * Append a chunk to a streaming message (for token-by-token streaming).
   */
  function appendChunk(id: string, chunk: string): void {
    const message = messages.value.find((m) => m.id === id)
    if (message) {
      message.content += chunk
    }
  }

  function clearMessages(): void {
    messages.value = []
    isStreaming.value = false
  }

  return {
    messages,
    isStreaming,
    addUserMessage,
    addAssistantMessage,
    addLoadingMessage,
    finaliseMessage,
    appendChunk,
    clearMessages
  }
})
