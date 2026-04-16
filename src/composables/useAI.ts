import { useAuthStore } from '@/stores/auth'
import { useGeoStore } from '@/stores/geo'
import { useSolarStore } from '@/stores/solar'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useEnvironmentStore } from '@/stores/environment'
import { useProtocolStore } from '@/stores/protocol'
import { useUserStore } from '@/stores/user'
import { buildChatContextSnapshot } from '@/lib/chatContext'
import type { VisualCard } from '@/stores/chat'
import { fmtTimeInZone } from '@/lib/timezoneUtils'

export interface AIResponse {
  message: string
  visualCards: VisualCard[]
}

export interface BackendAIResponse extends AIResponse {
  sessionId?: string
}

export const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', model: 'gpt-5.4', placeholder: 'sk-...' },
  { id: 'claude', name: 'Claude', model: 'claude-sonnet-4-6', placeholder: 'sk-ant-...' },
  { id: 'gemini', name: 'Gemini', model: 'gemini-3.1-flash-lite-preview', placeholder: 'AIzaSy...' },
  { id: 'grok', name: 'Grok', model: 'grok-4.20-0309-non-reasoning', placeholder: 'xai-...' },
  { id: 'perplexity', name: 'Perplexity', model: 'sonar-pro', placeholder: 'pplx-...' },
  { id: 'kimi', name: 'Kimi', model: 'moonshotai/Kimi-K2.5', placeholder: 'ai335...' },
  { id: 'glm', name: 'GLM', model: 'glm-5.1', placeholder: '...' },
] as const

export function useAI() {
  async function sendMessage(
    userMessage: string,
    provider: string,
    apiKey: string,
    conversationHistory: Array<{ role: 'user' | 'assistant'; content: string }> = [],
    sessionId?: string,
  ): Promise<BackendAIResponse> {
    const auth = useAuthStore()
    const backendUrl = import.meta.env.VITE_BACKEND_URL

    if (!auth.isAuthenticated || !auth.csrfToken) {
      throw new Error('HELIOS chat requires a signed-in session.')
    }

    const geo = useGeoStore()
    const solar = useSolarStore()
    const spaceWeather = useSpaceWeatherStore()
    const environment = useEnvironmentStore()
    const protocol = useProtocolStore()
    const user = useUserStore()
    const dp = protocol.dailyProtocol
    const displayTimezone = geo.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
    const fmtLocationTime = (date: Date) => fmtTimeInZone(date, displayTimezone)

    const contextSnapshot = buildChatContextSnapshot({
      geo: {
        lat: geo.lat,
        lng: geo.lng,
        timezone: displayTimezone,
        locationName: geo.locationName,
      },
      solar: {
        solarPhase: solar.solarPhase,
        elevationDeg: solar.elevationDeg,
        sunriseTime: fmtLocationTime(solar.sunriseTime),
        sunsetTime: fmtLocationTime(solar.sunsetTime),
        solarNoon: fmtLocationTime(solar.solarNoon),
      },
      spaceWeather: {
        kpIndex: spaceWeather.kpIndex,
        disruptionLabel: spaceWeather.disruptionLabel,
        bzComponent: spaceWeather.bzComponent,
        solarWindSpeed: spaceWeather.solarWindSpeed,
        disruptionAdvisory: spaceWeather.disruptionAdvisory,
      },
      environment: {
        uvIndexNow: environment.uvIndexNow,
        temperatureNow: environment.temperatureNow,
        temperatureNight: environment.temperatureNight,
        aqiLevel: environment.aqiLevel,
        humidity: environment.humidity,
      },
      protocol: {
        wakeWindow: `${fmtLocationTime(dp.wakeWindow.time)}-${fmtLocationTime(dp.wakeWindow.endTime ?? solar.wakeWindowEnd)}`,
        caffeineCutoff: fmtLocationTime(dp.caffeineCutoff.time),
        peakFocus: `${fmtLocationTime(dp.peakFocus.time)}-${fmtLocationTime(protocol.peakFocusEnd)}`,
        windDown: fmtLocationTime(dp.windDown.time),
        sleepTarget: fmtLocationTime(dp.sleepWindow.time),
      },
      user: {
        usualSleepTime: user.usualSleepTime,
        chronotype: user.chronotype,
      },
    })

    const apiBase = backendUrl ?? ''
    const response = await fetch(`${apiBase}/api/chat/send`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-HELIOS-CSRF': auth.csrfToken,
      },
      body: JSON.stringify({
        message: userMessage,
        provider,
        api_key: apiKey.trim(),
        session_id: sessionId ?? null,
        context: contextSnapshot,
        history: conversationHistory,
      }),
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText)
      throw new Error(`Backend error ${response.status}: ${errorText}`)
    }

    const data = await response.json()
    const messageText = typeof data.message === 'string' ? data.message : ''
    const parsed = parseAIResponse(messageText)

    return {
      message: parsed.message,
      visualCards: Array.isArray(data.visual_cards) ? data.visual_cards : parsed.visualCards,
      sessionId: data.session_id,
    }
  }

  return {
    sendMessage,
  }
}

function parseAIResponse(raw: string): AIResponse {
  if (!raw) {
    return { message: 'No response received from the backend.', visualCards: [] }
  }

  const stripped = raw
    .replace(/^\s*```(?:json)?\s*/i, '')
    .replace(/\s*```\s*$/, '')
    .trim()

  try {
    const parsed = JSON.parse(stripped) as { message?: unknown; visualCards?: unknown }
    const message = typeof parsed.message === 'string' ? parsed.message : raw
    const visualCards = Array.isArray(parsed.visualCards)
      ? (parsed.visualCards as VisualCard[])
      : []
    return { message, visualCards }
  } catch {
    return { message: raw, visualCards: [] }
  }
}
