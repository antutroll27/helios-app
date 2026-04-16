import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchPublicJson } from '@/lib/publicApi'

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

interface DonkiSummaryResponse {
  upcoming_cmes?: CMEAnalysis[]
  recent_storms?: GeomagneticStorm[]
  active_flares?: SolarFlare[]
  notifications?: DonkiNotification[]
  next_geostorm_eta_hours?: number | null
}

export const useDonkiStore = defineStore('donki', () => {
  const upcomingCMEs = ref<CMEAnalysis[]>([])
  const recentStorms = ref<GeomagneticStorm[]>([])
  const activeFlares = ref<SolarFlare[]>([])
  const notifications = ref<DonkiNotification[]>([])
  const nextGeostormEta = ref<number | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await fetchPublicJson('/donki/summary') as DonkiSummaryResponse
      upcomingCMEs.value = data.upcoming_cmes ?? []
      recentStorms.value = data.recent_storms ?? []
      activeFlares.value = data.active_flares ?? []
      notifications.value = data.notifications ?? []
      nextGeostormEta.value = data.next_geostorm_eta_hours ?? null
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.warn('[donki] fetch error:', message)
      error.value = message
    } finally {
      loading.value = false
    }
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
  }
})
