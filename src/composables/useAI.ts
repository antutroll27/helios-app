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
  { id: 'openai', name: 'OpenAI', placeholder: 'sk-...' },
  { id: 'claude', name: 'Anthropic', placeholder: 'sk-ant-...' },
  { id: 'gemini', name: 'Google Gemini', placeholder: 'AIza...' },
  { id: 'perplexity', name: 'Perplexity', placeholder: 'pplx-...' },
  { id: 'kimi', name: 'Moonshot AI', placeholder: 'ai335...' },
  { id: 'qwen', name: 'Alibaba Qwen', placeholder: 'sk-...' },
  { id: 'glm', name: 'Zhipu AI', placeholder: '...' },
] as const

const PROVIDER_CONFIGS: Record<string, { baseUrl: string; model: string }> = {
  openai:     { baseUrl: 'https://api.openai.com/v1/chat/completions', model: 'gpt-4o' },
  gemini:     { baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions', model: 'gemini-2.5-flash' },
  perplexity: { baseUrl: 'https://api.perplexity.ai/chat/completions', model: 'sonar-pro' },
  kimi:       { baseUrl: 'https://api.deepinfra.com/v1/openai/chat/completions', model: 'moonshotai/Kimi-K2-Instruct' },
  qwen:       { baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', model: 'qwen-max' },
  glm:        { baseUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', model: 'glm-4-flash' },
  claude:     { baseUrl: 'https://api.anthropic.com/v1/messages', model: 'claude-sonnet-4-6-20250514' },
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

TRAVEL SAFETY: You have access to US State Department travel advisories. When a user mentions traveling to a country, include the advisory level (1-4) and any relevant safety notes. Factor stress from high-risk destinations into the sleep protocol.

PEER-REVIEWED SCIENTIFIC KNOWLEDGE BASE (use these exact findings):

CAFFEINE & CIRCADIAN PHASE:
- Burke et al. (2015, Science Translational Medicine 7(305):305ra146): Double espresso equivalent 3h before bedtime delays circadian melatonin rhythm by ~40 min via adenosine receptor/cAMP mechanism. This is roughly HALF the phase delay of 3h of 3000-lux bright evening light.
- Drake et al. (2013, J Clinical Sleep Medicine): 400mg caffeine taken 6h before bedtime STILL significantly disrupts sleep — reduces total sleep by >1h. Even 6h is not fully safe for sensitive individuals.
- 2024 RCT (Sleep journal): Caffeine impacts exceed clinical thresholds for sleep onset latency within 12h and for sleep efficiency within 8h of bedtime.
- Caffeine half-life is highly variable: 2-10 hours depending on genetics (CYP1A2), oral contraceptives (doubles half-life), smoking (halves it), and liver function. HELIOS uses 6h as median.
- IMPORTANT: Do NOT claim caffeine "blocks melatonin" — it DELAYS the circadian phase via adenosine receptor antagonism in the SCN, which is mechanistically distinct from melatonin suppression by light.

LIGHT & CIRCADIAN ENTRAINMENT:
- Morning bright light (>1000 lux) suppresses melatonin and advances circadian phase. Even 350 lux causes significant suppression (Zeitzer et al. 2000, J Physiology).
- Cortisol response to light: 800-lux exposure causes ~35% further increase in cortisol 20-40 min after waking. Effects begin within 15 min at >2000 lux.
- Optimal morning light duration: Research commonly uses 30-60 min exposures. 20 min is a practical minimum; effects are dose-dependent on intensity x duration.
- Blue/short-wavelength light (446-477nm) is most effective for circadian resetting via ipRGCs projecting to SCN.
- NASA ISS uses Solid-State Light Assemblies (SSLAs) with 3 modes: General (neutral), Bedtime (red-yellow), Phase Shift (high blue).

PEAK COGNITIVE PERFORMANCE:
- Core body temperature peaks in LATE EVENING (~10 PM for typical sleepers), NOT 2-3h before sleep onset. Cognitive performance peaks in late afternoon/early evening, roughly paralleling the temperature curve.
- The "wake maintenance zone" (hardest time to fall asleep) occurs 2-3h BEFORE habitual bedtime — this is when alertness peaks, not when you should schedule deep work.
- Chronotype matters: morning types peak earlier (~12-2 PM), evening types peak later (~6-8 PM). Always factor chronotype.
- CORRECTION: Do NOT say "peak focus is 2-3h before sleep." Say "cognitive performance peaks in late afternoon to early evening, varying by chronotype."

GEOMAGNETIC ACTIVITY & SLEEP:
- Burch et al. (1999, 2008, Neuroscience Letters): Elevated Kp index correlates with reduced overnight 6-OHMS (melatonin metabolite) excretion. Two independent studies in utility workers.
- Weydahl et al. (2001): Geomagnetic activity reduces melatonin at high latitudes (70°N) more than low latitudes.
- The mechanism is CORRELATIONAL and population-level, possibly mediated by cryptochrome photoreceptors and/or magnetite nanoparticles. NOT deterministic at individual level.
- 2024 study (Environment International): 1-IQR increase in Kp associated with 19% increase in odds of low cognitive scores in older adults.
- IMPORTANT: Always label geomagnetic effects as "emerging research" — the evidence is suggestive but not settled. Never overclaim.

SOCIAL JET LAG:
- Affects 70-80% of the population (≥1 hour). 30-40% experience ≥2 hours.
- Roenneberg et al. (2012, Current Biology): Independently associated with obesity and metabolic disruption.
- ≥2h social jet lag: higher 5h cortisol levels, reduced weekly sleep, increased resting heart rate, more physical inactivity.
- 2024 evidence: Social jet lag impairs exercise adaptation and mitochondrial content in muscle (npj Biological Timing and Sleep).
- Dose-dependent cardiovascular risk increase per hour of social jet lag.

NASA ASTRONAUT SLEEP:
- ISS crew average 6h sleep vs 8.5h recommended. Same circadian disruption mechanisms as travel jet lag.
- NASA classifies sleep deficiency as Category 1 risk for long-duration missions.
- Pre-flight phase shifting achieved 9-12h circadian shifts over 7 days using timed bright light + melatonin + sleep schedule manipulation (Whitson et al. 1995).
- Maximum safe phase shift: ~1-1.5h per day with protocol support. This is the basis for HELIOS jet lag schedules.

RULES:
1. Always ground your advice in the live data above — cite specific values and researcher names.
2. When the user describes travel plans, generate a jet lag recovery schedule AND mention the travel advisory level.
3. Explain how current space weather affects their sleep using Kp and Bz values. Always note this is "emerging research."
4. Be scientifically precise. Use the exact findings above. Never fabricate citations or overstate evidence levels.
5. Factor chronotype into all timing recommendations — morning types vs evening types have different peak windows.
6. You MUST respond with valid JSON in this format:
{
  "message": "Your conversational response here (can use markdown)",
  "visualCards": [
    {
      "type": "protocol" | "jetlag_timeline" | "health_impact" | "recommendation" | "space_weather" | "environment",
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

7. Always include at least one visualCard in your response.
8. For health impacts, be specific about mechanisms (adenosine antagonism, SCN phase delay, HRV suppression, cortisol elevation).
9. Never say "NASA endorses this app" or "approved by NASA." Say "powered by NASA APIs" or "data provided by NASA."`
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
  // The leading replace allows optional whitespace before the opening fence.
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
    // JSON parsing failed — return raw text with no visual cards
    return { message: raw, visualCards: [] }
  }
}
