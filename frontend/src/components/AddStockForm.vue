<script setup lang="ts">
import { reactive, computed } from 'vue'
import type { Product, StockItemCreate, Location } from '@/types'

const props = defineProps<{
  product: Product
  locations: Location[]
  loading: boolean
}>()

const emit = defineEmits<{
  submit: [payload: StockItemCreate]
  cancel: []
}>()

const UNITS = ['unité', 'g', 'kg', 'ml', 'L', 'portion']

// ── Pré-remplissage depuis le champ quantity d'OpenFoodFacts ──────
function parseQuantityStr(qs: string | undefined): { quantity: number; unit: string } | null {
  if (!qs) return null

  // Normalise : "6 x 330 ml", "6 × 33 cl", "330ml", "1,5 L" …
  // Cherche d'abord le format N x M unit (prend M et unit)
  const multi = qs.match(/\d+\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)/i)
  const raw = multi
    ? { qty: multi[1], unit: multi[2] }
    : qs.match(/(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)/i)
      ? { qty: qs.match(/(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)/i)![1], unit: qs.match(/(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)/i)![2] }
      : null

  if (!raw) return null

  let qty = parseFloat(raw.qty.replace(',', '.'))
  const u = raw.unit.toLowerCase()

  if (u === 'g')   return { quantity: qty, unit: 'g' }
  if (u === 'kg')  return { quantity: qty, unit: 'kg' }
  if (u === 'ml')  return { quantity: qty, unit: 'ml' }
  if (u === 'l')   return { quantity: qty, unit: 'L' }
  if (u === 'cl')  return { quantity: Math.round(qty * 10), unit: 'ml' }
  if (u === 'dl')  return { quantity: Math.round(qty * 100), unit: 'ml' }

  return null
}

const prefilled = parseQuantityStr(props.product.quantity_str)

const form = reactive({
  quantity: prefilled?.quantity ?? 1,
  unit: prefilled?.unit ?? 'unité',
  location_id: '',
  opened: false,
  expiry_date: '',
  alert_days_before: 3,
})

// Build flat ordered list with depth from the locations tree
interface FlatLoc { loc: Location; depth: number }

function buildFlat(parentId: string | null, depth: number): FlatLoc[] {
  return props.locations
    .filter(l => (l.parent_id ?? null) === parentId)
    .flatMap(l => [{ loc: l, depth }, ...buildFlat(l.id, depth + 1)])
}

const flatLocations = computed<FlatLoc[]>(() => buildFlat(null, 0))

function locLabel(depth: number, name: string): string {
  return '\u00a0\u00a0'.repeat(depth * 2) + (depth > 0 ? '└ ' : '') + name
}

function onSubmit() {
  const payload: StockItemCreate = {
    product_barcode: props.product.barcode,
    quantity: form.quantity,
    unit: form.unit,
    location_id: form.location_id || undefined,
    opened: form.opened,
    expiry_date: form.expiry_date || undefined,
    alert_days_before: form.alert_days_before,
  }
  emit('submit', payload)
}
</script>

<template>
  <div class="add-form animate-slide-up">
    <h3 class="add-form__title">Ajouter au stock</h3>

    <div class="add-form__grid">
      <!-- Quantité + Unité -->
      <div class="field add-form__qty-unit">
        <label class="label">Quantité</label>
        <div class="qty-unit-wrap">
          <input
            v-model.number="form.quantity"
            type="number"
            min="0.1"
            step="0.1"
            class="input qty-input"
          />
          <select v-model="form.unit" class="input unit-select">
            <option v-for="u in UNITS" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
      </div>

      <!-- Emplacement -->
      <div class="field">
        <label class="label">Emplacement</label>
        <select v-model="form.location_id" class="input">
          <option value="">— choisir —</option>
          <option
            v-for="{ loc, depth } in flatLocations"
            :key="loc.id"
            :value="loc.id"
          >{{ locLabel(depth, loc.name) }}</option>
        </select>
      </div>

      <!-- DLC -->
      <div class="field">
        <label class="label">Date limite (DLC)</label>
        <input v-model="form.expiry_date" type="date" class="input" />
      </div>

      <!-- Alerte -->
      <div class="field" v-if="form.expiry_date">
        <label class="label">Alerte J-{{ form.alert_days_before }}</label>
        <input
          v-model.number="form.alert_days_before"
          type="range"
          min="1"
          max="14"
          class="range-input"
        />
      </div>
    </div>

    <!-- Ouvert -->
    <label class="toggle-row">
      <input v-model="form.opened" type="checkbox" class="sr-only" />
      <span class="toggle" :class="{ 'toggle--on': form.opened }"></span>
      <span>Produit déjà ouvert</span>
    </label>

    <div class="add-form__actions">
      <button class="btn btn--ghost" :disabled="loading" @click="emit('cancel')">Annuler</button>
      <button class="btn btn--primary" :disabled="loading" @click="onSubmit">
        <span v-if="loading">Ajout…</span>
        <span v-else>✓ Ajouter au stock</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.add-form {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 1.25rem;
}

.add-form__title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--color-accent);
}

.add-form__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .75rem;
  margin-bottom: .75rem;
}

@media (max-width: 480px) {
  .add-form__grid { grid-template-columns: 1fr; }
}

.qty-unit-wrap { display: flex; gap: .4rem; }
.qty-input { flex: 1; min-width: 0; }
.unit-select { width: 90px; flex-shrink: 0; }

.range-input {
  width: 100%;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.toggle-row {
  display: flex;
  align-items: center;
  gap: .6rem;
  cursor: pointer;
  font-size: .875rem;
  color: var(--color-muted);
  margin-bottom: 1rem;
  user-select: none;
}
.toggle {
  position: relative;
  width: 36px;
  height: 20px;
  background: var(--color-border);
  border-radius: 999px;
  transition: background var(--transition);
  flex-shrink: 0;
}
.toggle::after {
  content: '';
  position: absolute;
  top: 3px; left: 3px;
  width: 14px; height: 14px;
  background: #fff;
  border-radius: 50%;
  transition: transform var(--transition);
}
.toggle--on { background: var(--color-accent); }
.toggle--on::after { transform: translateX(16px); }

.add-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: .5rem;
  margin-top: .25rem;
}
</style>
