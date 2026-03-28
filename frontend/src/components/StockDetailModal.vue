<script setup lang="ts">
import { computed } from 'vue'
import type { StockItem, Recipe } from '@/types'
import NutriScore from './NutriScore.vue'

const props = defineProps<{
  item: StockItem
  recipes: Recipe[]
}>()

const emit = defineEmits<{
  edit: [item: StockItem]
  close: []
}>()

// ── Recettes utilisant ce produit ────────────────────────────────

const usedInRecipes = computed(() =>
  props.recipes.filter(r =>
    r.ingredients.some(i => i.product_barcode === props.item.product_barcode)
  )
)

// ── Nutrition ────────────────────────────────────────────────────

function toBaseUnit(qty: number, unit: string): number | null {
  switch (unit) {
    case 'g':  return qty
    case 'kg': return qty * 1000
    case 'ml': return qty
    case 'cl': return qty * 10
    case 'L':  return qty * 1000
    default:   return null
  }
}

const p = props.item.product
const hasNutrition = p.energy_kcal != null || p.proteins_g != null || p.carbs_g != null || p.fat_g != null

const stockQtyBase = computed(() => toBaseUnit(props.item.quantity, props.item.unit))

function forQty(per100: number | null | undefined): string {
  if (per100 == null || stockQtyBase.value === null) return '—'
  return (Math.round(per100 * stockQtyBase.value / 100 * 10) / 10).toString()
}

function fmt(v: number | null | undefined): string {
  return v != null ? v.toString() : '—'
}

// ── Expiry ───────────────────────────────────────────────────────

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
  if (d < 0)   return `Expiré (il y a ${Math.abs(d)}j)`
  if (d === 0) return 'Expire aujourd\'hui'
  if (d === 1) return 'Expire demain'
  return `Expire dans ${d} jours`
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal animate-slide-up">

      <!-- Header -->
      <header class="modal__header">
        <div class="modal__title-wrap">
          <img v-if="item.product.image_url" :src="item.product.image_url"
            :alt="item.product.name" class="modal__img" />
          <span v-else class="modal__img modal__img--placeholder">📦</span>
          <div>
            <h2 class="modal__title">{{ item.product.name }}</h2>
            <p v-if="item.product.brand" class="modal__brand">{{ item.product.brand }}</p>
          </div>
        </div>
        <button class="btn btn--ghost modal__close" @click="emit('close')">✕</button>
      </header>

      <!-- Infos principales -->
      <div class="info-grid">
        <div class="info-cell">
          <span class="info-label">Quantité</span>
          <span class="info-value">{{ item.quantity }} {{ item.unit }}</span>
        </div>
        <div class="info-cell">
          <span class="info-label">Emplacement</span>
          <span class="info-value">{{ item.location?.name ?? '—' }}</span>
        </div>
        <div class="info-cell">
          <span class="info-label">Nutriscore</span>
          <NutriScore :score="item.product.nutriscore" />
        </div>
        <div class="info-cell">
          <span class="info-label">État</span>
          <span class="info-value">{{ item.opened ? 'Ouvert' : 'Fermé' }}</span>
        </div>
        <div v-if="item.expiry_date" class="info-cell info-cell--full">
          <span class="info-label">Date limite</span>
          <span class="expiry-badge" :class="expiryClass(item.expiry_date.expiry_date)">
            {{ item.expiry_date.expiry_date }} — {{ expiryLabel(item.expiry_date.expiry_date) }}
          </span>
        </div>
      </div>

      <!-- Valeurs nutritionnelles -->
      <div v-if="hasNutrition" class="nutrition-section">
        <h3 class="section-title">Valeurs nutritionnelles</h3>
        <table class="nutrition-table">
          <thead>
            <tr>
              <th></th>
              <th>Pour 100g</th>
              <th>Pour {{ item.quantity }} {{ item.unit }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="nutrient-name">Énergie</td>
              <td>{{ fmt(p.energy_kcal) }} kcal</td>
              <td class="nutrient-total">{{ forQty(p.energy_kcal) }} kcal</td>
            </tr>
            <tr>
              <td class="nutrient-name">Protéines</td>
              <td>{{ fmt(p.proteins_g) }} g</td>
              <td class="nutrient-total">{{ forQty(p.proteins_g) }} g</td>
            </tr>
            <tr>
              <td class="nutrient-name">Glucides</td>
              <td>{{ fmt(p.carbs_g) }} g</td>
              <td class="nutrient-total">{{ forQty(p.carbs_g) }} g</td>
            </tr>
            <tr>
              <td class="nutrient-name">Lipides</td>
              <td>{{ fmt(p.fat_g) }} g</td>
              <td class="nutrient-total">{{ forQty(p.fat_g) }} g</td>
            </tr>
          </tbody>
        </table>
        <p v-if="stockQtyBase === null" class="nutrition-note">
          * Calcul indisponible pour l'unité "{{ item.unit }}"
        </p>
      </div>
      <div v-else class="nutrition-empty">
        Aucune valeur nutritionnelle disponible pour ce produit.
      </div>

      <!-- Recettes -->
      <div class="recipes-section">
        <h3 class="section-title">
          Utilisé dans
          <span class="recipe-count">{{ usedInRecipes.length }} recette{{ usedInRecipes.length !== 1 ? 's' : '' }}</span>
        </h3>
        <ul v-if="usedInRecipes.length > 0" class="recipe-list">
          <li v-for="r in usedInRecipes" :key="r.id" class="recipe-item">
            <span class="recipe-item__name">{{ r.name }}</span>
            <span class="recipe-item__qty">
              {{
                r.ingredients.find(i => i.product_barcode === item.product_barcode)?.quantity
              }} {{
                r.ingredients.find(i => i.product_barcode === item.product_barcode)?.unit
              }}
            </span>
          </li>
        </ul>
        <p v-else class="recipe-none">Non utilisé dans une recette.</p>
      </div>

      <!-- Actions -->
      <div class="modal__actions">
        <button class="btn btn--ghost" @click="emit('close')">Fermer</button>
        <button class="btn btn--primary" @click="emit('edit', item)">Modifier</button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.35);
  backdrop-filter: blur(3px);
  display: flex; align-items: flex-end; justify-content: center;
  z-index: 100; padding: 1rem;
}
@media (min-width: 480px) { .modal-backdrop { align-items: center; } }

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  padding: 1.5rem;
  width: 100%; max-width: 500px;
  max-height: 90vh; overflow-y: auto;
  display: flex; flex-direction: column; gap: 1.1rem;
}

