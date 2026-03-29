<script setup lang="ts">
import SpaceWeatherGauge from './SpaceWeatherGauge.vue'
import ProtocolCard from './ProtocolCard.vue'
import { Heart, Zap, Shield, Activity } from 'lucide-vue-next'

interface VisualCard {
  type: string
  title: string
  data: Record<string, unknown>
}

const props = defineProps<{
  cards: VisualCard[]
}>()

// Icon map for health metrics
const healthIconMap: Record<string, object> = {
  heart: Heart,
  energy: Zap,
  immunity: Shield,
  activity: Activity,
  default: Activity
}

function getHealthIcon(metricType: string) {
  return healthIconMap[metricType] || healthIconMap.default
}

function getSeverityColor(severity: string | number) {
  if (severity === 'low' || (typeof severity === 'number' && severity < 3)) return '#00D4AA'
  if (severity === 'medium' || (typeof severity === 'number' && severity < 7)) return '#FFBD76'
  return '#FF4444'
}

function safeDateParse(time: any): Date {
  try {
    const d = new Date(time)
    if (!isNaN(d.getTime())) return d
  } catch {}
  // If it's a time string like "05:48", create a date for today at that time
  if (typeof time === 'string' && /^\d{1,2}:\d{2}/.test(time)) {
    const [h, m] = time.split(':').map(Number)
    const d = new Date()
    d.setHours(h, m, 0, 0)
    return d
  }
  return new Date() // fallback to now
}

function safeProtocolStatus(time: any): 'upcoming' | 'active' | 'passed' {
  try {
    const d = safeDateParse(time)
    const diff = d.getTime() - Date.now()
    if (diff < 0) return 'passed'
    if (diff / 60_000 <= 60) return 'active'
    return 'upcoming'
  } catch {
    return 'upcoming'
  }
}

</script>

