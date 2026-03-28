declare module 'suncalc' {
  interface SunTimes {
    sunrise: Date
    sunriseEnd: Date
    goldenHourEnd: Date
    solarNoon: Date
    goldenHour: Date
    sunsetStart: Date
    sunset: Date
    dusk: Date
    nauticalDusk: Date
    night: Date
    nadir: Date
    nightEnd: Date
    nauticalDawn: Date
    dawn: Date
  }

  interface SunPosition {
    altitude: number
    azimuth: number
  }

  export function getTimes(date: Date, latitude: number, longitude: number): SunTimes
  export function getPosition(date: Date, latitude: number, longitude: number): SunPosition
}
