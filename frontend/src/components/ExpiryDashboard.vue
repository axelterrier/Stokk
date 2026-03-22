<script setup lang="ts">
import { computed } from 'vue'
import type { StockItem } from '@/types'
import NutriScore from './NutriScore.vue'

const props = defineProps<{ items: StockItem[] }>()

const emit = defineEmits<{ edit: [item: StockItem] }>()

const THRESHOLD_DAYS = 7

function daysUntil(dateStr: string): number {
  return Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86_400_000)
}

const urgentItems = computed(() =>
  props.items
    .filter(i => i.expiry_date && daysUntil(i.expiry_date.expiry_date) <= THRESHOLD_DAYS)
    .sort((a, b) => daysUntil(a.expiry_date!.expiry_date) - daysUntil(b.expiry_date!.expiry_date))
)

const expiredCount = computed(() => urgentItems.value.filter(i => daysUntil(i.expiry_date!.expiry_date) < 0).length)
const urgentCount  = computed(() => urgentItems.value.filter(i => { const d = daysUntil(i.expiry_date!.expiry_date); return d >= 0 && d <= 3 }).length)
const soonCount    = computed(() => urgentItems.value.length - expiredCount.value - urgentCount.value)

function expiryClass(dateStr: string): string {
  const d = daysUntil(dateStr)
  if (d < 0)  return 'badge--expired'
  if (d <= 3) return 'badge--urgent'
  return 'badge--soon'
}

function expiryLabel(dateStr: string): string {
  const d = daysUntil(dateStr)
  if (d < 0)  return `Expiré il y a ${Math.abs(d)}j`
  if (d === 0) return "Expire aujourd'hui !"
  if (d === 1) return 'Expire demain'
  return `Dans ${d} jours`
}
</script>

<template>
  <section class="dashboard">

    <!-- En-tête -->
    <header class="dashboard__header">
      <h2 class="dashboard__title">À consommer en priorité</h2>
      <div v-if="urgentItems.length" class="dashboard__pills">
        <span v-if="expiredCount" class="pill pill--expired">{{ expiredCount }} expiré{{ expiredCount > 1 ? 's' : '' }}</span>
        <span v-if="urgentCount"  class="pill pill--urgent">{{ urgentCount }} urgent{{ urgentCount > 1 ? 's' : '' }}</span>
        <span v-if="soonCount"    class="pill pill--soon">{{ soonCount }} bientôt</span>
      </div>
    </header>

    <!-- Tout va bien -->
    <div v-if="!urgentItems.length" class="dashboard__ok">
      <span>✓</span>
      <span>Rien à consommer en urgence — votre stock est sain.</span>
    </div>

    <!-- Cartes urgentes -->
    <div v-else class="dashboard__grid">
      <article
        v-for="item in urgentItems"
        :key="item.id"
        class="expiry-card"
        @click="emit('edit', item)"
        title="Modifier"
      >
        <div class="expiry-card__img-wrap">
          <img v-if="item.product.image_url" :src="item.product.image_url"
            :alt="item.product.name" class="expiry-card__img" />
          <span v-else class="expiry-card__no-img">📦</span>
        </div>

        <div class="expiry-card__body">
          <div class="expiry-card__top">
            <p class="expiry-card__name">{{ item.product.name }}</p>
            <NutriScore :score="item.product.nutriscore" />
          </div>
          <div class="expiry-card__meta">
            <span>{{ item.quantity }} {{ item.unit }}</span>
            <span v-if="item.location">· {{ item.location?.name }}</span>
            <span v-if="item.opened" class="expiry-card__opened">Ouvert</span>
          </div>
          <span class="expiry-badge" :class="expiryClass(item.expiry_date!.expiry_date)">
            {{ expiryLabel(item.expiry_date!.expiry_date) }}
          </span>
        </div>
      </article>
    </div>

  </section>
</template>

<style scoped>
/* ── Conteneur ───────────────────────────────────────────────── */
.dashboard {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: .85rem;
}

/* ── En-tête ─────────────────────────────────────────────────── */
.dashboard__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .75rem;
  flex-wrap: wrap;
}
.dashboard__title { font-size: .95rem; font-weight: 700; }
.dashboard__pills { display: flex; gap: .35rem; flex-wrap: wrap; }

.pill {
  font-size: .7rem; font-weight: 600;
  padding: .15rem .55rem; border-radius: 99px;
}
.pill--expired { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.pill--urgent  { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.pill--soon    { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }

/* ── État vide ───────────────────────────────────────────────── */
.dashboard__ok {
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: .85rem;
  color: var(--color-success);
  padding: .15rem 0;
}

/* ── Grille de cartes ────────────────────────────────────────── */
.dashboard__grid {
  display: flex;
  gap: .6rem;
  overflow-x: auto;
  padding-bottom: .25rem;
  scrollbar-width: none;
}
.dashboard__grid::-webkit-scrollbar { display: none; }

@media (min-width: 1024px) {
  .dashboard__grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
    overflow-x: visible;
    padding-bottom: 0;
  }
}

/* ── Carte individuelle ──────────────────────────────────────── */
.expiry-card {
  flex-shrink: 0;
  width: 190px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: .75rem;
  display: flex;
  flex-direction: column;
  gap: .5rem;
  cursor: pointer;
  transition: box-shadow var(--transition), border-color var(--transition);
}
.expiry-card:hover { box-shadow: var(--shadow-md); border-color: #d6d3d1; }

@media (min-width: 1024px) { .expiry-card { width: auto; } }

/* Image */
.expiry-card__img-wrap { display: flex; justify-content: center; }
.expiry-card__img    { width: 52px; height: 52px; object-fit: contain; border-radius: 8px; background: var(--color-surface); }
.expiry-card__no-img { width: 52px; height: 52px; display: grid; place-items: center; font-size: 1.6rem; background: var(--color-surface); border-radius: 8px; }

/* Corps */
.expiry-card__body { display: flex; flex-direction: column; gap: .3rem; }
.expiry-card__top  { display: flex; align-items: flex-start; justify-content: space-between; gap: .3rem; }
.expiry-card__name {
  font-size: .8rem; font-weight: 600; line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.expiry-card__meta {
  display: flex; flex-wrap: wrap; gap: .2rem .3rem;
  font-size: .72rem; color: var(--color-muted);
}
.expiry-card__opened {
  font-size: .68rem; padding: .05rem .3rem;
  background: #fff7ed; color: #c2410c;
  border: 1px solid #fed7aa; border-radius: 4px;
}

/* Badge DLC */
.expiry-badge {
  display: inline-block;
  font-size: .7rem; font-weight: 700;
  padding: .2rem .55rem; border-radius: 6px;
  width: fit-content;
}
.badge--expired { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.badge--urgent  { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.badge--soon    { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
</style>
