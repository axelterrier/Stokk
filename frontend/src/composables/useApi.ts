import type { ScanResponse, StockItem, StockItemCreate, StockItemUpdate } from '@/types'

const BASE = import.meta.env.VITE_API_URL as string

export function getToken(): string | null {
  return localStorage.getItem('token')
}

export function setToken(token: string) {
  localStorage.setItem('token', token)
}

export function clearToken() {
  localStorage.removeItem('token')
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  })
  if (res.status === 401) {
    clearToken()
    window.location.reload()
    throw new Error('Session expirée')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  login: async (username: string, password: string): Promise<void> => {
    const body = new URLSearchParams({ username, password })
    const res = await fetch(`${BASE}/auth/login`, { method: 'POST', body })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail ?? 'Identifiants incorrects')
    }
    const data = await res.json()
    setToken(data.access_token)
  },

  scan: (barcode: string) =>
    apiFetch<ScanResponse>(`/scan/${barcode}`),

  addStock: (payload: StockItemCreate) =>
    apiFetch<StockItem>('/stock', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listStock: () =>
    apiFetch<StockItem[]>('/stock'),

  updateStock: (itemId: string, payload: StockItemUpdate) =>
    apiFetch<StockItem>(`/stock/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteStock: (itemId: string) =>
    apiFetch<void>(`/stock/${itemId}`, { method: 'DELETE' }),
}
