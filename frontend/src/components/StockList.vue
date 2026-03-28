<script setup lang="ts">
import { ref, computed } from 'vue'
import type { StockItem, Location } from '@/types'
import NutriScore from './NutriScore.vue'
import { usePreferences } from '@/composables/usePreferences'

const { prefs } = usePreferences()

const props = defineProps<{
  items: StockItem[]
  locations: Location[]
  loading: boolean
}>()

const emit = defineEmits<{
  delete:     [id: string]
  deleteMany: [ids: string[]]
  edit:       [item: StockItem]
  detail:     [item: StockItem]
}>()

const confirmItem = ref<StockItem | null>(null)

// ── Sélection multiple ──────────────────────────────────────────
const selectionMode = ref(false)
const selectedIds   = ref<Set<string>>(new Set())
const confirmMass   = ref(false)

function enterSelection() {
  selectionMode.value = true
  selectedIds.value   = new Set()
  confirmMass.value   = false
}

function exitSelection() {
  selectionMode.value = false
  selectedIds.value   = new Set()
  confirmMass.value   = false
}

function toggleSelect(id: string) {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

function toggleSelectAll() {
  if (selectedIds.value.size === filteredItems.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(filteredItems.value.map(i => i.id))
  }
}

function doDeleteMany() {
  emit('deleteMany', Array.from(selectedIds.value))
  exitSelection()
}

// ── Filtres & tri ──────────────────────────────────────────────
const search   = ref('')
const location = ref('Tous')
const sortKey  = ref<'date' | 'expiry' | 'name'>('date')

const availableLocations = computed(() => {
  const locs = new Set(props.items.map(i => i.location?.name).filter(Boolean) as string[])
  return ['Tous', ...Array.from(locs).sort()]
})

const filteredItems = computed(() => {
  let list = props.items

  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase()
    list = list.filter(i =>
      i.product.name.toLowerCase().includes(q) ||
      i.product.brand?.toLowerCase().includes(q)
    )
  }

  if (location.value !== 'Tous') {
    list = list.filter(i => i.location?.name === location.value)
  }

  return [...list].sort((a, b) => {
    if (sortKey.value === 'name')
      return a.product.name.localeCompare(b.product.name)
    if (sortKey.value === 'expiry') {
      const da = a.expiry_date ? new Date(a.expiry_date.expiry_date).getTime() : Infinity
      const db = b.expiry_date ? new Date(b.expiry_date.expiry_date).getTime() : Infinity
      return da - db
    }
    return new Date(b.added_at).getTime() - new Date(a.added_at).getTime()
  })
})

const isFiltered = computed(() => search.value.trim() !== '' || location.value !== 'Tous')

function clearFilters() {
  search.value   = ''
  location.value = 'Tous'
}

// ── Expiry helpers ─────────────────────────────────────────────
function daysUntil(dateStr: string): number {
  return Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86_400_000)
}

function expiryClass(dateStr: string): string {
  const d = daysUntil(dateStr)
  if (d < 0)  return 'expiry--expired'
  if (d <= 3) return 'expiry--urgent'
  if (d <= 7) return 'expiry--soon'
  return 'expiry--ok'
}

function expiryLabel(dateStr: string): string {
  const d = daysUntil(dateStr)
  if (d < 0)  return `Expiré (${Math.abs(d)}j)`
  if (d === 0) return "Auj."
  if (d === 1) return 'Demain'
  return `J-${d}`
}

// ── Location ───────────────────────────────────────────────────
const COLOR_CLASS: Record<string, string> = {
  blue: 'loc--blue', cyan: 'loc--cyan', green: 'loc--green',
  yellow: 'loc--yellow', orange: 'loc--orange', red: 'loc--red',
  purple: 'loc--purple', pink: 'loc--pink',
}
function locColor(loc?: { color?: string | null }) {
  return COLOR_CLASS[loc?.color ?? ''] ?? 'loc--default'
}
</script>

