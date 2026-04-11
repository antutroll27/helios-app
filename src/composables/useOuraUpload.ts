import { useBiometricsStore } from '@/stores/biometrics'
import type { SleepLog } from '@/stores/biometrics'

export function useOuraUpload() {
  const biometrics = useBiometricsStore()

  async function handleFile(file: File): Promise<void> {
    // Validate extension
    const ext = file.name.toLowerCase()
    if (!ext.endsWith('.zip') && !ext.endsWith('.json')) {
      biometrics.setUploadStatus('error', 'Unsupported file type. Upload a .zip or .json export.')
      return
    }

    biometrics.setUploadStatus('parsing')

    // Phase 1: simulate 1.2s parse delay, then inject mock data tagged as oura
    await new Promise(resolve => setTimeout(resolve, 1200))

    // Re-tag existing store logs as uploaded from Oura
    const retagged: SleepLog[] = biometrics.logs.map(l => ({ ...l, source: 'oura' as const }))
    biometrics.ingestParsedLogs(retagged)
    // ingestParsedLogs sets status to 'success' internally
  }

  function reset() {
    biometrics.setUploadStatus('idle')
  }

  return { handleFile, reset }
}
