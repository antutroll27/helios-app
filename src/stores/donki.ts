import { defineStore } from 'pinia'
import { ref } from 'vue'

const BASE_URL = 'https://api.nasa.gov/DONKI'
const NASA_KEY = () => import.meta.env.VITE_NASA_API_KEY as string

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CMEAnalysis {
  time21_5: string
  latitude: number
  longitude: number
  halfAngle: number
  speed: number
  type: string
  isMostAccurate: boolean
  note: string
  levelOfData: number
  link: string
  enlilList?: EnlilModel[]
}

export interface EnlilModel {
  modelCompletionTime: string
  au: number
  isEarthGB: boolean
  impactList?: ImpactEntry[]
}

export interface ImpactEntry {
  isGlancingBlow: boolean
  location: string
  arrivalTime: string
}

export interface GeomagneticStorm {
  gstID: string
  startTime: string
  allKpIndex?: KpIndexEntry[]
  linkedEvents?: LinkedEvent[]
}

export interface KpIndexEntry {
  observedTime: string
  kpIndex: number
  source: string
}

export interface SolarFlare {
  flrID: string
  beginTime: string
  peakTime: string
  endTime: string
  classType: string
  sourceLocation: string
  activeRegionNum: number
  linkedEvents?: LinkedEvent[]
}

export interface LinkedEvent {
  activityID: string
}

export interface DonkiNotification {
  messageType: string
  messageID: string
  messageURL: string
  messageIssueTime: string
  messageBody: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function daysAgo(n: number): Date {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d
}

function daysAhead(n: number): Date {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useDonkiStore = defineStore('donki', () => {
  const upcomingCMEs = ref<CMEAnalysis[]>([])
  const recentStorms = ref<GeomagneticStorm[]>([])
  const activeFlares = ref<SolarFlare[]>([])
  const notifications = ref<DonkiNotification[]>([])
  const nextGeostormEta = ref<number | null>(null) // hours until next predicted storm
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // ─── Individual fetchers ──────────────────────────────────────────────────

  async function fetchCMEs(): Promise<void> {
    const start = formatDate(daysAgo(2))
    const end = formatDate(daysAhead(7))
    const url = `${BASE_URL}/CMEAnalysis?startDate=${start}&endDate=${end}&mostAccurateOnly=true&completeEntryOnly=true&speed=500&halfAngle=30&catalog=ALL&api_key=${NASA_KEY()}`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`CMEAnalysis fetch failed: ${response.status}`)
    const data: CMEAnalysis[] = await response.json()
    upcomingCMEs.value = Array.isArray(data) ? data : []

    // Compute ETA for next Earth-directed CME
    let earliestArrival: number | null = null
    for (const cme of upcomingCMEs.value) {
      if (!cme.enlilList) continue
      for (const model of cme.enlilList) {
        if (!model.isEarthGB || !model.impactList) continue
        for (const impact of model.impactList) {
          if (impact.location !== 'Earth') continue
          const arrivalMs = new Date(impact.arrivalTime).getTime()
          const hoursUntil = (arrivalMs - Date.now()) / (1000 * 60 * 60)
          if (hoursUntil > 0 && (earliestArrival === null || hoursUntil < earliestArrival)) {
            earliestArrival = hoursUntil
          }
        }
      }
    }
    nextGeostormEta.value = earliestArrival !== null ? parseFloat(earliestArrival.toFixed(1)) : null
  }

  async function fetchStorms(): Promise<void> {
    const start = formatDate(daysAgo(7))
    const end = formatDate(new Date())
    const url = `${BASE_URL}/GST?startDate=${start}&endDate=${end}&api_key=${NASA_KEY()}`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`GST fetch failed: ${response.status}`)
    const data: GeomagneticStorm[] = await response.json()
    recentStorms.value = Array.isArray(data) ? data : []
  }

  async function fetchFlares(): Promise<void> {
    const start = formatDate(daysAgo(1))
    const end = formatDate(new Date())
    const url = `${BASE_URL}/FLR?startDate=${start}&endDate=${end}&api_key=${NASA_KEY()}`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`FLR fetch failed: ${response.status}`)
    const data: SolarFlare[] = await response.json()
    activeFlares.value = Array.isArray(data) ? data : []
  }

  async function fetchNotifications(): Promise<void> {
    const start = formatDate(daysAgo(3))
    const end = formatDate(new Date())
    const url = `${BASE_URL}/notifications?startDate=${start}&endDate=${end}&type=all&api_key=${NASA_KEY()}`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`Notifications fetch failed: ${response.status}`)
    const data: DonkiNotification[] = await response.json()
    const relevantTypes = ['GST', 'CME', 'IPS', 'FLR']
    notifications.value = Array.isArray(data)
      ? data.filter((n) => relevantTypes.includes(n.messageType))
      : []
  }

  // ─── Parallel fetch all ───────────────────────────────────────────────────

  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null

    const results = await Promise.allSettled([
      fetchCMEs(),
      fetchStorms(),
      fetchFlares(),
      fetchNotifications()
    ])

    const errors: string[] = []
    for (const result of results) {
      if (result.status === 'rejected') {
        const msg = result.reason instanceof Error ? result.reason.message : String(result.reason)
        errors.push(msg)
        console.warn('[donki] fetch error:', msg)
      }
    }

    if (errors.length > 0) {
      error.value = errors.join('; ')
    }

    loading.value = false
  }

  return {
    upcomingCMEs,
    recentStorms,
    activeFlares,
    notifications,
    nextGeostormEta,
    loading,
    error,
    fetchAll,
    // Expose helpers for external use
    formatDate,
    daysAgo,
    daysAhead
  }
})
