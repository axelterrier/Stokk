<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Location } from '@/types'
import { api } from '@/composables/useApi'
import { useTheme } from '@/composables/useTheme'
import { usePreferences } from '@/composables/usePreferences'

const { theme, setTheme } = useTheme()
const { prefs, set: setPref } = usePreferences()

const locations  = ref<Location[]>([])
const loading    = ref(false)
const error      = ref<string | null>(null)

// Build flat ordered list (depth-first) with depth info
interface FlatLoc { loc: Location; depth: number }

function buildFlat(parentId: string | null, depth: number): FlatLoc[] {
  return locations.value
    .filter(l => (l.parent_id ?? null) === parentId)
    .sort((a, b) => a.name.localeCompare(b.name))
    .flatMap(l => [{ loc: l, depth }, ...buildFlat(l.id, depth + 1)])
}

const flatList = computed<FlatLoc[]>(() => buildFlat(null, 0))

// ── Ajout ──
const addingParentId = ref<string | 'root' | null>(null)
const newName    = ref('')
const newColor   = ref('blue')
const creating   = ref(false)
const createErr  = ref<string | null>(null)

function openAdd(parentId: string | null) {
  addingParentId.value = parentId ?? 'root'
  newName.value  = ''
  newColor.value = 'blue'
  createErr.value = null
  editingId.value = null
}

async function doCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  createErr.value = null
  try {
    const parentId = addingParentId.value === 'root' ? undefined : addingParentId.value as string
    const loc = await api.createLocation({ name: newName.value.trim(), parent_id: parentId ?? undefined, color: newColor.value })
    locations.value.push(loc)
    addingParentId.value = null
  } catch (e: unknown) {
    createErr.value = e instanceof Error ? e.message : 'Erreur'
  } finally {
    creating.value = false
  }
}

// ── Édition ──
const editingId  = ref<string | null>(null)
const editName   = ref('')
const editColor  = ref('blue')
const saving     = ref(false)

function startEdit(loc: Location) {
  editingId.value = loc.id
  editName.value  = loc.name
  editColor.value = loc.color ?? 'blue'
  addingParentId.value = null
}

async function doSave() {
  if (!editingId.value) return
  saving.value = true
  try {
    const updated = await api.updateLocation(editingId.value, { name: editName.value.trim(), color: editColor.value })
    locations.value = locations.value.map(l => l.id === updated.id ? updated : l)
    editingId.value = null
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur')
  } finally {
    saving.value = false
  }
}

// ── Suppression ──
const confirmDeleteId = ref<string | null>(null)
const deleting        = ref(false)

async function doDelete(id: string) {
  deleting.value = true
  try {
    await api.deleteLocation(id)
    locations.value = await api.listLocations()
    confirmDeleteId.value = null
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur suppression')
  } finally {
    deleting.value = false
  }
}

// ── Couleurs ──
const COLORS = [
  { id: 'blue', label: 'Bleu', hex: '#2563eb' },
  { id: 'cyan', label: 'Cyan', hex: '#0891b2' },
  { id: 'green', label: 'Vert', hex: '#15803d' },
  { id: 'yellow', label: 'Jaune', hex: '#a16207' },
  { id: 'orange', label: 'Orange', hex: '#c2410c' },
  { id: 'red', label: 'Rouge', hex: '#dc2626' },
  { id: 'purple', label: 'Violet', hex: '#7c3aed' },
  { id: 'pink', label: 'Rose', hex: '#be185d' },
]

const COLOR_HEX: Record<string, string> = Object.fromEntries(COLORS.map(c => [c.id, c.hex]))

async function load() {
  loading.value = true
  try { locations.value = await api.listLocations() }
  catch (e: unknown) { error.value = e instanceof Error ? e.message : 'Erreur' }
  finally { loading.value = false }
}

onMounted(load)
</script>

