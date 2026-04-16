const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL as string | undefined)?.replace(/\/$/, '')

export async function fetchPublicJson(path: string) {
  if (!BACKEND_URL) {
    throw new Error('Public backend URL not configured')
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const response = await fetch(`${BACKEND_URL}/api/public${normalizedPath}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Public backend error ${response.status}`)
  }

  return response.json()
}