<template>
  <section class="stock-list">

    <!-- En-tête -->
    <header class="stock-list__header">
      <h2 class="stock-list__title">
        Stock
        <span class="stock-list__count">
          {{ filteredItems.length }}<template v-if="isFiltered"> / {{ items.length }}</template>
        </span>
      </h2>
      <div class="stock-list__actions">
        <template v-if="!selectionMode">
          <button v-if="items.length" class="btn btn--ghost btn--sm" @click="enterSelection">Sélectionner</button>
        </template>
        <template v-else>
          <button class="sel-all-btn" @click="toggleSelectAll">
            {{ selectedIds.size === filteredItems.length ? 'Tout désélectionner' : 'Tout sélectionner' }}
          </button>
          <button class="btn btn--ghost btn--sm" @click="exitSelection">Annuler</button>
        </template>
      </div>
    </header>

    <!-- Filtres -->
    <div v-if="!loading && items.length" class="filters">
      <div class="filters__row">
        <div class="filters__search-wrap">
          <svg class="filters__icon" width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="search" type="search" placeholder="Rechercher…" class="input filters__search" />
        </div>
        <select v-model="sortKey" class="input filters__sort">
          <option value="date">Récent</option>
          <option value="expiry">DLC</option>
          <option value="name">Nom</option>
        </select>
      </div>

      <div class="filters__locs">
        <button
          v-for="loc in availableLocations" :key="loc"
          class="loc-pill" :class="{ 'loc-pill--active': location === loc }"
          @click="location = loc"
        >{{ loc }}</button>
        <button v-if="isFiltered" class="filters__reset" @click="clearFilters">✕ Réinitialiser</button>
      </div>
    </div>

    <!-- États vides -->
    <p v-if="loading" class="empty">Chargement…</p>
    <p v-else-if="!items.length" class="empty">Aucun article — commencez par scanner un produit !</p>
    <p v-else-if="!filteredItems.length" class="empty">
      Aucun résultat.
      <button class="filters__reset" style="text-decoration:underline" @click="clearFilters">Réinitialiser</button>
    </p>

    <!-- Grille d'articles -->
    <ul v-else class="stock-grid">
      <li
        v-for="item in filteredItems" :key="item.id"
        class="stock-card animate-slide-up"
        :class="{
          'stock-card--no-img':    !selectionMode && !prefs.showImages,
          'stock-card--selecting': selectionMode,
          'stock-card--selected':  selectedIds.has(item.id),
        }"
        @click="selectionMode ? toggleSelect(item.id) : emit('detail', item)"
        :title="selectionMode ? '' : 'Voir le détail'"
      >
        <!-- Checkbox sélection -->
        <div v-if="selectionMode" class="stock-card__check">
          <span class="check-circle" :class="{ 'check-circle--on': selectedIds.has(item.id) }">
            <svg v-if="selectedIds.has(item.id)" width="10" height="10" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </span>
        </div>

        <!-- Image -->
        <div v-else-if="prefs.showImages" class="stock-card__img-wrap">
          <img v-if="item.product.image_url" :src="item.product.image_url"
            :alt="item.product.name" class="stock-card__img" />
          <span v-else class="stock-card__no-img">📦</span>
        </div>

        <!-- Corps -->
        <div class="stock-card__body">
          <p class="stock-card__name">{{ item.product.name }}</p>
          <div class="stock-card__row">
            <div class="stock-card__left">
              <span class="stock-card__qty">{{ item.quantity }} {{ item.unit }}</span>
              <span v-if="item.location" class="loc-badge" :class="locColor(item.location)">
                {{ item.location.name }}
              </span>
              <span v-if="item.opened" class="stock-card__opened">Ouvert</span>
            </div>
            <div class="stock-card__right">
              <span v-if="item.expiry_date" class="expiry-badge"
                :class="expiryClass(item.expiry_date.expiry_date)">
                {{ expiryLabel(item.expiry_date.expiry_date) }}
              </span>
              <NutriScore :score="item.product.nutriscore" />
            </div>
          </div>
        </div>

        <!-- Boutons actions (masqués en mode sélection) -->
        <div v-if="!selectionMode" class="stock-card__btns">
          <button
            class="stock-card__action-btn"
            title="Modifier"
            @click.stop="emit('edit', item)"
            aria-label="Modifier"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button
            class="stock-card__delete"
            title="Supprimer"
            @click.stop="confirmItem = item"
            aria-label="Supprimer"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14H6L5 6"/>
              <path d="M10 11v6M14 11v6"/>
              <path d="M9 6V4h6v2"/>
            </svg>
          </button>
        </div>
      </li>
    </ul>

  </section>

  <!-- Barre mass delete -->
  <Teleport to="body">
    <div v-if="selectionMode && selectedIds.size > 0" class="mass-bar animate-slide-up">
      <span class="mass-bar__count">{{ selectedIds.size }} sélectionné{{ selectedIds.size > 1 ? 's' : '' }}</span>
      <div class="mass-bar__actions">
        <button v-if="!confirmMass" class="btn btn--danger-solid" @click="confirmMass = true">
          Supprimer
        </button>
        <template v-else>
          <span class="mass-bar__confirm-label">Confirmer ?</span>
          <button class="btn btn--danger-solid" @click="doDeleteMany">Oui</button>
          <button class="btn btn--ghost btn--sm" @click="confirmMass = false">Non</button>
        </template>
      </div>
    </div>
  </Teleport>

  <!-- Modale de confirmation suppression -->
  <Teleport to="body">
    <div v-if="confirmItem" class="confirm-backdrop" @click.self="confirmItem = null">
      <div class="confirm-dialog animate-slide-up">
        <div class="confirm-dialog__img-wrap">
          <img v-if="prefs.showImages && confirmItem.product.image_url" :src="confirmItem.product.image_url"
            :alt="confirmItem.product.name" class="confirm-dialog__img" />
          <span v-else class="confirm-dialog__no-img">📦</span>
        </div>
        <div class="confirm-dialog__body">
          <p class="confirm-dialog__title">Supprimer cet article ?</p>
          <p class="confirm-dialog__name">{{ confirmItem.product.name }}</p>
          <p class="confirm-dialog__detail">{{ confirmItem.quantity }} {{ confirmItem.unit }}<span v-if="confirmItem.location"> · {{ confirmItem.location.name }}</span></p>
        </div>
        <div class="confirm-dialog__actions">
          <button class="btn btn--ghost" @click="confirmItem = null">Annuler</button>
          <button class="btn btn--danger-solid" @click="emit('delete', confirmItem!.id); confirmItem = null">
            Supprimer
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* ── En-tête ─────────────────────────────────────────────────── */
.stock-list__header { margin-bottom: .75rem; display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
.stock-list__title  { font-size: 1.05rem; font-weight: 700; display: flex; align-items: baseline; gap: .5rem; }
.stock-list__actions { display: flex; align-items: center; gap: .4rem; flex-shrink: 0; }
.sel-all-btn {
  background: none; border: none; font-size: .78rem;
  color: var(--color-accent); cursor: pointer; font-weight: 600;
  padding: 0 .25rem;
}
.stock-list__count  {
  font-size: .78rem;
  font-weight: 500;
  color: var(--color-muted);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  padding: .1rem .5rem;
  border-radius: 99px;
}

/* ── État vide ───────────────────────────────────────────────── */
.empty {
  color: var(--color-muted);
  font-size: .9rem;
  padding: 2.5rem 0;
  text-align: center;
}

/* ── Filtres ─────────────────────────────────────────────────── */
.filters        { display: flex; flex-direction: column; gap: .5rem; margin-bottom: .85rem; }
.filters__row   { display: flex; gap: .5rem; }

.filters__search-wrap { position: relative; flex: 1; }
.filters__icon {
  position: absolute; left: .75rem; top: 50%;
  transform: translateY(-50%); color: var(--color-muted); pointer-events: none;
}
.filters__search { padding-left: 2.2rem; }
.filters__search::-webkit-search-cancel-button { display: none; }
.filters__sort  { width: auto; flex-shrink: 0; font-size: .82rem; }

.filters__locs  { display: flex; flex-wrap: wrap; gap: .35rem; align-items: center; }

.loc-pill {
  padding: .22rem .75rem;
  border-radius: 99px;
  font-size: .78rem;
  font-weight: 500;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-muted);
  cursor: pointer;
  transition: all var(--transition);
}
.loc-pill:hover      { border-color: #a8a29e; color: var(--color-text); }
.loc-pill--active    { background: var(--color-text); border-color: var(--color-text); color: #fff; }

.filters__reset {
  background: none; border: none;
  font-size: .78rem; color: var(--color-muted);
  cursor: pointer; padding: 0 .2rem;
  transition: color var(--transition);
}
.filters__reset:hover { color: var(--color-text); }

/* ── Grille ──────────────────────────────────────────────────── */
.stock-grid {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: .5rem;
}
@media (min-width: 1024px) {
  .stock-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
}

/* ── Carte article ───────────────────────────────────────────── */
.stock-card {
  position: relative;
  display: grid;
  grid-template-columns: 48px 1fr auto;
  align-items: center;
  gap: .75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  padding: .75rem .8rem;
  cursor: pointer;
  transition: box-shadow var(--transition), border-color var(--transition);
}
.stock-card--no-img {
  grid-template-columns: 1fr auto;
}
.stock-card:hover { box-shadow: var(--shadow-md); border-color: #d6d3d1; }

/* Image */
.stock-card__img-wrap { flex-shrink: 0; }
.stock-card__img    { width: 48px; height: 48px; object-fit: contain; border-radius: 8px; background: var(--color-surface-2); display: block; }
.stock-card__no-img { width: 48px; height: 48px; display: grid; place-items: center; font-size: 1.5rem; background: var(--color-surface-2); border-radius: 8px; }

/* Corps */
.stock-card__body { min-width: 0; display: flex; flex-direction: column; gap: .3rem; }
.stock-card__name {
  font-size: .88rem;
  font-weight: 600;
  line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Ligne info : gauche fixe / droite fixe */
.stock-card__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .4rem;
}
.stock-card__left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: .25rem;
  min-width: 0;
}
.stock-card__right {
  display: flex;
  align-items: center;
  gap: .25rem;
  flex-shrink: 0;
}

.stock-card__qty    { font-size: .75rem; color: var(--color-muted); white-space: nowrap; }
.stock-card__nutrition {
  display: flex;
  flex-wrap: wrap;
  gap: .2rem .4rem;
  font-size: .68rem;
  color: var(--color-muted);
}
.stock-card__opened {
  font-size: .68rem; padding: .05rem .35rem;
  background: #fff7ed; color: #c2410c;
  border: 1px solid #fed7aa; border-radius: 4px;
}

.loc-badge {
  font-size: .68rem; font-weight: 600;
  padding: .08rem .4rem; border-radius: 5px;
}
.loc--default { background: var(--color-surface-2); color: var(--color-muted); border: 1px solid var(--color-border); }
.loc--blue    { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.loc--cyan    { background: #ecfeff; color: #0891b2; border: 1px solid #a5f3fc; }
.loc--green   { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.loc--yellow  { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
.loc--orange  { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.loc--red     { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.loc--purple  { background: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; }
.loc--pink    { background: #fdf2f8; color: #be185d; border: 1px solid #fbcfe8; }


.expiry-badge {
  font-size: .68rem; font-weight: 700;
  padding: .08rem .4rem; border-radius: 5px;
  white-space: nowrap;
}
.expiry--ok      { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.expiry--soon    { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
.expiry--urgent  { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.expiry--expired { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }


/* ── Modale confirmation ─────────────────────────────────────── */
.confirm-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.35);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 1rem;
}
.confirm-dialog {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: var(--shadow-md);
  padding: 1.5rem;
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  text-align: center;
}
.confirm-dialog__img-wrap { display: flex; justify-content: center; }
.confirm-dialog__img    { width: 64px; height: 64px; object-fit: contain; border-radius: 10px; background: var(--color-surface-2); }
.confirm-dialog__no-img { width: 64px; height: 64px; display: grid; place-items: center; font-size: 2rem; background: var(--color-surface-2); border-radius: 10px; }
.confirm-dialog__body   { display: flex; flex-direction: column; gap: .25rem; }
.confirm-dialog__title  { font-family: var(--font-display); font-size: 1rem; font-weight: 700; }
.confirm-dialog__name   { font-size: .9rem; color: var(--color-text); font-weight: 500; }
.confirm-dialog__detail { font-size: .8rem; color: var(--color-muted); }
.confirm-dialog__actions {
  display: flex;
  gap: .6rem;
  width: 100%;
}
.confirm-dialog__actions .btn { flex: 1; justify-content: center; }
.btn--danger-solid {
  background: var(--color-danger);
  color: #fff;
  border: none;
  transition: background var(--transition);
}
.btn--danger-solid:hover { background: #b91c1c; }

/* ── Sélection multiple ──────────────────────────────────────── */
.stock-card--selecting { cursor: default; grid-template-columns: 48px 1fr; }
.stock-card__nutrition { display: none; }
.stock-card--selecting:hover { box-shadow: var(--shadow-sm); border-color: var(--color-border); }
.stock-card--selected  { border-color: var(--color-accent); background: rgba(234,88,12,.05); }

.stock-card__check { display: flex; align-items: center; justify-content: center; width: 48px; flex-shrink: 0; }
.check-circle {
  width: 22px; height: 22px; border-radius: 50%;
  border: 2px solid var(--color-border);
  display: grid; place-items: center;
  transition: all var(--transition);
  background: var(--color-surface);
}
.check-circle--on {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

/* Barre mass delete */
.mass-bar {
  position: fixed;
  bottom: 5rem;
  left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 99px;
  box-shadow: var(--shadow-md);
  padding: .6rem .6rem .6rem 1.25rem;
  z-index: 150;
  white-space: nowrap;
}
@media (min-width: 768px) { .mass-bar { bottom: 2rem; } }
.mass-bar__count { font-size: .875rem; font-weight: 600; color: var(--color-text); }
.mass-bar__actions { display: flex; align-items: center; gap: .4rem; }
.mass-bar__confirm-label { font-size: .8rem; color: var(--color-danger); font-weight: 600; }

/* Boutons actions */
.stock-card__btns {
  display: flex;
  flex-direction: column;
  gap: .25rem;
  flex-shrink: 0;
}

.stock-card__action-btn,
.stock-card__delete {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 7px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: background var(--transition), color var(--transition), border-color var(--transition);
}
.stock-card__action-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
  border-color: var(--color-border);
}
.stock-card__delete:hover {
  background: #fef2f2;
  color: var(--color-danger);
  border-color: #fecaca;
}
</style>
