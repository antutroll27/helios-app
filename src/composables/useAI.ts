import { useGeoStore } from '@/stores/geo'
import { useSolarStore } from '@/stores/solar'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useEnvironmentStore } from '@/stores/environment'
import { useProtocolStore } from '@/stores/protocol'
import { useUserStore } from '@/stores/user'
import type { VisualCard } from '@/stores/chat'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AIResponse {
  message: string
  visualCards: VisualCard[]
}

interface OpenAIMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

interface ClaudeMessage {
  role: 'user' | 'assistant'
  content: string
}

// ─── Provider registry ────────────────────────────────────────────────────────

export const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', model: 'gpt-5.3', placeholder: 'sk-...' },
  { id: 'claude', name: 'Claude', model: 'claude-opus-4-6 / claude-sonnet-4-6', placeholder: 'sk-ant-...' },
  { id: 'kimi', name: 'Kimi 2.5 (DeepInfra)', model: 'moonshotai/Kimi-K2-Instruct', placeholder: 'ai335...' },
  { id: 'glm', name: 'GLM-4', model: 'glm-4-flash', placeholder: '...' },
] as const

const PROVIDER_CONFIGS: Record<string, { baseUrl: string; model: string }> = {
  openai: { baseUrl: 'https://api.openai.com/v1/chat/completions', model: 'gpt-5.3' },
  kimi: { baseUrl: 'https://api.deepinfra.com/v1/openai/chat/completions', model: 'moonshotai/Kimi-K2-Instruct' },
  glm: { baseUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', model: 'glm-4-flash' },
  claude: { baseUrl: 'https://api.anthropic.com/v1/messages', model: 'claude-opus-4-6' },
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function fmt(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// ─── Composable ───────────────────────────────────────────────────────────────

export function useAI() {
  /**
   * Build the HELIOS system prompt dynamically from live stores.
   */
  function buildSystemPrompt(): string {
    const geo = useGeoStore()
    const solar = useSolarStore()
    const spaceWeather = useSpaceWeatherStore()
    const environment = useEnvironmentStore()
    const protocol = useProtocolStore()
    const user = useUserStore()

    const dp = protocol.dailyProtocol
    const wakeStart = fmt(dp.wakeWindow.time)
    const wakeEnd = fmt(solar.wakeWindowEnd)
    const lightDuration = protocol.morningLightDurationMin
    const caffeineCutoff = fmt(dp.caffeineCutoff.time)
    const focusStart = fmt(dp.peakFocus.time)
    const focusEnd = fmt(protocol.peakFocusEnd)
    const windDown = fmt(dp.windDown.time)
    const sleepTime = fmt(dp.sleepWindow.time)

    return `You are HELIOS, a circadian intelligence engine powered by live NASA satellite data and peer-reviewed chronobiology research. You help users optimize their sleep, circadian rhythm, and biological performance.

RIGHT NOW you have access to these live data feeds:

LOCATION: ${geo.locationName} (${geo.lat}°, ${geo.lng}°) | Timezone: ${geo.timezone}
SOLAR: ${solar.solarPhase} | Elevation: ${solar.elevationDeg}° | Sunrise: ${fmt(solar.sunriseTime)} | Sunset: ${fmt(solar.sunsetTime)} | Solar Noon: ${fmt(solar.solarNoon)}
SPACE WEATHER: Kp Index: ${spaceWeather.kpIndex} (${spaceWeather.disruptionLabel}) | Bz: ${spaceWeather.bzComponent} nT | Solar Wind: ${spaceWeather.solarWindSpeed} km/s
ADVISORY: ${spaceWeather.disruptionAdvisory}
ENVIRONMENT: UV Index: ${environment.uvIndexNow} | Temperature: ${environment.temperatureNow}°C | Night Temp: ${environment.temperatureNight}°C | AQI: ${environment.aqiLevel} | Humidity: ${environment.humidity}%

CURRENT PROTOCOL (computed from live data):
- Wake Window: ${wakeStart} - ${wakeEnd}
- Morning Light: ${lightDuration} min starting at ${wakeStart}
- Caffeine Cutoff: ${caffeineCutoff}
- Peak Focus: ${focusStart} - ${focusEnd}
- Wind-Down: ${windDown}
- Sleep Target: ${sleepTime}

USER PROFILE: Usual sleep time: ${user.usualSleepTime} | Chronotype: ${user.chronotype}

TRAVEL SAFETY: You have access to US State Department travel advisories. When a user mentions traveling to a country, include the advisory level (1-4) and any relevant safety notes. Levels: 1=Exercise Normal Precautions, 2=Exercise Increased Caution, 3=Reconsider Travel, 4=Do Not Travel. Factor stress from high-risk destinations into the sleep protocol (stress elevates cortisol, disrupts sleep architecture).

RULES:
1. Always ground your advice in the live data above — cite specific values
2. When the user describes travel plans, generate a jet lag recovery schedule AND mention the travel advisory level for the destination
3. Explain how current space weather affects their sleep (Kp, Bz values)
4. Be concise but scientifically precise. Cite researchers by name when relevant.
5. You MUST respond with valid JSON in this format:
{
  "message": "Your conversational response here (can use markdown)",
  "visualCards": [
    {
      "type": "protocol" | "jetlag_timeline" | "health_impact" | "recommendation" | "space_weather",
      "title": "Card title",
      "data": { ... card-specific data }
    }
  ]
}

Visual card data schemas:
- protocol: { items: [{ key, title, time, icon, subtitle }] }
- jetlag_timeline: { days: [{ day, date, lightWindow, caffeineWindow, sleepTime, wakeTime, shiftDirection, shiftHours }], origin, destination, totalShift }
- health_impact: { metric, value, unit, severity ("good"|"warning"|"concern"), explanation }
- recommendation: { action, timing, reason, citation }
- space_weather: { kp, bz, speed, score, label, advisory }

6. Always include at least one visualCard in your response.
7. For health impacts, be specific about mechanisms (melatonin suppression, cortisol phase, HRV impact).`
  }

  /**
   * Send a message to the selected AI provider and return a structured response.
   */
  async function sendMessage(
    userMessage: string,
    provider: string,
    apiKey: string,
    conversationHistory: ClaudeMessage[] = [],
    proxyUrl?: string
  ): Promise<AIResponse> {
    const systemPrompt = buildSystemPrompt()
    const config = PROVIDER_CONFIGS[provider]

    if (!config) {
      throw new Error(`Unknown provider: ${provider}`)
    }

    let responseText: string

    if (provider === 'claude') {
      // ── Claude format ──────────────────────────────────────────────────────
      const claudeMessages: ClaudeMessage[] = [
        ...conversationHistory,
        { role: 'user', content: userMessage },
      ]

      const url = config.baseUrl
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model: config.model,
          system: systemPrompt,
          messages: claudeMessages,
          max_tokens: 2000,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText)
        throw new Error(`Claude API error ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      responseText = data?.content?.[0]?.text ?? ''
    } else {
      // ── OpenAI-compatible format (OpenAI, Kimi, GLM) ──────────────────────
      const openAIMessages: OpenAIMessage[] = [
        { role: 'system', content: systemPrompt },
        ...conversationHistory.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        })),
        { role: 'user', content: userMessage },
      ]

      const url = proxyUrl ?? config.baseUrl
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      }

      if (proxyUrl) {
        headers['X-Provider'] = provider
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: config.model,
          messages: openAIMessages,
          temperature: 0.7,
          max_tokens: 2000,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText)
        throw new Error(`${provider} API error ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      responseText = data?.choices?.[0]?.message?.content ?? ''
    }

    // ── Parse structured JSON response ─────────────────────────────────────
    return parseAIResponse(responseText)
  }

  return {
    buildSystemPrompt,
    sendMessage,
  }
}

// ─── Response parser ──────────────────────────────────────────────────────────

function parseAIResponse(raw: string): AIResponse {
  if (!raw) {
    return { message: 'No response received from the AI provider.', visualCards: [] }
  }

  // Strip markdown code fences if the model wrapped JSON in ```json ... ```
  const stripped = raw
    .replace(/^```(?:json)?\s*/i, '')
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
    // JSON parsing failed — return raw text with no visual cards
    return { message: raw, visualCards: [] }
  }
}
