import { ref } from 'vue'
import { getToken, clearToken } from './useApi'

export interface AuthUser {
  id: string
  username: string
  is_admin: boolean
}

const user = ref<AuthUser | null>(null)

export function useAuth() {
  async function fetchMe(): Promise<void> {
    const token = getToken()
    if (!token) return
    const res = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) user.value = await res.json()
    else if (res.status === 401) { clearToken(); user.value = null }
  }

  function logout() {
    clearToken()
    user.value = null
  }

  return { user, fetchMe, logout }
}
