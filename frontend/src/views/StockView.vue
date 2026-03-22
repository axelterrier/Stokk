<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Product, StockItem, StockItemCreate, StockItemUpdate } from '@/types'
import { api } from '@/composables/useApi'
import ScanInput from '@/components/ScanInput.vue'
import ProductCard from '@/components/ProductCard.vue'
import AddStockForm from '@/components/AddStockForm.vue'
import StockList from '@/components/StockList.vue'
import EditStockModal from '@/components/EditStockModal.vue'
import ExpiryDashboard from '@/components/ExpiryDashboard.vue'

const scanLoading  = ref(false)
const addLoading   = ref(false)
const stockLoading = ref(false)

const scannedProduct = ref<Product | null>(null)
const scanSource     = ref<string | undefined>()
const scanError      = ref<string | null>(null)
const addSuccess     = ref(false)

const stockItems  = ref<StockItem[]>([])
const editingItem = ref<StockItem | null>(null)
const editLoading = ref(false)

async function onScan(barcode: string) {
  scanLoading.value    = true
  scanError.value      = null
  scannedProduct.value = null
  addSuccess.value     = false
  try {
    const result = await api.scan(barcode)
    if (!result.found || !result.product) {
      scanError.value = `Produit introuvable pour le code "${barcode}".`
      return
    }
    scannedProduct.value = result.product
    scanSource.value     = result.source
  } catch (e: unknown) {
    scanError.value = e instanceof Error ? e.message : 'Erreur lors du scan.'
  } finally {
    scanLoading.value = false
  }
}

async function onAddStock(payload: StockItemCreate) {
  addLoading.value = true
  try {
    await api.addStock(payload)
    addSuccess.value     = true
    scannedProduct.value = null
    await loadStock()
  } catch (e: unknown) {
    scanError.value = e instanceof Error ? e.message : "Erreur lors de l'ajout."
  } finally {
    addLoading.value = false
  }
}

function onCancelAdd() {
  scannedProduct.value = null
  scanError.value      = null
}

async function loadStock() {
  stockLoading.value = true
  try {
    stockItems.value = await api.listStock()
  } catch {
    // silencieux
  } finally {
    stockLoading.value = false
  }
}

function onEdit(item: StockItem) { editingItem.value = item }

async function onUpdateStock(payload: StockItemUpdate) {
  if (!editingItem.value) return
  editLoading.value = true
  try {
    const updated = await api.updateStock(editingItem.value.id, payload)
    stockItems.value  = stockItems.value.map(i => i.id === updated.id ? updated : i)
    editingItem.value = null
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : "Erreur lors de la mise à jour.")
  } finally {
    editLoading.value = false
  }
}

async function onDelete(id: string) {
  try {
    await api.deleteStock(id)
    stockItems.value = stockItems.value.filter(i => i.id !== id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur suppression.')
  }
}

onMounted(loadStock)
</script>

<template>
  <div class="stock-layout">

    <!-- Colonne gauche : scanner -->
    <div class="stock-col stock-col--scan">

      <section class="section">
        <h2 class="section__title">Scanner un produit</h2>
        <ScanInput :loading="scanLoading" @scan="onScan" />

        <div v-if="scanLoading" class="scan-feedback scan-feedback--loading">
          <span class="spinner"></span> Recherche en cours…
        </div>
        <div v-else-if="scanError" class="scan-feedback scan-feedback--error">
          ⚠️ {{ scanError }}
        </div>
        <div v-else-if="addSuccess" class="scan-feedback scan-feedback--success">
          ✓ Produit ajouté au stock avec succès.
        </div>
      </section>

      <section v-if="scannedProduct" class="section animate-slide-up">
        <ProductCard :product="scannedProduct" :source="scanSource" />
        <hr class="divider" />
        <AddStockForm
          :product="scannedProduct"
          :loading="addLoading"
          @submit="onAddStock"
          @cancel="onCancelAdd"
        />
      </section>

    </div>

    <!-- Colonne droite : tableau de bord + stock -->
    <div class="stock-col stock-col--content">
      <ExpiryDashboard :items="stockItems" @edit="onEdit" />
      <StockList
        :items="stockItems"
        :loading="stockLoading"
        @edit="onEdit"
        @delete="onDelete"
      />
    </div>

  </div>

  <EditStockModal
    v-if="editingItem"
    :item="editingItem"
    :loading="editLoading"
    @submit="onUpdateStock"
    @delete="onDelete($event); editingItem = null"
    @close="editingItem = null"
  />
</template>

<style scoped>
.stock-layout {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.stock-col { display: flex; flex-direction: column; gap: 1.25rem; }

@media (min-width: 1024px) {
  .stock-layout {
    display: grid;
    grid-template-columns: 360px 1fr;
    align-items: start;
    gap: 1.5rem 2rem;
  }
  .stock-col--scan {
    position: sticky;
    top: calc(var(--header-h) + 1.5rem);
    max-height: calc(100vh - var(--header-h) - 3rem);
    overflow-y: auto;
    scrollbar-width: none;
  }
  .stock-col--scan::-webkit-scrollbar { display: none; }
}

.section { display: flex; flex-direction: column; gap: .75rem; }
.section__title {
  font-family: var(--font-display);
  font-size: .75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--color-muted);
}

.scan-feedback {
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: .875rem;
  padding: .6rem .9rem;
  border-radius: var(--radius);
}
.scan-feedback--loading { color: var(--color-muted); background: var(--color-surface-2); border: 1px solid var(--color-border); }
.scan-feedback--error   { color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; }
.scan-feedback--success { color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; }

.spinner {
  width: 14px; height: 14px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin .7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
