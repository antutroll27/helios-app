import { useAuthStore } from '@/stores/auth'
import { useBiometricsStore } from '@/stores/biometrics'
import type { SleepLog } from '@/stores/biometrics'

export function useOuraUpload() {
  const biometrics = useBiometricsStore()

  async function handleFile(file: File): Promise<void> {
    const ext = file.name.toLowerCase()
    if (!ext.endsWith('.zip') && !ext.endsWith('.json')) {
      biometrics.setUploadStatus('error', 'Unsupported file type. Upload a .zip or .json export.')
      return
    }

    biometrics.setUploadStatus('parsing')

    const auth = useAuthStore()
    const backendUrl = import.meta.env.VITE_BACKEND_URL ?? ''

    // Phase 2: real backend upload when authenticated
    if (auth.isAuthenticated && auth.csrfToken) {
      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${backendUrl}/api/wearable/upload`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'X-HELIOS-CSRF': auth.csrfToken },
          body: formData,
        })

        if (response.ok) {
          const data = await response.json()
          if (Array.isArray(data.logs)) {
            const logs: SleepLog[] = data.logs.map((l: Record<string, unknown>) => ({
              date: l.date as string,
              sleep_onset: (l.sleep_onset as string) ?? '',
              wake_time: (l.wake_time as string) ?? '',
              total_sleep_min: (l.total_sleep_min as number) ?? 0,
              hrv_avg: l.hrv_avg as number | undefined,
              sleep_score: l.sleep_score as number | undefined,
              source: 'oura' as const,
            }))
            biometrics.ingestParsedLogs(logs)
          } else {
            biometrics.setUploadStatus('success')
          }
          return
        }

        const errorText = await response.text().catch(() => 'Upload failed')
        biometrics.setUploadStatus('error', errorText)
        return
      } catch {
        biometrics.setUploadStatus('error', 'Network error — please try again.')
        return
      }
    }

    // Phase 1 fallback (unauthenticated): simulate parse, retag existing logs as oura
    await new Promise(resolve => setTimeout(resolve, 1200))
    const retagged: SleepLog[] = biometrics.logs.map(l => ({ ...l, source: 'oura' as const }))
    biometrics.ingestParsedLogs(retagged)
  }

  function reset() {
    biometrics.setUploadStatus('idle')
  }

  return { handleFile, reset }
}
