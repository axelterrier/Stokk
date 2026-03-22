import { createRouter, createWebHistory } from 'vue-router'
import StockView    from '@/views/StockView.vue'
import RecipesView  from '@/views/RecipesView.vue'
import SettingsView from '@/views/SettingsView.vue'
import UsersView    from '@/views/UsersView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',         component: StockView },
    { path: '/recipes',  component: RecipesView },
    { path: '/settings', component: SettingsView },
    { path: '/users',    component: UsersView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
