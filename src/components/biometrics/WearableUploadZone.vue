<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'
import { useOuraUpload } from '@/composables/useOuraUpload'
import { Upload, CheckCircle, AlertCircle, Loader } from 'lucide-vue-next'

const biometrics = useBiometricsStore()
const { handleFile, reset } = useOuraUpload()

const isDragOver = ref(false)
const lastFileName = ref('')

const status = computed(() => biometrics.uploadStatus)

function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}
function onDragLeave() { isDragOver.value = false }
function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) { lastFileName.value = file.name; handleFile(file) }
}
function onFileInput(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) { lastFileName.value = file.name; handleFile(file) }
}
function triggerInput() {
  document.getElementById('wearable-file-input')?.click()
}
</script>

<template>
  <div
    class="upload-zone"
    :class="{ 'upload-zone--drag': isDragOver, [`upload-zone--${status}`]: true }"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <input
      type="file"
      id="wearable-file-input"
      accept=".zip,.json"
      class="upload-zone__input"
      @change="onFileInput"
    />

    <!-- IDLE state -->
    <div v-if="status === 'idle'" class="upload-zone__content">
      <Upload :size="28" class="upload-zone__icon" />
      <p class="upload-zone__title text-xs6">Wearable Data</p>
      <p class="upload-zone__hint text-xs4">Drop Oura .zip / .json</p>
      <button class="upload-zone__btn text-xs4 tracking-label" @click="triggerInput">BROWSE FILES</button>
      <p class="upload-zone__platforms text-xs3">Oura · Fitbit · Apple Health coming soon</p>
    </div>

    <!-- PARSING state -->
    <div v-else-if="status === 'parsing'" class="upload-zone__content upload-zone__content--parsing">
      <Loader :size="24" class="upload-zone__spinner" />
      <p class="upload-zone__title text-xs6">Parsing {{ lastFileName || 'file' }}…</p>
      <p class="upload-zone__hint text-xs4">Reading sleep data</p>
    </div>

    <!-- SUCCESS state -->
    <div v-else-if="status === 'success'" class="upload-zone__content">
      <CheckCircle :size="28" class="upload-zone__icon upload-zone__icon--success" />
      <p class="upload-zone__title text-xs6">Data loaded</p>
      <p class="upload-zone__hint text-xs4">{{ lastFileName || 'Oura export' }}</p>
      <button class="upload-zone__btn upload-zone__btn--ghost text-xs4 tracking-label" @click="reset">UPLOAD ANOTHER</button>
    </div>

    <!-- ERROR state -->
    <div v-else-if="status === 'error'" class="upload-zone__content">
      <AlertCircle :size="28" class="upload-zone__icon upload-zone__icon--error" />
      <p class="upload-zone__title text-xs6">Upload failed</p>
      <p class="upload-zone__hint upload-zone__hint--error text-xs4">{{ biometrics.uploadError }}</p>
      <button class="upload-zone__btn text-xs4 tracking-label" @click="reset">TRY AGAIN</button>
    </div>

  </div>
</template>

<style scoped>
.upload-zone {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--border-card);
  border-radius: 1rem;
  padding: 1.25rem 1rem;
  transition: border-color 0.2s ease, background 0.2s ease;
  background: var(--bg-card);
  min-height: 180px;
  cursor: pointer;
}

.upload-zone--drag {
  border-color: #00D4AA;
  background: rgba(0, 212, 170, 0.04);
}

.upload-zone--success {
  border-color: rgba(0, 212, 170, 0.3);
}

.upload-zone--error {
  border-color: rgba(255, 68, 68, 0.3);
}

.upload-zone__input {
  display: none;
}

.upload-zone__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  text-align: center;
}

.upload-zone__content--parsing {
  gap: 0.5rem;
}

.upload-zone__icon {
  color: var(--text-muted);
  margin-bottom: 0.2rem;
}

.upload-zone__icon--success { color: #00D4AA; }
.upload-zone__icon--error { color: #FF4444; }

.upload-zone__spinner {
  color: #00D4AA;
  animation: spin 0.9s linear infinite;
  margin-bottom: 0.2rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.upload-zone__title {
  margin: 0;
  font-family: var(--font-display);
  color: var(--text-primary);
  font-weight: 600;
}

.upload-zone__hint {
  margin: 0;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.upload-zone__hint--error {
  color: rgba(255, 68, 68, 0.8);
}

.upload-zone__btn {
  margin-top: 0.375rem;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--border-card);
  border-radius: 2rem;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  font-family: var(--font-mono);
  letter-spacing: 0.15em;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.upload-zone__btn:hover {
  border-color: #00D4AA;
  background: rgba(0, 212, 170, 0.08);
  color: #00D4AA;
}

.upload-zone__btn--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--text-muted);
}

.upload-zone__btn--ghost:hover {
  border-color: var(--border-card);
  background: transparent;
  color: var(--text-primary);
}

.upload-zone__platforms {
  margin: 0;
  font-family: var(--font-mono);
  color: var(--text-muted);
  opacity: 0.6;
}
</style>
