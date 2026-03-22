<script setup lang="ts">
import type { Product } from '@/types'
import NutriScore from './NutriScore.vue'

defineProps<{ product: Product; source?: string }>()
</script>

<template>
  <div class="product-card">
    <div class="product-card__media">
      <img
        v-if="product.image_url"
        :src="product.image_url"
        :alt="product.name"
        class="product-card__img"
      />
      <div v-else class="product-card__no-img">📦</div>
    </div>

    <div class="product-card__info">
      <div class="product-card__header">
        <div>
          <h2 class="product-card__name">{{ product.name }}</h2>
          <p v-if="product.brand" class="product-card__brand">{{ product.brand }}</p>
          <p v-if="product.category" class="product-card__category">{{ product.category }}</p>
        </div>
        <NutriScore :score="product.nutriscore" />
      </div>

      <div v-if="product.energy_kcal" class="product-card__nutrition">
        <span>🔥 {{ Math.round(product.energy_kcal) }} kcal</span>
        <span v-if="product.proteins_g">🥩 {{ product.proteins_g }}g prot.</span>
        <span v-if="product.carbs_g">🌾 {{ product.carbs_g }}g glucides</span>
        <span v-if="product.fat_g">🧈 {{ product.fat_g }}g lipides</span>
      </div>

      <p class="product-card__source">
        Source : <em>{{ source === 'cache' ? 'cache local' : 'OpenFoodFacts' }}</em>
      </p>
    </div>
  </div>
</template>

<style scoped>
.product-card {
  display: flex;
  gap: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  padding: 1rem;
  animation: fadeIn .25s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; } }

.product-card__media { flex-shrink: 0; }
.product-card__img { width: 80px; height: 80px; object-fit: contain; border-radius: 8px; background: var(--color-surface-2); }
.product-card__no-img { width: 80px; height: 80px; display: grid; place-items: center; font-size: 2rem; background: var(--color-surface-2); border-radius: 8px; }

.product-card__info { flex: 1; min-width: 0; }
.product-card__header { display: flex; justify-content: space-between; align-items: flex-start; gap: .5rem; margin-bottom: .5rem; }
.product-card__name { font-size: 1rem; font-weight: 600; margin: 0 0 .15rem; }
.product-card__brand { margin: 0; font-size: .8rem; color: var(--color-muted); }
.product-card__category { margin: 0; font-size: .75rem; color: var(--color-muted); font-style: italic; }

.product-card__nutrition {
  display: flex; flex-wrap: wrap; gap: .4rem .8rem;
  font-size: .78rem; color: var(--color-muted);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 6px; padding: .4rem .6rem;
  margin-top: .5rem;
}
.product-card__source { margin: .5rem 0 0; font-size: .72rem; color: var(--color-muted); }
</style>
