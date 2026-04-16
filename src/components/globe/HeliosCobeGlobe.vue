<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface GlobeAnchor {
  label: string
  lat: number
  lng: number
  timezone: string
}

interface GlobeComparisonMarker {
  id: string
  label: string
  lat: number
  lng: number
  timezone: string
  destinationElevationDeg: number
}

interface Props {
  current: GlobeAnchor
  comparisons: GlobeComparisonMarker[]
  selectedDestinationId: string | null
}

const props = defineProps<Props>()

const canvasRef = ref<HTMLCanvasElement | null>(null)

const surfaceSize = ref({ width: 0, height: 0 })
const isDragging = ref(false)
const isSettling = ref(false)

const DEG_TO_RAD = Math.PI / 180
const DRAG_SENSITIVITY = 0.005
const RECENTER_EASE = 0.08
const THETA_LIMIT = 0.72
const LATITUDE_FOCUS_WEIGHT = 0.58
const IDLE_DRIFT = 0.00045

const currentMarkerColor: [number, number, number] = [0.42, 0.9, 0.82]
const markerColor: [number, number, number] = [0.66, 0.76, 0.92]
const selectedMarkerColor: [number, number, number] = [0.14, 0.97, 0.82]
const globeBaseColor: [number, number, number] = [0.16, 0.28, 0.42]
const globeGlowColor: [number, number, number] = [0.48, 0.84, 1]

let globe: ReturnType<CreateGlobe> | null = null
let resizeObserver: ResizeObserver | null = null
let dragPointerId: number | null = null
let dragStartX = 0
let dragStartY = 0
let dragStartPhi = 0
let dragStartTheta = 0
let activePhi = 0
let activeTheta = 0
let targetPhi = 0
let targetTheta = 0
let isDisposed = false
type CreateGlobe = typeof import('cobe').default
let createGlobeFn: CreateGlobe | null = null

const selectedComparison = computed(
  () => props.comparisons.find((marker) => marker.id === props.selectedDestinationId) ?? null,
)

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function lerp(current: number, target: number, factor: number) {
  return current + (target - current) * factor
}

