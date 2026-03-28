<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Recipe, StockItem } from '@/types'

const props = defineProps<{
  recipe: Recipe
  stockItems: StockItem[]
}>()

const emit = defineEmits<{
  edit: [recipe: Recipe]
  delete: [id: string]
}>()

const confirmDelete = ref(false)

// ── Stock status ─────────────────────────────────────────────────────────────

function stockTotal(barcode: string | null | undefined): number {
  if (!barcode) return 0
  return props.stockItems
    .filter(s => s.product_barcode === barcode)
    .reduce((acc, s) => acc + s.quantity, 0)
}

type IngStatus = 'ok' | 'partial' | 'out' | 'unlinked'

function ingredientStatus(barcode: string | null | undefined, required: number): IngStatus {
  if (!barcode) return 'unlinked'
  const avail = stockTotal(barcode)
  if (avail <= 0) return 'out'
  if (avail < required) return 'partial'
  return 'ok'
}

const overallStatus = computed<'ready' | 'partial' | 'missing'>(() => {
  const linked = props.recipe.ingredients.filter(i => i.product_barcode)
  if (linked.length === 0) return 'ready'
  const statuses = linked.map(i => ingredientStatus(i.product_barcode, i.quantity))
  if (statuses.every(s => s === 'ok')) return 'ready'
  if (statuses.some(s => s === 'ok' || s === 'partial')) return 'partial'
  return 'missing'
})

const statusInfo: Record<string, { label: string; cls: string }> = {
  ready:   { label: '✓ Tous en stock', cls: 'status--ready' },
  partial: { label: '⚠ Stock partiel', cls: 'status--partial' },
  missing: { label: '✕ Ingrédients manquants', cls: 'status--missing' },
}

const ingStatusIcon: Record<IngStatus, string> = { ok: '✓', partial: '⚠', out: '✕', unlinked: '—' }
const ingStatusClass: Record<IngStatus, string> = {
  ok: 'ing-icon--ok', partial: 'ing-icon--partial', out: 'ing-icon--out', unlinked: 'ing-icon--unlinked',
}

// ── Nutritional aggregation ───────────────────────────────────────────────────

// Convert quantity to grams/ml for nutritional calculation (per 100g basis)
function toBaseUnit(qty: number, unit: string): number | null {
  switch (unit) {
    case 'g':   return qty
    case 'kg':  return qty * 1000
    case 'ml':  return qty
    case 'cl':  return qty * 10
    case 'L':   return qty * 1000
    default:    return null  // unité, portion → incalculable
  }
}

interface NutritionSummary {
  kcal: number
  proteins: number
  carbs: number
  fat: number
  hasData: boolean
}

const nutrition = computed<NutritionSummary>(() => {
  let kcal = 0, proteins = 0, carbs = 0, fat = 0, hasData = false

  for (const ing of props.recipe.ingredients) {
    const product = ing.product
    if (!product) continue
    const baseQty = toBaseUnit(ing.quantity, ing.unit)
    if (baseQty === null) continue

    const factor = baseQty / 100
    if (product.energy_kcal != null) { kcal += product.energy_kcal * factor; hasData = true }
    if (product.proteins_g != null)  { proteins += product.proteins_g * factor; hasData = true }
    if (product.carbs_g != null)     { carbs += product.carbs_g * factor; hasData = true }
    if (product.fat_g != null)       { fat += product.fat_g * factor; hasData = true }
  }

  return { kcal: Math.round(kcal), proteins: Math.round(proteins * 10) / 10, carbs: Math.round(carbs * 10) / 10, fat: Math.round(fat * 10) / 10, hasData }
})

// ── Nutriscore (worst grade among linked ingredients) ─────────────────────────

const GRADE_ORDER = ['A', 'B', 'C', 'D', 'E']

const worstNutriscore = computed<string | null>(() => {
  const grades = props.recipe.ingredients
    .map(i => i.product?.nutriscore?.toUpperCase())
    .filter((g): g is string => !!g && GRADE_ORDER.includes(g))

  if (grades.length === 0) return null
  return grades.reduce((worst, g) =>
    GRADE_ORDER.indexOf(g) > GRADE_ORDER.indexOf(worst) ? g : worst
  )
})

const nutriscoreClass: Record<string, string> = {
  A: 'ns--a', B: 'ns--b', C: 'ns--c', D: 'ns--d', E: 'ns--e',
}
</script>

