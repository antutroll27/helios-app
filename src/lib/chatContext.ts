export interface ChatContextInput {
  geo: {
    lat: number
    lng: number
    timezone: string
    locationName: string
  }
  solar: {
    solarPhase: string
    elevationDeg: number
    sunriseTime: string
    sunsetTime: string
    solarNoon: string
  }
  spaceWeather: {
    kpIndex: number
    disruptionLabel: string
    bzComponent: number
    solarWindSpeed: number
    disruptionAdvisory: string
  }
  environment: {
    uvIndexNow: number
    temperatureNow: number
    temperatureNight: number
    aqiLevel: number
    humidity: number
  }
  protocol: {
    wakeWindow: string
    caffeineCutoff: string
    peakFocus: string
    windDown: string
    sleepTarget: string
  }
  user: {
    usualSleepTime: string
    chronotype: string
  }
}

export interface BackendChatContextSnapshot {
  location: {
    lat: number
    lng: number
    timezone: string
    location_name: string
  }
  solar: {
    phase: string
    elevation: number
    sunrise: string
    sunset: string
    solar_noon: string
  }
  space_weather: {
    kp_index: number
    label: string
    bz: number
    solar_wind: number
    advisory: string
  }
  environment: {
    uv_index: number
    temperature: number
    night_temp: number
    aqi: number
    humidity: number
  }
  protocol: {
    wake_window: string
    caffeine_cutoff: string
    peak_focus: string
    wind_down: string
    sleep_target: string
  }
  user: {
    sleep_time: string
    chronotype: string
  }
}

export function buildChatContextSnapshot(input: ChatContextInput): BackendChatContextSnapshot {
  return {
    location: {
      lat: input.geo.lat,
      lng: input.geo.lng,
      timezone: input.geo.timezone,
      location_name: input.geo.locationName,
    },
    solar: {
      phase: input.solar.solarPhase,
      elevation: input.solar.elevationDeg,
      sunrise: input.solar.sunriseTime,
      sunset: input.solar.sunsetTime,
      solar_noon: input.solar.solarNoon,
    },
    space_weather: {
      kp_index: input.spaceWeather.kpIndex,
      label: input.spaceWeather.disruptionLabel,
      bz: input.spaceWeather.bzComponent,
      solar_wind: input.spaceWeather.solarWindSpeed,
      advisory: input.spaceWeather.disruptionAdvisory,
    },
    environment: {
      uv_index: input.environment.uvIndexNow,
      temperature: input.environment.temperatureNow,
      night_temp: input.environment.temperatureNight,
      aqi: input.environment.aqiLevel,
      humidity: input.environment.humidity,
    },
    protocol: {
      wake_window: input.protocol.wakeWindow,
      caffeine_cutoff: input.protocol.caffeineCutoff,
      peak_focus: input.protocol.peakFocus,
      wind_down: input.protocol.windDown,
      sleep_target: input.protocol.sleepTarget,
    },
    user: {
      sleep_time: input.user.usualSleepTime,
      chronotype: input.user.chronotype,
    },
  }
}