function normalizeAngle(value: number) {
  const wrapped = ((value + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2)
  return wrapped - Math.PI
}

function formatCanvasSize() {
  const canvas = canvasRef.value
  if (!canvas) return

  const width = Math.max(1, Math.round(canvas.clientWidth))
  const height = Math.max(1, Math.round(canvas.clientHeight))
  surfaceSize.value = { width, height }
}

function buildMarkerList() {
  const selectedId = selectedComparison.value?.id ?? null

  const markers = [
    {
      location: [props.current.lat, props.current.lng] as [number, number],
      size: 0.055,
      color: currentMarkerColor,
    },
  ]

  for (const comparison of props.comparisons) {
    markers.push({
      location: [comparison.lat, comparison.lng] as [number, number],
      size: comparison.id === selectedId ? 0.08 : 0.042,
      color: comparison.id === selectedId ? selectedMarkerColor : markerColor,
    })
  }

  return {
    markers,
  }
}

function getFocusAngles(lat: number, lng: number) {
  const phi = normalizeAngle(-(lng * DEG_TO_RAD))
  const theta = clamp(-(lat * DEG_TO_RAD) * LATITUDE_FOCUS_WEIGHT, -THETA_LIMIT, THETA_LIMIT)
  return { phi, theta }
}

function syncSelectionFocus() {
  const selectedMarker = selectedComparison.value
  if (!selectedMarker) return

  const focus = getFocusAngles(selectedMarker.lat, selectedMarker.lng)
  targetPhi = focus.phi
  targetTheta = focus.theta
  isSettling.value = true
}

function handlePointerDown(event: PointerEvent) {
  const canvas = canvasRef.value
  if (!canvas) return

  isDragging.value = true
  isSettling.value = false
  dragPointerId = event.pointerId
  dragStartX = event.clientX
  dragStartY = event.clientY
  dragStartPhi = activePhi
  dragStartTheta = activeTheta
  canvas.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (!isDragging.value || dragPointerId !== event.pointerId) return

  const dx = event.clientX - dragStartX
  const dy = event.clientY - dragStartY

  activePhi = normalizeAngle(dragStartPhi + dx * DRAG_SENSITIVITY)
  activeTheta = clamp(dragStartTheta + dy * DRAG_SENSITIVITY, -THETA_LIMIT, THETA_LIMIT)
}

function handlePointerUp(event: PointerEvent) {
  const canvas = canvasRef.value
  if (!canvas || dragPointerId !== event.pointerId) return

  isDragging.value = false
  dragPointerId = null
  canvas.releasePointerCapture(event.pointerId)
}

function handlePointerCancel(event: PointerEvent) {
  const canvas = canvasRef.value
  if (canvas && dragPointerId === event.pointerId) {
    canvas.releasePointerCapture(event.pointerId)
  }

  isDragging.value = false
  dragPointerId = null
}

async function startGlobe() {
  const canvas = canvasRef.value
  if (!canvas) return

  formatCanvasSize()

  if (!createGlobeFn) {
    const module = await import('cobe')
    if (isDisposed) return
    createGlobeFn = module.default
  }

  if (isDisposed) return

  const initial = buildMarkerList()
  const selectedMarker = selectedComparison.value
  if (selectedMarker) {
    const focus = getFocusAngles(selectedMarker.lat, selectedMarker.lng)
    activePhi = targetPhi = focus.phi
    activeTheta = targetTheta = focus.theta
  } else {
    const neutral = getFocusAngles(props.current.lat, props.current.lng)
    activePhi = targetPhi = neutral.phi
    activeTheta = targetTheta = neutral.theta
  }

  globe = createGlobeFn(canvas, {
    width: surfaceSize.value.width || 800,
    height: surfaceSize.value.height || 800,
    devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
    phi: activePhi,
    theta: activeTheta,
    dark: 0.82,
    diffuse: 1.35,
    scale: 0.72,
    mapSamples: 16000,
    mapBrightness: 8,
    baseColor: globeBaseColor,
    markerColor,
    glowColor: globeGlowColor,
    offset: [0, 0],
    markers: initial.markers,
    onRender: (state) => {
      const { markers } = buildMarkerList()

      if (isDragging.value) {
        state.phi = activePhi
        state.theta = activeTheta
      } else if (isSettling.value) {
        activePhi = lerp(activePhi, targetPhi, RECENTER_EASE)
        activeTheta = lerp(activeTheta, targetTheta, RECENTER_EASE)
        state.phi = activePhi
        state.theta = activeTheta

        const settled =
          Math.abs(normalizeAngle(activePhi - targetPhi)) < 0.002 &&
          Math.abs(activeTheta - targetTheta) < 0.002
        if (settled) {
          isSettling.value = false
        }
      } else {
        activePhi = normalizeAngle(activePhi + IDLE_DRIFT)
        state.phi = activePhi
        state.theta = activeTheta
      }

      state.width = surfaceSize.value.width || canvas.width
      state.height = surfaceSize.value.height || canvas.height
      state.markers = markers
    },
  })

  canvas.addEventListener('pointerdown', handlePointerDown)
  canvas.addEventListener('pointermove', handlePointerMove)
  canvas.addEventListener('pointerup', handlePointerUp)
  canvas.addEventListener('pointercancel', handlePointerCancel)
}

onMounted(() => {
  void startGlobe()

  const canvas = canvasRef.value
  if (!canvas) return

  resizeObserver = new ResizeObserver(() => {
    formatCanvasSize()
  })
  resizeObserver.observe(canvas)
})

watch(
  () =>
    [
      selectedComparison.value?.lat ?? null,
      selectedComparison.value?.lng ?? null,
      props.current.lat,
      props.current.lng,
    ] as const,
  ([lat, lng, currentLat, currentLng], previous) => {
    const [previousLat, previousLng, previousCurrentLat, previousCurrentLng] = previous ?? [
      null,
      null,
      null,
      null,
    ]
    if (
      lat === previousLat &&
      lng === previousLng &&
      currentLat === previousCurrentLat &&
      currentLng === previousCurrentLng
    ) {
      return
    }

    if (!selectedComparison.value) {
      const neutral = getFocusAngles(currentLat, currentLng)
      targetPhi = neutral.phi
      targetTheta = neutral.theta
      isSettling.value = true
      return
    }

    syncSelectionFocus()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  isDisposed = true

  const canvas = canvasRef.value
  if (canvas) {
    canvas.removeEventListener('pointerdown', handlePointerDown)
    canvas.removeEventListener('pointermove', handlePointerMove)
    canvas.removeEventListener('pointerup', handlePointerUp)
    canvas.removeEventListener('pointercancel', handlePointerCancel)
  }

  if (resizeObserver && canvas) {
    resizeObserver.unobserve(canvas)
    resizeObserver.disconnect()
  }

  globe?.destroy()
  globe = null
})
</script>

<template>
  <div class="cobe-globe" role="img" aria-label="HELIOS COBE globe visualization">
    <canvas ref="canvasRef" class="cobe-globe__canvas" aria-hidden="true" />
  </div>
</template>

<style scoped>
.cobe-globe {
  position: relative;
  width: min(100%, 50rem);
  aspect-ratio: 1 / 1;
  min-height: clamp(22rem, 42vw, 32rem);
  display: grid;
  place-items: center;
  justify-self: center;
  overflow: visible;
}

.cobe-globe__canvas {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 50%;
  touch-action: none;
  transform: translateY(-8%);
  background:
    radial-gradient(circle at 35% 28%, rgba(255, 255, 255, 0.16), transparent 22%),
    radial-gradient(circle at 50% 44%, rgba(0, 212, 170, 0.12), rgba(0, 180, 216, 0.06) 40%, rgba(4, 10, 24, 0.94) 68%);
  box-shadow: 0 24px 48px rgba(2, 8, 20, 0.26);
  cursor: grab;
}

.cobe-globe__canvas:active {
  cursor: grabbing;
}

@media (max-width: 720px) {
  .cobe-globe {
    min-height: 18rem;
  }

  .cobe-globe__canvas {
    transform: translateY(-5%);
  }
}
</style>
