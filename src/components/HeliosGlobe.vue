<template>
  <div class="helios-globe-wrapper" :style="{ height: height }">
    <div ref="globeContainer" class="helios-globe-canvas" />

    <!-- Right side HUD — mission control data overlay -->
    <div class="globe-hud-right">
      <div class="hud-section">
        <span class="hud-label">SOLAR ELEVATION</span>
        <span class="hud-value">{{ solarStore.elevationDeg.toFixed(1) }}°</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">PHASE</span>
        <span class="hud-value hud-value--sm">{{ solarStore.solarPhase }}</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">SUNRISE</span>
        <span class="hud-value">{{ fmt(solarStore.times.sunrise) }}</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">SUNSET</span>
        <span class="hud-value">{{ fmt(solarStore.times.sunset) }}</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">SOLAR NOON</span>
        <span class="hud-value">{{ fmt(solarStore.times.solarNoon) }}</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">NADIR</span>
        <span class="hud-value">{{ fmt(solarStore.times.nadir) }}</span>
      </div>
    </div>

    <!-- Left side — coordinates + satellite badge -->
    <div class="globe-hud-left">
      <div class="hud-section">
        <span class="hud-label">LATITUDE</span>
        <span class="hud-value">{{ geoStore.lat.toFixed(4) }}°</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">LONGITUDE</span>
        <span class="hud-value">{{ geoStore.lng.toFixed(4) }}°</span>
      </div>
      <div class="hud-divider" />
      <div class="hud-section">
        <span class="hud-label">TIMEZONE</span>
        <span class="hud-value hud-value--sm">{{ geoStore.timezone }}</span>
      </div>
    </div>

    <!-- Bottom center — attribution -->
    <div class="globe-badge-center">
      <span class="badge-dot pulse-live">●</span>
      <span class="badge-label">LIVE</span>
      <span class="badge-text">Powered by real-time NASA satellite data</span>
      <span class="badge-sats">DSCOVR · GOES-16 · SDO · NOAA SWPC · Open-Meteo</span>
    </div>

    <!-- Gradient fade at the bottom -->
    <div class="helios-globe-fade" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import Globe from 'globe.gl'
import { useGeoStore } from '@/stores/geo'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useSolarStore } from '@/stores/solar'

// ─── Props ───────────────────────────────────────────────────────────────────

const props = withDefaults(
  defineProps<{
    height?: string
  }>(),
  { height: '50vh' }
)

// ─── Stores ──────────────────────────────────────────────────────────────────

const geoStore = useGeoStore()
const spaceWeather = useSpaceWeatherStore()
const solarStore = useSolarStore()

// Keep old refs for existing globe code
const geo = geoStore
const solar = solarStore