<template>
  <div class="settings-view">
    <div class="view-header">
      <div>
        <h1 class="view-title">Paramètres</h1>
        <p class="view-subtitle">Gérez les emplacements de votre stock.</p>
      </div>
    </div>

    <!-- Apparence -->
    <section class="settings-section card">
      <div class="section-head">
        <h2 class="section-title">Apparence</h2>
      </div>
      <div class="theme-picker">
        <button
          class="theme-btn"
          :class="{ 'theme-btn--active': theme === 'light' }"
          @click="setTheme('light')"
        >
          <span class="theme-btn__icon">☀️</span>
          <span class="theme-btn__label">Clair</span>
        </button>
        <button
          class="theme-btn"
          :class="{ 'theme-btn--active': theme === 'dark' }"
          @click="setTheme('dark')"
        >
          <span class="theme-btn__icon">🌙</span>
          <span class="theme-btn__label">Sombre</span>
        </button>
        <button
          class="theme-btn"
          :class="{ 'theme-btn--active': theme === 'system' }"
          @click="setTheme('system')"
        >
          <span class="theme-btn__icon">💻</span>
          <span class="theme-btn__label">Système</span>
        </button>
      </div>
    </section>

    <!-- Affichage -->
    <section class="settings-section card">
      <div class="section-head">
        <h2 class="section-title">Affichage</h2>
      </div>
      <label class="pref-row">
        <div class="pref-row__text">
          <span class="pref-row__label">Photos des produits</span>
          <span class="pref-row__hint">Affiche les photos OpenFoodFacts sur les cartes de stock</span>
        </div>
        <button
          class="toggle-switch"
          :class="{ 'toggle-switch--on': prefs.showImages }"
          role="switch"
          :aria-checked="prefs.showImages"
          @click="setPref('showImages', !prefs.showImages)"
        >
          <span class="toggle-switch__thumb" />
        </button>
      </label>
    </section>

    <!-- Emplacements -->
    <section class="settings-section card">
      <div class="section-head">
        <h2 class="section-title">Emplacements</h2>
        <button class="btn btn--primary btn--sm" @click="openAdd(null)">+ Ajouter</button>
      </div>
      <p class="section-hint">Organisez en arborescence : Cuisine › Frigo › Bac à légumes.</p>

      <!-- Formulaire racine -->
      <div v-if="addingParentId === 'root'" class="loc-form animate-slide-up">
        <input v-model="newName" class="input" placeholder="Nom de l'emplacement" @keyup.enter="doCreate" />
        <div class="color-row">
          <button v-for="c in COLORS" :key="c.id"
            class="cdot" :class="{ 'cdot--on': newColor === c.id }"
            :style="{ background: c.hex }" :title="c.label" @click="newColor = c.id" />
        </div>
        <div v-if="createErr" class="ferr">{{ createErr }}</div>
        <div class="form-btns">
          <button class="btn btn--ghost btn--sm" @click="addingParentId = null">Annuler</button>
          <button class="btn btn--primary btn--sm" :disabled="creating || !newName.trim()" @click="doCreate">
            {{ creating ? '…' : 'Créer' }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="state-msg">Chargement…</div>
      <div v-else-if="error" class="state-msg state-msg--error">{{ error }}</div>
      <div v-else-if="!flatList.length && addingParentId !== 'root'" class="state-msg">
        Aucun emplacement — cliquez sur « + Ajouter » pour commencer.
      </div>

      <ul v-else class="loc-list">
        <template v-for="{ loc, depth } in flatList" :key="loc.id">
          <li class="loc-row" :style="{ paddingLeft: `${depth * 1.5 + 0.75}rem` }">

            <!-- Connecteur visuel -->
            <span v-if="depth > 0" class="loc-connector">└</span>

            <!-- Indicateur couleur -->
            <span class="loc-dot" :style="{ background: COLOR_HEX[loc.color ?? ''] ?? '#a8a29e' }"></span>

            <!-- Mode lecture -->
            <template v-if="editingId !== loc.id">
              <span class="loc-name">{{ loc.name }}</span>
              <div class="loc-actions">
                <button class="icon-btn" title="Ajouter un sous-emplacement" @click="openAdd(loc.id)">+</button>
                <button class="icon-btn" title="Renommer" @click="startEdit(loc)">✎</button>
                <button class="icon-btn icon-btn--danger" title="Supprimer" @click="confirmDeleteId = loc.id">✕</button>
              </div>
            </template>

            <!-- Mode édition inline -->
            <template v-else>
              <input v-model="editName" class="input input--inline" @keyup.enter="doSave" @keyup.escape="editingId = null" />
              <div class="color-row color-row--sm">
                <button v-for="c in COLORS" :key="c.id"
                  class="cdot cdot--sm" :class="{ 'cdot--on': editColor === c.id }"
                  :style="{ background: c.hex }" :title="c.label" @click="editColor = c.id" />
              </div>
              <div class="form-btns">
                <button class="btn btn--ghost btn--sm" @click="editingId = null">Annuler</button>
                <button class="btn btn--primary btn--sm" :disabled="saving" @click="doSave">
                  {{ saving ? '…' : 'OK' }}
                </button>
              </div>
            </template>
          </li>

          <!-- Sous-formulaire ajout enfant -->
          <li v-if="addingParentId === loc.id" class="loc-row loc-row--form animate-slide-up"
            :style="{ paddingLeft: `${(depth + 1) * 1.5 + 0.75}rem` }">
            <span class="loc-connector">└</span>
            <div class="loc-form loc-form--inline">
              <input v-model="newName" class="input" placeholder="Nom du sous-emplacement" @keyup.enter="doCreate" />
              <div class="color-row color-row--sm">
                <button v-for="c in COLORS" :key="c.id"
                  class="cdot cdot--sm" :class="{ 'cdot--on': newColor === c.id }"
                  :style="{ background: c.hex }" @click="newColor = c.id" />
              </div>
              <div v-if="createErr" class="ferr">{{ createErr }}</div>
              <div class="form-btns">
                <button class="btn btn--ghost btn--sm" @click="addingParentId = null">Annuler</button>
                <button class="btn btn--primary btn--sm" :disabled="creating || !newName.trim()" @click="doCreate">
                  {{ creating ? '…' : 'Créer' }}
                </button>
              </div>
            </div>
          </li>

          <!-- Confirmation suppression -->
          <li v-if="confirmDeleteId === loc.id" class="loc-row loc-row--confirm animate-slide-up"
            :style="{ paddingLeft: `${depth * 1.5 + 0.75}rem` }">
            <span class="confirm-text">Supprimer <strong>{{ loc.name }}</strong> ? Les sous-emplacements deviendront indépendants.</span>
            <div class="form-btns">
              <button class="btn btn--ghost btn--sm" @click="confirmDeleteId = null">Annuler</button>
              <button class="btn btn--danger-solid btn--sm" :disabled="deleting" @click="doDelete(loc.id)">
                {{ deleting ? '…' : 'Supprimer' }}
              </button>
            </div>
          </li>
        </template>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.settings-view { max-width: 600px; display: flex; flex-direction: column; gap: 1.25rem; }

.view-title    { font-family: var(--font-display); font-size: 1.4rem; font-weight: 800; letter-spacing: -.02em; }
.view-subtitle { font-size: .85rem; color: var(--color-muted); margin-top: .2rem; }

.settings-section { display: flex; flex-direction: column; gap: 1rem; }
.section-head  { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-family: var(--font-display); font-size: 1rem; font-weight: 700; }
.section-hint  { font-size: .8rem; color: var(--color-muted); }

/* Formulaire ajout */
.loc-form { display: flex; flex-direction: column; gap: .6rem; padding: .75rem; background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius); }
.loc-form--inline { flex: 1; }
.form-btns { display: flex; gap: .4rem; justify-content: flex-end; }
.ferr { font-size: .78rem; color: var(--color-danger); }