<template>
  <div class="recipe-card card">
    <!-- Header -->
    <div class="recipe-card__top">
      <div class="recipe-card__meta">
        <div class="recipe-card__title-row">
          <h3 class="recipe-card__name">{{ recipe.name }}</h3>
          <span v-if="worstNutriscore" class="nutriscore-badge" :class="nutriscoreClass[worstNutriscore]">
            {{ worstNutriscore }}
          </span>
        </div>
        <p v-if="recipe.description" class="recipe-card__desc">{{ recipe.description }}</p>
      </div>
      <span class="recipe-status" :class="statusInfo[overallStatus].cls">
        {{ statusInfo[overallStatus].label }}
      </span>
    </div>

    <!-- Ingrédients -->
    <ul class="recipe-card__ings" v-if="recipe.ingredients.length > 0">
      <li v-for="ing in recipe.ingredients" :key="ing.id" class="ing-line">
        <span class="ing-icon" :class="ingStatusClass[ingredientStatus(ing.product_barcode, ing.quantity)]">
          {{ ingStatusIcon[ingredientStatus(ing.product_barcode, ing.quantity)] }}
        </span>
        <span class="ing-name">{{ ing.ingredient_name }}</span>
        <span class="ing-qty">{{ ing.quantity }} {{ ing.unit }}</span>
        <span v-if="ing.product_barcode" class="ing-avail">
          / stock: {{ stockTotal(ing.product_barcode) }}
        </span>
        <span v-if="ing.product?.nutriscore" class="ing-ns" :class="nutriscoreClass[ing.product.nutriscore.toUpperCase()]">
          {{ ing.product.nutriscore.toUpperCase() }}
        </span>
      </li>
    </ul>
    <p v-else class="recipe-card__empty">Aucun ingrédient renseigné.</p>

    <!-- Résumé nutritionnel -->
    <div v-if="nutrition.hasData" class="nutrition-row">
      <span class="nutrition-label">Pour cette recette :</span>
      <span class="nutrition-chip">🔥 {{ nutrition.kcal }} kcal</span>
      <span class="nutrition-chip">🥩 {{ nutrition.proteins }}g prot.</span>
      <span class="nutrition-chip">🌾 {{ nutrition.carbs }}g gluc.</span>
      <span class="nutrition-chip">🧈 {{ nutrition.fat }}g lip.</span>
    </div>

    <!-- Actions -->
    <div class="recipe-card__actions">
      <div v-if="confirmDelete" class="confirm-row">
        <span class="confirm-label">Supprimer ?</span>
        <button class="btn btn--danger btn--sm" @click="emit('delete', recipe.id)">Oui</button>
        <button class="btn btn--ghost btn--sm" @click="confirmDelete = false">Non</button>
      </div>
      <template v-else>
        <button class="btn btn--danger btn--sm" @click="confirmDelete = true">Supprimer</button>
        <button class="btn btn--ghost btn--sm" @click="emit('edit', recipe)">Modifier</button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.recipe-card { display: flex; flex-direction: column; gap: .75rem; }

.recipe-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: .75rem;
  flex-wrap: wrap;
}

.recipe-card__title-row { display: flex; align-items: center; gap: .5rem; }
.recipe-card__name { font-size: 1rem; font-weight: 700; margin: 0; }
.recipe-card__desc { font-size: .8rem; color: var(--color-muted); margin: .2rem 0 0; }

.recipe-status {
  font-size: .7rem; font-weight: 600;
  padding: .2rem .6rem; border-radius: 999px; border: 1px solid;
  white-space: nowrap; flex-shrink: 0;
}
.status--ready   { background: #dcfce7; color: #15803d; border-color: #86efac; }
.status--partial { background: #fef9c3; color: #854d0e; border-color: #fde047; }
.status--missing { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

/* Nutriscore badge */
.nutriscore-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 5px;
  font-family: var(--font-display); font-weight: 800; font-size: .75rem; color: #fff;
}
.ns--a { background: #038141; }
.ns--b { background: #85bb2f; }
.ns--c { background: #fecb02; color: #1c1917; }
.ns--d { background: #ee8100; }
.ns--e { background: #e63e11; }

.recipe-card__ings { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: .3rem; }

.ing-line { display: flex; align-items: center; gap: .4rem; font-size: .85rem; }
.ing-icon { font-size: .7rem; font-weight: 700; width: 16px; text-align: center; flex-shrink: 0; }
.ing-icon--ok      { color: #16a34a; }
.ing-icon--partial { color: #ca8a04; }
.ing-icon--out     { color: #dc2626; }
.ing-icon--unlinked { color: var(--color-muted); }
.ing-name  { flex: 1; font-weight: 500; }
.ing-qty   { color: var(--color-muted); white-space: nowrap; }
.ing-avail { font-size: .75rem; color: var(--color-muted); }
.ing-ns {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; border-radius: 3px;
  font-size: .6rem; font-weight: 800; color: #fff; flex-shrink: 0;
}

/* Nutrition summary */
.nutrition-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .4rem;
  padding: .6rem .75rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: .8rem;
}
.nutrition-label { color: var(--color-muted); font-weight: 600; margin-right: .2rem; }
.nutrition-chip {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: .15rem .55rem;
  white-space: nowrap;
}

.recipe-card__empty { font-size: .8rem; color: var(--color-muted); }

.recipe-card__actions {
  display: flex; align-items: center; justify-content: flex-end;
  gap: .4rem; flex-wrap: wrap;
  padding-top: .25rem;
  border-top: 1px solid var(--color-border);
}
.btn--sm { padding: .3rem .65rem; font-size: .8rem; }
.confirm-row { display: flex; align-items: center; gap: .4rem; flex-wrap: wrap; width: 100%; justify-content: flex-end; }
.confirm-label { font-size: .8rem; color: var(--color-danger); font-weight: 600; }
</style>