function fmt(d: Date): string {
  try { return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  catch { return '--:--' }
}

// ─── Refs ────────────────────────────────────────────────────────────────────

const globeContainer = ref<HTMLElement | null>(null)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let globeInstance: any = null
let terminatorTimer: ReturnType<typeof setInterval> | null = null
let resizeObserver: ResizeObserver | null = null

// ─── Solar terminator helpers ────────────────────────────────────────────────

/**
 * Compute the sub-solar point (lat/lng where sun is directly overhead).
 * Uses the solar store's current sun position data.
 */
function getSubSolarPoint(): { lat: number; lng: number } {
  const now = solar.now
  // Julian date
  const JD = now.getTime() / 86400000 + 2440587.5
  const n = JD - 2451545.0
  // Mean longitude and mean anomaly (degrees)
  const L = (280.46 + 0.9856474 * n) % 360
  const g = ((357.528 + 0.9856003 * n) % 360) * (Math.PI / 180)
  // Ecliptic longitude
  const lambda = (L + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * (Math.PI / 180)
  // Obliquity of ecliptic
  const epsilon = 23.439 * (Math.PI / 180)
  // Declination
  const sinDec = Math.sin(epsilon) * Math.sin(lambda)
  const dec = Math.asin(sinDec) * (180 / Math.PI)
  // Greenwich Hour Angle
  const GMST = (18.697374558 + 24.06570982441908 * n) % 24
  const sunRA = Math.atan2(Math.cos(epsilon) * Math.sin(lambda), Math.cos(lambda)) * (12 / Math.PI)
  const GHA = ((GMST - sunRA) * 15 + 360) % 360
  const lng = GHA > 180 ? GHA - 360 : GHA

  return { lat: dec, lng: -lng }
}

/**
 * Build a GeoJSON polygon covering the night hemisphere.
 * We approximate it by creating a spherical cap centred on the anti-solar point.
 */
function buildTerminatorPolygon(): object[] {
  const { lat: sunLat, lng: sunLng } = getSubSolarPoint()

  // Anti-solar point
  const antiLat = -sunLat
  const antiLng = sunLng > 0 ? sunLng - 180 : sunLng + 180

  const antiLatRad = antiLat * (Math.PI / 180)
  const antiLngRad = antiLng * (Math.PI / 180)

  // Build a circle of radius ~90° around the anti-solar point
  const steps = 72
  const coords: [number, number][] = []

  for (let i = 0; i <= steps; i++) {
    const bearing = (i / steps) * 2 * Math.PI
    const angDist = Math.PI / 2 // 90° — the terminator circle

    // Spherical point at angDist from anti-solar point along bearing
    const lat2 = Math.asin(
      Math.sin(antiLatRad) * Math.cos(angDist) +
        Math.cos(antiLatRad) * Math.sin(angDist) * Math.cos(bearing)
    )
    const lng2 =
      antiLngRad +
      Math.atan2(
        Math.sin(bearing) * Math.sin(angDist) * Math.cos(antiLatRad),
        Math.cos(angDist) - Math.sin(antiLatRad) * Math.sin(lat2)
      )

    coords.push([lng2 * (180 / Math.PI), lat2 * (180 / Math.PI)])
  }

  // Close the ring
  coords.push(coords[0])

  return [
    {
      type: 'Feature',
      properties: { name: 'night' },
      geometry: {
        type: 'Polygon',
        coordinates: [coords]
      }
    }
  ]
}

// ─── Auroral oval ring data ───────────────────────────────────────────────────

interface RingDatum {
  lat: number
  lng: number
  maxR: number
  propagationSpeed: number
  repeatPeriod: number
  color: string
}

function buildAuroralRings(kp: number): RingDatum[] {
  const auroralLat = 90 - kp * 3
  const clamped = Math.max(55, Math.min(80, auroralLat))
  const color = kp >= 5 ? '#FF4444' : '#FFBD76'
  const opacity = Math.min(0.9, 0.3 + kp * 0.06)
  const colorWithOpacity = hexToRgba(color, opacity)

  // Each "ring" is a point on the auroral circle; we distribute several around
  // both poles to simulate a continuous oval
  const rings: RingDatum[] = []
  const pointCount = 12

  for (let i = 0; i < pointCount; i++) {
    const lngDeg = (i / pointCount) * 360 - 180
    // North pole oval
    rings.push({
      lat: clamped,
      lng: lngDeg,
      maxR: 4 + kp * 0.4,
      propagationSpeed: 1.5 + kp * 0.1,
      repeatPeriod: 1500 + Math.random() * 500,
      color: colorWithOpacity
    })
    // South pole oval
    rings.push({
      lat: -clamped,
      lng: lngDeg,
      maxR: 4 + kp * 0.4,
      propagationSpeed: 1.5 + kp * 0.1,
      repeatPeriod: 1500 + Math.random() * 500,
      color: colorWithOpacity
    })
  }

  return rings
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

// ─── Lifecycle ───────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!globeContainer.value) return

  const width = globeContainer.value.clientWidth
  const heightPx = globeContainer.value.clientHeight || 500

  globeInstance = Globe()(globeContainer.value)
    // Dimensions
    .width(width)
    .height(heightPx)
    // Earth textures
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
    .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
    // Stars
    .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
    // Atmosphere
    .showAtmosphere(true)
    .atmosphereColor('#1a3a5e')
    .atmosphereAltitude(0.15)

  // ── Sunlight — illuminate the dayside ──────────────────────────────────
  import('three').then((THREE) => {
    try {
      const scene = globeInstance?.scene()
      if (!scene) return

      const sunLight = new THREE.DirectionalLight(0xffeedd, 1.8)
      const subSolar = getSubSolarPoint()
      const sunR = 200
      const phi = (90 - subSolar.lat) * Math.PI / 180
      const theta = (subSolar.lng + 180) * Math.PI / 180
      sunLight.position.set(
        sunR * Math.sin(phi) * Math.cos(theta),
        sunR * Math.cos(phi),
        sunR * Math.sin(phi) * Math.sin(theta)
      )
      scene.add(sunLight)

      const ambient = new THREE.AmbientLight(0x222244, 0.4)
      scene.add(ambient)
    } catch (e) {
      console.warn('Sunlight skipped:', e)
    }
  })

  // ── Auto-rotate ──────────────────────────────────────────────────────────
  globeInstance.controls().autoRotate = true
  globeInstance.controls().autoRotateSpeed = 0.3
  globeInstance.controls().enableDamping = true
  globeInstance.controls().dampingFactor = 0.08

  // ── User location pin ────────────────────────────────────────────────────
  const userPin = [{ lat: geo.lat, lng: geo.lng, size: 0.5, color: '#FFBD76' }]

  globeInstance
    .pointsData(userPin)
    .pointColor('color')
    .pointAltitude(0.005)
    .pointRadius('size')
    .pointsMerge(false)
    .pointResolution(12)

  // ── Solar terminator ─────────────────────────────────────────────────────
  const applyTerminator = () => {
    globeInstance
      .polygonsData(buildTerminatorPolygon())
      .polygonCapColor(() => 'rgba(0, 0, 30, 0.38)')
      .polygonSideColor(() => 'rgba(0, 0, 0, 0)')
      .polygonStrokeColor(() => 'rgba(80, 140, 240, 0.55)')
      .polygonAltitude(0.001)
  }

  applyTerminator()
  terminatorTimer = setInterval(applyTerminator, 60_000)

  // ── Auroral rings ────────────────────────────────────────────────────────
  globeInstance
    .ringsData(buildAuroralRings(spaceWeather.kpIndex))
    .ringColor('color')
    .ringMaxRadius('maxR')
    .ringPropagationSpeed('propagationSpeed')
    .ringRepeatPeriod('repeatPeriod')

  // ── Rotate camera to user location ───────────────────────────────────────
  setTimeout(() => {
    if (globeInstance) {
      globeInstance.pointOfView({ lat: geo.lat, lng: geo.lng, altitude: 2.0 }, 1000)
    }
  }, 400)

  // ── Responsive resize ─────────────────────────────────────────────────────
  resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const { width: w, height: h } = entry.contentRect
      if (globeInstance && w > 0 && h > 0) {
        globeInstance.width(w).height(h)
      }
    }
  })
  resizeObserver.observe(globeContainer.value)
})

