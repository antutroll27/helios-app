export interface BackendAuthUser {
  id: string
  email: string | null
}

export interface BackendAuthPayload {
  user: BackendAuthUser
  csrfToken?: string | null
  requiresConfirmation?: boolean
}

function getBackendUrl(): string {
  return import.meta.env.VITE_BACKEND_URL ?? ''
}

function getSafeRedirectPath(redirect: string): string {
  if (!redirect.startsWith('/') || redirect.startsWith('//')) {
    return '/'
  }
  return redirect
}

export function getOAuthStartUrl(provider: 'google', redirect: string): string {
  const params = new URLSearchParams({
    provider,
    redirect: getSafeRedirectPath(redirect),
    return_origin: globalThis.location?.origin ?? '',
  })
  return `${getBackendUrl()}/api/auth/oauth/start?${params.toString()}`
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>
  }

  if (response.status === 401) {
    throw new Error('Unauthorized')
  }

  const payload = await response.json().catch(async () => ({ detail: await response.text().catch(() => 'Request failed') }))
  const detail =
    payload && typeof payload.detail === 'string'
      ? payload.detail
      : 'Request failed'
  throw new Error(detail)
}

export async function login(email: string, password: string): Promise<BackendAuthPayload> {
  const response = await fetch(`${getBackendUrl()}/api/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return parseResponse<BackendAuthPayload>(response)
}

export async function signup(email: string, password: string): Promise<BackendAuthPayload> {
  const response = await fetch(`${getBackendUrl()}/api/auth/signup`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return parseResponse<BackendAuthPayload>(response)
}

export async function logout(): Promise<void> {
  const response = await fetch(`${getBackendUrl()}/api/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })
  await parseResponse<{ ok: true }>(response)
}

export async function me(): Promise<BackendAuthPayload | null> {
  const response = await fetch(`${getBackendUrl()}/api/auth/me`, {
    credentials: 'include',
  })
  if (response.status === 401) {
    return null
  }
  return parseResponse<BackendAuthPayload>(response)
}
