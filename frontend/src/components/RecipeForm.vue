<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import { api } from '@/composables/useApi'
import type { Recipe, RecipeCreate, RecipeIngredientCreate, Product, StockItem } from '@/types'

const props = defineProps<{
  recipe: Recipe | null  // null = création, sinon édition
  stockItems: StockItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  submit: [payload: RecipeCreate]
  close: []
}>()

const UNITS = ['unité', 'g', 'kg', 'ml', 'L', 'cl', 'portion']

// ── Form state ──────────────────────────────────────────────────────────────

const form = reactive({
  name: '',
  description: '',
})

const ingredients = ref<RecipeIngredientCreate[]>([])

watch(() => props.recipe, (r) => {
  form.name = r?.name ?? ''
  form.description = r?.description ?? ''
  ingredients.value = r
    ? r.ingredients.map(i => ({
        product_barcode: i.product_barcode ?? null,
        ingredient_name: i.ingredient_name,
        quantity: i.quantity,
        unit: i.unit,
      }))
    : []
}, { immediate: true })

// ── Product search ──────────────────────────────────────────────────────────

interface SearchState {
  query: string
  results: Product[]
  open: boolean
  loading: boolean
  activeIndex: number  // which ingredient row is open
}

const search = reactive<SearchState>({
  query: '',
  results: [],
  open: false,
  loading: false,
  activeIndex: -1,
})

let searchDebounce: ReturnType<typeof setTimeout> | null = null

async function onSearchInput(idx: number, value: string) {
  ingredients.value[idx].ingredient_name = value
  ingredients.value[idx].product_barcode = null  // clear link on manual edit
  search.activeIndex = idx
  search.query = value
  search.open = false

  if (searchDebounce) clearTimeout(searchDebounce)
  if (value.length < 2) { search.results = []; return }

  searchDebounce = setTimeout(async () => {
    search.loading = true
    try {
      search.results = await api.searchProducts(value)
      search.open = search.results.length > 0 && search.activeIndex === idx
    } finally {
      search.loading = false
    }
  }, 250)
}

function selectProduct(idx: number, product: Product) {
  ingredients.value[idx].ingredient_name = product.name
  ingredients.value[idx].product_barcode = product.barcode
  search.open = false
  search.results = []
}

function closeSearch() {
  setTimeout(() => { search.open = false }, 150)
}

// ── Ingredient management ────────────────────────────────────────────────────

function addIngredient() {
  ingredients.value.push({ product_barcode: null, ingredient_name: '', quantity: 1, unit: 'g' })
}

function removeIngredient(idx: number) {
  ingredients.value.splice(idx, 1)
}

// ── Stock status per ingredient ──────────────────────────────────────────────

// Returns total quantity in stock for a barcode
function stockTotal(barcode: string | null | undefined): number {
  if (!barcode) return 0
  return props.stockItems
    .filter(s => s.product_barcode === barcode)
    .reduce((acc, s) => acc + s.quantity, 0)
}

function ingredientStatus(ing: RecipeIngredientCreate): 'ok' | 'partial' | 'out' | 'unlinked' {
  if (!ing.product_barcode) return 'unlinked'
  const avail = stockTotal(ing.product_barcode)
  if (avail <= 0) return 'out'
  if (avail < ing.quantity) return 'partial'
  return 'ok'
}

const statusLabel: Record<string, string> = {
  ok: '✓ En stock',
  partial: '⚠ Partiel',
  out: '✕ Hors stock',
  unlinked: '— Non lié',
}

const statusClass: Record<string, string> = {
  ok: 'badge--ok',
  partial: 'badge--partial',
  out: 'badge--out',
  unlinked: 'badge--unlinked',
}

// ── Submit ───────────────────────────────────────────────────────────────────

const canSubmit = computed(() => form.name.trim().length > 0)

