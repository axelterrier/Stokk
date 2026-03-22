<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getToken } from '@/composables/useApi'
import { useAuth } from '@/composables/useAuth'
import LoginForm from '@/components/LoginForm.vue'
import AppLayout from '@/components/AppLayout.vue'

const router = useRouter()
const { fetchMe } = useAuth()
const isAuthenticated = ref(!!getToken())

async function onLoginSuccess() {
  isAuthenticated.value = true
  await fetchMe()
  router.push('/')
}

onMounted(async () => {
  if (isAuthenticated.value) {
    await fetchMe()
    // Si fetchMe a vidé le token (expiré), on revient au login
    if (!getToken()) isAuthenticated.value = false
  }
})
</script>

<template>
  <LoginForm v-if="!isAuthenticated" @success="onLoginSuccess" />
  <AppLayout v-else />
</template>