<template>
  <div class="chat-cards-stack">
    <div
      v-for="(card, index) in cards"
      :key="index"
      class="chat-card-wrapper"
      :style="{ animationDelay: `${index * 0.1}s` }"
    >
      <!-- PROTOCOL -->
      <template v-if="card.type === 'protocol'">
        <div class="chat-section-card">
          <div class="chat-section-header">
            <span class="chat-section-label">{{ card.title || 'PROTOCOL' }}</span>
          </div>
          <div class="protocol-mini-grid">
            <ProtocolCard
              v-for="(item, i) in (card.data.items as Array<{ title: string; time: string; icon: string; citation: string; subtitle: string }>)"
              :key="i"
              :title="item.title"
              :time="safeDateParse(item.time)"
              :icon="item.icon || 'Sun'"
              :citation="item.citation || ''"
              :subtitle="item.subtitle || ''"
              :status="safeProtocolStatus(item.time)"
            />
          </div>
        </div>
      </template>

      <!-- HEALTH IMPACT -->
      <template v-else-if="card.type === 'health_impact'">
        <div class="bento-card health-impact-card" style="padding: 1.25rem;">
          <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
            <div
              class="health-icon-wrap"
              :style="{ background: getSeverityColor(card.data.severity as string) + '15' }"
            >
              <component
                :is="getHealthIcon(card.data.metricType as string || 'default')"
                :size="18"
                :color="getSeverityColor(card.data.severity as string)"
                :stroke-width="1.5"
              />
            </div>
            <div style="flex: 1; min-width: 0;">
              <span style="
                font-family: var(--font-display);
                font-size: 0.6rem;
                font-weight: 500;
                letter-spacing: 0.15em;
                text-transform: uppercase;
                color: var(--text-muted);
              ">{{ card.data.metric || card.title }}</span>
              <div style="display: flex; align-items: baseline; gap: 0.375rem; margin: 0.375rem 0;">
                <span style="
                  font-family: var(--font-mono);
                  font-size: 1.75rem;
                  font-weight: 700;
                  color: var(--text-primary);
                  line-height: 1;
                ">{{ card.data.value }}</span>
                <span style="
                  font-family: var(--font-mono);
                  font-size: 0.75rem;
                  color: var(--text-muted);
                ">{{ card.data.unit }}</span>
              </div>
              <!-- Severity bar -->
              <div style="
                width: 100%;
                height: 3px;
                border-radius: 2px;
                background: var(--border-subtle);
                margin-bottom: 0.75rem;
                overflow: hidden;
              ">
                <div :style="{
                  width: ((card.data.severityPercent as number) || 50) + '%',
                  height: '100%',
                  borderRadius: '2px',
                  background: getSeverityColor(card.data.severity as string),
                  transition: 'width 0.8s ease-out'
                }" />
              </div>
              <p style="
                font-family: var(--font-body);
                font-size: 0.72rem;
                color: var(--text-secondary);
                line-height: 1.5;
              ">{{ card.data.explanation }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- RECOMMENDATION -->
      <template v-else-if="card.type === 'recommendation'">
        <div
          class="bento-card recommendation-card"
          style="padding: 1rem 1.125rem; border-left: 3px solid #003F47;"
        >
          <p style="
            font-family: var(--font-body);
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.5;
            margin-bottom: 0.375rem;
          ">{{ card.data.action }}</p>
          <p v-if="card.data.timing" style="
            font-family: var(--font-mono);
            font-size: 0.7rem;
            color: #005A65;
            margin-bottom: 0.375rem;
          ">{{ card.data.timing }}</p>
          <p v-if="card.data.reason" style="
            font-family: var(--font-body);
            font-size: 0.72rem;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 0.25rem;
          ">{{ card.data.reason }}</p>
          <p v-if="card.data.citation" style="
            font-family: var(--font-body);
            font-size: 0.6rem;
            color: var(--text-muted);
            font-style: italic;
            opacity: 0.7;
          ">{{ card.data.citation }}</p>
        </div>
      </template>

      <!-- SPACE WEATHER -->
      <template v-else-if="card.type === 'space_weather'">
        <div class="chat-section-card">
          <SpaceWeatherGauge />
          <p v-if="card.data.commentary" style="
            font-family: var(--font-body);
            font-size: 0.75rem;
            color: var(--text-secondary);
            line-height: 1.6;
            padding: 0.75rem 1.25rem 0.5rem;
          ">{{ card.data.commentary }}</p>
        </div>
      </template>

      <!-- JETLAG TIMELINE -->
      <template v-else-if="card.type === 'jetlag_timeline'">
        <div class="bento-card jetlag-timeline-card" style="padding: 1.25rem;">
          <span style="
            font-family: var(--font-display);
            font-size: 0.6rem;
            font-weight: 600;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--text-muted);
            display: block;
            margin-bottom: 1rem;
          ">{{ card.title || 'JET LAG RECOVERY TIMELINE' }}</span>

          <div class="timeline-container">
            <div
              v-for="(day, i) in (card.data.days as Array<{
                day: number
                date: string
                lightWindow: string
                caffeineWindow: string
                sleepTime: string
                wakeTime: string
                direction: string
                shiftProgress: number
              }>)"
              :key="i"
              class="timeline-day"
            >
              <!-- Connecting line -->
              <div class="timeline-line" v-if="i < ((card.data.days as unknown[])?.length ?? 0) - 1" />

              <!-- Day node -->
              <div class="timeline-node">
                <div class="timeline-circle">
                  <span style="
                    font-family: var(--font-mono);
                    font-size: 0.7rem;
                    font-weight: 600;
                    color: var(--text-primary);
                  ">{{ day.day }}</span>
                </div>

                <div class="timeline-content">
                  <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <span style="
                      font-family: var(--font-body);
                      font-size: 0.72rem;
                      font-weight: 600;
                      color: var(--text-primary);
                    ">Day {{ day.day }}</span>
                    <span style="
                      font-family: var(--font-mono);
                      font-size: 0.6rem;
                      color: var(--text-muted);
                    ">{{ day.date }}</span>
                    <!-- Direction arrow -->
                    <span v-if="day.direction" style="
                      font-family: var(--font-mono);
                      font-size: 0.75rem;
                      color: #FFBD76;
                    ">{{ day.direction === 'advance' ? '\u2192' : '\u2190' }}</span>
                  </div>

                  <!-- Time segments -->
                  <div class="timeline-segments">
                    <div class="segment" v-if="day.lightWindow">
                      <div class="segment-bar" style="background: #FFBD76;" />
                      <span class="segment-label">Light</span>
                      <span class="segment-value">{{ day.lightWindow }}</span>
                    </div>
                    <div class="segment" v-if="day.caffeineWindow">
                      <div class="segment-bar" style="background: #005A65;" />
                      <span class="segment-label">Caffeine</span>
                      <span class="segment-value">{{ day.caffeineWindow }}</span>
                    </div>
                    <div class="segment" v-if="day.sleepTime">
                      <div class="segment-bar" style="background: #003F47;" />
                      <span class="segment-label">Sleep</span>
                      <span class="segment-value">{{ day.sleepTime }}{{ day.wakeTime ? ' \u2013 ' + day.wakeTime : '' }}</span>
                    </div>
                  </div>

                  <!-- Phase shift progress -->
                  <div v-if="day.shiftProgress !== undefined" style="margin-top: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                      <span class="segment-label">Phase Shift</span>
                      <span style="
                        font-family: var(--font-mono);
                        font-size: 0.6rem;
                        color: var(--text-secondary);
                      ">{{ Math.round(day.shiftProgress * 100) }}%</span>
                    </div>
                    <div style="
                      width: 100%;
                      height: 3px;
                      border-radius: 2px;
                      background: var(--border-subtle);
                      overflow: hidden;
                    ">
                      <div :style="{
                        width: (day.shiftProgress * 100) + '%',
                        height: '100%',
                        borderRadius: '2px',
                        background: 'linear-gradient(90deg, #003F47, #00D4AA)',
                        transition: 'width 0.8s ease-out'
                      }" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.chat-cards-stack {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-card-wrapper {
  opacity: 0;
  animation: chatCardFadeIn 0.5s ease-out forwards;
}

