<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { AppUser, UserCreate, UserUpdate } from '@/types'
import { api } from '@/composables/useApi'
import { useAuth } from '@/composables/useAuth'

import { useRouter } from 'vue-router'

const router    = useRouter()
const { user: me } = useAuth()

// Redirection si non-admin
if (me.value && !me.value.is_admin) router.replace('/')

const users     = ref<AppUser[]>([])
const loading   = ref(false)
const error     = ref<string | null>(null)

// ── Création ──
const showForm    = ref(false)
const createError = ref<string | null>(null)
const creating    = ref(false)
const form = ref<UserCreate>({ username: '', email: '', password: '', is_admin: false })

// ── Mot de passe ──
const editingPasswordId = ref<string | null>(null)
const newPassword       = ref('')
const passwordError     = ref<string | null>(null)
const savingPassword    = ref(false)

// ── Suppression ──
const confirmDeleteId = ref<string | null>(null)
const deleting        = ref(false)

async function load() {
  loading.value = true
  error.value   = null
  try {
    users.value = await api.listUsers()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur chargement'
  } finally {
    loading.value = false
  }
}

async function onCreateUser() {
  creating.value    = true
  createError.value = null
  try {
    const created = await api.createUser(form.value)
    users.value.push(created)
    showForm.value = false
    form.value = { username: '', email: '', password: '', is_admin: false }
  } catch (e: unknown) {
    createError.value = e instanceof Error ? e.message : 'Erreur création'
  } finally {
    creating.value = false
  }
}

async function toggleAdmin(user: AppUser) {
  try {
    const updated = await api.updateUser(user.id, { is_admin: !user.is_admin })
    users.value = users.value.map(u => u.id === updated.id ? updated : u)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur')
  }
}

async function savePassword(userId: string) {
  if (!newPassword.value.trim()) { passwordError.value = 'Mot de passe vide'; return }
  savingPassword.value = true
  passwordError.value  = null
  try {
    await api.updateUser(userId, { password: newPassword.value })
    editingPasswordId.value = null
    newPassword.value = ''
  } catch (e: unknown) {
    passwordError.value = e instanceof Error ? e.message : 'Erreur'
  } finally {
    savingPassword.value = false
  }
}

