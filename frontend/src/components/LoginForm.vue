<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/composables/useApi'

const emit = defineEmits<{ success: [] }>()

const username = ref('')
const password = ref('')
const loading  = ref(false)
const error    = ref<string | null>(null)

async function onSubmit() {
  if (!username.value || !password.value) return
  loading.value = true
  error.value   = null
  try {
    await api.login(username.value, password.value)
    emit('success')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="login-header">
        <span class="login-icon">🥫</span>
        <h1 class="login-title">Stokk</h1>
        <p class="login-sub">Connectez-vous pour accéder à votre stock</p>
      </div>

      <form class="login-form" @submit.prevent="onSubmit">
        <div class="field">
          <label class="label" for="username">Nom d'utilisateur</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="input"
            autocomplete="username"
            :disabled="loading"
            required
          />
        </div>

        <div class="field">
          <label class="label" for="password">Mot de passe</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="input"
            autocomplete="current-password"
            :disabled="loading"
            required
          />
        </div>

        <div v-if="error" class="login-error">{{ error }}</div>

        <button type="submit" class="btn btn--primary login-btn" :disabled="loading">
          <span v-if="loading">Connexion…</span>
          <span v-else>Se connecter</span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: var(--color-bg);
}

.login-card {
  width: 100%;
  max-width: 380px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 2rem 1.75rem;
  box-shadow: var(--shadow-sm);
}

.login-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.login-icon { font-size: 2.5rem; }

.login-title {
  font-family: var(--font-display);
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -.03em;
  color: var(--color-accent);
  margin: .35rem 0 .25rem;
}

.login-sub {
  font-size: .825rem;
  color: var(--color-muted);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-error {
  font-size: .825rem;
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius);
  padding: .5rem .75rem;
}

.login-btn { width: 100%; justify-content: center; margin-top: .25rem; }
</style>