.modal__header {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: .75rem;
}
.modal__title-wrap { display: flex; align-items: center; gap: .75rem; min-width: 0; }
.modal__img {
  width: 52px; height: 52px; object-fit: contain;
  border-radius: 10px; background: var(--color-surface-2); flex-shrink: 0;
}
.modal__img--placeholder {
  display: grid; place-items: center; font-size: 1.5rem;
}
.modal__title { font-size: 1rem; font-weight: 700; line-height: 1.3; }
.modal__brand { font-size: .78rem; color: var(--color-muted); margin-top: .1rem; }
.modal__close { padding: .3rem .55rem; font-size: .8rem; flex-shrink: 0; }

/* Info grid */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .6rem;
}
.info-cell {
  display: flex; flex-direction: column; gap: .2rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: .55rem .75rem;
}
.info-cell--full { grid-column: 1 / -1; }
.info-label { font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--color-muted); }
.info-value { font-size: .9rem; font-weight: 500; }

.expiry-badge {
  font-size: .78rem; font-weight: 600;
  padding: .1rem .45rem; border-radius: 5px;
  width: fit-content;
}
.expiry--ok      { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.expiry--soon    { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
.expiry--urgent  { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.expiry--expired { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

/* Nutrition */
.section-title {
  font-size: .8rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .07em;
  color: var(--color-muted); margin-bottom: .5rem;
  display: flex; align-items: center; gap: .5rem;
}

.nutrition-table {
  width: 100%; border-collapse: collapse; font-size: .85rem;
}
.nutrition-table th {
  text-align: right; font-size: .72rem; font-weight: 600;
  color: var(--color-muted); padding: .25rem .5rem;
  border-bottom: 1px solid var(--color-border);
}
.nutrition-table th:first-child { text-align: left; }
.nutrition-table td {
  padding: .35rem .5rem; text-align: right;
  border-bottom: 1px solid var(--color-border);
}
.nutrition-table tr:last-child td { border-bottom: none; }
.nutrient-name { text-align: left; font-weight: 500; }
.nutrient-total { font-weight: 700; color: var(--color-accent); }
.nutrition-note { font-size: .72rem; color: var(--color-muted); margin-top: .4rem; }
.nutrition-empty { font-size: .82rem; color: var(--color-muted); }

/* Recettes */
.recipe-count {
  font-weight: 700; color: var(--color-text);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 99px; padding: .05rem .5rem;
  font-size: .72rem;
}
.recipe-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: .3rem; }
.recipe-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: .4rem .65rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: .85rem;
}
.recipe-item__name { font-weight: 500; }
.recipe-item__qty  { color: var(--color-muted); font-size: .78rem; }
.recipe-none { font-size: .82rem; color: var(--color-muted); }

.modal__actions {
  display: flex; justify-content: flex-end; gap: .5rem; padding-top: .25rem;
}
</style>