async function deleteUser(userId: string) {
  deleting.value = true
  try {
    await api.deleteUser(userId)
    users.value = users.value.filter(u => u.id !== userId)
    confirmDeleteId.value = null
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur suppression')
  } finally {
    deleting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="users-view">

    <!-- En-tête -->
    <div class="view-header">
      <div>
        <h1 class="view-title">Utilisateurs</h1>
        <p class="view-subtitle">Gérez les membres qui ont accès à Stokk.</p>
      </div>
      <button class="btn btn--primary" @click="showForm = !showForm">
        {{ showForm ? 'Annuler' : '+ Ajouter' }}
      </button>
    </div>

    <!-- Formulaire de création -->
    <div v-if="showForm" class="card create-form animate-slide-up">
      <h2 class="form-title">Nouvel utilisateur</h2>
      <form @submit.prevent="onCreateUser" class="form-grid">
        <div class="field">
          <label class="field__label">Nom d'utilisateur</label>
          <input v-model="form.username" class="input" placeholder="jean" required />
        </div>
        <div class="field">
          <label class="field__label">Email</label>
          <input v-model="form.email" type="email" class="input" placeholder="jean@example.com" required />
        </div>
        <div class="field">
          <label class="field__label">Mot de passe</label>
          <input v-model="form.password" type="password" class="input" placeholder="••••••••" required minlength="6" />
        </div>
        <div class="field field--checkbox">
          <label class="checkbox-label">
            <input v-model="form.is_admin" type="checkbox" class="checkbox" />
            <span>Administrateur</span>
          </label>
        </div>
        <div v-if="createError" class="field-error">{{ createError }}</div>
        <div class="form-actions">
          <button type="submit" class="btn btn--primary" :disabled="creating">
            {{ creating ? 'Création…' : 'Créer' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Chargement / erreur -->
    <div v-if="loading" class="state-msg">Chargement…</div>
    <div v-else-if="error" class="state-msg state-msg--error">{{ error }}</div>

    <!-- Liste -->
    <ul v-else class="user-list">
      <li v-for="u in users" :key="u.id" class="user-card card">

        <div class="user-card__main">
          <div class="user-avatar">{{ u.username[0].toUpperCase() }}</div>
          <div class="user-info">
            <div class="user-info__name">
              {{ u.username }}
              <span v-if="u.id === me?.id" class="badge badge--muted">Vous</span>
              <span v-if="u.is_admin" class="badge badge--accent">Admin</span>
            </div>
            <div class="user-info__email">{{ u.email }}</div>
          </div>
        </div>

        <div class="user-card__actions">

          <!-- Toggle admin -->
          <button
            v-if="u.id !== me?.id"
            class="btn btn--ghost btn--sm"
            :title="u.is_admin ? 'Rétrograder' : 'Promouvoir admin'"
            @click="toggleAdmin(u)"
          >
            {{ u.is_admin ? 'Rétrograder' : 'Rendre admin' }}
          </button>

          <!-- Changer mot de passe -->
          <button class="btn btn--ghost btn--sm" @click="editingPasswordId = u.id; newPassword = ''; passwordError = null">
            Mot de passe
          </button>

          <!-- Supprimer -->
          <button
            v-if="u.id !== me?.id"
            class="btn btn--danger btn--sm"
            @click="confirmDeleteId = u.id"
          >
            Supprimer
          </button>

        </div>

        <!-- Inline : changement de mot de passe -->
        <div v-if="editingPasswordId === u.id" class="inline-edit animate-slide-up">
          <input
            v-model="newPassword"
            type="password"
            class="input input--sm"
            placeholder="Nouveau mot de passe"
            minlength="6"
            @keyup.enter="savePassword(u.id)"
          />
          <button class="btn btn--primary btn--sm" :disabled="savingPassword" @click="savePassword(u.id)">
            {{ savingPassword ? '…' : 'Enregistrer' }}
          </button>
          <button class="btn btn--ghost btn--sm" @click="editingPasswordId = null">Annuler</button>
          <div v-if="passwordError" class="field-error">{{ passwordError }}</div>
        </div>

        <!-- Inline : confirmation suppression -->
        <div v-if="confirmDeleteId === u.id" class="inline-edit inline-edit--danger animate-slide-up">
          <span>Supprimer <strong>{{ u.username }}</strong> ? Cette action est irréversible.</span>
          <div class="inline-edit__btns">
            <button class="btn btn--danger btn--sm" :disabled="deleting" @click="deleteUser(u.id)">
              {{ deleting ? '…' : 'Confirmer' }}
            </button>
            <button class="btn btn--ghost btn--sm" @click="confirmDeleteId = null">Annuler</button>
          </div>
        </div>

      </li>
    </ul>

  </div>
</template>

<style scoped>
.users-view {
  max-width: 680px;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── En-tête ── */
.view-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.view-title    { font-family: var(--font-display); font-size: 1.4rem; font-weight: 800; letter-spacing: -.02em; }
.view-subtitle { font-size: .85rem; color: var(--color-muted); margin-top: .2rem; }

/* ── Formulaire de création ── */
.create-form  { padding: 1.25rem; }
.form-title   { font-family: var(--font-display); font-size: 1rem; font-weight: 700; margin-bottom: 1rem; }
.form-grid    { display: flex; flex-direction: column; gap: .75rem; }
.field        { display: flex; flex-direction: column; gap: .3rem; }
.field__label { font-size: .75rem; font-weight: 600; color: var(--color-muted); text-transform: uppercase; letter-spacing: .06em; }
.field--checkbox { flex-direction: row; align-items: center; }
.checkbox-label  { display: flex; align-items: center; gap: .5rem; font-size: .875rem; cursor: pointer; }
.checkbox        { width: 16px; height: 16px; accent-color: var(--color-accent); }
.form-actions { display: flex; justify-content: flex-end; padding-top: .25rem; }
.field-error  { font-size: .8rem; color: var(--color-danger); }

/* ── Liste ── */
.user-list { list-style: none; display: flex; flex-direction: column; gap: .75rem; }

.user-card {
  display: flex;
  flex-direction: column;
  gap: .75rem;
  padding: 1rem 1.25rem;
}

.user-card__main {
  display: flex;
  align-items: center;
  gap: .875rem;
}

.user-avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info         { flex: 1; min-width: 0; }
.user-info__name   { display: flex; align-items: center; gap: .4rem; font-weight: 600; font-size: .925rem; flex-wrap: wrap; }
.user-info__email  { font-size: .8rem; color: var(--color-muted); margin-top: .1rem; }

.badge            { font-size: .65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; padding: .15rem .45rem; border-radius: 999px; }
.badge--accent    { background: #fff3ed; color: var(--color-accent); }
.badge--muted     { background: var(--color-surface-2); color: var(--color-muted); border: 1px solid var(--color-border); }

.user-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: .5rem;
}

/* ── Inline edit (mot de passe / confirmation) ── */
.inline-edit {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .5rem;
  padding: .75rem 1rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: .875rem;
}
.inline-edit--danger {
  background: #fef2f2;
  border-color: #fecaca;
  flex-direction: column;
  align-items: flex-start;
}
.inline-edit__btns { display: flex; gap: .5rem; }

/* ── Boutons taille sm ── */
.btn--sm { font-size: .78rem; padding: .3rem .65rem; }
.btn--danger {
  background: var(--color-danger);
  color: #fff;
  border: none;
}
.btn--danger:hover { background: #b91c1c; }

/* ── État vide / erreur ── */
.state-msg         { font-size: .9rem; color: var(--color-muted); padding: 2rem 0; text-align: center; }
.state-msg--error  { color: var(--color-danger); }

/* ── Input sm ── */
.input--sm { padding: .35rem .6rem; font-size: .875rem; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-slide-up { animation: slideUp .18s ease; }
</style>
