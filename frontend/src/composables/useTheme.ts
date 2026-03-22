import { ref, watch } from 'vue'

type Theme = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'ft-theme'

function systemPreference(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function resolvedTheme(t: Theme): 'light' | 'dark' {
  return t === 'system' ? systemPreference() : t
}

function getInitialTheme(): Theme {
  const saved = localStorage.getItem(STORAGE_KEY) as Theme | null
  if (saved === 'dark' || saved === 'light' || saved === 'system') return saved
  return 'system'
}

function applyTheme(t: Theme) {
  document.documentElement.setAttribute('data-theme', resolvedTheme(t))
}

const theme = ref<Theme>(getInitialTheme())
applyTheme(theme.value)

// Sync with OS preference changes when in system mode
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (theme.value === 'system') applyTheme('system')
})

watch(theme, (t) => {
  applyTheme(t)
  localStorage.setItem(STORAGE_KEY, t)
})

export function useTheme() {
  function setTheme(t: Theme) {
    theme.value = t
  }

  return { theme, setTheme }
}
