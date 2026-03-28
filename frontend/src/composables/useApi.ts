import type { ScanResponse, StockItem, StockItemCreate, StockItemUpdate, AppUser, UserCreate, UserUpdate, Location, LocationCreate, LocationUpdate, Product, Recipe, RecipeCreate, RecipeUpdate, CookResult } from '@/types'

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

  listUsers: () =>
    apiFetch<AppUser[]>('/users'),

  createUser: (payload: UserCreate) =>
    apiFetch<AppUser>('/users', { method: 'POST', body: JSON.stringify(payload) }),

  updateUser: (userId: string, payload: UserUpdate) =>
    apiFetch<AppUser>(`/users/${userId}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  deleteUser: (userId: string) =>
    apiFetch<void>(`/users/${userId}`, { method: 'DELETE' }),

  listLocations: () =>
    apiFetch<Location[]>('/locations'),

  createLocation: (payload: LocationCreate) =>
    apiFetch<Location>('/locations', { method: 'POST', body: JSON.stringify(payload) }),

  updateLocation: (locId: string, payload: LocationUpdate) =>
    apiFetch<Location>(`/locations/${locId}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  deleteLocation: (locId: string) =>
    apiFetch<void>(`/locations/${locId}`, { method: 'DELETE' }),

  searchProducts: (q: string) =>
    apiFetch<Product[]>(`/products?q=${encodeURIComponent(q)}`),

  listRecipes: () =>
    apiFetch<Recipe[]>('/recipes'),

  createRecipe: (payload: RecipeCreate) =>
    apiFetch<Recipe>('/recipes', { method: 'POST', body: JSON.stringify(payload) }),

  updateRecipe: (recipeId: string, payload: RecipeUpdate) =>
    apiFetch<Recipe>(`/recipes/${recipeId}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  deleteRecipe: (recipeId: string) =>
    apiFetch<void>(`/recipes/${recipeId}`, { method: 'DELETE' }),

  cookRecipe: (recipeId: string) =>
    apiFetch<CookResult>(`/recipes/${recipeId}/cook`, { method: 'POST' }),
}
