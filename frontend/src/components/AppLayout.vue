<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const route  = useRoute()
const { user, logout } = useAuth()

const navItems = computed(() => [
  { path: '/',         label: 'Stock',      icon: '📦' },
  { path: '/recipes',  label: 'Recettes',   icon: '🍽️' },
  { path: '/settings', label: 'Paramètres', icon: '⚙️' },
  ...(user.value?.is_admin ? [{ path: '/users', label: 'Utilisateurs', icon: '👥' }] : []),
])

function isActive(path: string) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

function onLogout() {
  logout()
  router.push('/').catch(() => {})
  window.location.reload()
}
</script>

<template>
  <div class="app-shell">

    <!-- ── Header (mobile top bar) ── -->
    <header class="app-header">
      <div class="app-header__inner">
        <div class="app-header__logo">
          <span class="app-header__icon">🥫</span>
          <span class="app-header__wordmark">Stokk</span>
        </div>
        <div class="app-header__right">
          <span v-if="user" class="app-header__username">{{ user.username }}</span>
          <button class="btn btn--ghost logout-btn" @click="onLogout">Déconnexion</button>
        </div>
      </div>
    </header>

    <div class="app-body">

      <!-- ── Sidebar (desktop only) ── -->
      <nav class="sidebar" aria-label="Navigation principale">
        <div class="sidebar__logo">
          <span class="sidebar__icon">🥫</span>
          <span class="sidebar__wordmark">Stokk</span>
        </div>

        <ul class="sidebar__nav">
          <li v-for="item in navItems" :key="item.path">
            <RouterLink
              :to="item.path"
              class="sidebar__link"
              :class="{ 'sidebar__link--active': isActive(item.path) }"
            >
              <span class="sidebar__link-icon">{{ item.icon }}</span>
              <span class="sidebar__link-label">{{ item.label }}</span>
            </RouterLink>
          </li>
        </ul>

        <div class="sidebar__footer">
          <span v-if="user" class="sidebar__username">{{ user.username }}</span>
          <button class="btn btn--ghost sidebar__logout" @click="onLogout">Déconnexion</button>
        </div>
      </nav>

      <!-- ── Main content ── -->
      <main class="app-main">
        <RouterView />
      </main>

    </div>

    <!-- ── Bottom tabs (mobile only) ── -->
    <nav class="bottom-tabs" aria-label="Navigation">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="bottom-tab"
        :class="{ 'bottom-tab--active': isActive(item.path) }"
      >
        <span class="bottom-tab__icon">{{ item.icon }}</span>
        <span class="bottom-tab__label">{{ item.label }}</span>
      </RouterLink>
    </nav>

  </div>
</template>

<style scoped>
/* ── Mobile : flux normal, header sticky, bottom tabs fixe ── */
.app-shell { min-height: 100vh; }

.app-header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 20;
}
.app-header__inner {
  padding: .75rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.app-header__logo     { display: flex; align-items: center; gap: .45rem; }
.app-header__icon     { font-size: 1.25rem; }
.app-header__wordmark {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: -.03em;
  color: var(--color-accent);
}
.app-header__right    { display: flex; align-items: center; gap: .75rem; }
.app-header__username { font-size: .8rem; color: var(--color-muted); }
.logout-btn           { font-size: .8rem; padding: .3rem .65rem; }

/* Sidebar masquée sur mobile */
.sidebar { display: none; }

.app-body { display: block; }

.app-main {
  padding: 1.25rem 1rem 5.5rem; /* espace pour les bottom tabs fixes */
}

/* ── Bottom tabs (mobile) ── */
.bottom-tabs {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  display: flex;
  z-index: 20;
  padding-bottom: env(safe-area-inset-bottom, 0);
}
.bottom-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: .2rem;
  padding: .6rem .25rem;
  text-decoration: none;
  color: var(--color-muted);
  font-size: .65rem;
  font-family: var(--font-display);
  font-weight: 600;
  transition: color var(--transition);
}
.bottom-tab--active  { color: var(--color-accent); }
.bottom-tab__icon    { font-size: 1.2rem; line-height: 1; }
.bottom-tab__label   { text-transform: uppercase; letter-spacing: .04em; }

/* ── Desktop : sidebar fixe + main scrollable ── */
@media (min-width: 1024px) {
  .app-header  { display: none; }
  .bottom-tabs { display: none; }

  .app-shell {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  .app-body {
    display: flex;
    flex: 1;
    min-width: 0;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    width: 220px;
    height: 100vh;
    background: var(--color-surface);
    border-right: 1px solid var(--color-border);
    padding: 1.5rem 1rem;
    gap: 1.5rem;
    overflow-y: auto;
  }
  .sidebar__logo {
    display: flex;
    align-items: center;
    gap: .45rem;
    padding: 0 .5rem .5rem;
  }
  .sidebar__icon { font-size: 1.4rem; }
  .sidebar__wordmark {
    font-family: var(--font-display);
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -.03em;
    color: var(--color-accent);
  }
  .sidebar__nav {
    flex: 1;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: .25rem;
  }
  .sidebar__link {
    display: flex;
    align-items: center;
    gap: .65rem;
    padding: .6rem .75rem;
    border-radius: var(--radius);
    text-decoration: none;
    color: var(--color-muted);
    font-family: var(--font-display);
    font-size: .875rem;
    font-weight: 600;
    transition: background var(--transition), color var(--transition);
  }
  .sidebar__link:hover     { background: var(--color-surface-2); color: var(--color-text); }
  .sidebar__link--active   { background: #fff3ed; color: var(--color-accent); }
  .sidebar__link-icon      { font-size: 1.1rem; }
  .sidebar__footer {
    display: flex;
    flex-direction: column;
    gap: .5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border);
  }
  .sidebar__username { font-size: .8rem; color: var(--color-muted); padding: 0 .25rem; }
  .sidebar__logout   { width: 100%; font-size: .8rem; padding: .4rem .75rem; }

  .app-main {
    flex: 1;
    min-width: 0;
    height: 100vh;
    overflow-y: auto;
    padding: 1.5rem 2rem 2rem;
  }
}
</style>
