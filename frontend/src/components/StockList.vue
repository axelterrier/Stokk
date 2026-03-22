<script setup lang="ts">
import { ref, computed } from 'vue'
import type { StockItem } from '@/types'
import NutriScore from './NutriScore.vue'

const props = defineProps<{
  items: StockItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  delete: [id: string]
  edit:   [item: StockItem]
}>()

// ── Filtres & tri ──────────────────────────────────────────────
const search   = ref('')
const location = ref('Tous')
const sortKey  = ref<'date' | 'expiry' | 'name'>('date')

const availableLocations = computed(() => {
  const locs = new Set(props.items.map(i => i.location).filter(Boolean) as string[])
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
    list = list.filter(i => i.location === location.value)
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
const LOC_CLASS: Record<string, string> = {
  'Frigo':       'loc--fridge',
  'Congélateur': 'loc--freezer',
  'Placard':     'loc--pantry',
  'Cave':        'loc--cellar',
}
function locClass(loc: string) { return LOC_CLASS[loc] ?? 'loc--other' }
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
        @click="emit('edit', item)"
        title="Modifier"
      >
        <!-- Image -->
        <div class="stock-card__img-wrap">
          <img v-if="item.product.image_url" :src="item.product.image_url"
            :alt="item.product.name" class="stock-card__img" />
          <span v-else class="stock-card__no-img">📦</span>
        </div>

        <!-- Corps -->
        <div class="stock-card__body">
          <p class="stock-card__name">{{ item.product.name }}</p>
          <div class="stock-card__meta">
            <span class="stock-card__qty">{{ item.quantity }} {{ item.unit }}</span>
            <span v-if="item.location" class="loc-badge" :class="locClass(item.location)">
              {{ item.location }}
            </span>
            <span v-if="item.opened" class="stock-card__opened">Ouvert</span>
          </div>
        </div>

        <!-- Droite : DLC + Nutriscore + suppression -->
        <div class="stock-card__side">
          <div class="stock-card__badges">
            <span v-if="item.expiry_date" class="expiry-badge"
              :class="expiryClass(item.expiry_date.expiry_date)">
              {{ expiryLabel(item.expiry_date.expiry_date) }}
            </span>
            <NutriScore :score="item.product.nutriscore" />
          </div>
          <button
            class="btn btn--danger stock-card__delete"
            title="Supprimer"
            @click.stop="emit('delete', item.id)"
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
</template>

<style scoped>
/* ── En-tête ─────────────────────────────────────────────────── */
.stock-list__header { margin-bottom: .75rem; }
.stock-list__title  { font-size: 1.05rem; font-weight: 700; display: flex; align-items: baseline; gap: .5rem; }
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
.stock-card:hover { box-shadow: var(--shadow-md); border-color: #d6d3d1; }

/* Image */
.stock-card__img    { width: 48px; height: 48px; object-fit: contain; border-radius: 8px; background: var(--color-surface-2); display: block; }
.stock-card__no-img { width: 48px; height: 48px; display: grid; place-items: center; font-size: 1.5rem; background: var(--color-surface-2); border-radius: 8px; }

/* Corps */
.stock-card__body { min-width: 0; }
.stock-card__name {
  font-size: .88rem;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: .3rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.stock-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .25rem .4rem;
}
.stock-card__qty    { font-size: .78rem; color: var(--color-muted); }
.stock-card__opened {
  font-size: .7rem; padding: .05rem .35rem;
  background: #fff7ed; color: #c2410c;
  border: 1px solid #fed7aa; border-radius: 4px;
}

/* Badges emplacement */
.loc-badge {
  font-size: .7rem; font-weight: 600;
  padding: .1rem .45rem; border-radius: 5px;
}
.loc--fridge  { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.loc--freezer { background: #ecfeff; color: #0891b2; border: 1px solid #a5f3fc; }
.loc--pantry  { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
.loc--cellar  { background: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; }
.loc--other   { background: var(--color-surface-2); color: var(--color-muted); border: 1px solid var(--color-border); }

/* Côté droit */
.stock-card__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: .4rem;
  flex-shrink: 0;
}
.stock-card__badges {
  display: flex;
  align-items: center;
  gap: .3rem;
}

/* Badge DLC */
.expiry-badge {
  font-size: .72rem; font-weight: 700;
  padding: .2rem .55rem; border-radius: 6px;
  white-space: nowrap;
}
.expiry--ok      { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.expiry--soon    { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
.expiry--urgent  { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.expiry--expired { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

/* Bouton suppression */
.stock-card__delete { padding: .4rem; border-radius: 7px; }
</style>
