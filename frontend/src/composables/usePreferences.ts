import { ref, watch } from 'vue'

const STORAGE_KEY = 'ft-prefs'

interface Prefs {
  showImages: boolean
}

function load(): Prefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { showImages: true, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { showImages: true }
}

const prefs = ref<Prefs>(load())

watch(prefs, (p) => localStorage.setItem(STORAGE_KEY, JSON.stringify(p)), { deep: true })

export function usePreferences() {
  function set<K extends keyof Prefs>(key: K, value: Prefs[K]) {
    prefs.value = { ...prefs.value, [key]: value }
  }

  return { prefs, set }
}
