import type { ScanResponse, StockItem, StockItemCreate, StockItemUpdate } from '@/types'

const BASE = import.meta.env.VITE_API_URL as string

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
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
