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

// ── State ─────────────────────────────────────────────────────────
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

// ── Scan ──────────────────────────────────────────────────────────
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

// ── Add to stock ──────────────────────────────────────────────────
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

// ── Stock list ────────────────────────────────────────────────────
async function loadStock() {
  stockLoading.value = true
  try {
    stockItems.value = await api.listStock()
  } catch {
    // silencieux pour le POC
  } finally {
    stockLoading.value = false
  }
}

function onEdit(item: StockItem) {
  editingItem.value = item
}

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
  <div class="app-shell">

    <!-- ── Header ── -->
    <header class="app-header">
      <div class="app-header__inner">
        <div class="app-header__logo">
          <span class="app-header__icon">🥫</span>
          <span class="app-header__wordmark">FoodTracker</span>
        </div>
        <span class="app-header__sub">Gestion de stock alimentaire</span>
      </div>
    </header>

    <main class="app-main">

      <!-- ── Colonne gauche : scanner ── -->
      <div class="app-col app-col--scan">

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

      <!-- ── Colonne droite : tableau de bord + stock ── -->
      <div class="app-col app-col--content">

        <ExpiryDashboard :items="stockItems" @edit="onEdit" />

        <StockList
          :items="stockItems"
          :loading="stockLoading"
          @edit="onEdit"
          @delete="onDelete"
        />

      </div>

    </main>

    <!-- ── Modal édition ── -->
    <EditStockModal
      v-if="editingItem"
      :item="editingItem"
      :loading="editLoading"
      @submit="onUpdateStock"
      @delete="onDelete($event); editingItem = null"
      @close="editingItem = null"
    />

  </div>
</template>

<style>
/* ── Shell ────────────────────────────────────────────────────── */
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Header ───────────────────────────────────────────────────── */
.app-header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.app-header__inner {
  max-width: 800px;
  margin: 0 auto;
  padding: .8rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.app-header__logo    { display: flex; align-items: center; gap: .5rem; }
.app-header__icon    { font-size: 1.3rem; }
.app-header__wordmark {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -.03em;
  color: var(--color-accent);
}
.app-header__sub { font-size: .75rem; color: var(--color-muted); }

/* ── Layout principal ─────────────────────────────────────────── */
.app-main {
  flex: 1;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 1.25rem 1rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.app-col {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* PC : 2 colonnes */
@media (min-width: 1024px) {
  .app-header__inner {
    max-width: 1320px;
    padding: .8rem 2rem;
  }
  .app-main {
    max-width: 1320px;
    display: grid;
    grid-template-columns: 360px 1fr;
    align-items: start;
    gap: 1.5rem 2rem;
    padding: 1.5rem 2rem 3rem;
  }
  .app-col--scan {
    position: sticky;
    top: 4.5rem; /* hauteur header */
    max-height: calc(100vh - 5.5rem);
    overflow-y: auto;
    scrollbar-width: none;
  }
  .app-col--scan::-webkit-scrollbar { display: none; }
}

/* ── Section ──────────────────────────────────────────────────── */
.section { display: flex; flex-direction: column; gap: .75rem; }
.section__title {
  font-family: var(--font-display);
  font-size: .75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--color-muted);
}

/* ── Feedbacks scan ───────────────────────────────────────────── */
.scan-feedback {
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: .875rem;
  padding: .6rem .9rem;
  border-radius: var(--radius);
  animation: slideUp .2s ease;
}
.scan-feedback--loading { color: var(--color-muted); background: var(--color-surface-2); border: 1px solid var(--color-border); }
.scan-feedback--error   { color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; }
.scan-feedback--success { color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; }

/* ── Spinner ──────────────────────────────────────────────────── */
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
