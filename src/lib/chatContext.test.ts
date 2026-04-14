import { describe, expect, it } from 'vitest'
import { buildChatContextSnapshot } from './chatContext'

describe('buildChatContextSnapshot', () => {
  it('serializes live store values for authenticated backend chat', () => {
    const snapshot = buildChatContextSnapshot({
      geo: { lat: 51.5, lng: -0.12, timezone: 'Europe/London', locationName: 'London, UK' },
      solar: { solarPhase: 'Night', elevationDeg: -12.5, sunriseTime: '06:08', sunsetTime: '19:47', solarNoon: '12:58' },
      spaceWeather: { kpIndex: 4, disruptionLabel: 'Active', bzComponent: -6, solarWindSpeed: 520, disruptionAdvisory: 'Observational context only' },
      environment: { uvIndexNow: 0, temperatureNow: 18, temperatureNight: 12, aqiLevel: 38, humidity: 74 },
      protocol: { wakeWindow: '07:00', caffeineCutoff: '14:30', peakFocus: '15:00-18:00', windDown: '21:30', sleepTarget: '22:45' },
      user: { usualSleepTime: '22:45', chronotype: 'late' },
    })

    expect(snapshot.location.location_name).toBe('London, UK')
    expect(snapshot.user.sleep_time).toBe('22:45')
    expect(snapshot.space_weather.kp_index).toBe(4)
    expect(snapshot.protocol.peak_focus).toBe('15:00-18:00')
  })
})
