<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/composables/useApi'
import type { Recipe, RecipeCreate, StockItem } from '@/types'
import RecipeCard from '@/components/RecipeCard.vue'
import RecipeForm from '@/components/RecipeForm.vue'

const recipes = ref<Recipe[]>([])
const stockItems = ref<StockItem[]>([])
const loadingRecipes = ref(false)
const formOpen = ref(false)
const editingRecipe = ref<Recipe | null>(null)
const formLoading = ref(false)
const error = ref<string | null>(null)

async function loadAll() {
  loadingRecipes.value = true
  try {
    ;[recipes.value, stockItems.value] = await Promise.all([
      api.listRecipes(),
      api.listStock(),
    ])
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur de chargement'
  } finally {
    loadingRecipes.value = false
  }
}

onMounted(loadAll)

function openCreate() {
  editingRecipe.value = null
  formOpen.value = true
}

function openEdit(recipe: Recipe) {
  editingRecipe.value = recipe
  formOpen.value = true
}

async function onFormSubmit(payload: RecipeCreate) {
  formLoading.value = true
  error.value = null
  try {
    if (editingRecipe.value) {
      const updated = await api.updateRecipe(editingRecipe.value.id, payload)
      const idx = recipes.value.findIndex(r => r.id === updated.id)
      if (idx !== -1) recipes.value[idx] = updated
    } else {
      const created = await api.createRecipe(payload)
      recipes.value.unshift(created)
    }
    formOpen.value = false
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la sauvegarde'
  } finally {
    formLoading.value = false
  }
}

async function onDelete(id: string) {
  error.value = null
  try {
    await api.deleteRecipe(id)
    recipes.value = recipes.value.filter(r => r.id !== id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la suppression'
  }
}
</script>

<template>
  <div class="recipes-view">
    <div class="recipes-view__header">
      <h1 class="recipes-view__title">Recettes</h1>
      <button class="btn btn--primary" @click="openCreate">+ Nouvelle recette</button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loadingRecipes" class="loading">Chargement…</div>

    <div v-else-if="recipes.length === 0 && !loadingRecipes" class="empty-state">
      <div class="empty-state__icon">📋</div>
      <p class="empty-state__text">Aucune recette enregistrée.</p>
      <button class="btn btn--primary" @click="openCreate">Créer ma première recette</button>
    </div>

    <div v-else class="recipes-grid">
      <RecipeCard
        v-for="recipe in recipes"
        :key="recipe.id"
        :recipe="recipe"
        :stockItems="stockItems"
        @edit="openEdit"
        @delete="onDelete"
      />
    </div>

    <RecipeForm
      v-if="formOpen"
      :recipe="editingRecipe"
      :stockItems="stockItems"
      :loading="formLoading"
      @submit="onFormSubmit"
      @close="formOpen = false"
    />
  </div>
</template>

<style scoped>
.recipes-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.recipes-view__header {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: .75rem;
}
.recipes-view__title { font-size: 1.4rem; font-weight: 700; }
.error-banner {
  background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5;
  border-radius: var(--radius); padding: .65rem 1rem; font-size: .875rem;
}
.loading { color: var(--color-muted); font-size: .9rem; text-align: center; padding: 2rem; }
.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: 1rem;
  padding: 3rem 1rem; color: var(--color-muted); text-align: center;
}
.empty-state__icon { font-size: 2.5rem; }
.empty-state__text { font-size: .9rem; }
.recipes-grid { display: flex; flex-direction: column; gap: 1rem; }
</style>