// ─── Watch kpIndex ───────────────────────────────────────────────────────────

watch(
  () => spaceWeather.kpIndex,
  (kp) => {
    if (globeInstance) {
      globeInstance.ringsData(buildAuroralRings(kp))
    }
  }
)

// ─── Watch user location (in case geo updates after mount) ───────────────────

watch(
  () => [geo.lat, geo.lng] as [number, number],
  ([lat, lng]) => {
    if (globeInstance) {
      const userPin = [{ lat, lng, size: 0.5, color: '#FFBD76' }]
      globeInstance.pointsData(userPin)
      globeInstance.pointOfView({ lat, lng, altitude: 2.0 }, 1000)
    }
  }
)

// ─── Cleanup ─────────────────────────────────────────────────────────────────

onBeforeUnmount(() => {
  if (terminatorTimer) clearInterval(terminatorTimer)
  if (resizeObserver) resizeObserver.disconnect()
  if (globeInstance) {
    globeInstance._destructor?.()
    globeInstance = null
  }
})
</script>

<style scoped>
.helios-globe-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
  /* Ensure the canvas itself has no margin/padding weirdness */
  display: block;
}

.helios-globe-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

/* ── Bottom fade — blends globe into page background ── */
.helios-globe-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20%;
  background: linear-gradient(to bottom, transparent 0%, var(--bg-primary, #0a0e1a) 100%);
  pointer-events: none;
  z-index: 1;
}

/* ── Right HUD — solar data overlay ── */
.globe-hud-right {
  position: absolute;
  top: 1.5rem;
  right: 1rem;
  z-index: 3;
  display: flex;
  flex-direction: column;
  gap: 0;
  pointer-events: none;
  user-select: none;
  font-family: var(--font-mono);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
}

.globe-hud-left {
  position: absolute;
  bottom: 5rem;
  left: 1rem;
  z-index: 3;
  display: flex;
  flex-direction: column;
  gap: 0;
  pointer-events: none;
  user-select: none;
  font-family: var(--font-mono);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
}

.hud-section {
  display: flex;
  flex-direction: column;
  padding: 0.3rem 0;
}

.hud-label {
  font-size: 0.4rem;
  letter-spacing: 0.2em;
  color: rgba(255, 246, 233, 0.35);
  font-weight: 500;
}

.hud-value {
  font-size: 0.85rem;
  font-weight: 700;
  color: rgba(255, 246, 233, 0.75);
  letter-spacing: -0.02em;
}

.hud-value--sm {
  font-size: 0.6rem;
  font-weight: 600;
}

.hud-divider {
  height: 1px;
  width: 40px;
  background: rgba(255, 246, 233, 0.1);
}

/* ── Bottom center badge ── */
.globe-badge-center {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  pointer-events: none;
  user-select: none;
  font-family: var(--font-mono);
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
  white-space: nowrap;
}

.badge-dot {
  font-size: 0.5rem;
  color: #00D4AA;
}

.badge-label {
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  color: #00D4AA;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border: 1.5px solid rgba(0, 212, 170, 0.4);
  border-radius: 4px;
  background: rgba(0, 212, 170, 0.1);
}

.badge-text {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 246, 233, 0.7);
  letter-spacing: 0.03em;
}

.badge-sats {
  font-size: 0.65rem;
  color: rgba(255, 246, 233, 0.4);
  letter-spacing: 0.08em;
  font-weight: 500;
}

@media (max-width: 768px) {
  .globe-hud-right {
    display: none;
  }
  .globe-hud-left {
    display: none;
  }
}
</style>
