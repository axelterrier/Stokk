<template>
  <div class="placeholder-view">
    <div class="placeholder-view__icon">🍽️</div>
    <h1 class="placeholder-view__title">Recettes</h1>
    <p class="placeholder-view__desc">Les suggestions de recettes basées sur votre stock arriveront ici.</p>
  </div>
</template>

<style scoped>
.placeholder-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  gap: 1rem;
  text-align: center;
  color: var(--color-muted);
}
.placeholder-view__icon  { font-size: 3rem; }
.placeholder-view__title { font-family: var(--font-display); font-size: 1.5rem; color: var(--color-text); }
.placeholder-view__desc  { font-size: .9rem; max-width: 380px; line-height: 1.6; }
</style>