function onSubmit() {
  if (!canSubmit.value) return
  emit('submit', {
    name: form.name.trim(),
    description: form.description.trim() || null,
    ingredients: ingredients.value.filter(i => i.ingredient_name.trim()),
  })
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal animate-slide-up">
      <header class="modal__header">
        <div class="modal__title-wrap">
          <span class="modal__icon">📋</span>
          <h2 class="modal__title">{{ recipe ? 'Modifier la recette' : 'Nouvelle recette' }}</h2>
        </div>
        <button class="btn btn--ghost modal__close" @click="emit('close')">✕</button>
      </header>

      <!-- Nom + Description -->
      <div class="field">
        <label class="label">Nom de la recette *</label>
        <input v-model="form.name" class="input" placeholder="Ex: Gratin dauphinois" />
      </div>

      <div class="field">
        <label class="label">Description (optionnel)</label>
        <textarea v-model="form.description" class="input textarea" placeholder="Notes, temps de cuisson…" rows="2" />
      </div>

      <hr class="divider" />

      <!-- Ingrédients -->
      <div class="ingredients-header">
        <span class="label" style="margin-bottom:0">Ingrédients</span>
        <button class="btn btn--ghost btn--sm" type="button" @click="addIngredient">+ Ajouter</button>
      </div>

      <div v-if="ingredients.length === 0" class="empty-ingredients">
        Aucun ingrédient — cliquez sur "+ Ajouter"
      </div>

      <div v-for="(ing, idx) in ingredients" :key="idx" class="ingredient-row">
        <!-- Recherche produit -->
        <div class="ing-search-wrap">
          <input
            :value="ing.ingredient_name"
            @input="onSearchInput(idx, ($event.target as HTMLInputElement).value)"
            @blur="closeSearch"
            @focus="search.activeIndex = idx; search.open = search.results.length > 0 && search.activeIndex === idx"
            class="input ing-name"
            placeholder="Nom ou recherche produit…"
          />
          <!-- Dropdown suggestions -->
          <ul v-if="search.open && search.activeIndex === idx" class="search-dropdown">
            <li
              v-for="p in search.results"
              :key="p.barcode"
              class="search-item"
              @mousedown.prevent="selectProduct(idx, p)"
            >
              <span class="search-item__name">{{ p.name }}</span>
              <span v-if="p.brand" class="search-item__brand">{{ p.brand }}</span>
            </li>
          </ul>
          <!-- Statut stock -->
          <span class="ing-badge" :class="statusClass[ingredientStatus(ing)]">
            {{ statusLabel[ingredientStatus(ing)] }}
          </span>
          <span v-if="ing.product_barcode" class="ing-avail">
            (dispo: {{ stockTotal(ing.product_barcode) }} {{ ing.unit }})
          </span>
        </div>

        <!-- Quantité + Unité + Supprimer -->
        <div class="ing-qty-row">
          <input
            v-model.number="ing.quantity"
            type="number"
            min="0.01"
            step="0.01"
            class="input qty-input"
          />
          <select v-model="ing.unit" class="input unit-select">
            <option v-for="u in UNITS" :key="u" :value="u">{{ u }}</option>
          </select>
          <button class="btn btn--danger btn--sm" type="button" @click="removeIngredient(idx)" title="Supprimer">✕</button>
        </div>
      </div>

      <!-- Actions -->
      <div class="modal__actions">
        <button class="btn btn--ghost" :disabled="loading" @click="emit('close')">Annuler</button>
        <button class="btn btn--primary" :disabled="loading || !canSubmit" @click="onSubmit">
          <span v-if="loading">Enregistrement…</span>
          <span v-else>✓ Enregistrer</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.35);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}
@media (min-width: 480px) { .modal-backdrop { align-items: center; } }

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  padding: 1.5rem;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: .9rem;
}

.modal__header { display: flex; align-items: center; justify-content: space-between; }
.modal__title-wrap { display: flex; align-items: center; gap: .5rem; }
.modal__title { font-size: 1.05rem; font-weight: 700; }
.modal__close { padding: .3rem .55rem; font-size: .8rem; }

.textarea { resize: vertical; min-height: 60px; }

.ingredients-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn--sm { padding: .3rem .65rem; font-size: .8rem; }

.empty-ingredients {
  font-size: .85rem;
  color: var(--color-muted);
  text-align: center;
  padding: .75rem;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius);
}

.ingredient-row {
  display: flex;
  flex-direction: column;
  gap: .4rem;
  padding: .75rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.ing-search-wrap { position: relative; display: flex; flex-direction: column; gap: .25rem; }

.ing-name { width: 100%; }

.search-dropdown {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  z-index: 200;
  max-height: 200px;
  overflow-y: auto;
  list-style: none;
  padding: .25rem 0;
  margin: 0;
}

.search-item {
  display: flex;
  align-items: baseline;
  gap: .5rem;
  padding: .5rem .75rem;
  cursor: pointer;
  font-size: .875rem;
}
.search-item:hover { background: var(--color-surface-2); }
.search-item__name { font-weight: 500; }
.search-item__brand { font-size: .75rem; color: var(--color-muted); }

.ing-badge {
  display: inline-block;
  font-size: .7rem;
  font-weight: 600;
  padding: .15rem .5rem;
  border-radius: 999px;
  border: 1px solid;
  width: fit-content;
}
.badge--ok       { background: #dcfce7; color: #15803d; border-color: #86efac; }
.badge--partial  { background: #fef9c3; color: #854d0e; border-color: #fde047; }
.badge--out      { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.badge--unlinked { background: var(--color-surface-2); color: var(--color-muted); border-color: var(--color-border); }

.ing-avail { font-size: .75rem; color: var(--color-muted); }

.ing-qty-row {
  display: flex;
  gap: .4rem;
  align-items: center;
}
.qty-input { flex: 1; min-width: 0; }
.unit-select { width: 85px; flex-shrink: 0; }

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: .5rem;
  margin-top: .25rem;
}
</style>