@keyframes chatCardFadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-section-card {
  border-radius: 1rem;
  overflow: hidden;
}

.chat-section-header {
  padding: 0.75rem 1.25rem 0;
}

.chat-section-label {
  font-family: var(--font-display);
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.protocol-mini-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  padding: 0.75rem;
}

@media (max-width: 480px) {
  .protocol-mini-grid {
    grid-template-columns: 1fr;
  }
}

.health-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 0.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.health-impact-card {
  transition: all 0.25s ease;
}
.health-impact-card:hover {
  transform: translateY(-1px);
}

.recommendation-card {
  transition: all 0.25s ease;
}
.recommendation-card:hover {
  border-left-color: #005A65 !important;
  transform: translateY(-1px);
}

/* Jetlag timeline */
.timeline-container {
  position: relative;
  padding-left: 0;
}

.timeline-day {
  position: relative;
  padding-bottom: 1rem;
}
.timeline-day:last-child {
  padding-bottom: 0;
}

.timeline-line {
  position: absolute;
  left: 16px;
  top: 34px;
  bottom: 0;
  width: 1px;
  background: var(--border-subtle);
}

.timeline-node {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.timeline-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-surface, rgba(255, 246, 233, 0.05));
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.timeline-content {
  flex: 1;
  min-width: 0;
  padding-top: 0.15rem;
}

.timeline-segments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.segment {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.segment-bar {
  width: 8px;
  height: 3px;
  border-radius: 1.5px;
  flex-shrink: 0;
}

.segment-label {
  font-family: var(--font-display);
  font-size: 0.55rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.segment-value {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-secondary);
}
</style>