/* Color picker */
.color-row { display: flex; gap: .35rem; flex-wrap: wrap; }
.color-row--sm { gap: .25rem; }
.cdot {
  width: 20px; height: 20px; border-radius: 50%; border: 2px solid transparent;
  cursor: pointer; transition: transform .1s, box-shadow .1s;
  flex-shrink: 0;
}
.cdot--sm { width: 16px; height: 16px; }
.cdot--on { border-color: var(--color-text); box-shadow: 0 0 0 2px #fff, 0 0 0 4px currentColor; transform: scale(1.1); }
.cdot:hover { transform: scale(1.1); }

/* Liste des emplacements */
.loc-list { list-style: none; display: flex; flex-direction: column; gap: 0; }
.loc-row {
  display: flex;
  align-items: center;
  gap: .5rem;
  padding-top: .45rem;
  padding-bottom: .45rem;
  padding-right: .75rem;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}
.loc-row:last-child { border-bottom: none; }
.loc-row--form    { background: var(--color-surface-2); }
.loc-row--confirm { background: rgba(220, 38, 38, .06); gap: .5rem; }

.loc-connector { color: var(--color-border); font-size: .8rem; flex-shrink: 0; user-select: none; }
.loc-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.loc-name { flex: 1; font-size: .9rem; font-weight: 500; min-width: 0; }

.loc-actions { display: flex; gap: .25rem; margin-left: auto; }
.icon-btn {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  border-radius: 6px; border: 1px solid transparent;
  background: transparent; color: var(--color-muted);
  font-size: .85rem; cursor: pointer;
  transition: background var(--transition), color var(--transition);
}
.icon-btn:hover { background: var(--color-surface-2); color: var(--color-text); border-color: var(--color-border); }
.icon-btn--danger:hover { background: #fef2f2; color: var(--color-danger); border-color: #fecaca; }

.input--inline { flex: 1; min-width: 120px; font-size: .875rem; padding: .3rem .5rem; }

.confirm-text { font-size: .85rem; flex: 1; }

/* Preference row */
.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  cursor: pointer;
  user-select: none;
}
.pref-row__text { display: flex; flex-direction: column; gap: .15rem; }
.pref-row__label { font-size: .9rem; font-weight: 500; color: var(--color-text); }
.pref-row__hint  { font-size: .78rem; color: var(--color-muted); }

.toggle-switch {
  position: relative;
  width: 44px; height: 24px;
  border-radius: 999px;
  border: none;
  background: var(--color-border);
  cursor: pointer;
  flex-shrink: 0;
  transition: background var(--transition);
}
.toggle-switch--on { background: var(--color-accent); }
.toggle-switch__thumb {
  position: absolute;
  top: 3px; left: 3px;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform var(--transition);
  pointer-events: none;
}
.toggle-switch--on .toggle-switch__thumb { transform: translateX(20px); }

/* Theme picker */
.theme-picker {
  display: flex;
  gap: .5rem;
}
.theme-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .35rem;
  padding: .75rem .5rem;
  border-radius: var(--radius);
  border: 2px solid var(--color-border);
  background: var(--color-surface-2);
  cursor: pointer;
  transition: border-color var(--transition), background var(--transition);
}
.theme-btn:hover { border-color: var(--color-muted); }
.theme-btn--active {
  border-color: var(--color-accent);
  background: var(--color-surface);
}
.theme-btn__icon { font-size: 1.3rem; line-height: 1; }
.theme-btn__label { font-size: .75rem; font-weight: 600; color: var(--color-muted); font-family: var(--font-display); }
.theme-btn--active .theme-btn__label { color: var(--color-accent); }

/* Misc */
.state-msg { font-size: .9rem; color: var(--color-muted); padding: 1rem 0; text-align: center; }
.state-msg--error { color: var(--color-danger); }
.btn--sm { font-size: .78rem; padding: .3rem .65rem; }
.btn--danger-solid { background: var(--color-danger); color: #fff; border: none; }
.btn--danger-solid:hover { background: #b91c1c; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-slide-up { animation: slideUp .15s ease; }
</style>
