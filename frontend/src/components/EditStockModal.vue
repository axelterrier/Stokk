<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import type { StockItem, StockItemUpdate, Location } from '@/types'

const props = defineProps<{
  item: StockItem
  locations: Location[]
  loading: boolean
}>()

const emit = defineEmits<{
  submit: [payload: StockItemUpdate]
  delete: [id: string]
  close: []
}>()

const confirmDelete = ref(false)

const UNITS = ['unité', 'g', 'kg', 'ml', 'L', 'portion']

const form = reactive({
  quantity: props.item.quantity,
  unit: props.item.unit,
  location_id: props.item.location?.id ?? '',
  opened: props.item.opened,
  expiry_date: props.item.expiry_date?.expiry_date ?? '',
  alert_days_before: props.item.expiry_date?.alert_days_before ?? 3,
  clear_expiry: false,
})

watch(() => props.item, (item) => {
  form.quantity = item.quantity
  form.unit = item.unit
  form.location_id = item.location?.id ?? ''
  form.opened = item.opened
  form.expiry_date = item.expiry_date?.expiry_date ?? ''
  form.alert_days_before = item.expiry_date?.alert_days_before ?? 3
  form.clear_expiry = false
})

// Flat ordered location list with depth
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
  const payload: StockItemUpdate = {
    quantity: form.quantity,
    unit: form.unit,
    location_id: form.location_id || null,
    opened: form.opened,
    alert_days_before: form.alert_days_before,
  }

  if (form.clear_expiry) {
    payload.clear_expiry = true
  } else if (form.expiry_date) {
    payload.expiry_date = form.expiry_date
  }

  emit('submit', payload)
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal animate-slide-up">
      <header class="modal__header">
        <div class="modal__title-wrap">
          <span class="modal__icon">✏️</span>
          <h2 class="modal__title">Modifier l'article</h2>
        </div>
        <button class="modal__close btn btn--ghost" @click="emit('close')" title="Fermer">✕</button>
      </header>

      <p class="modal__product-name">{{ item.product.name }}</p>

      <div class="modal__grid">
        <!-- Quantité + Unité -->
        <div class="field modal__qty-unit">
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
            <option value="">— aucun —</option>
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
          <input
            v-model="form.expiry_date"
            type="date"
            class="input"
            :disabled="form.clear_expiry"
          />
        </div>

        <!-- Alerte -->
        <div class="field" v-if="form.expiry_date && !form.clear_expiry">
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

      <!-- Supprimer DLC -->
      <label v-if="item.expiry_date && !form.expiry_date" class="toggle-row toggle-row--danger">
        <input v-model="form.clear_expiry" type="checkbox" class="sr-only" />
        <span class="toggle toggle--danger" :class="{ 'toggle--on toggle--danger-on': form.clear_expiry }"></span>
        <span>Supprimer la date de péremption</span>
      </label>

      <div class="modal__actions">
        <button
          v-if="!confirmDelete"
          class="btn btn--danger modal__delete"
          :disabled="loading"
          @click="confirmDelete = true"
        >
          Supprimer
        </button>
        <div v-else class="modal__confirm">
          <span class="modal__confirm-label">Confirmer ?</span>
          <button class="btn btn--danger" :disabled="loading" @click="emit('delete', item.id)">Oui</button>
          <button class="btn btn--ghost" @click="confirmDelete = false">Non</button>
        </div>

        <div class="modal__actions-right">
          <button class="btn btn--ghost" :disabled="loading" @click="emit('close')">Annuler</button>
          <button class="btn btn--primary" :disabled="loading" @click="onSubmit">
            <span v-if="loading">Enregistrement…</span>
            <span v-else>✓ Enregistrer</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .35);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

@media (min-width: 480px) {
  .modal-backdrop { align-items: center; }
}

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  padding: 1.5rem;
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: .9rem;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal__title-wrap { display: flex; align-items: center; gap: .5rem; }
.modal__title { font-size: 1.05rem; font-weight: 700; }
.modal__close { padding: .3rem .55rem; font-size: .8rem; }
.modal__product-name {
  font-size: .85rem;
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: -.4rem;
}

.modal__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .75rem;
}
@media (max-width: 480px) {
  .modal__grid { grid-template-columns: 1fr; }
}

.qty-unit-wrap { display: flex; gap: .4rem; }
.qty-input { flex: 1; min-width: 0; }
.unit-select { width: 90px; flex-shrink: 0; }

.range-input { width: 100%; accent-color: var(--color-accent); cursor: pointer; }

.toggle-row {
  display: flex;
  align-items: center;
  gap: .6rem;
  cursor: pointer;
  font-size: .875rem;
  color: var(--color-muted);
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
.toggle--danger-on { background: var(--color-danger); }

.modal__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: .5rem;
  margin-top: .25rem;
}
.modal__actions-right { display: flex; gap: .5rem; margin-left: auto; }
.modal__delete { padding: .55rem .85rem; }
.modal__confirm { display: flex; align-items: center; gap: .4rem; flex-wrap: wrap; }
.modal__confirm-label { font-size: .8rem; color: var(--color-danger); font-weight: 600; }
</style>
