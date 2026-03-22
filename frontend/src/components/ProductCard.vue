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
      <div class="product-card__top">
        <div class="product-card__text">
          <h2 class="product-card__name">{{ product.name }}</h2>
          <p v-if="product.brand" class="product-card__brand">{{ product.brand }}</p>
        </div>
        <NutriScore :score="product.nutriscore" />
      </div>

      <p v-if="product.category" class="product-card__category">{{ product.category }}</p>

      <div v-if="product.energy_kcal" class="product-card__nutrition">
        <span>🔥 {{ Math.round(product.energy_kcal) }} kcal</span>
        <span v-if="product.proteins_g">{{ product.proteins_g }}g prot.</span>
        <span v-if="product.carbs_g">{{ product.carbs_g }}g glucides</span>
        <span v-if="product.fat_g">{{ product.fat_g }}g lipides</span>
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
  gap: .875rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  padding: 1rem;
  animation: fadeIn .2s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }

.product-card__media { flex-shrink: 0; }
.product-card__img    { width: 72px; height: 72px; object-fit: contain; border-radius: 8px; background: var(--color-surface-2); display: block; }
.product-card__no-img { width: 72px; height: 72px; display: grid; place-items: center; font-size: 2rem; background: var(--color-surface-2); border-radius: 8px; }

.product-card__info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: .4rem; }

.product-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: .5rem;
}
.product-card__text { flex: 1; min-width: 0; }
.product-card__name  { font-size: .95rem; font-weight: 700; line-height: 1.3; }
.product-card__brand { font-size: .78rem; color: var(--color-muted); margin-top: .1rem; }

.product-card__category {
  font-size: .72rem;
  color: var(--color-muted);
  font-style: italic;
  /* Tronquer les longues catégories OpenFoodFacts */
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.product-card__nutrition {
  display: flex;
  flex-wrap: wrap;
  gap: .3rem .75rem;
  font-size: .75rem;
  color: var(--color-muted);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: .35rem .6rem;
}

.product-card__source { font-size: .7rem; color: var(--color-muted); }
</style>
